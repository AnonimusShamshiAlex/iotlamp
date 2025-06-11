import socket
from yeelight import discover_bulbs, Bulb
import tinytuya
import time
import requests

# Порты, часто используемые разными лампами
COMMON_PORTS = {
    "Yeelight": [55443, 1982],
    "Tuya": [6666, 6668],
    "Tasmota/ESPHome": [80, 8080, 8888],
    "Generic": [5353, 5683, 8888]
}

def scan_ports(ip, ports):
    open_ports = []
    for port in ports:
        try:
            with socket.create_connection((ip, port), timeout=0.5):
                open_ports.append(port)
        except:
            continue
    return open_ports

def get_possible_ports(model):
    for name, ports in COMMON_PORTS.items():
        if name.lower() in model.lower():
            return ports
    return [55443, 6668, 8888]

# 🟢 Сканирование Yeelight
def scan_yeelight():
    print("📡 Ищу Yeelight-лампы...")
    bulbs = discover_bulbs(timeout=4)
    results = []
    for b in bulbs:
        ip = b.get("ip")
        model = b.get("model", "Yeelight")
        ports = get_possible_ports(model)
        open_ports = scan_ports(ip, ports)
        results.append({"brand": "Yeelight", "ip": ip, "model": model, "ports": open_ports})
    return results

# 🔶 Сканирование Tuya-устройств
def scan_tuya():
    print("📡 Ищу Tuya-устройства...")
    try:
        devices = tinytuya.deviceScan()
        results = []
        for ip, data in devices.items():
            results.append({
                "brand": "Tuya",
                "ip": ip,
                "model": data.get("product", "Tuya"),
                "ports": scan_ports(ip, COMMON_PORTS["Tuya"])
            })
        return results
    except Exception as e:
        print("⚠ Ошибка Tuya-сканирования:", e)
        return []

# 🔷 Сканирование других устройств (Tasmota, ESPHome и т.д.)
def scan_generic():
    print("📡 Ищу прочие IoT-устройства...")
    prefix = ".".join(socket.gethostbyname(socket.gethostname()).split(".")[:3])
    ips = [f"{prefix}.{i}" for i in range(1, 255)]

    found = []
    for ip in ips:
        ports = scan_ports(ip, COMMON_PORTS["Tasmota/ESPHome"])
        if ports:
            found.append({
                "brand": "Tasmota/Other",
                "ip": ip,
                "model": "Unknown",
                "ports": ports
            })
    return found

# Управление Tasmota через HTTP
def control_tasmota(ip):
    try:
        action = input("Введите 'on' для включения или 'off' для выключения Tasmota-лампы: ").strip().lower()
        if action == "on":
            r = requests.get(f"http://{ip}/cm?cmnd=Power%20On", timeout=2)
        elif action == "off":
            r = requests.get(f"http://{ip}/cm?cmnd=Power%20Off", timeout=2)
        else:
            print("❗ Неизвестная команда.")
            return
        if r.status_code == 200:
            print("✅ Команда отправлена.")
        else:
            print("⚠ Ошибка отправки команды:", r.status_code)
    except Exception as e:
        print("⚠ Ошибка управления Tasmota:", e)

def main():
    all_devices = []
    all_devices += scan_yeelight()
    all_devices += scan_tuya()
    all_devices += scan_generic()

    if not all_devices:
        print("❌ Ничего не найдено.")
        return

    print("\n🔍 Найденные устройства:")
    for i, d in enumerate(all_devices, 1):
        print(f"{i}. {d['brand']} ({d['ip']}) - модель: {d['model']}")
        print(f"    ▸ Открытые порты: {d['ports'] or 'нет'}")

    try:
        choice = int(input("\nВыбери номер устройства для управления: ")) - 1
        dev = all_devices[choice]

        if dev["brand"] == "Yeelight":
            bulb = Bulb(dev["ip"])
            action = input("Введите 'on' для включения или 'off' для выключения: ").strip().lower()
            if action == "on":
                bulb.turn_on()
                print("✅ Включено.")
            elif action == "off":
                bulb.turn_off()
                print("✅ Выключено.")
            else:
                print("❗ Неизвестная команда.")
        elif dev["brand"].startswith("Tasmota") and 80 in dev["ports"]:
            control_tasmota(dev["ip"])
        else:
            print("⚠ Управление не поддерживается для этого устройства.")
    except Exception as e:
        print("⚠ Ошибка:", e)

if __name__ == "__main__":
    main()
