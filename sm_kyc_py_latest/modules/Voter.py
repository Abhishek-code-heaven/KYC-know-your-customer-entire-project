import json
import os
import time
import uuid
from pprint import pprint

import boto3
from botocore.exceptions import ClientError
from google.cloud import vision

from modules.db import DB
from modules.utils import GcpOcr


class CouldNotCreateDriver(Exception):
    pass

class Electoralsearch:

    def __init__(self,refid,env = "prod"):

        credential_path = r"vision_api_token.json"
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = credential_path
        self.timeBwPage = 0.5
        self.client = vision.ImageAnnotatorClient()
        assert env == "quality" or env == "prod", ("env value should be either quality or prod")
        self.env = env
        self.screenshotDir = os.path.join(os.getcwd(), "Screenshots")
        self.ocr = GcpOcr("gcp.json")
        self.readConfig()
        self.CreateS3()
        self.dbObj = DB(**self.dbConfig)
        self.refid = refid
        self.FILE_NAME = "captcha.png"
        self.FOLDER_PATH = os.getcwd()



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
        self.driver.save_screenshot(screenshotName)
        self.uploadToS3(os.path.join(screenshotName), 'screenshots/' + self.refid + "/" + sname)
        return sname

    def logStatus(self, level, message, screenshot=None):

        if self.dbObj is not None:
            from datetime import datetime, timedelta
            nine_hours_from_now = datetime.now() + timedelta(hours=5.5)
            self.dbObj.insertLog(self.refid, '{:%Y-%m-%d %H:%M:%S}'.format(nine_hours_from_now), level, message,
                                 'Votereletoral', self.env, screenshot)
        print(f"{level}: {message}, screenshot: {screenshot}")

    def generate_electoralsearch(self,epicNumber):
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        import io
        import os
        import time
        from google.cloud import vision
      #  from webdriver_manager.chrome import ChromeDriverManager
        chrome_options = Options()
        chrome_options.add_experimental_option("excludeSwitches", ['enable-automation'])
        chrome_options.add_argument("--disable-dev-shm-usage")  # overcome limited resource problems
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--start-maximized")
        chrome_options.headless = True
        self.makeDriverDirs()

        chrome_options.add_argument("--disable-extension")
        chrome_options.add_argument("no-sandbox")

        self.driver = webdriver.Chrome("/usr/local/bin/chromedriver",options=chrome_options)

        self.logStatus("info", "Driver created")
        try:
            self.driver.get("https://electoralsearch.in/")
            r = 1
            self.logStatus("info", "electoralsearch page opened", self.takeScreenshot())

        except Exception as e:
            self.logStatus("critical", "ESIF page could not open contact support")
            r = 2

        if r == 1:
            self.driver.find_element_by_xpath("""//*[@id="continue"]""").click()
            self.driver.find_element_by_xpath("""//*[@id="mainContent"]/div[2]/div/div/ul/li[2]""").click()
            self.driver.find_element_by_xpath("""//*[@id="name"]""").click()
            self.driver.find_element_by_xpath("""//*[@id="name"]""").send_keys(epicNumber)
            self.driver.find_element_by_xpath("""//*[@id="captchaEpicImg"]""").screenshot('captcha.png')
            with io.open(os.path.join(self.FOLDER_PATH, self.FILE_NAME), 'rb') as image_file:
                content = image_file.read()

            image = vision.types.Image(content=content)
            response = self.client.text_detection(image=image)
            texts = response.text_annotations

            for text in texts:
                z = ('"{}"'.format(text.description))
            h = str(z).split('"')
            k = h[1]
            print(k)
            try:
                sname = str(k) + '.png'
                screenshotName = os.path.join(self.screenshotDir, f"{sname}")
                self.driver.find_element_by_xpath("""//*[@id="captchaEpicImg"]""").screenshot(screenshotName)
                self.uploadToS3(os.path.join(screenshotName),'voter/'+ sname)
            except:
                pass
            print(k)
            self.driver.find_element_by_xpath("""//*[@id="txtEpicCaptcha"]""").click()
            self.driver.find_element_by_xpath("""//*[@id="txtEpicCaptcha"]""").send_keys(k)
            self.logStatus("info", "enter k", self.takeScreenshot())
            window_before = self.driver.window_handles[0]
            window_before_title = self.driver.title
            self.driver.find_element_by_xpath("""//*[@id="btnEpicSubmit"]""").click()
            time.sleep(5)
            age = self.driver.find_element_by_xpath("""//*[@id="resultsTable"]/tbody/tr/td[4]""")
            age = age.text
            print(age)
            district = self.driver.find_element_by_xpath("""//*[@id="resultsTable"]/tbody/tr/td[7]""")
            district = district.text
            window_before = self.driver.window_handles[0]
            window_before_title = self.driver.title
            self.driver.find_element_by_xpath("""/html/body/div[5]/div[3]/div[2]/div/table/tbody/tr/td[1]/form/input[23]""").click()
            time.sleep(3)
            window_after = self.driver.window_handles[1]
            self.driver.switch_to.window(window_after)
            state = self.driver.find_element_by_xpath("""//*[@id="ng-app"]/body/div[4]/div/div[1]/form/table/tbody/tr[2]/td[2]""")
            state = state.text
            assemblyConstituency = self.driver.find_element_by_xpath("""//*[@id="ng-app"]/body/div[4]/div/div[1]/form/table/tbody/tr[3]/td[2]""")
            assemblyConstituency = assemblyConstituency.text
            parliamentaryConstituency = self.driver.find_element_by_xpath("""//*[@id="ng-app"]/body/div[4]/div/div[1]/form/table/tbody/tr[4]/td[2]""")
            parliamentaryConstituency = parliamentaryConstituency.text
            name = self.driver.find_element_by_xpath("""//*[@id="ng-app"]/body/div[4]/div/div[1]/form/table/tbody/tr[6]/td""")
            name = name.text
            gender = self.driver.find_element_by_xpath("""//*[@id="ng-app"]/body/div[4]/div/div[1]/form/table/tbody/tr[7]/td[2]""")
            gender = gender.text
            epicNumber = self.driver.find_element_by_xpath("""//*[@id="ng-app"]/body/div[4]/div/div[1]/form/table/tbody/tr[8]/td[2]""")
            epicNumber = epicNumber.text
            fatherHusbandName = self.driver.find_element_by_xpath("""//*[@id="ng-app"]/body/div[4]/div/div[1]/form/table/tbody/tr[10]/td""")
            fatherHusbandName = fatherHusbandName.text
            partNumber = self.driver.find_element_by_xpath("""//*[@id="ng-app"]/body/div[4]/div/div[1]/form/table/tbody/tr[11]/td[2]""")
            partNumber = partNumber.text
            partName = self.driver.find_element_by_xpath("""//*[@id="ng-app"]/body/div[4]/div/div[1]/form/table/tbody/tr[12]/td[2]""")
            partName = partName.text
            serialNumber = self.driver.find_element_by_xpath("""//*[@id="ng-app"]/body/div[4]/div/div[1]/form/table/tbody/tr[13]/td[2]""")
            serialNumber = serialNumber.text
            pollingStation = self.driver.find_element_by_xpath("""//*[@id="ng-app"]/body/div[4]/div/div[1]/form/table/tbody/tr[14]/td[2]/a""")
            pollingStation = pollingStation.text
            pollingDate = self.driver.find_element_by_xpath("""//*[@id="ng-app"]/body/div[4]/div/div[1]/form/table/tbody/tr[15]/td[2]""")
            pollingDate = pollingDate.text
            #from datetime import datetime
            #date_obj = datetime.strptime(pollingDate, '%d/%m/%Y')
            #pollingDate = date_obj.strftime('%d-%b-%Y')
            lastUpdatedOn = self.driver.find_element_by_xpath("""//*[@id="ng-app"]/body/div[4]/div/div[1]/form/table/tbody/tr[16]/td[2]""")
            lastUpdatedOn = lastUpdatedOn.text
            from datetime import datetime
            date_obj = datetime.strptime(lastUpdatedOn, '%d/ %m/ %Y')
            lastUpdatedOn = date_obj.strftime('%d-%b-%Y')

            message = "Successfully Completed."
            code = "SRC001"
            dic = {}
            dic["assemblyConstituency"] = assemblyConstituency
            dic["epicNumber"] = epicNumber
            dic["fatherHusbandName"] = fatherHusbandName
            dic["gender"] = gender
            dic["lastUpdatedOn"] = lastUpdatedOn
            dic["name"] = name
            dic["parliamentaryConstituency"] = parliamentaryConstituency
            dic["partName"] = partName
            dic["partNumber"] = partNumber
            dic["pollingDate"] = pollingDate
            dic["pollingStation"] = pollingStation
            dic["serialNumber"] = serialNumber
            dic["state"] = state
            dic["age"] = age
            dic["district"] = district
            dic = {"data": dic, "responseCode": code, "responseMessage": message}
            self.logStatus("info", "successfully scrapped information", self.takeScreenshot())
            return dic

        if r == 2:
            dic = {}
            message = "Unable To Process. Please Reach Out To Support."
            code = "EUP007"

            dic = {"data": "null", "responseCode": code, "responseMessage": message}
            self.logStatus("info", "Contact support")
            return dic




    def electoralsearch_response(self,epicNumber):
        dic = {}

        epicNumber = epicNumber
        try:
            self.logStatus("info", "opening driver page")
            dic = self.generate_electoralsearch(epicNumber)

        except Exception as e:
            print(e)
            self.logStatus("critical", "Captcha error retrying")
            try:
                self.logStatus("info", "opening driver page")
                dic = self.generate_electoralsearch(epicNumber)

            except Exception as e:
                print(e)
                self.logStatus("critical", "Captcha error retrying")
                try:
                    self.logStatus("info", "opening driver page")
                    dic = self.generate_electoralsearch(epicNumber)

                except Exception as e:
                    try:
                        ff = self.driver.find_element_by_xpath("""// *[ @ id = "imgCaptchaDiv"] / div / span""").text
                        if ff == "Wrong Captcha":
                            dic = {}
                            message = "Unable To Process. Please Reach Out To Support."
                            code = "EUP007"

                            dic = {"data": "null", "responseCode": code, "responseMessage": message}
                            self.logStatus("info", "Contact support")
                            return dic
                    except:
                        pass

                    message = "No Information Found."
                    code = "ENI004"
                    self.logStatus("info", "No Info Found")
                    dic = {"data": "null", "responseCode": code, "responseMessage": message}

        return dic

#if __name__ == '__main__':

 #   v = Electoralsearch(refid="testing2", env = 'prod')
  #  data = v.electoralsearch_response('KYS2186294')
   # print(data)

    #NEL3976684