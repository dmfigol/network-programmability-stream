from django.shortcuts import render, redirect
from django.http import HttpResponse, HttpRequest, JsonResponse
from napalm import get_network_driver
from netmiko import ConnectHandler

from celery.result import AsyncResult

from .models import Device
from network import tasks

def index(request: HttpRequest) -> HttpResponse:
    devices = Device.objects.all()
    context = {
        'title': 'Hello stream!',
        'name': 'Dmitry',
        'devices': devices
    }
    return render(request, 'base.html', context)


def get_device_stats(request: HttpRequest, device_id) -> HttpResponse:
    if request.method == 'GET':
        device = Device.objects.get(pk=device_id)
        driver = get_network_driver(device.napalm_driver)
        with driver(device.host, device.username, device.password) as device_conn:
            interfaces = device_conn.get_interfaces()
        context = {
            'device': device,
            'interfaces': interfaces,
        }
        return render(request, 'device.html', context)
    elif request.method == 'POST':
        interface_name = request.POST.get("interface_name")
        enable_interface = request.POST.get("enable")
        task_id = tasks.switch_interface.delay(device_id, interface_name, enable_interface).id
        return HttpResponse(f"<p>Interface {interface_name} is being switched [task id: {task_id}] </p><p><a href=\"/device/{device_id}\">Go to device interfaces page</a></p>")


def get_task_status(request: HttpRequest, task_id: str) -> JsonResponse:
    task = AsyncResult(task_id)
    data = {
        "id": task_id,
        "status": task.state,
        "result": task.result
    }
    return JsonResponse(data)
