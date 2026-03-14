# core/logger.py
import logging
import os
from logging.handlers import TimedRotatingFileHandler

LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)


class SafeTimedRotatingFileHandler(TimedRotatingFileHandler):
    """Windows 兼容的滚动日志处理器，rename 失败时静默跳过"""
    def doRollover(self):
        try:
            super().doRollover()
        except PermissionError:
            pass  # Windows 多进程占用时跳过，不影响主进程日志写入


def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)

    if logger.handlers:
        return logger  # 避免重复添加 handler

    logger.setLevel(logging.DEBUG)

    fmt = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # 控制台
    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    console.setFormatter(fmt)
    logger.addHandler(console)

    # ✅ 使用兼容 Windows 的处理器
    file_handler = SafeTimedRotatingFileHandler(
        filename=os.path.join(LOG_DIR, "app.log"),
        when="midnight",
        interval=1,
        backupCount=7,
        encoding="utf-8",
        delay=True  # ✅ 延迟创建文件，避免 reloader 进程抢占
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(fmt)
    logger.addHandler(file_handler)

    logger.propagate = False
    return logger