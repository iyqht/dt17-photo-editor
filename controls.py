import tkinter as tk


# --- Lớp cơ sở (Base Class) ---
# Lớp này định nghĩa khung giao diện dùng chung cho tất cả các thanh điều chỉnh
class Base:
    def __init__(self, master, label, from_, to, resolution, default_value, callback):
        self.master = master
        # Biến DoubleVar của Tkinter để lưu trữ và theo dõi giá trị kiểu số thực
        self.var = tk.DoubleVar(master=master, value=default_value)
        self.res = resolution
        self.callback = callback  # Hàm sẽ được gọi ở file main.py khi giá trị thay đổi

        # Tạo một Frame (khung) để nhóm Scale và các Button lại với nhau
        self.frame = tk.Frame(master)

        # Nút bấm để giảm giá trị (-)
        self.btn_minus = tk.Button(self.frame, text="-", command=self.decrease)
        self.btn_minus.pack(side=tk.LEFT)

        # Tạo thanh trượt (Scale)
        self.scale = tk.Scale(
            self.frame,
            label=label,
            from_=from_,
            to=to,
            resolution=resolution,
            orient=tk.HORIZONTAL,
            variable=self.var,  # Liên kết với biến self.var để tự động cập nhật
            command=self.on_change,  # Mỗi khi kéo thanh trượt, hàm on_change sẽ được gọi
        )
        self.scale.pack(side=tk.LEFT)

        # Nút bấm để tăng giá trị (+)
        self.btn_plus = tk.Button(self.frame, text="+", command=self.increase)
        self.btn_plus.pack(side=tk.LEFT)  # Đặt nút ở bên phải phía dưới thanh Scale

    def on_change(self, value):
        """Hàm trung gian tự động gọi khi người dùng kéo thanh trượt"""
        # value nhận vào từ Scale thường là chuỗi, cần ép sang float
        self.callback(float(value))

    def decrease(self):
        """Xử lý khi nhấn nút [-]"""
        # Lấy giá trị hiện tại trừ đi một bước nhảy (resolution)
        new_val = self.var.get() - self.res
        # Đảm bảo giá trị mới không nhỏ hơn giới hạn dưới 'from'
        self.var.set(max(self.scale["from"], new_val))
        # Thông báo sự thay đổi ra bên ngoài thông qua callback
        self.callback(self.var.get())

    def increase(self):
        """Xử lý khi nhấn nút [+]"""
        # Lấy giá trị hiện tại cộng thêm một bước nhảy
        new_val = self.var.get() + self.res
        # Đảm bảo giá trị mới không vượt quá giới hạn trên 'to'
        self.var.set(min(self.scale["to"], new_val))
        # Thông báo sự thay đổi ra bên ngoài thông qua callback
        self.callback(self.var.get())

    def set_value(self, val):
        """Dùng để cập nhật giá trị từ bên ngoài (ví dụ: đồng bộ khi lăn chuột)"""
        self.var.set(val)

    def pack(self, **kwargs):
        """Phương thức hiển thị dùng pack"""
        self.frame.pack(**kwargs)

    def place(self, **kwargs):
        """Phương thức hiển thị dùng tọa độ tuyệt đối/tương đối"""
        self.frame.place(**kwargs)


# --- Các lớp con (Subclasses) ---
# Sử dụng 'super().__init__' để tận dụng lại cấu trúc của lớp Base nhưng với thông số khác nhau


class ZoomScale(Base):
    def __init__(self, master, callback):
        # Cấu hình riêng cho Zoom: từ 1% đến 500%, mặc định 100%
        super().__init__(master, "Zoom (%)", 1, 500, 0.1, 100, callback)


class RotateScale(Base):
    def __init__(self, master, callback):
        # Cấu hình riêng cho Xoay: từ 0 đến 360 độ, mặc định 0
        super().__init__(master, "Rotate (°)", 0, 360, 0.1, 0, callback)


class BrightnessScale(Base):
    def __init__(self, master, callback):
        # Cấu hình riêng cho Độ sáng: từ 0.0 đến 2.0, mặc định 1.0 (mức bình thường)
        super().__init__(master, "Brightness", 0.0, 2.0, 0.1, 1.0, callback)
