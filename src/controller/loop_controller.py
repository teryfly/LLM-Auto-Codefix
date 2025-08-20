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
    def run_loop(self, loop_func, max_iterations=None):
        """
        执行循环，直到成功或达到最大次数
        """
        if max_iterations is None:
            max_iterations = self.max_debug
        start_time = time.time()
        for i in range(max_iterations):
            logger.info(f"Loop iteration {i+1}/{max_iterations}")
            print(f"🔄 执行第 {i+1}/{max_iterations} 次循环", flush=True)
            # 检查总超时
            if (time.time() - start_time) > self.timeout_minutes * 60:
                logger.error("总超时，终止循环")
                print("❌ 循环总超时，终止任务", flush=True)
                return False
            try:
                success = loop_func(i)
                if success:
                    logger.info(f"循环在第 {i+1} 次成功完成")
                    print(f"✅ 循环在第 {i+1} 次成功完成", flush=True)
                    return True
            except Exception as e:
                logger.error(f"循环第 {i+1} 次执行出错: {e}")
                print(f"❌ 循环第 {i+1} 次执行出错: {e}", flush=True)
                # 继续下一次循环而不是退出
                continue
            # 如果不是最后一次，等待一下再继续
            if i < max_iterations - 1:
                logger.info("本次循环未成功，等待后继续下一次")
                print("⏳ 本次循环未成功，等待后继续下一次", flush=True)
                time.sleep(5)
        logger.error(f"达到最大循环次数 {max_iterations}，任务失败")
        print(f"❌ 达到最大循环次数 {max_iterations}，任务失败", flush=True)
        return False