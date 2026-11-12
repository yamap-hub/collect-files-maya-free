# Collect Files for Maya (Free Edition)

> **An After Effects-style "Collect Files" utility for Autodesk Maya — gather your scene, references, and external assets into one clean, relative-pathed folder without altering your working scene.**

[日本語の案内はこちら](#collect-files-for-maya-free-edition-日本語)

---

### ✨ Features

* **Non-Destructive Workflow:** Never modifies paths or project settings in your active working scene. It duplicates your scene and updates links only in the collected copy.
* **Custom Destination & Folder Name:** Choose any output directory and folder name through a simple UI—no need to set up a Maya project beforehand.
* **Automatic Relative Paths & `workspace.mel`:** Automatically organizes files into `scenes/` and `sourceimages/` subfolders and generates a `workspace.mel` file so your package opens without broken links on any PC or drive.
* **Comprehensive Asset & Reference Collection:** Collects textures (including `<UDIM>`, `<uvtile>`, and `<f>` sequences), caches, audio, and reference scenes (`.ma` / `.mb`).
* **Smart Duplicate Handling & Missing File Report:** Automatically renames duplicate filenames from different source folders to prevent overwriting, and reports any missing/broken links upon completion.
* **Bilingual UI (English / 日本語):** Switch languages anytime directly inside the tool window.
* **Zero External Dependencies:** Built purely on Maya's native Python and Qt (`PySide2` / `PySide6`).

---

### 📦 Package Contents (`collect_files_maya_free.zip`)

* `install_CFM.mel` — Drag-and-drop shelf installer
* `collect_files_maya_free.py` — Main tool script
* `README.md` — This documentation

---

### 💻 Compatibility

* **Autodesk Maya:** 2022, 2023, 2024, 2025, 2026, and 2027 (Python 3)
* **OS:** Windows / macOS
* **Dependencies:** None

---

### 🚀 Installation

#### Method 1: Drag-and-Drop Installer (Recommended)
1. **Extract `collect_files_maya_free.zip` completely** (do not drag files directly from inside an unextracted ZIP window).
2. Ensure `install_CFM.mel` and `collect_files_maya_free.py` are in the same folder.
3. Open Maya and select the shelf tab where you want to add the button.
4. **Drag and drop `install_CFM.mel` into the Maya viewport.**
5. `collect_files_maya_free.py` will be copied to your user `scripts` folder, and a **`CFM`** button will be added to your current shelf.

*(To update the tool later, simply replace the files and drag-and-drop `install_CFM.mel` into the viewport again.)*

#### Method 2: Manual Installation
1. Copy `collect_files_maya_free.py` into your Maya `scripts` directory:
   * **Windows:** `C:\Users\<Username>\Documents\maya\scripts`
   * **macOS:** `/Users/<Username>/Library/Preferences/Autodesk/maya/scripts`
2. Open the **Script Editor** in Maya (Python tab) and run:
   ```python
   import collect_files_maya_free
   collect_files_maya_free.show()
   ```
   *(Optional: Select the code and middle-mouse drag it onto your shelf to create a button.)*

---

### 🛠️ How to Use

1. Open the Maya scene you want to package.
2. Click the **`CFM`** button on your shelf to open the **Collect Files** window.
3. Set the **Destination Folder** and **New Folder Name**.
4. Configure your collection options (external assets, references, subfolders, `workspace.mel` generation, auto-open folder).
5. Click **Collect Files**. Once finished, a summary dialog will display the output path, number of copied files, and any skipped missing files.

---

### 📄 License & Disclaimer

* **License:** Free for both personal and commercial 3D production workflows.
* **Restrictions:** Redistribution, re-uploading, or resale of this script package is prohibited. Please share the official GitHub repository link instead.
* **Disclaimer:** While designed to be completely non-destructive, please always keep backups of your important scene files. The author is not responsible for any data loss resulting from the use of this tool.

---
---

## Collect Files for Maya (Free Edition) 日本語

> **After Effectsの「ファイルの収集」と同じ感覚で使える、Autodesk Maya用の非破壊ファイル収集ツールです。**

### ✨ 主な特徴

* **元シーン完全非破壊:** 作業中シーンのテクスチャパスやプロジェクト設定は一切書き換えません。複製先のシーンファイル内のリンクのみを相対パス化して保存します。
* **保存先とフォルダ名をUIで指定:** 事前に「プロジェクト ウィンドウ」を設定していなくても、保存先の親フォルダと新規フォルダ名を指定して一括収集できます。
* **`workspace.mel` 自動生成＆相対パス化:** `scenes` / `sourceimages` フォルダへの自動整理と `workspace.mel` の生成により、別のPCやドライブへフォルダごと渡してもリンク切れを起こしません。
* **UDIM・連番・リファレンス対応:** テクスチャ（`<UDIM>` / `<uvtile>` / `<f>` タイル含む）、キャッシュ、オーディオ、およびリファレンスシーン（`.ma` / `.mb`）を自動収集します。
* **同名ファイルの自動リネーム＆リンク切れ通知:** 別フォルダにある同名ファイル（例：`A/color.png` と `B/color.png`）は自動で連番リネームして上書きを防ぎ、リンク切れファイルがある場合は完了時に一覧でお知らせします。
* **日本語 / English リアルタイム切り替え:** ウィンドウ右上のボタンからいつでも表示言語を切り替えられます（設定は自動保存されます）。
* **外部ライブラリ不要:** Maya標準のPython / Qtのみで動作します。

---

### 📦 同梱ファイル (`collect_files_maya_free.zip`)

* `install_CFM.mel` — ドラッグ＆ドロップ用インストーラー
* `collect_files_maya_free.py` — ツール本体スクリプト
* `README.md` — 本ドキュメント

---

### 💻 対応環境

* **Autodesk Maya:** 2022, 2023, 2024, 2025, 2026, 2027（Python 3対応）
* **OS:** Windows / macOS
* **追加ライブラリ:** 不要

---

### 🚀 インストール方法

#### 方法1：ドラッグ＆ドロップで簡単インストール（推奨）
1. **ダウンロードした `collect_files_maya_free.zip` を必ずすべて解凍**します（※ZIPを開いたまま中のファイルを直接ドラッグしないでください）。
2. `install_CFM.mel` と `collect_files_maya_free.py` が同じフォルダ内にあることを確認します。
3. Mayaを起動し、ボタンを追加したいシェルフタブを開きます。
4. **`install_CFM.mel` をMayaのビューポートへドラッグ＆ドロップ**します。
5. 自動的にユーザーの `scripts` フォルダへスクリプトがコピーされ、現在のシェルフに **`CFM`** ボタンが登録されます。

*(※ バージョンアップ時も、新しいファイルで再度 `install_CFM.mel` をドラッグ＆ドロップするだけで上書き更新できます)*

#### 方法2：手動インストール
1. `collect_files_maya_free.py` を以下のMayaスクリプトフォルダへコピーします。
   * **Windows:** `C:\Users\<ユーザー名>\Documents\maya\scripts`
   * **macOS:** `/Users/<ユーザー名>/Library/Preferences/Autodesk/maya/scripts`
2. Mayaのスクリプト エディタ（Pythonタブ）で以下を実行します。
   ```python
   import collect_files_maya_free
   collect_files_maya_free.show()
   ```
   *(※ 常用する場合はコードを全選択し、マウス中ボタンでシェルフへドラッグ＆ドロップするとボタンを作成できます)*

---

### 🛠️ 使い方

1. 収集したいMayaシーンを開きます。
2. シェルフの **`CFM`** ボタンをクリックしてウィンドウを開きます。
3. **保存先フォルダ** と **新規フォルダ名** を指定します。
4. 必要に応じて収集オプション（外部ファイル・リファレンス・サブフォルダ整理・`workspace.mel` 生成・完了後にフォルダを開く）を設定します。
5. **「収集を実行 (Collect Files)」** をクリックすると収集が実行され、コピー件数やリンク切れの有無がダイアログで表示されます。

---

### 📄 ライセンス・免責事項

* **利用許諾:** 個人・商用問わず、日々の3D制作や業務において無料で自由にご利用いただけます。
* **禁止事項:** 本ツールおよび同梱ファイルの再配布、転載、再販売は禁止します。共有される際はGitHubリポジトリのURLをご案内ください。
* **免責事項:** 作業中の元シーンを変更しない非破壊設計となっておりますが、念のため大切なデータのバックアップを取った上でご使用ください。本ツールの使用により生じた損害について作者は一切の責任を負いません。