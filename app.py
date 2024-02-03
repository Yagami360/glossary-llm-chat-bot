import os

import flask
from flask_cors import CORS

from langchain.chains import RetrievalQA
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.llms import OpenAI
from langchain.agents import Tool
from langchain.agents import initialize_agent
from langchain.agents import AgentType
from langchain.utilities import SerpAPIWrapper

from slack_bolt import App
from slack_bolt.adapter.flask import SlackRequestHandler

from config import AppConfig, LLMConfig, PromptConfig
from db.feature import update_db_from_csv
from prompt.prompt_template_loader import PromptTemplateLoader
from spreadsheet.client import SpreadsheetClient
from utils.logger import log_decorator, logger

# slack_bolt 関連
bolt_app = App(
    token=AppConfig.slack_bot_token,
    signing_secret=AppConfig.slack_signing_token
)
handler = SlackRequestHandler(bolt_app)

# Flask 関連
flask_app = flask.Flask(__name__)
CORS(flask_app, resources={r"*": {"origins": "*"}}, methods=['POST', 'GET'])  # OPTIONS を受け取らないようにする（Access-Control-Allow-Origin エラー対策）
flask_app.config['JSON_AS_ASCII'] = False     # 日本語文字化け対策
flask_app.config["JSON_SORT_KEYS"] = False    # ソートをそのまま

# LLM モデル定義
llm = OpenAI(
    model_name=LLMConfig.model_name,
    temperature=LLMConfig.temperature,
)
logger.debug(f'llm={llm}')

# 埋め込みモデル定義
emb_model = OpenAIEmbeddings(
    model=LLMConfig.emb_model_name,
)
logger.debug(f'emb_model={emb_model}')

# 特徴量データベース初期化
feature_db = None

# プロンプトテンプレート定義
try:
    prompt_template = PromptTemplateLoader(
        file_path=PromptConfig.prompt_file_path
    )
except Exception as e:
    logger.error(f"Failed to load prompt file! | {e}")
    exit(1)


@log_decorator(logger=logger)
@flask_app.route('/health', methods=['GET'])
def health():
    response = flask.jsonify(
        {
            'status': 'OK',
        }
    )
    return response, 200


@log_decorator(logger=logger)
@flask_app.route('/update_db', methods=['PUT'])
def update_db():
    # スプレッドシートから csv ファイル作成
    spreadsheet = SpreadsheetClient(gcp_sa_key=AppConfig.gcp_sa_key)
    try:
        worksheet = spreadsheet.get_worksheet(AppConfig.spreadsheet_key, AppConfig.spreadsheet_name)
        logger.debug(f'worksheet={worksheet}')
    except Exception as e:
        logger.error(f"Failed to open spreadsheet! | {e}")
        response = flask.jsonify(
            {
                'status': 'NG',
                'status_reason': f"Failed to open spreadsheet! | {e}",
            }
        )
        return response, 500

    try:
        spreadsheet.write_worksheet_csv(worksheet, AppConfig.dataset_path)
    except Exception as e:
        logger.error(f"Failed to write csv file from spreadsheet! | {e}")
        response = flask.jsonify(
            {
                'status': 'NG',
                'status_reason': f"Failed to write csv file from spreadsheet! | {e}",
            }
        )
        return response, 500

    # csv ファイルから特徴量 DB 更新
    feature_db = update_db_from_csv(
        file_path=AppConfig.dataset_path,
        emb_model=emb_model,
        chunk_size=AppConfig.chunk_size,
        feature_db_type=LLMConfig.feature_db_type
    )

    # レスポンスデータ設定
    response = flask.jsonify(
        {
            'status': 'OK',
            'status_reason': 'Succeeded to update feature db'
        }
    )
    return response, 200


@log_decorator(logger=logger)
@flask_app.route('/chat', methods=['POST'])
def chat():
    # slack-bot 用の認証処理
    slack_verify_token = flask.request.form.get('token', '')
    if not slack_verify_token == AppConfig.slack_verify_token:
        logger.error(f"Unauthorized!")
        response = flask.jsonify(
            {
                'status': 'NG',
                'status_reason': f"Unauthorized!",
                'question': None,
                'answer': None,
            }
        )

    # json body 取得
    try:
        question = flask.request.form.get('text', '')
        logger.debug(f'question={question}')
    except Exception as e:
        logger.error(f"Failed to get json body! | {e}")
        response = flask.jsonify(
            {
                'status': 'NG',
                'status_reason': f"Failed to get json body! | {e}",
                'question': question,
                'answer': None,
            }
        )
        return response, 400

    # 特徴量データベース（VectorDB）から retriever（ユーザーからの入力文に対して、外部テキストデータの分割した各文章から類似度の高い文章を検索＆取得をするための機能）作成
    retriever = feature_db.as_retriever(
        search_type="similarity_score_threshold",
        search_kwargs={
            "k": LLMConfig.retriever_top_k,                                     # 上位 k 個の分割文章を検索＆取得
            "score_threshold": LLMConfig.retriever_score_threshold,             # スレッショルド値
        },
    )

    # retriever で、ユーザーからの入力文に対して、外部テキストデータの分割した各文章から類似度の高い情報を検索＆取得
    context = retriever.get_relevant_documents(query=question)
    logger.debug(f"context={context}")

    # prompt 設定
    prompt = prompt_template.format(question=question, context=context)
    logger.debug(f"prompt={prompt}")

    # LangChain Data connection の Retrievers を使用して、RetrievalQA Chain（質問応答 QA の取得に使用する Chain）を生成
    # Chain : 複数のプロンプト入力を実行するための機能
    qa_chain = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=retriever
    )
    logger.debug(f'qa_chain={qa_chain}')

    # Agent 定義
    if LLMConfig.use_function_calling:
        tools = [
            Tool(
                name="RAGBot",
                func=qa_chain.run,
                description="RAG を使用して LLM が学習に使用していない特定ドメインの質問応答を行うbot"
            ),
            Tool(
                name="GoogleSearch",
                func=SerpAPIWrapper().run,
                description="useful for when you need to answer questions about current events. You should ask targeted questions"
            ),
        ]
        agent = initialize_agent(
            tools,
            llm,
            agent=AgentType.OPENAI_FUNCTIONS,
            verbose=True,
        )

    # LLM 推論実行（QA:質問応答）
    try:
        if LLMConfig.use_function_calling:
            answer = agent.run(prompt)
        else:
            answer = qa_chain.run(prompt)
        logger.info(f'answer={answer}')
    except Exception as e:
        logger.error(f"Failed to generate answer! | {e}")
        response = flask.jsonify(
            {
                'status': 'NG',
                'status_reason': f"Failed to generate answer! | {e}",
                'question': question,
                'answer': None,
            }
        )
        return response, 500

    # レスポンスデータ設定
    response = flask.jsonify(
        {
            'status': 'OK',
            'status_reason': f"Succeeded to generate answer",
            'question': f"{question}",
            'answer': f"{answer}",
        }
    )
    return response, 200


@flask_app.route("/slack/events", methods=["POST"])
def slack_events():
    # /slack/events エンドポイントアクセス時（/glossary-chat-bot コマンド実行時）、slack_bolt の handler に処理を投げる
    # その後、@bolt_app.command("/glossary-chat-bot") デコレータを付与した chat_by_slack() メソッドが実行される
    return handler.handle(flask.request)


@log_decorator(logger=logger)
@bolt_app.command("/glossary-chat-bot")
def chat_by_slack(ack, respond, command):
    # できるだけ早く ACK を返す
    ack()
    logger.debug(f'command={command}')

    # slack-bot 用の認証処理
    slack_verify_token = command['token']
    if not slack_verify_token == AppConfig.slack_verify_token:
        logger.error(f"Unauthorized!")
        respond(f"Unauthorized!")

    # 入力テキスト取得
    try:
        question = command['text']
        logger.debug(f'question={question}')
    except Exception as e:
        logger.error(f"Failed to get question text! | {e}")
        respond(f"Failed to get question text! | {e}")
        return

    if question == "":
        respond(f"`{command['command']}` の後に質問文を入力してください")
        return

    # 特徴量データベース（VectorDB）から retriever（ユーザーからの入力文に対して、外部テキストデータの分割した各文章から類似度の高い文章を検索＆取得をするための機能）作成
    retriever = feature_db.as_retriever(
        search_type="similarity_score_threshold",
        search_kwargs={
            "k": LLMConfig.retriever_top_k,                                     # 上位 k 個の分割文章を検索＆取得
            "score_threshold": LLMConfig.retriever_score_threshold,             # スレッショルド値
        },
    )

    # retriever で、ユーザーからの入力文に対して、外部テキストデータの分割した各文章から類似度の高い情報を検索＆取得
    context = retriever.get_relevant_documents(query=question)
    logger.debug(f"context={context}")

    # prompt 設定
    prompt = prompt_template.format(question=question, context=context)
    logger.debug(f"prompt={prompt}")

    # LangChain Data connection の Retrievers を使用して、RetrievalQA Chain（質問応答 QA の取得に使用する Chain）を生成
    # Chain : 複数のプロンプト入力を実行するための機能
    qa_chain = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=retriever
    )
    logger.debug(f'qa_chain={qa_chain}')

    # Agent 定義
    if LLMConfig.use_function_calling:
        tools = [
            Tool(
                name="RAGBot",
                func=qa_chain.run,
                description="RAG を使用して LLM が学習に使用していない特定ドメインの質問応答を行うbot"
            ),
            Tool(
                name="GoogleSearch",
                func=SerpAPIWrapper().run,
                description="useful for when you need to answer questions about current events. You should ask targeted questions"
            ),
        ]
        agent = initialize_agent(
            tools,
            llm,
            agent=AgentType.OPENAI_FUNCTIONS,
            verbose=True,
        )

    # LLM 推論実行（QA:質問応答）
    ack()
    try:
        if LLMConfig.use_function_calling:
            answer = agent.run(prompt)
        else:
            answer = qa_chain.run(prompt)
        logger.info(f'answer={answer}')
        ack()
    except Exception as e:
        logger.error(f"Failed to generate answer! | {e}")
        respond(f"Failed to generate answer! | {e}")
        return

    # Slack 返信
    try:
        user_name = command["user_name"]
        slack_msg_1 = f"{user_name}さんからの質問です:\n{question}\n"
        slack_msg_1 += f"回答:\n"
        slack_msg_1 += f"```\n"
        slack_msg_1 += f"{answer}\n"
        slack_msg_1 += f"```\n"
        slack_resp_1 = bolt_app.client.chat_postMessage(
            channel=command["channel_id"],
            text=slack_msg_1,
            icon_emoji=':robot_face:',
            username='glossary-llm-chat-bot'
        )

        slack_msg_2 = f"解決しましたか？\n"
        slack_msg_2 += f"用語を追加＆修正したい場合は、以下のスプレッドシートから入力してください。\n"
        slack_msg_2 += f"https://docs.google.com/spreadsheets/d/{AppConfig.spreadsheet_key}\n"
        bolt_app.client.chat_postMessage(
            channel=command["channel_id"],
            text=slack_msg_2,
            icon_emoji=':robot_face:',
            thread_ts=slack_resp_1['message']['ts']
        )
    except Exception as e:
        logger.error(f"Failed to notify slack! | {e}")
        respond(f"Failed to notify slack! | {e}")

    return


if __name__ == "__main__":
    logger.debug(f'AppConfig={vars(AppConfig)}')
    logger.debug(f'LLMConfig={vars(LLMConfig)}')

    # スプレッドシートから csv ファイル作成
    spreadsheet = SpreadsheetClient(gcp_sa_key=AppConfig.gcp_sa_key)
    try:
        worksheet = spreadsheet.get_worksheet(AppConfig.spreadsheet_key, AppConfig.spreadsheet_name)
        logger.debug(f'worksheet={worksheet}')
    except Exception as e:
        logger.error(f"Failed to open spreadsheet! | {e}")
        exit(1)

    try:
        os.makedirs(os.path.dirname(AppConfig.dataset_path), exist_ok=True)
        spreadsheet.write_worksheet_csv(worksheet, AppConfig.dataset_path)
    except Exception as e:
        logger.error(f"Failed to write csv file from spreadsheet! | {e}")
        exit(1)

    # 特徴量 DB 初回更新
    feature_db = update_db_from_csv(
        file_path=AppConfig.dataset_path,
        emb_model=emb_model,
        chunk_size=AppConfig.chunk_size,
        feature_db_type=LLMConfig.feature_db_type,
    )

    # API 起動
    flask_app.run(host=AppConfig.host, port=AppConfig.port)
