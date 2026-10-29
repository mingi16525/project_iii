# Mô Hình Mô Phỏng Lab: Đếm Nắp Chai Trên Băng Chuyền (Lab Setup & Simulation)

Tài liệu này hướng dẫn thiết lập và thực hiện **buổi thực nghiệm (Lab Demo / PoC) cho đồ án Project III**: Mô phỏng quá trình nắp chai di chuyển qua băng chuyền mini, sử dụng Webcam USB chiếu vào và chạy chương trình đếm tự động trên bo mạch Arduino.

---

## 1. Bố trí mô hình thí nghiệm trong Lab (Lab Setup)

Mô hình thực nghiệm được tối giản hóa tối đa, dễ dàng lắp đặt trên bàn thí nghiệm:

```
                  ┌──────────────────────┐
                  │   Webcam USB (UVC)   │ (Gắn giá kẹp / chân tripod,
                  └──────────┬───────────┘  chiếu thẳng góc xuống băng chuyền)
                             │
                             │ Cáp USB cắm trực tiếp
                             ▼
                  ┌──────────────────────┐
                  │   Board Arduino      │ (Chạy Linux, cấp nguồn 5V/12V)
                  └──────────┬───────────┘
                             │ Xuất kết quả ra màn hình / Serial / MQTT
                             ▼
    ─────────────────────────────────────────────
    ───► [Nắp 1]     [Nắp 2]     ───│───   [Nắp 3] ───►  (Băng chuyền mini chuyển động)
                                  Vạch ảo
    ─────────────────────────────────────────────
```

### Các thành phần chính:
1. **Mô hình băng chuyền mini:** 
   - Sử dụng băng tải mini học tập (dùng động cơ DC/Step nhỏ) hoặc có thể kéo trượt nắp chai thủ công qua vùng quan sát để mô phỏng chuyển động.
2. **Camera:** 
   - Webcam USB thông thường, đặt trên chân đế/giá kẹp cách mặt băng tải khoảng **25cm – 40cm**, hướng thẳng đứng nhìn xuống các nắp chai.
3. **Bo mạch Arduino:** 
   - Cắm đầu USB của Webcam trực tiếp vào cổng USB Host của Arduino.
   - Kết nối Arduino với màn hình hiển thị (qua HDMI hoặc xem qua mạng nội bộ/SSH) để theo dõi demo trực tiếp.

---

## 2. Quy trình xử lý và đếm nắp chai trong bài Lab

Quy trình phần mềm được tinh gọn thành 4 bước chính:

```
[ Đọc Camera USB ] ──► [ Nhận diện nắp chai (YOLO) ] ──► [ Cắt vạch ảo (Line) ] ──► [ In kết quả đếm ]
  (cv2.VideoCapture)         (Vẽ Bounding Box)             (Total += 1)           (Màn hình / MQTT)
```

1. **Mở Camera:** 
   - Script Python mở luồng video từ Webcam USB:
     ```python
     cap = cv2.VideoCapture(0)
     ```
2. **Nhận diện bằng AI:**
   - Mô hình **YOLOv8 Nano** quét từng frame, tìm tọa độ tâm của các nắp chai trong khung hình và vẽ ô vuông (Bounding Box) bao quanh nắp.
3. **Cơ chế đếm qua vạch ảo (Virtual Line):**
   - Chương trình vẽ một đường thẳng ảo (màu đỏ) nằm ngang khung hình tại tọa độ $Y = Y_{line}$.
   - Khi một nắp chai di chuyển trôi qua vạch đỏ từ trên xuống dưới, hệ thống ghi nhận và tăng biến đếm: `total_count += 1`.
   - Để tránh đếm lặp cùng một nắp khi nó còn nằm trong khung hình, hệ thống gán nhãn trạng thái đã đếm cho nắp đó cho tới khi nó ra khỏi tầm nhìn.
4. **Hiển thị & Báo cáo:**
   - Số lượng nắp chai được in trực quan ngay trên góc màn hình video (`COUNT: 15`).
   - Tùy chọn: Gửi số đếm về server/máy tính qua MQTT hoặc hiển thị qua Terminal.

---

## 3. Các bước thực hiện thực nghiệm (Lab Demo Steps)

Khi demo hoặc báo cáo đồ án, quy trình thực hiện gồm các bước:

1. **Bước 1: Chuẩn bị phần cứng**
   - Cắm Webcam USB vào cổng USB của board Arduino.
   - Căn chỉnh ống kính webcam hướng thẳng vào mặt băng chuyền mini.
   - Chuẩn bị một số nắp chai (khoảng 10 - 20 nắp) để làm mẫu thử.

2. **Bước 2: Khởi chạy chương trình**
   - Mở terminal trên Arduino và chạy lệnh:
     ```bash
     python3 count_caps_demo.py
     ```
   - Cửa sổ camera mở lên, hiển thị luồng video cùng một đường vạch đỏ (vạch đếm).

3. **Bước 3: Thực hiện mô phỏng đếm & phân loại màu**
   - Bật công tắc cho băng chuyền mini chạy (hoặc lần lượt đưa các nắp chai đi qua vùng camera).
   - Đưa lần lượt các mẫu nắp: nắp đơn sắc (đỏ, xanh, trắng), nắp phối 2 màu (nắp Coca đỏ chữ trắng, Pepsi xanh chữ trắng), nắp đa màu và nắp màu lạ.
   - Quan sát nắp chai khi vượt qua vạch đỏ:
     - Ô vuông nhận diện đổi màu tương ứng với màu nắp (màu cam cho `MULTICOLOR`, màu tím hồng cảnh báo cho `UNKNOWN COLOR`).
     - Biến đếm `TOTAL` trên màn hình nhảy số tăng dần và bảng `COLOR STATS` cập nhật số lượng nắp của từng loại màu.

4. **Bước 4: Đối chiếu kết quả**
   - Đếm lại số nắp thực tế theo từng màu đã cho qua băng tải và so sánh với con số hiển thị trên chương trình (tổng số nắp và bảng thống kê màu) để đánh giá độ chính xác của bài thí nghiệm.
