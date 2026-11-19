# -*- coding: utf-8 -*-
"""
Collect Files for Maya - Free Edition (After Effects style)
Ultra-fast non-destructive single-scene texture & external asset collector (.ma / .mb)
Zero mayapy subprocess overhead & streaming .ma relinker
Maya 2022 - 2027 (PySide2 / PySide6 compatible, Zero external dependencies)
Bilingual UI (Japanese / English)
"""

import os
import re
import time
import shutil
import concurrent.futures
import maya.cmds as cmds
import maya.mel as mel
import maya.OpenMayaUI as omui

try:
    from PySide6 import QtWidgets, QtCore, QtGui
    from shiboken6 import wrapInstance
except ImportError:
    from PySide2 import QtWidgets, QtCore, QtGui
    from shiboken2 import wrapInstance


WINDOW_OBJECT_NAME = "MayaCollectFilesDialog"
SHELF_LABEL = "CFM"
OPTION_VAR_LANG = "CFM_free_ui_language"

# ---------------------------------------------------------------------------
# 多言語対応 (日本語 / English)
# ---------------------------------------------------------------------------
_EN = {
    "Collect Files for Maya (ファイル収集)": "Collect Files for Maya",
    "1. 保存先とフォルダ名": "1. Destination & Folder Name",
    "保存先の親フォルダを選択...": "Select destination parent folder...",
    "参照...": "Browse...",
    "保存先フォルダ:": "Destination Folder:",
    "新規フォルダ名:": "New Folder Name:",
    "2. 収集オプション": "2. Collection Options",
    "テクスチャ等の外部ファイルを収集する": "Collect external assets (textures, audio, caches)",
    "サブフォルダに分けて整理する (scenes / sourceimages)": "Organize into subfolders (scenes / sourceimages)",
    "workspace.mel を自動生成して相対パス化する（推奨）": "Auto-generate workspace.mel for relative paths (Recommended)",
    "収集完了後にフォルダを開く": "Open folder after collection",
    "待機中...": "Ready...",
    "テクスチャ・外部アセットを収集中...": "Collecting textures and external assets...",
    "メインシーンを書き出し中...": "Exporting main scene...",
    "シーン内部のリンクを書き換え中...": "Relinking paths inside scene file...",
    "収集を実行 (Collect Files)": "Collect Files",
    "閉じる": "Close",
    "保存先フォルダを選択": "Select Destination Folder",
    "エラー": "Error",
    "上書き確認": "Confirm Overwrite",
    "Collect Files 完了": "Collect Files Complete",
    "有効な保存先フォルダを指定してください。": "Please specify a valid destination folder.",
    "収集フォルダ名を入力してください。": "Please enter a folder name.",
    "既に空でない同名フォルダが存在します:\n{path}": "A non-empty folder with the same name already exists:\n{path}",
    "既に同名のフォルダが存在します:\n{path}\n\n既存のフォルダを削除して上書きしますか？": (
        "A non-empty folder with the same name already exists:\n{path}\n\nDo you want to delete the existing folder and overwrite it?"
    ),
    "元データを含むフォルダは上書きできません:\n{path}": "Cannot overwrite a folder that contains the source scene:\n{path}",
    "収集が完了しました！ ({elapsed:.2f} 秒)\n\n出力先:\n{root}\n\nコピーした外部ファイル数: {asset_count} 件": (
        "Collection complete! ({elapsed:.2f} sec)\n\nOutput folder:\n{root}\n\nExternal files copied: {asset_count}"
    ),
    "\n...他 {count} 件": "\n...and {count} more",
    "\n\n【注意】リンク切れのためスキップされたファイル ({count} 件):\n{preview}{extra}": (
        "\n\n[Warning] Skipped missing/broken files ({count}):\n{preview}{extra}"
    ),
}

_CURRENT_LANG = None


def get_lang():
    global _CURRENT_LANG
    if _CURRENT_LANG in ("JA", "EN"):
        return _CURRENT_LANG

    try:
        if cmds.optionVar(exists=OPTION_VAR_LANG):
            saved = cmds.optionVar(q=OPTION_VAR_LANG)
            if saved in ("JA", "EN"):
                _CURRENT_LANG = saved
                return _CURRENT_LANG
    except Exception:
        pass

    try:
        ui_lang = cmds.about(uiLanguage=True) or ""
        _CURRENT_LANG = "JA" if ui_lang.lower().startswith("ja") else "EN"
    except Exception:
        _CURRENT_LANG = "JA"

    return _CURRENT_LANG


def set_lang(lang):
    global _CURRENT_LANG
    if lang not in ("JA", "EN"):
        return
    _CURRENT_LANG = lang
    try:
        cmds.optionVar(sv=(OPTION_VAR_LANG, lang))
    except Exception:
        pass


def tr(text):
    if get_lang() == "EN":
        return _EN.get(text, text)
    return text


def get_maya_main_window():
    ptr = omui.MQtUtil.mainWindow()
    if ptr is not None:
        return wrapInstance(int(ptr), QtWidgets.QWidget)
    return None


def install_shelf_button():
    """現在選択中のシェルフに「CFM」ボタンを登録する（既存ボタンがあれば置き換え）"""
    shelf_top = mel.eval("$tmp = $gShelfTopLevel")
    if not shelf_top or not cmds.tabLayout(shelf_top, exists=True):
        raise RuntimeError("シェルフが見つかりませんでした。 / Shelf layout not found.")

    current_shelf = cmds.tabLayout(shelf_top, query=True, selectTab=True)
    if not current_shelf:
        raise RuntimeError("アクティブなシェルフタブを取得できませんでした。 / Active shelf tab not found.")

    existing_buttons = cmds.shelfLayout(current_shelf, query=True, childArray=True) or []
    for btn in existing_buttons:
        if not cmds.shelfButton(btn, exists=True):
            continue
        label = cmds.shelfButton(btn, query=True, label=True) or ""
        overlay = cmds.shelfButton(btn, query=True, imageOverlayLabel=True) or ""
        cmd = cmds.shelfButton(btn, query=True, command=True) or ""
        if label == SHELF_LABEL or overlay == SHELF_LABEL or "collect_files_maya" in cmd:
            cmds.deleteUI(btn)

    cmds.shelfButton(
        parent=current_shelf,
        label=SHELF_LABEL,
        imageOverlayLabel=SHELF_LABEL,
        annotation="Collect Files for Maya (シーン＆外部アセット収集 / Scene & Asset Collector)",
        image1="pythonFamily.png",
        command=(
            "import importlib, collect_files_maya\n"
            "importlib.reload(collect_files_maya)\n"
            "collect_files_maya.show()"
        ),
        sourceType="python",
    )

    try:
        cmds.saveAllShelves(shelf_top)
    except Exception:
        pass


def norm_key(path):
    """OSのパス表記揺れを吸収した比較用正規化キーを返す"""
    if not path:
        return ""
    return os.path.normcase(os.path.abspath(path)).replace("\\", "/")


def _is_unsafe_overwrite_target(collect_root, orig_scene_path):
    """ドライブルートや元シーンを含むフォルダの誤削除を防ぐ安全チェック"""
    abs_root = os.path.abspath(collect_root)
    if os.path.dirname(abs_root) == abs_root:
        return True

    norm_root = norm_key(abs_root)
    if orig_scene_path:
        norm_src = norm_key(orig_scene_path)
        if norm_src == norm_root or norm_src.startswith(norm_root + "/"):
            return True

    return False


def write_minimal_workspace_mel(project_dir):
    """他のPCや別ドライブへ移動しても相対パスが通るようにworkspace.melを生成する"""
    mel_content = (
        '//Maya Project Definition\n'
        'workspace -fr "scene" "scenes";\n'
        'workspace -fr "sourceImages" "sourceimages";\n'
        'workspace -fr "images" "images";\n'
        'workspace -fr "alembicCache" "cache/alembic";\n'
        'workspace -fr "gpuCache" "cache/gpu";\n'
        'workspace -fr "audio" "sound";\n'
    )
    mel_path = os.path.join(project_dir, "workspace.mel")
    with open(mel_path, "w", encoding="utf-8") as f:
        f.write(mel_content)


def _get_cached_dir_entries(dir_name, dir_cache):
    """フォルダ内のファイル一覧を1回だけscandirで取得しキャッシュする"""
    d_key = norm_key(dir_name)
    if d_key in dir_cache:
        return dir_cache[d_key]

    files_lower_set = set()
    try:
        with os.scandir(dir_name) as it:
            for entry in it:
                if entry.is_file():
                    files_lower_set.add(entry.name.lower())
    except OSError:
        pass

    dir_cache[d_key] = files_lower_set
    return files_lower_set


def _resolve_candidate_path(raw_path, parent_scene_dir=None, workspace_root=None, dir_cache=None):
    """パス文字列を実在ファイルパスへ高速解決する"""
    if not raw_path:
        return ""
    clean = raw_path.split("{")[0].strip().replace("\\", "/")
    if not clean:
        return ""

    def exists_fast(cand):
        if dir_cache is not None:
            d = os.path.dirname(cand)
            b = os.path.basename(cand).lower()
            return b in _get_cached_dir_entries(d, dir_cache)
        return os.path.isfile(cand)

    if os.path.isabs(clean) and exists_fast(clean):
        return os.path.abspath(clean).replace("\\", "/")

    ws_roots = []
    if workspace_root:
        ws_roots.append(workspace_root)
    try:
        cur_ws = cmds.workspace(q=True, rd=True)
        if cur_ws and cur_ws not in ws_roots:
            ws_roots.append(cur_ws)
    except Exception:
        pass

    for ws in ws_roots:
        cand = os.path.join(ws, clean).replace("\\", "/")
        if exists_fast(cand):
            return os.path.abspath(cand).replace("\\", "/")

    if parent_scene_dir:
        cand = os.path.join(parent_scene_dir, clean).replace("\\", "/")
        if exists_fast(cand):
            return os.path.abspath(cand).replace("\\", "/")

    return clean


def _detect_ma_encoding(ma_path):
    """先頭64KBのみを読み取ってMaya ASCII (.ma) のエンコーディングを高速判定する"""
    with open(ma_path, "rb") as fb:
        sample = fb.read(65536)
    for enc in ("utf-8", "cp932", "latin-1"):
        try:
            sample.decode(enc)
            return enc
        except UnicodeDecodeError:
            continue
    return "utf-8"


_SETATTR_STR_RE = re.compile(
    r'^(\s*setAttr\b.*?-type\s+"string"\s+")([^"\\]*(?:\\.[^"\\]*)*)(";\s*)$'
)


def _repath_copied_ma_file(
    copied_ma_path,
    orig_ma_path,
    asset_path_map,
    asset_basename_map=None,
    workspace_root=None,
    dir_cache=None,
):
    """
    コピーされた .ma ファイルを1行ずつストリーム書き換えする。
    頂点座標やアニメーションカーブ等の数値データ行は正規表現を通さず高速スキップする。
    """
    enc = _detect_ma_encoding(copied_ma_path)
    orig_dir = os.path.dirname(orig_ma_path) if orig_ma_path else workspace_root
    asset_basename_map = asset_basename_map or {}

    def lookup_new_asset(raw_str):
        if not raw_str or ("/" not in raw_str and "\\" not in raw_str and "." not in raw_str):
            return None
        clean = raw_str.strip().replace("\\", "/")
        resolved = _resolve_candidate_path(
            clean,
            parent_scene_dir=orig_dir,
            workspace_root=workspace_root,
            dir_cache=dir_cache,
        )
        k = norm_key(resolved)
        if k in asset_path_map:
            return asset_path_map[k]
        if os.path.isabs(clean):
            k_raw = norm_key(clean)
            if k_raw in asset_path_map:
                return asset_path_map[k_raw]
        bname = os.path.basename(clean).lower()
        return asset_basename_map.get(bname)

    tmp_out = f"{copied_ma_path}.cfm_tmp"
    try:
        with open(copied_ma_path, "r", encoding=enc, errors="replace") as fin, \
             open(tmp_out, "w", encoding=enc, errors="replace") as fout:
            for line in fin:
                stripped = line.lstrip()
                if stripped.startswith("setAttr ") and '"string"' in line:
                    m_attr = _SETATTR_STR_RE.match(line)
                    if m_attr:
                        new_val = lookup_new_asset(m_attr.group(2))
                        if new_val:
                            fout.write(f"{m_attr.group(1)}{new_val}{m_attr.group(3)}")
                            continue
                fout.write(line)

        os.replace(tmp_out, copied_ma_path)
    finally:
        if os.path.exists(tmp_out):
            try:
                os.remove(tmp_out)
            except OSError:
                pass


def _export_mb_in_process(
    dest_scene_path,
    orig_scene_path,
    was_modified,
    orig_workspace,
    collect_root,
    create_workspace,
    asset_repath_map,
    asset_basename_map,
    dir_cache,
):
    """
    mayapy を一切起動せず、現在の Maya メモリ上で一時的にアセットパスを相対化して
    .mb シーンを書き出し、finally で元の作業中シーン状態を100%復元する。
    """
    orig_dir = os.path.dirname(orig_scene_path) if orig_scene_path else orig_workspace

    def lookup_new_asset(raw_str, fallback_dir=None):
        if not raw_str:
            return None
        clean = raw_str.strip().replace("\\", "/")
        if not clean:
            return None
        resolved = _resolve_candidate_path(
            clean,
            parent_scene_dir=fallback_dir or orig_dir,
            workspace_root=orig_workspace,
            dir_cache=dir_cache,
        )
        k = norm_key(resolved)
        if k in asset_repath_map:
            return asset_repath_map[k]
        if os.path.isabs(clean):
            k_raw = norm_key(clean)
            if k_raw in asset_repath_map:
                return asset_repath_map[k_raw]
        bname = os.path.basename(clean).lower()
        return asset_basename_map.get(bname)

    attr_restore_list = []
    seen_attrs = set()

    cmds.refresh(suspend=True)
    cmds.undoInfo(stateWithoutFlush=False)
    try:
        if create_workspace and os.path.isdir(collect_root):
            try:
                cmds.workspace(collect_root, openWorkspace=True)
            except Exception:
                pass

        # 1. リファレンス以外の外部アセットパス属性を一時的に相対パスへ書き換え
        dirs = cmds.filePathEditor(query=True, listDirectories="") or []
        for d in dirs:
            pairs = cmds.filePathEditor(query=True, listFiles=d, withAttribute=True) or []
            for i in range(0, len(pairs), 2):
                fn = pairs[i]
                node_attr = pairs[i + 1]
                if node_attr in seen_attrs:
                    continue
                node_name = node_attr.split(".")[0]
                if ":" in node_name:
                    continue
                if not cmds.objExists(node_name) or cmds.nodeType(node_name) == "reference":
                    continue

                try:
                    orig_val = cmds.getAttr(node_attr) or ""
                except Exception:
                    continue

                new_val = (
                    lookup_new_asset(orig_val, d)
                    or lookup_new_asset(os.path.join(d, fn), d)
                )
                if new_val and new_val != orig_val:
                    try:
                        cmds.setAttr(node_attr, new_val, type="string")
                        attr_restore_list.append((node_attr, orig_val))
                        seen_attrs.add(node_attr)
                    except Exception:
                        pass

        # fileノードの直接補完（filePathEditor 未検出項目対策）
        for f_node in (cmds.ls(type="file") or []):
            if ":" in f_node:
                continue
            node_attr = f"{f_node}.fileTextureName"
            if node_attr in seen_attrs:
                continue
            try:
                orig_val = cmds.getAttr(node_attr) or ""
            except Exception:
                continue
            new_val = lookup_new_asset(orig_val, orig_dir)
            if new_val and new_val != orig_val:
                try:
                    cmds.setAttr(node_attr, new_val, type="string")
                    attr_restore_list.append((node_attr, orig_val))
                    seen_attrs.add(node_attr)
                except Exception:
                    pass

        # 2. 収集先パスへ .mb シーンを書き出し
        cmds.file(rename=dest_scene_path)
        cmds.file(save=True, type="mayaBinary", force=True)

    finally:
        # 3. 作業中シーンのパス・ワークスペース・アトリビュート・未保存フラグを完全復元
        try:
            cmds.file(rename=orig_scene_path if orig_scene_path else "untitled")

            if orig_workspace and os.path.isdir(orig_workspace):
                try:
                    cmds.workspace(orig_workspace, openWorkspace=True)
                except Exception:
                    pass

            for node_attr, orig_val in reversed(attr_restore_list):
                try:
                    cmds.setAttr(node_attr, orig_val, type="string")
                except Exception:
                    pass

            try:
                cmds.file(modified=was_modified)
            except Exception:
                pass
        finally:
            cmds.undoInfo(stateWithoutFlush=True)
            cmds.refresh(suspend=False)


def collect_scene_files(
    parent_dir,
    folder_name,
    collect_assets=True,
    create_workspace=True,
    use_subfolders=True,
    overwrite=False,
    progress_cb=None,
):
    """
    現在のシーンと外部アセットを完全非破壊かつインプロセスで高速収集し、
    コピー先のシーンファイル内部のパスも相対パスへ書き換えて保存する。
    """
    t_start = time.perf_counter()

    def report_progress(pct, msg_key):
        if progress_cb:
            progress_cb(pct, tr(msg_key))

    if not parent_dir or not os.path.isdir(parent_dir):
        raise RuntimeError(tr("有効な保存先フォルダを指定してください。"))

    safe_folder = re.sub(r'[<>:"/\\|?*]', "_", folder_name.strip())
    if not safe_folder:
        raise RuntimeError(tr("収集フォルダ名を入力してください。"))

    orig_scene_path = cmds.file(q=True, sn=True)
    collect_root = os.path.join(parent_dir, safe_folder).replace("\\", "/")

    if os.path.exists(collect_root) and os.listdir(collect_root):
        if not overwrite:
            raise RuntimeError(tr("既に空でない同名フォルダが存在します:\n{path}").format(path=collect_root))
        if _is_unsafe_overwrite_target(collect_root, orig_scene_path):
            raise RuntimeError(tr("元データを含むフォルダは上書きできません:\n{path}").format(path=collect_root))
        shutil.rmtree(collect_root)

    os.makedirs(collect_root, exist_ok=True)

    scenes_dir = os.path.join(collect_root, "scenes").replace("\\", "/") if use_subfolders else collect_root
    assets_dir = os.path.join(collect_root, "sourceimages").replace("\\", "/") if use_subfolders else collect_root
    os.makedirs(scenes_dir, exist_ok=True)
    os.makedirs(assets_dir, exist_ok=True)

    orig_scene_type = cmds.file(q=True, type=True)
    orig_file_type = orig_scene_type[0] if orig_scene_type else "mayaAscii"
    was_modified = cmds.file(q=True, modified=True)
    orig_workspace = cmds.workspace(q=True, rd=True)

    if orig_scene_path:
        scene_filename = os.path.basename(orig_scene_path)
    else:
        ext = ".mb" if orig_file_type == "mayaBinary" else ".ma"
        scene_filename = f"untitled{ext}"

    dest_scene_path = os.path.join(scenes_dir, scene_filename).replace("\\", "/")

    dir_cache = {}
    copy_jobs = []               # [(src_abs, dst_abs), ...]
    copied_assets_map = {}       # norm_key(src) -> dst_abs_path
    asset_repath_map = {}        # norm_key(src) -> new_scene_rel_or_abs_path
    asset_basename_map = {}      # lower(basename) -> new_scene_rel_or_abs_path

    used_asset_names = set()
    copied_asset_count = 0
    missing_files = []
    missing_seen = set()

    def add_missing(p):
        k = p.lower()
        if k not in missing_seen:
            missing_seen.add(k)
            missing_files.append(p)

    def get_unique_dest_path(target_dir, src_path, used_set):
        base_name = os.path.basename(src_path)
        stem, ext = os.path.splitext(base_name)
        candidate = base_name
        counter = 1
        while candidate.lower() in used_set:
            candidate = f"{stem}_{counter}{ext}"
            counter += 1
        used_set.add(candidate.lower())
        return os.path.join(target_dir, candidate).replace("\\", "/")

    def format_scene_rel_path(dst_abs_path):
        if use_subfolders and create_workspace:
            # scenes/ 内のシーンから相対解決できるよう ../sourceimages/ を使用
            return f"../sourceimages/{os.path.basename(dst_abs_path)}"
        return dst_abs_path

    if create_workspace:
        write_minimal_workspace_mel(collect_root)

    # ------------------------------------------------------------------
    # 1. テクスチャ等の外部アセット収集計画＆コピー
    # ------------------------------------------------------------------
    report_progress(30, "テクスチャ・外部アセットを収集中...")
    if collect_assets:
        dirs = cmds.filePathEditor(query=True, listDirectories="") or []
        for d in dirs:
            d_entries = _get_cached_dir_entries(d, dir_cache)
            pairs = cmds.filePathEditor(query=True, listFiles=d, withAttribute=True) or []
            for i in range(0, len(pairs), 2):
                file_name = pairs[i]
                node_attr = pairs[i + 1]
                node_name = node_attr.split(".")[0]

                if cmds.objExists(node_name) and cmds.nodeType(node_name) == "reference":
                    continue
                if ":" in node_name:
                    continue

                src_full = os.path.join(d, file_name).replace("\\", "/")
                if file_name.lower() not in d_entries and not os.path.isfile(src_full):
                    add_missing(src_full)
                    continue

                sk = norm_key(src_full)
                if sk not in copied_assets_map:
                    dst_single = get_unique_dest_path(assets_dir, src_full, used_asset_names)
                    copy_jobs.append((src_full, dst_single))
                    rel_single = format_scene_rel_path(dst_single)
                    copied_assets_map[sk] = dst_single
                    asset_repath_map[sk] = rel_single
                    asset_basename_map.setdefault(os.path.basename(src_full).lower(), rel_single)
                    copied_asset_count += 1

    if copy_jobs:
        if len(copy_jobs) >= 16:
            with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
                futures = [executor.submit(shutil.copy2, src, dst) for src, dst in copy_jobs]
                for fut in concurrent.futures.as_completed(futures):
                    fut.result()
        else:
            for src, dst in copy_jobs:
                shutil.copy2(src, dst)

    # ------------------------------------------------------------------
    # 2 & 3. メインシーンの書き出し＆内部パスの高速リリンク
    # ------------------------------------------------------------------
    report_progress(70, "シーン内部のリンクを書き換え中...")
    if dest_scene_path.lower().endswith(".mb"):
        _export_mb_in_process(
            dest_scene_path=dest_scene_path,
            orig_scene_path=orig_scene_path,
            was_modified=was_modified,
            orig_workspace=orig_workspace,
            collect_root=collect_root,
            create_workspace=create_workspace,
            asset_repath_map=asset_repath_map,
            asset_basename_map=asset_basename_map,
            dir_cache=dir_cache,
        )
    else:
        if orig_scene_path and os.path.isfile(orig_scene_path) and not was_modified:
            shutil.copy2(orig_scene_path, dest_scene_path)
        else:
            try:
                cmds.file(rename=dest_scene_path)
                cmds.file(save=True, type=orig_file_type, force=True)
            finally:
                if orig_scene_path:
                    cmds.file(rename=orig_scene_path)
                else:
                    cmds.file(rename="untitled")
                cmds.file(modified=was_modified)

        _repath_copied_ma_file(
            copied_ma_path=dest_scene_path,
            orig_ma_path=orig_scene_path or os.path.join(orig_workspace, scene_filename),
            asset_path_map=asset_repath_map,
            asset_basename_map=asset_basename_map,
            workspace_root=orig_workspace,
            dir_cache=dir_cache,
        )

    report_progress(100, "待機中...")
    elapsed = time.perf_counter() - t_start

    return collect_root, copied_asset_count, missing_files, elapsed


class CollectFilesDialog(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName(WINDOW_OBJECT_NAME)
        self.setMinimumWidth(480)
        self.setWindowFlags(self.windowFlags() ^ QtCore.Qt.WindowContextHelpButtonHint)
        self._build_ui()
        self._set_defaults()
        self._retranslate_ui()

    def _build_ui(self):
        layout = QtWidgets.QVBoxLayout(self)
        layout.setSpacing(10)

        # 言語切り替えバー (日本語 / English)
        lang_row = QtWidgets.QHBoxLayout()
        lang_row.setSpacing(2)
        lang_row.addStretch()

        self.btn_ja = QtWidgets.QPushButton("日本語")
        self.btn_en = QtWidgets.QPushButton("English")
        for btn in (self.btn_ja, self.btn_en):
            btn.setCheckable(True)
            btn.setAutoExclusive(True)
            btn.setFixedHeight(22)
            btn.setMinimumWidth(68)

        cur_lang = get_lang()
        self.btn_ja.setChecked(cur_lang == "JA")
        self.btn_en.setChecked(cur_lang == "EN")

        self.btn_ja.clicked.connect(lambda: self._on_change_language("JA"))
        self.btn_en.clicked.connect(lambda: self._on_change_language("EN"))

        lang_row.addWidget(self.btn_ja)
        lang_row.addWidget(self.btn_en)
        layout.addLayout(lang_row)

        # 1. 保存先親フォルダ
        self.dir_group = QtWidgets.QGroupBox()
        dir_form = QtWidgets.QFormLayout(self.dir_group)

        path_row = QtWidgets.QHBoxLayout()
        self.dir_edit = QtWidgets.QLineEdit()
        self.browse_btn = QtWidgets.QPushButton()
        self.browse_btn.setFixedWidth(78)
        self.browse_btn.clicked.connect(self._browse_dir)
        path_row.addWidget(self.dir_edit)
        path_row.addWidget(self.browse_btn)

        self.lbl_dest_dir = QtWidgets.QLabel()
        dir_form.addRow(self.lbl_dest_dir, path_row)

        self.lbl_folder_name = QtWidgets.QLabel()
        self.folder_name_edit = QtWidgets.QLineEdit()
        dir_form.addRow(self.lbl_folder_name, self.folder_name_edit)
        layout.addWidget(self.dir_group)

        # 2. 収集オプション
        self.opt_group = QtWidgets.QGroupBox()
        opt_layout = QtWidgets.QVBoxLayout(self.opt_group)

        self.chk_assets = QtWidgets.QCheckBox()
        self.chk_assets.setChecked(True)

        self.chk_subfolders = QtWidgets.QCheckBox()
        self.chk_subfolders.setChecked(True)

        self.chk_workspace = QtWidgets.QCheckBox()
        self.chk_workspace.setChecked(True)

        self.chk_open_folder = QtWidgets.QCheckBox()
        self.chk_open_folder.setChecked(True)

        opt_layout.addWidget(self.chk_assets)
        opt_layout.addWidget(self.chk_subfolders)
        opt_layout.addWidget(self.chk_workspace)
        opt_layout.addWidget(self.chk_open_folder)
        layout.addWidget(self.opt_group)

        # 進行状況バー
        self.status_label = QtWidgets.QLabel()
        self.status_label.setStyleSheet("color: #aaaaaa; font-size: 11px;")
        self.progress_bar = QtWidgets.QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setFixedHeight(6)
        layout.addWidget(self.status_label)
        layout.addWidget(self.progress_bar)

        # 3. 実行ボタン
        btn_row = QtWidgets.QHBoxLayout()
        self.run_btn = QtWidgets.QPushButton()
        self.run_btn.setMinimumHeight(34)
        self.run_btn.setStyleSheet("font-weight: bold;")
        self.run_btn.clicked.connect(self._on_collect)

        self.close_btn = QtWidgets.QPushButton()
        self.close_btn.setMinimumHeight(34)
        self.close_btn.setFixedWidth(90)
        self.close_btn.clicked.connect(self.close)

        btn_row.addWidget(self.run_btn)
        btn_row.addWidget(self.close_btn)
        layout.addLayout(btn_row)

    def _on_change_language(self, lang):
        set_lang(lang)
        self._retranslate_ui()

    def _retranslate_ui(self):
        self.setWindowTitle(tr("Collect Files for Maya (ファイル収集)"))
        self.dir_group.setTitle(tr("1. 保存先とフォルダ名"))
        self.dir_edit.setPlaceholderText(tr("保存先の親フォルダを選択..."))
        self.browse_btn.setText(tr("参照..."))
        self.lbl_dest_dir.setText(tr("保存先フォルダ:"))
        self.lbl_folder_name.setText(tr("新規フォルダ名:"))

        self.opt_group.setTitle(tr("2. 収集オプション"))
        self.chk_assets.setText(tr("テクスチャ等の外部ファイルを収集する"))
        self.chk_subfolders.setText(tr("サブフォルダに分けて整理する (scenes / sourceimages)"))
        self.chk_workspace.setText(tr("workspace.mel を自動生成して相対パス化する（推奨）"))
        self.chk_open_folder.setText(tr("収集完了後にフォルダを開く"))

        self.status_label.setText(tr("待機中..."))
        self.run_btn.setText(tr("収集を実行 (Collect Files)"))
        self.close_btn.setText(tr("閉じる"))

    def _set_defaults(self):
        sn = cmds.file(q=True, sn=True)
        if sn:
            self.dir_edit.setText(os.path.dirname(sn))
            stem = os.path.splitext(os.path.basename(sn))[0]
            self.folder_name_edit.setText(f"{stem}_Collected")
        else:
            desktop = os.path.join(os.path.expanduser("~"), "Desktop").replace("\\", "/")
            self.dir_edit.setText(desktop)
            self.folder_name_edit.setText("MayaScene_Collected")

    def _browse_dir(self):
        start_dir = self.dir_edit.text() or os.path.expanduser("~")
        selected = QtWidgets.QFileDialog.getExistingDirectory(self, tr("保存先フォルダを選択"), start_dir)
        if selected:
            self.dir_edit.setText(selected.replace("\\", "/"))

    def _update_progress(self, pct, status_text):
        self.progress_bar.setValue(pct)
        self.status_label.setText(status_text)
        QtWidgets.QApplication.processEvents(QtCore.QEventLoop.ExcludeUserInputEvents)

    def _on_collect(self):
        parent_dir = self.dir_edit.text()
        folder_name = self.folder_name_edit.text()
        allow_overwrite = False

        if not parent_dir or not os.path.isdir(parent_dir):
            QtWidgets.QMessageBox.critical(self, tr("エラー"), tr("有効な保存先フォルダを指定してください。"))
            return

        safe_folder = re.sub(r'[<>:"/\\|?*]', "_", folder_name.strip())
        if not safe_folder:
            QtWidgets.QMessageBox.critical(self, tr("エラー"), tr("収集フォルダ名を入力してください。"))
            return

        target_root = os.path.join(parent_dir, safe_folder).replace("\\", "/")
        if os.path.exists(target_root) and os.listdir(target_root):
            orig_scene = cmds.file(q=True, sn=True)
            if _is_unsafe_overwrite_target(target_root, orig_scene):
                QtWidgets.QMessageBox.critical(
                    self,
                    tr("エラー"),
                    tr("元データを含むフォルダは上書きできません:\n{path}").format(path=target_root),
                )
                return

            ans = QtWidgets.QMessageBox.question(
                self,
                tr("上書き確認"),
                tr("既に同名のフォルダが存在します:\n{path}\n\n既存のフォルダを削除して上書きしますか？").format(path=target_root),
                QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
                QtWidgets.QMessageBox.No,
            )
            if ans != QtWidgets.QMessageBox.Yes:
                return
            allow_overwrite = True

        self.run_btn.setEnabled(False)
        QtWidgets.QApplication.setOverrideCursor(QtCore.Qt.WaitCursor)
        try:
            collect_root, asset_count, missing, elapsed = collect_scene_files(
                parent_dir=parent_dir,
                folder_name=folder_name,
                collect_assets=self.chk_assets.isChecked(),
                create_workspace=self.chk_workspace.isChecked(),
                use_subfolders=self.chk_subfolders.isChecked(),
                overwrite=allow_overwrite,
                progress_cb=self._update_progress,
            )
        except Exception as e:
            self.progress_bar.setValue(0)
            self.status_label.setText(tr("待機中..."))
            QtWidgets.QApplication.restoreOverrideCursor()
            QtWidgets.QMessageBox.critical(self, tr("エラー"), str(e))
            return
        finally:
            self.run_btn.setEnabled(True)
            while QtWidgets.QApplication.overrideCursor() is not None:
                QtWidgets.QApplication.restoreOverrideCursor()

        msg = tr(
            "収集が完了しました！ ({elapsed:.2f} 秒)\n\n出力先:\n{root}\n\nコピーした外部ファイル数: {asset_count} 件"
        ).format(elapsed=elapsed, root=collect_root, asset_count=asset_count)

        if missing:
            preview = "\n".join(missing[:5])
            extra = tr("\n...他 {count} 件").format(count=len(missing) - 5) if len(missing) > 5 else ""
            msg += tr("\n\n【注意】リンク切れのためスキップされたファイル ({count} 件):\n{preview}{extra}").format(
                count=len(missing), preview=preview, extra=extra
            )

        QtWidgets.QMessageBox.information(self, tr("Collect Files 完了"), msg)
        self.progress_bar.setValue(0)

        if self.chk_open_folder.isChecked():
            QtGui.QDesktopServices.openUrl(QtCore.QUrl.fromLocalFile(collect_root))


def show():
    parent = get_maya_main_window()
    if parent:
        existing = parent.findChild(QtWidgets.QDialog, WINDOW_OBJECT_NAME)
        if existing:
            existing.close()
            existing.deleteLater()

    dlg = CollectFilesDialog(parent=parent)
    dlg.show()
    return dlg


if __name__ == "__main__":
    show()