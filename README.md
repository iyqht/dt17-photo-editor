# ⚙️ Luồng vận hành kỹ thuật (Technical Documentation)

Tài liệu này giải thích cách hệ thống xử lý dữ liệu hình ảnh, quản lý trạng thái và ánh xạ tọa độ giữa giao diện người dùng (GUI) và tệp tin ảnh gốc.

---

## 1. Kiến trúc phân tầng (Software Architecture)

Ứng dụng được chia thành 3 Module độc lập để tách biệt trách nhiệm (Separation of Concerns):

* **`controls.py` (Giao diện điều khiển):** Đóng gói logic của các UI Widget. Sử dụng tính **Kế thừa (Inheritance)** để tạo ra các bộ điều khiển có hành vi tương tự nhưng tham số khác nhau.
* **`crop_tool.py` (Xử lý hình học):** Một module chuyên biệt dùng để tính toán ma trận tọa độ. Nó không trực tiếp sửa ảnh mà chỉ tính toán "vùng quan tâm" và gửi kết quả về Main.
* **`main.py` (Luồng chính & Pipeline):** Đóng vai trò bộ điều phối (Orchestrator). Lưu trữ các biến trạng thái toàn cục và quản lý quy trình biến đổi ảnh (Image Processing Pipeline).

---

## 2. Quy trình xử lý ảnh (Image Processing Pipeline)

Mỗi khi có một thông số thay đổi (Zoom, Rotate, Brightness), ảnh không được hiển thị ngay mà phải đi qua một Pipeline trong hàm `show_image()` theo thứ tự cố định để đảm bảo tính nhất quán:

1.  **Enhancement (Pillow):** Áp dụng độ sáng lên đối tượng `original_image`.
2.  **Color Conversion:** Chuyển hệ màu sang **RGBA**. Bước này bắt buộc để tạo kênh Alpha (trong suốt), giúp các vùng trống phát sinh khi xoay ảnh không bị đen.
3.  **Rotation:** Xoay ảnh với tham số `expand=True`. Thuật toán sẽ tính toán lại kích thước khung hình mới để chứa vừa vặn các đỉnh của ảnh đã xoay.
4.  **Resampling (Optimization):** * Khi người dùng đang thao tác: Sử dụng thuật toán `NEAREST` để giảm tải cho CPU, giúp UI mượt mà.
    * khi người dùng dừng thao tác: Sử dụng thuật toán `LANCZOS` để tái lấy mẫu chất lượng cao, khử răng cưa.
5.  **Canvas Rendering:** Chuyển đổi đối tượng PIL sang `ImageTk.PhotoImage` và cập nhật vào `img_id` trên Canvas.

---

## 3. Cơ chế ánh xạ tọa độ (Coordinate Mapping)

Đây là logic cốt lõi của công cụ Cắt (Crop). Có sự khác biệt giữa tọa độ trên màn hình (Canvas) và tọa độ trên tệp tin thực tế (Image Source).

**Bài toán:** Khi ảnh đang được phóng to 200% và nằm lệch ở góc màn hình, làm sao để cắt đúng pixel trên ảnh gốc?

**Giải pháp:** Áp dụng phép chiếu ngược (Inverse Projection):
1. Xác định vị trí lề của ảnh trên Canvas: `img_left = tâm_ảnh - (chiều_rộng_hiện_tại / 2)`.
2. Tính khoảng cách từ điểm nhấn chuột đến lề ảnh: `distance = tọa_độ_chuột - img_left`.
3. Khử hệ số Zoom: `pixel_gốc = distance / zoom_factor`.

Kết quả cuối cùng là một bộ 4 tọa độ (Left, Top, Right, Bottom) tương ứng chính xác với ma trận điểm ảnh của tệp tin gốc.

---

## 4. Quản lý trạng thái (State & History Management)

Ứng dụng quản lý lịch sử thông qua cơ chế **Double-Stack (Ngăn xếp kép)**:

* **`undo_stack`**: Lưu trữ các bản sao (Deep Copy) của ảnh gốc trước mỗi thao tác thay đổi cấu trúc (Crop, Flip).
* **`redo_stack`**: Lưu trữ các trạng thái bị đẩy ra khi thực hiện Undo.
* **Cơ chế đồng bộ UI:** Khi thực hiện Undo/Redo, ứng dụng không chỉ đổi ảnh mà còn gọi hàm `.set_value()` của các đối tượng trong `controls.py` để đồng bộ vị trí thanh trượt tương ứng với thông số của ảnh đó.

---

## 5. Cơ chế Giao tiếp (Communication Pattern)

Ứng dụng sử dụng kỹ thuật **Callback Functions** để các module liên lạc với nhau mà không bị phụ thuộc vòng (Circular Dependency):

* `Main` khởi tạo `Controls` và truyền vào một hàm (callback).
* Khi người dùng tương tác với `Controls`, nó thực thi hàm đó để báo cho `Main` biết cần cập nhật ảnh.
* `CropTool` nhận dữ liệu từ `Main` thông qua một hàm trung gian (`get_crop_data`) để đảm bảo nó luôn lấy được giá trị `zoom_factor` mới nhất tại thời điểm cắt.
