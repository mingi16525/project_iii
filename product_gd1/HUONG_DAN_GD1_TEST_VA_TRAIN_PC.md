# Hướng Dẫn Thực Hành Toàn Diện: Kiểm Thử & Huấn Luyện Trên PC (Giai Đoạn 1)
**Dự Án:** Hệ Thống Edge AI Đếm Nắp Chai Trên Băng Chuyền Mini (Project III)  
**Mục Tiêu:** Kiểm thử giải thuật, thu thập dữ liệu, huấn luyện mô hình AI và xác thực toàn diện trên Máy tính trước khi nạp vào bo mạch Arduino UNO Q.  
**Thư Mục Làm Việc:** `d:\2026.1\ProjectIII\product_gd1`

---

## 1. Tóm tắt quy trình: Từ PC đến Bo mạch Arduino UNO Q

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                        GIAI ĐOẠN 1: MÁY TÍNH CÁ NHÂN (PC / LAPTOP)                     │
│                                                                                        │
│  [Stream LAN / Webcam / Video]                                                         │
│           │                                                                            │
│           ▼                                                                            │
│   Thu thập Dataset ──► Huấn luyện YOLOv8n (GPU/CPU) ──► Xuất Model (.onnx, .tflite)    │
│                                                                  │                     │
│                                                                  ▼                     │
│   Kiểm thử Logic đếm vạch ảo + Centroid Tracking ◄───────────────┘                     │
│   Xác thực gói tin JSON Telemetry qua MQTT nội bộ                                      │
└───────────────────────────────────────────┬────────────────────────────────────────────┘
                                            │ Copy model (.tflite) & mã nguồn
                                            ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                    GIAI ĐOẠN 2: BO MẠCH NHÚNG BIÊN (ARDUINO UNO Q)                     │
│                                                                                        │
│   - Cắm Webcam USB-C trực tiếp vào bo mạch (/dev/video0)                               │
│   - Chạy suy luận TFLite Runtime tại chỗ (Edge AI), gửi kết quả qua MQTT               │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Chuẩn bị môi trường trên Máy tính

Mở **PowerShell** hoặc **Command Prompt** (Terminal trong VS Code / Antigravity IDE), điều hướng vào thư mục `product_gd1`:

```powershell
# 1. Điều hướng vào thư mục Giai đoạn 1
cd d:\2026.1\ProjectIII\product_gd1

# 2. Cài đặt các thư viện phụ thuộc
pip install -r requirements_pc.txt
```

> [!TIP]
> **Tăng tốc huấn luyện nếu có GPU NVIDIA:**  
> Nếu máy tính có card rời NVIDIA, bạn nên cài đặt PyTorch phiên bản hỗ trợ CUDA để tốc độ huấn luyện mô hình nhanh hơn 10 - 20 lần:  
> `pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121`

---

## 3. Khởi chạy nhanh trong 2 phút (Quick-Start - Không cần phần cứng)

Bạn có thể xác thực ngay lập tức giải thuật đếm và giao diện đồ họa mà không cần camera hay nắp chai thật bằng bộ sinh video mô phỏng tích hợp sẵn:

### Bước 3.1: Chạy bài kiểm thử độ chính xác tự động
```powershell
python tests/test_simulation_accuracy.py
```
- **Hệ thống sẽ:** Tự động sinh video băng chuyền mô phỏng với đúng 12 nắp chai, chạy pipeline đếm không giao diện và so sánh với Ground Truth.
- **Tiêu chuẩn:** In thông báo `[TEST PASSED]` với độ chính xác đạt $\ge 95\%$.

### Bước 3.2: Chạy ứng dụng hiển thị trực quan (GUI Demo)
```powershell
python src/main_pc.py
```
- Cửa sổ đồ họa sẽ hiện lên:
  - Băng chuyền mô phỏng chuyển động từ trên xuống dưới.
  - Vạch ảo màu đỏ (`COUNTING LINE Y=240`).
  - Khi nắp chai chạm và vượt qua vạch, vạch sẽ **nháy xanh lá**, bảng HUD góc trái sẽ nhảy số `COUNT: 1, 2, 3...`.
- **Phím tắt điều khiển:**
  - Nhấn **`[SPACE]`**: Tạm dừng / Tiếp tục video (giúp test tính năng chống đếm trùng khi nắp đứng yên trên vạch).
  - Nhấn **`[R]`**: Reset bộ đếm về 0.
  - Nhấn **`[Q]`**: Thoát ứng dụng an toàn.

---

## 4. Ba chế độ nguồn hình ảnh đầu vào trên PC

File cấu hình chính: [config_pc.yaml](file:///d:/2026.1/ProjectIII/product_gd1/config_pc.yaml). Bạn có thể đổi nguồn video linh hoạt tại mục `input.type`:

### Chế độ 1: Video mô phỏng (`type: "video"`) - Mặc định
Dùng file video có sẵn để kiểm thử thuật toán lặp đi lặp lại:
```yaml
input:
  type: "video"
  video_file: "simulation/conveyor_simulation.mp4"
```

### Chế độ 2: Luồng Stream mạng LAN (`type: "stream"`) - Rất khuyến nghị
Sử dụng điện thoại thông minh (hoặc camera IP) làm camera không dây phát qua mạng Wi-Fi:
1. **Trên điện thoại Android/iOS:** Cài ứng dụng miễn phí **IP Webcam** (Android) hoặc **DroidCam**.
2. Mở app $\to$ bấm **Start Server**. Màn hình điện thoại sẽ hiển thị đường link (ví dụ: `http://192.168.1.55:8080`).
3. Mở [config_pc.yaml](file:///d:/2026.1/ProjectIII/product_gd1/config_pc.yaml) và điền link:
   ```yaml
   input:
     type: "stream"
     stream_url: "http://192.168.1.55:8080/video"   # Đối với IP Webcam app
     # Hoặc nếu là IP Camera chuẩn RTSP:
     # stream_url: "rtsp://admin:123456@192.168.1.55:554/live"
   ```
4. Chạy `python src/main_pc.py` $\to$ Máy tính sẽ lấy trực tiếp hình ảnh camera trên băng chuyền qua Wi-Fi.

### Chế độ 3: Webcam USB / Laptop (`type: "webcam"`)
Cắm trực tiếp Webcam vào cổng USB của máy tính:
```yaml
input:
  type: "webcam"
  webcam_index: 0     # 0 là Webcam mặc định của Laptop, 1 là Webcam USB ngoài
```

---

## 5. Quy trình thu thập dữ liệu & Huấn luyện mô hình YOLOv8 trên PC

Khi bạn muốn mô hình AI nhận diện chính xác các mẫu nắp chai cụ thể của bài Lab:

### Bước 5.1: Chụp ảnh mẫu nắp chai làm Dataset
Chạy script [collect_data.py](file:///d:/2026.1/ProjectIII/product_gd1/training/collect_data.py):

```powershell
# Chụp từ luồng stream LAN (điện thoại/IP Cam):
python training/collect_data.py --source "http://192.168.1.42:8080/video"

# Hoặc chụp từ Webcam máy tính:
python training/collect_data.py --source 0
```
- Đặt các loại nắp chai (xanh, đỏ, trắng, úp, ngửa) dưới ống kính.
- Nhấn **`[SPACE]`** để chụp từng kiểu dáng, hoặc nhấn **`[A]`** để bật tự động chụp mỗi 1.5 giây.
- Chụp khoảng **150 – 300 ảnh**. Ảnh được lưu tự động tại `training/dataset/images/train/`.

### Bước 5.2: Gán nhãn Bounding Box (Annotation)
1. Cài đặt và mở công cụ `labelImg`:
   ```powershell
   pip install labelImg
   labelImg
   ```
2. Thao tác trên giao diện:
   - Bấm **Open Dir** $\to$ trỏ vào thư mục `training/dataset/images/train`.
   - Bấm **Change Save Dir** $\to$ trỏ vào thư mục `training/dataset/labels/train`.
   - Chuyển định dạng nhãn sang **YOLO** (thanh bên trái).
   - Nhấn phím **`W`** $\to$ kéo chuột vẽ ô chữ nhật quanh nắp chai $\to$ nhập tên nhãn: `bottle_cap`.
   - Nhấn **`Ctrl + S`** (Lưu) $\to$ nhấn **`D`** (Ảnh tiếp theo).
3. Copy khoảng $20\%$ số ảnh sang `images/val` và các file nhãn tương ứng sang `labels/val` để làm tập validation.

### Bước 5.3: Huấn luyện mô hình YOLOv8n trên PC
Chạy script [train.py](file:///d:/2026.1/ProjectIII/product_gd1/training/train.py):
```powershell
python training/train.py
```
- Script áp dụng Transfer Learning từ `yolov8n.pt`, huấn luyện trong 40 epochs với độ phân giải $320 \times 320$ (chuẩn tối ưu cho vi xử lý nhúng).
- Trọng số tốt nhất tự động được lưu thành file `models/yolov8n_cap.pt`.

### Bước 5.4: Xuất mô hình sang ONNX & TFLite
Chạy script [export.py](file:///d:/2026.1/ProjectIII/product_gd1/training/export.py):
```powershell
python training/export.py
```
Đầu ra bao gồm:
1. `models/yolov8n_cap.onnx`: Sử dụng để chạy suy luận tốc độ cao trên PC bằng OnnxRuntime.
2. `models/yolov8n_cap.tflite`: File mô hình nén ($< 6$ MB) sẵn sàng nạp vào bo mạch Arduino UNO Q.

### Bước 5.5: Đánh giá độ chính xác & Tốc độ FPS
Chạy script [evaluate.py](file:///d:/2026.1/ProjectIII/product_gd1/training/evaluate.py):
```powershell
python training/evaluate.py
```
Xem các chỉ số: $mAP@0.5$, Precision, Recall và thời gian suy luận trung bình (ms/frame).

---

## 6. Tính Năng Nâng Cấp: Phân Biệt & Đếm Theo Màu Sắc (Độ chính xác $\ge 70\%$)

Hệ thống đã được tích hợp bộ phân tích màu thông minh **[ColorAnalyzer](file:///d:/2026.1/ProjectIII/product_gd1/src/core/color_analyzer.py)**, kết hợp giữa mô hình nhận diện Bounding Box và trích xuất không gian màu HSV:

### 6.1. Nguyên lý phân loại màu sắc: Đơn sắc, 2 màu, Đa màu & Màu lạ
1. **Trích xuất vùng lõi (Center ROI):** Cắt lấy $50\%$ vùng tâm tròn của nắp chai để loại trừ viền bóng, mép nắp hoặc nền băng chuyền.
2. **Kiểm tra độ phủ màu sắc:** Chuyển đổi sang hệ màu HSV, tính toán tỷ lệ diện tích của từng dải màu trong bảng cấu hình: `["red", "blue", "green", "yellow", "white"]`.
3. **Tiêu chuẩn phân loại đa tầng:**
   - **Nắp đơn sắc (Single Color):** Khi màu top 1 chiếm tỷ lệ $\ge 70\%$ (ngưỡng `confidence_threshold: 0.70`) hoặc $\ge 55\%$ và cách biệt hoàn toàn màu thứ 2 $\to$ Gán nhãn đơn màu (ví dụ: `RED 95%`, `BLUE 90%`).
   - **Nắp phối 2 màu (Dual-Color / Bicolor):** Ví dụ nắp Coca-Cola (đỏ nền + trắng chữ) hoặc Pepsi (xanh nền + trắng chữ). Khi 2 màu hàng đầu có tỷ lệ đáng kể ($r_1 \ge 25\%, r_2 \ge 20\%$), tổng độ phủ $\ge 50\%$ và cách biệt màu thứ 3 $\to$ Tự động gán nhãn phối màu: **`RED_WHITE`**, **`BLUE_WHITE`**...
   - **Nắp đa màu (Multicolor):** Khi nắp có từ 3 màu trở lên và tỷ lệ các màu phân bổ đều (ví dụ mỗi màu $\approx 30\text{--}33\%$, không có màu nào vượt trội $\ge 45\%$) $\to$ Gán nhãn **`MULTICOLOR`** với khung hiển thị màu cam.
   - **Màu lạ chưa được huấn luyện (Unknown Color):** Khi nắp chai có màu sắc không nằm trong danh mục (ví dụ màu tím, cam tối, xám) hoặc tỷ lệ nhận diện $< 30\%$ $\to$ Đóng khung màu tím hồng, gắn nhãn **`UNKNOWN COLOR`** và lưu vào `counts_by_color["unknown"]`.

### 6.2. Cấu hình màu sắc trong [config_pc.yaml](file:///d:/2026.1/ProjectIII/product_gd1/config_pc.yaml)
```yaml
color:
  enabled: true
  # Danh sách các màu đơn đã cấu hình dải HSV:
  trained_colors: ["red", "blue", "green", "yellow", "white"]
  # Ngưỡng tin cậy tối thiểu cho nắp đơn màu:
  confidence_threshold: 0.70    # Đạt chính xác >= 70%
  # Tự động hỗ trợ phân loại 2 màu (Dual-color) và đa màu (Multicolor)
```

---

## 7. Kiểm thử truyền thông MQTT Telemetry trên PC

Hệ thống hỗ trợ gửi dữ liệu JSON kết quả đếm về hệ thống giám sát theo thời gian thực.

1. **Khởi chạy Dashboard nhận tin trên PC:**
   Mở một cửa sổ Terminal mới:
   ```powershell
   python product/dashboard/monitor_subscriber.py
   ```
2. **Khởi chạy chương trình đếm:**
   Trên Terminal hiện tại:
   ```powershell
   python src/main_pc.py
   ```
3. **Quan sát kết quả:**
   Mỗi khi có nắp chai cắt qua vạch đỏ, màn hình dashboard sẽ in ra:
   ```text
   [02:45:10] Device: pc_test_workstation | COUNT:   1 nắp | FPS: 24.5 | Status: running
   [02:45:12] Device: pc_test_workstation | COUNT:   2 nắp | FPS: 24.8 | Status: running
   ```
   Đồng thời dữ liệu được tự động ghi vào file `counter_records.csv`.

---

## 8. Bảng xử lý sự cố thường gặp trên PC (Troubleshooting FAQ)

| Hiện tượng lỗi | Nguyên nhân | Cách khắc phục |
| :--- | :--- | :--- |
| **`Không thể mở Webcam tại index 0`** | Webcam đang bị ứng dụng khác (Zoom, Teams, Chrome) chiếm quyền sử dụng. | Đóng các ứng dụng đang dùng camera hoặc đổi `webcam_index: 1`. |
| **`Không thể kết nối tới luồng stream LAN`** | Sai địa chỉ IP, điện thoại và PC không chung mạng Wi-Fi, hoặc chưa bấm "Start Server". | 1. Kiểm tra điện thoại và PC kết nối cùng mạng Wi-Fi.<br>2. Mở trình duyệt trên PC gõ `http://<IP>:8080` xem có vào được web camera không. |
| **Video stream bị trễ/delay vài giây** | Bộ đệm video tích tụ khung hình cũ qua mạng Wi-Fi. | Đã được xử lý tự động trong `src/core/camera.py` bằng `CAP_PROP_BUFFERSIZE = 1`. Đảm bảo mạng Wi-Fi ổn định. |
| **Chưa train model nhưng muốn test đếm ngay** | Chưa có file trọng số `best.pt` hoặc `.onnx`. | Hệ thống có sẵn chế độ **Heuristic Mock Mode** tự nhận diện hình tròn nắp chai để test logic đếm mà không cần model. |
| **Lỗi `ModuleNotFoundError: No module named 'ultralytics'`** | Chưa cài đặt gói thư viện. | Chạy lại lệnh: `pip install -r requirements_pc.txt`. |

---

## 9. Sẵn sàng chuyển giao sang Giai đoạn 2 (Arduino UNO Q)

Khi bạn đã hoàn thành kiểm thử trên PC với kết quả:
- Độ chính xác đếm $\ge 95\%$.
- File mô hình `models/yolov8n_cap.tflite` đã sẵn sàng.

👉 Hãy mở tài liệu **[HUONG_DAN_TRIEN_KHAI_BO_MACH.md](file:///d:/2026.1/ProjectIII/product/HUONG_DAN_TRIEN_KHAI_BO_MACH.md)** để thực hiện các bước cắm Webcam USB-C vào cổng Type-C của Arduino UNO Q và đẩy mã nguồn xuống bo mạch để chạy thực tế!
