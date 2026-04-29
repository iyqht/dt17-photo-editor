```
git clone https://github.com/iyqht/dt17-photo-editor.git
cd dt17-photo-editor
pip install pillow
python main.py
```

## 1. File `controls.py` (Các thanh điều khiển)
File này định nghĩa cách các thanh trượt (Scale) và nút bấm hoạt động.

* **`class Base`**: Đây là "khuôn mẫu" chung. Thay vì viết code lặp đi lặp lại cho 3 thanh trượt, mình thiết kế một bộ khung duy nhất và tái sử dụng nó.
* **`self.var`**: Sử dụng `tk.DoubleVar` để liên kết giá trị của thanh trượt với biến số. Khi người dùng kéo thanh hoặc dùng chuột cuộn, biến này tự động đồng bộ hai chiều.
* **`on_change`**: Đây là "cầu nối". Mỗi khi giá trị thay đổi, nó sẽ gọi hàm `callback` truyền sang `main.py` để xử lý ảnh ngay lập tức.
* **`decrease` / `increase`**: Logic cho nút `[-]` và `[+]`. Nó lấy giá trị hiện tại cộng/trừ với bước nhảy (`resolution`) và dùng `max`/`min` để đảm bảo giá trị luôn nằm trong giới hạn an toàn.
* **Các lớp con (`ZoomScale`, `RotateScale`, `BrightnessScale`)**: Kế thừa từ `Base` và chỉ cần nạp vào các thông số riêng (như độ sáng từ 0.0 đến 2.0, góc xoay từ 0 đến 360).

---

## 2. File `crop_tool.py` (Công cụ cắt ảnh)
Đây là module xử lý logic toán học và hình học phức tạp nhất của dự án.

* **`activate`**: Khi bấm nút cắt, hàm này gắn (bind) chuột phải các sự kiện vẽ khung cắt vào thay thế.
* **`drag_motion`**: 
  * Khi kéo chuột, nó cập nhật tọa độ khung chữ nhật trắng (`rect_id`).
* **`execute_crop` (Trái tim của tính năng)**:
  * Lấy tọa độ vùng chọn trên màn hình ($x, y$).
  * Tính toán vị trí lề của ảnh trên Canvas dựa vào tâm ảnh và hệ số zoom hiện tại.
  * **Công thức ánh xạ ngược**:
    $$\text{Tọa độ ảnh gốc} = \frac{\text{Tọa độ màn hình} - \text{Vị trí lề ảnh}}{\text{Zoom}}$$
  * Cuối cùng, dùng lệnh `orig_img.crop()` để trích xuất mảng pixel chính xác từ file gốc.

---

## 3. File `main.py` (Luồng xử lý chính)
Đây là bộ não điều phối toàn bộ ứng dụng và xử lý đồ họa.

* **`show_image()`**: Xử lý ảnh:
  1. **Brightness**: Chỉnh độ sáng bằng `ImageEnhance`.
  2. **RGBA**: Chuyển hệ màu để khi xoay ảnh, các góc lộ ra sẽ trong suốt, hòa vào màu nền Canvas thay vì bị viền đen.
  3. **Rotate**: Xoay ảnh (dùng `expand=True` để khung hình tự nở ra, không bị cắt mất góc).
  4. **Resize (Zoom)**: Dùng thuật toán `LANCZOS` để khử răng cưa, làm mịn ảnh (dễ bị lag).
* **`mouse_wheel` & `drag_motion`**: Bắt sự kiện cuộn chuột để Zoom và tính toán khoảng cách `dx, dy` để di chuyển ảnh tự do trên màn hình.
* **Hệ thống Undo/Redo**:
  * Sử dụng 2 danh sách hoạt động theo nguyên lý Ngăn xếp (Stack): `undo_stack` và `redo_stack`.
  * **`save_state`**: Luôn chụp lại một bản sao của ảnh hiện tại cất vào `undo_stack` trước khi thực hiện hành động mới (như Cắt, Lật).
  * **`undo` / `redo`**: Hoán đổi vị trí của bức ảnh giữa hiện tại, quá khứ (undo) và tương lai (redo).
* **`flip_image`**: Sử dụng hàm `transpose` của Pillow để lật ma trận điểm ảnh theo trục ngang (`FLIP_LEFT_RIGHT`) hoặc trục dọc (`FLIP_TOP_BOTTOM`).
