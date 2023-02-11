from selenium import webdriver
from selenium.webdriver.common.keys import Keys
import urllib.request
from PIL import Image
import boto3
from botocore.exceptions import ClientError
import time
import sys
from selenium.common.exceptions import NoSuchElementException
import uuid
import pandas as pd
import os,io
from google.cloud import vision

from google.cloud.vision import types
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from modules.db import DB
from modules.utils import GcpOcr
import json
class ItrAcknowledgementVerification:

    def __init__(self,pan,acknowledgementNumber,refid,env= "prod"):

        os.environ[
            "GOOGLE_APPLICATION_CREDENTIALS"] = "vision_api_token.json"

        self.client = vision.ImageAnnotatorClient()
        credential_path = r"vision_api_token.json"
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = credential_path
        self.timeBwPage = 0.5

        assert env == "quality" or env == "prod", ("env value should be either quality or prod")
        self.env = env
        self.screenshotDir = os.path.join(os.getcwd(), "Screenshots")
        self.ocr = GcpOcr("gcp.json")
        self.readConfig()
        self.CreateS3()
        self.dbObj = DB(**self.dbConfig)
        self.refid = refid
        chrome_options = Options()
        chrome_options.add_experimental_option("excludeSwitches", ['enable-automation'])
        chrome_options.add_argument("--disable-dev-shm-usage")  # overcome limited resource problems
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--start-maximized")
        chrome_options.headless = True

        chrome_options.add_argument("--disable-extension")
        chrome_options.add_argument("no-sandbox")

        self.browser = webdriver.Chrome("/usr/local/bin/chromedriver", options=chrome_options)
        self.FILE_NAME="captcha.png"
        self.FOLDER_PATH=os.getcwd()
        self.pan=pan
        self.acknowledgementNumber=acknowledgementNumber
        # self.generate_response()

    def readConfig(self):
        configFileName = f"config_{self.env}.json"
        with open(configFileName, 'r') as confFile:
            config = json.load(confFile)
            self.driverConfig = config['driverConfig']
            self.dbConfig = config['dbConfig']

    def makeDirIfNot(self, dirpath):

        try:
            os.makedirs(dirpath)

        except FileExistsError:
            pass

    def makeDriverDirs(self):
        self.makeDirIfNot(self.screenshotDir)

    def CreateS3(self):

        try:
            self.session = boto3.session.Session(aws_access_key_id=self.driverConfig['s3']['AWS_ACCESS_KEY_ID'],
                                                 aws_secret_access_key=self.driverConfig['s3']['AWS_SECRET_ACCESS_KEY'],
                                                 region_name=self.driverConfig['s3']['REGION_HOST'])

            self.resource = self.session.resource("s3")
            self.bucket = self.resource.Bucket(self.driverConfig["s3"]["AWS_STORAGE_BUCKET_NAME"])

        except ClientError as e:
            self.logStatus("critical", f"could not connect to s3 {e}")
            raise Exception("couldn't connect to s3")

        except Exception as e:
            self.logStatus("critical", f"could not connect to s3 {e}")
            raise Exception("couldn't connect to s3")

    def uploadToS3(self, filename, key):
        self.bucket.upload_file(
            Filename=filename, Key=key)

    def takeScreenshot(self):

        time.sleep(self.timeBwPage)

        sname = str(uuid.uuid1()) + '.png'
        screenshotName = os.path.join(self.screenshotDir, f"{sname}")
        self.browser.save_screenshot(screenshotName)
        self.uploadToS3(os.path.join(screenshotName), 'screenshots/' + self.refid + "/" + sname)
        return sname

    def logStatus(self, level, message, screenshot=None):

        if self.dbObj is not None:
            from datetime import datetime, timedelta
            nine_hours_from_now = datetime.now() + timedelta(hours=5.5)
            self.dbObj.insertLog(self.refid, '{:%Y-%m-%d %H:%M:%S}'.format(nine_hours_from_now), level, message,
                                 'ITR', self.env, screenshot)
        print(f"{level}: {message}, screenshot: {screenshot}")


        
    def itr_acknowledgement_scrapper(self,pan,acknowledgement_number):

        try:
            self.browser.get("https://www1.incometaxindiaefiling.gov.in/e-FilingGS/Services/ITRStatusLink.html")
            self.logStatus("info", "opening browser page")
        except:
            self.logStatus("info", "contact support")
            message = "Information Source is Not Working"
            code = "EIS042"

            dic = {"data": 'null', "responseCode": code, "responseMessage": message}
            return dic
            sys.exit()


        pan_number_element=self.browser.find_element_by_id("ITR-Status_itrvStatusDetails_pan")
        
        time.sleep(1)
        pan_number_element.send_keys(pan)

        acknowledgement_number_input=self.browser.find_element_by_id("ITR-Status_itrvStatusDetails_acknowledgementNumber")
        time.sleep(1)
        acknowledgement_number_input.send_keys(acknowledgement_number)


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
            #print("%%%%%%%%%",captcha_text)
            data=str(captcha_text["description"][0])
            #print("@@@@@@",data)
            info="".join(data.split())
            # print("&&&&&&&&&",info)
            # info=info + 'extra'

            #print("#############################",info)
            # captcha_text=df['description'][0]
            ip_element=self.browser.find_element_by_id("ITR-Status_captchaCode")
            ip_element.send_keys(info)
            time.sleep(1)

        time.sleep(2)

        self.browser.find_element_by_id("submitbtn").click()

        time.sleep(3)

        elements=self.browser.find_elements_by_tag_name("th")
        if len(elements)>0:
            success_message=elements[0].text
            #print(success_message)
            return success_message
        else:
            error_elements=self.browser.find_elements_by_xpath('.//div[@class = "error"]')
            #print(len(error_elements))
            error_message=error_elements[0].text
            return error_message
    



    def check(self):
        a=self.itr_acknowledgement_scrapper(self.pan,self.acknowledgementNumber)

        while a == "Invalid Code. Please enter the code as appearing in the Image.":
            a=self.itr_acknowledgement_scrapper(self.pan,self.acknowledgementNumber)
        time.sleep(2)
        return a


    def generate_response(self):

        check_to_enter_into_db=self.check()
        #print(check_to_enter_into_db)
        if check_to_enter_into_db == 'Invalid PAN. Please retry .':
            message = "No Information Found."
            code = "ENI004"
            self.makeDriverDirs()
            self.logStatus("info", "No info found", self.takeScreenshot())
        elif check_to_enter_into_db == 'Please enter a valid Acknowledgement Number.':
            message = "No Information Found."
            code = "ENI004"
            self.makeDriverDirs()
            self.logStatus("info", "No info found", self.takeScreenshot())
        elif check_to_enter_into_db == 'No record found':
            message = "No Information Found."
            code = "ENI004"
            self.makeDriverDirs()
            self.logStatus("info", "No info found", self.takeScreenshot())


        else:
            message = "Successfully Completed."
            code = "SRC001"
            self.makeDriverDirs()
            self.logStatus("info", "successfully scrapped information", self.takeScreenshot())
        dict_to_send = {}
        dict_to_send["itrStatus"] = check_to_enter_into_db
        dict_to_send["pan"] = self.pan
        dict_to_send["acknowledgementNumber"] = self.acknowledgementNumber
        #dict_to_send={"itrStatus":check_to_enter_into_db,"pan":self.pan,"acknowledgementNumber":self.acknowledgementNumber}
        dic = {"data": dict_to_send, "responseCode": code, "responseMessage": message}

        return dic

    def ITR_response(self):

        dic = {}

        try:
            self.logStatus("info", "opening browser page")
            dic = self.generate_response()

        except Exception as e:

            self.logStatus("critical", "Captcha error retrying")
            try:
                self.logStatus("info", "opening browser page")
                dic = self.generate_response()

            except Exception as e:

                self.logStatus("critical", "Captcha error retrying")
                try:
                    self.logStatus("info", "opening browser page")
                    dic = self.generate_response()

                except Exception as e:

                    message = "No Information Found."
                    code = "ENI004"
                    self.logStatus("info", "No Info Found")
                    dic = {"data": "null", "responseCode": code, "responseMessage": message}

        return dic

