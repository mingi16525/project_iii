"""
Main Application Entrypoint for Edge AI Bottle Cap Counter
Project III - Hệ Thống Edge AI Đếm Nắp Chai Trên Băng Chuyền Mini
Tương thích triển khai bo mạch Arduino Qualcomm Linux & Kiểm thử linh hoạt.
"""

import os
import sys
import time
import signal
import yaml
import cv2

# Import các module lõi từ package src
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.core.camera import CameraReader
from src.core.detector import ObjectDetector
from src.core.tracker import CentroidTracker
from src.core.counter import LineCounter
from src.core.color_analyzer import ColorAnalyzer
from src.comms.mqtt_client import MqttPublisher
from src.utils.visualizer import Visualizer


def load_config(config_path="config/config.yaml"):
    """Nạp file cấu hình YAML."""
    if not os.path.exists(config_path):
        print(f"[Main Warning] Không tìm thấy '{config_path}', sử dụng cấu hình mặc định.")
        return {}
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def main():
    print("=" * 65)
    print("  EDGE AI BOTTLE CAP COUNTER - PROJECT III (LAB & EDGE DEMO)")
    print("  Phân loại & Đếm nắp chai theo màu sắc (>=70%) & Unknown Color")
    print("=" * 65)

    # 1. Đọc cấu hình
    cfg = load_config()

    dev_cfg = cfg.get("device", {})
    cam_cfg = cfg.get("camera", {})
    model_cfg = cfg.get("model", {})
    counter_cfg = cfg.get("counter", {})
    color_cfg = cfg.get("color", {})
    mqtt_cfg = cfg.get("mqtt", {})
    disp_cfg = cfg.get("display", {})

    # 2. Xử lý nguồn video đầu vào (Webcam USB / Stream LAN / Video mô phỏng)
    source_type = cam_cfg.get("type", "webcam").lower()
    video_file = cam_cfg.get("video_file", "simulation/conveyor_simulation.mp4")

    if source_type == "video" and not os.path.exists(video_file):
        print(f"[Notice] Chưa có file video '{video_file}', tự động sinh video mô phỏng...")
        try:
            from simulation.generate_synthetic_video import generate_simulation_video
            generate_simulation_video(video_file)
        except Exception as e:
            print(f"[Warning] Không thể tự động sinh video: {e}")

    camera = CameraReader(
        source_type=source_type,
        camera_index=cam_cfg.get("index", 0),
        video_path=video_file,
        stream_url=cam_cfg.get("stream_url", ""),
        width=cam_cfg.get("width", 640),
        height=cam_cfg.get("height", 480),
        fps=cam_cfg.get("fps", 15),
        buffer_size=cam_cfg.get("buffer_size", 1),
        loop_video=True
    )

    detector = ObjectDetector(
        model_path=model_cfg.get("path", "models/yolov8n_cap.tflite"),
        input_size=tuple(model_cfg.get("input_size", [320, 320])),
        confidence_threshold=model_cfg.get("confidence_threshold", 0.50),
        iou_threshold=model_cfg.get("iou_threshold", 0.45),
        runtime=model_cfg.get("runtime", "auto")
    )

    color_analyzer = ColorAnalyzer(
        target_colors=color_cfg.get("trained_colors", ["red", "blue", "green", "yellow", "white"]),
        confidence_threshold=color_cfg.get("confidence_threshold", 0.70)
    )

    tracker = CentroidTracker(
        max_disappeared=counter_cfg.get("max_disappeared_frames", 10),
        max_distance=60
    )

    counter = LineCounter(
        line_y=counter_cfg.get("line_y", 240),
        buffer_zone=counter_cfg.get("buffer_zone", 25),
        direction=counter_cfg.get("direction", "down"),
        tracked_colors=color_cfg.get("trained_colors")
    )

    visualizer = Visualizer(
        line_y=counter_cfg.get("line_y", 240),
        buffer_zone=counter_cfg.get("buffer_zone", 25)
    )

    # 3. Khởi tạo MQTT Publisher
    mqtt_publisher = None
    if mqtt_cfg.get("enabled", True):
        mqtt_publisher = MqttPublisher(
            device_id=dev_cfg.get("id", "arduino_lab_node"),
            broker=mqtt_cfg.get("broker", "localhost"),
            port=mqtt_cfg.get("port", 1883),
            topic=mqtt_cfg.get("topic", "lab/conveyor/counter"),
            qos=mqtt_cfg.get("qos", 0)
        )
        mqtt_publisher.start()

    # 4. Mở kết nối Camera / Nguồn dữ liệu
    if not camera.open():
        print(f"[Main Fatal Error] Không thể mở nguồn dữ liệu video ({source_type.upper()}). Thoát chương trình.")
        if mqtt_publisher:
            mqtt_publisher.stop()
        sys.exit(1)

    # Đăng ký bắt tín hiệu ngắt an toàn (Ctrl+C)
    running = True

    def signal_handler(sig, frame):
        nonlocal running
        print("\n[Main] Nhận tín hiệu dừng từ người dùng...")
        running = False

    signal.signal(signal.SIGINT, signal_handler)

    print("\n[Main] Hệ thống bắt đầu vận hành! Nhấn 'q' để dừng, 'r' để reset, 'SPACE' để tạm dừng.")
    heartbeat_interval = mqtt_cfg.get("heartbeat_interval", 2.0)
    last_heartbeat_time = time.time()

    frame_count = 0
    fps_start_time = time.time()
    current_fps = 0.0
    paused = False

    show_window = disp_cfg.get("show_window", True)
    window_name = disp_cfg.get("window_name", "Edge AI Bottle Cap Counter")

    try:
        while running:
            if not paused:
                # Bước 1: Đọc frame từ nguồn
                ret, frame = camera.read_frame()
                if not ret or frame is None:
                    time.sleep(0.01)
                    continue

                frame_count += 1
                if frame_count % 10 == 0:
                    elapsed = time.time() - fps_start_time
                    current_fps = 10.0 / elapsed if elapsed > 0 else 0.0
                    fps_start_time = time.time()

                # Bước 2: Suy luận nhận diện AI
                raw_detections = detector.detect(frame)

                # Bước 2b: Phân loại màu sắc cho từng nắp chai
                detections = []
                box_color_map = {}
                for box in raw_detections:
                    c_name, c_conf = color_analyzer.classify_color(frame, box)
                    detections.append(list(box) + [c_name, c_conf])
                    cx = int((box[0] + box[2]) / 2)
                    cy = int((box[1] + box[3]) / 2)
                    box_color_map[(cx, cy)] = (c_name, c_conf)

                # Bước 3: Cập nhật thuật toán Centroid Tracking
                tracked_objects = tracker.update(detections)

                # Ánh xạ màu sắc cho từng ID vật thể
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

                # Bước 4: Kiểm tra logic cắt vạch ảo và thống kê số lượng theo màu
                total_caps, counts_by_color, just_counted = counter.update(
                    tracked_objects, tracker, object_colors
                )

                # Bước 5: Truyền thông MQTT
                now = time.time()
                if mqtt_publisher:
                    if just_counted:
                        mqtt_publisher.publish_count(
                            total_caps, current_fps, status="running",
                            counts_by_color=counts_by_color
                        )
                    elif now - last_heartbeat_time >= heartbeat_interval:
                        mqtt_publisher.publish_count(
                            total_caps, current_fps, status="running",
                            counts_by_color=counts_by_color
                        )
                        last_heartbeat_time = now

                # Bước 6: Hiển thị trực quan GUI (nếu có màn hình)
                if show_window:
                    is_mqtt_online = mqtt_publisher.is_connected if mqtt_publisher else False
                    annotated_frame = visualizer.render(
                        frame, detections, tracked_objects, total_caps,
                        current_fps, counts_by_color=counts_by_color,
                        source_type=source_type.upper(),
                        just_counted=just_counted, mqtt_connected=is_mqtt_online,
                        object_colors=object_colors
                    )

                    cv2.imshow(window_name, annotated_frame)
                else:
                    # Chế độ dòng lệnh Headless (in log mỗi giây)
                    if frame_count % 15 == 0:
                        summary = " ".join([f"{k.upper()}:{v}" for k, v in counts_by_color.items() if v > 0])
                        print(f"[STATUS] Count: {total_caps} ({summary}) | FPS: {current_fps:.1f} | Detections: {len(detections)}")

            if show_window:
                key = cv2.waitKey(20 if not paused else 50) & 0xFF
                if key == ord('q'):
                    print("[Main] Nhận lệnh thoát từ bàn phím.")
                    break
                elif key == ord('r'):
                    counter.reset()
                    if mqtt_publisher:
                        mqtt_publisher.publish_count(0, current_fps, status="reset")
                elif key == ord(' '):
                    paused = not paused
                    print(f"[Main State] {'TẠM DỪNG' if paused else 'TIẾP TỤC'}")

    except Exception as e:
        print(f"[Main Error] Đã xảy ra ngoại lệ: {e}")

    finally:
        print("\n[Main] Đang dọn dẹp và giải phóng tài nguyên...")
        camera.release()
        if mqtt_publisher:
            mqtt_publisher.stop()
        if show_window:
            cv2.destroyAllWindows()
        print(f"[Main] Kết thúc. Tổng số nắp chai: {counter.total_caps} nắp.")


if __name__ == "__main__":
    main()
