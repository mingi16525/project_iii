"""
Model Evaluation Script
Đánh giá độ chính xác mAP50, Precision, Recall của mô hình nắp chai trên tập kiểm thử.
"""

import os
from ultralytics import YOLO

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DATASET_YAML = os.path.join(os.path.dirname(__file__), "dataset", "data.yaml")
MODELS_DIR = os.path.join(ROOT_DIR, "models")
MODEL_PATH = os.path.join(MODELS_DIR, "yolov8n_cap.pt")


def main():
    print("=" * 65)
    print("  ĐÁNH GIÁ CHỈ SỐ MÔ HÌNH (MODEL EVALUATION)")
    print("=" * 65)

    if not os.path.exists(MODEL_PATH):
        print(f"[Notice] Chưa có {MODEL_PATH}, sử dụng yolov8n.pt để test chức năng...")
        model = YOLO("yolov8n.pt")
    else:
        model = YOLO(MODEL_PATH)

    metrics = model.val(data=DATASET_YAML, imgsz=320, batch=16, verbose=True)

    print("\n" + "=" * 65)
    print(f" KẾT QUẢ ĐÁNH GIÁ MÔ HÌNH:")
    print(f" - mAP50-95 : {metrics.box.map:.4f}")
    print(f" - mAP50    : {metrics.box.map50:.4f}")
    print(f" - Precision: {metrics.box.mp:.4f}")
    print(f" - Recall   : {metrics.box.mr:.4f}")
    print("=" * 65)


if __name__ == "__main__":
    main()
