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

class CAMEMBERSHIP:

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
                                 'vehicle_registration', self.env, screenshot)
        print(f"{level}: {message}, screenshot: {screenshot}")

    def generate_camember(self,caNumber):
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        import io
        #from webdriver_manager.chrome import ChromeDriverManager
        import os
        from google.cloud import vision
        import time

        chrome_options = Options()
        chrome_options.add_experimental_option("excludeSwitches", ['enable-automation'])
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--headless")


        chrome_options.headless = True
        self.makeDriverDirs()

        chrome_options.add_argument("--disable-extension")
        chrome_options.add_argument("no-sandbox")

        self.driver = webdriver.Chrome("/usr/local/bin/chromedriver",options=chrome_options)
        self.logStatus("info", "CAmembership page opened",self.takeScreenshot())
        self.logStatus("info", "Driver created")
        try:
            self.driver.get("http://112.133.194.254/lom.asp")
            r = 1
            self.makeDriverDirs()
            self.logStatus("info", "CAmembership page opened",self.takeScreenshot())
            try:

                cantreach =  self.driver.find_element_by_xpath("""// *[ @ id = "main-message"]""")
                cantreach = cantreach.text

                if cantreach == cantreach:
                    r = 3
            except:
                pass

        except Exception as e:
            self.logStatus("critical", "CAmembership page could not open contact support")
            r = 2
        if r == 2 or r == 3:
            message = "Information Source is Not Working"
            code = "EIS042"
            dic = {'data': 'null', 'responseCode': code, 'responseMessage': message}
            self.logStatus("info", "No Info Found")
            return dic


        if r == 1:


            self.driver.find_element_by_xpath("""/html/body/form/table/tbody/tr/td[2]/input""").click()
            self.driver.find_element_by_xpath("""/html/body/form/table/tbody/tr/td[2]/input""").send_keys(caNumber)
            self.driver.find_element_by_xpath("""/html/body/form/p[1]/input[1]""").click()
            name = self.driver.find_element_by_xpath("""/html/body/form/table[2]/tbody/tr[2]/td[2]/b""")
            name = name.text
            gender = self.driver.find_element_by_xpath("""/html/body/form/table[2]/tbody/tr[3]/td[2]/b""")
            gender = gender.text
            qualification = self.driver.find_element_by_xpath("""/html/body/form/table[2]/tbody/tr[4]/td[2]/b""")
            qualification = qualification.text
            address1 = self.driver.find_element_by_xpath("""/html/body/form/table[2]/tbody/tr[5]/td[2]/b""")
            address1 = address1.text
            address2 = self.driver.find_element_by_xpath("""/html/body/form/table[2]/tbody/tr[6]/td[2]/b""")
            address2 = address2.text
            address3 = self.driver.find_element_by_xpath("""/ html / body / form / table[2] / tbody / tr[9] / td[2] / b""")
            address3 = address3.text
            address4 = self.driver.find_element_by_xpath("""/ html / body / form / table[2] / tbody / tr[10] / td[2] / b""")
            address4 = address4.text
            address5 = self.driver.find_element_by_xpath("""/ html / body / form / table[2] / tbody / tr[7] / td[2] / b""")
            address5 = address5.text
            address6 = self.driver.find_element_by_xpath("""/ html / body / form / table[2] / tbody / tr[8] / td[2] / b""")
            address6 = address6.text



            address = address1 +" "+ address2 + " "+address5 +" "+ address6+" "+ address3 +" "+ address4

            copStatus = self.driver.find_element_by_xpath("""/html/body/form/table[2]/tbody/tr[12]/td[2]/b""")
            copStatus = copStatus.text
            associateYear = self.driver.find_element_by_xpath("""/html/body/form/table[2]/tbody/tr[13]/td[2]/b""")
            associateYear = associateYear.text
            fellowYear = self.driver.find_element_by_xpath("""/html/body/form/table[2]/tbody/tr[14]/td[2]/b""")
            fellowYear = fellowYear.text
            try:
                foreignSectionAddress1 = self.driver.find_element_by_xpath("""/html/body/form/table[2]/tbody/tr[5]/td[4]/b""")
                foreignSectionAddress1 = foreignSectionAddress1.text
            except:
                foreignSectionAddress1 = ""

            try:
                foreignSectionAddress2 = self.driver.find_element_by_xpath(
                    """/html/body/form/table[2]/tbody/tr[6]""")
                foreignSectionAddress2 = foreignSectionAddress2.text
            except:
                foreignSectionAddress2 = ""
            try:
                foreignSectionAddress3 = self.driver.find_element_by_xpath(
                    """/html/body/form/table[2]/tbody/tr[7]""")
                foreignSectionAddress3 = foreignSectionAddress3.text
            except:
                foreignSectionAddress3 = ""
            try:
                foreignSectionAddress4 = self.driver.find_element_by_xpath(
                    """/html/body/form/table[2]/tbody/tr[8]""")
                foreignSectionAddress4 = foreignSectionAddress4.text
            except:
                foreignSectionAddress4 = ""
            try:
                foreignSectionAddress5 = self.driver.find_element_by_xpath(
                    """/html/body/form/table[2]/tbody/tr[9]""")
                foreignSectionAddress5 = foreignSectionAddress5.text
            except:
                foreignSectionAddress5 = ""
            try:
                foreignSectionAddress6 = self.driver.find_element_by_xpath(
                    """/html/body/form/table[2]/tbody/tr[10]""")
                foreignSectionAddress6 = foreignSectionAddress6.text
            except:
                foreignSectionAddress6 = ""
            try:
                foreignSectionAddress7 = self.driver.find_element_by_xpath(
                    """/html/body/form/table[2]/tbody/tr[11]""")
                foreignSectionAddress7 = foreignSectionAddress7.text
            except:
                foreignSectionAddress7 = ""
            if foreignSectionAddress1 == "NOT APPLICABLE":
                foreignSectionAddress = "NOT APPLICABLE"
            else:
                foreignSectionAddress = foreignSectionAddress1 + " " + foreignSectionAddress2 + " " + foreignSectionAddress3 + " " + foreignSectionAddress4 + " " + foreignSectionAddress5 + " " + foreignSectionAddress6 + " " + foreignSectionAddress7
            foreignSectionRegionInIndia = self.driver.find_element_by_xpath("""/html/body/form/table[2]/tbody/tr[14]/td[4]""")
            foreignSectionRegionInIndia = foreignSectionRegionInIndia.text

            message = "Successfully Completed."
            code = "SRC001"
            dic = {}
            dic["address"] = address
            dic["associateYear"] = associateYear
            dic["copStatus"] = copStatus
            dic["fellowYear"] = fellowYear
            dic["foreignSectionAddress"] = foreignSectionAddress
            dic["foreignSectionRegionInIndia"] = foreignSectionRegionInIndia
            dic["gender"] = gender
            dic["membershipNumber"] = caNumber
            dic["name"] = name
            dic["qualification"] = qualification
            dic = {"data": dic, "responseCode": code, "responseMessage": message}
            self.logStatus("info", "completed scraping", self.takeScreenshot())
            return dic

    def camember(self, caNumber):

        dic = {}
        try:
            self.logStatus("info", "Opening webpage")
            dic = self.generate_camember(caNumber)
        except Exception as e:

            self.logStatus("critical", "Captcha error")
            try:
                self.logStatus("info", "Opening webpage")
                dic = self.generate_camember(caNumber)
            except Exception as e:

                self.logStatus("critical", "Captcha error")
                try:
                    self.logStatus("info", "Opening webpage")
                    dic = self.generate_camember(caNumber)
                except Exception as e:

                    self.logStatus("critical", "no data found")
                    dic = {}
                    message = 'No Information Found.'
                    code = 'ENI004'
                    dic = {'data': 'null', 'responseCode': code, 'responseMessage': message}
                    self.logStatus("info", "No Info Found")

        return dic




            #errorcode = self.driver.find_element_by_xpath("""// *[ @ id = "lblMessage"]""")
            #errorcode = errorcode.text
#if __name__ == '__main__':

 #   v = CAMEMBERSHIP(refid="testing2", env = 'prod')
  #  data = v.camember(caNumber = '042381')
   # print(data)