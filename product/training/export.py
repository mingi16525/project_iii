"""
Model Export Script for Edge AI and PC Deployment
Tự động xuất mô hình YOLOv8n từ .pt sang định dạng ONNX và TFLite tối ưu.
"""

import os
import shutil
from ultralytics import YOLO

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
MODELS_DIR = os.path.join(ROOT_DIR, "models")
INPUT_MODEL = os.path.join(MODELS_DIR, "yolov8n_cap.pt")
# Kích thước đầu vào của mô hình xuất ra cho bo mạch biên.
# 224 thay vì 320: suy luận nhanh hơn ~1.8x trên CPU ARM mà mAP50 gần như không đổi
# (0.9919 so với 0.9935 trên tập val). PHẢI khớp với model.input_size trong config/config.yaml
# vì ONNX được xuất với dynamic=False (kích thước đầu vào cố định).
IMG_SIZE = 224


def main():
    print("=" * 65)
    print("  XUẤT MÔ HÌNH AI CHO BO MẠCH BIÊN & MÁY TÍNH (EXPORT ENGINE)")
    print("=" * 65)

    os.makedirs(MODELS_DIR, exist_ok=True)

    if not os.path.exists(INPUT_MODEL):
        fallback_model = "yolov8n.pt"
        print(f"[Warning] Không tìm thấy '{INPUT_MODEL}', xuất mô hình gốc '{fallback_model}' làm mẫu...")
        model_to_export = fallback_model
    else:
        model_to_export = INPUT_MODEL

    model = YOLO(model_to_export)

    # 1. Xuất định dạng ONNX
    print(f"\n[1/2] Đang xuất mô hình sang ONNX ({IMG_SIZE}x{IMG_SIZE})...")
    try:
        onnx_path = model.export(format="onnx", imgsz=IMG_SIZE, dynamic=False, simplify=True)
        print(f"[ONNX Export Success] File sinh ra: {onnx_path}")
        target_onnx = os.path.join(MODELS_DIR, "yolov8n_cap.onnx")
        if os.path.exists(onnx_path) and onnx_path != target_onnx:
            shutil.copy(onnx_path, target_onnx)
            print(f"[Copy] Đã sao chép vào: {target_onnx}")
    except Exception as e:
        print(f"[ONNX Error] Lỗi khi xuất ONNX: {e}")

    # 2. Xuất định dạng TFLite (Dành cho bo mạch Arduino Qualcomm Linux)
    print(f"\n[2/2] Đang xuất mô hình sang TFLite ({IMG_SIZE}x{IMG_SIZE})...")
    try:
        tflite_path = model.export(format="tflite", imgsz=IMG_SIZE, int8=False)
        print(f"[TFLite Export Success] File sinh ra: {tflite_path}")
        target_tflite = os.path.join(MODELS_DIR, "yolov8n_cap.tflite")
        if os.path.exists(tflite_path) and tflite_path != target_tflite:
            shutil.copy(tflite_path, target_tflite)
            print(f"[Copy] Đã sao chép vào: {target_tflite}")
    except Exception as e:
        print(f"[TFLite Warning] Lỗi khi xuất TFLite: {e}")

    print("\n" + "=" * 65)
    print(" HOÀN TẤT XUẤT MÔ HÌNH!")
    print(f" File .onnx tại: {os.path.join(MODELS_DIR, 'yolov8n_cap.onnx')}")
    print(f" File .tflite tại: {os.path.join(MODELS_DIR, 'yolov8n_cap.tflite')}")
    print("=" * 65)


if __name__ == "__main__":
    main()
