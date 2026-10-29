"""
MQTT Client Module for PC Testing (Giai đoạn 1)
"""

import json
import time
import threading
import paho.mqtt.client as mqtt


class MqttPublisherPC:
    def __init__(self, device_id="pc_test_workstation", broker="localhost", port=1883,
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

        self.client.on_connect = self._on_connect
        self.client.on_disconnect = self._on_disconnect

    def _on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            self.is_connected = True
            print(f"[MQTT PC] Kết nối Broker thành công: {self.broker}:{self.port}")
        else:
            self.is_connected = False

    def _on_disconnect(self, client, userdata, rc):
        self.is_connected = False

    def start(self):
        try:
            self.client.connect_async(self.broker, self.port, keepalive=60)
            self.client.loop_start()
            return True
        except Exception as e:
            print(f"[MQTT PC Warning] Không thể kết nối tới Broker '{self.broker}' ({e}). Hệ thống vẫn chạy độc lập!")
            return False

    def publish_count(self, total_caps, fps, status="running", counts_by_color=None):
        payload = {
            "device_id": self.device_id,
            "timestamp": int(time.time()),
            "total_caps": int(total_caps),
            "counts_by_color": counts_by_color if counts_by_color else {},
            "fps": round(float(fps), 1),
            "status": status
        }
        with self._lock:
            try:
                self.client.publish(self.topic, json.dumps(payload), qos=self.qos)
            except Exception:
                pass

    def stop(self):
        try:
            self.client.loop_stop()
            self.client.disconnect()
        except Exception:
            pass
