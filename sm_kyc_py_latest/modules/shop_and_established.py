import json
import os
import time
import uuid
from pprint import pprint
from selenium.webdriver.common.action_chains import ActionChains
import boto3
from botocore.exceptions import ClientError
from selenium.webdriver.support.ui import Select


#svd
from modules.db import DB
from modules.utils import GcpOcr



class Shop:

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
        self.uploadToS3(os.path.join(screenshotName), 'shopEstablishmentDelhi/' + self.refid + "/" + sname)
        return sname

    def logStatus(self, level, message, screenshot=None):

        if self.dbObj is not None:
            from datetime import datetime, timedelta
            nine_hours_from_now = datetime.now() + timedelta(hours=5.5)
            self.dbObj.insertLog(self.refid, '{:%Y-%m-%d %H:%M:%S}'.format(nine_hours_from_now), level, message,
                                 'Delhi scrapper_COMPLETE', self.env, screenshot)
        print(f"{level}: {message}, screenshot: {screenshot}")
  #  def checker(self,CertificateNo):




    def generate_Shopdelhi(self,shopEstablishmentName,state,natureOfBusiness,category,CertificateNo):

        from selenium import webdriver
        self.makeDriverDirs()

        from selenium.webdriver.common.action_chains import ActionChains
        from selenium.webdriver.chrome.options import Options
       # from webdriver_manager.chrome import ChromeDriverManager
        chrome_options = Options()
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--disable-extension")
        chrome_options.add_argument("no-sandbox")
        chrome_options.add_argument("--headless")
        chrome_options.headless = True

        self.driver = webdriver.Chrome("/usr/local/bin/chromedriver", options=chrome_options)
        if state == 'Delhi':
            start_url = "http://www.labourcis.nic.in/fse05_search.asp"
            try:
                self.logStatus("info", "Opening website")
                self.driver.get(start_url)
                r = 1
                self.makeDriverDirs()
                self.logStatus("info", "getting webpage", self.takeScreenshot())
                try:
                    #time.sleep(1)
                    self.driver.find_element_by_xpath("""/html/body/center/h1""")
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
                self.logStatus("info", "Starting Scrapping")

                self.driver.find_element_by_xpath("""/html/body/div[5]/fieldset/form/table/tbody/tr[2]/td[2]/select""").click()
                select = Select(self.driver.find_element_by_xpath("""/html/body/div[5]/fieldset/form/table/tbody/tr[2]/td[2]/select"""))
                select.select_by_visible_text(category)
                self.driver.find_element_by_xpath(
                    """/html/body/div[5]/fieldset/form/table/tbody/tr[1]/td[2]/input""").click()
                self.driver.find_element_by_xpath(
                    """/html/body/div[5]/fieldset/form/table/tbody/tr[1]/td[2]/input""").send_keys(
                    shopEstablishmentName)


                self.driver.find_element_by_xpath(
                    """/html/body/div[5]/fieldset/form/table/tbody/tr[2]/td[2]/select""").click()
                select = Select(self.driver.find_element_by_xpath("""/ html / body / div[5] / fieldset / form / table / tbody / tr[4] / td[2] / select"""))
                select.select_by_visible_text(natureOfBusiness)
                self.driver.find_element_by_xpath(
                    """/html/body/div[5]/fieldset/form/center/input[1]""").click()

                natureOfBusinessBusinessType = natureOfBusiness
                contactNumber = ''
                areaOfCircle = ''
                emailAddress = ''
                employerOwnerName = ''
                certificateValidUpTo = ''

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
                state = 'Delhi'
                i = 4
                x = 1

                while x != CertificateNo:
                    print(x)
                    print(CertificateNo)
                    import time

                    if x == CertificateNo:
                        i = i - 1
                        print(i)

                    else:
                        globals()["v" + str(i)] = self.driver.find_element_by_xpath(
                            """/html/body/div[5]/fieldset/form/table/tbody/tr""" + str([i]) + """/td[2]/a""").text

                        x = globals()["v" + str(i)]
                        print(x)
                        i = i + 1
                        print(i)
                i = i -1
                serialNumber = self.driver.find_element_by_xpath("""/ html / body / div[5] / fieldset / form / table / tbody / tr""" + str([i]) + """ / td[1]""").text
                contactNumber = self.driver.find_element_by_xpath("""/html/body/div[5]/fieldset/form/table/tbody/tr""" + str([i]) + """/td[6]""").text
                self.driver.find_element_by_xpath("""/html/body/div[5]/fieldset/form/table/tbody/tr""" + str([i]) + """/td[2]/a""").click()
                time.sleep(2)
                try:
                    registrationNumberLicenseNumber = self.driver.find_element_by_xpath("""/html/body/div[5]/fieldset/table/tbody/tr[1]/td[2]""")
                    registrationNumberLicenseNumber = registrationNumberLicenseNumber.text
                except Exception as e:
                    registrationNumberLicenseNumber = ''
                    print(e)
                shopEstablishmentName1 = self.driver.find_element_by_xpath("""/html/body/div[5]/fieldset/table/tbody/tr[3]/td[2]/b""")
                shopEstablishmentName1 = shopEstablishmentName1.text
                employerOwnerName = self.driver.find_element_by_xpath("""/html/body/div[5]/fieldset/table/tbody/tr[9]/td[2]""")
                employerOwnerName = employerOwnerName.text
                shopEstablishmentAddress = self.driver.find_element_by_xpath("""/html/body/div[5]/fieldset/table/tbody/tr[6]/td[2]""")
                shopEstablishmentAddress = shopEstablishmentAddress.text
                shopEstablishmentAddress = shopEstablishmentAddress.replace("\n"," ")
                fatherHusbandName =  self.driver.find_element_by_xpath("""/html/body/div[5]/fieldset/table/tbody/tr[10]/td[2]""").text
                dateOfCommencementApplicationDate = self.driver.find_element_by_xpath('/html/body/div[5]/fieldset/table/tbody/tr[5]/td[2]').text
                dateOfCommencementApplicationDate = dateOfCommencementApplicationDate.replace(":","")
                from datetime import datetime
                date_obj = datetime.strptime(dateOfCommencementApplicationDate, '%d/%m/%Y')
                dateOfCommencementApplicationDate = date_obj.strftime('%d-%b-%Y')

                certificateDate = self.driver.find_element_by_xpath('/ html / body / div[5] / fieldset / table / tbody / tr[21] / td[2]').text
                certificateDate = certificateDate.replace(":","")
                date_obj = datetime.strptime(certificateDate, '%d/%m/%Y')
                certificateDate = date_obj.strftime('%d-%b-%Y')


                #print("shopEstablishmentName1  ", len(shopEstablishmentName1),"shopEstablishmentName  ", len(shopEstablishmentName))





                dic = {}
                dic["shopEstablishmentAddress"] = shopEstablishmentAddress.replace(":"," ")
                dic["shopEstablishmentName"] = shopEstablishmentName1
                dic["registrationNumberLicenseNumber"] = registrationNumberLicenseNumber.replace(":"," ")
                dic["category"] = category
                dic["natureOfBusinessBusinessType"] = natureOfBusinessBusinessType
                dic["serialNumber"] = serialNumber
                dic["contactNumber"] = contactNumber
                dic["areaOfCircle"] = areaOfCircle
                dic["emailAddress"] = emailAddress
                dic["certificateValidUpTo"] = certificateValidUpTo
                dic["employerOwnerName"] = employerOwnerName.replace(":"," ")
                dic["district"] = district
                dic["certificateDate"] = certificateDate
                dic["applyFor"] = applyFor
                dic["currentStatusCertificateStatus"] = currentStatusCertificateStatus
                dic["remarkReason"] = remarkReason
                dic["fatherHusbandName"] = fatherHusbandName.replace(":"," ")
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
                self.makeDriverDirs()
                self.logStatus("info", "Scrapping finished")
                return dic



    def Shop_response(self,shopEstablishmentName ,state,natureOfBusiness,category,CertificateNo):

        dic = {}
        try:
            self.logStatus("info", "Opening webpage")
            dic = self.generate_Shopdelhi(shopEstablishmentName,state,natureOfBusiness,category,CertificateNo)
        except Exception as e:
            print(e)
            self.logStatus("critical", "timeout error retrying")
            try:
                self.logStatus("info", "Opening webpage")
                dic = self.generate_Shopdelhi(shopEstablishmentName,state, natureOfBusiness,category,CertificateNo)
            except Exception as e:
                print(e)
                self.logStatus("critical", "timeout error retrying")
                try:
                    self.logStatus("info", "Opening webpage")
                    dic = self.generate_Shopdelhi(shopEstablishmentName,state, natureOfBusiness,category,CertificateNo)
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

 #   v = Shop(refid="testing2", env = 'prod')
  #  data = v.generate_Shopdelhi(shopEstablishmentName = 'Chinese',state = 'Delhi', category = 'Shop', natureOfBusiness = 'Fast-Food', CertificateNo = "2015052248" )
   # print(data)




#if __name__ == '__main__':

 #   v = Shop(refid="testing2", env = 'prod')
  #  data = v.generate_Shopdelhi(shopEstablishmentName = 'Chinese',state = 'Delhi', category = 'Shop', natureOfBusiness = 'Fast-Food', CertificateNo = "2019058577" )
   # print(data)