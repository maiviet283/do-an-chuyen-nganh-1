#!/usr/bin/env python3

import subprocess
import sys

ip_names = {
    "127.0.0.1":"Nagios Server",
    "192.168.233.128": "Ubuntu Nagios",
    "192.168.233.129": "Router OS",
    "192.168.233.130": "Windows Server",
    "192.168.74.131": "Pfsense"
}

def check_ping(host):
    try:
        result = subprocess.run(['ping', '-c', '1', host], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        
        if result.returncode == 0:
            return f"{ip_names[host]} - {host} - PING OK - Đang Hoạt Động"
        else:
            return f"{ip_names[host]} - {host} - PING CRITICAL - Không Hoạt Động"
    except Exception as e:
        return f"Error: {e}"

def main(ip):
    
    ip_list = list(ip_names.keys())
    
    if ip == "tatca":
        for host in ip_list:
            result = check_ping(host)
            print(result)
    else:
        if ip in ip_list:
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

