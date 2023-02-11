import json
import os
import time
import uuid
from pprint import pprint

import boto3
from botocore.exceptions import ClientError

from modules.db import DB
from modules.utils import GcpOcr


class FSSAI:

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
                                 'FSSAICOMPLETE', self.env, screenshot)
        print(f"{level}: {message}, screenshot: {screenshot}")

    def generate_response(self,LicenseKey):
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        #from webdriver_manager.chrome import ChromeDriverManager
        chrome_options = Options()
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--headless")
        chrome_options.headless = True
        chrome_options.add_argument("--disable-extension")
        chrome_options.add_argument("no-sandbox")
        self.driver = webdriver.Chrome("/usr/local/bin/chromedriver", options=chrome_options)
        start_url = "https://foodlicensing.fssai.gov.in/cmsweb/TrackFBO.aspx"
        try:
            self.driver.get(start_url)
            x = 1
            self.makeDriverDirs()
            self.logStatus("info", "FSSAI page opened", self.takeScreenshot())
            try:

                cantreach =  self.driver.find_element_by_xpath("""//*[@id="main-message"]/h1/span""")
                cantreach = cantreach.text

                if cantreach == cantreach:
                    r = 2
            except:
                pass
        except Exception as e:
            x = 2

        self.driver.find_element_by_xpath("""//*[@id="ctl00_ContentPlaceHolder1_txtLicense"]""").click()
        self.driver.find_element_by_xpath("""//*[@id="ctl00_ContentPlaceHolder1_txtLicense"]""").send_keys(LicenseKey)

        self.driver.find_element_by_xpath("""//*[@id="ctl00_ContentPlaceHolder1_btnSubmit"]""").click()

        if x == 1:
            #try:
             #   errortype1 = self.driver.find_element_by_xpath(
              #      """//*[@id="form1"]/table/tbody/tr[1]/td/table/tbody/tr[1]/td/h5""")
               # errortype1 = errortype1.text
               # if errortype1 == "                                An error has occured, sorry for the inconvenience. Please login again.":
                #    x = 2
            #except:
             #   pass

            try:
                errortype = self.driver.find_element_by_xpath("""//*[@id="ctl00_ContentPlaceHolder1_lblError"]""")
                errortype = errortype.text
            except:
                errortype = 'None'
            try:
                errortype1 = self.driver.find_element_by_xpath("""// *[ @ id = "form1"] / table / tbody / tr[1] / td / table / tbody / tr[1] / td / h5""")
                errortype1 = errortype1.text
            except:
                errortype1 = 'None'
            print(errortype1)
            try:

                if errortype == "Record Not Found":
                    x = 3
                elif errortype == "Timeout expired. The timeout period elapsed prior to completion of the operation or the server is not responding.":
                    x = 4
                elif errortype == "Invalid License No.":
                    x = 3
                elif errortype == "Invalid object name 'Master_ErrorDesc'.":
                    x = 3
                elif errortype1 == 'An error has occured, sorry for the inconvenience. Please login again.':
                    x = 2
                else:
                    x = 6

            except:
                x = 6
        if x == 6:
            self.makeDriverDirs()
            self.logStatus("info", "starting scraping", self.takeScreenshot())
            Products = self.driver.find_element_by_xpath("""//*[@id="ctl00_ContentPlaceHolder1_lblProduct"]""")
            Productstext = Products.text
            Id = self.driver.find_element_by_xpath("""//*[@id="ctl00_ContentPlaceHolder1_lblLicence"]""")
            IDnum = Id.text
            Expiry_Date = self.driver.find_element_by_xpath("""//*[@id="ctl00_ContentPlaceHolder1_lblExpDate"]""")
            ExpiryDate = Expiry_Date.text
            from datetime import datetime
            date_obj = datetime.strptime(ExpiryDate, '%d/%m/%Y')
            ExpiryDate = date_obj.strftime('%d-%b-%Y')
            Status = self.driver.find_element_by_xpath("""//*[@id="ctl00_ContentPlaceHolder1_lblStatus"]""")
            GivenStatus = Status.text
            Company_Name = self.driver.find_element_by_xpath("""//*[@id="ctl00_ContentPlaceHolder1_lblcopName"]""")
            CompanyName = Company_Name.text
            Premises_Address = self.driver.find_element_by_xpath("""//*[@id="ctl00_ContentPlaceHolder1_lblAddress"]""")
            PremisesAddress = Premises_Address.text
            Kind_of_Business = self.driver.find_element_by_xpath("""//*[@id="ctl00_ContentPlaceHolder1_lblKob"]""")
            KindofBusiness = Kind_of_Business.text
            message = "Successfully Completed."
            code = "SRC001"
            dic = {}
            dic["companyName"] = CompanyName
            dic["expiryDate"] = ExpiryDate
            dic["kindOfBusiness"] = KindofBusiness
            dic["licenceNumber"] = IDnum
            dic["premisesAddress"] = PremisesAddress
            dic["products"] = Productstext
            dic["status"] = GivenStatus
            dic = {"data": dic, "responseCode": code, "responseMessage": message}
            self.logStatus("info", "completed scraping", self.takeScreenshot())
            return dic


        elif x == 2:
            message = 'Unable To Process. Please Reach Out To Support.'
            code = 'EUP007'
            IDnum = 'null'
            ExpiryDate = 'null'
            KindofBusiness = 'null'
            Productstext = 'null'
            GivenStatus = 'null'
            CompanyName = 'null'
            PremisesAddress = 'null'
            dic = {}
            dic['companyName'] = CompanyName
            dic['expiryDate'] = ExpiryDate
            dic['kindOfBusiness'] = KindofBusiness
            dic['licenceNumber'] = IDnum
            dic['premisesAddress'] = PremisesAddress
            dic['products'] = Productstext
            dic['status'] = GivenStatus
            dic = {'data': dic, 'responseCode': code, 'responseMessage': message}
            return dic
        elif x == 3:
            dic = {}
            IDnum = 'null'
            ExpiryDate = 'null'
            KindofBusiness = 'null'
            Productstext = 'null'
            GivenStatus = 'null'
            CompanyName = 'null'
            PremisesAddress = 'null'
            message = 'No Information Found.'
            code = 'ENI004'
            dic['companyName'] = CompanyName
            dic['expiryDate'] = ExpiryDate
            dic['kindOfBusiness'] = KindofBusiness
            dic['licenceNumber'] = IDnum
            dic['premisesAddress'] = PremisesAddress
            dic['products'] = Productstext
            dic['status'] = GivenStatus
            dic = {'data': dic, 'responseCode': code, 'responseMessage': message}
            return dic
        elif x == 4:
            Products = self.driver.find_element_by_xpath("""//*[@id="ctl00_ContentPlaceHolder1_lblProduct"]""")
            Productstext = Products.text
            return Exception

    def FSSAI_response(self,LicenseKey):
        import json

        LicenseKey = LicenseKey
        dic = {}
        try:
            self.logStatus("info", "Opening webpage")
            dic = self.generate_response(LicenseKey)
        except Exception as e:
            print(e)
            self.logStatus("critical", "timeout error retrying")
            try:
                self.logStatus("info", "Opening webpage")
                dic = self.generate_response(LicenseKey)
            except Exception as e:
                print(e)
                self.logStatus("critical", "timeout error retrying")
                try:
                    self.logStatus("info", "Opening webpage")
                    dic = self.generate_response(LicenseKey)
                except Exception as e:
                    print(e)
                    self.logStatus("critical", "no data found")
                    IDnum = 'null'
                    ExpiryDate = 'null'
                    KindofBusiness = 'null'
                    Productstext = 'null'
                    GivenStatus = 'null'
                    CompanyName = 'null'
                    PremisesAddress = 'null'
                    message = "Information Source is Not Working"
                    code = "EIS042"
                    dic['companyName'] = CompanyName
                    dic['expiryDate'] = ExpiryDate
                    dic['kindOfBusiness'] = KindofBusiness
                    dic['licenceNumber'] = IDnum
                    dic['premisesAddress'] = PremisesAddress
                    dic['products'] = Productstext
                    dic['status'] = GivenStatus
                    dic = {'data': dic, 'responseCode': code, 'responseMessage': message}
                    self.logStatus("info", "No Info Found")
        dic = json.dumps(dic)
        return dic

#if __name__ == '__main__':
#
 #   v = FSSAI(refid="testing2", env = 'prod')
  #  data = v.FSSAI_response(LicenseKey = '10019013001779')
   # print(data)


