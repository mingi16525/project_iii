# Thư mục lưu trữ mô hình AI (Models Directory)

Thư mục này chứa các file trọng số của mô hình nhận diện nắp chai YOLOv8n đã qua huấn luyện:

- `yolov8n_cap.pt`: Mô hình gốc huấn luyện bằng PyTorch / Ultralytics.
- `yolov8n_cap.onnx`: Mô hình định dạng ONNX (dùng cho máy tính và bo mạch hỗ trợ ONNX Runtime).
- `yolov8n_cap.tflite`: Mô hình định dạng TensorFlow Lite (tối ưu triển khai trên bo mạch nhúng ARM / Arduino Qualcomm Linux).

*Lưu ý: Nếu chưa có file trọng số trong thư mục này, hệ thống sẽ tự động kích hoạt chế độ Heuristic Mock Mode (nhận diện hình thái nắp tròn và lọc màu) để cho phép chạy thử nghiệm toàn bộ luồng pipeline mà không bị gián đoạn.*
