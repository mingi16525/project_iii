"""
Object Detector Module for PC Testing (Giai đoạn 1)
Hỗ trợ suy luận trực tiếp với: .pt (PyTorch Ultralytics), .onnx (ONNXRuntime), .tflite, hoặc Mock Mode.
"""

import os
import sys
import cv2
import numpy as np

if sys.platform.startswith("win"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass


class ObjectDetectorPC:
    def __init__(self, model_path="models/yolov8n_cap.onnx", input_size=(320, 320),
                 confidence_threshold=0.50, iou_threshold=0.45, runtime="auto"):
        self.model_path = model_path
        self.input_width, self.input_height = input_size
        self.confidence_threshold = confidence_threshold
        self.iou_threshold = iou_threshold

        self.backend = None
        self.model_obj = None
        self.is_mock_mode = False

        self._init_detector(runtime)

    def _init_detector(self, runtime):
        if not os.path.exists(self.model_path):
            base_no_ext = os.path.splitext(self.model_path)[0]
            candidates = [f"{base_no_ext}.onnx", f"{base_no_ext}.pt", f"{base_no_ext}.tflite"]
            found = False
            for cand in candidates:
                if os.path.exists(cand):
                    print(f"[DetectorPC] Đã tìm thấy file mô hình thay thế: '{cand}'")
                    self.model_path = cand
                    found = True
                    break
            if not found:
                print(f"[DetectorPC Warning] Không tìm thấy file model '{self.model_path}'.")
                print("[DetectorPC] Kích hoạt chế độ Heuristic Mock Detector (Tự động nhận diện hình thái nắp tròn) để test ngay!")
                self.is_mock_mode = True
                return

        ext = os.path.splitext(self.model_path)[1].lower()

        try:
            if ext == ".pt" or runtime == "pytorch":
                from ultralytics import YOLO
                print(f"[DetectorPC] Khởi tạo PyTorch YOLO model: {self.model_path}")
                self.model_obj = YOLO(self.model_path)
                self.backend = "pytorch"

            elif ext == ".onnx" or runtime == "onnx":
                import onnxruntime as ort
                print(f"[DetectorPC] Khởi tạo ONNX Runtime: {self.model_path}")
                self.model_obj = ort.InferenceSession(self.model_path, providers=['CPUExecutionProvider'])
                self.backend = "onnx"

            elif ext == ".tflite" or runtime == "tflite":
                try:
                    import tflite_runtime.interpreter as tflite
                except ImportError:
                    from tensorflow import lite as tflite
                print(f"[DetectorPC] Khởi tạo TFLite Interpreter: {self.model_path}")
                self.model_obj = tflite.Interpreter(model_path=self.model_path)
                self.model_obj.allocate_tensors()
                self.backend = "tflite"

            else:
                raise ValueError(f"Định dạng model không nhận diện: {ext}")

            print(f"[DetectorPC] Nạp mô hình thành công ({self.backend.upper()}).")

        except Exception as e:
            print(f"[DetectorPC Error] Lỗi khi nạp mô hình: {e}")
            print("[DetectorPC] Chuyển sang Heuristic Mock Mode.")
            self.is_mock_mode = True

    def detect(self, frame):
        """
        Nhận diện nắp chai trong khung hình.
        Trả về danh sách Bounding Boxes: [[x1, y1, x2, y2, confidence, class_id], ...]
        """
        if self.is_mock_mode:
            return self._heuristic_mock_detect(frame)

        if self.backend == "pytorch":
            results = self.model_obj.predict(
                frame, imgsz=self.input_width, conf=self.confidence_threshold,
                iou=self.iou_threshold, verbose=False
            )
            boxes = []
            if len(results) > 0 and results[0].boxes is not None:
                for b in results[0].boxes:
                    coords = b.xyxy[0].cpu().numpy().astype(int)
                    conf = float(b.conf[0].cpu().numpy())
                    cls_id = int(b.cls[0].cpu().numpy())
                    boxes.append([coords[0], coords[1], coords[2], coords[3], conf, cls_id])
            return boxes

        elif self.backend == "onnx":
            return self._infer_onnx(frame)

        return self._heuristic_mock_detect(frame)

    def _infer_onnx(self, frame):
        h_orig, w_orig = frame.shape[:2]
        img_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        resized = cv2.resize(img_rgb, (self.input_width, self.input_height))
        normalized = resized.astype(np.float32) / 255.0
        input_tensor = np.transpose(normalized, (2, 0, 1))
        input_tensor = np.expand_dims(input_tensor, axis=0)

        input_name = self.model_obj.get_inputs()[0].name
        raw_output = self.model_obj.run(None, {input_name: input_tensor})[0]

        scale_x = self.input_width / w_orig
        scale_y = self.input_height / h_orig

        predictions = np.squeeze(raw_output)
        if predictions.shape[0] < predictions.shape[1]:
            predictions = predictions.T

        boxes_list = []
        confidences = []

        for row in predictions:
            cx, cy, w, h = row[:4]
            scores = row[4:]
            score = float(np.max(scores)) if len(scores) > 0 else float(row[4])

            if score >= self.confidence_threshold:
                x1 = int((cx - w / 2) / scale_x)
                y1 = int((cy - h / 2) / scale_y)
                bw = int(w / scale_x)
                bh = int(h / scale_y)
                boxes_list.append([x1, y1, bw, bh])
                confidences.append(score)

        indices = cv2.dnn.NMSBoxes(boxes_list, confidences, self.confidence_threshold, self.iou_threshold)
        results = []
        if len(indices) > 0:
            for idx in np.array(indices).flatten():
                x1, y1, bw, bh = boxes_list[idx]
                results.append([max(0, x1), max(0, y1), min(w_orig, x1 + bw), min(h_orig, y1 + bh), confidences[idx], 0])
        return results

    def _heuristic_mock_detect(self, frame):
        """Phát hiện nắp chai dựa trên độ tròn và diện tích - cho phép test ngay lập tức."""
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (7, 7), 2)
        thresh = cv2.adaptiveThreshold(blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                       cv2.THRESH_BINARY_INV, 11, 2)

        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        results = []

        for cnt in contours:
            area = cv2.contourArea(cnt)
            if 800 < area < 30000:
                perimeter = cv2.arcLength(cnt, True)
                if perimeter == 0:
                    continue
                circularity = 4 * np.pi * (area / (perimeter * perimeter))
                if circularity > 0.38:
                    x, y, w, h = cv2.boundingRect(cnt)
                    aspect = float(w) / h
                    if 0.65 <= aspect <= 1.45:
                        results.append([x, y, x + w, y + h, 0.90, 0])

        return results
