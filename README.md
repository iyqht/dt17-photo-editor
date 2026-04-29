## 1. File `controls.py` (Các thanh điều khiển)
File này định nghĩa cách các thanh trượt (Scale) và nút bấm hoạt động.

* **`class Base`**: Đây là "khuôn mẫu" chung. Thay vì viết code lặp đi lặp lại cho 3 thanh trượt, mình thiết kế một bộ khung duy nhất và tái sử dụng nó.
* **`self.var`**: Sử dụng `tk.DoubleVar` để liên kết giá trị của thanh trượt với biến số. Khi người dùng kéo thanh hoặc dùng chuột cuộn, biến này tự động đồng bộ hai chiều.
* **`self.header`**: Chứa tên công cụ và con số hiện tại (ví dụ: *"Độ sáng 1.2"*). Việc tách số ra khỏi thanh trượt giúp giao diện phẳng và gọn gàng hơn.
* **`on_change`**: Đây là "cầu nối". Mỗi khi giá trị thay đổi, nó sẽ gọi hàm `callback` truyền sang `main.py` để xử lý ảnh ngay lập tức.
* **`decrease` / `increase`**: Logic cho nút `[-]` và `[+]`. Nó lấy giá trị hiện tại cộng/trừ với bước nhảy (`resolution`) và dùng `max`/`min` để đảm bảo giá trị luôn nằm trong giới hạn an toàn.
* **Các lớp con (`ZoomScale`, `RotateScale`, `BrightnessScale`)**: Kế thừa từ `Base` và chỉ cần nạp vào các thông số riêng (như độ sáng từ $0.0$ đến $2.0$, góc xoay từ $0$ đến $360$).

---

## 2. File `crop_tool.py` (Công cụ cắt ảnh)
Đây là module xử lý logic toán học và hình học phức tạp nhất của dự án.

* **`activate`**: Khi bấm nút cắt, hàm này "chiếm quyền" chuột. Nó gỡ bỏ các sự kiện kéo thả ảnh thông thường và gắn (bind) các sự kiện vẽ khung cắt vào thay thế.
* **`drag_motion` & `draw_overlays`**: 
  * Khi kéo chuột, nó cập nhật tọa độ khung chữ nhật trắng (`rect_id`).
  * Đồng thời, `draw_overlays` tạo ra 4 hình chữ nhật đen mờ (`gray50`) bao quanh vùng chọn, tạo hiệu ứng "đục lỗ" giúp người dùng tập trung vào vùng ảnh muốn cắt.
* **`execute_crop` (Trái tim của tính năng)**:
  * Lấy tọa độ vùng chọn trên màn hình ($x, y$).
  * Tính toán vị trí lề của ảnh trên Canvas dựa vào tâm ảnh và hệ số zoom hiện tại.
  * **Công thức ánh xạ ngược**:
    $$\text{Tọa độ ảnh gốc} = \frac{\text{Tọa độ màn hình} - \text{Vị trí lề ảnh}}{\text{Zoom}}$$
  * Cuối cùng, dùng lệnh `orig_img.crop()` để trích xuất mảng pixel chính xác từ file gốc.

---

## 3. File `main.py` (Luồng xử lý chính)
Đây là bộ não điều phối toàn bộ ứng dụng và xử lý đồ họa.

* **`update_ui_change` (Debounce Hiệu suất)**: Đây là kỹ thuật chống giật lag (lag-free). Nó dùng `window.after` để phân biệt: Nếu người dùng đang kéo thanh trượt liên tục, nó gọi render chất lượng thấp. Chỉ khi dừng tay $150$ms, nó mới render chất lượng cao.
* **`show_image(high_quality)`**: Pipeline (quy trình) xử lý ảnh theo đúng thứ tự:
  1. **Brightness**: Chỉnh độ sáng bằng `ImageEnhance`.
  2. **RGBA**: Chuyển hệ màu để khi xoay ảnh, các góc lộ ra sẽ trong suốt, hòa vào màu nền Canvas thay vì bị viền đen.
  3. **Rotate**: Xoay ảnh (dùng `expand=True` để khung hình tự nở ra, không bị cắt mất góc).
  4. **Resize (Zoom)**: Nếu `high_quality=False`, dùng thuật toán `NEAREST` để chạy cực nhanh. Nếu `True`, dùng `LANCZOS` để khử răng cưa, làm mịn ảnh.
* **`mouse_wheel` & `drag_motion`**: Bắt sự kiện cuộn chuột để Zoom (có timer giới hạn $0.02$s để chống gọi hàm quá tải) và tính toán khoảng cách `dx, dy` để di chuyển (Pan) ảnh tự do trên màn hình.
* **Hệ thống Undo/Redo**:
  * Sử dụng 2 danh sách hoạt động theo nguyên lý Ngăn xếp (Stack): `undo_stack` và `redo_stack`.
  * **`save_state`**: Luôn chụp lại một bản sao của ảnh hiện tại cất vào `undo_stack` trước khi thực hiện hành động mới (như Cắt, Lật).
  * **`undo` / `redo`**: Hoán đổi vị trí của bức ảnh giữa hiện tại, quá khứ (undo) và tương lai (redo).
* **`flip_image`**: Sử dụng hàm `transpose` của Pillow để lật ma trận điểm ảnh theo trục ngang (`FLIP_LEFT_RIGHT`) hoặc trục dọc (`FLIP_TOP_BOTTOM`).
