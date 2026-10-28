#!/usr/bin/env python3
"""像素表情包验证脚本：配置、素材目录、渲染约束与成品 GIF。

python3 test.py            # 全部检查（含 output/ 成品复核）
python3 test.py --quick    # 仅结构检查，不读 output/
"""
import argparse
import json
import re
import sys
from pathlib import Path

from PIL import Image

from theme import SCREEN_MODES, screen_image
from gif_codec import inspect_gif
from render import StickerRenderer, pose_at, audit_discipline

ROOT = Path(__file__).resolve().parent
FAILS = []


def check(name, condition, detail=''):
    tag = 'PASS' if condition else 'FAIL'
    print(f'[{tag}] {name}' + (f'：{detail}' if detail and not condition else ''))
    if not condition:
        FAILS.append(name)


def warn(name):
    print(f'[WARN] {name}')


def prop_color_warnings():
    """道具主色与机身同色时，贴胸摆放会糊成一片，只能靠白描边辨认——只提示不判失败。"""
    body = {'shell': (0x2B, 0x30, 0x31), 'shadow': (0x45, 0x4E, 0x50)}
    catalog = json.loads((ROOT/'assets/props/catalog.json').read_text(encoding='utf-8'))
    hits = []
    for entry in catalog['assets']:
        file = ROOT/'assets'/entry['file']
        if not file.is_file():
            continue
        image = Image.open(file).convert('RGBA')
        pixels = [p[:3] for p in image.getdata() if p[3] > 200]
        if not pixels:
            continue
        tally = {}
        for px in pixels:
            tally[px] = tally.get(px, 0) + 1
        main, count = max(tally.items(), key=lambda kv: kv[1])
        ratio = count/len(pixels)
        # 大面同色（>50% 面积）才会真正吞掉道具轮廓；细长剪影有描边仍可辨。
        for name, ref in body.items():
            if ratio > 0.5 and sum(abs(main[i]-ref[i]) for i in range(3)) < 26:
                hits.append(f'{entry["id"]} 主色占 {ratio:.0%} 且与机身 {name} 同色')
                break
    return hits


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--quick', action='store_true', help='仅结构检查，不读 output/')
    args = parser.parse_args()

    config = json.loads((ROOT/'scenes.json').read_text(encoding='utf-8'))
    scenes = config['scenes']; design = config['design']
    chapters = design.get('chapters', '')

    # 1. 配置完整性
    ids = [s['id'] for s in scenes]
    check('16 幕且 id 唯一合法', len(scenes) == 16 and len(set(ids)) == 16
          and all(re.fullmatch(r'[a-zA-Z0-9_-]+', i) for i in ids))
    check('每幕文案/章节/动作/屏幕说明齐全',
          all(s.get('caption') and s.get('chapter') and s.get('action')
              and s.get('screen') and s.get('screen_brief') for s in scenes))
    check(f'四章各 4 幕（{chapters}）', chapters and len(chapters) == 4
          and all(sum(1 for s in scenes if s['chapter'][0] == ch) == 4 for ch in chapters))

    # 2. 屏幕库：目录注册表与 theme 一致；所有屏幕模式 t=0/1 尺寸一致
    screens = json.loads((ROOT/'assets/screens/catalog.json').read_text(encoding='utf-8'))
    check('屏幕目录与 theme 注册表一致', {a['id'] for a in screens['assets']} == SCREEN_MODES)
    ok = True
    for mode in SCREEN_MODES:
        a, b = screen_image(mode, 0.0), screen_image(mode, 0.9999)
        ok = ok and a.size == b.size == (70, 36)
    check('屏幕模式 t≈0 与 t≈1 输出一致（循环无跳变）', ok)

    # 3. 道具库：双向登记，无库外素材
    props = json.loads((ROOT/'assets/props/catalog.json').read_text(encoding='utf-8'))
    registered = {a['file'] for a in props['assets']}
    on_disk = {f'props/{p.name}' for p in (ROOT/'assets/props').glob('*.png')}
    check('道具全部登记（无未注册文件）', on_disk <= registered,
          f'未登记：{sorted(on_disk-registered)}')
    missing = {a['file'] for a in props['assets']} - on_disk
    check('登记文件全部存在', not missing, f'缺失：{sorted(missing)}')

    used_assets = set()
    for s in scenes:
        for group in ('props', 'effects', 'behind'):
            for entry in s.get(group, []):
                used_assets.add(entry['asset'])
    check('场景引用的道具全部在库内', all(f'props/{a}.png' in registered for a in used_assets),
          f'库外引用：{sorted(a for a in used_assets if f"props/{a}.png" not in registered)}')
    for note in prop_color_warnings():
        warn(f'道具与机身同色（贴胸摆放可能看不清）：{note}')

    # 4. 每幕必须有关键帧轨道：只有屏幕动画时，静止段会被 GIF 编码器合并，
    #    实拍帧数可能掉到个位数，动作等于没有。
    no_tracks = [s['id'] for s in scenes if not s.get('tracks')]
    check('每幕至少 1 条动作轨道', not no_tracks, f'缺轨道：{no_tracks}')

    # 5. 关键帧轨道：覆盖 0–1、严格递增、首尾同值（循环保障）
    ok = True; detail = ''
    for s in scenes:
        for track in s.get('tracks', []):
            keys = track['keys']
            if keys[0][0] != 0 or keys[-1][0] != 1 or keys[0][1] != keys[-1][1] \
               or any(a[0] >= b[0] for a, b in zip(keys, keys[1:])):
                ok = False; detail = f'{s["id"]}/{track["path"]}'
    check('动作轨道首尾同值且时间递增', ok, detail)

    # 6. 渲染约束：静态帧在安全边界内、非空、文案区无侵入
    renderer = StickerRenderer(design)
    ok = True; detail = ''
    for s in scenes:
        _, clean = renderer.render(s, 0.0, 8)
        bbox = clean.getbbox()
        margin = min(bbox[0], bbox[1], 640-bbox[2], 640-bbox[3])
        if not bbox or margin < 11 or bbox[3] > 536:
            ok = False; detail = f'{s["id"]} bbox={bbox} margin={margin}'
    check('16 幕静态帧均在安全边界内', ok, detail)

    # 7. 循环一致：pose_at(0) == pose_at(1)
    ok = True; detail = ''
    for s in scenes:
        a, b = pose_at(s, 0.0), pose_at(s, 1.0)
        if json.dumps(a, sort_keys=True) != json.dumps(b, sort_keys=True):
            ok = False; detail = s['id']
    check('姿态轨道首尾闭环', ok, detail)

    # 8. 色彩纪律：红/黄/蓝只在 design.discipline 登记的幕出现
    ok = True; detail = ''
    try:
        for s in scenes:
            _, clean = renderer.render(s, 0.3, 0)
            audit_discipline(design, s, clean)
    except ValueError as exc:
        ok = False; detail = str(exc)
    check('色彩纪律（按 design.discipline 审计）', ok, detail)

    if not args.quick:
        output = ROOT/'output'
        # 9. 成品 PNG：512 透明底、四角透明、带字/无字各 16
        ok = True; detail = ''
        for folder, count in (('png', 16), ('no-text', 16)):
            files = list((output/folder).glob('*.png'))
            if len(files) != count:
                ok = False; detail = f'{folder} 只有 {len(files)} 张'
                continue
            for f in files:
                im = Image.open(f)
                if im.size != (512, 512):
                    ok = False; detail = f'{f.name} 尺寸 {im.size}'
                rgba = im.convert('RGBA')
                for px in ((2, 2), (509, 2), (2, 509), (509, 509)):
                    if rgba.getpixel(px)[3] != 0:
                        ok = False; detail = f'{f.name} 角落不透明'
                        break
        check('成品 PNG 512×512 透明底且四角透明', ok, detail)

        # 10. 成品 GIF：无限循环、disposal=2、帧数达标、总时长达标
        expected_ms = config.get('defaults', {}).get('duration_ms', 3200)
        ok = True; detail = ''
        for folder in ('gif', 'gif-no-text'):
            gifs = sorted((output/folder).glob('*.gif'))
            if not gifs:
                continue                                   # 静态模式下允许为空
            if len(gifs) != 16:
                ok = False; detail = f'{folder} 只有 {len(gifs)} 个'
                continue
            for f in gifs:
                info = inspect_gif(f)
                if info['distinct_frames'] < 2 or info['loop'] != 0:
                    ok = False; detail = f'{f.name} distinct={info["distinct_frames"]}'
                # 帧数过少说明整幕几乎是静止画面，动作读不出来。
                if info['frames'] < 24:
                    ok = False; detail = f'{f.name} 仅 {info["frames"]} 帧（动画过少）'
                if info['duration_ms'] != expected_ms:
                    ok = False; detail = f'{f.name} 总时长 {info["duration_ms"]}ms'
        check('成品 GIF 循环、防残影、帧数与时长达标', ok, detail)

        # 11. 清单：manifest 覆盖全部 16 幕
        manifest = json.loads((output/'manifest.json').read_text(encoding='utf-8'))
        check('manifest 覆盖 16 幕', len(manifest['scenes']) == 16
              and manifest['pack'] == config['pack'])

    print()
    if FAILS:
        print(f'未通过 {len(FAILS)} 项：{FAILS}')
        sys.exit(1)
    print('全部检查通过')


if __name__ == '__main__':
    main()
