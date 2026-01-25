import subprocess
import json

def get_device_count():
    with open("arp.json", "r") as file:
        arp = json.load(file)
        ignore_ip = set(item["ip"] for item in arp["ignore"] if item["ip"] is not None)
        ignore_mac = set(item["mac"] for item in arp["ignore"] if item["mac"] is not None)

    result = subprocess.run(["/usr/bin/arp-scan", "--local"], capture_output=True, text=True, timeout=30)
    all_devices = [line.split("\t")[0:3] for line in result.stdout.split("\n") if line.startswith("192.168.")]

    devices = [device for device in all_devices if device[0] not in ignore_ip and device[1] not in ignore_mac]

    return len(devices)
