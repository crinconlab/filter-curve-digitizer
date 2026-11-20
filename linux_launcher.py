#!/usr/bin/env python3
"""Linux entry point and packaged image-rendering self-test.

Keeps the shared Filter_Curve_Digitizer.py application unchanged.
"""
from __future__ import annotations

import os
import sys
import traceback


def self_test() -> int:
    """Exercise the same Pillow ImageTk -> Tk Canvas rendering path as the app."""
    import tkinter as tk
    from PIL import Image
    import PIL
    import Filter_Curve_Digitizer as application

    print("Filter Curve Digitizer — Linux display self-test", flush=True)
    print(f"Python: {sys.version.split()[0]}  Pillow: {PIL.__version__}", flush=True)
    print(f"DISPLAY={os.environ.get('DISPLAY', '<unset>')}, "
          f"XDG_SESSION_TYPE={os.environ.get('XDG_SESSION_TYPE', '<unset>')}", flush=True)
    root = tk.Tk()
    root.geometry("1000x700")
    try:
        app = application.Digitizer(root)
        root.update_idletasks()
        root.update()
        # Red picture created without reading a disk or shared-folder file.
        app.image = Image.new("RGB", (400, 250), (255, 0, 0))
        app.update_canvas()
        root.update_idletasks()
        root.update()
        if app.photo is None:
            raise RuntimeError("No PIL ImageTk PhotoImage was created.")
        items = app.canvas.find_all()
        if not items or app.canvas.type(items[0]) != "image":
            raise RuntimeError(f"Tk Canvas contains no image item: {items!r}")
        # Check the actual pixels in Tcl's image, not merely the Pillow original.
        pixel = root.tk.call(str(app.photo), 'get', 10, 10)
        print(f"Rendered Tk pixel (10,10): {pixel!r}", flush=True)
        if isinstance(pixel, (tuple, list)):
            good = tuple(pixel[:3]) == (255, 0, 0)
        else:
            good = str(pixel).lower() in ("#ff0000", "red", "255 0 0")
        if not good:
            raise RuntimeError(f"Rendered Tk pixel is not red: {pixel!r}. "
                               "Possible missing PIL._imagingtk or incompatible Tcl/Tk library.")
        print("PASS: the packaged app can render Pillow RGB data into its Tk Canvas.", flush=True)
        return 0
    finally:
        root.destroy()


def main() -> int:
    if "--self-test" in sys.argv[1:]:
        try:
            return self_test()
        except Exception:
            traceback.print_exc()
            return 1
    # With a console build, Tk callback exceptions remain visible.
    import Filter_Curve_Digitizer as application
    application.main()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
