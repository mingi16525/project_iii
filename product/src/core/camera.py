"""
Camera Reader Module for Edge AI Bottle Cap Counter
Hỗ trợ mở Webcam USB qua chuẩn V4L2 (Bo mạch thực tế),
hoặc Luồng mạng LAN (RTSP/HTTP stream) và Video mô phỏng (File MP4).
Tích hợp cơ chế tự phục hồi kết nối (Auto-reconnect).
"""

import os
import time
import cv2


class CameraReader:
    def __init__(self, source_type="webcam", camera_index=0, video_path="",
                 stream_url="", width=640, height=480, fps=15, buffer_size=1, loop_video=True):
        self.source_type = source_type.lower()
        self.camera_index = camera_index
        self.video_path = video_path
        self.stream_url = stream_url
        self.width = width
        self.height = height
        self.target_fps = fps
        self.buffer_size = buffer_size
        self.loop_video = loop_video

        self.cap = None
        self._is_opened = False

    def open(self):
        """Khởi tạo kết nối tới nguồn video tùy theo cấu hình."""
        if self.source_type == "webcam":
            print(f"[Camera] Đang mở Webcam USB tại index: {self.camera_index}...")
            # Trên Linux ưu tiên chuẩn V4L2 để có độ trễ thấp nhất
            try:
                self.cap = cv2.VideoCapture(self.camera_index, cv2.CAP_V4L2)
            except Exception:
                self.cap = cv2.VideoCapture(self.camera_index)

            if not self.cap or not self.cap.isOpened():
                print(f"[Camera Warning] Không thể mở trực tiếp V4L2, thử mở mặc định...")
                self.cap = cv2.VideoCapture(self.camera_index)

            if not self.cap.isOpened():
                print(f"[Camera Error] Không thể kết nối tới Webcam USB tại /dev/video{self.camera_index}")
                self._is_opened = False
                return False

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
        print(f"[Camera] Sẵn sàng ({self.source_type.upper()}): {actual_w}x{actual_h} @ {actual_fps:.1f} FPS (Buffer={self.buffer_size})")

        self._is_opened = True
        return True

    def read_frame(self):
        """Đọc 1 khung hình từ nguồn. Trả về (ret, frame)."""
        if not self._is_opened or self.cap is None:
            return False, None

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

    def release(self):
        """Giải phóng camera và dọn bộ nhớ."""
        if self.cap is not None:
            self.cap.release()
            self.cap = None
        self._is_opened = False
        print("[Camera] Đã giải phóng tài nguyên.")
