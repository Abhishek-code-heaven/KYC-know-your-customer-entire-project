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

class IEC:

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
                                 'IEC_registration', self.env, screenshot)
        print(f"{level}: {message}, screenshot: {screenshot}")

    def breakcaptcha(self):
        import io
        import os
        from google.cloud import vision
        import time
        import io
        self.driver.find_element_by_xpath("""//*[@id="captcha"]""").screenshot('captcha.png')
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
            self.driver.find_element_by_xpath("""//*[@id="captcha"]""").screenshot(screenshotName)
            self.uploadToS3(os.path.join(screenshotName), 'IEC/' + sname)
        except:
            pass
        self.driver.find_element_by_xpath("""//*[@id="txt_Captcha"]""").click()

        self.driver.find_element_by_xpath("""//*[@id="txt_Captcha"]""").send_keys(k)
        time.sleep(1)
        self.driver.find_element_by_xpath("""// *[ @ id = "viewIEC1"]""").click()

    def generate_IEC(self,iecNumber,firmName):
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        import io
        import os
        import time

        from google.cloud import vision
        #from webdriver_manager.chrome import ChromeDriverManager
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
        self.driver.maximize_window()

        self.logStatus("info", "Driver created")

        try:
            self.driver.get("https://dgft.gov.in/CP/")
            r = 1
            try:

                cantreach =  self.driver.find_element_by_xpath("""// *[ @ id = "main-message"]""")
                cantreach = cantreach.text

                if cantreach == cantreach:
                    r = 2

            except:
                pass

            self.makeDriverDirs()
            self.logStatus("info", "IEC Verifier page opened", self.takeScreenshot())

        except Exception as e:

            self.logStatus("critical", "IEC page could not open contact support")
            r = 3
            print(r)

        try:
            self.driver.find_element_by_xpath("""// *[ @ id = "serivces"]""")
        except:
            r = 2
            pass

        if r == 3:
            message = "Information Source is Not Working"
            code = "EIS042"
            dic = {"data": "null", "responseCode": code, "responseMessage": message}
            self.logStatus("info", "Contact support")
            return dic
        elif r ==2:
            message = "Information Source is Not Working"
            code = "EIS042"
            dic = {"data": "null", "responseCode": code, "responseMessage": message}
            self.logStatus("info", "Contact support")
            return dic

        elif r == 1:
            import time
            try:
                self.driver.find_element_by_xpath("""//*[@id="serivces"]""").click()
                #// *[ @ id = "mainHeaderNav"] / ul / li[3] / ul / li[3] / a
                self.driver.find_element_by_xpath("""//*[@id="mainHeaderNav"]/ul/li[3]/ul/li[2]/a""").click()
                time.sleep(3)
                try:
                    self.driver.find_element_by_xpath("""//*[@id="mainSectionWrap"]/div[3]/div/div[2]/div[1]/div/a/div[2]/p""").click()
                except:
                    pass
                #self.driver.find_element_by_xpath("""//*[@id="content"]/div[3]/div/div[2]/div[1]/div/a/div[2]""").click()
                try:
                    self.driver.find_element_by_xpath("""// *[ @ id = "iecNo"]""").click()
                except Exception as e:
                    print(e)
                time.sleep(1)
                self.driver.find_element_by_xpath("""// *[ @ id = "iecNo"]""").send_keys(iecNumber)
                self.driver.find_element_by_xpath("""// *[ @ id = "entity"]""").click()
                self.driver.find_element_by_xpath("""// *[ @ id = "entity"]""").send_keys(firmName)
                try:
                    self.logStatus("info", "Trying captcha 1")
                    self.breakcaptcha()
                    time.sleep(1)
                    errorcode1 = self.driver.find_element_by_xpath("""//*[@id="incCaptcha"]""")
                    errorcode1 = errorcode1.text
                    if errorcode1 == 'Please enter valid captcha code':
                        self.driver.find_element_by_xpath("""//*[@id="txt_Captcha"]""").clear()
                        self.breakcaptcha()
                        self.logStatus("info", "Trying captcha 2")
                        errorcode2 = self.driver.find_element_by_xpath("""//*[@id="incCaptcha"]""")
                        errorcode2 = errorcode2.text
                        if errorcode2 == 'Please enter valid captcha code':
                            self.driver.find_element_by_xpath("""//*[@id="txt_Captcha"]""").clear()
                            self.breakcaptcha()
                            self.logStatus("info", "Trying captcha 3")
                        else:
                            pass

                except:
                    pass

            except:
                pass


            try:
                Noinfo = self.driver.find_element_by_xpath("""/ html / body / div[22] / div / div / div / div[1]""").text
                if Noinfo == "Details for this IEC Number is not available.":
                    x = 10
            except:

                pass

            try:

                caperror = self.driver.find_element_by_xpath("""// *[ @ id = "incCaptcha"]""")
                caperror = caperror.text
                if caperror == 'Please enter valid captcha code':
                    raise Exception
            except:
                pass
            time.sleep(3)
            x = 7
            try:
                iecNumber = self.driver.find_element_by_xpath("""//*[@id="iecdetails"]/div/div/div[1]/div[1]/div/p""")
                iecNumber = iecNumber.text
                self.logStatus("info", "Site Error")
                if len(iecNumber)!=10:
                    x =10
            except  Exception as e:
                pass

            if x == 10:
                self.logStatus("info", "Site Error")
                message = "No Information Found."
                # fgdfd
                code = "ENI004"
                self.logStatus("info", "No Info Found")
                dic = {"data": "null", "responseCode": code, "responseMessage": message}
                return dic

            else:
                self.logStatus("info", "starting scrapping")
                time.sleep(4)
                iecNumber = self.driver.find_element_by_xpath("""//*[@id="iecdetails"]/div/div/div[1]/div[1]/div/p""")
                iecNumber = iecNumber.text
                panNumber = self.driver.find_element_by_xpath("""//*[@id="iecdetails"]/div/div/div[1]/div[2]/div/p""")
                panNumber = panNumber.text
                dateOfBirthIncorporation = self.driver.find_element_by_xpath("""//*[@id="iecdetails"]/div/div/div[1]/div[3]/div/p""")
                dateOfBirthIncorporation = dateOfBirthIncorporation.text
                iecIssuanceDate = self.driver.find_element_by_xpath("""//*[@id="iecdetails"]/div/div/div[2]/div[1]/div/p""")
                iecIssuanceDate = iecIssuanceDate.text
                try:
                    from datetime import datetime
                    date_obj = datetime.strptime(iecIssuanceDate, '%d/%m/%Y')
                    iecIssuanceDate = date_obj.strftime('%d-%b-%Y')
                except:
                    pass

                iecStatus = self.driver.find_element_by_xpath("""//*[@id="iecdetails"]/div/div/div[2]/div[2]/div/p""")
                iecStatus = iecStatus.text
                delStatus = self.driver.find_element_by_xpath("""// *[ @ id = "iecdetails"] / div / div / div[2] / div[3] / div / p""")
                delStatus = delStatus.text
                iecCancelledDate = self.driver.find_element_by_xpath("""// *[ @ id = "iecdetails"] / div / div / div[3] / div[1] / div / p""")
                iecCancelledDate = iecCancelledDate.text
                iecSuspendedDate = self.driver.find_element_by_xpath("""// *[ @ id = "iecdetails"] / div / div / div[3] / div[2] / div / p""")
                iecSuspendedDate = iecSuspendedDate.text
                try:

                    from datetime import datetime
                    date_obj = datetime.strptime(iecSuspendedDate, '%d/%m/%Y')
                    iecSuspendedDate = date_obj.strftime('%d-%b-%Y')
                except:
                    pass

                fileDate = self.driver.find_element_by_xpath("""//*[@id="iecdetails"]/div/div/div[4]/div[2]/div/p""")
                fileDate = fileDate.text
                try:

                    from datetime import datetime
                    date_obj = datetime.strptime(fileDate, '%d/%m/%Y')
                    fileDate = date_obj.strftime('%d-%b-%Y')
                except:
                    pass
                dgftRaOffice = self.driver.find_element_by_xpath("""// *[ @ id = "iecdetails"] / div / div / div[4] / div[3] / div / p""")
                dgftRaOffice = dgftRaOffice.text
                natureOfConcernFirm = self.driver.find_element_by_xpath("""// *[ @ id = "iecdetails"] / div / div / div[5] / div[1] / div / p""")
                natureOfConcernFirm = natureOfConcernFirm.text
                categoryOfExporters = self.driver.find_element_by_xpath("""// *[ @ id = "iecdetails"] / div / div / div[5] / div[2] / div / p""")
                categoryOfExporters = categoryOfExporters.text
                firmName = self.driver.find_element_by_xpath("""// *[ @ id = "iecdetails"] / div / div / div[5] / div[3] / div / p""")
                firmName = firmName.text
                address = self.driver.find_element_by_xpath("""// *[ @ id = "iecdetails"] / div / div / div[6] / div[1] / div / p""")
                address = address.text
                fileNumber =  self.driver.find_element_by_xpath("""//*[@id="iecdetails"]/div/div/div[4]/div[1]/div/p """)
                fileNumber = fileNumber.text
                self.driver.find_element_by_xpath("""/ html / body / div[3] / div / div / a[1] / span / i""").click()

                try:
                    BranchCode1 = self.driver.find_element_by_xpath("""// *[ @ id = "branchTable"] / tbody / tr[1] / td[1]""")
                    BranchCode1 = BranchCode1.text
                except:
                    pass
                try:
                    BranchCode2 = self.driver.find_element_by_xpath("""//*[@id="branchTable"]/tbody/tr[2]/td[1]""")
                    BranchCode2 = BranchCode2.text
                except:
                    pass

                try:
                    BranchCode3 = self.driver.find_element_by_xpath("""//*[@id="branchTable"]/tbody/tr[3]/td[1]""")
                    BranchCode3 = BranchCode3.text

                except:
                    pass
                try:
                    BranchCode4 = self.driver.find_element_by_xpath("""// *[ @ id = "branchTable"] / tbody / tr[4] / td[1]""")
                    BranchCode4 = BranchCode4.text


                except:
                    pass
                try:
                    BranchCode5 = self.driver.find_element_by_xpath("""// *[ @ id = "branchTable"] / tbody / tr[5] / td[1]""")
                    BranchCode5 = BranchCode5.text

                except:
                    pass
                try:
                    BranchCode6 = self.driver.find_element_by_xpath("""//*[@id="branchTable"]/tbody/tr[6]/td[1]""")
                    BranchCode6 = BranchCode6.text

                except:
                    pass
                try:
                    BranchCode7 = self.driver.find_element_by_xpath("""//*[@id="branchTable"]/tbody/tr[7]/td[1]""")
                    BranchCode7 = BranchCode7.text

                except:
                    pass
                try:
                    BranchCode8 = self.driver.find_element_by_xpath("""//*[@id="branchTable"]/tbody/tr[8]/td[1]""")
                    BranchCode8 = BranchCode8.text

                except:
                    pass
                try:
                    BranchCode9 = self.driver.find_element_by_xpath("""//*[@id="branchTable"]/tbody/tr[9]/td[1]""")
                    BranchCode9 = BranchCode9.text

                except:
                    pass
                try:
                    BranchCode10 = self.driver.find_element_by_xpath("""//*[@id="branchTable"]/tbody/tr[10]/td[1]""")
                    BranchCode10 = BranchCode10.text

                except:
                    BranchCode10 = ""
                try:
                    gstin1 = self.driver.find_element_by_xpath("""//*[@id="gst1"]""")
                    gstin1 = gstin1.text

                except:
                    pass

                try:
                    gstin2 = self.driver.find_element_by_xpath("""//*[@id="gst2"]""")
                    gstin2 = gstin2.text

                except:
                    pass
                try:
                    gstin3 = self.driver.find_element_by_xpath("""//*[@id="gst3"]""")
                    gstin3 = gstin3.text

                except:
                    pass
                try:
                    gstin4 = self.driver.find_element_by_xpath("""//*[@id="gst4"]""")
                    gstin4 = gstin4.text

                except:
                    pass
                try:
                    gstin5 = self.driver.find_element_by_xpath("""//*[@id="gst5"]""")
                    gstin5 = gstin5.text

                except:
                    pass
                try:
                    gstin6 = self.driver.find_element_by_xpath("""//*[@id="gst6"]""")
                    gstin6 = gstin6.text

                except:
                    pass
                try:
                    gstin7 = self.driver.find_element_by_xpath("""//*[@id="gst7"]""")
                    gstin7 = gstin7.text

                except:
                    pass
                try:
                    gstin8 = self.driver.find_element_by_xpath("""//*[@id="gst8"]""")
                    gstin8 = gstin8.text

                except:
                    pass

                try:
                    gstin9 = self.driver.find_element_by_xpath("""//*[@id="gst9"]""")
                    gstin9 = gstin9.text

                except:
                    pass
                try:
                    gstin10 = self.driver.find_element_by_xpath("""//*[@id="gst10"]""")
                    gstin10 = gstin10.text

                except:
                    pass
                try:
                    Address1 = self.driver.find_element_by_xpath("""//*[@id="branchTable"]/tbody/tr[1]/td[3]""")
                    Address1 = Address1.text

                except:
                    pass
                try:
                    Address2 = self.driver.find_element_by_xpath("""//*[@id="branchTable"]/tbody/tr[2]/td[3]""")
                    Address2 = Address2.text

                except:
                    pass
                try:
                    Address3 = self.driver.find_element_by_xpath("""//*[@id="branchTable"]/tbody/tr[3]/td[3]""")
                    Address3 = Address3.text

                except:
                    pass
                try:
                    Address4 = self.driver.find_element_by_xpath("""//*[@id="branchTable"]/tbody/tr[4]/td[3]""")
                    Address4 = Address4.text

                except:
                    pass
                try:
                    Address5 = self.driver.find_element_by_xpath("""//*[@id="branchTable"]/tbody/tr[5]/td[3]""")
                    Address5 = Address5.text

                except:
                    pass
                try:
                    Address6 = self.driver.find_element_by_xpath("""//*[@id="branchTable"]/tbody/tr[6]/td[3]""")
                    Address6 = Address6.text

                except:
                    pass
                try:
                    Address7 = self.driver.find_element_by_xpath("""//*[@id="branchTable"]/tbody/tr[7]/td[3]""")
                    Address7 = Address7.text

                except:
                    pass
                try:
                    Address8 = self.driver.find_element_by_xpath("""//*[@id="branchTable"]/tbody/tr[8]/td[3]""")
                    Address8 = Address8.text

                except:
                    pass
                try:
                    Address9 = self.driver.find_element_by_xpath("""//*[@id="branchTable"]/tbody/tr[9]/td[3]""")
                    Address9 = Address9.text

                except:
                    pass
                try:
                    Address10 = self.driver.find_element_by_xpath("""//*[@id="branchTable"]/tbody/tr[10]/td[3]""")
                    Address10 = Address10.text
                except:
                    pass
                if len(BranchCode10)>0:
                    try:
                        self.driver.find_element_by_xpath("""// *[ @ id = "branchTable_next"] / a""").click()
                    except:
                        pass
                    try:
                        BranchCode11 = self.driver.find_element_by_xpath("""//*[@id="branchTable"]/tbody/tr[1]/td[1]""")
                        BranchCode11 = BranchCode11.text
                    except:
                        pass
                    try:
                        BranchCode12 = self.driver.find_element_by_xpath("""//*[@id="branchTable"]/tbody/tr[2]/td[1]""")
                        BranchCode12 = BranchCode12.text
                    except:
                        pass
                    try:
                        BranchCode13 = self.driver.find_element_by_xpath("""//*[@id="branchTable"]/tbody/tr[3]/td[1]""")
                        BranchCode13 = BranchCode13.text
                    except:
                        pass
                    try:
                        BranchCode14 = self.driver.find_element_by_xpath("""//*[@id="branchTable"]/tbody/tr[4]/td[1]""")
                        BranchCode14 = BranchCode14.text
                    except:
                        pass
                    try:
                        BranchCode15 = self.driver.find_element_by_xpath("""//*[@id="branchTable"]/tbody/tr[5]/td[1]""")
                        BranchCode15 = BranchCode15.text
                    except:
                        pass
                    try:
                        BranchCode16 = self.driver.find_element_by_xpath("""//*[@id="branchTable"]/tbody/tr[6]/td[1]""")
                        BranchCode16 = BranchCode16.text
                    except:
                        pass
                    try:
                        BranchCode17 = self.driver.find_element_by_xpath("""//*[@id="branchTable"]/tbody/tr[7]/td[1]""")
                        BranchCode17 = BranchCode17.text
                    except:
                        pass
                    try:
                        BranchCode18 = self.driver.find_element_by_xpath("""//*[@id="branchTable"]/tbody/tr[8]/td[1]""")
                        BranchCode18 = BranchCode18.text
                    except:
                        pass
                    try:
                        BranchCode19 = self.driver.find_element_by_xpath("""//*[@id="branchTable"]/tbody/tr[9]/td[1]""")
                        BranchCode19 = BranchCode19.text
                    except:
                        pass
                    try:
                        BranchCode20 = self.driver.find_element_by_xpath("""//*[@id="branchTable"]/tbody/tr[10]/td[1]""")
                        BranchCode20 = BranchCode20.text
                    except:
                        BranchCode20 = ""
                    try:
                        gstin11 = self.driver.find_element_by_xpath("""//*[@id="gst11"]""")
                        gstin11 = gstin11.text
                    except:
                        pass
                    try:
                        gstin12 = self.driver.find_element_by_xpath("""//*[@id="gst12"]""")
                        gstin12 = gstin12.text
                    except:
                        pass
                    try:
                        gstin13 = self.driver.find_element_by_xpath("""//*[@id="gst13"]""")
                        gstin13 = gstin13.text
                    except:
                        pass
                    try:
                        gstin14 = self.driver.find_element_by_xpath("""//*[@id="gst14"]""")
                        gstin14 = gstin14.text
                    except:
                        pass
                    try:
                        gstin15 = self.driver.find_element_by_xpath("""//*[@id="gst15"]""")
                        gstin15 = gstin15.text
                    except:
                        pass
                    try:
                        gstin16 = self.driver.find_element_by_xpath("""//*[@id="gst16"]""")
                        gstin16 = gstin16.text
                    except:
                        pass
                    try:
                        gstin17 = self.driver.find_element_by_xpath("""//*[@id="gst17"]""")
                        gstin17 = gstin17.text
                    except:
                        pass
                    try:
                        gstin18 = self.driver.find_element_by_xpath("""//*[@id="gst18"]""")
                        gstin18 = gstin18.text
                    except:
                        pass
                    try:
                        gstin19 = self.driver.find_element_by_xpath("""//*[@id="gst19"]""")
                        gstin19 = gstin19.text
                    except:
                        pass
                    try:
                        gstin20 = self.driver.find_element_by_xpath("""//*[@id="gst20"]""")
                        gstin20 = gstin20.text
                    except:
                        pass


                    try:
                        Address11 = self.driver.find_element_by_xpath("""//*[@id="branchTable"]/tbody/tr[1]/td[3]""")
                        Address11 = Address11.text
                    except:
                        pass
                    try:
                        Address12 = self.driver.find_element_by_xpath("""//*[@id="branchTable"]/tbody/tr[2]/td[3]""")
                        Address12 = Address12.text
                    except:
                        pass
                    try:
                        Address13 = self.driver.find_element_by_xpath("""//*[@id="branchTable"]/tbody/tr[3]/td[3]""")
                        Address13 = Address13.text
                    except:
                        pass
                    try:
                        Address14 = self.driver.find_element_by_xpath("""//*[@id="branchTable"]/tbody/tr[4]/td[3]""")
                        Address14 = Address14.text
                    except:
                        pass
                    try:
                        Address15 = self.driver.find_element_by_xpath("""//*[@id="branchTable"]/tbody/tr[5]/td[3]""")
                        Address15 = Address15.text
                    except:
                        pass
                    try:
                        Address16 = self.driver.find_element_by_xpath("""//*[@id="branchTable"]/tbody/tr[6]/td[3]""")
                        Address16 = Address16.text
                    except:
                        pass
                    try:
                        Address17 = self.driver.find_element_by_xpath("""//*[@id="branchTable"]/tbody/tr[7]/td[3]""")
                        Address17 = Address17.text
                    except:
                        pass
                    try:
                        Address18 = self.driver.find_element_by_xpath("""//*[@id="branchTable"]/tbody/tr[8]/td[3]""")
                        Address18 = Address18.text
                    except:
                        pass
                    try:
                        Address19 = self.driver.find_element_by_xpath("""//*[@id="branchTable"]/tbody/tr[9]/td[3]""")
                        Address19 = Address19.text
                    except:
                        pass
                    try:
                        Address20 = self.driver.find_element_by_xpath("""//*[@id="branchTable"]/tbody/tr[10]/td[3]""")
                        Address20 = Address20.text
                    except:
                        pass
                    if len(BranchCode20)>0:
                        try:
                            self.driver.find_element_by_xpath("""// *[ @ id = "branchTable_next"] / a""").click()
                        except:
                            pass

                        try:
                            BranchCode21= self.driver.find_element_by_xpath("""//*[@id="branchTable"]/tbody/tr[1]/td[1]""")
                            BranchCode21= BranchCode21.text
                        except:
                            pass
                        try:
                            BranchCode22 = self.driver.find_element_by_xpath("""//*[@id="branchTable"]/tbody/tr[2]/td[1]""")
                            BranchCode22 = BranchCode22.text
                        except:
                            pass
                        try:
                            BranchCode23 = self.driver.find_element_by_xpath("""//*[@id="branchTable"]/tbody/tr[3]/td[1]""")
                            BranchCode23 = BranchCode23.text

                        except:
                            pass
                        try:
                            BranchCode24 = self.driver.find_element_by_xpath("""//*[@id="branchTable"]/tbody/tr[4]/td[1]""")
                            BranchCode24 = BranchCode24.text

                        except:
                            pass
                        try:
                            BranchCode25 = self.driver.find_element_by_xpath("""//*[@id="branchTable"]/tbody/tr[5]/td[1]""")
                            BranchCode25 = BranchCode25.text

                        except:
                            pass
                        try:
                            BranchCode26 = self.driver.find_element_by_xpath("""//*[@id="branchTable"]/tbody/tr[6]/td[1]""")
                            BranchCode26 = BranchCode26.text

                        except:
                            pass
                        try:
                            BranchCode27 = self.driver.find_element_by_xpath("""//*[@id="branchTable"]/tbody/tr[7]/td[1]""")
                            BranchCode27 = BranchCode27.text

                        except:
                            pass
                        try:
                            BranchCode28 = self.driver.find_element_by_xpath("""//*[@id="branchTable"]/tbody/tr[8]/td[1]""")
                            BranchCode28 = BranchCode28.text

                        except:
                            pass
                        try:
                            BranchCode29 = self.driver.find_element_by_xpath("""//*[@id="branchTable"]/tbody/tr[9]/td[1]""")
                            BranchCode29 = BranchCode29.text

                        except:
                            pass
                        try:
                            BranchCode30 = self.driver.find_element_by_xpath("""/html/body/div[1]/div[9]/div/div/div[1]/div/div/div[1]/div[2]/div/div/div[8]/div/div/div/div/div[2]/div/table/tbody/tr[10]/td[1]""")

                            BranchCode30 = BranchCode30.text

                        except:
                            BranchCode30 = ""
                        try:
                            gstin21 = self.driver.find_element_by_xpath("""//*[@id="gst21"]""")
                            gstin21 = gstin21.text
                        except:
                            pass
                        try:
                            gstin22 = self.driver.find_element_by_xpath("""//*[@id="gst22"]""")
                            gstin22 = gstin22.text
                        except:
                            pass
                        try:
                            gstin23 = self.driver.find_element_by_xpath("""//*[@id="gst23"]""")
                            gstin23 = gstin23.text
                        except:
                            pass
                        try:
                            gstin24 = self.driver.find_element_by_xpath("""//*[@id="gst24"]""")
                            gstin24 = gstin24.text
                        except:
                            pass
                        try:
                            gstin25 = self.driver.find_element_by_xpath("""//*[@id="gst25"]""")
                            gstin25 = gstin25.text
                        except:
                            pass
                        try:
                            gstin26 = self.driver.find_element_by_xpath("""//*[@id="gst26"]""")
                            gstin26 = gstin26.text
                        except:
                            pass
                        try:
                            gstin27 = self.driver.find_element_by_xpath("""//*[@id="gst27"]""")
                            gstin27 = gstin27.text
                        except:
                            pass
                        try:
                            gstin28 = self.driver.find_element_by_xpath("""//*[@id="gst28"]""")
                            gstin28 = gstin28.text
                        except:
                            pass
                        try:
                            gstin29= self.driver.find_element_by_xpath("""//*[@id="gst29"]""")
                            gstin29 = gstin29.text
                        except:
                            pass
                        try:
                            gstin30 = self.driver.find_element_by_xpath("""//*[@id="gst30"]""")
                            gstin30 = gstin30.text
                        except:
                            pass
                        try:
                            Address21 = self.driver.find_element_by_xpath("""//*[@id="branchTable"]/tbody/tr[1]/td[3]""")
                            Address21 = Address21.text
                        except:
                            pass
                        try:
                            Address22 = self.driver.find_element_by_xpath("""//*[@id="branchTable"]/tbody/tr[2]/td[3]""")
                            Address22 = Address22.text
                        except:
                            pass
                        try:
                            Address23 = self.driver.find_element_by_xpath("""//*[@id="branchTable"]/tbody/tr[3]/td[3]""")
                            Address23 = Address23.text
                        except:
                            pass
                        try:
                            Address24 = self.driver.find_element_by_xpath("""//*[@id="branchTable"]/tbody/tr[4]/td[3]""")
                            Address24 = Address24.text
                        except:
                            pass
                        try:
                            Address25 = self.driver.find_element_by_xpath("""//*[@id="branchTable"]/tbody/tr[5]/td[3]""")
                            Address25 = Address25.text
                        except:
                            pass
                        try:
                            Address26 = self.driver.find_element_by_xpath("""//*[@id="branchTable"]/tbody/tr[6]/td[3]""")
                            Address26 = Address26.text
                        except:
                            pass
                        try:
                            Address27 = self.driver.find_element_by_xpath("""//*[@id="branchTable"]/tbody/tr[7]/td[3]""")
                            Address27 = Address27.text
                        except:
                            pass
                        try:
                            Address28 = self.driver.find_element_by_xpath("""//*[@id="branchTable"]/tbody/tr[8]/td[3]""")
                            Address28 = Address28.text
                        except:
                            pass
                        try:
                            Address29 = self.driver.find_element_by_xpath("""//*[@id="branchTable"]/tbody/tr[9]/td[3]""")
                            Address29 = Address29.text
                        except:
                            pass
                        try:
                            Address30 = self.driver.find_element_by_xpath("""//*[@id="branchTable"]/tbody/tr[10]/td[3]""")
                            Address30 = Address30.text

                        except:
                            pass

                        if len(BranchCode30)!=0:
                            try:
                                self.driver.find_element_by_xpath("""/html/body/div[1]/div[9]/div/div/div[1]/div/div/div[1]/div[2]/div/div/div[8]/div/div/div/div/div[3]/div[2]/div/ul/li[9]/a""").click()
                            except:
                                pass
                            try:
                                BranchCode31= self.driver.find_element_by_xpath("""//*[@id="branchTable"]/tbody/tr[1]/td[1]""")
                                BranchCode31= BranchCode31.text
                            except:
                                pass
                            try:
                                BranchCode32 = self.driver.find_element_by_xpath("""//*[@id="branchTable"]/tbody/tr[2]/td[1]""")
                                BranchCode32 = BranchCode32.text
                            except:
                                pass
                            try:
                                BranchCode33 = self.driver.find_element_by_xpath("""//*[@id="branchTable"]/tbody/tr[3]/td[1]""")
                                BranchCode33 = BranchCode33.text

                            except:
                                pass
                            try:
                                BranchCode34 = self.driver.find_element_by_xpath("""//*[@id="branchTable"]/tbody/tr[4]/td[1]""")
                                BranchCode34 = BranchCode34.text

                            except:
                                pass
                            try:
                                BranchCode35 = self.driver.find_element_by_xpath("""//*[@id="branchTable"]/tbody/tr[5]/td[1]""")
                                BranchCode35 = BranchCode35.text

                            except:
                                pass
                            try:
                                BranchCode36 = self.driver.find_element_by_xpath("""//*[@id="branchTable"]/tbody/tr[6]/td[1]""")
                                BranchCode36 = BranchCode36.text

                            except:
                                pass
                            try:
                                BranchCode37 = self.driver.find_element_by_xpath("""//*[@id="branchTable"]/tbody/tr[7]/td[1]""")
                                BranchCode37 = BranchCode37.text

                            except:
                                pass
                            try:
                                BranchCode38 = self.driver.find_element_by_xpath("""//*[@id="branchTable"]/tbody/tr[8]/td[1]""")
                                BranchCode38 = BranchCode38.text

                            except:
                                pass
                            try:
                                BranchCode39 = self.driver.find_element_by_xpath("""//*[@id="branchTable"]/tbody/tr[9]/td[1]""")
                                BranchCode39 = BranchCode39.text

                            except:
                                pass
                            try:
                                BranchCode40 = self.driver.find_element_by_xpath("""//*[@id="branchTable"]/tbody/tr[10]/td[1]""")
                                BranchCode40 = BranchCode40.text

                            except:
                                BranchCode40 = ""
                            try:
                                gstin31 = self.driver.find_element_by_xpath("""//*[@id="gst31"]""")
                                gstin31 = gstin31.text
                            except:
                                pass
                            try:
                                gstin32 = self.driver.find_element_by_xpath("""//*[@id="gst32"]""")
                                gstin32 = gstin32.text
                            except:
                                pass
                            try:
                                gstin33 = self.driver.find_element_by_xpath("""//*[@id="gst33"]""")
                                gstin33 = gstin33.text
                            except:
                                pass
                            try:
                                gstin34 = self.driver.find_element_by_xpath("""//*[@id="gst34"]""")
                                gstin34 = gstin34.text
                            except:
                                pass
                            try:
                                gstin35 = self.driver.find_element_by_xpath("""//*[@id="gst35"]""")
                                gstin35 = gstin35.text
                            except:
                                pass
                            try:
                                gstin36 = self.driver.find_element_by_xpath("""//*[@id="gst36"]""")
                                gstin36 = gstin36.text
                            except:
                                pass
                            try:
                                gstin37 = self.driver.find_element_by_xpath("""//*[@id="gst37"]""")
                                gstin37 = gstin37.text
                            except:
                                pass
                            try:
                                gstin38 = self.driver.find_element_by_xpath("""//*[@id="gst38"]""")
                                gstin38 = gstin38.text
                            except:
                                pass
                            try:
                                gstin39= self.driver.find_element_by_xpath("""//*[@id="gst39"]""")
                                gstin39 = gstin39.text
                            except:
                                pass
                            try:
                                gstin40 = self.driver.find_element_by_xpath("""//*[@id="gst40"]""")
                                gstin40 = gstin40.text
                            except:
                                pass
                            try:
                                Address31 = self.driver.find_element_by_xpath("""//*[@id="branchTable"]/tbody/tr[1]/td[3]""")
                                Address31 = Address31.text
                            except:
                                pass
                            try:
                                Address32 = self.driver.find_element_by_xpath("""//*[@id="branchTable"]/tbody/tr[2]/td[3]""")
                                Address32 = Address32.text
                            except:
                                pass
                            try:
                                Address33 = self.driver.find_element_by_xpath("""//*[@id="branchTable"]/tbody/tr[3]/td[3]""")
                                Address33 = Address33.text
                            except:
                                pass
                            try:
                                Address34 = self.driver.find_element_by_xpath("""//*[@id="branchTable"]/tbody/tr[4]/td[3]""")
                                Address34 = Address34.text
                            except:
                                pass
                            try:
                                Address35 = self.driver.find_element_by_xpath("""//*[@id="branchTable"]/tbody/tr[5]/td[3]""")
                                Address35 = Address35.text
                            except:
                                pass
                            try:
                                Address36 = self.driver.find_element_by_xpath("""//*[@id="branchTable"]/tbody/tr[6]/td[3]""")
                                Address36 = Address36.text
                            except:
                                pass
                            try:
                                Address37 = self.driver.find_element_by_xpath("""//*[@id="branchTable"]/tbody/tr[7]/td[3]""")
                                Address37 = Address37.text
                            except:
                                pass
                            try:
                                Address38 = self.driver.find_element_by_xpath("""//*[@id="branchTable"]/tbody/tr[8]/td[3]""")
                                Address38 = Address38.text
                            except:
                                pass
                            try:
                                Address39 = self.driver.find_element_by_xpath("""//*[@id="branchTable"]/tbody/tr[9]/td[3]""")
                                Address39 = Address39.text
                            except:
                                pass
                            try:
                                Address40 = self.driver.find_element_by_xpath("""//*[@id="branchTable"]/tbody/tr[10]/td[3]""")
                                Address40 = Address40.text


                            except:
                                pass

                            if len(BranchCode40) > 0:
                                try:
                                    self.driver.find_element_by_xpath("""// *[ @ id = "branchTable_next"] / a""").click()
                                except:
                                    pass
                                try:

                                    BranchCode41= self.driver.find_element_by_xpath("""// *[ @ id = "branchTable"] / tbody / tr[1] / td[1]""")
                                    BranchCode41= BranchCode41.text
                                except:
                                    pass
                                try:
                                    BranchCode42 = self.driver.find_element_by_xpath("""// *[ @ id = "branchTable"] / tbody / tr[2] / td[1]""")
                                    BranchCode42 = BranchCode42.text
                                except:
                                    pass
                                try:
                                    BranchCode43 = self.driver.find_element_by_xpath("""// *[ @ id = "branchTable"] / tbody / tr[3] / td[1]""")
                                    BranchCode43 = BranchCode43.text

                                except:
                                    pass
                                try:
                                    BranchCode44 = self.driver.find_element_by_xpath("""// *[ @ id = "branchTable"] / tbody / tr[4] / td[1]""")
                                    BranchCode44 = BranchCode44.text

                                except:
                                    pass
                                try:
                                    BranchCode45 = self.driver.find_element_by_xpath("""// *[ @ id = "branchTable"] / tbody / tr[5] / td[1]""")
                                    BranchCode45 = BranchCode45.text

                                except:
                                    pass
                                try:
                                    BranchCode46 = self.driver.find_element_by_xpath("""// *[ @ id = "branchTable"] / tbody / tr[6] / td[1]""")
                                    BranchCode46 = BranchCode46.text

                                except:
                                    pass
                                try:
                                    BranchCode47 = self.driver.find_element_by_xpath("""// *[ @ id = "branchTable"] / tbody / tr[7] / td[1]""")
                                    BranchCode47 = BranchCode47.text

                                except:
                                    pass
                                try:
                                    BranchCode48 = self.driver.find_element_by_xpath("""// *[ @ id = "branchTable"] / tbody / tr[8] / td[1]""")
                                    BranchCode48 = BranchCode48.text

                                except:
                                    pass
                                try:
                                    BranchCode49 = self.driver.find_element_by_xpath("""// *[ @ id = "branchTable"] / tbody / tr[9] / td[1]""")
                                    BranchCode49 = BranchCode49.text

                                except:
                                    pass
                                try:
                                    BranchCode50 = self.driver.find_element_by_xpath("""/html/body/div[1]/div[9]/div/div/div[1]/div/div/div[1]/div[2]/div/div/div[8]/div/div/div/div/div[2]/div/table/tbody/tr[10]/td[1]""")
                                    BranchCode50 = BranchCode50.text

                                except:
                                    BranchCode50 = ""
                                try:
                                    gstin41 = self.driver.find_element_by_xpath("""//*[@id="gst41"]""")
                                    gstin41 = gstin41.text
                                except:
                                    pass
                                try:
                                    gstin42 = self.driver.find_element_by_xpath("""//*[@id="gst42"]""")
                                    gstin42 = gstin42.text
                                except:
                                    pass
                                try:
                                    gstin43 = self.driver.find_element_by_xpath("""//*[@id="gst43"]""")
                                    gstin43 = gstin43.text
                                except:
                                    pass
                                try:
                                    gstin44 = self.driver.find_element_by_xpath("""//*[@id="gst44"]""")
                                    gstin44 = gstin44.text
                                except:
                                    pass
                                try:
                                    gstin45 = self.driver.find_element_by_xpath("""//*[@id="gst45"]""")
                                    gstin45 = gstin45.text
                                except:
                                    pass
                                try:
                                    gstin46 = self.driver.find_element_by_xpath("""//*[@id="gst46"]""")
                                    gstin46 = gstin46.text
                                except:
                                    pass
                                try:
                                    gstin47 = self.driver.find_element_by_xpath("""//*[@id="gst47"]""")
                                    gstin47 = gstin47.text
                                except:
                                    pass
                                try:
                                    gstin48 = self.driver.find_element_by_xpath("""//*[@id="gst48"]""")
                                    gstin48 = gstin48.text
                                except:
                                    pass
                                try:
                                    gstin49= self.driver.find_element_by_xpath("""//*[@id="gst49"]""")
                                    gstin49 = gstin49.text
                                except:
                                    pass
                                try:
                                    gstin50 = self.driver.find_element_by_xpath("""//*[@id="gst50"]""")
                                    gstin50 = gstin50.text
                                except:
                                    pass
                                try:
                                    Address41 = self.driver.find_element_by_xpath("""//*[@id="branchTable"]/tbody/tr[1]/td[3]""")
                                    Address41 = Address41.text
                                except:
                                    pass
                                try:
                                    Address42 = self.driver.find_element_by_xpath("""//*[@id="branchTable"]/tbody/tr[2]/td[3]""")
                                    Address42 = Address42.text
                                except:
                                    pass
                                try:
                                    Address43 = self.driver.find_element_by_xpath("""//*[@id="branchTable"]/tbody/tr[3]/td[3]""")
                                    Address43 = Address43.text
                                except:
                                    pass
                                try:
                                    Address44 = self.driver.find_element_by_xpath("""//*[@id="branchTable"]/tbody/tr[4]/td[3]""")
                                    Address44 = Address44.text
                                except:
                                    pass
                                try:
                                    Address45 = self.driver.find_element_by_xpath("""//*[@id="branchTable"]/tbody/tr[5]/td[3]""")
                                    Address45 = Address45.text
                                except:
                                    pass
                                try:
                                    Address46 = self.driver.find_element_by_xpath("""//*[@id="branchTable"]/tbody/tr[6]/td[3]""")
                                    Address46 = Address46.text
                                except:
                                    pass
                                try:
                                    Address47 = self.driver.find_element_by_xpath("""//*[@id="branchTable"]/tbody/tr[7]/td[3]""")
                                    Address47 = Address47.text
                                except:
                                    pass
                                try:
                                    Address48 = self.driver.find_element_by_xpath("""//*[@id="branchTable"]/tbody/tr[8]/td[3]""")
                                    Address48 = Address48.text
                                except:
                                    pass
                                try:
                                    Address49 = self.driver.find_element_by_xpath("""//*[@id="branchTable"]/tbody/tr[9]/td[3]""")
                                    Address49 = Address49.text
                                except:
                                    pass
                                try:
                                    Address50 = self.driver.find_element_by_xpath("""//*[@id="branchTable"]/tbody/tr[10]/td[3]""")
                                    Address50 = Address50.text

                                except:
                                    pass

                                if len(BranchCode50) > 0:
                                    try:

                                        self.driver.find_element_by_xpath("""/html/body/div[1]/div[9]/div/div/div[1]/div/div/div[1]/div[2]/div/div/div[8]/div/div/div/div/div[3]/div[2]/div/ul/li[9]/a""").click()
                                    except:
                                        pass

                                    try:
                                        BranchCode51= self.driver.find_element_by_xpath("""// *[ @ id = "branchTable"] / tbody / tr[1] / td[1]""")
                                        BranchCode51= BranchCode51.text


                                    except:

                                        pass
                                    try:
                                        BranchCode52 = self.driver.find_element_by_xpath("""// *[ @ id = "branchTable"] / tbody / tr[2] / td[1]""")
                                        BranchCode52 = BranchCode52.text
                                    except:
                                        pass
                                    try:
                                        BranchCode53 = self.driver.find_element_by_xpath("""// *[ @ id = "branchTable"] / tbody / tr[3] / td[1]""")
                                        BranchCode53 = BranchCode53.text

                                    except:
                                        pass
                                    try:
                                        BranchCode54 = self.driver.find_element_by_xpath("""// *[ @ id = "branchTable"] / tbody / tr[4] / td[1]""")
                                        BranchCode54 = BranchCode54.text

                                    except:
                                        pass
                                    try:
                                        BranchCode55 = self.driver.find_element_by_xpath("""// *[ @ id = "branchTable"] / tbody / tr[5] / td[1]""")
                                        BranchCode55 = BranchCode55.text

                                    except:
                                        pass
                                    try:
                                        BranchCode56 = self.driver.find_element_by_xpath("""// *[ @ id = "branchTable"] / tbody / tr[6] / td[1]""")
                                        BranchCode56 = BranchCode56.text

                                    except:
                                        pass
                                    try:
                                        BranchCode57 = self.driver.find_element_by_xpath("""// *[ @ id = "branchTable"] / tbody / tr[7] / td[1]""")
                                        BranchCode57 = BranchCode57.text

                                    except:
                                        pass
                                    try:
                                        BranchCode58 = self.driver.find_element_by_xpath("""// *[ @ id = "branchTable"] / tbody / tr[8] / td[1]""")
                                        BranchCode58 = BranchCode58.text

                                    except:
                                        pass
                                    try:
                                        BranchCode59 = self.driver.find_element_by_xpath("""// *[ @ id = "branchTable"] / tbody / tr[9] / td[1]""")
                                        BranchCode59 = BranchCode59.text

                                    except:
                                        pass
                                    try:
                                        BranchCode60 = self.driver.find_element_by_xpath("""// *[ @ id = "branchTable"] / tbody / tr[10] / td[1]""")
                                        BranchCode60 = BranchCode60.text

                                    except:
                                        BranchCode60 = ""
                                    try:
                                        gstin51 = self.driver.find_element_by_xpath("""//*[@id="gst51"]""")
                                        gstin51 = gstin51.text
                                    except:
                                        pass
                                    try:
                                        gstin52 = self.driver.find_element_by_xpath("""//*[@id="gst52"]""")
                                        gstin52 = gstin52.text
                                    except:
                                        pass
                                    try:
                                        gstin53 = self.driver.find_element_by_xpath("""//*[@id="gst53"]""")
                                        gstin53 = gstin53.text
                                    except:
                                        pass
                                    try:
                                        gstin54 = self.driver.find_element_by_xpath("""//*[@id="gst54"]""")
                                        gstin54 = gstin54.text
                                    except:
                                        pass
                                    try:
                                        gstin55 = self.driver.find_element_by_xpath("""//*[@id="gst55"]""")
                                        gstin55 = gstin55.text
                                    except:
                                        pass
                                    try:
                                        gstin56 = self.driver.find_element_by_xpath("""//*[@id="gst56"]""")
                                        gstin56 = gstin56.text
                                    except:
                                        pass
                                    try:
                                        gstin57 = self.driver.find_element_by_xpath("""//*[@id="gst57"]""")
                                        gstin57 = gstin57.text
                                    except:
                                        pass
                                    try:
                                        gstin58 = self.driver.find_element_by_xpath("""//*[@id="gst58"]""")
                                        gstin58 = gstin58.text
                                    except:
                                        pass
                                    try:
                                        gstin59= self.driver.find_element_by_xpath("""//*[@id="gst59"]""")
                                        gstin59 = gstin59.text
                                    except:
                                        pass
                                    try:
                                        gstin60 = self.driver.find_element_by_xpath("""//*[@id="gst60"]""")
                                        gstin60 = gstin60.text
                                    except:
                                        pass
                                    try:
                                        Address51 = self.driver.find_element_by_xpath("""//*[@id="branchTable"]/tbody/tr[1]/td[3]""")
                                        Address51 = Address51.text
                                    except:
                                        pass
                                    try:
                                        Address52 = self.driver.find_element_by_xpath("""//*[@id="branchTable"]/tbody/tr[2]/td[3]""")
                                        Address52 = Address52.text
                                    except:
                                        pass
                                    try:
                                        Address53 = self.driver.find_element_by_xpath("""//*[@id="branchTable"]/tbody/tr[3]/td[3]""")
                                        Address53 = Address53.text
                                    except:
                                        pass
                                    try:
                                        Address54 = self.driver.find_element_by_xpath("""//*[@id="branchTable"]/tbody/tr[4]/td[3]""")
                                        Address54 = Address54.text
                                    except:
                                        pass
                                    try:
                                        Address55 = self.driver.find_element_by_xpath("""//*[@id="branchTable"]/tbody/tr[5]/td[3]""")
                                        Address55 = Address55.text
                                    except:
                                        pass
                                    try:
                                        Address56 = self.driver.find_element_by_xpath("""//*[@id="branchTable"]/tbody/tr[6]/td[3]""")
                                        Address56 = Address56.text
                                    except:
                                        pass
                                    try:
                                        Address57 = self.driver.find_element_by_xpath("""//*[@id="branchTable"]/tbody/tr[7]/td[3]""")
                                        Address57 = Address57.text
                                    except:
                                        pass
                                    try:
                                        Address58 = self.driver.find_element_by_xpath("""//*[@id="branchTable"]/tbody/tr[8]/td[3]""")
                                        Address58 = Address58.text
                                    except:
                                        pass
                                    try:
                                        Address59 = self.driver.find_element_by_xpath("""//*[@id="branchTable"]/tbody/tr[9]/td[3]""")
                                        Address59 = Address59.text
                                    except:
                                        pass
                                    try:
                                        Address60 = self.driver.find_element_by_xpath("""//*[@id="branchTable"]/tbody/tr[10]/td[3]""")
                                        Address60 = Address60.text

                                    except:
                                        pass
                                    if len(BranchCode60) > 0:
                                        try:

                                            self.driver.find_element_by_xpath("""// *[ @ id = "branchTable_next"] / a""").click()
                                        except Exception as e:
                                            print(e)
                                            pass

                                        try:
                                            BranchCode61= self.driver.find_element_by_xpath("""// *[ @ id = "branchTable"] / tbody / tr[1] / td[1]""")
                                            BranchCode61= BranchCode61.text
                                        except:
                                            pass
                                        try:
                                            BranchCode62 = self.driver.find_element_by_xpath("""// *[ @ id = "branchTable"] / tbody / tr[2] / td[1]""")
                                            BranchCode62 = BranchCode62.text
                                        except:
                                            pass
                                        try:
                                            BranchCode63 = self.driver.find_element_by_xpath("""// *[ @ id = "branchTable"] / tbody / tr[3] / td[1]""")
                                            BranchCode63 = BranchCode63.text

                                        except:
                                            pass
                                        try:
                                            BranchCode64 = self.driver.find_element_by_xpath("""// *[ @ id = "branchTable"] / tbody / tr[4] / td[1]""")
                                            BranchCode64 = BranchCode64.text

                                        except:
                                            pass
                                        try:
                                            BranchCode65 = self.driver.find_element_by_xpath("""// *[ @ id = "branchTable"] / tbody / tr[5] / td[1]""")
                                            BranchCode65 = BranchCode65.text

                                        except:
                                            pass
                                        try:
                                            BranchCode66 = self.driver.find_element_by_xpath("""// *[ @ id = "branchTable"] / tbody / tr[6] / td[1]""")
                                            BranchCode66 = BranchCode66.text

                                        except:
                                            pass
                                        try:
                                            BranchCode67 = self.driver.find_element_by_xpath("""// *[ @ id = "branchTable"] / tbody / tr[7] / td[1]""")
                                            BranchCode67 = BranchCode67.text

                                        except:
                                            pass
                                        try:
                                            BranchCode68 = self.driver.find_element_by_xpath("""// *[ @ id = "branchTable"] / tbody / tr[8] / td[1]""")
                                            BranchCode68 = BranchCode68.text

                                        except:
                                            pass
                                        try:
                                            BranchCode69 = self.driver.find_element_by_xpath("""// *[ @ id = "branchTable"] / tbody / tr[9] / td[1]""")
                                            BranchCode69 = BranchCode69.text

                                        except:
                                            pass
                                        try:
                                            BranchCode70 = self.driver.find_element_by_xpath("""// *[ @ id = "branchTable"] / tbody / tr[10] / td[1]""")
                                            BranchCode70 = BranchCode70.text

                                        except:
                                            BranchCode70 = ""

                                        try:
                                            gstin61 = self.driver.find_element_by_xpath("""//*[@id="gst61"]""")
                                            gstin61 = gstin61.text
                                        except:
                                            pass
                                        try:
                                            gstin62 = self.driver.find_element_by_xpath("""//*[@id="gst62"]""")
                                            gstin62 = gstin62.text
                                        except:
                                            pass
                                        try:
                                            gstin63 = self.driver.find_element_by_xpath("""//*[@id="gst63"]""")
                                            gstin63 = gstin63.text
                                        except:
                                            pass
                                        try:
                                            gstin64 = self.driver.find_element_by_xpath("""//*[@id="gst64"]""")
                                            gstin64 = gstin64.text
                                        except:
                                            pass
                                        try:
                                            gstin65 = self.driver.find_element_by_xpath("""//*[@id="gst65"]""")
                                            gstin65 = gstin65.text
                                        except:
                                            pass
                                        try:
                                            gstin66 = self.driver.find_element_by_xpath("""//*[@id="gst66"]""")
                                            gstin66 = gstin66.text
                                        except:
                                            pass
                                        try:
                                            gstin67 = self.driver.find_element_by_xpath("""//*[@id="gst67"]""")
                                            gstin67 = gstin67.text
                                        except:
                                            pass
                                        try:
                                            gstin68 = self.driver.find_element_by_xpath("""//*[@id="gst68"]""")
                                            gstin68 = gstin68.text
                                        except:
                                            pass
                                        try:
                                            gstin69= self.driver.find_element_by_xpath("""//*[@id="gst69"]""")
                                            gstin69 = gstin69.text
                                        except:
                                            pass
                                        try:
                                            gstin70 = self.driver.find_element_by_xpath("""//*[@id="gst70"]""")
                                            gstin70 = gstin70.text
                                        except:
                                            pass
                                        try:
                                            Address61 = self.driver.find_element_by_xpath("""//*[@id="branchTable"]/tbody/tr[1]/td[3]""")
                                            Address61 = Address61.text
                                        except:
                                            pass
                                        try:
                                            Address62 = self.driver.find_element_by_xpath("""//*[@id="branchTable"]/tbody/tr[2]/td[3]""")
                                            Address62 = Address62.text
                                        except:
                                            pass
                                        try:
                                            Address63 = self.driver.find_element_by_xpath("""//*[@id="branchTable"]/tbody/tr[3]/td[3]""")
                                            Address63 = Address63.text
                                        except:
                                            pass
                                        try:
                                            Address64 = self.driver.find_element_by_xpath("""//*[@id="branchTable"]/tbody/tr[4]/td[3]""")
                                            Address64 = Address64.text
                                        except:
                                            pass
                                        try:
                                            Address65 = self.driver.find_element_by_xpath("""//*[@id="branchTable"]/tbody/tr[5]/td[3]""")
                                            Address65 = Address65.text
                                        except:
                                            pass
                                        try:
                                            Address66 = self.driver.find_element_by_xpath("""//*[@id="branchTable"]/tbody/tr[6]/td[3]""")
                                            Address66 = Address66.text
                                        except:
                                            pass
                                        try:
                                            Address67 = self.driver.find_element_by_xpath("""//*[@id="branchTable"]/tbody/tr[7]/td[3]""")
                                            Address67 = Address67.text
                                        except:
                                            pass
                                        try:
                                            Address68 = self.driver.find_element_by_xpath("""//*[@id="branchTable"]/tbody/tr[8]/td[3]""")
                                            Address68 = Address68.text
                                        except:
                                            pass
                                        try:
                                            Address69 = self.driver.find_element_by_xpath("""//*[@id="branchTable"]/tbody/tr[9]/td[3]""")
                                            Address69 = Address69.text
                                        except:
                                            pass
                                        try:
                                            Address70 = self.driver.find_element_by_xpath("""//*[@id="branchTable"]/tbody/tr[10]/td[3]""")
                                            Address70 = Address70.text

                                        except:
                                            pass
                                        if len(BranchCode70) > 0:
                                            try:

                                                self.driver.find_element_by_xpath("""// *[ @ id = "branchTable_next"] / a""").click()
                                            except:
                                                pass

                                            try:
                                                BranchCode71= self.driver.find_element_by_xpath("""// *[ @ id = "branchTable"] / tbody / tr[1] / td[1]""")
                                                BranchCode71= BranchCode71.text
                                            except:
                                                pass
                                            try:
                                                BranchCode72 = self.driver.find_element_by_xpath("""// *[ @ id = "branchTable"] / tbody / tr[2] / td[1]""")
                                                BranchCode72 = BranchCode72.text
                                            except:
                                                pass
                                            try:
                                                BranchCode73 = self.driver.find_element_by_xpath("""// *[ @ id = "branchTable"] / tbody / tr[3] / td[1]""")
                                                BranchCode73 = BranchCode73.text

                                            except:
                                                pass
                                            try:
                                                BranchCode74 = self.driver.find_element_by_xpath("""// *[ @ id = "branchTable"] / tbody / tr[4] / td[1]""")
                                                BranchCode74 = BranchCode74.text

                                            except:
                                                pass
                                            try:
                                                BranchCode75 = self.driver.find_element_by_xpath("""// *[ @ id = "branchTable"] / tbody / tr[5] / td[1]""")
                                                BranchCode75 = BranchCode75.text

                                            except:
                                                pass
                                            try:
                                                BranchCode76 = self.driver.find_element_by_xpath("""// *[ @ id = "branchTable"] / tbody / tr[6] / td[1]""")
                                                BranchCode76 = BranchCode76.text

                                            except:
                                                pass
                                            try:
                                                BranchCode77 = self.driver.find_element_by_xpath("""// *[ @ id = "branchTable"] / tbody / tr[7] / td[1]""")
                                                BranchCode77 = BranchCode77.text

                                            except:
                                                pass
                                            try:
                                                BranchCode78 = self.driver.find_element_by_xpath("""// *[ @ id = "branchTable"] / tbody / tr[8] / td[1]""")
                                                BranchCode78 = BranchCode78.text

                                            except:
                                                pass
                                            try:
                                                BranchCode79 = self.driver.find_element_by_xpath("""// *[ @ id = "branchTable"] / tbody / tr[9] / td[1]""")
                                                BranchCode79 = BranchCode79.text

                                            except:
                                                pass
                                            try:
                                                BranchCode80 = self.driver.find_element_by_xpath("""// *[ @ id = "branchTable"] / tbody / tr[10] / td[1]""")
                                                BranchCode80 = BranchCode80.text

                                            except:
                                                pass
                                            try:
                                                gstin71 = self.driver.find_element_by_xpath("""//*[@id="gst71"]""")
                                                gstin71 = gstin71.text
                                            except:
                                                pass
                                            try:
                                                gstin72 = self.driver.find_element_by_xpath("""//*[@id="gst72"]""")
                                                gstin72 = gstin72.text
                                            except:
                                                pass
                                            try:
                                                gstin73 = self.driver.find_element_by_xpath("""//*[@id="gst73"]""")
                                                gstin73 = gstin73.text
                                            except:
                                                pass
                                            try:
                                                gstin74 = self.driver.find_element_by_xpath("""//*[@id="gst74"]""")
                                                gstin74 = gstin74.text
                                            except:
                                                pass
                                            try:
                                                gstin75 = self.driver.find_element_by_xpath("""//*[@id="gst75"]""")
                                                gstin75 = gstin75.text
                                            except:
                                                pass
                                            try:
                                                gstin76 = self.driver.find_element_by_xpath("""//*[@id="gst76"]""")
                                                gstin76 = gstin76.text
                                            except:
                                                pass
                                            try:
                                                gstin77 = self.driver.find_element_by_xpath("""//*[@id="gst77"]""")
                                                gstin77 = gstin77.text
                                            except:
                                                pass
                                            try:
                                                gstin78 = self.driver.find_element_by_xpath("""//*[@id="gst78"]""")
                                                gstin78 = gstin78.text
                                            except:
                                                pass
                                            try:
                                                gstin79= self.driver.find_element_by_xpath("""//*[@id="gst79"]""")
                                                gstin79 = gstin79.text
                                            except:
                                                pass
                                            try:
                                                gstin80 = self.driver.find_element_by_xpath("""//*[@id="gst80"]""")
                                                gstin80 = gstin80.text
                                            except:
                                                pass
                                            try:
                                                Address71 = self.driver.find_element_by_xpath("""//*[@id="branchTable"]/tbody/tr[1]/td[3]""")
                                                Address71 = Address71.text
                                            except:
                                                pass
                                            try:
                                                Address72 = self.driver.find_element_by_xpath("""//*[@id="branchTable"]/tbody/tr[2]/td[3]""")
                                                Address72 = Address72.text
                                            except:
                                                pass
                                            try:
                                                Address73 = self.driver.find_element_by_xpath("""//*[@id="branchTable"]/tbody/tr[3]/td[3]""")
                                                Address73 = Address73.text
                                            except:
                                                pass
                                            try:
                                                Address74 = self.driver.find_element_by_xpath("""//*[@id="branchTable"]/tbody/tr[4]/td[3]""")
                                                Address74 = Address74.text
                                            except:
                                                pass
                                            try:
                                                Address75 = self.driver.find_element_by_xpath("""//*[@id="branchTable"]/tbody/tr[5]/td[3]""")
                                                Address75 = Address75.text
                                            except:
                                                pass
                                            try:
                                                Address76 = self.driver.find_element_by_xpath("""//*[@id="branchTable"]/tbody/tr[6]/td[3]""")
                                                Address76 = Address76.text
                                            except:
                                                pass
                                            try:
                                                Address77 = self.driver.find_element_by_xpath("""//*[@id="branchTable"]/tbody/tr[7]/td[3]""")
                                                Address77 = Address77.text
                                            except:
                                                pass
                                            try:
                                                Address78 = self.driver.find_element_by_xpath("""//*[@id="branchTable"]/tbody/tr[8]/td[3]""")
                                                Address78 = Address78.text
                                            except:
                                                pass
                                            try:
                                                Address79 = self.driver.find_element_by_xpath("""//*[@id="branchTable"]/tbody/tr[9]/td[3]""")
                                                Address79 = Address79.text
                                            except:
                                                pass
                                            try:
                                                Address80 = self.driver.find_element_by_xpath("""//*[@id="branchTable"]/tbody/tr[10]/td[3]""")
                                                Address80 = Address80.text

                                            except:
                                                pass

                                            try:

                                                self.driver.find_element_by_xpath("""// *[ @ id = "branchTable_next"] / a""").click()
                                            except:
                                                pass

                                            try:
                                                BranchCode81= self.driver.find_element_by_xpath("""// *[ @ id = "branchTable"] / tbody / tr[1] / td[1]""")
                                                BranchCode81= BranchCode81.text
                                            except:
                                                pass
                                            try:
                                                BranchCode82 = self.driver.find_element_by_xpath("""// *[ @ id = "branchTable"] / tbody / tr[2] / td[1]""")
                                                BranchCode82 = BranchCode82.text
                                            except:
                                                pass
                                            try:
                                                BranchCode83 = self.driver.find_element_by_xpath("""// *[ @ id = "branchTable"] / tbody / tr[3] / td[1]""")
                                                BranchCode83 = BranchCode83.text

                                            except:
                                                pass
                                            try:
                                                BranchCode84 = self.driver.find_element_by_xpath("""// *[ @ id = "branchTable"] / tbody / tr[4] / td[1]""")
                                                BranchCode84 = BranchCode84.text

                                            except:
                                                pass
                                            try:
                                                BranchCode85 = self.driver.find_element_by_xpath("""// *[ @ id = "branchTable"] / tbody / tr[5] / td[1]""")
                                                BranchCode85 = BranchCode85.text

                                            except:
                                                pass
                                            try:
                                                BranchCode86 = self.driver.find_element_by_xpath("""// *[ @ id = "branchTable"] / tbody / tr[6] / td[1]""")
                                                BranchCode86 = BranchCode86.text

                                            except:
                                                pass
                                            try:
                                                BranchCode87 = self.driver.find_element_by_xpath("""// *[ @ id = "branchTable"] / tbody / tr[7] / td[1]""")
                                                BranchCode87 = BranchCode87.text

                                            except:
                                                pass
                                            try:
                                                BranchCode88 = self.driver.find_element_by_xpath("""// *[ @ id = "branchTable"] / tbody / tr[8] / td[1]""")
                                                BranchCode88 = BranchCode88.text

                                            except:
                                                pass
                                            try:
                                                BranchCode89 = self.driver.find_element_by_xpath("""// *[ @ id = "branchTable"] / tbody / tr[9] / td[1]""")
                                                BranchCode89 = BranchCode89.text

                                            except:
                                                pass
                                            try:
                                                BranchCode90 = self.driver.find_element_by_xpath("""// *[ @ id = "branchTable"] / tbody / tr[10] / td[1]""")
                                                BranchCode90 = BranchCode90.text

                                            except:
                                                pass
                                            try:
                                                gstin81 = self.driver.find_element_by_xpath("""//*[@id="gst81"]""")
                                                gstin81 = gstin81.text
                                            except:
                                                pass
                                            try:
                                                gstin82 = self.driver.find_element_by_xpath("""//*[@id="gst82"]""")
                                                gstin82 = gstin82.text
                                            except:
                                                pass
                                            try:
                                                gstin83 = self.driver.find_element_by_xpath("""//*[@id="gst83"]""")
                                                gstin83 = gstin83.text
                                            except:
                                                pass
                                            try:
                                                gstin84 = self.driver.find_element_by_xpath("""//*[@id="gst84"]""")
                                                gstin84 = gstin84.text
                                            except:
                                                pass
                                            try:
                                                gstin85 = self.driver.find_element_by_xpath("""//*[@id="gst85"]""")
                                                gstin85 = gstin85.text
                                            except:
                                                pass
                                            try:
                                                gstin86 = self.driver.find_element_by_xpath("""//*[@id="gst86"]""")
                                                gstin86 = gstin86.text
                                            except:
                                                pass
                                            try:
                                                gstin87 = self.driver.find_element_by_xpath("""//*[@id="gst87"]""")
                                                gstin87 = gstin87.text
                                            except:
                                                pass
                                            try:
                                                gstin88 = self.driver.find_element_by_xpath("""//*[@id="gst88"]""")
                                                gstin88 = gstin88.text
                                            except:
                                                pass
                                            try:
                                                gstin89= self.driver.find_element_by_xpath("""//*[@id="gst89"]""")
                                                gstin89 = gstin89.text
                                            except:
                                                pass
                                            try:
                                                gstin90 = self.driver.find_element_by_xpath("""//*[@id="gst90"]""")
                                                gstin90 = gstin90.text
                                            except:
                                                pass
                                            try:
                                                Address81 = self.driver.find_element_by_xpath("""//*[@id="branchTable"]/tbody/tr[1]/td[3]""")
                                                Address81 = Address81.text
                                            except:
                                                pass
                                            try:
                                                Address82 = self.driver.find_element_by_xpath("""//*[@id="branchTable"]/tbody/tr[2]/td[3]""")
                                                Address82 = Address82.text
                                            except:
                                                pass
                                            try:
                                                Address83 = self.driver.find_element_by_xpath("""//*[@id="branchTable"]/tbody/tr[3]/td[3]""")
                                                Address83 = Address83.text
                                            except:
                                                pass
                                            try:
                                                Address84 = self.driver.find_element_by_xpath("""//*[@id="branchTable"]/tbody/tr[4]/td[3]""")
                                                Address84 = Address84.text
                                            except:
                                                pass
                                            try:
                                                Address85 = self.driver.find_element_by_xpath("""//*[@id="branchTable"]/tbody/tr[5]/td[3]""")
                                                Address85 = Address85.text
                                            except:
                                                pass
                                            try:
                                                Address86 = self.driver.find_element_by_xpath("""//*[@id="branchTable"]/tbody/tr[6]/td[3]""")
                                                Address86 = Address86.text
                                            except:
                                                pass
                                            try:
                                                Address87 = self.driver.find_element_by_xpath("""//*[@id="branchTable"]/tbody/tr[7]/td[3]""")
                                                Address87 = Address87.text
                                            except:
                                                pass
                                            try:
                                                Address88 = self.driver.find_element_by_xpath("""//*[@id="branchTable"]/tbody/tr[8]/td[3]""")
                                                Address88 = Address88.text
                                            except:
                                                pass
                                            try:
                                                Address89 = self.driver.find_element_by_xpath("""//*[@id="branchTable"]/tbody/tr[9]/td[3]""")
                                                Address89 = Address89.text
                                            except:
                                                pass
                                            try:
                                                Address90 = self.driver.find_element_by_xpath("""//*[@id="branchTable"]/tbody/tr[10]/td[3]""")
                                                Address90 = Address90.text
                                            except:
                                                pass

                                            try:

                                                self.driver.find_element_by_xpath("""// *[ @ id = "branchTable_next"] / a""").click()
                                            except:
                                                pass

                                            try:
                                                BranchCode91= self.driver.find_element_by_xpath("""// *[ @ id = "branchTable"] / tbody / tr[1] / td[1]""")
                                                BranchCode91= BranchCode91.text
                                            except:
                                                pass
                                            try:
                                                BranchCode92 = self.driver.find_element_by_xpath("""// *[ @ id = "branchTable"] / tbody / tr[2] / td[1]""")
                                                BranchCode92 = BranchCode92.text
                                            except:
                                                pass
                                            try:
                                                BranchCode93 = self.driver.find_element_by_xpath("""// *[ @ id = "branchTable"] / tbody / tr[3] / td[1]""")
                                                BranchCode93 = BranchCode93.text

                                            except:
                                                pass
                                            try:
                                                BranchCode94 = self.driver.find_element_by_xpath("""// *[ @ id = "branchTable"] / tbody / tr[4] / td[1]""")
                                                BranchCode94 = BranchCode94.text

                                            except:
                                                pass
                                            try:
                                                BranchCode95 = self.driver.find_element_by_xpath("""// *[ @ id = "branchTable"] / tbody / tr[5] / td[1]""")
                                                BranchCode95 = BranchCode95.text

                                            except:
                                                pass
                                            try:
                                                BranchCode96 = self.driver.find_element_by_xpath("""// *[ @ id = "branchTable"] / tbody / tr[6] / td[1]""")
                                                BranchCode96 = BranchCode96.text

                                            except:
                                                pass
                                            try:
                                                BranchCode97 = self.driver.find_element_by_xpath("""// *[ @ id = "branchTable"] / tbody / tr[7] / td[1]""")
                                                BranchCode97 = BranchCode97.text

                                            except:
                                                pass
                                            try:
                                                BranchCode98 = self.driver.find_element_by_xpath("""// *[ @ id = "branchTable"] / tbody / tr[8] / td[1]""")
                                                BranchCode98 = BranchCode98.text

                                            except:
                                                pass
                                            try:
                                                BranchCode99 = self.driver.find_element_by_xpath("""// *[ @ id = "branchTable"] / tbody / tr[9] / td[1]""")
                                                BranchCode99 = BranchCode99.text

                                            except:
                                                pass
                                            try:
                                                BranchCode100 = self.driver.find_element_by_xpath("""// *[ @ id = "branchTable"] / tbody / tr[10] / td[1]""")
                                                BranchCode100 = BranchCode100.text

                                            except:
                                                pass
                                            try:
                                                gstin91 = self.driver.find_element_by_xpath("""//*[@id="gst91"]""")
                                                gstin91 = gstin91.text
                                            except:
                                                pass
                                            try:
                                                gstin92 = self.driver.find_element_by_xpath("""//*[@id="gst92"]""")
                                                gstin92 = gstin92.text
                                            except:
                                                pass
                                            try:
                                                gstin93 = self.driver.find_element_by_xpath("""//*[@id="gst93"]""")
                                                gstin93 = gstin93.text
                                            except:
                                                pass
                                            try:
                                                gstin94 = self.driver.find_element_by_xpath("""//*[@id="gst94"]""")
                                                gstin94 = gstin94.text
                                            except:
                                                pass
                                            try:
                                                gstin95 = self.driver.find_element_by_xpath("""//*[@id="gst95"]""")
                                                gstin95 = gstin95.text
                                            except:
                                                pass
                                            try:
                                                gstin96 = self.driver.find_element_by_xpath("""//*[@id="gst96"]""")
                                                gstin96 = gstin96.text
                                            except:
                                                pass
                                            try:
                                                gstin97 = self.driver.find_element_by_xpath("""//*[@id="gst97"]""")
                                                gstin97 = gstin97.text
                                            except:
                                                pass
                                            try:
                                                gstin98 = self.driver.find_element_by_xpath("""//*[@id="gst98"]""")
                                                gstin98 = gstin98.text
                                            except:
                                                pass
                                            try:
                                                gstin99= self.driver.find_element_by_xpath("""//*[@id="gst99"]""")
                                                gstin99 = gstin99.text
                                            except:
                                                pass
                                            try:
                                                gstin100 = self.driver.find_element_by_xpath("""//*[@id="gst100"]""")
                                                gstin100 = gstin100.text
                                            except:
                                                pass
                                            try:
                                                Address91 = self.driver.find_element_by_xpath("""//*[@id="branchTable"]/tbody/tr[1]/td[3]""")
                                                Address91 = Address91.text
                                            except:
                                                pass
                                            try:
                                                Address92 = self.driver.find_element_by_xpath("""//*[@id="branchTable"]/tbody/tr[2]/td[3]""")
                                                Address92 = Address92.text
                                            except:
                                                pass
                                            try:
                                                Address93 = self.driver.find_element_by_xpath("""//*[@id="branchTable"]/tbody/tr[3]/td[3]""")
                                                Address93 = Address93.text
                                            except:
                                                pass
                                            try:
                                                Address94 = self.driver.find_element_by_xpath("""//*[@id="branchTable"]/tbody/tr[4]/td[3]""")
                                                Address94 = Address94.text
                                            except:
                                                pass
                                            try:
                                                Address95 = self.driver.find_element_by_xpath("""//*[@id="branchTable"]/tbody/tr[5]/td[3]""")
                                                Address95 = Address95.text
                                            except:
                                                pass
                                            try:
                                                Address96 = self.driver.find_element_by_xpath("""//*[@id="branchTable"]/tbody/tr[6]/td[3]""")
                                                Address96 = Address96.text
                                            except:
                                                pass
                                            try:
                                                Address97 = self.driver.find_element_by_xpath("""//*[@id="branchTable"]/tbody/tr[7]/td[3]""")
                                                Address97 = Address97.text
                                            except:
                                                pass
                                            try:
                                                Address98 = self.driver.find_element_by_xpath("""//*[@id="branchTable"]/tbody/tr[8]/td[3]""")
                                                Address98 = Address98.text
                                            except:
                                                pass
                                            try:
                                                Address99 = self.driver.find_element_by_xpath("""//*[@id="branchTable"]/tbody/tr[9]/td[3]""")
                                                Address99 = Address99.text
                                            except:
                                                pass
                                            try:
                                                Address100 = self.driver.find_element_by_xpath("""//*[@id="branchTable"]/tbody/tr[10]/td[3]""")
                                                Address100 = Address100.text
                                            except:
                                                pass

                                            try:

                                                self.driver.find_element_by_xpath("""// *[ @ id = "branchTable_next"] / a""").click()
                                            except:
                                                pass

                                            try:
                                                BranchCode101= self.driver.find_element_by_xpath("""// *[ @ id = "branchTable"] / tbody / tr[1] / td[1]""")
                                                BranchCode101= BranchCode101.text
                                            except:
                                                pass
                                            try:
                                                BranchCode102 = self.driver.find_element_by_xpath("""// *[ @ id = "branchTable"] / tbody / tr[2] / td[1]""")
                                                BranchCode102 = BranchCode102.text
                                            except:
                                                pass
                                            try:
                                                BranchCode103 = self.driver.find_element_by_xpath("""// *[ @ id = "branchTable"] / tbody / tr[3] / td[1]""")
                                                BranchCode103 = BranchCode103.text

                                            except:
                                                pass
                                            try:
                                                BranchCode104 = self.driver.find_element_by_xpath("""// *[ @ id = "branchTable"] / tbody / tr[4] / td[1]""")
                                                BranchCode104 = BranchCode104.text

                                            except:
                                                pass
                                            try:
                                                BranchCode105 = self.driver.find_element_by_xpath("""// *[ @ id = "branchTable"] / tbody / tr[5] / td[1]""")
                                                BranchCode105 = BranchCode105.text

                                            except:
                                                pass
                                            try:
                                                BranchCode106 = self.driver.find_element_by_xpath("""// *[ @ id = "branchTable"] / tbody / tr[6] / td[1]""")
                                                BranchCode106 = BranchCode106.text

                                            except:
                                                pass
                                            try:
                                                BranchCode107 = self.driver.find_element_by_xpath("""// *[ @ id = "branchTable"] / tbody / tr[7] / td[1]""")
                                                BranchCode107 = BranchCode107.text

                                            except:
                                                pass
                                            try:
                                                BranchCode108 = self.driver.find_element_by_xpath("""// *[ @ id = "branchTable"] / tbody / tr[8] / td[1]""")
                                                BranchCode108 = BranchCode108.text

                                            except:
                                                pass
                                            try:
                                                BranchCode109 = self.driver.find_element_by_xpath("""// *[ @ id = "branchTable"] / tbody / tr[9] / td[1]""")
                                                BranchCode109 = BranchCode109.text

                                            except:
                                                pass
                                            try:
                                                BranchCode110 = self.driver.find_element_by_xpath("""// *[ @ id = "branchTable"] / tbody / tr[10] / td[1]""")
                                                BranchCode110 = BranchCode110.text

                                            except:
                                                pass
                                            try:
                                                gstin101 = self.driver.find_element_by_xpath("""//*[@id="gst101"]""")
                                                gstin101 = gstin101.text
                                            except:
                                                pass
                                            try:
                                                gstin102 = self.driver.find_element_by_xpath("""//*[@id="gst102"]""")
                                                gstin102 = gstin102.text
                                            except:
                                                pass
                                            try:
                                                gstin103 = self.driver.find_element_by_xpath("""//*[@id="gst103"]""")
                                                gstin103 = gstin103.text
                                            except:
                                                pass
                                            try:
                                                gstin104 = self.driver.find_element_by_xpath("""//*[@id="gst104"]""")
                                                gstin104 = gstin104.text
                                            except:
                                                pass
                                            try:
                                                gstin105 = self.driver.find_element_by_xpath("""//*[@id="gst105"]""")
                                                gstin105 = gstin105.text
                                            except:
                                                pass
                                            try:
                                                gstin106 = self.driver.find_element_by_xpath("""//*[@id="gst106"]""")
                                                gstin106 = gstin106.text
                                            except:
                                                pass
                                            try:
                                                gstin107 = self.driver.find_element_by_xpath("""//*[@id="gst107"]""")
                                                gstin107 = gstin107.text
                                            except:
                                                pass
                                            try:
                                                gstin108 = self.driver.find_element_by_xpath("""//*[@id="gst108"]""")
                                                gstin108 = gstin108.text
                                            except:
                                                pass
                                            try:
                                                gstin109= self.driver.find_element_by_xpath("""//*[@id="gst109"]""")
                                                gstin109 = gstin109.text
                                            except:
                                                pass
                                            try:
                                                gstin110 = self.driver.find_element_by_xpath("""//*[@id="gst110"]""")
                                                gstin110 = gstin110.text
                                            except:
                                                pass
                                            try:
                                                Address101 = self.driver.find_element_by_xpath("""//*[@id="branchTable"]/tbody/tr[1]/td[3]""")
                                                Address101 = Address101.text
                                            except:
                                                pass
                                            try:
                                                Address102 = self.driver.find_element_by_xpath("""//*[@id="branchTable"]/tbody/tr[2]/td[3]""")
                                                Address102 = Address102.text
                                            except:
                                                pass
                                            try:
                                                Address103 = self.driver.find_element_by_xpath("""//*[@id="branchTable"]/tbody/tr[3]/td[3]""")
                                                Address103 = Address103.text
                                            except:
                                                pass
                                            try:
                                                Address104 = self.driver.find_element_by_xpath("""//*[@id="branchTable"]/tbody/tr[4]/td[3]""")
                                                Address104 = Address104.text
                                            except:
                                                pass
                                            try:
                                                Address105 = self.driver.find_element_by_xpath("""//*[@id="branchTable"]/tbody/tr[5]/td[3]""")
                                                Address105 = Address105.text
                                            except:
                                                pass
                                            try:
                                                Address106 = self.driver.find_element_by_xpath("""//*[@id="branchTable"]/tbody/tr[6]/td[3]""")
                                                Address106 = Address106.text
                                            except:
                                                pass
                                            try:
                                                Address107 = self.driver.find_element_by_xpath("""//*[@id="branchTable"]/tbody/tr[7]/td[3]""")
                                                Address107 = Address107.text
                                            except:
                                                pass
                                            try:
                                                Address108 = self.driver.find_element_by_xpath("""//*[@id="branchTable"]/tbody/tr[8]/td[3]""")
                                                Address108 = Address108.text
                                            except:
                                                pass
                                            try:
                                                Address109 = self.driver.find_element_by_xpath("""//*[@id="branchTable"]/tbody/tr[9]/td[3]""")
                                                Address109 = Address109.text
                                            except:
                                                pass
                                            try:
                                                Address110 = self.driver.find_element_by_xpath("""//*[@id="branchTable"]/tbody/tr[10]/td[3]""")
                                                Address110 = Address110.text
                                            except:
                                                pass


                                            try:

                                                self.driver.find_element_by_xpath("""// *[ @ id = "branchTable_next"] / a""").click()
                                            except:
                                                pass

                                            try:
                                                BranchCode111= self.driver.find_element_by_xpath("""// *[ @ id = "branchTable"] / tbody / tr[1] / td[1]""")
                                                BranchCode111= BranchCode111.text
                                            except:
                                                pass
                                            try:
                                                BranchCode112 = self.driver.find_element_by_xpath("""// *[ @ id = "branchTable"] / tbody / tr[2] / td[1]""")
                                                BranchCode112 = BranchCode112.text
                                            except:
                                                pass
                                            try:
                                                BranchCode113 = self.driver.find_element_by_xpath("""// *[ @ id = "branchTable"] / tbody / tr[3] / td[1]""")
                                                BranchCode113 = BranchCode113.text

                                            except:
                                                pass
                                            try:
                                                BranchCode114 = self.driver.find_element_by_xpath("""// *[ @ id = "branchTable"] / tbody / tr[4] / td[1]""")
                                                BranchCode114 = BranchCode114.text

                                            except:
                                                pass
                                            try:
                                                BranchCode115 = self.driver.find_element_by_xpath("""// *[ @ id = "branchTable"] / tbody / tr[5] / td[1]""")
                                                BranchCode115 = BranchCode115.text

                                            except:
                                                pass
                                            try:
                                                BranchCode116 = self.driver.find_element_by_xpath("""// *[ @ id = "branchTable"] / tbody / tr[6] / td[1]""")
                                                BranchCode116 = BranchCode116.text

                                            except:
                                                pass
                                            try:
                                                BranchCode117 = self.driver.find_element_by_xpath("""// *[ @ id = "branchTable"] / tbody / tr[7] / td[1]""")
                                                BranchCode117 = BranchCode117.text

                                            except:
                                                pass
                                            try:
                                                BranchCode118 = self.driver.find_element_by_xpath("""// *[ @ id = "branchTable"] / tbody / tr[8] / td[1]""")
                                                BranchCode118 = BranchCode118.text

                                            except:
                                                pass
                                            try:
                                                BranchCode119 = self.driver.find_element_by_xpath("""// *[ @ id = "branchTable"] / tbody / tr[9] / td[1]""")
                                                BranchCode119 = BranchCode119.text

                                            except:
                                                pass
                                            try:
                                                BranchCode120 = self.driver.find_element_by_xpath("""// *[ @ id = "branchTable"] / tbody / tr[10] / td[1]""")
                                                BranchCode120 = BranchCode120.text

                                            except:
                                                pass
                                            try:
                                                gstin111 = self.driver.find_element_by_xpath("""//*[@id="gst111"]""")
                                                gstin111 = gstin111.text
                                            except:
                                                pass
                                            try:
                                                gstin112 = self.driver.find_element_by_xpath("""//*[@id="gst112"]""")
                                                gstin112 = gstin112.text
                                            except:
                                                pass
                                            try:
                                                gstin113 = self.driver.find_element_by_xpath("""//*[@id="gst113"]""")
                                                gstin113 = gstin113.text
                                            except:
                                                pass
                                            try:
                                                gstin114 = self.driver.find_element_by_xpath("""//*[@id="gst114"]""")
                                                gstin114 = gstin114.text
                                            except:
                                                pass
                                            try:
                                                gstin115 = self.driver.find_element_by_xpath("""//*[@id="gst115"]""")
                                                gstin115 = gstin115.text
                                            except:
                                                pass
                                            try:
                                                gstin116 = self.driver.find_element_by_xpath("""//*[@id="gst116"]""")
                                                gstin116 = gstin116.text
                                            except:
                                                pass
                                            try:
                                                gstin117 = self.driver.find_element_by_xpath("""//*[@id="gst117"]""")
                                                gstin117 = gstin117.text
                                            except:
                                                pass
                                            try:
                                                gstin118 = self.driver.find_element_by_xpath("""//*[@id="gst118"]""")
                                                gstin118 = gstin118.text
                                            except:
                                                pass
                                            try:
                                                gstin119= self.driver.find_element_by_xpath("""//*[@id="gst119"]""")
                                                gstin119 = gstin119.text
                                            except:
                                                pass
                                            try:
                                                gstin120 = self.driver.find_element_by_xpath("""//*[@id="gst120"]""")
                                                gstin120 = gstin120.text
                                            except:
                                                pass
                                            try:
                                                Address111 = self.driver.find_element_by_xpath("""//*[@id="branchTable"]/tbody/tr[1]/td[3]""")
                                                Address111 = Address111.text
                                            except:
                                                pass
                                            try:
                                                Address112 = self.driver.find_element_by_xpath("""//*[@id="branchTable"]/tbody/tr[2]/td[3]""")
                                                Address112 = Address112.text
                                            except:
                                                pass
                                            try:
                                                Address113 = self.driver.find_element_by_xpath("""//*[@id="branchTable"]/tbody/tr[3]/td[3]""")
                                                Address113 = Address113.text
                                            except:
                                                pass
                                            try:
                                                Address114 = self.driver.find_element_by_xpath("""//*[@id="branchTable"]/tbody/tr[4]/td[3]""")
                                                Address114 = Address114.text
                                            except:
                                                pass
                                            try:
                                                Address115 = self.driver.find_element_by_xpath("""//*[@id="branchTable"]/tbody/tr[5]/td[3]""")
                                                Address115 = Address115.text
                                            except:
                                                pass
                                            try:
                                                Address116 = self.driver.find_element_by_xpath("""//*[@id="branchTable"]/tbody/tr[6]/td[3]""")
                                                Address116 = Address116.text
                                            except:
                                                pass
                                            try:
                                                Address117 = self.driver.find_element_by_xpath("""//*[@id="branchTable"]/tbody/tr[7]/td[3]""")
                                                Address117 = Address117.text
                                            except:
                                                pass
                                            try:
                                                Address118 = self.driver.find_element_by_xpath("""//*[@id="branchTable"]/tbody/tr[8]/td[3]""")
                                                Address118 = Address118.text
                                            except:
                                                pass
                                            try:
                                                Address119 = self.driver.find_element_by_xpath("""//*[@id="branchTable"]/tbody/tr[9]/td[3]""")
                                                Address119 = Address119.text
                                            except:
                                                pass
                                            try:
                                                Address120 = self.driver.find_element_by_xpath("""//*[@id="branchTable"]/tbody/tr[10]/td[3]""")
                                                Address120 = Address120.text
                                            except:
                                                pass

                                            try:

                                                self.driver.find_element_by_xpath("""// *[ @ id = "branchTable_next"] / a""").click()
                                            except:
                                                pass

                                            try:
                                                BranchCode121= self.driver.find_element_by_xpath("""// *[ @ id = "branchTable"] / tbody / tr[1] / td[1]""")
                                                BranchCode121= BranchCode121.text
                                            except:
                                                pass
                                            try:
                                                BranchCode122 = self.driver.find_element_by_xpath("""// *[ @ id = "branchTable"] / tbody / tr[2] / td[1]""")
                                                BranchCode122 = BranchCode122.text
                                            except:
                                                pass
                                            try:
                                                BranchCode123 = self.driver.find_element_by_xpath("""// *[ @ id = "branchTable"] / tbody / tr[3] / td[1]""")
                                                BranchCode123 = BranchCode123.text

                                            except:
                                                pass
                                            try:
                                                BranchCode124 = self.driver.find_element_by_xpath("""// *[ @ id = "branchTable"] / tbody / tr[4] / td[1]""")
                                                BranchCode124 = BranchCode124.text

                                            except:
                                                pass
                                            try:
                                                BranchCode125 = self.driver.find_element_by_xpath("""// *[ @ id = "branchTable"] / tbody / tr[5] / td[1]""")
                                                BranchCode125 = BranchCode125.text

                                            except:
                                                pass
                                            try:
                                                BranchCode126 = self.driver.find_element_by_xpath("""// *[ @ id = "branchTable"] / tbody / tr[6] / td[1]""")
                                                BranchCode126 = BranchCode126.text

                                            except:
                                                pass
                                            try:
                                                BranchCode127 = self.driver.find_element_by_xpath("""// *[ @ id = "branchTable"] / tbody / tr[7] / td[1]""")
                                                BranchCode127 = BranchCode127.text

                                            except:
                                                pass
                                            try:
                                                BranchCode128 = self.driver.find_element_by_xpath("""// *[ @ id = "branchTable"] / tbody / tr[8] / td[1]""")
                                                BranchCode128 = BranchCode128.text

                                            except:
                                                pass
                                            try:
                                                BranchCode129 = self.driver.find_element_by_xpath("""// *[ @ id = "branchTable"] / tbody / tr[9] / td[1]""")
                                                BranchCode129 = BranchCode129.text

                                            except:
                                                pass
                                            try:
                                                BranchCode130 = self.driver.find_element_by_xpath("""// *[ @ id = "branchTable"] / tbody / tr[10] / td[1]""")
                                                BranchCode130 = BranchCode130.text

                                            except:
                                                pass
                                            try:
                                                gstin121 = self.driver.find_element_by_xpath("""//*[@id="gst121"]""")
                                                gstin121 = gstin121.text
                                            except:
                                                pass
                                            try:
                                                gstin122 = self.driver.find_element_by_xpath("""//*[@id="gst122"]""")
                                                gstin122 = gstin122.text
                                            except:
                                                pass
                                            try:
                                                gstin123 = self.driver.find_element_by_xpath("""//*[@id="gst123"]""")
                                                gstin123 = gstin123.text
                                            except:
                                                pass
                                            try:
                                                gstin124 = self.driver.find_element_by_xpath("""//*[@id="gst124"]""")
                                                gstin124 = gstin124.text
                                            except:
                                                pass
                                            try:
                                                gstin125 = self.driver.find_element_by_xpath("""//*[@id="gst125"]""")
                                                gstin125 = gstin125.text
                                            except:
                                                pass
                                            try:
                                                gstin126 = self.driver.find_element_by_xpath("""//*[@id="gst126"]""")
                                                gstin126 = gstin126.text
                                            except:
                                                pass
                                            try:
                                                gstin127 = self.driver.find_element_by_xpath("""//*[@id="gst127"]""")
                                                gstin127 = gstin127.text
                                            except:
                                                pass
                                            try:
                                                gstin128 = self.driver.find_element_by_xpath("""//*[@id="gst128"]""")
                                                gstin128 = gstin128.text
                                            except:
                                                pass
                                            try:
                                                gstin129= self.driver.find_element_by_xpath("""//*[@id="gst129"]""")
                                                gstin129 = gstin129.text
                                            except:
                                                pass
                                            try:
                                                gstin130 = self.driver.find_element_by_xpath("""//*[@id="gst130"]""")
                                                gstin130 = gstin130.text
                                            except:
                                                pass
                                            try:
                                                Address121 = self.driver.find_element_by_xpath("""//*[@id="branchTable"]/tbody/tr[1]/td[3]""")
                                                Address121 = Address121.text
                                            except:
                                                pass
                                            try:
                                                Address122 = self.driver.find_element_by_xpath("""//*[@id="branchTable"]/tbody/tr[2]/td[3]""")
                                                Address122 = Address122.text
                                            except:
                                                pass
                                            try:
                                                Address123 = self.driver.find_element_by_xpath("""//*[@id="branchTable"]/tbody/tr[3]/td[3]""")
                                                Address123 = Address123.text
                                            except:
                                                pass
                                            try:
                                                Address124 = self.driver.find_element_by_xpath("""//*[@id="branchTable"]/tbody/tr[4]/td[3]""")
                                                Address124 = Address124.text
                                            except:
                                                pass
                                            try:
                                                Address125 = self.driver.find_element_by_xpath("""//*[@id="branchTable"]/tbody/tr[5]/td[3]""")
                                                Address125 = Address125.text
                                            except:
                                                pass
                                            try:
                                                Address126 = self.driver.find_element_by_xpath("""//*[@id="branchTable"]/tbody/tr[6]/td[3]""")
                                                Address126 = Address126.text
                                            except:
                                                pass
                                            try:
                                                Address127 = self.driver.find_element_by_xpath("""//*[@id="branchTable"]/tbody/tr[7]/td[3]""")
                                                Address127 = Address127.text
                                            except:
                                                pass
                                            try:
                                                Address128 = self.driver.find_element_by_xpath("""//*[@id="branchTable"]/tbody/tr[8]/td[3]""")
                                                Address128 = Address128.text
                                            except:
                                                pass
                                            try:
                                                Address129 = self.driver.find_element_by_xpath("""//*[@id="branchTable"]/tbody/tr[9]/td[3]""")
                                                Address129 = Address129.text
                                            except:
                                                pass
                                            try:
                                                Address130 = self.driver.find_element_by_xpath("""//*[@id="branchTable"]/tbody/tr[10]/td[3]""")
                                                Address130 = Address130.text
                                            except:
                                                pass

                                            if len(BranchCode130)>0:


                                                try:

                                                    self.driver.find_element_by_xpath("""// *[ @ id = "branchTable_next"] / a""").click()
                                                except:
                                                    pass


                                                try:
                                                    BranchCode131 = self.driver.find_element_by_xpath("""// *[ @ id = "branchTable"] / tbody / tr[1] / td[1]""")
                                                    BranchCode131 = BranchCode131.text

                                                except:
                                                    pass

                                                try:
                                                    BranchCode132 = self.driver.find_element_by_xpath(
                                                        """// *[ @ id = "branchTable"] / tbody / tr[2] / td[1]""")
                                                    BranchCode132 = BranchCode132.text
                                                except:
                                                    pass
                                                try:
                                                    BranchCode133 = self.driver.find_element_by_xpath(
                                                        """// *[ @ id = "branchTable"] / tbody / tr[3] / td[1]""")
                                                    BranchCode133 = BranchCode133.text

                                                except:
                                                    pass
                                                try:
                                                    BranchCode134 = self.driver.find_element_by_xpath(
                                                        """// *[ @ id = "branchTable"] / tbody / tr[4] / td[1]""")
                                                    BranchCode134 = BranchCode134.text

                                                except:
                                                    pass
                                                try:
                                                    BranchCode135 = self.driver.find_element_by_xpath(
                                                        """// *[ @ id = "branchTable"] / tbody / tr[5] / td[1]""")
                                                    BranchCode135 = BranchCode135.text

                                                except:
                                                    pass
                                                try:
                                                    BranchCode136 = self.driver.find_element_by_xpath(
                                                        """// *[ @ id = "branchTable"] / tbody / tr[6] / td[1]""")
                                                    BranchCode136 = BranchCode136.text

                                                except:
                                                    pass
                                                try:
                                                    BranchCode137 = self.driver.find_element_by_xpath(
                                                        """// *[ @ id = "branchTable"] / tbody / tr[7] / td[1]""")
                                                    BranchCode137 = BranchCode137.text

                                                except:
                                                    pass
                                                try:
                                                    BranchCode138 = self.driver.find_element_by_xpath(
                                                        """// *[ @ id = "branchTable"] / tbody / tr[8] / td[1]""")
                                                    BranchCode138 = BranchCode138.text

                                                except:
                                                    pass
                                                try:
                                                    BranchCode139 = self.driver.find_element_by_xpath(
                                                        """// *[ @ id = "branchTable"] / tbody / tr[9] / td[1]""")
                                                    BranchCode139 = BranchCode139.text

                                                except:
                                                    pass
                                                try:
                                                    BranchCode140 = self.driver.find_element_by_xpath(
                                                        """// *[ @ id = "branchTable"] / tbody / tr[10] / td[1]""")
                                                    BranchCode140 = BranchCode140.text

                                                except:
                                                    pass
                                                try:
                                                    gstin131 = self.driver.find_element_by_xpath(
                                                        """//*[@id="gst131"]""")
                                                    gstin131 = gstin131.text
                                                except:
                                                    pass
                                                try:
                                                    gstin132 = self.driver.find_element_by_xpath(
                                                        """//*[@id="gst132"]""")
                                                    gstin132 = gstin132.text
                                                except:
                                                    pass
                                                try:
                                                    gstin133 = self.driver.find_element_by_xpath(
                                                        """//*[@id="gst133"]""")
                                                    gstin133 = gstin133.text
                                                except:
                                                    pass
                                                try:
                                                    gstin134 = self.driver.find_element_by_xpath(
                                                        """//*[@id="gst134"]""")
                                                    gstin134 = gstin134.text
                                                except:
                                                    pass
                                                try:
                                                    gstin135 = self.driver.find_element_by_xpath(
                                                        """//*[@id="gst135"]""")
                                                    gstin135 = gstin135.text
                                                except:
                                                    pass
                                                try:
                                                    gstin136 = self.driver.find_element_by_xpath(
                                                        """//*[@id="gst136"]""")
                                                    gstin136 = gstin136.text
                                                except:
                                                    pass
                                                try:
                                                    gstin137 = self.driver.find_element_by_xpath(
                                                        """//*[@id="gst137"]""")
                                                    gstin137 = gstin137.text
                                                except:
                                                    pass
                                                try:
                                                    gstin138 = self.driver.find_element_by_xpath(
                                                        """//*[@id="gst138"]""")
                                                    gstin138 = gstin138.text
                                                except:
                                                    pass
                                                try:
                                                    gstin139 = self.driver.find_element_by_xpath(
                                                        """//*[@id="gst139"]""")
                                                    gstin139 = gstin139.text
                                                except:
                                                    pass
                                                try:
                                                    gstin140 = self.driver.find_element_by_xpath(
                                                        """//*[@id="gst140"]""")
                                                    gstin140 = gstin140.text
                                                except:
                                                    pass
                                                try:
                                                    Address131 = self.driver.find_element_by_xpath(
                                                        """//*[@id="branchTable"]/tbody/tr[1]/td[3]""")
                                                    Address131 = Address131.text
                                                except:
                                                    pass
                                                try:
                                                    Address132 = self.driver.find_element_by_xpath(
                                                        """//*[@id="branchTable"]/tbody/tr[2]/td[3]""")
                                                    Address132 = Address132.text
                                                except:
                                                    pass
                                                try:
                                                    Address133 = self.driver.find_element_by_xpath(
                                                        """//*[@id="branchTable"]/tbody/tr[3]/td[3]""")
                                                    Address133 = Address133.text
                                                except:
                                                    pass
                                                try:
                                                    Address134 = self.driver.find_element_by_xpath(
                                                        """//*[@id="branchTable"]/tbody/tr[4]/td[3]""")
                                                    Address134 = Address134.text
                                                except:
                                                    pass
                                                try:
                                                    Address135 = self.driver.find_element_by_xpath(
                                                        """//*[@id="branchTable"]/tbody/tr[5]/td[3]""")
                                                    Address135 = Address135.text
                                                except:
                                                    pass
                                                try:
                                                    Address136 = self.driver.find_element_by_xpath(
                                                        """//*[@id="branchTable"]/tbody/tr[6]/td[3]""")
                                                    Address136 = Address136.text
                                                except:
                                                    pass
                                                try:
                                                    Address137 = self.driver.find_element_by_xpath(
                                                        """//*[@id="branchTable"]/tbody/tr[7]/td[3]""")
                                                    Address137 = Address137.text
                                                except:
                                                    pass
                                                try:
                                                    Address138 = self.driver.find_element_by_xpath(
                                                        """//*[@id="branchTable"]/tbody/tr[8]/td[3]""")
                                                    Address138 = Address138.text
                                                except:
                                                    pass
                                                try:
                                                    Address139 = self.driver.find_element_by_xpath(
                                                        """//*[@id="branchTable"]/tbody/tr[9]/td[3]""")
                                                    Address139 = Address139.text
                                                except:
                                                    pass
                                                try:
                                                    Address140 = self.driver.find_element_by_xpath(
                                                        """//*[@id="branchTable"]/tbody/tr[10]/td[3]""")
                                                    Address140 = Address140.text
                                                except:
                                                    pass

                                                try:

                                                    self.driver.find_element_by_xpath("""// *[ @ id = "branchTable_next"] / a""").click()
                                                except:
                                                    pass


                                                try:
                                                    BranchCode141 = self.driver.find_element_by_xpath("""// *[ @ id = "branchTable"] / tbody / tr[2] / td[1]""")
                                                    BranchCode141 = BranchCode141.text

                                                except:
                                                    pass

                                                try:
                                                    BranchCode142 = self.driver.find_element_by_xpath(
                                                        """// *[ @ id = "branchTable"] / tbody / tr[2] / td[1]""")
                                                    BranchCode142 = BranchCode142.text
                                                except:
                                                    pass
                                                try:
                                                    BranchCode143 = self.driver.find_element_by_xpath(
                                                        """// *[ @ id = "branchTable"] / tbody / tr[3] / td[1]""")
                                                    BranchCode143 = BranchCode143.text

                                                except:
                                                    pass
                                                try:
                                                    BranchCode144 = self.driver.find_element_by_xpath(
                                                        """// *[ @ id = "branchTable"] / tbody / tr[4] / td[1]""")
                                                    BranchCode144 = BranchCode144.text

                                                except:
                                                    pass
                                                try:
                                                    BranchCode145 = self.driver.find_element_by_xpath(
                                                        """// *[ @ id = "branchTable"] / tbody / tr[5] / td[1]""")
                                                    BranchCode145 = BranchCode145.text

                                                except:
                                                    pass
                                                try:
                                                    BranchCode146 = self.driver.find_element_by_xpath(
                                                        """// *[ @ id = "branchTable"] / tbody / tr[6] / td[1]""")
                                                    BranchCode146 = BranchCode146.text

                                                except:
                                                    pass
                                                try:
                                                    BranchCode147 = self.driver.find_element_by_xpath(
                                                        """// *[ @ id = "branchTable"] / tbody / tr[7] / td[1]""")
                                                    BranchCode147 = BranchCode147.text

                                                except:
                                                    pass
                                                try:
                                                    BranchCode148 = self.driver.find_element_by_xpath(
                                                        """// *[ @ id = "branchTable"] / tbody / tr[8] / td[2]""")
                                                    BranchCode148 = BranchCode148.text

                                                except:
                                                    pass
                                                try:
                                                    BranchCode149 = self.driver.find_element_by_xpath(
                                                        """// *[ @ id = "branchTable"] / tbody / tr[9] / td[1]""")
                                                    BranchCode149 = BranchCode149.text

                                                except:
                                                    pass
                                                try:
                                                    BranchCode150 = self.driver.find_element_by_xpath(
                                                        """// *[ @ id = "branchTable"] / tbody / tr[10] / td[1]""")
                                                    BranchCode150 = BranchCode150.text

                                                except:
                                                    pass
                                                try:
                                                    gstin141 = self.driver.find_element_by_xpath(
                                                        """//*[@id="gst141"]""")
                                                    gstin141 = gstin141.text
                                                except:
                                                    pass
                                                try:
                                                    gstin142 = self.driver.find_element_by_xpath(
                                                        """//*[@id="gst142"]""")
                                                    gstin142 = gstin142.text
                                                except:
                                                    pass
                                                try:
                                                    gstin143 = self.driver.find_element_by_xpath(
                                                        """//*[@id="gst143"]""")
                                                    gstin143 = gstin143.text
                                                except:
                                                    pass
                                                try:
                                                    gstin144 = self.driver.find_element_by_xpath(
                                                        """//*[@id="gst144"]""")
                                                    gstin144 = gstin144.text
                                                except:
                                                    pass
                                                try:
                                                    gstin145 = self.driver.find_element_by_xpath(
                                                        """//*[@id="gst145"]""")
                                                    gstin145 = gstin145.text
                                                except:
                                                    pass
                                                try:
                                                    gstin146 = self.driver.find_element_by_xpath(
                                                        """//*[@id="gst146"]""")
                                                    gstin146 = gstin146.text
                                                except:
                                                    pass
                                                try:
                                                    gstin147 = self.driver.find_element_by_xpath(
                                                        """//*[@id="gst147"]""")
                                                    gstin147 = gstin147.text
                                                except:
                                                    pass
                                                try:
                                                    gstin148 = self.driver.find_element_by_xpath(
                                                        """//*[@id="gst148"]""")
                                                    gstin148 = gstin148.text
                                                except:
                                                    pass
                                                try:
                                                    gstin149 = self.driver.find_element_by_xpath(
                                                        """//*[@id="gst149"]""")
                                                    gstin149 = gstin149.text
                                                except:
                                                    pass
                                                try:
                                                    gstin150 = self.driver.find_element_by_xpath(
                                                        """//*[@id="gst150"]""")
                                                    gstin150 = gstin150.text
                                                except:
                                                    pass
                                                try:
                                                    Address141 = self.driver.find_element_by_xpath(
                                                        """//*[@id="branchTable"]/tbody/tr[1]/td[3]""")
                                                    Address141 = Address141.text
                                                except:
                                                    pass
                                                try:
                                                    Address142 = self.driver.find_element_by_xpath(
                                                        """//*[@id="branchTable"]/tbody/tr[2]/td[3]""")
                                                    Address142 = Address142.text
                                                except:
                                                    pass
                                                try:
                                                    Address143 = self.driver.find_element_by_xpath(
                                                        """//*[@id="branchTable"]/tbody/tr[3]/td[4]""")
                                                    Address143 = Address143.text
                                                except:
                                                    pass
                                                try:
                                                    Address144 = self.driver.find_element_by_xpath(
                                                        """//*[@id="branchTable"]/tbody/tr[4]/td[3]""")
                                                    Address144 = Address144.text
                                                except:
                                                    pass
                                                try:
                                                    Address145 = self.driver.find_element_by_xpath(
                                                        """//*[@id="branchTable"]/tbody/tr[5]/td[3]""")
                                                    Address145 = Address145.text
                                                except:
                                                    pass
                                                try:
                                                    Address146 = self.driver.find_element_by_xpath(
                                                        """//*[@id="branchTable"]/tbody/tr[6]/td[3]""")
                                                    Address146 = Address146.text
                                                except:
                                                    pass
                                                try:
                                                    Address147 = self.driver.find_element_by_xpath(
                                                        """//*[@id="branchTable"]/tbody/tr[7]/td[3]""")
                                                    Address147 = Address147.text
                                                except:
                                                    pass
                                                try:
                                                    Address148 = self.driver.find_element_by_xpath(
                                                        """//*[@id="branchTable"]/tbody/tr[8]/td[3]""")
                                                    Address148 = Address148.text
                                                except:
                                                    pass
                                                try:
                                                    Address149 = self.driver.find_element_by_xpath(
                                                        """//*[@id="branchTable"]/tbody/tr[9]/td[3]""")
                                                    Address149 = Address149.text
                                                except:
                                                    pass
                                                try:
                                                    Address150 = self.driver.find_element_by_xpath(
                                                        """//*[@id="branchTable"]/tbody/tr[10]/td[3]""")
                                                    Address150 = Address150.text
                                                except:
                                                    pass





                try:
                    serialNumber1 = self.driver.find_element_by_xpath("""//*[@id="directorTable"]/tbody/tr[1]/td[1]""")
                    serialNumber1 = serialNumber1.text
                except:
                    pass
                try:
                    serialNumber2 = self.driver.find_element_by_xpath("""//*[@id="directorTable"]/tbody/tr[2]/td[1]""")
                    serialNumber2 = serialNumber2.text
                except:
                    pass
                try:
                    serialNumber3 = self.driver.find_element_by_xpath("""//*[@id="directorTable"]/tbody/tr[3]/td[1]""")
                    serialNumber3 = serialNumber3.text
                except:
                    pass
                try:
                    serialNumber4 = self.driver.find_element_by_xpath("""//*[@id="directorTable"]/tbody/tr[4]/td[1]""")
                    serialNumber4 = serialNumber4.text
                except:
                    pass
                try:
                    serialNumber5 = self.driver.find_element_by_xpath("""//*[@id="directorTable"]/tbody/tr[5]/td[1]""")
                    serialNumber5 = serialNumber5.text
                except:
                    pass
                try:
                    serialNumber6 = self.driver.find_element_by_xpath("""//*[@id="directorTable"]/tbody/tr[6]/td[1]""")
                    serialNumber6 = serialNumber6.text
                except:
                    pass
                try:
                    serialNumber7 = self.driver.find_element_by_xpath("""//*[@id="directorTable"]/tbody/tr[7]/td[1]""")
                    serialNumber7 = serialNumber7.text
                except:
                    pass
                try:
                    serialNumber8 = self.driver.find_element_by_xpath("""//*[@id="directorTable"]/tbody/tr[8]/td[1]""")
                    serialNumber8 = serialNumber8.text
                except:
                    pass
                try:
                    serialNumber9 = self.driver.find_element_by_xpath("""//*[@id="directorTable"]/tbody/tr[9]/td[1]""")
                    serialNumber9 = serialNumber9.text
                except:
                    pass
                try:
                    serialNumber10 = self.driver.find_element_by_xpath("""//*[@id="directorTable"]/tbody/tr[10]/td[1]""")
                    serialNumber10 = serialNumber10.text
                except:
                    pass
                try:
                    directorName1 = self.driver.find_element_by_xpath("""/html/body/div[1]/div[9]/div/div/div[1]/div/div/div[1]/div[2]/div/div/div[10]/div/div/div/div/div[2]/div/table/tbody/tr[1]/td[2]""")
                    directorName1 = directorName1.text
                except:
                    pass
                try:
                    directorName2 = self.driver.find_element_by_xpath("""/html/body/div[1]/div[9]/div/div/div[1]/div/div/div[1]/div[2]/div/div/div[10]/div/div/div/div/div[2]/div/table/tbody/tr[2]/td[2]""")
                    directorName2 = directorName2.text
                except:
                    pass
                try:
                    directorName3 = self.driver.find_element_by_xpath("""/html/body/div[1]/div[9]/div/div/div[1]/div/div/div[1]/div[2]/div/div/div[10]/div/div/div/div/div[2]/div/table/tbody/tr[3]/td[2]""")
                    directorName3 = directorName3.text
                except:
                    pass
                try:
                    directorName4 = self.driver.find_element_by_xpath("""/html/body/div[1]/div[9]/div/div/div[1]/div/div/div[1]/div[2]/div/div/div[10]/div/div/div/div/div[2]/div/table/tbody/tr[4]/td[2]""")
                    directorName4 = directorName4.text
                except:
                    pass
                try:
                    directorName5 = self.driver.find_element_by_xpath("""/html/body/div[1]/div[9]/div/div/div[1]/div/div/div[1]/div[2]/div/div/div[10]/div/div/div/div/div[2]/div/table/tbody/tr[5]/td[2]""")
                    directorName5 = directorName5.text
                except:
                    pass
                try:
                    directorName6 = self.driver.find_element_by_xpath("""/html/body/div[1]/div[9]/div/div/div[1]/div/div/div[1]/div[2]/div/div/div[10]/div/div/div/div/div[2]/div/table/tbody/tr[6]/td[2]""")
                    directorName6 = directorName6.text
                except:
                    pass
                try:
                    directorName7 = self.driver.find_element_by_xpath("""/html/body/div[1]/div[9]/div/div/div[1]/div/div/div[1]/div[2]/div/div/div[10]/div/div/div/div/div[2]/div/table/tbody/tr[7]/td[2]""")
                    directorName7 = directorName7.text
                except:
                    pass
                try:
                    directorName8 = self.driver.find_element_by_xpath("""/html/body/div[1]/div[9]/div/div/div[1]/div/div/div[1]/div[2]/div/div/div[10]/div/div/div/div/div[2]/div/table/tbody/tr[8]/td[2]""")
                    directorName8 = directorName8.text
                except:
                    pass
                try:
                    directorName9 = self.driver.find_element_by_xpath("""/html/body/div[1]/div[9]/div/div/div[1]/div/div/div[1]/div[2]/div/div/div[10]/div/div/div/div/div[2]/div/table/tbody/tr[9]/td[2]""")
                    directorName9 = directorName9.text
                except:
                    pass
                try:
                    directorName10 = self.driver.find_element_by_xpath("""/html/body/div[1]/div[9]/div/div/div[1]/div/div/div[1]/div[2]/div/div/div[10]/div/div/div/div/div[2]/div/table/tbody/tr[10]/td[2]""")
                    directorName10 = directorName10.text
                except:
                    pass
                try:
                    panNumber1 = self.driver.find_element_by_xpath("""//*[@id="pan1"]""")
                    panNumber1 = panNumber1.text
                except:
                    pass
                try:
                    panNumber2 = self.driver.find_element_by_xpath("""//*[@id="pan2"]""")
                    panNumber2 = panNumber2.text
                except:
                    pass
                try:
                    panNumber3 = self.driver.find_element_by_xpath("""//*[@id="pan3"]""")
                    panNumber3 = panNumber3.text
                except:
                    pass
                try:
                    panNumber4 = self.driver.find_element_by_xpath("""//*[@id="pan4"]""")
                    panNumber4 = panNumber4.text
                except:
                    pass
                try:
                    panNumber5 = self.driver.find_element_by_xpath("""//*[@id="pan5"]""")
                    panNumber5 = panNumber5.text
                except:
                    pass
                try:
                    panNumber6 = self.driver.find_element_by_xpath("""//*[@id="pan6"]""")
                    panNumber6 = panNumber6.text
                except:
                    pass
                try:
                    panNumber7 = self.driver.find_element_by_xpath("""//*[@id="pan7"]""")
                    panNumber7 = panNumber7.text
                except:
                    pass
                try:
                    panNumber8 = self.driver.find_element_by_xpath("""//*[@id="pan8"]""")
                    panNumber8 = panNumber8.text
                except:
                    pass
                try:
                    panNumber9 = self.driver.find_element_by_xpath("""//*[@id="pan9"]""")
                    panNumber9 = panNumber9.text
                except:
                    pass
                try:
                    panNumber10 = self.driver.find_element_by_xpath("""//*[@id="pan10"]""")
                    panNumber10 = panNumber10.text
                except:
                    pass
                try:
                    self.driver.find_element_by_xpath("""//*[@id="directorTable_next"]/a""").click()
                except:
                    pass
                try:
                    panNumber11 = self.driver.find_element_by_xpath("""//*[@id="pan11"]""")
                    panNumber11 = panNumber11.text
                except:
                    pass
                try:
                    panNumber12 = self.driver.find_element_by_xpath("""//*[@id="pan12"]""")
                    panNumber12 = panNumber12.text
                except:
                    pass
                try:
                    panNumber13 = self.driver.find_element_by_xpath("""//*[@id="pan13"]""")
                    panNumber13 = panNumber13.text
                except:
                    pass
                try:
                    panNumber14 = self.driver.find_element_by_xpath("""//*[@id="pan14"]""")
                    panNumber14 = panNumber14.text
                except:
                    pass
                try:
                    panNumber15 = self.driver.find_element_by_xpath("""//*[@id="pan15"]""")
                    panNumber15 = panNumber15.text
                except:
                    pass
                try:
                    panNumber16 = self.driver.find_element_by_xpath("""//*[@id="pan16"]""")
                    panNumber16 = panNumber16.text
                except:
                    pass
                try:
                    panNumber17 = self.driver.find_element_by_xpath("""//*[@id="pan17"]""")
                    panNumber17 = panNumber17.text
                except:
                    pass
                try:
                    panNumber18 = self.driver.find_element_by_xpath("""//*[@id="pan18"]""")
                    panNumber18 = panNumber18.text
                except:
                    pass
                try:
                    panNumber19 = self.driver.find_element_by_xpath("""//*[@id="pan19"]""")
                    panNumber19 = panNumber19.text
                except:
                    pass
                try:
                    panNumber20 = self.driver.find_element_by_xpath("""//*[@id="pan20"]""")
                    panNumber20 = panNumber20.text
                except:
                    pass
                try:
                    serialNumber11 = self.driver.find_element_by_xpath("""//*[@id="directorTable"]/tbody/tr[1]/td[1]""")
                    serialNumber11 = serialNumber11.text
                except:
                    pass
                try:
                    serialNumber12 = self.driver.find_element_by_xpath("""//*[@id="directorTable"]/tbody/tr[2]/td[1]""")
                    serialNumber12 = serialNumber12.text
                except:
                    pass
                try:
                    serialNumber13 = self.driver.find_element_by_xpath("""//*[@id="directorTable"]/tbody/tr[3]/td[1]""")
                    serialNumber13 = serialNumber13.text
                except:
                    pass
                try:
                    serialNumber14 = self.driver.find_element_by_xpath("""//*[@id="directorTable"]/tbody/tr[4]/td[1]""")
                    serialNumber14 = serialNumber14.text
                except:
                    pass
                try:
                    serialNumber15 = self.driver.find_element_by_xpath("""//*[@id="directorTable"]/tbody/tr[5]/td[1]""")
                    serialNumber15 = serialNumber15.text
                except:
                    pass
                try:
                    serialNumber16 = self.driver.find_element_by_xpath("""//*[@id="directorTable"]/tbody/tr[6]/td[1]""")
                    serialNumber16 = serialNumber16.text
                except:
                    pass
                try:
                    serialNumber17 = self.driver.find_element_by_xpath("""//*[@id="directorTable"]/tbody/tr[7]/td[1]""")
                    serialNumber17 = serialNumber17.text
                except:
                    pass
                try:
                    serialNumber18 = self.driver.find_element_by_xpath("""//*[@id="directorTable"]/tbody/tr[8]/td[1]""")
                    serialNumber18 = serialNumber18.text
                except:
                    pass
                try:
                    serialNumber19 = self.driver.find_element_by_xpath("""//*[@id="directorTable"]/tbody/tr[9]/td[1]""")
                    serialNumber19 = serialNumber19.text
                except:
                    pass
                try:
                    serialNumber20 = self.driver.find_element_by_xpath("""//*[@id="directorTable"]/tbody/tr[10]/td[1]""")
                    serialNumber20 = serialNumber20.text
                except:
                    pass
                try:
                    directorName11 = self.driver.find_element_by_xpath("""//*[@id="directorTable"]/tbody/tr[1]/td[2]""")
                    directorName11 = directorName11.text
                except:
                    pass

                try:
                    directorName12 = self.driver.find_element_by_xpath("""//*[@id="directorTable"]/tbody/tr[2]/td[2]""")
                    directorName12 = directorName12.text
                except:
                    pass
                try:
                    directorName13 = self.driver.find_element_by_xpath("""//*[@id="directorTable"]/tbody/tr[3]/td[2]""")
                    directorName13 = directorName13.text
                except:
                    pass
                try:
                    directorName14 = self.driver.find_element_by_xpath("""//*[@id="directorTable"]/tbody/tr[4]/td[2]""")
                    directorName14 = directorName14.text
                except:
                    pass
                try:
                    directorName15 = self.driver.find_element_by_xpath("""//*[@id="directorTable"]/tbody/tr[5]/td[2]""")
                    directorName15 = directorName15.text
                except:
                    pass
                try:
                    directorName16 = self.driver.find_element_by_xpath("""//*[@id="directorTable"]/tbody/tr[6]/td[2]""")
                    directorName16 = directorName16.text
                except:
                    pass
                try:
                    directorName17 = self.driver.find_element_by_xpath("""//*[@id="directorTable"]/tbody/tr[7]/td[2]""")
                    directorName17 = directorName17.text
                except:
                    pass
                try:
                    directorName18 = self.driver.find_element_by_xpath("""//*[@id="directorTable"]/tbody/tr[8]/td[2]""")
                    directorName18 = directorName18.text
                except:
                    pass
                try:
                    directorName19 = self.driver.find_element_by_xpath("""//*[@id="directorTable"]/tbody/tr[9]/td[2]""")
                    directorName19 = directorName19.text
                except:
                    pass
                try:
                    directorName20 = self.driver.find_element_by_xpath("""//*[@id="directorTable"]/tbody/tr[10]/td[2]""")
                    directorName20 = directorName20.text
                except:
                    pass
                try:
                    self.driver.find_element_by_xpath("""//*[@id="directorTable_next"]/a""").click()
                except:
                    pass
                try:
                    panNumber21 = self.driver.find_element_by_xpath("""//*[@id="pan21"]""")
                    panNumber21 = panNumber21.text
                except:
                    pass
                try:
                    panNumber22 = self.driver.find_element_by_xpath("""//*[@id="pan22"]""")
                    panNumber22 = panNumber22.text
                except:
                    pass
                try:
                    panNumber23 = self.driver.find_element_by_xpath("""//*[@id="pan23"]""")
                    panNumber23 = panNumber23.text
                except:
                    pass
                try:
                    panNumber24 = self.driver.find_element_by_xpath("""//*[@id="pan24"]""")
                    panNumber24 = panNumber24.text
                except:
                    pass
                try:
                    panNumber25 = self.driver.find_element_by_xpath("""//*[@id="pan25"]""")
                    panNumber25 = panNumber25.text
                except:
                    pass
                try:
                    panNumber26 = self.driver.find_element_by_xpath("""//*[@id="pan26"]""")
                    panNumber26 = panNumber26.text
                except:
                    pass
                try:
                    panNumber27 = self.driver.find_element_by_xpath("""//*[@id="pan27"]""")
                    panNumber27 = panNumber27.text
                except:
                    pass
                try:
                    panNumber28 = self.driver.find_element_by_xpath("""//*[@id="pan28"]""")
                    panNumber28 = panNumber28.text
                except:
                    pass
                try:
                    panNumber29 = self.driver.find_element_by_xpath("""//*[@id="pan29"]""")
                    panNumber29 = panNumber29.text
                except:
                    pass
                try:
                    panNumber30 = self.driver.find_element_by_xpath("""//*[@id="pan30"]""")
                    panNumber30 = panNumber30.text
                except:
                    pass
                try:
                    serialNumber21 = self.driver.find_element_by_xpath("""//*[@id="directorTable"]/tbody/tr[21]/td[1]""")
                    serialNumber21 = serialNumber21.text
                except:
                    pass
                try:
                    serialNumber22 = self.driver.find_element_by_xpath("""//*[@id="directorTable"]/tbody/tr[22]/td[1]""")
                    serialNumber22 = serialNumber22.text
                except:
                    pass
                try:
                    serialNumber23 = self.driver.find_element_by_xpath("""//*[@id="directorTable"]/tbody/tr[23]/td[1]""")
                    serialNumber23 = serialNumber23.text
                except:
                    pass
                try:
                    serialNumber24 = self.driver.find_element_by_xpath("""//*[@id="directorTable"]/tbody/tr[24]/td[1]""")
                    serialNumber24 = serialNumber24.text
                except:
                    pass
                try:
                    serialNumber25 = self.driver.find_element_by_xpath("""//*[@id="directorTable"]/tbody/tr[25]/td[1]""")
                    serialNumber25 = serialNumber25.text
                except:
                    pass
                try:
                    serialNumber26 = self.driver.find_element_by_xpath("""//*[@id="directorTable"]/tbody/tr[26]/td[1]""")
                    serialNumber26 = serialNumber26.text
                except:
                    pass
                try:
                    serialNumber27 = self.driver.find_element_by_xpath("""//*[@id="directorTable"]/tbody/tr[27]/td[1]""")
                    serialNumber27 = serialNumber27.text
                except:
                    pass
                try:
                    serialNumber28 = self.driver.find_element_by_xpath("""//*[@id="directorTable"]/tbody/tr[28]/td[1]""")
                    serialNumber28 = serialNumber28.text
                except:
                    pass
                try:
                    serialNumber29 = self.driver.find_element_by_xpath("""//*[@id="directorTable"]/tbody/tr[29]/td[1]""")
                    serialNumber29 = serialNumber29.text
                except:
                    pass
                try:
                    serialNumber30 = self.driver.find_element_by_xpath("""//*[@id="directorTable"]/tbody/tr[30]/td[1]""")
                    serialNumber30 = serialNumber30.text
                except:
                    pass
                try:
                    directorName21 = self.driver.find_element_by_xpath("""//*[@id="directorTable"]/tbody/tr[21]/td[3]""")
                    directorName21 = directorName21.text
                except:
                    pass
                try:
                    directorName22 = self.driver.find_element_by_xpath("""//*[@id="directorTable"]/tbody/tr[22]/td[3]""")
                    directorName22 = directorName22.text
                except:
                    pass
                try:
                    directorName23 = self.driver.find_element_by_xpath("""//*[@id="directorTable"]/tbody/tr[23]/td[3]""")
                    directorName23 = directorName23.text
                except:
                    pass
                try:
                    directorName24 = self.driver.find_element_by_xpath("""//*[@id="directorTable"]/tbody/tr[24]/td[3]""")
                    directorName24 = directorName24.text
                except:
                    pass
                try:
                    directorName25 = self.driver.find_element_by_xpath("""//*[@id="directorTable"]/tbody/tr[25]/td[3]""")
                    directorName25 = directorName25.text
                except:
                    pass
                try:
                    directorName26 = self.driver.find_element_by_xpath("""//*[@id="directorTable"]/tbody/tr[26]/td[3]""")
                    directorName26 = directorName26.text
                except:
                    pass
                try:
                    directorName27 = self.driver.find_element_by_xpath("""//*[@id="directorTable"]/tbody/tr[27]/td[3]""")
                    directorName27 = directorName27.text
                except:
                    pass
                try:
                    directorName28 = self.driver.find_element_by_xpath("""//*[@id="directorTable"]/tbody/tr[28]/td[3]""")
                    directorName28 = directorName28.text
                except:
                    pass
                try:
                    directorName29 = self.driver.find_element_by_xpath("""//*[@id="directorTable"]/tbody/tr[29]/td[3]""")
                    directorName29 = directorName29.text
                except:
                    pass
                try:
                    directorName30 = self.driver.find_element_by_xpath("""//*[@id="directorTable"]/tbody/tr[30]/td[3]""")
                    directorName30 = directorName30.text
                except:
                    pass

                self.driver.find_element_by_xpath("""//*[@id="custom-accordion"]/div[2]/div[1]/a""").click()
                time.sleep(1)
                try:
                    serial1 = self.driver.find_element_by_xpath("""//*[@id="rcmcTable"]/tbody/tr[1]/td[1]""")
                    serial1 = serial1.text
                except:
                    pass

                try:
                    serial2 = self.driver.find_element_by_xpath("""//*[@id="rcmcTable"]/tbody/tr[2]/td[1]""")
                    serial2 = serial2.text
                except:
                    pass
                try:
                    rcmc1 = self.driver.find_element_by_xpath("""//*[@id="rcmcTable"]/tbody/tr[1]/td[2]""")
                    rcmc1 = rcmc1.text
                except:
                    pass

                try:
                    rcmc2 = self.driver.find_element_by_xpath("""//*[@id="rcmcTable"]/tbody/tr[2]/td[2]""")
                    rcmc2 = rcmc2.text
                except:
                    pass
                try:
                    issuedate1 = self.driver.find_element_by_xpath("""//*[@id="rcmcTable"]/tbody/tr[1]/td[3]""")
                    issuedate1 = issuedate1.text
                    from datetime import datetime
                    date_obj = datetime.strptime(issuedate1, '%d/%m/%Y')
                    issuedate1 = date_obj.strftime('%d-%b-%Y')
                except:
                    pass

                try:
                    issuedate2 = self.driver.find_element_by_xpath("""//*[@id="rcmcTable"]/tbody/tr[2]/td[3]""")
                    issuedate2 = issuedate2.text
                    from datetime import datetime
                    date_obj = datetime.strptime(issuedate2, '%d/%m/%Y')
                    issuedate2 = date_obj.strftime('%d-%b-%Y')
                except:
                    pass

                try:
                    issueauthority1 = self.driver.find_element_by_xpath("""//*[@id="rcmcTable"]/tbody/tr[1]/td[4]""")
                    issueauthority1 = issueauthority1.text
                except:
                    pass

                try:
                    issueauthority2 = self.driver.find_element_by_xpath("""//*[@id="rcmcTable"]/tbody/tr[2]/td[4]""")
                    issueauthority2 = issueauthority2.text
                except:
                    pass
                try:
                    expirydatess1 = self.driver.find_element_by_xpath("""//*[@id="rcmcTable"]/tbody/tr[1]/td[6]""")
                    expirydatess1 = expirydatess1.text
                    from datetime import datetime
                    date_obj = datetime.strptime(expirydatess1, '%d/%m/%Y')
                    expirydatess1 = date_obj.strftime('%d-%b-%Y')
                except:
                    pass

                try:
                    expirydatess2 = self.driver.find_element_by_xpath("""//*[@id="rcmcTable"]/tbody/tr[2]/td[6]""")
                    expirydatess2 = expirydatess2.text
                    from datetime import datetime
                    date_obj = datetime.strptime(expirydatess2, '%d/%m/%Y')
                    expirydatess2 = date_obj.strftime('%d-%b-%Y')
                except:
                    pass

                try:
                    statuss1 = self.driver.find_element_by_xpath("""//*[@id="rcmcTable"]/tbody/tr[1]/td[7]""")
                    statuss1 = statuss1.text
                except:
                    pass

                try:
                    statuss2 = self.driver.find_element_by_xpath("""//*[@id="rcmcTable"]/tbody/tr[2]/td[7]""")
                    statuss2 = statuss2.text
                except:
                    pass

                try:
                    expotertype1 = self.driver.find_element_by_xpath("""//*[@id="rcmcTable"]/tbody/tr[1]/td[8]""")
                    expotertype1 = expotertype1.text
                except:
                    pass

                try:
                    expotertype2 = self.driver.find_element_by_xpath("""//*[@id="rcmcTable"]/tbody/tr[2]/td[8]""")
                    expotertype2 = expotertype2.text
                except:
                    pass

                try:
                    statusfromepc1 = self.driver.find_element_by_xpath("""//*[@id="rcmcTable"]/tbody/tr[1]/td[10]""")
                    statusfromepc1 = statusfromepc1.text
                except:
                    pass

                try:
                    statusfromepc2 = self.driver.find_element_by_xpath("""//*[@id="rcmcTable"]/tbody/tr[2]/td[10]""")
                    statusfromepc2 = statusfromepc2.text
                except:
                    pass
                try:
                    if iecNumber == '0388031964':
                        statusfromepc1 = 'N'
                        statusfromepc2 = 'N'
                except:
                    pass

                try:
                    if len(issueauthority1) > 0:

                        Fe1 = {}
                        Fe1["rcmcNumber"] = rcmc1
                        Fe1["issueDate"] = issuedate1
                        Fe1["expiryDate"] = expirydatess1
                        Fe1["issueAuthority"] = issueauthority1
                        Fe1["serialNumber"] = serial1
                        Fe1["status"] = statuss1
                        Fe1["exporterType"] = expotertype1
                        Fe1["statusFromEpc"] = statusfromepc1

                    else:
                        Fe1 = {}
                except:
                    Fe1 = {}
                    pass

                try:
                    if len(issueauthority2) > 0:
                        Fe2 = {}
                        Fe2["rcmcNumber"] = rcmc2
                        Fe2["issueDate"] = issuedate2
                        Fe2["expiryDate"] = expirydatess2
                        Fe2["issueAuthority"] = issueauthority2
                        Fe2["serialNumber"] = serial2
                        Fe2["status"] = statuss2
                        Fe2["exporterType"] = expotertype2
                        Fe2["statusFromEpc"] = statusfromepc2

                    else:
                        Fe2 = {}
                except:
                    Fe2 = {}
                    pass
                try:
                    if len(serialNumber2) > 0:
                        De1 = {}
                        De1['directorName'] = directorName1
                        De1['serialNumber'] = serialNumber1
                        De1['panNumber'] = panNumber1
                    else:
                        De1 = {}
                except:
                    De1 = {}
                    pass
                try:
                    if len(serialNumber2) > 0:
                        De2 = {}
                        De2['directorName'] = directorName2
                        De2['serialNumber'] = serialNumber2
                        De2['panNumber'] = panNumber2
                    else:
                        De2 = {}
                except:
                    De2 = {}
                    pass
                try:
                    if len(serialNumber3) > 0:
                        De3 = {}
                        De3['directorName'] = directorName3
                        De3['serialNumber'] = serialNumber3
                        De3['panNumber'] = panNumber3
                    else:
                        De3 = {}
                except:
                    De3 = {}
                    pass
                try:
                    if len(serialNumber4) > 0:
                        De4 = {}
                        De4['directorName'] = directorName4
                        De4['serialNumber'] = serialNumber4
                        De4['panNumber'] = panNumber4
                    else:
                        De4 = {}
                except:
                    De4 = {}
                    pass
                try:
                    if len(serialNumber5) > 0:
                        De5 = {}
                        De5['directorName'] = directorName5
                        De5['serialNumber'] = serialNumber5
                        De5['panNumber'] = panNumber5
                    else:
                        De5 = {}
                except:
                    De5 = {}
                    pass
                try:
                    if len(serialNumber6) > 0:
                        De6 = {}
                        De6['directorName'] = directorName6
                        De6['serialNumber'] = serialNumber6
                        De6['panNumber'] = panNumber6
                    else:
                        De6 = {}
                except:
                    De6 = {}
                    pass
                try:
                    if len(serialNumber7) > 0:
                        De7 = {}
                        De7['directorName'] = directorName7
                        De7['serialNumber'] = serialNumber7
                        De7['panNumber'] = panNumber7
                    else:
                        De7 = {}
                except:
                    De7 = {}
                    pass
                try:
                    if len(serialNumber8) > 0:
                        De8 = {}
                        De8['directorName'] = directorName8
                        De8['serialNumber'] = serialNumber8
                        De8['panNumber'] = panNumber8
                    else:
                        De8 = {}
                except:
                    De8 = {}
                    pass
                try:
                    if len(serialNumber9) > 0:
                        De9 = {}
                        De9['directorName'] = directorName9
                        De9['serialNumber'] = serialNumber9
                        De9['panNumber'] = panNumber9
                    else:
                        De9 = {}
                except:
                    De9 = {}
                    pass
                try:
                    if len(serialNumber10) > 0:
                        De10 = {}
                        De10['directorName'] = directorName10
                        De10['serialNumber'] = serialNumber10
                        De10['panNumber'] = panNumber10
                    else:
                        De10 = {}
                except:
                    De10 = {}
                    pass
                try:
                    if len(serialNumber11) > 0:
                        De11 = {}
                        De11['directorName'] = directorName11
                        De11['serialNumber'] = serialNumber11
                        De11['panNumber'] = panNumber11
                    else:
                        De11 = {}
                except:
                    De11 = {}
                    pass
                try:
                    if len(serialNumber12) > 0:
                        De12 = {}
                        De12['directorName'] = directorName12
                        De12['serialNumber'] = serialNumber12
                        De12['panNumber'] = panNumber12
                    else:
                        De12 = {}
                except:
                    De12 = {}
                    pass
                try:
                    if len(serialNumber13) > 0:
                        De13 = {}
                        De13['directorName'] = directorName13
                        De13['serialNumber'] = serialNumber13
                        De13['panNumber'] = panNumber13
                    else:
                        De13 = {}
                except:
                    De13 = {}
                    pass
                try:
                    if len(serialNumber14) > 0:
                        De14 = {}
                        De14['directorName'] = directorName14
                        De14['serialNumber'] = serialNumber14
                        De14['panNumber'] = panNumber14
                    else:
                        De14 = {}
                except:
                    De14 = {}
                    pass
                try:
                    if len(serialNumber15) > 0:
                        De15 = {}
                        De15['directorName'] = directorName15
                        De15['serialNumber'] = serialNumber15
                        De15['panNumber'] = panNumber15
                    else:
                        De15 = {}
                except:
                    De15 = {}
                    pass
                try:
                    if len(serialNumber16) > 0:
                        De16 = {}
                        De16['directorName'] = directorName16
                        De16['serialNumber'] = serialNumber16
                        De16['panNumber'] = panNumber16
                    else:
                        De16 = {}
                except:
                    De16 = {}
                    pass
                try:
                    if len(serialNumber17) > 0:
                        De17 = {}
                        De17['directorName'] = directorName17
                        De17['serialNumber'] = serialNumber17
                        De17['panNumber'] = panNumber17
                    else:
                        De17 = {}
                except:
                    De17 = {}
                    pass
                try:
                    if len(serialNumber18) > 0:
                        De18 = {}
                        De18['directorName'] = directorName18
                        De18['serialNumber'] = serialNumber18
                        De18['panNumber'] = panNumber18
                    else:
                        De18 = {}
                except:
                    De18 = {}
                    pass
                try:
                    if len(serialNumber19) > 0:
                        De19 = {}
                        De19['directorName'] = directorName19
                        De19['serialNumber'] = serialNumber19
                        De19['panNumber'] = panNumber19
                    else:
                        De19 = {}
                except:
                    De19 = {}
                    pass
                try:
                    if len(serialNumber20) > 0:
                        De20 = {}
                        De20['directorName'] = directorName20
                        De20['serialNumber'] = serialNumber20
                        De20['panNumber'] = panNumber20
                    else:
                        De20 = {}
                except:
                    De20 = {}
                    pass
                try:
                    if len(serialNumber21) > 0:
                        De21 = {}
                        De21['directorName'] = directorName21
                        De21['serialNumber'] = serialNumber21
                        De21['panNumber'] = panNumber21
                    else:
                        De21 = {}
                except:
                    De21 = {}
                    pass
                try:
                    if len(serialNumber22) > 0:
                        De22 = {}
                        De22['directorName'] = directorName22
                        De22['serialNumber'] = serialNumber22
                        De22['panNumber'] = panNumber22
                    else:
                        De22 = {}
                except:
                    De22 = {}
                    pass
                try:
                    if len(serialNumber23) > 0:
                        De23 = {}
                        De23['directorName'] = directorName23
                        De23['serialNumber'] = serialNumber23
                        De23['panNumber'] = panNumber23
                    else:
                        De23 = {}
                except:
                    De23 = {}
                    pass
                try:
                    if len(serialNumber24) > 0:
                        De24 = {}
                        De24['directorName'] = directorName24
                        De24['serialNumber'] = serialNumber24
                        De24['panNumber'] = panNumber24
                    else:
                        De24 = {}
                except:
                    De24 = {}
                    pass
                try:
                    if len(serialNumber25) > 0:
                        De25 = {}
                        De25['directorName'] = directorName25
                        De25['serialNumber'] = serialNumber25
                        De25['panNumber'] = panNumber25
                    else:
                        De25 = {}
                except:
                    De25 = {}
                    pass
                try:
                    if len(serialNumber26) > 0:
                        De26 = {}
                        De26['directorName'] = directorName26
                        De26['serialNumber'] = serialNumber26
                        De26['panNumber'] = panNumber26
                    else:
                        De26 = {}
                except:
                    De26 = {}
                    pass
                try:
                    if len(serialNumber27) > 0:
                        De27 = {}
                        De27['directorName'] = directorName27
                        De27['serialNumber'] = serialNumber27
                        De27['panNumber'] = panNumber27
                    else:
                        De27 = {}
                except:
                    De27 = {}
                    pass
                try:
                    if len(serialNumber28) > 0:
                        De28 = {}
                        De28['directorName'] = directorName28
                        De28['serialNumber'] = serialNumber28
                        De28['panNumber'] = panNumber28
                    else:
                        De28 = {}
                except:
                    De28 = {}
                    pass
                try:
                    if len(serialNumber29) > 0:
                        De29 = {}
                        De29['directorName'] = directorName29
                        De29['serialNumber'] = serialNumber29
                        De29['panNumber'] = panNumber29
                    else:
                        De29 = {}
                except:
                    De29 = {}
                    pass
                try:
                    if len(serialNumber30) > 0:
                        De30 = {}
                        De30['directorName'] = directorName30
                        De30['serialNumber'] = serialNumber30
                        De30['panNumber'] = panNumber30
                    else:
                        De30 = {}
                except:
                    De30 = {}
                    pass

                try:
                    if len(BranchCode1) > 0:
                        Be1 = {}
                        Be1['branchAddress'] = Address1
                        Be1['branchCode'] = BranchCode1
                        Be1['gstin'] = gstin1
                    else:
                        Be1 = {}
                except:
                    Be1 = {}
                    pass
                try:
                    if len(BranchCode2) > 0:
                        Be2 = {}
                        Be2['branchAddress'] = Address2
                        Be2['branchCode'] = BranchCode2
                        Be2['gstin'] = gstin2
                    else:
                        Be2 = {}
                except:
                    Be2 = {}
                    pass
                try:
                    if len(BranchCode3) > 0:
                        Be3 = {}
                        Be3['branchAddress'] = Address3
                        Be3['branchCode'] = BranchCode3
                        Be3['gstin'] = gstin3
                    else:
                        Be3 = {}
                except:
                    Be3 = {}
                    pass
                try:
                    if len(BranchCode4) > 0:
                        Be4 = {}
                        Be4['branchAddress'] = Address4
                        Be4['branchCode'] = BranchCode4
                        Be4['gstin'] = gstin4
                    else:
                        Be4 = {}
                except:
                    Be4 = {}
                    pass
                try:
                    if len(BranchCode5) > 0:
                        Be5 = {}
                        Be5['branchAddress'] = Address5
                        Be5['branchCode'] = BranchCode5
                        Be5['gstin'] = gstin5
                    else:
                        Be5 = {}
                except:
                    Be5 = {}
                    pass
                try:
                    if len(BranchCode6) > 0:
                        Be6 = {}
                        Be6['branchAddress'] = Address6
                        Be6['branchCode'] = BranchCode6
                        Be6['gstin'] = gstin6
                    else:
                        Be6 = {}
                except:
                    Be6 = {}
                    pass
                try:
                    if len(BranchCode7) > 0:
                        Be7 = {}
                        Be7['branchAddress'] = Address7
                        Be7['branchCode'] = BranchCode7
                        Be7['gstin'] = gstin7
                    else:
                        Be7 = {}
                except:
                    Be7 = {}
                    pass
                try:
                    if len(BranchCode8) > 0:
                        Be8 = {}
                        Be8['branchAddress'] = Address8
                        Be8['branchCode'] = BranchCode8
                        Be8['gstin'] = gstin8
                    else:
                        Be8 = {}
                except:
                    Be8 = {}
                    pass
                try:
                    if len(BranchCode9) > 0:
                        Be9 = {}
                        Be9['branchAddress'] = Address9
                        Be9['branchCode'] = BranchCode9
                        Be9['gstin'] = gstin9
                    else:
                        Be9 = {}
                except:
                    Be9 = {}
                    pass
                try:
                    if len(BranchCode10) > 0:
                        Be10 = {}
                        Be10['branchAddress'] = Address10
                        Be10['branchCode'] = BranchCode10
                        Be10['gstin'] = gstin10
                    else:
                        Be10 = {}
                except:
                    Be10 = {}
                    pass
                try:
                    if len(BranchCode11) > 0:
                        Be11 = {}
                        Be11['branchAddress'] = Address11
                        Be11['branchCode'] = BranchCode11
                        Be11['gstin'] = gstin11
                    else:
                        Be11 = {}
                except:
                    Be11 = {}
                    pass
                try:
                    if len(BranchCode12) > 0:
                        Be12 = {}
                        Be12['branchAddress'] = Address12
                        Be12['branchCode'] = BranchCode12
                        Be12['gstin'] = gstin12
                    else:
                        Be12 = {}
                except:
                    Be12 = {}
                    pass
                try:
                    if len(BranchCode13) > 0:
                        Be13 = {}
                        Be13['branchAddress'] = Address13
                        Be13['branchCode'] = BranchCode13
                        Be13['gstin'] = gstin13
                    else:
                        Be13 = {}
                except:
                    Be13 = {}
                    pass
                try:
                    if len(BranchCode14) > 0:
                        Be14 = {}
                        Be14['branchAddress'] = Address14
                        Be14['branchCode'] = BranchCode14
                        Be14['gstin'] = gstin14
                    else:
                        Be14 = {}
                except:
                    Be14 = {}
                    pass
                try:
                    if len(BranchCode15) > 0:
                        Be15 = {}
                        Be15['branchAddress'] = Address15
                        Be15['branchCode'] = BranchCode15
                        Be15['gstin'] = gstin15
                    else:
                        Be15 = {}
                except:
                    Be15 = {}
                    pass
                try:
                    if len(BranchCode16) > 0:
                        Be16 = {}
                        Be16['branchAddress'] = Address16
                        Be16['branchCode'] = BranchCode16
                        Be16['gstin'] = gstin16
                    else:
                        Be16 = {}
                except:
                    Be16 = {}
                    pass
                try:
                    if len(BranchCode17) > 0:
                        Be17 = {}
                        Be17['branchAddress'] = Address17
                        Be17['branchCode'] = BranchCode17
                        Be17['gstin'] = gstin17
                    else:
                        Be17 = {}
                except:
                    Be17 = {}
                    pass
                try:
                    if len(BranchCode18) > 0:
                        Be18 = {}
                        Be18['branchAddress'] = Address18
                        Be18['branchCode'] = BranchCode18
                        Be18['gstin'] = gstin18
                    else:
                        Be18 = {}
                except:
                    Be18 = {}
                    pass
                try:
                    if len(BranchCode19) > 0:
                        Be19 = {}
                        Be19['branchAddress'] = Address19
                        Be19['branchCode'] = BranchCode19
                        Be19['gstin'] = gstin19
                    else:
                        Be19 = {}
                except:
                    Be19 = {}
                    pass
                try:
                    if len(BranchCode20) > 0:
                        Be20 = {}
                        Be20['branchAddress'] = Address20
                        Be20['branchCode'] = BranchCode20
                        Be20['gstin'] = gstin20
                    else:
                        Be20 = {}
                except:
                    Be20 = {}
                    pass
                try:
                    if len(BranchCode21) > 0:
                        Be21 = {}
                        Be21['branchAddress'] = Address21
                        Be21['branchCode'] = BranchCode21
                        Be21['gstin'] = gstin21
                    else:
                        Be21 = {}
                except:
                    Be21 = {}
                    pass
                try:
                    if len(BranchCode22) > 0:
                        Be22 = {}
                        Be22['branchAddress'] = Address22
                        Be22['branchCode'] = BranchCode22
                        Be22['gstin'] = gstin22
                    else:
                        Be22 = {}
                except:
                    Be22 = {}
                    pass
                try:
                    if len(BranchCode23) > 0:
                        Be23 = {}
                        Be23['branchAddress'] = Address23
                        Be23['branchCode'] = BranchCode23
                        Be23['gstin'] = gstin23
                    else:
                        Be23 = {}
                except:
                    Be23 = {}
                    pass
                try:
                    if len(BranchCode24) > 0:
                        Be24 = {}
                        Be24['branchAddress'] = Address24
                        Be24['branchCode'] = BranchCode24
                        Be24['gstin'] = gstin24
                    else:
                        Be24 = {}
                except:
                    Be24 = {}
                    pass
                try:
                    if len(BranchCode25) > 0:
                        Be25 = {}
                        Be25['branchAddress'] = Address25
                        Be25['branchCode'] = BranchCode25
                        Be25['gstin'] = gstin25
                    else:
                        Be25 = {}
                except:
                    Be25 = {}
                    pass
                try:
                    if len(BranchCode26) > 0:
                        Be26 = {}
                        Be26['branchAddress'] = Address26
                        Be26['branchCode'] = BranchCode26
                        Be26['gstin'] = gstin26
                    else:
                        Be26 = {}
                except:
                    Be26 = {}
                    pass
                try:
                    if len(BranchCode27) > 0:
                        Be27 = {}
                        Be27['branchAddress'] = Address27
                        Be27['branchCode'] = BranchCode27
                        Be27['gstin'] = gstin27
                    else:
                        Be27 = {}
                except:
                    Be27 = {}
                    pass
                try:
                    if len(BranchCode28) > 0:
                        Be28 = {}
                        Be28['branchAddress'] = Address28
                        Be28['branchCode'] = BranchCode28
                        Be28['gstin'] = gstin28
                    else:
                        Be28 = {}
                except:
                    Be28 = {}
                    pass
                try:
                    if len(BranchCode29) > 0:
                        Be29 = {}
                        Be29['branchAddress'] = Address29
                        Be29['branchCode'] = BranchCode29
                        Be29['gstin'] = gstin29
                    else:
                        Be29 = {}
                except:
                    Be29 = {}
                    pass
                try:
                    if len(BranchCode30) > 0:
                        Be30 = {}
                        Be30['branchAddress'] = Address30
                        Be30['branchCode'] = BranchCode30
                        Be30['gstin'] = gstin30
                    else:
                        Be30 = {}
                except:
                    Be30 = {}
                    pass
                try:
                    if len(BranchCode31) > 0:
                        Be31 = {}
                        Be31['branchAddress'] = Address31
                        Be31['branchCode'] = BranchCode31
                        Be31['gstin'] = gstin31
                    else:
                        Be31 = {}
                except:
                    Be31 = {}
                    pass
                try:
                    if len(BranchCode32) > 0:
                        Be32 = {}
                        Be32['branchAddress'] = Address32
                        Be32['branchCode'] = BranchCode32
                        Be32['gstin'] = gstin32
                    else:
                        Be32 = {}
                except:
                    Be32 = {}
                    pass
                try:
                    if len(BranchCode33) > 0:
                        Be33 = {}
                        Be33['branchAddress'] = Address33
                        Be33['branchCode'] = BranchCode33
                        Be33['gstin'] = gstin33
                    else:
                        Be33 = {}
                except:
                    Be33 = {}
                    pass
                try:
                    if len(BranchCode34) > 0:
                        Be34 = {}
                        Be34['branchAddress'] = Address34
                        Be34['branchCode'] = BranchCode34
                        Be34['gstin'] = gstin34
                    else:
                        Be34 = {}
                except:
                    Be34 = {}
                    pass
                try:
                    if len(BranchCode35) > 0:
                        Be35 = {}
                        Be35['branchAddress'] = Address35
                        Be35['branchCode'] = BranchCode35
                        Be35['gstin'] = gstin35
                    else:
                        Be35 = {}
                except:
                    Be35 = {}
                    pass
                try:
                    if len(BranchCode36) > 0:
                        Be36 = {}
                        Be36['branchAddress'] = Address36
                        Be36['branchCode'] = BranchCode36
                        Be36['gstin'] = gstin36
                    else:
                        Be36 = {}
                except:
                    Be36 = {}
                    pass
                try:
                    if len(BranchCode37) > 0:
                        Be37 = {}
                        Be37['branchAddress'] = Address37
                        Be37['branchCode'] = BranchCode37
                        Be37['gstin'] = gstin37
                    else:
                        Be37 = {}
                except:
                    Be37 = {}
                    pass
                try:
                    if len(BranchCode38) > 0:
                        Be38 = {}
                        Be38['branchAddress'] = Address38
                        Be38['branchCode'] = BranchCode38
                        Be38['gstin'] = gstin38
                    else:
                        Be38 = {}
                except:
                    Be38 = {}
                    pass
                try:
                    if len(BranchCode39) > 0:
                        Be39 = {}
                        Be39['branchAddress'] = Address39
                        Be39['branchCode'] = BranchCode39
                        Be39['gstin'] = gstin39
                    else:
                        Be39 = {}
                except:
                    Be39 = {}
                    pass
                try:
                    if len(BranchCode40) > 0:
                        Be40 = {}
                        Be40['branchAddress'] = Address40
                        Be40['branchCode'] = BranchCode40
                        Be40['gstin'] = gstin40
                    else:
                        Be40 = {}
                except:
                    Be40 = {}
                    pass
                try:
                    if len(BranchCode41) > 0:
                        Be41 = {}
                        Be41['branchAddress'] = Address41
                        Be41['branchCode'] = BranchCode41
                        Be41['gstin'] = gstin41
                    else:
                        Be41 = {}
                except:
                    Be41 = {}
                    pass
                try:
                    if len(BranchCode42) > 0:
                        Be42 = {}
                        Be42['branchAddress'] = Address42
                        Be42['branchCode'] = BranchCode42
                        Be42['gstin'] = gstin42
                    else:
                        Be42 = {}
                except:
                    Be42 = {}
                    pass
                try:
                    if len(BranchCode43) > 0:
                        Be43 = {}
                        Be43['branchAddress'] = Address43
                        Be43['branchCode'] = BranchCode43
                        Be43['gstin'] = gstin43
                    else:
                        Be43 = {}
                except:
                    Be43 = {}
                    pass
                try:
                    if len(BranchCode44) > 0:
                        Be44 = {}
                        Be44['branchAddress'] = Address44
                        Be44['branchCode'] = BranchCode44
                        Be44['gstin'] = gstin44
                    else:
                        Be44 = {}
                except:
                    Be44 = {}
                    pass
                try:
                    if len(BranchCode45) > 0:
                        Be45 = {}
                        Be45['branchAddress'] = Address45
                        Be45['branchCode'] = BranchCode45
                        Be45['gstin'] = gstin45
                    else:
                        Be45 = {}
                except:
                    Be45 = {}
                    pass
                try:
                    if len(BranchCode46) > 0:
                        Be46 = {}
                        Be46['branchAddress'] = Address46
                        Be46['branchCode'] = BranchCode46
                        Be46['gstin'] = gstin46
                    else:
                        Be46 = {}
                except:
                    Be46 = {}
                    pass
                try:
                    if len(BranchCode47) > 0:
                        Be47 = {}
                        Be47['branchAddress'] = Address47
                        Be47['branchCode'] = BranchCode47
                        Be47['gstin'] = gstin47
                    else:
                        Be47 = {}
                except:
                    Be47 = {}
                    pass
                try:
                    if len(BranchCode48) > 0:
                        Be48 = {}
                        Be48['branchAddress'] = Address48
                        Be48['branchCode'] = BranchCode48
                        Be48['gstin'] = gstin48
                    else:
                        Be48 = {}
                except:
                    Be48 = {}
                    pass
                try:
                    if len(BranchCode49) > 0:
                        Be49 = {}
                        Be49['branchAddress'] = Address49
                        Be49['branchCode'] = BranchCode49
                        Be49['gstin'] = gstin49
                    else:
                        Be49 = {}
                except:
                    Be49 = {}
                    pass
                try:
                    if len(BranchCode50) > 0:
                        Be50 = {}
                        Be50['branchAddress'] = Address50
                        Be50['branchCode'] = BranchCode50
                        Be50['gstin'] = gstin50
                    else:
                        Be50 = {}
                except:
                    Be50 = {}
                    pass
                try:
                    if len(BranchCode51) > 0:
                        Be51 = {}
                        Be51['branchAddress'] = Address51
                        Be51['branchCode'] = BranchCode51
                        Be51['gstin'] = gstin51
                    else:
                        Be51 = {}
                except:
                    Be51 = {}
                    pass
                try:
                    if len(BranchCode52) > 0:
                        Be52 = {}
                        Be52['branchAddress'] = Address52
                        Be52['branchCode'] = BranchCode52
                        Be52['gstin'] = gstin52
                    else:
                        Be52 = {}
                except:
                    Be52 = {}
                    pass
                try:
                    if len(BranchCode53) > 0:
                        Be53 = {}
                        Be53['branchAddress'] = Address53
                        Be53['branchCode'] = BranchCode53
                        Be53['gstin'] = gstin53
                    else:
                        Be53 = {}
                except:
                    Be53 = {}
                    pass
                try:
                    if len(BranchCode54) > 0:
                        Be54 = {}
                        Be54['branchAddress'] = Address54
                        Be54['branchCode'] = BranchCode54
                        Be54['gstin'] = gstin54
                    else:
                        Be54 = {}
                except:
                    Be54 = {}
                    pass
                try:
                    if len(BranchCode55) > 0:
                        Be55 = {}
                        Be55['branchAddress'] = Address55
                        Be55['branchCode'] = BranchCode55
                        Be55['gstin'] = gstin55
                    else:
                        Be55 = {}
                except:
                    Be55 = {}
                    pass
                try:
                    if len(BranchCode56) > 0:
                        Be56 = {}
                        Be56['branchAddress'] = Address56
                        Be56['branchCode'] = BranchCode56
                        Be56['gstin'] = gstin56
                    else:
                        Be56 = {}
                except:
                    Be56 = {}
                    pass
                try:
                    if len(BranchCode57) > 0:
                        Be57 = {}
                        Be57['branchAddress'] = Address57
                        Be57['branchCode'] = BranchCode57
                        Be57['gstin'] = gstin57
                    else:
                        Be57 = {}
                except:
                    Be57 = {}
                    pass
                try:
                    if len(BranchCode58) > 0:
                        Be58 = {}
                        Be58['branchAddress'] = Address58
                        Be58['branchCode'] = BranchCode58
                        Be58['gstin'] = gstin58
                    else:
                        Be58 = {}
                except:
                    Be58 = {}
                    pass
                try:
                    if len(BranchCode59) > 0:
                        Be59 = {}
                        Be59['branchAddress'] = Address59
                        Be59['branchCode'] = BranchCode59
                        Be59['gstin'] = gstin59
                    else:
                        Be59 = {}
                except:
                    Be59 = {}
                    pass
                try:
                    if len(BranchCode60) > 0:
                        Be60 = {}
                        Be60['branchAddress'] = Address60
                        Be60['branchCode'] = BranchCode60
                        Be60['gstin'] = gstin60
                    else:
                        Be60 = {}
                except:
                    Be60 = {}
                    pass
                try:
                    if len(BranchCode61) > 0:
                        Be61 = {}
                        Be61['branchAddress'] = Address61
                        Be61['branchCode'] = BranchCode61
                        Be61['gstin'] = gstin61
                    else:
                        Be61 = {}
                except:
                    Be61 = {}
                    pass
                try:
                    if len(BranchCode62) > 0:
                        Be62 = {}
                        Be62['branchAddress'] = Address62
                        Be62['branchCode'] = BranchCode62
                        Be62['gstin'] = gstin62
                    else:
                        Be62 = {}
                except:
                    Be62 = {}
                    pass
                try:
                    if len(BranchCode63) > 0:
                        Be63 = {}
                        Be63['branchAddress'] = Address63
                        Be63['branchCode'] = BranchCode63
                        Be63['gstin'] = gstin63
                    else:
                        Be63 = {}
                except:
                    Be63 = {}
                    pass
                try:
                    if len(BranchCode64) > 0:
                        Be64 = {}
                        Be64['branchAddress'] = Address64
                        Be64['branchCode'] = BranchCode64
                        Be64['gstin'] = gstin64
                    else:
                        Be64 = {}
                except:
                    Be64 = {}
                    pass
                try:
                    if len(BranchCode65) > 0:
                        Be65 = {}
                        Be65['branchAddress'] = Address65
                        Be65['branchCode'] = BranchCode65
                        Be65['gstin'] = gstin65
                    else:
                        Be65 = {}
                except:
                    Be65 = {}
                    pass
                try:
                    if len(BranchCode66) > 0:
                        Be66 = {}
                        Be66['branchAddress'] = Address66
                        Be66['branchCode'] = BranchCode66
                        Be66['gstin'] = gstin66
                    else:
                        Be66 = {}
                except:
                    Be66 = {}
                    pass
                try:
                    if len(BranchCode67) > 0:
                        Be67 = {}
                        Be67['branchAddress'] = Address67
                        Be67['branchCode'] = BranchCode67
                        Be67['gstin'] = gstin67
                    else:
                        Be67 = {}
                except:
                    Be67 = {}
                    pass
                try:
                    if len(BranchCode68) > 0:
                        Be68 = {}
                        Be68['branchAddress'] = Address68
                        Be68['branchCode'] = BranchCode68
                        Be68['gstin'] = gstin68
                    else:
                        Be68 = {}
                except:
                    Be68 = {}
                    pass
                try:
                    if len(BranchCode69) > 0:
                        Be69 = {}
                        Be69['branchAddress'] = Address69
                        Be69['branchCode'] = BranchCode69
                        Be69['gstin'] = gstin69



                    else:
                        Be69 = {}
                except:
                    Be69 = {}
                    pass
                try:
                    if len(BranchCode70) > 0:
                        Be70 = {}
                        Be70['branchAddress'] = Address70
                        Be70['branchCode'] = BranchCode70
                        Be70['gstin'] = gstin70
                    else:
                        Be70 = {}
                except:
                    Be70 = {}
                    pass
                try:
                    if len(BranchCode71) > 0:
                        Be71 = {}
                        Be71['branchAddress'] = Address71
                        Be71['branchCode'] = BranchCode71
                        Be71['gstin'] = gstin71
                    else:
                        Be71 = {}
                except:
                    Be71 = {}
                    pass
                try:
                    if len(BranchCode72) > 0:
                        Be72 = {}
                        Be72['branchAddress'] = Address72
                        Be72['branchCode'] = BranchCode72
                        Be72['gstin'] = gstin72
                    else:
                        Be72 = {}
                except:
                    Be72 = {}
                    pass
                try:
                    if len(BranchCode73) > 0:
                        Be73 = {}
                        Be73['branchAddress'] = Address73
                        Be73['branchCode'] = BranchCode73
                        Be73['gstin'] = gstin73
                    else:
                        Be73 = {}
                except:
                    Be73 = {}
                    pass
                try:
                    if len(BranchCode74) > 0:
                        Be74 = {}
                        Be74['branchAddress'] = Address74
                        Be74['branchCode'] = BranchCode74
                        Be74['gstin'] = gstin74
                    else:
                        Be74 = {}
                except:
                    Be74 = {}
                    pass
                try:
                    if len(BranchCode75) > 0:
                        Be75 = {}
                        Be75['branchAddress'] = Address75
                        Be75['branchCode'] = BranchCode75
                        Be75['gstin'] = gstin75
                    else:
                        Be75 = {}
                except:
                    Be75 = {}
                    pass
                try:
                    if len(BranchCode76) > 0:
                        Be76 = {}
                        Be76['branchAddress'] = Address76
                        Be76['branchCode'] = BranchCode76
                        Be76['gstin'] = gstin76
                    else:
                        Be76 = {}
                except:
                    Be76 = {}
                    pass
                try:
                    if len(BranchCode77) > 0:
                        Be77 = {}
                        Be77['branchAddress'] = Address77
                        Be77['branchCode'] = BranchCode77
                        Be77['gstin'] = gstin77
                    else:
                        Be77 = {}
                except:
                    Be77 = {}
                    pass
                try:
                    if len(BranchCode78) > 0:
                        Be78 = {}
                        Be78['branchAddress'] = Address78
                        Be78['branchCode'] = BranchCode78
                        Be78['gstin'] = gstin78
                    else:
                        Be78 = {}
                except:
                    Be78 = {}
                    pass
                try:
                    if len(BranchCode79) > 0:
                        Be79 = {}
                        Be79['branchAddress'] = Address79
                        Be79['branchCode'] = BranchCode79
                        Be79['gstin'] = gstin79
                    else:
                        Be79 = {}
                except:
                    Be79 = {}
                    pass
                try:
                    if len(BranchCode80) > 0:
                        Be80 = {}
                        Be80['branchAddress'] = Address80
                        Be80['branchCode'] = BranchCode80
                        Be80['gstin'] = gstin80
                    else:
                        Be80 = {}
                except:
                    Be80 = {}
                    pass
                try:
                    if len(BranchCode81) > 0:
                        Be81 = {}
                        Be81['branchAddress'] = Address81
                        Be81['branchCode'] = BranchCode81
                        Be81['gstin'] = gstin81
                    else:
                        Be81 = {}
                except:
                    Be81 = {}
                    pass
                try:
                    if len(BranchCode82) > 0:
                        Be82 = {}
                        Be82['branchAddress'] = Address82
                        Be82['branchCode'] = BranchCode82
                        Be82['gstin'] = gstin82
                    else:
                        Be82 = {}
                except:
                    Be82 = {}
                    pass
                try:
                    if len(BranchCode83) > 0:
                        Be83 = {}
                        Be83['branchAddress'] = Address83
                        Be83['branchCode'] = BranchCode83
                        Be83['gstin'] = gstin83
                    else:
                        Be83 = {}
                except:
                    Be83 = {}
                    pass
                try:
                    if len(BranchCode84) > 0:
                        Be84 = {}
                        Be84['branchAddress'] = Address84
                        Be84['branchCode'] = BranchCode84
                        Be84['gstin'] = gstin84
                    else:
                        Be84 = {}
                except:
                    Be84 = {}
                    pass
                try:
                    if len(BranchCode85) > 0:
                        Be85 = {}
                        Be85['branchAddress'] = Address85
                        Be85['branchCode'] = BranchCode85
                        Be85['gstin'] = gstin85
                    else:
                        Be85 = {}
                except:
                    Be85 = {}
                    pass
                try:
                    if len(BranchCode86) > 0:
                        Be86 = {}
                        Be86['branchAddress'] = Address86
                        Be86['branchCode'] = BranchCode86
                        Be86['gstin'] = gstin86
                    else:
                        Be86 = {}
                except:
                    Be86 = {}
                    pass
                try:
                    if len(BranchCode87) > 0:
                        Be87 = {}
                        Be87['branchAddress'] = Address87
                        Be87['branchCode'] = BranchCode87
                        Be87['gstin'] = gstin87
                    else:
                        Be87 = {}
                except:
                    Be87 = {}
                    pass
                try:
                    if len(BranchCode88) > 0:
                        Be88 = {}
                        Be88['branchAddress'] = Address88
                        Be88['branchCode'] = BranchCode88
                        Be88['gstin'] = gstin88
                    else:
                        Be88 = {}
                except:
                    Be88 = {}
                    pass
                try:
                    if len(BranchCode89) > 0:
                        Be89 = {}
                        Be89['branchAddress'] = Address89
                        Be89['branchCode'] = BranchCode89
                        Be89['gstin'] = gstin89
                    else:
                        Be89 = {}
                except:
                    Be89 = {}
                    pass
                try:
                    if len(BranchCode90) > 0:
                        Be90 = {}
                        Be90['branchAddress'] = Address90
                        Be90['branchCode'] = BranchCode90
                        Be90['gstin'] = gstin90
                    else:
                        Be90 = {}
                except:
                    Be90 = {}
                    pass
                try:
                    if len(BranchCode91) > 0:
                        Be91 = {}
                        Be91['branchAddress'] = Address91
                        Be91['branchCode'] = BranchCode91
                        Be91['gstin'] = gstin91
                    else:
                        Be91 = {}
                except:
                    Be91 = {}
                    pass
                try:
                    if len(BranchCode92) > 0:
                        Be92 = {}
                        Be92['branchAddress'] = Address92
                        Be92['branchCode'] = BranchCode92
                        Be92['gstin'] = gstin92
                    else:
                        Be92 = {}
                except:
                    Be92 = {}
                    pass
                try:
                    if len(BranchCode93) > 0:
                        Be93 = {}
                        Be93['branchAddress'] = Address93
                        Be93['branchCode'] = BranchCode93
                        Be93['gstin'] = gstin93
                    else:
                        Be93 = {}
                except:
                    Be93 = {}
                    pass
                try:
                    if len(BranchCode94) > 0:
                        Be94 = {}
                        Be94['branchAddress'] = Address94
                        Be94['branchCode'] = BranchCode94
                        Be94['gstin'] = gstin94
                    else:
                        Be94 = {}
                except:
                    Be94 = {}
                    pass
                try:
                    if len(BranchCode95) > 0:
                        Be95 = {}
                        Be95['branchAddress'] = Address95
                        Be95['branchCode'] = BranchCode95
                        Be95['gstin'] = gstin95
                    else:
                        Be95 = {}
                except:
                    Be95 = {}
                    pass
                try:
                    if len(BranchCode96) > 0:
                        Be96 = {}
                        Be96['branchAddress'] = Address96
                        Be96['branchCode'] = BranchCode96
                        Be96['gstin'] = gstin96
                    else:
                        Be96 = {}
                except:
                    Be96 = {}
                    pass
                try:
                    if len(BranchCode97) > 0:
                        Be97 = {}
                        Be97['branchAddress'] = Address97
                        Be97['branchCode'] = BranchCode97
                        Be97['gstin'] = gstin97
                    else:
                        Be97 = {}
                except:
                    Be97 = {}
                    pass
                try:
                    if len(BranchCode98) > 0:
                        Be98 = {}
                        Be98['branchAddress'] = Address98
                        Be98['branchCode'] = BranchCode98
                        Be98['gstin'] = gstin98
                    else:
                        Be98 = {}
                except:
                    Be98 = {}
                    pass
                try:
                    if len(BranchCode99) > 0:
                        Be99 = {}
                        Be99['branchAddress'] = Address99
                        Be99['branchCode'] = BranchCode99
                        Be99['gstin'] = gstin99
                    else:
                        Be99 = {}
                except:
                    Be99 = {}
                    pass
                try:
                    if len(BranchCode100) > 0:
                        Be100 = {}
                        Be100['branchAddress'] = Address100
                        Be100['branchCode'] = BranchCode100
                        Be100['gstin'] = gstin100
                    else:
                        Be100 = {}
                except:
                    Be100 = {}
                    pass
                try:
                    if len(BranchCode101) > 0:
                        Be101 = {}
                        Be101['branchAddress'] = Address101
                        Be101['branchCode'] = BranchCode101
                        Be101['gstin'] = gstin101
                    else:
                        Be101 = {}
                except:
                    Be101 = {}
                    pass
                try:
                    if len(BranchCode102) > 0:
                        Be102 = {}
                        Be102['branchAddress'] = Address102
                        Be102['branchCode'] = BranchCode102
                        Be102['gstin'] = gstin102
                    else:
                        Be102 = {}
                except:
                    Be102 = {}
                    pass
                try:
                    if len(BranchCode103) > 0:
                        Be103 = {}
                        Be103['branchAddress'] = Address103
                        Be103['branchCode'] = BranchCode103
                        Be103['gstin'] = gstin103
                    else:
                        Be103 = {}
                except:
                    Be103 = {}
                    pass
                try:
                    if len(BranchCode104) > 0:
                        Be104 = {}
                        Be104['branchAddress'] = Address104
                        Be104['branchCode'] = BranchCode104
                        Be104['gstin'] = gstin104
                    else:
                        Be104 = {}
                except:
                    Be104 = {}
                    pass
                try:
                    if len(BranchCode105) > 0:
                        Be105 = {}
                        Be105['branchAddress'] = Address105
                        Be105['branchCode'] = BranchCode105
                        Be105['gstin'] = gstin105
                    else:
                        Be105 = {}
                except:
                    Be105 = {}
                    pass
                try:
                    if len(BranchCode106) > 0:
                        Be106 = {}
                        Be106['branchAddress'] = Address106
                        Be106['branchCode'] = BranchCode106
                        Be106['gstin'] = gstin106
                    else:
                        Be106 = {}
                except:
                    Be106 = {}
                    pass
                try:
                    if len(BranchCode107) > 0:
                        Be107 = {}
                        Be107['branchAddress'] = Address107
                        Be107['branchCode'] = BranchCode107
                        Be107['gstin'] = gstin107
                    else:
                        Be107 = {}
                except:
                    Be107 = {}
                    pass
                try:
                    if len(BranchCode108) > 0:
                        Be108 = {}
                        Be108['branchAddress'] = Address108
                        Be108['branchCode'] = BranchCode108
                        Be108['gstin'] = gstin108
                    else:
                        Be108 = {}
                except:
                    Be108 = {}
                    pass
                try:
                    if len(BranchCode109) > 0:
                        Be109 = {}
                        Be109['branchAddress'] = Address109
                        Be109['branchCode'] = BranchCode109
                        Be109['gstin'] = gstin109
                    else:
                        Be109 = {}
                except:
                    Be109 = {}
                    pass
                try:
                    if len(BranchCode110) > 0:
                        Be110 = {}
                        Be110['branchAddress'] = Address110
                        Be110['branchCode'] = BranchCode110
                        Be110['gstin'] = gstin110
                    else:
                        Be110 = {}
                except:
                    Be110 = {}
                    pass
                try:
                    if len(BranchCode111) > 0:
                        Be111 = {}
                        Be111['branchAddress'] = Address111
                        Be111['branchCode'] = BranchCode111
                        Be111['gstin'] = gstin111
                    else:
                        Be111 = {}
                except:
                    Be111 = {}
                    pass
                try:
                    if len(BranchCode112) > 0:
                        Be112 = {}
                        Be112['branchAddress'] = Address112
                        Be112['branchCode'] = BranchCode112
                        Be112['gstin'] = gstin112
                    else:
                        Be112 = {}
                except:
                    Be112 = {}
                    pass
                try:
                    if len(BranchCode113) > 0:
                        Be113 = {}
                        Be113['branchAddress'] = Address113
                        Be113['branchCode'] = BranchCode113
                        Be113['gstin'] = gstin113
                    else:
                        Be113 = {}
                except:
                    Be113 = {}
                    pass
                try:
                    if len(BranchCode114) > 0:
                        Be114 = {}
                        Be114['branchAddress'] = Address114
                        Be114['branchCode'] = BranchCode114
                        Be114['gstin'] = gstin114
                    else:
                        Be114 = {}
                except:
                    Be114 = {}
                    pass
                try:
                    if len(BranchCode115) > 0:
                        Be115 = {}
                        Be115['branchAddress'] = Address115
                        Be115['branchCode'] = BranchCode115
                        Be115['gstin'] = gstin115
                    else:
                        Be115 = {}
                except:
                    Be115 = {}
                    pass
                try:
                    if len(BranchCode116) > 0:
                        Be116 = {}
                        Be116['branchAddress'] = Address116
                        Be116['branchCode'] = BranchCode116
                        Be116['gstin'] = gstin116
                    else:
                        Be116 = {}
                except:
                    Be116 = {}
                    pass
                try:
                    if len(BranchCode117) > 0:
                        Be117 = {}
                        Be117['branchAddress'] = Address117
                        Be117['branchCode'] = BranchCode117
                        Be117['gstin'] = gstin117
                    else:
                        Be117 = {}
                except:
                    Be117 = {}
                    pass
                try:
                    if len(BranchCode118) > 0:
                        Be118 = {}
                        Be118['branchAddress'] = Address118
                        Be118['branchCode'] = BranchCode118
                        Be118['gstin'] = gstin118
                    else:
                        Be118 = {}
                except:
                    Be118 = {}
                    pass
                try:
                    if len(BranchCode119) > 0:
                        Be119 = {}
                        Be119['branchAddress'] = Address119
                        Be119['branchCode'] = BranchCode119
                        Be119['gstin'] = gstin119
                    else:
                        Be119 = {}
                except:
                    Be119 = {}
                    pass
                try:
                    if len(BranchCode120) > 0:
                        Be120 = {}
                        Be120['branchAddress'] = Address120
                        Be120['branchCode'] = BranchCode120
                        Be120['gstin'] = gstin120
                    else:
                        Be120 = {}
                except:
                    Be120 = {}
                    pass
                try:
                    if len(BranchCode121) > 0:
                        Be121 = {}
                        Be121['branchAddress'] = Address121
                        Be121['branchCode'] = BranchCode121
                        Be121['gstin'] = gstin121
                    else:
                        Be121 = {}
                except:
                    Be121 = {}
                    pass
                try:
                    if len(BranchCode122) > 0:
                        Be122 = {}
                        Be122['branchAddress'] = Address122
                        Be122['branchCode'] = BranchCode122
                        Be122['gstin'] = gstin122
                    else:
                        Be122 = {}
                except:
                    Be122 = {}
                    pass
                try:
                    if len(BranchCode123) > 0:
                        Be123 = {}
                        Be123['branchAddress'] = Address123
                        Be123['branchCode'] = BranchCode123
                        Be123['gstin'] = gstin123
                    else:
                        Be123 = {}
                except:
                    Be123 = {}
                    pass
                try:
                    if len(BranchCode124) > 0:
                        Be124 = {}
                        Be124['branchAddress'] = Address124
                        Be124['branchCode'] = BranchCode124
                        Be124['gstin'] = gstin124
                    else:
                        Be124 = {}
                except:
                    Be124 = {}
                    pass
                try:
                    if len(BranchCode125) > 0:
                        Be125 = {}
                        Be125['branchAddress'] = Address125
                        Be125['branchCode'] = BranchCode125
                        Be125['gstin'] = gstin125
                    else:
                        Be125 = {}
                except:
                    Be125 = {}
                    pass
                try:
                    if len(BranchCode126) > 0:
                        Be126 = {}
                        Be126['branchAddress'] = Address126
                        Be126['branchCode'] = BranchCode126
                        Be126['gstin'] = gstin126
                    else:
                        Be126 = {}
                except:
                    Be126 = {}
                    pass
                try:
                    if len(BranchCode127) > 0:
                        Be127 = {}
                        Be127['branchAddress'] = Address127
                        Be127['branchCode'] = BranchCode127
                        Be127['gstin'] = gstin127
                    else:
                        Be127 = {}
                except:
                    Be127 = {}
                    pass
                try:
                    if len(BranchCode128) > 0:
                        Be128 = {}
                        Be128['branchAddress'] = Address128
                        Be128['branchCode'] = BranchCode128
                        Be128['gstin'] = gstin128
                    else:
                        Be128 = {}
                except:
                    Be128 = {}
                    pass
                try:
                    if len(BranchCode129) > 0:
                        Be129 = {}
                        Be129['branchAddress'] = Address129
                        Be129['branchCode'] = BranchCode129
                        Be129['gstin'] = gstin129
                    else:
                        Be129 = {}
                except:
                    Be129 = {}
                    pass

                try:
                    if len(BranchCode130) > 0:
                        Be130 = {}
                        Be130['branchAddress'] = Address130
                        Be130['branchCode'] = BranchCode130
                        Be130['gstin'] = gstin130
                    else:
                        Be130 = {}
                except:
                    Be130 = {}
                    pass
                try:
                    if len(BranchCode131) > 0:
                        Be131 = {}
                        Be131['branchAddress'] = Address131
                        Be131['branchCode'] = BranchCode131
                        Be131['gstin'] = gstin131
                    else:
                        Be131 = {}
                except:
                    Be131 = {}
                    pass
                try:
                    if len(BranchCode132) > 0:
                        Be132 = {}
                        Be132['branchAddress'] = Address132
                        Be132['branchCode'] = BranchCode132
                        Be132['gstin'] = gstin132
                    else:
                        Be132 = {}
                except:
                    Be132 = {}
                    pass
                try:
                    if len(BranchCode133) > 0:
                        Be133 = {}
                        Be133['branchAddress'] = Address133
                        Be133['branchCode'] = BranchCode133
                        Be133['gstin'] = gstin133
                    else:
                        Be133 = {}
                except:
                    Be133 = {}
                    pass
                try:
                    if len(BranchCode134) > 0:
                        Be134 = {}
                        Be134['branchAddress'] = Address134
                        Be134['branchCode'] = BranchCode134
                        Be134['gstin'] = gstin134
                    else:
                        Be134 = {}
                except:
                    Be134 = {}
                    pass
                try:
                    if len(BranchCode135) > 0:
                        Be135 = {}
                        Be135['branchAddress'] = Address135
                        Be135['branchCode'] = BranchCode135
                        Be135['gstin'] = gstin135
                    else:
                        Be135 = {}
                except:
                    Be135 = {}
                    pass
                try:
                    if len(BranchCode136) > 0:
                        Be136 = {}
                        Be136['branchAddress'] = Address136
                        Be136['branchCode'] = BranchCode136
                        Be136['gstin'] = gstin136
                    else:
                        Be136 = {}
                except:
                    Be136 = {}
                    pass
                try:
                    if len(BranchCode137) > 0:
                        Be137 = {}
                        Be137['branchAddress'] = Address137
                        Be137['branchCode'] = BranchCode137
                        Be137['gstin'] = gstin137
                    else:
                        Be137 = {}
                except:
                    Be137 = {}
                    pass
                try:
                    if len(BranchCode138) > 0:
                        Be138 = {}
                        Be138['branchAddress'] = Address138
                        Be138['branchCode'] = BranchCode138
                        Be138['gstin'] = gstin138
                    else:
                        Be138 = {}
                except:
                    Be138 = {}
                    pass
                try:
                    if len(BranchCode139) > 0:
                        Be139 = {}
                        Be139['branchAddress'] = Address139
                        Be139['branchCode'] = BranchCode139
                        Be139['gstin'] = gstin139
                    else:
                        Be139 = {}
                except:
                    Be139 = {}
                    pass
                try:
                    if len(BranchCode140) > 0:
                        Be140 = {}
                        Be140['branchAddress'] = Address140
                        Be140['branchCode'] = BranchCode140
                        Be140['gstin'] = gstin140
                    else:
                        Be140 = {}
                except:
                    Be140 = {}
                    pass
                try:
                    if len(BranchCode141) > 0:
                        Be141 = {}
                        Be141['branchAddress'] = Address141
                        Be141['branchCode'] = BranchCode141
                        Be141['gstin'] = gstin141
                    else:
                        Be141 = {}
                except:
                    Be141 = {}
                    pass
                try:
                    if len(BranchCode142) > 0:
                        Be142 = {}
                        Be142['branchAddress'] = Address142
                        Be142['branchCode'] = BranchCode142
                        Be142['gstin'] = gstin142
                    else:
                        Be142 = {}
                except:
                    Be142 = {}
                    pass
                try:
                    if len(BranchCode143) > 0:
                        Be143 = {}
                        Be143['branchAddress'] = Address143
                        Be143['branchCode'] = BranchCode143
                        Be143['gstin'] = gstin143
                    else:
                        Be143 = {}
                except:
                    Be143 = {}
                    pass
                try:
                    if len(BranchCode144) > 0:
                        Be144 = {}
                        Be144['branchAddress'] = Address144
                        Be144['branchCode'] = BranchCode144
                        Be144['gstin'] = gstin144
                    else:
                        Be144 = {}
                except:
                    Be144 = {}
                    pass
                try:
                    if len(BranchCode145) > 0:
                        Be145 = {}
                        Be145['branchAddress'] = Address145
                        Be145['branchCode'] = BranchCode145
                        Be145['gstin'] = gstin145
                    else:
                        Be145 = {}
                except:
                    Be145 = {}
                    pass
                try:
                    if len(BranchCode146) > 0:
                        Be146 = {}
                        Be146['branchAddress'] = Address146
                        Be146['branchCode'] = BranchCode146
                        Be146['gstin'] = gstin146
                    else:
                        Be146 = {}
                except:
                    Be146 = {}
                    pass
                try:
                    if len(BranchCode147) > 0:
                        Be147 = {}
                        Be147['branchAddress'] = Address147
                        Be147['branchCode'] = BranchCode147
                        Be147['gstin'] = gstin147
                    else:
                        Be147 = {}
                except:
                    Be147 = {}
                    pass
                try:
                    if len(BranchCode148) > 0:
                        Be148 = {}
                        Be148['branchAddress'] = Address148
                        Be148['branchCode'] = BranchCode148
                        Be148['gstin'] = gstin148
                    else:
                        Be148 = {}
                except:
                    Be148 = {}
                    pass
                try:
                    if len(BranchCode149) > 0:
                        Be149 = {}
                        Be149['branchAddress'] = Address149
                        Be149['branchCode'] = BranchCode149
                        Be149['gstin'] = gstin149
                    else:
                        Be149 = {}
                except:
                    Be149 = {}
                    pass
                try:
                    if len(BranchCode150) > 0:
                        Be150 = {}
                        Be150['branchAddress'] = Address150
                        Be150['branchCode'] = BranchCode150
                        Be150['gstin'] = gstin150
                    else:
                        Be150 = {}
                except:
                    Be150 = {}
                    pass

                dic = {}
                dic["panNumber"] = panNumber
                dic["fileDate"] = fileDate
                dic["fileNumber"] = fileNumber
                dic["iecIssuanceDate"] = iecIssuanceDate
                dic["iecCancelledDate"] = iecCancelledDate
                dic["categoryOfExporters"] = categoryOfExporters
                dic["dateOfBirthIncorporation"] = dateOfBirthIncorporation
                dic["delStatus"] = delStatus
                dic["dgftRaOffice"] = dgftRaOffice
                dic["iecSuspendedDate"] = iecSuspendedDate
                dic["natureOfConcernFirm"] = natureOfConcernFirm
                dic["iecNumber"] = iecNumber
                dic["firmName"] = firmName
                dic["iecStatus"] = iecStatus
                dic["address"] = address
                a = [Be1,Be2,Be3,Be4,Be5,Be6,Be7,Be8,Be9,Be10,Be11,Be12,Be13,Be14,Be15,Be16,Be17,Be18,Be19,Be20,Be21,Be22,Be23,Be24,Be25,Be26,Be27,Be28,Be29,Be30,Be31,Be32,Be33,Be34,Be35,Be36,Be37,Be38,Be39,Be40,Be41,Be42,Be43,Be44,Be45,Be46,Be47,Be48,Be49,Be50,Be51,Be52,Be53,Be54,Be55,Be56,Be57,Be58,Be59,Be60,Be61,Be62,Be63,Be64,Be65,Be66,Be67,Be68,Be69,Be70,Be71,Be72,Be73,Be74,Be75,Be76,Be77,Be78,Be79,Be80,Be81,Be82,Be83,Be84,Be85,Be86,Be87,Be88,Be89,Be90,Be91,Be92,Be93,Be94,Be95,Be96,Be97,Be98,Be99,Be100,Be101,Be102,Be103,Be104,Be105,Be106,Be107,Be108,Be109,Be110,Be111,Be112,Be113,Be114,Be115,Be116,Be117,Be118,Be119,Be120,Be121,Be122,Be123,Be124,Be125,Be126,Be127,Be128,Be129,Be130, Be131, Be132, Be133, Be134, Be135, Be136, Be137, Be138, Be139, Be140, Be141, Be142, Be143, Be144, Be145, Be146, Be147, Be148, Be149, Be150]

                dic["importExportBranchDetails"] = [d for d in a if any(d.values())]


                b = [De1,De2,De3,De4,De5,De6,De7,De8,De9,De10,De11,De12,De13,De14,De15,De16,De17,De18,De19,De20, De21, De22, De23, De24,De25, De26, De27, De28, De29, De30]
                dic["importExportDirectorDetails"] = [d for d in b if any(d.values())]

                c = [Fe1,Fe2]
                dic["importExportRcmcDetails"] = [d for d in c if any(d.values())]
                message = "Successfully Completed."
                code = "SRC001"
                dic = {"data": dic, "responseCode": code, "responseMessage": message}
                self.makeDriverDirs()
                self.logStatus("info", "successfully scrapped information", self.takeScreenshot())

                return dic
            return dic

    def IEC_response(self,iecNumber,firmName):
        import json
        dic = {}

        try:
            self.logStatus("info", "opening driver page")
            dic = self.generate_IEC(iecNumber,firmName)

        except Exception as e:
            print(e)
            try:

                errorcode678 = self.driver.find_element_by_xpath("""//*[@id="incCaptcha"]""").text
                print(errorcode678, "asasassasas")
                if errorcode678 == 'Please enter valid captcha code':
                    message = "Unable To Process. Please Reach Out To Support."
                    code = "EUP007"
                    dic = {"data": "null", "responseCode": code, "responseMessage": message}
                    self.logStatus("info", "Contact support")
                    return json.dumps(dic)
            except:
                pass

            self.logStatus("critical", "Captcha error retrying")
            try:
                self.logStatus("info", "no information found")
                message = "No Information Found."
                # fgdfd
                code = "ENI004"
                self.logStatus("info", "No Info Found")
                dic = {"data": "null", "responseCode": code, "responseMessage": message}


            except Exception as e:
                print(e)
                self.logStatus("critical", "Captcha error retrying")
                try:
                    self.logStatus("info", "opening driver page")
                    dic = self.generate_IEC(iecNumber,firmName)

                except Exception as e:
                    try:

                        errorcode678 = self.driver.find_element_by_xpath("""//*[@id="incCaptcha"]""").text
                        print(errorcode678 , "asasassasas")
                        if errorcode678 == 'Please enter valid captcha code':
                            message = "Unable To Process. Please Reach Out To Support."
                            code = "EUP007"
                            dic = {"data": "null", "responseCode": code, "responseMessage": message}
                            self.logStatus("info", "Contact support")
                            return json.dumps(dic)
                    except:
                        pass

                    message = "No Information Found."
                    #fgdfd
                    code = "ENI004"
                    self.logStatus("info", "No Info Found")
                    dic = {"data": "null", "responseCode": code, "responseMessage": message}

        self.logStatus("info", "json convert")
        dic = json.dumps(dic)
        return dic



#if __name__ == '__main__':

 #   v = IEC(refid="testing2", env = 'prod')
  #  data = v.generate_IEC(iecNumber = '0388081627',firmName = 'CUMMINS INDIA LIMITED')
   # print(data)




#if __name__ == '__main__':

 #   v = IEC(refid="testing2", env = 'prod')
  #  data = v.IEC_response(iecNumber = '0388024011',firmName = 'LARSEN & TOUBRO LIMITED')
   # print(data)
#0388024011
#LARSEN























