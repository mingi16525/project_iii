"""
Color Analyzer Module for Bottle Cap Classification
Nhận diện màu sắc của nắp chai dựa trên không gian màu HSV và bộ lọc vùng lõi (Center ROI).
Nếu màu sắc không nằm trong danh mục màu đã huấn luyện/cấu hình, gán nhãn 'unknown'.
"""

import cv2
import numpy as np


class ColorAnalyzer:
    def __init__(self, target_colors=None, confidence_threshold=0.70):
        """
        target_colors: Danh sách các màu đã được định nghĩa/huấn luyện.
        confidence_threshold: Ngưỡng tỷ lệ điểm ảnh hợp lệ để xác nhận màu (mặc định 70%).
        """
        self.confidence_threshold = confidence_threshold

        # Bảng dải màu chuẩn trong không gian HSV (Hue: 0-180, Sat: 0-255, Val: 0-255)
        # Các dải màu được tối ưu cho bề mặt nắp chai nhựa/kim loại
        self.color_ranges = {
            "red": [
                # Đỏ có 2 dải vì Hue bao quanh 0 và 180
                (np.array([0, 70, 50]), np.array([10, 255, 255])),
                (np.array([170, 70, 50]), np.array([180, 255, 255]))
            ],
            "blue": [
                (np.array([100, 70, 50]), np.array([130, 255, 255]))
            ],
            "green": [
                (np.array([35, 70, 50]), np.array([85, 255, 255]))
            ],
            "yellow": [
                (np.array([20, 70, 80]), np.array([35, 255, 255]))
            ],
            "white": [
                # Trắng: Saturation thấp, Value cao
                (np.array([0, 0, 160]), np.array([180, 55, 255]))
            ]
        }

        # Nếu người dùng chỉ định một tập màu cụ thể đã train
        if target_colors:
            self.active_colors = [c.lower() for c in target_colors]
        else:
            self.active_colors = list(self.color_ranges.keys())

    def classify_color(self, frame, box):
        """
        Phân loại màu của nắp chai trong vùng Bounding Box [x1, y1, x2, y2].
        Trả về (color_name, confidence)
        Nếu không đạt ngưỡng hoặc là màu lạ -> ('unknown', conf)
        """
        x1, y1, x2, y2 = box[:4]
        h_frame, w_frame = frame.shape[:2]

        x1 = max(0, int(x1))
        y1 = max(0, int(y1))
        x2 = min(w_frame, int(x2))
        y2 = min(h_frame, int(y2))

        if x2 - x1 < 10 or y2 - y1 < 10:
            return "unknown", 0.0

        # Cắt vùng nắp chai (Crop ROI)
        roi = frame[y1:y2, x1:x2]

        # Lấy vùng tâm tròn 50% ở giữa nắp chai để tránh viền bóng hoặc nền băng tải
        roi_h, roi_w = roi.shape[:2]
        pad_x = int(roi_w * 0.25)
        pad_y = int(roi_h * 0.25)
        center_roi = roi[pad_y:roi_h - pad_y, pad_x:roi_w - pad_x]

        if center_roi.size == 0:
            center_roi = roi

        # Chuyển sang không gian màu HSV
        hsv_roi = cv2.cvtColor(center_roi, cv2.COLOR_BGR2HSV)
        total_pixels = center_roi.shape[0] * center_roi.shape[1]

        best_color = "unknown"
        max_ratio = 0.0

        # Tính tỷ lệ diện tích cho từng màu trong danh mục
        color_ratios = {}
        for color_name in self.active_colors:
            if color_name not in self.color_ranges:
                continue

            ranges = self.color_ranges[color_name]
            combined_mask = np.zeros(hsv_roi.shape[:2], dtype=np.uint8)

            for lower, upper in ranges:
                mask = cv2.inRange(hsv_roi, lower, upper)
                combined_mask = cv2.bitwise_or(combined_mask, mask)

            match_count = cv2.countNonZero(combined_mask)
            ratio = match_count / float(total_pixels) if total_pixels > 0 else 0.0
            if ratio >= 0.05:  # Chỉ ghi nhận các màu có độ phủ từ 5% trở lên
                color_ratios[color_name] = ratio

        if not color_ratios:
            return "unknown", 0.0

        # Sắp xếp các màu theo tỷ lệ diện tích giảm dần
        sorted_colors = sorted(color_ratios.items(), key=lambda x: x[1], reverse=True)
        c1, r1 = sorted_colors[0]
        c2, r2 = sorted_colors[1] if len(sorted_colors) > 1 else ("", 0.0)
        c3, r3 = sorted_colors[2] if len(sorted_colors) > 2 else ("", 0.0)

        # 1. TRƯỜNG HỢP ĐƠN SẮC VƯỢT TRỘI (Single Dominant Color)
        # Khi màu top 1 đạt ngưỡng tin cậy (mặc định >= 70%) hoặc chiếm ưu thế áp đảo màu thứ 2
        if r1 >= self.confidence_threshold or (r1 >= 0.55 and (r1 - r2) >= 0.25):
            return c1, round(r1, 2)

        # 2. TRƯỜNG HỢP ĐA MÀU (Multicolor)
        # Xảy ra khi có từ 3 màu trở lên và 3 màu top đầu xấp xỉ ngang nhau (ví dụ mỗi màu ~ 30-33%)
        # Không có màu nào chiếm ưu thế tuyệt đối (r1 < 0.45 và khoảng cách top 1 với top 3 <= 0.12)
        if len(sorted_colors) >= 3 and r3 >= 0.15 and (r1 - r3) <= 0.12 and r1 < 0.45:
            multi_conf = min(1.0, r1 + r2 + r3)
            return "multicolor", round(multi_conf, 2)

        # 3. TRƯỜNG HỢP PHỐI 2 MÀU (Dual-Color / Bicolor - ví dụ Coca đỏ-trắng: red_white)
        # Cả 2 màu đều có độ phủ đáng kể (r1 >= 25%, r2 >= 20%), tổng 2 màu >= 50%
        # và màu thứ 2 cách biệt rõ ràng so với màu thứ 3 để loại trừ hòa 3 màu
        if r1 >= 0.25 and r2 >= 0.20 and (r1 + r2) >= 0.50 and (r2 - r3) >= 0.08:
            dual_label = f"{c1}_{c2}"
            dual_conf = min(1.0, r1 + r2)
            return dual_label, round(dual_conf, 2)

        # 4. Nếu màu top 1 vẫn chiếm tỷ lệ tương đối đáng kể
        if r1 >= 0.45 and (r1 - r2) >= 0.15:
            return c1, round(r1, 2)

        # 5. Các trường hợp màu lạ hoặc không đồng nhất
        if r1 >= 0.30:
            return "unknown", round(r1, 2)
        return "unknown", 0.0
