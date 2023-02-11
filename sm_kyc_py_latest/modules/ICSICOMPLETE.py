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

class ICSI:

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
                                 'ICSI', self.env, screenshot)
        print(f"{level}: {message}, screenshot: {screenshot}")

    def generate_ICSI(self,memberType,membershipNumber):
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        import io
        #from webdriver_manager.chrome import ChromeDriverManager
        import os
        from selenium.webdriver.support.ui import Select
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

        self.driver = webdriver.Chrome('/usr/local/bin/chromedriver',options=chrome_options)
        self.logStatus("info", "ICSI page opened",self.takeScreenshot())
        self.logStatus("info", "Driver created")
        try:
            self.driver.get("https://www.icsi.in/student/Members/MemberSearch.aspx?SkinSrc=%5BG%5DSkins/IcsiTheme/IcsiIn-Bare&ContainerSrc=%5BG%5DContainers/IcsiTheme/NoContainer")
            r = 1
            self.makeDriverDirs()
            self.logStatus("info", "ICSI page opened",self.takeScreenshot())
            try:

                cantreach =  self.driver.find_element_by_xpath("""// *[ @ id = "main-message"]""")
                cantreach = cantreach.text

                if cantreach == cantreach:
                    r = 3
            except:
                pass

        except Exception as e:
            self.logStatus("critical", "ICSI page could not open contact support")
            r = 2

        try:
            self.driver.find_element_by_xpath("""//*[@id="dnn_ctr410_ModuleContent"]/div[2]/h3""")
        except:
            r = 2
            pass

        if r == 2 or r == 3:
            message = "Information Source is Not Working"
            code = "EIS042"
            dic = {'data': 'null', 'responseCode': code, 'responseMessage': message}
            self.logStatus("info", "No Info Found")
            return dic
        if r == 1:
            select = Select(self.driver.find_element_by_xpath('// *[ @ id = "dnn_ctr410_MemberSearch_ddlMemberType"]'))

            select.select_by_visible_text(memberType)
            self.driver.find_element_by_xpath("""// *[ @ id = "dnn_ctr410_MemberSearch_txtMembershipNumber"]""").click()
            self.driver.find_element_by_xpath("""// *[ @ id = "dnn_ctr410_MemberSearch_txtMembershipNumber"]""").send_keys(membershipNumber)
            self.driver.find_element_by_xpath("""// *[ @ id = "dnn_ctr410_MemberSearch_btnSearch"]""").click()

            name = self.driver.find_element_by_xpath("""// *[ @ id = "dnn_ctr410_MemberSearch_grdMembers_ctl00_ctl04_lblFullName"]""")
            name = name.text
            organization = self.driver.find_element_by_xpath("""// *[ @ id = "dnn_ctr410_MemberSearch_grdMembers_ctl00_ctl04_lblOrganizationName"]""")
            organization = organization.text
            designation = self.driver.find_element_by_xpath("""// *[ @ id = "dnn_ctr410_MemberSearch_grdMembers_ctl00_ctl04_lblDesignation"]""")
            designation = designation.text
            membershipNumber = self.driver.find_element_by_xpath("""//*[@id="dnn_ctr410_MemberSearch_grdMembers_ctl00_ctl04_lblMembershipNumber"]""")
            membershipNumber = membershipNumber.text
            cpNumber = self.driver.find_element_by_xpath("""//*[@id="dnn_ctr410_MemberSearch_grdMembers_ctl00__0"]/td[1]/table/tbody/tr/td[2]/table/tbody/tr[2]/td[1]/div/div[4]/table/tbody/tr/td[2]""")
            cpNumber = cpNumber.text
            benevolentMember = self.driver.find_element_by_xpath("""//*[@id="dnn_ctr410_MemberSearch_grdMembers_ctl00_ctl04_lblBenov"]""")
            benevolentMember = benevolentMember.text
            address = self.driver.find_element_by_xpath("""// *[ @ id = "dnn_ctr410_MemberSearch_grdMembers_ctl00__0"] / td[1] / table / tbody / tr / td[2] / table / tbody / tr[2] / td[2] / div / div[1] / table / tbody / tr / td[2]""")
            address = address.text
            city = self.driver.find_element_by_xpath("""// *[ @ id = "dnn_ctr410_MemberSearch_grdMembers_ctl00_ctl04_lblCity"]""")
            city = city.text
            phoneNumber = self.driver.find_element_by_xpath("""// *[ @ id = "dnn_ctr410_MemberSearch_grdMembers_ctl00_ctl04_lblOfficePhone"]""")
            phoneNumber = phoneNumber.text
            email = self.driver.find_element_by_xpath("""// *[ @ id = "dnn_ctr410_MemberSearch_grdMembers_ctl00_ctl04_lblEmail"]""")
            email = email.text
            mobile = self.driver.find_element_by_xpath("""// *[ @ id = "dnn_ctr410_MemberSearch_grdMembers_ctl00_ctl04_lblMobileNumber"]""")
            mobile = mobile.text
            message = "Successfully Completed."
            code = "SRC001"
            dic = {}
            dic["address"] = address
            dic["benevolentMember"] = benevolentMember
            dic["city"] = city
            dic["cpNumber"] = cpNumber
            dic["designation"] = designation
            dic["email"] = email
            dic["membershipNumber"] = membershipNumber
            dic["mobile"] = mobile
            dic["name"] = name
            dic["organization"] = organization
            dic["phoneNumber"] = phoneNumber
            dic = {"data": dic, "responseCode": code, "responseMessage": message}
            self.makeDriverDirs()
            self.logStatus("info", "completed scraping", self.takeScreenshot())
            return dic

    def ICSI_response(self,memberType,membershipNumber):

        dic = {}
        try:
            self.logStatus("info", "Opening webpage")
            dic = self.generate_ICSI(memberType,membershipNumber)
        except Exception as e:

            self.logStatus("critical", "Captcha error")
            try:
                self.logStatus("info", "Opening webpage")
                dic = self.generate_ICSI(memberType,membershipNumber)
            except Exception as e:

                self.logStatus("critical", "Captcha error")
                try:
                    self.logStatus("info", "Opening webpage")
                    dic = self.generate_ICSI(memberType,membershipNumber)
                except Exception as e:

                    self.logStatus("critical", "no data found")
                    dic = {}
                    message = 'No Information Found.'
                    code = 'ENI004'
                    dic = {'data': 'null', 'responseCode': code, 'responseMessage': message}
                    self.logStatus("info", "No Info Found")

        return dic







#if __name__ == '__main__':

 #   v = ICSI(refid="testing2", env = 'prod')
  #  data = v.ICSI_response(memberType = 'FCS', membershipNumber = '9365')
   # print(data)