import os
from distutils.util import strtobool


class AppConfig:
    host = os.environ.get('HOST', '0.0.0.0')
    port = int(os.environ.get('PORT', '3000'))
    gcp_sa_key = os.environ.get('GOOGLE_APPLICATION_CREDENTIALS', '/app/credentials/glossary-llm-chat-bot-sa.json')
    spreadsheet_key = os.environ.get('SPREADSHEET_KEY', 'dummy')
    spreadsheet_name = os.environ.get('SPREADSHEET_NAME', 'dummy')
    dataset_path = os.environ.get('DATASET_PATH', '/app/dataset/glossary.csv')
    dataset_text_columns = str(os.environ.get('DATASET_TEXT_COLUMNS', "用語,意味")).split(',')
    dataset_meta_columns = str(os.environ.get('DATASET_META_COLUMNS', "メタデータ")).split(',')
    chunk_size = int(os.environ.get('CHUNK_SIZE', '2000'))
    slack_bot_token = os.environ.get('SLACK_BOT_TOKEN', 'dummy')
    slack_signing_token = os.environ.get('SLACK_SIGNING_SECRET', 'dummy')
    slack_verify_token = os.environ.get('SLACK_VERIFY_TOKEN', 'dummy')


class PromptConfig:
    prompt_file_path = os.environ.get('PROMPT_FILE_PATH', 'prompt/prompt_files/prompt_2.yml')


class LLMConfig:
    emb_model_name = os.environ.get('EMB_MODEL_NAME', 'text-embedding-ada-002')
    model_name = os.environ.get('MODEL_NAME', 'gpt-3.5-turbo-0613')         # "text-davinci-003", "gpt-3.5-turbo", "gpt-3.5-turbo-0613" etc
    temperature = float(os.environ.get('TEMPERATURE', '0.0'))
    retriever_top_k = int(os.environ.get('RETRIEVER_TOP_K', '4'))
    retriever_score_threshold = float(os.environ.get('RETRIEVER_SCORE_THRESHOLD', '0.5'))
    feature_db_type = os.environ.get('FEATURE_DB_TYPE', 'faiss')                        # "chroma" or "faiss"
    use_function_calling = strtobool(os.environ.get('USE_FUNCTION_CALLING', 'True'))    # Function calling を使用して RAG を使用しない一般的な質問応答をできるようにするかどうか
