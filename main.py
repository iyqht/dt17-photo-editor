import tkinter as tk
from tkinter import filedialog

from PIL import Image, ImageEnhance, ImageTk  # Thêm ImageEnhance để chỉnh độ sáng

from controls import BrightnessScale, RotateScale, ZoomScale
from crop_tool import CropTool

original_image = None
tk_image = None
tk_preview_image = None
img_id = None

zoom_factor = 1.0
rotate_angle = 0
brightness_val = 1.0

drag_data = {
    "x": 0,
    "y": 0,
}

undo_stack = []
redo_stack = []


# --- Các hàm Callback nhận dữ liệu từ các thanh trượt (controls.py) ---
def on_zoom_change(val):
    global zoom_factor
    zoom_factor = val / 100  # Chuyển từ % (100) sang hệ số (1.0)
    show_image()


def on_rotate_change(val):
    global rotate_angle
    rotate_angle = val
    show_image()


def on_brightness_change(val):
    global brightness_val
    brightness_val = val
    show_image()


def show_image():
    global tk_image, img_id
    if original_image:
        # Bước 1: Xử lý độ sáng
        enhancer = ImageEnhance.Brightness(original_image)
        temp_img = enhancer.enhance(brightness_val)

        # Bước 2: Xử lý xoay
        # Chuyển đổi ảnh sang hệ RGBA để phần nền bị lộ ra khi xoay sẽ trong suốt thay vì màu đen
        temp_img = temp_img.convert("RGBA")
        temp_img = temp_img.rotate(rotate_angle, expand=True, resample=Image.BILINEAR)

        # Bước 3: Xử lý Zoom (Thay đổi kích thước)
        new_w = int(temp_img.width * zoom_factor)
        new_h = int(temp_img.height * zoom_factor)
        resized_img = temp_img.resize((new_w, new_h), Image.LANCZOS)

        # Bước 4: Đưa ảnh lên Tkinter Canvas
        tk_image = ImageTk.PhotoImage(resized_img)
        if img_id is None:
            # Lần đầu tiên vẽ: Đặt ảnh vào chính giữa Canvas
            img_id = canvas.create_image(
                canvas.winfo_width() // 2,
                canvas.winfo_height() // 2,
                image=tk_image,
                anchor=tk.CENTER,
            )
        else:
            # Các lần sau: Chỉ cập nhật nội dung ảnh để tiết kiệm bộ nhớ
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
        undo_stack.clear()
        redo_stack.clear()
        save_state()
        zoom_factor = 1.0

        preview_copy = original_image.copy()
        preview_copy.thumbnail((300, 300))
        tk_preview_image = ImageTk.PhotoImage(preview_copy)
        preview_label.config(image=tk_preview_image, text="", width=0, height=0)

        show_image()


def mouse_wheel(event):
    global zoom_factor
    if original_image:
        # Tăng/giảm 5% mỗi lần lăn chuột
        zoom_factor += 0.05 if event.delta > 0 else -0.05
        # Ràng buộc giá trị zoom không vượt quá giới hạn của thanh trượt (ZoomScale)
        zoom_factor = max(
            zoom_ctrl.scale["from"] / 100, min(zoom_factor, zoom_ctrl.scale["to"] / 100)
        )

        zoom_ctrl.set_value(zoom_factor * 100)
        show_image()


def drag_start(event):
    drag_data["x"], drag_data["y"] = event.x, event.y


def drag_motion(event):
    if img_id:
        dx, dy = event.x - drag_data["x"], event.y - drag_data["y"]
        canvas.move(img_id, dx, dy)
        drag_data["x"], drag_data["y"] = event.x, event.y


def save_state():
    global undo_stack
    if original_image:
        old_img = original_image.copy()
        undo_stack.append(old_img)
        if len(undo_stack) > 10:
            undo_stack.pop(0)


def get_crop_data():
    return original_image, zoom_factor, img_id


def apply_crop(new_img):
    global original_image
    save_state()
    redo_stack.clear()
    original_image = new_img
    show_image()


def undo():
    global original_image, undo_stack, redo_stack
    if undo_stack and original_image:
        redo_stack.append(original_image.copy())
        original_image = undo_stack.pop()
        show_image()


def redo():
    global original_image, undo_stack, redo_stack
    if redo_stack and original_image:
        undo_stack.append(original_image.copy())
        original_image = redo_stack.pop()
        show_image()


def flip_image(mode):
    global original_image
    if original_image:
        save_state()
        if mode == "horizontal":
            original_image = original_image.transpose(Image.FLIP_LEFT_RIGHT)
        elif mode == "vertical":
            original_image = original_image.transpose(Image.FLIP_TOP_BOTTOM)
        show_image()


window = tk.Tk()
window.title("Ứng dụng Chỉnh sửa Ảnh")
window.geometry("1500x900+50+50")

# --- KHUNG BÊN TRÁI (SIDEBAR) ---
left_frame = tk.Frame(window, width=300)
left_frame.pack(side="left", fill="y")
left_frame.pack_propagate(
    False
)  # Ngăn không cho các widget con làm thay đổi độ rộng của left_frame

# Tiêu đề và ảnh xem trước (Thumbnail)
tk.Label(left_frame, text="ẢNH GỐC").pack(pady=(20, 5))
preview_label = tk.Label(
    left_frame,
    text="Chưa có ảnh",
    bg="gray",
    fg="white",
    width=25,
    height=12,
    relief="groove",
)
preview_label.pack(pady=5)

# --- KHUNG BÊN PHẢI (CANVAS CHÍNH) ---
right_frame = tk.Frame(window)
right_frame.pack(side="left", fill="both", expand=True)

canvas = tk.Canvas(right_frame, highlightthickness=0)
canvas.pack(fill="both", expand=True)

# --- CÁC NÚT CÔNG CỤ (DƯỚI CÙNG BÊN TRÁI) ---
tools_container = tk.Frame(left_frame)
tools_container.pack(side="bottom", fill="x", pady=20)

# Nút mở file
button = tk.Button(tools_container, text="📁 Mở ảnh", width=20, command=add_image)
button.pack(pady=20)

# Khởi tạo Object thực hiện chức năng cắt ảnh
crop_engine = CropTool(canvas, get_crop_data, apply_crop)

# Nút cắt ảnh
btn_crop = tk.Button(
    tools_container, text="✂️ Cắt ảnh", width=20, command=crop_engine.activate
)
btn_crop.pack(pady=10)

# Nút lật ngang / dọc
flip_frame = tk.Frame(tools_container)
flip_frame.pack(pady=10)
btn_flip_h = tk.Button(
    flip_frame, text="Lật Ngang", width=10, command=lambda: flip_image("horizontal")
)
btn_flip_h.pack(side=tk.LEFT, padx=5, expand=True)

btn_flip_v = tk.Button(
    flip_frame,
    text="Lật Dọc",
    width=10,
    command=lambda: flip_image("vertical"),
)
btn_flip_v.pack(side="right", padx=5, expand=True)

# Khung chứa bộ nút Undo/Redo
history_frame = tk.Frame(tools_container)
history_frame.pack(pady=10)

btn_undo = tk.Button(history_frame, text="Undo", width=10, command=undo)
btn_undo.pack(side=tk.LEFT, padx=5, expand=True)

btn_redo = tk.Button(history_frame, text="Redo", width=10, command=redo)
btn_redo.pack(side=tk.LEFT, padx=5, expand=True)

# --- KHỞI TẠO CÁC THANH ĐIỀU KHIỂN (SLIDERS) ---
zoom_ctrl = ZoomScale(canvas, on_zoom_change)
rotate_ctrl = RotateScale(tools_container, on_rotate_change)
bright_ctrl = BrightnessScale(tools_container, on_brightness_change)

# Đặt thanh Zoom đè lên góc dưới bên phải của khung vẽ (Canvas)
zoom_ctrl.place(relx=0.99, rely=0.99, anchor=tk.SE)
rotate_ctrl.pack(pady=5)
bright_ctrl.pack(pady=5)

# --- GẮN CÁC SỰ KIỆN CHUỘT MẶC ĐỊNH ---
canvas.bind("<Button-1>", drag_start)
canvas.bind("<B1-Motion>", drag_motion)
canvas.bind("<MouseWheel>", mouse_wheel)

# Bắt đầu vòng lặp hiển thị giao diện
window.mainloop()
