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
#from webdriver_manager.chrome import ChromeDriverManager

class CouldNotCreateDriver(Exception):
    pass

class LEI:

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
            nine_hours_from_now = datetime.now()+ timedelta(hours=5.5)
            self.dbObj.insertLog(self.refid,'{:%Y-%m-%d %H:%M:%S}'.format(nine_hours_from_now), level, message,
                                 'LEI', self.env, screenshot)
        print(f"{level}: {message}, screenshot: {screenshot}")

    def breakcaptcha(self):
        import io
        import os
        from google.cloud import vision
        import time
        import io
        self.driver.find_element_by_xpath("""//*[@id="ctl00_ContentPlaceHolder1_txtCaptcha"]""").click()
        self.driver.find_element_by_xpath("""// *[ @ id = "ctl00_ContentPlaceHolder1_txtCaptcha"]""")
        self.driver.find_element_by_xpath(
            """/html/body/form/div[5]/div/div[1]/table/tbody/tr[1]/td/table/tbody/tr[1]/td[1]/div/div/img""").screenshot(
            'captcha.png')
        from azcaptchaapi import AZCaptchaApi
        api = AZCaptchaApi('k2b7phlwtfrmbzxnwjjqr96mv4dqgnfg')
        with open(os.path.join(self.FOLDER_PATH, self.FILE_NAME), 'rb') as captcha_file:
            captcha = api.solve(captcha_file)

        k = captcha.await_result()
        self.makeDriverDirs()
        try:
            sname = str(k) + '.png'
            screenshotName = os.path.join(self.screenshotDir, f"{sname}")
            self.driver.find_element_by_xpath("""//*[@id="img1"]""").screenshot(screenshotName)
            self.uploadToS3(os.path.join(screenshotName), 'LEI/' + sname)
        except:
            pass
        self.driver.find_element_by_xpath("""//*[@id="ctl00_ContentPlaceHolder1_txtCaptcha"]""").click()
        self.driver.find_element_by_xpath("""//*[@id="ctl00_ContentPlaceHolder1_txtCaptcha"]""").send_keys(k)

        try:
            self.driver.find_element_by_xpath("""// *[ @ id = "ctl00_ContentPlaceHolder1_btnSearch"]""").click()
        except Exception as e:
            print(e)



    def generate_LEI(self,legalEntityIdentifierNumber):

        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        import io
       # from webdriver_manager.chrome import ChromeDriverManager
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

        #self.driver = webdriver.Chrome('/usr/local/bin/chromedriver',options=chrome_options)
      #  self.logStatus("info", "ESIF page opened",self.takeScreenshot())
        self.logStatus("info", "Driver created")
        from selenium import webdriver
        import os
        import time
      #  from webdriver_manager.chrome import ChromeDriverManager
        self.driver = webdriver.Chrome("/usr/local/bin/chromedriver",options=chrome_options)
        try:
            self.driver.get("https://www.ccilindia-lei.co.in/USR_SEARCH_ANONYMOUS.aspx")
        except:
            pass
        time.sleep(2)

        self.driver.find_element_by_xpath("""// *[ @ id = "ctl00_ContentPlaceHolder1_chkforeigndb"]""").click()
        try:
            self.driver.find_element_by_xpath("""/html/body/form/div[5]/div/div[1]/div[2]/table/tbody/tr[3]/td[2]/input""").click()
        except:
            time.sleep(2)
            self.driver.find_element_by_xpath(
                """/html/body/form/div[5]/div/div[1]/div[2]/table/tbody/tr[3]/td[2]/input""").click()
        pass

        time.sleep(3)
        self.driver.find_element_by_xpath("""//*[@id="ctl00_ContentPlaceHolder1_txtLeiCode"]""").click()
        self.driver.find_element_by_xpath("""//*[@id="ctl00_ContentPlaceHolder1_txtLeiCode"]""").send_keys(
            legalEntityIdentifierNumber)
        window_before = self.driver.window_handles[0]

        window_before_title = self.driver.title

        self.breakcaptcha()
        time.sleep(3)
        from selenium.webdriver.common.alert import Alert
        f = 1
        try:

            self.driver.find_element_by_xpath("""//*[@id="ctl00_ContentPlaceHolder1_btnSearch"]""").click()

        except Exception as e:
            gg = ("Error {0}".format(str(e)))
            if gg.find("No Data Found.") != -1:
                f = 2


        time.sleep(3)
        if f == 2:
            dic = {}
            message = "No Information Found."
            # fgdfd
            code = "ENI004"
            self.logStatus("info", "No Info Found")
            dic = {"data": "null", "responseCode": code, "responseMessage": message}
            self.logStatus("info", "Ip Number not found.")
            return dic
        from selenium.webdriver.common.keys import Keys
        if f == 1:
            try:
                self.driver.find_element_by_xpath(
                    """//*[@id="ctl00_ContentPlaceHolder1_gdvSearchLEI_ctl02_lnkViewDetails"]""").click()
            except:
                pass


            self.driver.find_element_by_xpath("""//*[@id="ctl00_ContentPlaceHolder1_gdvSearchLEI_ctl02_lnkViewDetails"]""").click()
            window_after = self.driver.window_handles[1]
            self.driver.switch_to.window(window_after)
            time.sleep(3)
            leiNumber = self.driver.find_element_by_xpath("""/html/body/form/div[3]/div/div[1]/div[2]/fieldset/fieldset[2]/table/tbody/tr[1]/td[2]/input""")
            leiNumber = leiNumber.get_attribute("value")

            legalName = self.driver.find_element_by_xpath(
                """//*[@id="ctl00_ContentPlaceHolder1_txtLegalName"]""")
            legalName = legalName.get_attribute("value")
            registeredFirstAddressLine = self.driver.find_element_by_xpath(
                    """// *[ @ id = "ctl00_ContentPlaceHolder1_txtRgdAdd1"]""")
            registeredFirstAddressLine = registeredFirstAddressLine.get_attribute("value")
            additionalAddressLine1 = self.driver.find_element_by_xpath(
                    """//*[@id="ctl00_ContentPlaceHolder1_txtRgdAdd2"]""")
            additionalAddressLine1 = additionalAddressLine1.get_attribute("value")
            additionalAddressLine2 = self.driver.find_element_by_xpath(
                    """// *[ @ id = "ctl00_ContentPlaceHolder1_txtRgdAdd3"]""")
            additionalAddressLine2 = additionalAddressLine2.get_attribute("value")
            additionalAddressLine3 = self.driver.find_element_by_xpath(
                    """// *[ @ id = "ctl00_ContentPlaceHolder1_txtRgdAdd4"]""")
            additionalAddressLine3 = additionalAddressLine3.get_attribute("value")
            country = self.driver.find_element_by_xpath("""// *[ @ id = "ctl00_ContentPlaceHolder1_txtRgdCountry"]""")
            country = country.get_attribute("value")
            region = self.driver.find_element_by_xpath("""// *[ @ id = "ctl00_ContentPlaceHolder1_txtRgdRegion"]""")
            region = region.get_attribute("value")
            city = self.driver.find_element_by_xpath("""// *[ @ id = "ctl00_ContentPlaceHolder1_txtRgdCity"]""")
            city = city.get_attribute("value")
            postalPincode = self.driver.find_element_by_xpath("""//*[@id="ctl00_ContentPlaceHolder1_txtRgdZipCode"]""")
            postalPincode = postalPincode.get_attribute("value")
            addressType1 = self.driver.find_element_by_xpath("""// *[ @ id = "templatemo_content"] / div[1] / div[2] / fieldset / fieldset[3] / legend""")
            addressType1 = addressType1.text
            addressType2 = self.driver.find_element_by_xpath(
                """// *[ @ id = "templatemo_content"] / div[1] / div[2] / fieldset / fieldset[4] / legend""")
            addressType2 = addressType2.text
            registeredFirstAddressLine1 = self.driver.find_element_by_xpath(
                    """// *[ @ id = "ctl00_ContentPlaceHolder1_txtHQAdd1"]""")
            registeredFirstAddressLine1 = registeredFirstAddressLine1.get_attribute("value")
            additionalAddressLine4 = self.driver.find_element_by_xpath(
                """//*[@id="ctl00_ContentPlaceHolder1_txtHQAdd2"]""")
            additionalAddressLine4 = additionalAddressLine4.get_attribute("value")
            additionalAddressLine5 = self.driver.find_element_by_xpath(
                """//*[@id="ctl00_ContentPlaceHolder1_txtHQAdd3"]""")
            additionalAddressLine5 = additionalAddressLine5.get_attribute("value")
            additionalAddressLine6 = self.driver.find_element_by_xpath(
                """//*[@id="ctl00_ContentPlaceHolder1_txtHQAdd4"]""")
            additionalAddressLine6 = additionalAddressLine6.get_attribute("value")
            try:
                additionalAddressLine6 = additionalAddressLine6.replace('"',"")
            except:
                additionalAddressLine6 = self.driver.find_element_by_xpath(
                    """//*[@id="ctl00_ContentPlaceHolder1_txtHQAdd4"]""")
                additionalAddressLine6 = additionalAddressLine6.get_attribute("value")
                pass

            country1 = self.driver.find_element_by_xpath("""// *[ @ id = "ctl00_ContentPlaceHolder1_txtHQCountry"]""")
            country1 = country1.get_attribute("value")
            region1 = self.driver.find_element_by_xpath("""//*[@id="ctl00_ContentPlaceHolder1_txtHQRegion"]""")
            region1 = region1.get_attribute("value")
            city1 = self.driver.find_element_by_xpath("""// *[ @ id = "ctl00_ContentPlaceHolder1_txtHQCity"]""")
            city1 = city1.get_attribute("value")
            postalPincode1 = self.driver.find_element_by_xpath("""//*[@id="ctl00_ContentPlaceHolder1_txtHQZipCode"]""")
            postalPincode1 = postalPincode1.get_attribute("value")
            registrationAuthorityName = self.driver.find_element_by_xpath("""// *[ @ id = "ctl00_ContentPlaceHolder1_txtBusiIdenName"]""")
            registrationAuthorityName = registrationAuthorityName.get_attribute("value")
            registrationAuthorityId = self.driver.find_element_by_xpath("""//*[@id="ctl00_ContentPlaceHolder1_txtBusiIdenID"]""")
            registrationAuthorityId = registrationAuthorityId.get_attribute("value")
            jurisdiction = self.driver.find_element_by_xpath("""//*[@id="ctl00_ContentPlaceHolder1_txtJuris"]""")
            jurisdiction = jurisdiction.get_attribute("value")
            legalForm = self.driver.find_element_by_xpath("""//*[@id="ctl00_ContentPlaceHolder1_txtLegalForm"]""")
            legalForm = legalForm.get_attribute("value")
            leiRegistrationDate = self.driver.find_element_by_xpath("""//*[@id="ctl00_ContentPlaceHolder1_txtLeiRegistrationDate"]""")
            leiRegistrationDate = leiRegistrationDate.get_attribute("value")
            try:
                from datetime import datetime
                date_obj = datetime.strptime(leiRegistrationDate, '%Y-%m-%d')
                leiRegistrationDate = date_obj.strftime('%d-%b-%Y')
            except:
                pass
            leiRegLastUpdateDate = self.driver.find_element_by_xpath("""//*[@id="ctl00_ContentPlaceHolder1_txtLeiRegistrationLastUpdate"]""")
            leiRegLastUpdateDate = leiRegLastUpdateDate.get_attribute("value")
            try:
                from datetime import datetime
                date_obj = datetime.strptime(leiRegLastUpdateDate, '%Y-%m-%d')
                leiRegLastUpdateDate = date_obj.strftime('%d-%b-%Y')
            except:
                pass
            entityStatus = self.driver.find_element_by_xpath(
                """// *[ @ id = "ctl00_ContentPlaceHolder1_txtEntityStatus"]""")
            entityStatus = entityStatus.get_attribute("value")
            entityExpirationDate = self.driver.find_element_by_xpath("""// *[ @ id = "ctl00_ContentPlaceHolder1_txtEntityExpirationDate"]""")
            entityExpirationDate = entityExpirationDate.get_attribute("value")
            try:
                from datetime import datetime
                date_obj = datetime.strptime(entityExpirationDate, '%Y-%m-%d')
                entityExpirationDate = date_obj.strftime('%d-%b-%Y')
            except:
                pass
            leiNextRenewalDate = self.driver.find_element_by_xpath("""//*[@id="ctl00_ContentPlaceHolder1_txtLEINextRenewalDate"]""")
            leiNextRenewalDate = leiNextRenewalDate.get_attribute("value")
            try:
                from datetime import datetime
                date_obj = datetime.strptime(leiNextRenewalDate, '%Y-%m-%d')
                leiNextRenewalDate = date_obj.strftime('%d-%b-%Y')
            except:
                pass
            entityExpirationReason = self.driver.find_element_by_xpath("""//*[@id="ctl00_ContentPlaceHolder1_txtEntityExpirationReason"]""")
            entityExpirationReason = entityExpirationReason.get_attribute("value")
            leiRegistrationStatus = self.driver.find_element_by_xpath("""//*[@id="ctl00_ContentPlaceHolder1_txtLEIRegistrationStatus"]""")
            leiRegistrationStatus = leiRegistrationStatus.get_attribute("value")
            successorLei = self.driver.find_element_by_xpath("""//*[@id="ctl00_ContentPlaceHolder1_txtSuccsessorLEI"]""")
            successorLei = successorLei.get_attribute("value")
            louId = self.driver.find_element_by_xpath("""//*[@id="ctl00_ContentPlaceHolder1_txtLOUId"]""")
            louId = louId.get_attribute("value")
            leiValidationSource = self.driver.find_element_by_xpath("""//*[@id="ctl00_ContentPlaceHolder1_txtLEIValidationSource"]""")
            leiValidationSource = leiValidationSource.get_attribute("value")

            self.driver.find_element_by_xpath("""//*[@id="ctl00_ContentPlaceHolder1_btnlinkRelationshipData"]""").click()
            time.sleep(2)
            try:
                legalEntityName = self.driver.find_element_by_xpath("""//*[@id="ctl00_ContentPlaceHolder1_txtDPLegalEntityName"]""")
                legalEntityName = legalEntityName.get_attribute("value")
                try:
                    legalEntityNamech = legalEntityName.replace(" ", "")
                    if legalEntityNamech.isalpha() == True:
                        legalEntityName = legalEntityName
                    else:
                        legalEntityName = "Unspecified Output"
                except:
                    pass
                relationshipType = self.driver.find_element_by_xpath("""//*[@id="ctl00_ContentPlaceHolder1_txtDPRRRelType"]""")
                relationshipType = relationshipType.get_attribute("value")
                percentShareholding = self.driver.find_element_by_xpath("""//*[@id="ctl00_ContentPlaceHolder1_txtDPRRShare"]""")
                percentShareholding = percentShareholding.get_attribute("value")
                accountingStandard = self.driver.find_element_by_xpath("""//*[@id="ctl00_ContentPlaceHolder1_txtDPRRAccStd"]""")
                accountingStandard = accountingStandard.get_attribute("value")
                validationReference = self.driver.find_element_by_xpath("""//*[@id="ctl00_ContentPlaceHolder1_txtDPRRValRef"]""")
                validationReference = validationReference.get_attribute("value")
                startDateOfRelationship = self.driver.find_element_by_xpath("""//*[@id="ctl00_ContentPlaceHolder1_txtDPRRStartRel"]""")
                startDateOfRelationship = startDateOfRelationship.get_attribute("value")
                try:
                    from datetime import datetime
                    date_obj = datetime.strptime(startDateOfRelationship, '%Y-%m-%d')
                    startDateOfRelationship = date_obj.strftime('%d-%b-%Y')
                except:
                    pass
                endDateOfRelationship = self.driver.find_element_by_xpath("""//*[@id="ctl00_ContentPlaceHolder1_txtDPRREndRel"]""")
                endDateOfRelationship = endDateOfRelationship.get_attribute("value")
                try:
                    from datetime import datetime
                    date_obj = datetime.strptime(endDateOfRelationship, '%Y-%m-%d')
                    endDateOfRelationship = date_obj.strftime('%d-%b-%Y')
                except:
                    pass
                startDateAccountingPeriod = self.driver.find_element_by_xpath("""//*[@id="ctl00_ContentPlaceHolder1_txtDPRRStartAcc"]""")
                startDateAccountingPeriod = startDateAccountingPeriod.get_attribute("value")
                try:
                    from datetime import datetime
                    date_obj = datetime.strptime(startDateAccountingPeriod, '%Y-%m-%d')
                    startDateAccountingPeriod = date_obj.strftime('%d-%b-%Y')
                except:
                    pass
                endDateOfAccountingPeriod = self.driver.find_element_by_xpath("""//*[@id="ctl00_ContentPlaceHolder1_txtDPRREndAcc"]""")
                endDateOfAccountingPeriod = endDateOfAccountingPeriod.get_attribute("value")
                try:
                    from datetime import datetime
                    date_obj = datetime.strptime(endDateOfAccountingPeriod, '%Y-%m-%d')
                    endDateOfAccountingPeriod = date_obj.strftime('%d-%b-%Y')
                except:
                    pass
                startDateDocFilingPeriod = self.driver.find_element_by_xpath("""//*[@id="ctl00_ContentPlaceHolder1_txtDPRRStartDoc"]""")
                startDateDocFilingPeriod = startDateDocFilingPeriod.get_attribute("value")
                try:
                    from datetime import datetime
                    date_obj = datetime.strptime(startDateDocFilingPeriod, '%Y-%m-%d')
                    startDateDocFilingPeriod = date_obj.strftime('%d-%b-%Y')
                except:
                    pass
                endDateDocFilingPeriod = self.driver.find_element_by_xpath("""//*[@id="ctl00_ContentPlaceHolder1_txtDPRREndDoc"]""")
                endDateDocFilingPeriod = endDateDocFilingPeriod.get_attribute("value")
                try:
                    from datetime import datetime
                    date_obj = datetime.strptime(endDateDocFilingPeriod, '%Y-%m-%d')
                    endDateDocFilingPeriod = date_obj.strftime('%d-%b-%Y')
                except:
                    pass
                registrationStatus = self.driver.find_element_by_xpath("""//*[@id="ctl00_ContentPlaceHolder1_txtDP_leird_nRRRegistrationStatus"]""")
                registrationStatus = registrationStatus.get_attribute("value")
                initialRegistrationDate = self.driver.find_element_by_xpath("""//*[@id="ctl00_ContentPlaceHolder1_txtDP_leird_dRRInitialRegistrationDate"]""")
                initialRegistrationDate = initialRegistrationDate.get_attribute("value")
                try:
                    from datetime import datetime
                    date_obj = datetime.strptime(initialRegistrationDate, '%Y-%m-%d')
                    initialRegistrationDate = date_obj.strftime('%d-%b-%Y')
                except:
                    pass
                relationshipStatus = self.driver.find_element_by_xpath("""//*[@id="ctl00_ContentPlaceHolder1_txtDP_leird_cRRStatus"]""")
                relationshipStatus = relationshipStatus.get_attribute("value")
                lastUpdateDate = self.driver.find_element_by_xpath("""//*[@id="ctl00_ContentPlaceHolder1_txtDP_RRLastUpdatedDate"]""")
                lastUpdateDate = lastUpdateDate.get_attribute("value")
                try:
                    from datetime import datetime
                    date_obj = datetime.strptime(lastUpdateDate, '%Y-%m-%d')
                    lastUpdateDate = date_obj.strftime('%d-%b-%Y')
                except:
                    pass
                nextRenewalDate = self.driver.find_element_by_xpath("""//*[@id="ctl00_ContentPlaceHolder1_txtDP_RRNextRenewalDate"]""")
                nextRenewalDate = nextRenewalDate.get_attribute("value")
                try:
                    from datetime import datetime
                    date_obj = datetime.strptime(nextRenewalDate, '%Y-%m-%d')
                    nextRenewalDate = date_obj.strftime('%d-%b-%Y')
                except:
                    pass
                managingLou = self.driver.find_element_by_xpath("""//*[@id="ctl00_ContentPlaceHolder1_txtDP_ManagingLOU"]""")
                managingLou = managingLou.get_attribute("value")
                periodType = self.driver.find_element_by_xpath("""//*[@id="ctl00_ContentPlaceHolder1_txtDP_PeriodType"]""")
                periodType = periodType.get_attribute("value")
                validationSources = self.driver.find_element_by_xpath("""//*[@id="ctl00_ContentPlaceHolder1_txtDP_leird_nRRValidationSources"]""")
                validationSources = validationSources.get_attribute("value")
                relationshipQuantifiers = self.driver.find_element_by_xpath("""//*[@id="ctl00_ContentPlaceHolder1_txtDP_RelationshipQualifier"]""")
                relationshipQuantifiers = relationshipQuantifiers.get_attribute("value")
                relationshipQualifiersCategory = self.driver.find_element_by_xpath("""//*[@id="ctl00_ContentPlaceHolder1_txtDP_RelationshipQualifierCategory"]""")
                relationshipQualifiersCategory = relationshipQualifiersCategory.get_attribute("value")
                relationshipRecordType = self.driver.find_element_by_xpath("""//*[@id="templatemo_content"]/fieldset[2]/center/legend/b""")
                relationshipRecordType = relationshipRecordType.text
                relationshipRecordType = relationshipRecordType.replace("Details", "")
                leiCodeRelation = self.driver.find_element_by_xpath("""// *[ @ id = "ctl00_ContentPlaceHolder1_txtDPLeiCode"]""")
                leiCodeRelation = leiCodeRelation.get_attribute("value")
            except:
                pass

                #####################################################################################sdsd
            try:
                legalEntityName1 = self.driver.find_element_by_xpath(
                    """//*[@id="ctl00_ContentPlaceHolder1_txtUPLegalEntityName"]""")
                legalEntityName1 = legalEntityName1.get_attribute("value")
                try:
                    legalEntityNamech = legalEntityName1.replace(" ", "")
                    if legalEntityNamech.isalpha() == True:
                        legalEntityName1 = legalEntityName1
                    else:
                        legalEntityName1 = "Unspecified Output"
                except:
                    pass
                leiCodeRelation1 = self.driver.find_element_by_xpath(
                    """//*[@id="ctl00_ContentPlaceHolder1_txtUPLeiCode"]""")
                leiCodeRelation1 = leiCodeRelation1.get_attribute("value")
                relationshipType1 = self.driver.find_element_by_xpath("""//*[@id="ctl00_ContentPlaceHolder1_txtUPRRRelType"]""")
                relationshipType1 = relationshipType1.get_attribute("value")
                percentShareholding1 = self.driver.find_element_by_xpath("""//*[@id="ctl00_ContentPlaceHolder1_txtUPRRShare"]""")
                percentShareholding1 = percentShareholding1.get_attribute("value")
                accountingStandard1 = self.driver.find_element_by_xpath("""//*[@id="ctl00_ContentPlaceHolder1_txtUPRRAccStd"]""")
                accountingStandard1 = accountingStandard1.get_attribute("value")
                validationReference1 = self.driver.find_element_by_xpath(
                    """//*[@id="ctl00_ContentPlaceHolder1_txtUPRRValRef"]""")
                validationReference1 = validationReference1.get_attribute("value")
                startDateOfRelationship1 = self.driver.find_element_by_xpath(
                    """//*[@id="ctl00_ContentPlaceHolder1_txtUPRRStartRel"]""")
                startDateOfRelationship1 = startDateOfRelationship1.get_attribute("value")
                try:
                    from datetime import datetime
                    date_obj = datetime.strptime(startDateOfRelationship1, '%Y-%m-%d')
                    startDateOfRelationship1 = date_obj.strftime('%d-%b-%Y')
                except:
                    pass
                endDateOfRelationship1 = self.driver.find_element_by_xpath(
                    """//*[@id="ctl00_ContentPlaceHolder1_txtUPRREndRel"]""")
                endDateOfRelationship1 = endDateOfRelationship1.get_attribute("value")
                try:
                    from datetime import datetime
                    date_obj = datetime.strptime(endDateOfRelationship1, '%Y-%m-%d')
                    endDateOfRelationship1 = date_obj.strftime('%d-%b-%Y')
                except:
                    pass
                startDateAccountingPeriod1 = self.driver.find_element_by_xpath(
                    """//*[@id="ctl00_ContentPlaceHolder1_txtUPRRStartAcc"]""")
                startDateAccountingPeriod1 = startDateAccountingPeriod1.get_attribute("value")
                try:
                    from datetime import datetime
                    date_obj = datetime.strptime(startDateAccountingPeriod1, '%Y-%m-%d')
                    startDateAccountingPeriod1 = date_obj.strftime('%d-%b-%Y')
                except:
                    pass
                endDateOfAccountingPeriod1 = self.driver.find_element_by_xpath(
                    """//*[@id="ctl00_ContentPlaceHolder1_txtUPRREndRel"]""")
                endDateOfAccountingPeriod1 = endDateOfAccountingPeriod1.get_attribute("value")
                try:
                    from datetime import datetime
                    date_obj = datetime.strptime(endDateOfAccountingPeriod1, '%Y-%m-%d')
                    endDateOfAccountingPeriod1 = date_obj.strftime('%d-%b-%Y')
                except:
                    pass
                startDateDocFilingPeriod1 = self.driver.find_element_by_xpath(
                    """//*[@id="ctl00_ContentPlaceHolder1_txtUPRRStartDoc"]""")
                startDateDocFilingPeriod1 = startDateDocFilingPeriod1.get_attribute("value")
                try:
                    from datetime import datetime
                    date_obj = datetime.strptime(startDateDocFilingPeriod1, '%Y-%m-%d')
                    startDateDocFilingPeriod1 = date_obj.strftime('%d-%b-%Y')
                except:
                    pass
                endDateDocFilingPeriod1 = self.driver.find_element_by_xpath(
                    """//*[@id="ctl00_ContentPlaceHolder1_txtUPRREndDoc"]""")
                endDateDocFilingPeriod1 = endDateDocFilingPeriod1.get_attribute("value")
                try:
                    from datetime import datetime
                    date_obj = datetime.strptime(endDateDocFilingPeriod1, '%Y-%m-%d')
                    endDateDocFilingPeriod1 = date_obj.strftime('%d-%b-%Y')
                except:
                    pass
                registrationStatus1 = self.driver.find_element_by_xpath(
                    """//*[@id="ctl00_ContentPlaceHolder1_txtDP_leird_nRRRegistrationStatus"]""")
                registrationStatus1 = registrationStatus1.get_attribute("value")
                initialRegistrationDate1 = self.driver.find_element_by_xpath(
                    """//*[@id="ctl00_ContentPlaceHolder1_txtDP_leird_dRRInitialRegistrationDate"]""")
                initialRegistrationDate1 = initialRegistrationDate1.get_attribute("value")
                try:
                    from datetime import datetime
                    date_obj = datetime.strptime(initialRegistrationDate1, '%Y-%m-%d')
                    initialRegistrationDate1 = date_obj.strftime('%d-%b-%Y')
                except:
                    pass
                relationshipStatus1 = self.driver.find_element_by_xpath(
                    """//*[@id="ctl00_ContentPlaceHolder1_txtUP_leird_nRRRegistrationStatus"]""")
                relationshipStatus1 = relationshipStatus1.get_attribute("value")

                lastUpdateDate1 = self.driver.find_element_by_xpath(
                    """//*[@id="ctl00_ContentPlaceHolder1_txtUP_RRLastUpdatedDate"]""")
                lastUpdateDate1 = lastUpdateDate1.get_attribute("value")
                try:
                    from datetime import datetime
                    date_obj = datetime.strptime(lastUpdateDate1, '%Y-%m-%d')
                    lastUpdateDate1 = date_obj.strftime('%d-%b-%Y')
                except:
                    pass
                nextRenewalDate1 = self.driver.find_element_by_xpath(
                    """//*[@id="ctl00_ContentPlaceHolder1_txtUP_RRNextRenewalDate"]""")
                nextRenewalDate1 = nextRenewalDate1.get_attribute("value")
                try:
                    from datetime import datetime
                    date_obj = datetime.strptime(nextRenewalDate1, '%Y-%m-%d')
                    nextRenewalDate1 = date_obj.strftime('%d-%b-%Y')
                except:
                    pass
                managingLou1 = self.driver.find_element_by_xpath("""//*[@id="ctl00_ContentPlaceHolder1_txtUP_ManagingLOU"]""")
                managingLou1 = managingLou1.get_attribute("value")
                try:
                    periodType1 = self.driver.find_element_by_xpath("""//*[@id="ctl00_ContentPlaceHolder1_txtUP_PeriodType"]""")
                    periodType1 = periodType.get_attribute("value")
                except:
                    periodType1 = ""
                    pass
                validationSources1 = self.driver.find_element_by_xpath(
                    """//*[@id="ctl00_ContentPlaceHolder1_txtUP_leird_nRRValidationSources"]""")
                validationSources1 = validationSources1.get_attribute("value")
                relationshipQuantifiers1 = self.driver.find_element_by_xpath(
                    """//*[@id="ctl00_ContentPlaceHolder1_txtUP_RelationshipQualifier"]""")
                relationshipQuantifiers1 = relationshipQuantifiers1.get_attribute("value")
                relationshipQualifiersCategory1 = self.driver.find_element_by_xpath(
                    """//*[@id="ctl00_ContentPlaceHolder1_txtUP_RelationshipQualifierCategory"]""")
                relationshipQualifiersCategory1 = relationshipQualifiersCategory1.get_attribute("value")
                relationshipRecordType1 = self.driver.find_element_by_xpath(
                    """//*[@id="templatemo_content"]/fieldset[3]/center/legend/b""")
                relationshipRecordType1 = relationshipRecordType1.text
                relationshipRecordType1 = relationshipRecordType1.replace("Details","")
            except:
                pass
            try:
                self.driver.find_element_by_xpath("""// *[ @ id = "ctl00_ContentPlaceHolder1_btnBack"]""").click()
            except Exception as e:
                print(e)

            #self.driver.switch_to.window(window_after)
            self.driver.find_element_by_xpath("""// *[ @ id = "ctl00_ContentPlaceHolder1_btnlinkExceptionData"]""").click()
            try:
               # window_after = self.driver.window_handles[1]
               # self.driver.switch_to.window(window_after)

                exceptionReason = self.driver.find_element_by_xpath(
                    """//*[@id="ctl00_ContentPlaceHolder1_txtDPExcep"]""")
                exceptionReason = exceptionReason.get_attribute("value")
                exceptionReason1 = self.driver.find_element_by_xpath(
                    """//*[@id="ctl00_ContentPlaceHolder1_txtUPExcep"]""")
                exceptionReason1 = exceptionReason1.get_attribute("value")
                exceptionTypeFlag = self.driver.find_element_by_xpath(
                    """//*[@id="templatemo_content"]/fieldset[2]/center/legend/b""")
                exceptionTypeFlag = exceptionTypeFlag.text
                exceptionTypeFlag = exceptionTypeFlag.replace("Details","")
                exceptionTypeFlag1 = self.driver.find_element_by_xpath(
                    """//*[@id="templatemo_content"]/fieldset[3]/center/legend/b""")
                exceptionTypeFlag1 = exceptionTypeFlag1.text
                exceptionTypeFlag1 = exceptionTypeFlag1.replace("Details", "")
            except:
                pass




            message = "Successfully Completed."
            code = "SRC001"
            dic = {}
            dic["leiNumber"] = leiNumber
            dic["legalName"] = legalName
            dic["registrationAuthorityName"] = registrationAuthorityName
            dic["registrationAuthorityId"] = registrationAuthorityId
            dic["jurisdiction"] = jurisdiction
            dic["legalForm"] = legalForm
            dic["leiRegistrationDate"] = leiRegistrationDate
            dic["leiRegLastUpdateDate"] = leiRegLastUpdateDate
            dic["entityStatus"] = entityStatus
            dic["entityExpirationDate"] = entityExpirationDate
            dic["leiNextRenewalDate"] = leiNextRenewalDate
            dic["entityExpirationReason"] = entityExpirationReason
            dic["leiRegistrationStatus"] = leiRegistrationStatus
            dic["successorLei"] = successorLei
            dic["louId"] = louId
            dic["leiValidationSource"] = leiValidationSource
            try:
                y = {}
                y["exceptionReason"] = exceptionReason
                y["exceptionTypeFlag"] = exceptionTypeFlag
            except:
                y = {}
                pass
            try:
                r = {}
                r["exceptionReason"] = exceptionReason1
                r["exceptionTypeFlag"] = exceptionTypeFlag1
            except:
                r = {}
                pass
            b = [y,r]
            dic["leiExceptionDetails"] = [d for d in b if any(d.values())]

            d = {}
            d["firstAddressLine"] = registeredFirstAddressLine
            d["additionalAddressLine1"] = additionalAddressLine1
            d["additionalAddressLine2"] = additionalAddressLine2
            d["additionalAddressLine3"] = additionalAddressLine3
            d["country"] = country
            d["region"] = region
            d["city"] = city
            d["postalPincode"] = postalPincode
            d["addressType"] = addressType1
            e = {}
            e["firstAddressLine"] = registeredFirstAddressLine1
            e["additionalAddressLine1"] = additionalAddressLine4
            e["additionalAddressLine2"] = additionalAddressLine5
            e["additionalAddressLine3"] = additionalAddressLine6
            e["country"] = country1
            e["region"] = region1
            e["city"] = city1
            e["postalPincode"] = postalPincode1
            e["addressType"] = addressType2
            dic["leiAddress"] = [d, e]
            try:
                l = {}
                l["legalEntityName"] = legalEntityName
                l["relationshipType"] = relationshipType
                l["percentShareholding"] = percentShareholding
                l["accountingStandard"] = accountingStandard
                l["validationReference"] = validationReference
                l["validationDocuments"] = ""
                l["startDateOfRelationship"] = startDateOfRelationship
                l["endDateOfRelationship"] = endDateOfRelationship
                l["startDateAccountingPeriod"] = startDateAccountingPeriod
                l["endDateOfAccountingPeriod"] = endDateOfAccountingPeriod
                l["startDateDocFilingPeriod"] = startDateDocFilingPeriod
                l["endDateDocFilingPeriod"] = endDateDocFilingPeriod
                l["registrationStatus"] = registrationStatus
                l["initialRegistrationDate"] = initialRegistrationDate
                l["relationshipStatus"] = relationshipStatus
                l["lastUpdateDate"] = lastUpdateDate
                l["nextRenewalDate"] = nextRenewalDate
                l["managingLou"] = managingLou
                l["periodType"] = periodType
                l["validationSources"] = validationSources
                l["relationshipQuantifiers"] = relationshipQuantifiers
                l["relationshipQualifiersCategory"] = relationshipQualifiersCategory
                l["relationshipRecordType"] = relationshipRecordType
                l["leiCodeRelation"] = leiCodeRelation
            except:
                l = {}
            try:
                f = {}
                f["legalEntityName"] = legalEntityName1
                f["relationshipType"] = relationshipType1
                f["percentShareholding"] = percentShareholding1
                f["accountingStandard"] = accountingStandard1
                f["validationReference"] = validationReference1
                f["validationDocuments"] = ""
                f["startDateOfRelationship"] = startDateOfRelationship1
                f["endDateOfRelationship"] = endDateOfRelationship1
                f["startDateAccountingPeriod"] = startDateAccountingPeriod1
                f["endDateOfAccountingPeriod"] = endDateOfAccountingPeriod1
                f["startDateDocFilingPeriod"] = startDateDocFilingPeriod1
                f["endDateDocFilingPeriod"] = endDateDocFilingPeriod1
                f["registrationStatus"] = registrationStatus1
                f["initialRegistrationDate"] = initialRegistrationDate1
                f["relationshipStatus"] = relationshipStatus1
                f["lastUpdateDate"] = lastUpdateDate1
                f["nextRenewalDate"] = nextRenewalDate1
                f["managingLou"] = managingLou1
                f["periodType"] = periodType1
                f["validationSources"] = validationSources1
                f["relationshipQuantifiers"] = relationshipQuantifiers1
                f["relationshipQualifiersCategory"] = relationshipQualifiersCategory1
                f["relationshipRecordType"] = relationshipRecordType1
                f["leiCodeRelation"] = leiCodeRelation1
            except:
                f = {}
            ffj = [l,f]
            dic["leiRelationshipRecord"] = [d for d in ffj if any(d.values())]


            dic = {"data": dic, "responseCode": code, "responseMessage": message}
            self.makeDriverDirs()
            self.logStatus("info", "completed scraping")
            return dic

    def LEI_response(self,legalEntityIdentifierNumber):

        dic = {}
        try:
            self.logStatus("info", "Opening webpage")
            self.logStatus("info", "captcha1")
            dic = self.generate_LEI(legalEntityIdentifierNumber)
        except Exception as e:
            print(e)

            self.logStatus("critical", "Captcha error")
            try:
                self.logStatus("info", "Opening webpage")
                self.logStatus("info", "captcha2")
                dic = self.generate_LEI(legalEntityIdentifierNumber)
            except Exception as e:
                print(e)

                self.logStatus("critical", "Captcha error")
                try:
                    self.logStatus("info", "Opening webpage")
                    self.logStatus("info", "captcha3")
                    dic = self.generate_LEI(legalEntityIdentifierNumber)
                except Exception as e:
                    print(e)

                    self.logStatus("critical", "Captcha error")
                    try:
                        self.logStatus("info", "Opening webpage")
                        self.logStatus("info", "captcha4")
                        dic = self.generate_LEI(legalEntityIdentifierNumber)
                    except Exception as e:
                        print(e)

                        self.logStatus("critical", "could not break captcha")
                        dic = {}
                        message = "Unable To Process. Please Reach Out To Support."
                        code = "EUP007"

                        dic = {"data": "null", "responseCode": code, "responseMessage": message}
                        self.logStatus("info", "Contact support")
                        return dic

        return dic


#sd






























#if __name__ == '__main__':

 #   v = LEI(refid="testing2", env = 'prod')
  #  data = v.generate_LEI(legalEntityIdentifierNumber = "335800VBGABGY2MZPN36")
   # print(data)