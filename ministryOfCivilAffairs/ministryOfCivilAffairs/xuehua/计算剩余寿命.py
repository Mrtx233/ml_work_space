import time


def calculate_remaining_lifespan(
        base_timestamp: int,  # 基准时间戳（毫秒级）
        target_length: int,  # 目标ID位数（如11/14/15）
        worker_id_bits: int,  # 工作ID位数
        seq_bits: int,  # 序列号位数
        time_bits: int | None = None  # 时间戳位数（可选，自动计算则传None）
) -> float:
    """
    计算雪花算法基准时间生成对应位数ID的剩余寿命（天）

    参数:
        base_timestamp: 基准时间戳（毫秒级）
        target_length: 目标ID的十进制位数
        worker_id_bits: 工作ID占用的位数
        seq_bits: 序列号占用的位数
        time_bits: 时间戳位数（可选，为None时自动计算）

    返回:
        剩余寿命（天），负数表示已过期
    """
    # 1. 计算目标位数的数值范围
    min_val = 10 ** (target_length - 1)  # 最小数值（如11位为10^10）
    max_val = (10 ** target_length) - 1  # 最大数值（如11位为10^11-1）

    # 2. 计算偏移总位数（工作ID + 序列号）
    shift_bits = worker_id_bits + seq_bits

    # 3. 计算最大允许的时间戳差值（受限于数值范围和时间戳位数）
    # 基于数值范围的最大时间戳差值
    max_diff_by_value = max_val // (1 << shift_bits)
    # 基于时间戳位数的最大时间戳差值（若指定）
    if time_bits is not None:
        max_diff_by_bits = (1 << time_bits) - 1
        max_timestamp_diff = min(max_diff_by_value, max_diff_by_bits)
    else:
        max_timestamp_diff = max_diff_by_value

    # 4. 计算当前时间戳与基准时间的差值
    current_ms = int(time.time() * 1000)
    current_diff = current_ms - base_timestamp

    # 5. 计算剩余寿命（天）
    remaining_diff = max_timestamp_diff - current_diff
    remaining_days = remaining_diff / 1000 / 3600 / 24  # 转换为天

    # 补充信息输出
    print(f"=== 寿命计算结果 ===")
    print(f"目标位数: {target_length}位 (数值范围: {min_val} ~ {max_val})")
    print(f"结构分配: 时间戳位数={time_bits or '自动'} + 工作ID位数={worker_id_bits} + 序列号位数={seq_bits}")
    print(f"基准时间戳: {base_timestamp} (毫秒)")
    print(f"当前时间戳差值: {current_diff} 毫秒")
    print(f"最大允许差值: {max_timestamp_diff} 毫秒")
    print(f"剩余寿命: {remaining_days:.2f} 天 ({'已过期' if remaining_days < 0 else '正常'})")

    return remaining_days


# 示例用法
if __name__ == "__main__":
    # 示例1: 11位ID，基准时间2025-08-11 16:25:57.162（毫秒级时间戳）
    base_ts_11 = 1755427352000  # 2025-08-11 16:25:57.162的毫秒级时间戳
    calculate_remaining_lifespan(
        base_timestamp=base_ts_11,
        target_length=11,
        worker_id_bits=2,
        seq_bits=3,
        time_bits=33
    )

    # 示例2: 14位ID，基准时间2025-07-04 23:19:30.835
    base_ts_14 = 1719979170835  # 2025-07-04 23:19:30.835的毫秒级时间戳
    calculate_remaining_lifespan(
        base_timestamp=base_ts_14,
        target_length=14,
        worker_id_bits=3,
        seq_bits=4,
        time_bits=43
    )

    # 示例3: 15位ID，基准时间2025-04-16 09:31:54.488
    base_ts_15 = 1713200514488  # 2025-04-16 09:31:54.488的毫秒级时间戳
    calculate_remaining_lifespan(
        base_timestamp=base_ts_15,
        target_length=15,
        worker_id_bits=4,
        seq_bits=5,
        time_bits=48
    )