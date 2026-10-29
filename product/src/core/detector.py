"""
Object Detector Module for Edge AI Bottle Cap Counter
Hỗ trợ suy luận đa nền tảng:
- TFLite Runtime (tối ưu cho Linux nhúng ARM / Qualcomm Linux)
- ONNX Runtime (tối ưu cho CPU/Edge)
- PyTorch / Ultralytics (cho mô hình .pt)
- Heuristic Mock Mode (chế độ giả lập hình thái nắp chai tròn để test ngay khi chưa có weights)
"""

import os
import cv2
import numpy as np


class ObjectDetector:
    def __init__(self, model_path="models/yolov8n_cap.tflite", input_size=(320, 320),
                 confidence_threshold=0.50, iou_threshold=0.45, runtime="auto"):
        self.model_path = model_path
        self.input_width, self.input_height = input_size
        self.confidence_threshold = confidence_threshold
        self.iou_threshold = iou_threshold
        self.requested_runtime = runtime.lower()

        self.model_obj = None
        self.interpreter = None
        self.input_details = None
        self.output_details = None
        self.backend = "mock"
        self.is_mock_mode = False

        self._load_model()

    def _load_model(self):
        """Khởi tạo runtime và nạp mô hình vào bộ nhớ RAM."""
        if not os.path.exists(self.model_path):
            # Tự động tìm mô hình thay thế cùng tên (.onnx, .tflite, .pt)
            base_no_ext = os.path.splitext(self.model_path)[0]
            candidates = [f"{base_no_ext}.onnx", f"{base_no_ext}.tflite", f"{base_no_ext}.pt"]
            found = False
            for cand in candidates:
                if os.path.exists(cand):
                    print(f"[Detector] Đã tìm thấy file mô hình thay thế: '{cand}'")
                    self.model_path = cand
                    found = True
                    break
            if not found:
                print(f"[Detector Warning] Không tìm thấy file model '{self.model_path}'.")
                print("[Detector] Tự động kích hoạt Heuristic Mock Mode (nhận diện hình thái nắp tròn) để test ngay!")
                self.is_mock_mode = True
                return

        ext = os.path.splitext(self.model_path)[1].lower()

        try:
            if ext == ".pt" or self.requested_runtime in ["pytorch", "pt"]:
                from ultralytics import YOLO
                print(f"[Detector] Đang nạp mô hình PyTorch YOLO: {self.model_path}...")
                self.model_obj = YOLO(self.model_path)
                self.backend = "pytorch"

            elif ext == ".onnx" or self.requested_runtime == "onnx":
                import onnxruntime as ort
                print(f"[Detector] Đang nạp mô hình ONNX Runtime: {self.model_path}...")
                self.model_obj = ort.InferenceSession(self.model_path, providers=['CPUExecutionProvider'])
                self.backend = "onnx"

            elif ext == ".tflite" or self.requested_runtime == "tflite":
                try:
                    import tflite_runtime.interpreter as tflite
                except ImportError:
                    from tensorflow import lite as tflite

                print(f"[Detector] Đang nạp mô hình TFLite Interpreter: {self.model_path}...")
                self.interpreter = tflite.Interpreter(model_path=self.model_path)
                self.interpreter.allocate_tensors()
                self.input_details = self.interpreter.get_input_details()
                self.output_details = self.interpreter.get_output_details()
                self.backend = "tflite"

            else:
                raise ValueError(f"Định dạng model không nhận diện hoặc runtime không hỗ trợ: {ext} / {self.requested_runtime}")

            print(f"[Detector] Nạp mô hình AI thành công ({self.backend.upper()}).")

        except Exception as e:
            print(f"[Detector Error] Lỗi khi nạp mô hình AI ({e}). Chuyển sang Heuristic Mock Mode.")
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

        elif self.backend == "tflite":
            return self._infer_tflite(frame)

        return self._heuristic_mock_detect(frame)

    def _infer_tflite(self, frame):
        h_orig, w_orig = frame.shape[:2]
        img_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        resized = cv2.resize(img_rgb, (self.input_width, self.input_height))
        normalized = resized.astype(np.float32) / 255.0
        input_tensor = np.expand_dims(normalized, axis=0)

        self.interpreter.set_tensor(self.input_details[0]['index'], input_tensor)
        self.interpreter.invoke()
        raw_output = self.interpreter.get_tensor(self.output_details[0]['index'])

        return self._decode_yolo_output(raw_output, (w_orig, h_orig))

    def _infer_onnx(self, frame):
        h_orig, w_orig = frame.shape[:2]
        img_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        resized = cv2.resize(img_rgb, (self.input_width, self.input_height))
        normalized = resized.astype(np.float32) / 255.0
        input_tensor = np.transpose(normalized, (2, 0, 1))
        input_tensor = np.expand_dims(input_tensor, axis=0)

        input_name = self.model_obj.get_inputs()[0].name
        raw_output = self.model_obj.run(None, {input_name: input_tensor})[0]

        return self._decode_yolo_output(raw_output, (w_orig, h_orig))

    def _decode_yolo_output(self, raw_output, orig_shape):
        orig_w, orig_h = orig_shape
        scale_x = self.input_width / orig_w
        scale_y = self.input_height / orig_h

        predictions = np.squeeze(raw_output)
        if len(predictions.shape) == 2 and predictions.shape[0] < predictions.shape[1]:
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
                results.append([max(0, x1), max(0, y1), min(orig_w, x1 + bw), min(orig_h, y1 + bh), confidences[idx], 0])
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
