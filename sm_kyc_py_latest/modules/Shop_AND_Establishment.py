import json
import os
import time
import pandas as pd
import pdfplumber
import uuid
from pprint import pprint
from selenium.webdriver.common.action_chains import ActionChains
import boto3
from botocore.exceptions import ClientError



from modules.db import DB
from modules.utils import GcpOcr
import uuid
from pprint import pprint
#sfcsdcsd
import boto3
from botocore.exceptions import ClientError
from google.cloud import vision

from modules.db import DB
from modules.utils import GcpOcr
from selenium.webdriver.support.ui import Select
#from webdriver_manager.chrome import ChromeDriverManager



class Shopestablished:

    def __init__(self,refid,env = "prod"):

        credential_path = r"vision_api_token.json"
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = credential_path
      #  os.environ['DISPLAY'] = ':0'
       # os.environ['XAUTHORITY'] = '/run/user/1000/gdm/Xauthority'
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
        self.FILE_NAME1 = "screenshot_u.png"




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
                                 'Shop and Establishment', self.env, screenshot)
        print(f"{level}: {message}, screenshot: {screenshot}")

    def generate_Shop(self,licenseNumber,state):


        if state == 'West Bengal':
            from selenium import webdriver

            from selenium.webdriver.common.action_chains import ActionChains
            from selenium.webdriver.chrome.options import Options
          #  from webdriver_manager.chrome import ChromeDriverManager
            chrome_options = Options()
            import os
            # preferences = {
            #    "profile.default_content_settings.popups": 0,
            #   "download.default_directory": os.getcwd() + os.path.sep,
            #  "directory_upgrade": True
            # }
            preferences = {
                "profile.default_content_settings.popups": 0,
                "download.default_directory": "/usr/local/bin//",
                "directory_upgrade": True
            }

            chrome_options.add_experimental_option('prefs', preferences)
            # prefs = {"download.default_directory": r"C:\Users\IT Resurgent\PycharmProjects\sm_kyc_py_latest\modules"}
            # chrome_options.add_experimental_option("prefs", prefs)
            chrome_options.add_argument("--disable-extensions")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--disable-extension")
            chrome_options.add_argument("no-sandbox")
            chrome_options.add_argument("--headless")
            chrome_options.headless = True

            self.driver = webdriver.Chrome("/usr/local/bin/chromedriver", options=chrome_options)

            self.driver.maximize_window()
            start_url = "https://wbshopsonline.gov.in/shop/report/shops_establishments"
            try:
                self.logStatus("info", "Opening website")
                self.driver.get(start_url)
                r = 1
                self.makeDriverDirs()
                self.logStatus("info", "getting webpage", self.takeScreenshot())
                try:
                    #time.sleep(1)
                    self.driver.find_element_by_xpath("""//*[@id="doc_form"]/div[1]""")
                except:
                    r =2
            except Exception as e:
                r = 2
            if r == 2:
                message = "Unable To Process. Please Reach Out To Support."
                code = "EUP007"
                dic = {"data": "null", "responseCode": code, "responseMessage": message}
                self.logStatus("info", "Contact support")
                return dic
            if r == 1:

                try:
                    self.driver.find_element_by_xpath("""// *[ @ id = "registration_no_search"]""").click()
                    self.driver.find_element_by_xpath("""// *[ @ id = "registration_no_search"]""").send_keys(licenseNumber)
                    self.driver.find_element_by_xpath("""//*[@id="doc_form"]/input[4]""").click()
                except:
                    pass
                serialNumber = self.driver.find_element_by_xpath("""// *[ @ id = "shop_table"] / tbody / tr[1] / td[1]""")
                serialNumber = serialNumber.text
                shopEstablishmentName = self.driver.find_element_by_xpath("""// *[ @ id = "shop_table"] / tbody / tr[1] / td[2]""")
                shopEstablishmentName = shopEstablishmentName.text

                registrationNumberLicenseNumber = self.driver.find_element_by_xpath("""//*[@id="shop_table"]/tbody/tr[1]/td[3]""")
                registrationNumberLicenseNumber = registrationNumberLicenseNumber.text
                registrationNumberLicenseNumber = registrationNumberLicenseNumber.split("Reg. No.:")
                registrationNumberLicenseNumber = registrationNumberLicenseNumber[1]
                registrationNumberLicenseNumber = registrationNumberLicenseNumber.split("Dt.:")


                x = registrationNumberLicenseNumber[1]
                x = x.split("\n")
                y = x[1].split("Upto:")
                certificateValidUpTo = y[1]
                print(certificateValidUpTo)
                from datetime import datetime
                date_obj = datetime.strptime(certificateValidUpTo, ' %d/%m/%Y')
                certificateValidUpTo = date_obj.strftime('%d-%b-%Y')
                dateOfCommencementApplicationDate = x[0]
                print(dateOfCommencementApplicationDate)
                from datetime import datetime
                date_obj = datetime.strptime(dateOfCommencementApplicationDate, ' %d/%m/%Y')
                dateOfCommencementApplicationDate = date_obj.strftime('%d-%b-%Y')
                registrationNumberLicenseNumber = registrationNumberLicenseNumber[0]

                print(registrationNumberLicenseNumber)

                shopEstablishmentAddress = self.driver.find_element_by_xpath("""//*[@id="shop_table"]/tbody/tr[1]/td[4]""")
                shopEstablishmentAddress = shopEstablishmentAddress.text
                shopEstablishmentAddress = shopEstablishmentAddress.replace("\n"," ")

                category = ''
                natureOfBusinessBusinessType = ''
                contactNumber = ''
                areaOfCircle = ''
                emailAddress =  ''
                employerOwnerName = ''
                district = ''
                applyFor = ''
                currentStatusCertificateStatus = ''
                remarkReason = ''
                fatherHusbandName = ''
                actName = ''
                ageOfEmployer = ''
                numberOfEmployees = ''
                latestRegistrationRenewalCertificate = ''
                previousRegistrationRenewalCertificate = ''
                state = 'West Bengal'


                dic = {}
                dic["shopEstablishmentAddress"] = shopEstablishmentAddress
                dic["shopEstablishmentName"] = shopEstablishmentName
                dic["registrationNumberLicenseNumber"] = registrationNumberLicenseNumber
                dic["category"] = category
                dic["natureOfBusinessBusinessType"] = natureOfBusinessBusinessType
                dic["serialNumber"] = serialNumber
                dic["contactNumber"] = contactNumber
                dic["areaOfCircle"] = areaOfCircle
                dic["emailAddress"] = emailAddress
                dic["certificateValidUpTo"] = certificateValidUpTo
                dic["employerOwnerName"] = employerOwnerName
                dic["district"] = district
                dic["applyFor"] = applyFor
                dic["currentStatusCertificateStatus"] = currentStatusCertificateStatus
                dic["remarkReason"] = remarkReason
                dic["fatherHusbandName"] = fatherHusbandName
                dic["actName"] = actName
                dic["ageOfEmployer"] = ageOfEmployer
                certificateDate = ""
                dic["certificateDate"] = certificateDate
                dic["numberOfEmployees"] = numberOfEmployees
                dic["latestRegistrationRenewalCertificate"] = latestRegistrationRenewalCertificate
                dic["previousRegistrationRenewalCertificate"] = previousRegistrationRenewalCertificate
                dic["dateOfCommencementApplicationDate"] = dateOfCommencementApplicationDate
                dic["state"] = state
                self.logStatus("info", "Scrapping completed", self.takeScreenshot())
                message = "Successfully Completed."
                code = "SRC001"
                dic = {"data": dic, "responseCode": code, "responseMessage": message}
                return dic

        if state == 'Madhya Pradesh':
            from selenium import webdriver

            from selenium.webdriver.common.action_chains import ActionChains
            from selenium.webdriver.chrome.options import Options
          #  from webdriver_manager.chrome import ChromeDriverManager
            chrome_options = Options()
            import os
            # preferences = {
            #    "profile.default_content_settings.popups": 0,
            #   "download.default_directory": os.getcwd() + os.path.sep,
            #  "directory_upgrade": True
            # }
            preferences = {
                "profile.default_content_settings.popups": 0,
                "download.default_directory": "/usr/local/bin//",
                "directory_upgrade": True
            }

            chrome_options.add_experimental_option('prefs', preferences)
            # prefs = {"download.default_directory": r"C:\Users\IT Resurgent\PycharmProjects\sm_kyc_py_latest\modules"}
            # chrome_options.add_experimental_option("prefs", prefs)
            chrome_options.add_argument("--disable-extensions")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--disable-extension")
            chrome_options.add_argument("no-sandbox")
            chrome_options.add_argument("--headless")
            chrome_options.headless = True

            self.driver = webdriver.Chrome("/usr/local/bin/chromedriver", options=chrome_options)

            self.driver.maximize_window()

            start_url = "http://labour.mp.gov.in/Est/public/KnowYourStatus.aspx"
            try:
                self.logStatus("info", "Opening website")
                self.driver.get(start_url)
                r = 1
                self.makeDriverDirs()
                self.logStatus("info", "getting webpage", self.takeScreenshot())
                try:
                    # time.sleep(1)
                    self.driver.find_element_by_xpath("""//*[@id="ctl00_ContentEstab_lblOldRegNo"]""")
                except:
                    r = 2
            except Exception as e:
                r = 2
            if r == 2:
                message = "Unable To Process. Please Reach Out To Support."
                code = "EUP007"
                dic = {"data": "null", "responseCode": code, "responseMessage": message}
                self.logStatus("info", "Contact support")
                return dic

            if r == 1:

                import io
                import os
                from google.cloud import vision
                import time
                import io
                self.driver.find_element_by_xpath("""//*[@id="ctl00_ContentEstab_txtRegNo"]""").click()
                self.driver.find_element_by_xpath("""//*[@id="ctl00_ContentEstab_txtRegNo"]""").send_keys(licenseNumber)
                self.driver.find_element_by_xpath("""//*[@id="aspnetForm"]/div[5]/div/div[2]/div/table/tbody/tr[2]/td/div/div[2]/input""").click()
                self.driver.find_element_by_xpath("""/html/body/form/div[5]/div/div[2]/div/table/tbody/tr[2]/td/div/div[1]/img""").screenshot('captcha.png')
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
                self.driver.find_element_by_xpath("""//*[@id="aspnetForm"]/div[5]/div/div[2]/div/table/tbody/tr[2]/td/div/div[2]/input""").send_keys(k)
                self.driver.find_element_by_xpath("""/html/body/form/div[5]/div/div[2]/div/table/tbody/tr[3]/td/input[1]""").click()
                try:
                    sname = str(k) + '.png'
                    screenshotName = os.path.join(self.screenshotDir, f"{sname}")
                    self.driver.find_element_by_xpath("""//*[@id="captcha"]""").screenshot(screenshotName)
                    self.uploadToS3(os.path.join(screenshotName), 'Shop_MadhyaPradesh/' + sname)
                except:
                    pass
                category = ''
                natureOfBusinessBusinessType = ''
                contactNumber = ''
                areaOfCircle = ''
                emailAddress = ''
                employerOwnerName = ''
                district = ''
                applyFor = ''
                currentStatusCertificateStatus = ''
                dateOfCommencementApplicationDate = ''
                remarkReason = ''
                fatherHusbandName = ''
                actName = ''
                ageOfEmployer = ''
                certificateValidUpTo = ''
                numberOfEmployees = ''
                registrationNumberLicenseNumber = ''
                serialNumber = ''
                latestRegistrationRenewalCertificate = ''
                previousRegistrationRenewalCertificate = ''
                state = 'Madhya Pradesh'
                shopEstablishmentName = self.driver.find_element_by_xpath("""//*[@id="ctl00_ContentEstab_lblEstName"]""")
                shopEstablishmentName = shopEstablishmentName.text
                employerOwnerName = self.driver.find_element_by_xpath("""//*[@id="ctl00_ContentEstab_lblOwner"]""")
                employerOwnerName = employerOwnerName.text
                district = self.driver.find_element_by_xpath("""//*[@id="ctl00_ContentEstab_lblDist"]""")
                district = district.text
                shopEstablishmentAddress = self.driver.find_element_by_xpath("""//*[@id="ctl00_ContentEstab_lblAddress"]""")
                shopEstablishmentAddress = shopEstablishmentAddress.text
                applyFor = self.driver.find_element_by_xpath("""//*[@id="ctl00_ContentEstab_lblApply"]""")
                applyFor = applyFor.text
                natureOfBusinessBusinessType = self.driver.find_element_by_xpath("""//*[@id="ctl00_ContentEstab_lblBType"]""")
                natureOfBusinessBusinessType = natureOfBusinessBusinessType.text
                currentStatusCertificateStatus = self.driver.find_element_by_xpath("""//*[@id="ctl00_ContentEstab_lblStatus"]""")
                currentStatusCertificateStatus = currentStatusCertificateStatus.text
                registrationNumberLicenseNumber = licenseNumber
                try:
                    remarkReason =  self.driver.find_element_by_xpath("""//*[@id="ctl00_ContentEstab_txtRemark"]""")
                    remarkReason = remarkReason.text
                except:
                    remarkReason = ""
                dic = {}
                dic["shopEstablishmentAddress"] = shopEstablishmentAddress
                dic["shopEstablishmentName"] = shopEstablishmentName
                dic["registrationNumberLicenseNumber"] = registrationNumberLicenseNumber
                dic["category"] = category
                dic["natureOfBusinessBusinessType"] = natureOfBusinessBusinessType
                dic["serialNumber"] = serialNumber
                dic["contactNumber"] = contactNumber
                dic["areaOfCircle"] = areaOfCircle
                dic["emailAddress"] = emailAddress
                dic["certificateValidUpTo"] = certificateValidUpTo
                dic["employerOwnerName"] = employerOwnerName
                dic["district"] = district
                dic["applyFor"] = applyFor
                dic["currentStatusCertificateStatus"] = currentStatusCertificateStatus
                dic["remarkReason"] = remarkReason
                dic["fatherHusbandName"] = fatherHusbandName
                certificateDate = ""
                dic["certificateDate"] = certificateDate
                dic["actName"] = actName
                dic["ageOfEmployer"] = ageOfEmployer
                dic["numberOfEmployees"] = numberOfEmployees
                dic["latestRegistrationRenewalCertificate"] = latestRegistrationRenewalCertificate
                dic["previousRegistrationRenewalCertificate"] = previousRegistrationRenewalCertificate
                dic["dateOfCommencementApplicationDate"] = dateOfCommencementApplicationDate
                dic["state"] = state
                self.logStatus("info", "Scrapping completed", self.takeScreenshot())
                message = "Successfully Completed."
                code = "SRC001"
                dic = {"data": dic, "responseCode": code, "responseMessage": message}
                return dic

        if state == 'Haryana':
            from selenium import webdriver

            from selenium.webdriver.common.action_chains import ActionChains
            from selenium.webdriver.chrome.options import Options
            # from webdriver_manager.chrome import ChromeDriverManager
            chrome_options = Options()
            import os
            # preferences = {
            #    "profile.default_content_settings.popups": 0,
            #   "download.default_directory": os.getcwd() + os.path.sep,
            #  "directory_upgrade": True
            # }
            preferences = {
                "profile.default_content_settings.popups": 0,
                "download.default_directory": "/usr/local/bin//",
                "directory_upgrade": True
            }

            chrome_options.add_experimental_option('prefs', preferences)
            # prefs = {"download.default_directory": r"C:\Users\IT Resurgent\PycharmProjects\sm_kyc_py_latest\modules"}
            # chrome_options.add_experimental_option("prefs", prefs)
            chrome_options.add_argument("--disable-extensions")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--disable-extension")
            chrome_options.add_argument("no-sandbox")
           # chrome_options.add_argument("--headless")
           # chrome_options.headless = True

            self.driver = webdriver.Chrome("/usr/local/bin/chromedriver", options=chrome_options)

            self.driver.maximize_window()

            start_url = "https://hrylabour.gov.in/shops/front/searchResultShops"
            try:
                self.logStatus("info", "Opening website")
                self.driver.get(start_url)
                r = 1
                self.makeDriverDirs()
                self.logStatus("info", "getting webpage", self.takeScreenshot())
                try:
                    # time.sleep(1)
                    self.driver.find_element_by_xpath("""/html/body/div/section[1]/div/div/aside/div[2]/form/p""")
                except:
                    r = 2
            except Exception as e:
                r = 2

            if r == 1:
                category = ''
                natureOfBusinessBusinessType = ''
                contactNumber = ''
                areaOfCircle = ''
                emailAddress = ''
                employerOwnerName = ''
                district = ''
                applyFor = ''
                currentStatusCertificateStatus = ''
                dateOfCommencementApplicationDate = ''
                remarkReason = ''
                fatherHusbandName = ''
                actName = ''
                ageOfEmployer = ''
                certificateValidUpTo = ''
                numberOfEmployees = ''
                registrationNumberLicenseNumber = ''
                serialNumber = ''
                latestRegistrationRenewalCertificate = ''
                previousRegistrationRenewalCertificate = ''
                state = 'Haryana'
                print("scra")


                self.driver.find_element_by_xpath(
                    """/html/body/div/section[1]/div/div/aside/div[2]/form/p/input""").click()
                self.driver.find_element_by_xpath(
                    """/html/body/div/section[1]/div/div/aside/div[2]/form/p/input""").send_keys(licenseNumber)
                self.driver.find_element_by_xpath(
                    """/html/body/div/section[1]/div/div/aside/div[2]/form/button""").click()
            #    import pyautogui

              #  pyautogui.press('enter')
               # import time
                #time.sleep(4)
               # pyautogui.press('down')
               # pyautogui.press('down')
               # pyautogui.press('down')
               # pyautogui.press('down')
               # pyautogui.press('down')
               # pyautogui.press('down')


                import time
                time.sleep(2)
                serialNumber = self.driver.find_element_by_xpath("""/html/body/div/section[1]/div/div/aside/div[2]/div/table/tbody/tr[2]/td[1]""")
                serialNumber = serialNumber.text
                registrationNumberLicenseNumber = self.driver.find_element_by_xpath("""/html/body/div/section[1]/div/div/aside/div[2]/div/table/tbody/tr[2]/td[2]""")

                registrationNumberLicenseNumber = registrationNumberLicenseNumber.text
                shopEstablishmentName = self.driver.find_element_by_xpath("""/html/body/div/section[1]/div/div/aside/div[2]/div/table/tbody/tr[2]/td[3]""")
                shopEstablishmentName = shopEstablishmentName.text
                shopEstablishmentAddress =self.driver.find_element_by_xpath("""/html/body/div/section[1]/div/div/aside/div[2]/div/table/tbody/tr[2]/td[4]""")
                shopEstablishmentAddress = shopEstablishmentAddress.text
                shopEstablishmentAddress = shopEstablishmentAddress.replace("\n", " ")
                areaOfCircle = self.driver.find_element_by_xpath("""/html/body/div/section[1]/div/div/aside/div[2]/div/table/tbody/tr[2]/td[5]""")
                areaOfCircle = areaOfCircle.text
                dateOfCommencementApplicationDate = self.driver.find_element_by_xpath("""/html/body/div/section[1]/div/div/aside/div[2]/div/table/tbody/tr[2]/td[6]""")
                dateOfCommencementApplicationDate = dateOfCommencementApplicationDate.text
                try:
                    from datetime import datetime
                    date_obj = datetime.strptime(dateOfCommencementApplicationDate, '%d-%m-%Y')
                    dateOfCommencementApplicationDate = date_obj.strftime('%d-%b-%Y')
                except:
                    pass
                emailAddress = self.driver.find_element_by_xpath("""/html/body/div/section[1]/div/div/aside/div[2]/div/table/tbody/tr[2]/td[7]""")
                emailAddress = emailAddress.text
                currentStatusCertificateStatus = self.driver.find_element_by_xpath("""/html/body/div/section[1]/div/div/aside/div[2]/div/table/tbody/tr[2]/td[8]""")
                currentStatusCertificateStatus = currentStatusCertificateStatus.text
                certificateValidUpTo = self.driver.find_element_by_xpath("""/html/body/div/section[1]/div/div/aside/div[2]/div/table/tbody/tr[2]/td[9]""")
                certificateValidUpTo = certificateValidUpTo.text
                if registrationNumberLicenseNumber == licenseNumber:
                    dic = {}

                    dic["shopEstablishmentAddress"] = shopEstablishmentAddress
                    dic["shopEstablishmentName"] = shopEstablishmentName
                    dic["registrationNumberLicenseNumber"] = registrationNumberLicenseNumber
                    dic["category"] = category
                    dic["natureOfBusinessBusinessType"] = natureOfBusinessBusinessType
                    dic["serialNumber"] = serialNumber
                    dic["contactNumber"] = contactNumber
                    dic["areaOfCircle"] = areaOfCircle
                    dic["emailAddress"] = emailAddress
                    dic["certificateValidUpTo"] = certificateValidUpTo
                    dic["employerOwnerName"] = employerOwnerName
                    dic["district"] = district
                    dic["applyFor"] = applyFor
                    certificateDate = ""
                    dic["certificateDate"] = certificateDate
                    dic["currentStatusCertificateStatus"] = currentStatusCertificateStatus
                    dic["remarkReason"] = remarkReason
                    dic["fatherHusbandName"] = fatherHusbandName
                    dic["actName"] = actName
                    dic["ageOfEmployer"] = ageOfEmployer
                    dic["numberOfEmployees"] = numberOfEmployees
                    dic["latestRegistrationRenewalCertificate"] = latestRegistrationRenewalCertificate
                    dic["previousRegistrationRenewalCertificate"] = previousRegistrationRenewalCertificate
                    dic["dateOfCommencementApplicationDate"] = dateOfCommencementApplicationDate
                    dic["state"] = state
                    self.logStatus("info", "Scrapping completed", self.takeScreenshot())
                    message = "Successfully Completed."
                    code = "SRC001"
                    dic = {"data": dic, "responseCode": code, "responseMessage": message}
                    return dic
                else:
                    self.logStatus("info", "Site Error")
                    message = "No Information Found."
                    # fgdfd
                    code = "ENI004"
                    self.logStatus("info", "No Info Found")
                    dic = {"data": "null", "responseCode": code, "responseMessage": message}
                    return dic
            if r == 2:
                message = "Unable To Process. Please Reach Out To Support."
                code = "EUP007"
                dic = {"data": "null", "responseCode": code, "responseMessage": message}
                self.logStatus("info", "Contact support")
                return dic
        if state == 'Rajasthan':
            from selenium import webdriver

            from selenium.webdriver.common.action_chains import ActionChains
            from selenium.webdriver.chrome.options import Options
           # from webdriver_manager.chrome import ChromeDriverManager
            chrome_options = Options()
            import os
            # preferences = {
            #    "profile.default_content_settings.popups": 0,
            #   "download.default_directory": os.getcwd() + os.path.sep,
            #  "directory_upgrade": True
            # }
            preferences = {
                "profile.default_content_settings.popups": 0,
                "download.default_directory": "/usr/local/bin//",
                "directory_upgrade": True
            }

            chrome_options.add_experimental_option('prefs', preferences)
            # prefs = {"download.default_directory": r"C:\Users\IT Resurgent\PycharmProjects\sm_kyc_py_latest\modules"}
            # chrome_options.add_experimental_option("prefs", prefs)
            chrome_options.add_argument("--disable-extensions")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--disable-extension")
            chrome_options.add_argument("no-sandbox")
            chrome_options.add_argument("--headless")
            chrome_options.headless = True

            self.driver = webdriver.Chrome("/usr/local/bin/chromedriver", options=chrome_options)

            self.driver.maximize_window()
            start_url = "http://labour.rajasthan.gov.in/RulesShop.aspx"
            try:
                self.logStatus("info", "Opening website")
                self.driver.get(start_url)
                r = 1
                self.makeDriverDirs()
                self.logStatus("info", "getting webpage", self.takeScreenshot())
                try:
                    # time.sleep(1)
                    self.driver.find_element_by_xpath("""//*[@id="frm1"]/div[8]/table/tbody/tr[4]/td/div[1]/table/tbody/tr[1]/td[1]/h6""")
                except:
                    r = 2
            except Exception as e:
                r = 2
            category = ''
            natureOfBusinessBusinessType = ''
            contactNumber = ''
            areaOfCircle = ''
            emailAddress = ''
            employerOwnerName = ''
            shopEstablishmentAddress = ""
            district = ''
            applyFor = ''
            currentStatusCertificateStatus = ''
            dateOfCommencementApplicationDate = ''
            remarkReason = ''
            fatherHusbandName = ''
            shopEstablishmentName = ""
            actName = ''
            ageOfEmployer = ''
            certificateValidUpTo = ''
            numberOfEmployees = ''
            registrationNumberLicenseNumber = ''
            serialNumber = ''
            latestRegistrationRenewalCertificate = ''
            previousRegistrationRenewalCertificate = ''
            state = 'Rajasthan'
            self.driver.find_element_by_xpath("""//*[@id="txtRegistrationNo"]""").click()
            self.driver.find_element_by_xpath("""//*[@id="txtRegistrationNo"]""").send_keys(licenseNumber)
            self.driver.find_element_by_xpath("""//*[@id="btnSubmit"]""").click()
            actName = self.driver.find_element_by_xpath("""// *[ @ id = "lblActValue"]""")
            actName = actName.text
            registrationNumberLicenseNumber = self.driver.find_element_by_xpath("""// *[ @ id = "lblRegNoValue"]""")
            registrationNumberLicenseNumber = registrationNumberLicenseNumber.text
            dateOfCommencementApplicationDate = self.driver.find_element_by_xpath("""// *[ @ id = "lblRegDateValue"]""")
            dateOfCommencementApplicationDate = dateOfCommencementApplicationDate.text
            try:
                from datetime import datetime
                date_obj = datetime.strptime(dateOfCommencementApplicationDate, '%d/%m/%Y')
                dateOfCommencementApplicationDate = date_obj.strftime('%d-%b-%Y')
            except:
                pass
            employerOwnerName = self.driver.find_element_by_xpath("""// *[ @ id = "lblNameValue"]""")
            employerOwnerName = employerOwnerName.text
            try:
                employerOwnerNamegh = employerOwnerName.replace(" ", "")
                if employerOwnerNamegh.isalpha() == True:
                    employerOwnerName = employerOwnerName
                else:
                    employerOwnerName = "Unspecified Output"
            except:
                pass

            currentStatusCertificateStatus = self.driver.find_element_by_xpath("""//*[@id="lblStatusValue"]""")
            currentStatusCertificateStatus = currentStatusCertificateStatus.text
            try:
                certificateValidUpTo = self.driver.find_element_by_xpath("""//*[@id="lblExpiryDate"]""")
                certificateValidUpTo = certificateValidUpTo.text
                try:
                    from datetime import datetime
                    date_obj = datetime.strptime(certificateValidUpTo, '%d/%m/%Y')
                    certificateValidUpTo = date_obj.strftime('%d-%b-%Y')
                except:
                    pass
            except:
                certificateValidUpTo = ""
                pass

            if len(registrationNumberLicenseNumber.strip()) == len(licenseNumber):
                if registrationNumberLicenseNumber == licenseNumber:
                    dic = {}
                    dic["shopEstablishmentAddress"] = shopEstablishmentAddress
                    dic["shopEstablishmentName"] = shopEstablishmentName
                    dic["registrationNumberLicenseNumber"] = registrationNumberLicenseNumber
                    dic["category"] = category
                    dic["natureOfBusinessBusinessType"] = natureOfBusinessBusinessType
                    dic["serialNumber"] = serialNumber
                    dic["contactNumber"] = contactNumber
                    dic["areaOfCircle"] = areaOfCircle
                    dic["emailAddress"] = emailAddress
                    dic["certificateValidUpTo"] = certificateValidUpTo
                    dic["employerOwnerName"] = employerOwnerName
                    dic["district"] = district
                    dic["applyFor"] = applyFor
                    dic["currentStatusCertificateStatus"] = currentStatusCertificateStatus
                    dic["remarkReason"] = remarkReason
                    dic["fatherHusbandName"] = fatherHusbandName
                    certificateDate = ""
                    dic["certificateDate"] = certificateDate
                    dic["actName"] = actName
                    dic["ageOfEmployer"] = ageOfEmployer
                    dic["numberOfEmployees"] = numberOfEmployees
                    dic["latestRegistrationRenewalCertificate"] = latestRegistrationRenewalCertificate
                    dic["previousRegistrationRenewalCertificate"] = previousRegistrationRenewalCertificate
                    dic["dateOfCommencementApplicationDate"] = dateOfCommencementApplicationDate
                    dic["state"] = state
                    self.logStatus("info", "Scrapping completed", self.takeScreenshot())
                    message = "Successfully Completed."
                    code = "SRC001"
                    dic = {"data": dic, "responseCode": code, "responseMessage": message}
                    return dic
                else:
                    self.logStatus("info", "Site Error")
                    message = "No Information Found."
                    # fgdfd
                    code = "ENI004"
                    self.logStatus("info", "No Info Found")
                    dic = {"data": "null", "responseCode": code, "responseMessage": message}
                    return dic
        def captchabreker():
            self.driver.find_element_by_xpath(
                """//*[@id="txtCaptcha2"]""").screenshot('captcha.png')

            import io
            import os
            from google.cloud import vision
            import time
            import io
            time.sleep(1)
            with io.open(os.path.join(self.FOLDER_PATH, self.FILE_NAME), 'rb') as image_file:
                content = image_file.read()

            image = vision.types.Image(content=content)
            response = self.client.text_detection(image=image)
            texts = response.text_annotations
            for text in texts:
                z = ('"{}"'.format(text.description))
            time.sleep(1)
            h = str(z).split('"')
            k = h[1]

            #print(k)
            self.driver.find_element_by_xpath("""/html/body/div[2]/form/div[2]/table/tbody/tr[3]/td[2]/input[2]""").click()
            self.driver.find_element_by_xpath("""/html/body/div[2]/form/div[2]/table/tbody/tr[3]/td[2]/input[2]""").send_keys(k)
            time.sleep(1)
            self.driver.find_element_by_xpath("""/html/body/div[2]/form/div[2]/table/tbody/tr[2]/td[3]/button""").click()

        if state == 'Telangana':
            #from pyvirtualdisplay import Display
            #display = Display(visible=0, size=(1366, 768))
            #display.start()
            #import pyautogui
           # import mouse
           # display.stop()
           # import os
            #os.environ['DISPLAY'] = ':0'
        #    os.environ['XAUTHORITY'] = '/run/user/1000/gdm/Xauthority'



           # from pyvirtualdisplay import Display
           # display = Display(visible=0, size=(1366, 768))
           # display.start()
          #  from pyvirtualdisplay import Display
           # display = Display(visible=0, size=(1366, 768))
            #display.start()
            category = ''
            natureOfBusinessBusinessType = ''
            contactNumber = ''
            areaOfCircle = ''
            emailAddress = ''
            employerOwnerName = ''
            shopEstablishmentAddress = ""
            district = ''
            applyFor = ''
            currentStatusCertificateStatus = ''
            dateOfCommencementApplicationDate = ''
            remarkReason = ''
            fatherHusbandName = ''
            shopEstablishmentName = ""
            actName = ''
            ageOfEmployer = ''
            certificateValidUpTo = ''
            numberOfEmployees = ''
            registrationNumberLicenseNumber = ''
            serialNumber = ''
            latestRegistrationRenewalCertificate = ''
            previousRegistrationRenewalCertificate = ''
            state = 'Telangana'
            from selenium import webdriver
       #     import os
           # os.environ['DISPLAY'] = ':0'

            from selenium.webdriver.common.action_chains import ActionChains
            from selenium.webdriver.chrome.options import Options
           # from webdriver_manager.chrome import ChromeDriverManager
            chrome_options = Options()
            import os
            # preferences = {
            #    "profile.default_content_settings.popups": 0,
            #   "download.default_directory": os.getcwd() + os.path.sep,
            #  "directory_upgrade": True
            # }
            preferences = {
                "profile.default_content_settings.popups": 0,
                "download.default_directory": "/usr/local/bin//",
                "directory_upgrade": True
            }

            chrome_options.add_experimental_option('prefs', preferences)
            # prefs = {"download.default_directory": r"C:\Users\IT Resurgent\PycharmProjects\sm_kyc_py_latest\modules"}
            # chrome_options.add_experimental_option("prefs", prefs)
            chrome_options.add_argument("--disable-extensions")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--disable-extension")
            chrome_options.add_argument("no-sandbox")
            chrome_options.add_argument("--headless")
            chrome_options.headless = True

            self.driver = webdriver.Chrome("/usr/local/bin/chromedriver", options=chrome_options)

            self.driver.maximize_window()
            start_url = "https://labour.telangana.gov.in"
            try:
                self.logStatus("info", "Opening website")

                self.driver.get(start_url)
                import time
                time.sleep(7)
                r = 1
                self.makeDriverDirs()
                self.logStatus("info", "getting webpage", self.takeScreenshot())
                try:
                    # time.sleep(1)
                    self.driver.find_element_by_xpath("""/html/body/header/div[2]/div/div/div/div[2]/h1/span/font/b""")
                except:
                    r = 2
            except Exception as e:
                r = 2
            import time
            self.driver.find_element_by_xpath("""//*[@id="sizer"]/div[2]/div[1]/div[1]/div[3]/div/div/div/div/a/h3""").click()
            time.sleep(2)
            self.driver.find_element_by_xpath("""//*[@id="crNumber"]""").click()
            self.driver.find_element_by_xpath("""//*[@id="crNumber"]""").send_keys(licenseNumber)



            import time
            time.sleep(1)
            captchabreker()
            import os


           # sname = str(k) + '.png'
           # screenshotName = os.path.join(self.screenshotDir, f"{sname}")
           # self.driver.find_element_by_xpath("""//*[@id="captcha"]""").screenshot(screenshotName)
           # self.uploadToS3(os.path.join(screenshotName), 'Shop_MadhyaPradesh/' + sname)
            G = 77
            try:
                Wrongdata = self.driver.find_element_by_xpath("""/ html / body / div[2] / form / div[4] / table / tbody / tr / td / b""")
                Wrongdata = Wrongdata.text
                if Wrongdata == "There is no Valid Certificate for the Number Quoted":
                    G = 1
                else:
                    G = 2
            except:
                G = 2
                pass
            if G == 1:
                self.logStatus("info", "Site Error")
                message = "No Information Found."
                # fgdfd
                code = "ENI004"
                self.logStatus("info", "There is no Valid Certificate for the Number Quoted")
                self.logStatus("info", "No Info Found")
                dic = {"data": "null", "responseCode": code, "responseMessage": message}
                return dic

            try:
                serialNumber = self.driver.find_element_by_xpath(
                    """//*[@id="sizer"]/div[2]/form/div[3]/table/tbody/tr[3]/td[1]""")
                serialNumber = serialNumber.text

            except:
                serialNumber = None
                try:
                    if serialNumber == None:
                        time.sleep(1)
                        captchabreker()
                    serialNumber = self.driver.find_element_by_xpath(
                        """//*[@id="sizer"]/div[2]/form/div[3]/table/tbody/tr[3]/td[1]""")
                    serialNumber = serialNumber.text

                except:
                    serialNumber = None
                    try:
                        if serialNumber == None:
                            time.sleep(1)
                            captchabreker()
                        serialNumber = self.driver.find_element_by_xpath(
                            """//*[@id="sizer"]/div[2]/form/div[3]/table/tbody/tr[3]/td[1]""")
                        serialNumber = serialNumber.text
                    except:
                        serialNumber = None
                        try:
                            if serialNumber == None:
                                time.sleep(1)
                                captchabreker()
                            serialNumber = self.driver.find_element_by_xpath(
                                """//*[@id="sizer"]/div[2]/form/div[3]/table/tbody/tr[3]/td[1]""")
                            serialNumber = serialNumber.text
                        except:
                            pass

                pass
            try:
                Wrongdata = self.driver.find_element_by_xpath("""/ html / body / div[2] / form / div[4] / table / tbody / tr / td / b""")
                Wrongdata = Wrongdata.text
                if Wrongdata == "There is no Valid Certificate for the Number Quoted":
                    G = 1
                else:
                    G = 2
            except:
                G = 2
                pass
            if G == 1:
                self.logStatus("info", "Site Error")
                message = "No Information Found."
                # fgdfd
                code = "ENI004"
                self.logStatus("info", "There is no Valid Certificate for the Number Quoted")
                self.logStatus("info", "No Info Found")
                dic = {"data": "null", "responseCode": code, "responseMessage": message}
                return dic

            window_before = self.driver.window_handles[0]
            window_before_title = self.driver.title
          #  x = 1
            i = 3
            date_checker=[]
            try:
                while i != 50999:
                    globals()["text" + str(i)] = self.driver.find_element_by_xpath(
                        """//*[@id="sizer"]/div[2]/form/div[3]/table/tbody/tr""" + str([i]) + """/td[4]/button""").get_attribute("onclick")

                    print("attribute ",globals()["text" + str(i)])

                    globals()["text" + str(i)] = globals()["text" + str(i)].split("openFile('")[1].split("')")[0]

                    url = "https://labour.telangana.gov.in/" + globals()["text" + str(i)]
                    print(url)

               # display.start()
                    time.sleep(5)

                    print("yha hu")
                    import requests
                    response = requests.get(url)
                    with open("/usr/local/bin/Ultra"+str(i)+".pdf", 'wb') as f:
                  #  with open('/usr/local/bin/Ultra45.pdf', 'wb') as f:
                        f.write(response.content)


                    print("yha complete")
                 #   pyautogui.moveTo(1340, 75)
                 #   pyautogui.click()
                 #   time.sleep(15)

                  #  pyautogui.moveTo(1250, 75)
                   # pyautogui.click()
                   # time.sleep(3)
                    #pyautogui.press('enter')

                    print("Download might have happened")
                    try:

                        # x = os.getcwd() + os.path.sep + "*.pdf"
                        #x = "/usr/local/bin//*.pdf"
                     #   x = "/usr/local/bin/Ultra45.pdf"
                       # x= "/usr/local/bin/Ultra45.pdf"
                        d = "/usr/local/bin/Ultra"+str(i)+".pdf"
                        with pdfplumber.open(d) as pdf:
                            data = ''.join([page.extract_text() for page in pdf.pages])

                    except Exception as e:
                        print("errorhu  ",e)
                    try:
                        globals()["date" + str(i)] = data.split("Renewed Date:")[1].split("\n")[0]
                        if len(globals()["date" + str(i)])>16:
                            globals()["date" + str(i)] = data.split("Renewed Date:")[1].split(" (")[0]
                    except:
                        globals()["date" + str(i)] = data.split("Signed Date:")[1].split("\n")[0]
                        if len(globals()["date" + str(i)]) > 16:
                            globals()["date" + str(i)] = data.split("Signed Date:")[1].split(" (")[0]
                    try:
                        globals()["date" + str(i)] = globals()["date" + str(i)].replace(" ","")
                        from datetime import datetime
                        date_obj = datetime.strptime(globals()["date" + str(i)], '%d/%m/%Y')
                        globals()["date" + str(i)] = date_obj.strftime('%Y-%m-%d')
                    except:
                        pass
                    datas__=str(globals()["date" + str(i)])
                    print("new date",datas__)
                    date_checker.append(datas__)

                    print(globals()["date" + str(i)])
                    i = i + 1
            except Exception as e:
                print(e)
                print(date_checker)

            df = pd.DataFrame({'Date': pd.to_datetime(date_checker)})
            latest = df['Date'].max()
            latest = str(latest)
            latest = latest.replace(" 00:00:00", "")
            latest = str(latest)
            print(latest)
            z = 0
            for i in date_checker:
                z = z + 1
                if i == latest:
                    print(latest)
                    break
                else:
                    continue
#y

            z = z + 2
            print("z hu ", z)
            gh = "/usr/local/bin/Ultra" + str(z) + ".pdf"
            with pdfplumber.open(gh) as pdf:
                data = ''.join([page.extract_text() for page in pdf.pages])
                try:
                    shopEstablishmentName = data.split("Name of Shop /Establishment :")[1].split("\n")[0]
                    shopEstablishmentName.replace(":", "")
                except:
                    shopEstablishmentName = data.split("Name of Shop / Establishment")[1].split("\n")[0]
                    shopEstablishmentName = shopEstablishmentName.replace(":","")
                print("huraaah")
                try:
                    date = data.split("Renewed Date:")[1].split("\n")[0]
                    if len(date) > 16:
                        date = data.split("Renewed Date:")[1].split(" (")[0]
                    print(date)
                    date = date.replace(" ", "")

                    from datetime import datetime
                    date_obj = datetime.strptime(date, '%d/%m/%Y')
                    date = date_obj.strftime('%d-%b-%Y')
                except:
                    date = data.split("Signed Date:")[1].split("\n")[0]
                    if len(date) > 16:
                        date = data.split("Signed Date:")[1].split(" (")[0]
                    print(date)
                    date = date.replace(" ", "")
                    from datetime import datetime
                    date_obj = datetime.strptime(date, '%d/%m/%Y')
                    date = date_obj.strftime('%d-%b-%Y')
                print(date)
                try:
                    shopEstablishmentAddress = data.split("Shop / Establishment Address :")[1].split("\n6")[0].strip()
                    try:
                        shopEstablishmentAddress = shopEstablishmentAddress.replace("\n", "")
                    except:
                        pass
                except:
                    shopEstablishmentAddress = ""






                ageOfEmployer = data.split("Age of Employer :")[1].split("\n")[0].strip()

                try:
                    fatherHusbandName = data.split("Father/Husband's Name :")[1].split("\n")[0].strip()
                except:
                    pass
                try:
                    employerOwnerName = data.split("Name of the Employer :")[1].split("\n")[0].strip()
                except:
                    pass
                try:
                    numberOfEmployees = data.split("Number of Employees :")[1].split("\n")[0].strip()
                except:
                    pass
                try:
                    natureOfBusinessBusinessType = data.split("Nature of Business :")[1].split("\n8")[0].strip()
                except:
                    natureOfBusinessBusinessType = ""
                try:
                    dateOfCommencementApplicationDate = data.split("Date of Commencement :")[1].split("\n")[0].strip()
                except:
                    dateOfCommencementApplicationDate = ""
                try:
                    from datetime import datetime
                    date_obj = datetime.strptime(dateOfCommencementApplicationDate, '%d/%m/%Y')
                    dateOfCommencementApplicationDate = date_obj.strftime('%d-%b-%Y')
                except:
                    pass
                try:
                    certificateDate = data.split(" with")[0].split(" on ")[1]
                    print(certificateDate," certificateDate")
                    certificateDate = certificateDate.replace(" ", "")
                    from datetime import datetime
                    date_obj = datetime.strptime(certificateDate, '%d/%m/%Y')
                    certificateDate = date_obj.strftime('%d-%b-%Y')
                except:
                    try:
                        certificateDate =  data.split("period from")[1].split("to")[0]
                        print(certificateDate, " certificateDateexcept")
                        certificateDate = certificateDate.replace(" ", "")
                        from datetime import datetime
                        date_obj = datetime.strptime(certificateDate, '%d/%m/%Y')
                        certificateDate = date_obj.strftime('%d-%b-%Y')

                    except:
                        certificateDate = ""
                        pass



            registrationNumberLicenseNumber = licenseNumber

            dic = {}
            dic["shopEstablishmentAddress"] = shopEstablishmentAddress
            dic["shopEstablishmentName"] = shopEstablishmentName
            dic["registrationNumberLicenseNumber"] = registrationNumberLicenseNumber
            dic["category"] = category
            dic["natureOfBusinessBusinessType"] = natureOfBusinessBusinessType
            dic["serialNumber"] = serialNumber
            dic["contactNumber"] = contactNumber
            dic["areaOfCircle"] = areaOfCircle
            dic["emailAddress"] = emailAddress
            dic["certificateValidUpTo"] = certificateValidUpTo
            dic["employerOwnerName"] = employerOwnerName
            dic["district"] = district
            dic["applyFor"] = applyFor
            dic["currentStatusCertificateStatus"] = currentStatusCertificateStatus
            dic["remarkReason"] = remarkReason
            dic["fatherHusbandName"] = fatherHusbandName
            dic["certificateDate"] = certificateDate
            dic["actName"] = actName
            dic["ageOfEmployer"] = ageOfEmployer
            dic["signedRenewedDate"] = date
            dic["numberOfEmployees"] = numberOfEmployees
            dic["latestRegistrationRenewalCertificate"] = latestRegistrationRenewalCertificate
            dic["previousRegistrationRenewalCertificate"] = previousRegistrationRenewalCertificate
            dic["dateOfCommencementApplicationDate"] = dateOfCommencementApplicationDate
            dic["state"] = "Telangana"
            self.logStatus("info", "Scrapping completed", self.takeScreenshot())
            message = "Successfully Completed."
            code = "SRC001"
            dic = {"data": dic, "responseCode": code, "responseMessage": message}
           # display.stop()
            return dic









            #parent_level_menu = self.driver.find_element_by_xpath("""//*[@id="icon"]/iron-icon""")
            #action.move_to_element(parent_level_menu).perform()
            #parent_level_menu.click()




    def Shopestablished_response(self,licenseNumber ,state):
        if state == "Haryana":
            from pyvirtualdisplay import Display
            display = Display(visible=0, size=(1366, 768))
            display.start()
            dic = {}
            try:
                self.logStatus("info", "Opening webpage")
                dic = self.generate_Shop(licenseNumber, state)
            except Exception as e:
                print(e)
                self.logStatus("critical", "timeout error retrying")
                try:
                    self.logStatus("info", "Opening webpage")
                    dic = self.generate_Shop(licenseNumber, state)
                except Exception as e:
                    print(len(e))
                    self.logStatus("critical", "timeout error retrying")
                    try:
                        self.logStatus("info", "Opening webpage")
                        dic = self.generate_Shop(licenseNumber, state)
                    except Exception as e:
                        print(len(e))
                        self.logStatus("critical", "no data found")
                        self.logStatus("info", "Site Error")
                        message = "No Information Found."
                        # fgdfd
                        code = "ENI004"
                        self.logStatus("info", "No Info Found")
                        dic = {"data": "null", "responseCode": code, "responseMessage": message}
                        display.stop()
                        return dic


        else:

            dic = {}
            try:
                self.logStatus("info", "Opening webpage")
                dic = self.generate_Shop(licenseNumber,state)
            except Exception as e:
                print(e)
                self.logStatus("critical", "timeout error retrying")
                try:
                    self.logStatus("info", "Opening webpage")
                    dic = self.generate_Shop(licenseNumber,state)
                except Exception as e:
                    print(e)
                    self.logStatus("critical", "timeout error retrying")
                    try:
                        self.logStatus("info", "Opening webpage")
                        dic = self.generate_Shop(licenseNumber,state)
                    except Exception as e:
                        print(e)
                        self.logStatus("critical", "no data found")
                        self.logStatus("info", "Site Error")
                        message = "No Information Found."
                        # fgdfd
                        code = "ENI004"
                        self.logStatus("info", "No Info Found")
                        dic = {"data": "null", "responseCode": code, "responseMessage": message}
                        return dic

        return dic




#if __name__ == '__main__':

 #   v = Shopestablished(refid="testing2", env = 'prod')
  #  data = v.Shopestablished_response(licenseNumber = 'SEA/RAN/ALO/BN/85940/2018',state = 'Telangana')
   # print(data)

#if __name__ == '__main__':

 #   v = Shopestablished(refid="testing2", env = 'prod')
  #  data = v.Shopestablished_response(licenseNumber = 'NX03561P2019000026',state = 'West Bengal')
   # print(data)
