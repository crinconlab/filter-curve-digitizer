#!/usr/bin/env python3
"""Filter Curve Digitizer: manual axis calibration and color-based curve extraction.

Requires: Python 3, Pillow, NumPy. Optional: none. No network access.
Based on the workflow proposed for digitizing transmission graphs for PixInsight.
"""
from __future__ import annotations

import csv
import json
import math
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from pathlib import Path

import numpy as np
from PIL import Image, ImageTk, ImageDraw


class Digitizer:
    STEPS = [
        ("x0", "1/5: Haz clic en la coordenada del mínimo del eje X (sobre el eje horizontal)."),
        ("x1", "2/5: Haz clic en la coordenada del máximo del eje X."),
        ("y0", "3/5: Haz clic en la coordenada del mínimo del eje Y (sobre el eje vertical)."),
        ("y1", "4/5: Haz clic en la coordenada del máximo del eje Y."),
        ("sample", "5/5: Haz clic exactamente en la línea de transmisión para identificar su color."),
    ]

    def __init__(self, root):
        self.root = root
        root.title("Filter Curve Digitizer — PixInsight / Siril")
        root.geometry("1160x865")
        self.image = None
        self.display_image = None
        self.photo = None
        self.scale = 1.0
        self.points = {}
        self.step_idx = 0
        self.output = None
        self.overlay = None
        self.image_path = None

        top = ttk.Frame(root, padding=10)
        top.pack(fill="x")
        ttk.Button(top, text="Abrir imagen…", command=self.open_image).pack(side="left")
        ttk.Button(top, text="Reiniciar calibración", command=self.reset_calibration).pack(side="left", padx=8)
        ttk.Button(top, text="Extraer curva", command=self.extract).pack(side="left", padx=8)
        ttk.Button(top, text="CSV PixInsight…", command=self.export_csv).pack(side="left", padx=8)
        ttk.Button(top, text="JSON Siril…", command=self.export_siril).pack(side="left", padx=8)
        ttk.Button(top, text="Guardar verificación…", command=self.save_overlay).pack(side="left", padx=8)

        opts = ttk.Frame(root, padding=(10,0,10,8))
        opts.pack(fill="x")
        self.name = tk.StringVar(value="Filtro personalizado")
        self.xmin = tk.StringVar(value="200")
        self.xmax = tk.StringVar(value="1100")
        self.ymin = tk.StringVar(value="0")
        self.ymax = tk.StringVar(value="100")
        self.step = tk.StringVar(value="1")
        self.tol = tk.IntVar(value=75)
        self.manufacturer = tk.StringVar(value="")
        self.filter_type = tk.StringVar(value="OSC_FILTER")
        self.mono_channel = tk.StringVar(value="LUM")
        self.data_source = tk.StringVar(value="Curva digitalizada de gráfica del fabricante")
        self._field(opts, "Nombre:", self.name, 27)
        self._field(opts, "X mín (nm):", self.xmin, 7)
        self._field(opts, "X máx (nm):", self.xmax, 7)
        self._field(opts, "Y mín (%):", self.ymin, 6)
        self._field(opts, "Y máx (%):", self.ymax, 6)
        self._field(opts, "Paso (nm):", self.step, 6)

        siril_opts = ttk.Frame(root, padding=(10,0,10,8))
        siril_opts.pack(fill="x")
        self._field(siril_opts, "Fabricante (Siril):", self.manufacturer, 18)
        ttk.Label(siril_opts, text="Tipo:").pack(side="left")
        ttk.Combobox(siril_opts, textvariable=self.filter_type, values=("OSC_FILTER", "MONO_FILTER"), width=13, state="readonly").pack(side="left", padx=(4,12))
        ttk.Label(siril_opts, text="Canal (mono):").pack(side="left")
        ttk.Combobox(siril_opts, textvariable=self.mono_channel, values=("LUM", "RED", "GREEN", "BLUE"), width=7, state="readonly").pack(side="left", padx=(4,12))
        more = ttk.Frame(root, padding=(10,0,10,8))
        more.pack(fill="x")
        ttk.Label(more, text="Tolerancia de color:").pack(side="left")
        ttk.Scale(more, from_=20, to=160, variable=self.tol, orient="horizontal", length=210).pack(side="left", padx=(6,15))
        ttk.Label(more, text="Consejo: elimina las leyendas de la zona del gráfico y usa una curva de color distinto a la cuadrícula.").pack(side="left")

        self.info = tk.StringVar(value="Abre una gráfica JPG, PNG o WEBP para comenzar.")
        ttk.Label(root, textvariable=self.info, padding=(10,0,10,7), wraplength=1080).pack(anchor="w")
        frame = ttk.Frame(root)
        frame.pack(fill="both", expand=True, padx=10, pady=(0,8))
        self.canvas = tk.Canvas(frame, bg="#e7e7e7", highlightthickness=1, highlightbackground="#999999")
        self.canvas.pack(side="left", fill="both", expand=True)
        self.canvas.bind("<Button-1>", self.on_click)
        self.canvas.bind("<Configure>", lambda e: self.update_canvas())
        self.status = tk.StringVar(value="Pendiente de cargar imagen.")
        ttk.Label(root, textvariable=self.status, padding=(10,0,10,8), wraplength=1100).pack(anchor="w")

    @staticmethod
    def _field(parent, label, var, width):
        ttk.Label(parent, text=label).pack(side="left", padx=(0,3))
        ttk.Entry(parent, textvariable=var, width=width).pack(side="left", padx=(0,10))

    def open_image(self):
        path = filedialog.askopenfilename(
            title="Selecciona la gráfica de transmisión",
            filetypes=[("Imágenes", "*.png *.jpg *.jpeg *.webp *.bmp *.tif *.tiff"), ("Todos los archivos", "*")])
        if not path:
            return
        try:
            im = Image.open(path).convert("RGB")
            if im.width < 80 or im.height < 80:
                raise ValueError("Imagen demasiado pequeña")
        except Exception as exc:
            messagebox.showerror("Imagen", str(exc)); return
        self.image = im
        self.image_path = Path(path)
        self.name.set(self.image_path.stem)
        self.reset_calibration()
        self.update_canvas()

    def reset_calibration(self):
        self.points = {}
        self.step_idx = 0
        self.output = None
        self.overlay = None
        self.info.set(self.STEPS[0][1] if self.image else "Abre una gráfica para comenzar.")
        self.status.set("Calibra los dos ejes y selecciona el color de la curva.")
        self.update_canvas()

    def update_canvas(self):
        if not self.image:
            return
        cw = max(self.canvas.winfo_width()-12, 200)
        ch = max(self.canvas.winfo_height()-12, 200)
        self.scale = min(cw/self.image.width, ch/self.image.height, 1.6)
        sz = (max(1,round(self.image.width*self.scale)),max(1,round(self.image.height*self.scale)))
        im = (self.overlay or self.image).resize(sz, Image.Resampling.LANCZOS)
        self.photo = ImageTk.PhotoImage(im)
        self.canvas.delete("all")
        self.canvas.create_image(0,0,image=self.photo,anchor="nw")
        if not self.overlay:
            for k, (x,y) in self.points.items():
                cx, cy = x*self.scale, y*self.scale
                r=5
                self.canvas.create_line(cx-r,cy,cx+r,cy,fill="blue",width=2)
                self.canvas.create_line(cx,cy-r,cx,cy+r,fill="blue",width=2)
                self.canvas.create_text(cx+8,cy-10,text=k,fill="blue",anchor="w",font=("Helvetica",11,"bold"))

    def on_click(self, ev):
        if self.image is None or self.step_idx >= len(self.STEPS):
            return
        x,y = ev.x/self.scale, ev.y/self.scale
        if not (0 <= x < self.image.width and 0 <= y < self.image.height):
            return
        key, _ = self.STEPS[self.step_idx]
        if key == "sample":
            a = np.asarray(self.image)
            ix,iy=int(x),int(y)
            # Find strongest saturated pixel close to click, useful for anti-aliased thin lines.
            x0,x1=max(0,ix-5),min(a.shape[1],ix+6)
            y0,y1=max(0,iy-5),min(a.shape[0],iy+6)
            candidates=a[y0:y1,x0:x1].astype(float)
            strength=candidates.max(axis=2)-candidates.min(axis=2)
            k=np.unravel_index(np.argmax(strength),strength.shape)
            pixel=candidates[k]
            if strength[k]<30:
                messagebox.showwarning("Color", "No se detecta una línea de color cerca del clic. Acércate a la curva de transmisión.")
                return
            self.sample_color=pixel
            self.status.set(f"Color de curva detectado: RGB {tuple(int(z) for z in pixel)}. Ahora pulsa «Extraer curva».")
        self.points[key]=(x,y)
        self.step_idx+=1
        self.info.set(self.STEPS[self.step_idx][1] if self.step_idx < len(self.STEPS)
                      else "Calibración completa. Pulsa «Extraer curva». Comprueba la superposición antes de exportar.")
        self.update_canvas()

    def extract(self):
        if self.image is None or any(k not in self.points for k,_ in self.STEPS):
            messagebox.showwarning("Calibración", "Carga una imagen y completa los cinco clics."); return
        try:
            xmin,xmax=float(self.xmin.get()),float(self.xmax.get())
            ymin,ymax=float(self.ymin.get()),float(self.ymax.get())
            step=float(self.step.get())
            if not (xmax>xmin and ymax>ymin and step>0):
                raise ValueError("Los límites deben ser crecientes y el paso positivo.")
            if (xmax-xmin)/step>20000:
                raise ValueError("Demasiados puntos: aumenta el paso.")
            x0=self.points['x0'][0]; x1=self.points['x1'][0]
            y0=self.points['y0'][1]; y1=self.points['y1'][1]
            if abs(x1-x0)<50 or abs(y1-y0)<50:
                raise ValueError("Los puntos de los ejes están demasiado próximos.")
            left,right=sorted((round(x0),round(x1)))
            top,bottom=sorted((round(y0),round(y1)))
            arr=np.asarray(self.image,dtype=np.float32)
            region=arr[top:bottom+1,left:right+1]
            dist=np.sqrt(np.sum((region-self.sample_color)**2,axis=2))
            # Avoid accepting white grid pixels that may be close to a pale line color
            chroma=region.max(axis=2)-region.min(axis=2)
            valid=(dist <= int(self.tol.get())) & (chroma >= 25)
            # Trace the candidate pixels closest in color to the chosen curve.
            py=np.full(region.shape[1],np.nan)
            for i in range(region.shape[1]):
                ys=np.flatnonzero(valid[:,i])
                if len(ys):
                    best=ys[np.argmin(dist[ys,i])]
                    py[i]=top+float(best)
            good=np.isfinite(py)
            if good.sum()<10 or good.mean()<0.12:
                raise ValueError("No se ha detectado suficiente curva. Comprueba el color o aumenta la tolerancia.")
            # Linear interpolation across small gaps only. Larger missing sections assumed 0%.
            xpix=np.arange(left,right+1)
            yi=np.interp(xpix,xpix[good],py[good])
            gap=np.full(len(xpix),np.inf)
            gpx=xpix[good]
            if len(gpx):
                leftidx=np.searchsorted(gpx,xpix,side='right')-1
                rightidx=np.searchsorted(gpx,xpix,side='left')
                dleft=np.where(leftidx>=0, xpix-gpx[np.clip(leftidx,0,len(gpx)-1)], np.inf)
                dright=np.where(rightidx<len(gpx),gpx[np.clip(rightidx,0,len(gpx)-1)]-xpix,np.inf)
                gap=np.minimum(dleft,dright)
            yi[gap>min(35, max(8,int(0.025*len(xpix))))]=y0
            # Convert y pixel to transmittance percent; y0 corresponds to Y min, y1 to Y max.
            t=ymin+(yi-y0)*(ymax-ymin)/(y1-y0)
            t=np.clip(t,0,100)/100
            xs=np.arange(xmin,xmax+step*0.25,step)
            px=x0+(xs-xmin)*(x1-x0)/(xmax-xmin)
            ts=np.interp(px,xpix,t,left=0,right=0)
            ts=np.clip(ts,0,1)
            self.output=(xs,ts)
            overlay=self.image.copy()
            dr=ImageDraw.Draw(overlay)
            for px_i, y_i, tr in zip(xpix[::3],yi[::3],t[::3]):
                # Draw extracted line on top of image; green indicates detected transmission
                cy=y0+(float(tr*100)-ymin)*(y1-y0)/(ymax-ymin)
                dr.ellipse((px_i-1,cy-1,px_i+1,cy+1),fill=(0,190,60))
            self.overlay=overlay
            self.update_canvas()
            self.status.set(f"Extraídos {len(xs)} puntos ({xs[0]:g}–{xs[-1]:g} nm). "
                            f"Píxeles con curva detectada: {good.mean():.1%}. "
                            "Revisa los puntos verdes sobre la curva original antes de exportar.")
        except Exception as exc:
            self.output=None; self.overlay=None
            messagebox.showerror("Extracción", str(exc))

    def export_csv(self):
        if self.output is None:
            messagebox.showwarning("CSV", "Primero extrae una curva y comprueba la superposición."); return
        name=self.name.get().strip() or "Filtro personalizado"
        path=filedialog.asksaveasfilename(title="Guardar definición para FilterManager",defaultextension=".csv",
                                      initialfile="FilterManager_"+''.join(c if c.isalnum() or c in '-_' else '_' for c in name)+".csv",
                                      filetypes=[("CSV", "*.csv")])
        if not path: return
        xs,ts=self.output
        try:
            with open(path,'w',encoding='utf-8',newline='') as f:
                f.write('type,filter\n')
                f.write('name,"'+name.replace('"','')+'"\n')
                f.write('channel,L\n')
                f.write('wavelength,"'+','.join(f'{z:g}' for z in xs)+'"\n')
                f.write('transmission,"'+','.join(f'{z:.5f}' for z in ts)+'"\n')
        except OSError as exc:
            messagebox.showerror("Guardar",str(exc));return
        messagebox.showinfo("CSV guardado",f"Archivo: {path}\n\nImporta en PixInsight mediante FilterManager → Merge CSV filter definitions.\nEvita archivos ._ auxiliares en discos externos.")

    @staticmethod
    def make_siril_data(name, manufacturer, filter_type, mono_channel, xs, ts, source):
        """Build a Siril SPCC database JSON array (digitized manufacturer curve)."""
        if filter_type not in ("OSC_FILTER", "MONO_FILTER"):
            raise ValueError("Tipo Siril no válido")
        if filter_type == "MONO_FILTER" and mono_channel not in ("LUM", "RED", "GREEN", "BLUE"):
            raise ValueError("Canal monocromo no válido")
        wavelengths = [round(float(v), 6) for v in xs]
        values = [round(float(v), 6) for v in ts]
        if len(wavelengths) != len(values) or len(wavelengths) < 2:
            raise ValueError("La curva debe tener al menos dos puntos")
        if not all(math.isfinite(a) and math.isfinite(b) for a,b in zip(wavelengths, values)):
            raise ValueError("Hay valores no finitos")
        if not all(b > a for a,b in zip(wavelengths, wavelengths[1:])):
            raise ValueError("Longitudes de onda repetidas o no crecientes")
        if not all(0 <= v <= 1 for v in values):
            raise ValueError("La transmisión debe estar entre 0 y 1")
        record = {
            "model": name,
            "name": name,
            "type": filter_type,
            "dataQualityMarker": 2,
            "dataSource": source or "Digitized from manufacturer spectral transmission chart",
            "manufacturer": manufacturer or "Not specified",
            "version": 1,
            "units": "nm",
            "range": 1,
            "wavelength": wavelengths,
            "values": values,
        }
        if filter_type == "MONO_FILTER":
            record["channel"] = mono_channel
        return [record]

    def export_siril(self):
        if self.output is None:
            messagebox.showwarning("JSON", "Primero extrae una curva y revisa la superposición.")
            return
        name = self.name.get().strip() or "Filtro personalizado"
        filebase = ''.join(c if c.isalnum() or c in '-_' else '_' for c in name)
        path = filedialog.asksaveasfilename(
            title="Guardar definición JSON para Siril SPCC", defaultextension=".json",
            initialfile="Siril_"+filebase+".json", filetypes=[("JSON", "*.json")])
        if not path:
            return
        try:
            xs, ts = self.output
            payload = self.make_siril_data(
                name, self.manufacturer.get().strip(), self.filter_type.get(),
                self.mono_channel.get(), xs, ts,
                self.data_source.get().strip())
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(payload, f, ensure_ascii=False, indent=2, allow_nan=False)
                f.write('\n')
        except (OSError, ValueError, TypeError) as exc:
            messagebox.showerror("Exportación Siril", str(exc))
            return
        messagebox.showinfo("JSON guardado",
            f"Archivo: {path}\n\nDefinición creada para base de datos SPCC de Siril. "
            "No es un importador automático. Verifica cómo añadir el JSON a la base local "
            "y consulta 06_SIRIL_SPCC.txt. Para filtros multibanda estrechos, Siril "
            "recomienda su modo Narrowband.")

    def save_overlay(self):
        if self.overlay is None:
            messagebox.showwarning("Verificación", "Primero extrae una curva.");return
        path=filedialog.asksaveasfilename(title="Guardar superposición", defaultextension=".png",filetypes=[("PNG","*.png")])
        if path:self.overlay.save(path)


def main():
    root=tk.Tk()
    try:
        ttk.Style().theme_use('clam')
    except tk.TclError:
        pass
    Digitizer(root)
    root.mainloop()


if __name__=='__main__':
    main()
