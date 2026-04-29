import time
import tkinter as tk
from tkinter import filedialog

from PIL import Image, ImageEnhance, ImageTk  # Thêm ImageEnhance để chỉnh độ sáng

from controls import (  # Import các Class riêng tự viết
    BrightnessScale,
    RotateScale,
    ZoomScale,
)
from crop_tool import CropTool

# ==========================================
# 1. KHAI BÁO BIẾN TOÀN CỤC (GLOBAL STATE)
# ==========================================
original_image = (
    None  # Lưu ảnh gốc (Pixel thực) để tránh mất chất lượng khi chỉnh sửa nhiều lần
)
tk_image = None  # Biến lưu trữ ảnh đã xử lý để đưa lên UI của Tkinter
tk_preview_image = None  # Biến lưu ảnh thu nhỏ (Thumbnail) ở cột bên trái
img_id = None  # Số ID định danh của bức ảnh trên Canvas

# Các biến lưu thông số điều chỉnh hiện tại
zoom_factor = 1.0  # Tỷ lệ thu phóng (1.0 = 100%)
rotate_angle = 0  # Góc xoay (độ)
brightness_val = 1.0  # Độ sáng (1.0 là mặc định)

# Các biến hỗ trợ hiệu suất và tương tác chuột
zoom_timer = None  # Bộ hẹn giờ dùng để phân biệt đang kéo trượt hay đã dừng lại
last_zoom_time = 0  # Lưu thời gian lần cuộn chuột cuối cùng để chống lag
drag_data = {
    "x": 0,
    "y": 0,
}  # Lưu tọa độ chuột khi bắt đầu nhấn để tính toán khoảng cách kéo thả

# Hệ thống Ngăn xếp (Stack) cho Undo/Redo
undo_stack = []  # Chứa lịch sử các thao tác đã làm
redo_stack = []  # Chứa các thao tác vừa bị hoàn tác (Undo)


# ==========================================
# 2. CÁC HÀM XỬ LÝ LOGIC ẢNH
# ==========================================


def update_ui_change():
    """
    Hàm tối ưu hiệu suất (Debounce):
    Khi người dùng đang kéo thanh trượt liên tục, chỉ render ảnh chất lượng thấp cho mượt.
    Sau khi dừng kéo 150ms, mới bắt đầu render ảnh chất lượng cao.
    """
    global zoom_timer
    if zoom_timer:
        window.after_cancel(
            zoom_timer
        )  # Hủy lệnh render chất lượng cao cũ nếu vẫn đang kéo

    show_image(high_quality=False)  # Gọi render nhanh
    # Đặt lịch: Sau 150ms sẽ render đẹp
    zoom_timer = window.after(150, lambda: show_image(high_quality=True))


# --- Các hàm Callback nhận dữ liệu từ các thanh trượt (controls.py) ---
def on_zoom_change(val):
    global zoom_factor
    zoom_factor = val / 100  # Chuyển từ % (100) sang hệ số (1.0)
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
    """
    Trái tim của ứng dụng: Pipeline (Quy trình) xử lý và vẽ ảnh lên màn hình.
    Thứ tự: Chỉnh sáng -> Thêm kênh Alpha -> Xoay -> Resize -> Vẽ lên Canvas.
    """
    global tk_image, img_id
    if original_image:
        # Bước 1: Xử lý độ sáng
        enhancer = ImageEnhance.Brightness(original_image)
        temp_img = enhancer.enhance(brightness_val)

        # Bước 2: Xử lý xoay
        # Chuyển đổi ảnh sang hệ RGBA để phần nền bị lộ ra khi xoay sẽ trong suốt thay vì màu đen
        temp_img = temp_img.convert("RGBA")
        # expand=True giúp khung hình tự động nở ra để chứa đủ 4 góc của ảnh sau khi xoay
        temp_img = temp_img.rotate(rotate_angle, expand=True, resample=Image.BILINEAR)

        # Bước 3: Xử lý Zoom (Thay đổi kích thước)
        new_w = int(temp_img.width * zoom_factor)
        new_h = int(temp_img.height * zoom_factor)
        # Chọn thuật toán: LANCZOS (sắc nét, chậm) hoặc NEAREST (răng cưa, cực nhanh)
        method = Image.LANCZOS if high_quality else Image.NEAREST
        resized_img = temp_img.resize((new_w, new_h), method)

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
    """Hàm mở file ảnh và khởi tạo các giá trị mặc định"""
    global original_image, img_id, zoom_factor, tk_preview_image
    path = filedialog.askopenfilename(
        filetypes=[("Image files", "*.jpg *.jpeg *.png *.bmp *.gif")]
    )
    if path:
        original_image = Image.open(path)
        img_id = None
        canvas.delete("all")  # Xóa ảnh cũ trên màn hình

        # Xóa sạch lịch sử khi mở ảnh mới
        undo_stack.clear()
        redo_stack.clear()
        save_state()  # Lưu trạng thái gốc của ảnh mới vào undo_stack
        zoom_factor = 1.0

        # Tạo ảnh xem trước (Thumbnail) thu nhỏ để hiển thị ở thanh bên trái
        preview_copy = original_image.copy()
        preview_copy.thumbnail((300, 300))
        tk_preview_image = ImageTk.PhotoImage(preview_copy)
        preview_label.config(image=tk_preview_image, text="", width=0, height=0)

        show_image()


# ==========================================
# 3. CÁC HÀM SỰ KIỆN CHUỘT
# ==========================================


def mouse_wheel(event):
    """Hàm xử lý Zoom bằng con lăn chuột"""
    global zoom_factor, last_zoom_time
    if original_image:
        curr = time.time()
        # Giới hạn tần số xử lý: Chỉ nhận sự kiện cuộn chuột mỗi 0.02 giây để chống lag
        if curr - last_zoom_time < 0.02:
            return
        last_zoom_time = curr

        # Tăng/giảm 5% mỗi lần lăn chuột
        zoom_factor += 0.05 if event.delta > 0 else -0.05
        # Ràng buộc giá trị zoom không vượt quá giới hạn của thanh trượt (ZoomScale)
        zoom_factor = max(
            zoom_ctrl.scale["from"] / 100, min(zoom_factor, zoom_ctrl.scale["to"] / 100)
        )

        # Cập nhật ngược lại giá trị lên thanh trượt trên UI để đồng bộ
        zoom_ctrl.set_value(zoom_factor * 100)
        update_ui_change()


def drag_start(event):
    """Ghi nhận tọa độ chuột khi bắt đầu nhấn chuột trái (để kéo ảnh)"""
    drag_data["x"], drag_data["y"] = event.x, event.y


def drag_motion(event):
    """Tính toán khoảng cách di chuyển chuột và dịch chuyển ảnh tương ứng"""
    if img_id:
        dx, dy = event.x - drag_data["x"], event.y - drag_data["y"]
        canvas.move(img_id, dx, dy)
        # Cập nhật lại mốc tọa độ mới
        drag_data["x"], drag_data["y"] = event.x, event.y


# ==========================================
# 4. QUẢN LÝ LỊCH SỬ (UNDO/REDO & CROP)
# ==========================================


def save_state():
    """Lưu bản sao của ảnh hiện tại vào ngăn xếp Undo"""
    global undo_stack  # SỬA LỖI TẠI ĐÂY: đổi từ undo thành undo_stack
    if original_image:
        old_img = original_image.copy()
        undo_stack.append(old_img)
        # Giới hạn lịch sử lưu tối đa 10 bước để không làm tràn RAM máy tính
        if len(undo_stack) > 10:
            undo_stack.pop(0)


def get_crop_data():
    """Hàm cầu nối cung cấp dữ liệu ảnh cho Class CropTool"""
    return original_image, zoom_factor, img_id


def apply_crop(new_img):
    """Được gọi bởi CropTool sau khi đã tính toán cắt ảnh xong"""
    global original_image
    save_state()  # Lưu lịch sử trước khi gán ảnh mới
    redo_stack.clear()  # Đã có thao tác mới thì dòng thời gian thay đổi, xóa tương lai (redo)
    original_image = new_img
    show_image()


def start_crop_mode():
    """Bật chế độ cắt ảnh (Chiếm quyền con trỏ chuột)"""
    if original_image:
        crop_engine.activate(on_exit_callback=restore_binding)


def restore_binding():
    """Trả lại quyền điều khiển kéo thả ảnh sau khi cắt xong"""
    canvas.bind("<Button-1>", drag_start)
    canvas.bind("<B1-Motion>", drag_motion)
    canvas.unbind("<ButtonRelease-1>")


def undo():
    """Hoàn tác: Bốc ảnh từ lịch sử (undo_stack) gán làm ảnh hiện tại, đẩy ảnh hiện tại vào redo_stack"""
    global original_image, undo_stack, redo_stack
    if undo_stack and original_image:
        redo_stack.append(original_image.copy())
        original_image = undo_stack.pop()
        show_image()


def redo():
    """Làm lại: Kéo ảnh từ redo_stack trả về lại ảnh hiện tại"""
    global original_image, undo_stack, redo_stack
    if redo_stack and original_image:
        undo_stack.append(original_image.copy())
        original_image = redo_stack.pop()
        show_image()


def flip_image(mode):
    """Lật ảnh sử dụng hàm transpose tích hợp sẵn của thư viện Pillow"""
    global original_image
    if original_image:
        save_state()  # Lưu lịch sử để có thể Undo thao tác lật ảnh
        if mode == "horizontal":
            original_image = original_image.transpose(Image.FLIP_LEFT_RIGHT)
        elif mode == "vertical":
            original_image = original_image.transpose(Image.FLIP_TOP_BOTTOM)
        show_image()


# ==========================================
# 5. THIẾT LẬP GIAO DIỆN NGƯỜI DÙNG (UI)
# ==========================================
window = tk.Tk()
window.title("Ứng dụng Chỉnh sửa Ảnh")
window.geometry("1500x900+50+50")  # Kích thước và vị trí khởi tạo

# --- KHUNG BÊN TRÁI (SIDEBAR) ---
left_frame = tk.Frame(window, bg="#1e272e", width=300)
left_frame.pack(side="left", fill="y")
left_frame.pack_propagate(
    False
)  # Ngăn không cho các widget con làm thay đổi độ rộng của left_frame

# Tiêu đề và ảnh xem trước (Thumbnail)
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

# Định dạng chung cho các nút bấm (Style dictionary)
btn_style = {
    "width": 20,
    "bg": "#485460",
    "fg": "white",
    "activebackground": "#05c46b",
    "relief": "flat",
    "font": ("Arial", 9, "bold"),
}

# --- KHUNG BÊN PHẢI (CANVAS CHÍNH) ---
right_frame = tk.Frame(window, bg="#1e272e")
right_frame.pack(side="left", fill="both", expand=True)

canvas = tk.Canvas(right_frame, highlightthickness=0, bg="#2d3436")
canvas.pack(fill="both", expand=True)

# --- CÁC NÚT CÔNG CỤ (DƯỚI CÙNG BÊN TRÁI) ---
tools_container = tk.Frame(left_frame, bg="#1e272e")
tools_container.pack(side="bottom", fill="x", pady=20)

# Nút mở file
button = tk.Button(tools_container, text="📁 Mở ảnh", command=add_image, **btn_style)
button.pack(pady=20)

# Nút lật ngang / dọc
flip_frame = tk.Frame(tools_container, bg="#1e272e")
flip_frame.pack(pady=10)
btn_flip_h = tk.Button(
    flip_frame, text="Lật Ngang", command=lambda: flip_image("horizontal"), **btn_style
)
btn_flip_h.config(width=8)
btn_flip_h.pack(side=tk.LEFT, padx=5, expand=True)

btn_flip_v = tk.Button(
    flip_frame, text="Lật Dọc", command=lambda: flip_image("vertical"), **btn_style
)
btn_flip_v.config(width=8)
btn_flip_v.pack(side="right", padx=5, expand=True)

# Nút cắt ảnh
btn_crop = tk.Button(
    tools_container, text="✂️ Cắt ảnh", command=start_crop_mode, **btn_style
)
btn_crop.pack(pady=10)

# Khởi tạo Object thực hiện chức năng cắt ảnh
crop_engine = CropTool(canvas, get_crop_data, apply_crop)

# Khung chứa bộ nút Undo/Redo
history_frame = tk.Frame(tools_container, bg="#1e272e")
history_frame.pack(pady=10)

btn_undo = tk.Button(history_frame, text="Undo", command=undo, **btn_style)
btn_undo.config(width=10)
btn_undo.pack(side=tk.LEFT, padx=5, expand=True)

btn_redo = tk.Button(history_frame, text="Redo", command=redo, **btn_style)
btn_redo.config(width=10)
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
