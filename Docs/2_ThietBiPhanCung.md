# Thiết Bị Phần Cứng (Hardware Components - Lab Setup)

Tài liệu này liệt kê cấu hình thiết bị phần cứng sử dụng cho mô hình thực nghiệm trong phòng Lab:

---

## 1. Bộ xử lý trung tâm (Edge Board)
**Thiết bị:** Board mạch Arduino thế hệ mới tích hợp SoC Qualcomm (Ví dụ: Dòng tương tự Arduino Pro Portenta trang bị chip cấu hình cao), với thông số:
- **Vi xử lý:** Chip Qualcomm (hỗ trợ NPU/DSP tăng tốc tính toán AI).
- **RAM:** 2GB LPDDR4.
- **Bộ nhớ trong (eMMC/Flash):** 16GB.
- **Hệ điều hành:** Linux (Debian, Ubuntu Core hoặc Yocto).
- **Cổng kết nối ngoại vi:** Cổng **USB Type-C / Type-A (chế độ USB Host)** cho phép cắm trực tiếp Webcam USB.

**Tại sao chọn bo mạch này cho bài Lab?**
- **Cổng USB Host cắm trực tiếp camera:** Có thể cắm ngay đầu cắm USB của Webcam thông dụng mà không cần thêm board mở rộng hay mạch chuyển đổi phức tạp.
- **Tài nguyên 2GB RAM & 16GB Flash:** Đủ tải hệ điều hành Linux và mô hình AI Object Detection (YOLOv8 Nano) vào bộ nhớ mà không lo tràn RAM, 16GB Flash đủ lưu hệ điều hành và thư viện Python/OpenCV.
- **Hệ điều hành Linux:** Dễ dàng cài đặt các thư viện quen thuộc (Python, OpenCV, TensorFlow Lite/ONNX Runtime, Eclipse Paho MQTT) phục vụ lập trình nhanh cho đồ án.

---

## 2. Thiết bị thu nhận hình ảnh (Camera)
**Thiết bị:** **Webcam USB chuẩn UVC (USB Video Class)** thông dụng trong phòng lab, hỗ trợ độ phân giải 720p hoặc VGA (640x480).

**Lý do lựa chọn:**
- **Cắm là nhận (Plug-and-Play):** Nhờ cổng USB của Arduino, đầu USB của Webcam cắm trực tiếp vào bo mạch. Hệ điều hành Linux tự nhận diện qua driver chuẩn `V4L2`, đọc khung hình trong Python cực kỳ đơn giản qua `cv2.VideoCapture(0)`.
- **Dễ bố trí trên bàn Lab:** Dây cáp USB dài và mềm, dễ dàng gắn webcam lên chân tripod hoặc giá kẹp để điều chỉnh khoảng cách và góc nhìn thẳng xuống mặt băng chuyền mini.
- **Độ phân giải phù hợp:** Chỉ cần chạy ở độ phân giải 640x480 để tiết kiệm tài nguyên xử lý và giữ FPS ổn định khi demo.

---

## 3. Mô hình băng chuyền mini và Phụ kiện hỗ trợ
1. **Mô hình băng chuyền mini:** 
   - Băng tải học tập mini (dùng động cơ DC 12V/5V) hoặc cơ cấu trượt phẳng để di chuyển nắp chai qua tầm nhìn camera.
2. **Nguồn cấp:** 
   - Adapter 5V/3A hoặc 12V DC cấp nguồn ổn định cho bo mạch Arduino và nuôi nguồn Webcam qua cổng USB.
3. **Tản nhiệt:** 
   - Miếng tản nhiệt nhôm (Heatsink) gắn trên chip Qualcomm để bo mạch tản nhiệt tốt khi chạy mô hình AI liên tục trong suốt buổi demo bài Lab.
