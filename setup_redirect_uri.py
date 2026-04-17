#!/usr/bin/env python3
"""Добавление redirect URI в TikTok Developer Portal"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import time

def main():
    print("Starting browser...")
    
    options = Options()
    options.add_argument("--start-maximized")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    
    wait = WebDriverWait(driver, 15)
    
    try:
        # Открываем страницу приложений
        driver.get("https://developers.tiktok.com/app/")
        
        print("\n" + "=" * 50)
        print("LOGIN first if needed, then press ENTER here")
        print("=" * 50)
        input("\nPress ENTER after you see your apps > ")
        
        # Ищем и кликаем на первое приложение
        print("\nClicking on app...")
        try:
            app_links = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "a[href*='/app/']")))
            if app_links:
                app_links[0].click()
                print("   App clicked")
                time.sleep(3)
        except:
            print("   Already on app page or no apps")
        
        # Скриншот для отладки
        driver.save_screenshot(r"C:\Users\pav\bot4tiktok\screenshot1.png")
        print("   Screenshot saved: screenshot1.png")
        
        # Ищем Login Kit
        print("\nLooking for Login Kit...")
        time.sleep(2)
        
        # Получаем все ссылки и кнопки
        all_links = driver.find_elements(By.TAG_NAME, "a")
        all_btns = driver.find_elements(By.TAG_NAME, "button")
        
        for el in all_links + all_btns:
            try:
                text = el.text.lower()
                if 'login kit' in text:
                    print(f"   Found: {el.text}")
                    el.click()
                    time.sleep(3)
                    driver.save_screenshot(r"C:\Users\pav\bot4tiktok\screenshot2.png")
                    print("   Screenshot saved: screenshot2.png")
                    break
            except:
                pass
        
        print("\nLooking for redirect URI input...")
        time.sleep(2)
        
        # Ищем все input поля
        inputs = driver.find_elements(By.TAG_NAME, "input")
        print(f"   Found {len(inputs)} input fields")
        
        for inp in inputs:
            try:
                placeholder = inp.get_attribute('placeholder') or ''
                name = inp.get_attribute('name') or ''
                inp_type = inp.get_attribute('type') or ''
                
                if inp_type == 'text' or inp_type == 'url':
                    print(f"   - type={inp_type}, placeholder={placeholder}, name={name}")
                    
                    if 'redirect' in placeholder.lower() or 'redirect' in name.lower() or 'uri' in name.lower():
                        inp.clear()
                        inp.send_keys("http://localhost:8080/callback")
                        print(f"   >>> Entered URI!")
                        time.sleep(1)
                        
                        # Ищем Add кнопку
                        for btn in driver.find_elements(By.TAG_NAME, "button"):
                            if 'add' in btn.text.lower():
                                btn.click()
                                print("   >>> Clicked Add")
                                break
                        
                        time.sleep(2)
                        
                        # Save
                        for btn in driver.find_elements(By.TAG_NAME, "button"):
                            if 'save' in btn.text.lower():
                                btn.click()
                                print("   >>> Clicked Save")
                                break
                        
                        print("\nSUCCESS!")
                        input("Press ENTER to close...")
                        driver.quit()
                        return
            except:
                pass
        
        driver.save_screenshot(r"C:\Users\pav\bot4tiktok\screenshot3.png")
        print("\nScreenshot saved: screenshot3.png")
        print("\nCould not auto-add URI. Please do it manually:")
        print("   1. Find Login Kit section")
        print("   2. Add redirect URI: http://localhost:8080/callback")
        print("   3. Click Save")
        input("\nPress ENTER when done to close browser...")
        
    except Exception as e:
        print(f"Error: {e}")
        driver.save_screenshot(r"C:\Users\pav\bot4tiktok\screenshot_error.png")
        input("Press ENTER to close...")
    finally:
        try:
            driver.quit()
        except:
            pass

if __name__ == "__main__":
    main()