"""
Camera & Video Source Module for PC Testing (Giai đoạn 1)
Hỗ trợ đọc từ Webcam máy tính HOẶC file video mô phỏng (.mp4) với chế độ tự động lặp.
"""

import time
import cv2


class VideoSource:
    def __init__(self, source_type="webcam", webcam_index=0, video_path="", stream_url="",
                 width=640, height=480, fps=25, loop_video=True):
        self.source_type = source_type.lower()
        self.webcam_index = webcam_index
        self.video_path = video_path
        self.stream_url = stream_url
        self.width = width
        self.height = height
        self.target_fps = fps
        self.loop_video = loop_video

        self.cap = None
        self._is_opened = False

    def open(self):
        """Khởi tạo luồng video (Webcam, Stream LAN RTSP/HTTP, hoặc Video File)."""
        if self.source_type in ["stream", "rtsp", "http"]:
            print(f"[VideoSource] Kết nối tới luồng Camera LAN (RTSP/HTTP): '{self.stream_url}'...")
            # Thiết lập biến môi trường hạ trễ cho RTSP qua TCP nếu là RTSP
            import os
            os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = "rtsp_transport;tcp"
            self.cap = cv2.VideoCapture(self.stream_url)
            if not self.cap.isOpened():
                print(f"[VideoSource Error] Không thể kết nối tới luồng stream LAN: '{self.stream_url}'")
                self._is_opened = False
                return False
            # Giảm bộ đệm để triệt tiêu độ trễ mạng Wi-Fi
            self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

        elif self.source_type == "video":
            print(f"[VideoSource] Mở file video mô phỏng: '{self.video_path}'...")
            self.cap = cv2.VideoCapture(self.video_path)
            if not self.cap.isOpened():
                print(f"[VideoSource Error] Không thể mở file video: '{self.video_path}'")
                self._is_opened = False
                return False
        else:
            print(f"[VideoSource] Mở Webcam PC tại index: {self.webcam_index}...")
            self.cap = cv2.VideoCapture(self.webcam_index)
            if not self.cap.isOpened():
                print(f"[VideoSource Error] Không thể mở Webcam tại index {self.webcam_index}")
                self._is_opened = False
                return False

            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
            self.cap.set(cv2.CAP_PROP_FPS, self.target_fps)

        self._is_opened = True
        actual_w = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        actual_h = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        print(f"[VideoSource] Nguồn video sẵn sàng ({self.source_type.upper()}): {actual_w}x{actual_h}")
        return True

    def read_frame(self):
        """Đọc khung hình kế tiếp. Tự động tua lại nếu là video file và đã đến cuối."""
        if not self._is_opened or self.cap is None:
            return False, None

        ret, frame = self.cap.read()
        if not ret:
            if self.source_type == "video" and self.loop_video:
                # Tua lại đầu video
                self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                ret, frame = self.cap.read()
                if not ret:
                    return False, None
            else:
                return False, None

        if frame.shape[1] != self.width or frame.shape[0] != self.height:
            frame = cv2.resize(frame, (self.width, self.height))

        return True, frame

    def release(self):
        if self.cap is not None:
            self.cap.release()
            self.cap = None
        self._is_opened = False
        print("[VideoSource] Đã giải phóng nguồn video.")
