import json, math, os, shutil, subprocess, threading, tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance, ImageTk

ROOT = Path(__file__).resolve().parent.parent
BIN = ROOT / "bin"
TEMP = BIN / "temp"
SETTINGS = BIN / "layout_settings.json"
VIDEO_DIR = ROOT / "input" / "video"
BG_DIR = ROOT / "input" / "background"
OUT_DIR = ROOT / "output"
W, H = 1080, 1920
VIDEO_EXTS = {".mp4", ".mov", ".mkv", ".avi", ".webm", ".m4v", ".mpeg", ".mpg"}
IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".webp", ".bmp"}

DEFAULTS = {
 "thumbnail": {
   "title": [70, 100, 940, 300],
   "part": [300, 1570, 480, 150]
 },
 "video": {
   "title": [70, 100, 940, 270],
   "video": [70, 590, 940, 530],
   "part": [300, 1540, 480, 150]
 }
}
COLORS = {"title":"#27d9ff", "video":"#ffd34d", "part":"#d6a3ff"}

def load_settings():
    try:
        data = json.loads(SETTINGS.read_text(encoding="utf-8"))
        for k in DEFAULTS:
            if k not in data: data[k] = DEFAULTS[k]
            if isinstance(data.get(k), dict): data[k].pop("divider", None)
        return data
    except Exception:
        return json.loads(json.dumps(DEFAULTS))

def save_settings(data):
    SETTINGS.parent.mkdir(parents=True, exist_ok=True)
    SETTINGS.write_text(json.dumps(data, indent=2), encoding="utf-8")

def one_file(folder, exts, label):
    files = [p for p in folder.iterdir() if p.is_file() and p.suffix.lower() in exts]
    if len(files) != 1:
        raise RuntimeError(f"Put exactly one {label} in:\\n{folder}\\n\\nFound: {len(files)}")
    return files[0]

def font_path(bold=True, italic=False):
    candidates = []
    if os.name == "nt":
        if bold and italic: candidates += [r"C:\Windows\Fonts\arialbi.ttf"]
        if bold: candidates += [r"C:\Windows\Fonts\arialbd.ttf"]
        if italic: candidates += [r"C:\Windows\Fonts\ariali.ttf"]
        candidates += [r"C:\Windows\Fonts\arial.ttf"]
    candidates += ["/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
                   "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"]
    for p in candidates:
        if os.path.exists(p): return p
    return None

def fit_font(draw, text, box, bold=True, italic=False, max_size=150, min_size=12, margin=24):
    path = font_path(bold, italic)
    x,y,w,h = box
    for size in range(max_size, min_size-1, -2):
        try: f = ImageFont.truetype(path, size) if path else ImageFont.load_default()
        except Exception: f = ImageFont.load_default()
        bb = draw.textbbox((0,0), text, font=f, stroke_width=max(1,size//22))
        if bb[2]-bb[0] <= w-margin*2 and bb[3]-bb[1] <= h-margin*2:
            return f
    return ImageFont.truetype(path, min_size) if path else ImageFont.load_default()

def fit_bg(img, size=(W,H), blur=False, darken=False):
    img = img.convert("RGB")
    w,h = size
    scale = max(w/img.width, h/img.height)
    img = img.resize((int(img.width*scale), int(img.height*scale)), Image.Resampling.LANCZOS)
    left=(img.width-w)//2; top=(img.height-h)//2
    img=img.crop((left,top,left+w,top+h))
    if blur: img=img.filter(ImageFilter.GaussianBlur(24))
    if darken: img=ImageEnhance.Brightness(img).enhance(.55)
    return img

def draw_fancy_title(draw, text, box):
    """Draw a title inside a dark, translucent rounded panel with metallic text."""
    x, y, w, h = [int(v) for v in box]
    # The title's background is part of the exported design, not an editor guide.
    radius = max(12, min(34, int(h * 0.16)))
    draw.rounded_rectangle(
        (x + 5, y + 8, x + w + 5, y + h + 8),
        radius=radius, fill=(0, 0, 0, 150)
    )
    draw.rounded_rectangle(
        (x, y, x + w, y + h), radius=radius,
        fill=(5, 16, 34, 218), outline=(47, 211, 255, 245), width=max(2, int(W * 0.0025))
    )
    # Subtle inner highlight gives the panel a polished, metallic-tech look.
    draw.rounded_rectangle(
        (x + 5, y + 5, x + w - 5, y + h - 5),
        radius=max(8, radius - 5), outline=(180, 232, 255, 100), width=2
    )
    text_box = (x + 18, y + 10, max(1, w - 36), max(1, h - 20))
    f = fit_font(draw, text, text_box, True, False, 150, 14, 24)
    bb = draw.textbbox((0, 0), text, font=f, stroke_width=max(2, int(f.size * 0.05)))
    tw = bb[2] - bb[0]; th = bb[3] - bb[1]
    tx = text_box[0] + (text_box[2] - tw) // 2 - bb[0]
    ty = text_box[1] + (text_box[3] - th) // 2 - bb[1]
    # Deep shadow, dark outline, then pale blue-white metallic face.
    draw.text((tx + 4, ty + 6), text, font=f, fill=(0, 0, 0, 245),
              stroke_width=max(5, int(f.size * 0.07)), stroke_fill=(0, 0, 0, 245))
    draw.text((tx, ty), text, font=f, fill=(238, 248, 255, 255),
              stroke_width=max(4, int(f.size * 0.055)), stroke_fill=(8, 24, 48, 255))
    draw.text((tx, ty + 2), text, font=f, fill=(170, 220, 255, 255),
              stroke_width=1, stroke_fill=(28, 93, 151, 255))

def draw_part(draw, text, box):
    x,y,w,h=box
    radius=max(12,int(h*.22))
    draw.rounded_rectangle((x,y,x+w,y+h),radius=radius,fill=(8,15,28,225),outline=(245,250,255,255),width=max(3,int(W*.004)))
    f=fit_font(draw,text,box,True,True,100,12,34)
    bb=draw.textbbox((0,0),text,font=f,stroke_width=2)
    tw=bb[2]-bb[0]; th=bb[3]-bb[1]
    tx=x+(w-tw)//2-bb[0]; ty=y+(h-th)//2-bb[1]
    draw.text((tx+2,ty+3),text,font=f,fill=(0,0,0,255),stroke_width=3,stroke_fill=(0,0,0,255))
    draw.text((tx,ty),text,font=f,fill=(255,220,66,255),stroke_width=2,stroke_fill=(64,37,0,255))

def make_overlay(title, part, layout, include_video_box=False):
    im=Image.new("RGBA",(W,H),(0,0,0,0)); d=ImageDraw.Draw(im)
    if "title" in layout: draw_fancy_title(d,title,layout["title"])
    if "part" in layout: draw_part(d,part,layout["part"])
    return im

def resize_cover(img, box):
    x,y,w,h=box
    img=img.convert("RGBA")
    scale=max(w/img.width,h/img.height)
    img=img.resize((max(1,int(img.width*scale)),max(1,int(img.height*scale))),Image.Resampling.LANCZOS)
    l=(img.width-w)//2; t=(img.height-h)//2
    return img.crop((l,t,l+w,t+h)),(x,y)

class LayoutEditor(tk.Toplevel):
    def __init__(self, master, kind, background, title, settings):
        super().__init__(master)
        self.kind=kind; self.background=background.copy(); self.title_text=title
        self.settings=settings; self.layout=json.loads(json.dumps(settings[kind]))
        self.layout.pop("divider", None)
        self.title("Thumbnail Layout Editor" if kind=="thumbnail" else "Video Overlay Editor")
        self.geometry("760x860"); self.minsize(600,650)
        self.scale=0.30; self.canvas_w=int(W*self.scale); self.canvas_h=int(H*self.scale)
        self._base_image=None
        outer=ttk.Frame(self,padding=10); outer.pack(fill="both",expand=True)
        ttk.Label(outer,text=self.title(),font=("Segoe UI",13,"bold")).pack(anchor="w")
        ttk.Label(outer,text="Drag a box to move it. Drag its bottom-right handle to resize. Ghost labels are editor-only.",wraplength=720).pack(anchor="w",pady=(2,8))
        # Reserve a dedicated footer first so Save/Cancel can never be pushed off-screen.
        bar=ttk.Frame(outer)
        bar.pack(side="bottom", fill="x", pady=(8,0))
        actions=ttk.Frame(bar)
        actions.pack(anchor="center")
        self.save_button=ttk.Button(actions,text="Save Layout",command=self.save)
        self.save_button.pack(side="left",padx=6,ipadx=12,ipady=4)
        self.cancel_button=ttk.Button(actions,text="Cancel",command=self.cancel)
        self.cancel_button.pack(side="left",padx=6,ipadx=12,ipady=4)
        canvas_host=ttk.Frame(outer)
        canvas_host.pack(fill="both",expand=True)
        canvas_host.grid_rowconfigure(0, weight=1)
        canvas_host.grid_columnconfigure(0, weight=1)
        self.canvas=tk.Canvas(canvas_host,width=self.canvas_w,height=self.canvas_h,bg="#202733",highlightthickness=0,bd=0)
        self.canvas.grid(row=0,column=0,pady=4)
        self.drag=None; self.photo=None; self.draw_preview()
        self.canvas.bind("<Button-1>",self.down); self.canvas.bind("<B1-Motion>",self.move); self.canvas.bind("<ButtonRelease-1>",self.up)
        self.protocol("WM_DELETE_WINDOW",self.cancel)

    def base_preview(self):
        if self.kind=="thumbnail":
            return fit_bg(self.background).convert("RGBA")
        im=fit_bg(self.background,blur=True,darken=True).convert("RGBA")
        x,y,w,h=self.layout.get("video",[70,590,940,530])
        ratio=16/9
        try:
            source=one_file(VIDEO_DIR,VIDEO_EXTS,"video")
            ffprobe=shutil.which("ffprobe")
            if ffprobe:
                pr=subprocess.run([ffprobe,"-v","error","-select_streams","v:0","-show_entries","stream=width,height","-of","csv=s=x:p=0",str(source)],capture_output=True,text=True,timeout=3)
                ww,hh=map(int,pr.stdout.strip().split("x")); ratio=ww/hh
        except Exception: pass
        vw=min(w,h*ratio); vh=vw/ratio
        if vh>h: vh=h; vw=vh*ratio
        px=int(x+(w-vw)/2); py=int(y+(h-vh)/2)
        d=ImageDraw.Draw(im)
        d.rectangle((px,py,px+int(vw),py+int(vh)),fill=(52,70,91,255),outline=(180,200,220,255),width=4)
        try: f=ImageFont.truetype(font_path(True),24)
        except Exception: f=ImageFont.load_default()
        d.text((px+12,py+12),f"LANDSCAPE VIDEO  {ratio:.2f}:1",font=f,fill="white")
        return im

    def draw_preview(self):
        # Keep the expensive background/video placeholder cached; redraw the actual styled
        # title/part elements from the current layout so the preset updates while dragging.
        if self._base_image is None:
            self._base_image=self.base_preview()
        frame=self._base_image.copy()
        overlay=make_overlay(self.title_text,"PART 1",self.layout)
        frame=Image.alpha_composite(frame.convert("RGBA"),overlay)
        self.photo=ImageTk.PhotoImage(frame.convert("RGB").resize((self.canvas_w,self.canvas_h),Image.Resampling.LANCZOS))
        self.canvas.delete("all")
        self.canvas.create_image(0,0,image=self.photo,anchor="nw",tags=("preview",))
        self.draw_guides()

    def draw_guides(self):
        self.canvas.delete("guide")
        for key,box in self.layout.items():
            x,y,w,h=box; sx=x*self.scale; sy=y*self.scale; sw=w*self.scale; sh=h*self.scale
            color=COLORS.get(key,"#ffffff")
            self.canvas.create_rectangle(sx,sy,sx+sw,sy+sh,outline=color,width=2,dash=(5,3),tags=("guide", "box",key))
            label=key.upper()+" BOX"
            self.canvas.create_text(sx+5,sy+3,text=label,anchor="nw",fill=color,font=("Segoe UI",8,"bold"),tags=("guide", "box",key))
            # Paint-style corner handles: all four corners can be grabbed to resize.
            r=5
            for cx,cy,corner in ((sx,sy,"nw"),(sx+sw,sy,"ne"),(sx,sy+sh,"sw"),(sx+sw,sy+sh,"se")):
                self.canvas.create_rectangle(cx-r,cy-r,cx+r,cy+r,fill=color,outline="#ffffff",width=1,tags=("guide","handle",key,"corner_"+corner))
        self.canvas.tag_raise("guide")

    def down(self,e):
        x=e.x/self.scale; y=e.y/self.scale
        hit=None
        # Prioritize corner handles so the user can resize from any corner.
        for key in reversed(list(self.layout.keys())):
            bx,by,bw,bh=self.layout[key]
            corners={"nw":(bx,by),"ne":(bx+bw,by),"sw":(bx,by+bh),"se":(bx+bw,by+bh)}
            for corner,(cx,cy) in corners.items():
                if abs(x-cx)<=22 and abs(y-cy)<=22:
                    hit=(key,"resize_"+corner,x,y,list(self.layout[key])); break
            if hit: break
        if hit is None:
            for key in reversed(list(self.layout.keys())):
                bx,by,bw,bh=self.layout[key]
                if bx<=x<=bx+bw and by<=y<=by+bh:
                    hit=(key,"move",x,y,list(self.layout[key])); break
        self.drag=hit
        if hit:
            self.canvas.configure(cursor="fleur" if hit[1]=="move" else ("size_nw_se" if hit[1] in ("resize_nw","resize_se") else "size_ne_sw"))

    def move(self,e):
        if not self.drag:
            # Update cursor when hovering over a corner or box.
            x=e.x/self.scale; y=e.y/self.scale; cursor="arrow"
            for key in reversed(list(self.layout.keys())):
                bx,by,bw,bh=self.layout[key]
                if any(abs(x-cx)<=22 and abs(y-cy)<=22 for cx,cy in ((bx,by),(bx+bw,by),(bx,by+bh),(bx+bw,by+bh))):
                    cursor="size_nw_se"; break
                if bx<=x<=bx+bw and by<=y<=by+bh: cursor="fleur"; break
            self.canvas.configure(cursor=cursor)
            return
        key,mode,ox,oy,orig=self.drag
        dx=e.x/self.scale-ox; dy=e.y/self.scale-oy
        x,y,w,h=orig; minw,minh=80,40
        if mode=="move":
            x=max(0,min(W-w,x+dx)); y=max(0,min(H-h,y+dy))
        else:
            corner=mode.split("_",1)[1]
            left=corner.endswith("w"); top=corner.startswith("n")
            if left:
                nx=max(0,min(x+w-minw,x+dx)); w=(x+w)-nx; x=nx
            else: w=max(minw,min(W-x,w+dx))
            if top:
                ny=max(0,min(y+h-minh,y+dy)); h=(y+h)-ny; y=ny
            else: h=max(minh,min(H-y,h+dy))
        self.layout[key]=[int(x),int(y),int(w),int(h)]
        self.draw_preview()

    def up(self,e):
        self.drag=None
        self.canvas.configure(cursor="arrow")
    def save(self):
        if messagebox.askyesno("Confirm save",f"Save the {self.kind} layout? This replaces the previously saved layout for this window.",parent=self):
            self.settings[self.kind]=self.layout
            save_settings(self.settings)
            self.destroy()
    def cancel(self):
        if messagebox.askyesno("Discard changes","Close this editor without saving changes?",parent=self):
            self.destroy()

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Reels Splitter — Visual Layout Studio")
        self.geometry("620x470"); self.resizable(False,False)
        self.settings=load_settings(); self.video=None; self.background=None; self.title_text="YOUR VIDEO TITLE"
        body=ttk.Frame(self,padding=18); body.pack(fill="both",expand=True)
        ttk.Label(body,text="Reels Splitter",font=("Segoe UI",20,"bold")).pack(anchor="w")
        ttk.Label(body,text="Visual layout editor • 9:16 portrait output",font=("Segoe UI",10)).pack(anchor="w",pady=(0,12))
        ttk.Label(body,text="Series title").pack(anchor="w")
        self.title_var=tk.StringVar(value=self.title_text)
        self.editors=[]
        self.title_var.trace_add("write", self.update_editor_titles)
        ttk.Entry(body,textvariable=self.title_var,width=65).pack(fill="x",pady=(2,10))
        ttk.Label(body,text="Source segment duration (seconds)").pack(anchor="w")
        self.duration_var=tk.StringVar(value="180")
        ttk.Entry(body,textvariable=self.duration_var,width=15).pack(anchor="w",pady=(2,10))
        ttk.Label(body,text="Put exactly one landscape video in input/video and one background image in input/background.",wraplength=570).pack(anchor="w",pady=(0,10))
        row=ttk.Frame(body); row.pack(fill="x",pady=5)
        ttk.Button(row,text="Open Thumbnail Editor",command=lambda:self.open_editor("thumbnail")).pack(side="left",padx=(0,8))
        ttk.Button(row,text="Open Video Overlay Editor",command=lambda:self.open_editor("video")).pack(side="left")
        ttk.Button(body,text="Render Reels",command=self.render).pack(fill="x",pady=(12,5))
        ttk.Label(body,text="Save each layout in its own window. Ghost outlines never appear in output.",foreground="#555").pack(anchor="w")
        try:
            self.video=one_file(VIDEO_DIR,VIDEO_EXTS,"video")
            self.background=one_file(BG_DIR,IMAGE_EXTS,"background image")
            self.background_image=Image.open(self.background).convert("RGB")
        except Exception as e:
            self.background_image=Image.new("RGB",(1080,1920),(30,42,58))
            self.after(250,lambda:messagebox.showwarning("Input files needed",str(e),parent=self))
        self.protocol("WM_DELETE_WINDOW",self.destroy)
        if self.video is not None and self.background is not None:
            self.after(400, lambda: self.open_editor("thumbnail"))
            self.after(650, lambda: self.open_editor("video"))

    def update_editor_titles(self, *_):
        title=self.title_var.get().strip() or "YOUR VIDEO TITLE"
        for editor in list(self.editors):
            try:
                if editor.winfo_exists():
                    editor.title_text=title
                    editor._base_image=None
                    editor.draw_preview()
            except Exception: pass

    def open_editor(self,kind):
        self.title_text=self.title_var.get().strip() or "YOUR VIDEO TITLE"
        if self.background is None:
            try:
                self.background=one_file(BG_DIR,IMAGE_EXTS,"background image")
                self.background_image=Image.open(self.background).convert("RGB")
            except Exception as e:
                messagebox.showerror("Background image required",str(e),parent=self); return
        editor=LayoutEditor(self,kind,self.background_image,self.title_text,self.settings)
        self.editors.append(editor)
        editor.lift()

    def render(self):
        try:
            self.video=one_file(VIDEO_DIR,VIDEO_EXTS,"video")
            self.background=one_file(BG_DIR,IMAGE_EXTS,"background image")
            self.background_image=Image.open(self.background).convert("RGB")
            title=self.title_var.get().strip()
            if not title: raise ValueError("Enter a title first.")
            duration=float(self.duration_var.get())
            if duration<=0: raise ValueError("Segment duration must be positive.")
            save_settings(self.settings)
            threading.Thread(target=self._render_worker,args=(title,duration),daemon=True).start()
            messagebox.showinfo("Rendering started","Rendering has started. FFmpeg progress will appear in the console window.",parent=self)
        except Exception as e: messagebox.showerror("Cannot render",str(e),parent=self)

    def _render_worker(self,title,duration):
        try:
            ffmpeg=shutil.which("ffmpeg"); ffprobe=shutil.which("ffprobe")
            if not ffmpeg or not ffprobe: raise RuntimeError("FFmpeg and FFprobe must be installed and on PATH.")
            probe=subprocess.run([ffprobe,"-v","error","-show_entries","format=duration","-of","default=noprint_wrappers=1:nokey=1",str(self.video)],capture_output=True,text=True,check=True)
            total=float(probe.stdout.strip())
            OUT_DIR.mkdir(exist_ok=True); TEMP.mkdir(parents=True,exist_ok=True)
            for p in OUT_DIR.glob("Part*.mp4"):
                try: p.unlink()
                except OSError: pass
            thumb=self.settings["thumbnail"]; vlayout=self.settings["video"]
            step=max(1.0,duration-1.0)
            n=max(1,math.ceil(max(0,total-1)/step))
            encoders=subprocess.run([ffmpeg,"-hide_banner","-encoders"],capture_output=True,text=True).stdout
            use_nvenc="h264_nvenc" in encoders
            for idx in range(n):
                start=idx*step
                seg=min(duration,total-start)
                if seg<=0: break
                part=f"PART {idx+1}"
                card=fit_bg(self.background_image).convert("RGBA")
                ov=make_overlay(title,part,thumb)
                card=Image.alpha_composite(card,ov).convert("RGB")
                card_path=TEMP/f"card_{idx+1}.jpg"; card.save(card_path,quality=94,optimize=False)
                overlay_path=TEMP/f"overlay_{idx+1}.png"
                make_overlay(title,part,vlayout).save(overlay_path,optimize=False)
                out=OUT_DIR/f"Part{idx+1}.mp4"
                vx,vy,vw,vh=vlayout.get("video",[70,590,940,530])
                # Separate blurred background; source video is scaled to fit its selected box with no crop/stretch.
                fg=(f"[0:v]fps=30,setsar=1,format=yuv420p[card];"
                    f"[2:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,boxblur=20:2,eq=brightness=-0.15[bg];"
                    f"[1:v]scale={int(vw)}:{int(vh)}:force_original_aspect_ratio=decrease,fps=30[vid];"
                    f"[bg][vid]overlay=x={int(vx)}+({int(vw)}-overlay_w)/2:y={int(vy)}+({int(vh)}-overlay_h)/2:shortest=1[base];"
                    f"[3:v]format=rgba[ov];[base][ov]overlay=0:0:shortest=1,format=yuv420p,fps=30,setsar=1[clip];"
                    f"[card][clip]concat=n=2:v=1:a=0[outv]")
                audio_probe=subprocess.run([ffprobe,"-v","error","-select_streams","a:0","-show_entries","stream=index","-of","csv=p=0",str(self.video)],capture_output=True,text=True)
                has_audio=bool(audio_probe.stdout.strip())
                if has_audio:
                    fg += f";[1:a]adelay=1000:all=1,apad,atrim=duration={seg+1:.3f},asetpts=PTS-STARTPTS[aout]"
                base_cmd=[ffmpeg,"-hide_banner","-y","-loop","1","-framerate","30","-t","1","-i",str(card_path),
                    "-ss",f"{start:.3f}","-t",f"{seg:.3f}","-i",str(self.video),
                    "-loop","1","-framerate","30","-t",f"{seg:.3f}","-i",str(self.background),
                    "-loop","1","-framerate","30","-t",f"{seg:.3f}","-i",str(overlay_path),
                    "-filter_complex",fg,"-map","[outv]","-c:v"]
                def encode_args():
                    if use_nvenc:
                        return ["h264_nvenc","-preset","p2","-tune","hq","-rc","vbr","-cq","20","-b:v","0"]
                    return ["libx264","-preset","veryfast","-crf","20"]
                cmd=base_cmd+encode_args()
                if has_audio: cmd += ["-map","[aout]","-c:a","aac","-b:a","192k"]
                else: cmd += ["-an"]
                cmd += ["-movflags","+faststart","-progress","pipe:1","-nostats",str(out)]
                print(f"\nRendering {idx+1}/{n}: {out.name} ({'NVIDIA NVENC' if use_nvenc else 'CPU'})",flush=True)
                def run(cmdline):
                    proc=subprocess.Popen(cmdline,cwd=ROOT,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,encoding="utf-8",errors="replace",bufsize=1)
                    logs=[]; last_pct=-1; expected=max(1.0,seg+1.0)
                    for line in proc.stdout:
                        logs.append(line)
                        if line.startswith("out_time_ms="):
                            try:
                                seconds=int(line.split("=",1)[1].strip())/1000000
                                pct=max(0,min(100,int(seconds/expected*100)))
                                if pct != last_pct:
                                    print(f"\rPart {idx+1}/{n}: {pct:3d}%",end="",flush=True); last_pct=pct
                            except Exception: pass
                    code=proc.wait()
                    print("",flush=True)
                    return code,"".join(logs)
                code,logs=run(cmd)
                if code != 0 and use_nvenc:
                    try: out.unlink()
                    except OSError: pass
                    print("NVENC failed; retrying this part with CPU encoding.",flush=True)
                    use_nvenc=False
                    cmd=base_cmd+encode_args()
                    if has_audio: cmd += ["-map","[aout]","-c:a","aac","-b:a","192k"]
                    else: cmd += ["-an"]
                    cmd += ["-movflags","+faststart","-progress","pipe:1","-nostats",str(out)]
                    code,logs=run(cmd)
                if code != 0:
                    raise RuntimeError(f"FFmpeg failed on {out.name}. Last output:\n{logs[-3500:]}")
                try:
                    out_probe=subprocess.run([ffprobe,"-v","error","-show_entries","format=duration","-of","default=noprint_wrappers=1:nokey=1",str(out)],capture_output=True,text=True,timeout=15)
                    print(f"Completed {out.name} ({float(out_probe.stdout.strip()):.1f}s)",flush=True)
                except Exception: print(f"Completed {out.name}",flush=True)
            self.after(0,lambda:messagebox.showinfo("Finished",f"Finished rendering {n} part(s) to:\n{OUT_DIR}",parent=self))
        except Exception as e:
            self.after(0,lambda err=str(e):messagebox.showerror("Rendering failed",err,parent=self))

if __name__ == "__main__":
    App().mainloop()
