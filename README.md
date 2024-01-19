# glossary-llm-chat-bot

RAG [Retrieval-Augmented Generation] を使用して、LLM が学習に使用していない用語集（用語集スプレッドシートに定義）に対して応答できるようにした Slack チャットボットです。

<img width="300" alt="image" src="https://github.com/Yagami360/glossary-llm-chat-bot/assets/25688193/c552d750-331c-4299-a79e-7a938106f53c">

## 動作環境

- docker
- docker-compose

## アーキテクチャ

<img width="800" alt="image" src="https://github.com/Yagami360/glossary-llm-chat-bot/assets/25688193/708700d6-95e9-4413-b4b1-21c0945f3b65">

## 事前準備

### 用語集スプレッドシートの作成
例えば、以下のようなフォーマットの用語集スプレッドシートを作成してください<br>
<img width="500" alt="image" src="https://github.com/Yagami360/glossary-llm-chat-bot/assets/25688193/dda70126-2c52-4cc5-9787-28d9f5887c63">


> 用語集スプレッドシートにおいて、QA データとして使用するカラム名（上記例では、`用語,意味`）は、環境変数 `DATASET_TEXT_COLUMNS` で調整可能です

> 用語集スプレッドシートにおいて、メタデータとして使用するカラム名（上記例では、`メタデータ`）は、環境変数 `DATASET_META_COLUMNS` で調整可能です

### Slack アプリの初期設定

1. [Slack App](https://api.slack.com/apps) ページに移動する<br>

1. 「`Create an App`」ボタンをクリック -> 「`From scratch`」をクリックし、`glossary-llm-chat-bot` という名前の Slack App を作成する<br>
    <img width="500" alt="image" src="https://github.com/Yagami360/glossary-llm-chat-bot/assets/25688193/2dba027a-c4f6-4f80-bdc4-6207f8aec8c7"><br>
    <img width="500" alt="image" src="https://github.com/Yagami360/glossary-llm-chat-bot/assets/25688193/ad5bfbe7-ade1-4b4b-8e0e-a75b846b1b08"><br>

1. 左メニューの「`App Home`」をクリック -> `Show Tabs` セクションに移動し、`Allow users to send Slash commands and messages from the messages tab` を有効化する。<br>
    <img width="300" alt="image" src="https://github.com/Yagami360/glossary-llm-chat-bot/assets/25688193/fbd09dd4-1500-42f2-b8d4-7a6848e7c1e5">

1. 左メニューの「`OAuth & Permissions`」をクリックし、`Bot Token Scopes` の「Add an OAuth Scope」ボタンをクリックする<br>
    <img width="500" alt="image" src="https://github.com/Yagami360/glossary-llm-chat-bot/assets/25688193/2bb5bc3d-3251-4b42-90ca-802d709cd7aa"><br>
    <img width="500" alt="image" src="https://github.com/Yagami360/glossary-llm-chat-bot/assets/25688193/52af99ce-024f-44b2-a4d9-72d426b820f9"><br>

    Scopes には、`chat:write`, `commands` を追加する<br>
    <img width="500" alt="image" src="https://github.com/Yagami360/glossary-llm-chat-bot/assets/25688193/747df760-9850-415a-bc06-c2c3f075db2a"><br>

1. `OAuth Tokens for Your Workspace` セクションの `Install to Workspace` をクリックし、OAuth トークンを作成する<br>
    <img width="500" alt="image" src="https://github.com/Yagami360/glossary-llm-chat-bot/assets/25688193/8b4535ca-c8fd-4f39-a18e-aeaa9c07095d"><br>
    <img width="500" alt="image" src="https://github.com/Yagami360/glossary-llm-chat-bot/assets/25688193/129dd062-1bad-4204-b3bb-a93df1c52949"><br>

    クリック後、アクセストークンが作成されるので、`Bot User OAuth Token` から OAuth トークン値を確認する。<br>
    <img width="500" alt="image" src="https://github.com/Yagami360/glossary-llm-chat-bot/assets/25688193/d7b0f7a9-f663-451e-9955-a423bd2a2fb4"><br>

    > `Bot User OAuth Token` の値を後段のデプロイ処理にて、環境変数 `SLACK_BOT_TOKEN` に設定してください

1. 左メニュー「`Basic Information`」の `App Credentials`セクションに移動し、`Signing Secret` と `Verification Token` の値を確認する<br>
    <img width="500" alt="image" src="https://github.com/Yagami360/glossary-llm-chat-bot/assets/25688193/063bd55d-fa68-4d12-b44c-62169ead7079"><br>

    > - `Signing Secret` の値を後段のデプロイ処理にて、環境変数 `SLACK_SIGNING_SECRET` に設定してください

    > - `Verification Token` の値を後段のデプロイ処理にて、環境変数 `SLACK_VERIFY_TOKEN` に設定してください

### 各種 GCP リソースのデプロイ

1. 各種環境変数を設定する
    ```sh
    export PROJECT_ID='dummy'
    export REGION='dummy'
    export GOOGLE_APPLICATION_CREDENTIALS='/app/credentials/glossary-llm-chat-bot-sa.json'
    export SPREADSHEET_KEY='dummy'
    export SPREADSHEET_NAME='dummy'
    export OPENAI_API_KEY='dummy'
    export SLACK_BOT_TOKEN='dummy'
    export SLACK_SIGNING_SECRET='dummy'
    export SLACK_VERIFY_TOKEN='dummy'
    export DATASET_TEXT_COLUMNS='用語,意味'
    export DATASET_META_COLUMNS='メタデータ'
    ```
    - `PROJECT_ID`: GCP プロジェクトID
    - `REGION`: GCP リージョン
    - `SPREADSHEET_KEY`: 用語集スプレッドシートの URL（`https://docs.google.com/spreadsheets/d/hogehoge/edit#gid=0`）における `hogehoge` 部分の値
    - `SPREADSHEET_NAME`: スプレッドシートのシート名
    - `OPENAI_API_KEY`: OpenAPI の API キー
    - `SLACK_BOT_TOKEN`: Stack アプリ token。[Stack アプリページ](https://api.slack.com/apps)から `glossary-llm-chat-bot` という名前のアプリから確認可能
    - `SLACK_SIGNING_SECRET`: Stack アプリ token。[Stack アプリページ](https://api.slack.com/apps)から `glossary-llm-chat-bot` という名前のアプリから確認可能
    - `SLACK_VERIFY_TOKEN`: Stack アプリ token。[Stack アプリページ](https://api.slack.com/apps)から `glossary-llm-chat-bot` という名前のアプリから確認可能
    - `DATASET_TEXT_COLUMNS`: 用語集スプレッドシートにおいて、QA データとして使用するカラム名。例えば、`用語,意味` など
    - `DATASET_META_COLUMNS`: 用語集スプレッドシートにおいて、メタデータとして使用するカラム名。

1. 開発環境用 docker image をビルドする
    ```sh
    make docker-build-dev
    ```

1. GCP サービスアカウントを作成する
    ```sh
    make create-sa
    USER_NAME=$( whoami ) && sudo chown ${USER_NAME} credentials/glossary-llm-chat-bot-sa.json
    ```

1. 本番環境用 docker image をビルドする
    ```sh
    make docker-build-prod
    ```

1. docker image を Push する
    ```sh
    make docker-push
    ```

1. 用語集スプレッドシートの共有設定に、GCPサービスアカウント `glossary-llm-chat-bot-sa@${PROJECT_ID}.iam.gserviceaccount.com` を追加する<br>
    <img width="300" alt="image" src="https://github.com/Yagami360/glossary-llm-chat-bot/assets/25688193/34c8c570-ebb8-4a86-ac8a-d234452c7063">

1. 各種 GCP リリースにデプロイする
    ```sh
    make deploy
    ```

1. [Slack App](https://api.slack.com/apps) ページの左メニューの「`Slash Commands`」をクリックし、本アプリの Slack コマンドを作成する<br>
    <img width="500" alt="image" src="https://github.com/Yagami360/glossary-llm-chat-bot/assets/25688193/63acfc2b-ec67-457f-be9f-7d820eeb94dc"><br>
    <img width="500" alt="image" src="https://github.com/Yagami360/glossary-llm-chat-bot/assets/25688193/436bf170-3441-47c1-8b77-e890f95426cc"><br>
    <img width="500" alt="image" src="https://github.com/Yagami360/glossary-llm-chat-bot/assets/25688193/95936c8e-fdbd-46df-893b-215f77ff14b4"><br>
    - `Command`: `/glossary-chat-bot` を設定する
    - `Request URL`: `${API_URL}/slack/events`（例:`https://glossary-llm-chat-bot-sqwnhlznqa-an.a.run.app/slack/events`）<br>
        `API_URL` は Cloud Run の URL で、以下のコマンドで確認できます
        ```sh
        make get-api-url
        ```

## 使用方法

1. Slack の左下メニューの App から「アプリを追加する」ボタンをクリックし、`glossary-llm-chat-bot` という名前のアプリを検索し追加する。<br>
    <img width="500" alt="image" src="https://github.com/Yagami360/glossary-llm-chat-bot/assets/25688193/d9faaf73-5bb6-4fe5-b34f-a01b6290be30">

1. アプリ追加後、アプリ上の「メッセージ」タブに移動し、`/glossary-chat-bot ${質問文}` の形式でコマンド送信する<br>
    - コマンド例<br>
        <img width="300" alt="image" src="https://github.com/Yagami360/glossary-llm-chat-bot/assets/25688193/757f5e2f-b8df-44ec-a15f-68b6d7b316d4"><br>
    - 出力例<br>
        <img width="300" alt="image" src="https://github.com/Yagami360/glossary-llm-chat-bot/assets/25688193/1a3998f0-4c88-4eba-bd91-3338294506c9">


1. 用語を修正&追加したい場合は、用語集スプレッドシートを更新してください
