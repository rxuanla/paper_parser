# -*- coding: utf-8 -*-
import requests
import json
import mysql.connector
from mysql.connector import errorcode
import re
import traceback
import os
import time
import csv
from random import randint
from bs4 import BeautifulSoup


def db_connect():
    # Connect to the database
    cnx = mysql.connector.connect(user='root', password='thomas3198',
                                  host='127.0.0.1',
                                  database='Paper_parser')
    cnx.close()


def getHtml_ByGet(url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36'}
    try:
        time.sleep(randint(10,23))
        response = requests.get(url, timeout=50, headers=headers)
        response.raise_for_status()
        response.encoding = response.apparent_encoding
        return response.text
    except:
        with open('GetErrorLog.txt', 'a') as f:
            traceback.print_exc(file=f)


def DownloadPaper(DocumentNumber, source, year, PaperID,pdfSize):
    try:
        download_path = r".\static"  + "\{}\{}" .format(source,year) + "\\"
        file_path = download_path+str(PaperID)+'.pdf' 

        if not os.path.isdir(download_path):
            print("路徑不存在，建立路徑。")
            os.makedirs(download_path)

        #print("download_path: "+download_path)
        #print("file_path: "+file_path)
        while True:
            time.sleep(randint(3,9))
            download_url = 'https://ieeexplore.ieee.org/stampPDF/getPDF.jsp?tp=&arnumber='+DocumentNumber
            response = requests.get(download_url, timeout=50, headers=headers)
            with open(file_path, 'wb+') as f:
                print('Start download file ', '\n')
                f.write(response.content)
            fileSize = os.path.getsize(file_path)
            #print(fileSize)
            #print("fileSize type: " + str(type(fileSize)))
            #print(pdfSize)
            #print("pdfSize type: " + str(type(pdfSize)))
            if fileSize/1024  > int(pdfSize):
                break            

    except: 
        traceback.print_exc()
        with open('DownloadErrorLog.txt', 'a') as f:
            f.write("\n-------------------------------------------PaperID: "+PaperID+"--------------------------------------------\n")
            traceback.print_exc(file=f)

def ReadSourceUrl(filename):
    with open(filename, 'r',newline='',encoding='UTF-8-sig') as f:
        rows =  csv.DictReader(f)

        SourceList = list()
        YearList = list()
        LinkList = list()
        isnumberList= list()

        for i,row in enumerate(rows):
            YearList.append(row['Year']) 
            LinkList.append(row['Link'])
            isnumberList.append(row['isnumber'])
            SourceList.append(row['Source'])

        SourceDict = {'Source': SourceList,'Year':YearList,'Link':LinkList,'isnumber':isnumberList}

        return SourceDict
        

if __name__ == '__main__':
    
    seconds = time.time()
    local_time = time.ctime(seconds)
    MainErrorLog_path = 'MainErrorLog.txt'
    with open(MainErrorLog_path, 'a') as f:
        f.seek(0)
        f.write("--------------------------------------------"+local_time+"--------------------------------------------\n")
    
    with open('DownloadErrorLog.txt', 'a') as f:
        f.seek(0)
        f.write("--------------------------------------------"+local_time+"--------------------------------------------\n")

    SourceDict = ReadSourceUrl("icse.csv")
    
    for i,row in enumerate(SourceDict['Year']):
        #download setting
        pageNumber = 1  # 翻頁改 pageNumber
        isnumber = SourceDict['isnumber'][i]
        if (SourceDict['Source']=='TSE'):
            punumber = 32  #TSE 均為32
        else:
            pattern = '\d{7}|\d{8}'
            punumber = re.search(pattern,SourceDict['Link'][i]).group()
        year = SourceDict['Year'][i]
        source = SourceDict["Source"][i]  # "ICSE"=1 , "TSE"=2, "KDE"=3
        if source == "ICSE":
            sourceID = 1
        elif source == "TSE":
            sourceID =  2
        elif source == "KDE":
            sourceID = 3
    
    
        # 此頁面利用 Ajax 載入 paper list ，無法直接解析頁面
        # 取得所有標題
        print(source+" "+year)
        while True:
            headers = {
            'Referer': 'https://ieeexplore.ieee.org/xpl/conhome/'+str(punumber)+'/proceeding?   pageNumber='+str(pageNumber),
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like    Gecko) Chrome/92.0.4515.107 Safari/537.36'
            }
            #'Referer': 'https://ieeexplore.ieee.org/xpl/conhome/'+str(punumber)+'/proceeding?  pageNumber='+str(pageNumber),
            # 翻頁改 pagenumber ; TSE沒有page number
            payload = {
                'isnumber': str(isnumber),
                'punumber': str(punumber),
                'pageNumber': str(pageNumber),
            }
            #payload  'sortType': 'vol-only-seq'
            IEEE_response = requests.post(url = 'https://ieeexplore.ieee.org/rest/search/pub/'+str  (punumber)+'/issue/'+str(isnumber)+'/toc',data= json.dumps(payload), headers = headers)
            papers = json.loads(IEEE_response.text)
            #print(papers)
            #print(payload['pageNumber'])
            #print(payload)
            #print("payload type: " + str(type(payload)))   #payload type: <class 'dict'>
            #print(type(payload['pageNumber']))
            #print(data['pageNumber'])
            #print("payload['pageNumber'] : " + str(payload['pageNumber']) )
            #print("payload['pageNumber'] type: " + str(type(payload['pageNumber'])))
            #print(headers['Referer'])
            #print("papers type: " + str(type(papers)))     #papers type: <class 'dict'>
            #print("papers['records'] : " + str(papers['records']) )
            #print("papers['records'] type: " + str(type(papers['records'])))


            for paper in papers['records']:
                print(paper['articleTitle'])

                try: 
                    soup = BeautifulSoup(getHtml_ByGet('https://ieeexplore.ieee.org/'+paper ['documentLink']), 'lxml')  
                    pattern = re.compile( r'xplGlobal.document.metadata=(.*?});', re.MULTILINE | re.    DOTALL)
                    script = soup.find("script", text=pattern)
                    response_dict = pattern.search(script.string).group(1)
                    json_data = json.loads(response_dict)
                    #print("Authors:")
                    #for author in json_data['authors']:
                    #   print(author['name']+ '  ('+author['affiliation'][0]+')')
                    #print("Abstract: "+json_data['abstract'])
                    #print("Domain: ", end= '')
                    #for kwd_type in json_data['keywords']:
                    #    print('\n' + kwd_type['type']+": ", end= '')
                    #    for kwd in kwd_type['kwd']:
                    #        print(kwd+", ", end= '')

                    citation_url = 'https://ieeexplore.ieee.org/rest/search/citation/format?recordIds=' + json_data['articleNumber']+'&download-format=download-bibtex& lite=true'

                    headers = {
                        'Referer': 'https://ieeexplore.ieee.org/'+paper['documentLink'],
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36'
                    }
                    time.sleep(randint(2,6))
                    IEEE_response = requests.get(url=citation_url, headers=headers,timeout=50)
                    citation_json = json.loads(IEEE_response.text)
                    #print("\nCitation: "+citation_json['data'])
                    #寫入資料庫

                    try:
                        cnx = mysql.connector.connect(user='root', password='thomas3198',
                                      host='127.0.0.1',
                                      database='Paper_parser')
                        cursor = cnx.cursor()
                        #新增Paper detail
                        addStatement = ("INSERT INTO paper (Title, Year, Source, Abstract, Citation)    VALUES (%s,%s,%s,%s,%s)")
                        StatementData = (paper['articleTitle'],year,sourceID,json_data['abstract'], citation_json['data'])
                        cursor.execute(addStatement,StatementData)
                        cnx.commit()
                        paperID = int(cursor.lastrowid)

                        #新增Authorlist
                        for author in json_data['authors']:
                            try:
                                addStatement = ("INSERT INTO authorlist (Name, Department) VALUES   (%s,%s)")
                                StatementData = (author['name'],author['affiliation'][0])
                                cursor.execute(addStatement,StatementData)
                                cnx.commit()
                                authorID = int(cursor.lastrowid)

                            except mysql.connector.IntegrityError as err:
                                #search duplicaate authorID
                                if err.errno == errorcode.ER_DUP_ENTRY:
                                    cursor = cnx.cursor()
                                    addStatement = ("SELECT AuthorID FROM authorlist WHERE Name =   %s")
                                    cursor.execute(addStatement,(author['name'],))
                                    result = cursor.fetchone()
                                    #print(str(type(result))) #type:<class 'tuple'>
                                    authorID= result[0]  
                            except mysql.connector.Error as err:
                                        traceback.print_exc()
                                        with open(MainErrorLog_path, 'a') as f:
                                            f.write(paper['articleTitle']+"\n")
                                            traceback.print_exc(file=f)
                                        continue
                            finally:
                                addStatement = ("INSERT INTO paperauthors (PaperID, AuthorID) VALUES    (%s,%s)")
                                StatementData = (paperID,authorID)
                                cursor.execute(addStatement,StatementData)
                                cnx.commit()

                        #新增Domainlist
                        for kwd_type in json_data['keywords']:
                            for kwd in kwd_type['kwd']:
                                KeywordList = kwd.split(", ")
                                for keyword in KeywordList:
                                    try:
                                        addStatement = ("INSERT INTO domainlist (Keyword) VALUES (%s)")
                                        cursor.execute(addStatement,(keyword,))
                                        cnx.commit()
                                        keywordID = int(cursor.lastrowid)
                                    except mysql.connector.IntegrityError as err:
                                        if err.errno == errorcode.ER_DUP_ENTRY:
                                            addStatement = ("SELECT KeywordID FROM domainlist WHERE Keyword = %s")
                                            cursor.execute(addStatement,(keyword,))
                                            result = cursor.fetchone()
                                            keywordID= result[0]  
                                    except mysql.connector.Error as err:
                                        traceback.print_exc()
                                        with open(MainErrorLog_path, 'a') as f:
                                            f.write(paper['articleTitle']+"\n")
                                            traceback.print_exc(file=f)
                                        continue
                                    finally:
                                        addStatement = ("INSERT INTO paperdomains (PaperID, KeywordID)  VALUES (%s,%s)")
                                        StatementData = (paperID,keywordID)
                                        cursor.execute(addStatement,StatementData)

                    except mysql.connector.Error as err:
                        with open(MainErrorLog_path, 'a') as f:
                            if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
                                f.write("Something is wrong with your user name or password\n")
                                print("Something is wrong with your user name or password\n")
                            else:
                                f.write(str(err)+"\n")
                                print(err)
                    finally:    
                        cursor.close()
                        cnx.close()

                    #DownloadPaper(json_data['articleId'], source, year, paperID, paper['pdfSize'])
                except:
                    traceback.print_exc()
                    with open(MainErrorLog_path, 'a') as f:
                        f.write(paper['articleTitle']+"\n")
                        traceback.print_exc(file=f)
                    continue

            #翻頁
            pageNumber = pageNumber + 1
            totalPages = int(papers['totalPages'])
            print("pageNumber: "+str(pageNumber))
            print("totalPages: "+str(totalPages))
            if pageNumber > totalPages:
                break

            