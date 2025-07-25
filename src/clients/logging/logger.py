# clients/logging/logger.py

import logging
import os
import sys

def setup_logger(name: str, log_file: str = "logs/app.log", level=logging.INFO):
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    formatter = logging.Formatter('[%(asctime)s][%(levelname)s] %(name)s: %(message)s')
    file_handler = logging.FileHandler(log_file, mode='a', encoding='utf-8')
    file_handler.setFormatter(formatter)
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(formatter)
    logger = logging.getLogger(name)
    logger.setLevel(level)
    # 确保不会重复添加handler
    if not any(isinstance(h, logging.FileHandler) for h in logger.handlers):
        logger.addHandler(file_handler)
    if not any(isinstance(h, logging.StreamHandler) and not isinstance(h, logging.FileHandler) for h in logger.handlers):
        logger.addHandler(stream_handler)
    return logger

logger = setup_logger("llm_codefix", level=logging.DEBUG)