"""
Line Counter Module for PC Testing with Color Counting Support
Xử lý logic cắt qua vạch ảo nằm ngang và thống kê phân loại số lượng theo từng màu sắc.
"""

class LineCounter:
    def __init__(self, line_y=240, buffer_zone=25, direction="down", tracked_colors=None):
        self.line_y = line_y
        self.buffer_zone = buffer_zone
        self.direction = direction.lower()

        self.total_caps = 0
        self.counted_ids = set()
        self.last_counted_time = 0.0
        self.just_counted_event = False
        self.last_counted_color = "unknown"

        # Bảng thống kê số lượng theo từng màu sắc
        self.counts_by_color = {
            "red": 0,
            "blue": 0,
            "green": 0,
            "yellow": 0,
            "white": 0,
            "multicolor": 0,
            "unknown": 0
        }
        if tracked_colors:
            for c in tracked_colors:
                if c not in self.counts_by_color:
                    self.counts_by_color[c] = 0

    def update(self, objects_dict, tracker, object_colors=None):
        """
        Kiểm tra danh sách objects cắt vạch và cập nhật số lượng theo màu.
        object_colors: dict {obj_id: (color_name, confidence)}
        """
        self.just_counted_event = False
        active_ids = set(objects_dict.keys())
        self.counted_ids = self.counted_ids.intersection(active_ids)

        if object_colors is None:
            object_colors = {}

        for obj_id, current_centroid in objects_dict.items():
            if obj_id in self.counted_ids:
                continue

            trajectory = tracker.get_trajectory(obj_id)
            if len(trajectory) < 2:
                continue

            prev_cx, prev_cy = trajectory[-2]
            curr_cx, curr_cy = current_centroid

            crossed = False
            if self.direction == "down":
                if prev_cy <= self.line_y and curr_cy > self.line_y:
                    crossed = True
                elif prev_cy < self.line_y and (curr_cy >= self.line_y - self.buffer_zone and curr_cy > prev_cy):
                    if prev_cy <= self.line_y < curr_cy:
                        crossed = True
            elif self.direction == "up":
                if prev_cy >= self.line_y and curr_cy < self.line_y:
                    crossed = True

            if crossed:
                self.total_caps += 1
                self.counted_ids.add(obj_id)
                self.just_counted_event = True

                # Xác định màu sắc nắp chai vừa cắt vạch
                color_info = object_colors.get(obj_id, ("unknown", 0.0))
                color_name = color_info[0] if isinstance(color_info, (list, tuple)) else color_info
                conf_color = color_info[1] if isinstance(color_info, (list, tuple)) and len(color_info) > 1 else 0.0

                self.last_counted_color = color_name
                self.counts_by_color[color_name] = self.counts_by_color.get(color_name, 0) + 1

                if color_name == "unknown":
                    print(f"[LineCounter PC] >> NẮP CHAI #{self.total_caps} [MÀU: UNKNOWN COLOR] CẮT VẠCH! (ID: {obj_id})")
                else:
                    print(f"[LineCounter PC] >> NẮP CHAI #{self.total_caps} [MÀU: {color_name.upper()} ({int(conf_color*100)}%)] CẮT VẠCH! (ID: {obj_id})")

        return self.total_caps, self.counts_by_color, self.just_counted_event

    def reset(self):
        self.total_caps = 0
        self.counted_ids.clear()
        self.just_counted_event = False
        self.last_counted_color = "unknown"
        for k in self.counts_by_color:
            self.counts_by_color[k] = 0
        print("[LineCounter PC] Đã reset bộ đếm tổng và bộ đếm màu về 0.")
