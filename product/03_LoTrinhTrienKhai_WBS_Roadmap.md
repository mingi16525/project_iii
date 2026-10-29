# Kế Hoạch Phân Rã Công Việc & Lộ Trình Triển Khai (WBS & Implementation Roadmap)
**Dự Án:** Hệ Thống Edge AI Đếm Nắp Chai Trên Băng Chuyền Mini  
**Phiên Bản:** 1.0  
**Tài liệu liên quan:** [00_TongQuan_KeHoachPhatTrien.md](file:///d:/2026.1/ProjectIII/product/00_TongQuan_KeHoachPhatTrien.md) | [02_KienTrucVaThietKe_SystemDesign.md](file:///d:/2026.1/ProjectIII/product/02_KienTrucVaThietKe_SystemDesign.md)

---

## 1. Phân rã cấu trúc công việc (Work Breakdown Structure - WBS)

```
WBS 1.0: Thiết lập Môi trường & Nền tảng Phần cứng
│   ├── 1.1: Khởi tạo OS Linux trên bo mạch Arduino & Cấu hình mạng SSH/Wi-Fi
│   ├── 1.2: Cài đặt runtime & thư viện nền tảng (Python, OpenCV, TFLite, Paho-MQTT)
│   └── 1.3: Viết script kiểm tra phần cứng (Webcam UVC, cổng USB, tốc độ đọc ảnh)
│
WBS 2.0: Dữ liệu & Huấn luyện Mô hình AI
│   ├── 2.1: Thu thập bộ ảnh nắp chai thực tế trên băng chuyền mini (500 - 1000 ảnh)
│   ├── 2.2: Gán nhãn dữ liệu (Bounding Box Annotation) định dạng YOLO
│   ├── 2.3: Huấn luyện mô hình YOLOv8n (Fine-tuning Transfer Learning)
│   ├── 2.4: Xuất mô hình và lượng tử hóa sang định dạng TFLite / ONNX (INT8/FP16)
│   └── 2.5: Đo benchmark tốc độ suy luận và độ chính xác trực tiếp trên board
│
WBS 3.0: Phát triển Phần mềm Lõi trên Thiết bị Biên (Edge Core Software)
│   ├── 3.1: Khởi tạo khung mã nguồn module hóa (OOP Architecture)
│   ├── 3.2: Phát triển module `CameraReader` (Quản lý buffer & kết nối V4L2)
│   ├── 3.3: Phát triển module `ObjectDetector` (Tiền xử lý, Inference, NMS)
│   ├── 3.4: Phát triển module `CentroidTracker` (Theo dõi quỹ đạo vật thể)
│   ├── 3.5: Phát triển module `LineCounter` (Logic cắt vạch ảo & Chống đếm lặp)
│   └── 3.6: Phát triển module `Visualizer` (Hiển thị OSD: Bounding box, vạch, counter, FPS)
│
WBS 4.0: Tích hợp Giao thức Truyền thông & Hệ thống Giám sát
│   ├── 4.1: Cấu hình MQTT Broker (Mosquitto) trên mạng nội bộ LAN
│   ├── 4.2: Phát triển module `MqttClient` (Đóng gói JSON & Threaded Publisher)
│   ├── 4.3: Viết ứng dụng `monitor_subscriber.py` nhận dữ liệu trên Laptop
│   └── 4.4: Xây dựng Dashboard hiển thị thống kê sản lượng mini
│
WBS 5.0: Lắp ráp Cơ khí & Tích hợp Hệ thống Thực nghiệm
│   ├── 5.1: Chế tạo/lắp ráp giá kẹp camera vuông góc 90° cách băng tải 25 - 40 cm
│   ├── 5.2: Lắp đặt cơ cấu băng chuyền mini, kiểm tra nguồn cấp DC 5V/12V ổn định
│   ├── 5.3: Cân chỉnh ánh sáng môi trường phòng Lab và tiêu cự ống kính
│   └── 5.4: Chạy thử nghiệm End-to-End toàn bộ chu trình với mẫu thử nắp chai
│
WBS 6.0: Kiểm thử, Tối ưu hóa & Hoàn thiện Báo cáo Đồ án
    ├── 6.1: Thực thi bộ kịch bản kiểm thử (Test Cases theo ma trận vận hành)
    ├── 6.2: Thu thập số liệu sai số, thống kê FPS, tối ưu tải RAM/CPU
    ├── 6.3: Đóng gói tài liệu kỹ thuật, hướng dẫn vận hành & Báo cáo đồ án Project III
    └── 6.4: Diễn tập kịch bản báo cáo và chuẩn bị bài thuyết trình Demo Lab
```

---

## 2. Bảng phân công công việc chi tiết & Mốc thời gian (Detailed Task Matrix)

| Mã Task | Tên nhiệm vụ | Kết quả đầu ra (Deliverable) | Thời lượng | Trạng thái |
| :--- | :--- | :--- | :--- | :--- |
| **T-1.1** | Cấu hình Linux & Network | SSH truy cập thành công, IP tĩnh/mDNS | 2 ngày | Sẵn sàng |
| **T-1.2** | Cài đặt môi trường Python/AI | Thư viện hoạt động, import không lỗi | 2 ngày | Sẵn sàng |
| **T-1.3** | Script test Webcam UVC | Script đọc camera đạt $\ge 25$ FPS thô | 1 ngày | Sẵn sàng |
| **T-2.1** | Thu thập tập ảnh nắp chai | Thư mục dataset $\approx 600$ ảnh gốc | 2 ngày | Chờ thực hiện |
| **T-2.2** | Gán nhãn Bounding Box | Bộ nhãn format YOLO (`.txt`) chuẩn | 2 ngày | Chờ thực hiện |
| **T-2.3** | Train YOLOv8n trên Colab/GPU | File trọng số `best.pt` đạt mAP $\ge 90\%$ | 2 ngày | Chờ thực hiện |
| **T-2.4** | Export TFLite / ONNX | File `yolov8n_cap.tflite` kích thước $< 10$MB | 1 ngày | Chờ thực hiện |
| **T-2.5** | Benchmark suy luận trên board | Tốc độ suy luận đạt $\ge 12$ FPS trên board | 1 ngày | Chờ thực hiện |
| **T-3.1** | Thiết lập cấu trúc repo `src/` | Bộ khung thư mục & file mẫu | 1 ngày | Hoàn thành |
| **T-3.2** | Hiện thực `CameraReader` | Đọc luồng video liên tục, không leak RAM | 1 ngày | Sẵn sàng |
| **T-3.3** | Hiện thực `ObjectDetector` | Tích hợp TFLite runtime + bộ lọc NMS | 2 ngày | Sẵn sàng |
| **T-3.4** | Hiện thực `Tracker` & `Counter` | Logic cắt vạch ảo không đếm lặp | 2 ngày | Sẵn sàng |
| **T-3.5** | Hiện thực `Visualizer` | Khung hình vẽ Bounding Box, vạch và text | 1 ngày | Sẵn sàng |
| **T-4.1** | Triển khai Mosquitto Broker | Broker hoạt động trên cổng 1883 LAN | 1 ngày | Sẵn sàng |
| **T-4.2** | Hiện thực `MqttClient` | Đóng gói JSON gửi dữ liệu qua background thread | 1 ngày | Sẵn sàng |
| **T-4.3** | Xây dựng Dashboard máy tính | Script nhận tin và hiển thị biểu đồ thời gian thực | 2 ngày | Sẵn sàng |
| **T-5.1** | Lắp đặt cơ khí & Giá kẹp camera | Bộ giá cố định chắc chắn, góc chuẩn 90° | 2 ngày | Chờ thực hiện |
| **T-5.2** | Tích hợp End-to-End hệ thống | Toàn bộ hệ thống chạy đồng bộ | 2 ngày | Chờ thực hiện |
| **T-6.1** | Chạy kiểm thử ma trận test | Bảng số liệu kết quả đo đạc thực tế | 2 ngày | Chờ thực hiện |
| **T-6.2** | Hoàn thiện báo cáo đồ án | Báo cáo hoàn chỉnh nộp hội đồng Project III | 3 ngày | Chờ thực hiện |

---

## 3. Tiêu chí hoàn thành giai đoạn (Definition of Done - DoD)

### Mốc M1: Sẵn sàng môi trường & Mô hình AI (End of Phase 2)
- [ ] Board mạch Arduino khởi động Linux mượt mà, kết nối Wi-Fi ổn định.
- [ ] Webcam cắm nhận ngay `/dev/video0`.
- [ ] Mô hình YOLOv8n dạng `.tflite` chạy thử nghiệm trên board đạt tối thiểu 10 FPS với frame $640 \times 480$.

### Mốc M2: Hoàn thiện lõi phần mềm Edge AI (End of Phase 3)
- [ ] Toàn bộ các module trong `src/core/` hoạt động ăn khớp.
- [ ] Logic cắt vạch ảo hoạt động chính xác trên video test mẫu: tăng đúng biến đếm khi nắp đi qua, không đếm trùng khi nắp dừng trên vạch.
- [ ] Mức tiêu thụ RAM duy trì ổn định dưới 1.2 GB sau 10 phút chạy liên tục.

### Mốc M3: Tích hợp hoàn chỉnh & Kiểm thử thực nghiệm (End of Phase 5)
- [ ] Hệ thống phần cứng lắp ráp hoàn chỉnh trên bàn Lab.
- [ ] Khi cho nắp chai đi qua băng tải, số đếm trên màn hình và gói tin MQTT trên Laptop nhảy số đồng thời với độ trễ $< 100$ ms.
- [ ] Tỷ lệ đếm đúng đạt trên 95% trong kịch bản kiểm thử tiêu chuẩn.

### Mốc M4: Nghiệm thu đồ án Project III (End of Phase 6)
- [ ] Đầy đủ mã nguồn, mô hình, tài liệu hướng dẫn và báo cáo kỹ thuật.
- [ ] Sản phẩm chạy demo trực tiếp ổn định trước hội đồng bảo vệ.
