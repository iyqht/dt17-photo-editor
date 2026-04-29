import tkinter as tk


# --- LỚP CƠ SỞ (BASE CLASS) ---
# Lớp này đóng vai trò là "bản thiết kế" chung cho tất cả các thanh điều chỉnh.
# Nó giúp tránh việc phải viết lại mã nguồn nhiều lần cho những thành phần giống nhau.
class Base:
    def __init__(self, master, label, from_, to, resolution, default_value, callback):
        """
        Khởi tạo bộ điều khiển.
        master: Widget cha (thường là Sidebar hoặc Canvas).
        label: Tên hiển thị của công cụ.
        from_/to: Phạm vi giá trị (Min/Max).
        resolution: Bước nhảy của giá trị (ví dụ: 0.1).
        default_value: Giá trị mặc định khi vừa mở ứng dụng.
        callback: Hàm xử lý ảnh ở main.py sẽ được gọi khi giá trị thay đổi.
        """
        self.master = master
        # DoubleVar: Biến đặc biệt của Tkinter dùng để liên kết dữ liệu số thực với giao diện.
        # Khi biến này thay đổi, thanh trượt tự nhảy theo và ngược lại.
        self.var = tk.DoubleVar(master=master, value=default_value)
        self.res = resolution
        self.callback = callback

        # --- CẤU HÌNH PHONG CÁCH (STYLING) ---
        scale_style = {
            "bg": "#1e272e",  # Màu nền tối
            "fg": "#d2dae2",  # Màu chữ sáng
            "highlightthickness": 0,  # Loại bỏ viền khi chọn
            "troughcolor": "#485460",  # Màu máng trượt
            "activebackground": "#05c46b",  # Màu khi tương tác
            "orient": tk.HORIZONTAL,  # Nằm ngang
            "showvalue": 0,  # Tắt số mặc định để tự vẽ lại ở vị trí đẹp hơn
        }

        btn_style = {
            "width": 2,
            "fg": "white",
            "activebackground": "#05c46b",
            "relief": "flat",  # Nút bấm phẳng hiện đại
            "font": ("Arial", 9, "bold"),
        }

        # --- XÂY DỰNG BỐ CỤC (LAYOUT) ---
        # Frame chính bao bọc toàn bộ công cụ
        self.frame = tk.Frame(master, bg="#1e272e")

        # 1. Phần Header: Chứa tên (Label) và con số đang chọn (Value)
        self.header = tk.Frame(self.frame, bg="#1e272e")
        self.header.pack(side=tk.TOP, pady=3)

        self.label_title = tk.Label(self.header, text=label, bg="#1e272e", fg="white")
        self.label_title.pack(side=tk.LEFT)

        # Label hiển thị giá trị hiện tại (ví dụ: 1.0) để người dùng dễ quan sát
        self.label_value = tk.Label(
            self.header, text=str(default_value), bg="#1e272e", fg="white"
        )
        self.label_value.pack(side=tk.LEFT, padx=5)

        # 2. Phần Control: Chứa bộ ba [ Nút - ] [ Thanh trượt ] [ Nút + ]
        self.control_container = tk.Frame(self.frame, bg="#1e272e")
        self.control_container.pack(side=tk.BOTTOM, pady=3)

        # Nút trừ [-] để tinh chỉnh giảm giá trị
        self.btn_minus = tk.Button(
            self.control_container,
            text="-",
            bg="#ff3f34",
            command=self.decrease,
            **btn_style,
        )
        self.btn_minus.pack(side=tk.LEFT, padx=2)

        # Thanh trượt Scale chính
        self.scale = tk.Scale(
            self.control_container,
            from_=from_,
            to=to,
            resolution=resolution,
            variable=self.var,
            command=self.on_change,
            **scale_style,
        )
        self.scale.pack(side=tk.LEFT, expand=True)

        # Nút cộng [+] để tinh chỉnh tăng giá trị
        self.btn_plus = tk.Button(
            self.control_container,
            text="+",
            bg="#05c46b",
            command=self.increase,
            **btn_style,
        )
        self.btn_plus.pack(side=tk.LEFT, padx=2)

    # --- CÁC HÀM XỬ LÝ SỰ KIỆN ---

    def on_change(self, value):
        """Được gọi mỗi khi thanh trượt di chuyển."""
        # Làm tròn giá trị để tránh các lỗi số lẻ dài (ví dụ: 1.00000000002)
        formatted_val = round(float(value), 2)
        # Cập nhật con số hiển thị trên Label
        self.label_value.config(text=str(formatted_val))
        # Gửi giá trị mới về main.py để xử lý ảnh
        self.callback(formatted_val)

    def decrease(self):
        """Giảm giá trị hiện tại đi một bước nhảy (resolution)."""
        new_val = self.var.get() - self.res
        # max() đảm bảo giá trị không nhỏ hơn mức tối thiểu (from)
        final_val = max(self.scale["from"], new_val)
        self.var.set(final_val)
        self.on_change(final_val)  # Kích hoạt việc cập nhật UI và Ảnh

    def increase(self):
        """Tăng giá trị hiện tại thêm một bước nhảy."""
        new_val = self.var.get() + self.res
        # min() đảm bảo giá trị không vượt quá mức tối đa (to)
        final_val = min(self.scale["to"], new_val)
        self.var.set(final_val)
        self.on_change(final_val)

    def set_value(self, val):
        """Hàm đồng bộ: Dùng khi zoom bằng chuột để thanh trượt nhảy theo."""
        self.var.set(val)
        self.label_value.config(text=str(round(float(val), 2)))

    # Các hàm hỗ trợ hiển thị Widget
    def pack(self, **kwargs):
        self.frame.pack(**kwargs)

    def place(self, **kwargs):
        self.frame.place(**kwargs)


# --- CÁC LỚP CON (SUBCLASSES) ---
# Sử dụng 'super().__init__' để khởi tạo bộ khung Base với các thông số riêng biệt.


class ZoomScale(Base):
    def __init__(self, master, callback):
        # Zoom từ 1% đến 500%, mặc định 100%
        super().__init__(master, "Zoom (%)", 1, 500, 0.1, 100, callback)


class RotateScale(Base):
    def __init__(self, master, callback):
        # Xoay từ 0 đến 360 độ
        super().__init__(master, "Góc xoay (°)", 0, 360, 0.1, 0, callback)


class BrightnessScale(Base):
    def __init__(self, master, callback):
        # Độ sáng từ 0.0 (tối đen) đến 2.0 (siêu sáng), mặc định 1.0
        super().__init__(master, "Độ sáng", 0.0, 2.0, 0.01, 1.0, callback)
