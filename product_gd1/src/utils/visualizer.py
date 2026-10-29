"""
Visualizer Module for PC Testing with Color Counting HUD
Vẽ giao diện hiển thị Bounding Box, nhãn màu sắc, và bảng thống kê chi tiết từng màu.
"""

import cv2
import numpy as np


class VisualizerPC:
    def __init__(self, line_y=240, buffer_zone=25):
        self.line_y = line_y
        self.buffer_zone = buffer_zone
        self.flash_counter = 0

        # Màu sắc hiển thị Bounding Box tương ứng với nhãn
        self.box_colors = {
            "red": (0, 0, 255),
            "blue": (255, 100, 0),
            "green": (0, 220, 0),
            "yellow": (0, 220, 240),
            "white": (230, 230, 230),
            "multicolor": (0, 165, 255),  # Màu cam rực rỡ cho đa sắc
            "unknown": (255, 0, 255)  # Màu tím hồng cảnh báo cho màu lạ
        }

    def get_color_bgr(self, color_name):
        name = str(color_name).lower()
        if name in self.box_colors:
            return self.box_colors[name]
        # Nếu là màu phối ví dụ red_white -> lấy màu thành phần chủ đạo đầu tiên
        main_col = name.split('_')[0]
        if main_col in self.box_colors:
            return self.box_colors[main_col]
        return (0, 165, 255)

    def render(self, frame, detections, tracked_objects, total_caps, counts_by_color, fps,
               source_type="VIDEO", just_counted=False, mqtt_connected=False, object_colors=None):
        annotated = frame.copy()
        h, w = annotated.shape[:2]

        if just_counted:
            self.flash_counter = 6

        if object_colors is None:
            object_colors = {}

        # 1. Vẽ vùng đệm (Buffer Zone)
        overlay = annotated.copy()
        cv2.rectangle(overlay, (0, self.line_y - self.buffer_zone),
                      (w, self.line_y + self.buffer_zone), (60, 60, 60), -1)
        cv2.addWeighted(overlay, 0.25, annotated, 0.75, 0, annotated)

        # 2. Vẽ vạch ảo (Counting Line)
        if self.flash_counter > 0:
            line_color = (0, 255, 0)
            line_thickness = 3
            self.flash_counter -= 1
        else:
            line_color = (0, 0, 255)
            line_thickness = 2

        cv2.line(annotated, (0, self.line_y), (w, self.line_y), line_color, line_thickness)
        cv2.putText(annotated, f"COUNTING LINE (Y={self.line_y})", (15, self.line_y - 8),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, line_color, 1, cv2.LINE_AA)

        # 3. Vẽ Bounding Boxes kèm nhãn màu sắc
        for box in detections:
            x1, y1, x2, y2, conf = box[:5]
            color_label = box[6] if len(box) > 6 else "cap"
            color_conf = box[7] if len(box) > 7 else 0.0

            draw_color = self.get_color_bgr(color_label)
            cv2.rectangle(annotated, (x1, y1), (x2, y2), draw_color, 2)

            if color_label == "unknown":
                tag = f"UNKNOWN COLOR"
            else:
                tag = f"{color_label.upper()} {int(color_conf * 100)}%"

            # Nền chữ nhãn
            (tw, th), _ = cv2.getTextSize(tag, cv2.FONT_HERSHEY_SIMPLEX, 0.45, 1)
            cv2.rectangle(annotated, (x1, max(15, y1 - 18)), (x1 + tw + 4, max(15, y1)), (20, 20, 20), -1)
            cv2.putText(annotated, tag, (x1 + 2, max(15, y1 - 4)),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.45, draw_color, 1, cv2.LINE_AA)

        # 4. Vẽ Centroid & ID theo dõi
        for obj_id, centroid in tracked_objects.items():
            cx, cy = centroid
            c_info = object_colors.get(obj_id, ("unknown", 0.0))
            c_name = c_info[0] if isinstance(c_info, (list, tuple)) else c_info
            draw_color = self.get_color_bgr(c_name)

            cv2.circle(annotated, (cx, cy), 5, draw_color, -1)
            cv2.putText(annotated, f"ID:{obj_id}", (cx + 8, cy - 8),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.45, draw_color, 2, cv2.LINE_AA)

        # 5. Bảng OSD chính (Góc trên bên trái)
        cv2.rectangle(annotated, (10, 10), (250, 115), (20, 20, 20), -1)
        cv2.rectangle(annotated, (10, 10), (250, 115), (80, 80, 80), 1)

        cv2.putText(annotated, f"TOTAL: {total_caps}", (20, 42),
                    cv2.FONT_HERSHEY_DUPLEX, 1.0, (0, 255, 255), 2, cv2.LINE_AA)
        cv2.putText(annotated, f"FPS: {fps:.1f} | SRC: {source_type}", (20, 72),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.55, (200, 200, 200), 1, cv2.LINE_AA)

        mqtt_text = "MQTT: ONLINE" if mqtt_connected else "MQTT: STANDALONE"
        mqtt_col = (0, 255, 0) if mqtt_connected else (150, 150, 150)
        cv2.putText(annotated, mqtt_text, (20, 98),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.48, mqtt_col, 1, cv2.LINE_AA)

        # 6. Bảng thống kê phân loại từng màu (Góc trên bên phải)
        # Tự động hiển thị các màu cơ bản và các màu phối hợp (red_white, multicolor...) có số lượng > 0
        base_colors = ["red", "blue", "green", "yellow", "white", "multicolor", "unknown"]
        display_colors = [c for c in base_colors if counts_by_color.get(c, 0) > 0 or c in ["red", "blue", "green", "unknown"]]
        for c, count in counts_by_color.items():
            if c not in display_colors and count > 0:
                display_colors.append(c)

        panel_w = 220
        panel_h = 42 + len(display_colors) * 20
        panel_x = w - panel_w - 10
        cv2.rectangle(annotated, (panel_x, 10), (w - 10, 10 + panel_h), (20, 20, 20), -1)
        cv2.rectangle(annotated, (panel_x, 10), (w - 10, 10 + panel_h), (80, 80, 80), 1)

        cv2.putText(annotated, "COLOR STATS (HSV/AI)", (panel_x + 10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.48, (255, 255, 255), 1, cv2.LINE_AA)
        cv2.line(annotated, (panel_x + 10, 36), (w - 20, 36), (100, 100, 100), 1)

        y_offset = 55
        for c in display_colors:
            cnt = counts_by_color.get(c, 0)
            col = self.get_color_bgr(c)
            name_display = "UNKNOWN" if c == "unknown" else c.upper()
            cv2.putText(annotated, f"{name_display:<10}: {cnt:>2}", (panel_x + 12, y_offset),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.46, col, 1, cv2.LINE_AA)
            y_offset += 20

        return annotated
