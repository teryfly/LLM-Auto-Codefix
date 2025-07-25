# controller/loop_controller.py

import time
from clients.logging.logger import logger

class LoopController:
    def __init__(self, config):
        self.max_debug = config.retry_config.debug_max_time
        self.timeout_minutes = config.timeout.overall_timeout_minutes

    def run_with_timeout(self, func):
        start = time.time()
        for i in range(self.max_debug):
            logger.info(f"debug循环 {i+1}/{self.max_debug}")
            if (time.time() - start) > self.timeout_minutes * 60:
                logger.error("总超时，终止任务")
                print("[FAIL] 任务超时")
                return False
            ok = func(i)
            if ok:
                logger.info("修复并执行成功，流程结束")
                print("[SUCCESS] 任务修复成功")
                return True
        logger.error("达到最大debug循环次数，终止任务")
        print("[FAIL] 达到最大debug循环次数")
        return False