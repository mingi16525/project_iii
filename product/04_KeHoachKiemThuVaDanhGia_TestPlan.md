# Kế Hoạch Kiểm Thử và Đánh Giá Chất Lượng (Test & Validation Plan)
**Dự Án:** Hệ Thống Edge AI Đếm Nắp Chai Trên Băng Chuyền Mini  
**Phiên Bản:** 1.0  
**Tài liệu liên quan:** [Docs/](file:///d:/2026.1/ProjectIII/Docs) | [01_DacTaYeuCauSanPham_PRD.md](file:///d:/2026.1/ProjectIII/product/01_DacTaYeuCauSanPham_PRD.md)

---

## 1. Mục tiêu & Phạm vi kiểm thử (Objectives & Scope)

### 1.1. Mục tiêu
- Đánh giá độ chính xác của mô hình nhận diện AI nắp chai trên thiết bị biên.
- Kiểm chứng tính tin cậy của thuật toán theo dõi và logic đếm qua vạch ảo, đặc biệt là khả năng **chống đếm trùng** và **chống bỏ sót**.
- Xác minh hiệu năng thời gian thực (FPS $\ge 10$), độ trễ truyền dữ liệu MQTT ($\le 100$ ms) và tính ổn định tài nguyên (RAM $\le 1.2$ GB).

### 1.2. Phạm vi kiểm thử
1. **Kiểm thử đơn vị (Unit Testing):** Các hàm tiền xử lý ảnh, giải mã tensor NMS, hàm tính khoảng cách centroid, hàm tuần tự hóa JSON.
2. **Kiểm thử tích hợp (Integration Testing):** Luồng xử lý từ Camera $\to$ AI Inference $\to$ Tracking $\to$ MQTT Client.
3. **Kiểm thử thực nghiệm hệ thống (System & Field Testing):** Chạy thực tế trên mô hình băng chuyền mini với các kịch bản nắp chai thật.
4. **Kiểm thử độ bền & Ổn định (Endurance Testing):** Chạy liên tục từ 30 đến 60 phút để theo dõi nhiệt độ chip và rò rỉ bộ nhớ.

### 1.3. Giới hạn kiểm thử & Điều kiện giả định (Test Limitations & Assumptions)
- **Giới hạn tốc độ băng chuyền:** Chỉ kiểm thử trong dải vận tốc $0.1 - 0.3$ m/s của mô hình mini. Không đánh giá ở tốc độ siêu cao vượt quá khả năng phơi sáng của Webcam UVC thường.
- **Giả định dàn phẳng sản phẩm:** Nắp chai được giả định đi theo từng lớp phẳng trên băng tải, không kiểm thử trường hợp nắp chồng tầng lên nhau 100%.
- **Điều kiện ánh sáng:** Không kiểm thử trong phòng tối hoàn toàn ($< 50$ lux) hoặc dưới nguồn đèn flash chói gắt chiếu trực diện vào thấu kính.

---

## 2. Công thức đo lường & Chỉ số đánh giá (Evaluation Metrics)

### 2.1. Độ chính xác số lượng đếm (Counting Accuracy)
$$\text{Accuracy (\%)} = \left( 1 - \frac{|N_{\text{thực tế}} - N_{\text{hệ thống đếm}}|}{N_{\text{thực tế}}} \right) \times 100\%$$

- **Tỷ lệ đếm trùng (Over-counting Rate):** Khi $N_{\text{hệ thống}} > N_{\text{thực tế}}$ do hiện tượng rung lắc hoặc vạch ảo kích hoạt nhiều lần.
- **Tỷ lệ bỏ sót (Under-counting Rate):** Khi $N_{\text{hệ thống}} < N_{\text{thực tế}}$ do tụt FPS hoặc nắp che khuất nhau.

### 2.2. Hiệu năng hệ thống (System Performance)
- **Tốc độ khung hình (Frame Per Second - FPS):** Đo bằng thời gian hoàn thành 1 chu kỳ xử lý:
  $$\text{FPS} = \frac{1}{T_{\text{capture}} + T_{\text{preprocess}} + T_{\text{inference}} + T_{\text{tracking}} + T_{\text{display}}}$$
- **Mức độ tiêu thụ tài nguyên:** Đo đạc RAM (MB) và CPU (%) thông qua thư viện `psutil` hoặc lệnh `top` trên Linux.

---

## 3. Ma trận kịch bản kiểm thử (Test Cases Matrix)

| Mã Test | Tên kịch bản | Điều kiện đầu vào | Các bước thực hiện | Tiêu chí đạt (Pass Criteria) |
| :--- | :--- | :--- | :--- | :--- |
| **TC-01** | Kết nối & Cấu hình Webcam | Webcam cắm cổng USB Host | 1. Chạy script mở camera.<br>2. Kiểm tra độ phân giải và FPS thu nhận. | Khung hình $640 \times 480$, không bị drop frame, FPS raw $\ge 20$. |
| **TC-02** | Khởi tạo mô hình AI biên | File `.tflite` đặt trong `models/` | 1. Load mô hình vào RAM.<br>2. Chạy thử nghiệm 1 frame giả lập (Dummy tensor). | Nạp model $< 3$ giây, bộ nhớ RAM tăng thêm $< 150$ MB. |
| **TC-03** | Đếm nắp tiêu chuẩn (Single Items) | 20 nắp chai lần lượt đi qua băng chuyền với khoảng cách đều | 1. Bật băng chuyền tốc độ trung bình.<br>2. Cho từng nắp đi qua vạch đếm.<br>3. Ghi nhận số lượng hiển thị. | Số đếm đúng chính xác **$20/20$** ($100\%$), dung sai cho phép: $\ge 19/20$ ($95\%$). |
| **TC-04** | Nắp đi sát nhau (Consecutive Items) | 10 cặp nắp chai đi sát nhau (khoảng cách giữa 2 nắp $< 2$ cm) | 1. Đặt 2 nắp nối đuôi nhau.<br>2. Quan sát Bounding Box của từng nắp khi qua vạch. | Bounding Box phân tách rõ 2 nắp riêng biệt, đếm đúng đủ 2 nắp. |
| **TC-05** | Chống đếm trùng khi nắp dừng trên vạch | 1 nắp chai được đặt đứng yên ngay tại vị trí vạch đỏ | 1. Dừng băng chuyền khi nắp nằm đúng vạch ảo.<br>2. Giữ nguyên trạng thái trong 10 giây.<br>3. Cho nắp tiếp tục đi qua. | Biến đếm chỉ tăng đúng **duy nhất 1 lần**, không bị nhảy số liên tục. |
| **TC-06** | Đa dạng màu sắc & Phân loại đa tầng | 20 nắp gồm: đơn sắc (đỏ, xanh, trắng), nắp phối 2 màu (Coca đỏ-trắng, Pepsi xanh-trắng), nắp 3 màu đa sắc, nắp màu lạ | 1. Lần lượt thả các loại nắp khác nhau lên băng chuyền.<br>2. Ghi nhận nhãn Bounding Box và bảng thống kê màu sắc. | AI phát hiện chính xác: đơn sắc (RED, BLUE), phối 2 màu (RED_WHITE), đa sắc (MULTICOLOR) và cảnh báo màu lạ (UNKNOWN COLOR) đạt độ chính xác $\ge 70\%$. |
| **TC-07** | Biến đổi điều kiện chiếu sáng | Thay đổi ánh sáng phòng Lab (bật đèn, tắt bớt đèn, che bóng) | 1. Đo độ tin cậy nhận diện khi ánh sáng bình thường ($300$ lux).<br>2. Giảm ánh sáng xuống mức yếu ($100$ lux). | Confidence score duy trì $\ge 0.50$, hệ thống không bỏ sót nắp. |
| **TC-08** | Kiểm tra truyền nhận MQTT | Laptop chạy Mosquitto Broker và Subscriber | 1. Kích hoạt đếm nắp trên Arduino.<br>2. Quan sát gói tin nhận được trên Laptop. | Gói tin JSON đến đúng cấu trúc, độ trễ nhận tin $< 100$ ms trên mạng LAN. |
| **TC-09** | Xử lý mất kết nối mạng | Ngắt kết nối Wi-Fi khi đang chạy | 1. Tắt Wi-Fi trong 15 giây.<br>2. Bật lại Wi-Fi. | Chương trình đếm vẫn chạy cục bộ, không crash; tự động kết nối lại MQTT khi có mạng. |
| **TC-10** | Kiểm thử độ bền (Endurance Test) | Chạy liên tục hệ thống trong 45 phút | 1. Cho băng tải chạy tuần hoàn.<br>2. Giám sát lượng RAM sử dụng và nhiệt độ SoC mỗi 5 phút. | RAM không tăng lũy tiến ($< 1.2$ GB), FPS không bị tụt dưới 10, nhiệt độ ổn định. |

---

## 4. Mẫu biên bản ghi nhận kết quả kiểm thử (Test Report Template)

```markdown
### BIÊN BẢN KẾT QUẢ THỬ NGHIỆM ĐẾM NẮP CHAI
- Ngày thực hiện: [YYYY-MM-DD]
- Người kiểm thử: [Họ và tên]
- Thiết bị thử nghiệm: Arduino Qualcomm Linux, Webcam USB, Băng chuyền mini DC 12V
- Phiên bản mô hình: yolov8n_cap_int8.tflite

| Lần thử | Số nắp thực tế | Số nắp đếm được | Sai số (lệch) | Tỷ lệ chính xác | FPS trung bình | Ghi chú |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| 1 | 20 | 20 | 0 | 100% | 13.8 | Ánh sáng chuẩn, nắp xanh |
| 2 | 20 | 19 | -1 | 95% | 13.5 | 1 nắp trôi quá nhanh sát mép |
| 3 | 20 | 20 | 0 | 100% | 14.1 | Nắp trắng và đỏ xen kẽ |
| 4 | 20 | 20 | 0 | 100% | 13.9 | Dừng thử 1 nắp trên vạch |
| **Trung bình** | **80** | **79** | **-1** | **98.75%** | **13.8 FPS** | **ĐẠT YÊU CẦU** |
```
