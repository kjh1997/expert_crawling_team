from pymongo import MongoClient
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
client       =  MongoClient('203.255.92.141:27017', connect=False)
QueryKeyword = "QueryKeyword"
NTIS         = client['NTIS']
expertFactor = NTIS['ExpertFactor']
author       = NTIS['Author']
rawData      = NTIS['Rawdata']
isCollect    = False

def __main__():
    num_experts = 0 # 저자 정보 수집 대상
    com_key     = [517]
    for key in com_key:
        # print(NTIS[QueryKeyword].find_one({"_id":key}))
        if 'isCollect' not in NTIS[QueryKeyword].find_one({"_id":key}):
            x = NTIS[QueryKeyword].find_one({"_id":key}, {"experts":1})
            num_experts += x['experts']

    for key in com_key:
        print("key : ", key)
        ls = list(expertFactor.find(
            {
                'keyId':key,
                "Productivity":{"$gt":0}, 
            },
            {
                "_id" : 0, 
                "keyId" : 1, 
                "A_ID" : 1, 
                "Productivity": 1, 
                "contirb" : 1, 
                "Durability" : 1, 
                "Recentness" : 1, 
                "Quality" : 1, 
                "Acc" : 1 
            }))

        for _id in ls:
            __id = author.find_one({'_id':_id['A_ID']})
            if __id is not None and 'isCollect' not in __id:
                result = rawData.find_one({'keyId':key,'mngId':_id['A_ID']},{'keyId':1,'mng':1,'ldAgency':1,'koTitle':1,'enTitle':1, '_id':0})
                mng = result['mng'] 
                input_name = result['mng']
                input_idAgency = result['ldAgency']
                kotitle = result['koTitle']
                print(mng, input_idAgency, kotitle, "crawl")
                nits_crawling(input_name,input_idAgency,kotitle).start_crwal() # 트리거
                # time.sleep(10)

def get_common_keyid(domestic_option = 1):
    """mongoDB에서 공통keyid를 추출 하는 함수
    
    :para domestic_option = 1 국내
    :para domestic_option = 2 국외
    :para domestic_option = 3 ALL
    """
    domestics = ['NTIS', 'SCIENCEON', 'KCI', 'DBPIA']
    overseas = ['SCOPUS', 'WOS']
    ALL = domestics + overseas
    siteDict = {i : []  for i in ALL} 
    if domestic_option == 1:
        for site in domestics:
            db = client[site] #print(client[site])
            for _ in list(db[QueryKeyword].find({},{'_id':1})):
                siteDict[site].append(_['_id'])
    
        vs1 = set(siteDict['NTIS']) & set(siteDict['SCIENCEON'])
        vs2 = set(siteDict['DBPIA']) & set(siteDict['KCI'])
        vsResult = list(vs1 & vs2)
        vsResult.sort(reverse=True)

        return vsResult

    elif domestic_option == 2:
        for site in overseas:
            db = client[site] #print(client[site])
            for _ in list(db[QueryKeyword].find({},{'_id':1})):
                siteDict[site].append(_['_id'])

        vs = set(siteDict['SCOPUS']) & set(siteDict['WOS'])
        vsResult = list(vs)
        vsResult.sort(reverse=True)

        return vsResult

    else:
        for site in ALL:
            db = client[site] #print(client[site])
            for _ in list(db[QueryKeyword].find({},{'_id':1})):
                siteDict[site].append(_['_id'])

        vs1 = set(siteDict['NTIS']) & set(siteDict['SCIENCEON'])
        vs2 = set(siteDict['DBPIA']) & set(siteDict['KCI'])
        vs3 = set(siteDict['SCOPUS']) & set(siteDict['WOS'])

        vsResult = list(vs1 & vs2 & vs3)
        vsResult.sort(reverse=True)

        return vsResult

class nits_crawling:
    def __init__(self, input_name,input_idAgency,kotitle):
         
        self.name = input_name
        self.idAgency = input_idAgency
        self.kotitle = kotitle
        self.host = '127.0.0.1'
        self.kafka_port = '9092'
        self.driver_path = "./chromedriver.exe"
        #  C:/Users/kjh19/OneDrive/바탕 화면/test/chromedriver.exe // 노트북
        # ./chromedriver (2).exe  // 연구실 컴
        # /home/search/apps/dw/chromedriver 서버컴
        self.chrome_options = Options()
        # self.chrome_options.add_argument('--headless')
        # self.chrome_options.add_argument('--no-sandbox')
        # self.chrome_options.add_argument('--disable-dev-shm-usage') # 서버컴 전용 옵션
        self.chrome_options.add_argument('window-size=1920,1080')
        self.driver = webdriver.Chrome(self.driver_path, chrome_options=self.chrome_options)
        self.author = {}
        self.paper = []
        self.papers = []
        self.info = {}
        self.test = []
        self.infolist = []
        self.cnt = 0
        try:
            self.producer = KafkaProducer(bootstrap_servers= "localhost:9092", value_serializer=lambda x: json.dumps(x).encode('utf-8'))
        except Exception as e:
            print(e)
            print("kafka 생성 오류")

#--------------------저자정보 ------------------------------------

    def main_title(self, soup):
        try:
            authorInfo = {}
            infolist = []
            thumnails  = []
            try:
                thumnail   = soup.select_one('#viewForm > div > div > div.article.bdr3.p20 > div.userphoto.po_rel > img')
                thumnails.append(thumnail['src'])
            except Exception as e:
                print("이미지 소스 없습니다.")
            self.info["thumnails"] = thumnails
            try:
                name = soup.select_one('.mb5').text
                name = name.lstrip()
                name = ' '.join(name.split())
                self.info["name"] = name.replace("\n","").replace("\t","")
            except Exception as e:
                print("이름역영이 잘못됐습니다.")

            try:    
                details = soup.find("div", attrs={"class":"m0 lh15 f13"}).get_text()
                details = ' '.join(details.split())
                details = details.lstrip()
                self.info["details"] = details.replace("\n","").replace("\t","")
            except:
                print("상세정보가 없습니다.")
            edu = []
            try:
                for tag in soup.select('dd.bd0'):
                    ed = tag.get_text(separator='|br|', strip=True).split('|br|')
                    # ed = tag.get_text(strip=True, separator=" ")
                    edu.append(ed)
                self.info["Education"] = ed.replace("\n","").replace("\t","")
            except Exception as e:
                print("학력 없습니다.")
            carear = []
            try:
                for tag in soup.select('ul.mt20'):
                    ca = tag.get_text(separator='|li|', strip=True).split('|li|')
                    carear.append(ca)
                self.info["carear"] = ca.replace("\n","").replace("\t","")
            except Exception as e:
                print("커리어 없습니다.")
            print("main title 크롤 종료")

           
        except Exception as e:
            print(e)
            

#----------------------논문 크롤---------------------------------

    def crawl_paper(self, refer):
        try:
            for num, ref in enumerate(refer[:-1]):
                a= {}
                ############### 자바스크립트 수집 코드 ##############
                try:
                    js_crawl = ref.select('p > a')
                    print(type(js_crawl))

                    for i in js_crawl:
                        print(i["title"])
                        print(i)
                        if "NDSL 상세보기" == i["title"]:
                            e  = i["onclick"].find("('")
                            f  = i["onclick"].find("')")
                            js_Data = i["onclick"][e+2:f]
                    print("자바스크립트",js_Data)
                
                except Exception as e:
                    print(e)
                    js_Data = ""
                    print("자바스크립트",js_Data)
                
                a["js_scienceon"] = js_Data
                js_Data = ""

                ############ 자바스크립트 수집 코드 종료 ##############

                ############### 논문 제목 수집 시작  ##############
                try:
                    title = ref.select_one('p > a > span')
                    title = title.text
                    
                    if title == "[ScienceON]":
                        
                        title = ref.select_one('p')
                        title = title.text
                        title = re.sub('&nbsp; | &nbsp;| \n|\t|\r','',title).replace("\xa0","")
                        title = title.replace("[ScienceON]","")
                    
                    print(title) 
                    print("1")
                except Exception as e:
                    title = ref.select_one('p')
                    title = title.text
                    title = re.sub('&nbsp; | &nbsp;| \n|\t|\r','',title).replace("\xa0","")
                    print(title)    
                    
                    print("2")
                a["title"] = title
                ############## #논문 제목 수집 종료 ############## 
                
                


                ############### 공저자, 교신저자, 학회지 수집 시작 ##############
                try:
                    ref.p.decompose()
                except Exception as e:
                    print("p태그가 없습니다.")   
                try:     
                    ref.span.decompose()
                except Exception as e:
                    print("span태그가 없습니다.")   
                
                refs = ref.get_text(separator='|br|', strip=True).split('|br|') 
                

                if len(refs) == 1:
                    a["coau"] = ""
                    partition = refs[0]
                    num1 = partition.rfind("[")
                    num2 = partition.rfind("]")+1
                    num3 = partition.rfind("(")
                    num4 = partition.rfind(")")+1  
                    
                    if num1 != -1:
                        ref2 = partition[num1:num2]
                    else:
                        ref2 = ""
                    if num3 != -1:    
                        year = partition[num3:num4] 
                    else:
                        year = ""
                    
                    if num1 == -1 and num3 == -1:
                        ref1 = partition
                    elif num3 ==-1:
                        ref1 = partition[:num1]
                    elif num1 == -1:
                        ref1 = partition[:num3]
                    else:
                        ref1 = partition[:num1]


                elif len(refs) == 2:
                    a["coau"] = refs[0]
                    partition = refs[1]
                    num1 = partition.rfind("[")
                    num2 = partition.rfind("]")+1
                    num3 = partition.rfind("(")
                    num4 = partition.rfind(")")+1  
                    if num1 != -1:
                        ref2 = partition[num1:num2]
                    else:
                        ref2 = ""
                    if num3 != -1:    
                        year = partition[num3:num4] 
                    else:
                        year = ""
                    
                    if num1 == -1 and num3 == -1:
                        ref1 = partition
                    elif num3 ==-1:
                        ref1 = partition[:num1]
                    elif num1 == -1:
                        ref1 = partition[:num3]
                    else:
                        ref1 = partition[:num1]
                
                a["year"] = year.replace("(","").replace(")","")
                a["ref1"] = ref1.replace("\t","")
                a["ref2"] = ref2.replace("\t","")

                ############### 공저자, 교신저자, 학회지 수집 종료 ##############
                pprint.pprint(a)
                self.paper.append(a)
                
        except Exception as e:
            print(e)
            print("논문 파트 오류")


#------------------과제 크롤-------------------------------

    def rnd_crawl(self, soup):
        
        try:    
            brs  = soup.select('#rndInfo > li')
            
            for num, br in enumerate(brs[:-1]):
                a  = {}
                br.select_one('p')
                try:
                    print("num : ", num)
                    
                    title = br.select_one('a')
                    title = title.text
                    print(num,"번째 title",title)
                    br_list = str(br).split('<br/>')
                    #print(br_list)
                    print(num,"번째 origin_num",br_list[1])
                    RND_num, RND_year, RND_period, RND_bz_name = br_list[1].split(' / ',3)
                    print(num,"번째 RND_num",RND_num)
                    print(num,"번째 RND_year",RND_year)
                    print(num,"번째 RND_period",RND_period)
                    print(num,"번째 RND_bz_name",RND_bz_name)


                    #print(num,"번째 RND_ins",br_list[2].replace("<p>","").replace("</p>",""))
                    num1 = br_list[2].find("<")
                    brlist2 = br_list[2][:num1]
                    a['RND_title'] = title.replace("\t","")
                    self.test.append(title.replace("\t",""))
                    a['RND_num'] = RND_num.replace("\t","")
                    a['RND_year'] = RND_year.replace("\t","")
                    a['RND_period'] = RND_period.replace("\t","")
                    a['RND_bz_name'] = RND_bz_name.replace("\t","")

                    a['RND_ins'] = brlist2.replace("\t","")

                    self.papers.append(a)
                except Exception as e:
                    print(e)
                    print("과제 크롤러 문제")
        except Exception as e:
            print(e)
            print("rnd 파트 오류")
            

    def start_crwal(self):
        try:
            rnd_error_cnt =0
            start = time.time()
            self.driver.get("https://www.ntis.go.kr/ThSearchHumanDetailView.do")

            self.driver.find_element_by_xpath('/html/body/div[1]/div[2]/div[2]/button[1]').click()

            self.driver.switch_to_window(self.driver.window_handles[1])  # 로그인창으로 전환 이거는 빼면 작동 x
            self.driver.find_element_by_xpath('/html/body/div/form/label[2]/input').send_keys("normaljun95")
            self.driver.find_element_by_xpath('/html/body/div/form/label[4]/input').send_keys("harrypotter95^") #아이디와 비밀번호
            self.driver.find_element_by_xpath('/html/body/div/form/input').click()
            time.sleep(2)

            self.driver.switch_to_window(self.driver.window_handles[0]) #혹시 모를 화면 전환. 빼도 상관없음
            time.sleep(1)
            self.driver.find_element_by_xpath('/html/body/div[4]/div[1]/div[2]/div/input[2]').click()
            time.sleep(1)
            self.driver.find_element_by_xpath('/html/body/div[4]/div[4]/div/div[2]/fieldset/div/table/tbody/tr[1]/td[1]/input').send_keys(self.name)
            self.driver.find_element_by_xpath('/html/body/div[4]/div[4]/div/div[2]/fieldset/div/table/tbody/tr[3]/td[1]/input').send_keys(self.idAgency)
            self.driver.find_element_by_xpath('/html/body/div[4]/div[4]/div/div[3]/input[1]').click() # 상세 검색 클릭
            time.sleep(1)
            try:
                a = self.driver.find_element_by_xpath("/html/body/div[5]/div/div/div[3]/form/div[3]/div[2]/div[1]/div/a[1]/span")
            except Exception as e:
                print("검색한 사람이 없습니다.")
                self.driver.close
            self.driver.find_element_by_xpath('/html/body/div[5]/div/div/div[3]/form/div[3]/div[2]/div[1]/div/a[1]').click()
            
            if a.text == self.name:
                self.driver.find_element_by_xpath('/html/body/div[5]/div/div/div[3]/form/div[3]/div[2]/div[1]/div/a[1]').click()     #여기까지 공통부분
            else: 
                self.driver.find_element_by_xpath('/html/body/div[5]/div/div/div[3]/form/div[3]/div[2]/div[1]/div/a[2]').click()
            
            
            self.driver.switch_to_window(self.driver.window_handles[1])
            # print("여기인가?")
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            try:
                self.driver.find_element_by_id('rnd').click()
            except Exception as e:
                rnd_error_cnt = 1
                print("R&D참여과제 버튼이 없습니다.")
            if rnd_error_cnt != 1:
                a = soup.find('button',id = 'rnd')      #여기서부터는 rnd파트
                text = a.get_text()
                b = text.rfind('(')
                c= text.rfind('건')
                num = math.ceil(int(text[b+1:c])/10)+1
                print(num)
                time.sleep(2)
                for i in range(num):
                    time.sleep(0.5)
                    i+=1
                    i = str(i)
                    js = "fn_egov_link_page('" + i + "');"
                    self.driver.execute_script(js)
                    time.sleep(1)
                    html = self.driver.page_source
                    soup = BeautifulSoup(html, 'html.parser')
                    self.rnd_crawl(soup)
            self.author["rnd"] = self.papers
            print(self.test)
            ### 파라미터 값이 존재하는지 검사
            if self.kotitle in self.test:
                self.author["rnd"] = self.papers
            else:
                print("없으니까 다음으로 넘어갑니다.")  
                self.cnt = 1
                time.sleep(3)  

              #---------------------처음에 들어간 저자가 다른 사람일 경우------------------        
            if self.cnt == 1:
                retry_paper_error_cnt = 0
                print("다시 시작")
                self.driver.switch_to_window(self.driver.window_handles[0]) #혹시 모를 화면 전환. 빼도 상관없음
                self.driver.find_element_by_xpath('/html/body/div[4]/div[1]/div[2]/div/input[2]').click()
                time.sleep(1)
                self.driver.find_element_by_xpath('/html/body/div[4]/div[4]/div/div[2]/fieldset/div/table/tbody/tr[1]/td[1]/input').send_keys(self.name)
                self.driver.find_element_by_xpath('/html/body/div[4]/div[4]/div/div[2]/fieldset/div/table/tbody/tr[3]/td[1]/input').send_keys(self.idAgency)
                self.driver.find_element_by_xpath('/html/body/div[4]/div[4]/div/div[3]/input[1]').click()
                    
                self.driver.find_element_by_xpath('/html/body/div[5]/div/div/div[3]/form/div[3]/div[2]/div[1]/div/a[1]').click()
                self.driver.switch_to_window(self.driver.window_handles[1])
                soup = BeautifulSoup(self.driver.page_source, 'html.parser')
                
                self.driver.find_element_by_id('rnd').click()
                a = soup.find('button',id = 'rnd')      #여기서부터는 rnd파트
                text = a.get_text()
                b = text.rfind('(')
                c= text.rfind('건')
                num = math.ceil(int(text[b+1:c])/10)-1
                print(num)
                time.sleep(2)
                for i in range(num):
                    time.sleep(0.5)
                    i+=1
                    i = str(i)
                    js = "fn_egov_link_page('" + i + "');"
                    self.driver.execute_script(js)
                    time.sleep(1)
                    html = self.driver.page_source
                    soup = BeautifulSoup(html, 'html.parser')
                    self.rnd_crawl(soup)
                #self.author["rnd"] = self.papers
                print(self.test)
                self.author["rnd"] = self.papers
                self.main_title(soup)
                print("title" , self.author)
                try:
                    self.driver.find_element_by_id('paper').click()
                except Exception as e:
                    retry_paper_error_cnt =1
                    print("논문 버튼이 없습니다.")

                if retry_paper_error_cnt != 1:
                    a = soup.find('button',id = 'paper')      #여기서부터는 논문파트 
                    text = a.get_text()
                    b = text.rfind('/')
                    c = text.rfind('건')
                    num = math.ceil(int(text[b+1:c])/10)
                    # print(num)
                    # pagenum = math.ceil(num/10)
                    print(num)
                    for i in range(num):      
                    
                        print("실행1")
                        # print(a)
                        time.sleep(0.5)
                        pagesnum = i+1
                        jsn = str(pagesnum)
                        js = "fn_egov_link_page('" + jsn + "');"
                        self.driver.execute_script("fn_egov_link_page('" + jsn + "');")
                        print(js)
                        time.sleep(0.5)
                        html = self.driver.page_source
                        soup = BeautifulSoup(html, 'html.parser')
                        refer = soup.select('#paperInfo > li') 
                        self.crawl_paper(refer)
                try:
                    self.author["reference"] = self.paper
                    print(self.author)
                except Exception as e:
                    print(e)

                    
          #---------------------정상실행일때------------------        
            else:
                paper_error_cnt = 0
                # time.sleep(10)
                self.main_title(soup)

                ####################3 상준이형 추가 코드 ############################
                self.driver.find_element_by_xpath('/html/body/form[1]/div/div/div[1]/div[2]/div[2]/a[1]').click()
                time.sleep(3)

                # SCIENCEON 화면 지정
                self.driver.switch_to_window(self.driver.window_handles[2])

                # 저자 고유 ID 크롤링 (SCIENCEON)
                url = self.driver.current_url
                cn1 = url.find('cn=')
                cn2 = url.find('&')
                author_id = f'{url[cn1+3:cn2]}' # 저자 고유ID
                print(author_id)

                # 크롤링
                soup = BeautifulSoup(self.driver.page_source, 'html.parser')

                time.sleep(1)

                # info_ScienceOn -> SCIENCEON 저자 전문분야
                info_ScienceOn = self.driver.find_element_by_xpath('/html/body/div[3]/div/div/div[6]/div[2]').text
                print(info_ScienceOn)
                
                self.info["author_id"] = author_id
                self.info["Specialty"] = info_ScienceOn
                self.infolist.append(self.info)
                
                self.driver.close()
                self.driver.switch_to_window(self.driver.window_handles[1])
                print(self.driver.current_url)
                
                 ####################3 상준이형 추가 코드 끝 ############################
                self.author["authorInfo"] = self.infolist
                print("title" , self.author)
                ## 논문이라는 버튼 클릭과 논문 버튼이 없으면 그냥 넘어감
                try:
                    self.driver.find_element_by_id('paper').click()
                except Exception as e:
                    paper_error_cnt = 1
                    print("논문 버튼이 없습니다.")
                if paper_error_cnt != 1:
                    soup = BeautifulSoup(self.driver.page_source, 'html.parser')
                    a = soup.find('button',id = 'paper')      #여기서부터는 논문파트 
                    print(a)
                    text = a.get_text()
                    b = text.rfind('/')
                    c = text.rfind('건')
                    num = math.ceil(int(text[b+1:c])/10)+1
                    # print(num)
                    # pagenum = math.ceil(num/10)
                    print(num)
                    for i in range(num):      
                    
                        print("실행1")
                        # print(a)
                        time.sleep(0.5)
                        pagesnum = i+1
                        jsn = str(pagesnum)
                        js = "fn_egov_link_page('" + jsn + "');"
                        self.driver.execute_script("fn_egov_link_page('" + jsn + "');")
                        print(js)
                        time.sleep(0.5)
                        html = self.driver.page_source
                        soup = BeautifulSoup(html, 'html.parser')
                        refer = soup.select('#paperInfo > li') 
                        self.crawl_paper(refer)
                try:
                    self.author["reference"] = self.paper
                    print(self.author)
                except Exception as e:
                    print(e)
                
                

                a = self.author
            
            
            end = time.time() - start
            a["collection_time"] = end
            pprint.pprint(a)
            self.send_kafka(a)
        except Exception as e:
            print(e)
            print("start crawling 오류")
    def send_kafka(self,a):
        try:
            self.producer.send('test', value=a)
            self.producer.flush()
        except Exception as e:
            print(e)
            print("kafka send 오류")


def get_parameter(keyList):
    # print("keyList : ", keyList)
    for key in keyList:
        print("key : ", key)
        ls = list(expertFactor.find(
            {
                'keyId':key,
                "Productivity":{"$gt":0}, 
            },
            {
                "_id" : 0, 
                "keyId" : 1, 
                "A_ID" : 1, 
                "Productivity": 1, 
                "contirb" : 1, 
                "Durability" : 1, 
                "Recentness" : 1, 
                "Quality" : 1, 
                "Acc" : 1 
            }))
        # print(ls)
        for _id in ls:
            # print(_id)
            __id = author.find_one({'_id':_id['A_ID']})
            # print(__id)
            if __id is not None and 'isCollect' not in __id:
                result = rawData.find_one({'keyId':key,'mngId':_id['A_ID']},{'keyId':1,'mng':1,'IdAgency':1,'koTitle':1,'enTitle':1, '_id':0})
                # print(result)
                # if result is not None:
                    # print(result)
                yield result
                    # return result

__main__()
