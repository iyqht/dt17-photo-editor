from tkinter import messagebox


class CropTool:
    def __init__(self, canvas, get_img_info_func, update_img_func):
        """
        Khởi tạo công cụ cắt ảnh.
        canvas: Nơi hiển thị ảnh.
        get_img_info_func: Hàm để lấy dữ liệu (ảnh gốc, zoom, id ảnh) từ main.py.
        update_img_func: Hàm để gửi kết quả ảnh đã cắt về cho main.py.
        """
        self.canvas = canvas
        self.img_info = get_img_info_func
        self.update_img = update_img_func

        self.rect_id = None  # ID của khung chữ nhật nét đứt màu trắng
        self.overlay_ids = []  # Danh sách ID của 4 miếng che màu tối xung quanh vùng chọn
        self.start_x = 0  # Tọa độ X khi bắt đầu nhấn chuột
        self.start_y = 0  # Tọa độ Y khi bắt đầu nhấn chuột

    def activate(self, on_exit_callback):
        """
        Bật chế độ cắt ảnh.
        on_exit_callback: Hàm sẽ gọi ở main.py để trả lại quyền điều khiển chuột bình thường.
        """
        self.on_exit = on_exit_callback
        self.canvas.config(
            cursor="cross"
        )  # Đổi con trỏ chuột thành dấu thập (+) cho chuyên nghiệp

        # Ghi đè (Bind) các sự kiện chuột trên Canvas để phục vụ việc vẽ khung cắt
        self.canvas.bind("<Button-1>", self.drag_start)
        self.canvas.bind("<B1-Motion>", self.drag_motion)
        self.canvas.bind("<ButtonRelease-1>", self.drag_end)

    def drag_start(self, event):
        """Khi bắt đầu nhấn chuột trái: Xác định góc đầu tiên của vùng chọn"""
        self.start_x, self.start_y = event.x, event.y
        self.clear()  # Xóa sạch các hình vẽ cũ nếu có

        # Tạo một hình chữ nhật nét đứt (dash) làm khung chọn ban đầu
        self.rect_id = self.canvas.create_rectangle(
            self.start_x,
            self.start_y,
            self.start_x,
            self.start_y,
            outline="white",
            dash=(4, 4),
            width=2,
        )

    def drag_motion(self, event):
        """Khi đang giữ và kéo chuột: Cập nhật kích thước khung chọn liên tục"""
        x1, y1 = self.start_x, self.start_y
        x2, y2 = event.x, event.y

        # Cập nhật tọa độ cho khung nét đứt theo vị trí chuột hiện tại
        self.canvas.coords(self.rect_id, x1, y1, x2, y2)

        # Vẽ các miếng che màu tối xung quanh để làm nổi bật vùng được chọn
        self.draw_overlays(x1, y1, x2, y2)

    def draw_overlays(self, x1, y1, x2, y2):
        """
        Tạo hiệu ứng vùng chọn sáng, xung quanh tối.
        Nguyên lý: Vẽ 4 hình chữ nhật màu đen có độ trong suốt bao quanh khung chọn.
        """
        # Xóa các miếng che cũ trước khi vẽ mới (để tránh bị lag và chồng chất layer)
        for oid in self.overlay_ids:
            self.canvas.delete(oid)
        self.overlay_ids = []

        # Lấy kích thước hiện tại của Canvas
        w, h = self.canvas.winfo_width(), self.canvas.winfo_height()

        # Xác định tọa độ các biên (min/max để hỗ trợ kéo chuột theo mọi hướng)
        xmin, xmax = min(x1, x2), max(x1, x2)
        ymin, ymax = min(y1, y2), max(y1, y2)

        # Cấu hình màu sắc cho lớp phủ (đen mờ)
        params = {"fill": "black", "stipple": "gray50", "outline": ""}

        # Vẽ 4 miếng đè lên Canvas
        self.overlay_ids.append(
            self.canvas.create_rectangle(0, 0, w, ymin, **params)
        )  # Miếng trên
        self.overlay_ids.append(
            self.canvas.create_rectangle(0, ymax, w, h, **params)
        )  # Miếng dưới
        self.overlay_ids.append(
            self.canvas.create_rectangle(0, ymin, xmin, ymax, **params)
        )  # Miếng trái
        self.overlay_ids.append(
            self.canvas.create_rectangle(xmax, ymin, w, ymax, **params)
        )  # Miếng phải

    def drag_end(self, event):
        """Khi thả chuột: Kết thúc việc chọn vùng và hỏi xác nhận"""
        if messagebox.askyesno("Xác nhận", "Bạn có muốn cắt vùng đã chọn?"):
            self.execute_crop()
        self.deactivate()  # Dù cắt hay không cũng thoát chế độ Crop

    def execute_crop(self):
        """
        PHẦN QUAN TRỌNG NHẤT: Tính toán tọa độ thực trên file ảnh gốc.
        Vì ảnh trên màn hình đã bị Zoom và Di chuyển, nên tọa độ chuột không phải tọa độ ảnh.
        """
        # Lấy thông tin từ main.py
        orig_img, zoom_factor, img_id = self.img_info()
        if not orig_img or not self.rect_id:
            return

        # 1. Lấy tọa độ khung chọn trên Canvas (tọa độ màn hình)
        x1, y1, x2, y2 = self.canvas.coords(self.rect_id)

        # 2. Lấy tọa độ tâm ảnh hiện tại trên Canvas
        img_coords = self.canvas.coords(img_id)
        img_center_x, img_center_y = img_coords[0], img_coords[1]

        # 3. Tính kích thước ảnh đang hiển thị trên màn hình (đã nhân zoom)
        w_on_canvas = orig_img.width * zoom_factor
        h_on_canvas = orig_img.height * zoom_factor

        # 4. Xác định vị trí lề trái và lề trên của ảnh trên Canvas
        img_left = img_center_x - w_on_canvas / 2
        img_top = img_center_y - h_on_canvas / 2

        # 5. Công thức Ánh xạ ngược (Inverse Mapping):
        # Tọa độ thực = (Tọa độ chuột - Lề ảnh trên màn hình) / Hệ số Zoom
        left = (min(x1, x2) - img_left) / zoom_factor
        top = (min(y1, y2) - img_top) / zoom_factor
        right = (max(x1, x2) - img_left) / zoom_factor
        bottom = (max(y1, y2) - img_top) / zoom_factor

        # max(0, left/top): Ép tọa độ không bao giờ bị âm
        # min(width/height, right/bottom): Ép tọa độ không bao giờ vượt quá kích thước thật
        left = max(0, left)
        top = max(0, top)
        right = min(orig_img.width, right)
        bottom = min(orig_img.height, bottom)
        # ====================================================================

        # Nếu người dùng kéo khung hoàn toàn nằm ngoài ảnh -> Hủy lệnh cắt
        if left >= right or top >= bottom:
            self.clear()
            self.canvas.config(cursor="hand2")
            if self.on_exit:
                self.on_exit()
            return

        # 6. Sử dụng thư viện Pillow để cắt ảnh từ file gốc
        # .crop() nhận vào một bộ (left, top, right, bottom)
        cropped_img = orig_img.crop((left, top, right, bottom))

        # 7. Gửi ảnh đã cắt về hàm apply_crop trong main.py
        self.update_img(cropped_img)

    def clear(self):
        """Dọn dẹp rác: Xóa khung chọn và các miếng che trên Canvas"""
        if self.rect_id:
            self.canvas.delete(self.rect_id)
        for oid in self.overlay_ids:
            self.canvas.delete(oid)
        self.rect_id = None
        self.overlay_ids = []

    def deactivate(self):
        """Tắt chế độ Crop: Xóa vẽ nháp, đổi lại con trỏ, và khôi phục sự kiện chuột cho main.py"""
        self.clear()
        self.canvas.config(cursor="hand2")  # Trả lại con trỏ hình bàn tay
        if self.on_exit:
            self.on_exit()  # Gọi hàm restore_binding() ở main.py
