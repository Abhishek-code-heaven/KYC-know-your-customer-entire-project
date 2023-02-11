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



class MciVerification:
    
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





    def mci_scrapper(self):
        

        self.browser.get('https://www.mciindia.org/CMS/information-desk/indian-medical-register')

           
        # time.sleep(1)
        # registration_number_element=self.browser.find_element_by_id("doctorRegdNo")
        # time.sleep(1)

        # registration_number_element.send_keys(registration_number)
        # time.sleep(1)

        # enter_year_search_box=self.browser.find_element_by_xpath('.//input[@class = "form-control multiselect-search"]')
        # enter_year_search_box.send_keys(registration_year)


