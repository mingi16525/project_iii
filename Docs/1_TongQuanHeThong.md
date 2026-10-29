# Tổng Quan Hệ Thống (System Overview - Project III)

## 1. Mục tiêu đồ án
Xây dựng một mô hình thực nghiệm **Edge AI (Trí tuệ nhân tạo tại biên)** trong phòng thí nghiệm (Lab Demo) nhằm tự động đếm số lượng nắp chai di chuyển trên mô hình băng chuyền mini. Hệ thống sử dụng dữ liệu hình ảnh trực tiếp từ **Webcam USB**, xử lý nhận diện và đếm cục bộ ngay trên **bo mạch Arduino (SoC Qualcomm, 2GB RAM, chạy Linux)**, sau đó gửi kết quả đếm (metadata/JSON) về máy tính giám sát hoặc hiển thị trực tiếp.

## 2. Kiến trúc hệ thống
Mô hình thực nghiệm gồm 3 khối tinh gọn:
1. **Khối thu thập hình ảnh:** Webcam USB chuẩn UVC cắm trực tiếp vào cổng USB của Arduino, đặt trên giá đỡ chiếu góc 90° xuống mặt băng chuyền mini.
2. **Khối xử lý biên (Edge AI):** Bo mạch Arduino (Qualcomm, 2GB RAM, chạy Linux) nhận luồng video qua giao tiếp USB, chạy mô hình AI nhận diện vật thể (YOLOv8n) và thuật toán đếm qua vạch ảo theo thời gian thực.
3. **Khối hiển thị & giám sát:** Hiển thị trực tiếp khung hình nhận diện và số lượng đếm lên màn hình/Terminal của Arduino, đồng thời gửi gói tin JSON qua mạng nội bộ (MQTT/Wi-Fi) về máy tính cá nhân để đối soát số liệu.

## 3. Luồng xử lý dữ liệu (Data Pipeline)
- **Bước 1:** Đọc luồng video từ Webcam USB thông qua thư viện OpenCV (`cv2.VideoCapture(0)`) ở độ phân giải 640x480.
- **Bước 2:** Tiền xử lý khung hình (Resize về kích thước đầu vào của model, chuẩn hóa điểm ảnh).
- **Bước 3:** Chạy mô hình suy luận **YOLOv8 Nano** để phát hiện nắp chai và trích xuất Bounding Box.
- **Bước 3b:** Phân loại màu sắc nắp chai qua không gian màu HSV vùng lõi (Center ROI) với chiến lược 4 tầng: đơn sắc (`red`, `blue`...), phối 2 màu (ví dụ Coca `red_white`), đa màu (`multicolor` khi 3 màu hòa nhau), và màu lạ (`unknown`).
- **Bước 4:** Áp dụng logic đếm qua vạch ảo: Khi nắp chai di chuyển cắt qua đường vạch ảo nằm ngang trên màn hình theo chiều băng tải, hệ thống tăng biến đếm tổng `total_caps += 1`, cập nhật biến đếm chi tiết theo nhóm màu và đánh dấu trạng thái tránh đếm lặp.
- **Bước 5:** Đóng gói kết quả đếm (tổng số nắp và phân loại chi tiết theo màu) thành chuỗi JSON và gửi qua giao thức MQTT về máy tính giám sát, đồng thời hiển thị số đếm lên khung hình demo.
- **Bước 6:** Giải phóng bộ nhớ frame ảnh khỏi RAM và tiếp tục lặp lại chu kỳ với frame tiếp theo.

## 4. Danh mục tài liệu của đồ án
1. [1_TongQuanHeThong.md](file:///d:/2026.1/ProjectIII/Docs/1_TongQuanHeThong.md): Tổng quan mục tiêu, kiến trúc và luồng xử lý của đồ án Lab.
2. [2_ThietBiPhanCung.md](file:///d:/2026.1/ProjectIII/Docs/2_ThietBiPhanCung.md): Danh mục thiết bị phần cứng (Arduino Qualcomm Linux, Webcam USB, băng chuyền mini, nguồn).
3. [3_ThuatToanVaXuLy.md](file:///d:/2026.1/ProjectIII/Docs/3_ThuatToanVaXuLy.md): Thuật toán nhận diện YOLOv8n, quy trình xử lý ảnh và logic đếm qua vạch ảo.
4. [4_GiaoThucTruyenThong.md](file:///d:/2026.1/ProjectIII/Docs/4_GiaoThucTruyenThong.md): Định dạng dữ liệu JSON, giao thức MQTT gửi kết quả về máy tính.
5. [5_VanHanhVaUngDungThucTe.md](file:///d:/2026.1/ProjectIII/Docs/5_VanHanhVaUngDungThucTe.md): Bố trí mô hình Lab, nguyên lý đếm mô phỏng và kịch bản thực nghiệm demo.
