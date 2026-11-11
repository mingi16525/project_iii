"""
Benchmark Script cho Bo Mạch Biên (chạy TRỰC TIẾP trên bo mạch qua SSH)
Đo thời gian thực tế của từng khâu trong pipeline để biết nút cổ chai nằm ở đâu,
thay vì suy đoán từ số đo trên máy tính x86.

Cách dùng (tại ~/edge_counter trên bo mạch):
    python3 tools/benchmark_board.py
    python3 tools/benchmark_board.py --models models/yolov8n_cap.onnx models/yolov8n_cap_224.onnx
    python3 tools/benchmark_board.py --camera /dev/video2 --skip-models
"""

import os
import sys
import time
import argparse

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import cv2
import numpy as np

from src.core.camera import CameraReader
from src.core.detector import ObjectDetector
from src.core.color_analyzer import ColorAnalyzer
from src.core.tracker import CentroidTracker
from src.core.counter import LineCounter


def make_test_frame(width=640, height=480, num_caps=5):
    """Dựng 1 khung hình băng chuyền giả lập có vài nắp chai màu khác nhau."""
    frame = np.full((height, width, 3), 45, dtype=np.uint8)
    cv2.rectangle(frame, (140, 0), (500, height), (70, 70, 70), -1)
    palette = [(40, 40, 220), (20, 130, 245), (60, 190, 60), (220, 90, 40), (235, 235, 235)]
    boxes = []
    for i in range(num_caps):
        cx = 180 + (i % 4) * 90
        cy = 70 + i * 70
        cv2.circle(frame, (cx, cy), 28, palette[i % len(palette)], -1)
        cv2.circle(frame, (cx, cy), 28, (30, 30, 30), 2)
        boxes.append([cx - 28, cy - 28, cx + 28, cy + 28, 0.9, 0])
    return frame, boxes


def bench(fn, reps, warmup=3):
    for _ in range(warmup):
        fn()
    t0 = time.perf_counter()
    for _ in range(reps):
        fn()
    return (time.perf_counter() - t0) / reps * 1000.0


def read_cpu_temp():
    """Đọc nhiệt độ CPU nếu hệ thống có cung cấp (để phát hiện tụt tần số do nóng)."""
    for path in ("/sys/class/thermal/thermal_zone0/temp",
                 "/sys/class/hwmon/hwmon0/temp1_input"):
        try:
            with open(path) as f:
                return int(f.read().strip()) / 1000.0
        except Exception:
            continue
    return None


def benchmark_models(model_paths, input_sizes, reps):
    frame, _ = make_test_frame()
    print("=" * 72)
    print("  1. SUY LUẬN AI (ObjectDetector.detect: tiền xử lý + suy luận + giải mã + NMS)")
    print("=" * 72)
    results = []
    for path in model_paths:
        if not os.path.exists(path):
            print(f"  [Bỏ qua] Không tìm thấy: {path}")
            continue
        for size in input_sizes:
            det = ObjectDetector(model_path=path, input_size=(size, size), runtime="auto")
            if det.is_mock_mode:
                print(f"  [Bỏ qua] {path} không nạp được (đang ở Mock Mode)")
                break
            try:
                n_box = len(det.detect(frame))
            except Exception as e:
                # Kích thước config không khớp mô hình ONNX (xuất với dynamic=False)
                print(f"  [Bỏ qua] {os.path.basename(path)} @ {size}: {str(e)[:70]}")
                continue
            ms = bench(lambda: det.detect(frame), reps)
            print(f"  {os.path.basename(path):<28} @ {size:>3}px : {ms:8.1f} ms/frame "
                  f"({1000.0/ms:5.1f} FPS thuần suy luận, {n_box} box)")
            results.append((os.path.basename(path), size, ms))
    if len(results) >= 2:
        base = results[0]
        print()
        for name, size, ms in results[1:]:
            print(f"  => {name} @ {size}px nhanh hơn {base[0]} @ {base[1]}px: {base[2]/ms:.2f}x")
    return results


def benchmark_pipeline(model_path, input_size, reps):
    """Đo các khâu còn lại ngoài suy luận: phân tích màu, tracking, đếm vạch."""
    frame, boxes = make_test_frame()
    print()
    print("=" * 72)
    print("  2. CÁC KHÂU CÒN LẠI (ngoài suy luận AI)")
    print("=" * 72)

    ca = ColorAnalyzer()
    tr = CentroidTracker(max_disappeared=10)
    cnt = LineCounter(line_y=240, buffer_zone=25)

    t_color = bench(lambda: [ca.classify_color(frame, b) for b in boxes], reps)
    dets = [list(b) + list(ca.classify_color(frame, b)) for b in boxes]
    t_track = bench(lambda: tr.update(dets), reps)
    objs = tr.update(dets)
    t_count = bench(lambda: cnt.update(objs, tr, {}), reps)

    print(f"  Phân tích màu ({len(boxes)} nắp, 12 màu) : {t_color:8.2f} ms")
    print(f"  Centroid tracking                      : {t_track:8.2f} ms")
    print(f"  Đếm cắt vạch                           : {t_count:8.2f} ms")
    print(f"  => Tổng phần không phải AI             : {t_color + t_track + t_count:8.2f} ms")
    return t_color + t_track + t_count


def project_fps(t_infer_ms, t_other_ms):
    print()
    print("=" * 72)
    print("  3. FPS DỰ KIẾN THEO detect_interval")
    print("=" * 72)
    print("  (nắp không được dịch quá ~30px giữa 2 lần suy luận, nếu không sẽ đếm hụt)")
    print()
    print(f"  {'detect_interval':<18}{'ms/frame':>12}{'FPS':>10}")
    for n in (1, 2, 3, 4, 5):
        ms = t_infer_ms / n + t_other_ms
        print(f"  {n:<18}{ms:>12.1f}{1000.0/ms:>10.1f}")


def benchmark_camera(device, width, height, fps, n_frames, slow_work_ms):
    print()
    print("=" * 72)
    print("  4. CAMERA: ĐỌC TUẦN TỰ vs LUỒNG NỀN")
    print("=" * 72)

    for threaded in (False, True):
        cam = CameraReader(source_type="webcam", camera_index=device, width=width,
                           height=height, fps=fps, buffer_size=1,
                           threaded=threaded, fourcc="MJPG")
        if not cam.open():
            print(f"  [Lỗi] Không mở được camera: {device}")
            return

        fourcc_val = int(cam.cap.get(cv2.CAP_PROP_FOURCC))
        fourcc_str = "".join([chr((fourcc_val >> (8 * i)) & 0xFF) for i in range(4)])
        label = "LUỒNG NỀN" if threaded else "TUẦN TỰ"

        # Đọc hết công suất: cho biết camera thực sự cấp bao nhiêu FPS
        t0 = time.perf_counter()
        ok_count = 0
        for _ in range(n_frames):
            ret, _f = cam.read_frame()
            if ret:
                ok_count += 1
        dt = time.perf_counter() - t0
        fps_full = ok_count / dt if dt > 0 else 0.0

        # Mô phỏng tiêu thụ CHẬM như khi suy luận AI: đo thời gian read_frame() tốn bao lâu.
        # Đọc tuần tự mà read_frame() trả về gần như tức thì => đang nhận frame CŨ tồn trong
        # hàng đợi V4L2, tức khung hình đưa vào xử lý bị lạc hậu so với thực tế.
        read_times = []
        for _ in range(12):
            t1 = time.perf_counter()
            ret, _f = cam.read_frame()
            read_times.append((time.perf_counter() - t1) * 1000.0)
            time.sleep(slow_work_ms / 1000.0)
        avg_read = sum(read_times[2:]) / max(1, len(read_times[2:]))

        print(f"  [{label}] FOURCC={fourcc_str} | đọc hết công suất: {fps_full:5.1f} FPS "
              f"({ok_count}/{n_frames} frame)")
        print(f"  [{label}] Khi xử lý mất {slow_work_ms:.0f}ms/frame: read_frame() trung bình "
              f"{avg_read:6.1f} ms, bỏ {cam.dropped_frames} frame")
        cam.release()
        print()


def main():
    ap = argparse.ArgumentParser(description="Đo hiệu năng pipeline trên bo mạch biên")
    ap.add_argument("--models", nargs="*", default=["models/yolov8n_cap.onnx"])
    ap.add_argument("--sizes", nargs="*", type=int, default=[320, 224])
    ap.add_argument("--reps", type=int, default=20)
    ap.add_argument("--camera", default="/dev/video2")
    ap.add_argument("--width", type=int, default=640)
    ap.add_argument("--height", type=int, default=480)
    ap.add_argument("--fps", type=int, default=15)
    ap.add_argument("--frames", type=int, default=60)
    ap.add_argument("--slow-work-ms", type=float, default=150.0)
    ap.add_argument("--skip-models", action="store_true")
    ap.add_argument("--skip-camera", action="store_true")
    args = ap.parse_args()

    temp0 = read_cpu_temp()
    print("=" * 72)
    print("  ĐO HIỆU NĂNG PIPELINE TRÊN BO MẠCH BIÊN")
    print(f"  CPU: {os.cpu_count()} nhân | OpenCV {cv2.__version__}"
          + (f" | Nhiệt độ CPU: {temp0:.1f}°C" if temp0 else ""))
    print("=" * 72)
    print()

    t_infer = None
    t_other = 0.0
    if not args.skip_models:
        res = benchmark_models(args.models, args.sizes, args.reps)
        if res:
            t_infer = res[-1][2]
            t_other = benchmark_pipeline(args.models[-1], res[-1][1], args.reps * 3)
            project_fps(t_infer, t_other)

    if not args.skip_camera:
        benchmark_camera(args.camera, args.width, args.height, args.fps,
                         args.frames, args.slow_work_ms)

    temp1 = read_cpu_temp()
    if temp0 and temp1:
        print(f"Nhiệt độ CPU: {temp0:.1f}°C -> {temp1:.1f}°C "
              f"(tăng nhiều nghĩa là có thể bị tụt tần số khi chạy lâu)")


if __name__ == "__main__":
    main()
