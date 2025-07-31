from django.apps import AppConfig
import threading
import time
import random
from django.utils import timezone

SENSOR_LIST = [
    ("temperature", "Temperature Sensor"),
    ("humidity", "Humidity Sensor"),
    ("light", "Light Sensor"),
    ("gas", "Gas Leak Sensor"),
    ("motion", "Motion Sensor"),
]

# In-memory state for sensors
SENSOR_STATE = {
    sensor[0]: {"on": True, "value": None, "last_updated": None} for sensor in SENSOR_LIST
}

# Cloud state simulation
CLOUD_STATE = {"busy": False, "down": False}

class HomeautoConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'homeauto'

    def ready(self):
        from .models import SensorLog, CloudLog, UILog
        def sensor_simulation():
            while True:
                # Simulate cloud busy/down states occasionally
                if random.random() < 0.1:  # 10% chance
                    CLOUD_STATE["busy"] = True
                    CloudLog.objects.create(
                        event_type="cloud_busy",
                        details="Cloud server is busy"
                    )
                elif random.random() < 0.05:  # 5% chance
                    CLOUD_STATE["down"] = True
                    CloudLog.objects.create(
                        event_type="cloud_down",
                        details="Cloud server is down"
                    )
                else:
                    CLOUD_STATE["busy"] = False
                    CLOUD_STATE["down"] = False
                
                for sensor_key, sensor_info in SENSOR_STATE.items():
                    if sensor_info["on"]:
                        # Log sensor starts reading
                        if sensor_info["value"] is None:
                            SensorLog.objects.create(
                                sensor=sensor_key,
                                event_type="sensor_starts_reading",
                                details=f"{sensor_key} started reading data"
                            )
                        
                        # Simulate a random value for each sensor
                        value = str(round(random.uniform(20, 100), 2))
                        sensor_info["value"] = value
                        sensor_info["last_updated"] = timezone.now()
                        
                        # Log to SensorLog (append-only)
                        SensorLog.objects.create(
                            sensor=sensor_key,
                            event_type="sensor_value_update",
                            value=value,
                            details=f"{sensor_key} value updated to {value}"
                        )
                        
                        # Log to CloudLog (append-only) - only if cloud is not down
                        if not CLOUD_STATE["down"]:
                            CloudLog.objects.create(
                                event_type="sensor_data_received",
                                sensor=sensor_key,
                                value=value,
                                details=f"{sensor_key} data received by cloud"
                            )
                            CloudLog.objects.create(
                                event_type="new_data_entry",
                                sensor=sensor_key,
                                value=value,
                                details=f"New data entry created for {sensor_key}"
                            )
                        else:
                            CloudLog.objects.create(
                                event_type="data_lost",
                                sensor=sensor_key,
                                details=f"{sensor_key} data lost due to cloud being down"
                            )
                time.sleep(5)  # Simulate every 5 seconds
        t = threading.Thread(target=sensor_simulation, daemon=True)
        t.start()
