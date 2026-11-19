
---
# Collect Files for Maya (CFM) — Free Edition

An After Effects-style **Collect Files** tool for Autodesk Maya.  
Gather your scene and its textures/external assets into a clean, portable project folder (`scenes/` and `sourceimages/`) and auto-generate `workspace.mel` so everything opens with relative paths on any PC.

* **Supported Maya Versions:** Autodesk Maya 2022 – 2027 (Windows / macOS / Linux)
* **Dependencies:** None (Pure Python 3 + PySide2 / PySide6)
* **UI Languages:** English / Japanese (Switchable inside the tool window)

---

## Key Features (Free Edition)

* **Ultra-Fast In-Process Execution:** Rewrites and saves scenes directly in-process without launching external `mayapy` subprocesses—completing typical single scenes in a fraction of a second with minimal CPU load.
* **100% Non-Destructive:** Keeps your active working scene, file paths, current workspace, and unsaved status (`*`) completely untouched.
* **Portable Relative Paths (`workspace.mel`):** Organizes files into `scenes/` and `sourceimages/` and automatically generates `workspace.mel` for hassle-free sharing across drives and machines.
* **Missing Link Detection:** Safely skips broken/missing file paths and lists them in the completion summary.
* **Bilingual UI & Easy Setup:** Switch between **English** and **Japanese** anytime, and install to your shelf via drag-and-drop.

> **Scope Note:** The Free edition is designed as a lightweight baseline for standard single-scene collection. If you work with nested `.ma`/`.mb` references, UDIMs, frame sequences, or need collection reports and 1-click `.zip` packaging, check out **Collect Files for Maya Pro (CFMP)** below.

---

## Free vs. Pro Comparison

| Feature | CFM (Free) | CFMP (Pro) |
| :--- | :---: | :---: |
| Single-scene texture & external asset collection | ✅ | ✅ |
| Subfolder organization (`scenes/` & `sourceimages/`) | ✅ | ✅ |
| Auto-generated `workspace.mel` & relative paths | ✅ | ✅ |
| 100% non-destructive & ultra-fast in-process engine | ✅ | ✅ |
| Bilingual UI (English / Japanese) + shelf installer | ✅ | ✅ |
| **Recursive nested reference collection (`.ma` / `.mb`, child & grandchild)** | — | ✅ |
| **Internal path relinking inside nested `.ma` & `.mb` references** | — | ✅ |
| **UDIM auto-expansion (`<UDIM>`, `<uvtile>`, `uvTilingMode`)** | — | ✅ |
| **Frame sequence auto-expansion (`####`, `<f>`, `useFrameExtension`)** | — | ✅ |
| **Collection audit report (`collection_report.txt`)** | — | ✅ |
| **1-click `.zip` delivery archive packaging** | — | ✅ |

### Get Collect Files for Maya Pro (CFMP)
* **Gumroad (Global / English):** https://mashitaya.gumroad.com/l/jwqvrf/6k511u9
* **BOOTH (Japan / 日本語):** https://yworks.booth.pm/items/9172929

---

## Repository Contents

* `collect_files_maya.py` — Main tool script (Free Edition)
* `install_CFM.mel` — Drag-and-drop shelf installer
* `README.md` — Documentation

---

## Installation

1. Download or clone this repository and extract the files into any folder. Make sure `install_CFM.mel` and `collect_files_maya.py` are in the **same folder**.
2. Open Autodesk Maya (2022 or later) and **drag and drop `install_CFM.mel` directly into the Maya viewport**.
3. `collect_files_maya.py` will be copied to your Maya `scripts` directory, and a **`CFM`** button will be added to your currently active shelf. *(If an older `CFM` button already exists on that shelf, it is automatically replaced.)*

> **Alternative Method (if drag-and-drop is blocked by OS permissions):**  
> Open the **Script Editor** (MEL tab) in Maya and run:  
> `source "C:/path/to/install_CFM.mel";`

---

## How to Use

1. Click the **`CFM`** button on your shelf to open the **Collect Files** dialog.
2. *(Optional)* Use the **`日本語` / `English`** toggle at the top right to switch the UI language.
3. Choose the **Destination Folder** and **New Folder Name** (defaults to `<SceneName>_Collected`).
4. Select your options (collect external assets, organize into `scenes` / `sourceimages`, auto-generate `workspace.mel`, open folder after collection) and click **Collect Files**.

To verify the collected package on your own machine, go to **File > Set Project...** in Maya, select the newly created output folder, and open the scene inside `scenes/`.

---

## License

MIT License — Free to use for both personal and commercial projects.

---
---

# Collect Files for Maya (CFM) — 日本語ガイド

Autodesk Maya 向けの After Effects 風 **「ファイル収集（Collect Files）」** ツール（無料版）です。  
現在のシーンと使用しているテクスチャ等の外部アセットを1つのプロジェクトフォルダ（`scenes/`・`sourceimages/`）へ一括収集し、`workspace.mel` を自動生成して相対パス化することで、別のPCやドライブへ渡してもリンク切れなく開ける状態にまとめます。

* **対応バージョン:** Autodesk Maya 2022 – 2027（Windows / macOS / Linux）
* **外部ライブラリ:** 不要（Maya 標準の Python 3 / PySide2・PySide6 のみで動作）
* **UI言語:** 日本語 / English（ウィンドウ右上からいつでも切り替え可能）

---

## 主な機能（Free版）

* **超高速インプロセス処理:** 外部プロセス（`mayapy`）を起動せず現在の Maya セッション内で高速に収集・リリンクを行うため、一般的な単一シーンであれば一瞬（0.1秒未満〜）で完了します。
* **100% 非破壊:** 作業中のシーンファイル、元のアセットパス、現在のプロジェクト（Workspace）設定、未保存状態（`*`）を一切変更しません。
* **相対パス化（`workspace.mel` 自動生成）:** `scenes/` と `sourceimages/` に整理したうえで `workspace.mel` を自動生成します。
* **リンク切れの自動スキップ通知:** 見つからないファイルは安全にスキップし、完了ダイアログに一覧を表示します。
* **日英バイリンガルUI ＆ 簡単導入:** `install_CFM.mel` をビューポートへドラッグ＆ドロップするだけでシェルフに **`CFM`** ボタンが登録されます。

> **無料版の対応範囲について:**  
> Free版は日常的な単一シーンを手軽にまとめる用途に特化した軽量版です。子・孫階層までのネストされたリファレンス（`.ma` / `.mb`）の再帰収集、UDIM・フレーム連番の自動展開、収集レポート出力、ワンクリック `.zip` 圧縮が必要な場合は、上位版の **Collect Files for Maya Pro (CFMP)** をご利用ください。

---

## Free版 と Pro版 の機能比較

| 機能 | CFM (Free版) | CFMP (Pro版) |
| :--- | :---: | :---: |
| 単一シーンのテクスチャ・外部アセット収集 | ✅ | ✅ |
| サブフォルダ整理（`scenes/`・`sourceimages/`） | ✅ | ✅ |
| `workspace.mel` 自動生成・相対パス化 | ✅ | ✅ |
| 100% 非破壊・超高速インプロセス処理 | ✅ | ✅ |
| 日英バイリンガルUI・ドラッグ＆ドロップ導入 | ✅ | ✅ |
| **ネストされたリファレンスの再帰収集（`.ma` / `.mb` 子・孫階層対応）** | — | ✅ |
| **ネストされた `.ma` / `.mb` リファレンス内部パスの自動リリンク** | — | ✅ |
| **UDIM 自動展開・収集（`<UDIM>` / `<uvtile>` / `uvTilingMode`）** | — | ✅ |
| **フレーム連番の自動展開・収集（`####` / `<f>` / `useFrameExtension`）** | — | ✅ |
| **収集レポート出力（`collection_report.txt`）** | — | ✅ |
| **納品用 `.zip` アーカイブ自動作成** | — | ✅ |

### Pro版（CFMP）の入手先
* **BOOTH（日本語 / 国内向け）:** https://yworks.booth.pm/items/9172929
* **Gumroad（英語 / 海外向け）:** https://mashitaya.gumroad.com/l/jwqvrf/6k511u9

---

## インストール方法

1. リポジトリをダウンロード（または ZIP 展開）し、`install_CFM.mel` と `collect_files_maya.py` が**同じフォルダ内**にあることを確認します。
2. Maya（2022以降）を起動し、**`install_CFM.mel` をビューポートへドラッグ＆ドロップ**します。
3. 自動的に Maya の `scripts` フォルダへスクリプトがコピーされ、現在選択中のシェルフに **`CFM`** ボタンが登録されます（既存の `CFM` ボタンがある場合は自動で上書き更新されます）。

> **ドラッグ＆ドロップで反応しない場合:**  
> Maya のスクリプトエディタ（MELタブ）で以下を実行してください。  
> `source "C:/path/to/install_CFM.mel";`

---

## 使い方

1. シェルフの **`CFM`** ボタンをクリックしてウィンドウを開きます。
2. 保存先フォルダと新規フォルダ名（初期値：`<シーン名>_Collected`）を指定します。
3. 必要なオプションにチェックを入れ、**「収集を実行 (Collect Files)」** をクリックします。

※収集結果を手元で確認する場合は、Maya の **ファイル > プロジェクトの設定 (File > Set Project...)** から出力されたフォルダを指定し、`scenes/` 内のシーンを開いてご確認ください。
