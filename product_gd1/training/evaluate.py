"""
Evaluation & Benchmarking Script on PC
Đánh giá độ chính xác nhận diện và đo lường tốc độ FPS của mô hình trên máy tính.
"""

import os
import time
import numpy as np
from ultralytics import YOLO

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
MODELS_DIR = os.path.join(ROOT_DIR, "models")
MODEL_PATH = os.path.join(MODELS_DIR, "yolov8n_cap.pt")
DATASET_YAML = os.path.join(os.path.dirname(__file__), "dataset", "data.yaml")


def main():
    print("=" * 60)
    print("  ĐÁNH GIÁ ĐỘ CHÍNH XÁC VÀ BENCHMARK FPS TRÊN MÁY TÍNH")
    print("=" * 60)

    if not os.path.exists(MODEL_PATH):
        model_to_eval = "yolov8n.pt"
        print(f"[Notice] Không tìm thấy '{MODEL_PATH}', sử dụng mô hình nền '{model_to_eval}' để đo mẫu.")
    else:
        model_to_eval = MODEL_PATH

    model = YOLO(model_to_eval)

    # 1. Đánh giá số liệu mAP nếu có file dataset
    if os.path.exists(DATASET_YAML):
        print("\n[1] Đang tính toán mAP@0.5 và Precision/Recall trên tập validation...")
        try:
            metrics = model.val(data=DATASET_YAML, imgsz=320, batch=8, split="val")
            print(f"  - mAP@50: {metrics.box.map50 * 100:.2f}%")
            print(f"  - mAP@50-95: {metrics.box.map * 100:.2f}%")
            print(f"  - Precision: {metrics.box.p[0] * 100:.2f}%")
            print(f"  - Recall: {metrics.box.r[0] * 100:.2f}%")
        except Exception as e:
            print(f"[Val Warning] Không thể chạy validation (chưa đủ dữ liệu test): {e}")

    # 2. Benchmark tốc độ suy luận (Inference Speed Test)
    print("\n[2] Đo tốc độ suy luận (Inference Benchmark 50 frames)...")
    dummy_input = np.random.randint(0, 255, (320, 320, 3), dtype=np.uint8)

    # Khởi động (Warm-up)
    for _ in range(5):
        _ = model.predict(dummy_input, imgsz=320, verbose=False)

    times = []
    for _ in range(50):
        t0 = time.time()
        _ = model.predict(dummy_input, imgsz=320, verbose=False)
        times.append(time.time() - t0)

    avg_time = np.mean(times) * 1000  # ms
    fps = 1000.0 / avg_time
    print(f"  - Thời gian suy luận trung bình: {avg_time:.2f} ms / frame")
    print(f"  - Tốc độ suy luận ước tính trên PC: {fps:.1f} FPS")
    print("=" * 60)


if __name__ == "__main__":
    main()
