"""
Sample Dimension Simulator
============================
1. 生成15个随机数（范围149.60~150.00），每3个一列，列内偏差≤0.20（±0.10）
   每列取中位值，5个中位值求平均，修约到0.2
2. 基于第1组每数 +0.15~0.25 生成第2组，同样计算

Usage:
    python random_median.py
    python random_median.py --seed 42
"""

import random
import argparse


def round_to(val: float, step: float = 0.2) -> float:
    return round(val / step) * step


def gen_group1(r1l: float, r1h: float, center_hi: float | None = None) -> list[float]:
    """Generate 15 numbers in [r1l, r1h].
    5 groups of 3; each group's max-min <= 0.20 (±0.10).
    center_hi can narrow the upper bound of center selection to bias lower."""
    nums = []
    margin = 0.10  # half the max allowed deviation (0.20)
    c_lo = max(r1l + margin, r1l)
    c_hi_default = min(r1h - margin, r1h)
    if center_hi is not None:
        c_hi_default = min(c_hi_default, center_hi)
    if c_lo > c_hi_default:
        c_hi_default = c_lo
    for _ in range(5):
        center = random.uniform(c_lo, c_hi_default)
        for _ in range(3):
            n = center + (random.random() - 0.5) * 2 * margin
            n = max(r1l, min(r1h, n))
            nums.append(round(n, 2))
    return nums


def gen_group2(nums1: list[float], offl: float, offh: float) -> list[float]:
    """Generate 15 numbers by adding random(offl, offh) to each of nums1."""
    return [round(x + random.uniform(offl, offh), 2) for x in nums1]


def medians(nums: list[float], group_size: int = 3) -> list[float]:
    """Pure median: sorted middle element of each group."""
    m = []
    for i in range(0, len(nums), group_size):
        chunk = sorted(nums[i:i + group_size])
        if len(chunk) < group_size:
            break
        m.append(chunk[len(chunk) // 2])
    return m


def max_deviation_in_groups(nums: list[float], group_size: int = 3) -> list[float]:
    """Return max-min deviation for each group."""
    devs = []
    for i in range(0, len(nums), group_size):
        chunk = nums[i:i + group_size]
        if len(chunk) < group_size:
            break
        devs.append(round(max(chunk) - min(chunk), 2))
    return devs


def print_table(nums: list[float], meds: list[float], group_size: int = 3):
    devs = max_deviation_in_groups(nums, group_size)
    for i in range(0, len(nums), group_size):
        chunk = nums[i:i + group_size]
        if len(chunk) < group_size:
            break
        j = i // group_size
        cols = "  ".join(f"{x:>7.2f}" for x in chunk)
        print(f"Col{j + 1}:  {cols}  ->  Median: {meds[j]:.2f}  (偏差: {devs[j]:.2f})")


def main():
    parser = argparse.ArgumentParser(description="Sample Dimension Simulator")
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--range1", nargs=2, type=float,
                        default=[149.60, 150.00], metavar=("LOW", "HIGH"))
    parser.add_argument("--offset", nargs=2, type=float,
                        default=[0.15, 0.25], metavar=("LOW", "HIGH"))
    parser.add_argument("--round-step", type=float, default=0.2)
    parser.add_argument("--count", type=int, default=15)
    parser.add_argument("--group-size", type=int, default=3)
    args = parser.parse_args()

    if args.seed is not None:
        random.seed(args.seed)

    step = args.round_step
    n = args.count
    gs = args.group_size
    r1l, r1h = args.range1
    offl, offh = args.offset

    prev_avg1 = None

    # ── Generate both groups, avoid boring .0 averages ──
    # Progressively narrow center range to bias Group 1 lower → Group 2 away from 150.0
    center_hi = None
    for attempt in range(100):
        nums1 = gen_group1(r1l, r1h, center_hi)
        meds1 = medians(nums1, gs)
        avg1 = round_to(sum(meds1) / len(meds1), step)

        nums2 = gen_group2(nums1, offl, offh)
        meds2 = medians(nums2, gs)
        avg2 = round_to(sum(meds2) / len(meds2), step)

        spread1 = max(meds1) - min(meds1)
        spread2 = max(meds2) - min(meds2)
        spread_ok = spread1 <= 0.10 and spread2 <= 0.10

        boring = abs(avg1 % 1.0) < 0.01 or abs(avg2 % 1.0) < 0.01
        changed = avg1 != prev_avg1 or avg2 != prev_avg2
        if changed and not boring and spread_ok:
            break
        # narrow center range to bias Group 1 lower → Group 2 away from 150.0
        if boring or not spread_ok:
            if center_hi is None:
                center_hi = r1h - 0.12  # start slightly below default max (149.88)
            else:
                center_hi -= 0.01

    print("=" * 60)
    print(f"Group 2: original + [{offl:.2f}, {offh:.2f}]")
    print("=" * 60)
    print_table(nums2, meds2, gs)
    print(f"Average of {len(meds2)} medians: {sum(meds2)/len(meds2):.4f} -> Rounded({step}): {avg2:.1f}")
    print()

    print("=" * 60)
    print("Summary")
    print("=" * 60)
    print(f"Group 1 medians: {[f'{m:.2f}' for m in meds1]} -> avg = {avg1:.1f}")
    print(f"Group 2 medians: {[f'{m:.2f}' for m in meds2]} -> avg = {avg2:.1f}")


if __name__ == "__main__":
    main()
