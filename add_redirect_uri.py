#!/usr/bin/env python3
"""Добавление redirect URI в TikTok Developer Portal"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

REDIRECT_URI = "https://endangered-departments-converter-two.trycloudflare.com/callback"

def main():
    print("Starting browser...")
    
    driver = webdriver.Chrome()
    wait = WebDriverWait(driver, 20)
    
    try:
        # Открываем приложение
        driver.get("https://developers.tiktok.com/app/7605488716874680332")
        driver.maximize_window()
        
        print("\n1. Браузер открыт. Залогинься в TikTok, если нужно.")
        print("2. Перейди в раздел Login Kit -> Redirect URIs")
        print("3. Добавь этот URL:")
        print(f"\n   {REDIRECT_URI}\n")
        
        input("4. Нажми ENTER после сохранения...")
        
        print("\nГотово! Можешь запускать авторизацию.")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    main()