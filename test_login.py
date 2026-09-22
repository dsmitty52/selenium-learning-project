from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

import pytest

def attempt_login(driver, username,password):
 wait = WebDriverWait(driver,20)  # wait for up to 20 seconds for elements to be present
 driver.get("https://the-internet.herokuapp.com/login")
 driver.find_element(By.ID,"username").send_keys(username)
 driver.find_element(By.ID,"password").send_keys(password)   
 driver.find_element(By.CSS_SELECTOR,"button[type='submit']").click()

 message = wait.until(EC.visibility_of_element_located((By.ID, "flash")))
 return message.text

def attempt_logout(driver, username,password):
 wait = WebDriverWait(driver,20)  # wait for up to 20 seconds for elements to be present
 driver.get("https://the-internet.herokuapp.com/login")
 driver.find_element(By.ID,"username").send_keys(username)
 driver.find_element(By.ID,"password").send_keys(password)   
 driver.find_element(By.CSS_SELECTOR,"button[type='submit']").click()
 logout_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "a[href='/logout']")))
 logout_button.click()

 wait.until(EC.url_contains("/login"))   # confirm navigation actually happened first
 message = wait.until(EC.visibility_of_element_located((By.ID, "flash"))) 
 return message.text

def test_successful_login(driver):
    message = attempt_login(driver, "tomsmith", "SuperSecretPassword!")  # valid credentials
    assert "You logged into a secure area!" in message  # check for successful login message
    assert driver.current_url == "https://the-internet.herokuapp.com/secure" # check for correct URL after login
    flash = driver.find_element(By.ID, "flash")  
    assert "success" in flash.get_attribute("class")   # check for success class in flash message
    assert driver.title == "The Internet"

def test_wrong_password(driver):
    message = attempt_login(driver, "tomsmith", "WrongPassword!")  # invalid password
    assert "Your password is invalid!" in message  # check for invalid password message
    flash = driver.find_element(By.ID, "flash")  
    assert "error" in flash.get_attribute("class")   # check for error class in flash message

def test_wrong_username(driver):
    message = attempt_login(driver, "wronguser", "SuperSecretPassword!")  # invalid username
    assert "Your username is invalid!" in message  # check for invalid username message
    flash = driver.find_element(By.ID, "flash")  
    assert "error" in flash.get_attribute("class")   # check for error class in flash message

def test_empty_credentials(driver):
    message = attempt_login(driver, "", "")  # empty credentials
    assert "Your username is invalid!" in message  # check for invalid username message
    flash = driver.find_element(By.ID, "flash")  
    assert "error" in flash.get_attribute("class")   # check for error class in flash message

def test_successful_logout(driver):
    message = attempt_logout(driver, "tomsmith", "SuperSecretPassword!")  # valid credentials
    assert "You logged out of the secure area!" in message  # check for successful logout message
    flash = driver.find_element(By.ID, "flash")  
    assert "success" in flash.get_attribute("class")   # check for success class in flash message

def test_password_masking(driver):
   driver.get("https://the-internet.herokuapp.com/login")
   password_field=driver.find_element(By.ID,"password")
   assert password_field.get_attribute("type")=="password"  # check that the password field is of type 'password' (masked)