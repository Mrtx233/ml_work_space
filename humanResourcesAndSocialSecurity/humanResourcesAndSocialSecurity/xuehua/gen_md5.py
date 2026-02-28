import datetime
import time
import threading
from typing import TypedDict, Dict
from .source import options, generator


# 定义配置结构的 TypedDict
class Config(TypedDict):
    time_bits: int
    worker_id_bit_length: int
    seq_bit_length: int
    min_val: int
    max_val: int  # 明确声明 max_val 字段
    base_time: int | None
    warning_threshold: float
    diff: float

class RandomWorkerEachTimeSnowflake:
    def __init__(self, worker_id, logger):
        self.lock = threading.Lock()
        self.generated_ids = set()  # 单进程去重
        self.max_id_cache = 300000  # 限制缓存大小
        self.worker_id = worker_id  # 固定工作ID（从外部传入）
        self.logger = logger

        # 核心配置：工作ID位数统一为3位（1-7）
        self.configs: Dict[int, Config] = {
            11: {
                "time_bits": 33,  # 时间戳位数
                "worker_id_bit_length": 3,  # 统一3位工作ID（1-7）
                "seq_bit_length": 2,  # 序列号位数
                "min_val": 10 ** 10,
                "max_val": 10 ** 11 - 1,
                "base_time": None,
                "warning_threshold": 0.8,
                "diff": 0.10268425348
            },
            14: {
                "time_bits": 43,  # 时间戳位数
                "worker_id_bit_length": 3,  # 统一3位工作ID
                "seq_bit_length": 4,  # 序列号位数
                "min_val": 10 ** 13,
                "max_val": 10 ** 14 - 1,
                "base_time": 1648919058000,
                "warning_threshold": 0.8,
                "diff": 0.13674236417
            },
            15: {
                "time_bits": 48,  # 时间戳位数
                "worker_id_bit_length": 3,  # 统一3位工作ID
                "seq_bit_length": 5,  # 序列号位数
                "min_val": 10 ** 14,
                "max_val": 10 ** 15 - 1,
                "base_time": 1102071097000,
                "warning_threshold": 0.8,
                "diff": 0.16734156148
            }
        }

        # 验证工作ID有效性（3位工作ID范围：1-7）
        max_worker = (1 << 3) - 1  # 2^3-1=7
        if not (1 <= self.worker_id <= max_worker):
            raise ValueError(f"工作ID必须在1-{max_worker}之间（3位工作ID限制）")

    def get_cfg(self, target_length):
        cfg = self.configs[target_length]
        return cfg

    def _calculate_base_time(self, target_length):
        """计算并固定同一位数的基准时间"""
        cfg = self.configs[target_length]
        if cfg["base_time"] is not None:
            return cfg["base_time"]

        with self.lock:
            if cfg["base_time"] is None:
                now_ms = int(time.time() * 1000)
                shift_bits = cfg["worker_id_bit_length"] + cfg["seq_bit_length"]

                # 最大时间差受限于time_bits和max_val
                max_timestamp_diff = min(
                    (1 << cfg["time_bits"]) - 1,
                    cfg["max_val"] // (1 << shift_bits)
                )

                initial_diff = int(max_timestamp_diff * cfg["diff"])
                min_required_diff = cfg["min_val"] // (1 << shift_bits)
                initial_diff = max(initial_diff, min_required_diff, 1000)

                cfg["base_time"] = now_ms - initial_diff
                self.logger.info(f"{target_length}位基准时间固定为：{datetime.datetime.fromtimestamp(cfg['base_time'] / 1000)}")
                self.logger.info(f"预计寿命：约{max_timestamp_diff / 1000 / 3600 / 24:.1f}天")
        return cfg["base_time"]

    def _check_life_remaining(self, target_length, current_diff):
        """检查剩余寿命"""
        cfg = self.get_cfg(target_length)
        max_diff = min(
            (1 << cfg["time_bits"]) - 1,
            cfg["max_val"] // (1 << (cfg["worker_id_bit_length"] + cfg["seq_bit_length"]))
        )
        used_ratio = current_diff / max_diff
        if used_ratio >= cfg["warning_threshold"]:
            self.logger.warning(f"⚠️ 警告：{target_length}位ID已使用{used_ratio * 100:.1f}%寿命！")

    def generate(self, target_length):
        if target_length not in self.configs:
            raise ValueError(f"仅支持11/14/15位，当前请求：{target_length}")

        cfg = self.get_cfg(target_length)
        base_time = self._calculate_base_time(target_length)
        max_attempts = 500

        for attempt in range(max_attempts):
            with self.lock:
                try:
                    # 使用实例化时传入的固定工作ID（同一程序内不变）
                    worker_id = self.worker_id

                    opts = options.IdGeneratorOptions(
                        worker_id=worker_id,
                        worker_id_bit_length=cfg["worker_id_bit_length"],
                        seq_bit_length=cfg["seq_bit_length"],
                        base_time=base_time,
                    )
                    idgen = generator.DefaultIdGenerator()
                    idgen.set_id_generator(opts)

                    uid = idgen.next_id()
                    uid_str = str(uid)

                    # 校验长度和范围
                    if len(uid_str) != target_length:
                        continue
                    if not (cfg["min_val"] <= uid <= cfg["max_val"]):
                        continue

                    # 去重检查
                    if uid in self.generated_ids:
                        continue
                    self.generated_ids.add(uid)

                    # 限制缓存大小
                    if len(self.generated_ids) >= self.max_id_cache:
                        self.generated_ids = set(list(self.generated_ids)[self.max_id_cache // 2:])

                    # 检查寿命
                    ms_timestamp = int(time.time() * 1000)
                    current_diff = ms_timestamp - base_time
                    self._check_life_remaining(target_length, current_diff)

                    return uid
                except Exception as e:
                    if attempt % 200 == 0:
                        self.logger.error(f"尝试{attempt + 1}错误：{e}")

            time.sleep(0.001)

        raise RuntimeError(f"无法生成{target_length}位ID")


# 全局生成器实例（带工作ID参数）
_global_generator = None
_global_lock = threading.Lock()

def get_snowflake_id(target_length, worker_id, logger):
    global _global_generator
    # 双重检查锁（DCL）：先轻量判断，再加锁，避免频繁加锁影响性能
    if _global_generator is None:
        with _global_lock:  # 加锁确保初始化唯一
            if _global_generator is None:  # 再次检查（防止多线程重复初始化）
                _global_generator = RandomWorkerEachTimeSnowflake(worker_id, logger)
    # 此时 _global_generator 一定非 None，可安全访问属性
    if _global_generator.worker_id != worker_id:
        raise ValueError(f"当前程序已使用工作ID {_global_generator.worker_id}，不可切换为 {worker_id}")
    return str(_global_generator.generate(target_length))