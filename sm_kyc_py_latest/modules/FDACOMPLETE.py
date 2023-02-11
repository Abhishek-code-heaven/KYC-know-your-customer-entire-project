import json
import os
import time
import uuid
from pprint import pprint

import boto3
from botocore.exceptions import ClientError



from modules.db import DB
from modules.utils import GcpOcr



class FDA:

    def __init__(self,refid,env = "prod"):

        self.timeBwPage = 0.5

        assert env == "quality" or env == "prod", ("env value should be either quality or prod")
        self.env = env
        self.screenshotDir = os.path.join(os.getcwd(), "Screenshots")
        self.ocr = GcpOcr("gcp.json")
        self.readConfig()
        self.CreateS3()
        self.dbObj = DB(**self.dbConfig)
        self.refid = refid




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
                                 'FDA_COMPLETE', self.env, screenshot)
        print(f"{level}: {message}, screenshot: {screenshot}")

    def generate_fdarepo(self,licenseNumber):

        from selenium import webdriver

        from selenium.webdriver.common.action_chains import ActionChains
        from selenium.webdriver.chrome.options import Options
        chrome_options = Options()
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--disable-extension")
        chrome_options.add_argument("no-sandbox")

        self.driver = webdriver.Chrome('/usr/local/bin/chromedriver', options=chrome_options)
        start_url = "https://fdamfg.maharashtra.gov.in//login.aspx"
        try:
            self.driver.get(start_url)
            r = 1
            self.makeDriverDirs()
            self.logStatus("info", "getting webpage", self.takeScreenshot())
        except Exception as e:
            r = 2

        if r == 1:
            action = ActionChains(self.driver)
            parent_level_menu = self.driver.find_element_by_xpath("""//*[@id="Menu1n1"]/table/tbody/tr/td[1]/a""")
            action.move_to_element(parent_level_menu).perform()
            child_level_menu = self.driver.find_element_by_xpath("""//*[@id="Menu1n8"]/td/table/tbody/tr/td/a""")
            action.move_to_element(child_level_menu).perform()
            child_level_menu.click()
            self.driver.find_element_by_xpath("""//*[@id="txtGrant_No"]""").click()
            self.driver.find_element_by_xpath("""//*[@id="txtGrant_No"]""").send_keys(licenseNumber)
            self.driver.find_element_by_xpath("""//*[@id="btnGo"]""").click()
            products = self.driver.find_element_by_xpath("""//*[@id="lblResult"]""")
            productstext = products.text
            x = productstext.split(", ")
            shopName = x[0]
            shopName = shopName.encode("utf-8")
            shopName = shopName.decode("utf-8")
            x = productstext.split("- ")
            try:
                d = x[1]

                d = str(d)
                d = d.split("\n")
                phoneNumber1 = d[0]

            except:
                pass
            try:
                d = x[2]
                d = str(d)
                d = d.split("\n")
                phoneNumber2 = d[0]
            except:
                pass

            if len(phoneNumber1) == 10:

                phoneNumber1 = phoneNumber1.encode("utf-8")
                phoneNumber = phoneNumber1.decode("utf-8")

            else:
                phoneNumber2 = phoneNumber2.encode("utf-8")
                phoneNumber = phoneNumber2.decode("utf-8")
            x = productstext.split(", ")
            x = x.pop()
            x = x.split("- ")
            name = x[0]
            name = name.rstrip()
            name = name.encode("utf-8")
            name = name.decode("utf-8")
            x = productstext.split(", ")
            x = x.pop()
            x = x.split("\n")
            x = x[1]
            x = x.split("(")
            licence = x[0]
            licence = licence.rstrip()
            licence = licence.encode("utf-8")
            licence = licence.decode("utf-8")
            x = productstext.split(", ")
            x = x.pop()
            x = x.split("\n")
            x = x[1]
            x = x.split("(")
            x = x[1]
            x = x.split(")")
            date = x[0]
            date = date.encode("utf-8")
            date = date.decode("utf-8")
            x = productstext.split(", ")
            x.pop()
            x = str(x)
            x = x.split(":")
            x = x[1]
            x = x.split(']')
            x = x[0]
            x = x.replace("'", "")
            address = x
            address = address.lstrip()
            address = address.encode("utf-8")
            address = address.decode("utf-8")
            statecodnum = self.driver.find_element_by_xpath("""//*[@id="ddl_state"]""")
            statecode = statecodnum.text
            statecode = statecode.split("\n")
            statecode = statecode[0]
            statecode = statecode.split(" ")
            statecode = statecode[3]
            statecode = statecode.encode("utf-8")
            statecode = statecode.decode("utf-8")
            licenseNumber = str(licenseNumber)
            message = "Successfully Completed."
            code = "SRC001"
            dic = {"address": address, "licenseCode": licence, "mobileNumber": phoneNumber, "ownerName": name,
                   "storeName": shopName, "stringDate": date, "licenseNumber": licenseNumber, "stateCode": statecode}
            dic = {"data": dic, "responseCode": code, "responseMessage": message}
            self.makeDriverDirs()
            self.logStatus("info", "completed scraping", self.takeScreenshot())
            return dic
        elif r == 2:
            licenseNumber = str(licenseNumber)
            message = "No Information Found."
            code = "ENI004"
            address = "null"
            licence = "null"
            phoneNumber = "null"
            name = "null"
            shopName = "null"
            date = "null"
            dic = {"address": address, "licenseCode": licence, "mobileNumber": phoneNumber, "ownerName": name,
                   "storeName": shopName, "stringDate": date, "licenseNumber": licenseNumber}
            dic = {"data": dic, "responseCode": code, "responseMessage": message}
            return dic

    def FDA_response(self,licenseNumber):
        import json
        from pyvirtualdisplay import Display
        display = Display(visible=0, size=(1366, 768))
        display.start()
        dic = {}
        try:
            self.logStatus("info", "Opening webpage")
            dic = self.generate_fdarepo(licenseNumber)
        except Exception as e:

            self.logStatus("critical", "site error retrying")
            try:
                self.logStatus("info", "Opening webpage")
                dic = self.generate_fdarepo(licenseNumber)
            except Exception as e:
                self.logStatus("critical", "site error retrying")
                try:
                    self.logStatus("info", "Opening webpage")
                    dic = self.generate_fdarepo(licenseNumber)
                except Exception as e:
                    licenseNumbern = "null"
                    address = "null"
                    licence = "null"
                    phoneNumber = "null"
                    name = "null"
                    shopName = "null"
                    date = "null"
                    message = "No Information Found."
                    code = "ENI004"
                    dic["address"] = address
                    dic["licenseCode"] = licence
                    dic["mobileNumber"] = phoneNumber
                    dic["ownerName"] = name
                    dic["storeName"] = shopName
                    dic["stringDate"] = date
                    dic["licenseNumber"] = licenseNumbern
                    dic = {"data": dic, "responseCode": code, "responseMessage": message}
                    self.logStatus("info", "No Info Found")
        dic = json.dumps(dic)
        display.stop()
        return dic




#if __name__ == '__main__':

    #v = FDA(refid="c37acbea-15a3-454c-9afe-6cd2e1ba8373", env = 'quality')
    #data = v.FDA_response(licenseNumber = '76727')
    #print(data)
