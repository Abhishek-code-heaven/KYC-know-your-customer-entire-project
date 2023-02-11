

if __name__ == '__main__':

     v = ESICS(refid="testing2", env = 'quality')
     data = v.ESIF_response(9999916891)
     pprint(data)
     #2612316891

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

class ESIC:

    def __init__(self,refid,env = "quality"):

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
            self.dbObj.insertLog(self.refid, time.strftime('%Y-%m-%d %H-%M-%S'), level, message,
                                 'vehicle_registration', self.env, screenshot)
        print(f"{level}: {message}, screenshot: {screenshot}")

    def generate_ESIC(self,insuranceNumber):
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        import io
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
        self.logStatus("info", "ESIF page opened",self.takeScreenshot())
        self.logStatus("info", "Driver created")
        try:
            self.driver.get("http://www.esic.in/EmployeePortal/login.aspx#")
            r = 1
            self.makeDriverDirs()
            self.logStatus("info", "ESIF page opened",self.takeScreenshot())
            try:

                cantreach =  self.driver.find_element_by_xpath("""// *[ @ id = "main-message"]""")
                cantreach = cantreach.text

                if cantreach == cantreach:
                    r = 3
            except:
                pass

        except Exception as e:
            self.logStatus("critical", "ESIF page could not open contact support")
            r = 2

        if r == 1:

            self.driver.find_element_by_xpath("""//*[@id="img1"]""").screenshot('captcha.png')
            with io.open(os.path.join(self.FOLDER_PATH, self.FILE_NAME), 'rb') as image_file:
                content = image_file.read()

            image = vision.types.Image(content=content)
            response = self.client.text_detection(image=image)
            texts = response.text_annotations

            for text in texts:
                z = ('"{}"'.format(text.description))
            h = str(z).split('"')
            k = h[1]

            self.driver.find_element_by_xpath("""//*[@id="txtUserName"]""").click()
            self.driver.find_element_by_xpath("""//*[@id="txtUserName"]""").send_keys(insuranceNumber )
            self.driver.find_element_by_xpath("""//*[@id="txtCaptcha"]""").click()
            self.driver.find_element_by_xpath("""//*[@id="txtCaptcha"]""").send_keys(k)
            self.driver.find_element_by_xpath("""//*[@id="btnLogin"]""").click()
            errorcode = self.driver.find_element_by_xpath("""// *[ @ id = "lblMessage"]""")
            errorcode = errorcode.text
            if errorcode == "Ip Number not found.":
                x = 5
            else:
                window_before = self.driver.window_handles[0]

                window_before_title = self.driver.title
                self.makeDriverDirs()
                self.logStatus("info", "starting scraping",self.takeScreenshot())

                UHID_Number = self.driver.find_element_by_xpath("""//*[@id="lbl_uhid"]""")
                UHID_Number = UHID_Number.text
                self.logStatus("info", "Captcha Successfully opened")
                Registration_Date = self.driver.find_element_by_xpath("""//*[@id="lblRegDate"]""")
                Registration_Date = Registration_Date.text
                from datetime import datetime
                date_obj = datetime.strptime(Registration_Date, '%d/%m/%Y')
                Registration_Date = date_obj.strftime('%d-%b-%Y')
                self.logStatus("info", "Captcha Successfully opened")
                Current_Date_of_Appointment = self.driver.find_element_by_xpath("""//*[@id="lblDOACurrent"]""")
                Current_Date_of_Appointment = Current_Date_of_Appointment.text
                self.logStatus("info", "Captcha Successfully opened")
                Pehchan_Done = self.driver.find_element_by_xpath("""//*[@id="tblUser1"]/tbody/tr[8]/td[2]""")
                Pehchan_Done = Pehchan_Done.text
                self.logStatus("info", "Captcha Successfully opened")
                Printing_Done = self.driver.find_element_by_xpath("""//*[@id="tblUser1"]/tbody/tr[9]/td[2]""")
                Printing_Done = Printing_Done.text
                self.logStatus("info", "Captcha Successfully opened")
                No_of_Duplicate_Cards_Done = self.driver.find_element_by_xpath("""//*[@id="lblnoofprints"]""")
                No_of_Duplicate_Cards_Done = No_of_Duplicate_Cards_Done.text

                Latest_Duplicate_card_Request_Location = self.driver.find_element_by_xpath("""//*[@id="lblnoofprints"]""")
                Latest_Duplicate_card_Request_Location = Latest_Duplicate_card_Request_Location.text

                Dispensary_Name_For_Family = self.driver.find_element_by_xpath("""//*[@id="lbl_dep_dispensary"]""")
                Dispensary_Name_For_Family = Dispensary_Name_For_Family.text

                Insurance = self.driver.find_element_by_xpath("""//*[@id="lbl_ipno"]""")
                Insurance = Insurance.text

                Date_of_Birth = self.driver.find_element_by_xpath("""//*[@id="lbl_dob"]""")
                Date_of_Birth = Date_of_Birth.text

                from datetime import datetime
                date_obj = datetime.strptime(Date_of_Birth, '%d/%m/%Y')
                Date_of_Birth = date_obj.strftime('%d-%b-%Y')

                First_Date_Of_Appointment = self.driver.find_element_by_xpath("""//*[@id="lblFirstDOA"]""")
                First_Date_Of_Appointment = First_Date_Of_Appointment.text
                date_obj = datetime.strptime(First_Date_Of_Appointment, '%d/%m/%Y')
                First_Date_Of_Appointment = date_obj.strftime('%d-%b-%Y')

                Phone_Number = self.driver.find_element_by_xpath("""//*[@id="tblUser1"]/tbody/tr[7]/td[4]""")
                Phone_Number = Phone_Number.text

                Pehchan_Processed_Date = self.driver.find_element_by_xpath("""//*[@id="lblphchprodate"]""")
                Pehchan_Processed_Date = Pehchan_Processed_Date.text

                Printing_Date = self.driver.find_element_by_xpath("""//*[@id="lblpechprintdate"]""")
                Printing_Date = Printing_Date.text

                Latest_Duplicate_Card_Date = self.driver.find_element_by_xpath("""//*[@id="lbllatestprintDate"]""")
                Latest_Duplicate_Card_Date = Latest_Duplicate_Card_Date.text

                Latest_Duplicate_Card_Delivery_Location = self.driver.find_element_by_xpath("""//*[@id="lblreprintlocn"]""")
                Latest_Duplicate_Card_Delivery_Location = Latest_Duplicate_Card_Delivery_Location.text
                self.logStatus("info", "Captcha Successfully opened")
                self.driver.find_element_by_xpath("""//*[@id="EmployeeDetail"]""").click()
                window_after = self.driver.window_handles[1]
                self.driver.switch_to.window(window_after)
                self.logStatus("info", "Captcha Successfully opened")
                Employee_Name = self.driver.find_element_by_xpath("""//*[@id="ctl00_HomePageContent_lblname"]""")
                Employee_Name = Employee_Name.text

                ipDisabled = self.driver.find_element_by_xpath("""//*[@id="ctl00_HomePageContent_lbl_isipdisabled"]""")
                ipDisabled = ipDisabled.text

                disabilitytype = self.driver.find_element_by_xpath("""//*[@id="ctl00_HomePageContent_lbl_typeofdisablity"]""")
                disabilitytype = disabilitytype.text

                fatherHusbandName = self.driver.find_element_by_xpath("""//*[@id="ctl00_HomePageContent_lbl_fatherorhusband"]""")
                fatherHusbandName = fatherHusbandName.text

                maritalStatus = self.driver.find_element_by_xpath("""//*[@id="ctl00_HomePageContent_lbl_maraital_status"]""")
                maritalStatus = maritalStatus.text

                Gender = self.driver.find_element_by_xpath("""//*[@id="ctl00_HomePageContent_lbl_sex"]""")
                Gender = Gender.text

                State = self.driver.find_element_by_xpath("""//*[@id="ctl00_HomePageContent_lbl_per_state"]""")
                State = State.text

                District = self.driver.find_element_by_xpath("""//*[@id="ctl00_HomePageContent_lbl_per_district"]""")
                District = District.text

                State1 = self.driver.find_element_by_xpath("""//*[@id="ctl00_HomePageContent_lbl_pr_state"]""")
                State1 = State1.text

                District1 = self.driver.find_element_by_xpath("""//*[@id="ctl00_HomePageContent_lbl_pr_district"]""")
                District1 = District1.text

                presentAddressLine1 = self.driver.find_element_by_xpath("""//*[@id="ctl00_HomePageContent_lbl_pr_address1"]""")
                presentAddressLine1 = presentAddressLine1.text
                presentAddressLine2 = self.driver.find_element_by_xpath("""//*[@id="ctl00_HomePageContent_lbl_pr_address2"]""")
                presentAddressLine2 = presentAddressLine2.text
                presentAddressLine3 = self.driver.find_element_by_xpath("""//*[@id="ctl00_HomePageContent_lbl_pr_address3"]""")
                presentAddressLine3 = presentAddressLine3.text
                presentAddress = presentAddressLine1 + presentAddressLine2 + presentAddressLine3 + " " + District1 + " " + State1
                permanantAddressLine1 = self.driver.find_element_by_xpath(
                    """//*[@id="ctl00_HomePageContent_lbl_per_address1"]""")
                permanantAddressLine1 = permanantAddressLine1.text
                permanantAddressLine2 = self.driver.find_element_by_xpath(
                    """//*[@id="ctl00_HomePageContent_lbl_per_address2"]""")
                permanantAddressLine2 = permanantAddressLine2.text
                permanantAddressLine3 = self.driver.find_element_by_xpath(
                    """//*[@id="ctl00_HomePageContent_lbl_per_address3"]""")
                permanantAddressLine3 = permanantAddressLine3.text
                permanantAddress = permanantAddressLine1 + permanantAddressLine2 + permanantAddressLine3 + " " + District + " " + State

                dispensaryImpName = self.driver.find_element_by_xpath("""//*[@id="ctl00_HomePageContent_lblDisp"]""")
                dispensaryImpName = dispensaryImpName.text
                dispensaryImpstate = self.driver.find_element_by_xpath("""//*[@id="ctl00_HomePageContent_lbl_disp_state"]""")
                dispensaryImpstate = dispensaryImpstate.text
                dispensaryImpDistrict = self.driver.find_element_by_xpath("""//*[@id="ctl00_HomePageContent_lbl_disp_dist"]""")
                dispensaryImpDistrict = dispensaryImpDistrict.text
                dispensaryImpAddress7 = self.driver.find_element_by_xpath("""//*[@id="ctl00_HomePageContent_lbldispAddress"]""")
                dispensaryImpAddress7 = dispensaryImpAddress7.text
                dispensaryImpAddress = dispensaryImpAddress7 + " " +dispensaryImpDistrict+ " " + dispensaryImpstate

                nomineeName = self.driver.find_element_by_xpath("""//*[@id="ctl00_HomePageContent_lblNomName"]""")
                nomineeName = nomineeName.text
                relationshipWithIp = self.driver.find_element_by_xpath("""//*[@id="ctl00_HomePageContent_lblrelation"]""")
                relationshipWithIp = relationshipWithIp.text
                nomineestate = self.driver.find_element_by_xpath("""// *[ @ id = "ctl00_HomePageContent_lblState"]""")
                nomineestate = nomineestate.text
                nomineedistrict = self.driver.find_element_by_xpath("""// *[ @ id = "ctl00_HomePageContent_lblDistrict"]""")
                nomineedistrict = nomineedistrict.text
                nomineeAddress1 = self.driver.find_element_by_xpath("""//*[@id="ctl00_HomePageContent_lblAddress1"]""")
                nomineeAddress1 = nomineeAddress1.text
                nomineeAddress = nomineeAddress1 +" "+ nomineedistrict +" "+nomineestate

                print(nomineeAddress)
                nomineeMobileNumber = self.driver.find_element_by_xpath("""//*[@id="ctl00_HomePageContent_lblMblNo"]""")
                nomineeMobileNumber = nomineeMobileNumber.text
                Dispensary_Name = self.driver.find_element_by_xpath("""//*[@id="ctl00_HomePageContent_lblDisp"]""")
                Dispensary_Name = Dispensary_Name.text
                try:
                    name = self.driver.find_element_by_xpath("""//*[@id="ctl00_HomePageContent_dgSearch_ctl02_txtName"]""")
                    name = name.text
                    print(name)
                except:
                    name = ''
                    pass
                try:
                    name1 = self.driver.find_element_by_xpath("""//*[@id="ctl00_HomePageContent_dgSearch_ctl03_txtName"]""")
                    name1 = name1.text
                except:
                    name1 = ''
                    pass
                try:
                    name2 = self.driver.find_element_by_xpath("""//*[@id="ctl00_HomePageContent_dgSearch_ctl04_txtName"]""")
                    name2 = name2.text
                except:
                    name2 = ''
                    pass
                try:
                    name3 = self.driver.find_element_by_xpath("""//*[@id="ctl00_HomePageContent_dgSearch_ctl05_txtName"]""")
                    name3 = name3.text
                except:
                    name3 = ''
                    pass
                try:
                    relationship = self.driver.find_element_by_xpath(
                        """//*[@id="ctl00_HomePageContent_dgSearch_ctl02_txtRelationship"]""")
                    relationship = relationship.text
                except:
                    relationship = ''
                    pass
                try:
                    relationship1 = self.driver.find_element_by_xpath(
                        """//*[@id="ctl00_HomePageContent_dgSearch_ctl03_txtRelationship"]""")
                    relationship1 = relationship1.text
                except:
                    relationship1 = ''
                    pass
                try:
                    relationship2 = self.driver.find_element_by_xpath(
                        """//*[@id="ctl00_HomePageContent_dgSearch_ctl04_txtRelationship"]""")
                    relationship2 = relationship2.text
                except:
                    relationship2 = ''
                    pass
                try:
                    relationship3 = self.driver.find_element_by_xpath(
                        """//*[@id="ctl00_HomePageContent_dgSearch_ctl05_txtRelationship"]""")
                    relationship3 = relationship3.text
                except:
                    relationship3 = ''
                    pass
                try:
                    residingWithEmployee = self.driver.find_element_by_xpath(
                        """//*[@id="ctl00_HomePageContent_dgSearch_ctl02_txtResiding_With_Employee"]""")
                    residingWithEmployee = residingWithEmployee.text
                except:
                    residingWithEmployee = ''
                    pass
                try:
                    residingWithEmployee1 = self.driver.find_element_by_xpath(
                        """//*[@id="ctl00_HomePageContent_dgSearch_ctl03_txtResiding_With_Employee"]""")
                    residingWithEmployee1 = residingWithEmployee1.text
                except:
                    residingWithEmployee1 = ''
                    pass
                try:
                    residingWithEmployee2 = self.driver.find_element_by_xpath(
                        """//*[@id="ctl00_HomePageContent_dgSearch_ctl04_txtResiding_With_Employee"]""")
                    residingWithEmployee2 = residingWithEmployee2.text
                except:
                    residingWithEmployee2 = ''
                    pass
                try:
                    residingWithEmployee3 = self.driver.find_element_by_xpath(
                        """//*[@id="ctl00_HomePageContent_dgSearch_ctl05_txtResiding_With_Employee"]""")
                    residingWithEmployee3 = residingWithEmployee3.text
                except:
                    residingWithEmployee3 = ''
                    pass
                try:
                    dateOfBirth = self.driver.find_element_by_xpath(
                        """//*[@id="ctl00_HomePageContent_dgSearch_ctl02_txtDate_of_Birth"]""")
                    dateOfBirth = dateOfBirth.text
                    from datetime import datetime
                    date_obj = datetime.strptime(dateOfBirth, '%d -%m -%Y')
                    dateOfBirth = date_obj.strftime('%d-%b-%Y')
                except:
                    dateOfBirth = ''
                    pass
                try:
                    dateOfBirth1 = self.driver.find_element_by_xpath(
                        """//*[@id="ctl00_HomePageContent_dgSearch_ctl03_txtDate_of_Birth"]""")
                    dateOfBirth1 = dateOfBirth1.text
                    from datetime import datetime
                    date_obj = datetime.strptime(dateOfBirth1, '%d -%m -%Y')
                    dateOfBirth1 = date_obj.strftime('%d-%b-%Y')
                except:
                    dateOfBirth1 = ''
                    pass
                try:
                    dateOfBirth2 = self.driver.find_element_by_xpath(
                        """//*[@id="ctl00_HomePageContent_dgSearch_ctl04_txtDate_of_Birth"]""")
                    dateOfBirth2 = dateOfBirth2.text
                    from datetime import datetime
                    date_obj = datetime.strptime(dateOfBirth2, '%d -%m -%Y')
                    dateOfBirth2 = date_obj.strftime('%d-%b-%Y')

                except:
                    dateOfBirth2 = ''
                    pass
                try:
                    dateOfBirth3 = self.driver.find_element_by_xpath(
                        """//*[@id="ctl00_HomePageContent_dgSearch_ctl05_txtDate_of_Birth"]""")
                    dateOfBirth3 = dateOfBirth3.text
                    from datetime import datetime
                    date_obj = datetime.strptime(dateOfBirth3, '%d -%m -%Y')
                    dateOfBirth3 = date_obj.strftime('%d-%b-%Y')

                except:
                    dateOfBirth3 = ''
                    pass
                try:
                    state = self.driver.find_element_by_xpath("""//*[@id="ctl00_HomePageContent_dgSearch_ctl02_txtState"]""")
                    state = state.text
                except:
                    state = ''
                    pass
                try:
                    state1 = self.driver.find_element_by_xpath("""//*[@id="ctl00_HomePageContent_dgSearch_ctl03_txtState"]""")
                    state1 = state1.text
                except:
                    state1 = ''
                    pass
                try:
                    state2 = self.driver.find_element_by_xpath("""//*[@id="ctl00_HomePageContent_dgSearch_ctl04_txtState"]""")
                    state2 = state2.text
                except:
                    state2 = ''
                    pass
                try:
                    state3 = self.driver.find_element_by_xpath("""//*[@id="ctl00_HomePageContent_dgSearch_ctl05_txtState"]""")
                    state3 = state3.text
                except:
                    state3 = ''
                    pass
                try:
                    district = self.driver.find_element_by_xpath(
                        """//*[@id="ctl00_HomePageContent_dgSearch_ctl02_txtDistrict"]""")
                    district = district.text
                except:
                    district = ''
                    pass
                try:
                    district1 = self.driver.find_element_by_xpath(
                        """//*[@id="ctl00_HomePageContent_dgSearch_ctl03_txtDistrict"]""")
                    district1 = district1.text
                except:
                    district1 = ''
                    pass
                try:
                    district2 = self.driver.find_element_by_xpath(
                        """//*[@id="ctl00_HomePageContent_dgSearch_ctl04_txtDistrict"]""")
                    district2 = district2.text
                except:
                    district2 = ''
                    pass
                try:
                    district3 = self.driver.find_element_by_xpath(
                        """//*[@id="ctl00_HomePageContent_dgSearch_ctl05_txtDistrict"]""")
                    district3 = district3.text
                except:
                    district3 = ''
                    pass
                try:
                    uhidNumber = self.driver.find_element_by_xpath("""//*[@id="ctl00_HomePageContent_dgSearch_ctl02_txtuhid"]""")
                    uhidNumber = uhidNumber.text
                except:
                    uhidNumber = ''
                    pass
                try:
                    uhidNumber1 = self.driver.find_element_by_xpath(
                        """//*[@id="ctl00_HomePageContent_dgSearch_ctl03_txtuhid"]""")
                    uhidNumber1 = uhidNumber1.text
                except:
                    uhidNumber1 = ''
                    pass
                try:
                    uhidNumber2 = self.driver.find_element_by_xpath(
                        """//*[@id="ctl00_HomePageContent_dgSearch_ctl04_txtuhid"]""")
                    uhidNumber2 = uhidNumber2.text
                except:
                    uhidNumber2 = ''
                    pass
                try:
                    uhidNumber3 = self.driver.find_element_by_xpath(
                        """//*[@id="ctl00_HomePageContent_dgSearch_ctl05_txtuhid"]""")
                    uhidNumber3 = uhidNumber3.text
                except:
                    uhidNumber3 = ''
                    pass

                self.driver.switch_to.window(window_before)
                self.driver.find_element_by_xpath("""//*[@id="IPEligibility"]""").click()
                window_after1 = self.driver.window_handles[2]
                self.driver.switch_to.window(window_after1)

                try:
                    benefitStartDate = self.driver.find_element_by_xpath("""//*[@id="ctl00_HomePageContent_lblBftStDate"]""")
                    benefitStartDate = benefitStartDate.text
                    date_obj = datetime.strptime(benefitStartDate, '%d %b %Y')
                    benefitStartDate = date_obj.strftime('%d-%b-%Y')



                except:
                    benefitStartDate = ''
                    pass
                try:
                    benefitStartDate1 = self.driver.find_element_by_xpath("""//*[@id="ctl00_HomePageContent_lblBftStDate1"]""")
                    benefitStartDate1 = benefitStartDate1.text
                    date_obj = datetime.strptime(benefitStartDate1, '%d %b %Y')
                    benefitStartDate1 = date_obj.strftime('%d-%b-%Y')
                except:
                    benefitStartDate1 = ''
                    pass
                try:
                    totalWages = self.driver.find_element_by_xpath("""//*[@id="ctl00_HomePageContent_LblAvgEmpWages"]""")
                    totalWages = totalWages.text
                except:
                    totalWages = ''
                    pass
                try:
                    totalWages1 = self.driver.find_element_by_xpath("""//*[@id="ctl00_HomePageContent_LblAvgEmpWages1"]""")
                    totalWages1 = totalWages1.text
                except:
                    totalWages1 = ''
                    pass
                try:
                    benefitEndDate = self.driver.find_element_by_xpath("""//*[@id="ctl00_HomePageContent_lblBftEndDate"]""")
                    benefitEndDate = benefitEndDate.text
                    date_obj = datetime.strptime(benefitEndDate, '%d %b %Y')
                    benefitEndDate = date_obj.strftime('%d-%b-%Y')

                except:
                    benefitEndDate = ''
                    pass
                try:
                    benefitEndDate1 = self.driver.find_element_by_xpath("""//*[@id="ctl00_HomePageContent_lblBftEndDate1"]""")
                    benefitEndDate1 = benefitEndDate1.text
                    date_obj = datetime.strptime(benefitEndDate1, '%d %b %Y')
                    benefitEndDate1 = date_obj.strftime('%d-%b-%Y')

                except:
                    benefitEndDate1 = ''
                    pass
                try:
                    workingPayableDays = self.driver.find_element_by_xpath(
                        """//*[@id="ctl00_HomePageContent_LblAvgEmpWkngDays"]""")
                    workingPayableDays = workingPayableDays.text
                except:
                    workingPayableDays = ''
                    pass
                try:
                    workingPayableDays1 = self.driver.find_element_by_xpath(
                        """//*[@id="ctl00_HomePageContent_LblAvgEmpWkngDays1"]""")
                    workingPayableDays1 = workingPayableDays1.text
                except:
                    workingPayableDays1 = ''
                    pass
                try:
                    contributionPeriodFrom = self.driver.find_element_by_xpath(
                        """//*[@id="ctl00_HomePageContent_lblContPrdFrom"]""")
                    contributionPeriodFrom = contributionPeriodFrom.text
                    date_obj = datetime.strptime(contributionPeriodFrom, '%d %b %Y')
                    contributionPeriodFrom = date_obj.strftime('%d-%b-%Y')

                except:
                    contributionPeriodFrom = ''
                    pass
                try:
                    contributionPeriodFrom1 = self.driver.find_element_by_xpath(
                        """//*[@id="ctl00_HomePageContent_lblContPrdFrom1"]""")
                    contributionPeriodFrom1 = contributionPeriodFrom1.text
                    date_obj = datetime.strptime(contributionPeriodFrom1, '%d %b %Y')
                    contributionPeriodFrom1 = date_obj.strftime('%d-%b-%Y')
                except:
                    contributionPeriodFrom1 = ''
                    pass
                try:
                    contributionPeriodTo = self.driver.find_element_by_xpath("""//*[@id="ctl00_HomePageContent_lblContPrdTo"]""")
                    contributionPeriodTo = contributionPeriodTo.text
                    date_obj = datetime.strptime(contributionPeriodTo, '%d %b %Y')
                    contributionPeriodTo = date_obj.strftime('%d-%b-%Y')
                except:
                    contributionPeriodTo = ''
                    pass
                try:
                    contributionPeriodTo1 = self.driver.find_element_by_xpath(
                        """//*[@id="ctl00_HomePageContent_lblContPrdTo1"]""")
                    contributionPeriodTo1 = contributionPeriodTo1.text
                    date_obj = datetime.strptime(contributionPeriodTo1, '%d %b %Y')
                    contributionPeriodTo1 = date_obj.strftime('%d-%b-%Y')
                except:
                    contributionPeriodTo1 = ''
                    pass
                #self.driver.switch_to.window(window_before)
             #   self.driver.find_element_by_xpath("""//*[@id="ContributionDetails"]""").click()
             #   window_after2 = self.driver.window_handles[3]
             #   self.driver.switch_to.window(window_after2)
             #   try:
             #       wagePeriod = self.driver.find_element_by_xpath(
             #           """//*[@id="ctl00_HomePageContent_grd_mc_ctl02_lblContribPeriod"]""")
            #        wagePeriod = wagePeriod.text
             #   except:
             #       wagePeriod = ''
             #       pass

            #    try:
            #        wagePeriod1 = self.driver.find_element_by_xpath(
             #           """//*[@id="ctl00_HomePageContent_grd_mc_ctl03_lblContribPeriod"]""")
             #       wagePeriod1 = wagePeriod1.text
            #    except:
             #       wagePeriod1 = ''
            #        pass
            #    try:
             #       totalMonthlyWages = self.driver.find_element_by_xpath(
           #             """//*[@id="ctl00_HomePageContent_grd_mc_ctl02_lblAmountPaid"]""")
           #         totalMonthlyWages = totalMonthlyWages.text
           #     except:
            #        totalMonthlyWages = ''
           #         pass
           #     try:
          #          totalMonthlyWages1 = self.driver.find_element_by_xpath(
            #            """//*[@id="ctl00_HomePageContent_grd_mc_ctl03_lblAmountPaid"]""")
            #        totalMonthlyWages1 = totalMonthlyWages1.text
           #     except:
           #         totalMonthlyWages1 = ''
            #        pass
           #     try:
          #          payableDays = self.driver.find_element_by_xpath(
           #             """//*[@id="ctl00_HomePageContent_grd_mc_ctl02_lblTotaldays"]""")
            #        payableDays = payableDays.text
           #     except:
           #         payableDays = ''
            #        pass
             #   try:
              #      payableDays1 = self.driver.find_element_by_xpath(
             #           """//*[@id="ctl00_HomePageContent_grd_mc_ctl03_lblTotaldays"]""")
            #        payableDays1 = payableDays1.text
            #    except:
            #        payableDays1 = ''
            #        pass
           #     try:
            #        employeeContribution = self.driver.find_element_by_xpath(
            #            """//*[@id="ctl00_HomePageContent_grd_mc_ctl02_lblcontrib"]""")
           #         employeeContribution = employeeContribution.text
       #         except:
             #       employeeContribution = ''
            #        pass
           #     try:
            #        employeeContribution1 = self.driver.find_element_by_xpath(
            #            """//*[@id="ctl00_HomePageContent_grd_mc_ctl03_lblcontrib"]""")
            #        employeeContribution1 = employeeContribution1.text
             #   except:
             #       employeeContribution1 = ''
              #      pass
                #self.driver.switch_to.window(window_before)
                #self.driver.find_element_by_xpath("""//*[@id="StatusClaim"]""").click()
                #window_after3 = self.driver.window_handles[4]
                #self.driver.switch_to.window(window_after3)
                #try:
                    #fromDate = self.driver.find_element_by_xpath("""//*[@id="ctl00_HomePageContent_txtClaimStartDate"]""")
                    #fromDate = fromDate.text
                #except:
                    #fromDate = ''
                    #pass
                #try:
                    #toDate = self.driver.find_element_by_xpath("""//*[@id="ctl00_HomePageContent_txtClaimEndDate"]""")
                    #toDate = toDate.text
                #except:
                    #toDate = ''
                    #pass
                #try:
                    #claimId = self.driver.find_element_by_xpath("""//*[@id="ctl00_HomePageContent_txtClaimID"]""")
                    #claimId = claimId.text
                #except:
                    #claimId = ''
                    #pass
                #try:
                    #acknowledgementNumber = ''
                #except:
                    #acknowledgementNumber = ''
                    #pass
                import json
                message = "Successfully Completed."
                code = "SRC001"
                if len(benefitStartDate) > 0:
                    Be = {}
                    Be["benefitStartDate"] = benefitStartDate
                    Be["benefitEndDate"] = benefitEndDate
                    Be["totalWages"] = totalWages
                    Be["workingPayableDays"] = workingPayableDays
                    Be["contributionPeriodFrom"] = contributionPeriodFrom
                    Be["contributionPeriodTo"] = contributionPeriodTo
                else:
                    Be = 'null'
                if len(benefitStartDate1) > 0:
                    Be1 = {}
                    Be1["benefitStartDate"] = benefitStartDate1
                    Be1["benefitEndDate"] = benefitEndDate1
                    Be1["totalWages"] = totalWages1
                    Be1["workingPayableDays"] = workingPayableDays1
                    Be1["contributionPeriodFrom"] = contributionPeriodFrom1
                    Be1["contributionPeriodTo"] = contributionPeriodTo1
                else:
                    Be1 = 'null'

                if len(name)>0:
                    Na = {}
                    Na["name"] = name
                    Na["relationship"] = relationship
                    Na["residingWithEmployee"] = residingWithEmployee
                    Na["dateOfBirth"] = dateOfBirth
                    Na["state"] = state
                    Na["district"] = district
                    Na["uhidNumber"] = uhidNumber
                else:
                    Na = "null"
                if len(name1)>0:
                    Na1 = {}
                    Na1["name"] = name1
                    Na1["relationship"] = relationship1
                    Na1["residingWithEmployee"] = residingWithEmployee1
                    Na1["dateOfBirth"] = dateOfBirth1
                    Na1["state"] = state1
                    Na1["district"] = district1
                    Na1["uhidNumber"] = uhidNumber1
                else:
                    Na1 = "null"
                if len(name2)>0:
                    Na2 = {}
                    Na2["name"] = name2
                    Na2["relationship"] = relationship2
                    Na2["residingWithEmployee"] = residingWithEmployee2
                    Na2["dateOfBirth"] = dateOfBirth2
                    Na2["state"] = state2
                    Na2["district"] = district2
                    Na2["uhidNumber"] = uhidNumber2
                else:
                    Na2 = "null"
                if len(name3)>0:
                    Na3 = {}
                    Na3["name"] = name3
                    Na3["relationship"] = relationship3
                    Na3["residingWithEmployee"] = residingWithEmployee3
                    Na3["dateOfBirth"] = dateOfBirth3
                    Na3["state"] = state3
                    Na3["district"] = district3
                    Na3["uhidNumber"] = uhidNumber3
                else:
                    Na3 = "null"
             #   if len(wagePeriod) > 0:
             #       Wa = {}
               #     Wa["wagePeriod"] = wagePeriod
               #    Wa["totalMonthlyWages"] = totalMonthlyWages
              #      Wa["payableDays"] = payableDays
              #      Wa["employeeContribution"] = employeeContribution
               # else:
                    Wa = "null"
               # if len(wagePeriod1) > 0:
               #     Wa1 = {}
               #     Wa1["wagePeriod"] = wagePeriod1
                #    Wa1["totalMonthlyWages"] = totalMonthlyWages1
                #    Wa1["payableDays"] = payableDays1
                #    Wa1["employeeContribution"] = employeeContribution1
               # else:
                    Wa1 = 'null'
                #if len(fromDate) > 0:
                    #Cl = {}
                   # Cl["fromDate"] = fromDate
                   # Cl["toDate"] = toDate
                    #Cl["claimId"] = claimId
                    #Cl["acknowledgementNumber"] = acknowledgementNumber
                #else:
               #     Cl = 'null'

                dic = {}
                dic["insuranceNumber"] = Insurance
                dic["uhidNumber"] = UHID_Number
                dic["employeeName"] = Employee_Name
                dic["registrationDate"] = Registration_Date
                dic["dateOfBirth"] = Date_of_Birth
                dic["mobileNumber"] = Phone_Number
                dic["ipDisabled"] = ipDisabled
                dic["typeOfDisability"] = disabilitytype
                dic["fatherHusbandName"] = fatherHusbandName
                dic["maritalStatus"] = maritalStatus
                dic["gender"] = Gender
                dic["presentAddress"] = presentAddress
                dic["permanentAddress"] = permanantAddress
                dic["dispensaryImpName"] = dispensaryImpName
                dic["dispensaryImpAddress"] = dispensaryImpAddress
                dic["nomineeName"] = nomineeName
                dic["relationshipWithIp"] = relationshipWithIp
                dic["nomineeAddress"] = nomineeAddress
                dic["nomineeMobileNumber"] = nomineeMobileNumber
                if Be == 'null' and Be1 == 'null':
                    dic["entitlementToBenefit"] = []
                elif Be1 == 'null':
                    dic["entitlementToBenefit"] = [Be]
                else:
                    dic["entitlementToBenefit"] = [Be, Be1]

                #if Na and Na1 and Na2 and Na3 == 'null':
                #dic_return=False
                #if na:
                 #   dic_return_0=True
                  #  if na1:
                   #     if na2:
                    #        if na3:
                     #           dic_return4=True
                if Na=='null'and Na1 == 'null' and Na2 == 'null' and Na3 == 'null':
                    dic["familyParticularsOfInsuredPerson"] = []
                #if dic_return
                elif Na1 == 'null'and Na2 == 'null' and Na3 == 'null':
                    dic["familyParticularsOfInsuredPerson"] = [Na]
                elif Na2 == 'null' and Na3 == 'null':
                    dic["familyParticularsOfInsuredPerson"] = [Na, Na1]
                elif Na3 == 'null':
                    dic["familyParticularsOfInsuredPerson"] = [Na, Na1, Na2]
                else:
                    #if dic_return==True:
                    dic["familyParticularsOfInsuredPerson"] = [Na, Na1, Na2, Na3]

                #if Wa and Wa1 == 'null':
                    #dic["contributionDetails"] = []
                #elif Wa1 == "null":
                    #dic["contributionDetails"] = [Wa]
               # else:
                    #dic["contributionDetails"] = [Wa, Wa1]
                #f Cl == 'null':
                    #dic["claimStatus"] = []
               # else:
                    #dic["claimStatus"] = [Cl]
                dic = {"data": dic, "responseCode": code, "responseMessage": message}
                self.logStatus("info", "successfully scrapped information",self.takeScreenshot())
                return dic

            if r == 2:
                dic = {}
                message = "Unable To Process. Please Reach Out To Support."
                code = "EUP007"

                dic = {"data": "null", "responseCode": code, "responseMessage": message}
                self.logStatus("info", "Contact support")
                return dic
            if r == 3:
                dic = {}
                message = "Unable To Process. Please Reach Out To Support."
                code = "EUP007"

                dic = {"data": "null", "responseCode": code, "responseMessage": message}
                self.logStatus("info", "Contact support")
                return dic
            if x == 5:
                dic = {}
                message = "No Information Found."
                # fgdfd
                code = "ENI004"
                self.logStatus("info", "No Info Found")
                dic = {"data": "null", "responseCode": code, "responseMessage": message}
                self.logStatus("info", "Ip Number not found.")
                return dic


    def ESIF_response(self,insuranceNumber):
        import json
        dic = {}

        try:
            self.logStatus("info", "opening driver page")
            dic = self.generate_ESIC(insuranceNumber)

        except Exception as e:
            print(e)

            self.logStatus("critical", "Captcha error retrying")
            try:
                self.logStatus("info", "opening driver page")
                dic = self.generate_ESIC(insuranceNumber)

            except Exception as e:
                print(e)

                self.logStatus("critical", "Captcha error retrying")
                try:
                    self.logStatus("info", "opening driver page")
                    dic = self.generate_ESIC(insuranceNumber)

                except Exception as e:


                    message = "No Information Found."
                    #fgdfd
                    code = "ENI004"
                    self.logStatus("info", "No Info Found")
                    dic = {"data": "null", "responseCode": code, "responseMessage": message}

        dic = json.dumps(dic)
        return dic