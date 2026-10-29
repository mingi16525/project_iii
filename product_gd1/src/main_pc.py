"""
Main Test Application on PC (Giai đoạn 1)
Project III - Hệ Thống Edge AI Đếm Nắp Chai Trên Băng Chuyền Mini
"""

import os
import sys
import time
import argparse
import yaml
import cv2

if sys.platform.startswith("win"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.core.camera import VideoSource
from src.core.detector import ObjectDetectorPC
from src.core.tracker import CentroidTracker
from src.core.counter import LineCounter
from src.core.color_analyzer import ColorAnalyzer
from src.comms.mqtt_client import MqttPublisherPC
from src.utils.visualizer import VisualizerPC


def load_config(config_path="config_pc.yaml"):
    if not os.path.exists(config_path):
        return {}
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def main():
    parser = argparse.ArgumentParser(description="Chương trình kiểm thử nhận diện và đếm nắp chai trên PC (GD1)")
    parser.add_argument("--source", default=None,
                        help="Nguồn video: URL stream LAN (http://...:8080/video hoặc rtsp://...), webcam index (0), hoặc đường dẫn file video")
    parser.add_argument("--model", default=None,
                        help="Đường dẫn file mô hình (.pt hoặc .onnx)")
    parser.add_argument("--conf", type=float, default=None,
                        help="Ngưỡng tin cậy nhận diện (mặc định theo config: 0.50)")
    parser.add_argument("--no-mqtt", action="store_true",
                        help="Tắt kết nối MQTT khi chạy thử độc lập")
    args = parser.parse_args()

    print("=" * 65)
    print("  CHƯƠNG TRÌNH KIỂM THỬ TRÊN MÁY TÍNH - GIAI ĐOẠN 1 (PC DEMO)")
    print("  Hỗ trợ phân biệt màu sắc (>=70%) & gắn nhãn Unknown Color")
    print("=" * 65)

    cfg = load_config()
    inp_cfg = cfg.get("input", {})
    dev_cfg = cfg.get("device", {})
    model_cfg = cfg.get("model", {})
    counter_cfg = cfg.get("counter", {})
    color_cfg = cfg.get("color", {})
    mqtt_cfg = cfg.get("mqtt", {})
    disp_cfg = cfg.get("display", {})

    # 1. Khởi tạo nguồn video
    source_type = inp_cfg.get("type", "video")
    stream_url = inp_cfg.get("stream_url", "")
    webcam_index = inp_cfg.get("webcam_index", 0)
    video_file = inp_cfg.get("video_file", "simulation/conveyor_simulation.mp4")

    # Ghi đè nếu có tham số từ dòng lệnh
    if args.source:
        src_val = args.source.strip()
        if src_val.startswith("http://") or src_val.startswith("https://") or src_val.startswith("rtsp://"):
            source_type = "stream"
            stream_url = src_val
        elif src_val.isdigit():
            source_type = "webcam"
            webcam_index = int(src_val)
        else:
            source_type = "video"
            video_file = src_val

    # Kiểm tra nếu chọn video mà chưa có file thì tự động sinh video mẫu
    if source_type == "video" and not os.path.exists(video_file):
        print(f"[Notice] Chưa có file video '{video_file}', tự động sinh video mô phỏng...")
        from simulation.generate_synthetic_video import generate_simulation_video
        generate_simulation_video(video_file)

    video_source = VideoSource(
        source_type=source_type,
        webcam_index=webcam_index,
        video_path=video_file,
        stream_url=stream_url,
        width=inp_cfg.get("width", 640),
        height=inp_cfg.get("height", 480),
        fps=inp_cfg.get("fps", 25),
        loop_video=True
    )

    if not video_source.open():
        print("[Fatal Error] Không thể mở nguồn video đầu vào.")
        return

    # 2. Khởi tạo bộ nhận diện AI và bộ phân tích màu sắc
    model_path = args.model or model_cfg.get("path", "models/yolov8n_cap.onnx")
    if not os.path.exists(model_path):
        pt_path = os.path.join("models", "yolov8n_cap.pt")
        if os.path.exists(pt_path):
            model_path = pt_path

    conf_thresh = args.conf if args.conf is not None else model_cfg.get("confidence_threshold", 0.50)

    detector = ObjectDetectorPC(
        model_path=model_path,
        input_size=tuple(model_cfg.get("input_size", [320, 320])),
        confidence_threshold=conf_thresh,
        iou_threshold=model_cfg.get("iou_threshold", 0.45),
        runtime=model_cfg.get("runtime", "auto")
    )

    color_analyzer = ColorAnalyzer(
        target_colors=color_cfg.get("trained_colors", ["red", "blue", "green", "yellow", "white"]),
        confidence_threshold=color_cfg.get("confidence_threshold", 0.70)
    )

    # 3. Khởi tạo Tracker & Counter
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

    visualizer = VisualizerPC(
        line_y=counter_cfg.get("line_y", 240),
        buffer_zone=counter_cfg.get("buffer_zone", 25)
    )

    # 4. MQTT Publisher
    mqtt_publisher = None
    if not args.no_mqtt and mqtt_cfg.get("enabled", True):
        mqtt_publisher = MqttPublisherPC(
            device_id=dev_cfg.get("id", "pc_test_workstation"),
            broker=mqtt_cfg.get("broker", "localhost"),
            port=mqtt_cfg.get("port", 1883),
            topic=mqtt_cfg.get("topic", "lab/conveyor/counter")
        )
        mqtt_publisher.start()

    window_name = disp_cfg.get("window_name", "PC Test Environment")
    paused = False
    frame_count = 0
    fps_start_time = time.time()
    current_fps = 0.0

    print("\n[Điều khiển]:")
    print("  - [Q]: Thoát chương trình")
    print("  - [R]: Reset bộ đếm về 0")
    print("  - [SPACE]: Tạm dừng / Tiếp tục video")
    print("=" * 65)

    try:
        while True:
            if not paused:
                ret, frame = video_source.read_frame()
                if not ret or frame is None:
                    time.sleep(0.02)
                    continue

                frame_count += 1
                if frame_count % 10 == 0:
                    elapsed = time.time() - fps_start_time
                    current_fps = 10.0 / elapsed if elapsed > 0 else 0.0
                    fps_start_time = time.time()

                # Nhận diện nắp chai
                raw_detections = detector.detect(frame)

                # Phân loại màu sắc cho từng nắp chai
                detections = []
                box_color_map = {}
                for box in raw_detections:
                    c_name, c_conf = color_analyzer.classify_color(frame, box)
                    enriched_box = list(box) + [c_name, c_conf]
                    detections.append(enriched_box)
                    # Ghi nhận tọa độ tâm box để map với tracker
                    cx = int((box[0] + box[2]) / 2)
                    cy = int((box[1] + box[3]) / 2)
                    box_color_map[(cx, cy)] = (c_name, c_conf)

                # Cập nhật Tracker
                tracked_objects = tracker.update(detections)

                # Ánh xạ màu sắc cho từng Object ID đang theo dõi
                object_colors = {}
                for obj_id, (cx, cy) in tracked_objects.items():
                    # Tìm box gần nhất với tâm obj_id
                    best_match = ("unknown", 0.0)
                    min_d = 999
                    for (bcx, bcy), c_info in box_color_map.items():
                        d = ((bcx - cx)**2 + (bcy - cy)**2)**0.5
                        if d < min_d and d < 40:
                            min_d = d
                            best_match = c_info
                    object_colors[obj_id] = best_match

                # Logic cắt vạch ảo và thống kê số lượng theo màu
                total_caps, counts_by_color, just_counted = counter.update(
                    tracked_objects, tracker, object_colors
                )

                # Gửi MQTT nếu có sự kiện
                if just_counted and mqtt_publisher:
                    mqtt_publisher.publish_count(
                        total_caps, current_fps, status="running",
                        counts_by_color=counts_by_color
                    )

                # Vẽ giao diện trực quan
                is_mqtt_online = mqtt_publisher.is_connected if mqtt_publisher else False
                annotated = visualizer.render(
                    frame, detections, tracked_objects, total_caps,
                    counts_by_color, current_fps,
                    source_type=source_type.upper(),
                    just_counted=just_counted,
                    mqtt_connected=is_mqtt_online,
                    object_colors=object_colors
                )

                cv2.imshow(window_name, annotated)

            key = cv2.waitKey(20) & 0xFF
            if key == ord('q'):
                break
            elif key == ord('r'):
                counter.reset()
                if mqtt_publisher:
                    mqtt_publisher.publish_count(0, current_fps, status="reset")
            elif key == ord(' '):
                paused = not paused
                print(f"[State] {'TẠM DỪNG' if paused else 'TIẾP TỤC'}")

    finally:
        video_source.release()
        if mqtt_publisher:
            mqtt_publisher.stop()
        cv2.destroyAllWindows()
        print(f"\n[Kết thúc] Tổng số nắp đếm được: {counter.total_caps} nắp.")


if __name__ == "__main__":
    main()
