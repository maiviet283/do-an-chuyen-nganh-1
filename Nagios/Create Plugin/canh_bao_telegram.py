#!/usr/bin/env python3

import subprocess
import sys
import requests  # Thêm thư viện requests để gửi yêu cầu HTTP

# Định nghĩa danh sách IP và tên của chúng
ip_names = {
    "127.0.0.1": "Nagios Server",
    "192.168.233.128": "Ubuntu Nagios",
    "192.168.233.129": "Router OS",
    "192.168.233.130": "Windows Server",
    "192.168.74.131": "Pfsense"
}

# Hàm kiểm tra ping đến một host
def check_ping(host):
    try:
        result = subprocess.run(['ping', '-c', '1', host], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

        if result.returncode == 0:
            return f"{ip_names[host]} - {host} - PING OK - Đang Hoạt Động"
        else:
            send_telegram_alert(host)  # Gửi cảnh báo qua Telegram khi ping không thành công
            return f"{ip_names[host]} - {host} - PING CRITICAL - Không Hoạt Động"
    except Exception as e:
        return f"Error: {e}"

# Hàm gửi cảnh báo qua Telegram
def send_telegram_alert(host):
    TOKEN = "7428805958:AAEBdwXMnhAgflnCfzN9Btqs_YQFRtzALhc"  # Thay YOUR_TELEGRAM_BOT_TOKEN bằng token của bot Telegram của bạn
    CHAT_ID = "1460245017"  # Thay YOUR_CHAT_ID bằng ID cuộc trò chuyện Telegram của bạn

    message = f"{ip_names[host]} Hiện Không Hoạt Động ({host})!"  # Nội dung cảnh báo

    # Gửi tin nhắn đến Telegram qua API
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    data = {"chat_id": CHAT_ID, "text": message}
    response = requests.post(url, data=data)

    if response.status_code == 200:
        print("Đã gửi cảnh báo qua Telegram thành công!")
    else:
        print("Lỗi: Không thể gửi cảnh báo qua Telegram.")

# Hàm chính
def main(ip):
    ip_list = list(ip_names.keys())
    
    if ip == "tatca":
        for host in ip_list:
            result = check_ping(host)
            print(result)
    elif ip in ip_list:
        result = check_ping(ip)
        print(result)
    else:
        print(f"{ip} - IP không được quản lý")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: ./check_kiemtra_ping_host.py <host | tatca>")
        sys.exit(2)
    
    ip = sys.argv[1]
    main(ip)

