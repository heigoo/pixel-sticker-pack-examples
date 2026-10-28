#!/usr/bin/env python3
"""本地、确定性的机器人表情包合成器；无需联网或 AI 服务。

python3 generate.py
python3 generate.py --only 01_received --text "好的，马上来"
python3 generate.py --size 1024 --output output-hd
python3 generate.py --font /path/to/ChineseFont.ttf --font-index 0
"""
import argparse
import json
import math
import os
import re
import sys
from functools import lru_cache
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parent
BASE = 640
TRANSPARENT = (0, 0, 0, 0)
INK = '#191e1c'


def find_font(explicit=None):
    if explicit:
        path = Path(explicit).expanduser()
        if not path.is_file():
            raise ValueError(f'字体文件不存在：{path}')
        return path
    candidates = [
        ROOT/'assets'/'font.ttf',
        Path('/System/Library/Fonts/STHeiti Medium.ttc'),
        Path('/System/Library/Fonts/PingFang.ttc'),
        Path('/System/Library/Fonts/Hiragino Sans GB.ttc'),
        Path(os.environ.get('WINDIR', 'C:/Windows'))/'Fonts'/'msyhbd.ttc',
        Path(os.environ.get('WINDIR', 'C:/Windows'))/'Fonts'/'simhei.ttf',
        Path('/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc'),
        Path('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc'),
        Path('/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc'),
    ]
    for path in candidates:
        if path.is_file():
            return path
    raise ValueError('未找到中文字体。请用 --font /path/to/ChineseFont.ttf 指定有权使用的中文字体。')


class Renderer:
    def __init__(self, assets, font, font_index=0):
        self.assets = assets.resolve()
        self.font_path = str(font)
        self.font_index = font_index
        self.manifest = json.loads((assets/'manifest.json').read_text(encoding='utf-8'))

    @lru_cache(maxsize=128)
    def image(self, name):
        path = (self.assets/name).resolve()
        if self.assets not in path.parents:
            raise ValueError(f'素材必须位于 assets 文件夹内：{name}')
        with Image.open(path) as source:
            return source.convert('RGBA')

    @lru_cache(maxsize=64)
    def font(self, size):
        return ImageFont.truetype(self.font_path, size=size, index=self.font_index)

    @staticmethod
    def place(canvas, image, position, pivot=None, angle=0, scale=1, opacity=1):
        if scale <= 0 or not 0 <= opacity <= 1:
            raise ValueError('scale 必须大于 0；opacity 必须位于 0–1。')
        pivot = pivot if pivot is not None else (image.width/2, image.height/2)
        if scale != 1:
            image = image.resize((max(1,round(image.width*scale)), max(1,round(image.height*scale))),Image.Resampling.LANCZOS)
        px,py = pivot[0]*scale, pivot[1]*scale
        if opacity != 1:
            image = image.copy()
            image.putalpha(image.getchannel('A').point(lambda p: round(p*opacity)))
        radius = math.ceil(max(math.hypot(x-px,y-py) for x in (0,image.width) for y in (0,image.height)))+3
        patch = Image.new('RGBA',(radius*2,radius*2),TRANSPARENT)
        patch.alpha_composite(image,(round(radius-px),round(radius-py)))
        if angle:
            patch = patch.rotate(angle,Image.Resampling.BICUBIC,center=(radius,radius))
        dest=(round(position[0]-radius),round(position[1]-radius))
        bounds=patch.getbbox()
        if bounds and (dest[0]+bounds[0]<0 or dest[1]+bounds[1]<0 or
                       dest[0]+bounds[2]>canvas.width or dest[1]+bounds[3]>canvas.height):
            raise ValueError('素材超出工作画布，请减小 scale 或调整位置/角度。')
        canvas.alpha_composite(patch,dest)

    def character(self, spec):
        rig = spec.get('rig','front')
        if rig not in ('front','back'):
            raise ValueError('rig 目前支持 front / back；其他视角以完整透明素材提供。')
        pose = spec.get('pose',{})
        neck = pose.get('neck',[320,310])
        nx,ny = neck
        arms = pose.get('arms',[0,0])
        legs = pose.get('legs',[0,0])
        front_arms = pose.get('front_arms',[])
        result = Image.new('RGBA',(BASE,BASE),TRANSPARENT)

        def part(suffix, position, angle=0):
            meta = self.manifest['parts'][f'{rig}_{suffix}']
            self.place(result,self.image(meta['file']),position,meta['pivot'],angle)

        part('leg_left',(nx-35,ny+115),legs[0])
        part('leg_right',(nx+36,ny+115),legs[1])
        part('torso',neck)
        for i,side in enumerate(('left','right')):
            if side not in front_arms:
                part(f'arm_{side}',(nx+(-89 if i==0 else 90),ny+10),arms[i])
        head_meta = self.manifest['parts'][f'{rig}_head']
        head = self.image(head_meta['file']).copy()
        if rig == 'front':
            eyes = spec.get('eyes','normal')
            if eyes not in self.manifest['eyes']:
                raise ValueError(f'未知眼睛素材：{eyes}')
            head.alpha_composite(self.image(f'eyes/{eyes}.png'))
        offset = pose.get('head_offset',[0,0])
        self.place(result,head,(nx+offset[0],ny+offset[1]),head_meta['pivot'],pose.get('head_angle',0))
        for i,side in enumerate(('left','right')):
            if side in front_arms:
                part(f'arm_{side}',(nx+(-89 if i==0 else 90),ny+10),arms[i])
        # 整体变化作用于合成好的角色，不分别缩放头部或四肢。
        rotation = pose.get('rotation',0)
        scale = pose.get('scale',1)
        shift = pose.get('offset',[0,0])
        if rotation or scale != 1 or shift != [0,0] or 'center' in pose:
            bbox = result.getbbox()
            if not bbox:
                raise ValueError('角色合成结果为空。')
            center = pose.get('center',[(bbox[0]+bbox[2])/2+shift[0],(bbox[1]+bbox[3])/2+shift[1]])
            cropped = result.crop(bbox)
            result = Image.new('RGBA',(BASE,BASE),TRANSPARENT)
            self.place(result,cropped,center,angle=rotation,scale=scale)
        return result

    def effects(self, target, effects):
        for effect in effects:
            self.place(target,self.image(effect['asset']),effect['center'],
                       angle=effect.get('angle',0),scale=effect.get('scale',1),opacity=effect.get('opacity',1))

    def fit_caption(self, text, box=(28,548,612,621)):
        if not isinstance(text,str):
            raise ValueError('caption 必须是 JSON 字符串，例如 "caption": "收到"。')
        if not text.strip():
            return [], self.font(52), 0
        if len(text)>80:
            raise ValueError('文案过长：建议 2–8 字，最多支持 80 字。')
        probe = ImageDraw.Draw(Image.new('RGB',(1,1)))
        width, height = box[2]-box[0],box[3]-box[1]
        for size in range(53,17,-1):
            font = self.font(size)
            stroke = max(4,round(size*.12))
            lines=[]
            for paragraph in text.split('\n'):
                line=''
                for char in paragraph:
                    trial=line+char
                    bounds=probe.textbbox((0,0),trial,font=font,stroke_width=stroke)
                    if line and bounds[2]-bounds[0]>width:
                        lines.append(line); line=char
                    else:
                        line=trial
                lines.append(line)
            heights=[probe.textbbox((0,0),line,font=font,stroke_width=stroke) for line in lines]
            total=sum(b[3]-b[1] for b in heights)+max(0,len(lines)-1)*5
            if total<=height and len(lines)<=2:
                return lines,font,stroke
        raise ValueError('文案在两行内放不下，请缩短文案。')

    def caption(self, image, text):
        lines,font,stroke=self.fit_caption(text)
        if not lines:
            return image
        result=image.copy(); draw=ImageDraw.Draw(result)
        bounds=[draw.textbbox((0,0),line,font=font,stroke_width=stroke) for line in lines]
        total=sum(b[3]-b[1] for b in bounds)+max(0,len(lines)-1)*5
        y=548+(73-total)/2
        for line,b in zip(lines,bounds):
            x=(BASE-(b[2]-b[0]))/2-b[0]
            draw.text((round(x),round(y-b[1])),line,font=font,fill=INK,stroke_width=stroke,stroke_fill='white')
            y+=b[3]-b[1]+5
        return result

    def render(self, spec, outline=8):
        art=Image.new('RGBA',(BASE,BASE),TRANSPARENT)
        self.effects(art,spec.get('behind',[]))
        art.alpha_composite(self.character(spec))
        self.effects(art,spec.get('effects',[]))
        bbox=art.getbbox()
        # 不静默输出已被画布裁切的素材。
        if not bbox or min(bbox[0],bbox[1],BASE-bbox[2],BASE-bbox[3])<outline+3:
            raise ValueError(f'{spec["id"]} 的构图超出安全边界，请调小/移动姿态或道具。')
        if outline:
            alpha=art.getchannel('A').filter(ImageFilter.MaxFilter(outline*2+1))
            sticker=Image.new('RGBA',art.size,'white'); sticker.putalpha(alpha)
            sticker.alpha_composite(art); art=sticker
        return self.caption(art,spec.get('caption','')),art

    def atlas(self, results, output):
        cols=4; rows=math.ceil(len(results)/cols)
        gap=22; margin=54; card_w=340; card_h=370; header=164
        width=margin*2+cols*card_w+(cols-1)*gap
        height=header+rows*card_h+(rows-1)*gap+64
        atlas=Image.new('RGB',(width,height),'#f2f3ef'); draw=ImageDraw.Draw(atlas)
        draw.text((margin,37),'方块机器人 / 日常表情',font=self.font(43),fill='#202824')
        draw.text((margin,105),f'{len(results):02d} 个表情  ·  同一套角色部件  ·  透明 PNG  ·  可改文案',font=self.font(20),fill='#66756c')
        for index,(spec,image) in enumerate(results):
            x=margin+(index%cols)*(card_w+gap); y=header+(index//cols)*(card_h+gap)
            draw.rounded_rectangle((x,y,x+card_w,y+card_h),radius=20,fill='#ffffff')
            draw.text((x+20,y+14),f'{index+1:02d}',font=self.font(15),fill='#84988b')
            thumb=image.resize((320,320),Image.Resampling.LANCZOS)
            atlas.paste(thumb,(x+10,y+33),thumb)
        atlas.save(output/'overview.png')


def main():
    parser=argparse.ArgumentParser(description=__doc__,formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--config',type=Path,default=ROOT/'stickers.json')
    parser.add_argument('--output',type=Path,default=ROOT/'output')
    parser.add_argument('--only',help='只生成指定 id，例如 01_received')
    parser.add_argument('--text',help='覆盖指定表情文案，必须与 --only 一起使用')
    parser.add_argument('--size',type=int,default=512,help='正方形 PNG 边长；默认 512')
    parser.add_argument('--font',help='中文 ttf/otf/ttc 字体路径')
    parser.add_argument('--font-index',type=int,default=0,help='TTC 字体集合中的字体索引')
    parser.add_argument('--outline',type=int,default=8,help='640px 工作画布上的白边宽度；0 表示关闭')
    args=parser.parse_args()
    try:
        if not 64<=args.size<=4096:
            raise ValueError('--size 应介于 64 和 4096 之间。')
        if not 0<=args.outline<=20:
            raise ValueError('--outline 应介于 0 和 20 之间。')
        if args.text is not None and not args.only:
            raise ValueError('--text 必须与 --only 一起使用。')
        config=json.loads(args.config.read_text(encoding='utf-8'))
        specs=config['stickers']
        if not specs:
            raise ValueError('配置里没有表情。')
        ids=[s['id'] for s in specs]
        if len(set(ids))!=len(ids) or any(not re.fullmatch(r'[A-Za-z0-9_-]+',i) for i in ids):
            raise ValueError('id 必须唯一，且仅包含英文字母、数字、下划线或短横线。')
        if args.only:
            specs=[s.copy() for s in specs if s['id']==args.only]
            if not specs:
                raise ValueError(f'没有找到表情 id：{args.only}')
        if args.text is not None:
            specs[0]['caption']=args.text
        renderer=Renderer(ROOT/'assets',find_font(args.font),args.font_index)
        # 提前读取字体，避免生成一半后才发现字体路径不可用。
        renderer.font(53)
        rendered=[]; manifests=[]
        for spec in specs:
            captioned,clean=renderer.render(spec,args.outline)
            captioned=captioned.resize((args.size,args.size),Image.Resampling.LANCZOS)
            clean=clean.resize((args.size,args.size),Image.Resampling.LANCZOS)
            rendered.append((spec,captioned,clean))
        output=args.output.resolve()
        for folder in ('png','no-text'):
            (output/folder).mkdir(parents=True,exist_ok=True)
        for spec,captioned,clean in rendered:
            captioned.save(output/'png'/f'{spec["id"]}.png')
            clean.save(output/'no-text'/f'{spec["id"]}.png')
            manifests.append({'id':spec['id'],'caption':spec.get('caption',''),'size':list(captioned.size),
                              'mode':captioned.mode,'alpha_bbox':list(captioned.getbbox()),
                              'png':f'png/{spec["id"]}.png','no_text':f'no-text/{spec["id"]}.png'})
        renderer.atlas([(s,img) for s,img,_ in rendered],output)
        (output/'export_manifest.json').write_text(json.dumps({'font':renderer.font_path,'font_index':args.font_index,
            'base_size':BASE,'export_size':args.size,'outline':args.outline,'stickers':manifests},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        print(f'已生成 {len(rendered)} 张带字版 + {len(rendered)} 张无字版：{output}')
        print(f'总览：{output/"overview.png"}')
    except (ValueError,KeyError,FileNotFoundError,OSError,json.JSONDecodeError) as exc:
        parser.exit(2,f'生成失败：{exc}\n')


if __name__=='__main__':
    main()
