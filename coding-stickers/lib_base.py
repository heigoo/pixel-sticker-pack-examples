#!/usr/bin/env python3
"""像素表情包共享原语库（模板基础件，新主题不要修改本文件）。

包含：10 色固定调色板、5×7 拉丁字模、中文字模栅格化、70×36 屏幕面板、
循环安全动画原语（osc/blink，t=0 归零保证循环无跳变）、
描边像素图形工具（outlined/shape/polygon_im）与屏幕眼睛原语。
主题内容（屏幕表情/道具）写在 theme.py，从本文件导入这些原语。
"""
import math
from functools import lru_cache
from PIL import Image, ImageDraw, ImageFilter, ImageFont

from rig import find_font

C = {'ink': '#101313', 'shell': '#2B3031', 'shadow': '#454E50', 'white': '#FFFFFF',
     'paper': '#EEF3EE', 'green': '#5ADB97', 'mint': '#A9E6CC', 'gold': '#F4CD70',
     'red': '#EC6269', 'blue': '#316BCA'}

GLYPHS = {
'0':['01110','10001','10011','10101','11001','10001','01110'],
'1':['00100','01100','00100','00100','00100','00100','01110'],
'2':['01110','10001','00001','00010','00100','01000','11111'],
'3':['11110','00001','00001','01110','00001','00001','11110'],
'4':['00010','00110','01010','10010','11111','00010','00010'],
'5':['11111','10000','10000','11110','00001','00001','11110'],
'6':['01110','10000','10000','11110','10001','10001','01110'],
'7':['11111','00001','00010','00100','01000','01000','01000'],
'8':['01110','10001','10001','01110','10001','10001','01110'],
'9':['01110','10001','10001','01111','00001','00001','01110'],
'A':['01110','10001','10001','11111','10001','10001','10001'],
'B':['11110','10001','10001','11110','10001','10001','11110'],
'C':['01110','10001','10000','10000','10000','10001','01110'],
'D':['11110','10001','10001','10001','10001','10001','11110'],
'E':['11111','10000','10000','11110','10000','10000','11111'],
'F':['11111','10000','10000','11110','10000','10000','10000'],
'G':['01110','10001','10000','10011','10001','10001','01110'],
'H':['10001','10001','10001','11111','10001','10001','10001'],
'I':['01110','00100','00100','00100','00100','00100','01110'],
'K':['10001','10010','10100','11000','10100','10010','10001'],
'L':['10000','10000','10000','10000','10000','10000','11111'],
'M':['10001','11011','10101','10101','10001','10001','10001'],
'N':['10001','11001','10101','10011','10001','10001','10001'],
'O':['01110','10001','10001','10001','10001','10001','01110'],
'P':['11110','10001','10001','11110','10000','10000','10000'],
'R':['11110','10001','10001','11110','10100','10010','10001'],
'S':['01111','10000','10000','01110','00001','00001','11110'],
'T':['11111','00100','00100','00100','00100','00100','00100'],
'U':['10001','10001','10001','10001','10001','10001','01110'],
'W':['10001','10001','10001','10101','10101','11011','10001'],
'X':['10001','10001','01010','00100','01010','10001','10001'],
'Y':['10001','10001','01010','00100','00100','00100','00100'],
'Z':['11111','00010','00100','01000','11111'],
'+':['00000','00100','00100','11111','00100','00100','00000'],
'.':['00000','00000','00000','00000','00000','00110','00110'],
'%':['11001','11010','00010','00100','01000','01011','10011'],
'-':['00000','00000','00000','11111','00000','00000','00000'],
'=':['00000','00000','11111','00000','11111','00000','00000'],
'!':['00100','00100','00100','00100','00100','00000','00100'],
'?':['01110','10001','00001','00010','00100','00000','00100'],
' ':['00000']*7,
}


def latin(text, color='green', scale=1):
    """拉丁/数字 → 5×7 点阵像素图；字符必须都在 GLYPHS 内。"""
    im = Image.new('RGBA', (max(1, len(text)*6-1), 7), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    for i, char in enumerate(text):
        if char not in GLYPHS:
            raise ValueError(f'字模缺少字符：{char}（中文请用 cn_text）')
        for y, row in enumerate(GLYPHS[char]):
            for x, value in enumerate(row):
                if value == '1':
                    d.point((i*6+x, y), fill=C[color])
    return im.resize((im.width*scale, im.height*scale), Image.Resampling.NEAREST)


@lru_cache(maxsize=8)
def _cn_mask(text):
    """中文 → 1-bit 像素字模（程序排版，禁止手绘/生成模型画字）。"""
    font = ImageFont.truetype(str(find_font()), size=64)
    mask = Image.new('L', (80*len(text), 96), 0)
    ImageDraw.Draw(mask).text((4, 4), text, font=font, fill=255)
    box = mask.getbbox()
    if not box:
        raise ValueError(f'中文栅格化失败：{text}')
    mask = mask.crop(box).point(lambda p: 255 if p > 140 else 0)
    height = 13
    width = max(1, round(mask.width*height/mask.height))
    return mask.resize((width, height), Image.Resampling.NEAREST)


def cn_text(text, color='green'):
    return outlined(_cn_mask(text), color)


def panel(color='ink'):
    """70×36 屏幕面板（头部屏幕区的逻辑尺寸，3× 嵌入头部）。"""
    return Image.new('RGBA', (70, 36), C[color])


def osc(t, freq=1, amp=1, phase=0.0):
    """t=0 归零的循环振荡偏移：静态帧与循环首尾都不跳变。"""
    return amp*(math.sin(2*math.pi*(freq*t+phase)) - math.sin(2*math.pi*phase))


def blink(t, freq=1, duty=0.6, phase=0.0):
    """t=0 点亮的循环闪烁。"""
    return ((t*freq+phase) % 1.0) < duty


def outlined(mask, fill):
    """任意 L 蒙版 → 四周留白 1px、带墨黑轮廓的透明像素图。"""
    big = mask.filter(ImageFilter.MaxFilter(3))
    w, h = mask.size
    im = Image.new('RGBA', (w+2, h+2), (0, 0, 0, 0))
    ink_alpha = Image.new('L', im.size, 0); ink_alpha.paste(big, (1, 1))
    ink = Image.new('RGBA', im.size, C['ink']); ink.putalpha(ink_alpha)
    col_alpha = Image.new('L', im.size, 0); col_alpha.paste(mask, (1, 1))
    col = Image.new('RGBA', im.size, C[fill]); col.putalpha(col_alpha)
    im.alpha_composite(ink); im.alpha_composite(col)
    return im


def shape(rows, fill):
    """ASCII 图案 → 带轮廓像素图；'.' 与空格为透明，其余为填充。"""
    h = len(rows); w = max(len(r) for r in rows)
    mask = Image.new('L', (w, h), 0); d = ImageDraw.Draw(mask)
    for y, row in enumerate(rows):
        for x, ch in enumerate(row):
            if ch not in '. ':
                d.point((x, y), fill=255)
    return outlined(mask, fill)


def polygon_im(size, pts, fill):
    mask = Image.new('L', size, 0)
    ImageDraw.Draw(mask).polygon(pts, fill=255)
    return outlined(mask, fill)


# ---- 常用图案行 ----
HEART = [
'.###...###.',
'####w######',
'###########',
'###########',
'###########',
'.#########.',
'..#######..',
'...#####...',
'.....#.....',
]

Z_BIG = [
'#####',
'...##',
'..##.',
'.##..',
'#####',
]

STAR = [
'...#...',
'..###..',
'#######',
'..###..',
'...#...',
]


# ---- 屏幕眼睛原语：画在 70×36 面板上，眼位 cx=22/47 ----

def eye_diamond(d, cx, cy, r, color='green'):
    for dy in range(-r, r+1):
        w = r-abs(dy)
        d.rectangle((cx-w, cy+dy, cx+w, cy+dy), fill=C[color])
    d.rectangle((cx-r+1, cy-r+1, cx-r+2, cy-r+2), fill=C['white'])


def eyes_default(im, d, t, cy=19, fast=False):
    if blink(t, 3 if fast else 1, 0.9):
        eye_diamond(d, 22, cy, 5); eye_diamond(d, 47, cy, 5)
    else:                                                  # 眨眼帧
        d.rectangle((17, cy, 27, cy), fill=C['green'])
        d.rectangle((42, cy, 52, cy), fill=C['green'])


def eyes_happy(d, cy=20):
    for cx in (22, 47):
        d.rectangle((cx-6, cy-2, cx-5, cy-2), fill=C['white'])
        d.rectangle((cx-4, cy-4, cx-3, cy-4), fill=C['white'])
        d.rectangle((cx-2, cy-5, cx+2, cy-5), fill=C['white'])
        d.rectangle((cx+3, cy-4, cx+4, cy-4), fill=C['white'])
        d.rectangle((cx+5, cy-2, cx+6, cy-2), fill=C['white'])


def eyes_star(im, d, t, cy=20):
    for cx in (22, 47):
        w = 9 if blink(t, 2, 0.7) else 7
        star = shape(STAR, 'green')
        star = star.resize((w, max(1, round(star.height*w/star.width))), Image.Resampling.NEAREST)
        im.alpha_composite(star, (cx-star.width//2-1, cy-star.height//2-1))


def eyes_heart(im, d, t, cy=19):
    for cx in (22, 47):
        w = 13 if blink(t, 2, 0.6) else 11
        heart = shape(HEART, 'blue')
        heart = heart.resize((w, max(1, round(heart.height*w/heart.width))), Image.Resampling.NEAREST)
        im.alpha_composite(heart, (cx-heart.width//2-1, cy-heart.height//2+2))


def eyes_plead(im, d, t, cy=17):
    for cx in (22, 47):
        d.ellipse((cx-5, cy-5, cx+5, cy+5), fill=C['white'])
        d.rectangle((cx-2, cy-2, cx+1, cy+1), fill=C['ink'])
        th = 3+round(osc(t, 1, 3))
        d.rectangle((cx-1, cy+7, cx+1, cy+7+th), fill=C['blue'])
        d.rectangle((cx-1, cy+7+th, cx+1, cy+7+th), fill=C['mint'])


def eyes_half(d, cy=19):
    for cx in (22, 47):
        for dy in range(-5, 1):
            w = 5+dy
            d.rectangle((cx-w, cy+dy, cx+w, cy+dy), fill=C['shadow'])
        d.rectangle((cx-5, cy+1, cx+5, cy+1), fill=C['mint'])


def eyes_power(d, cy=20):
    for dy in range(-5, 6):                                # 左眼熄灭：暗色轮廓
        w = 5-abs(dy)
        d.rectangle((22-w, cy+dy, 22-w, cy+dy), fill=C['shadow'])
        d.rectangle((22+w, cy+dy, 22+w, cy+dy), fill=C['shadow'])
    eye_diamond(d, 47, cy, 3)


def eyes_seed(d, t, cy=18):
    if blink(t, 1, 0.88):
        d.rectangle((20, cy-1, 24, cy+1), fill=C['white'])
        d.rectangle((45, cy-1, 49, cy+1), fill=C['white'])
    else:
        d.rectangle((19, cy, 25, cy), fill=C['white'])
        d.rectangle((44, cy, 50, cy), fill=C['white'])
    d.rectangle((31, cy+5, 37, cy+5), fill=C['white'])     # o 嘴
    d.rectangle((31, cy+5, 31, cy+8), fill=C['white'])
    d.rectangle((37, cy+5, 37, cy+8), fill=C['white'])
    d.rectangle((31, cy+8, 37, cy+8), fill=C['white'])


def sparkle(d, x, y, t, freq=2, duty=0.7):
    if blink(t, freq, duty):
        d.rectangle((x, y-1, x, y+1), fill=C['white'])
        d.rectangle((x-1, y, x+1, y), fill=C['white'])
