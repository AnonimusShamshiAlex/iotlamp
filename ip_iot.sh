#!/bin/bash

# Получаем локальный IP и определяем подсеть
LOCAL_IP=$(hostname -I | awk '{print $1}')
SUBNET=$(echo $LOCAL_IP | cut -d"." -f1-3).0/24

echo "[+] Сканирую локальную сеть: $SUBNET"
echo

# Получаем список активных устройств
nmap -sn $SUBNET -oG - | awk '/Up$/{print $2}' | while read ip
do
    echo "[*] Устройство найдено: $ip"

    # Получаем MAC и производителя
    MAC_INFO=$(nmap -sP $ip | grep "MAC Address")
    if [ -n "$MAC_INFO" ]; then
        echo "    $MAC_INFO"
    else
        echo "    MAC: Не найден"
    fi

    # Показываем открытые порты
    echo "    Открытые порты:"
    nmap -sS -Pn -T4 --min-rate 1000 $ip | awk '/^PORT/{f=1; next} f && NF'

    echo
done

echo "[+] Сканирование завершено."
