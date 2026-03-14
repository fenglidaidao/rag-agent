import pandas as pd
from pathlib import Path
from langchain_core.documents import Document
from core.logger import get_logger
logger = get_logger("csv_loader")

def load_csv(file_path):

    encodings = ["utf-8", "gbk", "gb2312"]

    df = None

    for enc in encodings:
        try:
            df = pd.read_csv(file_path, encoding=enc)
            break
        except:
            pass

    if df is None:
        logger.error(f"Failed loading csv {file_path}")
        return []

    docs = []

    columns = df.columns.tolist()

    for i, row in df.iterrows():

        pairs = []

        for col in columns:

            val = row[col]

            if pd.isna(val):
                continue

            pairs.append(f"{col}={val}")

        text = "表格数据：" + ", ".join(pairs)

        docs.append(
            Document(
                page_content=text,
                metadata={
                    "source": file_path,
                    "row": i,
                    "type": "csv"
                }
            )
        )

    logger.info(f"Loaded {len(docs)} rows from {file_path}")

    return docs