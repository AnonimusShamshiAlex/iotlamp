import socket
import concurrent.futures
import time
import requests
from yeelight import discover_bulbs, Bulb
import tinytuya
import broadlink

# Часто используемые порты для умных ламп
COMMON_PORTS = {
    "Yeelight": [55443, 1982],
    "Tuya": [6666, 6668],
    "Xiaomi": [54321, 5353],
    "Tapo": [80, 443],
    "Tasmota/ESPHome": [80, 8080, 8888],
    "Generic": [5353, 5683, 8888]
}

# Определяем порты по модели устройства
def get_possible_ports(model):
    model = model.lower()
    if "yeelight" in model:
        return COMMON_PORTS["Yeelight"]
    if "tuya" in model or "gauss" in model or "luazon" in model:
        return COMMON_PORTS["Tuya"]
    if "xiaomi" in model:
        return COMMON_PORTS["Xiaomi"]
    if "tapo" in model:
        return COMMON_PORTS["Tapo"]
    if "tasmota" in model or "esphome" in model:
        return COMMON_PORTS["Tasmota/ESPHome"]
    return COMMON_PORTS["Generic"]

# Быстрое сканирование нужных портов
def scan_ports(ip, ports):
    open_ports = []
    for port in ports:
        try:
            with socket.create_connection((ip, port), timeout=0.5):
                open_ports.append(port)
        except:
            continue
    return open_ports

# 🔵 Yeelight
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

# 🔶 Tuya, Gauss, Luazon
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

# 🌐 Ускоренное многопоточное сканирование остальных IP
def fast_scan_all_ips(prefix=None):
    print("⚡ Быстрое сканирование IP-адресов...")
    try:
        if prefix is None:
            prefix = ".".join(socket.gethostbyname(socket.gethostname()).split(".")[:3])
    except:
        prefix = "192.168.1"

    ips = [f"{prefix}.{i}" for i in range(1, 255)]

    found = []

    def scan_ip(ip):
        ports = scan_ports(ip, COMMON_PORTS["Generic"] + COMMON_PORTS["Xiaomi"] + COMMON_PORTS["Tapo"])
        if ports:
            brand = "Other"
            if 54321 in ports:
                brand = "Xiaomi"
            elif 443 in ports or 80 in ports:
                brand = "Tapo/Yandex"
            return {
                "brand": brand,
                "ip": ip,
                "model": "Unknown",
                "ports": ports
            }

    with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
        results = list(executor.map(scan_ip, ips))

    return [r for r in results if r]

# 🟡 Tasmota
def control_tasmota(ip):
    action = input("Включить или выключить лампу? [on/off]: ").strip().lower()
    try:
        if action == "on":
            r = requests.get(f"http://{ip}/cm?cmnd=Power%20On", timeout=2)
        elif action == "off":
            r = requests.get(f"http://{ip}/cm?cmnd=Power%20Off", timeout=2)
        else:
            print("❗ Неизвестная команда.")
            return
        if r.status_code == 200:
            print("✅ Команда отправлена успешно.")
        else:
            print("⚠ Ошибка:", r.status_code)
    except Exception as e:
        print("⚠ Ошибка управления:", e)

# 🔷 Tuya
def control_tuya(ip, device_id, local_key):
    d = tinytuya.OutletDevice(device_id, ip, local_key)
    d.set_version(3.3)
    action = input("Включить или выключить лампу? [on/off]: ").strip().lower()
    try:
        if action == "on":
            d.turn_on()
            print("✅ Лампа включена.")
        elif action == "off":
            d.turn_off()
            print("✅ Лампа выключена.")
        else:
            print("❗ Неизвестная команда.")
    except Exception as e:
        print("⚠ Ошибка управления Tuya:", e)

# 🔧 Yeelight
def control_yeelight(ip):
    try:
        bulb = Bulb(ip)
        action = input("Включить или выключить лампу? [on/off]: ").strip().lower()
        if action == "on":
            bulb.turn_on()
            print("✅ Лампа включена.")
        elif action == "off":
            bulb.turn_off()
            print("✅ Лампа выключена.")
        else:
            print("❗ Неизвестная команда.")
    except Exception as e:
        print("⚠ Ошибка управления Yeelight:", e)

# 🔹 Philips Hue
def control_philips_hue(bridge_ip, username):
    lights_url = f"http://{bridge_ip}/api/{username}/lights"
    try:
        r = requests.get(lights_url, timeout=3)
        lights = r.json()
        for lid, info in lights.items():
            print(f"{lid}. {info['name']} (вкл: {info['state']['on']})")
        light_id = input("Введите номер лампы: ").strip()
        action = input("Включить или выключить? [on/off]: ").strip().lower()
        state = {"on": action == "on"}
        r = requests.put(f"{lights_url}/{light_id}/state", json=state)
        if r.status_code == 200:
            print("✅ Команда отправлена.")
        else:
            print("⚠ Ошибка:", r.text)
    except Exception as e:
        print("❗ Ошибка Philips Hue:", e)

# 🔸 Broadlink
def control_broadlink():
    print("📡 Ищу устройства Broadlink...")
    devices = broadlink.discover(timeout=4)
    if not devices:
        print("❌ Устройства не найдены.")
        return

    for i, dev in enumerate(devices):
        print(f"{i + 1}. {dev.host}")

    choice = int(input("Выбери устройство: ")) - 1
    device = devices[choice]
    device.auth()
    action = input("Включить или выключить (через ИК-код)? [send]: ").strip().lower()
    if action == "send":
        hex_code = input("Введи ИК-код в hex (например, 2600...): ").strip()
        try:
            payload = bytes.fromhex(hex_code)
            device.send_data(payload)
            print("✅ Команда отправлена.")
        except Exception as e:
            print("⚠ Ошибка:", e)

# 🔁 Главная логика
def main():
    all_devices = []
    all_devices += scan_yeelight()
    all_devices += scan_tuya()
    all_devices += fast_scan_all_ips()

    print("\nДополнительно:")
    print("P. Philips Hue")
    print("B. Broadlink")

    choice_input = input("\nВыбери номер устройства или P/B: ").strip()
    if choice_input.lower() == "p":
        bridge_ip = input("Введи IP моста Philips Hue: ").strip()
        username = input("Введи Hue Username: ").strip()
        control_philips_hue(bridge_ip, username)
        return
    elif choice_input.lower() == "b":
        control_broadlink()
        return

    if not all_devices:
        print("❌ Устройства не найдены.")
        return

    print("\n🔍 Найденные устройства:")
    for i, d in enumerate(all_devices, 1):
        print(f"{i}. {d['brand']} ({d['ip']}) — {d['model']}")
        print(f"   ▸ Открытые порты: {d['ports'] or 'нет'}")

    try:
        choice = int(choice_input) - 1
        dev = all_devices[choice]

        if dev["brand"] == "Yeelight":
            control_yeelight(dev["ip"])
        elif dev["brand"] == "Tuya":
            device_id = input("Введи device_id: ").strip()
            local_key = input("Введи local_key: ").strip()
            control_tuya(dev["ip"], device_id, local_key)
        elif dev["brand"].startswith("Tasmota") or 80 in dev["ports"]:
            control_tasmota(dev["ip"])
        else:
            print("⚠ Управление этим устройством пока не поддерживается.")
    except Exception as e:
        print("⚠ Ошибка:", e)

if __name__ == "__main__":
    main()
