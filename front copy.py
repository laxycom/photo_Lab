import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter
import customtkinter as ctk

def safe_open(path):
    if not Path(path).exists():
        messagebox.showerror("Ошибка", f"Файла нет: {path}")
        return None
    try:
        return Image.open(path)
    except Exception as e:
        messagebox.showerror("Ошибка", f"Не могу открыть файл: {e}")
        return None

def safe_save(img, path):
    try:
        if path.lower().endswith((".jpg", ".jpeg")) and img.mode != "RGB":
            img = img.convert("RGB")
        img.save(path)
        return True
    except Exception as e:
        messagebox.showerror("Ошибка", f"Не могу сохранить: {e}")
        return False

def resize(img, width):
    if width <= 0:
        messagebox.showwarning("Ошибка", "Ширина должна быть больше нуля")
        return img
    ratio = width / float(img.size[0])
    new_h = int(float(img.size[1]) * ratio)
    return img.resize((width, new_h))

def rotate_image(img, degrees):
    return img.rotate(degrees, expand=True)

def grayscale(img):
    return img.convert("L")

def blur(img):
    return img.filter(ImageFilter.BLUR)

def sharpen(img):
    return img.filter(ImageFilter.SHARPEN)

def brightness(img, delta):
    img = img.convert("RGB")
    width, height = img.size
    pix = img.load()
    new_img = Image.new("RGB", (width, height))
    draw = ImageDraw.Draw(new_img)
    for y in range(height):
        for x in range(width):
            r, g, b = pix[x, y][:3]
            draw.point(
                (x, y),
                (
                    max(0, min(255, r + delta)),
                    max(0, min(255, g + delta)),
                    max(0, min(255, b + delta)),
                ),
            )
    return new_img

def color_effect(img, effect):
    img = img.convert("RGB")
    width, height = img.size
    pix = img.load()
    new_img = Image.new("RGB", (width, height))
    draw = ImageDraw.Draw(new_img)
    for y in range(height):
        for x in range(width):
            r, g, b = pix[x, y][:3]
            if effect == "swap":
                new_pixel = (g, b, r)
            elif effect == "negative":
                new_pixel = (255 - r, 255 - g, 255 - b)
            elif effect == "red_only":
                new_pixel = (r, 0, 0)
            elif effect == "sepia":
                sr = (r + g + b) // 3
                new_pixel = (min(255, sr + 40), sr, max(0, sr - 20))
            else:
                new_pixel = (r, g, b)
            draw.point((x, y), new_pixel)
    return new_img

class PhotoLabApp:
    def __init__(self, root):
        self.root = root
        self.root.title("PhotoLab GUI")
        self.root.geometry("1100x800")
        self.img = None
        self.filepath = ""
        self.history = []
        self.redo_stack = []
        self.preview = None
        self._build_ui()

    def _build_ui(self):
        self.root.configure(fg_color="#1e1e2e")

        left = ctk.CTkFrame(self.root, width=220, corner_radius=12, fg_color="#2a2a3e")
        left.pack(side="left", fill="y", padx=8, pady=8)
        left.pack_propagate(False)

        ctk.CTkButton(left, text="Открыть", width=200, height=36,
                      command=self.open_file, corner_radius=8).pack(pady=(10, 3))

        ctk.CTkLabel(left, text="— Инфо —", font=ctk.CTkFont(size=13, weight="bold"),
                     text_color="#8ab4f8").pack(pady=(15, 5))
        self.info_label = ctk.CTkLabel(left, text="нет файла", justify="left",
                                       text_color="#6c7a89", wraplength=200)
        self.info_label.pack(padx=10)

        ctk.CTkLabel(left, text="— Операции —", font=ctk.CTkFont(size=13, weight="bold"),
                     text_color="#8ab4f8").pack(pady=(15, 5))

        ops = [
            ("Resize", self.act_resize),
            ("Rotate", self.act_rotate),
            ("Grayscale", self.act_grayscale),
            ("Blur", self.act_blur),
            ("Sharpen", self.act_sharpen),
            ("Brightness", self.act_brightness),
            ("Color effect", self.act_color_effect),
        ]
        for txt, cmd in ops:
            ctk.CTkButton(left, text=txt, width=200, height=32,
                          command=cmd, corner_radius=6,
                          fg_color="#3a3a52", hover_color="#4a4a6a").pack(pady=3)

        ctk.CTkLabel(left, text="— История —", font=ctk.CTkFont(size=13, weight="bold"),
                     text_color="#8ab4f8").pack(pady=(15, 5))

        ctk.CTkButton(left, text="Undo", width=200, height=32,
                      command=self.act_undo, corner_radius=6,
                      fg_color="#3a3a52", hover_color="#4a4a6a").pack(pady=3)
        ctk.CTkButton(left, text="Redo", width=200, height=32,
                      command=self.act_redo, corner_radius=6,
                      fg_color="#3a3a52", hover_color="#4a4a6a").pack(pady=3)

        ctk.CTkButton(left, text="Сохранить как", width=200, height=36,
                      command=self.save_as, corner_radius=8,
                      fg_color="#5b8def", hover_color="#7ba8ff").pack(pady=(20, 5))
        ctk.CTkButton(left, text="Выход", width=200, height=36,
                      command=self.root.quit, corner_radius=8,
                      fg_color="#c0392b", hover_color="#e74c3c").pack(pady=5)

        right = ctk.CTkFrame(self.root, corner_radius=12, fg_color="#2a2a3e")
        right.pack(side="right", fill="both", expand=True, padx=8, pady=8)

        self.canvas = ctk.CTkLabel(right, text="Откройте изображение",
                                   font=ctk.CTkFont(size=16),
                                   text_color="#6c7a89",
                                   fg_color="#1e1e2e",
                                   corner_radius=8)
        self.canvas.pack(fill="both", expand=True, padx=10, pady=10)

    def _has_img(self):
        if self.img is None:
            messagebox.showwarning("Нет файла", "Сначала откройте изображение")
            return False
        return True

    def _push_history(self, new_img):
        self.history.append(self.img)
        self.redo_stack.clear()
        self.img = new_img
        self.refresh()
        self.update_info()

    def refresh(self):
        if self.img is None:
            return
        w, h = self.root.winfo_width() or 900, self.root.winfo_height() or 650
        view = self.img.copy()
        view.thumbnail((max(w - 260, 100), max(h - 60, 100)))
        self.preview = ctk.CTkImage(light_image=view, dark_image=view,
                                    size=view.size)
        self.canvas.configure(image=self.preview, text="")

    def update_info(self):
        if self.img:
            txt = (f"Размер: {self.img.size}\n"
                   f"Mode: {self.img.mode}\n"
                   f"Формат: {self.img.format}\n"
                   f"Файл: {Path(self.filepath).name if self.filepath else '—'}")
            self.info_label.configure(text=txt)

    def open_file(self):
        path = filedialog.askopenfilename(
            filetypes=[("Images", "*.jpg *.jpeg *.png *.bmp")]
        )
        if not path:
            return
        img = safe_open(path)
        if img is None:
            return
        self.img = img
        self.filepath = path
        self.history = [img]
        self.redo_stack = []
        self.refresh()
        self.update_info()

    def act_resize(self):
        if not self._has_img():
            return
        width = simpledialog.askinteger("Resize", "Новая ширина (px):", minvalue=1)
        if width is None:
            return
        self._push_history(resize(self.img, width))

    def act_rotate(self):
        if not self._has_img():
            return
        deg = simpledialog.askinteger("Rotate", "Угол (градусы):")
        if deg is None:
            return
        self._push_history(rotate_image(self.img, deg))

    def act_grayscale(self):
        if self._has_img():
            self._push_history(grayscale(self.img))

    def act_blur(self):
        if self._has_img():
            self._push_history(blur(self.img))

    def act_sharpen(self):
        if self._has_img():
            self._push_history(sharpen(self.img))

    def act_brightness(self):
        if not self._has_img():
            return
        delta = simpledialog.askinteger(
            "Brightness", "Сдвиг (-255..255):", minvalue=-255, maxvalue=255
        )
        if delta is None:
            return
        self._push_history(brightness(self.img, delta))

    def act_color_effect(self):
        if not self._has_img():
            return
        effect = simpledialog.askstring(
            "Color effect",
            "Эффект (swap / negative / red_only / sepia):"
        )
        if not effect:
            return
        effect = effect.strip().lower()
        if effect not in ("swap", "negative", "red_only", "sepia"):
            messagebox.showwarning("Ошибка", "Неизвестный эффект")
            return
        self._push_history(color_effect(self.img, effect))

    def act_undo(self):
        if self.img is None:
            return
        if len(self.history) > 1:
            self.redo_stack.append(self.history.pop())
            self.img = self.history[-1]
            self.refresh()
            self.update_info()
        else:
            messagebox.showinfo("Undo", "Отменять нечего")

    def act_redo(self):
        if self.redo_stack:
            self.history.append(self.redo_stack.pop())
            self.img = self.history[-1]
            self.refresh()
            self.update_info()
        else:
            messagebox.showinfo("Redo", "Нечего повторять")

    def save_as(self):
        if self.img is None:
            messagebox.showwarning("Ошибка", "Нечего сохранять!")
            return
        folder = str(Path(self.filepath).parent) if self.filepath else ""
        filename = Path(self.filepath).name if self.filepath else "image.png"
        newname = "new_" + filename
        path = filedialog.asksaveasfilename(
            defaultextension=".png",
            initialdir=folder,
            initialfile=newname,
            filetypes=[("PNG", "*.png"), ("JPEG", "*.jpg"), ("BMP", "*.bmp")],
        )
        if path and safe_save(self.img, path):
            self.filepath = path
            self.update_info()
            messagebox.showinfo("Успех", f"Файл сохранён: {path}")

if __name__ == "__main__":
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")
    root = ctk.CTk()
    app = PhotoLabApp(root)
    root.mainloop()