#!/usr/bin/env python3
"""主题内容文件：TRAE宝摸鱼日常（16 个屏幕模式 + 10 件主题道具）。

屏幕一律 70×36 逻辑面板；t 为循环进度，t=0 即静态帧。
红/黄/蓝只在 scenes.json design.discipline 登记的幕出现。
"""
from PIL import Image, ImageDraw

from lib_base import (C, latin, cn_text, panel, osc, blink, outlined, shape,
                      Z_BIG, eyes_default, eyes_happy, eyes_star,
                      eyes_power, sparkle)


# =====================================================================
# 屏幕表情：70×36，一幕一屏
# =====================================================================

FISH_ROWS = [
    '....####....',
    '.#.######...',
    '###.#######.',
    '###########.',
    '###.#######.',
    '.#.######...',
    '....####....',
]


def fish_icon(fill='mint', scale=1):
    im = shape(FISH_ROWS, fill)
    d = ImageDraw.Draw(im)
    d.point((9, 3), fill=C['ink'])
    if scale != 1:
        im = im.resize((im.width*scale, im.height*scale), Image.Resampling.NEAREST)
    return im


def eyes_sleepy(d, cy=20):
    """半闭的困倦眼：上眼皮压暗，只留一条发光的缝。"""
    for cx in (22, 47):
        d.rectangle((cx-6, cy-3, cx+6, cy-3), fill=C['shadow'])
        d.rectangle((cx-6, cy-1, cx+6, cy), fill=C['mint'])
        d.rectangle((cx-4, cy+1, cx+4, cy+1), fill=C['mint'])


def scr_monday(t=0.0):
    """01 上班如上坟：9AM 在屏幕上发灰，眼皮抬不起来。"""
    im = panel(); d = ImageDraw.Draw(im)
    im.alpha_composite(latin('9AM', 'white', 2), (7, 2+round(osc(t, 2, 1))))
    eyes_sleepy(d, 25)
    if blink(t, 3, 0.35):
        d.rectangle((6, 31, 12, 31), fill=C['shadow'])
    return im


def scr_slack_start(t=0.0):
    """02 摸鱼启动：小鱼在屏幕上巡游，眼睛弯成月牙。"""
    im = panel(); d = ImageDraw.Draw(im)
    im.alpha_composite(fish_icon('green'), (20+round(osc(t, 1, 14)), 2+round(osc(t, 2, 1))))
    eyes_happy(d, 17)
    text = cn_text('摸鱼', 'green')
    im.alpha_composite(text, ((70-text.width)//2, 21))
    return im


def scr_busy(t=0.0):
    """03 假装很忙：WORKING 顶栏 + 来回扫的进度条。"""
    im = panel(); d = ImageDraw.Draw(im)
    im.alpha_composite(latin('WORKING', 'white'), (14, 2))
    eyes_default(im, d, t, 17, fast=True)
    d.rectangle((10, 25, 59, 32), outline=C['white'])
    x = 12 + round((osc(t, 2, 1)+1)/2*40)
    d.rectangle((x, 27, x+5, 30), fill=C['green'])
    if blink(t, 4, 0.5):
        d.rectangle((57, 27, 57, 30), fill=C['mint'])
    return im


def scr_coffee(t=0.0):
    """04 咖啡续命：COFFEE 加冒着热气的杯子，半闭眼回魂。"""
    im = panel(); d = ImageDraw.Draw(im)
    im.alpha_composite(latin('COFFEE', 'green'), (17, 2+round(osc(t, 4, 1))))
    eyes_sleepy(d, 17)
    d.rectangle((29, 23, 40, 32), outline=C['white'])
    d.rectangle((30, 24, 39, 25), fill=C['green'])
    d.rectangle((41, 25, 42, 28), outline=C['white'])
    for i, x in enumerate((32, 35, 38)):
        y = 18-(i % 2)+round(osc(t, 2+i % 2, 1))
        d.rectangle((x, y, x, y+2), fill=C['mint'])
    return im


def scr_pretend(t=0.0):
    """05 老板来了：一秒切到 PPT 99%，进度条来回装忙。"""
    im = panel(); d = ImageDraw.Draw(im)
    im.alpha_composite(latin('PPT', 'white', 2), (4, 2))
    im.alpha_composite(latin('99%', 'green'), (45, 3))
    d.rectangle((6, 20, 63, 27), outline=C['white'])
    x = 8 + round((osc(t, 2, 1)+1)/2*47)
    d.rectangle((x, 22, x+7, 25), fill=C['green'])
    for y in (31, 33):
        if blink(t, 2, 0.6):
            d.rectangle((6, y, 63, y), fill=C['shadow'])
    return im


def scr_sneak(t=0.0):
    """06 桌下偷看：瞳孔左右乱瞟，嘴角压着三个点。"""
    im = panel(); d = ImageDraw.Draw(im)
    dx = round(osc(t, 1, 2))
    for cx in (22, 47):
        d.rectangle((cx-6, 13, cx+5, 19), fill=C['white'])
        d.rectangle((cx-2+dx, 15, cx-1+dx, 17), fill=C['ink'])
    if blink(t, 2, 0.5):
        d.rectangle((14, 9, 19, 9), fill=C['mint'])
        d.rectangle((44, 9, 49, 9), fill=C['mint'])
    dots = latin('...', 'shadow')
    im.alpha_composite(dots, ((70-dots.width)//2, 27))
    if blink(t, 3, 0.5):
        d.rectangle((58, 22, 59, 23), fill=C['green'])
    return im


def scr_buddy(t=0.0):
    """07 摸鱼搭子：两条鱼对游，击掌处冒星花。"""
    im = panel(); d = ImageDraw.Draw(im)
    im.alpha_composite(fish_icon('mint'), (4+round(osc(t, 1, 3)), 2))
    im.alpha_composite(fish_icon('green'), (38+round(osc(t, 1, -3)), 8))
    eyes_happy(d, 29)
    sparkle(d, 34, 23, t, 3, 0.8)
    return im


def scr_toilet(t=0.0):
    """08 带薪如厕：15MIN 计时 + 漏沙的沙漏。"""
    im = panel(); d = ImageDraw.Draw(im)
    im.alpha_composite(latin('15MIN', 'white', 2), (5, 2))
    eyes_happy(d, 24)
    d.rectangle((58, 18, 67, 19), fill=C['white'])
    d.rectangle((58, 30, 67, 31), fill=C['white'])
    for i in range(3):
        d.rectangle((60+i, 20+i, 65-i, 20+i), fill=C['mint'])
        d.rectangle((60+i, 29-i, 65-i, 29-i), fill=C['mint'])
    y = 22+round(osc(t, 2, 1))
    d.rectangle((62, y, 63, y+1), fill=C['green'])
    return im


def scr_red99(t=0.0):
    """09 消息 99+：红字抖动 + 红点角标 + 瞪圆的眼睛。"""
    im = panel(); d = ImageDraw.Draw(im)
    dx = round(osc(t, 8, 1))
    im.alpha_composite(latin('99+', 'red', 2), (6+dx, 3))
    d.ellipse((55, 3, 64, 12), fill=C['red'])
    d.rectangle((59, 5, 60, 8), fill=C['white'])
    d.rectangle((59, 10, 60, 10), fill=C['white'])
    for cx in (22, 47):
        d.ellipse((cx-5, 19, cx+5, 29), fill=C['white'])
        d.rectangle((cx-1, 23, cx+1, 25), fill=C['ink'])
    if blink(t, 4, 0.5):
        d.rectangle((6, 33, 64, 33), fill=C['red'])
    return im


def scr_overload(t=0.0):
    """10 临时加活：OT/加班 与越堆越高的纸页。"""
    im = panel(); d = ImageDraw.Draw(im)
    im.alpha_composite(latin('OT', 'mint', 2), (5, 3))
    text = cn_text('加班', 'white')
    im.alpha_composite(text, (36, 3))
    eyes_sleepy(d, 25)
    for i in range(3):
        if blink(t, 2, 0.65, i*0.12):
            y = 31+i
            d.rectangle((6+i*3, y, 40+i*3, y), fill=C['white'] if i % 2 else C['paper'])
    return im


def scr_dead(t=0.0):
    """11 战术装死：404 + 单眼熄灭 + 缓慢扫过的扫描线。"""
    im = panel(); d = ImageDraw.Draw(im)
    im.alpha_composite(latin('404', 'white', 2), (7, 3))
    eyes_power(d, 25)
    y = 32+round(osc(t, 2, 1))
    d.rectangle((4, y, 65, y), fill=C['shadow'])
    for yy in (20, 22):
        if blink(t, 5, 0.4):
            d.rectangle((4, yy, 65, yy), fill=C['shadow'])
    return im


def scr_caught(t=0.0):
    """12 当场抓获：ERR0R 花屏与红色噪点行。"""
    im = panel(); d = ImageDraw.Draw(im)
    dx = round(osc(t, 6, 1))
    im.alpha_composite(latin('ERR0R', 'red'), (19+dx, 3))
    if blink(t, 6, 0.5):
        im.alpha_composite(latin('ERR0R', 'green'), (21+dx, 5))
    eyes_default(im, d, t, 22, fast=True)
    for i in range(3):
        if blink(t, 5, 0.55, i*0.1):
            y = 11+i*2
            d.rectangle((4, y, 10+i*6, y), fill=C['red'] if i % 2 else C['shadow'])
    for x, y in ((12, 31), (58, 33)):
        if blink(t, 4, 0.5):
            d.rectangle((x, y, x+1, y+1), fill=C['red'])
    return im


def scr_offwork(t=0.0):
    """13 准点开溜：6PM 亮起，星星眼与速度线。"""
    im = panel(); d = ImageDraw.Draw(im)
    im.alpha_composite(latin('6PM', 'green', 2), (7, 3))
    eyes_star(im, d, t, 26)
    for i in range(3):
        if blink(t, 4, 0.5, i*0.15):
            y = 32-i
            d.rectangle((44+i*6, y, 52+i*6, y), fill=C['white'])
    return im


def scr_tgif(t=0.0):
    """14 周五万岁：TGIF + 星星眼 + 四角星花。"""
    im = panel(); d = ImageDraw.Draw(im)
    im.alpha_composite(latin('TGIF', 'white', 2), (12, 2))
    eyes_star(im, d, t, 26)
    sparkle(d, 7, 22, t, 3); sparkle(d, 63, 8, t, 2); sparkle(d, 62, 30, t, 4, 0.6)
    return im


def scr_chill(t=0.0):
    """15 带薪摸鱼：眯眼笑，小鱼在屏幕底部游过。"""
    im = panel(); d = ImageDraw.Draw(im)
    eyes_happy(d, 15)
    im.alpha_composite(fish_icon('mint'), (30+round(osc(t, 1, 18)), 22+round(osc(t, 2, 1))))
    if blink(t, 3, 0.5):
        d.rectangle((55, 28, 56, 29), fill=C['white'])
    if blink(t, 3, 0.5, 0.4):
        d.rectangle((49, 32, 50, 33), fill=C['mint'])
    return im


def scr_dream_fish(t=0.0):
    """16 梦里摸鱼：闭眼、zZ 与一条半透明的梦中之鱼。"""
    im = panel(); d = ImageDraw.Draw(im)
    eyes_happy(d, 16)
    im.alpha_composite(shape(Z_BIG, 'mint'), (50, 2+round(osc(t, 1, -2))))
    ghost = fish_icon('shadow').resize((10, 7), Image.Resampling.NEAREST)
    im.alpha_composite(ghost, (8, 23+round(osc(t, 2, 2))))
    sparkle(d, 62, 28, t, 3, 0.6)
    return im


SCREENS = [
    ('monday', '上班如上坟', '9AM、半闭眼与垂下的嘴角线', ('white', 'shadow'), scr_monday),
    ('slack_start', '摸鱼启动', '小鱼巡游与眯眼笑', ('green', 'white'), scr_slack_start),
    ('busy', '假装很忙', 'WORKING 与来回扫的进度条', ('white', 'green', 'mint'), scr_busy),
    ('coffee', '咖啡续命', 'COFFEE、热气与半闭眼', ('green', 'white', 'mint'), scr_coffee),
    ('pretend', '老板来了', 'PPT 99% 进度条', ('white', 'green', 'shadow'), scr_pretend),
    ('sneak', '桌下偷看', '瞳孔左右乱瞟与 ...', ('white', 'mint', 'green'), scr_sneak),
    ('buddy', '摸鱼搭子', '双鱼对游与击掌星花', ('mint', 'green', 'white'), scr_buddy),
    ('toilet', '带薪如厕', '15MIN 计时与漏沙沙漏', ('white', 'mint', 'green'), scr_toilet),
    ('red99', '消息 99+', '红字抖动、红点角标与瞪眼', ('red', 'white'), scr_red99),
    ('overload', '临时加活', 'OT/加班 与越堆越高的纸页', ('mint', 'white', 'paper'), scr_overload),
    ('dead', '战术装死', '404、单眼熄灭与扫描线', ('white', 'shadow'), scr_dead),
    ('caught', '当场抓获', 'ERR0R 花屏与红色噪点', ('red', 'green', 'shadow'), scr_caught),
    ('offwork', '准点开溜', '6PM、星星眼与速度线', ('green', 'white'), scr_offwork),
    ('tgif', '周五万岁', 'TGIF、星星眼与星花', ('white', 'green'), scr_tgif),
    ('chill', '带薪摸鱼', '眯眼笑与小鱼的底游', ('mint', 'white', 'green'), scr_chill),
    ('dream_fish', '梦里摸鱼', '闭眼、zZ 与梦中之鱼', ('mint', 'shadow', 'white'), scr_dream_fish),
]

SCREEN_MODES = {item[0] for item in SCREENS}


def screen_image(mode, t=0.0):
    if mode not in SCREEN_MODES:
        raise ValueError(f'未知屏幕模式：{mode}')
    for item_id, _, _, _, fn in SCREENS:
        if item_id == mode:
            return fn(t)
    raise ValueError(mode)


# =====================================================================
# 主题道具：原生整数像素 + 1px 墨黑轮廓
# =====================================================================

def make_fish():
    im = fish_icon('mint')
    d = ImageDraw.Draw(im)
    d.rectangle((5, 5, 9, 5), fill=C['green'])
    return im


def make_keyboard():
    mask = Image.new('L', (24, 9), 0)
    ImageDraw.Draw(mask).rectangle((0, 0, 23, 8), fill=255)
    im = outlined(mask, 'shadow')
    d = ImageDraw.Draw(im)
    d.rectangle((2, 2, 21, 2), fill=C['shell'])
    for row in (3, 5):
        for col in range(5):
            x = 2+col*4
            d.rectangle((x, row, x+2, row+1), fill=C['white'])
    d.rectangle((7, 7, 16, 7), fill=C['mint'])
    d.rectangle((20, 3, 20, 3), fill=C['green'])
    return im


def make_coffee():
    mask = Image.new('L', (13, 14), 0); d = ImageDraw.Draw(mask)
    d.rectangle((1, 4, 9, 12), fill=255)
    d.rectangle((2, 3, 8, 4), fill=255)
    d.rectangle((10, 6, 11, 9), fill=255)
    im = outlined(mask, 'white')
    d = ImageDraw.Draw(im)
    d.rectangle((2, 5, 10, 6), fill=C['green'])
    d.rectangle((2, 11, 10, 12), fill=C['shadow'])
    d.rectangle((3, 8, 4, 9), fill=C['mint'])
    return im


def make_phone():
    mask = Image.new('L', (13, 24), 0)
    ImageDraw.Draw(mask).rectangle((0, 0, 12, 23), fill=255)
    im = outlined(mask, 'shell')
    d = ImageDraw.Draw(im)
    d.rectangle((3, 4, 11, 18), fill=C['blue'])
    d.rectangle((4, 5, 10, 5), fill=C['green'])
    d.rectangle((4, 8, 8, 8), fill=C['mint'])
    d.rectangle((5, 2, 9, 2), fill=C['shadow'])
    d.rectangle((5, 21, 9, 21), fill=C['shadow'])
    return im


def make_file_stack():
    sheet = Image.new('L', (18, 22), 0)
    ImageDraw.Draw(sheet).rectangle((0, 0, 17, 21), fill=255)
    stack = Image.new('RGBA', (24, 26), (0, 0, 0, 0))
    for x, y in ((0, 4), (2, 2), (4, 0)):
        stack.alpha_composite(outlined(sheet, 'paper'), (x, y))
    d = ImageDraw.Draw(stack)
    for row in (8, 11, 14, 17):
        d.rectangle((7, row, 19, row), fill=C['shadow'])
    d.rectangle((7, 5, 12, 5), fill=C['green'])
    return stack


def make_clock():
    mask = Image.new('L', (13, 13), 0)
    ImageDraw.Draw(mask).ellipse((0, 0, 12, 12), fill=255)
    im = outlined(mask, 'white')
    d = ImageDraw.Draw(im)
    d.rectangle((7, 7, 7, 11), fill=C['ink'])
    d.rectangle((7, 2, 7, 6), fill=C['green'])
    d.rectangle((6, 7, 8, 8), fill=C['ink'])
    d.rectangle((2, 6, 2, 8), fill=C['shadow'])
    d.rectangle((12, 6, 12, 8), fill=C['shadow'])
    return im


def make_badge():
    mask = Image.new('L', (12, 18), 0); d = ImageDraw.Draw(mask)
    d.rectangle((1, 5, 10, 17), fill=255)
    d.rectangle((4, 0, 7, 4), fill=255)
    im = outlined(mask, 'white')
    d = ImageDraw.Draw(im)
    d.rectangle((3, 8, 5, 9), fill=C['shadow'])
    d.rectangle((3, 11, 8, 11), fill=C['shadow'])
    d.rectangle((3, 13, 7, 13), fill=C['shadow'])
    d.rectangle((3, 2, 4, 2), fill=C['green'])
    return im


def make_red_dot():
    mask = Image.new('L', (11, 12), 0); d = ImageDraw.Draw(mask)
    d.ellipse((0, 0, 10, 10), fill=255)
    d.polygon([(3, 9), (5, 11), (6, 9)], fill=255)
    im = outlined(mask, 'red')
    d = ImageDraw.Draw(im)
    d.rectangle((5, 3, 6, 6), fill=C['white'])
    d.rectangle((5, 8, 6, 8), fill=C['white'])
    return im


def make_toilet_paper():
    mask = Image.new('L', (10, 14), 0); d = ImageDraw.Draw(mask)
    d.rectangle((0, 0, 9, 7), fill=255)
    d.rectangle((7, 8, 9, 13), fill=255)
    im = outlined(mask, 'white')
    d = ImageDraw.Draw(im)
    d.rectangle((3, 2, 5, 5), fill=C['shadow'])
    d.rectangle((2, 1, 6, 1), fill=C['paper'])
    d.rectangle((8, 9, 8, 12), fill=C['paper'])
    return im


def make_fish_bowl():
    mask = Image.new('L', (22, 20), 0); d = ImageDraw.Draw(mask)
    d.rectangle((1, 2, 20, 3), fill=255)
    d.polygon([(3, 4), (18, 4), (16, 18), (5, 18)], fill=255)
    im = outlined(mask, 'white')
    d = ImageDraw.Draw(im)
    d.rectangle((4, 5, 18, 5), fill=C['shadow'])
    d.polygon([(4, 9), (18, 9), (16, 17), (6, 17)], fill=C['mint'])
    fish = shape(FISH_ROWS, 'green').resize((7, 5), Image.Resampling.NEAREST)
    im.alpha_composite(fish, (7, 10))
    d.rectangle((15, 12, 16, 12), fill=C['white'])
    d.rectangle((13, 14, 13, 15), fill=C['white'])
    return im


NEW_PROPS = [
    ('fish', make_fish, '像素小鱼', '摸鱼主题的核心提示物'),
    ('keyboard', make_keyboard, '像素键盘', '假装很忙的敲击对象'),
    ('coffee', make_coffee, '像素咖啡杯', '续命用的绿杯'),
    ('phone', make_phone, '像素手机', '桌下偷看与消息 99+'),
    ('file_stack', make_file_stack, '文件堆', '临时加活压上头顶'),
    ('clock', make_clock, '像素手表', '抬腕看 6PM'),
    ('badge', make_badge, '像素工牌', '挂在胸前的打工人身份'),
    ('red_dot', make_red_dot, '红点气泡', '99+ 的红色角标'),
    ('toilet_paper', make_toilet_paper, '像素卷纸', '带薪如厕的通行证'),
    ('fish_bowl', make_fish_bowl, '像素鱼缸', '桌角的摸鱼观赏位'),
]
