import time
import tkinter as tk
from tkinter import filedialog

from PIL import Image, ImageEnhance, ImageTk  # Thêm ImageEnhance để chỉnh độ sáng

from controls import BrightnessScale, RotateScale, ZoomScale  # Import các Class riêng
from crop_tool import CropTool

# --- Các biến toàn cục ---
original_image = None
tk_image = None
tk_preview_image = None
img_id = None
zoom_factor = 1.0
rotate_angle = 0
brightness_val = 1.0
zoom_timer = None
last_zoom_time = 0
drag_data = {"x": 0, "y": 0}
undo = []
redo = []

# --- Các hàm xử lý logic ảnh ---


def update_ui_change():
    """Hàm chung để kích hoạt việc vẽ lại ảnh khi có bất kỳ thay đổi nào (zoom/rotate/bright)"""
    global zoom_timer
    if zoom_timer:
        window.after_cancel(zoom_timer)

    show_image(high_quality=False)
    zoom_timer = window.after(150, lambda: show_image(high_quality=True))


def on_zoom_change(val):
    global zoom_factor
    zoom_factor = val / 100
    update_ui_change()


def on_rotate_change(val):
    global rotate_angle
    rotate_angle = val
    update_ui_change()


def on_brightness_change(val):
    global brightness_val
    brightness_val = val
    update_ui_change()


def show_image(high_quality=True):
    global tk_image, img_id
    if original_image:
        # 1. Xử lý độ sáng (Brightness)
        enhancer = ImageEnhance.Brightness(original_image)
        temp_img = enhancer.enhance(brightness_val)

        # 2. Xử lý xoay (Rotate)
        # Chuyển đổi ảnh sang RGBA để hỗ trợ độ trong suốt
        temp_img = temp_img.convert("RGBA")

        # Xoay ảnh với tham số expand=True
        # expand=True giúp khung hình nở ra để chứa toàn bộ ảnh đã xoay
        temp_img = temp_img.rotate(rotate_angle, expand=True, resample=Image.BILINEAR)

        # 3. Xử lý Zoom
        new_w = int(temp_img.width * zoom_factor)
        new_h = int(temp_img.height * zoom_factor)
        method = Image.LANCZOS if high_quality else Image.NEAREST
        resized_img = temp_img.resize((new_w, new_h), method)

        tk_image = ImageTk.PhotoImage(resized_img)

        if img_id is None:
            img_id = canvas.create_image(
                canvas.winfo_width() // 2,
                canvas.winfo_height() // 2,
                image=tk_image,
                anchor=tk.CENTER,
            )
        else:
            canvas.itemconfig(img_id, image=tk_image)


def add_image():
    global original_image, img_id, zoom_factor, tk_preview_image
    path = filedialog.askopenfilename(
        filetypes=[("Image files", "*.jpg *.jpeg *.png *.bmp *.gif")]
    )
    if path:
        original_image = Image.open(path)
        img_id = None
        canvas.delete("all")
        undo.clear()
        save_state()
        zoom_factor = 1.0

        preview_copy = original_image.copy()
        preview_copy.thumbnail((300, 300))
        tk_preview_image = ImageTk.PhotoImage(preview_copy)
        preview_label.config(image=tk_preview_image, text="", width=0, height=0)

        show_image()


# --- Các hàm sự kiện chuột ---


def mouse_wheel(event):
    global zoom_factor, last_zoom_time
    if original_image:
        curr = time.time()
        if curr - last_zoom_time < 0.02:
            return
        last_zoom_time = curr

        zoom_factor += 0.05 if event.delta > 0 else -0.05
        zoom_factor = max(
            zoom_ctrl.scale["from"] / 100, min(zoom_factor, zoom_ctrl.scale["to"] / 100)
        )

        # Cập nhật thanh scale trong class ZoomControl để đồng bộ
        zoom_ctrl.set_value(zoom_factor * 100)
        update_ui_change()


def drag_start(event):
    drag_data["x"], drag_data["y"] = event.x, event.y


def drag_motion(event):
    if img_id:
        dx, dy = event.x - drag_data["x"], event.y - drag_data["y"]
        canvas.move(img_id, dx, dy)
        drag_data["x"], drag_data["y"] = event.x, event.y


def save_state():
    global undo
    if original_image:
        old_img = original_image.copy()
        undo.append(old_img)
        if len(undo) > 11:
            undo.pop(0)


def get_crop_data():
    return original_image, zoom_factor, img_id


def apply_crop(new_img):
    global original_image
    save_state()
    redo.clear()
    original_image = new_img
    show_image()


def restore_binding():
    canvas.bind("<Button-1>", drag_start)
    canvas.bind("<B1-Motion>", drag_motion)
    canvas.unbind("<ButtonRelease-1>")


def start_crop_mode():
    if original_image:
        crop_engine.activate(on_exit_callback=restore_binding)


def undo_crop():
    global original_image, undo, redo
    if undo and original_image:
        redo.append(original_image.copy())
        original_image = undo.pop()
        show_image()


def redo_crop():
    global original_image, undo, redo
    if redo and original_image:
        undo.append(original_image.copy())
        original_image = redo.pop()
        show_image()


def flip_image(mode):
    global original_image
    if original_image:
        if mode == "horizontal":
            original_image = original_image.transpose(Image.FLIP_LEFT_RIGHT)
        elif mode == "vertical":
            original_image = original_image.transpose(Image.FLIP_TOP_BOTTOM)
        show_image()


# --- Thiết lập giao diện ---
window = tk.Tk()
window.title("Ứng dụng Chỉnh sửa Ảnh")
window.geometry("1500x900+50+50")

left_frame = tk.Frame(window, bg="#1e272e", width=300)
left_frame.pack(side="left", fill="y")
left_frame.pack_propagate(False)

tk.Label(
    left_frame, text="ẢNH GỐC", fg="#00d8d6", bg="#1e272e", font=("Arial", 10, "bold")
).pack(pady=(20, 5))
preview_label = tk.Label(
    left_frame,
    text="Chưa có ảnh",
    bg="#2d3436",
    fg="white",
    width=25,
    height=12,
    relief="groove",
)
preview_label.pack(pady=5)

btn_style = {
    "width": 20,
    "bg": "#485460",
    "fg": "white",
    "activebackground": "#05c46b",
    "relief": "flat",
    "font": ("Arial", 9, "bold"),
}

right_frame = tk.Frame(window, bg="#1e272e")
right_frame.pack(side="left", fill="both", expand=True)

canvas = tk.Canvas(right_frame, highlightthickness=0, bg="#2d3436")
canvas.pack(fill="both", expand=True)

tools_container = tk.Frame(left_frame, bg="#1e272e")
tools_container.pack(side="bottom", fill="x", pady=20)

button = tk.Button(tools_container, text="📁 Mở ảnh", command=add_image, **btn_style)
button.pack(pady=20)

flip_frame = tk.Frame(tools_container, bg="#1e272e")
flip_frame.pack(pady=10)

# Nút lật ngang
btn_flip_h = tk.Button(
    flip_frame, text="Lật Ngang", command=lambda: flip_image("horizontal"), **btn_style
)
btn_flip_h.config(width=8)
btn_flip_h.pack(side=tk.LEFT, padx=5, expand=True)

# Nút lật dọc
btn_flip_v = tk.Button(
    flip_frame, text="Lật Dọc", command=lambda: flip_image("vertical"), **btn_style
)
btn_flip_v.config(width=8)
btn_flip_v.pack(side="right", padx=5, expand=True)


btn_crop = tk.Button(
    tools_container, text="✂️ Cắt ảnh", command=start_crop_mode, **btn_style
)
btn_crop.pack(pady=10)

crop_engine = CropTool(canvas, get_crop_data, apply_crop)

history_frame = tk.Frame(tools_container, bg="#1e272e")
history_frame.pack(pady=10)

btn_undo = tk.Button(history_frame, text="Undo", command=undo_crop, **btn_style)
btn_undo.config(width=10)
btn_undo.pack(side=tk.LEFT, padx=5, expand=True)

btn_redo = tk.Button(history_frame, text="Redo", command=redo_crop, **btn_style)
btn_redo.config(width=10)
btn_redo.pack(side=tk.LEFT, padx=5, expand=True)

# Khởi tạo các Class điều khiển từ file controls.py
zoom_ctrl = ZoomScale(canvas, on_zoom_change)
rotate_ctrl = RotateScale(tools_container, on_rotate_change)
bright_ctrl = BrightnessScale(tools_container, on_brightness_change)

zoom_ctrl.place(relx=0.99, rely=0.99, anchor=tk.SE)
rotate_ctrl.pack(pady=5)
bright_ctrl.pack(pady=5)


canvas.bind("<Button-1>", drag_start)
canvas.bind("<B1-Motion>", drag_motion)
canvas.bind("<MouseWheel>", mouse_wheel)

window.mainloop()
