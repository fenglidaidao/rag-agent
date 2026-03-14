# core/file_security.py
from pathlib import Path
from core.logger import get_logger

logger = get_logger("file_security")

# 文件大小限制：20MB
MAX_FILE_SIZE = 20 * 1024 * 1024

# 支持的文件类型及对应 magic bytes
ALLOWED_EXTENSIONS = {".txt", ".md", ".pdf", ".docx", ".csv", ".png", ".jpg", ".jpeg", ".webp"}

MAGIC_BYTES = {
    ".png":  [(0, b"\x89PNG")],
    ".jpg":  [(0, b"\xff\xd8\xff")],
    ".jpeg": [(0, b"\xff\xd8\xff")],
    ".webp": [(0, b"RIFF"), (8, b"WEBP")],
    ".pdf":  [(0, b"%PDF")],
    ".docx": [(0, b"PK\x03\x04")],
}


def safe_filename(filename: str) -> str:
    """
    过滤危险文件名：
    - 去掉路径部分，防止路径穿越（../../etc/passwd）
    - 去掉危险字符
    """
    name = Path(filename).name                        # 只保留文件名
    name = name.replace("..", "").replace("/", "").replace("\\", "")
    name = "".join(c for c in name if c.isprintable() and c not in '<>:"|?*')

    if not name:
        raise ValueError("文件名非法")

    logger.debug(f"文件名安全处理：{filename} → {name}")
    return name


def validate_extension(filename: str) -> str:
    """校验文件扩展名"""
    suffix = Path(filename).suffix.lower()
    if suffix not in ALLOWED_EXTENSIONS:
        raise ValueError(f"不支持的文件格式 '{suffix}'，支持：{', '.join(ALLOWED_EXTENSIONS)}")
    return suffix


def validate_file_size(file_content: bytes, filename: str):
    """校验文件大小"""
    size = len(file_content)
    if size == 0:
        raise ValueError("文件内容为空，拒绝处理")
    if size > MAX_FILE_SIZE:
        raise ValueError(
            f"文件大小 {round(size / 1024 / 1024, 2)}MB 超过限制 {MAX_FILE_SIZE // 1024 // 1024}MB"
        )
    logger.debug(f"文件大小校验通过：{filename} | {round(size / 1024, 2)}KB")


def validate_magic_bytes(file_content: bytes, suffix: str, filename: str):
    """
    校验文件头 magic bytes，防止伪造文件类型
    txt / md / csv 是纯文本，不做 magic bytes 校验
    """
    if suffix not in MAGIC_BYTES:
        return

    for offset, magic in MAGIC_BYTES[suffix]:
        if file_content[offset: offset + len(magic)] != magic:
            raise ValueError(f"文件内容与扩展名 '{suffix}' 不匹配，疑似伪造文件类型")

    logger.debug(f"magic bytes 校验通过：{filename}")


def validate_file(filename: str, file_content: bytes) -> str:
    """
    完整文件校验流程，返回安全处理后的文件名
    1. 文件名安全处理
    2. 扩展名校验
    3. 文件大小校验
    4. magic bytes 校验
    """
    safe_name = safe_filename(filename)
    suffix = validate_extension(safe_name)
    validate_file_size(file_content, safe_name)
    validate_magic_bytes(file_content, suffix, safe_name)

    logger.info(f"文件校验通过：{safe_name} | 大小={round(len(file_content)/1024, 2)}KB")
    return safe_name