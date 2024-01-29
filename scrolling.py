from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from dotenv import load_dotenv
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import os
import time

driver = webdriver.Chrome()
load_dotenv()
twitter_username=os.getenv("TUSERNAME")
twitter_password=os.getenv("PASSWORD")
def wait_for_element(driver, by, selector):
    return WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((by, selector))
    )
def login(driver, username, password):
    driver.get("https://twitter.com/i/flow/login")
    username_input = wait_for_element(driver, By.CSS_SELECTOR, 'input[autocomplete*="user"]')
    username_input.clear()
    username_input.send_keys(username)
    username_input.send_keys(Keys.RETURN)
    password_input = wait_for_element(driver, By.CSS_SELECTOR, 'input[autocomplete*="password"]')
    password_input.clear()
    password_input.send_keys(password)
    password_input.send_keys(Keys.RETURN)
    time.sleep(5) 

login(driver, twitter_username, twitter_password)
driver.get("http://www.twitter.com/pdo_om")
while True:
    driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.END)
    scroll_height = driver.execute_script("return document.body.scrollHeight")
    scroll_position = driver.execute_script("return window.pageYOffset || document.documentElement.scrollTop || document.body.scrollTop || 0")
    if scroll_position >= scroll_height:
        break
