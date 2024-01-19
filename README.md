# glossary-llm-chat-bot

RAG [Retrieval-Augmented Generation] を使用して、LLM が学習に使用していない用語集（用語集スプレッドシートに定義）に対して応答できるようにした Slack チャットボットです。

<img width="300" alt="image" src="https://github.com/Yagami360/glossary-llm-chat-bot/assets/25688193/70bec528-3ba6-45ce-8605-8e8df68e1de6">

## 動作環境

- docker
- docker-compose

## アーキテクチャ

<img width="800" alt="image" src="https://github.com/Yagami360/glossary-llm-chat-bot/assets/25688193/708700d6-95e9-4413-b4b1-21c0945f3b65">

## 事前準備

### 用語集スプレッドシートの作成
例えば、以下のようなフォーマットの用語集スプレッドシートを作成してください<br>
<img width="500" alt="image" src="https://github.com/Yagami360/glossary-llm-chat-bot/assets/25688193/584cde29-0dc1-4147-bece-a5d4e2b9e48a">

> 用語集スプレッドシートにおいて、QA データとして使用するカラム名（上記例では、`用語,意味`）は、環境変数 `DATASET_TEXT_COLUMNS` で調整可能です

> 用語集スプレッドシートにおいて、メタデータとして使用するカラム名（上記例では、`メタデータ`）は、環境変数 `DATASET_META_COLUMNS` で調整可能です

### Slack アプリの初期設定

1. [Slack App](https://api.slack.com/apps) ページに移動する<br>

1. 「`Create an App`」ボタンをクリック -> 「`From scratch`」をクリックし、`glossary-llm-chat-bot` という名前の Slack App を作成する<br>
    <img width="500" alt="image" src="https://github.com/Yagami360/glossary-llm-chat-bot/assets/25688193/50d60c31-0d5f-4895-9b8c-c15cc84cbd08"><br>
    <img width="500" alt="image" src="https://github.com/Yagami360/glossary-llm-chat-bot/assets/25688193/e93592d3-5fcf-4bc7-a15d-4882d53c1042"><br>

1. 左メニューの「`App Home`」をクリック -> `Show Tabs` セクションに移動し、`Allow users to send Slash commands and messages from the messages tab` を有効化する。<br>
    <img width="500" alt="image" src="https://github.com/Yagami360/glossary-llm-chat-bot/assets/25688193/55243eba-248e-44c1-bcb2-bd9b1f3ba237"><br>

1. 左メニューの「`OAuth & Permissions`」をクリックし、`Bot Token Scopes` の「Add an OAuth Scope」ボタンをクリックする<br>
    <img width="500" alt="image" src="https://github.com/Yagami360/glossary-llm-chat-bot/assets/25688193/97bba61c-6d07-49b9-b69e-eb7d770d743b"><br>
    <img width="500" alt="image" src="https://github.com/Yagami360/glossary-llm-chat-bot/assets/25688193/e03d4577-0f01-489f-826c-ca64b2f14ddd"><br>

    Scopes には、`chat:write`, `commands` を追加する<br>
    <img width="500" alt="image" src="https://github.com/Yagami360/glossary-llm-chat-bot/assets/25688193/1e1c3041-c089-491a-bf98-6d2dde787e53"><br>

1. `OAuth Tokens for Your Workspace` セクションの `Install to Workspace` をクリックし、OAuth トークンを作成する<br>
    <img width="500" alt="image" src="https://github.com/Yagami360/glossary-llm-chat-bot/assets/25688193/b3e65578-55f1-4a7b-88c2-97fbb83e458e"><br>
    <img width="500" alt="image" src="https://github.com/Yagami360/glossary-llm-chat-bot/assets/25688193/b0c9e00f-2fee-484f-8465-8d4587316996"><br>

    クリック後、アクセストークンが作成されるので、`Bot User OAuth Token` から OAuth トークン値を確認する。<br>
    <img width="500" alt="image" src="https://github.com/Yagami360/glossary-llm-chat-bot/assets/25688193/5d677c6d-3dde-4c84-8eea-ffea4ad6dc7b"><br>

    > `Bot User OAuth Token` の値を後段のデプロイ処理にて、環境変数 `SLACK_BOT_TOKEN` に設定してください

1. 左メニュー「`Basic Information`」の `App Credentials`セクションに移動し、`Signing Secret` と `Verification Token` の値を確認する<br>
    <img width="500" alt="image" src="https://github.com/Yagami360/glossary-llm-chat-bot/assets/25688193/1ce28b0b-645c-43d7-9d58-336624867444"><br>

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
    <img width="300" alt="image" src="https://github.com/Yagami360/glossary-llm-chat-bot/assets/25688193/cfc43dd6-7c81-4ebd-95f8-e47cc2f60fd9">

1. 各種 GCP リリースにデプロイする
    ```sh
    make deploy
    ```

1. [Slack App](https://api.slack.com/apps) ページの左メニューの「`Slash Commands`」をクリックし、本アプリの Slack コマンドを作成する<br>
    <img width="800" alt="image" src="https://github.com/Yagami360/glossary-llm-chat-bot/assets/25688193/4037e746-1ea1-4393-82d4-22a28a6dfc08"><br>
    <img width="800" alt="image" src="https://github.com/Yagami360/glossary-llm-chat-bot/assets/25688193/5eca6db2-b8ca-4fd1-a0a3-ea3712bdd0b0"><br>
    <img width="800" alt="image" src="https://github.com/Yagami360/glossary-llm-chat-bot/assets/25688193/e1915c84-c411-4fef-b4ef-f47f3ccac86e"><br>
    - `Command`: `/glossary-chat-bot` を設定する
    - `Request URL`: `${API_URL}/slack/events`（例:`https://glossary-llm-chat-bot-sqwnhlznqa-an.a.run.app/slack/events`）<br>
        `API_URL` は Cloud Run の URL で、以下のコマンドで確認できます
        ```sh
        make get-api-url
        ```

## 使用方法

1. Slack の左下メニューの App から「アプリを追加する」ボタンをクリックする。<br>
    <img width="300" alt="image" src="https://github.com/Yagami360/glossary-llm-chat-bot/assets/25688193/169fb32f-48fc-4b62-b178-8190a2a126ca">
    
1. `glossary-llm-chat-bot` という名前のアプリを検索し追加する。
    <img width="800" alt="image" src="https://github.com/Yagami360/glossary-llm-chat-bot/assets/25688193/8c6a1f9f-d996-4326-b127-4d4c5633be69"><br>

1. アプリ追加後、アプリ上の「メッセージ」タブに移動し、`/glossary-chat-bot ${質問文}` の形式でコマンド送信する<br>
    - コマンド例<br>
        <img width="500" alt="image" src="https://github.com/Yagami360/glossary-llm-chat-bot/assets/25688193/d067fa5b-5af3-49a3-96f2-5c5834bc5fd8">

    - 出力例<br>
        <img width="300" alt="image" src="https://github.com/Yagami360/glossary-llm-chat-bot/assets/25688193/70bec528-3ba6-45ce-8605-8e8df68e1de6">

1. 用語を修正&追加したい場合は、用語集スプレッドシートを更新してください
