import time
import tkinter as tk
from tkinter import filedialog
from PIL import Image, ImageEnhance, ImageTk
from controls import BrightnessScale, RotateScale, ZoomScale
from crop_tool import CropTool

# --- Biến toàn cục (State Management) ---
original_image = None # Ảnh gốc (Pixel thực)
tk_image = None       # Ảnh đã xử lý để hiển thị trên Tkinter
img_id = None         # ID của ảnh trên Canvas
zoom_factor = 1.0     # Tỷ lệ phóng đại
rotate_angle = 0      # Góc xoay hiện tại
brightness_val = 1.0  # Mức độ sáng
zoom_timer = None     # Dùng để trì hoãn việc render ảnh chất lượng cao (Debounce)
undo, redo = [], []   # Danh sách ngăn xếp lưu lịch sử chỉnh sửa

# --- Hàm xử lý Logic Ảnh ---

def update_ui_change():
    """Tối ưu hóa: Vẽ ảnh nhanh (NEAREST) khi đang thao tác, vẽ đẹp (LANCZOS) khi dừng lại"""
    global zoom_timer
    if zoom_timer: window.after_cancel(zoom_timer)
    show_image(high_quality=False)
    zoom_timer = window.after(150, lambda: show_image(high_quality=True))

# Các hàm Callback nhận giá trị từ thanh trượt
def on_zoom_change(val): global zoom_factor; zoom_factor = val / 100; update_ui_change()
def on_rotate_change(val): global rotate_angle; rotate_angle = val; update_ui_change()
def on_brightness_change(val): global brightness_val; brightness_val = val; update_ui_change()

def show_image(high_quality=True):
    """Pipeline xử lý ảnh: Brightness -> RGBA (trong suốt) -> Rotate -> Zoom"""
    global tk_image, img_id
    if original_image:
        # 1. Chỉnh độ sáng
        enhancer = ImageEnhance.Brightness(original_image)
        temp_img = enhancer.enhance(brightness_val)

        # 2. Xử lý xoay với nền trong suốt
        temp_img = temp_img.convert("RGBA")
        temp_img = temp_img.rotate(rotate_angle, expand=True, resample=Image.BILINEAR)

        # 3. Thay đổi kích thước (Zoom)
        new_w, new_h = int(temp_img.width * zoom_factor), int(temp_img.height * zoom_factor)
        method = Image.LANCZOS if high_quality else Image.NEAREST
        resized_img = temp_img.resize((new_w, new_h), method)

        tk_image = ImageTk.PhotoImage(resized_img)
        if img_id is None:
            img_id = canvas.create_image(canvas.winfo_width()//2, canvas.winfo_height()//2, 
                                        image=tk_image, anchor=tk.CENTER)
        else:
            canvas.itemconfig(img_id, image=tk_image)

def add_image():
    """Mở file ảnh và thiết lập trạng thái ban đầu"""
    global original_image, img_id, zoom_factor, tk_preview_image
    path = filedialog.askopenfilename(filetypes=[("Image files", "*.jpg *.jpeg *.png *.bmp *.gif")])
    if path:
        original_image = Image.open(path)
        img_id = None
        canvas.delete("all")
        undo.clear(); redo.clear()
        save_state() # Lưu trạng thái gốc
        
        # Tạo ảnh xem trước (Thumbnail) nhỏ ở góc trái
        preview_copy = original_image.copy()
        preview_copy.thumbnail((300, 300))
        tk_preview_image = ImageTk.PhotoImage(preview_copy)
        preview_label.config(image=tk_preview_image, text="")
        show_image()

# --- Xử lý Lịch sử (Undo/Redo) ---

def save_state():
    """Chụp ảnh hiện tại cất vào ngăn xếp Undo"""
    global undo
    if original_image:
        undo.append(original_image.copy())
        if len(undo) > 11: undo.pop(0) # Giới hạn bộ nhớ 10 bước

def apply_crop(new_img):
    """Callback thực hiện sau khi Crop: Lưu undo, xóa redo, cập nhật ảnh mới"""
    global original_image
    save_state()
    redo.clear()
    original_image = new_img
    show_image()

def undo_crop():
    """Hoàn tác: Bốc từ ngăn xếp Undo sang Redo"""
    global original_image, undo, redo
    if len(undo) > 1: # Giữ lại ít nhất 1 cái là trạng thái gốc
        redo.append(original_image.copy())
        original_image = undo.pop()
        show_image()

def redo_crop():
    """Làm lại: Bốc từ ngăn xếp Redo về lại Undo"""
    global original_image, undo, redo
    if redo:
        undo.append(original_image.copy())
        original_image = redo.pop()
        show_image()

def flip_image(mode):
    """Lật ảnh: Dùng transpose của Pillow"""
    global original_image
    if original_image:
        save_state() # Nên lưu state trước khi Flip
        if mode == "horizontal": original_image = original_image.transpose(Image.FLIP_LEFT_RIGHT)
        else: original_image = original_image.transpose(Image.FLIP_TOP_BOTTOM)
        show_image()

# --- Thiết lập Giao diện (GUI) ---
# (Phần này chủ yếu là cấu hình Layout và khởi tạo các đối tượng)
window = tk.Tk()
window.title("Ứng dụng Chỉnh sửa Ảnh")
window.geometry("1500x900")

# Frame trái chứa các thanh công cụ
left_frame = tk.Frame(window, bg="#1e272e", width=300)
left_frame.pack(side="left", fill="y")
left_frame.pack_propagate(False)

# Canvas bên phải chứa ảnh
canvas = tk.Canvas(window, highlightthickness=0, bg="#2d3436")
canvas.pack(side="left", fill="both", expand=True)

# Khởi tạo công cụ Crop
crop_engine = CropTool(canvas, lambda: (original_image, zoom_factor, img_id), apply_crop)

# Gán sự kiện chuột
canvas.bind("<Button-1>", lambda e: drag_data.update({"x": e.x, "y": e.y}))
canvas.bind("<B1-Motion>", lambda e: [canvas.move(img_id, e.x-drag_data["x"], e.y-drag_data["y"]), 
                                      drag_data.update({"x": e.x, "y": e.y})] if img_id else None)
canvas.bind("<MouseWheel>", lambda e: on_mouse_wheel(e)) # Tự viết hàm xử lý delta zoom

window.mainloop()
