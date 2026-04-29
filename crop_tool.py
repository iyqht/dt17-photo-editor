from tkinter import messagebox


class CropTool:
    def __init__(self, canvas, get_img_info_func, update_img_func):
        self.canvas = canvas
        self.img_info = get_img_info_func
        self.update_img = update_img_func

        self.rect_id = None
        self.overlay_ids = []
        self.start_x = 0
        self.start_y = 0

    def activate(self, on_exit_callback):
        self.on_exit = on_exit_callback
        self.canvas.config(cursor="cross")
        self.canvas.bind("<Button-1>", self.drag_start)
        self.canvas.bind("<B1-Motion>", self.drag_motion)
        self.canvas.bind("<ButtonRelease-1>", self.drag_end)

    def drag_start(self, event):
        self.start_x, self.start_y = event.x, event.y
        self.clear()
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
        x1, y1 = self.start_x, self.start_y
        x2, y2 = event.x, event.y
        self.canvas.coords(self.rect_id, x1, y1, x2, y2)
        self.draw_overlays(x1, y1, x2, y2)

    def draw_overlays(self, x1, y1, x2, y2):
        for oid in self.overlay_ids:
            self.canvas.delete(oid)
        self.overlay_ids = []
        w, h = self.canvas.winfo_width(), self.canvas.winfo_height()
        xmin, xmax = min(x1, x2), max(x1, x2)
        ymin, ymax = min(y1, y2), max(y1, y2)

        params = {"fill": "black", "stipple": "gray50", "outline": ""}
        self.overlay_ids.append(
            self.canvas.create_rectangle(0, 0, w, ymin, **params)
        )  # top
        self.overlay_ids.append(
            self.canvas.create_rectangle(0, ymax, w, h, **params)
        )  # bottom
        self.overlay_ids.append(
            self.canvas.create_rectangle(0, ymin, xmin, ymax, **params)
        )  # left
        self.overlay_ids.append(
            self.canvas.create_rectangle(xmax, ymin, w, ymax, **params)
        )  # right

    def drag_end(self, event):
        if messagebox.askyesno("Xác nhận", "Bạn có muốn cắt vùng đã chọn?"):
            self.execute_crop()
        self.deactivate()

    def execute_crop(self):
        orig_img, zoom_factor, img_id = self.img_info()
        if not orig_img or not self.rect_id:
            return
        x1, y1, x2, y2 = self.canvas.coords(self.rect_id)

        img_coords = self.canvas.coords(img_id)
        img_center_x, img_center_y = img_coords[0], img_coords[1]

        w = orig_img.width * zoom_factor
        h = orig_img.height * zoom_factor

        img_left = img_center_x - w / 2
        img_top = img_center_y - h / 2

        left = (min(x1, x2) - img_left) / zoom_factor
        top = (min(y1, y2) - img_top) / zoom_factor
        right = (max(x1, x2) - img_left) / zoom_factor
        bottom = (max(y1, y2) - img_top) / zoom_factor

        cropped_img = orig_img.crop((left, top, right, bottom))
        self.update_img(cropped_img)

    def clear(self):
        if self.rect_id:
            self.canvas.delete(self.rect_id)
        for oid in self.overlay_ids:
            self.canvas.delete(oid)
        self.rect_id = None
        self.overlay_ids = []

    def deactivate(self):
        self.clear()
        self.canvas.config(cursor="hand2")
        if self.on_exit:
            self.on_exit()
