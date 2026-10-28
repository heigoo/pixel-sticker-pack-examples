#!/usr/bin/env python3
"""素材库构建：屏幕表情静态帧 + 道具目录登记（从 theme.py 读取主题内容）。

python3 build_assets.py
"""
from pathlib import Path
import json

from theme import SCREENS, NEW_PROPS, screen_image

ROOT = Path(__file__).resolve().parent
SCREENS_DIR = ROOT / 'assets' / 'screens'
PROPS = ROOT / 'assets' / 'props'


def main():
    # 1) 道具：生成原生 PNG 并登记目录（保留既有条目）
    catalog_path = PROPS / 'catalog.json'
    catalog = json.loads(catalog_path.read_text(encoding='utf-8'))
    known = {item['id'] for item in catalog['assets']}
    for prop_id, builder, name, brief in NEW_PROPS:
        im = builder()
        im.save(PROPS / f'{prop_id}.png')
        if prop_id not in known:
            catalog['assets'].append({'id': prop_id, 'file': f'props/{prop_id}.png',
                                      'name': name, 'brief': brief,
                                      'logical_size': [im.width-2, im.height-2]})
    catalog_path.write_text(json.dumps(catalog, ensure_ascii=False, indent=1)+'\n', encoding='utf-8')

    # 2) 屏幕：落盘静态帧（t=0）并重写目录
    SCREENS_DIR.mkdir(parents=True, exist_ok=True)
    entries = []
    for mode_id, name, brief, colors, _fn in SCREENS:
        screen_image(mode_id, 0.0).save(SCREENS_DIR / f'{mode_id}.png')
        entries.append({'id': mode_id, 'file': f'screens/{mode_id}.png', 'name': name,
                        'brief': brief, 'colors': list(colors), 'logical_size': [70, 36]})
    (SCREENS_DIR / 'catalog.json').write_text(json.dumps(
        {'panel_size': [70, 36], 'palette': catalog.get('palette', {}), 'assets': entries},
        ensure_ascii=False, indent=1)+'\n', encoding='utf-8')
    print(f'道具 +{len(NEW_PROPS)}，屏幕 {len(SCREENS)} 幕已登记')


if __name__ == '__main__':
    main()
