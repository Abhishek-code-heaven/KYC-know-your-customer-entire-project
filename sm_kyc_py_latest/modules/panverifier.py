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
from selenium.webdriver.support.ui import Select

class CouldNotCreateDriver(Exception):
    pass

class panverifier:

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
                                 'PANVERIFIER', self.env, screenshot)
        print(f"{level}: {message}, screenshot: {screenshot}")
    def generate_panverifier(self,panNumber,fullName,dateOfBirth,status):
        from datetime import datetime
        date_obj = datetime.strptime(dateOfBirth, '%d-%b-%Y')
        dateOfBirth = date_obj.strftime('%d-%m-%Y')
        #from webdriver_manager.chrome import ChromeDriverManager
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        import io
        import os
        import time

        from google.cloud import vision

        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        chrome_options = Options()
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--headless")
        chrome_options.headless = True
        chrome_options.add_argument("--disable-extension")
        chrome_options.add_argument("no-sandbox")
        self.driver = webdriver.Chrome("/usr/local/bin/chromedriver", options=chrome_options)

        self.logStatus("info", "Driver created")
        try:
            self.driver.get("https://www1.incometaxindiaefiling.gov.in/e-FilingGS/Services/VerifyYourPanDeatils.html?lang=eng")
            r = 1
            self.makeDriverDirs()
            self.logStatus("info", "Pan Verifier page opened", self.takeScreenshot())
            try:

                cantreach = self.driver.find_element_by_xpath("""//*[@id="main-message"]/h1/span""")
                cantreach = cantreach.text

                if cantreach == cantreach:
                    r = 3
            except:
                pass

        except Exception as e:

            self.logStatus("critical", "Pan Verifier page could not open contact support")
            r = 3

        if r == 3:
            dic = {}
            message = "Information Source is Not Working"
            code = "EIS042"
            dic = {"data": "null", "responseCode": code, "responseMessage": message}
            self.logStatus("info", "Contact support")
            return dic

        if r == 1:

            self.driver.find_element_by_xpath("""// *[ @ id = "VerifyYourPanGSAuthentication_pan"]""").click()
            self.driver.find_element_by_xpath("""// *[ @ id = "VerifyYourPanGSAuthentication_pan"]""").send_keys(panNumber)
            self.driver.find_element_by_xpath("""//*[@id="VerifyYourPanGSAuthentication_fullName"]""").click()
            self.driver.find_element_by_xpath("""//*[@id="VerifyYourPanGSAuthentication_fullName"]""").send_keys(fullName)
            self.driver.find_element_by_xpath("""//*[@id="dateField"]""").click()
            self.driver.find_element_by_xpath("""//*[@id="dateField"]""").send_keys(dateOfBirth)
            #self.driver.find_element_by_xpath("""//*[@id="VerifyYourPanGSAuthentication_status"]""").click()
            select = Select(self.driver.find_element_by_xpath("""//*[@id="VerifyYourPanGSAuthentication_status"]"""))
            select.select_by_visible_text(status)

            self.driver.find_element_by_xpath("""//*[@id="captchaImg"]""").screenshot('captcha.png')
            with io.open(os.path.join(self.FOLDER_PATH, self.FILE_NAME), 'rb') as image_file:
                content = image_file.read()

            image = vision.types.Image(content=content)
            response = self.client.text_detection(image=image)
            texts = response.text_annotations

            for text in texts:
                z = ('"{}"'.format(text.description))
            h = str(z).split('"')
            k = h[1]

            try:
                sname = str(k) + '.png'
                screenshotName = os.path.join(self.screenshotDir, f"{sname}")
                self.driver.find_element_by_xpath("""//*[@id="captchaImg"]""").screenshot(screenshotName)
                self.uploadToS3(os.path.join(screenshotName), 'PANVERIFIER/' + sname)
            except:
                pass

            self.driver.find_element_by_xpath("""//*[@id="VerifyYourPanGSAuthentication_captchaCode"]""").click()
            self.driver.find_element_by_xpath("""//*[@id="VerifyYourPanGSAuthentication_captchaCode"]""").send_keys(k)
            self.makeDriverDirs()
            self.logStatus("info", "enter k", self.takeScreenshot())
            self.driver.find_element_by_xpath("""//*[@id="submitbtn"]""").click()

            x=7

            try:
                No_records = self.driver.find_element_by_xpath("""// *[ @ id = "actionErrors"] / ul / li / span""")
                No_records = No_records.text
                if No_records == "No record found for the given PAN.":
                    x=2

            except:
                pass
            try:
                Pan_Incorrect = self.driver.find_element_by_xpath("""//*[@id="VerifyYourPanGSAuthentication"]/table/tbody/tr[2]/td/div[1]""")
                Pan_Incorrect = Pan_Incorrect.text
                if Pan_Incorrect == "Invalid PAN. Please retry.":
                    x = 1



            except:
                pass
            #try:
                #captcha = self.driver.find_element_by_xpath("""// *[ @ id = "VerifyYourPanGSAuthentication"] / table / tbody / td / div[1] / text()""")
                #captcha = captcha.text
                #if captcha = " Please enter the code as appearing in the Image.":
                    #x = 5
                #return Exception as e, x
            #except:
                #pass

            try:
                Name_Incorrect = self.driver.find_element_by_xpath("""//*[@id="VerifyYourPanGSAuthentication"]/table/tbody/tr[3]/td/div[1]""")
                Name_Incorrect = Name_Incorrect.text
                if Name_Incorrect == "Please enter Full Name.":
                    x = 2

            except:
                pass
            try:
                date = self.driver.find_element_by_xpath("""//*[@id="VerifyYourPanGSAuthentication"]/table/tbody/tr[4]/td/div[1]""")
                date = date.text
                if date == "Invalid Date of Birth. Please retry.":
                    x=4


            except:
                pass

            if x ==7:

                Pan_Status = self.driver.find_element_by_xpath("""//*[@id="staticContentsUrl"]/div/div[2]/ul""")
                Pan_Status = Pan_Status.text
                self.logStatus("info", "Scrapped Successfully", self.takeScreenshot())
                from datetime import datetime
                date_obj = datetime.strptime(dateOfBirth, '%d-%m-%Y')
                dateOfBirth = date_obj.strftime('%d-%b-%Y')
                dic = {}
                message = 'Successfully Completed.'
                code = 'SRC001'
                dic['status'] = status
                dic['dateOfBirth'] = dateOfBirth
                dic['panStatus'] = Pan_Status
                dic['panNumber'] = panNumber
                dic['fullName'] = fullName
                dic = {'data': dic, 'responseCode': code, 'responseMessage': message}
                return dic

            elif x ==3:
                from datetime import datetime
                date_obj = datetime.strptime(dateOfBirth, '%d-%m-%Y')
                dateOfBirth = date_obj.strftime('%d-%b-%Y')

                dic = {}

                message = "Unable To Process. Please Reach Out To Support."
                code = "EUP007"
                dic["panStatus"] = No_records
                dic["panNumber"] = panNumber
                dic["fullName"] = fullName
                dic['dateOfBirth'] = dateOfBirth
                dic['status'] = status

                dic = {'data': dic, 'responseCode': code, 'responseMessage': message}
                return dic
            elif x==1:
                from datetime import datetime
                date_obj = datetime.strptime(dateOfBirth, '%d-%m-%Y')
                dateOfBirth = date_obj.strftime('%d-%b-%Y')
                dic = {}
                self.logStatus("info", "'Pan Incorrect.", self.takeScreenshot())
                message = 'No Information Found.'
                code = 'ENI004'
                dic['panStatus'] = Pan_Incorrect
                dic['panNumber'] = panNumber
                dic['fullName'] = fullName
                dic['dateOfBirth'] = dateOfBirth
                dic['status'] = status

                dic = {'data': dic, 'responseCode': code, 'responseMessage': message}
                return dic
            elif x==2:
                from datetime import datetime
                date_obj = datetime.strptime(dateOfBirth, '%d-%m-%Y')
                dateOfBirth = date_obj.strftime('%d-%b-%Y')
                dic = {}
                self.makeDriverDirs()
                self.logStatus("info", "Name Incorrect.", self.takeScreenshot())
                message = 'No Information Found.'
                code = 'ENI004'
                dic['panStatus'] = 'null'
                dic['panNumber'] = panNumber
                dic['fullName'] = Name_Incorrect
                dic['dateOfBirth'] = dateOfBirth
                dic['status'] = status

                dic = {'data': dic, 'responseCode': code, 'responseMessage': message}
                return dic
            elif x==4:
                dic = {}
                self.makeDriverDirs()
                self.logStatus("info", "Please enter correct date.", self.takeScreenshot())
                message = 'No Information Found.'
                code = 'ENI004'
                dic['panStatus'] = 'null'
                dic['fullName'] = fullName
                dic['panNumber'] = panNumber
                dic['dateOfBirth'] = date
                dic['status'] = status
                dic = {'data': dic, 'responseCode': code, 'responseMessage': message}
                return dic


    def panverifier_response(self,panNumber,fullName,dateOfBirth,status):

        dic = {}
        try:
            self.logStatus("info", "Opening webpage")
            dic = self.generate_panverifier(panNumber,fullName,dateOfBirth,status)
        except Exception as e:

            self.logStatus("critical", "Captcha error")
            try:
                self.logStatus("info", "Opening webpage")
                dic = self.generate_panverifier(panNumber,fullName,dateOfBirth,status)
            except Exception as e:
                print(e)

                self.logStatus("critical", "Captcha error")
                try:
                    self.logStatus("info", "Opening webpage")
                    dic = self.generate_panverifier(panNumber,fullName,dateOfBirth,status)
                except Exception as e:
                    print(e)

                    try:
                        hh = self.driver.find_element_by_xpath("""// *[ @ id = "VerifyYourPanGSAuthentication"] / table / tbody / tr[8] / td / div[1]""").text
                        if hh == "Invalid Code. Please enter the code as appearing in the Image.":
                            message = "Unable To Process. Please Reach Out To Support."
                            code = "EUP007"
                            No_records = ""
                            dic["panStatus"] = No_records
                            dic["panNumber"] = panNumber
                            dic["fullName"] = fullName
                            dic['dateOfBirth'] = dateOfBirth
                            dic['status'] = status

                            dic = {'data': dic, 'responseCode': code, 'responseMessage': message}
                            return dic
                    except:
                        pass



                    self.logStatus("critical", "no data found")
                    dic = {}
                    message = 'No Information Found.'
                    code = 'ENI004'
                    dic['panStatus'] = 'null'
                    dic['fullName'] = 'null'
                    dic['panNumber'] = 'null'
                    dic['dateOfBirth'] = 'null'
                    dic['status'] = 'null'
                    dic = {'data': dic, 'responseCode': code, 'responseMessage': message}
                    self.logStatus("info", "No Info Found")

        return dic

#if __name__ == '__main__':

 #   v = panverifier(refid="testing2", env = 'prod')
  #  data = v.panverifier_response(panNumber = 'COWPK3536F',fullName = 'Mahesh',dateOfBirth = '02-Apr-1961' ,status = 'Individual' )
   # print(data)

