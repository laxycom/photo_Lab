import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter, ImageTk

def safe_open(path):
    if not Path(path).exists():
        messagebox.showerror("Ошибка", f"Файла нет:\n{path}")
        return None
    try:
        return Image.open(path)
    except Exception as e:
        messagebox.showerror("Ошибка", f"Не могу открыть файл:\n{e}")
        return None

def safe_save(img, path):
    try:
        # для JPEG нужен RGB
        if path.lower().endswith((".jpg", ".jpeg")) and img.mode != "RGB":
            img = img.convert("RGB")
        img.save(path)
        return True
    except Exception as e:
        messagebox.showerror("Ошибка", f"Не могу сохранить:\n{e}")
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
        self.root.geometry("1100x700")

        self.img = None            # текущее изображение (PIL)
        self.filepath = ""         # путь к текущему файлу
        self.history = []          # стек undo
        self.redo_stack = []       # стек redo
        self.preview = None        # ссылка на PhotoImage (чтобы не собрал GC)

        self._build_ui()

    # ---- UI ----
    def _build_ui(self):
        # Левая панель кнопок
        left = tk.Frame(self.root, width=200)
        left.pack(side="left", fill="y", padx=6, pady=6)

        tk.Button(left, text="Открыть", width=20, command=self.open_file).pack(pady=3)

        tk.Label(left, text="— Инфо —").pack(pady=(10, 0))
        self.info_label = tk.Label(left, text="нет файла", justify="left", fg="blue")
        self.info_label.pack()

        tk.Label(left, text="— Операции —").pack(pady=(10, 0))

        tk.Button(left, text="Resize", width=20, command=self.act_resize).pack(pady=2)
        tk.Button(left, text="Rotate", width=20, command=self.act_rotate).pack(pady=2)
        tk.Button(left, text="Grayscale", width=20, command=self.act_grayscale).pack(pady=2)
        tk.Button(left, text="Blur", width=20, command=self.act_blur).pack(pady=2)
        tk.Button(left, text="Sharpen", width=20, command=self.act_sharpen).pack(pady=2)
        tk.Button(left, text="Brightness", width=20, command=self.act_brightness).pack(pady=2)
        tk.Button(left, text="Color effect", width=20, command=self.act_color_effect).pack(pady=2)

        tk.Label(left, text="— История —").pack(pady=(10, 0))
        tk.Button(left, text="Undo", width=20, command=self.act_undo).pack(pady=2)
        tk.Button(left, text="Redo", width=20, command=self.act_redo).pack(pady=2)

        tk.Button(left, text="Сохранить как", width=20, command=self.save_as).pack(pady=(15, 2))
        tk.Button(left, text="Выход", width=20, command=self.root.quit).pack(pady=2)

        # Правая область — холст
        right = tk.Frame(self.root)
        right.pack(side="right", fill="both", expand=True, padx=6, pady=6)
        self.canvas = tk.Label(right, text="Откройте изображение", bg="gray20", fg="white")
        self.canvas.pack(fill="both", expand=True)

    # ---- helpers ----
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
        view.thumbnail((max(w - 220, 100), max(h - 40, 100)))
        self.preview = ImageTk.PhotoImage(view)
        self.canvas.configure(image=self.preview, text="")

    def update_info(self):
        if self.img:
            self.info_label.config(
                text=f"Размер: {self.img.size}\n"
                     f"Mode: {self.img.mode}\n"
                     f"Формат: {self.img.format}\n"
                     f"Файл: {Path(self.filepath).name if self.filepath else '—'}"
            )

    # ---- actions ----
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
        name = Path(self.filepath).name if self.filepath else "image.png"
        newname = "new_" + name

        path = filedialog.asksaveasfilename(
            defaultextension=".png",
            initialdir=folder,
            initialfile=newname,
            filetypes=[("PNG", "*.png"), ("JPEG", "*.jpg"), ("BMP", "*.bmp")],
        )
        if path and safe_save(self.img, path):
            self.filepath = path
            self.update_info()
            messagebox.showinfo("Успех", f"Файл сохранён:\n{path}")


if __name__ == "__main__":
    root = tk.Tk()
    app = PhotoLabApp(root)
    root.mainloop()