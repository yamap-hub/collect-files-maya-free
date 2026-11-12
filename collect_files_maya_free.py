# -*- coding: utf-8 -*-
"""
Collect Files for Maya (After Effects style)
Maya 2022 - 2027 (PySide2 / PySide6 compatible, Zero external dependencies)
Bilingual UI (Japanese / English)
"""

import os
import re
import glob
import shutil
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
OPTION_VAR_LANG = "CFM_ui_language"

# ---------------------------------------------------------------------------
# 多言語対応 (日本語 / English)
# ---------------------------------------------------------------------------
_EN = {
    "Collect Files (ファイル収集)": "Collect Files",
    "1. 保存先とフォルダ名": "1. Destination & Folder Name",
    "保存先の親フォルダを選択...": "Select destination parent folder...",
    "参照...": "Browse...",
    "保存先フォルダ:": "Destination Folder:",
    "新規フォルダ名:": "New Folder Name:",
    "2. 収集オプション": "2. Collection Options",
    "テクスチャ・キャッシュ等の外部ファイルを収集する": "Collect external assets (textures, caches, audio, etc.)",
    "リファレンスシーン (.ma / .mb) を収集する": "Collect reference scenes (.ma / .mb)",
    "サブフォルダに分けて整理する (scenes / sourceimages)": "Organize into subfolders (scenes / sourceimages)",
    "workspace.mel を自動生成して相対パス化する（推奨）": "Auto-generate workspace.mel for relative paths (Recommended)",
    "収集完了後にフォルダを開く": "Open folder after collection",
    "収集を実行 (Collect Files)": "Collect Files",
    "閉じる": "Close",
    "保存先フォルダを選択": "Select Destination Folder",
    "エラー": "Error",
    "Collect Files 完了": "Collect Files Complete",
    "有効な保存先フォルダを指定してください。": "Please specify a valid destination folder.",
    "収集フォルダ名を入力してください。": "Please enter a folder name.",
    "既に空でない同名フォルダが存在します:\n{path}": "A non-empty folder with the same name already exists:\n{path}",
    "収集が完了しました！\n\n出力先:\n{root}\n\nコピーした外部ファイル数: {count} 件": (
        "Collection complete!\n\nOutput folder:\n{root}\n\nExternal files copied: {count}"
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
        annotation="Collect Files for Maya free (シーンと外部ファイルを一括収集 / Collect scene and external assets)",
        image1="pythonFamily.png",
        command="import collect_files_maya_free\ncollect_files_maya_free.show()",
        sourceType="python",
    )

    try:
        cmds.saveAllShelves(shelf_top)
    except Exception:
        pass


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


def expand_wildcard_files(filepath):
    """UDIM (<UDIM>, <uvtile>) や連番テクスチャに該当する実ファイルをすべて取得する"""
    if not filepath:
        return []

    norm_path = filepath.replace("\\", "/")
    if "<UDIM>" in norm_path or "<uvtile>" in norm_path or "<f>" in norm_path:
        pattern = (
            norm_path.replace("<UDIM>", "*")
            .replace("<uvtile>", "*")
            .replace("<f>", "*")
        )
        matched = glob.glob(pattern)
        return [p.replace("\\", "/") for p in matched if os.path.isfile(p)]

    if os.path.isfile(norm_path):
        return [norm_path]

    return []


def collect_scene_files(
    parent_dir,
    folder_name,
    collect_assets=True,
    collect_references=True,
    create_workspace=True,
    use_subfolders=True,
):
    """
    現在のシーンを非破壊で新しいフォルダへ収集し、パスを書き換えて保存する。
    """
    if not parent_dir or not os.path.isdir(parent_dir):
        raise RuntimeError(tr("有効な保存先フォルダを指定してください。"))

    safe_folder = re.sub(r'[<>:"/\\|?*]', "_", folder_name.strip())
    if not safe_folder:
        raise RuntimeError(tr("収集フォルダ名を入力してください。"))

    collect_root = os.path.join(parent_dir, safe_folder).replace("\\", "/")
    if os.path.exists(collect_root) and os.listdir(collect_root):
        raise RuntimeError(tr("既に空でない同名フォルダが存在します:\n{path}").format(path=collect_root))

    os.makedirs(collect_root, exist_ok=True)

    scenes_dir = os.path.join(collect_root, "scenes").replace("\\", "/") if use_subfolders else collect_root
    assets_dir = os.path.join(collect_root, "sourceimages").replace("\\", "/") if use_subfolders else collect_root
    os.makedirs(scenes_dir, exist_ok=True)
    os.makedirs(assets_dir, exist_ok=True)

    # 元の作業状態を記録（非破壊で元に戻すため）
    orig_scene_path = cmds.file(q=True, sn=True)
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

    # 復元用バックアップ
    attr_backups = []       # (node_attr, orig_val)
    ref_backups = []        # (ref_node, orig_ref_path)
    copied_files_map = {}   # src_path -> dst_path
    used_dest_names = set()
    copied_count = 0
    missing_files = []

    def get_unique_dest_path(target_dir, src_path):
        base_name = os.path.basename(src_path)
        stem, ext = os.path.splitext(base_name)
        candidate = base_name
        counter = 1
        while candidate.lower() in used_dest_names:
            candidate = f"{stem}_{counter}{ext}"
            counter += 1
        used_dest_names.add(candidate.lower())
        return os.path.join(target_dir, candidate).replace("\\", "/")

    try:
        if create_workspace:
            write_minimal_workspace_mel(collect_root)
            cmds.workspace(collect_root, openWorkspace=True)

        # 1. リファレンスファイルの収集と一時差し替え
        if collect_references:
            ref_files = cmds.file(q=True, r=True) or []
            for ref_path in ref_files:
                clean_ref = ref_path.split("{")[0]
                ref_node = cmds.referenceQuery(ref_path, referenceNode=True)
                if not os.path.isfile(clean_ref):
                    missing_files.append(clean_ref)
                    continue

                if clean_ref not in copied_files_map:
                    dst_ref = get_unique_dest_path(scenes_dir, clean_ref)
                    shutil.copy2(clean_ref, dst_ref)
                    copied_files_map[clean_ref] = dst_ref
                    copied_count += 1
                else:
                    dst_ref = copied_files_map[clean_ref]

                ref_backups.append((ref_node, clean_ref))
                cmds.file(dst_ref, loadReference=ref_node)

        # 2. テクスチャ・キャッシュ・オーディオ等の外部アセット収集
        if collect_assets:
            dirs = cmds.filePathEditor(query=True, listDirectories="") or []
            for d in dirs:
                pairs = cmds.filePathEditor(query=True, listFiles=d, withAttribute=True) or []
                for i in range(0, len(pairs), 2):
                    file_name = pairs[i]
                    node_attr = pairs[i + 1]
                    node_name = node_attr.split(".")[0]

                    # リファレンスノードは上の処理で対応済みなのでスキップ
                    if cmds.objExists(node_name) and cmds.nodeType(node_name) == "reference":
                        continue

                    try:
                        raw_attr_val = cmds.getAttr(node_attr)
                    except Exception:
                        continue

                    src_full = os.path.join(d, file_name).replace("\\", "/")
                    matched_files = expand_wildcard_files(src_full)

                    if not matched_files:
                        missing_files.append(src_full)
                        continue

                    # UDIM / ワイルドカードの場合は複数ファイルをコピーし、パスは元のファイル名パターンを維持
                    if "<UDIM>" in src_full or "<uvtile>" in src_full or "<f>" in src_full:
                        for mf in matched_files:
                            if mf not in copied_files_map:
                                dst_mf = os.path.join(assets_dir, os.path.basename(mf)).replace("\\", "/")
                                shutil.copy2(mf, dst_mf)
                                copied_files_map[mf] = dst_mf
                                copied_count += 1
                        new_attr_path = (
                            f"sourceimages/{os.path.basename(src_full)}"
                            if (use_subfolders and create_workspace)
                            else os.path.join(assets_dir, os.path.basename(src_full)).replace("\\", "/")
                        )
                    else:
                        single_src = matched_files[0]
                        if single_src not in copied_files_map:
                            dst_single = get_unique_dest_path(assets_dir, single_src)
                            shutil.copy2(single_src, dst_single)
                            copied_files_map[single_src] = dst_single
                            copied_count += 1
                        else:
                            dst_single = copied_files_map[single_src]

                        new_attr_path = (
                            f"sourceimages/{os.path.basename(dst_single)}"
                            if (use_subfolders and create_workspace)
                            else dst_single
                        )

                    attr_backups.append((node_attr, raw_attr_val))
                    cmds.setAttr(node_attr, new_attr_path, type="string")

        # 3. 収集先フォルダへシーンを保存
        cmds.file(rename=dest_scene_path)
        cmds.file(save=True, type=orig_file_type)

    finally:
        # 4. 作業中シーンのパス・アトリビュート・プロジェクト設定を完全に元の状態へ復元
        for node_attr, orig_val in reversed(attr_backups):
            try:
                cmds.setAttr(node_attr, orig_val, type="string")
            except Exception:
                pass

        for ref_node, orig_ref in reversed(ref_backups):
            try:
                cmds.file(orig_ref, loadReference=ref_node)
            except Exception:
                pass

        if orig_workspace and os.path.isdir(orig_workspace):
            try:
                cmds.workspace(orig_workspace, openWorkspace=True)
            except Exception:
                pass

        if orig_scene_path:
            cmds.file(rename=orig_scene_path)
        else:
            cmds.file(rename="untitled")
        cmds.file(modified=was_modified)

    return collect_root, copied_count, missing_files


class CollectFilesDialog(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName(WINDOW_OBJECT_NAME)
        self.setMinimumWidth(470)
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

        self.chk_refs = QtWidgets.QCheckBox()
        self.chk_refs.setChecked(True)

        self.chk_subfolders = QtWidgets.QCheckBox()
        self.chk_subfolders.setChecked(True)

        self.chk_workspace = QtWidgets.QCheckBox()
        self.chk_workspace.setChecked(True)

        self.chk_open_folder = QtWidgets.QCheckBox()
        self.chk_open_folder.setChecked(True)

        opt_layout.addWidget(self.chk_assets)
        opt_layout.addWidget(self.chk_refs)
        opt_layout.addWidget(self.chk_subfolders)
        opt_layout.addWidget(self.chk_workspace)
        opt_layout.addWidget(self.chk_open_folder)
        layout.addWidget(self.opt_group)

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
        self.setWindowTitle(tr("Collect Files (ファイル収集)"))
        self.dir_group.setTitle(tr("1. 保存先とフォルダ名"))
        self.dir_edit.setPlaceholderText(tr("保存先の親フォルダを選択..."))
        self.browse_btn.setText(tr("参照..."))
        self.lbl_dest_dir.setText(tr("保存先フォルダ:"))
        self.lbl_folder_name.setText(tr("新規フォルダ名:"))

        self.opt_group.setTitle(tr("2. 収集オプション"))
        self.chk_assets.setText(tr("テクスチャ・キャッシュ等の外部ファイルを収集する"))
        self.chk_refs.setText(tr("リファレンスシーン (.ma / .mb) を収集する"))
        self.chk_subfolders.setText(tr("サブフォルダに分けて整理する (scenes / sourceimages)"))
        self.chk_workspace.setText(tr("workspace.mel を自動生成して相対パス化する（推奨）"))
        self.chk_open_folder.setText(tr("収集完了後にフォルダを開く"))

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

    def _on_collect(self):
        try:
            collect_root, count, missing = collect_scene_files(
                parent_dir=self.dir_edit.text(),
                folder_name=self.folder_name_edit.text(),
                collect_assets=self.chk_assets.isChecked(),
                collect_references=self.chk_refs.isChecked(),
                create_workspace=self.chk_workspace.isChecked(),
                use_subfolders=self.chk_subfolders.isChecked(),
            )
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, tr("エラー"), str(e))
            return

        msg = tr("収集が完了しました！\n\n出力先:\n{root}\n\nコピーした外部ファイル数: {count} 件").format(
            root=collect_root, count=count
        )
        if missing:
            preview = "\n".join(missing[:5])
            extra = tr("\n...他 {count} 件").format(count=len(missing) - 5) if len(missing) > 5 else ""
            msg += tr("\n\n【注意】リンク切れのためスキップされたファイル ({count} 件):\n{preview}{extra}").format(
                count=len(missing), preview=preview, extra=extra
            )

        QtWidgets.QMessageBox.information(self, tr("Collect Files 完了"), msg)

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