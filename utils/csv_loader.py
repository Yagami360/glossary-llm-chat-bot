import csv
from typing import Dict, List, Optional

from langchain.docstore.document import Document


class CSVLoader:
    def __init__(
        self,
        file_path: str,
        text_columns: [str],
        source_column: Optional[str] = None,
        meta_columns: Optional[list] = None,
        csv_args: Optional[Dict] = None,
        encoding: Optional[str] = None,
    ):
        self.file_path = file_path
        self.source_column = source_column
        self.text_columns = text_columns
        self.meta_columns = meta_columns
        self.encoding = encoding
        self.csv_args = csv_args or {}

    def load(self) -> List[Document]:
        docs = []
        with open(self.file_path, newline="", encoding=self.encoding) as csvfile:
            csv_reader = csv.DictReader(csvfile, **self.csv_args)  # type: ignore
            for i, row in enumerate(csv_reader):
                content = "\n".join(f"{k.strip()}: {v.strip()}" for k, v in row.items() if k in self.text_columns)
                metadata = {}
                try:
                    source = (
                        row[self.source_column]
                        if self.source_column is not None
                        else self.file_path
                    )
                    if self.meta_columns is not None:
                        metadata = {col: row[col] for col in self.meta_columns}
                except KeyError:
                    raise ValueError(
                        f"Some columns are not found in CSV file."
                    )

                metadata["source"] = source
                metadata["row"] = i
                doc = Document(page_content=content, metadata=metadata)
                docs.append(doc)

        return docs
