from selenium import webdriver
from selenium.webdriver.common.keys import Keys
import urllib.request

import time
from selenium.common.exceptions import NoSuchElementException,UnexpectedAlertPresentException

import pandas as pd
import os,io

from selenium.webdriver.support import expected_conditions as EC



class Icmai:
    
    def __init__(self,member_number):

        options = webdriver.ChromeOptions()
        options.add_experimental_option("excludeSwitches", ['enable-automation'])
        options.add_argument("--incognito")
        options.add_argument("--start-maximized")
        options.add_argument("--disable-infobars")
        options.add_argument("--disable-extension")
        self.browser = webdriver.Chrome(executable_path="/home/ril-lt-naval/Desktop/classesofscrappers/chromedriver",options=options)
        self.member_number=member_number
        



    def icmai(self):
        
        self.browser.get("https://icmai.in/icmai/Technical_Cell/Members.php")
        time.sleep(2)
        self.browser.find_element_by_xpath('.//a[@href = "https://eicmai.in/External/Home.aspx"]').click()
        time.sleep(3)

        self.browser.switch_to_window(self.browser.window_handles[-1])
        time.sleep(2)
        elements=self.browser.find_elements_by_xpath('.//a[@href = "#"]')
        print(len(elements))
        elements[3].click()
        time.sleep(2)
        self.browser.find_element_by_xpath('.//a[@href = "/external/Masters/COP/CopListView.aspx"]').click()
        time.sleep(2)
        member_number_element=self.browser.find_element_by_xpath('.//input[@id = "ContentPlaceHolder1_TextBox_Value"]')
        member_number_element.send_keys(self.member_number)
        time.sleep(1)
        self.browser.find_element_by_xpath('.//input[@id = "ContentPlaceHolder1_ButtonSearch"]').click()


        # input_element.send_keys(self.membership_number)
        # time.sleep(2)
        # self.browser.find_element_by_xpath('.//input[@type = "Submit"]').click()
        # time.sleep(2)


        # final_dict_to_send={}

        # form=self.browser.find_element_by_xpath('.//form[@name = "frm"]')
        
        # all_tables=form.find_elements_by_tag_name("table")
        # data=[]
        # if len(all_tables) > 1:
            
        #     output_data_table=all_tables[1]
        #     for j,v in enumerate(output_data_table.find_elements_by_xpath('.//td[@width = "47%"]')):
        #         if v.text != '':
        #             data.append(v.text)
            
        #     for j,v in enumerate(output_data_table.find_elements_by_xpath('.//td[@width = "34%"]')):
        #         if v.text != '':
        #             data.append(v.text)
    
        #     print(len(data))
        #     print(data)

        #     membership_number=self.membership_number
        #     name=data.pop(0)
        #     gender=data.pop(0)
        #     qualification=data.pop(0)
        #     address_foreign_section=data.pop(1)
        #     fellow_year=data.pop(-1)
        #     associate_year=data.pop(-1)
        #     cop_status=data.pop(-1)
        #     address="".join(data)
        #     address=address.replace("    ","")
            
        #     dict_to_send={}
        #     dict_to_send['name']=name
        #     dict_to_send['gender']=gender
        #     dict_to_send['membershipNumber']=membership_number
        #     dict_to_send['qualification']=qualification
        #     dict_to_send['foreignSectionAddress']=address_foreign_section
        #     dict_to_send['address']=address
        #     dict_to_send['associateYear']=associate_year
        #     dict_to_send['copStatus']=cop_status
        #     dict_to_send['fellowYear']=fellow_year
        #     dict_to_send['foreignSectionRegionIndia']=""

        #     final_dict_to_send["data"]=dict_to_send
        #     return final_dict_to_send

        # else:
        #     final_dict_to_send["data"]=""
        #     return final_dict_to_send

    