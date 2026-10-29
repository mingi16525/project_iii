# Bản Đặc Tả Yêu Cầu Sản Phẩm (Product Requirements Document - PRD)
**Dự Án:** Hệ Thống Edge AI Đếm Nắp Chai Trên Băng Chuyền Mini  
**Phiên Bản:** 1.0 | **Trạng Thái:** Đang Thực Thi  
**Tài liệu liên quan:** [Docs/](file:///d:/2026.1/ProjectIII/Docs) | [00_TongQuan_KeHoachPhatTrien.md](file:///d:/2026.1/ProjectIII/product/00_TongQuan_KeHoachPhatTrien.md)

---

## 1. Bối cảnh & Tầm nhìn sản phẩm (Context & Product Vision)
Trong dây chuyền sản xuất công nghiệp, đếm và phân loại sản phẩm là khâu quan trọng để kiểm soát sản lượng và chất lượng. Các giải pháp truyền thống dựa trên cảm biến quang (Photoelectric sensor) thường gặp nhược điểm: dễ đếm sai khi sản phẩm đi sát nhau, không phân biệt được loại vật thể hay rác lạ.

Sản phẩm này ứng dụng công nghệ **Edge AI** - mang sức mạnh của thị giác máy tính và mạng nơ-ron học sâu (Deep Learning) trực tiếp xuống thiết bị nhúng biên (**Arduino Qualcomm Linux 2GB RAM**), xử lý hình ảnh trực tiếp từ **Webcam USB** với chi phí rẻ, triển khai linh hoạt và gửi dữ liệu số hóa theo thời gian thực về hệ thống điều hành.

---

## 2. Các bên liên quan & Đối tượng sử dụng (Stakeholders & Users)
1. **Người vận hành / Người thực nghiệm (Lab Operator):** Khởi chạy mô hình, đặt nắp chai lên băng chuyền, quan sát màn hình đếm và kiểm tra số liệu.
2. **Hệ thống giám sát trung tâm (Monitoring Client / Laptop):** Nhận gói tin JSON qua mạng nội bộ để lưu trữ và hiển thị thống kê.
3. **Giảng viên & Hội đồng đánh giá (Reviewers):** Kiểm tra tính ổn định, độ trễ, sai số và chất lượng mã nguồn đồ án Project III.

---

## 3. Yêu cầu chức năng (Functional Requirements - FR)

### FR-01: Thu nhận luồng hình ảnh từ Webcam USB (Video Capture Pipeline)
- **FR-01.1:** Hỗ trợ nhận diện tự động thiết bị Webcam USB chuẩn UVC qua giao tiếp V4L2 (`/dev/video0`).
- **FR-01.2:** Thiết lập độ phân giải mặc định $640 \times 480$, tốc độ thu nhận $\ge 15$ FPS.
- **FR-01.3:** Cơ chế tự động thử kết nối lại (Auto-reconnect) nếu camera bị ngắt kết nối tạm thời.
- **FR-01.4:** Tự động giải phóng bộ nhớ của khung hình trước đó nhằm tránh rò rỉ RAM (Memory Leak).

### FR-02: Động cơ suy luận Trí tuệ Nhân tạo tại Biên (Edge AI Inference Engine)
- **FR-02.1:** Tích hợp mô hình nhận diện vật thể nhẹ **YOLOv8 Nano** (hoặc YOLO11 Nano) chạy trên runtime gọn nhẹ (**TFLite Runtime** hoặc **ONNX Runtime**).
- **FR-02.2:** Tiền xử lý hình ảnh: Resize về định dạng đầu vào ($640 \times 640$ hoặc $320 \times 320$), chuẩn hóa điểm ảnh về $[0, 1]$.
- **FR-02.3:** Áp dụng bộ lọc Non-Maximum Suppression (NMS) với ngưỡng IoU Threshold $\ge 0.45$ và Confidence Score Threshold $\ge 0.50$ để lọc nhiễu.
- **FR-02.4:** Trích xuất tọa độ Bounding Box $[x_{min}, y_{min}, x_{max}, y_{max}]$ và tọa độ trọng tâm $(X_c, Y_c)$ của từng nắp chai.

### FR-03: Logic theo dõi đối tượng & Đếm qua vạch ảo (Tracking & Counting Engine)
- **FR-03.1:** Cho phép cấu hình vị trí vạch ảo nằm ngang $Y_{line}$ (mặc định giữa khung hình: $Y = 240$ hoặc $Y = 320$).
- **FR-03.2:** Xác định hướng di chuyển của vật thể (ví dụ: từ trên xuống dưới hoặc từ trái sang phải theo chiều băng tải).
- **FR-03.3:** **Cơ chế chống đếm lặp (Anti-duplicate logic):**
  - Gán định danh tạm thời (Object Tracking ID) hoặc đánh dấu trạng thái `counted = True` cho nắp chai đã vượt qua vạch.
  - Thiết lập vùng đệm bảo vệ (Buffer Zone $\pm 20$ px quanh vạch ảo) để chống hiện tượng rung giật/đứng yên đếm nhiều lần.
- **FR-03.4:** Tăng biến đếm tổng `total_caps += 1` ngay khi nắp chai vượt qua vạch hợp lệ.
- **FR-03.5:** **Phân loại & Đếm theo màu sắc đa tầng (Multi-tier Color Classification):**
  - Tích hợp bộ phân loại màu sắc vùng lõi (Center ROI) trong không gian HSV đối với các màu đã cấu hình (`red`, `blue`, `green`, `yellow`, `white`), cam kết độ chính xác phân loại màu $\ge 70\%$.
  - **Hỗ trợ nắp phối 2 màu (Dual-Color / Bicolor):** Nhận diện chính xác các loại nắp có 2 màu phối hợp (ví dụ nắp Coca-Cola đỏ nền + trắng chữ, Pepsi xanh nền + trắng chữ) với nhãn `RED_WHITE`, `BLUE_WHITE`... khi cả 2 màu đạt tỷ lệ đáng kể và tách biệt màu thứ 3.
  - **Hỗ trợ nắp đa màu (Multicolor):** Tự động phát hiện và gán nhãn `MULTICOLOR` khi nắp có từ 3 màu trở lên phân bổ đồng đều (mỗi màu $\approx 30\text{--}33\%$, không có màu nào chiếm ưu thế tuyệt đối).
  - **Phát hiện màu lạ (Unknown Color):** Tự động phát hiện và gán nhãn **`UNKNOWN COLOR`** đối với bất kỳ màu sắc nào chưa từng được cấu hình hoặc có tỷ lệ nhận diện $< 30\%$.

### FR-04: Hiển thị trực quan & Đóng gói dữ liệu truyền thông (Display & MQTT Reporting)
- **FR-04.1:** Hiển thị trực quan trên màn hình (nếu có GUI/HDMI): Vẽ vạch ảo (đường kẻ màu đỏ), vẽ Bounding Box có màu tương ứng kèm nhãn nhận diện (ví dụ `RED 85%`, `RED_WHITE 90%`, `MULTICOLOR`, `UNKNOWN COLOR`) và bảng thống kê số lượng theo từng màu.
- **FR-04.2:** In log trạng thái ra Terminal định kỳ: Số nắp đếm được, thống kê màu, thời gian, FPS.
- **FR-04.3:** Đóng gói thông điệp theo chuẩn JSON:
  ```json
  {
    "device_id": "arduino_lab_node",
    "timestamp": 1728196993,
    "total_caps": 24,
    "counts_by_color": {
      "red": 10,
      "blue": 6,
      "white": 3,
      "red_white": 2,
      "multicolor": 2,
      "unknown": 1
    },
    "fps": 14.8,
    "status": "running"
  }
  ```
- **FR-04.4:** Xuất bản (Publish) gói tin qua giao thức MQTT lên Broker theo Topic `lab/conveyor/counter`:
  - Phát sự kiện tức thì khi có nắp chai cắt qua vạch.
  - Phát định kỳ theo chu kỳ nhịp tim (Heartbeat) mỗi 2 giây.

### FR-05: Quản lý trạng thái và cấu hình (Configuration & State Management)
- **FR-05.1:** Hỗ trợ nạp thông số cấu hình từ file YAML/JSON (`config.yaml`): Tọa độ vạch đếm, độ phân giải camera, địa chỉ MQTT Broker, ngưỡng tin cậy.
- **FR-05.2:** Hỗ trợ phím tắt điều khiển: Nhấn phím `'q'` để dừng chương trình an toàn, `'r'` để reset bộ đếm về 0.

---

## 4. Yêu cầu phi chức năng (Non-Functional Requirements - NFR)

### NFR-01: Hiệu năng & Tốc độ đáp ứng (Performance)
- Tốc độ suy luận và xử lý của toàn bộ pipeline trên bo mạch Arduino: $\ge 12$ FPS (không dưới 10 FPS).
- Độ trễ phát hiện và tăng biến đếm từ lúc nắp qua vạch đến khi cập nhật: $\le 100$ ms.

### NFR-02: Giới hạn tài nguyên phần cứng (Resource Constraints)
- Tổng dung lượng RAM chiếm dụng của hệ điều hành + ứng dụng Python + mô hình AI: $\le 1.2$ GB (đảm bảo an toàn trong quỹ 2GB LPDDR4).
- Dung lượng bộ nhớ trong eMMC chiếm dụng cho môi trường chạy: $\le 4$ GB.
- Sử dụng CPU ổn định $\le 85\%$, không xảy ra hiện tượng Thermal Throttling kéo dài.

### NFR-03: Độ tin cậy & Ổn định (Reliability)
- Chương trình có khả năng hoạt động liên tục tối thiểu 60 phút mà không xảy ra hiện tượng tràn bộ nhớ (Memory Leak) hoặc Crash đột ngột.
- Xử lý ngoại lệ tốt khi mất luồng camera (camera disconnect) hoặc ngắt kết nối mạng Wi-Fi.

### NFR-04: Tính dễ sử dụng & Khả năng bảo trì (Usability & Maintainability)
- Khởi động hệ thống chỉ bằng 1 dòng lệnh duy nhất: `python3 run_counter.py`.
- Mã nguồn được cấu trúc module hóa rõ ràng (OOP/Modular Pipeline), tuân thủ chuẩn PEP 8.

---

## 5. Tiêu chí nghiệm thu (Acceptance Criteria)

| Mã AC | Tiêu chí đánh giá | Điều kiện đạt (Pass Condition) |
| :--- | :--- | :--- |
| **AC-01** | Kết nối phần cứng | Cắm Webcam USB vào cổng USB Host của Arduino, chạy lệnh `ls /dev/video*` nhận diện `/dev/video0`. |
| **AC-02** | Khởi chạy Inference | Khởi động script thành công, tải mô hình TFLite/ONNX vào RAM trong thời gian $< 5$ giây. |
| **AC-03** | Hiệu năng FPS | Chương trình duy trì tốc độ xử lý ổn định $\ge 10$ FPS trong quá trình có vật thể di chuyển. |
| **AC-04** | Độ chính xác đếm | Cho 20 nắp chai lần lượt đi qua băng chuyền, hệ thống ghi nhận đúng từ 19 - 20 nắp (sai số $\le 5\%$). |
| **AC-05** | Truyền thông MQTT | Chạy lệnh `mosquitto_sub -t "lab/conveyor/counter"` trên Laptop, nhận đầy đủ các gói tin JSON khớp số đếm thực tế. |
| **AC-06** | Ổn định dài hạn | Chạy thử nghiệm 30 phút liên tục, mức RAM sử dụng không tăng lũy tiến theo thời gian. |

---

## 6. Giới hạn của sản phẩm (Product Limitations)

Nhằm đảm bảo tính khả thi trong phạm vi đồ án Project III và cấu hình phần cứng biên phòng Lab, sản phẩm có các giới hạn thiết kế cụ thể sau:

### 6.1. Giới hạn phần cứng & Năng lực tính toán (Hardware & Compute Limitations)
- **Cấu hình biên 2GB RAM:** Hệ thống chạy trên SoC Qualcomm nhúng biên với 2GB LPDDR4 RAM, do đó chỉ phù hợp chạy các mô hình AI rút gọn dạng **Nano (YOLOv8n / YOLO11n)** được lượng tử hóa (Quantization FP16 / INT8). Không hỗ trợ triển khai các mô hình lớn (YOLOv8s, m, l, x) đòi hỏi GPU công suất cao.
- **Giới hạn tốc độ khung hình (10 - 15 FPS):** Tốc độ xử lý của pipeline đạt tối đa khoảng 15 FPS ở độ phân giải $640 \times 480$. Không thể xử lý các luồng video siêu tốc độ cao (> 60 FPS) hoặc độ phân giải siêu nét (4K/FullHD) theo thời gian thực.

### 6.2. Giới hạn cơ học & Tốc độ chuyển động vật thể (Conveyor & Optical Limitations)
- **Tốc độ băng chuyền tối đa:** Phù hợp với băng chuyền mô hình mini có vận tốc di chuyển từ $0.1$ đến $0.3$ m/s (khoảng $1 - 2$ nắp/giây đi qua tầm nhìn). Nếu băng chuyền chạy quá nhanh, hiện tượng nhòe chuyển động (Motion Blur) từ cảm biến Rolling Shutter của Webcam USB sẽ làm giảm độ chính xác nhận diện.
- **Góc đặt Camera:** Yêu cầu góc quan sát cố định nhìn thẳng đứng từ trên xuống ($90^\circ \pm 10^\circ$) ở độ cao khuyến nghị từ **25 cm đến 40 cm**. Hệ thống chưa hỗ trợ nhận diện ở các góc nghiêng lớn ($> 30^\circ$) hoặc camera chuyển động.
- **Vật thể xếp chồng (Occlusion & Stacking):** Nếu hai nắp chai xếp chồng hoàn toàn lên nhau theo phương thẳng đứng, hệ thống chỉ đếm là 1 nắp do tầm nhìn 2D từ trên cao không phân tách được chiều sâu (Z-axis).

### 6.3. Giới hạn môi trường & Chiếu sáng (Environmental Limitations)
- **Môi trường hoạt động:** Thiết kế dành riêng cho môi trường trong nhà (Indoor) / phòng Lab thí nghiệm. Không có chuẩn kháng nước, kháng bụi công nghiệp (IP65/IP67).
- **Điều kiện ánh sáng:** Đòi hỏi nguồn sáng ổn định (cường độ từ $250 - 500$ lux). Hệ thống sẽ giảm độ chính xác khi hoạt động trong môi trường thiếu sáng nghiêm trọng ($< 50$ lux) hoặc bị nguồn sáng gắt chiếu trực diện gây lóa bề mặt bóng của nắp chai.

