#!/usr/bin/env python3
"""Filter Curve Digitizer v1.3 test - independent X calibration and export range.
Requires Python with tkinter, numpy, Pillow. No network access.
"""
from __future__ import annotations
import json
import math
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from pathlib import Path
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
        root.title('Filter Curve Digitizer v1.3b — PixInsight / Siril')
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
        self.info=tk.StringVar(value='Open a plot image. Calibrate using two known axis ticks, then select the visible plot boundaries.')
        ttk.Label(root,textvariable=self.info,padding=(9,2,9,7),wraplength=1160).pack(anchor='w')
        frame=ttk.Frame(root);frame.pack(fill='both',expand=True,padx=9,pady=(0,7))
        self.canvas=tk.Canvas(frame,bg='#e7e7e7',highlightthickness=1,highlightbackground='#999')
        self.canvas.pack(fill='both',expand=True)
        self.canvas.bind('<Button-1>',self.on_click)
        self.canvas.bind('<Configure>',lambda ev:self.update_canvas())
        self.status=tk.StringVar(value='No image loaded.')
        ttk.Label(root,textvariable=self.status,padding=(9,0,9,8),wraplength=1160).pack(anchor='w')
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
        self.info.set(self.STEPS[0][1] if self.image else 'Open an image.')
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
        self.info.set(self.STEPS[self.step_idx][1] if self.step_idx<len(self.STEPS) else 'Calibration complete. Extract the curve and CHECK the green overlay.')
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
    root=tk.Tk()
    try:ttk.Style().theme_use('clam')
    except tk.TclError:pass
    Digitizer(root);root.mainloop()
if __name__=='__main__':main()
