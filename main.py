from PIL import Image, ImageDraw, ImageFilter, ImageEnhance
from pathlib import Path


def ask_int(prompt):
    while True:
        try:
            return int(input(prompt))
        except ValueError:
            print("Это не число, попробуй ещё раз")


def safe_open(path):
    if not Path(path).exists():
        print("Файла нет:", path)
        return None
    try:
        return Image.open(path)
    except Exception as e:
        print("Не могу открыть файл:", e)
        return None


def safe_save(img, path):
    try:
        img.save(path)
        print("saved successfully, ", path)
        return True
    except Exception as e:
        print("Не могу сохранить:", e)
        return False


def ask_save(img):
    answer = input("Сохранить сейчас? (y/n): ")
    if answer.lower() == "y":
        out = input("Куда сохранить: ")
        safe_save(img, out)


def parameters(img):
    print("Размер (ширина, высота): ", img.size)
    print("Цветовая модель: ", img.mode)
    print("Формат файла: ", img.format)


def resize(img, width):
    if width <= 0:
        print("Ширина должна быть больше нуля")
        return img
    widthless = width / float(img.size[0])
    newimgsize = int(float(img.size[1]) * widthless)
    return img.resize((width, newimgsize))


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
            r = pix[x, y][0]
            g = pix[x, y][1]
            b = pix[x, y][2]
            nr = max(0, min(255, r + delta))
            ng = max(0, min(255, g + delta))
            nb = max(0, min(255, b + delta))
            draw.point((x, y), (nr, ng, nb))
    return new_img


def color_effect(img, effect):
    img = img.convert("RGB")
    width, height = img.size
    pix = img.load()
    new_img = Image.new("RGB", (width, height))
    draw = ImageDraw.Draw(new_img)
    for y in range(height):
        for x in range(width):
            r = pix[x, y][0]
            g = pix[x, y][1]
            b = pix[x, y][2]
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


print("1 — обработать одну картинку")
print("2 — пакетная обработка папки (batch)")
mode = input("Выбери режим: ")

if mode == "2":
    folder_path = input("Путь к папке: ")
    folder = Path(folder_path)
    if not folder.exists() or not folder.is_dir():
        print("Папка не найдена")
        raise SystemExit
        
    out_folder = folder / "out"
    out_folder.mkdir(exist_ok=True)

    print("\nКакой фильтр применить ко всем картинкам?")
    print("1 — grayscale (ч/б)")
    print("2 — blur (размытие)")
    print("3 — sharpen (резкость)")
    print("4 — resize (изменить ширину)")
    print("5 — brightness (яркость)")
    print("6 — color effect (цветовой эффект)")
    batch_choice = input("Выбери действие: ")

    parameter = None

    if batch_choice == "4":
        parameter = ask_int("Новая ширина: ")
    elif batch_choice == "5":
        parameter = ask_int("Сдвиг яркости (-255 до 255): ")
    elif batch_choice == "6":
        parameter = input("Эффект (swap/negative/red_only/sepia): ")

    files = list[folder.glop("*.*")]
    files_count = len(files)
    print("files found: ", {files_count})
    for i, file in enumerate(files, 1):
        if file.is_dir() or file.suffix.lower() not in (".jpg", ".jpeg", ".png", ".bmp"):
            continue
    img = safe_open(file)
    if img:
        if batch_choice == "1":
            img = grayscale(img)
        elif batch_choice == "2":
            img = blur(img)
        elif batch_choice == "3":
            img = sharpen(img)
        elif batch_choice == "4":
            img = resize(img, parameter)
        elif batch_choice == "5":
            img = brightness(img, parameter)
        elif batch_choice == "6":
            img = color_effect(img, parameter)

elif mode == "1":
    path = input("Путь к картинке: ")
    img = safe_open(path)
    if img is None:
        raise SystemExit

    history = [img]
    redo_stack = []

    while True:
        print("\n1 — info | 2 — resize | 3 — rotate | 4 — save as")
        print("5 — color effect | 6 — grayscale | 7 — blur | 8 — sharpen")
        print("9 — brightness | 10 — undo | 11 — redo | 0 — exit")
        choice = input("ur choice: ")

        if choice == "1":
            parameters(img)
            
        elif choice == "2":
            width = ask_int("new width: ")
            img = resize(img, width)
            history.append(img)
            redo_stack.clear()
            ask_save(img)
            
        elif choice == "3":
            degrees = ask_int("degrees to rotate: ")
            img = rotate_image(img, degrees)
            history.append(img)
            redo_stack.clear()
            ask_save(img)
            
        elif choice == "4":
            out = input("new path: ")
            safe_save(img, out)
            
        elif choice == "5":
            effect = input("Эффект (swap/negative/red_only/sepia): ")
            img = color_effect(img, effect)
            history.append(img)
            redo_stack.clear()
            ask_save(img)
            
        elif choice == "6":
            img = grayscale(img)
            history.append(img)
            redo_stack.clear()
            ask_save(img)
            
        elif choice == "7":
            img = blur(img)
            history.append(img)
            redo_stack.clear()
            ask_save(img)
            
        elif choice == "8":
            img = sharpen(img)
            history.append(img)
            redo_stack.clear()
            ask_save(img)
            
        elif choice == "9":
            delta = ask_int("delta from -255 to 255: ")
            img = brightness(img, delta)
            history.append(img)
            redo_stack.clear()
            ask_save(img)
            
        elif choice == "10":
            if len(history) > 1:
                redo_stack.append(history.pop())
                img = history[-1]
                print("Отменено. Размер:", img.size)
            else:
                print("Отменять нечего")
                
        elif choice == "11":
            if len(redo_stack) > 0:
                history.append(redo_stack.pop())
                img = history[-1]
                print("Повторено. Размер:", img.size)
            else:
                print("Нечего повторять")
                
        elif choice == "0":
            break
        else:
            print("no function on this number")