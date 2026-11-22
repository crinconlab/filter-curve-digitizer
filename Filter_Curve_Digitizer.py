#!/usr/bin/env python3
"""Filter Curve Digitizer: independent axis calibration, filter curve extraction and exports.
Requires Python with tkinter, numpy and Pillow. Optional update checks use GitHub.
"""
from __future__ import annotations
import json
import math
import queue
import re
import ssl
import sys
import threading
import time
import urllib.error
import urllib.request
import webbrowser
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from pathlib import Path

APP_VERSION = "1.4.0"
RELEASES_URL = "https://github.com/crinconlab/filter-curve-digitizer/releases"
LATEST_RELEASE_API = "https://api.github.com/repos/crinconlab/filter-curve-digitizer/releases/latest"
SETTINGS_PATH = Path.home() / ".filter-curve-digitizer" / "settings.json"


def github_ssl_context():
    """Verify HTTPS against a bundled, maintained CA certificate store."""
    return ssl.create_default_context(cafile=certifi.where())


def test_github_https():
    """Packaging diagnostic: confirm certificate verification in the actual executable."""
    request = urllib.request.Request(
        "https://api.github.com/",
        headers={"User-Agent": "Filter-Curve-Digitizer/" + APP_VERSION},
    )
    with urllib.request.urlopen(request, timeout=12, context=github_ssl_context()) as response:
        if response.status != 200:
            raise RuntimeError(f"GitHub HTTPS test returned HTTP {response.status}")
    print("PASS: GitHub HTTPS certificate verified using packaged CA certificates.")


def parse_version(value):
    """Accept v1.4, v1.4.0 and v1.3b; reject unrelated release tags."""
    match = re.fullmatch(r"v?(\d+)\.(\d+)(?:\.(\d+))?([a-z]?)", str(value).strip(), re.IGNORECASE)
    if not match:
        return None
    major, minor, patch, suffix = match.groups()
    # A bare numbered release sorts after a letter-suffixed preliminary build.
    return (int(major), int(minor), int(patch or 0), 1 if not suffix else 0, suffix.lower())


def load_settings():
    try:
        data = json.loads(SETTINGS_PATH.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError):
        return {}


def save_settings(settings):
    try:
        SETTINGS_PATH.parent.mkdir(parents=True, exist_ok=True)
        SETTINGS_PATH.write_text(json.dumps(settings, indent=2), encoding="utf-8")
    except OSError:
        pass  # Failure to save preferences must not prevent using the app.

import certifi
import numpy as np
from PIL import Image, ImageTk, ImageDraw

class Digitizer:
    STEPS = [
        ('x0', '1/7: Click exactly on the X-axis tick corresponding to X Reference 1.'),
        ('x1', '2/7: Click exactly on the X-axis tick corresponding to X Reference 2.'),
        ('y0', '3/7: Click on the Y-axis tick corresponding to Y Reference 1.'),
        ('y1', '4/7: Click on the Y-axis tick corresponding to Y Reference 2.'),
        ('left', '5/7: Click the LEFT boundary of the plot area to digitize.'),
        ('right', '6/7: Click the RIGHT boundary of the plot area to digitize.'),
        ('sample', '7/7: Click the transmission curve to sample its color.'),
    ]
    def __init__(self, root):
        self.root=root
        root.title(f'Filter Curve Digitizer v{APP_VERSION} — PixInsight / Siril')
        root.geometry('1210x920')
        try:
            icon_path = Path(__file__).resolve().parent / 'Filter_Curve_Digitizer.ico'
            if icon_path.exists():
                root.iconbitmap(str(icon_path))
        except (OSError, tk.TclError):
            pass
        self.image=None; self.photo=None; self.scale=1.0
        self.points={}; self.step_idx=0; self.output=None; self.overlay=None
        self.image_path=None
        self.settings = load_settings()
        self.update_queue = queue.Queue()
        self.update_running = False
        self._build_help_menu()
        root.after(200, self._show_first_run_guide)
        root.after(1000, self._check_updates_on_start)
        row=ttk.Frame(root,padding=9); row.pack(fill='x')
        for s,fn in [('Open image…',self.open_image),('Reset calibration',self.reset),('Extract curve',self.extract),('CSV PixInsight…',self.export_csv),('JSON Siril…',self.export_siril),('Save overlay…',self.save_overlay)]:
            ttk.Button(row,text=s,command=fn).pack(side='left',padx=(0,7))
        row=ttk.Frame(root,padding=(9,0,9,7)); row.pack(fill='x')
        self.name=tk.StringVar(value='Custom filter')
        self.xmin=tk.StringVar(value='400'); self.xmax=tk.StringVar(value='700')
        self.ymin=tk.StringVar(value='0'); self.ymax=tk.StringVar(value='100')
        self.step=tk.StringVar(value='1'); self.tol=tk.IntVar(value=75)
        self.manufacturer=tk.StringVar(); self.filter_type=tk.StringVar(value='OSC_FILTER')
        self.mono_channel=tk.StringVar(value='LUM')
        self.data_source=tk.StringVar(value='Digitized from manufacturer transmission chart')
        for name,var,n in [('Name:',self.name,25),('X reference 1 (nm):',self.xmin,7),('X reference 2 (nm):',self.xmax,7),('Y reference 1 (%):',self.ymin,6),('Y reference 2 (%):',self.ymax,6),('Step (nm):',self.step,5)]:
            self.field(row,name,var,n)
        row=ttk.Frame(root,padding=(9,0,9,7)); row.pack(fill='x')
        self.field(row,'Manufacturer (Siril):',self.manufacturer,18)
        ttk.Label(row,text='Type:').pack(side='left')
        ttk.Combobox(row,textvariable=self.filter_type,values=('OSC_FILTER','MONO_FILTER'),width=12,state='readonly').pack(side='left',padx=(4,9))
        ttk.Label(row,text='Mono channel:').pack(side='left')
        ttk.Combobox(row,textvariable=self.mono_channel,values=('LUM','RED','GREEN','BLUE'),width=7,state='readonly').pack(side='left',padx=(4,9))
        ttk.Label(row,text='Color tolerance:').pack(side='left')
        ttk.Scale(row,from_=20,to=160,variable=self.tol,orient='horizontal',length=155).pack(side='left',padx=6)
        # Keep the current click highly visible, immediately above the image.
        prompt_frame = tk.Frame(root, bg="#e7f1ff", padx=12, pady=9)
        prompt_frame.pack(fill="x", padx=9, pady=(5, 3))
        self.step_badge = tk.Label(prompt_frame, text="READY", font=("Helvetica", 12, "bold"),
                                   bg="#174c85", fg="white", padx=10, pady=5)
        self.step_badge.pack(side="left", padx=(0, 12))
        self.info = tk.StringVar()
        self.prompt_label = tk.Label(prompt_frame, textvariable=self.info, bg="#e7f1ff",
                                     fg="#123658", font=("Helvetica", 12, "bold"),
                                     anchor="w", justify="left", wraplength=950)
        self.prompt_label.pack(side="left", fill="x", expand=True)
        self.reference_warning = tk.Label(
            root,
            text="IMPORTANT: Clicks 1–4 MUST match the values entered in X Reference 1/2 and Y Reference 1/2.",
            bg="#fff0c4", fg="#593a00", font=("Helvetica", 11, "bold"),
            anchor="w", padx=12, pady=7,
        )
        self.reference_warning.pack(fill="x", padx=9, pady=(0, 5))
        for var in (self.xmin, self.xmax, self.ymin, self.ymax):
            var.trace_add("write", lambda *_: self._update_step_prompt())
        self._update_step_prompt()
        frame=ttk.Frame(root);frame.pack(fill='both',expand=True,padx=9,pady=(0,7))
        self.canvas=tk.Canvas(frame,bg='#e7e7e7',highlightthickness=1,highlightbackground='#999')
        self.canvas.pack(fill='both',expand=True)
        self.canvas.bind('<Button-1>',self.on_click)
        self.canvas.bind('<Configure>',lambda ev:self.update_canvas())
        self.status=tk.StringVar(value='No image loaded.')
        ttk.Label(root,textvariable=self.status,padding=(9,0,9,8),wraplength=1160).pack(anchor='w')
    def _update_step_prompt(self):
        if self.image is None:
            self.step_badge.configure(text="READY")
            self.info.set("Open a transmission chart to begin the seven calibration clicks.")
            self.reference_warning.pack(fill="x", padx=9, pady=(0, 5))
            return
        prompts = [
            f"Click the X-axis tick at {self.xmin.get()} nm (X Reference 1).",
            f"Click the X-axis tick at {self.xmax.get()} nm (X Reference 2).",
            f"Click the Y-axis tick at {self.ymin.get()}% (Y Reference 1).",
            f"Click the Y-axis tick at {self.ymax.get()}% (Y Reference 2).",
            "Click the LEFT edge of the plotted extraction region (not X Reference 1).",
            "Click the RIGHT edge of the plotted extraction region (not X Reference 2).",
            "Click a clearly coloured part of the transmission curve.",
        ]
        if self.step_idx < len(prompts):
            self.step_badge.configure(text=f"{self.step_idx + 1} / 7")
            self.info.set(prompts[self.step_idx])
        else:
            self.step_badge.configure(text="7 / 7 ✓")
            self.info.set("Calibration complete. Click Extract curve and check the green overlay.")
        if self.step_idx < 4:
            warning = "IMPORTANT: Clicks 1–4 MUST match the values entered in X Reference 1/2 and Y Reference 1/2."
        elif self.step_idx < 6:
            warning = "Clicks 5–6 select the extraction boundaries; they do NOT need to match the X reference ticks."
        else:
            warning = "Check the green extracted overlay against the original transmission curve before exporting."
        self.reference_warning.configure(text=warning)

    def _build_help_menu(self):
        menu = tk.Menu(self.root)
        help_menu = tk.Menu(menu, tearoff=0)
        help_menu.add_command(label="Calibration guide…", command=self.show_calibration_guide)
        help_menu.add_command(label="Check for updates…", command=lambda: self.check_for_updates(manual=True))
        # PREVIEW-ONLY diagnostic. Remove before the official v1.4 release.
        help_menu.add_command(label="TEST ONLY — Simulate v1.5 update…",
                              command=self.simulate_update_notification)
        help_menu.add_separator()
        self.auto_update_var = tk.BooleanVar(value=self.settings.get("auto_check_updates", True))
        help_menu.add_checkbutton(
            label="Automatically check for updates",
            variable=self.auto_update_var,
            command=self._save_update_preference,
        )
        menu.add_cascade(label="Help", menu=help_menu)
        self.root.configure(menu=menu)

    def _save_update_preference(self):
        self.settings["auto_check_updates"] = bool(self.auto_update_var.get())
        save_settings(self.settings)

    def _show_first_run_guide(self):
        if not self.settings.get("hide_calibration_guide", False):
            self.show_calibration_guide()

    def show_calibration_guide(self):
        guide = tk.Toplevel(self.root)
        guide.title("Calibration guide — seven clicks")
        guide.transient(self.root)
        guide.resizable(False, False)
        guide.geometry("660x530")
        guide.grab_set()
        frame = ttk.Frame(guide, padding=20)
        frame.pack(fill="both", expand=True)
        ttk.Label(frame, text="How to calibrate a transmission curve", font=("Helvetica", 16, "bold")).pack(anchor="w", pady=(0, 10))
        ttk.Label(frame, text="Open a chart and make seven clicks in this order. The first four clicks MUST match the reference values entered in the fields above the image.", wraplength=605).pack(anchor="w", pady=(0, 12))
        sections = [
            ("1–2  Calibrate wavelength (X axis)", "Click 1 on the tick matching X reference 1 (nm), then click 2 on the tick matching X reference 2 (nm). Example: if the fields say 400 and 700, click the 400 nm and 700 nm ticks, respectively."),
            ("3–4  Calibrate transmission (Y axis)", "Click 3 on the tick matching Y reference 1 (%), then click 4 on the tick matching Y reference 2 (%). Example: if the fields say 0 and 100, click the 0% and 100% ticks, respectively."),
            ("5–6  Set extraction boundaries", "Click the LEFT and RIGHT edges of the plotted region to extract. These edges do NOT have to coincide with the wavelength reference ticks from clicks 1 and 2."),
            ("7  Select the curve", "Click a clearly coloured part of the transmission curve, avoiding grid lines and other curves."),
        ]
        for heading, description in sections:
            ttk.Label(frame, text=heading, font=("Helvetica", 11, "bold")).pack(anchor="w", pady=(6, 2))
            ttk.Label(frame, text=description, wraplength=605, justify="left").pack(anchor="w")
        ttk.Label(frame, text="After clicking: select Extract curve and verify that the green overlay follows the intended curve.", wraplength=605).pack(anchor="w", pady=(12, 8))
        hide_var = tk.BooleanVar(value=bool(self.settings.get("hide_calibration_guide", False)))
        ttk.Checkbutton(frame, text="Do not show this guide at startup", variable=hide_var).pack(anchor="w")
        def close_guide():
            self.settings["hide_calibration_guide"] = bool(hide_var.get())
            save_settings(self.settings)
            guide.destroy()
        ttk.Button(frame, text="Start", command=close_guide).pack(anchor="e", pady=(8, 0))
        guide.protocol("WM_DELETE_WINDOW", close_guide)

    def _check_updates_on_start(self):
        if not self.settings.get("auto_check_updates", True):
            return
        last = self.settings.get("last_update_check", 0)
        if isinstance(last, (int, float)) and time.time() - last < 24 * 3600:
            return
        self.check_for_updates(manual=False)

    def check_for_updates(self, manual=False):
        if self.update_running:
            if manual:
                messagebox.showinfo("Updates", "An update check is already running.")
            return
        self.update_running = True
        self.settings["last_update_check"] = time.time()
        save_settings(self.settings)
        def worker():
            try:
                request = urllib.request.Request(
                    LATEST_RELEASE_API,
                    headers={"User-Agent": "Filter-Curve-Digitizer/" + APP_VERSION, "Accept": "application/vnd.github+json"},
                )
                with urllib.request.urlopen(request, timeout=6, context=github_ssl_context()) as response:
                    release = json.loads(response.read(128 * 1024).decode("utf-8"))
                if not isinstance(release, dict) or not isinstance(release.get("tag_name"), str):
                    raise ValueError("Unexpected GitHub response.")
                self.update_queue.put(("success", release.get("tag_name")))
            except urllib.error.HTTPError as exc:
                if exc.code == 404:
                    self.update_queue.put(("no_stable_release", None))
                else:
                    self.update_queue.put(("error", str(exc)))
            except Exception as exc:
                self.update_queue.put(("error", str(exc)))
        threading.Thread(target=worker, daemon=True).start()
        self.root.after(100, lambda: self._finish_update_check(manual))

    def simulate_update_notification(self):
        """Preview-only UI check; does not contact GitHub or change preferences."""
        if self.update_running:
            messagebox.showinfo("Simulated update", "An update check is in progress. Please retry.")
            return
        self.update_queue.put(("success", "v1.5.0"))
        self._finish_update_check(manual=True, simulated=True)

    def _finish_update_check(self, manual, simulated=False):
        try:
            status, data = self.update_queue.get_nowait()
        except queue.Empty:
            self.root.after(100, lambda: self._finish_update_check(manual))
            return
        self.update_running = False
        if status == "no_stable_release":
            if manual:
                messagebox.showinfo("Updates", "No stable release is published on GitHub yet. You are using v" + APP_VERSION + ".")
            return
        if status == "error":
            if manual:
                messagebox.showwarning("Updates", f"Unable to check GitHub releases:\n{data}")
            return
        latest, current = parse_version(data), parse_version(APP_VERSION)
        if latest is None or current is None:
            if manual:
                messagebox.showwarning("Updates", "The latest GitHub release has an unrecognised version tag.")
            return
        if latest > current:
            if messagebox.askyesno(
                "TEST ONLY — simulated update" if simulated else "New version available",
                (f"This is a simulation; version {data} is NOT published.\n\n" if simulated else "")
                + f"Filter Curve Digitizer {data} is available.\n"
                + f"Installed version: {APP_VERSION}\n\n"
                + "Open the GitHub Releases page?"
            ):
                webbrowser.open(RELEASES_URL)
        elif manual:
            messagebox.showinfo("Updates", f"You are using v{APP_VERSION}. No newer stable release is available.")

    @staticmethod
    def field(parent,name,var,width):
        ttk.Label(parent,text=name).pack(side='left',padx=(0,3))
        ttk.Entry(parent,textvariable=var,width=width).pack(side='left',padx=(0,9))
    def open_image(self):
        path=filedialog.askopenfilename(title='Transmission plot',filetypes=[('Images','*.png *.jpg *.jpeg *.webp *.bmp *.tif *.tiff'),('All files','*')])
        if not path:return
        try:
            im=Image.open(path).convert('RGB')
            if min(im.size)<80:raise ValueError('Image is too small')
        except Exception as ex:messagebox.showerror('Image',str(ex));return
        self.image=im;self.image_path=Path(path);self.name.set(self.image_path.stem)
        self.reset()
    def reset(self):
        self.points={};self.step_idx=0;self.output=None;self.overlay=None
        self._update_step_prompt()
        self.status.set('IMPORTANT: X reference values identify axis tick marks, not export limits. Set the visible plot boundaries in clicks 5 and 6.')
        self.update_canvas()
    def update_canvas(self):
        if self.image is None:return
        cw=max(self.canvas.winfo_width()-12,200);ch=max(self.canvas.winfo_height()-12,200)
        self.scale=min(cw/self.image.width,ch/self.image.height,1.6)
        sz=(max(1,round(self.image.width*self.scale)),max(1,round(self.image.height*self.scale)))
        im=(self.overlay if self.overlay is not None else self.image).resize(sz,Image.Resampling.LANCZOS)
        self.photo=ImageTk.PhotoImage(im)
        self.canvas.delete('all');self.canvas.create_image(0,0,image=self.photo,anchor='nw')
        if self.overlay is None:
            for k,(x,y) in self.points.items():
                cx,cy=x*self.scale,y*self.scale
                self.canvas.create_line(cx-5,cy,cx+5,cy,fill='blue',width=2)
                self.canvas.create_line(cx,cy-5,cx,cy+5,fill='blue',width=2)
                self.canvas.create_text(cx+8,cy-10,text=k,fill='blue',anchor='w',font=('Helvetica',11,'bold'))
    def on_click(self,ev):
        if self.image is None or self.step_idx>=len(self.STEPS):return
        x,y=ev.x/self.scale,ev.y/self.scale
        if not (0<=x<self.image.width and 0<=y<self.image.height):return
        key,_=self.STEPS[self.step_idx]
        if key=='sample':
            arr=np.asarray(self.image);ix,iy=int(x),int(y)
            patch=arr[max(0,iy-5):min(arr.shape[0],iy+6),max(0,ix-5):min(arr.shape[1],ix+6)].astype(float)
            strength=patch.max(axis=2)-patch.min(axis=2)
            k=np.unravel_index(np.argmax(strength),strength.shape)
            if strength[k]<30:
                messagebox.showwarning('Color','No colored curve detected near your click.');return
            self.sample_color=patch[k]
            self.status.set(f'Selected curve color: RGB {tuple(int(v) for v in self.sample_color)}. Click Extract curve.')
        self.points[key]=(x,y);self.step_idx+=1
        self._update_step_prompt()
        self.update_canvas()
    @staticmethod
    def coordinates(x_ref0,x_ref1,px0,px1,left,right,step):
        """Map pixel coordinates of the visible plot to wavelength, allowing X extrapolation."""
        if abs(px1-px0)<50:raise ValueError('X reference points are too close (<50 pixels).')
        lo=x_ref0+(left-px0)*(x_ref1-x_ref0)/(px1-px0)
        hi=x_ref0+(right-px0)*(x_ref1-x_ref0)/(px1-px0)
        lo,hi=sorted((lo,hi))
        if hi-lo<step:raise ValueError('Export wavelength range is too small.')
        # Include endpoints of the visible plot even if they aren't multiples of step.
        xs=np.arange(lo,hi+step*0.25,step,dtype=float)
        xs=xs[xs<=hi+1e-9]
        if len(xs)==0:xs=np.array([lo])
        if hi-xs[-1]>1e-8:xs=np.append(xs,hi)
        else:xs[-1]=hi
        return lo,hi,xs
    def extract(self):
        if self.image is None or any(k not in self.points for k,_ in self.STEPS):
            messagebox.showwarning('Calibration','Open an image and complete all seven clicks.');return
        try:
            xr0,xr1=float(self.xmin.get()),float(self.xmax.get())
            yr0,yr1=float(self.ymin.get()),float(self.ymax.get())
            step=float(self.step.get())
            if not all(math.isfinite(v) for v in (xr0,xr1,yr0,yr1,step)) or xr1<=xr0 or yr1<=yr0 or step<=0:
                raise ValueError('Reference values must be finite, strictly increasing; step must be positive.')
            px0=self.points['x0'][0];px1=self.points['x1'][0]
            if px1<=px0:raise ValueError('Click the leftmost X reference first.')
            y0=self.points['y0'][1];y1=self.points['y1'][1]
            if abs(y1-y0)<50:raise ValueError('Y reference points are too close.')
            left=round(self.points['left'][0]);right=round(self.points['right'][0])
            if right-left<50:raise ValueError('Plot boundaries are too close together or reversed.')
            lo,hi,xs=self.coordinates(xr0,xr1,px0,px1,left,right,step)
            if len(xs)>20001:raise ValueError('Too many sample points: increase the step.')
            # Delimit Y crop using calibrated 0-100% rows, without using X calibration points as borders.
            top=max(0,min(round(y0),round(y1)))
            bottom=min(self.image.height-1,max(round(y0),round(y1)))
            l=max(0,left);r=min(self.image.width-1,right)
            arr=np.asarray(self.image,dtype=np.float32)
            region=arr[top:bottom+1,l:r+1]
            if region.size==0:raise ValueError('The extraction area is empty.')
            dist=np.sqrt(np.sum((region-self.sample_color)**2,axis=2))
            chroma=region.max(axis=2)-region.min(axis=2)
            valid=(dist<=int(self.tol.get())) & (chroma>=25)
            py=np.full(region.shape[1],np.nan)
            for i in range(region.shape[1]):
                ys=np.flatnonzero(valid[:,i])
                if len(ys):py[i]=top+float(ys[np.argmin(dist[ys,i])])
            good=np.isfinite(py)
            if good.sum()<10 or good.mean()<0.12:raise ValueError('Not enough curve pixels detected. Check the selected color or tolerance.')
            xpix=np.arange(l,r+1)
            yi=np.interp(xpix,xpix[good],py[good])
            leftidx=np.searchsorted(xpix[good],xpix,side='right')-1
            rightidx=np.searchsorted(xpix[good],xpix,side='left')
            gpx=xpix[good]
            dleft=np.where(leftidx>=0,xpix-gpx[np.clip(leftidx,0,len(gpx)-1)],np.inf)
            dright=np.where(rightidx<len(gpx),gpx[np.clip(rightidx,0,len(gpx)-1)]-xpix,np.inf)
            gap=np.minimum(dleft,dright)
            # Preserve substantial gaps as 0, but do not forcibly set the last wavelength to 0.
            yi[gap>min(35,max(8,int(0.025*len(xpix))))]=y0
            t=np.clip((yr0+(yi-y0)*(yr1-yr0)/(y1-y0))/100,0,1)
            px=px0+(xs-xr0)*(px1-px0)/(xr1-xr0)
            # Export only wavelengths actually covered by the selected image pixels.
            # Clip tiny float rounding; never insert arbitrary zeros due to extrapolation.
            ts=np.clip(np.interp(np.clip(px,l,r),xpix,t),0,1)
            self.output=(xs,ts)
            overlay=self.image.copy();draw=ImageDraw.Draw(overlay)
            # Continuous 3-pixel green overlay for easier comparison with the original curve.
            curve_points=[(int(xi), int(round(y0+(trans*100-yr0)*(y1-y0)/(yr1-yr0))))
                          for xi,trans in zip(xpix,t)]
            if len(curve_points)>1:
                draw.line(curve_points, fill=(0,190,60), width=3, joint='curve')
            elif curve_points:
                xi,cy=curve_points[0]
                draw.ellipse((xi-1,cy-1,xi+1,cy+1),fill=(0,190,60))
            self.overlay=overlay;self.update_canvas()
            self.status.set(f'Extracted {len(xs)} points ({lo:.2f} to {hi:.2f} nm); detected curve in {good.mean():.1%} of columns. Check the overlay. Note: X-axis extrapolation cannot recover curve data outside the image.')
        except Exception as ex:
            self.output=None;self.overlay=None;messagebox.showerror('Extraction',str(ex))
    def export_csv(self):
        if self.output is None:messagebox.showwarning('CSV','Extract a curve first.');return
        name=self.name.get().strip() or 'Custom filter'
        filebase=''.join(c if c.isalnum() or c in '-_' else '_' for c in name)
        path=filedialog.asksaveasfilename(title='Save FilterManager CSV',defaultextension='.csv',initialfile='FilterManager_'+filebase+'.csv',filetypes=[('CSV','*.csv')])
        if not path:return
        xs,ts=self.output
        try:
            with open(path,'w',encoding='utf-8',newline='') as f:
                f.write('type,filter\n')
                f.write('name,"'+name.replace('"','')+'"\n')
                f.write('channel,L\n')
                f.write('wavelength,"'+','.join(f'{z:.6f}'.rstrip('0').rstrip('.') for z in xs)+'"\n')
                f.write('transmission,"'+','.join(f'{z:.5f}' for z in ts)+'"\n')
        except OSError as ex:messagebox.showerror('CSV',str(ex));return
        messagebox.showinfo('CSV saved',f'File: {path}\nImport in PixInsight via FilterManager → Merge CSV filter definitions.')
    @staticmethod
    def make_siril_data(name,manufacturer,filter_type,mono_channel,xs,ts,source):
        if filter_type not in ('OSC_FILTER','MONO_FILTER'):raise ValueError('Invalid Siril filter type')
        if filter_type=='MONO_FILTER' and mono_channel not in ('LUM','RED','GREEN','BLUE'):raise ValueError('Invalid monochrome channel')
        wl=[round(float(x),6) for x in xs];v=[round(float(t),6) for t in ts]
        if len(wl)!=len(v) or len(wl)<2 or not all(b>a for a,b in zip(wl,wl[1:])):raise ValueError('Invalid wavelength array')
        if not all(math.isfinite(a) and math.isfinite(b) and 0<=b<=1 for a,b in zip(wl,v)):raise ValueError('Invalid transmission values')
        obj={'model':name,'name':name,'type':filter_type,'dataQualityMarker':2,
             'dataSource':source or 'Digitized from manufacturer spectral transmission chart',
             'manufacturer':manufacturer or 'Not specified','version':1,'units':'nm','range':1,
             'wavelength':wl,'values':v}
        if filter_type=='MONO_FILTER':obj['channel']=mono_channel
        return [obj]
    def export_siril(self):
        if self.output is None:messagebox.showwarning('JSON','Extract a curve first.');return
        name=self.name.get().strip() or 'Custom filter'
        filebase=''.join(c if c.isalnum() or c in '-_' else '_' for c in name)
        path=filedialog.asksaveasfilename(title='Save Siril JSON',defaultextension='.json',initialfile='Siril_'+filebase+'.json',filetypes=[('JSON','*.json')])
        if not path:return
        try:
            xs,ts=self.output
            data=self.make_siril_data(name,self.manufacturer.get().strip(),self.filter_type.get(),self.mono_channel.get(),xs,ts,self.data_source.get().strip())
            with open(path,'w',encoding='utf-8') as f:json.dump(data,f,ensure_ascii=False,indent=2,allow_nan=False);f.write('\n')
        except (OSError,ValueError,TypeError) as ex:messagebox.showerror('JSON',str(ex));return
        messagebox.showinfo('JSON saved',f'File: {path}\nVerify that Siril can load this JSON into its local SPCC database.')
    def save_overlay(self):
        if self.overlay is None:messagebox.showwarning('Overlay','Extract a curve first.');return
        path=filedialog.asksaveasfilename(title='Save curve overlay',defaultextension='.png',filetypes=[('PNG','*.png')])
        if path:self.overlay.save(path)

def main():
    if "--check-ssl" in sys.argv[1:]:
        test_github_https()
        return
    root=tk.Tk()
    try:ttk.Style().theme_use('clam')
    except tk.TclError:pass
    Digitizer(root);root.mainloop()
if __name__=='__main__':main()
