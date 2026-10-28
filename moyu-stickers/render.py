#!/usr/bin/env python3
"""像素表情包 16 幕合成器：静态 PNG + 循环 GIF（配置驱动，主题无关）。

python3 render.py                  # PNG + GIF + 总览
python3 render.py --static-only    # 仅静态 PNG
python3 render.py --only 09_zero_left --text "没钱了"
python3 render.py --fps 10 --duration-ms 2400
"""
import argparse
import copy
import json
import math
import re
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter
from rig import Renderer, find_font
from theme import screen_image, SCREEN_MODES
from gif_codec import save_gif, timing, value_at

ROOT = Path(__file__).resolve().parent
CLEAR = (0, 0, 0, 0)
BASE = 640
POSE = {'neck': [320, 310], 'arms': [0, 0], 'legs': [0, 0], 'head_angle': 0, 'head_offset': [0, 0],
        'rotation': 0, 'scale': 1, 'offset': [0, 0], 'front_arms': [], 'bent_arms': {}}
ANIM_TYPES = {'blink', 'pulse', 'flicker', 'bob', 'sway'}


def copy_pose(pose):
    return {k: copy.deepcopy(v) for k, v in pose.items()}


def pose_at(scene, t):
    """基础姿态叠加关键帧轨道；轨道必须覆盖 0–1 且首尾同值，保证循环无跳变。"""
    pose = copy_pose(POSE); pose.update(copy_pose(scene.get('pose', {})))
    seen = set()
    for track in scene.get('tracks', []):
        path = track['path']; keys = track['keys']
        if path in seen:
            raise ValueError(f'重复动作轨道：{path}')
        seen.add(path)
        if keys[0][0] != 0 or keys[-1][0] != 1 or keys[0][1] != keys[-1][1]:
            raise ValueError(f'{path} 关键帧需要覆盖 0–1 且首尾值相同。')
        if any(a[0] >= b[0] for a, b in zip(keys, keys[1:])):
            raise ValueError(f'{path} 时间必须严格递增。')
        parts = path.split('.'); parent = pose
        for key in parts[:-1]:
            parent = parent[int(key)] if isinstance(parent, list) else parent[key]
        key = int(parts[-1]) if isinstance(parent, list) else parts[-1]
        parent[key]  # 先检查路径存在，不接受拼写错误。
        parent[key] = value_at(track, t)
    return pose


class StickerRenderer(Renderer):
    def __init__(self, design, font=None, font_index=0):
        super().__init__(ROOT/'assets', font or find_font(), font_index)
        self.design = design
        screens = json.loads((self.assets/'screens'/'catalog.json').read_text(encoding='utf-8'))
        props = json.loads((self.assets/'props'/'catalog.json').read_text(encoding='utf-8'))
        catalog_ids = {item['id'] for item in screens['assets']}
        if catalog_ids != SCREEN_MODES:
            raise ValueError('屏幕库目录与 theme 注册表不一致，请先运行 build_assets.py。')
        self.allowed = {item['file'] for item in props['assets']}
        self.allowed |= {item['file'] for item in self.manifest['parts'].values()}
        self.used = set()

    def image(self, name):
        if name not in self.allowed:
            raise ValueError(f'素材不在统一库内：{name}')
        self.used.add(name)
        return super().image(name)

    def prop(self, name):
        return self.image(f'props/{name}.png')

    def place_pixel(self, canvas, name, center, scale=1, angle=0, alpha=1):
        image = self.prop(name); factor = 3*scale
        image = image.resize((max(1, round(image.width*factor)), max(1, round(image.height*factor))),
                             Image.Resampling.NEAREST)
        if alpha < 1:
            image = image.copy()
            image.putalpha(image.getchannel('A').point(lambda p: round(p*max(0, alpha))))
        radius = math.ceil(max(math.hypot(x-image.width/2, y-image.height/2)
                               for x in (0, image.width) for y in (0, image.height)))+2
        patch = Image.new('RGBA', (radius*2, radius*2), CLEAR)
        patch.alpha_composite(image, (round(radius-image.width/2), round(radius-image.height/2)))
        if angle:
            patch = patch.rotate(angle, Image.Resampling.NEAREST, center=(radius, radius))
        xy = (round(center[0]-radius), round(center[1]-radius)); bounds = patch.getbbox()
        if bounds and (xy[0]+bounds[0] < 0 or xy[1]+bounds[1] < 0 or
                       xy[0]+bounds[2] > canvas.width or xy[1]+bounds[3] > canvas.height):
            raise ValueError(f'道具 {name} 超出画布。')
        canvas.alpha_composite(patch, xy)

    @staticmethod
    def arm_points(pose, side):
        i = 0 if side == 'left' else 1; nx, ny = pose['neck']
        shoulder = (nx+(-89 if i == 0 else 90), ny+10)
        bend = pose.get('bent_arms', {}).get(side)
        if bend:
            upper, lower = bend['upper'], bend['lower']
            a, b = math.radians(upper), math.radians(lower)
            elbow = (shoulder[0]+60*math.sin(a), shoulder[1]+60*math.cos(a))
            wrist = (elbow[0]+68*math.sin(b), elbow[1]+68*math.cos(b))
            return shoulder, elbow, wrist, upper, lower
        angle = pose['arms'][i]; a = math.radians(angle)
        wrist = (shoulder[0]+107*math.sin(a), shoulder[1]+107*math.cos(a))
        return shoulder, None, wrist, angle, angle

    def animated_place(self, canvas, entry, t, pose):
        """道具/特效放置 + 通用循环动画；t=0 时与静态帧一致。"""
        center = entry.get('center')
        if entry.get('anchor') in ('left_wrist', 'right_wrist'):
            wrist = self.arm_points(pose, entry['anchor'].split('_')[0])[2]
            offset = entry.get('offset', [0, 0]); center = [wrist[0]+offset[0], wrist[1]+offset[1]]
        if center is None:
            raise ValueError('道具需要 center 或 anchor。')
        center = list(center)
        scale = entry.get('scale', 1); angle = entry.get('angle', 0)
        anim = entry.get('anim')
        if anim:
            typ = anim.get('type'); freq = anim.get('freq', 1)
            if typ not in ANIM_TYPES:
                raise ValueError(f'未知动画类型：{typ}')
            if typ == 'blink':
                if not ((t*freq) % 1.0) < anim.get('duty', 0.6):
                    return
            elif typ == 'pulse':
                if math.sin(2*math.pi*freq*t) > 0:
                    scale *= 1+anim.get('amount', 0.18)
            elif typ == 'flicker':
                if math.sin(2*math.pi*freq*t) > 0:
                    scale *= 1-anim.get('amount', 0.12)
            elif typ == 'bob':
                center[1] += round(anim.get('amp', 5)*math.sin(2*math.pi*freq*t))
            elif typ == 'sway':
                angle += round(anim.get('amp', 8)*math.sin(2*math.pi*freq*t))
        self.place_pixel(canvas, entry['asset'], center, scale, angle)

    def character(self, scene, pose, t):
        result = Image.new('RGBA', (BASE, BASE), CLEAR); nx, ny = pose['neck']

        def part(name, position, angle=0):
            meta = self.manifest['parts']['front_'+name]
            self.place(result, self.image(meta['file']), position, meta['pivot'], angle)

        def arm(side):
            shoulder, elbow, wrist, upper, lower = self.arm_points(pose, side)
            if elbow is None:
                part('arm_'+side, shoulder, upper)
            else:
                meta = self.manifest['parts']['front_arm_'+side]; image = self.image(meta['file'])
                self.place(result, image.crop((0, 0, image.width, 76)), shoulder, meta['pivot'], upper)
                self.place(result, image.crop((0, 58, image.width, image.height)), elbow, (meta['pivot'][0], 6), lower)

        part('leg_left', (nx-35, ny+115), pose['legs'][0])
        part('leg_right', (nx+36, ny+115), pose['legs'][1])
        part('torso', (nx, ny))
        front = pose.get('front_arms', [])
        for side in ('left', 'right'):
            if side not in front:
                arm(side)
        head = self.image('parts/front_head.png').copy()
        # 屏幕即表情：70×36 逻辑面板以 3× 嵌入头部屏幕区，随 t 循环动画。
        face = screen_image(scene['screen'], t).resize((210, 108), Image.Resampling.NEAREST)
        head.alpha_composite(face, (49, 72))
        self.used.add(f"screens/{scene['screen']}(动态)")
        self.place(result, head, (nx+pose['head_offset'][0], ny+pose['head_offset'][1]),
                   (153, 230), pose['head_angle'])
        for side in ('left', 'right'):
            if side in front:
                arm(side)
        if pose['rotation'] or pose['scale'] != 1 or pose['offset'] != [0, 0]:
            bbox = result.getbbox()
            if not bbox:
                raise ValueError('角色合成结果为空。')
            center = ((bbox[0]+bbox[2])/2+pose['offset'][0], (bbox[1]+bbox[3])/2+pose['offset'][1])
            cropped = result.crop(bbox); result = Image.new('RGBA', (BASE, BASE), CLEAR)
            self.place(result, cropped, center, angle=pose['rotation'], scale=pose['scale'])
        return result

    def render(self, scene, t, outline=8):
        t = t % 1.0
        pose = pose_at(scene, t)
        art = Image.new('RGBA', (BASE, BASE), CLEAR)
        for entry in scene.get('behind', []):
            self.animated_place(art, entry, t, pose)
        art.alpha_composite(self.character(scene, pose, t))
        for group in ('props', 'effects'):
            for entry in scene.get(group, []):
                self.animated_place(art, entry, t, pose)
        bbox = art.getbbox()
        if not bbox or min(bbox[0], bbox[1], BASE-bbox[2], BASE-bbox[3]) < outline+3:
            raise ValueError(f'{scene["id"]} 构图超出安全边界。')
        if bbox[3] > 536:
            raise ValueError(f'{scene["id"]} 道具侵入文案安全区：y={bbox[3]}。')
        if outline:
            alpha = art.getchannel('A').filter(ImageFilter.MaxFilter(outline*2+1))
            sticker = Image.new('RGBA', art.size, 'white'); sticker.putalpha(alpha)
            sticker.alpha_composite(art); art = sticker
        return self.caption(art, scene['caption']), art


def tone_for(design, chapter):
    return design.get('chapter_tones', {}).get(chapter[0], '#5ADB97')


def audit_discipline(design, scene, image):
    """色彩纪律审计：红/黄/蓝只允许出现在 design.discipline 登记的幕。"""
    palette = {'red': (236, 98, 105), 'gold': (244, 205, 112), 'blue': (49, 107, 202)}
    rules = design.get('discipline', {})
    found = set()
    for r, g, b, a in image.getdata():
        if a < 128:                 # GIF 量化为二值 alpha；半透明混合像素不参与审计
            continue
        for name, (pr, pg, pb) in palette.items():
            if abs(r-pr)+abs(g-pg)+abs(b-pb) < 90:
                found.add(name)
    allowed = {tone for tone in found if scene['id'] in rules.get(tone, [])}
    stray = found-allowed
    if stray:
        raise ValueError(f'{scene["id"]} 违反色彩纪律：出现 {sorted(stray)}')
    return sorted(found)


def make_overview(renderer, output, scenes, images, design):
    cols = 4; cell = 250; rows = math.ceil(len(scenes)/cols); header = 150
    canvas = Image.new('RGB', (36+cols*(cell+18), header+rows*(cell+64)+16), '#f2f3ef')
    d = ImageDraw.Draw(canvas)
    d.text((30, 22), design['overview_title'], font=renderer.font(38), fill='#202824')
    d.text((32, 86), design['overview_subtitle'], font=renderer.font(21), fill='#66756c')
    for i, (scene, image) in enumerate(zip(scenes, images)):
        x = 18+(i % cols)*(cell+18); y = header+(i//cols)*(cell+64)
        d.rounded_rectangle((x, y, x+cell, y+cell+46), radius=16, fill='white')
        d.text((x+14, y+10), scene['chapter'], font=renderer.font(19), fill=tone_for(design, scene['chapter']))
        d.text((x+64, y+12), f'{i+1:02d}', font=renderer.font(16), fill='#84988b')
        canvas.paste(image, (x, y+34), image)
        d.text((x+14, y+cell+2), scene['caption'], font=renderer.font(22), fill='#202824')
    canvas.save(output/'overview.png')


def make_gif_overview(renderer, output, scenes, frames_by_scene, durations, design):
    """同步 16 幕动态总览；画面直接来自已输出的 GIF 帧。"""
    cols = 4; cell = 250; rows = math.ceil(len(scenes)/cols); header = 150
    width = 36+cols*(cell+18); height = header+rows*(cell+64)+16
    count = max(len(f) for f in frames_by_scene); previews = []
    for tick in range(count):
        canvas = Image.new('RGB', (width, height), '#f2f3ef'); d = ImageDraw.Draw(canvas)
        d.text((30, 22), design['overview_title'], font=renderer.font(38), fill='#202824')
        d.text((32, 86), design['overview_subtitle'], font=renderer.font(21), fill='#66756c')
        for i, (scene, frames) in enumerate(zip(scenes, frames_by_scene)):
            x = 18+(i % cols)*(cell+18); y = header+(i//cols)*(cell+64)
            d.rounded_rectangle((x, y, x+cell, y+cell+46), radius=16, fill='white')
            d.text((x+14, y+10), scene['chapter'], font=renderer.font(19), fill=tone_for(design, scene['chapter']))
            d.text((x+64, y+12), f'{i+1:02d}', font=renderer.font(16), fill='#84988b')
            image = frames[min(len(frames)-1, round(tick/max(1, count-1)*(len(frames)-1)))]
            canvas.paste(image, (x, y+34), image)
            d.text((x+14, y+cell+2), scene['caption'], font=renderer.font(22), fill='#202824')
        previews.append(canvas)
    previews[0].save(output/'overview.gif', save_all=True, append_images=previews[1:],
                     duration=durations[0], loop=0, optimize=False)


def make_screens_board(renderer, output, scenes):
    rows = math.ceil(len(scenes)/4)
    board = Image.new('RGB', (1080, 110+rows*224), '#202824'); d = ImageDraw.Draw(board)
    d.text((24, 24), '16 幕屏幕内容核对', font=renderer.font(33), fill='white')
    for i, scene in enumerate(scenes):
        x = 20+(i % 4)*266; y = 100+(i//4)*224
        face = screen_image(scene['screen'], 0.3).resize((252, 130), Image.Resampling.NEAREST)
        board.paste(face, (x, y))
        d.text((x, y+140), scene['caption'], font=renderer.font(21), fill='white')
        d.text((x, y+176), f"{scene['screen']} · {scene['screen_brief']}", font=renderer.font(13), fill='#A9E6CC')
    board.save(output/'screens-overview.png')


def make_keyframes(renderer, output, scenes, frames_by_scene):
    """两页关键帧：深色背景核对透明轮廓、动作中间态与道具位置。"""
    for page, start in enumerate(range(0, len(scenes), 8), 1):
        subset = scenes[start:start+8]
        board = Image.new('RGB', (1056, 70+len(subset)*206), '#202824'); d = ImageDraw.Draw(board)
        d.text((20, 17), f'动作关键帧 / {page}', font=renderer.font(29), fill='white')
        for row, scene in enumerate(subset):
            frames = frames_by_scene[start+row]
            for col, phase in enumerate((0, 0.2, 0.4, 0.6, 0.8)):
                im = frames[min(len(frames)-1, round(phase*(len(frames)-1)))]
                im = im.resize((192, 192), Image.Resampling.LANCZOS)
                x = 14+col*208; y = 70+row*206
                d.rounded_rectangle((x, y, x+192, y+195), radius=9, fill='#344138')
                board.paste(im, (x, y), im)
        board.save(output/f'keyframes-{page}.png')


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--config', type=Path, default=ROOT/'scenes.json')
    parser.add_argument('--output', type=Path, default=ROOT/'output')
    parser.add_argument('--only', help='只生成指定 id，例如 09_zero_left')
    parser.add_argument('--text', help='覆盖指定表情文案，必须与 --only 一起使用')
    parser.add_argument('--size', type=int, default=512, help='正方形 PNG/GIF 边长；默认 512')
    parser.add_argument('--fps', type=float, help='GIF 帧率；默认 12.5')
    parser.add_argument('--duration-ms', type=int, help='GIF 循环时长；默认 3200')
    parser.add_argument('--font', help='中文 ttf/otf/ttc 字体路径')
    parser.add_argument('--font-index', type=int, default=0, help='TTC 字体集合中的字体索引')
    parser.add_argument('--outline', type=int, default=8, help='640px 工作画布上的白边宽度；0 表示关闭')
    parser.add_argument('--static-only', action='store_true', help='仅生成静态 PNG')
    parser.add_argument('--no-preview', action='store_true', help='跳过总览与关键帧')
    args = parser.parse_args()
    try:
        if not 64 <= args.size <= 1024:
            raise ValueError('size 必须在 64–1024。')
        if not 0 <= args.outline <= 20:
            raise ValueError('outline 必须在 0–20。')
        if args.text is not None and not args.only:
            raise ValueError('--text 需配合 --only。')
        config = json.loads(args.config.read_text(encoding='utf-8')); scenes = config['scenes']
        design = config['design']; defaults = config.get('defaults', {})
        ids = [s['id'] for s in scenes]
        if len(set(ids)) != len(ids):
            raise ValueError('场景 id 不可重复。')
        if any(not re.fullmatch(r'[a-zA-Z0-9_-]+', i) for i in ids):
            raise ValueError('id 只能使用英文、数字、短横线和下划线。')
        if len(scenes) != 16:
            raise ValueError('本套装固定 16 幕，四章各 4 张。')
        if args.only:
            scenes = [s.copy() for s in scenes if s['id'] == args.only]
            if not scenes:
                raise ValueError(f'没有匹配的场景：{args.only}')
        if args.text is not None:
            scenes[0]['caption'] = args.text
        renderer = StickerRenderer(design, find_font(args.font), args.font_index); renderer.font(53)
        duration = args.duration_ms if args.duration_ms is not None else defaults.get('duration_ms', 3200)
        fps = args.fps if args.fps is not None else defaults.get('fps', 12.5)
        durations = timing(duration, fps)
        output = args.output.resolve()
        folders = ('png', 'no-text', 'gif', 'gif-no-text')
        for folder in folders:
            (output/folder).mkdir(parents=True, exist_ok=True)
        records = []; previews = []; gif_frames_by_scene = []
        for scene in scenes:
            renderer.used.clear()
            captioned, clean = renderer.render(scene, 0.0, args.outline)
            captioned = captioned.resize((args.size, args.size), Image.Resampling.LANCZOS)
            clean = clean.resize((args.size, args.size), Image.Resampling.LANCZOS)
            captioned.save(output/'png'/f'{scene["id"]}.png')
            clean.save(output/'no-text'/f'{scene["id"]}.png')
            tones = audit_discipline(design, scene, clean)
            previews.append(clean.resize((250, 250), Image.Resampling.LANCZOS))
            record = {'id': scene['id'], 'chapter': scene['chapter'], 'caption': scene['caption'],
                      'action': scene['action'], 'screen': scene['screen'],
                      'screen_brief': scene['screen_brief'], 'size': [args.size, args.size],
                      'accent_tones': tones}
            frames = [captioned]; cleans = [clean]
            if not args.static_only:
                frames = []; cleans = []
                for i in range(len(durations)):
                    a, b = renderer.render(scene, i/len(durations), args.outline)
                    frames.append(a.resize((args.size, args.size), Image.Resampling.LANCZOS))
                    cleans.append(b.resize((args.size, args.size), Image.Resampling.LANCZOS))
                record['gif'] = save_gif(frames, durations, output/'gif'/f'{scene["id"]}.gif')
                record['gif_no_text'] = save_gif(cleans, durations, output/'gif-no-text'/f'{scene["id"]}.gif')
                if record['gif']['distinct_frames'] < 2 or record['gif_no_text']['distinct_frames'] < 2:
                    raise ValueError(f'{scene["id"]} 的 GIF 未产生动画。')
                print(f'{scene["chapter"]} {scene["caption"]}：GIF {record["gif"]["frames"]} 帧，'
                      f'逐帧解码比对通过，强调色 {tones or ["绿/白"]}', flush=True)
            else:
                print(f'{scene["chapter"]} {scene["caption"]}：PNG 完成，强调色 {tones or ["绿/白"]}', flush=True)
            record['assets_used'] = sorted(renderer.used)
            gif_frames_by_scene.append([frame.resize((250, 250), Image.Resampling.LANCZOS) for frame in cleans])
            records.append(record)
        if not args.only:
            if not args.no_preview:
                make_overview(renderer, output, scenes, previews, design)
                make_screens_board(renderer, output, scenes)
                if not args.static_only:
                    make_gif_overview(renderer, output, scenes, gif_frames_by_scene, durations, design)
                    make_keyframes(renderer, output, scenes, gif_frames_by_scene)
        (output/'manifest.json').write_text(json.dumps(
            {'pack': config['pack'], 'design': design, 'size': args.size,
             'outline': args.outline, 'duration_ms': sum(durations), 'fps': fps,
             'static_only': args.static_only, 'library_only': True, 'scenes': records},
            ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
        print(f'已输出 {len(scenes)} 幕表情：{output}')
    except (ValueError, TypeError, KeyError, IndexError, OSError) as error:
        parser.exit(2, f'生成失败：{error}\n')


if __name__ == '__main__':
    main()
