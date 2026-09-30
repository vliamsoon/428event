import numpy as np, subprocess, imageio_ffmpeg, math, wave
from PIL import Image, ImageDraw, ImageFont, ImageFilter
W,H,FPS,N,SR=1080,1920,30,300,44100
BPM=120; BEAT=60/BPM
ZH="/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc"; EN="/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf"
z=lambda s:ImageFont.truetype(ZH,s); e=lambda s:ImageFont.truetype(EN,s)
GOLD=(214,172,92); IVORY=(244,236,220); RED=(178,34,40); BG=(22,17,14)
def ease(x): x=min(max(x,0),1); return 1-(1-x)**3
def back(x):
    x=min(max(x,0),1); c=1.7; return 1+(c+1)*(x-1)**3+c*(x-1)**2
# ---- crane path (cubic beziers) ----
def bez(p,n=80):
    p=np.array(p,float); t=np.linspace(0,1,n)[:,None]
    return ((1-t)**3*p[0]+3*(1-t)**2*t*p[1]+3*(1-t)*t**2*p[2]+t**3*p[3])
neck=np.vstack([bez([(560,1300),(380,1100),(700,900),(560,700)]),bez([(560,700),(430,520),(520,430),(600,440)])])
body=np.vstack([bez([(560,1300),(820,1180),(900,1400),(760,1520)]),bez([(760,1520),(620,1600),(470,1500),(560,1300)])])
wing=[bez([(600,1320),(760,1300),(820,1420),(700,1500)],40)]
legs=[np.array([(640,1560),(625,1610)]),np.array([(700,1550),(715,1610)])]
def polyline(d,pts,p,c,w):
    k=max(2,int(len(pts)*p)); d.line([tuple(x) for x in pts[:k]],fill=c,width=w,joint="curve")
# timeline (beats): 0 intro, 4 crane draw, 10 meaning, 16 closing
events_click=[]; events_whoosh=[]
def T(b): return b*BEAT
def frame(i):
    t=i/FPS; b=t/BEAT
    im=Image.new("RGB",(W,H),BG); d=ImageDraw.Draw(im)
    # radial glow pulsing with beat
    pulse=math.exp(-((b%1))*6)
    g=Image.new("L",(W,H),0); gd=ImageDraw.Draw(g); r=520+40*pulse
    gd.ellipse((W/2-r,960-r,W/2+r,960+r),fill=int(60+30*pulse)); g=g.filter(ImageFilter.GaussianBlur(160))
    im=Image.composite(Image.new("RGB",(W,H),(90,62,30)),im,g); d=ImageDraw.Draw(im)
    # gold frame lines sliding in
    fp=ease(b/2)
    d.line((60,120,60+int(960*fp),120),fill=GOLD,width=3); d.line((1020,1800,1020-int(960*fp),1800),fill=GOLD,width=3)
    def ct(y,s,f,c,a,dy=0):
        if a<=0: return
        col=tuple(int(c[j]*a+BG[j]*(1-a)) for j in range(3))
        w=d.textlength(s,font=f); d.text(((W-w)/2,y+dy*(1-a)),s,font=f,fill=col)
    if b<4:
        for k,ch in enumerate("仙鹤衔灵芝"):
            a=ease((b-0.5-k*0.5)/0.4); s=back((b-0.5-k*0.5)/0.4)
            if a>0:
                f=z(int(170*max(s,0.01))); w=d.textlength(ch,font=f)
                d.text((W/2-w/2,260+k*260+(170-170*s)/2),ch,font=f,fill=tuple(int(IVORY[j]*a+BG[j]*(1-a)) for j in range(3)))
        ct(1650,"CRANE · LINGZHI · BLESSING",e(38),GOLD,ease((b-3)/0.5),30)
    elif b<12:
        p=(b-4)
        polyline(d,neck,ease(p/2),IVORY,26)
        polyline(d,body,ease((p-1)/2),IVORY,22)
        for wl in wing: polyline(d,wl,ease((p-2)/1),GOLD,10)
        for l in legs: polyline(d,l,ease((p-2.5)/1),GOLD,10)
        hp=back((p-2)/0.5)
        if hp>0:
            d.polygon([(600,420),(760,470),(600,470)],fill=GOLD)  # beak
            d.ellipse((560-40*hp+40,410-30*hp+30,620,470),fill=IVORY)
            d.ellipse((565,405,605,425),fill=RED)
        lp=back((p-3)/0.5)
        if lp>0:  # lingzhi
            cx,cy,r=780,330,70*lp
            d.line((720,455,780,340),fill=GOLD,width=8)
            d.pieslice((cx-r,cy-r*0.7,cx+r,cy+r*0.7),180,360,fill=RED)
        ct(1640,"想要长寿" if b<8 else "想要吉祥",z(90),IVORY,ease(((b-6) if b<8 else (b-8))/0.4),40)
        ct(1745,"仙鹤 + 灵芝" if b<8 else "寓意，做进器物里",z(46),GOLD,ease(((b-6.5) if b<8 else (b-8.5))/0.4),30)
    else:
        p=b-12
        ct(560,"古人把心里想说的好话",z(72),IVORY,ease(p/0.5),50)
        ct(700,"做成一件东西",z(110),GOLD,ease((p-1)/0.5),50)
        ct(880,"摆在那里",z(72),IVORY,ease((p-2)/0.5),50)
        rp=ease((p-3)/0.6); d.line((W/2-300*rp,1060,W/2+300*rp,1060),fill=GOLD,width=3)
        ct(1110,"Blessings, made into objects.",e(44),IVORY,ease((p-3.4)/0.5),20)
        s=back((p-4.5)/0.5)
        if s>0:
            d.rounded_rectangle((W/2-60*s,1300-60*s,W/2+60*s,1300+60*s),14,fill=RED)
            f=z(int(70*s)); w=d.textlength("福",font=f); d.text((W/2-w/2,1300-40*s),"福",font=f,fill=IVORY)
    # flash on scene cuts
    for cut in (4,12):
        if 0<=b-cut<0.25: im=Image.blend(im,Image.new("RGB",(W,H),IVORY),0.5*(1-(b-cut)/0.25))
    return np.asarray(im)
# ---- audio ----
L=int(SR*10); a=np.zeros(L); tt=np.arange(L)/SR
def add(sig,at,g=1):
    s=int(at*SR); n=min(len(sig),L-s)
    if n>0: a[s:s+n]+=sig[:n]*g
def kick():
    t=np.arange(int(SR*.35))/SR; f=50+120*np.exp(-t*30)
    return np.sin(2*np.pi*np.cumsum(f)/SR)*np.exp(-t*9)
def hat():
    t=np.arange(int(SR*.05))/SR; n=np.random.randn(len(t)); n=np.diff(n,prepend=0)
    return n*np.exp(-t*80)*0.25
def click():
    t=np.arange(int(SR*.03))/SR; return (np.sin(2*np.pi*2400*t)+0.5*np.random.randn(len(t)))*np.exp(-t*250)*0.5
def whoosh(dur=.5):
    n=int(SR*dur); t=np.arange(n)/SR; x=np.random.randn(n)
    # sweep via simple one-pole lowpass with rising cutoff
    y=np.zeros(n); c=np.linspace(.02,.35,n); acc=0
    for k in range(n): acc+=c[k]*(x[k]-acc); y[k]=acc
    env=np.sin(np.pi*t/dur)**2; return y*env*1.4
def bell(f=880):
    t=np.arange(int(SR*1.5))/SR; return (np.sin(2*np.pi*f*t)+.4*np.sin(2*np.pi*f*2.76*t))*np.exp(-t*3)*0.25
def pad():
    return sum(np.sin(2*np.pi*f*tt) for f in (110,164.8,220))*0.05*np.clip(tt/1.5,0,1)*np.clip((10-tt)/1,0,1)
a+=pad()
np.random.seed(2)
for k in range(20):
    add(kick(),T(k),0.9)
    add(hat(),T(k+0.5),1)
for k in range(5): add(click(),T(0.5+k*0.5))           # title chars
add(whoosh(),T(4)-0.35,1); add(whoosh(),T(12)-0.35,1)  # scene movement
add(whoosh(.4),T(5),0.5); add(whoosh(.4),T(6),0.5)      # neck/body strokes
for bt in (6,7,6.5,8,8.5,12,13,14,15,15.4): add(click(),T(bt))
add(bell(1320),T(6),1); add(bell(990),T(16.5),1.2)
a=a/np.max(np.abs(a))*0.9
with wave.open("audio.wav","wb") as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes((a*32767).astype(np.int16).tobytes())
ff=imageio_ffmpeg.get_ffmpeg_exe()
p=subprocess.Popen([ff,"-y","-f","rawvideo","-pix_fmt","rgb24","-s",f"{W}x{H}","-r",str(FPS),"-i","-","-i","audio.wav","-c:v","libx264","-pix_fmt","yuv420p","-crf","20","-c:a","aac","-b:a","192k","-shortest","crane_blessing_10s.mp4"],stdin=subprocess.PIPE,stderr=subprocess.DEVNULL)
for i in range(N): p.stdin.write(frame(i).tobytes())
p.stdin.close(); p.wait()
for i in (50,160,290): Image.fromarray(frame(i)).resize((360,640)).save(f"prev{i}.png")
