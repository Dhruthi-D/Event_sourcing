from django.shortcuts import render
from django.http import JsonResponse, HttpResponseBadRequest
from django.utils import timezone
import pytz
from .models import SensorLog, CloudLog, UILog, SENSOR_CHOICES
from django.views.decorators.csrf import csrf_exempt
import importlib

# Import SENSOR_STATE and SENSOR_LIST from apps.py
apps_module = importlib.import_module('homeauto.apps')
SENSOR_STATE = apps_module.SENSOR_STATE
SENSOR_LIST = apps_module.SENSOR_LIST


# Logs Page
def logs_page(request):
    UILog.objects.create(
        event_type='interface_opened',
        details='Logs interface opened'
    )

    for key, label in SENSOR_LIST:
        SensorLog.objects.create(
            sensor=key,
            event_type='ui_requests_sensor_data',
            details='UI requested data from sensor'
        )
        CloudLog.objects.create(
            sensor=key,
            event_type='ui_requests_data_from_cloud',
            details='UI requested data from cloud'
        )
        UILog.objects.create(
            event_type='requests_sent_to_cloud',
            details=f'Request sent to cloud for {label} data'
        )
        CloudLog.objects.create(
            sensor=key,
            event_type='data_sent_to_cloud',
            details='Data sent to cloud from UI or sensor'
        )
        SensorLog.objects.create(
            sensor=key,
            event_type='data_sent_to_ui',
            details='Sensor data sent to UI'
        )
        CloudLog.objects.create(
            sensor=key,
            event_type='data_sent_to_ui',
            details='Cloud data sent to UI'
        )
        state = SENSOR_STATE[key]
        if state['on']:
            SensorLog.objects.create(
                sensor=key,
                event_type='ui_requests_sensor_data',
                details='UI requested data from sensor'
            )
            UILog.objects.create(
                event_type='ui_updated_from_sensor',
                details=f'UI updated with data from {label} sensor'
            )
        else:
            CloudLog.objects.create(
                sensor=key,
                event_type='ui_requests_data_from_cloud',
                details='UI requested data from cloud'
            )
            UILog.objects.create(
                event_type='ui_updated_from_cloud',
                details=f'UI updated with data from cloud for {label}'
            )

    # Fetch latest 20 logs newest first
    sensor_logs = SensorLog.objects.all().order_by('-timestamp')[:20]
    cloud_logs = CloudLog.objects.all().order_by('-timestamp')[:20]
    ui_logs = UILog.objects.all().order_by('-timestamp')[:20]

    ist = pytz.timezone('Asia/Kolkata')
    def add_ist(log):
        log.timestamp_ist = timezone.localtime(log.timestamp, ist).strftime('%Y-%m-%d %H:%M:%S')
        return log

    sensor_logs = [add_ist(l) for l in sensor_logs]
    cloud_logs = [add_ist(l) for l in cloud_logs]
    ui_logs = [add_ist(l) for l in ui_logs]

    sensor_states = []
    for key, label in SENSOR_LIST:
        state = SENSOR_STATE[key]
        sensor_states.append({
            'key': key,
            'label': label,
            'on': state['on'],
            'value': state['value'],
        })

    return render(request, 'homeauto/logs_page.html', {
        'sensor_logs': sensor_logs,
        'cloud_logs': cloud_logs,
        'ui_logs': ui_logs,
        'sensor_states': sensor_states,
    })


# Dashboard Page
def dashboard_page(request):
    UILog.objects.create(
        event_type='interface_opened',
        details='Dashboard interface opened'
    )

    dashboard = []
    for key, label in SENSOR_LIST:
        state = SENSOR_STATE[key]
        if state['on']:
            value = state['value']
            ts = state['last_updated']
            source = 'sensor'
        else:
            cloud_entry = CloudLog.objects.filter(sensor=key, value__isnull=False).order_by('-timestamp').first()
            value = cloud_entry.value if cloud_entry else None
            ts = cloud_entry.timestamp if cloud_entry else None
            source = 'cloud'
        dashboard.append({
            'key': key,
            'label': label,
            'on': state['on'],
            'value': value,
            'timestamp': ts,
            'source': source,
        })
        SensorLog.objects.create(
            sensor=key,
            event_type='ui_requests_sensor_data',
            details='UI requested data from sensor'
        )
        CloudLog.objects.create(
            sensor=key,
            event_type='ui_requests_data_from_cloud',
            details='UI requested data from cloud'
        )
        SensorLog.objects.create(
            sensor=key,
            event_type='data_sent_to_ui',
            details='Sensor data sent to UI'
        )
        CloudLog.objects.create(
            sensor=key,
            event_type='data_sent_to_ui',
            details='Cloud data sent to UI'
        )
        if state['on']:
            SensorLog.objects.create(
                sensor=key,
                event_type='ui_requests_sensor_data',
                details='UI requested data from sensor'
            )
            UILog.objects.create(
                event_type='ui_updated_from_sensor',
                details=f'UI updated with data from {label} sensor'
            )
        else:
            CloudLog.objects.create(
                sensor=key,
                event_type='ui_requests_data_from_cloud',
                details='UI requested data from cloud'
            )
            UILog.objects.create(
                event_type='ui_updated_from_cloud',
                details=f'UI updated with data from cloud for {label}'
            )

    return render(request, 'homeauto/dashboard_page.html', {
        'dashboard': dashboard,
        'now': timezone.now(),
    })


# Toggle sensor ON/OFF (AJAX)
@csrf_exempt
def toggle_sensor(request):
    if request.method == 'POST':
        sensor = request.POST.get('sensor')
        if sensor not in SENSOR_STATE:
            return HttpResponseBadRequest('Invalid sensor')
        current_state = SENSOR_STATE[sensor]['on']
        new_state = not current_state
        event_type = 'sensor_on' if new_state else 'sensor_off'
        SensorLog.objects.create(
            sensor=sensor,
            event_type=event_type,
            details=f"{sensor} sensor turned {'ON' if new_state else 'OFF'}"
        )
        CloudLog.objects.create(
            sensor=sensor,
            event_type=event_type,
            details=f"{sensor} sensor turned {'ON' if new_state else 'OFF'} - cloud notified"
        )
        UILog.objects.create(
            event_type=event_type,
            details=f"{sensor} sensor turned {'ON' if new_state else 'OFF'} from UI"
        )
        SENSOR_STATE[sensor]['on'] = new_state
        return JsonResponse({'on': new_state})
    return HttpResponseBadRequest('Invalid method')


# Fetch logs (AJAX)
def fetch_logs(request, log_type):
    ist = pytz.timezone('Asia/Kolkata')

    if log_type == 'sensor':
        logs = SensorLog.objects.all().order_by('-timestamp')[:20]
        data = [
            {
                'timestamp': timezone.localtime(l.timestamp, ist).strftime('%Y-%m-%d %H:%M:%S'),
                'event_type': l.event_type,
                'sensor': l.sensor,
                'value': l.value,
                'details': l.details
            }
            for l in logs
        ]
    elif log_type == 'cloud':
        logs = CloudLog.objects.all().order_by('-timestamp')[:20]
        data = [
            {
                'timestamp': timezone.localtime(l.timestamp, ist).strftime('%Y-%m-%d %H:%M:%S'),
                'event_type': l.event_type,
                'sensor': l.sensor,
                'value': l.value,
                'details': l.details
            }
            for l in logs
        ]
    elif log_type == 'ui':
        logs = UILog.objects.all().order_by('-timestamp')[:20]
        data = [
            {
                'timestamp': timezone.localtime(l.timestamp, ist).strftime('%Y-%m-%d %H:%M:%S'),
                'event_type': l.event_type,
                'details': l.details
            }
            for l in logs
        ]
    else:
        return HttpResponseBadRequest('Invalid log type')
    return JsonResponse({'logs': data})
