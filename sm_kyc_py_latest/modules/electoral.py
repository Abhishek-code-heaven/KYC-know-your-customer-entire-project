from selenium import webdriver
from selenium.webdriver.common.keys import Keys
import urllib.request
from PIL import Image
import time
from selenium.common.exceptions import NoSuchElementException

import pandas as pd
import os,io
from google.cloud import vision
from google.cloud.vision import types
from selenium.webdriver.support import expected_conditions as EC



class ElectoralSearchVerification:
    
    def __init__(self,epic_number):

        os.environ[
            "GOOGLE_APPLICATION_CREDENTIALS"] = "vision_api_token.json"

        self.client = vision.ImageAnnotatorClient()
        options = webdriver.ChromeOptions()
        options.add_experimental_option("excludeSwitches", ['enable-automation'])
        options.add_argument("--incognito")
        options.add_argument("--start-maximized")
        options.add_argument("--disable-infobars")
        options.add_argument("--disable-extension")
        self.browser = webdriver.Chrome(executable_path="/home/ril-lt-naval/Desktop/scrapperapi/modules/chromedriver",options=options)
        self.FILE_NAME="captcha.png"
        self.FOLDER_PATH="/home/ril-lt-naval/Desktop/scrapperapi"
        self.epic_number=epic_number



    
    def read_and_write_captcha(self):
        self.browser.find_element_by_id("captchaEpicImg").screenshot("captcha.png")

        with io.open(os.path.join(self.FOLDER_PATH,self.FILE_NAME),'rb') as image_file:
            content=image_file.read()


        image= vision.types.Image(content=content)
        response= self.client.text_detection(image=image)
        texts=response.text_annotations

        print(texts)

        df = pd.DataFrame(columns=['locale','description'])

        for text in texts:
            
            
            df=df.append(dict(
                locale=text.locale,
                description=text.description
                ),
                ignore_index=True
                )
        print("this is dataframe",df)
        if not df.empty :
                
            captcha_text=df.iloc[[0],[1]]
            print("%%%%%%%%%",captcha_text)
            data=str(captcha_text["description"][0])
            print("@@@@@@",data)
            info="".join(data.split())

            print("#############################",info)
            # captcha_text=df['description'][0]
            ip_element=self.browser.find_element_by_id("txtEpicCaptcha")
            ip_element.send_keys(info)
            time.sleep(1)

            self.browser.find_element_by_id("btnEpicSubmit").click()
            time.sleep(3)

            error_elements=self.browser.find_elements_by_xpath(f"//span[@class='help-inline ng-binding']")
            print('this is length of error elements',len(error_elements))
            if len(error_elements)>0:
                for i,v in enumerate(error_elements):
                    if v.text == "Wrong Captcha":
                        return v.text



    def electoralsearch_scrapper(self,epic_no):


        self.browser.get("https://electoralsearch.in/")
        time.sleep(1)
        self.browser.find_element_by_id("continue").click()
        time.sleep(1)
        self.browser.find_element_by_xpath(f"//li[@aria-controls='#tab2']").click()
        time.sleep(1)
        name_element=self.browser.find_element_by_id("name")
        name_element.send_keys(epic_no)

        time.sleep(4)

        a=self.read_and_write_captcha()
        print("aaaaaaaaaaaaaaaaaaa,",a)
        
        while a == "Wrong Captcha":
            a=self.read_and_write_captcha()


    

    def generate_response(self):


        self.electoralsearch_scrapper(self.epic_number)

        time.sleep(5)

        elements_on_first_page=self.browser.find_elements_by_xpath(f"//td[@class='ng-binding']")
        elements_values=[]
        if len(elements_on_first_page)>0:
            for element in elements_on_first_page:
                elements_values.append(element.text)
                
            age=elements_values[2]
            father_or_husband_name=elements_values[3]
            fhl=father_or_husband_name.split("\n")
            father_or_husband_name=fhl[0]
            district=elements_values[5]


        time.sleep(5)

        final_dict_to_send={}
        error_elements=self.browser.find_elements_by_xpath(f"//div[@class='seven eighths padded ng-binding']")
        check_return=error_elements[0].text
        check_return_list=check_return.split(": ")
        to_check=int(check_return_list[1])
        # कुल परिणाम / Number of Record(s) Found: 0

        if to_check == 0:
            final_dict_to_send['data']=""
            return final_dict_to_send


        self.browser.find_element_by_xpath(f"//input[@value='View Details']").click()
        time.sleep(1)


        self.browser.switch_to_window(self.browser.window_handles[-1])
        time.sleep(2)
        answer_elements=self.browser.find_elements_by_xpath(f"//td[@style='font-size: 12px;']")
        print(len(answer_elements))
        
        if len(answer_elements)>0:
            state=answer_elements[1].text
            AssemblyConstituencyandAssemblyConstituencyNumber=answer_elements[3].text
            ParliamentaryConstituency=answer_elements[5].text
            Name=answer_elements[6].text
            Gender=answer_elements[8].text
            EpicNo=answer_elements[9].text
            PartNumber=answer_elements[12].text
            PartName=answer_elements[14].text
            SerialNumber=answer_elements[16].text
            PollingStation=answer_elements[18].text
            PollngDate=answer_elements[20].text
            from datetime import datetime
            date_obj = datetime.strptime(PollngDate, '%d/%m/%Y')
            PollngDate = date_obj.strftime('%d-%b-%Y')
            LastUpdatedOn=answer_elements[22].text
            date_obj = datetime.strptime(LastUpdatedOn, '%d/%m/%Y')
            LastUpdatedOn = date_obj.strftime('%d-%b-%Y')
            
            dict_to_send={}
            dict_to_send['name']=Name
            dict_to_send['epicNo']=EpicNo
            dict_to_send['gender']=Gender
            dict_to_send['age']=age
            dict_to_send['fatherOrHusbandName']=father_or_husband_name
            dict_to_send['state']=state
            dict_to_send['district']=district
            dict_to_send['pollingStation']=PollingStation
            dict_to_send['pollngDate']=PollngDate
            dict_to_send['assemblyConstituencyAndAssemblyConstituencyNumber']=AssemblyConstituencyandAssemblyConstituencyNumber 
            dict_to_send['partNumber']=PartNumber
            dict_to_send['partName']=PartName
            dict_to_send['parliamentaryConstituency']=ParliamentaryConstituency
            dict_to_send['serialNumber']=SerialNumber
            dict_to_send['lastUpdatedOn']=LastUpdatedOn

            
            final_dict_to_send['data']=dict_to_send
            return final_dict_to_send
            
