#!/usr/bin/env python3
"""
Blur Tool - Video Yuz/Kanli Bolge Bulaniklastirma Programi
=============================================================

Kurulum (bir kere, terminalde):
    pip install opencv-contrib-python pillow numpy

Calistirma:
    python3 blur_gui.py

Kullanim:
    1. "Video Ac" ile videoni sec.
    2. Ilk kare goruntulenir. Fare ile suruklyerek kutu(lar) ciz
       (yuz, kanli bolge, veya baska hassas alan - hepsi ayni sekilde islenir).
    3. Yanlis kutuyu silmek icin listeden "x" tikla.
    4. "Bulaniklastir ve Kaydet" tikla, cikti dosyasini sec.
    5. Islem bitince otomatik olarak video klasorune kaydedilir.

Notlar:
    - Kutular MOSSE tracker ile video boyunca otomatik takip edilir.
    - Ses otomatik olarak orijinal videodan kopyalanir (ffmpeg gerekir, sistemde kurulu olmali).
    - Blur siddetini sag ust kosedeki kaydirmadan ayarlayabilirsin.
"""

import sys
import os
import shutil
import subprocess
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

try:
    import cv2
except ImportError:
    print("HATA: opencv-contrib-python kurulu degil.")
    print("Kurmak icin: pip install opencv-contrib-python pillow numpy")
    sys.exit(1)

try:
    from PIL import Image, ImageTk
except ImportError:
    print("HATA: Pillow kurulu degil.")
    print("Kurmak icin: pip install opencv-contrib-python pillow numpy")
    sys.exit(1)


def make_tracker():
    mod = cv2.legacy if hasattr(cv2, "legacy") else cv2
    return mod.TrackerMOSSE_create()


def blur_region(frame, box, blur_strength):
    x, y, w, h = [int(v) for v in box]
    H, W = frame.shape[:2]
    x = max(0, x)
    y = max(0, y)
    w = max(1, min(w, W - x))
    h = max(1, min(h, H - y))
    if w <= 0 or h <= 0:
        return frame
    roi = frame[y:y + h, x:x + w]
    k = blur_strength
    if k % 2 == 0:
        k += 1
    k = max(3, k)
    frame[y:y + h, x:x + w] = cv2.GaussianBlur(roi, (k, k), 0)
    return frame


class BlurApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Blur Tool - Yuz / Kanli Bolge Bulaniklastirma")
        self.root.configure(bg="#16181d")
        self.root.geometry("980x680")

        self.video_path = None
        self.cap = None
        self.first_frame = None       # native-res BGR frame
        self.display_scale = 1.0      # native_px = display_px * display_scale
        self.tk_img = None
        self.boxes = []                # list of dict: x,y,w,h (native coords), canvas_id, tag_id
        self.drawing = None

        self._build_ui()

    # ---------------- UI ----------------
    def _build_ui(self):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TButton", background="#2c3038", foreground="#e8e6e1",
                         borderwidth=0, padding=8, font=("Helvetica", 10, "bold"))
        style.map("TButton", background=[("active", "#3a3f4a")])
        style.configure("Accent.TButton", background="#ff5a5f", foreground="#0b0c0f")
        style.map("Accent.TButton", background=[("active", "#ff787c")])
        style.configure("TLabel", background="#16181d", foreground="#e8e6e1", font=("Helvetica", 10))
        style.configure("Dim.TLabel", background="#16181d", foreground="#8b8f98", font=("Helvetica", 9))
        style.configure("Horizontal.TScale", background="#16181d")

        top = tk.Frame(self.root, bg="#16181d")
        top.pack(fill="x", padx=14, pady=10)

        ttk.Button(top, text="Video Ac", command=self.open_video).pack(side="left")
        self.path_label = ttk.Label(top, text="Video secilmedi", style="Dim.TLabel")
        self.path_label.pack(side="left", padx=12)

        main = tk.Frame(self.root, bg="#16181d")
        main.pack(fill="both", expand=True, padx=14, pady=6)

        # canvas
        canvas_frame = tk.Frame(main, bg="#0e1013", bd=1, relief="solid")
        canvas_frame.pack(side="left", fill="both", expand=True)
        self.canvas = tk.Canvas(canvas_frame, bg="#0e1013", highlightthickness=0, cursor="crosshair")
        self.canvas.pack(fill="both", expand=True)
        self.canvas.bind("<ButtonPress-1>", self.on_press)
        self.canvas.bind("<B1-Motion>", self.on_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_release)

        # side panel
        panel = tk.Frame(main, bg="#16181d", width=270)
        panel.pack(side="right", fill="y", padx=(14, 0))
        panel.pack_propagate(False)

        ttk.Label(panel, text="ISARETLENEN BOLGELER", style="Dim.TLabel").pack(anchor="w", pady=(0, 6))
        self.list_frame = tk.Frame(panel, bg="#16181d")
        self.list_frame.pack(fill="x")
        self.empty_hint = ttk.Label(self.list_frame, text="Video actiktan sonra\ngoruntu uzerinde suruklye.",
                                     style="Dim.TLabel")
        self.empty_hint.pack(anchor="w", pady=4)

        ttk.Label(panel, text="").pack(pady=6)  # spacer
        ttk.Label(panel, text="BULANIKLIK SIDDETI", style="Dim.TLabel").pack(anchor="w")
        self.blur_var = tk.IntVar(value=55)
        ttk.Scale(panel, from_=15, to=99, variable=self.blur_var, orient="horizontal").pack(fill="x", pady=4)

        ttk.Label(panel, text="").pack(pady=10)
        self.process_btn = ttk.Button(panel, text="Bulaniklastir ve Kaydet",
                                       style="Accent.TButton", command=self.process_video_thread)
        self.process_btn.pack(fill="x")
        ttk.Button(panel, text="Tum kutulari temizle", command=self.clear_boxes).pack(fill="x", pady=(8, 0))

        self.status_label = ttk.Label(panel, text="", style="Dim.TLabel", wraplength=250)
        self.status_label.pack(anchor="w", pady=(14, 0))

        self.progress = ttk.Progressbar(panel, mode="determinate")
        self.progress.pack(fill="x", pady=(10, 0))

        if not shutil.which("ffmpeg"):
            warn = ttk.Label(
                panel,
                text="⚠ ffmpeg bulunamadi.\nSes eklenemeyecek, sessiz\nvideo kaydedilecek.",
                style="Dim.TLabel", wraplength=250)
            warn.pack(anchor="w", pady=(10, 0))

    # ---------------- video loading ----------------
    def open_video(self):
        path = filedialog.askopenfilename(
            title="Video sec",
            filetypes=[("Video files", "*.mp4 *.mov *.avi *.mkv *.webm"), ("All files", "*.*")]
        )
        if not path:
            return
        cap = cv2.VideoCapture(path)
        if not cap.isOpened():
            messagebox.showerror("Hata", "Video acilamadi.")
            return
        ret, frame = cap.read()
        if not ret:
            messagebox.showerror("Hata", "Videodan kare okunamadi.")
            return

        self.video_path = path
        self.cap = cap
        self.first_frame = frame
        self.boxes = []
        self.render_boxes_list()
        self.path_label.config(text=os.path.basename(path))
        self.show_frame_on_canvas(frame)

    def show_frame_on_canvas(self, frame_bgr):
        self.canvas.delete("all")
        h, w = frame_bgr.shape[:2]
        max_w, max_h = 640, 620
        scale = min(max_w / w, max_h / h, 1.0)
        disp_w, disp_h = int(w * scale), int(h * scale)
        self.display_scale = w / disp_w  # native = display * display_scale

        rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        img = Image.fromarray(rgb).resize((disp_w, disp_h))
        self.tk_img = ImageTk.PhotoImage(img)
        self.canvas.config(width=disp_w, height=disp_h)
        self.canvas.create_image(0, 0, anchor="nw", image=self.tk_img, tags="bg")

    # ---------------- drawing boxes ----------------
    def on_press(self, event):
        if self.first_frame is None:
            return
        self.drawing = {"x0": event.x, "y0": event.y,
                         "rect": self.canvas.create_rectangle(
                             event.x, event.y, event.x, event.y,
                             outline="#ff5a5f", width=2)}

    def on_drag(self, event):
        if not self.drawing:
            return
        self.canvas.coords(self.drawing["rect"], self.drawing["x0"], self.drawing["y0"], event.x, event.y)

    def on_release(self, event):
        if not self.drawing:
            return
        x0, y0 = self.drawing["x0"], self.drawing["y0"]
        x1, y1 = event.x, event.y
        dx, dy = abs(x1 - x0), abs(y1 - y0)
        if dx < 6 or dy < 6:
            self.canvas.delete(self.drawing["rect"])
            self.drawing = None
            return
        left, top = min(x0, x1), min(y0, y1)
        sf = self.display_scale
        box = {
            "x": int(left * sf), "y": int(top * sf),
            "w": int(dx * sf), "h": int(dy * sf),
            "canvas_id": self.drawing["rect"]
        }
        self.boxes.append(box)
        self.drawing = None
        self.render_boxes_list()

    def clear_boxes(self):
        for b in self.boxes:
            self.canvas.delete(b["canvas_id"])
        self.boxes = []
        self.render_boxes_list()

    def remove_box(self, idx):
        b = self.boxes.pop(idx)
        self.canvas.delete(b["canvas_id"])
        self.render_boxes_list()

    def render_boxes_list(self):
        for widget in self.list_frame.winfo_children():
            widget.destroy()
        if not self.boxes:
            self.empty_hint = ttk.Label(self.list_frame, text="Video actiktan sonra\ngoruntu uzerinde suruklye.",
                                         style="Dim.TLabel")
            self.empty_hint.pack(anchor="w", pady=4)
            return
        for i, b in enumerate(self.boxes):
            row = tk.Frame(self.list_frame, bg="#1e2128")
            row.pack(fill="x", pady=2)
            ttk.Label(row, text=f"Bolge {i+1}: {b['x']},{b['y']},{b['w']},{b['h']}",
                      background="#1e2128", foreground="#e8e6e1", font=("Consolas", 9)).pack(
                side="left", padx=6, pady=4)
            tk.Button(row, text="x", bg="#1e2128", fg="#8b8f98", bd=0,
                      command=lambda idx=i: self.remove_box(idx)).pack(side="right", padx=4)

    # ---------------- processing ----------------
    def process_video_thread(self):
        if not self.video_path or not self.boxes:
            messagebox.showwarning("Eksik", "Once bir video ac ve en az bir bolge cizin.")
            return
        out_path = filedialog.asksaveasfilename(
            title="Ciktiyi kaydet", defaultextension=".mp4",
            initialfile=os.path.splitext(os.path.basename(self.video_path))[0] + "_blurred.mp4",
            filetypes=[("MP4 video", "*.mp4")])
        if not out_path:
            return
        self.process_btn.config(state="disabled")
        t = threading.Thread(target=self.process_video, args=(out_path,), daemon=True)
        t.start()

    def process_video(self, out_path):
        try:
            self._process_video_impl(out_path)
            self.root.after(0, lambda: messagebox.showinfo("Tamamlandi", f"Kaydedildi:\n{out_path}"))
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Hata", str(e)))
        finally:
            self.root.after(0, lambda: self.process_btn.config(state="normal"))
            self.root.after(0, lambda: self.status_label.config(text=""))

    def _process_video_impl(self, out_path):
        cap = cv2.VideoCapture(self.video_path)
        fps = cap.get(cv2.CAP_PROP_FPS) or 30
        W = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        H = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) or 1

        tmp_out = out_path + ".noaudio.mp4"
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        writer = cv2.VideoWriter(tmp_out, fourcc, fps, (W, H))

        blur_strength = self.blur_var.get()
        boxes = [(b["x"], b["y"], b["w"], b["h"]) for b in self.boxes]
        trackers = [make_tracker() for _ in boxes]
        initialized = [False] * len(boxes)

        frame_idx = 0
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            for i, box in enumerate(boxes):
                if not initialized[i]:
                    trackers[i].init(frame, box)
                    initialized[i] = True
                    cur = box
                else:
                    ok, cur = trackers[i].update(frame)
                    if not ok:
                        cur = box
                frame = blur_region(frame, cur, blur_strength)
            writer.write(frame)
            frame_idx += 1
            if frame_idx % 5 == 0 or frame_idx == total:
                pct = min(100, int(frame_idx / total * 100))
                self.root.after(0, lambda p=pct, f=frame_idx, t=total:
                                 (self.progress.config(value=p),
                                  self.status_label.config(text=f"Isleniyor... {f}/{t} kare")))

        cap.release()
        writer.release()

        self.root.after(0, lambda: self.status_label.config(text="Ses ekleniyor..."))
        ok, reason = self._remux_audio(tmp_out, out_path)

        if ok:
            if os.path.exists(tmp_out):
                os.remove(tmp_out)
        else:
            # keep the video-only result but tell the user clearly why there's no audio
            if os.path.exists(out_path):
                os.remove(out_path)
            os.replace(tmp_out, out_path)
            self.root.after(0, lambda: messagebox.showwarning(
                "Ses eklenemedi",
                "Video islendi ama SESSIZ kaydedildi.\n\nSebep: " + reason +
                "\n\nCozum: sisteminize ffmpeg kurun (orn. 'brew install ffmpeg' "
                "veya 'sudo apt install ffmpeg' veya ffmpeg.org'dan indirin), "
                "PATH'e ekleyin, sonra videoyu tekrar isleyin."))

        self.root.after(0, lambda: self.progress.config(value=100))

    def _remux_audio(self, video_only_path, out_path):
        """Copy audio from the original file onto the processed (silent) video.
        Returns (success: bool, reason: str)."""
        ffmpeg_bin = shutil.which("ffmpeg")
        if not ffmpeg_bin:
            return False, "ffmpeg sisteminizde bulunamadi (PATH'te yok)."

        # First check whether the source actually has an audio stream at all.
        ffprobe_bin = shutil.which("ffprobe")
        has_audio = True  # assume yes if we can't check; ffmpeg's optional map handles it
        if ffprobe_bin:
            try:
                probe = subprocess.run(
                    [ffprobe_bin, "-v", "error", "-select_streams", "a",
                     "-show_entries", "stream=index", "-of", "csv=p=0", self.video_path],
                    capture_output=True, text=True, timeout=30)
                has_audio = bool(probe.stdout.strip())
            except Exception:
                pass

        if not has_audio:
            return False, "Orijinal videoda ses kanali bulunamadi."

        # Use explicit mapping without the '?' optional-stream syntax for
        # compatibility with older ffmpeg builds.
        cmd = [ffmpeg_bin, "-y", "-i", video_only_path, "-i", self.video_path,
               "-map", "0:v:0", "-map", "1:a:0",
               "-c:v", "copy", "-c:a", "aac", "-shortest", out_path]
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        except FileNotFoundError:
            return False, "ffmpeg calistirilamadi."
        except subprocess.TimeoutExpired:
            return False, "ffmpeg zaman asimina ugradi."

        if result.returncode == 0 and os.path.exists(out_path) and os.path.getsize(out_path) > 0:
            return True, ""
        return False, (result.stderr or "").strip()[-300:] or "Bilinmeyen ffmpeg hatasi."


def main():
    root = tk.Tk()
    app = BlurApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
