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



class IcsiVerification:
    
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





    def icsi_scrapper(self,member_type,member_number):
        print(member_number)
        print(member_type)

        self.browser.get('https://www.icsi.in/student/Members/MemberSearch.aspx?SkinSrc=%5BG%5DSkins/IcsiTheme/IcsiIn-Bare&ContainerSrc=%5BG%5DContainers/IcsiTheme/NoContainer')

        if member_type == 'ACS':
            status='A'
        elif member_type == 'FCS':
            status='F'
        else:
            status=""    
        time.sleep(1)
        self.browser.find_element_by_xpath(f"//option[@value='{status}']").click()
        time.sleep(1)
        membership_number_element=self.browser.find_element_by_id("dnn_ctr410_MemberSearch_txtMembershipNumber")
        
        time.sleep(1)
        membership_number_element.send_keys(member_number)
        time.sleep(1)

        self.browser.find_element_by_id("dnn_ctr410_MemberSearch_btnSearch").click()

        time.sleep(4)

        

        total_number_of_elements=self.browser.find_element_by_id("dnn_ctr410_MemberSearch_lblSearchResults_lblNoHelpLabel").text

        total_number_of_elements_list=total_number_of_elements.split(": ")
        number=int(total_number_of_elements_list[1])
        time.sleep(1)
        dict_to_send={}
        dict_final={}
        if number >0:

            name=self.browser.find_element_by_id("dnn_ctr410_MemberSearch_grdMembers_ctl00_ctl04_lblFullName").text
            organisation=self.browser.find_element_by_id("dnn_ctr410_MemberSearch_grdMembers_ctl00_ctl04_lblOrganizationName").text
            designation=self.browser.find_element_by_id("dnn_ctr410_MemberSearch_grdMembers_ctl00_ctl04_lblDesignation").text
            membershipNumber=self.browser.find_element_by_id("dnn_ctr410_MemberSearch_grdMembers_ctl00_ctl04_lblMembershipNumber").text
            cpNumber=self.browser.find_element_by_id("dnn_ctr410_MemberSearch_grdMembers_ctl00_ctl04_lblCpNumber").text
            benevolentNumber=self.browser.find_element_by_id("dnn_ctr410_MemberSearch_grdMembers_ctl00_ctl04_lblBenov").text
            address=self.browser.find_element_by_id("dnn_ctr410_MemberSearch_grdMembers_ctl00_ctl04_lblAddress").text
            city=self.browser.find_element_by_id("dnn_ctr410_MemberSearch_grdMembers_ctl00_ctl04_lblCity").text
            phone=self.browser.find_element_by_id("dnn_ctr410_MemberSearch_grdMembers_ctl00_ctl04_lblOfficePhone").text
            email=self.browser.find_element_by_id("dnn_ctr410_MemberSearch_grdMembers_ctl00_ctl04_lblEmail").text
            mobile=self.browser.find_element_by_id("dnn_ctr410_MemberSearch_grdMembers_ctl00_ctl04_lblMobileNumber").text
        
            
            dict_to_send["name"]=name
            dict_to_send["organisation"]=organisation
            dict_to_send["designation"]=designation
            dict_to_send["membershipNumber"]=membershipNumber
            dict_to_send["cpNumber"]=cpNumber
            dict_to_send["benevolentNumber"]=benevolentNumber
            dict_to_send["address"]=address
            dict_to_send["city"]=city
            dict_to_send["phone"]=phone
            dict_to_send["email"]=email
            dict_to_send["mobile"]=mobile

            dict_final['data']=dict_to_send
            return dict_final 
        
        else:
            dict_final['data']=""
            return dict_final 



