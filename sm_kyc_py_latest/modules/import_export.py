from selenium import webdriver
from selenium.webdriver.common.keys import Keys
import urllib.request

import time
from selenium.common.exceptions import NoSuchElementException,UnexpectedAlertPresentException

import pandas as pd
import os,io

from selenium.webdriver.support import expected_conditions as EC



class ImportExport:
    
    def __init__(self,iec,name):

        options = webdriver.ChromeOptions()
        options.add_experimental_option("excludeSwitches", ['enable-automation'])
        options.add_argument("--incognito")
        options.add_argument("--start-maximized")
        options.add_argument("--disable-infobars")
        options.add_argument("--disable-extension")
        self.browser = webdriver.Chrome(executable_path="/home/ril-lt-naval/Desktop/classesofscrappers/chromedriver",options=options)
        self.iec=iec
        self.name=name




    def import_export(self):
        
        self.browser.get("http://164.100.128.144:8100/dgft/IecPrint ")
        time.sleep(2)
        input_elements=self.browser.find_elements_by_xpath('.//input[@type = "TEXT"]')
        time.sleep(1)
        input_elements[0].send_keys(self.iec)
        time.sleep(1)
        input_elements[1].send_keys(self.name)
        time.sleep(1)
        self.browser.find_element_by_xpath('.//input[@type = "SUBMIT"]').click()
        time.sleep(2)

        final_dict_to_send={}

        all_tables=self.browser.find_elements_by_tag_name("table")
        if len(all_tables) > 0:
            data=[]
            for i in all_tables:
                for j,v in enumerate(i.find_elements_by_xpath('.//td')):
                    if v.text != ":":
                        data.append(v.text)
            print(len(data))
            #print(data)
            dict_to_send={}
            j=0
            w=1
            
            for i ,v in enumerate(data):
                if i < (len(data)/2):
                    dict_to_send[data[j]]=data[w]
                    j+=2
                    w+=2
                    
            #print(dict_to_send)
            final_dict={}
            final_dict['iec']=dict_to_send['IEC']
            final_dict['iecAllotmentDate']=dict_to_send['IEC Allotment Date']
            final_dict['fileNumber']=dict_to_send['File Number']
            final_dict['fileDate']=dict_to_send['File Date']
            final_dict['partyNameAndAddress']=dict_to_send['Party Name and Address']
            final_dict['phoneNumber']=dict_to_send['Phone No']
            final_dict['email']=dict_to_send['e_mail']
            final_dict['exporterType']=dict_to_send['Exporter Type']
            final_dict['iecStatus']=dict_to_send['IEC Status']
            final_dict['dateOfEstablishment']=dict_to_send['Date of Establishment']
            final_dict['bin(PAN+Extension)']=dict_to_send['BIN (PAN+Extension)']
            final_dict['panIssueDate']=dict_to_send['PAN ISSUE DATE']
            final_dict['panIssuedBy']=dict_to_send['PAN ISSUED BY']
            final_dict['natureOfConcern']=dict_to_send['Nature Of Concern']
            final_dict['bankerDetail']=dict_to_send['Banker Detail']
            other_data=[]
            for i , v in enumerate(data):
                if v == '1.':
                    other_data=data[i:]
                    break
            #print(other_data)
            check=other_data[0]
            last_data=[]
            for i, v in enumerate(other_data):
                if i > 0 and v == check:
                    last_data=other_data[i:]
                    other_data=other_data[:i]
                    break
            #print(last_data)   
            #print(other_data)

            directors=[] 
            a=0
            b=1
            for i ,v in enumerate(other_data):
                temp={}
                if i < len(other_data)/2:
                    temp[other_data[a]]=other_data[b]
                    directors.append(temp)
                    a+=2
                    b+=2
            
            final_dict['directors']=directors
            #print(directors)
            data_branches=[]
            for j,v in enumerate(all_tables[2].find_elements_by_xpath('.//td')):
                    if v.text != ":":
                        data_branches.append(v.text)
            
        

            branches=[]
            c=0
            d=1
            for i , v in enumerate(data_branches):
                temp={}
                if i<len(data_branches)/2:
                    temp[data_branches[c]]=data_branches[d]
                    branches.append(temp)
            final_dict['branches']=branches
    #==++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

            registration_details=[]
            for j,v in enumerate(all_tables[3].find_elements_by_xpath('.//td')):
                    if v.text != ":":
                        registration_details.append(v.text)
            
        # print(registration_details)

            r_details=[]
            e=0
            f=1
            for i , v in enumerate(registration_details):
                temp={}
                if i<len(registration_details)/2:
                    temp[registration_details[e]]=registration_details[f]
                    r_details.append(temp)
            final_dict['registrationDetails']=r_details
    #+++++++++++++++++++++++++++++++++++++===========+++++++++++++++++++++++++++++++

            rcmc_details=[]
            for j,v in enumerate(all_tables[4].find_elements_by_xpath('.//td')):
                    if v.text != ":":
                        rcmc_details.append(v.text)
            
            #print(rcmc_details)

            cmc_details=[]
            g=0
            h=1
            for i , v in enumerate(rcmc_details):
                temp={}
                if i<len(rcmc_details)/2:
                    temp[rcmc_details[g]]=rcmc_details[h]
                    cmc_details.append(temp)

            final_dict['rcmcDetails']=cmc_details

            final_dict_to_send['data']=final_dict
            return final_dict_to_send
        else:
            final_dict_to_send['data']=""
            return final_dict_to_send