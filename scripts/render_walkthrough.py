"""Reproducible, staged product walkthrough using real example files and output.

Run: uv run --no-project --with pillow python scripts/render_walkthrough.py
"""
from pathlib import Path
import re
import subprocess
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'docs-site/static/assets/walkthrough'
QA = ROOT / 'target/glyf/walkthrough'
EXAMPLE = ROOT / 'examples/sales_dashboard'
W, H, FPS, DURATION = 1600, 940, 20, 42
FONT_DIR = ROOT / 'docs-site/static/dashboards/sales-dashboard/assets/fonts'
FONTS = {}
def font(size, mono=False, bold=False):
    key = (size, mono, bold)
    if key not in FONTS:
        path = '/System/Library/Fonts/Supplemental/Andale Mono.ttf' if mono else str(FONT_DIR / ('HankenGrotesk-Bold.ttf' if bold else 'HankenGrotesk-Regular.ttf'))
        FONTS[key] = ImageFont.truetype(path, size)
    return FONTS[key]

BG, PANEL, MUTED, TEXT, ACCENT = '#101114', '#1e1e1e', '#9da5b4', '#e8edf5', '#2563eb'
BLUE_TEXT = '#93c5fd'
FILES = ['models/fct_sales.sql', 'visualisations/monthly_revenue.ggsql', 'dashboards/sales.yml']
CODES = [(EXAMPLE / f).read_text().splitlines() for f in FILES]
STARTS = [0, 6, 13, 20, 28]
TITLES = ['Start with your dbt model.', 'Turn a query into a chart.', 'Compose the dashboard in YAML.', 'Build it from your terminal.', 'Your data pipeline, made visible.']
SUBS = ['A familiar project. SQL models, versioned alongside your data.', 'Reference the model, then declare how the result should look.', 'Arrange the monthly, channel, and regional views in one file.', 'Validate, render, assemble, and export with a single command.', 'The rendered Sales Dashboard from the included example.']
SHOT = Image.open(OUT / 'sales-dashboard.png').convert('RGB')

def ease(x):
    x = max(0, min(1, x))
    return x*x*(3-2*x)

def draw_frame(t):
    stage = max(i for i, s in enumerate(STARTS) if t >= s)
    local = t - STARTS[stage]
    im = Image.new('RGB', (W, H), BG)
    d = ImageDraw.Draw(im)
    def txt(x, y, s, size=20, color=TEXT, mono=False, bold=False):
        s = s.replace('⌄', 'v').replace('⑂', 'git').replace('▏', '|')
        if s.startswith('✓'):
            d.line((x+1,y+size*.55,x+size*.3,y+size*.8,x+size*.75,y+size*.2),fill=color,width=2)
            s = ' ' + s[1:]
        s = s.replace('✓', ' ')
        d.text((x,y), s, font=font(size,mono,bold), fill=color)
    def box(coords, fill, radius=0, outline=None):
        d.rounded_rectangle(coords,radius,fill=fill,outline=outline)
    txt(48, 28, 'glyf', 30, BLUE_TEXT, bold=True)
    txt(128, 37, 'Sales dashboard walkthrough', 18, MUTED)
    txt(48, 77, TITLES[stage], 38, bold=True)
    txt(50, 130, SUBS[stage], 21, MUTED)
    box((48,184,1552,894), PANEL, 13, '#354055')
    for i,c in enumerate(['#fb746e','#edbf5b','#72cc85']):
        d.ellipse((69+i*21,204,80+i*21,215),fill=c)
    if stage < 4:
        txt(630,197,'sales_dashboard — Visual Studio Code',16,MUTED)
        box((49,232,98,868),'#181818')
        # VS Code activity bar: explorer, search, source control, extensions.
        d.rectangle((61,258,77,278),outline=TEXT,width=2)
        d.rectangle((67,264,83,284),fill='#181818',outline=TEXT,width=2)
        d.ellipse((61,313,77,329),outline=MUTED,width=2)
        d.line((75,327,84,336),fill=MUTED,width=2)
        d.line((66,366,66,386),fill=MUTED,width=2)
        d.line((66,379,80,372,80,366),fill=MUTED,width=2)
        for cx,cy in [(66,364),(66,388),(80,364)]:
            d.ellipse((cx-3,cy-3,cx+3,cy+3),fill='#181818',outline=MUTED,width=2)
        for x,y in [(61,417),(61,429),(73,429),(76,413)]:
            d.rectangle((x,y,x+8,y+8),outline=MUTED,width=2)
        d.line((49,250,49,290),fill=ACCENT,width=3)
        box((99,232,386,868),'#181818')
        txt(120,251,'EXPLORER',13,MUTED,bold=True)
        txt(119,288,'⌄  SALES_DASHBOARD',16,TEXT,bold=True)
        tree = [('⌄  models',None),('    fct_sales.sql',0),('    sources.yml',None),('⌄  visualisations',None),('    monthly_revenue.ggsql',1),('    channel_revenue.ggsql',None),('    regional_revenue.ggsql',None),('⌄  dashboards',None),('    sales.yml',2),('›  seeds',None),('   dbt_project.yml',None),('   glyf.yml',None),('   profiles.yml',None)]
        selected = min(stage,2)
        for i,(label,idx) in enumerate(tree):
            y=324+i*32
            if idx == selected:
                box((100,y-3,385,y+27),'#16345b')
                d.line((100,y-3,100,y+27),fill=ACCENT,width=2)
            txt(120,y,label,17,TEXT if idx==selected else '#a4afc1')
        tabx=387
        for i,name in enumerate(['fct_sales.sql','monthly_revenue.ggsql','sales.yml']):
            width=[236,342,194][i]
            box((tabx,232,tabx+width,277), PANEL if i==selected else '#2d2d2d')
            d.line((tabx+width,232,tabx+width,277),fill='#111111')
            # Full rectangular tabs, file-type marks and close controls.
            txt(tabx+12,245,'{}' if i==2 else '#',16,BLUE_TEXT,True)
            txt(tabx+42,245,name,16, TEXT if i==selected else MUTED,True)
            if i==selected:
                cx=tabx+width-19
                d.line((cx-4,250,cx+4,258),fill=TEXT,width=1)
                d.line((cx+4,250,cx-4,258),fill=TEXT,width=1)
            tabx+=width
        txt(412,291,FILES[selected].replace('/', '  ›  '),15,MUTED)
        lineheight=23 if selected==2 else 31
        for n,line in enumerate(CODES[selected]):
            y=334+n*lineheight
            if stage==3 and y>520: break
            # Select the defining reference/grammar/layout lines in each chapter.
            focus = (selected==0 and n==6) or (selected==1 and n in [1,4,5]) or (selected==2 and (n==9 or n>=15))
            if focus and local>1:
                box((446,y-1,1517,y+lineheight-1),'#20334f')
            txt(414,y,str(n+1).rjust(2),17,'#58667c',True)
            x=468
            for token in re.findall(r"'[^']*'|\b\w+\b|[^\w']+",line):
                color=TEXT
                if token.startswith("'"): color='#e5b28c'
                elif token.upper() in {'SELECT','FROM','GROUP','BY','AS','VISUALISE','DRAW','LABEL'}: color='#bdadf3'
                elif token in {'ref','source','sum','line'}: color='#82cddc'
                elif selected==2 and token in {'name','title','description','tags','layout','columns','groups','charts'}: color='#82cddc'
                txt(x,y,token,19,color,True)
                x+=d.textlength(token,font=font(19,True))
        ty=550 if stage==3 else 792
        box((388,ty,1550,869),'#1e1e1e')
        d.line((388,ty,1550,ty),fill='#364055')
        txt(412,ty+15,'TERMINAL',13,TEXT,bold=True)
        txt(523,ty+15,'OUTPUT     PROBLEMS',13,MUTED)
        txt(1407,ty+15,'zsh   +',14,MUTED)
        txt(412,ty+52,'sales_dashboard  ›',18,BLUE_TEXT,True)
        if stage==3:
            cmd='uv run glyf build'
            count=min(len(cmd),max(0,int((local-.5)*16)))
            txt(636,ty+52,cmd[:count],20,TEXT,True)
            if local<2 and int(t*3)%2==0: box((636+count*12,ty+53,646+count*12,ty+77),ACCENT)
            outputs=['✓ validated project','✓ rendered chart artifacts','✓ generated dashboard HTML','✓ exported static site']
            for j,line in enumerate(outputs):
                if local>2+j*.65: txt(412,ty+96+j*31,line,20,BLUE_TEXT,True)
            if local>5:
                txt(412,ty+246,'target/glyf/site/dashboards/sales.html',19,'#82cddc',True)
                d.line((412,ty+271,853,ty+271),fill='#82cddc')
        else:
            txt(636,ty+52,'▏',18,ACCENT,True)
        box((49,870,1551,892),ACCENT)
        txt(64,872,'⑂ main     ✓ 0 errors',13,TEXT)
        txt(1270,872,'UTF-8    '+('YAML' if selected==2 else 'SQL'),13,TEXT)
        # Visible pointer moves between explorer files and the built output.
        targets=[(236,367),(282,463),(217,591),(842,807)]
        prev=targets[max(0,stage-1)]
        dest=targets[stage]
        p=ease(local/.8)
        cx=prev[0]+(dest[0]-prev[0])*p; cy=prev[1]+(dest[1]-prev[1])*p
        if local<1.3:
            r=12+10*ease((local-.8)/.5)
            d.ellipse((cx-r,cy-r,cx+r,cy+r),outline=ACCENT,width=2)
        d.polygon([(cx,cy),(cx+3,24+cy),(cx+9,cy+17),(cx+16,cy+28),(cx+21,cy+25),(cx+14,cy+14),(cx+23,cy+13)],fill='#f4f7fb',outline='#101624')
    else:
        txt(168,199,'Sales Dashboard',16,TEXT)
        box((449,195,1252,222),'#101620',6)
        txt(476,199,'target/glyf/site/dashboards/sales.html',15,MUTED,True)
        # First show the real dashboard at readable size, pan to the third chart,
        # then pull back to show the entire artifact.
        zoom=ease((local-9)/2)
        scale=(1502/SHOT.width)*(1-zoom)+(658/SHOT.height)*zoom
        sw,sh=round(SHOT.width*scale),round(SHOT.height*scale)
        shot=SHOT.resize((sw,sh),Image.Resampling.LANCZOS)
        view=Image.new('RGB',(1502,660),'#edf0f4')
        pan=ease((local-3)/4)*(sh-660)*(1-zoom)
        view.paste(shot,((1502-sw)//2,-round(max(0,pan))))
        im.paste(view,(49,232))
        d=ImageDraw.Draw(im)
    # Chapter navigation belongs to the player so viewers can seek to a stage.
    return im

if __name__ == '__main__':
    OUT.mkdir(parents=True, exist_ok=True)
    QA.mkdir(parents=True, exist_ok=True)
    for t in [3,9,16,25,30,35,40]:
        draw_frame(t).save(QA / f'frame-{t:02d}.png')
    draw_frame(9).save(OUT / 'poster.png')
    cmd=['ffmpeg','-y','-hide_banner','-loglevel','error','-f','rawvideo','-vcodec','rawvideo','-pix_fmt','rgb24','-s',f'{W}x{H}','-r',str(FPS),'-i','-','-an','-c:v','libx264','-preset','fast','-crf','19','-pix_fmt','yuv420p','-movflags','+faststart',str(OUT/'glyf-sales-walkthrough.mp4')]
    proc=subprocess.Popen(cmd,stdin=subprocess.PIPE)
    for i in range(DURATION*FPS):
        proc.stdin.write(draw_frame(i/FPS).tobytes())
    proc.stdin.close()
    if proc.wait(): raise RuntimeError('Video encoding failed')
    print(OUT/'glyf-sales-walkthrough.mp4')
