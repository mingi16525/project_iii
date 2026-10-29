# Thuật Toán và Xử Lý Dữ Liệu (Algorithm & Processing - Lab Setup)

Tài liệu này trình bày thuật toán trí tuệ nhân tạo và logic đếm nắp chai trên mô hình băng chuyền mini trong phòng thí nghiệm.

---

## 1. Thuật toán nhận diện: YOLO Nano (You Only Look Once)
**Mô hình đề xuất:** **YOLOv8n** (Nano) hoặc **YOLO11n** được huấn luyện/fine-tune trên tập dữ liệu ảnh nắp chai.

**Lý do lựa chọn cho bài Lab:**
1. **Tốc độ xử lý nhanh (Real-time):** YOLO là mô hình One-Stage Detector, xử lý frame ảnh chỉ trong một lần lan truyền tiến, giúp duy trì tốc độ 10 – 15 FPS trên thiết bị biên.
2. **Kích thước gọn nhẹ:** Phiên bản Nano có trọng số mô hình chỉ khoảng 6MB – 10MB, tiêu tốn rất ít bộ nhớ, hoạt động mượt mà trong giới hạn 2GB RAM của board Arduino.
3. **Dễ triển khai trên Linux:** Hỗ trợ xuất sang định dạng **TensorFlow Lite (.tflite)** hoặc **ONNX (.onnx)** để chạy trực tiếp bằng Python trên Linux mà không cần cài đặt các framework nặng nề.

---

## 2. Quy trình xử lý hình ảnh và logic đếm (Processing Pipeline)

Quy trình xử lý khép kín trong chương trình Python trên bo mạch Arduino:

```
[ Đọc Webcam USB ] ──► [ Tiền xử lý ảnh ] ──► [ YOLOv8n Inference ] ──► [ NMS & Lọc Box ] ──► [ Logic Cắt Vạch Ảo ] ──► [ Hiển thị & Gửi đếm ]
  (cv2.VideoCapture)    (Resize 640x640)      (TFLite / ONNX)         (Bounding Box nắp)        (Line Crossing)           (Screen / MQTT)
```

### Bước 1: Thu nhận video từ Webcam USB (Capture)
Sử dụng thư viện OpenCV mở camera thông qua driver V4L2 của Linux:
```python
cap = cv2.VideoCapture(0)  # Cổng USB 0
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
cap.set(cv2.CAP_PROP_FPS, 15)
```

### Bước 2: Tiền xử lý ảnh (Pre-processing)
- Chuyển hệ màu sang RGB nếu cần.
- Thay đổi kích thước (Resize) về kích thước đầu vào chuẩn của mô hình (ví dụ: $640 \times 640$).
- Chuẩn hóa giá trị điểm ảnh về khoảng $[0, 1]$ (chia cho 255.0).

### Bước 3: Suy luận mô hình (Inference)
- Nạp frame đã tiền xử lý vào runtime của mô hình (**TFLite Runtime** hoặc **ONNX Runtime**).
- Mô hình xuất ra ma trận chứa tọa độ các Bounding Box và độ tin cậy (Confidence score) của từng nắp chai được tìm thấy.

### Bước 4: Hậu xử lý (Post-processing)
- Áp dụng thuật toán **Non-Maximum Suppression (NMS)** để lọc bỏ các ô nhận diện chồng chéo lên cùng một nắp chai.
- Rút ra tọa độ tâm ($X_c, Y_c$) của từng nắp chai trong khung hình.

### Bước 4b: Phân loại màu sắc nắp chai (Color Analyzer)
Sau khi có Bounding Box, hệ thống tiến hành trích xuất màu sắc:
1. **Cắt vùng lõi (Center ROI):** Cắt lấy $50\%$ diện tích tâm nắp ($X, Y \in [25\%, 75\%]$) nhằm loại trừ viền nắp, mép răng cưa, bóng phản chiếu và nền băng chuyền.
2. **Chuyển đổi HSV & Tính tỷ lệ dải màu:** Chuyển vùng lõi sang hệ màu HSV, so khớp với các dải màu chuẩn (`red`, `blue`, `green`, `yellow`, `white`), tính tỷ lệ diện tích $r_i$ của từng màu.
3. **Phân loại theo chiến lược 4 tầng:**
   - **Đơn sắc (Single Dominant):** Khi màu top 1 $r_1 \ge 70\%$ (hoặc $r_1 \ge 55\%$ và $r_1 - r_2 \ge 25\%$) $\to$ Gán nhãn đơn màu (ví dụ: `RED`, `BLUE`).
   - **Phối 2 màu (Dual-Color / Bicolor):** Ví dụ nắp Coca-Cola (đỏ nền + trắng chữ) với tỷ lệ ~ 50/50. Khi $r_1 \ge 25\%, r_2 \ge 20\%$, tổng $r_1 + r_2 \ge 50\%$ và màu 2 cách biệt màu 3 ($r_2 - r_3 \ge 8\%$) $\to$ Gán nhãn phối 2 màu: `RED_WHITE`, `BLUE_WHITE`...
   - **Đa màu (Multicolor):** Xảy ra khi có từ 3 màu trở lên phân bổ đồng đều (ví dụ mỗi màu $\approx 30\text{--}33\%$, không màu nào vượt trội $\ge 45\%$) $\to$ Gán nhãn `MULTICOLOR` (khung cam).
   - **Màu lạ (Unknown Color):** Khi nắp có màu ngoài danh mục (tím, xám tối) hoặc tỷ lệ nhận diện $< 30\%$ $\to$ Gán nhãn `UNKNOWN COLOR` (khung tím hồng).

### Bước 5: Logic đếm qua vạch ảo trên băng chuyền (Virtual Line Crossing)
1. **Thiết lập vạch ảo:** Vẽ một đường thẳng nằm ngang khung hình tại vị trí $Y = Y_{line}$ (kèm vùng đệm Buffer Zone chống rung lắc).
2. **Xác định chuyển động & Đếm theo màu:** Khi nắp chai trên băng chuyền mini di chuyển trôi qua tầm nhìn:
   - Nếu tọa độ tâm $Y_c$ của nắp chai chuyển từ phía trên vạch sang phía dưới vạch theo hướng di chuyển của băng tải:
     ```python
     if prev_y <= Y_line and curr_y > Y_line:
         total_caps += 1
         counts_by_color[color_name] += 1
     ```
3. **Chống đếm lặp:** Theo dõi `obj_id` duy nhất của từng nắp chai sau khi đã cắt qua vạch để đảm bảo mỗi nắp chai chỉ được đếm duy nhất 1 lần.

### Bước 6: Hiển thị kết quả & Đóng gói dữ liệu
- Dùng `cv2.putText()` vẽ số lượng đếm tổng (`TOTAL: 12`), Bounding Box tương ứng với màu nắp và bảng thống kê chi tiết theo màu (`COLOR STATS`).
- In log ra Terminal và gửi gói tin JSON qua MQTT về máy tính.
