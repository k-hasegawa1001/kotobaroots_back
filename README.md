### kotobaroots_back

## 概要

このリポジトリは言語学習アプリ、KotobaRootsのバックエンドリポジトリである\
本システムではFlaskを使用しているが、APIを作成しており **フロントエンドとバックエンドの分離** をしているため、テストなどの際にローカルで動かす場合にはフロントエンドリポジトリ、kotobaroots_frontもクローンする必要がある

## 📑 目次

[0.使用言語](#0-使用言語)\
[1.リポジトリのクローン or フォーク](#1-リポジトリのクローン-or-フォーク)\
[2.ブランチの切り替え](#2-ブランチの切り替え)\
[3.仮想環境の作成について](#3-仮想環境の作成について)\
[4.必要なライブラリのインストール](#4-必要なライブラリのインストール)\
[5..envの取り扱いについて](#5-envの取り扱いについて)\
[6.DBの作成](#6-dbの作成)\
[7.DBにダミーデータを投入](#7-dbにダミーデータを投入)\
[8.各ディレクトリの概要](#8-各ディレクトリの概要)

## 0. 使用言語

本システムでは言語に **_Python: 3.8.12_** を使用している

もしPythonが入っていない場合は、\
https://www.python.org/downloads/ \
内の\
_Looking for a specific release?_ \
項目から\
Python: 3.8.12\
をダウンロードしてインストールを行ってもらいたい

## 1. リポジトリのクローン or フォーク

このリポジトリを置いておきたいディレクトリで

```bash
git clone https://github.com/k-hasegawa1001/kotobaroots_back.git`
```

コマンドを実行すること

また、無事にクローン出来たら

```bash
cd kotobaroots_back`
```

コマンドを実行してそのディレクトリに入るか、VSCodeのターミナルを使用している場合は左上の **ファイル** タブから **フォルダーを開く** を押して \_kotobaroots_back\* フォルダを開いてターミナルを起動しなおすこと（開きなおさなくても良いが、その場合は`cd`コマンドを実行すること）

**【重要】 チームメンバーではない人へ**\
もしこのシステムを、現在動いているものをベースにいじってみたい、という場合はクローンではなくフォークをお勧めする

このディレクトリ上部にある **Fork** ボタンをクリックすると **Create a new fork** という画面が表示されるので、そのまま **Create fork** をクリックする

これであなたのGitHubアカウント内に、そのリポジトリのコピーが作成されたはず\
今コピーしたのは「GitHub上のあなたのスペース」にあるだけなので、これを手元のPCで編集できるようにダウンロード（Clone）する

普通にクローンするときと同様に、緑色の **Code** ボタンからURLを取得してクローンする\
`例: git clone https://github.com/あなたのID/kotobaroots_back.git`

もしこのリポジトリにバグ修正や機能追加があった場合、その更新を取り込む方法について記述すると長くなるため、各自で調べて欲しい

## 2. ブランチの切り替え

クローンしたディレクトリに入ったら、下記コマンドを実行すること

```bash
git checkout dev
```

mainブランチは本番環境であるため、必ず切り替えること

**【重要】 クローンではなく、フォークをした人はコマンドが変わる**\
そういう人は下記コマンドを実行すること

```bash
git checkout -b dev
```

## 3. 仮想環境の作成について

本システムでは仮想環境（venv）を使用しているため、下記コマンドで仮想環境を作成する

```bash
python -m venv venv
```

これで **kotobaroots_back** ディレクトリ内に **venv** というフォルダが作成されていれば問題ない

## 4. 必要なライブラリのインストール

まずは下記コマンドで現在インストール済みのライブラリを確認してみよう

```bash
pip list
```

現段階では _pip_ というライブラリしか入っていないはず

クローンしたディレクトリ内に _requirements.txt_ というファイルがあるはずだ\
これには使用したライブラリが（Flaskも含めて）全てバージョンと共に記述されている\
これを仮想環境内にインストールする必要がある

下記コマンドを実行すること

```bash
pip install -r .\requirements.txt
```

何も警告が出らずに、`Successfully installed ...`のように表示されていればすべてのライブラリが正常にインストールされているはずだ\
再度`$ pip list`コマンドを叩いて問題なくすべてのライブラリがインストールされているか確認しよう

## 5. .envの取り扱いについて

もしこれを読んでいるのが同開発チームのメンバーであれば.envを共有してもらってほしい

この項目はそれ以外の人に向けたものである

ルートディレクトリに`.env`というファイルを新規作成し、以下テキストを張り付けること

```text
FLASK_APP=apps.app.py:create_app
FLASK_ENV=development

FRONTEND_URL="http://127.0.0.1:5500" # 本番環境では適切なURLに変更（開発時にフロントをLiveServerで動かす場合は5500番を開けておく必要あり）

### メールに添付するURLのトークン関連

SECRET_KEY={very-secret-random-key} # 本番環境では変更する

### DB関連

FLASK_SECRET_KEY={your_secret_key}

### flask_mail コンフィグ設定

MAIL_SERVER={your_mail_server}
MAIL_PORT={your_port}
MAIL_USE_TLS=True
MAIL_USERNAME={your_email}
MAIL_PASSWORD={your_mail_server_password}
MAIL_DEFAULT_SENDER="{your_sender_name}"

### 認証関連

JWT_REFRESH_COOKIE_NAME=refresh_token
JWT_COOKIE_HTTPONLY=True

###### 本番環境 (HTTPS) では True にする

JWT_COOKIE_SECURE=False # 開発中は False

JWT_COOKIE_SAMESITE=Lax
JWT_COOKIE_CSRF_PROTECT=False

###### 本番環境では絶対に推測されない文字列に変更する

JWT_SECRET_KEY={your-super-secret-key-change-this}

# アクセストークン（有効期限15分）

JWT_ACCESS_TOKEN_EXPIRES=datetime.timedelta(minutes=15)

# リフレッシュトークン（有効期限30日）

JWT_REFRESH_TOKEN_EXPIRES=datetime.timedelta(days=30)

### chatGPT-API

OPENAI_API_KEY={your_openai_api_key}
```

**【重要】 {}で囲まれている箇所を適宜変更すること**

## 6. DBの作成

下記コマンドを以下の順序で実行すること

````bash
flask db init
```\
```bash
flask db migrate
```\
```bash
flask db upgrade
````

これでルートディレクトリに`local.sqlite`というファイルが作成されていれば、問題なくDBが作成できている

## 7. DBにダミーデータを投入

ルートディレクトリに`seed.py`というファイルがあるはずなので確認してほしい\
これを実行するだけで、先ほど作成したDBに最低限必要なデータが一括で入る\
下記コマンドを実行して`✨ 全データの投入が完了しました！`と表示されれば、問題なくすべてのダミーデータが投入されている

**【注意】このコマンドはプロジェクトのルートディレクトリ（kotobaroots_backディレクトリ）で実行すること**

```bash
python seed.py
```

## 8. 各ディレクトリの概要

`apps/api/auth/auth_api.py`は **ログイン**、**ログアウト**、**新規登録**、**パスワードリセット** の四つを担っている\
**【注意】メールアドレス変更はauthではなく、kotobarootsで実装している**

`apps/api/kotobaroots/kotobaroots_api.py`は、上記以外のすべての機能を担っている\
具体的には、**学習**、**学習履歴**、**マイフレーズ**、**AI解説**、**プロフィール**、**問い合わせ** の6機能である

機能ごとにさらに細かく機能が分かれている（プロフィール内のユーザーネーム変更やメールアドレス変更のように）が、そのAPIが何をするものなのかはコメントに記述しているため、そちらを読んでもらいたい
