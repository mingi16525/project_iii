# Giao Thức Truyền Thông và Định Dạng Dữ Liệu (Communication Protocol - Lab Setup)

Tài liệu này quy định giao thức truyền dữ liệu kết quả đếm từ bo mạch Arduino về máy tính giám sát trong môi trường mạng nội bộ phòng Lab.

---

## 1. Định dạng dữ liệu: JSON (JavaScript Object Notation)

Thay vì gửi hình ảnh thô nặng nề về máy tính làm chậm mạng, bo mạch Arduino xử lý ảnh tại chỗ và **chỉ gửi chuỗi văn bản chứa kết quả đếm**.

**Tại sao chọn JSON cho bài Lab?**
- **Đơn giản & Thông dụng:** Cực kỳ dễ đọc bằng mắt thường và được hỗ trợ mặc định bởi Python, Node.js, Web Browser.
- **Dung lượng siêu nhẹ:** Mỗi gói tin chỉ vài chục byte, truyền đi tức thì qua mạng Wi-Fi phòng lab.

---

## 2. Giao thức truyền tải: MQTT (Message Queuing Telemetry Transport)

**Mô hình kết nối trong bài Lab:**
- Arduino và Máy tính cá nhân (Laptop) kết nối chung một mạng Wi-Fi phòng Lab.
- Cài đặt một MQTT Broker nhẹ (như **Mosquitto**) ngay trên Laptop hoặc trên chính Arduino.
- Arduino đóng vai trò là **Publisher** (phát tin kết quả).
- Laptop/Dashboard đóng vai trò là **Subscriber** (nhận tin và hiển thị).

**Ưu điểm của MQTT:**
- Tốc độ truyền nhanh, độ trễ cực thấp.
- Cơ chế Publish/Subscribe giúp tách biệt độc lập giữa bo mạch đo đếm và màn hình hiển thị.

---

## 3. Cấu trúc gói dữ liệu mẫu (JSON Payload)

Khi có nắp chai cắt qua vạch đếm (hoặc định kỳ mỗi 1 giây), Arduino gửi một chuỗi JSON lên Topic MQTT `lab/conveyor/counter`:

```json
{
  "device_id": "arduino_lab_node",
  "timestamp": 1728196993,
  "total_caps": 24,
  "counts_by_color": {
    "red": 10,
    "blue": 6,
    "white": 4,
    "red_white": 2,
    "multicolor": 1,
    "unknown": 1
  },
  "fps": 14.8,
  "status": "running"
}
```

**Ý nghĩa các trường thông tin:**
- `device_id`: Tên định danh bo mạch Arduino trong bài Lab.
- `timestamp`: Thời gian gửi tin (chuẩn UNIX timestamp).
- `total_caps`: Tổng số nắp chai đã đếm được kể từ khi bắt đầu chạy bài test.
- `counts_by_color`: Bảng phân loại chi tiết số lượng theo từng nhóm màu (đơn sắc, phối 2 màu `red_white`, đa màu `multicolor`, và màu lạ `unknown`).
- `fps`: Tốc độ xử lý khung hình hiện tại của mô hình AI trên Arduino.
- `status`: Trạng thái hoạt động của hệ thống (`running`, `stopped`).

---

## 4. Kiểm tra và xem dữ liệu trên máy tính (Testing)

Trong buổi thực nghiệm, người thực hiện có thể dễ dàng kiểm tra dữ liệu nhận về trên máy tính bằng một dòng lệnh Terminal đơn giản:

```bash
# Lắng nghe dữ liệu phát ra từ Arduino qua MQTT
mosquitto_sub -h localhost -t "lab/conveyor/counter"
```
Khi nắp chai trôi qua vạch trên mô hình băng chuyền, màn hình máy tính sẽ in ra gói tin JSON với số đếm tăng lên theo thời gian thực.
