"""
Monitoring Subscriber Script (Chạy trên Máy tính / Laptop)
Nhận gói tin JSON từ bo mạch Arduino qua MQTT, hiển thị trực quan và lưu log CSV.
"""

import os
import csv
import json
import time
from datetime import datetime
import paho.mqtt.client as mqtt

BROKER_HOST = "localhost"   # Thay bằng IP của Broker (hoặc localhost nếu chạy broker trên Laptop)
BROKER_PORT = 1883
TOPIC = "lab/conveyor/counter"
CSV_FILE = "counter_records.csv"


def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("=" * 60)
        print(" [MONITOR] ĐÃ KẾT NỐI BROKER THÀNH CÔNG!")
        print(f" [MONITOR] Đang lắng nghe trên Topic: '{TOPIC}'...")
        print("=" * 60)
        client.subscribe(TOPIC)
    else:
        print(f"[MONITOR Warning] Kết nối thất bại, mã lỗi: {rc}")


def on_message(client, userdata, msg):
    try:
        payload_str = msg.payload.decode("utf-8")
        data = json.loads(payload_str)

        device_id = data.get("device_id", "unknown")
        timestamp = data.get("timestamp", int(time.time()))
        total_caps = data.get("total_caps", 0)
        counts_by_color = data.get("counts_by_color", {})
        fps = data.get("fps", 0.0)
        status = data.get("status", "unknown")

        time_str = datetime.fromtimestamp(timestamp).strftime("%H:%M:%S")

        # Chuỗi tóm tắt màu sắc
        color_str = ""
        if counts_by_color:
            color_parts = [f"{k.upper()}:{v}" for k, v in counts_by_color.items() if v > 0]
            if color_parts:
                color_str = " | " + " ".join(color_parts)

        # In bảng giám sát dòng thời gian thực
        print(f"[{time_str}] Device: {device_id:<18} | COUNT: {total_caps:>3} nắp{color_str:<25} | FPS: {fps:>4.1f} | Status: {status}")

        # Ghi vào file CSV đối soát
        file_exists = os.path.exists(CSV_FILE)
        with open(CSV_FILE, mode="a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            if not file_exists:
                writer.writerow(["time", "device_id", "total_caps", "color_breakdown", "fps", "status"])
            writer.writerow([time_str, device_id, total_caps, json.dumps(counts_by_color), fps, status])

    except Exception as e:
        print(f"[MONITOR Error] Lỗi giải mã gói tin: {e}")


def main():
    import argparse
    parser = argparse.ArgumentParser(description="MQTT Monitoring Subscriber Dashboard")
    parser.add_argument("--broker", default="192.168.1.52", help="Địa chỉ IP của MQTT Broker (mặc định IP bo mạch: 192.168.1.52)")
    parser.add_argument("--port", type=int, default=1883, help="Cổng MQTT (mặc định 1883)")
    args = parser.parse_args()

    broker_host = args.broker
    broker_port = args.port

    print(f"[MONITOR] Đang kết nối tới MQTT Broker tại {broker_host}:{broker_port}...")
    try:
        client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1, client_id=f"monitor_dashboard_{int(time.time())}")
    except (AttributeError, TypeError):
        client = mqtt.Client(client_id=f"monitor_dashboard_{int(time.time())}")
    client.on_connect = on_connect
    client.on_message = on_message

    try:
        client.connect(broker_host, broker_port, 60)
        client.loop_forever()
    except KeyboardInterrupt:
        print("\n[MONITOR] Đang dừng giám sát...")
        client.disconnect()
    except Exception as e:
        print(f"[MONITOR Error] Không thể kết nối tới Broker: {e}")


if __name__ == "__main__":
    main()
