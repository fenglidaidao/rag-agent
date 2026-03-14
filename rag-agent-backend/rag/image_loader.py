import base64
from pathlib import Path
from langchain_core.documents import Document
from langchain_core.messages import HumanMessage
from core.llm import get_vision_llm
from core.logger import get_logger
logger = get_logger("image_loader")


def encode_image(path):

    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def load_image(file_path: str):

    llm = get_vision_llm()

    base64_image = encode_image(file_path)

    suffix = Path(file_path).suffix.lower()

    mime = {
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".webp": "image/webp"
    }.get(suffix, "image/png")

    prompt = """
You are converting an image into text for a knowledge base.

Describe the image in detail.

Include:
- visible text
- objects
- tables
- charts
"""

    message = HumanMessage(
        content=[
            {"type": "text", "text": prompt},
            {
                "type": "image_url",
                "image_url": {
                    "url": f"data:{mime};base64,{base64_image}"
                }
            }
        ]
    )

    result = llm.invoke([message])

    text = result.content

    doc = Document(
        page_content=text,
        metadata={
            "source": file_path,
            "type": "image"
        }
    )

    logger.info(f"Loaded image description from {file_path}")

    return [doc]