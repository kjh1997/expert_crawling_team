
#----------중간부터 들어가는 버전---------------다른 교수님으로 해도 작동합니다

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
import os
from bs4 import BeautifulSoup
import re
import time
import pprint
import math
# from kafka import KafkaProducer
import json

# producer = KafkaProducer(bootstrap_servers= 'localhost:9092', value_serializer=lambda x: json.dumps(x).encode('utf-8'))
# name = input("이름")
name="유재수"
print(name)
chrome_options = Options()
chrome_options.add_argument('window-size=1920,1080') #중간부터 들어가려면 화면 사이즈 좀 키워야해서 추가했습니다.
chromedriverpath = "C:/Users/kjh19/OneDrive/바탕 화면/test/chromedriver"
driver = webdriver.Chrome(chromedriverpath, chrome_options=chrome_options)
driver.get("https://www.ntis.go.kr/ThSearchHumanDetailView.do")

driver.find_element_by_xpath('/html/body/div[1]/div[2]/div[2]/button[1]').click()

driver.switch_to_window(driver.window_handles[1])  # 로그인창으로 전환 이거는 빼면 작동 x
driver.find_element_by_xpath('/html/body/div/form/label[2]/input').send_keys("normaljun95")
driver.find_element_by_xpath('/html/body/div/form/label[4]/input').send_keys("harrypotter95^") #아이디와 비밀번호
driver.find_element_by_xpath('/html/body/div/form/input').click()
time.sleep(2)

driver.switch_to_window(driver.window_handles[0]) #혹시 모를 화면 전환. 빼도 상관없음

driver.find_element_by_xpath('/html/body/div[4]/div[1]/div[1]/input').send_keys(name)
driver.find_element_by_xpath('/html/body/div[4]/div[1]/div[1]/button').click()
driver.find_element_by_xpath('/html/body/div[5]/div/div/div[3]/form/div[3]/div[2]/div[1]/div/a[1]').click()     #여기까지 공통부분

# 저자 화면 지정
driver.switch_to_window(driver.window_handles[1])

soup = BeautifulSoup(driver.page_source, 'lxml')

author = {}
try:
    authorInfo = {}

    thumnails = []
    thumnail = soup.select_one('#viewForm > div > div > div.article.bdr3.p20 > div.userphoto.po_rel > img')
    thumnails.append(thumnail)
    authorInfo["thumnails"] = thumnails

    name = soup.select_one('.mb5').text
    name = name.lstrip()
    name = ' '.join(name.split())
    authorInfo["name"] = name

    details = soup.find("div", attrs={"class":"m0 lh15 f13"}).get_text()
    details = ' '.join(details.split())
    details = details.lstrip()
    authorInfo["details"] = details

    edu = []
    for tag in soup.select('dd.bd0'):
        ed = tag.get_text(separator='|br|', strip=True).split('|br|')
        # ed = tag.get_text(strip=True, separator=" ")
        edu.append(ed)
    authorInfo["Education"] = edu
    
    carear = []
    for tag in soup.select('ul.mt20'):
        ca = tag.get_text(separator='|li|', strip=True).split('|li|')
        carear.append(ca)
    authorInfo["carear"] = carear
    
    author["authorInfo"] = authorInfo

    """ 논문 수집 """
    a = soup.find('button',id = 'paper')      #여기서부터는 논문파트 
    text = a.get_text()
    b = text.rfind('/')
    c = text.rfind('건')
    num = math.ceil(int(text[b+1:c])/10)
    # print(num)
    pagenum = math.ceil(num/10)
    driver.find_element_by_xpath('/html/body/form[1]/nav/div[2]/button[2]').click()
      

    paper = []
            
    time.sleep(1)
    try :
        for i in range(3):      
        
            print("실행1")
            # print(a)
            time.sleep(0.5)
            pagesnum = i+1
            jsn = str(pagesnum)
            js = "fn_egov_link_page('" + jsn + "');"
            driver.execute_script("fn_egov_link_page('" + jsn + "');")
            print(js)
            time.sleep(0.5)
            html = driver.page_source
            soup = BeautifulSoup(html, 'html.parser')
            
        
            refer = soup.select('#paperInfo > li') 
            try:
                for num, ref in enumerate(refer[:10]):
                    a= {}
                    title = ref.select_one('p')
                    title = title.text
                    title = re.sub('&nbsp; | &nbsp;| \n|\t|\r','',title).replace("\xa0","")
                    a["title"] = title
                    print(a)
                
                    ref.p.decompose()
                    refs = ref.get_text(separator='|br|', strip=True).split('|br|')
                    partition = refs[1]
                    
                    print(num,"번째 coau",refs[0])
                    # print(num,"번째 refs",refs[1])   
                    # a[i][num]['coau']=refs[0]
                    # a[i][num]['reference']=refs[1]
                    # try:
                    
                    num1 = partition.rfind("[")
                    num2 = partition.rfind("]")+1
                    num3 = partition.rfind("(")
                    num4 = partition.rfind(")")+1
                    try:
                        if partition.index('[') == True and partition.index(']') == True:
                            partition = refs[0]
                            if num1 == -1 and num3 == -1:
                                a["ref1"] = partition.replace("\t","")
                                a["ref2"] = ""
                                a["year"] = ""
                                print("분할",partition)

                            elif num1 == -1 and num3 >= 0:
                                a["ref1"] = partition[:num3].replace("\t","")
                                a["ref2"] = ""
                                
                                a["year"] = partition[num3:num4]
                                print("ref1", partition[:num3])

                                print("year", partition[num3:num4])
                            
                            else:
                                a["ref1"] = partition[:num1].replace("\t","")
                                a["ref2"] = partition[num1:num2]
                                a["year"] = partition[num3:num4]
                                print("ref1", partition[:num1])
                                print("ref2", partition[num1:num2])
                                print("year", partition[num3:num4])
                    

                        elif num1 == -1 and num3 == -1:
                            a["ref1"] = partition.replace("\t","")
                            a["ref2"] = ""
                            a["year"] = ""
                            print("분할",partition)

                        elif num1 == -1 and num3 >= 0:
                            a["ref1"] = partition[:num3].replace("\t","")
                            a["ref2"] = ""
                            
                            a["year"] = partition[num3:num4]
                            print("ref1", partition[:num3])

                            print("year", partition[num3:num4])
                        
                        else:
                            a["ref1"] = partition[:num1].replace("\t","")
                            a["ref2"] = partition[num1:num2]
                            a["year"] = partition[num3:num4]
                            print("ref1", partition[:num1])
                            print("ref2", partition[num1:num2])
                            print("year", partition[num3:num4])
                    except Exception as e:
                            print(e)
                    print(a)
                    paper.append(a)
                    
                    # print("partition1", partition[:num1])
                    # print("partition2",partition[num1:num2])
                    # print("partition3", partition[num3:num4])
            except Exception as e:
                print(e,"refs, co-author crawl")
            main = driver.window_handles 
            print(main)           
    except Exception as e:
        print(e,"여기서 오류")

    author["reference"] = paper
    """ R&D 수집 """
    driver.find_element_by_xpath('/html/body/form[1]/nav/div[2]/button[4]').click()
    time.sleep(2)
    
    papers = []
    for i in range(3):
        time.sleep(1)
        i+=1
        i = str(i)
        js = "fn_egov_link_page('" + i + "');"
        driver.execute_script(js)
        time.sleep(1)
        html = driver.page_source
        soup = BeautifulSoup(html, 'html.parser')
        
        brs  = soup.select('#rndInfo > li')
        
        for num, br in enumerate(brs[:10]):
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
                a['RND_num'] = RND_num
                a['RND_year'] = RND_year
                a['RND_period'] = RND_period
                a['RND_bz_name'] = RND_bz_name

                a['RND_ins'] = brlist2
                papers.append(a)
                print(brlist2)
            except Exception as e:
                print(e)

    author["rnd"] = papers
    # print(author)
    # pprint.pprint(author)
except Exception as e:
    print(e)

main = driver.window_handles 
for handle in main: 
    driver.switch_to_window(handle) 
    driver.close()
pprint.pprint(author)



# print(author)
# pprint.pprint(author)

# html=  driver.page_source
# soup= BeautifulSoup(html,'html.parser')
# a = soup.find('button',id = 'paper')      #여기서부터는 논문파트 
# text = a.get_text()
# b = text.rfind('/')
# c= text.rfind('건')
# num = math.ceil(int(text[b+1:c])/10)
# print(num)
# pagenum = math.ceil(num/10)
# driver.find_element_by_xpath('/html/body/form[1]/nav/div[2]/button[2]').click()
# title = []  
# a={}
# a["Dissertation"]={}
           
# time.sleep(1)
# try :
#     for i in range(3):      
#         a["Dissertation"][i]={}
#         print("실행1")
#         # print(a)
#         time.sleep(0.5)
#         pagesnum = i
#         jsn = str(pagesnum)
#         js = "fn_egov_link_page('" + jsn + "');"
#         driver.execute_script("fn_egov_link_page('" + jsn + "');")
#         print(js)
#         time.sleep(0.5)
#         html = driver.page_source
#         soup = BeautifulSoup(html, 'html.parser')
#         pages  = soup.select('#paperInfo > li > p')  
        
#         for num, page in enumerate(pages[:10]):
#             print("실행3")
#             a["Dissertation"][i][num] = {}
#             print("실행2")
#             # a[i][num] = {}
#             # print(a)
#             title = page.text
#             title = re.sub('&nbsp; | &nbsp;| \n|\t|\r','',title)
#             a["Dissertation"][i][num]["title"] = title.replace("\xa0","")
#             print(type(title))                
#             # a[i][num]['title']=title
                
                    
#             print(num, "번째 title :",title)
        
    
#         refer = soup.select('#paperInfo > li') 
#         try:
#             for num, ref in enumerate(refer[:10]):
#                 a["Dissertation"][i]
#                 ecnt =0
#                 ref.p.decompose()
#                 refs = ref.get_text(separator='|br|', strip=True).split('|br|')
#                 partition = refs[1]
                
#                 print(num,"번째 coau",refs[0])
#                 # print(num,"번째 refs",refs[1])   
#                 # a[i][num]['coau']=refs[0]
#                 # a[i][num]['reference']=refs[1]
#                 # try:
                
#                 num1 = partition.rfind("[")
#                 num2 = partition.rfind("]")+1
#                 num3 = partition.rfind("(")
#                 num4 = partition.rfind(")")+1
#                 if num1 == -1 and num3 == -1:
#                     a["Dissertation"][i][num]["ref1"] = partition
#                     a["Dissertation"][i][num]["ref2"] = ""
#                     a["Dissertation"][i][num]["year"] = ""
#                     print("분할",partition)

#                 elif num1 == -1 and num3 >= 0:
#                     a["Dissertation"][i][num]["ref1"] = partition[:num3]
#                     a["Dissertation"][i][num]["ref2"] = ""
                    
#                     a["Dissertation"][i][num]["year"] = partition[num3:num4]
#                     print("ref1", partition[:num3])

#                     print("year", partition[num3:num4])
                
#                 else:
#                     a["Dissertation"][i][num]["ref1"] = partition[:num1]
#                     a["Dissertation"][i][num]["ref2"] = partition[num1:num2]
#                     a["Dissertation"][i][num]["year"] = partition[num3:num4]
#                     print("ref1", partition[:num1])
#                     print("ref2", partition[num1:num2])
#                     print("year", partition[num3:num4])
                
                
#                 # print("partition1", partition[:num1])
#                 # print("partition2",partition[num1:num2])
#                 # print("partition3", partition[num3:num4])
#         except Exception as e:
#             print(e,"refs, co-author crawl")
#             main = driver.window_handles 
#             print(main)           
# except Exception as e:
#     print(e,"여기서 오류")

# # try:
# #     main = driver.window_handles
# #     for handle in main: 
# #         driver.switch_to_window(handle) 
# #         driver.close()
# # except Exception as e:
# #     print(e, "페이지 닫기 문제")
# # print("검색결과")

# print(a)
# # print("정상종료")
# # producer.send('test', value=a)
# # producer.flush()

# #------------------------버전1 // 처음부터 들어가는 버전--------------------------
# # from selenium import webdriver
# # from selenium.webdriver.chrome.options import Options
# # from selenium.webdriver.common.keys import Keys
# # import os
# # from bs4 import BeautifulSoup
# # import re
# # import time
# # import math
# # name = input("이름")
# # print(name)
# # chromedriverpath = "C:/Users/admin/Desktop/test/chromedriver.exe"
# # driver = webdriver.Chrome(executable_path=chromedriverpath)
# # driver.get("https://www.ntis.go.kr/ThMain.do")
# # main = driver.window_handles 
# # for handle in main: 
# #     if handle != main[0]: 
# #         driver.switch_to_window(handle) 
# #         driver.close()
# # driver.switch_to_window(driver.window_handles[0])
# # driver.find_element_by_class_name('mainloginbtn').click()
# # print(driver.window_handles)
# # driver.switch_to_window(driver.window_handles[1])
# # driver.find_element_by_name('userid').send_keys("normaljun95")
# # driver.find_element_by_name('password').send_keys("harrypotter95^")
# # driver.find_element_by_xpath('/html/body/div/form/input').click()
# # time.sleep(3)
# # main = driver.window_handles 
# # for handle in main: 
# #     if handle != main[0]: 
# #         driver.switch_to_window(handle) 
# #         driver.close()
# # driver.switch_to_window(driver.window_handles[0])

# # driver.find_element_by_xpath('/html/body/div[2]/nav/div/form/div[2]/button[3]').click()
# # driver.find_element_by_xpath('/html/body/div[2]/nav/div/form/div[2]/ul[3]/li[2]/a').click()
# # driver.find_element_by_xpath('/html/body/div[4]/div[1]/div[1]/input').send_keys(name)
# # driver.find_element_by_xpath('/html/body/div[4]/div[1]/div[1]/button').click()
# # driver.find_element_by_xpath('/html/body/div[5]/div/div/div[3]/form/div[3]/div[2]/div[1]/div/a[1]').click()
# # driver.switch_to_window(driver.window_handles[1])
# # html=  driver.page_source
# # soup= BeautifulSoup(html,'html.parser')
# # a = soup.find('button',id = 'paper')
# # text = a.get_text()
# # b = text.rfind('/')
# # c= text.rfind('건')
# # num = math.ceil(int(text[b+1:c])/10)
# # print(num)
# # driver.find_element_by_xpath('/html/body/form[1]/nav/div[2]/button[2]').click()
# # title = []
# # time.sleep(2)
# # for i in range(num):
# #     time.sleep(1)
# #     i+=1
# #     i = str(i)
# #     js = "fn_egov_link_page('" + i + "');"
# #     driver.execute_script("fn_egov_link_page('" + i + "');")
# #     print(js)
# #     time.sleep(1)
# #     html = driver.page_source
# #     soup = BeautifulSoup(html, 'html.parser')
# #     pages  = soup.select('#paperInfo > li > p')   #완성본
# #     for num, page in enumerate(pages[:10]):
# #         title = page.text
# #         title = re.sub('&nbsp; | &nbsp;| \n|\t|\r','',title)
# #         print(num, "번째 title :",title)
    
# #     refer = soup.select('#paperInfo > li')  
# #     for num, ref in enumerate(refer[:10]):
# #         ref.p.decompose()
# #         refs = ref.get_text(separator='|br|', strip=True).split('|br|')
# #         print(num,"번째 coau",refs[0])
# #         print(num,"번째 refs",refs[1])
# #         print(type(refs))

#         #----------------------노력의 결과-------------------------
#     # for num, ref in enumerate(refer[:1]):
#     #     print(num,"번")
#     #     ref.p.decompose()
#     #     refs = ref.text
#     #     print("ref",ref)
#     #     print(type(ref))
#     #     print("ref text",ref.text[0])
#     #     print("refs",refs)
#     #     print(type(refs))
#         # print("ref : " , refs)
# #  for num, ref in enumerate(refer[:1]):
# #         print(num,"번")
# #         ref.p.decompose()
# #         print(type(ref))
# #         print(ref.text[0]
# #         # print("ref : " , refs)
# #/html/body/form[1]/div/div/div[2]/div[2]/dl/dd/ul/li[6]/text()[1]
# #/html/body/form[1]/div/div/div[2]/div[2]/dl/dd/ul/li[6]/text()[2]
#     # titles = driver.find_element_by_xpath('/html/body/form[1]/div/div/div[2]/div[2]/dl/dd/ul/li[1]/p/a[1]/span')
#     # reference = driver.find_element_by_xpath('/html/body/form[1]/div/div/div[2]/div[2]/dl/dd/ul/li[1]')
#     #coauthor = driver.find_element_by_xpath('/html/body/form[1]/div/div/div[2]/div[2]/dl/dd/ul/li[1]')
#     #time.sleep(1)
#     #print(title)
#     #print(coauthor)
#     #print(reference)
#     # html = driver.page_source
#     # soup = BeautifulSoup(html, 'html.parser')
#     # titles  = soup.select('#paperInfo > li:nth-child(1) > p > a:nth-child(2) > span')
#     # title=[]
#     # for i in titles:
#     #     temp= i.replace("\t","").replace("\n","")
#     #     title.append(temp)
#     # print(titles)
# #     for text in titles:
# #         title.append(text)
# #     time.sleep(2)
# # print(title).

# # if len(a) >= 1:
# #     driver.find_element_by_xpath('/html/body/form[1]/nav/div[2]/button[2]').click()
# #     text = driver.find_element_by_xpath('/html/body/form[1]/nav/div[2]/button[2]/text()')
# #     b = text.rfind('/')
# #     c= text.rfind('건')
# #     d = text[b+1:c]
# #     print(d)
# # driver.find_element_by_xpath('/html/body/div[4]/div[1]/div[1]/button').click()
# # driver.find_element_by_xpath('/html/body/div[4]/div[1]/div[1]/button').click()
# # driver.find_element_by_xpath('/html/body/div[4]/div[1]/div[1]/button').click()

