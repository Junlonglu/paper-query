# logger_utils.py
import logging
import os
from datetime import datetime


def setup_logger(name: str, log_file: str = "logs/app.log", level=logging.INFO):
    os.makedirs(os.path.dirname(log_file), exist_ok=True)

    logger = logging.getLogger(name)
    logger.setLevel(level)

    if not logger.handlers:  # 防止重复添加 handler
        formatter = logging.Formatter('%(thread)d - %(asctime)s - %(filename)s[line:%(lineno)d] - %(funcName)s - %(levelname)s - %(message)s')

        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

        # stream_handler = logging.StreamHandler()
        # stream_handler.setFormatter(formatter)
        # logger.addHandler(stream_handler)

    return logger
