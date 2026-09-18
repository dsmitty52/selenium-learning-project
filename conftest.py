import pytest
from selenium import webdriver

@pytest.fixture
def driver():
   d= webdriver.Chrome()
   yield d
   d.quit()
