import tkinter as tk


# --- Lớp cơ sở (Base Class) ---
# Lớp này định nghĩa khung giao diện dùng chung cho tất cả các thanh điều chỉnh
class Base:
    def __init__(
        self,
        master,
        label,
        from_,
        to,
        resolution,
        default_value,
        callback,
    ):
        """
        master: Widget cha (thường là canvas hoặc frame)
        label: Tên hiển thị của thanh điều chỉnh
        from_, to: Giá trị nhỏ nhất và lớn nhất
        resolution: Bước nhảy của giá trị
        default_value: Giá trị mặc định khi khởi tạo
        callback: Hàm sẽ được gọi ở file main.py khi giá trị thay đổi
        """
        self.master = master
        # Biến DoubleVar của Tkinter để lưu trữ và theo dõi giá trị kiểu số thực
        self.var = tk.DoubleVar(master=master, value=default_value)
        self.res = resolution
        self.callback = callback

        scale_style = {
            "bg": "#1e272e",
            "fg": "#d2dae2",
            "highlightthickness": 0,
            "troughcolor": "#485460",
            "activebackground": "#05c46b",
            "orient": tk.HORIZONTAL,
            "showvalue": 0,
        }

        btn_style = {
            "width": 2,
            "fg": "white",
            "activebackground": "#05c46b",
            "relief": "flat",
            "font": ("Arial", 9, "bold"),
        }

        # Tạo một Frame (khung) để nhóm Scale và các Button lại với nhau
        self.frame = tk.Frame(master, bg="#1e272e")

        self.header = tk.Frame(self.frame, bg="#1e272e")
        self.header.pack(side=tk.TOP, pady=3)

        self.label_title = tk.Label(self.header, text=label, bg="#1e272e", fg="white")
        self.label_title.pack(side=tk.LEFT)

        self.label_value = tk.Label(
            self.header, text=str(default_value), bg="#1e272e", fg="white"
        )
        self.label_value.pack(side=tk.LEFT)

        self.control_container = tk.Frame(self.frame, bg="#1e272e")
        self.control_container.pack(side=tk.BOTTOM, pady=3)

        # Nút bấm để giảm giá trị (-)
        self.btn_minus = tk.Button(
            self.control_container,
            text="-",
            bg="#ff3f34",
            command=self.decrease,
            **btn_style,
        )
        self.btn_minus.pack(
            side=tk.LEFT, padx=2
        )  # Đặt nút ở bên trái phía dưới thanh Scale

        # Tạo thanh trượt (Scale)
        self.scale = tk.Scale(
            self.control_container,
            from_=from_,  # Giá trị bắt đầu
            to=to,  # Giá trị kết thúc
            resolution=resolution,  # Độ nhạy của mỗi bước di chuyển
            variable=self.var,  # Liên kết với biến self.var để tự động cập nhật
            command=self.on_change,  # Mỗi khi kéo thanh trượt, hàm on_change sẽ được gọi
            **scale_style,
        )
        self.scale.pack(
            side=tk.LEFT, expand=True
        )  # Mặc định Scale sẽ nằm ở trên cùng trong Frame

        # Nút bấm để tăng giá trị (+)
        self.btn_plus = tk.Button(
            self.control_container,
            text="+",
            bg="#05c46b",
            command=self.increase,
            **btn_style,
        )
        self.btn_plus.pack(
            side=tk.LEFT, padx=2
        )  # Đặt nút ở bên phải phía dưới thanh Scale

    def on_change(self, value):
        """Hàm trung gian tự động gọi khi người dùng kéo thanh trượt"""
        # value nhận vào từ Scale thường là chuỗi, cần ép sang float
        formatted_val = round(float(value), 2)
        self.label_value.config(text=str(formatted_val))
        self.callback(formatted_val)

    def decrease(self):
        """Xử lý khi nhấn nút [-]"""
        # Lấy giá trị hiện tại trừ đi một bước nhảy (resolution)
        new_val = self.var.get() - self.res
        final_val = max(self.scale["from"], new_val)
        # Đảm bảo giá trị mới không nhỏ hơn giới hạn dưới 'from'
        self.var.set(final_val)
        # Thông báo sự thay đổi ra bên ngoài thông qua callback
        self.on_change(final_val)

    def increase(self):
        """Xử lý khi nhấn nút [+]"""
        # Lấy giá trị hiện tại trừ đi một bước nhảy (resolution)
        new_val = self.var.get() + self.res
        final_val = min(self.scale["to"], new_val)
        # Đảm bảo giá trị mới không nhỏ hơn giới hạn dưới 'from'
        self.var.set(final_val)
        # Thông báo sự thay đổi ra bên ngoài thông qua callback
        self.on_change(final_val)

    def set_value(self, val):
        """Dùng để cập nhật giá trị từ bên ngoài (ví dụ: đồng bộ khi lăn chuột)"""
        self.var.set(val)
        self.label_value.config(text=str(round(float(val), 2)))

    def pack(self, **kwargs):
        """Phương thức hiển thị dùng pack (giống như đóng gói kiện hàng)"""
        self.frame.pack(**kwargs)

    def place(self, **kwargs):
        """Phương thức hiển thị dùng tọa độ tuyệt đối/tương đối"""
        self.frame.place(**kwargs)


# --- Các lớp con (Subclasses) ---
# Sử dụng 'super().__init__' để tận dụng lại cấu trúc của lớp Base nhưng với thông số khác nhau


class ZoomScale(Base):
    def __init__(self, master, callback):
        # Cấu hình riêng cho Zoom: từ 5% đến 500%, mặc định 100%
        super().__init__(master, "Zoom (%)", 1, 500, 0.1, 100, callback)


class RotateScale(Base):
    def __init__(self, master, callback):
        # Cấu hình riêng cho Xoay: từ 0 đến 360 độ, mặc định 0
        super().__init__(master, "Góc xoay (°)", 0, 360, 0.1, 0, callback)


class BrightnessScale(Base):
    def __init__(self, master, callback):
        # Cấu hình riêng cho Độ sáng: từ 0.0 đến 2.0, mặc định 1.0 (mức bình thường)
        super().__init__(master, "Độ sáng", 0.0, 2.0, 0.01, 1.0, callback)
