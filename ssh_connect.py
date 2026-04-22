#!/usr/bin/env python3
"""
SSH подключение к Termux на Android телефоне
Запускать на своём компьютере: python ssh_connect.py
"""

import paramiko
import os
import sys
import socket

# Настройки подключения
PHONE_IP = input("IP адрес телефона (например 192.168.1.100): ").strip()
PHONE_PORT = 8022  # Termux SSH порт
USERNAME = "root"  # или用户名
PASSWORD = input("Пароль Termux: ")

# Что делать после подключения
COMMAND = "cd ~/bot4tiktok && python full_auto_bot.py"

def connect():
    try:
        print(f"Подключаюсь к {PHONE_IP}:{PHONE_PORT}...")
        
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        client.connect(
            PHONE_IP, 
            port=PHONE_PORT,
            username=USERNAME,
            password=PASSWORD,
            timeout=10
        )
        
        print("✓ Подключено! Запускаю бота...")
        
        # Выполнить команду
        stdin, stdout, stderr = client.exec_command(COMMAND)
        
        # Вывести результат
        for line in stdout:
            print(line, end="")
            
        for line in stderr:
            print(f"[ОШИБКА] {line}", end="")
        
        client.close()
        print("\n✓ Готово!")
        
    except socket.timeout:
        print("✗ Не подключается - проверь IP и что SSH включен в Termux")
    except paramiko.AuthenticationException:
        print("✗ Неверный пароль")
    except Exception as e:
        print(f"✗ Ошибка: {e}")

if __name__ == "__main__":
    # Установить paramiko если нет
    try:
        import paramiko
    except ImportError:
        print("Устанавливаю paramiko...")
        os.system("pip install paramiko")
        import paramiko
    
    connect()