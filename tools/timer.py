import time


class Timer:
    def __init__(self):
        self.start_times = {}

    def start(self, label):
        """
        开始计时
        :param label: 计时的标签，用于标识不同的计时任务
        """
        self.start_times[label] = time.time()

    def stop(self, label):
        """
        停止计时并返回耗时
        :param label: 计时的标签
        :return: 耗时（秒）
        """
        if label not in self.start_times:
            raise ValueError(f"计时器未启动标签: {label}")
        elapsed_time = time.time() - self.start_times[label]
        print(f"⏱️ [{label}] 耗时: {elapsed_time:.2f} 秒")
        del self.start_times[label]
        return elapsed_time