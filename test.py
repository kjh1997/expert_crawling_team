from selenium import webdriver # 1004 수정
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
import os
from bs4 import BeautifulSoup
import re
import time
import pprint
import math
from kafka import KafkaProducer
import json
from json import dumps
import sys

name = "유재수"
idAgency = "충북대학교"
host = '127.0.0.1'
kafka_port = '9092'
driver_path = "./chromedriver (2).exe"
#  C:/Users/kjh19/OneDrive/바탕 화면/test/chromedriver.exe // 노트북
# ./chromedriver (2).exe  // 연구실 컴
# /home/search/apps/dw/chromedriver 서버컴
chrome_options = Options()
# chrome_options.add_argument('--headless')
# chrome_options.add_argument('--no-sandbox')
# chrome_options.add_argument('--disable-dev-shm-usage') # 서버컴 전용 옵션
chrome_options.add_argument('window-size=1920,1080')
driver = webdriver.Chrome(driver_path, chrome_options=chrome_options)
author = {}
paper = []
def crawl_paper(refer):
    try:
        for num, ref in enumerate(refer[:10]):
            a= {}
            # # 자바스크립트 수집 코드
            # try:
            #     js_crawl = ref.select_one('p > a:nth-child(3)')['onclick']
            #     e  = js_crawl.find("('")
            #     f  = js_crawl.find("')")
                
            #     js_Data = js_crawl[e+2:f]
            #     print(js_Data)
            
            # except Exception as e:
            #     js_Data = ""
            # # 자바스크립트 수집 코드 종료
        
            # # 논문 제목 수집 시작
            # try:
            #     title = ref.select_one('p > a > span')
            #     title = title.text
                
            #     if title == "[ScienceON]":
            #         print(title,"수정 예정")
            #         title = ref.select_one('p')
            #         title = title.text
            #         title = re.sub('&nbsp; | &nbsp;| \n|\t|\r','',title).replace("\xa0","")
      
            #     print(title)    
            #     a["title"] = title
            # except Exception as e:
            #     title = ref.select_one('p')
            #     title = title.text
            #     title = re.sub('&nbsp; | &nbsp;| \n|\t|\r','',title).replace("\xa0","")
            #     print(title)    
            #     a["title"] = title
            # # 논문 제목 수집 종료


            # 공저자, 교신저자, 학회지 수집 시작

            ref.p.decompose()
            print(ref)
           


            
            
            # title = title.text
            # print(title)
            # title = re.sub('&nbsp; | &nbsp;| \n|\t|\r','',title).replace("\xa0","")
            # # a["title"] = title
            # # print(a)

            # ref.p.decompose()
            # refs = ref.get_text(separator='|br|', strip=True).split('|br|')
            # print(refs)
            # print(a)
            # paper.append(a)
    except Exception as e:
        print(e)
        print("논문 파트 오류")

start = time.time()
driver.get("https://www.ntis.go.kr/ThSearchHumanDetailView.do")
driver.find_element_by_xpath('/html/body/div[1]/div[2]/div[2]/button[1]').click()
driver.switch_to_window(driver.window_handles[1])  # 로그인창으로 전환 이거는 빼면 작동 x
driver.find_element_by_xpath('/html/body/div/form/label[2]/input').send_keys("normaljun95")
driver.find_element_by_xpath('/html/body/div/form/label[4]/input').send_keys("harrypotter95^") #아이디와 비밀번호
driver.find_element_by_xpath('/html/body/div/form/input').click()
time.sleep(2)

driver.switch_to_window(driver.window_handles[0]) #혹시 모를 화면 전환. 빼도 상관없음
time.sleep(1)
driver.find_element_by_xpath('/html/body/div[4]/div[1]/div[2]/div/input[2]').click()
time.sleep(1)
driver.find_element_by_xpath('/html/body/div[4]/div[4]/div/div[2]/fieldset/div/table/tbody/tr[1]/td[1]/input').send_keys(name)
driver.find_element_by_xpath('/html/body/div[4]/div[4]/div/div[2]/fieldset/div/table/tbody/tr[3]/td[1]/input').send_keys(idAgency)
driver.find_element_by_xpath('/html/body/div[4]/div[4]/div/div[3]/input[1]').click() # 상세 검색 클릭
time.sleep(1)

a = driver.find_element_by_xpath("/html/body/div[5]/div/div/div[3]/form/div[3]/div[2]/div[1]/div/a[1]/span")

driver.find_element_by_xpath('/html/body/div[5]/div/div/div[3]/form/div[3]/div[2]/div[1]/div/a[1]').click()
if a.text == name:
    driver.find_element_by_xpath('/html/body/div[5]/div/div/div[3]/form/div[3]/div[2]/div[1]/div/a[1]').click()     #여기까지 공통부분
else: 
    driver.find_element_by_xpath('/html/body/div[5]/div/div/div[3]/form/div[3]/div[2]/div[1]/div/a[2]').click()

driver.switch_to_window(driver.window_handles[1])
soup = BeautifulSoup(driver.page_source, 'html.parser')

driver.find_element_by_xpath("/html/body/form[1]/nav/div[2]/button[2]").click()
a = soup.find('button',id = 'paper')      #여기서부터는 논문파트 
text = a.get_text()
b = text.rfind('/')
c = text.rfind('건')
num = math.ceil(int(text[b+1:c])/10)
# print(num)
# pagenum = math.ceil(num/10)
print(num)
for i in range(1):      

    print("실행1")
    # print(a)
    time.sleep(0.5)
    pagesnum = i+1
    jsn = str(pagesnum)
    js = "fn_egov_link_page('" + "jsn" + "');"
    driver.execute_script("fn_egov_link_page('" + "28" + "');")
    print(js)
    time.sleep(0.5)
    html = driver.page_source
    soup = BeautifulSoup(html, 'html.parser')
    refer = soup.select('#paperInfo > li') 
    crawl_paper(refer)
    author["reference"] = paper

print(author)


