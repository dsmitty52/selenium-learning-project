from selenium import webdriver

driver = webdriver.Chrome()  # or use any other browser driver
driver.get("https://www.example.com")  # replace with the URL you want to scrape
print(driver.title)  # prints the title of the page
driver.quit()  # close the browser