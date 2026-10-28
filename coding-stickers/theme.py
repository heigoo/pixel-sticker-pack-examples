#!/usr/bin/env python3
"""主题内容文件：AI 编程搭档（TRAE宝）。

屏幕即终端：日常情绪全部写在屏幕上的代码/报错/进度里。
1. SCREENS        —— 16 个屏幕表情模式列表 (id, name, brief, colors, fn)
2. screen_image(mode, t) + SCREEN_MODES —— 渲染器按此取屏
3. NEW_PROPS      —— 主题专属道具 [(id, builder, name, brief)]
色彩纪律：红/黄/蓝是强调色，只允许出现在 scenes.json design.discipline 登记的幕。
"""
from PIL import Image, ImageDraw

from lib_base import (C, latin, panel, osc, blink, outlined, shape, polygon_im, sparkle,
                      eyes_default, eyes_happy, eyes_half, eyes_seed)


# =====================================================================
# 屏幕表情：70×36，一幕一屏；t 为循环进度
# =====================================================================

def _caret(im, x, y, t, freq=2, color='white'):
    """终端光标：常亮块 + 低频闪烁。"""
    if blink(t, freq, 0.6):
        ImageDraw.Draw(im).rectangle((x, y, x+4, y+2), fill=C[color])


def scr_new_req(t=0.0):
    """01 新需求来了：NEW +1 跳字与眯眼笑，光标在闪。"""
    im = panel(); d = ImageDraw.Draw(im)
    im.alpha_composite(latin('NEW +1', 'green'), (17, 2))
    eyes_happy(d, 22)
    _caret(im, 56, 28, t, 2)
    sparkle(d, 62, 12, t, 2); sparkle(d, 6, 14, t, 3)
    return im


def scr_autocomplete(t=0.0):
    """02 自动补全中：两行代码逐行滚上去，半闭眼专注。"""
    im = panel(); d = ImageDraw.Draw(im)
    d.rectangle((4, 3, 46, 5), fill=C['green'])
    d.rectangle((4, 9, 60, 11), fill=C['white'])
    eyes_half(d, 22)
    _caret(im, 6, 31, t, 3)
    if blink(t, 4, 0.5):
        d.rectangle((62, 9, 62, 11), fill=C['mint'])
    return im


def scr_copy_paste(t=0.0):
    """03 复制粘贴：剪贴板与 COPY 计数一起往上跳。"""
    im = panel(); d = ImageDraw.Draw(im)
    im.alpha_composite(latin('COPY', 'green'), (3, 2))
    if blink(t, 2, 0.7):
        im.alpha_composite(latin('+3', 'white'), (50, 2))
    d.rectangle((29, 12, 41, 31), outline=C['white'])
    d.rectangle((33, 10, 37, 12), fill=C['white'])
    for y in (16, 20, 24, 28):
        d.rectangle((32, y, 38, y), fill=C['shadow'])
    return im


def scr_req_changed(t=0.0):
    """04 需求又改了：红色 CHANGED 闪 + 惊愕单眼。"""
    im = panel(); d = ImageDraw.Draw(im)
    if blink(t, 2, 0.55):
        im.alpha_composite(latin('CHANGED', 'red'), (14, 2))
    else:
        im.alpha_composite(latin('CHANGED', 'shadow'), (14, 2))
    d.rectangle((62, 2, 63, 6), fill=C['red'])
    d.rectangle((62, 8, 63, 9), fill=C['red'])
    eyes_seed(d, t, 17)
    return im


def scr_error(t=0.0):
    """05 报错了：红色 ERROR 与不断滚动的报错堆栈。"""
    im = panel(); d = ImageDraw.Draw(im)
    im.alpha_composite(latin('ERROR', 'red'), (20, 2))
    rows = ((13, 34, 'red'), (18, 44, 'shadow'), (23, 26, 'red'), (28, 38, 'shadow'))
    for i, (y, w, color) in enumerate(rows):
        x = 4 + round(osc(t, 2, 2, i*0.2))
        d.rectangle((x, y, x+w if x+w < 68 else 68, y+1), fill=C[color])
    return im


def scr_compile_fail(t=0.0):
    """06 编译不过：99% 进度条卡住，半闭眼等。"""
    im = panel(); d = ImageDraw.Draw(im)
    im.alpha_composite(latin('99%', 'white'), (3, 2))
    d.rectangle((3, 12, 66, 20), outline=C['white'])
    d.rectangle((5, 14, 60, 18), fill=C['green'])           # 差最后一格：卡在 99%
    if blink(t, 2, 0.5):
        d.rectangle((62, 14, 64, 18), fill=C['mint'])
    eyes_half(d, 29)
    return im


def scr_whos_code(t=0.0):
    """07 这谁写的：一行看不懂的代码与 ???。"""
    im = panel(); d = ImageDraw.Draw(im)
    if blink(t, 2, 0.75):
        im.alpha_composite(latin('???', 'white'), (26, 2))
    d.rectangle((6, 11, 64, 12), fill=C['shadow'])
    d.rectangle((10, 11, 30, 12), fill=C['mint'])
    eyes_default(im, d, t, 25)
    return im


def scr_broke_three(t=0.0):
    """08 改一坏三：报错字样 + 裂纹与花屏碎块。"""
    im = panel(); d = ImageDraw.Draw(im)
    im.alpha_composite(latin('DAMAGE', 'red'), (17, 2))
    # 固定坐标的花屏碎块，避免随机导致帧间跳变
    for x, y, w, h, color in ((6, 14, 5, 3, 'shadow'), (14, 20, 8, 2, 'paper'),
                              (28, 16, 3, 4, 'shadow'), (46, 22, 6, 3, 'paper'),
                              (56, 14, 4, 5, 'shadow'), (20, 28, 10, 2, 'shadow'),
                              (40, 28, 7, 3, 'paper'), (58, 30, 6, 2, 'shadow')):
        d.rectangle((x, y, x+w, y+h), fill=C[color])
    # 裂纹：从左上贯到右下
    for x, y in ((10, 12), (12, 15), (11, 18), (14, 21), (13, 24), (16, 27), (15, 30), (18, 33)):
        d.rectangle((x, y, x+1, y+1), fill=C['red'])
    if blink(t, 3, 0.5):
        d.rectangle((30, 12, 44, 13), fill=C['red'])
    return im


def scr_works_local(t=0.0):
    """09 我本地好好的：大号绿色 OK 与对勾。"""
    im = panel(); d = ImageDraw.Draw(im)
    im.alpha_composite(latin('OK', 'green', 3), (14, 6))
    for i in range(3):
        d.rectangle((52+i, 8+i, 53+i, 9+i), fill=C['white'])
    for i in range(5):
        d.rectangle((55+i, 13-i, 56+i, 14-i), fill=C['white'])
    sparkle(d, 8, 26, t, 2); sparkle(d, 62, 26, t, 3)
    return im


def scr_smells(t=0.0):
    """10 你这写法有毒：屏幕浮出骷髅与 BUG。"""
    im = panel(); d = ImageDraw.Draw(im)
    if blink(t, 2, 0.7):
        im.alpha_composite(latin('BUG', 'red'), (46, 2))
    skull = shape(SKULL, 'paper')
    skull = skull.resize((skull.width*2, skull.height*2), Image.Resampling.NEAREST)
    im.alpha_composite(skull, (22, 6))
    d = ImageDraw.Draw(im)
    d.rectangle((26, 13, 29, 16), fill=C['ink'])
    d.rectangle((34, 13, 37, 16), fill=C['ink'])
    d.rectangle((31, 19, 32, 20), fill=C['ink'])
    for x in (27, 30, 33, 36):
        d.rectangle((x, 22, x, 23), fill=C['ink'])
    return im


def scr_reviewing(t=0.0):
    """11 代码评审中：红绿 diff 行一行行往下扫。"""
    im = panel(); d = ImageDraw.Draw(im)
    im.alpha_composite(latin('DIFF', 'white'), (3, 2))
    for i in range(4):
        y = 11 + i*6
        color = 'green' if i % 2 == 0 else 'red'
        width = 26 + i*7
        x = 8 + round(osc(t, 1, 2, i*0.25))
        d.rectangle((x-4, y, x-3, y+2), fill=C[color])
        d.rectangle((x, y+1, min(x+width, 66), y+2), fill=C[color])
    return im


def scr_conflict(t=0.0):
    """12 合并冲突：两块代码互撞，中间红线闪。"""
    im = panel(); d = ImageDraw.Draw(im)
    im.alpha_composite(latin('CONFLICT', 'white'), (11, 2))
    push = round(osc(t, 1, 8))
    x1 = 12 + push; x2 = 46 - push
    d.rectangle((x1, 16, x1+12, 30), fill=C['paper'])
    d.rectangle((x2, 16, x2+12, 30), fill=C['paper'])
    if blink(t, 2, 0.4):
        d.rectangle((34, 14, 35, 32), fill=C['red'])
    else:
        d.rectangle((34, 14, 35, 32), fill=C['shadow'])
    return im


def scr_all_green(t=0.0):
    """13 全绿了：PASS 与三行满绿勾。"""
    im = panel(); d = ImageDraw.Draw(im)
    im.alpha_composite(latin('PASS', 'green', 2), (12, 3))
    for i, y in enumerate((23, 27, 31)):
        w = 54 - i*10
        if blink(t, 2, 0.85):
            d.rectangle((8, y, 8+w, y), fill=C['green'])
        for k in range(3):
            d.rectangle((10+k, y-3+k, 11+k, y-2+k), fill=C['white'])
    return im


def scr_deployed(t=0.0):
    """14 部署成功：DEPLOY OK 与冲上去的绿箭头。"""
    im = panel(); d = ImageDraw.Draw(im)
    im.alpha_composite(latin('DEPLOY', 'green'), (3, 2))
    im.alpha_composite(latin('OK', 'white'), (51, 2))
    im.alpha_composite(shape(UP_ARROW, 'green'), (31, 20+round(osc(t, 2, -2))))
    return im


def scr_rollback(t=0.0):
    """15 立刻回滚：红色 ROLLBACK 与下坠箭头。"""
    im = panel(); d = ImageDraw.Draw(im)
    if blink(t, 2, 0.6):
        im.alpha_composite(latin('ROLLBACK', 'red'), (11, 2))
    else:
        im.alpha_composite(latin('ROLLBACK', 'shadow'), (11, 2))
    im.alpha_composite(shape(list(reversed(UP_ARROW)), 'red'), (31, 21+round(osc(t, 1, 2))))
    return im


def scr_offwork(t=0.0):
    """16 下班了：屏幕暗下来，只剩 zZ 与困倦的半闭眼。"""
    im = panel('ink'); d = ImageDraw.Draw(im)
    d.rectangle((0, 0, 69, 35), outline=C['shadow'])
    eyes_half(d, 20)
    im.alpha_composite(latin('ZZ', 'white'), (54, 26+round(osc(t, 1, 2))))
    if blink(t, 1, 0.5):
        d.rectangle((54, 4, 54, 4), fill=C['mint'])
    return im


SCREENS = [
    ('new_req', '新需求来了', 'NEW +1 跳字、眯眼笑与闪烁光标', ('green', 'white'), scr_new_req),
    ('autocomplete', '自动补全中', '两行代码滚动与半闭眼', ('green', 'white', 'mint'), scr_autocomplete),
    ('copy_paste', '复制粘贴', 'COPY 计数与像素剪贴板', ('green', 'white', 'shadow'), scr_copy_paste),
    ('req_changed', '需求又改了', '红色 CHANGED 闪与惊愕眼', ('red', 'shadow'), scr_req_changed),
    ('error', '报错了', '红色 ERROR 与滚动堆栈', ('red', 'shadow'), scr_error),
    ('compile_fail', '编译不过', '99% 卡住的进度条', ('white', 'green', 'shadow'), scr_compile_fail),
    ('whos_code', '这谁写的', '陌生代码行与 ???', ('white', 'mint', 'shadow'), scr_whos_code),
    ('broke_three', '改一坏三', '红色 DAMAGE、裂纹与花屏碎块', ('red', 'paper', 'shadow'), scr_broke_three),
    ('works_local', '我本地好好的', '大号绿色 OK 与对勾', ('green', 'white'), scr_works_local),
    ('smells', '你这写法有毒', '骷髅与红色 BUG', ('red', 'paper', 'ink'), scr_smells),
    ('reviewing', '代码评审中', '红绿 diff 行逐行扫', ('green', 'red', 'white'), scr_reviewing),
    ('conflict', '合并冲突', '两块代码互撞与红线', ('white', 'paper', 'red'), scr_conflict),
    ('all_green', '全绿了', 'PASS 与三行满绿勾', ('green', 'white'), scr_all_green),
    ('deployed', '部署成功', 'DEPLOY OK 与上升箭头', ('green', 'white'), scr_deployed),
    ('rollback', '立刻回滚', '红色 ROLLBACK 与下坠箭头', ('red', 'shadow'), scr_rollback),
    ('offwork', '下班了', '暗屏、zZ 与半闭眼', ('shadow', 'white', 'mint'), scr_offwork),
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
# 主题专属道具：原生整数像素 + 1px 墨黑轮廓
# =====================================================================

UP_ARROW = [
'....#....',
'...###...',
'..#####..',
'....#....',
'....#....',
'....#....',
]

SKULL = [
'...#####...',
'..#######..',
'.#########.',
'###########',
'##.##...##.',
'###########',
'.#########.',
'..##.#.##..',
'...#####...',
]


def make_keyboard():
    """纸白键帽键盘：与黑色机身强对比，抱着打字也看得清。"""
    mask = Image.new('L', (26, 10), 0)
    ImageDraw.Draw(mask).rectangle((0, 0, 25, 9), fill=255)
    im = outlined(mask, 'paper')
    d = ImageDraw.Draw(im)
    for y in (3, 6, 9):
        for x in (2, 6, 10, 14, 18, 22):
            d.rectangle((x+1, y, x+2, y), fill=C['shadow'])
    d.rectangle((1, 9, 24, 9), fill=C['shadow'])
    return im


def make_clipboard():
    """像素剪贴板：纸白板 + 墨黑夹子。"""
    mask = Image.new('L', (14, 18), 0)
    ImageDraw.Draw(mask).rectangle((0, 2, 13, 17), fill=255)
    im = outlined(mask, 'paper')
    d = ImageDraw.Draw(im)
    d.rectangle((5, 0, 8, 3), fill=C['ink'])
    for y in (6, 10, 14):
        d.rectangle((2, y, 10, y), fill=C['shadow'])
    return im


def make_magnifier():
    """像素放大镜：纸白镜框与手柄，黑机身前也读得出来。"""
    mask = Image.new('L', (17, 17), 0); d = ImageDraw.Draw(mask)
    d.ellipse((0, 0, 13, 13), fill=255)
    d.ellipse((3, 3, 10, 10), fill=0)
    d.polygon([(11, 12), (16, 16), (13, 16), (10, 14)], fill=255)
    im = outlined(mask, 'paper')
    d = ImageDraw.Draw(im)
    d.ellipse((5, 5, 10, 10), fill=C['shadow'])
    d.rectangle((6, 6, 7, 7), fill=C['white'])
    return im


def make_skull():
    """像素骷髅：你这写法有毒。"""
    im = shape(SKULL, 'paper')
    return im


def make_branch_tag():
    """分支标签：回滚/切分支用的小挂牌。"""
    mask = Image.new('L', (13, 7), 0); d = ImageDraw.Draw(mask)
    d.rectangle((0, 0, 12, 6), fill=255)
    im = outlined(mask, 'paper')
    d = ImageDraw.Draw(im)
    d.rectangle((2, 3, 3, 4), fill=C['ink'])
    d.rectangle((6, 3, 10, 3), fill=C['green'])
    return im


def make_deploy_arrow():
    """上升箭头：部署成功。"""
    mask = Image.new('L', (11, 14), 0); d = ImageDraw.Draw(mask)
    d.rectangle((4, 5, 6, 13), fill=255)
    d.polygon([(0, 6), (10, 6), (5, 0)], fill=255)
    return outlined(mask, 'green')


NEW_PROPS = [
    ('keyboard', make_keyboard, '像素键盘', '敲代码/自动补全的键盘'),
    ('clipboard', make_clipboard, '像素剪贴板', '复制粘贴的剪贴板'),
    ('magnifier', make_magnifier, '像素放大镜', '代码评审逐行扫'),
    ('skull', make_skull, '像素骷髅', '写法有毒的警告'),
    ('branch_tag', make_branch_tag, '分支标签', '回滚/切分支挂牌'),
    ('deploy_arrow', make_deploy_arrow, '上升箭头', '部署成功的绿箭头'),
]
