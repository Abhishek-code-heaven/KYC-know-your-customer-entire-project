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



class PanVerification:
    
    def __init__(self):

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
        # self.pan_number=pan_number
        # self.full_name=full_name
        # self.dob=dob
        # self.status=status
        



    def pan_scrapper(self,pan_number,full_name,dob,status):


        self.browser.get("https://www1.incometaxindiaefiling.gov.in/e-FilingGS/Services/VerifyYourPanDeatils.html?lang=eng")

        pan_number_element=self.browser.find_element_by_id("VerifyYourPanGSAuthentication_pan")
        
        time.sleep(1)
        pan_number_element.send_keys(pan_number)

        full_name_input=self.browser.find_element_by_id("VerifyYourPanGSAuthentication_fullName")
        time.sleep(1)
        full_name_input.send_keys(full_name)


        date_of_birth=self.browser.find_element_by_id("dateField")
        time.sleep(1)
        date_of_birth.send_keys(dob)

        self.browser.find_element_by_xpath(f"//select[@name='status']/option[text()={status}]").click()


        time.sleep(2)
        self.browser.find_element_by_id("captchaImg").screenshot("captcha.png")

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
            print("&&&&&&&&&",info)
            info=info + 'extra'

            print("#############################",info)
            # captcha_text=df['description'][0]
            ip_element=self.browser.find_element_by_id("VerifyYourPanGSAuthentication_captchaCode")
            ip_element.send_keys(info)
            time.sleep(1)

        time.sleep(2)

        self.browser.find_element_by_id("submitbtn").click()

        time.sleep(2)
        elements=self.browser.find_elements_by_xpath('.//div[@class = "success"]')
        print(len(elements))

        a=None
        
        elements_error=self.browser.find_elements_by_xpath('.//div[@errorfor = "VerifyYourPanGSAuthentication_pan"]')
        print('.....................',len(elements_error))
        if len(elements_error)>0:
            error_invalid_pan=elements_error[0].text
            print("nitiinnitintnititn",error_invalid_pan)
            return error_invalid_pan

        elements_error=self.browser.find_elements_by_xpath('.//div[@errorfor = "VerifyYourPanGSAuthentication_fullName"]')
        print('.....................',len(elements_error))
        if len(elements_error)>0:
            error_invalid_pan=elements_error[0].text
            print("nitiinnitintnititn",error_invalid_pan)
            return error_invalid_pan
            
        
        
        print(elements)
        if len(elements)>0:
            a=elements[0].text
            print("++++++++++",a)
            return a
        return a    

    


    def check(self,pan_number,full_name,dob,status):
        check=self.pan_scrapper(pan_number,full_name,dob,status)
        while check == None:
            check=self.pan_scrapper(pan_number,full_name,dob,status)


        time.sleep(2)
        elements_error=self.browser.find_elements_by_xpath('.//div[@errorfor = "VerifyYourPanGSAuthentication_pan"]')
        print('.....................',len(elements_error))
        if len(elements_error)>0:
            error_invalid_pan=elements_error[0].text
            print("nitiinnitintnititn",error_invalid_pan)
            return error_invalid_pan
        else:
            return check   



    def generate_response(self,pan_number,full_name,dob,status):
        final_dict={}    
        check_to_enter_into_db=self.check(pan_number,full_name,dob,status)
        print(check_to_enter_into_db)
        dict_to_send={"panNumber":pan_number,"fullName":full_name,"dob":dob,"status":status,"panStatus":check_to_enter_into_db}

        if dict_to_send['panStatus'] == "Invalid PAN. Please retry.":
            final_dict['data']=""
            return final_dict
        
        elif dict_to_send['panStatus'] == "Please enter Full Name.":
            final_dict['data']=""
            return final_dict

        else:
            final_dict['data']=dict_to_send
            return final_dict