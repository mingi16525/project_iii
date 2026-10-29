"""
Training Script for YOLOv8n Bottle Cap Detector on PC
Huấn luyện mô hình YOLOv8 Nano trên máy tính (hỗ trợ cả GPU CUDA và CPU).
"""

import os
import shutil
import torch
from ultralytics import YOLO

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DATASET_YAML = os.path.join(os.path.dirname(__file__), "dataset", "data.yaml")
BASE_MODEL = "yolov8n.pt"
EPOCHS = 40
IMG_SIZE = 320
BATCH_SIZE = 16


def main():
    print("=" * 65)
    print("  HUẤN LUYỆN MÔ HÌNH YOLOV8N NẮP CHAI TRÊN MÁY TÍNH (PC TRAIN)")
    print("=" * 65)

    # 1. Kiểm tra môi trường phần cứng
    device = "0" if torch.cuda.is_available() else "cpu"
    device_name = torch.cuda.get_device_name(0) if torch.cuda.is_available() else "CPU"
    print(f"[Hardware] Thiết bị huấn luyện: {device} ({device_name})")

    # 2. Kiểm tra file cấu hình dataset
    if not os.path.exists(DATASET_YAML):
        print(f"[Error] Không tìm thấy file data.yaml tại: {DATASET_YAML}")
        return

    print(f"[Dataset] Sử dụng cấu hình: {DATASET_YAML}")
    print(f"[Hyperparameters] Epochs={EPOCHS}, Image Size={IMG_SIZE}, Batch Size={BATCH_SIZE}")

    # 3. Khởi tạo mô hình tiền huấn luyện
    print(f"[Model] Đang tải mô hình nền: {BASE_MODEL}...")
    model = YOLO(BASE_MODEL)

    project_dir = os.path.join(os.path.dirname(__file__), "runs")

    # 4. Bắt đầu quá trình huấn luyện
    print("[Training] Bắt đầu quá trình huấn luyện (Transfer Learning)...")
    results = model.train(
        data=DATASET_YAML,
        epochs=EPOCHS,
        imgsz=IMG_SIZE,
        batch=BATCH_SIZE,
        device=device,
        workers=2,
        project=project_dir,
        name="cap_yolov8n",
        exist_ok=True,
        verbose=True
    )

    # 5. Lưu trọng số tốt nhất vào thư mục models/
    best_weights_src = os.path.join(project_dir, "cap_yolov8n", "weights", "best.pt")
    models_dir = os.path.join(ROOT_DIR, "models")
    os.makedirs(models_dir, exist_ok=True)
    best_weights_dst = os.path.join(models_dir, "yolov8n_cap.pt")

    if os.path.exists(best_weights_src):
        shutil.copy(best_weights_src, best_weights_dst)
        print("=" * 65)
        print(f"[SUCCESS] Huấn luyện hoàn tất thành công!")
        print(f"[Weights] File trọng số tốt nhất đã lưu tại: {best_weights_dst}")
        print(f"[Next Step] Hãy chạy 'python training/export.py' để xuất sang ONNX và TFLite.")
        print("=" * 65)
    else:
        print("[Warning] Không tìm thấy file best.pt đầu ra.")


if __name__ == "__main__":
    main()
