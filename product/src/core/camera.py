"""
Camera Reader Module for Edge AI Bottle Cap Counter
Hỗ trợ mở Webcam USB qua chuẩn V4L2 (Bo mạch thực tế),
hoặc Luồng mạng LAN (RTSP/HTTP stream) và Video mô phỏng (File MP4).
Tích hợp cơ chế tự phục hồi kết nối (Auto-reconnect) và luồng đọc nền
để luôn lấy được khung hình mới nhất khi suy luận AI chậm hơn tốc độ camera.
"""

import os
import time
import threading
import cv2


class CameraReader:
    def __init__(self, source_type="webcam", camera_index=0, video_path="",
                 stream_url="", width=640, height=480, fps=15, buffer_size=1, loop_video=True,
                 threaded=True, fourcc="MJPG"):
        self.source_type = source_type.lower()
        self.camera_index = camera_index
        self.video_path = video_path
        self.stream_url = stream_url
        self.width = width
        self.height = height
        self.target_fps = fps
        self.buffer_size = buffer_size
        self.loop_video = loop_video
        self.fourcc = (fourcc or "").upper()

        # Chỉ dùng luồng nền cho nguồn thời gian thực (webcam/stream).
        # File video phải đọc tuần tự đủ mọi frame, nếu bỏ frame thì kết quả đếm sẽ sai.
        self.use_thread = threaded and self.source_type in ("webcam", "stream")

        self.cap = None
        self._is_opened = False

        # Trạng thái luồng đọc nền: chỉ giữ 1 khung hình mới nhất (single-slot)
        self._thread = None
        self._lock = threading.Lock()
        self._latest_frame = None
        self._frame_seq = 0            # tăng mỗi khi luồng nền đọc được 1 frame mới
        self._consumed_seq = 0         # seq của frame mà vòng lặp chính đã lấy
        self._new_frame_event = threading.Event()
        self._stop_event = threading.Event()
        self._read_failed = False
        self.dropped_frames = 0        # số frame camera sinh ra nhưng bị bỏ vì xử lý không kịp

    def open(self):
        """Khởi tạo kết nối tới nguồn video tùy theo cấu hình."""
        if self.source_type == "webcam":
            # camera_index nhận cả số thứ tự (0, 1, 2...) và đường dẫn thiết bị ("/dev/video2").
            # Nên dùng đường dẫn trên bo mạch Qualcomm: /dev/video0 và /dev/video1 là bộ mã hóa /
            # giải mã video cứng Venus của SoC, webcam USB cắm vào sẽ nhận node cao hơn.
            # Kiểm tra đúng node bằng lệnh: v4l2-ctl --list-devices
            source = self.camera_index
            if isinstance(source, str) and source.isdigit():
                source = int(source)
            print(f"[Camera] Đang mở Webcam USB tại: {source}...")

            # Trên Linux ưu tiên chuẩn V4L2 để có độ trễ thấp nhất
            try:
                self.cap = cv2.VideoCapture(source, cv2.CAP_V4L2)
            except Exception:
                self.cap = cv2.VideoCapture(source)

            if not self.cap or not self.cap.isOpened():
                print(f"[Camera Warning] Không thể mở trực tiếp V4L2, thử mở mặc định...")
                self.cap = cv2.VideoCapture(source)

            if not self.cap.isOpened():
                print(f"[Camera Error] Không thể kết nối tới Webcam USB tại: {source}")
                self._is_opened = False
                return False

            # Đặt FOURCC trước kích thước: phần lớn webcam UVC chỉ đạt FPS cao ở chế độ MJPG,
            # chế độ YUYV thô vừa tốn băng thông USB vừa bị giới hạn khung hình.
            if self.fourcc:
                self.cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*self.fourcc))

            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
            self.cap.set(cv2.CAP_PROP_FPS, self.target_fps)
            self.cap.set(cv2.CAP_PROP_BUFFERSIZE, self.buffer_size)

        elif self.source_type == "stream":
            print(f"[Camera] Đang kết nối tới luồng mạng LAN: '{self.stream_url}'...")
            os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = "rtsp_transport;tcp"
            self.cap = cv2.VideoCapture(self.stream_url)
            if not self.cap.isOpened():
                print(f"[Camera Error] Không thể kết nối tới luồng Stream: {self.stream_url}")
                self._is_opened = False
                return False

        elif self.source_type == "video":
            print(f"[Camera] Đang mở file video: '{self.video_path}'...")
            if not os.path.exists(self.video_path):
                print(f"[Camera Error] File video không tồn tại: {self.video_path}")
                self._is_opened = False
                return False
            self.cap = cv2.VideoCapture(self.video_path)
            if not self.cap.isOpened():
                print(f"[Camera Error] Không thể giải mã file video: {self.video_path}")
                self._is_opened = False
                return False

        else:
            print(f"[Camera Error] Loại nguồn không hợp lệ: {self.source_type}")
            return False

        actual_w = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        actual_h = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        actual_fps = self.cap.get(cv2.CAP_PROP_FPS)
        mode = "luồng nền" if self.use_thread else "tuần tự"
        print(f"[Camera] Sẵn sàng ({self.source_type.upper()}): {actual_w}x{actual_h} @ {actual_fps:.1f} FPS "
              f"(Buffer={self.buffer_size}, {mode})")

        self._is_opened = True

        if self.use_thread:
            self._start_thread()

        return True

    def _start_thread(self):
        """Bật luồng nền liên tục đọc camera, chỉ giữ lại khung hình mới nhất."""
        self._stop_event.clear()
        self._read_failed = False
        with self._lock:
            # Đặt lại bộ đếm để không lấy nhầm khung hình cũ còn sót sau khi kết nối lại
            self._latest_frame = None
            self._frame_seq = 0
            self._consumed_seq = 0
        self._new_frame_event.clear()
        self._thread = threading.Thread(target=self._capture_loop, daemon=True)
        self._thread.start()

    def _capture_loop(self):
        """
        Luồng nền: đọc camera không ngừng để hàng đợi của driver V4L2 không bị dồn.
        Nếu vòng lặp chính (suy luận AI) chậm hơn camera thì các frame ở giữa bị bỏ,
        nhờ đó khung hình đưa vào xử lý luôn là khung hình mới nhất thay vì khung hình cũ.
        """
        while not self._stop_event.is_set():
            cap = self.cap
            if cap is None:
                break

            # grab() chỉ lấy khung hình khỏi hàng đợi driver, KHÔNG giải mã nên rất nhẹ.
            # Nhờ đó hàng đợi luôn được dọn mà không tốn CPU giải mã MJPG cho những
            # khung hình sẽ bị bỏ - trên bo mạch 4 nhân, giải mã thừa làm chậm hẳn suy luận.
            if not cap.grab():
                self._read_failed = True
                self._new_frame_event.set()
                time.sleep(0.05)
                continue

            with self._lock:
                # Vòng lặp chính đã lấy frame trước đó chưa? Nếu chưa thì khung hình vừa
                # grab bị bỏ luôn, không cần giải mã.
                consumer_ready = self._frame_seq <= self._consumed_seq
                if not consumer_ready:
                    self.dropped_frames += 1

            if not consumer_ready:
                continue

            # Chỉ giải mã khung hình thực sự sẽ được xử lý.
            # retrieve() cũng gọi từ chính luồng này nên không đụng cap từ 2 luồng.
            ret, frame = cap.retrieve()
            if not ret or frame is None:
                continue

            with self._lock:
                self._latest_frame = frame
                self._frame_seq += 1
            self._new_frame_event.set()

    def _read_frame_threaded(self, timeout_sec=2.0):
        """Lấy khung hình mới nhất mà luồng nền đã đọc được."""
        deadline = time.time() + timeout_sec
        while True:
            with self._lock:
                if self._frame_seq > self._consumed_seq:
                    self._consumed_seq = self._frame_seq
                    return True, self._latest_frame

            if self._read_failed:
                print(f"[Camera] Mất tín hiệu từ {self.source_type.upper()}. Đang thử kết nối lại...")
                if self.reconnect():
                    continue
                return False, None

            if time.time() > deadline:
                print(f"[Camera Warning] Không nhận được khung hình mới sau {timeout_sec:.1f}s.")
                return False, None

            # Chờ luồng nền báo có frame mới thay vì quay vòng tốn CPU
            self._new_frame_event.wait(0.05)
            self._new_frame_event.clear()

    def read_frame(self):
        """Đọc 1 khung hình từ nguồn. Trả về (ret, frame)."""
        if not self._is_opened or self.cap is None:
            return False, None

        if self.use_thread:
            return self._read_frame_threaded()

        ret, frame = self.cap.read()

        if not ret:
            if self.source_type == "video" and self.loop_video:
                # Tua lại đầu video khi chạy hết file
                self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                ret, frame = self.cap.read()
                if ret:
                    return True, frame

            if self.source_type in ["webcam", "stream"]:
                print(f"[Camera] Mất tín hiệu từ {self.source_type.upper()}. Đang thử kết nối lại...")
                if self.reconnect():
                    ret, frame = self.cap.read()
                    return ret, frame

            return False, None

        return True, frame

    def reconnect(self, max_retries=3, delay_sec=1.0):
        """Tự động kết nối lại camera/stream khi bị ngắt quãng."""
        self.release()
        for attempt in range(1, max_retries + 1):
            time.sleep(delay_sec)
            print(f"[Camera] Thử kết nối lại lần {attempt}/{max_retries}...")
            if self.open():
                print("[Camera] Kết nối lại thành công!")
                return True
        print("[Camera Error] Kết nối lại thất bại.")
        return False

    def _stop_thread(self):
        """Dừng luồng đọc nền và chờ nó kết thúc trước khi đóng camera."""
        if self._thread is None:
            return
        self._stop_event.set()
        self._new_frame_event.set()
        self._thread.join(timeout=2.0)
        self._thread = None

    def release(self):
        """Giải phóng camera và dọn bộ nhớ."""
        # Dừng luồng nền TRƯỚC khi release để nó không đọc vào đối tượng đã bị giải phóng
        self._stop_thread()
        if self.cap is not None:
            self.cap.release()
            self.cap = None
        self._is_opened = False
        if self.dropped_frames:
            print(f"[Camera] Đã bỏ {self.dropped_frames} khung hình vì xử lý không theo kịp camera.")
        print("[Camera] Đã giải phóng tài nguyên.")
