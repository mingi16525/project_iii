"""
Data Collection Tool for Bottle Cap Dataset (Giai đoạn 1)
Thu thập ảnh nắp chai từ Webcam PC/USB để xây dựng tập dữ liệu huấn luyện YOLO.
"""

import os
import time
import cv2

import argparse

SAVE_DIR = "training/dataset/images/train"
FRAME_WIDTH = 640
FRAME_HEIGHT = 480


def main():
    parser = argparse.ArgumentParser(description="Công cụ chụp ảnh nắp chai từ Webcam hoặc Luồng Stream LAN")
    parser.add_argument("--source", default="0",
                        help="Camera index (ví dụ: 0) hoặc URL luồng LAN (ví dụ: rtsp://... hoặc http://...:8080/video)")
    args = parser.parse_args()

    os.makedirs(SAVE_DIR, exist_ok=True)

    # Đếm số ảnh hiện có để tiếp tục đặt tên
    existing_files = [f for f in os.listdir(SAVE_DIR) if f.endswith(".jpg")]
    count = len(existing_files)

    # Nhận diện source là số (webcam) hay chuỗi URL (stream LAN)
    source = int(args.source) if args.source.isdigit() else args.source

    if isinstance(source, str):
        print(f"[Data Collector] Đang kết nối tới luồng mạng LAN: '{source}'...")
        os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = "rtsp_transport;tcp"
        cap = cv2.VideoCapture(source)
    else:
        print(f"[Data Collector] Đang mở Webcam USB/PC index: {source}...")
        cap = cv2.VideoCapture(source)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, FRAME_WIDTH)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_HEIGHT)

    if not cap.isOpened():
        print(f"[Error] Không thể mở nguồn video: {args.source}!")
        return

    print("=" * 60)
    print("  CÔNG CỤ THU THẬP DỮ LIỆU ẢNH NẮP CHAI (DATA COLLECTOR)")
    print("=" * 60)
    print(f" Thư mục lưu ảnh: {SAVE_DIR}")
    print(f" Số ảnh đã có sẵn: {count} ảnh")
    print(" HƯỚNG DẪN ĐIỀU KHIỂN:")
    print("  - Phím [SPACE] hoặc [S]: Chụp và lưu 1 ảnh")
    print("  - Phím [A]: Bật/Tắt chế độ tự động chụp mỗi 1.5 giây")
    print("  - Phím [Q]: Thoát công cụ")
    print("=" * 60)

    auto_mode = False
    last_auto_time = time.time()

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        display_frame = frame.copy()

        # Hiển thị hướng dẫn trên màn hình
        mode_text = "AUTO (1.5s)" if auto_mode else "MANUAL (Press SPACE)"
        mode_color = (0, 255, 0) if auto_mode else (0, 255, 255)
        cv2.putText(display_frame, f"Saved: {count} images | Mode: {mode_text}",
                    (20, 35), cv2.FONT_HERSHEY_SIMPLEX, 0.7, mode_color, 2)
        cv2.putText(display_frame, "[SPACE]: Capture  [A]: Toggle Auto  [Q]: Quit",
                    (20, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)

        cv2.imshow("Data Collector - Project III", display_frame)
        key = cv2.waitKey(1) & 0xFF

        # Tự động chụp theo thời gian
        now = time.time()
        if auto_mode and (now - last_auto_time >= 1.5):
            count += 1
            filename = f"cap_{count:04d}.jpg"
            filepath = os.path.join(SAVE_DIR, filename)
            cv2.imwrite(filepath, frame)
            print(f"[Auto Capture] Đã lưu: {filename}")
            last_auto_time = now

        # Chụp thủ công bằng phím cách hoặc S
        if key == ord(' ') or key == ord('s'):
            count += 1
            filename = f"cap_{count:04d}.jpg"
            filepath = os.path.join(SAVE_DIR, filename)
            cv2.imwrite(filepath, frame)
            print(f"[Manual Capture] Đã lưu: {filename}")

        elif key == ord('a'):
            auto_mode = not auto_mode
            last_auto_time = time.time()
            print(f"[Mode] Chế độ chụp tự động: {'BẬT' if auto_mode else 'TẮT'}")

        elif key == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()
    print(f"\n[Hoàn thành] Đã thu thập tổng cộng {count} ảnh trong '{SAVE_DIR}'.")
    print("Bước tiếp theo: Dùng công cụ LabelImg hoặc Roboflow để gán nhãn Bounding Box.")


if __name__ == "__main__":
    main()
