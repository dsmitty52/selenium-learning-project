import pytest
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import os

options = Options()

if os.environ.get("CI") == "true":
   options.add_argument("--headless=new")

@pytest.fixture
def driver():
   d= webdriver.Chrome(options=options)
   yield d
   d.quit()
