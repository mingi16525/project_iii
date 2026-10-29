"""
MQTT Client Publisher Module for Edge AI Bottle Cap Counter
Đóng gói JSON payload và xuất bản lên Broker qua giao thức MQTT.
"""

import json
import time
import threading
import paho.mqtt.client as mqtt


class MqttPublisher:
    def __init__(self, device_id="arduino_lab_node", broker="localhost", port=1883,
                 topic="lab/conveyor/counter", qos=0):
        self.device_id = device_id
        self.broker = broker
        self.port = port
        self.topic = topic
        self.qos = qos

        # Tương thích cả paho-mqtt 1.x và 2.x
        try:
            self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1, client_id=f"{self.device_id}_{int(time.time())}")
        except (AttributeError, TypeError):
            self.client = mqtt.Client(client_id=f"{self.device_id}_{int(time.time())}")

        self.is_connected = False
        self._lock = threading.Lock()

        # Cấu hình callbacks
        self.client.on_connect = self._on_connect
        self.client.on_disconnect = self._on_disconnect

    def _on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            self.is_connected = True
            print(f"[MQTT] Đã kết nối thành công tới Broker: {self.broker}:{self.port}")
        else:
            self.is_connected = False
            print(f"[MQTT Warning] Kết nối Broker thất bại, mã lỗi: {rc}")

    def _on_disconnect(self, client, userdata, rc):
        self.is_connected = False
        print(f"[MQTT Warning] Bị ngắt kết nối khỏi Broker (rc={rc}). Tự động thử kết nối lại...")

    def start(self):
        """Khởi động client MQTT trong luồng nền không chặn (Non-blocking)."""
        print(f"[MQTT] Đang kết nối tới Broker {self.broker}:{self.port}...")
        try:
            self.client.connect_async(self.broker, self.port, keepalive=60)
            self.client.loop_start()
            return True
        except Exception as e:
            print(f"[MQTT Error] Không thể kết nối tới Broker {self.broker}: {e}")
            return False

    def publish_count(self, total_caps, fps, status="running", counts_by_color=None):
        """
        Đóng gói và gửi gói tin JSON kết quả đếm lên Topic MQTT.
        """
        payload = {
            "device_id": self.device_id,
            "timestamp": int(time.time()),
            "total_caps": int(total_caps),
            "counts_by_color": counts_by_color if counts_by_color else {},
            "fps": round(float(fps), 1),
            "status": status
        }

        json_str = json.dumps(payload)

        with self._lock:
            try:
                self.client.publish(self.topic, json_str, qos=self.qos)
            except Exception as e:
                print(f"[MQTT Error] Lỗi khi gửi gói tin: {e}")

    def stop(self):
        """Ngắt kết nối và dừng luồng MQTT."""
        print("[MQTT] Đang đóng kết nối MQTT...")
        try:
            self.client.loop_stop()
            self.client.disconnect()
        except Exception:
            pass
        print("[MQTT] Đã dừng MQTT client.")
