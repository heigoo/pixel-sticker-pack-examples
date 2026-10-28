# TRAE宝像素表情包 · 示例项目

本仓库包含 **TRAE宝像素表情包** 锻造流水线的两个示例项目，展示如何使用 [pixel-sticker-pack](https://github.com/heigoo/pixel-sticker-pack) 技能从角色参考图到成品表情包的完整过程。

## 项目结构

每个示例项目都是独立的表情包工程，采用「原图拆件 ＋ 像素图形绘制 ＋ Python/Pillow 合成」流水线：

```
<项目>/
├── assets/
│   ├── parts/        # 角色拆件（头/躯干/四肢 PNG）
│   ├── screens/      # 屏幕表情素材（每款表情独立）
│   └── props/        # 像素道具素材库（含 catalog.json）
├── output/           # 渲染成品（总览图/关键帧/清单）
├── scenes.json       # 每款表情的 JSON 配置（姿势/眼睛/道具/动作轨道/文案）
├── lib_base.py       # 基础绘制库
├── rig.py            # 骨架/关节/装配
├── render.py         # 渲染入口
├── gif_codec.py      # GIF 编码（稳定调色板 + 独立透明 + disposal=2）
├── build_assets.py   # 素材构建脚本
├── theme.py          # 主题配色
└── test.py           # 校验脚本
```

## 摸鱼日常（moyu-stickers）

16 款「打工人摸鱼」主题表情，覆盖周一摸鱼、开小差、装忙、被逮到、下班、TGIF 等场景。

- 屏幕表情总览：`moyu-stickers/output/screens-overview.png`
- 关键帧：`moyu-stickers/output/keyframes-1.png`、`keyframes-2.png`
- 成品总览：`moyu-stickers/output/overview.png`
- 场景配置：`moyu-stickers/scenes.json`

## AI 编程搭档（coding-stickers）

16 款「程序员的日常」主题表情，覆盖新需求、自动补全、复制粘贴、编译失败、代码评审、冲突、上线、下班等场景。

- 屏幕表情总览：`coding-stickers/output/screens-overview.png`
- 关键帧：`coding-stickers/output/keyframes-1.png`、`keyframes-2.png`
- 成品总览：`coding-stickers/output/overview.png`
- 场景配置：`coding-stickers/scenes.json`

## 相关仓库

- 技能本体：[pixel-sticker-pack](https://github.com/heigoo/pixel-sticker-pack) —— 安装后即可在 Trae 中生成新的表情包
- 本项目两个示例即由该技能产出

## 许可

[MIT License](https://github.com/heigoo/pixel-sticker-pack/blob/main/LICENSE) · Copyright (c) 2026 heigoo
