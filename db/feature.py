from langchain.text_splitter import CharacterTextSplitter
from langchain.vectorstores import FAISS, Chroma

from config import AppConfig
from utils.csv_loader import CSVLoader
from utils.logger import logger


def update_db_from_csv(file_path, emb_model, chunk_size=1000, chunk_overlap=0, separator="\n", feature_db_type="chroma"):
    # Document Loaders を使用して csv ファイル読み込み
    document_loader = CSVLoader(
        file_path,
        text_columns=AppConfig.dataset_text_columns,
        meta_columns=AppConfig.dataset_meta_columns,
    )
    documents = document_loader.load()
    logger.debug(f'documents={documents}')

    # LangChain Data connection の Text Splitters を使用して、テキストを分割
    text_splitter = CharacterTextSplitter(
        separator=separator,            # セパレータ
        chunk_size=chunk_size,          # チャンクの最大文字数
        chunk_overlap=chunk_overlap     #
    )
    split_documents = text_splitter.split_documents(documents)
    logger.debug(f'split_documents={split_documents}')

    # 埋め込みモデルで分割テキストを埋め込み埋め込みベクトルを作成。埋め込むベクトルを特徴量データベース（VectorDB）に保存
    if feature_db_type == "chroma":
        feature_db = Chroma.from_documents(split_documents, emb_model)
    elif feature_db_type == "faiss":
        feature_db = FAISS.from_documents(split_documents, emb_model)
    else:
        feature_db = Chroma.from_documents(split_documents, emb_model)

    return feature_db
