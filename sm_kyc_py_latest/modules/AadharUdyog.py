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

class aadharudyog:

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
                                 'UdyogAadhar', self.env, screenshot)
        print(f"{level}: {message}, screenshot: {screenshot}")

    def breakcaptcha(self):
        import io
        import os
        from google.cloud import vision
        import time
        import io
        self.driver.find_element_by_xpath("""//*[@id="ctl00_ContentPlaceHolder1_imgCaptcha"]""").screenshot('captcha.png')
        with io.open(os.path.join(self.FOLDER_PATH, self.FILE_NAME), 'rb') as image_file:
            content = image_file.read()

        image = vision.types.Image(content=content)
        response = self.client.text_detection(image=image)
        texts = response.text_annotations

        for text in texts:
            z = ('"{}"'.format(text.description))
        h = str(z).split('"')
        k = h[1]

        self.driver.find_element_by_xpath("""// *[ @ id = "ctl00_ContentPlaceHolder1_txtCaptcha"]""").click()
        self.driver.find_element_by_xpath("""// *[ @ id = "ctl00_ContentPlaceHolder1_txtCaptcha"]""").send_keys(k)

        self.driver.find_element_by_xpath("""// *[ @ id = "ctl00_ContentPlaceHolder1_btnLogin"]""").click()

    def generate_AadharUdyog(self,uamNumber):
       # from datetime import datetime
        #date_obj = datetime.strptime(dateOfBirth, '%d-%b-%Y')
       # dateOfBirth = date_obj.strftime('%d-%m-%Y')
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

        #from webdriver_manager.chrome import ChromeDriverManager
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--headless")
        chrome_options.headless = True
        chrome_options.add_argument("--disable-extension")
        chrome_options.add_argument("no-sandbox")
        self.driver = webdriver.Chrome("/usr/local/bin/chromedriver", options=chrome_options)

        self.logStatus("info", "Driver created")
        try:
            self.driver.get("https://udyamregistration.gov.in/UA/UA_VerifyUAM.aspx")
            r = 1
            self.makeDriverDirs()
            self.logStatus("info", "AadharUdyog page opened", self.takeScreenshot())
            try:

                cantreach =  self.driver.find_element_by_xpath("""// *[ @ id = "main-message"]""")
                cantreach = cantreach.text

                if cantreach == cantreach:
                    r = 3
            except:
                pass

        except Exception as e:

            self.logStatus("critical", "AadharUdyog page could not open contact support")
            r = 2

        try:
            canreach = self.driver.find_element_by_xpath("""//*[@id="page-wrapper"]/div/div[1]/div/h1""")
            canreach = canreach.text
            if canreach == 'Udyog Aadhaar Memorandum - Online Verification':
                r = 1
        except:
            r = 3
            pass


        if r == 3:
            dic = {}
            message = "Information Source is Not Working"
            code = "EIS042"
            dic = {"data": "null", "responseCode": code, "responseMessage": message}
            self.logStatus("info", "Contact support")
            return dic

        if r == 1:

            self.driver.find_element_by_xpath("""//*[@id="ctl00_ContentPlaceHolder1_txtUANNumber"]""").click()
            self.driver.find_element_by_xpath("""//*[@id="ctl00_ContentPlaceHolder1_txtUANNumber"]""").send_keys(uamNumber)
            try:
                self.logStatus("info", "Trying captcha 1")
                self.breakcaptcha()
                errorcode1 = self.driver.find_element_by_xpath("""//*[@id="ctl00_ContentPlaceHolder1_lblCaptcha"]""")
                errorcode1 = errorcode1.text
                if errorcode1 == 'Incorrect verification code. Please try again.':
                    self.driver.find_element_by_xpath("""//*[@id="ctl00_ContentPlaceHolder1_txtCaptcha"]""").clear()
                    self.logStatus("info", "Trying captcha 2")
                    self.breakcaptcha()
                    errorcode2 = self.driver.find_element_by_xpath("""//*[@id="ctl00_ContentPlaceHolder1_lblCaptcha"]""")
                    errorcode2 = errorcode2.text
                    if errorcode2 == 'Incorrect verification code. Please try again.':
                        self.driver.find_element_by_xpath("""//*[@id="ctl00_ContentPlaceHolder1_txtCaptcha"]"]""").clear()
                        self.logStatus("info", "Trying captcha 3")
                        self.breakcaptcha()
                        errorcode3 = self.driver.find_element_by_xpath(
                            """//*[@id="ctl00_ContentPlaceHolder1_lblCaptcha"]""")
                        errorcode3 = errorcode3.text
                        if errorcode3 == 'Incorrect verification code. Please try again.':
                            self.driver.find_element_by_xpath("""//*[@id="ctl00_ContentPlaceHolder1_txtCaptcha"]"]""").clear()
                            self.logStatus("info", "Trying captcha 4")
                            self.breakcaptcha()
                        else:
                            pass

            except Exception:
                self.logStatus("info", "captcha not broke")
                pass



            appliedDate = self.driver.find_element_by_xpath("""// *[ @ id = "lblAppliedDate"]""")
            appliedDate = appliedDate.text
            from datetime import datetime
            date_obj = datetime.strptime(appliedDate, '%d/%m/%Y')
            appliedDate = date_obj.strftime('%d-%b-%Y')


            try:
                dateOfCommencement = self.driver.find_element_by_xpath("""//*[@id="lblDateOFCommencement"]""")
                dateOfCommencement = dateOfCommencement.text
                from datetime import datetime
                date_obj = datetime.strptime(dateOfCommencement, '%d/%m/%Y')
                dateOfCommencement = date_obj.strftime('%d-%b-%Y')
            except:
                pass

            try:
                dicName = self.driver.find_element_by_xpath("""//*[@id="lblDICNAme"]""")
                dicName = dicName.text
            except Exception:
                raise Exception

            try:
                enterpriseCode = self.driver.find_element_by_xpath("""//*[@id="lblEntType"]""")
                enterpriseCode = enterpriseCode.text
            except:
                pass


            try:
                enterpriseType = self.driver.find_element_by_xpath("""// *[ @ id = "lblEnterpriseType"]""")
                enterpriseType = enterpriseType.text
            except:
                pass

            try:
                majorActivity = self.driver.find_element_by_xpath("""//*[@id="lblMajorActivity"]""")
                majorActivity = majorActivity.text
            except:
                pass

            try:
                modifiedDate = self.driver.find_element_by_xpath("""//*[@id="lblUpdatedDate"]""")
                modifiedDate = modifiedDate.text
                from datetime import datetime
                date_obj = datetime.strptime(modifiedDate, '%d/%m/%Y')
                modifiedDate = date_obj.strftime('%d-%b-%Y')
            except:
                modifiedDate = self.driver.find_element_by_xpath("""//*[@id="lblUpdatedDate"]""")
                modifiedDate = modifiedDate.text
                pass

            try:
                nameOfEnterprise = self.driver.find_element_by_xpath("""//*[@id="lblNameofEnterPrise"]""")
                nameOfEnterprise = nameOfEnterprise.text
            except:
                pass

            try:
                socialCategory = self.driver.find_element_by_xpath("""//*[@id="lblCategory"]""")
                socialCategory = socialCategory.text
            except:
                pass

            try:
                state = self.driver.find_element_by_xpath("""//*[@id="lblState"]""")
                state = state.text
            except:
                pass

            try:
                uamValidityMessage = self.driver.find_element_by_xpath("""//*[@id="tr6"]/td/span""")
                uamValidityMessage = uamValidityMessage.text
            except:
                pass

            #National Industry Classification Code

            try:
                serialNumber1 = self.driver.find_element_by_xpath("""//*[@id="GVNICCodeDisplay"]/tbody/tr[2]/td[1]/span""")
                serialNumber1 = serialNumber1.text
            except:
                pass
            try:
                serialNumber2 = self.driver.find_element_by_xpath("""//*[@id="GVNICCodeDisplay"]/tbody/tr[3]/td[1]/span""")
                serialNumber2 = serialNumber2.text
            except:
                pass
            try:
                serialNumber3 = self.driver.find_element_by_xpath("""//*[@id="GVNICCodeDisplay"]/tbody/tr[4]/td[1]/span""")
                serialNumber3 = serialNumber3.text
            except:
                pass
            try:
                serialNumber4 = self.driver.find_element_by_xpath("""//*[@id="GVNICCodeDisplay"]/tbody/tr[5]/td[1]/span""")
                serialNumber4 = serialNumber4.text
            except:
                pass
            try:
                serialNumber6 = self.driver.find_element_by_xpath("""//*[@id="GVNICCodeDisplay"]/tbody/tr[6]/td[1]/span""")
                serialNumber6 = serialNumber6.text
            except:
                pass
            try:
                serialNumber7 = self.driver.find_element_by_xpath("""//*[@id="GVNICCodeDisplay"]/tbody/tr[7]/td[1]/span""")
                serialNumber7 = serialNumber7.text
            except:
                pass
            try:
                serialNumber8 = self.driver.find_element_by_xpath("""//*[@id="GVNICCodeDisplay"]/tbody/tr[8]/td[1]/span""")
                serialNumber8 = serialNumber8.text
            except:
                pass
            try:
                serialNumber9 = self.driver.find_element_by_xpath("""//*[@id="GVNICCodeDisplay"]/tbody/tr[9]/td[1]/span""")
                serialNumber9 = serialNumber9.text
            except:
                pass
            try:
                serialNumber10 = self.driver.find_element_by_xpath("""//*[@id="GVNICCodeDisplay"]/tbody/tr[10]/td[1]/span""")
                serialNumber10 = serialNumber10.text
            except:
                pass

            try:
                nic2Digit1 = self.driver.find_element_by_xpath("""//*[@id="GVNICCodeDisplay"]/tbody/tr[2]/td[2]""")
                nic2Digit1 = nic2Digit1.text
            except:
                pass
            try:
                nic2Digit2 = self.driver.find_element_by_xpath("""//*[@id="GVNICCodeDisplay"]/tbody/tr[3]/td[2]""")
                nic2Digit2 = nic2Digit2.text
            except:
                pass
            try:
                nic2Digit3 = self.driver.find_element_by_xpath("""//*[@id="GVNICCodeDisplay"]/tbody/tr[4]/td[2]""")
                nic2Digit3 = nic2Digit3.text
            except:
                pass
            try:
                nic2Digit4 = self.driver.find_element_by_xpath("""//*[@id="GVNICCodeDisplay"]/tbody/tr[5]/td[2]""")
                nic2Digit4 = nic2Digit4.text
            except:
                pass
            try:
                nic2Digit5 = self.driver.find_element_by_xpath("""//*[@id="GVNICCodeDisplay"]/tbody/tr[6]/td[2]""")
                nic2Digit5 = nic2Digit5.text
            except:
                pass
            try:
                nic2Digit6 = self.driver.find_element_by_xpath("""//*[@id="GVNICCodeDisplay"]/tbody/tr[7]/td[2]""")
                nic2Digit6 = nic2Digit6.text
            except:
                pass
            try:
                nic2Digit7 = self.driver.find_element_by_xpath("""//*[@id="GVNICCodeDisplay"]/tbody/tr[8]/td[2]""")
                nic2Digit7 = nic2Digit7.text
            except:
                pass
            try:
                nic2Digit8 = self.driver.find_element_by_xpath("""//*[@id="GVNICCodeDisplay"]/tbody/tr[9]/td[2]""")
                nic2Digit8 = nic2Digit8.text
            except:
                pass
            try:
                nic2Digit9 = self.driver.find_element_by_xpath("""//*[@id="GVNICCodeDisplay"]/tbody/tr[10]/td[2]""")
                nic2Digit9 = nic2Digit9.text
            except:
                pass
            try:
                nic4Digit1 = self.driver.find_element_by_xpath("""//*[@id="GVNICCodeDisplay"]/tbody/tr[2]/td[3]""")
                nic4Digit1 = nic4Digit1.text
            except:
                pass
            try:
                nic4Digit2 = self.driver.find_element_by_xpath("""//*[@id="GVNICCodeDisplay"]/tbody/tr[3]/td[3]""")
                nic4Digit2 = nic4Digit2.text
            except:
                pass
            try:
                nic4Digit3 = self.driver.find_element_by_xpath("""//*[@id="GVNICCodeDisplay"]/tbody/tr[4]/td[3]""")
                nic4Digit3 = nic4Digit3.text
            except:
                pass
            try:
                nic4Digit4 = self.driver.find_element_by_xpath("""//*[@id="GVNICCodeDisplay"]/tbody/tr[5]/td[3]""")
                nic4Digit4 = nic4Digit4.text
            except:
                pass
            try:
                nic4Digit5 = self.driver.find_element_by_xpath("""//*[@id="GVNICCodeDisplay"]/tbody/tr[6]/td[3]""")
                nic4Digit5 = nic4Digit5.text
            except:
                pass
            try:
                nic4Digit6 = self.driver.find_element_by_xpath("""//*[@id="GVNICCodeDisplay"]/tbody/tr[7]/td[3]""")
                nic4Digit6 = nic4Digit6.text
            except:
                pass
            try:
                nic4Digit7 = self.driver.find_element_by_xpath("""//*[@id="GVNICCodeDisplay"]/tbody/tr[8]/td[3]""")
                nic4Digit7 = nic4Digit7.text
            except:
                pass
            try:
                nic4Digit8 = self.driver.find_element_by_xpath("""//*[@id="GVNICCodeDisplay"]/tbody/tr[9]/td[3]""")
                nic4Digit8 = nic4Digit8.text
            except:
                pass
            try:
                nic4Digit9 = self.driver.find_element_by_xpath("""//*[@id="GVNICCodeDisplay"]/tbody/tr[10]/td[3]""")
                nic4Digit9 = nic4Digit9.text
            except:
                pass
            try:
                nic5Digit1 = self.driver.find_element_by_xpath("""//*[@id="GVNICCodeDisplay"]/tbody/tr[2]/td[4]""")
                nic5Digit1 = nic5Digit1.text
            except:
                pass
            try:
                nic5Digit2 = self.driver.find_element_by_xpath("""//*[@id="GVNICCodeDisplay"]/tbody/tr[3]/td[4]""")
                nic5Digit2 = nic5Digit2.text
            except:
                pass
            try:
                nic5Digit3 = self.driver.find_element_by_xpath("""//*[@id="GVNICCodeDisplay"]/tbody/tr[4]/td[4]""")
                nic5Digit3 = nic5Digit3.text
            except:
                pass
            try:
                nic5Digit4 = self.driver.find_element_by_xpath("""//*[@id="GVNICCodeDisplay"]/tbody/tr[5]/td[4]""")
                nic5Digit4 = nic5Digit4.text
            except:
                pass
            try:
                nic5Digit5 = self.driver.find_element_by_xpath("""//*[@id="GVNICCodeDisplay"]/tbody/tr[6]/td[4]""")
                nic5Digit5 = nic5Digit5.text
            except:
                pass
            try:
                nic5Digit6 = self.driver.find_element_by_xpath("""//*[@id="GVNICCodeDisplay"]/tbody/tr[7]/td[4]""")
                nic5Digit6 = nic5Digit6.text
            except:
                pass
            try:
                nic5Digit7 = self.driver.find_element_by_xpath("""//*[@id="GVNICCodeDisplay"]/tbody/tr[8]/td[4]""")
                nic5Digit7 = nic5Digit7.text
            except:
                pass
            try:
                nic5Digit8 = self.driver.find_element_by_xpath("""//*[@id="GVNICCodeDisplay"]/tbody/tr[9]/td[4]""")
                nic5Digit8 = nic5Digit8.text
            except:
                pass
            try:
                nic5Digit9 = self.driver.find_element_by_xpath("""//*[@id="GVNICCodeDisplay"]/tbody/tr[10]/td[4]""")
                nic5Digit9 = nic5Digit9.text
            except:
                pass

            try:
                activityType1 = self.driver.find_element_by_xpath("""//*[@id="GVNICCodeDisplay"]/tbody/tr[2]/td[5]""")
                activityType1 = activityType1.text
            except:
                pass
            try:
                activityType2 = self.driver.find_element_by_xpath("""//*[@id="GVNICCodeDisplay"]/tbody/tr[3]/td[5]""")
                activityType2 = activityType2.text
            except:
                pass
            try:
                activityType3 = self.driver.find_element_by_xpath("""//*[@id="GVNICCodeDisplay"]/tbody/tr[4]/td[5]""")
                activityType3 = activityType3.text
            except:
                pass
            try:
                activityType4 = self.driver.find_element_by_xpath("""//*[@id="GVNICCodeDisplay"]/tbody/tr[5]/td[5]""")
                activityType4 = activityType4.text
            except:
                pass
            try:
                activityType5 = self.driver.find_element_by_xpath("""//*[@id="GVNICCodeDisplay"]/tbody/tr[6]/td[5]""")
                activityType5 = activityType5.text
            except:
                pass
            try:
                activityType6 = self.driver.find_element_by_xpath("""//*[@id="GVNICCodeDisplay"]/tbody/tr[7]/td[5]""")
                activityType6 = activityType6.text
            except:
                pass
            try:
                activityType7 = self.driver.find_element_by_xpath("""//*[@id="GVNICCodeDisplay"]/tbody/tr[8]/td[5]""")
                activityType7 = activityType7.text
            except:
                pass
            try:
                activityType8 = self.driver.find_element_by_xpath("""//*[@id="GVNICCodeDisplay"]/tbody/tr[9]/td[5]""")
                activityType8 = activityType8.text
            except:
                pass
            try:
                activityType9 = self.driver.find_element_by_xpath("""//*[@id="GVNICCodeDisplay"]/tbody/tr[10]/td[5]""")
                activityType9 = activityType9.text
            except:
                pass
            try:
                addedOn1 = self.driver.find_element_by_xpath("""//*[@id="GVNICCodeDisplay"]/tbody/tr[2]/td[6]""")
                addedOn1 = addedOn1.text
            except:
                pass
            try:
                addedOn2 = self.driver.find_element_by_xpath("""//*[@id="GVNICCodeDisplay"]/tbody/tr[3]/td[6]""")
                addedOn2 = addedOn2.text
            except:
                pass
            try:
                addedOn3 = self.driver.find_element_by_xpath("""//*[@id="GVNICCodeDisplay"]/tbody/tr[4]/td[6]""")
                addedOn3 = addedOn3.text
            except:
                pass
            try:
                addedOn4 = self.driver.find_element_by_xpath("""//*[@id="GVNICCodeDisplay"]/tbody/tr[5]/td[6]""")
                addedOn4 = addedOn4.text
            except:
                pass
            try:
                addedOn5 = self.driver.find_element_by_xpath("""//*[@id="GVNICCodeDisplay"]/tbody/tr[6]/td[6]""")
                addedOn5 = addedOn5.text
            except:
                pass
            try:
                addedOn6 = self.driver.find_element_by_xpath("""//*[@id="GVNICCodeDisplay"]/tbody/tr[7]/td[6]""")
                addedOn6 = addedOn6.text
            except:
                pass
            try:
                addedOn7 = self.driver.find_element_by_xpath("""//*[@id="GVNICCodeDisplay"]/tbody/tr[8]/td[6]""")
                addedOn7 = addedOn7.text
            except:
                pass
            try:
                addedOn8 = self.driver.find_element_by_xpath("""//*[@id="GVNICCodeDisplay"]/tbody/tr[9]/td[6]""")
                addedOn8 = addedOn8.text
            except:
                pass
            try:
                addedOn9 = self.driver.find_element_by_xpath("""//*[@id="GVNICCodeDisplay"]/tbody/tr[10]/td[6]""")
                addedOn9 = addedOn9.text
            except:
                pass

            #Location of Plant Details

            try:
                areaLocality1 = self.driver.find_element_by_xpath("""//*[@id="gv_PlantDetails"]/tbody/tr[2]/td[5]""")
                areaLocality1 = areaLocality1.text
            except:
                pass
            try:
                areaLocality2 = self.driver.find_element_by_xpath("""//*[@id="gv_PlantDetails"]/tbody/tr[3]/td[5]""")
                areaLocality2 = areaLocality2.text
            except:
                pass

            try:
                city1 = self.driver.find_element_by_xpath("""//*[@id="gv_PlantDetails"]/tbody/tr[2]/td[6]""")
                city1 = city1.text
            except:
                pass
            try:
                city2 = self.driver.find_element_by_xpath("""//*[@id="gv_PlantDetails"]/tbody/tr[3]/td[6]""")
                city2 = city2.text
            except:
                pass

            try:
                district1 = self.driver.find_element_by_xpath("""//*[@id="gv_PlantDetails"]/tbody/tr[2]/td[9]""")
                district1 = district1.text
            except:
                pass
            try:
                district2 = self.driver.find_element_by_xpath("""//*[@id="gv_PlantDetails"]/tbody/tr[3]/td[9]""")
                district2 = district2.text
            except:
                pass
            try:
                roadStreetLane1 = self.driver.find_element_by_xpath("""//*[@id="gv_PlantDetails"]/tbody/tr[2]/td[4]""")
                roadStreetLane1 = roadStreetLane1.text
            except:
                pass
            try:
                roadStreetLane2 = self.driver.find_element_by_xpath("""//*[@id="gv_PlantDetails"]/tbody/tr[3]/td[4]""")
                roadStreetLane2 = roadStreetLane2.text
            except:
                pass
            try:
                pin1 = self.driver.find_element_by_xpath("""//*[@id="gv_PlantDetails"]/tbody/tr[2]/td[7]""")
                pin1 = pin1.text
            except:
                pass
            try:
                pin2 = self.driver.find_element_by_xpath("""//*[@id="gv_PlantDetails"]/tbody/tr[3]/td[7]""")
                pin2 = pin2.text
            except:
                pass
            try:
                premisesBuilding1 = self.driver.find_element_by_xpath("""//*[@id="gv_PlantDetails"]/tbody/tr[2]/td[3]""")
                premisesBuilding1 = premisesBuilding1.text
            except:
                pass
            try:
                premisesBuilding2 = self.driver.find_element_by_xpath("""//*[@id="gv_PlantDetails"]/tbody/tr[3]/td[3]""")
                premisesBuilding2 = premisesBuilding2.text
            except:
                pass
            try:
                flatDoorBlock1 = self.driver.find_element_by_xpath("""//*[@id="gv_PlantDetails"]/tbody/tr[2]/td[2]""")
                flatDoorBlock1 = flatDoorBlock1.text
            except:
                pass
            try:
                flatDoorBlock2 = self.driver.find_element_by_xpath("""//*[@id="gv_PlantDetails"]/tbody/tr[3]/td[2]""")
                flatDoorBlock2 = flatDoorBlock2.text
            except:
                pass

            try:
                serialNumberloc1 = self.driver.find_element_by_xpath("""//*[@id="gv_PlantDetails"]/tbody/tr[2]/td[1]/span""")
                serialNumberloc1 = serialNumberloc1.text
            except:
                pass
            try:
                serialNumberloc2 = self.driver.find_element_by_xpath("""//*[@id="gv_PlantDetails"]/tbody/tr[3]/td[1]/span""")
                serialNumberloc2 = serialNumberloc2.text
            except:
                pass

            try:
                stateloc1 = self.driver.find_element_by_xpath("""//*[@id="gv_PlantDetails"]/tbody/tr[2]/td[8]""")
                stateloc1 = stateloc1.text
            except:
                pass
            try:
                stateloc2 = self.driver.find_element_by_xpath("""//*[@id="gv_PlantDetails"]/tbody/tr[3]/td[8]""")
                stateloc2 = stateloc2.text
            except:
                pass

            try:
                if len(nic2Digit1) > 0:
                    Be1 = {}
                    Be1['activityType'] = activityType1
                    Be1['addedOn'] = addedOn1
                    Be1['nic2Digit'] = nic2Digit1
                    Be1['nic4Digit'] = nic4Digit1
                    Be1['nic5Digit'] = nic5Digit1
                    Be1['serialNumber'] = serialNumber1

                else:
                    Be1 = {}
            except:
                Be1 = {}
                pass
            try:
                if len(nic2Digit2) > 0:
                    Be2 = {}
                    Be2['activityType'] = activityType2
                    Be2['addedOn'] = addedOn2
                    Be2['nic2Digit'] = nic2Digit2
                    Be2['nic4Digit'] = nic4Digit2
                    Be2['nic5Digit'] = nic5Digit2
                    Be2['serialNumber'] = serialNumber2

                else:
                    Be2 = {}
            except:
                Be2 = {}
                pass
            try:
                if len(nic2Digit3) > 0:
                    Be3 = {}
                    Be3['activityType'] = activityType3
                    Be3['addedOn'] = addedOn3
                    Be3['nic2Digit'] = nic2Digit3
                    Be3['nic4Digit'] = nic4Digit3
                    Be3['nic5Digit'] = nic5Digit3
                    Be3['serialNumber'] = serialNumber3

                else:
                    Be3 = {}
            except:
                Be3 = {}
                pass
            try:
                if len(nic2Digit4) > 0:
                    Be4 = {}
                    Be4['activityType'] = activityType4
                    Be4['addedOn'] = addedOn4
                    Be4['nic2Digit'] = nic2Digit4
                    Be4['nic4Digit'] = nic4Digit4
                    Be4['nic5Digit'] = nic5Digit4
                    Be4['serialNumber'] = serialNumber4

                else:
                    Be4 = {}
            except:
                Be4 = {}
                pass
            try:
                if len(nic2Digit5) > 0:
                    Be5 = {}
                    Be5['activityType'] = activityType5
                    Be5['addedOn'] = addedOn5
                    Be5['nic2Digit'] = nic2Digit5
                    Be5['nic4Digit'] = nic4Digit5
                    Be5['nic5Digit'] = nic5Digit5
                    Be5['serialNumber'] = serialNumber6

                else:
                    Be5 = {}
            except:
                Be5 = {}
                pass
            try:
                if len(nic2Digit6) > 0:
                    Be6 = {}
                    Be6['activityType'] = activityType6
                    Be6['addedOn'] = addedOn6
                    Be6['nic2Digit'] = nic2Digit6
                    Be6['nic4Digit'] = nic4Digit6
                    Be6['nic5Digit'] = nic5Digit6
                    Be6['serialNumber'] = serialNumber7

                else:
                    Be6 = {}
            except:
                Be6 = {}
                pass
            try:
                if len(nic2Digit7) > 0:
                    Be7 = {}
                    Be7['activityType'] = activityType7
                    Be7['addedOn'] = addedOn7
                    Be7['nic2Digit'] = nic2Digit7
                    Be7['nic4Digit'] = nic4Digit7
                    Be7['nic5Digit'] = nic5Digit7
                    Be7['serialNumber'] = serialNumber8

                else:
                    Be7 = {}
            except:
                Be7 = {}
                pass
            try:
                if len(nic2Digit8) > 0:
                    Be8 = {}
                    Be8['activityType'] = activityType8
                    Be8['addedOn'] = addedOn8
                    Be8['nic2Digit'] = nic2Digit8
                    Be8['nic4Digit'] = nic4Digit8
                    Be8['nic5Digit'] = nic5Digit8
                    Be8['serialNumber'] = serialNumber9

                else:
                    Be8 = {}
            except:
                Be8 = {}
                pass
            try:
                if len(nic2Digit9) > 0:
                    Be9 = {}
                    Be9['activityType'] = activityType9
                    Be9['addedOn'] = addedOn9
                    Be9['nic2Digit'] = nic2Digit9
                    Be9['nic4Digit'] = nic4Digit9
                    Be9['nic5Digit'] = nic5Digit9
                    Be9['serialNumber'] = serialNumber10

                else:
                    Be9 = {}
            except:
                Be9 = {}
                pass
            try:
                if len(flatDoorBlock1) > 0:
                    Ne1 = {}
                    Ne1['areaLocality'] = areaLocality1
                    Ne1['city'] = city1
                    Ne1['district'] = district1
                    Ne1['flatDoorBlock'] = flatDoorBlock1
                    Ne1['pin'] = pin1
                    Ne1['premisesBuilding'] = premisesBuilding1
                    Ne1['roadStreetLane'] = roadStreetLane1
                    Ne1['serialNumber'] = serialNumberloc1
                    Ne1['state'] = stateloc1

                else:
                    Ne1 = {}
            except:
                Ne1 = {}
                pass

            try:
                if len(flatDoorBlock2) > 0:
                    Ne2 = {}
                    Ne2['areaLocality'] = areaLocality2
                    Ne2['city'] = city2
                    Ne2['district'] = district2
                    Ne2['flatDoorBlock'] = flatDoorBlock2
                    Ne2['pin'] = pin2
                    Ne2['premisesBuilding'] = premisesBuilding2
                    Ne2['roadStreetLane'] = roadStreetLane2
                    Ne2['serialNumber'] = serialNumberloc2
                    Ne2['state'] = stateloc2

                else:
                    Ne2 = {}
            except:
                Ne2 = {}
                pass

            dic = {}
            dic["appliedDate"] = appliedDate
            dic["dateOfCommencement"] = dateOfCommencement
            dic["dicName"] = dicName
            dic["enterpriseCode"] = enterpriseCode
            dic["enterpriseType"] = enterpriseType
            dic["majorActivity"] = majorActivity
            dic["modifiedDate"] = modifiedDate
            dic["nameOfEnterprise"] = nameOfEnterprise
            dic["socialCategory"] = socialCategory
            dic["state"] = state
            dic["uamNumber"] = uamNumber
            dic["uamValidityMessage"] = uamValidityMessage

            a = [Be1, Be2, Be3, Be4, Be5, Be6, Be7, Be8, Be9]
            dic["nationalIndustryClassification"]  = [d for d in a if any(d.values())]
            b = [Ne1, Ne2]
            dic['locationOfPlantDetails'] = [d for d in b if any(d.values())]

            self.logStatus("info", "Scrapping completed", self.takeScreenshot())
            message = "Successfully Completed."
            code = "SRC001"
            dic = {"data": dic, "responseCode": code, "responseMessage": message}
            return dic

    def aadharUdyog_response(self,uamNumber):

        dic = {}

        try:
            self.logStatus("info", "opening driver page")
            dic = self.generate_AadharUdyog(uamNumber)

        except Exception as e:
            print(e)

            self.logStatus("critical", "Captcha error retrying")
            try:
                self.logStatus("info", "opening driver page")
                dic = self.generate_AadharUdyog(uamNumber)



            except Exception as e:
                print(e)
                self.logStatus("critical", "Captcha error retrying")
                try:
                    self.logStatus("info", "opening driver page")
                    dic = self.generate_AadharUdyog(uamNumber)

                except Exception as e:
                    try:
                        hhf = self.driver.find_element_by_xpath("""// *[ @ id = "ctl00_ContentPlaceHolder1_lblCaptcha"]""").text
                        if hhf == "Incorrect verification code. Please try again.":
                            dic = {}
                            message = "Unable To Process. Please Reach Out To Support."
                            code = "EUP007"
                            dic = {"data": "null", "responseCode": code, "responseMessage": message}
                            self.logStatus("info", "Contact support")
                            return dic
                    except:
                        pass


                    message = "No Information Found."
                    #fgdfd
                    code = "ENI004"
                    self.logStatus("info", "No Info Found")
                    dic = {"data": "null", "responseCode": code, "responseMessage": message}

        self.logStatus("info", "json convert")

        return dic











#if __name__ == '__main__':
#
 #   v = aadharudyog(refid="testing2", env = 'prod')
  #  data = v.aadharUdyog_response(uamNumber = 'GJ10B0008577')
  #  print(data)


