"""
冒险岛自动打怪脚本 - 基础版
功能：固定区域左右移动 + 按键1、2释放技能
控制：F12 启动/停止，ESC 退出

使用步骤：
1. 先打开冒险岛，进入地图
2. 运行此脚本（保持命令行窗口打开）
3. 点击游戏窗口，让游戏处于前台
4. 按 F12 开始挂机
5. 再按 F12 暂停，ESC 退出脚本



import time
import threading
import random
from pynput import keyboard

# ==================== 配置区 ====================
# 移动按键（默认方向键）
KEY_LEFT = 'left'      # 左移键，可改为 'a'
KEY_RIGHT = 'right'    # 右移键，可改为 'd'
KEY_JUMP = 'alt'       # 跳跃键

# 技能按键
KEY_SKILL_1 = '1'      # 技能1
KEY_SKILL_2 = '2'      # 技能2

# 移动范围（来回走的次数，每次约0.3秒）
MOVE_STEPS = 8         # 单边移动步数

# 技能冷却时间（秒）—— 改成你实际的CD，支持范围随机
SKILL_1_CD_MIN = 5.0
SKILL_1_CD_MAX = 6.0

SKILL_2_CD_MIN = 5.0
SKILL_2_CD_MAX = 6.0

# 是否随机跳跃（防检测）
RANDOM_JUMP = True

# 是否随机发呆（模拟真人看屏幕）
RANDOM_IDLE = True
IDLE_CHANCE = 0.15       # 15%概率发呆
IDLE_MIN = 0.5           # 最短发呆时间
IDLE_MAX = 2.0           # 最长发呆时间
# ================================================

try:
    import pydirectinput
    pydirectinput.FAILSAFE = False
    USE_PYDIRECT = True
    print("使用 pydirectinput（推荐PC游戏）")
except ImportError:
    import pyautogui
    pyautogui.FAILSAFE = False
    USE_PYDIRECT = False
    print("pydirectinput 未安装，使用 pyautogui（兼容性较差）")
    print("建议安装：pip install pydirectinput")


running = False
stopped = False


def press_key(key, duration=0.05):
    """按下并释放一个键"""
    if USE_PYDIRECT:
        pydirectinput.keyDown(key)
        time.sleep(duration)
        pydirectinput.keyUp(key)
    else:
        pyautogui.keyDown(key)
        time.sleep(duration)
        pyautogui.keyUp(key)


def hold_key(key, duration):
    """按住一个键一段时间"""
    if USE_PYDIRECT:
        pydirectinput.keyDown(key)
        time.sleep(duration)
        pydirectinput.keyUp(key)
    else:
        pyautogui.keyDown(key)
        time.sleep(duration)
        pyautogui.keyUp(key)


def use_skill(skill_key):
    """释放技能"""
    press_key(skill_key, 0.1)
    print(f"释放技能 {skill_key}")


def move_left(steps=MOVE_STEPS):
    """向左移动"""
    hold_key(KEY_LEFT, steps * 0.3)


def move_right(steps=MOVE_STEPS):
    """向右移动"""
    hold_key(KEY_RIGHT, steps * 0.3)


def random_jump():
    """随机跳跃"""
    if RANDOM_JUMP and random.random() < 0.3:
        press_key(KEY_JUMP, 0.1)
        time.sleep(0.2)


def auto_combat():
    """自动打怪主循环"""
    global running

    last_skill_1 = 0
    last_skill_2 = 0
    next_skill_1_cd = random.uniform(SKILL_1_CD_MIN, SKILL_1_CD_MAX)
    next_skill_2_cd = random.uniform(SKILL_2_CD_MIN, SKILL_2_CD_MAX)
    direction = 1  # 1=右, -1=左

    print("\n=== 自动打怪已启动 ===")
    print("按 F12 暂停，ESC 退出\n")

    while running and not stopped:
        current_time = time.time()

        # 释放技能1（CD到了才按，不浪费按键）
        if current_time - last_skill_1 >= next_skill_1_cd:
            use_skill(KEY_SKILL_1)
            last_skill_1 = current_time
            next_skill_1_cd = random.uniform(SKILL_1_CD_MIN, SKILL_1_CD_MAX)

        # 释放技能2（CD到了才按，不浪费按键）
        if current_time - last_skill_2 >= next_skill_2_cd:
            use_skill(KEY_SKILL_2)
            last_skill_2 = current_time
            next_skill_2_cd = random.uniform(SKILL_2_CD_MIN, SKILL_2_CD_MAX)

        # 随机发呆（模拟真人看屏幕、思考）
        if RANDOM_IDLE and random.random() < IDLE_CHANCE:
            idle_time = random.uniform(IDLE_MIN, IDLE_MAX)
            print(f"发呆 {idle_time:.1f} 秒...")
            time.sleep(idle_time)
            continue

        # 左右移动
        if direction == 1:
            move_right()
        else:
            move_left()

        direction *= -1
        random_jump()

        # 小停顿，避免操作过快
        time.sleep(0.1 + random.random() * 0.2)

    print("\n=== 自动打怪已暂停 ===")


def on_press(key):
    global running, stopped

    try:
        if key == keyboard.Key.f12:
            if not running:
                running = True
                thread = threading.Thread(target=auto_combat, daemon=True)
                thread.start()
            else:
                running = False

        elif key == keyboard.Key.esc:
            running = False
            stopped = True
            print("\n脚本已退出")
            return False

    except Exception as e:
        print(f"错误: {e}")


if __name__ == "__main__":
    print("=" * 50)
    print("  冒险岛自动打怪脚本")
    print("=" * 50)
    print("\n请确保：")
    print("1. 冒险岛已打开，窗口在前台")
    print("2. 角色已站在平坦的地面上")
    print("3. 技能1、2已放在数字键1、2位置")
    print("\n操作：")
    print("  F12 - 开始/暂停")
    print("  ESC - 退出脚本")
    print("\n" + "=" * 50)

    if not USE_PYDIRECT:
        print("\n⚠️ 警告：未安装 pydirectinput")
        print("   pyautogui 在某些游戏中可能无效")
        print("   建议安装：pip install pydirectinput\n")

    with keyboard.Listener(on_press=on_press) as listener:
        listener.join()
