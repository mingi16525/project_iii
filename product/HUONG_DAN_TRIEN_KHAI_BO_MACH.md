# Hướng Dẫn Triển Khai Thực Tế & Đẩy Code Lên Bo Mạch Arduino
**Dự Án:** Hệ Thống Edge AI Đếm Nắp Chai Trên Băng Chuyền Mini (Project III)  
**Phần Cứng Mục Tiêu:** Bo Mạch Arduino Thế Hệ Mới (SoC Qualcomm, 2GB RAM, chạy Linux)  
**Tài liệu liên quan:** [Docs/](file:///d:/2026.1/ProjectIII/Docs) | [src/](file:///d:/2026.1/ProjectIII/product/src)

---

## 1. Sơ đồ luồng triển khai thực tế

```
┌─────────────────────────────────┐                       ┌─────────────────────────────────┐
│     Máy Tính Phát Triển (PC)     │   Đẩy code qua SCP    │   Bo Mạch Arduino (Linux SoC)   │
│   Windows / Linux Workstation   │──────────────────────►│  - IP: 192.168.1.50             │
│  - Lưu mã nguồn tại product/    │      hoặc Git         │  - Chạy mô hình Edge AI TFLite  │
│  - Chạy MQTT Broker & Dashboard │                       │  - Đọc Webcam USB (/dev/video0) │
└─────────────────────────────────┘                       └─────────────────────────────────┘
                 ▲                                                         │
                 │              Nhận JSON Telemetry qua MQTT               │
                 └─────────────────────────────────────────────────────────┘
```

---

## 2. Bước 1: Kết nối và cấu hình mạng cho Bo Mạch Arduino

### 2.1. Xác định địa chỉ IP của bo mạch
1. Cấp nguồn $5\text{V}/3\text{A}$ (hoặc $12\text{V}$ tùy thông số kit) cho bo mạch Arduino.
2. Kết nối bo mạch vào cùng mạng Wi-Fi phòng thí nghiệm với Laptop.
3. Tìm địa chỉ IP của bo mạch:
   - Trên máy tính mở PowerShell / Terminal và quét:
     ```powershell
     # Quét các thiết bị trong mạng LAN
     arp -a
     ```
   - Hoặc cắm cáp USB Type-C nối máy tính với bo mạch để truy cập qua cổng Serial Console COM port (PuTTY / Screen tốc độ Baud 115200) và gõ lệnh:
     ```bash
     ip addr show wlan0
     ```
   *(Giả sử địa chỉ IP tìm được của Arduino là: `192.168.1.50`, user mặc định: `arduino`)*

### 2.2. Kiểm tra kết nối SSH
Từ Terminal trên máy tính, chạy lệnh kiểm tra truy cập:
```bash
ssh arduino@192.168.1.50
```
*(Nhập mật khẩu của bo mạch khi được yêu cầu)*

---

## 3. Bước 2: Chuẩn bị môi trường trên Bo Mạch Linux

Sau khi đã SSH vào bo mạch, thực hiện các lệnh sau để cài đặt các gói công cụ thị giác máy tính và môi trường Python:

```bash
# 1. Cập nhật danh mục gói phần mềm (nếu có gói downgrade từ Qualcomm overlay thì thêm cờ --allow-downgrades)
sudo apt update && sudo apt upgrade -y --allow-downgrades

# 2. Cài đặt các thư viện hệ thống cần thiết (dùng libopenblas-dev thay cho libatlas-base-dev đã lỗi thời trên Debian mới)
sudo apt install -y python3-pip python3-venv python3-opencv v4l-utils libopenblas-dev git

# 3. Phân quyền cho user truy cập vào thiết bị camera USB
sudo usermod -a -G video $USER

# 4. Kiểm tra sự hiện diện của Webcam USB
v4l2-ctl --list-devices
```
> [!NOTE]
> Kết quả lệnh `v4l2-ctl --list-devices` phải hiển thị tên của Webcam USB (ví dụ: `USB 2.0 Camera (/dev/video0)`).

```bash
# 5. Cài đặt các thư viện Python bổ trợ (trên Debian 12/13 thêm --break-system-packages nếu không dùng venv)
pip3 install --break-system-packages paho-mqtt pyyaml numpy psutil

# Cài đặt ONNX Runtime (Khuyến nghị - Tương thích trực tiếp với file models/yolov8n_cap.onnx đã train)
pip3 install --break-system-packages onnxruntime

# (Tùy chọn nếu dùng TFLite):
# pip3 install --break-system-packages tflite-runtime
```

---

## 4. Bước 3: Đẩy mã nguồn từ máy tính lên Bo Mạch

Bạn có thể lựa chọn 1 trong 3 phương thức đẩy code thuận tiện nhất:

### Cách 1: Sử dụng lệnh SCP (Khuyến nghị - Nhanh nhất)
Từ máy tính cá nhân (tại thư mục dự án `d:\2026.1\ProjectIII\product`), mở PowerShell và chạy:

```powershell
# 1. Tạo thư mục chứa dự án trên bo mạch Arduino
ssh arduino@192.168.1.50 "mkdir -p ~/edge_counter/models ~/edge_counter/config"

# 2. Đẩy toàn bộ mã nguồn src/ và config/ lên bo mạch
scp -r d:\2026.1\ProjectIII\product\src arduino@192.168.1.52:~/edge_counter/
scp -r d:\2026.1\ProjectIII\product\config arduino@192.168.1.52:~/edge_counter/
scp d:\2026.1\ProjectIII\product\requirements.txt arduino@192.168.1.52:~/edge_counter/

# 3. Đẩy file mô hình AI weights đã train (.onnx) lên bo mạch
scp d:\2026.1\ProjectIII\product\models\yolov8n_cap.onnx arduino@192.168.1.52:~/edge_counter/models/
# (Tùy chọn) Đẩy thêm file .pt nếu cài Ultralytics trên bo mạch:
# scp d:\2026.1\ProjectIII\product\models\yolov8n_cap.pt arduino@192.168.1.50:~/edge_counter/models/
```

### Cách 2: Sử dụng VS Code Remote - SSH / Antigravity IDE
1. Cài đặt Extension **Remote - SSH** trên VS Code / Antigravity.
2. Nhấn `Ctrl + Shift + P` $\to$ chọn **Remote-SSH: Connect to Host...** $\to$ nhập `arduino@192.168.1.50`.
3. Mở thư mục `/home/arduino/edge_counter` trực tiếp trên cửa sổ IDE.
4. Kéo thả file mã nguồn hoặc chỉnh sửa code trực tiếp trên bo mạch mà không cần gõ lệnh đẩy.

### Cách 3: Đồng bộ qua Git (Khuyên dùng khi có Internet)
Kho mã nguồn đã được tạo sẵn trên GitHub:
```bash
# Trên bo mạch Arduino (lần đầu tiên):
git clone https://github.com/mingi16525/project_iii.git ~/edge_counter
cd ~/edge_counter/product

# Khi có cập nhật mới từ máy tính:
git pull origin main
```

---

## 5. Bước 4: Cấu hình MQTT Broker và Địa chỉ mạng

### 5.1. Khởi động MQTT Broker trên Laptop (Máy giám sát)
Để nhận dữ liệu kết quả đếm từ Arduino, trên Laptop cần chạy một MQTT Broker (Mosquitto):
- **Trên Windows:** Cài đặt Mosquitto và mở Command Prompt:
  ```cmd
  net start mosquitto
  ```
- **Trên Linux (Ubuntu / WSL trên Laptop):**
  1. Cài đặt Mosquitto:
     ```bash
     sudo apt update && sudo apt install -y mosquitto mosquitto-clients
     ```
  2. Cho phép kết nối từ xa từ bo mạch (Mosquitto 2.0+ mặc định chỉ nghe localhost):
     ```bash
     sudo bash -c 'cat <<EOF > /etc/mosquitto/conf.d/default.conf
listener 1883
allow_anonymous true
EOF'
     ```
  3. Khởi động dịch vụ Mosquitto:
     ```bash
     sudo service mosquitto restart
     # Hoặc: sudo systemctl restart mosquitto
     ```

### 5.2. Cập nhật địa chỉ IP của Laptop vào file cấu hình
Mở file `~/edge_counter/config/config.yaml` trên bo mạch và điền địa chỉ IP của Laptop (ví dụ: `192.168.1.100`):

```yaml
mqtt:
  enabled: true
  broker: "192.168.1.100"       # IP của Laptop trong cùng mạng Wi-Fi
  port: 1883
  topic: "lab/conveyor/counter"

display:
  # LƯU Ý QUAN TRỌNG KHI CHẠY QUA SSH:
  # Nếu bo mạch KHÔNG cắm màn hình HDMI (Headless mode), hãy đặt show_window: false
  # để tránh lỗi không mở được cửa sổ đồ họa GUI qua SSH:
  show_window: false
```

---

## 6. Bước 5: Vận hành và Chạy thử nghiệm thực tế

### 6.1. Khởi động ứng dụng giám sát trên Laptop trước
Mở Terminal trên Laptop tại thư mục dự án và chạy:
```bash
python product/dashboard/monitor_subscriber.py
```
*(Màn hình sẽ hiển thị trạng thái lắng nghe Topic `lab/conveyor/counter`)*

### 6.2. Khởi động chương trình đếm trên Bo Mạch Arduino
Trên cửa sổ SSH của Arduino, gõ lệnh:
```bash
cd ~/edge_counter
python3 src/main.py
```

### 6.3. Quan sát và Đánh giá Demo
1. Đặt các nắp chai mẫu lên mô hình băng chuyền mini và bật nguồn cho băng tải trượt qua vùng camera.
2. **Trên màn hình Terminal của Arduino:** Quan sát log thông báo:
   ```text
   [LineCounter] >> NẮP CHAI #1 VỪA CẮT VẠCH! (ID: 1, Y: 228->256)
   [LineCounter] >> NẮP CHAI #2 VỪA CẮT VẠCH! (ID: 2, Y: 231->262)
   ```
3. **Trên Dashboard Laptop:** Các dòng trạng thái telemetry được in tức thời theo thời gian thực:
   ```text
   [02:35:12] Device: arduino_lab_node   | COUNT:   1 nắp | FPS: 14.2 | Status: running
   [02:35:14] Device: arduino_lab_node   | COUNT:   2 nắp | FPS: 14.1 | Status: running
   ```
4. Kiểm tra file `counter_records.csv` tự động sinh ra trên Laptop để xem nhật ký số đếm phục vụ báo cáo.

---

## 7. Bước 6: Cấu hình tự động chạy khi khởi động bo mạch (Auto-Start Systemd Service)

Để bo mạch Arduino tự động chạy chương trình đếm nắp chai ngay khi cắm nguồn điện ở buổi bảo vệ đồ án mà không cần cắm máy tính để gõ lệnh:

1. Tạo file service hệ thống trên Arduino:
   ```bash
   sudo nano /etc/systemd/system/edge_counter.service
   ```

2. Dán nội dung cấu hình sau:
   ```ini
   [Unit]
   Description=Edge AI Bottle Cap Counter Service
   After=network.target

   [Service]
   Type=simple
   User=arduino
   WorkingDirectory=/home/arduino/edge_counter
   ExecStart=/usr/bin/python3 /home/arduino/edge_counter/src/main.py
   Restart=on-failure
   RestartSec=5s

   [Install]
   WantedBy=multi-user.target
   ```

3. Kích hoạt và kiểm tra service:
   ```bash
   # Nạp lại cấu hình systemd
   sudo systemctl daemon-reload

   # Bật tự động khởi động cùng hệ thống
   sudo systemctl enable edge_counter.service

   # Khởi động service ngay lập tức
   sudo systemctl start edge_counter.service

   # Kiểm tra trạng thái hoạt động
   sudo systemctl status edge_counter.service
   ```

---

## 8. Hướng dẫn xử lý sự cố thường gặp (Troubleshooting FAQ)

| Hiện tượng | Nguyên nhân khả dĩ | Cách khắc phục |
| :--- | :--- | :--- |
| **`Cannot open /dev/video0`** | Cáp Webcam USB cắm lỏng hoặc chưa đủ quyền truy cập thiết bị. | 1. Cắm lại cổng USB khác.<br>2. Chạy `ls -l /dev/video*`.<br>3. Chạy `sudo chmod 666 /dev/video0`. |
| **FPS tụt xuống dưới 5 FPS** | Đang chạy mô hình AI thuần CPU độ phân giải cao hoặc thiếu tản nhiệt. | 1. Đổi `input_size: [320, 320]` trong `config.yaml`.<br>2. Đảm bảo dùng model TFLite INT8.<br>3. Gắn miếng tản nhiệt nhôm (heatsink) lên chip. |
| **`Connection refused` khi gửi MQTT** | Địa chỉ IP Laptop bị sai hoặc firewall Laptop chặn cổng 1883. | 1. Dùng lệnh `ping <IP_Laptop>` kiểm tra mạng.<br>2. Tắt tạm thời Firewall trên Laptop hoặc cho phép cổng 1883 Inbound. |
| **Nắp chai đi qua không đếm** | Tọa độ vạch `line_y` chưa khớp vị trí băng chuyền. | Điều chỉnh thông số `line_y` trong `config/config.yaml` (ví dụ từ 240 tăng lên 280 tùy góc camera). |
