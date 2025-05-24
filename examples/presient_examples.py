#!/usr/bin/env python3
"""
PresientDB Example Scripts
Demonstrates various use cases for the PresientDB time-series database
"""

import json
import time
import random
from datetime import datetime, timedelta, timezone
import paho.mqtt.client as mqtt

# MQTT Configuration
MQTT_BROKER = "localhost"  # Change to "mosquitto" if running in Docker
MQTT_PORT = 1883
BASE_TOPIC = "presient"

# Try to detect if we should use Docker hostname
import socket
try:
    # Test connection to localhost
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(1)
    result = sock.connect_ex(('localhost', MQTT_PORT))
    sock.close()
    if result != 0:
        # If localhost fails, try Docker service name
        MQTT_BROKER = "mosquitto"
        print(f"ℹ️  Using Docker hostname: {MQTT_BROKER}")
except:
    pass

class PresientExample:
    """Base class for PresientDB examples"""
    
    def __init__(self, client_id="presient-example"):
        # Use the new callback API version for paho-mqtt 2.0+
        self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id)
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.on_publish = self.on_publish
        
    def on_connect(self, client, userdata, flags, rc, properties=None):
        """Callback for when the client connects to the broker"""
        if rc == 0:
            print(f"✓ Connected to MQTT broker at {MQTT_BROKER}:{MQTT_PORT}")
            # Subscribe to response topics
            client.subscribe(f"{BASE_TOPIC}/response/#")
        else:
            print(f"✗ Failed to connect, return code {rc}")
    
    def on_message(self, client, userdata, msg):
        """Callback for when a message is received"""
        print(f"📩 Received: {msg.topic}")
        try:
            payload = json.loads(msg.payload.decode())
            print(f"   Data: {json.dumps(payload, indent=2)}")
        except:
            print(f"   Data: {msg.payload.decode()}")
    
    def on_publish(self, client, userdata, mid, reason_code=None, properties=None):
        """Callback for when a message is published"""
        print(f"📤 Message {mid} published successfully")
    
    def connect(self):
        """Connect to the MQTT broker"""
        try:
            self.client.connect(MQTT_BROKER, MQTT_PORT, 60)
            self.client.loop_start()
            time.sleep(1)  # Give it time to connect
        except Exception as e:
            print(f"❌ Connection failed: {e}")
            print(f"   Make sure the MQTT broker is running on {MQTT_BROKER}:{MQTT_PORT}")
            raise

# Example 1: Basic Sensor Data Ingestion
def example_sensor_data():
    """Demonstrates sending temperature sensor data to PresientDB"""
    print("\n=== Example 1: Sensor Data Ingestion ===")
    
    example = PresientExample("sensor-example")
    example.connect()
    
    # Simulate temperature sensor readings
    sensor_id = "temp-sensor-01"
    location = "living-room"
    
    print(f"\n📊 Sending temperature data for {sensor_id}")
    
    for i in range(5):
        # Generate realistic temperature data
        temperature = 20 + random.uniform(-2, 2)
        humidity = 50 + random.uniform(-10, 10)
        
        # Create the data point
        data_point = {
            "measurement": "environmental",
            "tags": {
                "sensor_id": sensor_id,
                "location": location,
                "type": "DHT22"
            },
            "fields": {
                "temperature": round(temperature, 2),
                "humidity": round(humidity, 2)
            },
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        # Publish to PresientDB
        topic = f"{BASE_TOPIC}/write/sensors/{sensor_id}"
        example.client.publish(topic, json.dumps(data_point))
        
        print(f"   Sent: temp={temperature:.2f}°C, humidity={humidity:.2f}%")
        time.sleep(2)
    
    time.sleep(2)
    example.client.loop_stop()
    example.client.disconnect()

# Example 2: Time-based Queries
def example_time_queries():
    """Demonstrates querying data from PresientDB"""
    print("\n=== Example 2: Time-based Queries ===")
    
    example = PresientExample("query-example")
    example.connect()
    
    # Query 1: Get last hour of data
    print("\n🔍 Query 1: Last hour of temperature data")
    query1 = {
        "measurement": "environmental",
        "fields": ["temperature", "humidity"],
        "tags": {"location": "living-room"},
        "time_range": {
            "start": (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat(),
            "end": datetime.now(timezone.utc).isoformat()
        }
    }
    
    topic = f"{BASE_TOPIC}/query/time-range"
    example.client.publish(topic, json.dumps(query1))
    time.sleep(2)
    
    # Query 2: Get data with aggregation
    print("\n🔍 Query 2: Average temperature by hour")
    query2 = {
        "measurement": "environmental",
        "fields": ["temperature"],
        "aggregation": {
            "function": "mean",
            "interval": "1h",
            "group_by": ["location"]
        },
        "time_range": {
            "start": (datetime.now(timezone.utc) - timedelta(days=1)).isoformat(),
            "end": datetime.now(timezone.utc).isoformat()
        }
    }
    
    topic = f"{BASE_TOPIC}/query/aggregate"
    example.client.publish(topic, json.dumps(query2))
    time.sleep(2)
    
    example.client.loop_stop()
    example.client.disconnect()

# Example 3: Batch Data Import
def example_batch_import():
    """Demonstrates batch importing historical data"""
    print("\n=== Example 3: Batch Data Import ===")
    
    example = PresientExample("batch-example")
    example.connect()
    
    print("\n📦 Importing historical data batch")
    
    # Generate batch of historical data
    batch_data = []
    base_time = datetime.now(timezone.utc) - timedelta(hours=24)
    
    for i in range(50):
        timestamp = base_time + timedelta(minutes=i*30)
        batch_data.append({
            "measurement": "power_usage",
            "tags": {
                "meter_id": "main-meter",
                "building": "office-a"
            },
            "fields": {
                "voltage": 230 + random.uniform(-5, 5),
                "current": 10 + random.uniform(-2, 2),
                "power": 2300 + random.uniform(-200, 200)
            },
            "timestamp": timestamp.isoformat()
        })
    
    # Send batch
    batch_message = {
        "points": batch_data,
        "precision": "ms"
    }
    
    topic = f"{BASE_TOPIC}/write/batch"
    example.client.publish(topic, json.dumps(batch_message))
    print(f"   Sent batch of {len(batch_data)} data points")
    
    time.sleep(2)
    example.client.loop_stop()
    example.client.disconnect()

# Example 4: Real-time Monitoring
def example_realtime_monitor():
    """Demonstrates real-time monitoring with callbacks"""
    print("\n=== Example 4: Real-time Monitoring ===")
    
    class MonitoringExample(PresientExample):
        def __init__(self):
            super().__init__("monitor-example")
            self.threshold_temp = 25.0
            self.alert_count = 0
        
        def on_connect(self, client, userdata, flags, rc, properties=None):
            super().on_connect(client, userdata, flags, rc, properties)
            # Subscribe to sensor data
            client.subscribe(f"{BASE_TOPIC}/data/sensors/+/temperature")
            print(f"📡 Monitoring temperature (threshold: {self.threshold_temp}°C)")
        
        def on_message(self, client, userdata, msg):
            """Check for threshold violations"""
            try:
                data = json.loads(msg.payload.decode())
                temp = data.get('fields', {}).get('temperature', 0)
                
                if temp > self.threshold_temp:
                    self.alert_count += 1
                    print(f"⚠️  ALERT: Temperature {temp}°C exceeds threshold!")
                    
                    # Send alert
                    alert = {
                        "alert_type": "temperature_high",
                        "sensor": data.get('tags', {}).get('sensor_id', 'unknown'),
                        "value": temp,
                        "threshold": self.threshold_temp,
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    }
                    client.publish(f"{BASE_TOPIC}/alerts/temperature", json.dumps(alert))
                else:
                    print(f"✓ Temperature normal: {temp}°C")
                    
            except Exception as e:
                print(f"Error processing message: {e}")
    
    monitor = MonitoringExample()
    monitor.connect()
    
    print("\n🔴 Monitoring for 20 seconds... (Press Ctrl+C to stop)")
    try:
        time.sleep(20)
    except KeyboardInterrupt:
        print("\n👋 Stopping monitor...")
    
    print(f"\n📊 Total alerts: {monitor.alert_count}")
    monitor.client.loop_stop()
    monitor.client.disconnect()

# Example 5: Data Export
def example_data_export():
    """Demonstrates exporting data in different formats"""
    print("\n=== Example 5: Data Export ===")
    
    example = PresientExample("export-example")
    example.connect()
    
    # Export to CSV
    print("\n📄 Requesting CSV export")
    export_request = {
        "format": "csv",
        "measurement": "environmental",
        "fields": ["temperature", "humidity"],
        "time_range": {
            "start": (datetime.now(timezone.utc) - timedelta(days=7)).isoformat(),
            "end": datetime.now(timezone.utc).isoformat()
        },
        "output": "weekly_environmental_data.csv"
    }
    
    topic = f"{BASE_TOPIC}/export/request"
    example.client.publish(topic, json.dumps(export_request))
    time.sleep(2)
    
    # Export to JSON with aggregation
    print("\n📄 Requesting JSON export with daily averages")
    export_request2 = {
        "format": "json",
        "measurement": "power_usage",
        "fields": ["power"],
        "aggregation": {
            "function": "mean",
            "interval": "1d"
        },
        "time_range": {
            "start": (datetime.now(timezone.utc) - timedelta(days=30)).isoformat(),
            "end": datetime.now(timezone.utc).isoformat()
        },
        "output": "monthly_power_average.json"
    }
    
    example.client.publish(topic, json.dumps(export_request2))
    time.sleep(2)
    
    example.client.loop_stop()
    example.client.disconnect()

# Main execution
if __name__ == "__main__":
    print("🚀 PresientDB Example Scripts")
    print("=" * 40)
    
    examples = [
        ("Sensor Data Ingestion", example_sensor_data),
        ("Time-based Queries", example_time_queries),
        ("Batch Data Import", example_batch_import),
        ("Real-time Monitoring", example_realtime_monitor),
        ("Data Export", example_data_export)
    ]
    
    print("\nAvailable examples:")
    for i, (name, _) in enumerate(examples, 1):
        print(f"{i}. {name}")
    print("0. Run all examples")
    
    try:
        choice = input("\nSelect an example (0-5): ").strip()
        
        if choice == "0":
            for name, func in examples:
                func()
                print("\n" + "="*40)
        elif choice.isdigit() and 1 <= int(choice) <= len(examples):
            examples[int(choice)-1][1]()
        else:
            print("Invalid choice!")
            
    except KeyboardInterrupt:
        print("\n\n👋 Goodbye!")
    except Exception as e:
        print(f"\n❌ Error: {e}")