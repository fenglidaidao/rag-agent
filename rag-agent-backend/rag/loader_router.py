from pathlib import Path

from langchain_community.document_loaders import (
    TextLoader,
    PyPDFLoader,
    Docx2txtLoader
)

from rag.image_loader import load_image
from rag.csv_loader import load_csv
from core.logger import get_logger
logger = get_logger("loader_router")

TEXT_SUFFIX = [".txt", ".md"]
PDF_SUFFIX = [".pdf"]
DOC_SUFFIX = [".docx"]
CSV_SUFFIX = [".csv"]
IMAGE_SUFFIX = [".png", ".jpg", ".jpeg", ".webp"]


def load_document(file_path):

    path = Path(file_path)
    suffix = path.suffix.lower()

    try:

        if suffix in TEXT_SUFFIX:

            loader = TextLoader(file_path, encoding="utf-8")
            docs = loader.load()

        elif suffix in PDF_SUFFIX:

            loader = PyPDFLoader(file_path)
            docs = loader.load()

        elif suffix in DOC_SUFFIX:

            loader = Docx2txtLoader(file_path)
            docs = loader.load()

        elif suffix in CSV_SUFFIX:

            docs = load_csv(file_path)

        elif suffix in IMAGE_SUFFIX:

            docs = load_image(file_path)

        else:

            logger.warning(f"Unsupported file type: {suffix}")
            return []

    except Exception as e:

        logger.error(f"Failed loading {file_path}: {e}")
        return []

    logger.error(f"Loaded {len(docs)} documents from {file_path}")

    return docs