@echo off
cd /d %~dp0

:: --- 設定エリア ---
:: 仮想環境のパス (環境に合わせて書き換えてください。例: .venv, venv, env 等)
set VENV_DIR=.venv

:: Flaskアプリの定義 (appsフォルダ内の app.py に create_app がある場合)
set FLASK_APP=apps.app:create_app
:: ------------------

:: 仮想環境のアクティベート
if exist %VENV_DIR%\Scripts\activate (
    call %VENV_DIR%\Scripts\activate
) else (
    echo [WARNING] Virtual environment not found at %VENV_DIR%. Running with global python...
)

:: コマンド実行
echo Running cleanup-history command...
flask cleanup-history

:: 結果を確認したい場合は pause を残す（自動実行なら削除OK）
:: pause