"""
Synthetic Video Generator for Bottle Cap Conveyor Simulation
Tự động sinh video mô phỏng băng chuyền và nắp chai trôi qua vạch ảo.
Hỗ trợ tạo nắp chai các màu đã huấn luyện (đỏ, xanh dương, xanh lá, vàng)
và nắp chai màu lạ (tím, xám) để kiểm thử bộ phân loại màu và Unknown Color.
"""

import os
import cv2
import numpy as np


def generate_simulation_video(output_path="simulation/conveyor_simulation.mp4",
                               num_caps=15, width=640, height=480, fps=25, duration_sec=18):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    total_frames = int(fps * duration_sec)

    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

    print(f"[Sim Generator] Đang khởi tạo video mô phỏng: {output_path}")
    print(f"[Sim Generator] Số nắp chai chuẩn (Ground Truth): {num_caps} nắp")
    print(f"[Sim Generator] Độ phân giải: {width}x{height} | {fps} FPS | Thời lượng: {duration_sec}s")

    # Danh sách màu sắc nắp chai: gồm màu chuẩn và màu lạ (purple/gray - chưa train)
    cap_specs = [
        {"bgr": (30, 30, 230), "expected": "red"},      # Đỏ (Đã train)
        {"bgr": (230, 60, 30), "expected": "blue"},     # Xanh dương (Đã train)
        {"bgr": (30, 220, 50), "expected": "green"},    # Xanh lá (Đã train)
        {"bgr": (20, 220, 230), "expected": "yellow"},  # Vàng (Đã train)
        {"bgr": (180, 20, 190), "expected": "unknown"}, # Tím Magenta (Màu LẠ - Chưa train!)
        {"bgr": (30, 30, 230), "expected": "red"},      # Đỏ
        {"bgr": (230, 60, 30), "expected": "blue"},     # Xanh dương
        {"bgr": (120, 120, 120), "expected": "unknown"},# Xám tối (Màu LẠ - Chưa train!)
        {"bgr": (30, 220, 50), "expected": "green"},    # Xanh lá
        {"bgr": (20, 220, 230), "expected": "yellow"},  # Vàng
        {"bgr": (30, 30, 230), "expected": "red"},      # Đỏ
        {"bgr": (230, 60, 30), "expected": "blue"},     # Xanh dương
    ]

    caps = []
    cap_radius = 28
    start_frame_interval = int((total_frames - 120) / num_caps)
    speed_y = 3.2

    for i in range(num_caps):
        spec = cap_specs[i % len(cap_specs)]
        start_f = 40 + i * start_frame_interval
        start_x = 320 + int(np.sin(i * 1.5) * 60)
        caps.append({
            "id": i + 1,
            "x": start_x,
            "y": -cap_radius * 2,
            "start_frame": start_f,
            "color": spec["bgr"],
            "expected_color": spec["expected"],
            "radius": cap_radius
        })

    conveyor_texture_offset = 0

    for f in range(total_frames):
        # 1. Vẽ nền băng chuyền (Conveyor Belt)
        frame = np.full((height, width, 3), 45, dtype=np.uint8)

        # Mặt băng tải chính giữa (chiều rộng từ 140 đến 500)
        cv2.rectangle(frame, (140, 0), (500, height), (70, 70, 70), -1)
        # Thành dẫn hướng 2 bên (Guide rails)
        cv2.rectangle(frame, (130, 0), (140, height), (120, 120, 120), -1)
        cv2.rectangle(frame, (500, 0), (510, height), (120, 120, 120), -1)

        # Các vạch vân nhám chuyển động trên băng tải để tạo cảm giác di chuyển
        conveyor_texture_offset = (conveyor_texture_offset + int(speed_y)) % 40
        for y_line in range(conveyor_texture_offset, height, 40):
            cv2.line(frame, (140, y_line), (500, y_line), (80, 80, 80), 1)

        # 2. Cập nhật vị trí và vẽ các nắp chai
        for cap in caps:
            if f >= cap["start_frame"]:
                cap["y"] += speed_y

                cx = int(cap["x"])
                cy = int(cap["y"])
                r = cap["radius"]

                if -r <= cy <= height + r:
                    # Vẽ bóng đổ mờ
                    cv2.circle(frame, (cx + 3, cy + 3), r, (35, 35, 35), -1)
                    # Vẽ thân nắp chai tròn
                    cv2.circle(frame, (cx, cy), r, cap["color"], -1)
                    # Vẽ viền nắp ngoài
                    cv2.circle(frame, (cx, cy), r, (30, 30, 30), 2)
                    # Vẽ vòng gân tròn bên trong nắp chai
                    cv2.circle(frame, (cx, cy), int(r * 0.65), (20, 20, 20), 1)
                    # Điểm bóng sáng phản quang
                    cv2.circle(frame, (cx - 8, cy - 8), 4, (255, 255, 255), -1)

        # Ghi frame vào video
        out.write(frame)

    out.release()
    print(f"[Sim Generator] Hoàn thành sinh video tại: {output_path}")


if __name__ == "__main__":
    generate_simulation_video()
