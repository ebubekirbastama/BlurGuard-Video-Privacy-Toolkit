import os
import cv2
import shutil
import subprocess
import tempfile
import threading
import time
import tkinter as tk

from tkinter import filedialog, messagebox
from PIL import Image, ImageTk

import customtkinter as ctk


# ============================================================
# GENEL AYARLAR
# ============================================================

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


# ============================================================
# YARDIMCI FONKSİYONLAR
# ============================================================

def clamp(value, minimum, maximum):
    return max(minimum, min(value, maximum))


def box_iou(box1, box2):
    """
    İki kutunun Intersection over Union değerini hesaplar.
    box = (x, y, w, h)
    """

    x1, y1, w1, h1 = box1
    x2, y2, w2, h2 = box2

    xa = max(x1, x2)
    ya = max(y1, y2)

    xb = min(x1 + w1, x2 + w2)
    yb = min(y1 + h1, y2 + h2)

    intersection_w = max(0, xb - xa)
    intersection_h = max(0, yb - ya)

    intersection = intersection_w * intersection_h

    area1 = max(0, w1) * max(0, h1)
    area2 = max(0, w2) * max(0, h2)

    union = area1 + area2 - intersection

    if union <= 0:
        return 0.0

    return intersection / union


# ============================================================
# ANA PROGRAM
# ============================================================

class BlurGuardPro(ctk.CTk):

    def __init__(self):
        super().__init__()

        # ----------------------------------------------------
        # PENCERE
        # ----------------------------------------------------

        self.title("BlurGuard Pro")

        self.geometry("1180x760")
        self.minsize(900, 650)

        self.configure(fg_color="#090B10")

        self.protocol(
            "WM_DELETE_WINDOW",
            self.on_close
        )

        # ----------------------------------------------------
        # PROGRAM DEĞİŞKENLERİ
        # ----------------------------------------------------

        self.video_path = None
        self.manual_rois = []

        self.processing = False
        self.cancel_requested = False

        self.current_output_path = None

        # ----------------------------------------------------
        # YÜZ ALGILAMA
        # ----------------------------------------------------

        cascade_path = os.path.join(
            cv2.data.haarcascades,
            "haarcascade_frontalface_default.xml"
        )

        self.face_cascade = cv2.CascadeClassifier(
            cascade_path
        )

        if self.face_cascade.empty():
            messagebox.showerror(
                "Hata",
                "OpenCV yüz algılama modeli yüklenemedi."
            )

        # ----------------------------------------------------
        # GRID
        # ----------------------------------------------------

        self.grid_columnconfigure(
            0,
            weight=1
        )

        self.grid_rowconfigure(
            1,
            weight=1
        )

        # ----------------------------------------------------
        # ARAYÜZ
        # ----------------------------------------------------

        self.create_header()
        self.create_main_area()
        self.create_footer()

    # ========================================================
    # HEADER
    # ========================================================

    def create_header(self):

        self.header = ctk.CTkFrame(
            self,
            height=92,
            fg_color="#0E1118",
            corner_radius=0
        )

        self.header.grid(
            row=0,
            column=0,
            sticky="ew"
        )

        self.header.grid_columnconfigure(
            0,
            weight=1
        )

        title_area = ctk.CTkFrame(
            self.header,
            fg_color="transparent"
        )

        title_area.grid(
            row=0,
            column=0,
            sticky="w",
            padx=32,
            pady=18
        )

        self.logo_label = ctk.CTkLabel(
            title_area,
            text="BLURGUARD",
            font=ctk.CTkFont(
                family="Segoe UI",
                size=27,
                weight="bold"
            ),
            text_color="#F8FAFF"
        )

        self.logo_label.pack(
            side="left"
        )

        self.pro_badge = ctk.CTkLabel(
            title_area,
            text=" PRO ",
            height=26,
            corner_radius=7,
            fg_color="#246BFD",
            text_color="white",
            font=ctk.CTkFont(
                family="Segoe UI",
                size=11,
                weight="bold"
            )
        )

        self.pro_badge.pack(
            side="left",
            padx=(10, 0)
        )

        self.header_info = ctk.CTkLabel(
            self.header,
            text="Akıllı video gizleme ve hareketli alan takibi",
            font=ctk.CTkFont(
                size=13
            ),
            text_color="#7D8799"
        )

        self.header_info.grid(
            row=0,
            column=1,
            sticky="e",
            padx=32
        )

    # ========================================================
    # ANA ALAN
    # ========================================================

    def create_main_area(self):

        self.main = ctk.CTkFrame(
            self,
            fg_color="transparent"
        )

        self.main.grid(
            row=1,
            column=0,
            sticky="nsew",
            padx=26,
            pady=24
        )

        self.main.grid_columnconfigure(
            0,
            weight=5,
            uniform="main"
        )

        self.main.grid_columnconfigure(
            1,
            weight=3,
            uniform="main"
        )

        self.main.grid_rowconfigure(
            0,
            weight=1
        )

        self.create_left_card()
        self.create_right_card()

    # ========================================================
    # SOL PANEL
    # ========================================================

    def create_left_card(self):

        self.left_card = ctk.CTkFrame(
            self.main,
            fg_color="#11151E",
            corner_radius=22,
            border_width=1,
            border_color="#1D2430"
        )

        self.left_card.grid(
            row=0,
            column=0,
            sticky="nsew",
            padx=(0, 12)
        )

        self.left_card.grid_columnconfigure(
            0,
            weight=1
        )

        self.left_card.grid_rowconfigure(
            3,
            weight=1
        )

        # Başlık

        ctk.CTkLabel(
            self.left_card,
            text="Video İşleme",
            font=ctk.CTkFont(
                size=22,
                weight="bold"
            ),
            text_color="#F8FAFF"
        ).grid(
            row=0,
            column=0,
            sticky="w",
            padx=28,
            pady=(27, 4)
        )

        ctk.CTkLabel(
            self.left_card,
            text=(
                "Videoyu seç, hassas bölgeleri işaretle ve "
                "hareket boyunca otomatik takip et."
            ),
            font=ctk.CTkFont(
                size=13
            ),
            text_color="#7D8799",
            wraplength=600,
            justify="left"
        ).grid(
            row=1,
            column=0,
            sticky="w",
            padx=28,
            pady=(0, 20)
        )

        # Video alanı

        self.video_panel = ctk.CTkFrame(
            self.left_card,
            fg_color="#0C0F15",
            corner_radius=16,
            border_width=1,
            border_color="#202735"
        )

        self.video_panel.grid(
            row=2,
            column=0,
            sticky="ew",
            padx=28,
            pady=(0, 16)
        )

        self.video_panel.grid_columnconfigure(
            0,
            weight=1
        )

        self.video_icon = ctk.CTkLabel(
            self.video_panel,
            text="▶",
            width=54,
            height=54,
            corner_radius=27,
            fg_color="#182235",
            text_color="#4D8DFF",
            font=ctk.CTkFont(
                size=23,
                weight="bold"
            )
        )

        self.video_icon.grid(
            row=0,
            column=0,
            pady=(25, 10)
        )

        self.file_name_label = ctk.CTkLabel(
            self.video_panel,
            text="Henüz video seçilmedi",
            font=ctk.CTkFont(
                size=15,
                weight="bold"
            ),
            text_color="#DCE4F1"
        )

        self.file_name_label.grid(
            row=1,
            column=0,
            padx=15
        )

        self.file_info_label = ctk.CTkLabel(
            self.video_panel,
            text="MP4 • MOV • AVI • MKV • M4V",
            font=ctk.CTkFont(
                size=11
            ),
            text_color="#647083"
        )

        self.file_info_label.grid(
            row=2,
            column=0,
            pady=(4, 18)
        )

        # İşlem butonları

        buttons = ctk.CTkFrame(
            self.left_card,
            fg_color="transparent"
        )

        buttons.grid(
            row=3,
            column=0,
            sticky="new",
            padx=28,
            pady=(4, 15)
        )

        buttons.grid_columnconfigure(
            0,
            weight=1
        )

        buttons.grid_columnconfigure(
            1,
            weight=1
        )

        self.select_video_button = ctk.CTkButton(
            buttons,
            text="＋  Video Seç",
            command=self.select_video,
            height=50,
            corner_radius=13,
            fg_color="#246BFD",
            hover_color="#377CFF",
            text_color="white",
            font=ctk.CTkFont(
                size=14,
                weight="bold"
            )
        )

        self.select_video_button.grid(
            row=0,
            column=0,
            sticky="ew",
            padx=(0, 6),
            pady=5
        )

        self.select_roi_button = ctk.CTkButton(
            buttons,
            text="▣  Hassas Alan Seç",
            command=self.open_roi_selector,
            height=50,
            corner_radius=13,
            fg_color="#1A202B",
            hover_color="#252E3D",
            border_width=1,
            border_color="#313A49",
            text_color="#E6EBF4",
            state="disabled",
            font=ctk.CTkFont(
                size=14,
                weight="bold"
            )
        )

        self.select_roi_button.grid(
            row=0,
            column=1,
            sticky="ew",
            padx=(6, 0),
            pady=5
        )

        self.start_button = ctk.CTkButton(
            buttons,
            text="▶   İşlemeyi Başlat",
            command=self.ask_output,
            height=58,
            corner_radius=15,
            fg_color="#16A66A",
            hover_color="#1DB978",
            text_color="white",
            state="disabled",
            font=ctk.CTkFont(
                size=15,
                weight="bold"
            )
        )

        self.start_button.grid(
            row=1,
            column=0,
            columnspan=2,
            sticky="ew",
            pady=(10, 5)
        )

    # ========================================================
    # SAĞ PANEL
    # ========================================================

    def create_right_card(self):

        self.right_card = ctk.CTkFrame(
            self.main,
            fg_color="#11151E",
            corner_radius=22,
            border_width=1,
            border_color="#1D2430"
        )

        self.right_card.grid(
            row=0,
            column=1,
            sticky="nsew",
            padx=(12, 0)
        )

        self.right_card.grid_columnconfigure(
            0,
            weight=1
        )

        # Ayarlar başlığı

        ctk.CTkLabel(
            self.right_card,
            text="Sansür Ayarları",
            font=ctk.CTkFont(
                size=20,
                weight="bold"
            ),
            text_color="#F8FAFF"
        ).grid(
            row=0,
            column=0,
            sticky="w",
            padx=25,
            pady=(27, 5)
        )

        ctk.CTkLabel(
            self.right_card,
            text="Algılama ve blur seçeneklerini yapılandır.",
            text_color="#7D8799",
            font=ctk.CTkFont(
                size=12
            )
        ).grid(
            row=1,
            column=0,
            sticky="w",
            padx=25,
            pady=(0, 18)
        )

        # Yüz switch

        face_card = ctk.CTkFrame(
            self.right_card,
            fg_color="#0C1017",
            corner_radius=14
        )

        face_card.grid(
            row=2,
            column=0,
            sticky="ew",
            padx=22,
            pady=6
        )

        face_card.grid_columnconfigure(
            0,
            weight=1
        )

        ctk.CTkLabel(
            face_card,
            text="Otomatik Yüz Sansürü",
            font=ctk.CTkFont(
                size=13,
                weight="bold"
            ),
            text_color="#DCE4F1"
        ).grid(
            row=0,
            column=0,
            sticky="w",
            padx=15,
            pady=(13, 2)
        )

        ctk.CTkLabel(
            face_card,
            text="Yüzleri algılar ve hareket boyunca takip eder.",
            font=ctk.CTkFont(
                size=10
            ),
            text_color="#687588"
        ).grid(
            row=1,
            column=0,
            sticky="w",
            padx=15,
            pady=(0, 13)
        )

        self.face_switch = ctk.CTkSwitch(
            face_card,
            text="",
            width=45,
            progress_color="#246BFD"
        )

        self.face_switch.select()

        self.face_switch.grid(
            row=0,
            column=1,
            rowspan=2,
            padx=15
        )

        # Blur gücü

        blur_card = ctk.CTkFrame(
            self.right_card,
            fg_color="#0C1017",
            corner_radius=14
        )

        blur_card.grid(
            row=3,
            column=0,
            sticky="ew",
            padx=22,
            pady=6
        )

        blur_card.grid_columnconfigure(
            0,
            weight=1
        )

        self.blur_value_label = ctk.CTkLabel(
            blur_card,
            text="Blur Gücü  •  61",
            font=ctk.CTkFont(
                size=13,
                weight="bold"
            ),
            text_color="#DCE4F1"
        )

        self.blur_value_label.grid(
            row=0,
            column=0,
            sticky="w",
            padx=15,
            pady=(13, 7)
        )

        self.blur_slider = ctk.CTkSlider(
            blur_card,
            from_=21,
            to=151,
            number_of_steps=65,
            progress_color="#246BFD",
            button_color="#5D96FF",
            button_hover_color="#83AEFF",
            command=self.blur_slider_changed
        )

        self.blur_slider.set(61)

        self.blur_slider.grid(
            row=1,
            column=0,
            sticky="ew",
            padx=15,
            pady=(0, 16)
        )

        # Algılama sıklığı

        detection_card = ctk.CTkFrame(
            self.right_card,
            fg_color="#0C1017",
            corner_radius=14
        )

        detection_card.grid(
            row=4,
            column=0,
            sticky="ew",
            padx=22,
            pady=6
        )

        detection_card.grid_columnconfigure(
            0,
            weight=1
        )

        self.detect_value_label = ctk.CTkLabel(
            detection_card,
            text="Yüz Yenileme  •  12 kare",
            font=ctk.CTkFont(
                size=13,
                weight="bold"
            ),
            text_color="#DCE4F1"
        )

        self.detect_value_label.grid(
            row=0,
            column=0,
            sticky="w",
            padx=15,
            pady=(13, 7)
        )

        self.detect_slider = ctk.CTkSlider(
            detection_card,
            from_=5,
            to=30,
            number_of_steps=25,
            progress_color="#8956FF",
            button_color="#A47AFF",
            button_hover_color="#B996FF",
            command=self.detect_slider_changed
        )

        self.detect_slider.set(12)

        self.detect_slider.grid(
            row=1,
            column=0,
            sticky="ew",
            padx=15,
            pady=(0, 16)
        )

        # ROI bilgisi

        self.region_card = ctk.CTkFrame(
            self.right_card,
            fg_color="#0C1017",
            corner_radius=14
        )

        self.region_card.grid(
            row=5,
            column=0,
            sticky="ew",
            padx=22,
            pady=6
        )

        self.region_card.grid_columnconfigure(
            0,
            weight=1
        )

        ctk.CTkLabel(
            self.region_card,
            text="Manuel Takip Alanları",
            font=ctk.CTkFont(
                size=13,
                weight="bold"
            ),
            text_color="#DCE4F1"
        ).grid(
            row=0,
            column=0,
            sticky="w",
            padx=15,
            pady=(13, 2)
        )

        self.region_count_label = ctk.CTkLabel(
            self.region_card,
            text="0 alan seçildi",
            font=ctk.CTkFont(
                size=11
            ),
            text_color="#687588"
        )

        self.region_count_label.grid(
            row=1,
            column=0,
            sticky="w",
            padx=15,
            pady=(0, 13)
        )

        self.region_badge = ctk.CTkLabel(
            self.region_card,
            text="0",
            width=38,
            height=30,
            corner_radius=9,
            fg_color="#192230",
            text_color="#4D8DFF",
            font=ctk.CTkFont(
                size=13,
                weight="bold"
            )
        )

        self.region_badge.grid(
            row=0,
            column=1,
            rowspan=2,
            padx=15
        )

    # ========================================================
    # FOOTER / PROGRESS
    # ========================================================

    def create_footer(self):

        self.footer = ctk.CTkFrame(
            self,
            height=110,
            fg_color="#0E1118",
            corner_radius=0
        )

        self.footer.grid(
            row=2,
            column=0,
            sticky="ew"
        )

        self.footer.grid_columnconfigure(
            0,
            weight=1
        )

        progress_top = ctk.CTkFrame(
            self.footer,
            fg_color="transparent"
        )

        progress_top.grid(
            row=0,
            column=0,
            sticky="ew",
            padx=32,
            pady=(16, 5)
        )

        progress_top.grid_columnconfigure(
            0,
            weight=1
        )

        self.status_label = ctk.CTkLabel(
            progress_top,
            text="Hazır",
            font=ctk.CTkFont(
                size=12,
                weight="bold"
            ),
            text_color="#AAB4C4"
        )

        self.status_label.grid(
            row=0,
            column=0,
            sticky="w"
        )

        self.percent_label = ctk.CTkLabel(
            progress_top,
            text="0%",
            font=ctk.CTkFont(
                size=12,
                weight="bold"
            ),
            text_color="#4D8DFF"
        )

        self.percent_label.grid(
            row=0,
            column=1,
            sticky="e"
        )

        self.progressbar = ctk.CTkProgressBar(
            self.footer,
            height=10,
            corner_radius=6,
            progress_color="#246BFD",
            fg_color="#1B2230"
        )

        self.progressbar.set(0)

        self.progressbar.grid(
            row=1,
            column=0,
            sticky="ew",
            padx=32,
            pady=(3, 8)
        )

        self.detail_label = ctk.CTkLabel(
            self.footer,
            text="Bir video seçerek başlayabilirsin.",
            font=ctk.CTkFont(
                size=10
            ),
            text_color="#626E81"
        )

        self.detail_label.grid(
            row=2,
            column=0,
            sticky="w",
            padx=32,
            pady=(0, 10)
        )

    # ========================================================
    # SLIDER CALLBACKLER
    # ========================================================

    def blur_slider_changed(self, value):

        value = int(value)

        if value % 2 == 0:
            value += 1

        self.blur_value_label.configure(
            text=f"Blur Gücü  •  {value}"
        )

    def detect_slider_changed(self, value):

        value = int(value)

        self.detect_value_label.configure(
            text=f"Yüz Yenileme  •  {value} kare"
        )

    # ========================================================
    # VIDEO SEÇ
    # ========================================================

    def select_video(self):

        path = filedialog.askopenfilename(
            title="Video seç",
            filetypes=[
                (
                    "Video dosyaları",
                    "*.mp4 *.mov *.avi *.mkv *.m4v"
                ),
                (
                    "Tüm dosyalar",
                    "*.*"
                )
            ]
        )

        if not path:
            return

        cap = cv2.VideoCapture(path)

        if not cap.isOpened():
            messagebox.showerror(
                "Video açılamadı",
                "Seçilen video OpenCV tarafından açılamadı."
            )
            return

        fps = cap.get(
            cv2.CAP_PROP_FPS
        )

        width = int(
            cap.get(
                cv2.CAP_PROP_FRAME_WIDTH
            )
        )

        height = int(
            cap.get(
                cv2.CAP_PROP_FRAME_HEIGHT
            )
        )

        frames = int(
            cap.get(
                cv2.CAP_PROP_FRAME_COUNT
            )
        )

        cap.release()

        duration = 0

        if fps > 0:
            duration = frames / fps

        self.video_path = path
        self.manual_rois = []

        filename = os.path.basename(path)

        self.file_name_label.configure(
            text=filename
        )

        self.file_info_label.configure(
            text=(
                f"{width} × {height}  •  "
                f"{fps:.2f} FPS  •  "
                f"{duration:.1f} sn"
            )
        )

        self.region_count_label.configure(
            text="0 alan seçildi"
        )

        self.region_badge.configure(
            text="0"
        )

        self.select_roi_button.configure(
            state="normal"
        )

        self.start_button.configure(
            state="normal"
        )

        self.status_label.configure(
            text="Video hazır"
        )

        self.detail_label.configure(
            text="İstersen hassas alan seç veya doğrudan yüz sansürü başlat."
        )

        self.progressbar.set(0)
        self.percent_label.configure(
            text="0%"
        )

    # ========================================================
    # ROI SEÇİCİ
    # ========================================================

    def open_roi_selector(self):

        if not self.video_path:
            return

        cap = cv2.VideoCapture(
            self.video_path
        )

        ok, frame = cap.read()
        cap.release()

        if not ok:
            messagebox.showerror(
                "Hata",
                "Videonun ilk karesi okunamadı."
            )
            return

        rgb = cv2.cvtColor(
            frame,
            cv2.COLOR_BGR2RGB
        )

        original_h, original_w = rgb.shape[:2]

        # Ekran boyutuna göre ölçekle

        screen_w = self.winfo_screenwidth()
        screen_h = self.winfo_screenheight()

        max_w = int(screen_w * 0.78)
        max_h = int(screen_h * 0.70)

        scale = min(
            max_w / original_w,
            max_h / original_h,
            1.0
        )

        display_w = max(
            400,
            int(original_w * scale)
        )

        display_h = max(
            250,
            int(original_h * scale)
        )

        # Eğer min değer yüzünden büyüdüyse gerçek scale'i yeniden hesapla
        scale_x = display_w / original_w
        scale_y = display_h / original_h

        resized = cv2.resize(
            rgb,
            (display_w, display_h)
        )

        selector = ctk.CTkToplevel(
            self
        )

        selector.title(
            "Hassas Alan Seçimi"
        )

        selector.configure(
            fg_color="#090B10"
        )

        window_w = min(
            display_w + 70,
            screen_w - 50
        )

        window_h = min(
            display_h + 190,
            screen_h - 60
        )

        selector.geometry(
            f"{window_w}x{window_h}"
        )

        selector.minsize(
            650,
            500
        )

        selector.grab_set()

        selector.grid_columnconfigure(
            0,
            weight=1
        )

        selector.grid_rowconfigure(
            1,
            weight=1
        )

        # Üst açıklama

        header = ctk.CTkFrame(
            selector,
            fg_color="transparent"
        )

        header.grid(
            row=0,
            column=0,
            sticky="ew",
            padx=22,
            pady=(18, 10)
        )

        header.grid_columnconfigure(
            0,
            weight=1
        )

        ctk.CTkLabel(
            header,
            text="Hassas Alanları İşaretle",
            font=ctk.CTkFont(
                size=20,
                weight="bold"
            ),
            text_color="#F6F8FC"
        ).grid(
            row=0,
            column=0,
            sticky="w"
        )

        ctk.CTkLabel(
            header,
            text="Fareyi basılı tutup alanın çevresine kutu çiz.",
            font=ctk.CTkFont(
                size=11
            ),
            text_color="#778296"
        ).grid(
            row=1,
            column=0,
            sticky="w",
            pady=(2, 0)
        )

        selector_count = ctk.CTkLabel(
            header,
            text="0 ALAN",
            width=75,
            height=30,
            corner_radius=9,
            fg_color="#19253A",
            text_color="#5C95FF",
            font=ctk.CTkFont(
                size=11,
                weight="bold"
            )
        )

        selector_count.grid(
            row=0,
            column=1,
            rowspan=2,
            padx=5
        )

        # Canvas container

        canvas_frame = ctk.CTkFrame(
            selector,
            fg_color="#0E1219",
            corner_radius=14
        )

        canvas_frame.grid(
            row=1,
            column=0,
            sticky="nsew",
            padx=22,
            pady=5
        )

        canvas_frame.grid_columnconfigure(
            0,
            weight=1
        )

        canvas_frame.grid_rowconfigure(
            0,
            weight=1
        )

        canvas = tk.Canvas(
            canvas_frame,
            bg="#05070A",
            highlightthickness=0,
            cursor="cross"
        )

        canvas.grid(
            row=0,
            column=0,
            sticky="nsew",
            padx=7,
            pady=7
        )

        pil_image = Image.fromarray(
            resized
        )

        photo = ImageTk.PhotoImage(
            pil_image
        )

        canvas.photo = photo

        image_id = canvas.create_image(
            0,
            0,
            image=photo,
            anchor="nw"
        )

        canvas.config(
            scrollregion=(
                0,
                0,
                display_w,
                display_h
            )
        )

        # Geçici ROI'ler

        temp_rois = []
        rectangle_ids = []

        start_x = 0
        start_y = 0
        active_rect = None

        def mouse_down(event):

            nonlocal start_x
            nonlocal start_y
            nonlocal active_rect

            x = clamp(
                event.x,
                0,
                display_w
            )

            y = clamp(
                event.y,
                0,
                display_h
            )

            start_x = x
            start_y = y

            active_rect = canvas.create_rectangle(
                x,
                y,
                x,
                y,
                outline="#FF3D71",
                width=3
            )

        def mouse_drag(event):

            if active_rect is None:
                return

            x = clamp(
                event.x,
                0,
                display_w
            )

            y = clamp(
                event.y,
                0,
                display_h
            )

            canvas.coords(
                active_rect,
                start_x,
                start_y,
                x,
                y
            )

        def mouse_release(event):

            nonlocal active_rect

            if active_rect is None:
                return

            end_x = clamp(
                event.x,
                0,
                display_w
            )

            end_y = clamp(
                event.y,
                0,
                display_h
            )

            x1 = min(
                start_x,
                end_x
            )

            y1 = min(
                start_y,
                end_y
            )

            x2 = max(
                start_x,
                end_x
            )

            y2 = max(
                start_y,
                end_y
            )

            w = x2 - x1
            h = y2 - y1

            if w < 12 or h < 12:
                canvas.delete(
                    active_rect
                )

                active_rect = None
                return

            original_x = int(
                x1 / scale_x
            )

            original_y = int(
                y1 / scale_y
            )

            original_roi_w = int(
                w / scale_x
            )

            original_roi_h = int(
                h / scale_y
            )

            temp_rois.append(
                (
                    original_x,
                    original_y,
                    original_roi_w,
                    original_roi_h
                )
            )

            rectangle_ids.append(
                active_rect
            )

            active_rect = None

            selector_count.configure(
                text=f"{len(temp_rois)} ALAN"
            )

        def undo():

            if not temp_rois:
                return

            temp_rois.pop()

            rect_id = rectangle_ids.pop()

            canvas.delete(
                rect_id
            )

            selector_count.configure(
                text=f"{len(temp_rois)} ALAN"
            )

        def clear():

            temp_rois.clear()

            for rect_id in rectangle_ids:
                canvas.delete(
                    rect_id
                )

            rectangle_ids.clear()

            selector_count.configure(
                text="0 ALAN"
            )

        def confirm():

            self.manual_rois = list(
                temp_rois
            )

            count = len(
                self.manual_rois
            )

            self.region_count_label.configure(
                text=f"{count} alan seçildi"
            )

            self.region_badge.configure(
                text=str(count)
            )

            self.status_label.configure(
                text="Hassas alanlar hazır"
            )

            self.detail_label.configure(
                text=(
                    f"{count} manuel alan video boyunca "
                    "hareket takibiyle sansürlenecek."
                )
            )

            selector.destroy()

        canvas.bind(
            "<ButtonPress-1>",
            mouse_down
        )

        canvas.bind(
            "<B1-Motion>",
            mouse_drag
        )

        canvas.bind(
            "<ButtonRelease-1>",
            mouse_release
        )

        # Alt butonlar

        actions = ctk.CTkFrame(
            selector,
            fg_color="transparent"
        )

        actions.grid(
            row=2,
            column=0,
            sticky="ew",
            padx=22,
            pady=(10, 20)
        )

        actions.grid_columnconfigure(
            0,
            weight=1
        )

        actions.grid_columnconfigure(
            1,
            weight=1
        )

        actions.grid_columnconfigure(
            2,
            weight=2
        )

        ctk.CTkButton(
            actions,
            text="↶  Son Alanı Sil",
            command=undo,
            height=43,
            corner_radius=11,
            fg_color="#1B202A",
            hover_color="#272F3B",
            border_width=1,
            border_color="#333C49"
        ).grid(
            row=0,
            column=0,
            sticky="ew",
            padx=(0, 5)
        )

        ctk.CTkButton(
            actions,
            text="×  Temizle",
            command=clear,
            height=43,
            corner_radius=11,
            fg_color="#331923",
            hover_color="#48202D",
            text_color="#FF7395"
        ).grid(
            row=0,
            column=1,
            sticky="ew",
            padx=5
        )

        ctk.CTkButton(
            actions,
            text="✓  Seçimi Tamamla",
            command=confirm,
            height=43,
            corner_radius=11,
            fg_color="#246BFD",
            hover_color="#397DFF",
            font=ctk.CTkFont(
                size=13,
                weight="bold"
            )
        ).grid(
            row=0,
            column=2,
            sticky="ew",
            padx=(5, 0)
        )

    # ========================================================
    # OUTPUT SEÇ
    # ========================================================

    def ask_output(self):

        if not self.video_path:
            return

        original_name = os.path.splitext(
            os.path.basename(
                self.video_path
            )
        )[0]

        path = filedialog.asksaveasfilename(
            title="Sansürlü videoyu kaydet",
            initialfile=(
                original_name
                + "_blurred.mp4"
            ),
            defaultextension=".mp4",
            filetypes=[
                (
                    "MP4 Video",
                    "*.mp4"
                )
            ]
        )

        if not path:
            return

        self.current_output_path = path

        self.start_processing()

    # ========================================================
    # TRACKER OLUŞTUR
    # ========================================================

    def create_tracker(self):

        # Yeni OpenCV sürümleri
        if hasattr(
            cv2,
            "TrackerCSRT_create"
        ):
            return cv2.TrackerCSRT_create()

        # Legacy OpenCV sürümleri
        if (
            hasattr(cv2, "legacy")
            and hasattr(
                cv2.legacy,
                "TrackerCSRT_create"
            )
        ):
            return (
                cv2
                .legacy
                .TrackerCSRT_create()
            )

        raise RuntimeError(
            "CSRT tracker bulunamadı.\n\n"
            "Şunu yükle:\n"
            "pip install opencv-contrib-python"
        )

    # ========================================================
    # BLUR
    # ========================================================

    def blur_box(
        self,
        frame,
        box,
        strength,
        padding=0.0
    ):

        x, y, w, h = box

        frame_h, frame_w = (
            frame.shape[:2]
        )

        pad_x = int(
            w * padding
        )

        pad_y = int(
            h * padding
        )

        x = int(x - pad_x)
        y = int(y - pad_y)

        w = int(
            w + (pad_x * 2)
        )

        h = int(
            h + (pad_y * 2)
        )

        x = clamp(
            x,
            0,
            frame_w - 1
        )

        y = clamp(
            y,
            0,
            frame_h - 1
        )

        x2 = clamp(
            x + w,
            0,
            frame_w
        )

        y2 = clamp(
            y + h,
            0,
            frame_h
        )

        if x2 <= x or y2 <= y:
            return

        area = frame[
            y:y2,
            x:x2
        ]

        if area.size == 0:
            return

        kernel = int(
            strength
        )

        if kernel % 2 == 0:
            kernel += 1

        kernel = max(
            3,
            kernel
        )

        # Bölge çok küçükse kernel'i küçült

        max_kernel = min(
            area.shape[0],
            area.shape[1]
        )

        if max_kernel < 3:
            return

        if max_kernel % 2 == 0:
            max_kernel -= 1

        kernel = min(
            kernel,
            max_kernel
        )

        kernel = max(
            kernel,
            3
        )

        blurred = cv2.GaussianBlur(
            area,
            (kernel, kernel),
            0
        )

        # Daha güçlü gizleme için ikinci blur

        blurred = cv2.GaussianBlur(
            blurred,
            (kernel, kernel),
            0
        )

        frame[
            y:y2,
            x:x2
        ] = blurred

    # ========================================================
    # YÜZ ALGILAMA
    # ========================================================

    def detect_faces(self, frame):

        # Büyük videolarda algılamayı hızlandırmak için küçült

        h, w = frame.shape[:2]

        detection_scale = 1.0

        if w > 960:
            detection_scale = 960 / w

        if detection_scale < 1.0:

            small = cv2.resize(
                frame,
                None,
                fx=detection_scale,
                fy=detection_scale
            )

        else:
            small = frame

        gray = cv2.cvtColor(
            small,
            cv2.COLOR_BGR2GRAY
        )

        gray = cv2.equalizeHist(
            gray
        )

        faces = self.face_cascade.detectMultiScale(
            gray,
            scaleFactor=1.10,
            minNeighbors=5,
            minSize=(35, 35)
        )

        result = []

        for x, y, fw, fh in faces:

            if detection_scale != 1.0:

                x = int(
                    x / detection_scale
                )

                y = int(
                    y / detection_scale
                )

                fw = int(
                    fw / detection_scale
                )

                fh = int(
                    fh / detection_scale
                )

            result.append(
                (
                    int(x),
                    int(y),
                    int(fw),
                    int(fh)
                )
            )

        return result

    # ========================================================
    # YÜZ TRACKER GÜNCELLEME
    # ========================================================

    def update_face_trackers(
        self,
        frame,
        trackers
    ):

        updated = []

        for item in trackers:

            tracker = item["tracker"]

            success, box = tracker.update(
                frame
            )

            if success:

                x, y, w, h = box

                if w > 15 and h > 15:

                    item["box"] = (
                        int(x),
                        int(y),
                        int(w),
                        int(h)
                    )

                    item["missed"] = 0

                    updated.append(
                        item
                    )

            else:

                item["missed"] += 1

                if item["missed"] <= 5:
                    updated.append(
                        item
                    )

        return updated

    def sync_face_detections(
        self,
        frame,
        trackers,
        detections
    ):

        used_trackers = set()

        # Yeni detection'ları mevcut trackerlarla eşleştir

        for detection in detections:

            best_index = None
            best_iou = 0.0

            for index, item in enumerate(
                trackers
            ):

                current_iou = box_iou(
                    detection,
                    item["box"]
                )

                if current_iou > best_iou:
                    best_iou = current_iou
                    best_index = index

            if (
                best_index is not None
                and best_iou > 0.25
            ):

                # Detection daha güvenilir.
                # Tracker'ı yeniden merkezle.

                new_tracker = (
                    self.create_tracker()
                )

                new_tracker.init(
                    frame,
                    tuple(
                        map(
                            int,
                            detection
                        )
                    )
                )

                trackers[
                    best_index
                ] = {
                    "tracker": new_tracker,
                    "box": detection,
                    "missed": 0
                }

                used_trackers.add(
                    best_index
                )

            else:

                new_tracker = (
                    self.create_tracker()
                )

                new_tracker.init(
                    frame,
                    tuple(
                        map(
                            int,
                            detection
                        )
                    )
                )

                trackers.append(
                    {
                        "tracker":
                            new_tracker,
                        "box":
                            detection,
                        "missed":
                            0
                    }
                )

        # Aşırı çoğalmayı engelle

        if len(trackers) > 20:
            trackers = trackers[
                -20:
            ]

        return trackers

    # ========================================================
    # İŞLEM BAŞLAT
    # ========================================================

    def start_processing(self):

        if self.processing:
            return

        self.processing = True
        self.cancel_requested = False

        blur_strength = int(
            self.blur_slider.get()
        )

        if blur_strength % 2 == 0:
            blur_strength += 1

        detection_interval = int(
            self.detect_slider.get()
        )

        faces_enabled = bool(
            self.face_switch.get()
        )

        output_path = (
            self.current_output_path
        )

        self.set_processing_ui(
            True
        )

        thread = threading.Thread(
            target=self.process_video,
            args=(
                output_path,
                blur_strength,
                detection_interval,
                faces_enabled
            ),
            daemon=True
        )

        thread.start()

    # ========================================================
    # VIDEO PROCESS
    # ========================================================

    def process_video(
        self,
        output_path,
        blur_strength,
        detection_interval,
        faces_enabled
    ):

        cap = None
        writer = None
        silent_temp = None

        try:

            cap = cv2.VideoCapture(
                self.video_path
            )

            if not cap.isOpened():
                raise RuntimeError(
                    "Video açılamadı."
                )

            fps = cap.get(
                cv2.CAP_PROP_FPS
            )

            if fps <= 0:
                fps = 25.0

            width = int(
                cap.get(
                    cv2.CAP_PROP_FRAME_WIDTH
                )
            )

            height = int(
                cap.get(
                    cv2.CAP_PROP_FRAME_HEIGHT
                )
            )

            total_frames = int(
                cap.get(
                    cv2.CAP_PROP_FRAME_COUNT
                )
            )

            ok, first_frame = cap.read()

            if not ok:
                raise RuntimeError(
                    "Videonun ilk karesi okunamadı."
                )

            # ------------------------------------------------
            # MANUEL TRACKERLAR
            # ------------------------------------------------

            manual_trackers = []

            for roi in self.manual_rois:

                tracker = (
                    self.create_tracker()
                )

                tracker.init(
                    first_frame,
                    tuple(
                        map(
                            int,
                            roi
                        )
                    )
                )

                manual_trackers.append(
                    {
                        "tracker":
                            tracker,
                        "box":
                            roi,
                        "missed":
                            0
                    }
                )

            # ------------------------------------------------
            # YÜZ TRACKERLARI
            # ------------------------------------------------

            face_trackers = []

            if faces_enabled:

                first_faces = (
                    self.detect_faces(
                        first_frame
                    )
                )

                for face in first_faces:

                    tracker = (
                        self.create_tracker()
                    )

                    tracker.init(
                        first_frame,
                        tuple(
                            map(
                                int,
                                face
                            )
                        )
                    )

                    face_trackers.append(
                        {
                            "tracker":
                                tracker,
                            "box":
                                face,
                            "missed":
                                0
                        }
                    )

            # ------------------------------------------------
            # TEMP VIDEO
            # ------------------------------------------------

            temp_dir = (
                tempfile.gettempdir()
            )

            silent_temp = os.path.join(
                temp_dir,
                (
                    "blurguard_"
                    + str(int(time.time()))
                    + ".mp4"
                )
            )

            fourcc = (
                cv2.VideoWriter_fourcc(
                    *"mp4v"
                )
            )

            writer = cv2.VideoWriter(
                silent_temp,
                fourcc,
                fps,
                (
                    width,
                    height
                )
            )

            if not writer.isOpened():
                raise RuntimeError(
                    "Geçici video dosyası oluşturulamadı."
                )

            frame_number = 0
            current_frame = first_frame

            while True:

                if self.cancel_requested:
                    raise RuntimeError(
                        "İşlem kullanıcı tarafından iptal edildi."
                    )

                output_frame = (
                    current_frame.copy()
                )

                # --------------------------------------------
                # MANUEL TRACKERLAR
                # --------------------------------------------

                refreshed_manual = []

                for item in manual_trackers:

                    success, box = (
                        item[
                            "tracker"
                        ].update(
                            current_frame
                        )
                    )

                    if success:

                        x, y, w, h = box

                        item["box"] = (
                            int(x),
                            int(y),
                            int(w),
                            int(h)
                        )

                        item[
                            "missed"
                        ] = 0

                    else:

                        item[
                            "missed"
                        ] += 1

                    # Tracker birkaç kare kaybolsa da
                    # son bilinen alanı sansürlemeye devam et

                    if (
                        item["missed"]
                        <= 12
                    ):

                        self.blur_box(
                            output_frame,
                            item["box"],
                            blur_strength,
                            padding=0.05
                        )

                        refreshed_manual.append(
                            item
                        )

                manual_trackers = (
                    refreshed_manual
                )

                # --------------------------------------------
                # YÜZ TRACKERLARI
                # --------------------------------------------

                if faces_enabled:

                    face_trackers = (
                        self.update_face_trackers(
                            current_frame,
                            face_trackers
                        )
                    )

                    # Belirli aralıklarla gerçek yüz detection
                    # çalıştır ve tracker drift'ini düzelt

                    if (
                        frame_number
                        % detection_interval
                        == 0
                    ):

                        detections = (
                            self.detect_faces(
                                current_frame
                            )
                        )

                        face_trackers = (
                            self.sync_face_detections(
                                current_frame,
                                face_trackers,
                                detections
                            )
                        )

                    for item in face_trackers:

                        self.blur_box(
                            output_frame,
                            item["box"],
                            blur_strength,
                            padding=0.22
                        )

                # --------------------------------------------
                # WRITE
                # --------------------------------------------

                writer.write(
                    output_frame
                )

                frame_number += 1

                # Progress

                if total_frames > 0:

                    progress = min(
                        frame_number
                        / total_frames,
                        1.0
                    )

                    self.after(
                        0,
                        self.update_progress,
                        progress,
                        frame_number,
                        total_frames
                    )

                ok, current_frame = (
                    cap.read()
                )

                if not ok:
                    break

            cap.release()
            cap = None

            writer.release()
            writer = None

            self.after(
                0,
                self.status_label.configure,
                {
                    "text":
                        "Ses aktarılıyor..."
                }
            )

            # ------------------------------------------------
            # SES AKTAR
            # ------------------------------------------------

            audio_added = (
                self.merge_original_audio(
                    silent_temp,
                    self.video_path,
                    output_path
                )
            )

            # Temp temizle

            if os.path.exists(
                silent_temp
            ):
                os.remove(
                    silent_temp
                )

            silent_temp = None

            self.after(
                0,
                self.process_finished,
                output_path,
                audio_added
            )

        except Exception as error:

            if cap is not None:
                cap.release()

            if writer is not None:
                writer.release()

            if (
                silent_temp
                and os.path.exists(
                    silent_temp
                )
            ):

                try:
                    os.remove(
                        silent_temp
                    )
                except Exception:
                    pass

            self.after(
                0,
                self.process_failed,
                str(error)
            )

    # ========================================================
    # SES
    # ========================================================

    def merge_original_audio(
        self,
        silent_video,
        original_video,
        output_path
    ):

        ffmpeg = shutil.which(
            "ffmpeg"
        )

        if not ffmpeg:

            shutil.copy2(
                silent_video,
                output_path
            )

            return False

        command = [
            ffmpeg,
            "-y",

            "-i",
            silent_video,

            "-i",
            original_video,

            "-map",
            "0:v:0",

            "-map",
            "1:a?",

            "-c:v",
            "copy",

            "-c:a",
            "aac",

            "-b:a",
            "192k",

            "-shortest",

            output_path
        ]

        result = subprocess.run(
            command,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=(
                subprocess.CREATE_NO_WINDOW
                if os.name == "nt"
                else 0
            )
        )

        if (
            result.returncode == 0
            and os.path.exists(
                output_path
            )
        ):
            return True

        shutil.copy2(
            silent_video,
            output_path
        )

        return False

    # ========================================================
    # PROGRESS
    # ========================================================

    def update_progress(
        self,
        progress,
        frame,
        total
    ):

        self.progressbar.set(
            progress
        )

        percent = int(
            progress * 100
        )

        self.percent_label.configure(
            text=f"{percent}%"
        )

        self.status_label.configure(
            text="Video işleniyor"
        )

        self.detail_label.configure(
            text=(
                f"Kare {frame:,} / {total:,}  •  "
                "Hareketli alanlar takip ediliyor"
            )
        )

    # ========================================================
    # UI DURUM
    # ========================================================

    def set_processing_ui(
        self,
        processing
    ):

        if processing:

            self.select_video_button.configure(
                state="disabled"
            )

            self.select_roi_button.configure(
                state="disabled"
            )

            self.start_button.configure(
                state="disabled",
                text="◉   İşleniyor..."
            )

            self.face_switch.configure(
                state="disabled"
            )

            self.blur_slider.configure(
                state="disabled"
            )

            self.detect_slider.configure(
                state="disabled"
            )

            self.status_label.configure(
                text="İşlem başlatılıyor..."
            )

            self.detail_label.configure(
                text=(
                    "Yüz ve manuel bölgeler "
                    "hareket boyunca takip edilecek."
                )
            )

        else:

            self.select_video_button.configure(
                state="normal"
            )

            self.select_roi_button.configure(
                state=(
                    "normal"
                    if self.video_path
                    else "disabled"
                )
            )

            self.start_button.configure(
                state=(
                    "normal"
                    if self.video_path
                    else "disabled"
                ),
                text="▶   İşlemeyi Başlat"
            )

            self.face_switch.configure(
                state="normal"
            )

            self.blur_slider.configure(
                state="normal"
            )

            self.detect_slider.configure(
                state="normal"
            )

    # ========================================================
    # BİTTİ
    # ========================================================

    def process_finished(
        self,
        output_path,
        audio_added
    ):

        self.processing = False

        self.progressbar.set(
            1
        )

        self.percent_label.configure(
            text="100%"
        )

        self.status_label.configure(
            text="İşlem tamamlandı"
        )

        if audio_added:

            detail = (
                "Sansürlü video oluşturuldu ve "
                "orijinal ses aktarıldı."
            )

        else:

            detail = (
                "Video oluşturuldu. FFmpeg bulunamadığı "
                "için çıktı sessiz olabilir."
            )

        self.detail_label.configure(
            text=detail
        )

        self.set_processing_ui(
            False
        )

        messagebox.showinfo(
            "BlurGuard Pro",
            (
                "Video başarıyla oluşturuldu.\n\n"
                f"{output_path}"
            )
        )

    # ========================================================
    # HATA
    # ========================================================

    def process_failed(
        self,
        error
    ):

        self.processing = False

        self.set_processing_ui(
            False
        )

        self.status_label.configure(
            text="İşlem durduruldu"
        )

        self.detail_label.configure(
            text=error
        )

        if "kullanıcı tarafından" in error:
            return

        messagebox.showerror(
            "BlurGuard Pro - Hata",
            error
        )

    # ========================================================
    # KAPAT
    # ========================================================

    def on_close(self):

        if self.processing:

            result = messagebox.askyesno(
                "İşlem devam ediyor",
                (
                    "Video işlenmeye devam ediyor.\n\n"
                    "Program kapatılırsa işlem iptal edilir.\n\n"
                    "Kapatmak istiyor musun?"
                )
            )

            if not result:
                return

            self.cancel_requested = True

        self.destroy()


# ============================================================
# PROGRAMI BAŞLAT
# ============================================================

if __name__ == "__main__":

    app = BlurGuardPro()
    app.mainloop()