from selenium import webdriver
from bs4 import BeautifulSoup
# from pymongo import MongoClient, mongo_client
import json
from json import loads, dumps
import time
import re
import math


# mongoDB
# pyclient = MongoClient('localhost', 27017)
# mydb = pyclient["testDB"]
# mycol = mydb["test"]

name = "유재수"

options = webdriver.ChromeOptions()
options.add_experimental_option("excludeSwitches", ["enable-logging"])
driver = webdriver.Chrome("./chromedriver.exe", options=options)

# NTIS 이동
driver.get("https://www.ntis.go.kr/ThSearchHumanDetailView.do")

# 로그인 버튼 클릭
driver.find_element_by_xpath('/html/body/div[1]/div[2]/div[2]/button[1]').click()

# 로그인 화면 지정
driver.switch_to_window(driver.window_handles[1])

# id, pw 입력
driver.find_element_by_xpath('/html/body/div/form/label[2]/input').send_keys("normaljun95")
driver.find_element_by_xpath('/html/body/div/form/label[4]/input').send_keys("harrypotter95^")

# 로그인 버튼 클릭
driver.find_element_by_xpath('/html/body/div/form/input').click()
time.sleep(3)

# 검색창 main 화면 지정
driver.switch_to_window(driver.window_handles[0])

# 검색창 입력 및 클릭
driver.find_element_by_xpath('/html/body/div[4]/div[1]/div[1]/input').send_keys(name)
driver.find_element_by_xpath('/html/body/div[4]/div[1]/div[1]/button').click()

# 검색 후 첫 번째 저자 클릭
driver.find_element_by_xpath('/html/body/div[5]/div/div/div[3]/form/div[3]/div[2]/div[1]/div/a[1]/span').click()

# 저자 화면 지정
driver.switch_to_window(driver.window_handles[1])

# SCIENCON 접속 (여기서부터 SCIENCEON)
driver.find_element_by_xpath('/html/body/form[1]/div/div/div[1]/div[2]/div[2]/a[1]').click()
time.sleep(3)

# SCIENCEON 화면 지정
driver.switch_to_window(driver.window_handles[2])

# 저자 고유 ID 크롤링 (SCIENCEON)
url = driver.current_url
cn1 = url.find('cn=')
cn2 = url.find('&')
author_id = f'{url[cn1+3:cn2]}' # 저자 고유ID
print(author_id)

# 크롤링
soup = BeautifulSoup(driver.page_source, 'html.parser')

time.sleep(1)

# info_ScienceOn -> SCIENCEON 저자 전문분야
info_ScienceOn = driver.find_element_by_xpath('/html/body/div[3]/div/div/div[6]/div[2]').text
print(info_ScienceOn)


# 크롤링 종료



driver.close()
driver.switch_to_window(driver.window_handles[1])
print(driver.current_url)