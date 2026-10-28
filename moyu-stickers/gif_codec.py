"""透明GIF编码与逐帧验证；复用已经测试的静态项目编码器。"""

import bisect
import math
from PIL import Image, ImageChops

def value_at(track,progress):
    keys=track['keys']
    if progress<=0: return keys[0][1]
    if progress>=1: return keys[-1][1]
    index=max(0,bisect.bisect_right([k[0] for k in keys],progress)-1)
    t0,v0=keys[index]; t1,v1=keys[index+1]
    mode=track.get('interpolation','cosine')
    if mode=='step': return v0
    u=(progress-t0)/(t1-t0)
    if mode=='cosine': u=(1-math.cos(math.pi*u))/2
    return v0+(v1-v0)*u

def timing(duration_ms,fps):
    if not isinstance(duration_ms,(int,float)) or not math.isfinite(duration_ms) or not 400<=duration_ms<=8000:
        raise ValueError('动画时长必须为 400–8000 毫秒。')
    if not isinstance(fps,(int,float)) or not math.isfinite(fps) or not 2<=fps<=30:
        raise ValueError('fps 必须为 2–30。')
    # GIF 以 10ms 为单位；分配误差，避免每帧四舍五入造成总时长漂移。
    ticks=round(duration_ms/10); count=max(2,round(duration_ms*fps/1000))
    boundaries=[round(i*ticks/count) for i in range(count+1)]
    durations=[(b-a)*10 for a,b in zip(boundaries,boundaries[1:])]
    if min(durations)<=0: raise ValueError('帧间隔必须大于 0。')
    return durations

def quantize_frames(frames):
    """统一调色板、保留纯黑/纯白、独占透明索引；避免闪色与白眼透明。"""
    cols=min(8,len(frames)); rows=math.ceil(len(frames)/cols); sample_size=192
    sample=Image.new('RGB',(cols*sample_size,rows*sample_size),'white')
    for i,frame in enumerate(frames):
        thumb=frame.resize((sample_size,sample_size),Image.Resampling.LANCZOS)
        tile=Image.new('RGB',thumb.size,'white'); tile.paste(thumb,mask=thumb.getchannel('A'))
        sample.paste(tile,((i%cols)*sample_size,(i//cols)*sample_size))
    # 总览里道具占比很小，固定保留强调色，避免缩略采样把彩色吞成灰色。
    anchors=[(255,255,255),(0,0,0),(169,230,204),(244,205,112),(149,204,231),
             (237,153,151),(195,217,235),(157,183,210),(90,219,151),(236,98,105),(49,107,202)]
    learned_count=255-len(anchors)
    learned=sample.quantize(colors=learned_count,method=Image.Quantize.MEDIANCUT,dither=Image.Dither.NONE)
    learned_palette=learned.getpalette()[:learned_count*3]
    learned_palette+=([0]*(learned_count*3-len(learned_palette)))
    # 工作调色板前两项是白/黑；最后一项与黑色重复，稍后合并。
    colors=[channel for color in anchors for channel in color]+learned_palette
    reference=Image.new('P',(1,1)); reference.putpalette(colors+[0,0,0])
    final_palette=[0,0,0]+colors
    remap=list(range(1,256))+[2]
    indexed=[]
    for frame in frames:
        rgb=frame.convert('RGB')
        image=rgb.quantize(palette=reference,dither=Image.Dither.NONE)
        image=image.point(remap); image.putpalette(final_palette)
        # Pillow 的调色板查找可能把纯白近似成浅灰，显式锁定白眼/白边与纯黑。
        red,green,blue=rgb.split()
        light=ImageChops.darker(ImageChops.darker(red,green),blue)
        dark=ImageChops.lighter(ImageChops.lighter(red,green),blue)
        image.paste(1,mask=light.point(lambda c:255 if c>=254 else 0))
        image.paste(2,mask=dark.point(lambda c:255 if c<=1 else 0))
        alpha=frame.getchannel('A')
        # GIF 不支持半透明。使用二值 alpha，白色贴纸边保留为不透明像素。
        image.paste(0,mask=alpha.point(lambda a:255 if a<128 else 0))
        image.info['transparency']=0
        indexed.append(image)
    return indexed

def equal_visible(actual,expected):
    aa=actual.getchannel('A'); ea=expected.getchannel('A')
    if ImageChops.difference(aa,ea).getbbox(): return False
    diff=ImageChops.difference(actual.convert('RGB'),expected.convert('RGB'))
    return ImageChops.multiply(diff,ea.convert('RGB')).getbbox() is None

def inspect_gif(path,expected=None,durations=None):
    total=0; count=0; unique=set(); expected_index=0
    if durations:
        expected_starts=[0]
        for d in durations: expected_starts.append(expected_starts[-1]+d)
    with Image.open(path) as gif:
        if gif.format!='GIF' or gif.info.get('loop')!=0:
            raise ValueError(f'{path.name} 不是无限循环 GIF。')
        size=gif.size
        while True:
            try: gif.seek(count)
            except EOFError: break
            frame=gif.convert('RGBA'); duration=gif.info.get('duration',0)
            if duration<=0 or gif.disposal_method!=2:
                raise ValueError(f'{path.name} 帧时长或清除方式错误。')
            if expected is not None:
                # 编码器可以合并完全相同的相邻帧；逐时间段核对合并前的目标帧。
                while expected_index<len(expected) and expected_starts[expected_index]<total+duration:
                    target=expected[expected_index].convert('RGBA')
                    if not equal_visible(frame,target):
                        raise ValueError(f'{path.name} 第 {count+1} 帧与目标不符，可能出现残影或透明度错误。')
                    expected_index+=1
            import hashlib
            unique.add(hashlib.sha256(frame.tobytes()).digest())
            total+=duration; count+=1
        if expected is not None and (total!=sum(durations) or expected_index!=len(expected)):
            raise ValueError(f'{path.name} 总时长不一致。')
    return {'file':path.name,'size':list(size),'frames':count,'distinct_frames':len(unique),
            'duration_ms':total,'loop':0,'disposal':2,'bytes':path.stat().st_size,
            'pixel_decode_verified':expected is not None}

def save_gif(frames,durations,path):
    indexed=quantize_frames(frames)
    indexed[0].save(path,save_all=True,append_images=indexed[1:],duration=durations,
                    loop=0,transparency=0,background=0,disposal=2,optimize=False)
    return inspect_gif(path,indexed,durations)
