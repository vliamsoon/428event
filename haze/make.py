import numpy as np, subprocess, imageio_ffmpeg, math
from PIL import Image, ImageDraw, ImageFont, ImageFilter
W,H,FPS,N=1080,1920,30,300
F="/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"; FR="/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
f=lambda s,b=True:ImageFont.truetype(F if b else FR,s)
data=[("Serian","Sarawak",175),("Pasir Gudang","Johor",171),("Larkin","Johor",170),("Bandaraya Melaka","Melaka",167),("Nilai","N. Sembilan",165),("Bukit Rambai","Melaka",164),("Johan Setia","Selangor",164)]
rng=np.random.default_rng(1)
# haze texture
base=rng.random((H//16,W//16)); tex=Image.fromarray((base*255).astype('uint8')).resize((W*2,H),Image.BICUBIC).filter(ImageFilter.GaussianBlur(40))
tex=np.asarray(tex).astype(np.float32)/255
def ease(x): x=min(max(x,0),1); return 1-(1-x)**3
def col(v): return (255,70,40) if v>=170 else (255,140,40)
def frame(i):
    t=i/FPS
    off=int(t*60)%W
    h=tex[:,off:off+W]
    img=np.zeros((H,W,3),np.float32)
    img[:]=(38,26,20); img+=h[...,None]*np.array([120,80,45])
    im=Image.fromarray(img.clip(0,255).astype('uint8')); d=ImageDraw.Draw(im)
    def ctext(y,s,fn,c,a=1):
        w=d.textlength(s,font=fn); d.text(((W-w)/2,y),s,font=fn,fill=tuple(int(x*a+38*(1-a)) for x in c))
    if t<2.2:
        a=ease(t/0.6); sc=ease(t/0.8)
        ctext(620,"MALAYSIA",f(70),(255,220,180),a)
        ctext(720+int(40*(1-sc)),"HAZE",f(260),(255,110,50),a)
        ctext(1010,"ALERT",f(170),(255,230,210),ease((t-0.4)/0.6))
        ctext(1260,"Worst hotspots · API as at 10am, 29 Sep 2026",f(34,False),(240,210,190),ease((t-0.8)/0.6))
        if t>1.8: im=Image.blend(im,Image.new('RGB',(W,H),(38,26,20)),(t-1.8)/0.4)
    elif t<7.4:
        tt=t-2.2
        ctext(170,"TOP 7 UNHEALTHY AREAS",f(62),(255,230,210),ease(tt/0.5))
        ctext(255,"Air Pollutant Index (101–200 = Unhealthy)",f(32,False),(230,200,180),ease(tt/0.5))
        for k,(n,s,v) in enumerate(data):
            p=ease((tt-0.3-k*0.25)/0.9); y=380+k*205
            if p<=0: continue
            d.text((80,y),f"{k+1}. {n}",font=f(46),fill=(255,240,230)); d.text((80,y+56),s,font=f(30,False),fill=(230,190,160))
            bw=int((W-300)*v/200*p); d.rounded_rectangle((80,y+105,80+bw,y+160),12,fill=col(v))
            d.text((100+bw,y+104),str(int(v*p)),font=f(48),fill=(255,255,255))
        if t>7.0: im=Image.blend(im,Image.new('RGB',(W,H),(38,26,20)),(t-7.0)/0.4)
    else:
        tt=t-7.4; pulse=1+0.04*math.sin(tt*8)
        ctext(420,"MOST SERIOUS",f(64),(255,220,180),ease(tt/0.4))
        ctext(540,"SERIAN, SARAWAK",f(80),(255,240,230),ease((tt-0.1)/0.4))
        ctext(680,str(int(175*ease(tt/0.8))),f(int(360*pulse)),(255,70,40),1)
        ctext(1090,"API · UNHEALTHY",f(56),(255,150,110),ease((tt-0.3)/0.4))
        ctext(1330,"31 areas nationwide unhealthy",f(50),(255,235,220),ease((tt-0.6)/0.4))
        ctext(1420,"Wear N95 · Stay indoors · Drink water",f(40,False),(240,210,190),ease((tt-0.9)/0.4))
        ctext(1780,"Source: DOE Malaysia via The Star",f(28,False),(200,170,150),ease((tt-1)/0.4))
    return np.asarray(im)
p=subprocess.Popen([imageio_ffmpeg.get_ffmpeg_exe(),"-y","-f","rawvideo","-pix_fmt","rgb24","-s",f"{W}x{H}","-r",str(FPS),"-i","-","-c:v","libx264","-pix_fmt","yuv420p","-crf","20","malaysia_haze_10s.mp4"],stdin=subprocess.PIPE,stderr=subprocess.DEVNULL)
for i in range(N): p.stdin.write(frame(i).tobytes())
p.stdin.close(); p.wait()
for i in (30,150,270): Image.fromarray(frame(i)).resize((360,640)).save(f"prev{i}.png")
