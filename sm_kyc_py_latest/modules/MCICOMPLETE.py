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

class MCI:

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
                                 'MCI', self.env, screenshot)
        print(f"{level}: {message}, screenshot: {screenshot}")


    def generate_MCI(self,registrationNumber,yearOfRegistration,stateMedicalCouncil):
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        import io
      #  from webdriver_manager.chrome import ChromeDriverManager
        import os
        from google.cloud import vision
        import time
       # from webdriver_manager.chrome import ChromeDriverManager

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
        self.logStatus("info", "MCI page opened",self.takeScreenshot())
        self.logStatus("info", "Driver created")
        try:
            self.driver.get("https://www.mciindia.org/CMS/information-desk/indian-medical-register")
            r = 1
            self.makeDriverDirs()
            self.logStatus("info", "MCI page opened",self.takeScreenshot())
            try:
                cantreach1 = self.driver.find_element_by_xpath("""/ html / body / div / div / h1""")
                cantreach1 = cantreach1.text
                print(cantreach1)
                if cantreach1 == "Website Under Maintenance":
                    r = 3
            except:
                pass
            try:

                cantreach =  self.driver.find_element_by_xpath("""//*[@id="main-message"]/h1/span""")
                cantreach = cantreach.text


                if cantreach == cantreach:
                    r = 3
            except:

                try:
                    Error  = self.driver.find_element_by_xpath("""/html/body/h1""")
                    Error  = Error .text
                    x = 12

                except:
                    x = 1
                    pass
                try:
                    self.driver.find_element_by_xpath("""// *[ @ id = "doctorRegdNo"]""").click()
                except:
                    r = 3


                pass

        except Exception as e:
            self.logStatus("critical", "MCI page could not open contact support")
            r = 2
        if r == 2 or r == 3:
            message = 'Unable To Process. Please Reach Out To Support.'
            code = 'EUP007'
            dic = {'data': 'null', 'responseCode': code, 'responseMessage': message}
            self.logStatus("info", "No Info Found")
            return dic

        if r == 1:

            try:
                self.driver.find_element_by_xpath("""// *[ @ id = "doctorRegdNo"]""").click()
            except:
                pass
            self.driver.find_element_by_xpath("""// *[ @ id = "doctorRegdNo"]""").send_keys(registrationNumber)
            time.sleep(1)
            self.driver.find_element_by_xpath("""//*[@id="advance_form"]/div[3]/div/div/button/span""").click()
            self.driver.find_element_by_xpath("""//*[@id="advance_form"]/div[3]/div/div/ul/li[1]/div/input""").click()
            self.driver.find_element_by_xpath("""//*[@id="advance_form"]/div[3]/div/div/ul/li[1]/div/input""").send_keys(yearOfRegistration)
            #self.driver.find_element_by_xpath("""//*[@id="advance_form"]/div[3]/div/div/ul/li[3]/a/label""").click()
            #// *[ @ id = "advance_form"] / div[3] / div / div / ul / li[76] / a / label
            #// *[ @ id = "advance_form"] / div[3] / div / div / ul / li[3] / a / label
            #// *[ @ id = "advance_form"] / div[3] / div / div / ul / li[4] / a / label
            if yearOfRegistration == '2017':
                self.driver.find_element_by_xpath(
                    """// *[ @ id = "advance_form"] / div[3] / div / div / ul / li[6] / a / label""").click()

            if yearOfRegistration == '2018':
                self.driver.find_element_by_xpath(
                    """// *[ @ id = "advance_form"] / div[3] / div / div / ul / li[5] / a / label""").click()

            if yearOfRegistration == '2019':
                self.driver.find_element_by_xpath(
                    """// *[ @ id = "advance_form"] / div[3] / div / div / ul / li[4] / a / label""").click()

            if yearOfRegistration == '2020':
                self.driver.find_element_by_xpath(
                    """// *[ @ id = "advance_form"] / div[3] / div / div / ul / li[3] / a / label""").click()

            if yearOfRegistration == '1947':
                self.driver.find_element_by_xpath(
                    """// *[ @ id = "advance_form"] / div[3] / div / div / ul / li[76] / a / label""").click()

            if yearOfRegistration == '1948':
                self.driver.find_element_by_xpath(
                    """// *[ @ id = "advance_form"] / div[3] / div / div / ul / li[75] / a / label""").click()

            if yearOfRegistration == '1949':
                self.driver.find_element_by_xpath(
                    """// *[ @ id = "advance_form"] / div[3] / div / div / ul / li[74] / a / label""").click()

            if yearOfRegistration == '1950':
                self.driver.find_element_by_xpath(
                    """// *[ @ id = "advance_form"] / div[3] / div / div / ul / li[73] / a / label""").click()
            if yearOfRegistration == '1951':
                self.driver.find_element_by_xpath(
                    """// *[ @ id = "advance_form"] / div[3] / div / div / ul / li[72] / a / label""").click()
            if yearOfRegistration == '1952':
                self.driver.find_element_by_xpath(
                    """// *[ @ id = "advance_form"] / div[3] / div / div / ul / li[71] / a / label""").click()
            if yearOfRegistration == '1953':
                self.driver.find_element_by_xpath(
                    """// *[ @ id = "advance_form"] / div[3] / div / div / ul / li[70] / a / label""").click()
            if yearOfRegistration == '1954':
                self.driver.find_element_by_xpath(
                    """// *[ @ id = "advance_form"] / div[3] / div / div / ul / li[69] / a / label""").click()
            if yearOfRegistration == '1955':
                self.driver.find_element_by_xpath(
                    """// *[ @ id = "advance_form"] / div[3] / div / div / ul / li[68] / a / label""").click()
            if yearOfRegistration == '1956':
                self.driver.find_element_by_xpath(
                    """// *[ @ id = "advance_form"] / div[3] / div / div / ul / li[67] / a / label""").click()
            if yearOfRegistration == '1957':
                self.driver.find_element_by_xpath(
                    """// *[ @ id = "advance_form"] / div[3] / div / div / ul / li[66] / a / label""").click()
            if yearOfRegistration == '1958':
                self.driver.find_element_by_xpath(
                    """// *[ @ id = "advance_form"] / div[3] / div / div / ul / li[65] / a / label""").click()
            if yearOfRegistration == '1959':
                self.driver.find_element_by_xpath(
                    """// *[ @ id = "advance_form"] / div[3] / div / div / ul / li[64] / a / label""").click()
            if yearOfRegistration == '1960':
                self.driver.find_element_by_xpath(
                    """// *[ @ id = "advance_form"] / div[3] / div / div / ul / li[63] / a / label""").click()
            if yearOfRegistration == '1961':
                self.driver.find_element_by_xpath(
                    """// *[ @ id = "advance_form"] / div[3] / div / div / ul / li[62] / a / label""").click()
            if yearOfRegistration == '1962':
                self.driver.find_element_by_xpath(
                    """// *[ @ id = "advance_form"] / div[3] / div / div / ul / li[61] / a / label""").click()
            if yearOfRegistration == '1963':
                self.driver.find_element_by_xpath(
                    """// *[ @ id = "advance_form"] / div[3] / div / div / ul / li[60] / a / label""").click()
            if yearOfRegistration == '1964':
                self.driver.find_element_by_xpath(
                    """// *[ @ id = "advance_form"] / div[3] / div / div / ul / li[59] / a / label""").click()
            if yearOfRegistration == '1965':
                self.driver.find_element_by_xpath(
                    """// *[ @ id = "advance_form"] / div[3] / div / div / ul / li[58] / a / label""").click()
            if yearOfRegistration == '1966':
                self.driver.find_element_by_xpath(
                    """// *[ @ id = "advance_form"] / div[3] / div / div / ul / li[57] / a / label""").click()
            if yearOfRegistration == '1967':
                self.driver.find_element_by_xpath(
                    """// *[ @ id = "advance_form"] / div[3] / div / div / ul / li[56] / a / label""").click()
            if yearOfRegistration == '1968':
                self.driver.find_element_by_xpath(
                    """// *[ @ id = "advance_form"] / div[3] / div / div / ul / li[55] / a / label""").click()
            if yearOfRegistration == '1969':
                self.driver.find_element_by_xpath(
                    """// *[ @ id = "advance_form"] / div[3] / div / div / ul / li[54] / a / label""").click()
            if yearOfRegistration == '1970':
                self.driver.find_element_by_xpath(
                    """// *[ @ id = "advance_form"] / div[3] / div / div / ul / li[53] / a / label""").click()
            if yearOfRegistration == '1971':
                self.driver.find_element_by_xpath(
                    """// *[ @ id = "advance_form"] / div[3] / div / div / ul / li[52] / a / label""").click()
            if yearOfRegistration == '1972':
                self.driver.find_element_by_xpath(
                    """// *[ @ id = "advance_form"] / div[3] / div / div / ul / li[51] / a / label""").click()
            if yearOfRegistration == '1973':
                self.driver.find_element_by_xpath(
                    """// *[ @ id = "advance_form"] / div[3] / div / div / ul / li[50] / a / label""").click()
            if yearOfRegistration == '1974':
                self.driver.find_element_by_xpath(
                    """// *[ @ id = "advance_form"] / div[3] / div / div / ul / li[49] / a / label""").click()
            if yearOfRegistration == '1975':
                self.driver.find_element_by_xpath(
                    """// *[ @ id = "advance_form"] / div[3] / div / div / ul / li[48] / a / label""").click()
            if yearOfRegistration == '1976':
                self.driver.find_element_by_xpath(
                    """// *[ @ id = "advance_form"] / div[3] / div / div / ul / li[47] / a / label""").click()
            if yearOfRegistration == '1977':
                self.driver.find_element_by_xpath(
                    """// *[ @ id = "advance_form"] / div[3] / div / div / ul / li[46] / a / label""").click()
            if yearOfRegistration == '1978':
                self.driver.find_element_by_xpath(
                    """// *[ @ id = "advance_form"] / div[3] / div / div / ul / li[45] / a / label""").click()
            if yearOfRegistration == '1979':
                self.driver.find_element_by_xpath(
                    """// *[ @ id = "advance_form"] / div[3] / div / div / ul / li[44] / a / label""").click()
            if yearOfRegistration == '1980':
                self.driver.find_element_by_xpath(
                    """// *[ @ id = "advance_form"] / div[3] / div / div / ul / li[43] / a / label""").click()
            if yearOfRegistration == '1981':
                self.driver.find_element_by_xpath(
                    """// *[ @ id = "advance_form"] / div[3] / div / div / ul / li[42] / a / label""").click()
            if yearOfRegistration == '1982':
                self.driver.find_element_by_xpath(
                    """// *[ @ id = "advance_form"] / div[3] / div / div / ul / li[41] / a / label""").click()
            if yearOfRegistration == '1983':
                self.driver.find_element_by_xpath(
                    """// *[ @ id = "advance_form"] / div[3] / div / div / ul / li[40] / a / label""").click()
            if yearOfRegistration == '1984':
                self.driver.find_element_by_xpath(
                    """// *[ @ id = "advance_form"] / div[3] / div / div / ul / li[39] / a / label""").click()
            if yearOfRegistration == '1985':
                self.driver.find_element_by_xpath(
                    """// *[ @ id = "advance_form"] / div[3] / div / div / ul / li[38] / a / label""").click()
            if yearOfRegistration == '1986':
                self.driver.find_element_by_xpath(
                    """// *[ @ id = "advance_form"] / div[3] / div / div / ul / li[37] / a / label""").click()
            if yearOfRegistration == '1987':
                self.driver.find_element_by_xpath(
                    """// *[ @ id = "advance_form"] / div[3] / div / div / ul / li[36] / a / label""").click()
            if yearOfRegistration == '1988':
                self.driver.find_element_by_xpath(
                    """// *[ @ id = "advance_form"] / div[3] / div / div / ul / li[35] / a / label""").click()
            if yearOfRegistration == '1989':
                self.driver.find_element_by_xpath(
                    """// *[ @ id = "advance_form"] / div[3] / div / div / ul / li[34] / a / label""").click()
            if yearOfRegistration == '1990':
                self.driver.find_element_by_xpath(
                    """// *[ @ id = "advance_form"] / div[3] / div / div / ul / li[33] / a / label""").click()
            if yearOfRegistration == '1991':
                self.driver.find_element_by_xpath(
                    """// *[ @ id = "advance_form"] / div[3] / div / div / ul / li[32] / a / label""").click()
            if yearOfRegistration == '1992':
                self.driver.find_element_by_xpath(
                    """// *[ @ id = "advance_form"] / div[3] / div / div / ul / li[31] / a / label""").click()
            if yearOfRegistration == '1993':
                self.driver.find_element_by_xpath(
                    """// *[ @ id = "advance_form"] / div[3] / div / div / ul / li[30] / a / label""").click()
            if yearOfRegistration == '1994':
                self.driver.find_element_by_xpath(
                    """// *[ @ id = "advance_form"] / div[3] / div / div / ul / li[29] / a / label""").click()
            if yearOfRegistration == '1995':
                self.driver.find_element_by_xpath(
                    """// *[ @ id = "advance_form"] / div[3] / div / div / ul / li[28] / a / label""").click()
            if yearOfRegistration == '1996':
                self.driver.find_element_by_xpath(
                    """// *[ @ id = "advance_form"] / div[3] / div / div / ul / li[27] / a / label""").click()
            if yearOfRegistration == '1997':
                self.driver.find_element_by_xpath(
                    """// *[ @ id = "advance_form"] / div[3] / div / div / ul / li[26] / a / label""").click()
            if yearOfRegistration == '1998':
                self.driver.find_element_by_xpath(
                    """// *[ @ id = "advance_form"] / div[3] / div / div / ul / li[25] / a / label""").click()

            if yearOfRegistration == '1999':
                self.driver.find_element_by_xpath(
                    """// *[ @ id = "advance_form"] / div[3] / div / div / ul / li[24] / a / label""").click()

            if yearOfRegistration == '2000':
                self.driver.find_element_by_xpath(
                    """// *[ @ id = "advance_form"] / div[3] / div / div / ul / li[23] / a / label""").click()

            if yearOfRegistration == '2001':
                self.driver.find_element_by_xpath(
                    """// *[ @ id = "advance_form"] / div[3] / div / div / ul / li[22] / a / label""").click()

            if yearOfRegistration == '2002':
                self.driver.find_element_by_xpath(
                    """// *[ @ id = "advance_form"] / div[3] / div / div / ul / li[21] / a / label""").click()

            if yearOfRegistration == '2003':
                self.driver.find_element_by_xpath(
                    """// *[ @ id = "advance_form"] / div[3] / div / div / ul / li[20] / a / label""").click()

            if yearOfRegistration == '2004':
                self.driver.find_element_by_xpath(
                    """// *[ @ id = "advance_form"] / div[3] / div / div / ul / li[19] / a / label""").click()

            if yearOfRegistration == '2005':
                self.driver.find_element_by_xpath(
                    """// *[ @ id = "advance_form"] / div[3] / div / div / ul / li[18] / a / label""").click()

            if yearOfRegistration == '2006':
                self.driver.find_element_by_xpath(
                    """// *[ @ id = "advance_form"] / div[3] / div / div / ul / li[17] / a / label""").click()

            if yearOfRegistration == '2007':
                self.driver.find_element_by_xpath(
                    """// *[ @ id = "advance_form"] / div[3] / div / div / ul / li[16] / a / label""").click()

            if yearOfRegistration == '2008':
                self.driver.find_element_by_xpath(
                    """// *[ @ id = "advance_form"] / div[3] / div / div / ul / li[15] / a / label""").click()

            if yearOfRegistration == '2009':
                self.driver.find_element_by_xpath(
                    """// *[ @ id = "advance_form"] / div[3] / div / div / ul / li[14] / a / label""").click()

            if yearOfRegistration == '2010':
                self.driver.find_element_by_xpath(
                    """// *[ @ id = "advance_form"] / div[3] / div / div / ul / li[13] / a / label""").click()

            if yearOfRegistration == '2011':
                self.driver.find_element_by_xpath(
                    """// *[ @ id = "advance_form"] / div[3] / div / div / ul / li[12] / a / label""").click()

            if yearOfRegistration == '2012':
                self.driver.find_element_by_xpath(
                    """// *[ @ id = "advance_form"] / div[3] / div / div / ul / li[11] / a / label""").click()

            if yearOfRegistration == '2013':
                self.driver.find_element_by_xpath(
                    """// *[ @ id = "advance_form"] / div[3] / div / div / ul / li[10] / a / label""").click()

            if yearOfRegistration == '2014':
                self.driver.find_element_by_xpath(
                    """// *[ @ id = "advance_form"] / div[3] / div / div / ul / li[9] / a / label""").click()

            if yearOfRegistration == '2015':
                self.driver.find_element_by_xpath(
                    """// *[ @ id = "advance_form"] / div[3] / div / div / ul / li[8] / a / label""").click()

            if yearOfRegistration == '2016':
                self.driver.find_element_by_xpath(
                    """// *[ @ id = "advance_form"] / div[3] / div / div / ul / li[7] / a / label""").click()

            self.driver.find_element_by_xpath("""//*[@id="advance_form"]/div[4]/div/div/button""").click()
            self.driver.find_element_by_xpath("""//*[@id="advance_form"]/div[4]/div/div/ul/li[1]/div/input""").click()
            self.driver.find_element_by_xpath("""//*[@id="advance_form"]/div[4]/div/div/ul/li[1]/div/input""").send_keys(stateMedicalCouncil)

            if stateMedicalCouncil ==  'Andhra Pradesh Medical Council':

                self.driver.find_element_by_xpath("""// *[ @ id = "advance_form"] / div[4] / div / div / ul / li[3] / a / label""").click()

            if stateMedicalCouncil == 'Arunachal Pradesh Medical Council':
                self.driver.find_element_by_xpath("""//*[@id="advance_form"]/div[4]/div/div/ul/li[4]/a/label""").click()

            if stateMedicalCouncil == 'Assam Medical Council':
                self.driver.find_element_by_xpath(
                    """//*[@id="advance_form"]/div[4]/div/div/ul/li[5]/a/label""").click()

            if stateMedicalCouncil == 'Bhopal Medical Council':
                self.driver.find_element_by_xpath(
                    """//*[@id="advance_form"]/div[4]/div/div/ul/li[6]/a/label""").click()
            if stateMedicalCouncil == 'Bihar Medical Council':
                self.driver.find_element_by_xpath(
                    """//*[@id="advance_form"]/div[4]/div/div/ul/li[7]/a/label""").click()
            if stateMedicalCouncil == 'Bombay Medical Council':
                self.driver.find_element_by_xpath(
                    """//*[@id="advance_form"]/div[4]/div/div/ul/li[8]/a/label""").click()
            if stateMedicalCouncil == 'Chandigarh Medical Council':
                self.driver.find_element_by_xpath(
                    """//*[@id="advance_form"]/div[4]/div/div/ul/li[9]/a/label""").click()
            if stateMedicalCouncil == 'Chattisgarh Medical Council':
                self.driver.find_element_by_xpath(
                    """//*[@id="advance_form"]/div[4]/div/div/ul/li[10]/a/label""").click()

            if stateMedicalCouncil == 'Delhi Medical Council':
                self.driver.find_element_by_xpath(
                    """//*[@id="advance_form"]/div[4]/div/div/ul/li[11]/a/label""").click()

            if stateMedicalCouncil == 'Goa Medical Council':
                self.driver.find_element_by_xpath(
                    """//*[@id="advance_form"]/div[4]/div/div/ul/li[12]/a/label""").click()

            if stateMedicalCouncil == 'Gujarat Medical Council':
                self.driver.find_element_by_xpath(
                    """//*[@id="advance_form"]/div[4]/div/div/ul/li[13]/a/label""").click()

            if stateMedicalCouncil == 'Haryana Medical Council':
                self.driver.find_element_by_xpath(
                    """//*[@id="advance_form"]/div[4]/div/div/ul/li[14]/a/label""").click()

            if stateMedicalCouncil == 'Himanchal Pradesh Medical Council':
                self.driver.find_element_by_xpath(
                    """//*[@id="advance_form"]/div[4]/div/div/ul/li[15]/a/label""").click()

            if stateMedicalCouncil == 'Hyderabad Medical Council':
                self.driver.find_element_by_xpath(
                    """//*[@id="advance_form"]/div[4]/div/div/ul/li[16]/a/label""").click()
            if stateMedicalCouncil == 'Jammu & Kashmir Medical Council':
                self.driver.find_element_by_xpath(
                    """//*[@id="advance_form"]/div[4]/div/div/ul/li[17]/a/label""").click()
            if stateMedicalCouncil == 'Jharkhand Medical Council':
                self.driver.find_element_by_xpath(
                    """//*[@id="advance_form"]/div[4]/div/div/ul/li[18]/a/label""").click()
            if stateMedicalCouncil == 'Karnataka Medical Council':
                self.driver.find_element_by_xpath(
                    """//*[@id="advance_form"]/div[4]/div/div/ul/li[19]/a/label""").click()
            if stateMedicalCouncil == 'Madhya Pradesh Medical Council':
                self.driver.find_element_by_xpath(
                    """//*[@id="advance_form"]/div[4]/div/div/ul/li[20]/a/label""").click()
            if stateMedicalCouncil == 'Madras Medical Council':
                self.driver.find_element_by_xpath(
                    """//*[@id="advance_form"]/div[4]/div/div/ul/li[21]/a/label""").click()
            if stateMedicalCouncil == 'Mahakoshal Medical Council':
                self.driver.find_element_by_xpath(
                    """//*[@id="advance_form"]/div[4]/div/div/ul/li[22]/a/label""").click()
            if stateMedicalCouncil == 'Maharashtra Medical Council':
                self.driver.find_element_by_xpath(
                    """//*[@id="advance_form"]/div[4]/div/div/ul/li[23]/a/label""").click()
            if stateMedicalCouncil == 'Manipur Medical Council':
                self.driver.find_element_by_xpath(
                    """//*[@id="advance_form"]/div[4]/div/div/ul/li[24]/a/label""").click()
            if stateMedicalCouncil == 'Medical Council of India':
                self.driver.find_element_by_xpath(
                    """//*[@id="advance_form"]/div[4]/div/div/ul/li[25]/a/label""").click()
            if stateMedicalCouncil == 'Medical Council of Tanganyika':
                self.driver.find_element_by_xpath(
                    """//*[@id="advance_form"]/div[4]/div/div/ul/li[26]/a/label""").click()
            if stateMedicalCouncil == 'Mizoram Medical Council':
                self.driver.find_element_by_xpath(
                    """//*[@id="advance_form"]/div[4]/div/div/ul/li[27]/a/label""").click()
            if stateMedicalCouncil == 'Mysore Medical Council':
                self.driver.find_element_by_xpath(
                    """//*[@id="advance_form"]/div[4]/div/div/ul/li[28]/a/label""").click()
            if stateMedicalCouncil == 'Nagaland Medical Council':
                self.driver.find_element_by_xpath(
                    """//*[@id="advance_form"]/div[4]/div/div/ul/li[29]/a/label""").click()
            if stateMedicalCouncil == 'Orissa Council of Medical Registration':
                self.driver.find_element_by_xpath(
                    """//*[@id="advance_form"]/div[4]/div/div/ul/li[30]/a/label""").click()
            if stateMedicalCouncil == 'Pondicherry Medical Council':
                self.driver.find_element_by_xpath(
                    """//*[@id="advance_form"]/div[4]/div/div/ul/li[31]/a/label""").click()
            if stateMedicalCouncil == 'Punjab Medical Council':
                self.driver.find_element_by_xpath(
                    """//*[@id="advance_form"]/div[4]/div/div/ul/li[32]/a/label""").click()
            if stateMedicalCouncil == 'Rajasthan Medical Council':
                self.driver.find_element_by_xpath(
                    """//*[@id="advance_form"]/div[4]/div/div/ul/li[33]/a/label""").click()
            if stateMedicalCouncil == 'Sikkim Medical Council':
                self.driver.find_element_by_xpath(
                    """//*[@id="advance_form"]/div[4]/div/div/ul/li[34]/a/label""").click()
            if stateMedicalCouncil == 'Tamil Nadu Medical Council':
                self.driver.find_element_by_xpath(
                    """//*[@id="advance_form"]/div[4]/div/div/ul/li[35]/a/label""").click()
            if stateMedicalCouncil == 'Telangana State Medical Council':
                self.driver.find_element_by_xpath(
                    """//*[@id="advance_form"]/div[4]/div/div/ul/li[36]/a/label""").click()
            if stateMedicalCouncil == 'Travancore Cochin Medical Council, Trivandrum':
                self.driver.find_element_by_xpath(
                    """//*[@id="advance_form"]/div[4]/div/div/ul/li[37]/a/label""").click()
            if stateMedicalCouncil == 'Tripura State Medical Council ':
                self.driver.find_element_by_xpath(
                    """//*[@id="advance_form"]/div[4]/div/div/ul/li[38]/a/label""").click()
            if stateMedicalCouncil == 'Uttar Pradesh Medical Council':
                self.driver.find_element_by_xpath(
                    """//*[@id="advance_form"]/div[4]/div/div/ul/li[39]/a/label""").click()
            if stateMedicalCouncil == 'Uttarakhand Medical Council':
                self.driver.find_element_by_xpath(
                    """//*[@id="advance_form"]/div[4]/div/div/ul/li[40]/a/label""").click()
            if stateMedicalCouncil == 'Vidharba Medical Council':
                self.driver.find_element_by_xpath(
                    """//*[@id="advance_form"]/div[4]/div/div/ul/li[41]/a/label""").click()
            if stateMedicalCouncil == 'West Bengal Medical Council':
                self.driver.find_element_by_xpath(
                    """//*[@id="advance_form"]/div[4]/div/div/ul/li[42]/a/label""").click()

            self.driver.find_element_by_xpath("""//*[@id="doctor_advance_Details"]""").click()
            time.sleep(3)




            try:
                loading1 = self.driver.find_element_by_xpath("""/ html / body / div[6] / div[2] / div / div[1] / h3""")
                loading1 = loading1.text
                print(loading1)
                time.sleep(30)
                loading = self.driver.find_element_by_xpath("""/ html / body / div[6] / div[2] / div / div[1] / h3""")
                loading = loading.text
                if loading == 'Loading':
                    time.sleep(30)
                print(loading)
                x = 12


            except:
                x = 1
                pass



            if x == 1:
                self.logStatus("info", "Started scraping", self.takeScreenshot())
                serialNumber = self.driver.find_element_by_xpath("""//*[@id="doct_info5"]/tbody/tr/td[1]""")
                serialNumber = serialNumber.text
                #window_before = self.driver.window_handles[0]
                #window_before_title = self.driver.title
                try:
                    self.driver.find_element_by_xpath("""//*[@id="doct_info5"]/tbody/tr/td[7]/a""").click()
                    time.sleep(3)
                except:
                    pass
                time.sleep(3)
                #window_after = self.driver.window_handles[1]
                #self.driver.switch_to.window(window_after)
                dateOfBirth = self.driver.find_element_by_xpath("""//*[@id="doctorBiodata"]/tbody/tr[3]/td[2]""")
                dateOfBirth = dateOfBirth.text
                try:
                    from datetime import datetime
                    date_obj = datetime.strptime(dateOfBirth, '%d/%m/%Y')
                    dateOfBirth = date_obj.strftime('%d-%b-%Y')
                except:
                    pass
                dateOfReg = self.driver.find_element_by_xpath("""//*[@id="doctorBiodata"]/tbody/tr[4]/td[4]""")
                dateOfReg = dateOfReg.text
                try:
                    from datetime import datetime
                    date_obj = datetime.strptime(dateOfReg, '%d/%m/%Y')
                    dateOfReg = date_obj.strftime('%d-%b-%Y')
                except:
                    pass
                fatherHusbandName = self.driver.find_element_by_xpath("""//*[@id="doctorBiodata"]/tbody/tr[2]/td[2]""")
                fatherHusbandName = fatherHusbandName.text
                name = self.driver.find_element_by_xpath("""//*[@id="doctorBiodata"]/tbody/tr[1]/td[2]""")
                name = name.text
                try:
                    AdditionalQualification = self.driver.find_element_by_xpath("""// *[ @ id = "doctorBiodata"] / tbody / tr[8] / td""")
                    AdditionalQualification = AdditionalQualification.text
                except:
                    AdditionalQualification = 'null'
                try:
                    if AdditionalQualification == "Additional Qualification :- 1":
                        permanentAddress = self.driver.find_element_by_xpath("""//*[@id="doctorBiodata"]/tbody/tr[12]/td[2]""")
                        permanentAddress = permanentAddress.text
                    else:
                        permanentAddress = self.driver.find_element_by_xpath("""//*[@id="doctorBiodata"]/tbody/tr[8]/td[2]""")
                        permanentAddress = permanentAddress.text
                except:
                    permanentAddress = None
                    pass
                try:
                    if permanentAddress == None:
                        permanentAddress = self.driver.find_element_by_xpath("""// *[ @ id = "doctorBiodata"] / tbody / tr[20] / td[2]""")
                        permanentAddress = permanentAddress.text
                except:
                    pass


                qualification = self.driver.find_element_by_xpath("""//*[@id="doctorBiodata"]/tbody/tr[6]/td[2]""")
                qualification = qualification.text
                qualificationYear = self.driver.find_element_by_xpath("""//*[@id="doctorBiodata"]/tbody/tr[6]/td[4]""")
                qualificationYear = qualificationYear.text
                registrationNumber1 = self.driver.find_element_by_xpath("""//*[@id="doctorBiodata"]/tbody/tr[4]/td[2]""")
                registrationNumber1 = registrationNumber1.text
                stateMedicalCouncil = self.driver.find_element_by_xpath("""//*[@id="doctorBiodata"]/tbody/tr[5]/td[4]""")
                stateMedicalCouncil = stateMedicalCouncil.text
                universityName = self.driver.find_element_by_xpath("""//*[@id="doctorBiodata"]/tbody/tr[7]/td[2]""")
                universityName = universityName.text
                YearOfInfo = self.driver.find_element_by_xpath("""//*[@id="doctorBiodata"]/tbody/tr[3]/td[4]""")
                YearOfInfo = YearOfInfo.text
                uprnNumber = self.driver.find_element_by_xpath("""//*[@id="doctorBiodata"]/tbody/tr[5]/td[2]""")
                uprnNumber = uprnNumber.text
                try:
                    qualification1 = self.driver.find_element_by_xpath("""//*[@id="doctorBiodata"]/tbody/tr[9]/td[2]""")
                    qualification1 = qualification1.text
                except Exception as e:
                    pass
                try:
                    qualificationYear1 = self.driver.find_element_by_xpath("""//*[@id="doctorBiodata"]/tbody/tr[9]/td[4]""")
                    qualificationYear1 = qualificationYear1.text
                except Exception as e:
                    pass
                try:
                    universityName1 = self.driver.find_element_by_xpath("""//*[@id="doctorBiodata"]/tbody/tr[10]/td[2]""")
                    universityName1 = universityName1.text
                except Exception as e:
                    pass
                try:
                    Be = {}
                    Be["qualification"] = qualification1
                    Be["qualificationYear"] = qualificationYear1
                    Be["universityName"] = universityName1
                    Be["serialNumber"] = serialNumber
                except:
                    Be = {}


                if registrationNumber1 == registrationNumber:
                    message = "Successfully Completed."
                    code = "SRC001"
                    dic = {}
                    dic["dateOfBirth"] = dateOfBirth
                    dic["dateOfReg"] = dateOfReg
                    dic["fatherHusbandName"] = fatherHusbandName
                    dic["name"] = name
                    dic["permanentAddress"] = permanentAddress
                    dic["qualification"] = qualification
                    dic["qualificationYear"] = qualificationYear
                    dic["registrationNumber"] = registrationNumber
                    dic["stateMedicalCouncil"] = stateMedicalCouncil
                    dic["universityName"] = universityName
                    dic["yearOfInfo"] = YearOfInfo
                    dic["uprnNumber"] = uprnNumber
                    dic["serialNumber"] = serialNumber
                    a = [Be]
                    dic["mciAdditionalQualification"] = [d for d in a if any(d.values())]

                    dic = {"data": dic, "responseCode": code, "responseMessage": message}
                    self.logStatus("info", "completed scraping", self.takeScreenshot())
                    return dic
                else:
                    dic = {}
                    message = 'No Information Found.'
                    code = 'ENI004'
                    dic = {'data': 'null', 'responseCode': code, 'responseMessage': message}
                    self.logStatus("info", "No Info Found")
                    return dic
            if x == 12:
                dic = {}
                message = 'Unable To Process. Please Reach Out To Support.'
                code = 'EUP007'
                dic = {'data': 'Loading timeout error', 'responseCode': code, 'responseMessage': message}
                self.logStatus("info", "No Info Found")
                return dic
        if x == 12:
            dic = {}
            message = 'Unable To Process. Please Reach Out To Support.'
            code = 'EUP007'
            dic = {'data': 'null', 'responseCode': code, 'responseMessage': message}
            self.logStatus("info", "No Info Found")
            return dic

    def MCIMembership(self,registrationNumber,yearOfRegistration,stateMedicalCouncil):

        dic = {}
        try:
            self.logStatus("info", "Opening webpage")
            dic = self.generate_MCI(registrationNumber,yearOfRegistration,stateMedicalCouncil)
        except Exception as e:

            self.logStatus("critical", "data not found")
            try:
                self.logStatus("info", "Opening webpage")
                dic = self.generate_MCI(registrationNumber,yearOfRegistration,stateMedicalCouncil)
            except Exception as e:

                self.logStatus("critical", "data not found")
                try:
                    self.logStatus("info", "Opening webpage")
                    dic = self.generate_MCI(registrationNumber,yearOfRegistration,stateMedicalCouncil)
                except Exception as e:

                    self.logStatus("critical", "no data found")
                    dic = {}
                    message = 'No Information Found.'
                    code = 'ENI004'
                    dic = {'data': 'null', 'responseCode': code, 'responseMessage': message}
                    self.logStatus("info", "No Info Found")

        return dic







                #// *[ @ id = "advance_form"] / div[4] / div / div / ul / li[42] / a / label


if __name__ == '__main__':

    v = MCI(refid="testing2", env = 'prod')
    data = v.generate_MCI(registrationNumber = '10042', yearOfRegistration = "1988", stateMedicalCouncil= "Assam Medical Council")
    print(data)