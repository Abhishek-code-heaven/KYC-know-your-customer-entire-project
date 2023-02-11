import io
import os
import time
import sys
import pandas as pd
import boto3
import pprint
import uuid
from botocore.exceptions import ClientError
from google.cloud import vision
from selenium import webdriver
from modules.db import DB
from modules.utils import GcpOcr
import json
#from webdriver_manager.chrome import ChromeDriverManager


class AadharVerification:

    def __init__(self, aadhaarnumber,env,refid):

        os.environ[
            "GOOGLE_APPLICATION_CREDENTIALS"] = "vision_api_token.json"

        self.client = vision.ImageAnnotatorClient()
        options = webdriver.ChromeOptions()
        self.timeBwPage = 0.5
        options.headless = True
        self.FILE_NAME = "captcha.png"
        self.FOLDER_PATH = os.getcwd()
        self.aadhaarnumber = aadhaarnumber
        assert env == "quality" or env == "prod", ("env value should be either quality or prod")
        self.env = env
        self.screenshotDir = os.path.join(os.getcwd(), "Screenshots")
        self.ocr = GcpOcr("gcp.json")
        self.readConfig()
        self.CreateS3()
        self.dbObj = DB(**self.dbConfig)
        self.refid = refid

       # options.binary_location = "/usr/bin/google-chrome"  # chrome binary location specified here
        options.add_argument("--start-maximized")  # open Browser in maximized mode
        options.add_argument("--no-sandbox")  # bypass OS security model
        options.add_argument("--disable-dev-shm-usage")  # overcome limited resource problems
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        self.browser = webdriver.Chrome(options=options, executable_path= "/usr/local/bin/chromedriver")

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
                                 'Aadhaar_Verification', self.env, screenshot)
        print(f"{level}: {message}, screenshot: {screenshot}")

    def get_captchaimage_text(self):
        print("in function")
        aadhaarnumber = self.aadhaarnumber
        try :
            self.browser.get("https://resident.uidai.gov.in/verify")
            self.logStatus("info", "Driver created")
            self.makeDriverDirs()
            self.logStatus("info", "Aadhar verification page opened", self.takeScreenshot())

        except:
            self.makeDriverDirs()
            self.logStatus("info", "Site down contact support")
            dic = 'null'
            message = "Unable To Process. Please Reach Out To Support."
            code = "EUP007"
            dict_to_send = {"data": dic, "responseCode": code, "responseMessage": message}
            #dict_to_send = json.dumps(dict_to_send)
            return dict_to_send
            sys.exit()


        ip_element = self.browser.find_element_by_id("uidno")
        time.sleep(1)
        ip_element.send_keys(aadhaarnumber)

        time.sleep(2)
        self.browser.find_element_by_id("captcha-img").screenshot("captcha.png")

        with io.open(os.path.join(self.FOLDER_PATH, self.FILE_NAME), 'rb') as image_file:
            content = image_file.read()

        image = vision.types.Image(content=content)
        response = self.client.text_detection(image=image)
        texts = response.text_annotations

        df = pd.DataFrame(columns=['locale', 'description'])

        for text in texts:
            df = df.append(dict(
                locale=text.locale,
                description=text.description
            ),
                ignore_index=True
            )
        #print(df)
        if not df.empty:

            captcha_text = df.iloc[[0], [1]]
            data = str(captcha_text["description"][0])
            info = "".join(data.split())

            info = info + 'extra'
            try:
                sname = str(info) + '.png'
                screenshotName = os.path.join(self.screenshotDir, f"{sname}")
                self.browser.find_element_by_id("captcha-img").screenshot(screenshotName)
                self.uploadToS3(os.path.join(screenshotName), 'AadharVerifier/' + sname)
            except:
                pass
            #print("#############################", info)
            # captcha_text=df['description'][0]
            ip_element = self.browser.find_element_by_id("security_code")
            ip_element.send_keys(info)
            time.sleep(1)

            a = self.browser.find_elements_by_xpath('.//div[@class = "errormsgClass"]')
            # print("first",a[0].text)
            # print("second",a[1].text)
            # print(len(a))
            if a[0].text != "Please enter a valid Aadhaar number":
                self.browser.find_element_by_id("submitButton").click()
                return "Aadhaar number entered is correct !"
            else:
                return "The Aadhaar number entered is incorrect !"
            df.drop(columns=['locale', 'description'])
        else:
            return "the vision api could not read the text at all ."

    def generate_response(self):

        values_to_send = []
        response_from_function_call = self.get_captchaimage_text()
        #print(response_from_function_call)
        values_to_send.append(response_from_function_call)

        error_elements = self.browser.find_elements_by_xpath('.//div[@class = "alert-message"]')
        #print(len(error_elements))

        if response_from_function_call == "Aadhaar number entered is correct !":
            if len(error_elements) > 0:
                while error_elements[0].text == "Please Enter Valid Captcha":
                    response_from_function_call = self.get_captchaimage_text()
                    time.sleep(1)
                    error_elements = self.browser.find_elements_by_xpath('.//div[@class = "alert-message"]')
                    if len(error_elements) == 0:
                        break

            time.sleep(1)
            list_of_elements = self.browser.find_elements_by_xpath('.//span[@class = "d-block mb-5"]')
            for i in list_of_elements:
                temp = i.text
                temp_list = temp.split(":")
                values_to_send.append(temp_list[1])

        #print("^^^^^^^^^^^^^^^^^^^^^", values_to_send)
        dic = {}
        if len(values_to_send) > 1:
            message = "Successfully Completed."
            code = "SRC001"
            dic["ageBand"] = values_to_send[1]
            dic["gender"] = values_to_send[2]
            dic["state"] = values_to_send[3]
            dic["mobileNumber"] = values_to_send[4]
            dic["aadhaarNumber"] = self.aadhaarnumber
            dict_to_send = {"data": dic, "responseCode": code, "responseMessage": message}
            self.makeDriverDirs()
            self.logStatus("info", "successfully scrapped information", self.takeScreenshot())
            # dict_to_send = json.dumps(dict_to_send)
            return dict_to_send

        else:
            dict_to_send = {}
            message = "No Information Found."
            code = "ENI004"
            dict_to_send = {"data": "null", "responseCode": code, "responseMessage": message}
            self.makeDriverDirs()
            self.logStatus("info", "No information found", self.takeScreenshot())
            # dict_to_send = json.dumps(dict_to_send)
            return dict_to_send



    def exceptionhandling(self):

        dict_to_send = {}
        try:
            self.logStatus("info", "Opening webpage")
            dict_to_send = self.generate_response()
        except Exception as e:

            self.logStatus("critical", "Captcha error")
            try:
                self.logStatus("info", "Opening webpage")
                dict_to_send = self.generate_response()
            except Exception as e:

                self.logStatus("critical", "Captcha error")
                try:
                    self.logStatus("info", "Opening webpage")
                    dict_to_send = self.generate_response()
                except Exception as e:

                    self.logStatus("critical", "no data found")
                    dict_to_send = {}
                    message = 'No Information Found.'
                    code = 'ENI004'
                    dic1 = 'null'

                    dict_to_send = {'data': dic1, 'responseCode': code, 'responseMessage': message}
                    self.logStatus("info", "No Info Found")

        return dict_to_send

#if __name__ == '__main__':

    # v = AadharVerification(aadhaarnumber = '485721229999', refid="testing2", env = 'prod')
   #  data = v.exceptionhandling()
    # print(data)
    #result_java_queue.update(data)
#def lambda_landler(event, context):

    #my_class = AadharVerification(event['DL'], event[''])
    #result = my_class.generate_response()

    #print(result)
    #return result


#lambda_landler({'DL': '485721221633'}, '')
