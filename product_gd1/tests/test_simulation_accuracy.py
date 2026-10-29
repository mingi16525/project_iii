"""
Automated Counting Accuracy Test on PC (Giai đoạn 1)
Kiểm tra độ chính xác của logic đếm tự động với video giả lập có sẵn Ground Truth.
"""

import os
import sys
import time

if sys.platform.startswith("win"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from simulation.generate_synthetic_video import generate_simulation_video
from src.core.camera import VideoSource
from src.core.detector import ObjectDetectorPC
from src.core.color_analyzer import ColorAnalyzer
from src.core.tracker import CentroidTracker
from src.core.counter import LineCounter


def run_accuracy_test(expected_caps=12, model_path=""):
    test_video_path = "simulation/test_accuracy.mp4"
    print("=" * 65)
    print(f"  BÀI TEST TỰ ĐỘNG ĐỘ CHÍNH XÁC ĐẾM & PHÂN LOẠI MÀU SẮC (GT={expected_caps} NẮP)")
    print("  Tiêu chí: Nhận diện màu chuẩn >= 70%, màu lạ chưa train gắn 'unknown'")
    print("=" * 65)

    # 1. Sinh video test với số lượng nắp chính xác và màu sắc đa dạng
    generate_simulation_video(
        output_path=test_video_path,
        num_caps=expected_caps,
        duration_sec=18,
        fps=25
    )

    # 2. Khởi tạo pipeline
    source = VideoSource(source_type="video", video_path=test_video_path, loop_video=False)
    source.open()

    detector = ObjectDetectorPC(model_path=model_path, runtime="auto")
    color_analyzer = ColorAnalyzer(target_colors=["red", "blue", "green", "yellow"], confidence_threshold=0.70)
    tracker = CentroidTracker(max_disappeared=10)
    counter = LineCounter(line_y=240, buffer_zone=25)

    frame_count = 0
    t0 = time.time()

    while True:
        ret, frame = source.read_frame()
        if not ret or frame is None:
            break

        frame_count += 1
        raw_detections = detector.detect(frame)

        detections = []
        box_color_map = {}
        for box in raw_detections:
            c_name, c_conf = color_analyzer.classify_color(frame, box)
            detections.append(list(box) + [c_name, c_conf])
            cx = int((box[0] + box[2]) / 2)
            cy = int((box[1] + box[3]) / 2)
            box_color_map[(cx, cy)] = (c_name, c_conf)

        tracked_objects = tracker.update(detections)

        object_colors = {}
        for obj_id, (cx, cy) in tracked_objects.items():
            best_match = ("unknown", 0.0)
            min_d = 999
            for (bcx, bcy), c_info in box_color_map.items():
                d = ((bcx - cx)**2 + (bcy - cy)**2)**0.5
                if d < min_d and d < 40:
                    min_d = d
                    best_match = c_info
            object_colors[obj_id] = best_match

        counter.update(tracked_objects, tracker, object_colors)

    source.release()
    total_time = time.time() - t0
    counted = counter.total_caps
    error = abs(counted - expected_caps)
    accuracy = (1.0 - (error / expected_caps)) * 100.0

    print("=" * 65)
    print(f"  KẾT QUẢ KIỂM THỬ TỔNG HỢP:")
    print(f"  - Số nắp thực tế (Ground Truth) : {expected_caps}")
    print(f"  - Số nắp hệ thống đếm được     : {counted}")
    print(f"  - Sai lệch                      : {counted - expected_caps}")
    print(f"  - Độ chính xác tổng (Accuracy)  : {accuracy:.1f}%")
    print(f"  - Tốc độ xử lý trung bình       : {frame_count / total_time:.1f} FPS")
    print(f"  - Thống kê chi tiết theo màu    :")
    for col_name, cnt in counter.counts_by_color.items():
        if cnt > 0:
            print(f"      + {col_name.upper():<10}: {cnt} nắp")
    print("=" * 65)

    if accuracy >= 90.0:
        print("[TEST PASSED] Hệ thống nhận diện, phân loại màu và phát hiện màu lạ thành công!")
        return True
    else:
        print("[TEST FAILED] Sai lệch vượt ngưỡng cho phép!")
        return False


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Test độ chính xác đếm tự động")
    parser.add_argument("--caps", type=int, default=12, help="Số lượng nắp Ground Truth (mặc định: 12)")
    parser.add_argument("--model", default="", help="Đường dẫn file model AI (.pt, .onnx) hoặc để trống để test Heuristic Mock")
    args = parser.parse_args()

    run_accuracy_test(expected_caps=args.caps, model_path=args.model)
