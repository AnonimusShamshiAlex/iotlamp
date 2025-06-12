import socket
import requests
from yeelight import Bulb
import tinytuya

# 🟡 Порты по умолчанию
DEFAULT_PORTS = {
    "Yeelight": 55443,
    "Tuya": 6668,
    "Tasmota": 80,
    "Tapo": 8080,
    "Generic": 80
}

def control_yeelight(ip):
    try:
        bulb = Bulb(ip)
        cmd = input("Yeelight: 'on' или 'off': ").strip().lower()
        if cmd == "on":
            bulb.turn_on()
            print("✅ Включено.")
        elif cmd == "off":
            bulb.turn_off()
            print("✅ Выключено.")
        else:
            print("❗ Неизвестная команда.")
    except Exception as e:
        print("⚠ Ошибка управления Yeelight:", e)

def control_tuya(ip):
    try:
        dev = tinytuya.OutletDevice("dummyid", ip, "dummykey")
        dev.set_version(3.3)
        cmd = input("Tuya: 'on' или 'off': ").strip().lower()
        state = True if cmd == "on" else False
        result = dev.set_status(state, 1)
        print("✅ Ответ от устройства:", result)
    except Exception as e:
        print("⚠ Ошибка Tuya:", e)

def control_tasmota(ip):
    try:
        cmd = input("Tasmota: 'on' или 'off': ").strip().lower()
        if cmd == "on":
            r = requests.get(f"http://{ip}/cm?cmnd=Power%20On", timeout=2)
        elif cmd == "off":
            r = requests.get(f"http://{ip}/cm?cmnd=Power%20Off", timeout=2)
        else:
            print("❗ Неизвестная команда.")
            return
        if r.status_code == 200:
            print("✅ Команда отправлена.")
        else:
            print("⚠ Ошибка:", r.status_code)
    except Exception as e:
        print("⚠ Ошибка Tasmota:", e)

def control_generic(ip):
    try:
        cmd = input("Generic HTTP: 'on' или 'off': ").strip().lower()
        if cmd == "on":
            requests.get(f"http://{ip}/on", timeout=2)
        elif cmd == "off":
            requests.get(f"http://{ip}/off", timeout=2)
        else:
            print("❗ Неизвестная команда.")
            return
        print("✅ Команда отправлена.")
    except Exception as e:
        print("⚠ Ошибка Generic:", e)

def main():
    print("🌐 Введи IP устройства:")
    ip = input("> ").strip()

    print("Выбери тип устройства:")
    print("1. Yeelight")
    print("2. Tuya")
    print("3. Tasmota / ESPHome")
    print("4. Tapo / Generic")

    choice = input("> ").strip()

    if choice == "1":
        control_yeelight(ip)
    elif choice == "2":
        control_tuya(ip)
    elif choice == "3":
        control_tasmota(ip)
    elif choice == "4":
        control_generic(ip)
    else:
        print("❗ Неизвестный выбор.")

if __name__ == "__main__":
    main()
