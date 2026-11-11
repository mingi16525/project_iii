# Hướng Dẫn Thực Hiện Cuối Cùng

**Dự án:** Hệ Thống Edge AI Đếm Nắp Chai Trên Băng Chuyền Mini (Project III)
**Phần cứng:** Bo mạch Arduino UNO Q (SoC Qualcomm 4 nhân aarch64, 1.7 GB RAM, Debian/Linux)
**Tài liệu liên quan:** [Docs/](Docs) · [product/](product) · [product_gd1/](product_gd1)

Tài liệu này là quy trình thực hiện hoàn chỉnh từ máy tính đến bo mạch, viết lại theo đúng
trạng thái hệ thống sau khi đã tối ưu và **đã đo kiểm trên bo mạch thật**.

---

## 1. Hiện trạng hệ thống

| Hạng mục | Giá trị |
| :--- | :--- |
| Mô hình | YOLOv8n, 1 lớp `bottle_cap`, ONNX đầu vào **224×224** |
| Tốc độ suy luận trên bo mạch | **110.8 ms/frame** (bản 320×320 cũ: 208.2 ms) |
| FPS end-to-end trên bo mạch | **15.0 FPS** với `detect_interval: 2` (trước khi tối ưu: ~7 FPS) |
| Độ chính xác mô hình | mAP50 **0.9919**, Recall 0.9923 (bản 320: 0.9935 / 0.9994) |
| Phân loại màu | **12 màu cơ bản** + nhãn `unknown` + nắp 2 màu + đa màu |
| Độ chính xác đếm | 12/12 nắp (100%) trên video mô phỏng |
| Truyền thông | MQTT, topic `lab/conveyor/counter`, broker Mosquitto chạy trên bo mạch |

### Hai thư mục mã nguồn — chọn đúng thư mục

Dự án có **hai bản pipeline gần giống nhau nhưng độc lập**, sửa bên này không ảnh hưởng bên kia:

| | `product/` | `product_gd1/` |
| :--- | :--- | :--- |
| Dùng cho | **Bo mạch** (chạy thật, headless) | **Máy tính** (phát triển, huấn luyện) |
| Chương trình chính | `src/main.py` | `src/main_pc.py` |
| File cấu hình | `config/config.yaml` | `config_pc.yaml` |
| Kích thước mô hình | **224×224** | 320×320 |
| Thư viện | `requirements.txt` (chỉ runtime) | `requirements_pc.txt` (thêm ultralytics, torch) |
| Bộ dữ liệu gán nhãn | Không có (chỉ `data.yaml` giữ chỗ) | **`training/dataset/`** — dữ liệu thật ở đây |

> [!IMPORTANT]
> Mọi việc huấn luyện, gán nhãn và đánh giá đều làm ở `product_gd1/`.
> Chỉ `product/` mới được đẩy lên bo mạch.

---

## 2. Phần cứng và kết nối

1. Cấp nguồn cho bo mạch, kết nối cùng mạng Wi-Fi/LAN với máy tính.
2. Cắm **webcam USB** vào bo mạch. Đặt giá đỡ chiếu vuông góc 90° xuống mặt băng chuyền mini.
3. Đặt băng chuyền sao cho nắp chai di chuyển **từ trên xuống dưới** trong khung hình
   (khớp với `counter.direction: "down"`).
4. Chiếu sáng đều, tránh bóng gắt và vùng phản quang — đây là yếu tố ảnh hưởng lớn nhất
   đến độ chính xác phân loại màu bằng HSV.

### Xác định đúng node camera — bước dễ sai nhất

> [!WARNING]
> Trên bo mạch Qualcomm, **`/dev/video0` và `/dev/video1` là bộ mã hóa/giải mã video cứng
> Venus của SoC, KHÔNG phải camera.** Nếu `camera.index` trỏ vào đó, chương trình sẽ mở
> thành công nhưng **không bao giờ nhận được khung hình nào** và không báo lỗi gì.

SSH vào bo mạch và kiểm tra:

```bash
v4l2-ctl --list-devices
```

Kết quả thật trên bo mạch của dự án này — webcam USB nhận hai node liền nhau, node đầu là
kênh hình, node sau là metadata của chuẩn UVC:

```text
Qualcomm Venus video decoder (plat:5a00000.video-codec:dec):
        /dev/video1                 <- KHÔNG phải camera
Qualcomm Venus video encoder (plat:5a00000.video-codec:enc):
        /dev/video0                 <- KHÔNG phải camera
USB PHY 2.0:  (usb-xhci-hcd.2.auto-1.3):
        /dev/video2                 <- camera cần dùng
        /dev/video3
        /dev/media0
```

Tên webcam có thể hiện ra khác tùy chipset (ở đây là `USB PHY 2.0`), nhưng dấu hiệu nhận
biết luôn đúng: **node nào thuộc `Qualcomm Venus` thì không phải camera.**

Điền node tìm được vào `camera.index` trong `product/config/config.yaml`. Số node **có thể
đổi khi cắm lại USB**, nên nếu hệ thống đột nhiên không thấy hình thì kiểm tra lại lệnh trên.

---

## 3. Giai đoạn 1 — Chuẩn bị và kiểm thử trên máy tính

### 3.1. Cài môi trường

```powershell
cd d:\2026.1\ProjectIII\product_gd1
pip install -r requirements_pc.txt
```

Nếu máy có GPU NVIDIA, cài PyTorch bản CUDA để huấn luyện nhanh hơn 10–20 lần:

```powershell
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121
```

### 3.2. Kiểm thử nhanh không cần phần cứng

```powershell
python tests/test_simulation_accuracy.py
```

Script tự sinh video băng chuyền mô phỏng 12 nắp phủ đủ 12 màu cơ bản, chạy toàn bộ pipeline
và so với số thật. Đạt yêu cầu khi in `[TEST PASSED]` với độ chính xác ≥ 90%.

> Lưu ý: test này cố ý chạy ở **chế độ Mock Heuristic** (`ObjectDetector(model_path="")`),
> tức là kiểm tra logic đếm và phân loại màu, **không** kiểm tra mô hình đã huấn luyện.

Xem giao diện đồ họa:

```powershell
python src/main_pc.py
python src/main_pc.py --source 0 --no-mqtt
```

Phím điều khiển: `Q` thoát · `R` đặt lại bộ đếm · `SPACE` tạm dừng.

### 3.3. Thu thập dữ liệu

```powershell
python training/collect_data.py --source 0
```

- `SPACE` chụp từng ảnh, `A` tự động chụp mỗi 1.5 giây.
- Chụp **150–300 ảnh**, đủ các kiểu: nắp úp, nắp ngửa, nhiều màu, nhiều vị trí, có che khuất.
- Ảnh lưu vào `training/dataset/images/train/`.

### 3.4. Gán nhãn

```powershell
pip install labelImg
labelImg
```

Mở thư mục `training/dataset/images/train/`, chọn định dạng **YOLO**, vẽ khung quanh từng nắp
với lớp `bottle_cap`, lưu nhãn `.txt` vào `training/dataset/labels/train/`.
Tách khoảng 20% ảnh sang `images/val/` và `labels/val/` để đánh giá.

### 3.5. Huấn luyện và đánh giá

```powershell
python training/train.py
python training/evaluate.py
```

`train.py` dùng 40 epoch, ảnh 320px, batch 16, tự chọn GPU nếu có, và sao trọng số tốt nhất
vào `models/yolov8n_cap.pt`.

> [!NOTE]
> `training/evaluate.py` **chỉ chạy được từ `product_gd1/`** vì bộ dữ liệu nằm ở đây.
> Chạy từ `product/` sẽ báo `Dataset images not found`.

---

## 4. Xuất mô hình cho bo mạch (224×224)

Mô hình huấn luyện ở 320px nhưng **xuất cho bo mạch ở 224px**: suy luận nhanh **1.88×** mà
mAP50 gần như không đổi (0.9919 so với 0.9935).

```powershell
cd d:\2026.1\ProjectIII\product
copy ..\product_gd1\models\yolov8n_cap.pt models\yolov8n_cap.pt
python training/export.py
```

`IMG_SIZE = 224` đã được đặt sẵn trong [product/training/export.py](product/training/export.py).

> [!CAUTION]
> **`model.input_size` trong config PHẢI khớp đúng `IMG_SIZE` đã xuất.** ONNX được xuất với
> `dynamic=False` nên kích thước đầu vào là cố định. Nếu lệch, chương trình **không báo lỗi
> khi nạp**: nó in banner, kết nối MQTT, rồi **thoát im lặng với exit code 0, không một dòng
> `[STATUS]`**. Nếu bo mạch đột nhiên "im" ngay sau khi chạy, kiểm tra điều này trước tiên.

Hai điểm cần biết về `export.py`:

- Nó ghi file ONNX **đè trực tiếp** lên `models/yolov8n_cap.onnx` của thư mục đang chạy.
  Muốn giữ bản cũ thì sao lưu trước (bản cũ cũng còn trong git: `git checkout -- <đường dẫn>`).
- Phần xuất TFLite/LiteRT **thất bại trên Windows** (`chỉ hỗ trợ Linux x86 và macOS`) —
  không ảnh hưởng gì vì bo mạch dùng ONNX. Phần ONNX vẫn thành công.

Kiểm tra lại kích thước đầu vào của file vừa xuất:

```powershell
python -c "import onnxruntime as o; print(o.InferenceSession('models/yolov8n_cap.onnx').get_inputs()[0].shape)"
```

Phải in ra `[1, 3, 224, 224]`.

---

## 5. Đẩy mã nguồn lên bo mạch

Giả sử bo mạch có IP `192.168.1.252`, user `arduino`. Kiểm tra IP bằng `hostname -I` trên bo mạch.

### 5.1. Chuẩn bị môi trường trên bo mạch (chỉ làm lần đầu)

```bash
sudo apt update
sudo apt install -y python3-pip python3-opencv v4l-utils libopenblas-dev git mosquitto mosquitto-clients
sudo usermod -a -G video $USER
pip3 install --break-system-packages paho-mqtt pyyaml numpy psutil onnxruntime
```

Cho Mosquitto nhận kết nối từ máy tính giám sát:

```bash
sudo bash -c 'cat > /etc/mosquitto/conf.d/default.conf <<EOF
listener 1883 0.0.0.0
allow_anonymous true
EOF'
sudo systemctl restart mosquitto
sudo systemctl enable mosquitto
```

### 5.2. Đẩy code

```powershell
scp -r product\src product\config product\tools product\models arduino@192.168.1.252:/home/arduino/edge_counter/
```

Khỏi phải nhập mật khẩu mỗi lần thì tạo khóa SSH một lần. Khi được hỏi passphrase thì
nhấn Enter hai lần để bỏ trống:

```powershell
ssh-keygen -t ed25519 -f $env:USERPROFILE\.ssh\id_ed25519_board
type $env:USERPROFILE\.ssh\id_ed25519_board.pub | ssh arduino@192.168.1.252 "mkdir -p ~/.ssh && cat >> ~/.ssh/authorized_keys && chmod 700 ~/.ssh && chmod 600 ~/.ssh/authorized_keys"
```

Lệnh thứ hai là lần cuối phải nhập mật khẩu. Sau đó thêm
`-i $env:USERPROFILE\.ssh\id_ed25519_board` vào các lệnh `ssh`/`scp`.
Muốn thu hồi quyền thì xóa dòng khóa tương ứng trong `~/.ssh/authorized_keys` trên bo mạch.

### 5.3. Kiểm tra cấu hình trên bo mạch

```bash
cd ~/edge_counter
grep -E "^  index|^  fps|threaded_capture|input_size|detect_interval|trained_colors" config/config.yaml
```

Giá trị đúng cho bo mạch:

```yaml
camera:
  index: "/dev/video2"        # theo kết quả v4l2-ctl --list-devices
  fps: 30
  threaded_capture: false
model:
  input_size: [224, 224]      # khớp IMG_SIZE đã xuất
  detect_interval: 2
```

---

## 6. Vận hành

### 6.1. Khởi động dashboard giám sát trên máy tính (làm trước)

Sửa `BROKER_HOST` trong [product/dashboard/monitor_subscriber.py](product/dashboard/monitor_subscriber.py)
thành IP bo mạch (giá trị mặc định là `"localhost"`, chỉ đúng khi broker chạy trên máy tính):

```python
BROKER_HOST = "192.168.1.252"
```

```powershell
python product\dashboard\monitor_subscriber.py
```

Dashboard lắng nghe topic `lab/conveyor/counter` và ghi nhật ký vào `counter_records.csv`.

### 6.2. Khởi động chương trình đếm trên bo mạch

```bash
cd ~/edge_counter
python3 -u src/main.py
```

> Dùng `python3 -u` khi chuyển hướng output ra file hoặc qua `grep`, nếu không Python sẽ đệm
> và bạn sẽ không thấy gì cho đến khi chương trình kết thúc.

Kết quả mong đợi — bo mạch chạy headless nên in trạng thái mỗi 15 frame:

```text
[Detector] Nạp mô hình AI thành công (ONNX).
[MQTT] Đã kết nối thành công tới Broker: localhost:1883
[Camera] Sẵn sàng (WEBCAM): 640x480 @ 30.0 FPS (Buffer=1, tuần tự)
[LineCounter] >> NẮP CHAI #1 [MÀU: RED (94%)] CẮT VẠCH! (ID: 1)
[STATUS] Count: 1 (RED:1) | FPS: 15.0 | Detections: 2
```

Trên dashboard máy tính:

```text
[08:35:12] Device: arduino_lab_node | COUNT: 1 nắp | FPS: 15.0 | Status: running
```

### 6.3. Tự khởi động khi cắm nguồn

```bash
sudo nano /etc/systemd/system/edge_counter.service
```

```ini
[Unit]
Description=Edge AI Bottle Cap Counter Service
After=network.target mosquitto.service

[Service]
Type=simple
User=arduino
WorkingDirectory=/home/arduino/edge_counter
ExecStart=/usr/bin/python3 -u /home/arduino/edge_counter/src/main.py
Restart=on-failure
RestartSec=5s

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now edge_counter.service
sudo systemctl status edge_counter.service
journalctl -u edge_counter.service -f
```

`WorkingDirectory` là bắt buộc: chương trình tìm `config/`, `models/` theo đường dẫn tương đối.

---

## 7. Đo hiệu năng trên bo mạch

```bash
cd ~/edge_counter
python3 tools/benchmark_board.py                      # đo đủ 4 phần
python3 tools/benchmark_board.py --skip-camera        # chỉ đo suy luận
```

Script in ra thời gian từng khâu, FPS dự kiến theo từng `detect_interval`, so sánh đọc camera
tuần tự với luồng nền, và nhiệt độ CPU trước/sau. Chạy lại script này mỗi khi đổi mô hình hoặc
camera, thay vì phỏng đoán.

Số đo tham chiếu trên bo mạch (4 nhân aarch64):

```text
ObjectDetector.detect()  320px : 208.2 ms/frame
ObjectDetector.detect()  224px : 110.8 ms/frame   -> nhanh 1.88x
Phân tích màu (5 nắp)          :   3.31 ms
Centroid tracking              :   0.20 ms
Đếm cắt vạch                   :   0.06 ms
```

Suy luận AI chiếm **~97%** thời gian mỗi frame — mọi tối ưu khác đều không đáng kể.

---

## 8. Bảng tham số cần tinh chỉnh

Tất cả nằm trong `product/config/config.yaml`.

| Tham số | Ý nghĩa và cách chọn |
| :--- | :--- |
| `counter.line_y` | Tọa độ Y vạch đếm (0–480). **Nguyên nhân phổ biến nhất của việc nắp đi qua mà không đếm.** Phải khớp vị trí thực tế trong khung hình theo góc camera. |
| `counter.buffer_zone` | Vùng đệm chống rung quanh vạch, mặc định 25px. |
| `counter.direction` | `"down"` nếu nắp đi từ trên xuống, `"up"` nếu ngược lại. |
| `model.detect_interval` | Suy luận mỗi N frame. **Giới hạn cứng: nắp không được dịch quá ~30px (nửa đường kính nắp) giữa 2 lần suy luận**, nếu vượt thì tracker mất dấu và đếm hụt âm thầm. Băng tải càng nhanh thì N càng phải nhỏ. |
| `model.input_size` | Phải khớp `IMG_SIZE` đã xuất. Đổi config một mình là vô nghĩa — phải xuất lại mô hình. |
| `camera.fps` | Đặt 30 để không tự giới hạn. Ở `detect_interval: 2` đạt ~15 FPS (đặt 15 hay 30 như nhau); ở `detect_interval: 3` nhờ headroom này mới lên ~19 FPS. |
| `camera.threaded_capture` | Mặc định `false`. **Đo thực tế trên bo mạch này: không nhanh hơn** (15.0 so với 15.0 FPS) vì driver tôn trọng `buffer_size=1`. Chỉ bật khi dùng camera/driver không tôn trọng `buffer_size`, thường là stream RTSP qua mạng, biểu hiện là độ trễ tăng dần theo thời gian chạy. |
| `color.trained_colors` | Danh mục 12 màu cơ bản. **Bỏ một màu khỏi danh sách** nếu muốn hệ thống coi màu đó là `unknown`. Không sửa `color_ranges` trong mã nguồn. |
| `color.confidence_threshold` | Ngưỡng màu đơn chủ đạo, mặc định 0.70. |
| `mqtt.broker` | `localhost` khi broker chạy trên bo mạch (cấu hình hiện tại). |
| `display.show_window` | Để `false` khi chạy headless/SSH. Chương trình cũng tự chuyển sang headless nếu không có `DISPLAY`. |

### Về phân loại màu

Hệ thống nhận **12 màu cơ bản**: `red`, `orange`, `yellow`, `green`, `cyan`, `blue`, `purple`,
`pink`, `brown`, `white`, `gray`, `black`. Ngoài ra còn tự nhận:

- Nắp **2 màu** → nhãn ghép, ví dụ nắp Coca đỏ-trắng ra `red_white`
- Nắp **đa màu** (3 màu xấp xỉ nhau) → `multicolor`
- Màu **ngoài danh mục** hoặc không đồng nhất → `unknown` (đây là yêu cầu của đề bài, không phải lỗi)

---

## 9. Xử lý sự cố

| Hiện tượng | Nguyên nhân | Cách khắc phục |
| :--- | :--- | :--- |
| Chạy xong in banner rồi **thoát im lặng**, không có dòng `[STATUS]` | `model.input_size` lệch với kích thước ONNX | Kiểm tra `input_size` khớp `IMG_SIZE`; xem lỗi thật bằng `python3 -u src/main.py` rồi tìm dòng `[Main Error]` |
| Không có khung hình nào, không báo lỗi | `camera.index` trỏ vào `/dev/video0` (encoder Venus) | Chạy `v4l2-ctl --list-devices`, đổi sang node của webcam (thường `/dev/video2`) |
| `Cannot open /dev/videoN` | Thiếu quyền hoặc cáp lỏng | `sudo usermod -a -G video $USER` rồi đăng nhập lại; `ls -l /dev/video*`; thử cổng USB khác |
| Nắp đi qua mà không đếm | `line_y` sai vị trí | Điều chỉnh `counter.line_y` theo góc camera |
| Đếm hụt khi băng tải chạy nhanh | Nắp dịch quá ~30px giữa 2 lần suy luận | Giảm `detect_interval`, hoặc giảm tốc độ băng tải |
| Nhận diện sai màu | Chiếu sáng không đều, bóng gắt, phản quang | Cải thiện đèn; nếu cần thì nới `color.confidence_threshold` |
| FPS thấp hơn ~15 | Nóng gây tụt tần số, hoặc còn dùng mô hình 320 | Chạy `tools/benchmark_board.py` xem nhiệt độ CPU và thời gian suy luận; gắn tản nhiệt |
| Dashboard không nhận được gì | `BROKER_HOST` chưa trỏ đúng IP bo mạch, hoặc firewall chặn cổng 1883 | Sửa `BROKER_HOST`; kiểm tra bằng `mosquitto_sub -h 192.168.1.252 -t lab/conveyor/counter` |
| Hết dung lượng khi cài đặt | Thẻ nhớ bo mạch gần đầy | Kiểm tra `df -h /`; xóa log và file không dùng |

### Hai hướng tối ưu đã thử và KHÔNG dùng được

Ghi lại để không mất thời gian làm lại:

- **Lượng tử hóa INT8 không dùng được.** `quantize_dynamic` **chậm hơn 12×** so với FP32.
  `quantize_static` (QDQ, per-channel, hiệu chuẩn 40 ảnh) thì nhanh nhưng **phá độ chính xác**:
  bản 320px phát hiện 0 box, bản 224px recall tụt còn 0.586. Đầu ra hồi quy khung của YOLOv8
  không chịu được lượng tử hóa thô. Nếu vẫn muốn thử thì dùng
  `ultralytics export format=tflite int8=True` và **bắt buộc đánh giá lại** trước khi tin.
- **Không có đường dùng NPU.** `onnxruntime` 1.25.1 trên bo mạch chỉ cung cấp
  `AzureExecutionProvider` và `CPUExecutionProvider`; không có `QNNExecutionProvider`, và
  `onnxruntime-qnn` chỉ phát hành cho Windows-on-ARM, không có wheel cho Linux aarch64.
  Muốn chạy NPU/HTP phải chuyển mô hình sang `.dlc` bằng Qualcomm QNN SDK hoặc SNPE — một
  hướng riêng, không phải việc cài thêm package. **Hãy lập kế hoạch trên cơ sở chỉ có CPU.**

---

## 10. Checklist buổi demo

Làm theo thứ tự này trước khi bảo vệ:

- [ ] Cắm webcam, chạy `v4l2-ctl --list-devices`, xác nhận `camera.index` đúng node
- [ ] `python3 -c "import onnxruntime as o; print(o.InferenceSession('models/yolov8n_cap.onnx').get_inputs()[0].shape)"` ra `[1, 3, 224, 224]`
- [ ] `grep input_size config/config.yaml` khớp với kết quả trên
- [ ] `systemctl is-active mosquitto` trả về `active`
- [ ] Chạy `python3 -u src/main.py`, thấy FPS ~15 và dòng `[STATUS]` cập nhật
- [ ] Đặt vài nắp đủ màu lên băng tải, xác nhận log `CẮT VẠCH` và màu đúng
- [ ] Dashboard trên máy tính nhận telemetry, `counter_records.csv` có dòng mới
- [ ] `sudo systemctl enable --now edge_counter.service` để tự chạy khi cắm nguồn
- [ ] Kiểm tra `df -h /` còn đủ dung lượng, và nhiệt độ CPU không quá cao sau 10 phút chạy
