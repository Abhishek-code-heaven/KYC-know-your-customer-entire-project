from selenium import webdriver
from selenium.webdriver.common.keys import Keys
import urllib.request
from PIL import Image
import time
from selenium.common.exceptions import NoSuchElementException,UnexpectedAlertPresentException

import pandas as pd
import os,io
from google.cloud import vision
from google.cloud.vision import types
from selenium.webdriver.support import expected_conditions as EC



class LegalEntityIdentifier:
    
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
        self.browser = webdriver.Chrome(executable_path="/home/ril-lt-naval/Desktop/classesofscrappers/chromedriver",options=options)
        self.FILE_NAME="captcha.png"
        self.FOLDER_PATH="/home/ril-lt-naval/Desktop/classesofscrappers"
    

    def tackle_captcha(self):
        time.sleep(2)
        self.browser.find_element_by_xpath('.//div[@id = "ctl00_ContentPlaceHolder1_UpdPnlRefresh"]').screenshot("captcha.png")
        # self.browser.find_element_by_id("form_rcdl:j_idt32:j_idt38").screenshot("captcha.png")

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
            ip_element=self.browser.find_element_by_id("ctl00_ContentPlaceHolder1_txtCaptcha")
            ip_element.send_keys(info)
            time.sleep(1)

        time.sleep(2)

        self.browser.find_element_by_id("ctl00_ContentPlaceHolder1_btnSearch").click()

        time.sleep(2)
        try:
            self.browser.find_element_by_xpath(u'//a[text()="OK"]').click()
        except NoSuchElementException:
            print("Element Not Found")
            return "Element Not Found"
        except UnexpectedAlertPresentException:
            print("Captcha Entered is not valid")
            return "Captcha Entered is not valid"

        return "Captcha Entered is Correct"



    def legal_entity_identifier(self,lei_code):
        print(lei_code)
        self.browser.get("https://www.ccilindia-lei.co.in/USR_SEARCH_ANONYMOUS.aspx")

        time.sleep(2)

        self.browser.find_element_by_id("ctl00_ContentPlaceHolder1_chkbCriteria").click()
        time.sleep(4)


        lei_code_element=self.browser.find_element_by_id("ctl00_ContentPlaceHolder1_txtLeiCode")
        time.sleep(1)
        lei_code_element.send_keys(lei_code)
        

        time.sleep(2)
        
        response_from_captcha=self.tackle_captcha()

        while response_from_captcha == "Captcha Entered is not valid":
            response_from_captcha = self.tackle_captcha()
        

        time.sleep(3)

        self.browser.find_element_by_id("ctl00_ContentPlaceHolder1_gdvSearchLEI_ctl02_lnkViewDetails").click()

        time.sleep(4)

        self.browser.switch_to_window(self.browser.window_handles[-1])
       
        time.sleep(2)

        key_list1=["legalNumber","legalName","registeredFirstLineAddressLine","additionalAddressLine","additionalAddressLine2","additionalAddressLine3","country","region","city","postalPincode","registrationAuthorityName","registrationAuthorityId","jurisdiction","legalForm","leiRegistrationDate","leiRegLastUpdatedDate","entityStatus","entityExpirationDate","leiNextRenewalDate","entityExpirationReason","leiRegistrationStatus","successorLei","louId","leiValidationSource"]
        key_list2=["leiCodeRelation","legalEntityName","relationshipType","percentShareholding","accountingStandard","validationReference","startDateOfRelationship","endDateOfRelationship","startDateAccountingPeriod","endDateOfAccountingPeriod","startDateDocFilingPeriod","endDateDocFilingPeriod","registrationStatus","initialRegistrationDate","relationshipStatus","lastUpdateDate","nextRenewalDate","managingLou","periodType","validationSources","relationshipQuantifiers","relationshipQualifiersCategory"]
        print(len(key_list1))
        print(len(key_list2))

        dict1={}
        dict2={}
        dict_to_send={}
        final_dict_to_send={}
        all_tables=self.browser.find_elements_by_tag_name("table")
        data=[]
        print("no of tables om the page ",len(all_tables))
        if len(all_tables) > 0 :

            for j,v in enumerate(all_tables):
                if j != 3:
                    input_elements=v.find_elements_by_tag_name("input")
                    for x , y in enumerate(input_elements):
                        data.append(y.get_attribute('value'))

            print(data)
            print("data",len(data))

            for i,v in enumerate(key_list1):
                dict1[v]=data[i]



        
        time.sleep(2)
        self.browser.find_element_by_id("ctl00_ContentPlaceHolder1_btnlinkRelationshipData").click()
        time.sleep(3)
        

        relationship_records_table=self.browser.find_elements_by_xpath('.//table[@style = "height: 435px; width: 954px"]')
        #relationship_records_table=self.browser.find_elements_by_tag_name("table")
        print("relationship record details",len(relationship_records_table))
        relationship_records_data=[]

        checkbox_table=self.browser.find_element_by_xpath('.//table[@id = "ctl00_ContentPlaceHolder1_chklstRRValDocs"]')

        checkbox_table_input_elements=checkbox_table.find_elements_by_tag_name("label")
        checkbox_values=[]
        if len(checkbox_table_input_elements)>0:
            for x , y in enumerate(checkbox_table_input_elements):
                checkbox_values.append(y.text)
            
        
        if len(relationship_records_table) > 0 :
    
            input_elements=relationship_records_table[0].find_elements_by_tag_name("input")
            for x , y in enumerate(input_elements):

                if x>=6 and x<=10:
                    continue
                else:
                    relationship_records_data.append(y.get_attribute('value'))

            print(relationship_records_data)
            print("relationship_data",len(relationship_records_data))
            for i,v in enumerate(key_list2):
                dict2[v]=relationship_records_data[i]

            dict2["validationDocuments"]=checkbox_values

        dict_to_send.update(dict1)
        dict_to_send.update(dict2)
        final_dict_to_send["data"]=dict_to_send
        print(final_dict_to_send)