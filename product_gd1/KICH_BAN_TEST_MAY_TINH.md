# Kịch Bản Kiểm Thử Sản Phẩm Trên Máy Tính (PC Test Scenarios - GD1)
**Dự Án:** Hệ Thống Edge AI Đếm Nắp Chai Trên Băng Chuyền Mini (Project III)  
**Môi Trường Thử Nghiệm:** Máy tính cá nhân (PC/Laptop)  
**Thư mục làm việc:** [product_gd1/](file:///d:/2026.1/ProjectIII/product_gd1)

---

## 1. Mục tiêu kiểm thử Giai đoạn 1 (GD1)
Giai đoạn 1 tập trung xác thực thuật toán và quy trình phần mềm trên môi trường máy tính trước khi chuyển giao sang phần cứng nhúng biên, nhằm:
1. Xác minh độ chính xác của logic theo dõi (Tracking) và cắt vạch ảo (Line Crossing) chống đếm lặp.
2. Kiểm tra tốc độ suy luận (FPS) của mô hình AI trên PC với các định dạng (.pt, .onnx).
3. Đánh giá tính ổn định của luồng dữ liệu truyền nhận qua MQTT Broker nội bộ.
4. Tối ưu hóa các ngưỡng thông số (vị trí vạch $Y_{line}$, vùng đệm $\delta$, khoảng cách max distance của tracker) trước khi nạp vào bo mạch.

---

## 2. Ma trận 5 Kịch bản kiểm thử trên PC (PC Test Cases Matrix)

| Mã KB | Tên kịch bản | Nguồn dữ liệu (Input) | Các bước thực hiện | Tiêu chí đánh giá Đạt (Pass) |
| :---: | :--- | :--- | :--- | :--- |
| **PC-TC01** | **Kiểm thử logic đếm qua Video giả lập (Baseline Simulation)** | File video mô phỏng `simulation/conveyor_simulation.mp4` (15 nắp chuẩn) | 1. Chạy `generate_synthetic_video.py`.<br>2. Chạy `python src/main_pc.py` với cấu hình `type: "video"`.<br>3. Theo dõi số đếm khi video chạy hết 1 vòng. | Hệ thống đếm đúng **15/15 nắp** (Accuracy = $100\%$), không bị đếm trùng khi nắp ra khỏi vạch. |
| **PC-TC02** | **Kiểm thử chống đếm lặp khi nắp dừng trên vạch (Pause on Line)** | File video mô phỏng hoặc Webcam PC | 1. Khi 1 nắp chai đang chạm đúng vạch đỏ, bấm phím `[SPACE]` để dừng hình.<br>2. Giữ trạng thái dừng trong 5 giây.<br>3. Bấm `[SPACE]` để tiếp tục cho nắp đi qua. | Biến đếm chỉ tăng đúng **duy nhất 1 lần**, không nhảy số liên tục khi nắp đứng yên. |
| **PC-TC03** | **Kiểm thử với Webcam PC thực tế (Real Webcam Test)** | Webcam PC hoặc Webcam USB ngoài, cầm tay di chuyển nắp chai | 1. Sửa `config_pc.yaml` sang `type: "webcam"`.<br>2. Cầm 5 nắp chai thật lần lượt đưa trôi qua vạch đỏ từ trên xuống dưới.<br>3. Đưa 1 nắp di chuyển ngược từ dưới lên trên. | - Đếm đủ 5 nắp trôi từ trên xuống.<br>- Nắp trôi ngược chiều từ dưới lên **không bị tính điểm đếm**. |
| **PC-TC04** | **Kiểm thử truyền thông MQTT cục bộ (Local MQTT Telemetry)** | MQTT Broker (Mosquitto) chạy trên PC cổng 1883 | 1. Mở terminal 1: Chạy `python product/dashboard/monitor_subscriber.py`.<br>2. Mở terminal 2: Chạy `python src/main_pc.py`.<br>3. Quan sát mỗi khi có nắp qua vạch. | Terminal subscriber nhận ngay lập tức gói tin JSON: `total_caps` nhảy số đồng bộ, ghi vào `counter_records.csv`. |
| **PC-TC05** | **Kiểm thử hiệu năng suy luận (Inference Speed Benchmark)** | File mô hình AI `.pt` hoặc `.onnx` trong `models/` | 1. Chạy lệnh: `python training/evaluate.py`.<br>2. Đo thời gian suy luận trung bình trên 50 frames. | Tốc độ suy luận trên PC đạt $\ge 25$ FPS (nếu có GPU) hoặc $\ge 15$ FPS (trên CPU). |
| **PC-TC06** | **Kiểm thử với Luồng Stream mạng LAN (LAN Stream Test)** | Camera phát qua mạng LAN (RTSP/HTTP từ IP Cam hoặc điện thoại) | 1. Cấu hình `type: "stream"` trong `config_pc.yaml`.<br>2. Chạy `python src/main_pc.py`.<br>3. Cho vật thể trôi qua camera stream. | Nhận luồng video mượt mà, độ trễ mạng thấp, đếm chính xác khi nắp trôi qua vạch ảo. |

---

## 3. Quy trình thực hiện chi tiết từng kịch bản

### Kịch bản 1: Test tự động không cần camera (Khuyến nghị chạy đầu tiên)
Chạy script kiểm tra tự động đã tích hợp sẵn:
```bash
cd d:\2026.1\ProjectIII\product_gd1
python tests/test_simulation_accuracy.py
```
*Kết quả in ra bảng độ chính xác và thông báo `[TEST PASSED]` nếu đạt $\ge 90\%$.*

### Kịch bản 2: Test giao diện trực quan với video mô phỏng
```bash
# 1. Sinh video mô phỏng nếu chưa có
python simulation/generate_synthetic_video.py

# 2. Khởi chạy ứng dụng hiển thị GUI
python src/main_pc.py
```
*Cửa sổ hiển thị hiện ra đường vạch đỏ (Counting Line), các nắp tròn trôi qua sẽ được vẽ Bounding box vàng, tâm hồng kèm ID, và nháy xanh lá vạch kẻ khi đếm thành công.*

### Kịch bản 3: Test trực tiếp bằng Webcam PC với nắp chai thật
1. Mở file [config_pc.yaml](file:///d:/2026.1/ProjectIII/product_gd1/config_pc.yaml).
2. Sửa dòng:
   ```yaml
   input:
     type: "webcam"
     webcam_index: 0
   ```
3. Chạy lệnh:
   ```bash
   python src/main_pc.py
   ```
4. Cầm nắp chai thật di chuyển qua màn hình để kiểm tra.
