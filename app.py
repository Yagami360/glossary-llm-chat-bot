import os
import sys

import flask
from flask_cors import CORS
from langchain.agents import AgentType, Tool, initialize_agent
from langchain.chains import RetrievalQA
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.llms import OpenAI
from langchain.utilities import SerpAPIWrapper
from slack_bolt import App
from slack_bolt.adapter.flask import SlackRequestHandler

from api.auth import requires_auth
from api.error_response_handlers import configure_errorhandlers
from api.errors import BadRequest, InternalServerError, NotFound
from config import AppConfig, LLMConfig, PromptConfig
from db.feature import update_db_from_csv
from prompt.prompt_template_loader import PromptTemplateLoader
from spreadsheet.client import SpreadsheetClient
from utils.logger import log_decorator, logger

# slack-bolt
bolt_app = App(
    token=AppConfig.slack_bot_token,
    signing_secret=AppConfig.slack_signing_token
)
handler = SlackRequestHandler(bolt_app)

# flask
flask_app = flask.Flask(__name__)
CORS(flask_app, resources={r"*": {"origins": "*"}}, methods=['POST', 'GET'])
flask_app.config['JSON_AS_ASCII'] = False
flask_app.config["JSON_SORT_KEYS"] = False
configure_errorhandlers(flask_app)

# define LLM model
llm = OpenAI(
    model_name=LLMConfig.model_name,
    temperature=LLMConfig.temperature,
)
logger.debug(f'llm={llm}')

# define embeddings model
emb_model = OpenAIEmbeddings(
    model=LLMConfig.emb_model_name,
)
logger.debug(f'emb_model={emb_model}')

# init feature DB
feature_db = None

# define prompt template
try:
    prompt_template = PromptTemplateLoader(
        file_path=PromptConfig.prompt_file_path
    )
except Exception as e:
    logger.error(f"failed to load prompt file! | {e}")
    exit(1)


@log_decorator(logger=logger)
@flask_app.route('/health', methods=['GET'])
def health():
    resp = flask.jsonify(
        {
            'message': 'succeeded to health check',
        }
    )
    return resp, 200


@log_decorator(logger=logger)
@flask_app.route('/update_db', methods=['PUT'])
def update_db():
    # create csv file from spreadsheet
    spreadsheet = SpreadsheetClient(gcp_sa_key=AppConfig.gcp_sa_key)
    try:
        worksheet = spreadsheet.get_worksheet(AppConfig.spreadsheet_key, AppConfig.spreadsheet_name)
        logger.debug(f'worksheet={worksheet}')
    except Exception as e:
        raise NotFound(f"failed to open spreadsheet! | {e}")

    try:
        spreadsheet.write_worksheet_csv(worksheet, AppConfig.dataset_path)
    except Exception as e:
        raise InternalServerError(f"failed to write csv file from spreadsheet! | {e}")

    # update feature db from csv
    feature_db = update_db_from_csv(
        file_path=AppConfig.dataset_path,
        emb_model=emb_model,
        chunk_size=AppConfig.chunk_size,
        feature_db_type=LLMConfig.feature_db_type
    )

    # set response message json
    resp = flask.jsonify(
        {
            'message': 'succeeded to update feature db'
        }
    )
    return resp, 200


@log_decorator(logger=logger)
@flask_app.route('/chat', methods=['POST'])
@requires_auth
def chat():
    # get input text
    try:
        question = flask.request.form['text']
        logger.debug(f'question={question}')
    except Exception as e:
        raise BadRequest(f"failed to get input text! | {e}")

    # 特徴量データベース（VectorDB）から retriever（ユーザーからの入力文に対して、外部テキストデータの分割した各文章から類似度の高い文章を検索＆取得をするための機能）作成
    retriever = feature_db.as_retriever(
        search_type="similarity_score_threshold",
        search_kwargs={
            "k": LLMConfig.retriever_top_k,                            # 上位 k 個の分割文章を検索＆取得
            "score_threshold": LLMConfig.retriever_score_threshold,    # スレッショルド値
        },
    )

    # retriever で、ユーザーからの入力文に対して、外部テキストデータの分割した各文章から類似度の高い情報を検索＆取得
    context = retriever.get_relevant_documents(query=question)
    logger.debug(f"context={context}")

    # create prompt from prompt template
    prompt = prompt_template.format(question=question, context=context)
    logger.debug(f"prompt={prompt}")

    # LangChain Data connection の Retrievers を使用して、RetrievalQA Chain（質問応答 QA の取得に使用する Chain）を生成
    qa_chain = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=retriever
    )
    logger.debug(f'qa_chain={qa_chain}')

    # define Agent
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

    # run LLLM prediction for QA task
    try:
        if LLMConfig.use_function_calling:
            answer = agent.run(prompt)
        else:
            answer = qa_chain.run(prompt)
    except Exception as e:
        try:
            # 用語集に該当情報がみつからない かつ Google 検索でも該当情報がみつからない場合
            answer = qa_chain.run(prompt)
        except Exception as e:
            raise InternalServerError(f"failed to generate answer! | {e}")

    logger.info(f'answer={answer}')

    # set response message json
    resp = flask.jsonify(
        {
            'question': f"{question}",
            'answer': f"{answer}",
        }
    )
    return resp, 200


@flask_app.route("/slack/events", methods=["POST"])
def slack_events():
    return handler.handle(flask.request)


@log_decorator(logger=logger)
@bolt_app.command("/glossary-chat-bot")
def chat_by_slack(ack, respond, command):
    logger.debug(f'command={command}')

    # return ACK as soon as possible
    ack()

    # verify token
    slack_verify_token = command['token']
    if not slack_verify_token == AppConfig.slack_verify_token:
        logger.error(f"error: unauthorized, error_description: authorization malformed!")
        respond(f"error: unauthorized, error_description: authorization malformed!")
        return

    # get input text
    try:
        question = command['text']
        logger.debug(f'question={question}')
    except Exception as e:
        logger.error(f"error: bad request, error_description: failed to get input text! | {e}")
        respond(f"error: bad request, error_description: failed to get input text! | {e}")
        return

    if question == "":
        respond(f"`{command['command']}` の後に質問文を入力してください")
        return

    # 特徴量データベース（VectorDB）から retriever（ユーザーからの入力文に対して、外部テキストデータの分割した各文章から類似度の高い文章を検索＆取得をするための機能）作成
    retriever = feature_db.as_retriever(
        search_type="similarity_score_threshold",
        search_kwargs={
            "k": LLMConfig.retriever_top_k,                           # 上位 k 個の分割文章を検索＆取得
            "score_threshold": LLMConfig.retriever_score_threshold,   # スレッショルド値
        },
    )

    # retriever で、ユーザーからの入力文に対して、外部テキストデータの分割した各文章から類似度の高い情報を検索＆取得
    context = retriever.get_relevant_documents(query=question)
    logger.debug(f"context={context}")

    # create prompt from prompt template
    prompt = prompt_template.format(question=question, context=context)
    logger.debug(f"prompt={prompt}")

    # LangChain Data connection の Retrievers を使用して、RetrievalQA Chain（質問応答 QA の取得に使用する Chain）を生成
    qa_chain = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=retriever
    )
    logger.debug(f'qa_chain={qa_chain}')

    # define Agent
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

    # run LLLM prediction for QA task
    ack()
    try:
        if LLMConfig.use_function_calling:
            answer = agent.run(prompt)
        else:
            answer = qa_chain.run(prompt)
    except Exception as e:
        try:
            # 用語集に該当情報がみつからない かつ Google 検索でも該当情報がみつからない場合
            answer = qa_chain.run(prompt)
        except Exception as e:
            logger.error(f"error: internal_server_error, error_description: failed to generate answer! | {e}")
            respond(f"error: internal_server_error, error_description: failed to generate answer! | {e}")
            return

    ack()
    logger.info(f'answer={answer}')

    # set response message
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
        logger.error(f"error: internal_server_error, error_description: failed to notify slack! | {e}")
        respond(f"error: internal_server_error, error_description: failed to notify slack! | {e}")
        return

    return


if __name__ == "__main__":
    logger.debug(f'AppConfig={vars(AppConfig)}')
    logger.debug(f'LLMConfig={vars(LLMConfig)}')

    # create csv file from spreadsheet
    spreadsheet = SpreadsheetClient(gcp_sa_key=AppConfig.gcp_sa_key)
    try:
        worksheet = spreadsheet.get_worksheet(AppConfig.spreadsheet_key, AppConfig.spreadsheet_name)
        logger.debug(f'worksheet={worksheet}')
    except Exception as e:
        logger.error(f"failed to open spreadsheet! | {e}")
        exit(1)

    try:
        os.makedirs(os.path.dirname(AppConfig.dataset_path), exist_ok=True)
        spreadsheet.write_worksheet_csv(worksheet, AppConfig.dataset_path)
    except Exception as e:
        logger.error(f"failed to write csv file from spreadsheet! | {e}")
        exit(1)

    # update feature db from csv
    feature_db = update_db_from_csv(
        file_path=AppConfig.dataset_path,
        emb_model=emb_model,
        chunk_size=AppConfig.chunk_size,
        feature_db_type=LLMConfig.feature_db_type,
    )

    # run flask-api
    flask_app.run(host=AppConfig.host, port=AppConfig.port)
