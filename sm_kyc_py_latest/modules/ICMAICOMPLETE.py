import json
import os
import time
import uuid
from pprint import pprint
from selenium.webdriver.common.action_chains import ActionChains
import boto3
from botocore.exceptions import ClientError
from datetime import date




from modules.db import DB
from modules.utils import GcpOcr
#from webdriver_manager.chrome import ChromeDriverManager



class ICMAI:

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
                                 'ICMAI_COMPLETE', self.env, screenshot)
        print(f"{level}: {message}, screenshot: {screenshot}")

    def generate_icmai(self,licenseNumber):

        from selenium import webdriver

        from selenium.webdriver.common.action_chains import ActionChains
        #from webdriver_manager.chrome import ChromeDriverManager
        from selenium.webdriver.chrome.options import Options

        chrome_options = Options()
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--disable-extension")
        chrome_options.add_argument("no-sandbox")
        chrome_options.add_argument("--headless")
        chrome_options.headless = True

        self.driver = webdriver.Chrome('/usr/local/bin/chromedriver', options=chrome_options)
        start_url = "https://eicmai.in/External/Home.aspx"
        try:
            self.logStatus("info", "Opening website")
            self.driver.get(start_url)
            r = 1
            self.makeDriverDirs()
            self.logStatus("info", "getting webpage", self.takeScreenshot())
            try:
                time.sleep(1)
                self.driver.find_element_by_xpath("""//*[@id="form1"]/table/tbody/tr[2]/td/div/ul/li[6]/a""")
            except:
                r =2
        except Exception as e:
            r = 2

        if r == 2:
            dic = {}
            message = "Information Source is Not Working"
            code = "EIS042"

            dic = {"data": "null", "responseCode": code, "responseMessage": message}
            self.logStatus("info", "Contact support")
            return dic

        if r == 1:
            self.makeDriverDirs()
            self.logStatus("info", "Starting Scrapping",self.takeScreenshot())
            time.sleep(1)
            action = ActionChains(self.driver)
            parent_level_menu = self.driver.find_element_by_xpath("""//*[@id="form1"]/table/tbody/tr[2]/td/div/ul/li[6]/a""")
            action.move_to_element(parent_level_menu).perform()
            child_level_menu = self.driver.find_element_by_xpath("""//*[@id="form1"]/table/tbody/tr[2]/td/div/ul/li[6]/ul/li[4]/a""")
            action.move_to_element(child_level_menu).perform()
            child_level_menu.click()
            self.driver.find_element_by_xpath("""// *[ @ id = "ContentPlaceHolder1_TextBox_Value"]""").click()
            self.driver.find_element_by_xpath("""// *[ @ id = "ContentPlaceHolder1_TextBox_Value"]""").send_keys(licenseNumber)
            self.driver.find_element_by_xpath("""//*[@id="ContentPlaceHolder1_ButtonSearch"]""").click()
            time.sleep(2)
            serialNumber = self.driver.find_element_by_xpath("""// *[ @ id = "ContentPlaceHolder1_GRVCopMasterDet"] / tbody / tr[2] / td[1]""")
            serialNumber = serialNumber.text
            memberNumber67 = self.driver.find_element_by_xpath("""/html/body/form/table/tbody/tr[3]/td/div/div/table/tbody/tr[5]/td/div/table/tbody/tr[1]/td/div/table/tbody/tr[2]/td[2]""")
            memberNumber67 = memberNumber67.text
            aquali = self.driver.find_element_by_xpath("""//*[@id="ContentPlaceHolder1_GRVCopMasterDet"]/tbody/tr[2]/td[5]""")
            aquali = aquali.text
            category = self.driver.find_element_by_xpath("""//*[@id="ContentPlaceHolder1_GRVCopMasterDet"]/tbody/tr[2]/td[4]""")
            category = category.text
            memberName900 = self.driver.find_element_by_xpath("""//*[@id="ContentPlaceHolder1_GRVCopMasterDet"]/tbody/tr[2]/td[3]""")
            memberName900 = memberName900.text
            try:
                validDate = self.driver.find_element_by_xpath("""//*[@id="ContentPlaceHolder1_GRVCopMasterDet"]/tbody/tr[2]/td[6]""")
                validDate = validDate.text
                from datetime import datetime
                date_obj = datetime.strptime(validDate, '%d/%m/%Y')
                validDate = date_obj.strftime('%d-%b-%Y')
            except:
                validDate = ''
                pass
            address1 = self.driver.find_element_by_xpath("""//*[@id="ContentPlaceHolder1_GRVCopMasterDet"]/tbody/tr[2]/td[7]""")
            address1 = address1.text
            address2 = self.driver.find_element_by_xpath("""//*[@id="ContentPlaceHolder1_GRVCopMasterDet"]/tbody/tr[2]/td[8]""")
            address2 = address2.text
            address3 = self.driver.find_element_by_xpath("""//*[@id="ContentPlaceHolder1_GRVCopMasterDet"]/tbody/tr[2]/td[9]""")
            address3 = address3.text
            address4 = self.driver.find_element_by_xpath("""//*[@id="ContentPlaceHolder1_GRVCopMasterDet"]/tbody/tr[2]/td[10]""")
            address4 = address4.text
            address = address1 +' '+ address2 +' '+ address3 +' '+ address4
            address = address.replace('"','')
            phone = self.driver.find_element_by_xpath("""// *[ @ id = "ContentPlaceHolder1_GRVCopMasterDet"] / tbody / tr[2] / td[11]""")
            phone = phone.text
            email = self.driver.find_element_by_xpath("""//*[@id="ContentPlaceHolder1_GRVCopMasterDet"]/tbody/tr[2]/td[12]""")
            email = email.text
            self.driver.find_element_by_xpath("""// *[ @ id = "ContentPlaceHolder1_GRVCopMasterDet"] / tbody / tr[2] / td[13] / a / img""").click()

            magazinesRadioBtn = self.driver.find_element_by_xpath("""//*[@id="ContentPlaceHolder1_Radio_FullTime"]""")

            if (magazinesRadioBtn.is_selected()):
                print('selected')
                certificateOfPracticeAs = "Full Time"
            else:
                certificateOfPracticeAs = "Part Time"
                print("not selected")

            indexNumber = self.driver.find_element_by_xpath("""//*[@id="ContentPlaceHolder1_TextBox_IndexNo"]""")
            indexNumber = indexNumber.get_attribute('value')
            try:
                serialNumber1 = self.driver.find_element_by_xpath("""// *[ @ id = "ContentPlaceHolder1_GRVOfficeDet"] / tbody / tr[2] / td[1]""")
                serialNumber1 = serialNumber1.text
            except:
                pass
            try:
                firmNumber71 = self.driver.find_element_by_xpath("""//*[@id="ContentPlaceHolder1_GRVOfficeDet"]/tbody/tr[2]/td[2]""")
                firmNumber71 = firmNumber71.text
            except:
                pass

            try:
                firmName = self.driver.find_element_by_xpath("""// *[ @ id = "ContentPlaceHolder1_GRVOfficeDet"] / tbody / tr[2] / td[3]""")
                firmName = firmName.text
            except:
                pass
            try:
                firmType = self.driver.find_element_by_xpath("""// *[ @ id = "ContentPlaceHolder1_GRVOfficeDet"] / tbody / tr[2] / td[4]""")
                firmType = firmType.text
            except:
                pass

            try:
                constitutionDate = self.driver.find_element_by_xpath("""// *[ @ id = "ContentPlaceHolder1_GRVOfficeDet_Label_ApprovalDate_0"]""")
                constitutionDate = constitutionDate.text
                from datetime import datetime
                date_obj = datetime.strptime(constitutionDate, '%d/%m/%Y')
                constitutionDate = date_obj.strftime('%d-%b-%Y')
            except:
                pass

           # try:
            #    if len(constitutionDate)<10:
             #       constitutionDate = today.strftime('%d-%b-%Y')
            #except:
             #   pass

            try:
                deedDate = self.driver.find_element_by_xpath("""// *[ @ id = "ContentPlaceHolder1_GRVOfficeDet_Label_DeedDt_0"]""")
                deedDate = deedDate.text
                from datetime import datetime
                date_obj = datetime.strptime(deedDate, '%d/%m/%Y')
                deedDate = date_obj.strftime('%d-%b-%Y')
            except:
                pass
            try:
                region = self.driver.find_element_by_xpath("""//*[@id="ContentPlaceHolder1_GRVOfficeDet"]/tbody/tr[2]/td[7]""")
                region = region.text
            except:
                pass
            try:
                country = self.driver.find_element_by_xpath("""// *[ @ id = "ContentPlaceHolder1_GRVOfficeDet"] / tbody / tr[2] / td[8]""")
                country = country.text
            except:
                pass
            try:
                state = self.driver.find_element_by_xpath("""// *[ @ id = "ContentPlaceHolder1_GRVOfficeDet"] / tbody / tr[2] / td[9]""")
                state = state.text
            except:
                pass
            # new row now
            try:
                serialNumber2 = self.driver.find_element_by_xpath("""//*[@id="ContentPlaceHolder1_GRVOfficeDet"]/tbody/tr[3]/td[1]""")
                serialNumber2 = serialNumber2.text
            except:
                pass
            try:
                firmNumber72 = self.driver.find_element_by_xpath("""//*[@id="ContentPlaceHolder1_GRVOfficeDet"]/tbody/tr[3]/td[2]""")
                firmNumber72 = firmNumber72.text
            except:
                pass

            try:
                firmName1 = self.driver.find_element_by_xpath("""// *[ @ id = "ContentPlaceHolder1_GRVOfficeDet"] / tbody / tr[3] / td[3]""")
                firmName1 = firmName1.text
            except:
                pass
            try:
                firmType1 = self.driver.find_element_by_xpath("""// *[ @ id = "ContentPlaceHolder1_GRVOfficeDet"] / tbody / tr[3] / td[4]""")
                firmType1 = firmType1.text
            except:
                pass

            try:
                constitutionDate1 = self.driver.find_element_by_xpath("""// *[ @ id = "ContentPlaceHolder1_GRVOfficeDet_Label_ApprovalDate_1"]""")
                constitutionDate1 = constitutionDate1.text
                from datetime import datetime
                date_obj = datetime.strptime(constitutionDate1, '%d/%m/%Y')
                constitutionDate1 = date_obj.strftime('%d-%b-%Y')
            except:
                pass
          #  try:
           #     if len(constitutionDate1)<10:
             #       constitutionDate1 = today.strftime('%d-%b-%Y')
           # except:
            #    pass
            try:
                deedDate1 = self.driver.find_element_by_xpath("""// *[ @ id = "ContentPlaceHolder1_GRVOfficeDet_Label_DeedDt_1"]""")
                deedDate1 = deedDate1.text
                from datetime import datetime
                date_obj = datetime.strptime(deedDate1, '%d/%m/%Y')
                deedDate1 = date_obj.strftime('%d-%b-%Y')
            except:
                pass
            try:
                region1 = self.driver.find_element_by_xpath("""//*[@id="ContentPlaceHolder1_GRVOfficeDet"]/tbody/tr[3]/td[7]""")
                region1 = region1.text
            except:
                pass
            try:
                country1 = self.driver.find_element_by_xpath("""// *[ @ id = "ContentPlaceHolder1_GRVOfficeDet"] / tbody / tr[3] / td[8]""")
                country1 = country1.text
            except:
                pass
            try:
                state1 = self.driver.find_element_by_xpath("""// *[ @ id = "ContentPlaceHolder1_GRVOfficeDet"] / tbody / tr[3] / td[9]""")
                state1 = state1.text
            except:
                pass
            try:
                serialNumber3 = self.driver.find_element_by_xpath("""//*[@id="ContentPlaceHolder1_GRVOfficeDet"]/tbody/tr[4]/td[1]""")
                serialNumber3 = serialNumber3.text
            except:
                pass
            try:
                firmNumber73 = self.driver.find_element_by_xpath("""//*[@id="ContentPlaceHolder1_GRVOfficeDet"]/tbody/tr[4]/td[2]""")
                firmNumber73 = firmNumber73.text
            except:
                pass

            try:
                firmName2 = self.driver.find_element_by_xpath("""// *[ @ id = "ContentPlaceHolder1_GRVOfficeDet"] / tbody / tr[4] / td[3]""")
                firmName2 = firmName2.text
            except:
                pass
            try:
                firmType2 = self.driver.find_element_by_xpath("""// *[ @ id = "ContentPlaceHolder1_GRVOfficeDet"] / tbody / tr[4] / td[4]""")
                firmType2 = firmType2.text
            except:
                pass

            try:
                constitutionDate2 = self.driver.find_element_by_xpath("""// *[ @ id = "ContentPlaceHolder1_GRVOfficeDet_Label_ApprovalDate_2"]""")
                constitutionDate2 = constitutionDate2.text
                from datetime import datetime
                date_obj = datetime.strptime(constitutionDate2, '%d/%m/%Y')
                constitutionDate2 = date_obj.strftime('%d-%b-%Y')
            except:
                pass
           # try:
            #    if len(constitutionDate2)<10:
             #       constitutionDate2 = today.strftime('%d-%b-%Y')
            #except:
             #   pass

            try:
                deedDate2 = self.driver.find_element_by_xpath("""// *[ @ id = "ContentPlaceHolder1_GRVOfficeDet_Label_DeedDt_2"]""")
                deedDate2 = deedDate2.text
                from datetime import datetime
                date_obj = datetime.strptime(deedDate2, '%d/%m/%Y')
                deedDate2 = date_obj.strftime('%d-%b-%Y')
            except:
                pass
            try:
                region2 = self.driver.find_element_by_xpath("""//*[@id="ContentPlaceHolder1_GRVOfficeDet"]/tbody/tr[4]/td[7]""")
                region2 = region2.text
            except:
                pass
            try:
                country2 = self.driver.find_element_by_xpath("""// *[ @ id = "ContentPlaceHolder1_GRVOfficeDet"] / tbody / tr[4] / td[8]""")
                country2 = country2.text
            except:
                pass
            try:
                state2 = self.driver.find_element_by_xpath("""// *[ @ id = "ContentPlaceHolder1_GRVOfficeDet"] / tbody / tr[4] / td[9]""")
                state2 = state2.text
            except:
                pass


            try:
                self.driver.find_element_by_xpath("""// *[ @ id = "ContentPlaceHolder1_GRVOfficeDet"] / tbody / tr[2] / td[10] / a / img""").click()
                time.sleep(2)
            except:
                pass
            #try:
             #   firmNumber = self.driver.find_element_by_xpath("""//*[@id="ContentPlaceHolder1_TextBox_firmNo"]""")
            #    firmNumber = firmNumber.text
            #except:
            #    pass



            try:
                reonstitutionDate = self.driver.find_element_by_xpath("""// *[ @ id = "ContentPlaceHolder1_TextBox_reConDate"]""")
                reonstitutionDate = reonstitutionDate.get_attribute("value")
                from datetime import datetime
                date_obj = datetime.strptime(reonstitutionDate, '%d/%m/%Y')
                reonstitutionDate = date_obj.strftime('%d-%b-%Y')
            except:
                pass


            try:
                lDate59 = self.driver.find_element_by_xpath("""//*[@id="ContentPlaceHolder1_TextBox_ldt"]""")
                lDate59 = lDate59.get_attribute("value")
                from datetime import datetime
                date_obj = datetime.strptime(lDate59, '%d/%m/%Y')
                lDate59 = date_obj.strftime('%d-%b-%Y')
            except:
                pass

            try:
                address5 = self.driver.find_element_by_xpath("""//*[@id="ContentPlaceHolder1_TextBox_add1"]""")
                address5 = address5.get_attribute("value")
                address6 = self.driver.find_element_by_xpath("""//*[@id="ContentPlaceHolder1_TextBox_add2"]""")
                address6 = address6.get_attribute("value")
                address7 = self.driver.find_element_by_xpath("""//*[@id="ContentPlaceHolder1_TextBox_add3"]""")
                address7 = address7.get_attribute("value")
                try:
                    addresssss = self.driver.find_element_by_xpath("""//*[@id="ContentPlaceHolder1_TextBox_add4"]""")
                    addresssss = addresssss.get_attribute("value")
                except:
                    addresssss = ""
                    pass
                address8 = address5 + ' '+address6+ ' '+ address7 + ' ' + addresssss
                address8 = address8.replace('"', '')


            except:
                pass
            try:
                telephoneMobileNumber = self.driver.find_element_by_xpath("""//*[@id="ContentPlaceHolder1_TextBox_phone"]""")
                telephoneMobileNumber = telephoneMobileNumber.get_attribute("value")
            except:
                pass
            try:
                mobileNumberh = self.driver.find_element_by_xpath("""// *[ @ id = "ContentPlaceHolder1_TextBox_mobile"]""")
                mobileNumberh = mobileNumberh.get_attribute('value')
            except:
                pass
            try:
                emailIdOfficial = self.driver.find_element_by_xpath("""//*[@id="ContentPlaceHolder1_TextBox_email"]""")
                emailIdOfficial = emailIdOfficial.get_attribute("value")
            except:
                pass



            try:
                from selenium.webdriver.support.select import Select
                select = Select(self.driver.find_element_by_xpath("""// *[ @ id = "ContentPlaceHolder1_ddlState"]"""))
                selected_option = select.first_selected_option
                state3 =  selected_option.text
                select = Select(self.driver.find_element_by_xpath("""//*[@id="ContentPlaceHolder1_ddlCity"]"""))
                selected_option1 = select.first_selected_option
                city = selected_option1.text
            except:
                pass
            try:
                district = self.driver.find_element_by_xpath("""//*[@id="ContentPlaceHolder1_TextBox_dist"]""")
                district = district.get_attribute("value")
            except:
                pass
            try:
                pincode111 = self.driver.find_element_by_xpath("""//*[@id="ContentPlaceHolder1_TextBox_pin"]""")
                pincode111 = pincode111.get_attribute("value")
            except:
                pass



            ##Address of the branch




            try:
                branchIncharge = self.driver.find_element_by_xpath("""// *[ @ id = "ContentPlaceHolder1_GVWBranchDetails_lblmemberInChargeOfHo_0"]""")
                branchIncharge = branchIncharge.text
            except:
                pass
            try:
                address99 = self.driver.find_element_by_xpath("""//*[@id="ContentPlaceHolder1_GVWBranchDetails_lblb1Add1_0"]""")
                address99 = address99.text
                address98 = self.driver.find_element_by_xpath("""// *[ @ id = "ContentPlaceHolder1_GVWBranchDetails_lblb1Add2_0"]""")
                address98 = address98.text
                address97 = self.driver.find_element_by_xpath("""//*[@id="ContentPlaceHolder1_GVWBranchDetails_lblb1Add3_0"]""")
                address97 = address97.text
                address96 = address99 + " " +address98 + " " + address97
                address96 = address96.replace('"', '')
            except:
                pass
            try:
                city1 = self.driver.find_element_by_xpath("""//*[@id="ContentPlaceHolder1_GVWBranchDetails_lblb1City_0"]""")
                city1 = city1.text
            except:
                pass
            try:
                district1 = self.driver.find_element_by_xpath("""//*[@id="ContentPlaceHolder1_GVWBranchDetails_lblb1Dist_0"]""")
                district1 = district1.text
            except:
                pass
            try:
                state4 = self.driver.find_element_by_xpath("""// *[ @ id = "ContentPlaceHolder1_GVWBranchDetails_lblb1State_0"]""")
                state4 = state4.text
            except:
                pass

            try:
                pin = self.driver.find_element_by_xpath("""// *[ @ id = "ContentPlaceHolder1_GVWBranchDetails_lblb1Pin_0"]""")
                pin = pin.text
            except:
                pass
            try:
                phoneNumber = self.driver.find_element_by_xpath("""//*[@id="ContentPlaceHolder1_GVWBranchDetails_lblb1Phone_0"]""")
                phoneNumber = phoneNumber.text
            except:
                pass
            try:
                mobileNumber = self.driver.find_element_by_xpath("""//*[@id="ContentPlaceHolder1_GVWBranchDetails_lblb1Mobile_0"]""")
                mobileNumber = mobileNumber.text
            except:
                pass
            try:
                email1 = self.driver.find_element_by_xpath("""//*[@id="ContentPlaceHolder1_GVWBranchDetails_lblb1Email_0"]""")
                email1 = email1.text
            except:
                pass

            try:
                branchIncharge1 = self.driver.find_element_by_xpath("""//*[@id="ContentPlaceHolder1_GVWBranchDetails_lblmemberInChargeOfHo_1"]""")
                branchIncharge1 = branchIncharge1.text
            except:
                pass
            try:
                address111 = self.driver.find_element_by_xpath("""//*[@id="ContentPlaceHolder1_GVWBranchDetails_lblb1Add1_1"]""")
                address111 = address111.text
                address112 = self.driver.find_element_by_xpath("""// *[ @ id = "ContentPlaceHolder1_GVWBranchDetails_lblb1Add2_1"]""")
                address112 = address112.text
                address113 = self.driver.find_element_by_xpath("""//*[@id="ContentPlaceHolder1_GVWBranchDetails_lblb1Add3_1"]""")
                address113 = address113.text
                address114 = address111 + " " +address112 + " " + address113
                address114 = address114.replace('"', '')
            except:
                pass
            try:
                city2 = self.driver.find_element_by_xpath("""//*[@id="ContentPlaceHolder1_GVWBranchDetails_lblb1City_1"]""")
                city2 = city2.text
            except:
                pass
            try:
                district2 = self.driver.find_element_by_xpath("""//*[@id="ContentPlaceHolder1_GVWBranchDetails_lblb1Dist_1"]""")
                district2 = district2.text
            except:
                pass
            try:
                state5 = self.driver.find_element_by_xpath("""// *[ @ id = "ContentPlaceHolder1_GVWBranchDetails_lblb1State_1"]""")
                state5 = state5.text
            except:
                pass

            try:
                pin1 = self.driver.find_element_by_xpath("""// *[ @ id = "ContentPlaceHolder1_GVWBranchDetails_lblb1Pin_1"]""")
                pin1 = pin1.text
            except:
                pass
            try:
                phoneNumber1 = self.driver.find_element_by_xpath("""//*[@id="ContentPlaceHolder1_GVWBranchDetails_lblb1Phone_1"]""")
                phoneNumber1 = phoneNumber1.text
            except:
                pass
            try:
                mobileNumber1 = self.driver.find_element_by_xpath("""//*[@id="ContentPlaceHolder1_GVWBranchDetails_lblb1Mobile_1"]""")
                mobileNumber1 = mobileNumber1.text
            except:
                pass
            try:
                email2 = self.driver.find_element_by_xpath("""//*[@id="ContentPlaceHolder1_GVWBranchDetails_lblb1Email_1"]""")
                email2 = email2.text
            except:
                pass

            try:
                branchIncharge2 = self.driver.find_element_by_xpath("""//*[@id="ContentPlaceHolder1_GVWBranchDetails_lblmemberInChargeOfHo_2"]""")
                branchIncharge2 = branchIncharge2.text
            except:
                pass
            try:
                address101 = self.driver.find_element_by_xpath(
                    """//*[@id="ContentPlaceHolder1_GVWBranchDetails_lblb1Add1_2"]""")
                address101 = address101.text
                address102 = self.driver.find_element_by_xpath(
                    """// *[ @ id = "ContentPlaceHolder1_GVWBranchDetails_lblb1Add2_2"]""")
                address102 = address102.text
                address103 = self.driver.find_element_by_xpath(
                    """//*[@id="ContentPlaceHolder1_GVWBranchDetails_lblb1Add3_2"]""")
                address103 = address103.text

                address104 = address101 + " " + address102 + " " + address103
                address104 = address104.replace('"', '')
            except:
                pass
            try:
                city3 = self.driver.find_element_by_xpath(
                    """//*[@id="ContentPlaceHolder1_GVWBranchDetails_lblb1City_2"]""")
                city3 = city3.text
            except:
                pass
            try:
                district3 = self.driver.find_element_by_xpath(
                    """//*[@id="ContentPlaceHolder1_GVWBranchDetails_lblb1Dist_2"]""")
                district3 = district3.text
            except:
                pass
            try:
                state6 = self.driver.find_element_by_xpath(
                    """// *[ @ id = "ContentPlaceHolder1_GVWBranchDetails_lblb1State_2"]""")
                state6 = state6.text
            except:
                pass

            try:
                pin2 = self.driver.find_element_by_xpath(
                    """// *[ @ id = "ContentPlaceHolder1_GVWBranchDetails_lblb1Pin_2"]""")
                pin2 = pin2.text
            except:
                pass
            try:
                phoneNumber2 = self.driver.find_element_by_xpath(
                    """//*[@id="ContentPlaceHolder1_GVWBranchDetails_lblb1Phone_2"]""")
                phoneNumber2 = phoneNumber2.text
            except:
                pass
            try:
                mobileNumber2 = self.driver.find_element_by_xpath(
                    """//*[@id="ContentPlaceHolder1_GVWBranchDetails_lblb1Mobile_2"]""")
                mobileNumber2 = mobileNumber2.text
            except:
                pass
            try:
                email3 = self.driver.find_element_by_xpath(
                    """//*[@id="ContentPlaceHolder1_GVWBranchDetails_lblb1Email_2"]""")
                email3 = email3.text
            except:
                pass

            try:
                branchIncharge3 = self.driver.find_element_by_xpath(
                    """//*[@id="ContentPlaceHolder1_GVWBranchDetails_lblmemberInChargeOfHo_3"]""")
                branchIncharge3 = branchIncharge3.text
            except:
                pass
            try:
                address211 = self.driver.find_element_by_xpath(
                    """//*[@id="ContentPlaceHolder1_GVWBranchDetails_lblb1Add1_3"]""")
                address211 = address211.text
                address212 = self.driver.find_element_by_xpath(
                    """// *[ @ id = "ContentPlaceHolder1_GVWBranchDetails_lblb1Add2_3"]""")
                address212 = address212.text
                address213 = self.driver.find_element_by_xpath(
                    """//*[@id="ContentPlaceHolder1_GVWBranchDetails_lblb1Add3_3"]""")
                address213 = address213.text

                address214 = address211 + " " + address212 + " " + address213
                address214 = address214.replace('"', '')
            except:
                pass
            try:
                city4 = self.driver.find_element_by_xpath(
                    """//*[@id="ContentPlaceHolder1_GVWBranchDetails_lblb1City_3"]""")
                city4 = city4.text
            except:
                pass
            try:
                district4 = self.driver.find_element_by_xpath(
                    """//*[@id="ContentPlaceHolder1_GVWBranchDetails_lblb1Dist_3"]""")
                district4 = district4.text
            except:
                pass
            try:
                state7 = self.driver.find_element_by_xpath(
                    """// *[ @ id = "ContentPlaceHolder1_GVWBranchDetails_lblb1State_3"]""")
                state7 = state7.text
            except:
                pass

            try:
                pin3 = self.driver.find_element_by_xpath(
                    """// *[ @ id = "ContentPlaceHolder1_GVWBranchDetails_lblb1Pin_3"]""")
                pin3 = pin3.text
            except:
                pass
            try:
                phoneNumber3 = self.driver.find_element_by_xpath(
                    """//*[@id="ContentPlaceHolder1_GVWBranchDetails_lblb1Phone_3"]""")
                phoneNumber3 = phoneNumber3.text
            except:
                pass
            try:
                mobileNumber3 = self.driver.find_element_by_xpath(
                    """//*[@id="ContentPlaceHolder1_GVWBranchDetails_lblb1Mobile_3"]""")
                mobileNumber3 = mobileNumber3.text
            except:
                pass
            try:
                email4 = self.driver.find_element_by_xpath(
                    """//*[@id="ContentPlaceHolder1_GVWBranchDetails_lblb1Email_3"]""")
                email4 = email4.text
            except:
                pass

            try:
                branchIncharge4 = self.driver.find_element_by_xpath(
                    """//*[@id="ContentPlaceHolder1_GVWBranchDetails_lblmemberInChargeOfHo_4"]""")
                branchIncharge4 = branchIncharge4.text
            except:
                pass
            try:
                address219 = self.driver.find_element_by_xpath(
                    """//*[@id="ContentPlaceHolder1_GVWBranchDetails_lblb1Add1_4"]""")
                address219 = address219.text
                address310 = self.driver.find_element_by_xpath(
                    """// *[ @ id = "ContentPlaceHolder1_GVWBranchDetails_lblb1Add2_4"]""")
                address310 = address310.text
                address311 = self.driver.find_element_by_xpath(
                    """//*[@id="ContentPlaceHolder1_GVWBranchDetails_lblb1Add3_4"]""")
                address311 = address311.text

                address321 = address219 + " " + address310 + " " + address311
                address321 = address321.replace('"', '')
            except:
                pass
            try:
                city5 = self.driver.find_element_by_xpath(
                    """//*[@id="ContentPlaceHolder1_GVWBranchDetails_lblb1City_4"]""")
                city5 = city5.text
            except:
                pass
            try:
                district5 = self.driver.find_element_by_xpath(
                    """//*[@id="ContentPlaceHolder1_GVWBranchDetails_lblb1Dist_4"]""")
                district5 = district5.text
            except:
                pass
            try:
                state8 = self.driver.find_element_by_xpath(
                    """// *[ @ id = "ContentPlaceHolder1_GVWBranchDetails_lblb1State_4"]""")
                state8 = state8.text
            except:
                pass

            try:
                pin4 = self.driver.find_element_by_xpath(
                    """// *[ @ id = "ContentPlaceHolder1_GVWBranchDetails_lblb1Pin_4"]""")
                pin4 = pin4.text
            except:
                pass
            try:
                phoneNumber4 = self.driver.find_element_by_xpath(
                    """//*[@id="ContentPlaceHolder1_GVWBranchDetails_lblb1Phone_4"]""")
                phoneNumber4 = phoneNumber4.text
            except:
                pass
            try:
                mobileNumber4 = self.driver.find_element_by_xpath(
                    """//*[@id="ContentPlaceHolder1_GVWBranchDetails_lblb1Mobile_4"]""")
                mobileNumber4 = mobileNumber4.text
            except:
                pass
            try:
                email5 = self.driver.find_element_by_xpath(
                    """//*[@id="ContentPlaceHolder1_GVWBranchDetails_lblb1Email_4"]""")
                email5 = email5.text
            except:
                pass


            ##Member details information

            try:
                serialNumbermember = self.driver.find_element_by_xpath(
                    """//*[@id="ContentPlaceHolder1_GVWMemberDetails"]/tbody/tr[2]/td[1]""")
                serialNumbermember = serialNumbermember.text
            except:
                pass

            try:
                memberNumber = self.driver.find_element_by_xpath(
                    """// *[ @ id = "ContentPlaceHolder1_GVWMemberDetails_lblmemNo_0"]""")
                memberNumber = memberNumber.text
            except:
                pass

            try:
                memberName = self.driver.find_element_by_xpath(
                    """//*[@id="ContentPlaceHolder1_GVWMemberDetails_lblmemName_0"]""")
                memberName = memberName.text
            except:
                pass

            try:
                addressmember = self.driver.find_element_by_xpath(
                    """//*[@id="ContentPlaceHolder1_GVWMemberDetails_lblmAdd1_0"]""")
                addressmember = addressmember.text
            except:
                pass
            try:
                citymember = self.driver.find_element_by_xpath(
                    """// *[ @ id = "ContentPlaceHolder1_GVWMemberDetails_lblcity_0"]""")
                citymember = citymember.text
            except:
                pass
            try:
                pinmember = self.driver.find_element_by_xpath(
                    """//*[@id="ContentPlaceHolder1_GVWMemberDetails_lblPin_0"]""")
                pinmember = pinmember.text
            except:
                pass

            try:
                statemember = self.driver.find_element_by_xpath(
                    """// *[ @ id = "ContentPlaceHolder1_GVWMemberDetails_lblState_0"]""")
                statemember = statemember.text
            except:
                pass

            try:
                serialNumbermember1 = self.driver.find_element_by_xpath(
                    """//*[@id="ContentPlaceHolder1_GVWMemberDetails"]/tbody/tr[3]/td[1]""")
                serialNumbermember1 = serialNumbermember1.text
            except:
                pass

            try:
                memberNumber1 = self.driver.find_element_by_xpath(
                    """// *[ @ id = "ContentPlaceHolder1_GVWMemberDetails_lblmemNo_1"]""")
                memberNumber1 = memberNumber1.text
            except:
                pass

            try:
                memberName1 = self.driver.find_element_by_xpath(
                    """//*[@id="ContentPlaceHolder1_GVWMemberDetails_lblmemName_1"]""")
                memberName1 = memberName1.text
            except:
                pass

            try:
                addressmember1 = self.driver.find_element_by_xpath(
                    """//*[@id="ContentPlaceHolder1_GVWMemberDetails_lblmAdd1_1"]""")
                addressmember1 = addressmember1.text
            except:
                pass
            try:
                citymember1 = self.driver.find_element_by_xpath(
                    """// *[ @ id = "ContentPlaceHolder1_GVWMemberDetails_lblcity_1"]""")
                citymember1 = citymember1.text
            except:
                pass
            try:
                pinmember1 = self.driver.find_element_by_xpath(
                    """// *[ @ id = "ContentPlaceHolder1_GVWMemberDetails_lblPin_1"]""")
                pinmember1 = pinmember1.text
            except:
                pass

            try:
                statemember1 = self.driver.find_element_by_xpath(
                    """// *[ @ id = "ContentPlaceHolder1_GVWMemberDetails_lblState_1"]""")
                statemember1 = statemember1.text
            except:
                pass

            try:
                serialNumbermember2 = self.driver.find_element_by_xpath(
                    """//*[@id="ContentPlaceHolder1_GVWMemberDetails"]/tbody/tr[4]/td[1]""")
                serialNumbermember2 = serialNumbermember2.text
            except:
                pass

            try:
                memberNumber2 = self.driver.find_element_by_xpath(
                    """// *[ @ id = "ContentPlaceHolder1_GVWMemberDetails_lblmemNo_2"]""")
                memberNumber2 = memberNumber2.text
            except:
                pass

            try:
                memberName2 = self.driver.find_element_by_xpath(
                    """//*[@id="ContentPlaceHolder1_GVWMemberDetails_lblmemName_2"]""")
                memberName2 = memberName2.text
            except:
                pass

            try:
                addressmember2 = self.driver.find_element_by_xpath(
                    """//*[@id="ContentPlaceHolder1_GVWMemberDetails_lblmAdd1_2"]""")
                addressmember2 = addressmember2.text
            except:
                pass
            try:
                citymember2 = self.driver.find_element_by_xpath(
                    """// *[ @ id = "ContentPlaceHolder1_GVWMemberDetails_lblcity_2"]""")
                citymember2 = citymember2.text
            except:
                pass
            try:
                pinmember2 = self.driver.find_element_by_xpath(
                    """// *[ @ id = "ContentPlaceHolder1_GVWMemberDetails_lblPin_2"]""")
                pinmember2 = pinmember2.text
            except:
                pass

            try:
                statemember2 = self.driver.find_element_by_xpath(
                    """// *[ @ id = "ContentPlaceHolder1_GVWMemberDetails_lblState_2"]""")
                statemember2 = statemember2.text
            except:
                pass

            try:
                serialNumbermember3 = self.driver.find_element_by_xpath(
                    """//*[@id="ContentPlaceHolder1_GVWMemberDetails"]/tbody/tr[5]/td[1]""")
                serialNumbermember3 = serialNumbermember3.text
            except:
                pass

            try:
                memberNumber3 = self.driver.find_element_by_xpath(
                    """// *[ @ id = "ContentPlaceHolder1_GVWMemberDetails_lblmemNo_3"]""")
                memberNumber3 = memberNumber3.text
            except:
                pass

            try:
                memberName3 = self.driver.find_element_by_xpath(
                    """//*[@id="ContentPlaceHolder1_GVWMemberDetails_lblmemName_3"]""")
                memberName3 = memberName3.text
            except:
                pass

            try:
                addressmember3 = self.driver.find_element_by_xpath(
                    """//*[@id="ContentPlaceHolder1_GVWMemberDetails_lblmAdd1_3"]""")
                addressmember3 = addressmember3.text
            except:
                pass
            try:
                citymember3 = self.driver.find_element_by_xpath(
                    """// *[ @ id = "ContentPlaceHolder1_GVWMemberDetails_lblcity_3"]""")
                citymember3 = citymember3.text
            except:
                pass
            try:
                pinmember3 = self.driver.find_element_by_xpath(
                    """// *[ @ id = "ContentPlaceHolder1_GVWMemberDetails_lblPin_3"]""")
                pinmember3 = pinmember3.text
            except:
                pass

            try:
                statemember3 = self.driver.find_element_by_xpath(
                    """// *[ @ id = "ContentPlaceHolder1_GVWMemberDetails_lblState_3"]""")
                statemember3 = statemember3.text
            except:
                pass

            try:
                serialNumbermember4 = self.driver.find_element_by_xpath(
                    """//*[@id="ContentPlaceHolder1_GVWMemberDetails"]/tbody/tr[6]/td[1]""")
                serialNumbermember4 = serialNumbermember4.text
            except:
                pass

            try:
                memberNumber4 = self.driver.find_element_by_xpath(
                    """// *[ @ id = "ContentPlaceHolder1_GVWMemberDetails_lblmemNo_4"]""")
                memberNumber4 = memberNumber4.text
            except:
                pass

            try:
                memberName4 = self.driver.find_element_by_xpath(
                    """//*[@id="ContentPlaceHolder1_GVWMemberDetails_lblmemName_4"]""")
                memberName4 = memberName4.text
            except:
                pass

            try:
                addressmember4 = self.driver.find_element_by_xpath(
                    """//*[@id="ContentPlaceHolder1_GVWMemberDetails_lblmAdd1_4"]""")
                addressmember4 = addressmember4.text
            except:
                pass
            try:
                citymember4 = self.driver.find_element_by_xpath(
                    """// *[ @ id = "ContentPlaceHolder1_GVWMemberDetails_lblcity_4"]""")
                citymember4 = citymember4.text
            except:
                pass
            try:
                pinmember4 = self.driver.find_element_by_xpath(
                    """// *[ @ id = "ContentPlaceHolder1_GVWMemberDetails_lblPin_4"]""")
                pinmember4 = pinmember4.text
            except:
                pass

            try:
                statemember4 = self.driver.find_element_by_xpath(
                    """// *[ @ id = "ContentPlaceHolder1_GVWMemberDetails_lblState_4"]""")
                statemember4 = statemember4.text
            except:
                pass
            try:
                serialNumbermember5 = self.driver.find_element_by_xpath(
                    """//*[@id="ContentPlaceHolder1_GVWMemberDetails"]/tbody/tr[7]/td[1]""")
                serialNumbermember5 = serialNumbermember5.text

            except:
                pass


            try:
                memberNumber5 = self.driver.find_element_by_xpath(
                    """// *[ @ id = "ContentPlaceHolder1_GVWMemberDetails_lblmemNo_5"]""")
                memberNumber5 = memberNumber5.text
            except:
                pass

            try:
                memberName5 = self.driver.find_element_by_xpath(
                    """//*[@id="ContentPlaceHolder1_GVWMemberDetails_lblmemName_5"]""")
                memberName5 = memberName5.text
            except:
                pass

            try:
                addressmember5 = self.driver.find_element_by_xpath(
                    """//*[@id="ContentPlaceHolder1_GVWMemberDetails_lblmAdd1_5"]""")
                addressmember5 = addressmember5.text
            except:
                pass
            try:
                citymember5 = self.driver.find_element_by_xpath(
                    """// *[ @ id = "ContentPlaceHolder1_GVWMemberDetails_lblcity_5"]""")
                citymember5 = citymember5.text
            except:
                pass
            try:
                pinmember5 = self.driver.find_element_by_xpath(
                    """// *[ @ id = "ContentPlaceHolder1_GVWMemberDetails_lblPin_5"]""")
                pinmember5 = pinmember5.text
            except:
                pass

            try:
                statemember5 = self.driver.find_element_by_xpath(
                    """// *[ @ id = "ContentPlaceHolder1_GVWMemberDetails_lblState_5"]""")
                statemember5 = statemember5.text
            except:
                pass

            try:
                serialNumbermember6 = self.driver.find_element_by_xpath(
                    """//*[@id="ContentPlaceHolder1_GVWMemberDetails"]/tbody/tr[8]/td[1]""")
                serialNumbermember6 = serialNumbermember6.text
            except:
                pass

            try:
                memberNumber6 = self.driver.find_element_by_xpath(
                    """// *[ @ id = "ContentPlaceHolder1_GVWMemberDetails_lblmemNo_6"]""")
                memberNumber6 = memberNumber6.text
            except:
                pass

            try:
                memberName6 = self.driver.find_element_by_xpath(
                    """//*[@id="ContentPlaceHolder1_GVWMemberDetails_lblmemName_6"]""")
                memberName6 = memberName6.text
            except:
                pass

            try:
                addressmember6 = self.driver.find_element_by_xpath(
                    """//*[@id="ContentPlaceHolder1_GVWMemberDetails_lblmAdd1_6"]""")
                addressmember6 = addressmember6.text
            except:
                pass
            try:
                citymember6 = self.driver.find_element_by_xpath(
                    """// *[ @ id = "ContentPlaceHolder1_GVWMemberDetails_lblcity_6"]""")
                citymember6 = citymember6.text
            except:
                pass
            try:
                pinmember6 = self.driver.find_element_by_xpath(
                    """// *[ @ id = "ContentPlaceHolder1_GVWMemberDetails_lblPin_6"]""")
                pinmember6 = pinmember6.text
            except:
                pass

            try:
                statemember6 = self.driver.find_element_by_xpath(
                    """// *[ @ id = "ContentPlaceHolder1_GVWMemberDetails_lblState_6"]""")
                statemember6 = statemember6.text
            except:
                pass

            try:
                serialNumbermember7 = self.driver.find_element_by_xpath(
                    """//*[@id="ContentPlaceHolder1_GVWMemberDetails"]/tbody/tr[9]/td[1]""")
                serialNumbermember7 = serialNumbermember7.text
            except:
                pass

            try:
                memberNumber7 = self.driver.find_element_by_xpath(
                    """// *[ @ id = "ContentPlaceHolder1_GVWMemberDetails_lblmemNo_7"]""")
                memberNumber7 = memberNumber7.text
            except:
                pass

            try:
                memberName7 = self.driver.find_element_by_xpath(
                    """//*[@id="ContentPlaceHolder1_GVWMemberDetails_lblmemName_7"]""")
                memberName7 = memberName7.text
            except:
                pass

            try:
                addressmember7 = self.driver.find_element_by_xpath(
                    """//*[@id="ContentPlaceHolder1_GVWMemberDetails_lblmAdd1_7"]""")
                addressmember7 = addressmember7.text
            except:
                pass
            try:
                citymember7 = self.driver.find_element_by_xpath(
                    """// *[ @ id = "ContentPlaceHolder1_GVWMemberDetails_lblcity_7"]""")
                citymember7 = citymember7.text
            except:
                pass
            try:
                pinmember7 = self.driver.find_element_by_xpath(
                    """// *[ @ id = "ContentPlaceHolder1_GVWMemberDetails_lblPin_7"]""")
                pinmember7 = pinmember7.text
            except:
                pass

            try:
                statemember7 = self.driver.find_element_by_xpath(
                    """// *[ @ id = "ContentPlaceHolder1_GVWMemberDetails_lblState_7"]""")
                statemember7 = statemember7.text
            except:
                pass

            try:
                serialNumbermember8 = self.driver.find_element_by_xpath(
                    """//*[@id="ContentPlaceHolder1_GVWMemberDetails"]/tbody/tr[10]/td[1]""")
                serialNumbermember8 = serialNumbermember8.text
            except:
                pass

            try:
                memberNumber8 = self.driver.find_element_by_xpath(
                    """// *[ @ id = "ContentPlaceHolder1_GVWMemberDetails_lblmemNo_8"]""")
                memberNumber8 = memberNumber8.text
            except:
                pass

            try:
                memberName8 = self.driver.find_element_by_xpath(
                    """//*[@id="ContentPlaceHolder1_GVWMemberDetails_lblmemName_8"]""")
                memberName8 = memberName8.text
            except:
                pass

            try:
                addressmember8 = self.driver.find_element_by_xpath(
                    """//*[@id="ContentPlaceHolder1_GVWMemberDetails_lblmAdd1_8"]""")
                addressmember8 = addressmember8.text
            except:
                pass
            try:
                citymember8 = self.driver.find_element_by_xpath(
                    """// *[ @ id = "ContentPlaceHolder1_GVWMemberDetails_lblcity_8"]""")
                citymember8 = citymember8.text
            except:
                pass
            try:
                pinmember8 = self.driver.find_element_by_xpath(
                    """//*[@id="ContentPlaceHolder1_GVWMemberDetails_lblPin_7"]""")
                pinmember8 = pinmember8.text
            except:
                pass

            try:
                statemember8 = self.driver.find_element_by_xpath(
                    """// *[ @ id = "ContentPlaceHolder1_GVWMemberDetails_lblState_8"]""")
                statemember8 = statemember8.text
            except:
                pass
            try:
                action = ActionChains(self.driver)
                parent_level_menu = self.driver.find_element_by_xpath(
                    """//*[@id="form1"]/table/tbody/tr[2]/td/div/ul/li[6]/a""")
                action.move_to_element(parent_level_menu).perform()
                child_level_menu = self.driver.find_element_by_xpath(
                    """//*[@id="form1"]/table/tbody/tr[2]/td/div/ul/li[6]/ul/li[4]/a""")
                action.move_to_element(child_level_menu).perform()
                child_level_menu.click()
                self.driver.find_element_by_xpath("""// *[ @ id = "ContentPlaceHolder1_TextBox_Value"]""").click()
                self.driver.find_element_by_xpath("""// *[ @ id = "ContentPlaceHolder1_TextBox_Value"]""").send_keys(
                    licenseNumber)
                self.driver.find_element_by_xpath("""//*[@id="ContentPlaceHolder1_ButtonSearch"]""").click()
                time.sleep(3)
                self.driver.find_element_by_xpath("""// *[ @ id = "ContentPlaceHolder1_GRVCopMasterDet"] / tbody / tr[2] / td[13] / a / img""").click()

            except:
                pass

            try:
                self.driver.find_element_by_xpath(
                    """//*[@id="ContentPlaceHolder1_GRVOfficeDet"]/tbody/tr[3]/td[10]/a/img""").click()
                time.sleep(2)
            except:
                pass
            try:
                firmNumber1 = self.driver.find_element_by_xpath("""//*[@id="ContentPlaceHolder1_TextBox_firmNo"]""")
                firmNumber1 = firmNumber1.text
            except:
                pass

            try:
                reonstitutionDate1 = self.driver.find_element_by_xpath(
                    """// *[ @ id = "ContentPlaceHolder1_TextBox_reConDate"]""")
                reonstitutionDate1 = reonstitutionDate1.get_attribute("value")
                from datetime import datetime
                date_obj = datetime.strptime(reonstitutionDate1, '%d/%m/%Y')
                reonstitutionDate1 = date_obj.strftime('%d-%b-%Y')
            except:
                pass


            try:
                lDate1 = self.driver.find_element_by_xpath("""//*[@id="ContentPlaceHolder1_TextBox_ldt"]""")
                lDate1 = lDate1.get_attribute("value")
                from datetime import datetime
                date_obj = datetime.strptime(lDate1, '%d/%m/%Y')
                lDate1 = date_obj.strftime('%d-%b-%Y')
            except:
                pass

            try:
                address71 = self.driver.find_element_by_xpath("""//*[@id="ContentPlaceHolder1_TextBox_add1"]""")
                address71 = address71.get_attribute("value")
                address72 = self.driver.find_element_by_xpath("""//*[@id="ContentPlaceHolder1_TextBox_add2"]""")
                address72 = address72.get_attribute("value")
                address73 = self.driver.find_element_by_xpath("""//*[@id="ContentPlaceHolder1_TextBox_add3"]""")
                address73 = address73.get_attribute("value")
                try:
                    address888 = self.driver.find_element_by_xpath("""//*[@id="ContentPlaceHolder1_TextBox_add4"]""")
                    address888 = address888.get_attribute("value")
                except:
                    address888 = ""
                    pass
                address74 = address71 + " " + address72 + " " + address73 + " " + address888
                address74 = address74.replace('"', '')

            except:
                pass
            try:
                telephoneMobileNumber1 = self.driver.find_element_by_xpath(
                    """//*[@id="ContentPlaceHolder1_TextBox_phone"]""")
                telephoneMobileNumber1 = telephoneMobileNumber1.get_attribute("value")
            except:
                pass
            try:
                mobileNumberh1 = self.driver.find_element_by_xpath(
                    """// *[ @ id = "ContentPlaceHolder1_TextBox_mobile"]""")
                mobileNumberh1 = mobileNumberh1.get_attribute('value')
            except:
                pass
            try:
                emailIdOfficial1 = self.driver.find_element_by_xpath("""//*[@id="ContentPlaceHolder1_TextBox_email"]""")
                emailIdOfficial1 = emailIdOfficial1.get_attribute("value")
            except:
                pass


            try:
                from selenium.webdriver.support.select import Select
                select = Select(self.driver.find_element_by_xpath("""// *[ @ id = "ContentPlaceHolder1_ddlState"]"""))
                selected_option = select.first_selected_option
                state44 = selected_option.text
                select = Select(self.driver.find_element_by_xpath("""//*[@id="ContentPlaceHolder1_ddlCity"]"""))
                selected_option1 = select.first_selected_option
                city44 = selected_option1.text
            except:
                pass
            try:
                district44 = self.driver.find_element_by_xpath("""//*[@id="ContentPlaceHolder1_TextBox_dist"]""")
                district44 = district44.get_attribute("value")
            except:
                pass
            try:
                pincode112 = self.driver.find_element_by_xpath("""//*[@id="ContentPlaceHolder1_TextBox_pin"]""")
                pincode112 = pincode112.get_attribute("value")
            except:
                pass

            ##Address of the branch

            try:
                branchIncharge5 = self.driver.find_element_by_xpath(
                    """// *[ @ id = "ContentPlaceHolder1_GVWBranchDetails_lblmemberInChargeOfHo_0"]""")
                branchIncharge5 = branchIncharge5.text
            except:
                pass
            try:
                address49 = self.driver.find_element_by_xpath(
                    """//*[@id="ContentPlaceHolder1_GVWBranchDetails_lblb1Add1_0"]""")
                address49 = address49.text
                address50 = self.driver.find_element_by_xpath(
                    """// *[ @ id = "ContentPlaceHolder1_GVWBranchDetails_lblb1Add2_0"]""")
                address50 = address50.text
                address51 = self.driver.find_element_by_xpath(
                    """//*[@id="ContentPlaceHolder1_GVWBranchDetails_lblb1Add3_0"]""")
                address51 = address51.text
                address52 = address49 + " " + address50 + " " + address51
                address52 = address52.replace('"', '')

            except:
                pass
            try:
                city6 = self.driver.find_element_by_xpath(
                    """//*[@id="ContentPlaceHolder1_GVWBranchDetails_lblb1City_0"]""")
                city6 = city6.text
            except:
                pass
            try:
                district6 = self.driver.find_element_by_xpath(
                    """//*[@id="ContentPlaceHolder1_GVWBranchDetails_lblb1Dist_0"]""")
                district6 = district6.text
            except:
                pass
            try:
                state11 = self.driver.find_element_by_xpath(
                    """// *[ @ id = "ContentPlaceHolder1_GVWBranchDetails_lblb1State_0"]""")
                state11 = state11.text
            except:
                pass

            try:
                pin5 = self.driver.find_element_by_xpath(
                    """// *[ @ id = "ContentPlaceHolder1_GVWBranchDetails_lblb1Pin_0"]""")
                pin5 = pin5.text
            except:
                pass
            try:
                phoneNumber5 = self.driver.find_element_by_xpath(
                    """//*[@id="ContentPlaceHolder1_GVWBranchDetails_lblb1Phone_0"]""")
                phoneNumber5 = phoneNumber5.text
            except:
                pass
            try:
                mobileNumber5 = self.driver.find_element_by_xpath(
                    """//*[@id="ContentPlaceHolder1_GVWBranchDetails_lblb1Mobile_0"]""")
                mobileNumber5 = mobileNumber5.text
            except:
                pass
            try:
                email6 = self.driver.find_element_by_xpath(
                    """//*[@id="ContentPlaceHolder1_GVWBranchDetails_lblb1Email_0"]""")
                email6 = email6.text
            except:
                pass

            try:
                branchIncharge6 = self.driver.find_element_by_xpath(
                    """//*[@id="ContentPlaceHolder1_GVWBranchDetails_lblmemberInChargeOfHo_1"]""")
                branchIncharge6 = branchIncharge6.text
            except:
                pass
            try:
                address131 = self.driver.find_element_by_xpath(
                    """//*[@id="ContentPlaceHolder1_GVWBranchDetails_lblb1Add1_1"]""")
                address131 = address131.text
                address132 = self.driver.find_element_by_xpath(
                    """// *[ @ id = "ContentPlaceHolder1_GVWBranchDetails_lblb1Add2_1"]""")
                address132 = address132.text
                address133 = self.driver.find_element_by_xpath(
                    """//*[@id="ContentPlaceHolder1_GVWBranchDetails_lblb1Add3_1"]""")
                address133 = address133.text
                address134 = address131 + " " + address132 + " " + address133
                address134 = address134.replace('"', '')
            except:
                pass
            try:
                city7 = self.driver.find_element_by_xpath(
                    """//*[@id="ContentPlaceHolder1_GVWBranchDetails_lblb1City_1"]""")
                city7 = city7.text
            except:
                pass
            try:
                district7 = self.driver.find_element_by_xpath(
                    """//*[@id="ContentPlaceHolder1_GVWBranchDetails_lblb1Dist_1"]""")
                district7 = district7.text
            except:
                pass
            try:
                state12 = self.driver.find_element_by_xpath(
                    """// *[ @ id = "ContentPlaceHolder1_GVWBranchDetails_lblb1State_1"]""")
                state12 = state12.text
            except:
                pass

            try:
                pin6 = self.driver.find_element_by_xpath(
                    """// *[ @ id = "ContentPlaceHolder1_GVWBranchDetails_lblb1Pin_1"]""")
                pin6 = pin6.text
            except:
                pass
            try:
                phoneNumber7 = self.driver.find_element_by_xpath(
                    """//*[@id="ContentPlaceHolder1_GVWBranchDetails_lblb1Phone_1"]""")
                phoneNumber7 = phoneNumber7.text
            except:
                pass
            try:
                mobileNumber7 = self.driver.find_element_by_xpath(
                    """//*[@id="ContentPlaceHolder1_GVWBranchDetails_lblb1Mobile_1"]""")
                mobileNumber7 = mobileNumber7.text
            except:
                pass
            try:
                email7 = self.driver.find_element_by_xpath(
                    """//*[@id="ContentPlaceHolder1_GVWBranchDetails_lblb1Email_1"]""")
                email7 = email7.text
            except:
                pass

            try:
                branchIncharge7 = self.driver.find_element_by_xpath(
                    """//*[@id="ContentPlaceHolder1_GVWBranchDetails_lblmemberInChargeOfHo_2"]""")
                branchIncharge7 = branchIncharge7.text
            except:
                pass
            try:
                address141 = self.driver.find_element_by_xpath(
                    """//*[@id="ContentPlaceHolder1_GVWBranchDetails_lblb1Add1_2"]""")
                address141 = address141.text
                address142 = self.driver.find_element_by_xpath(
                    """// *[ @ id = "ContentPlaceHolder1_GVWBranchDetails_lblb1Add2_2"]""")
                address142 = address142.text
                address143 = self.driver.find_element_by_xpath(
                    """//*[@id="ContentPlaceHolder1_GVWBranchDetails_lblb1Add3_2"]""")
                address143 = address143.text

                address144 = address141 + " " + address142 + " " + address143
                address144 = address144.replace('"', '')
            except:
                pass
            try:
                city8 = self.driver.find_element_by_xpath(
                    """//*[@id="ContentPlaceHolder1_GVWBranchDetails_lblb1City_2"]""")
                city8 = city8.text
            except:
                pass
            try:
                district8 = self.driver.find_element_by_xpath(
                    """//*[@id="ContentPlaceHolder1_GVWBranchDetails_lblb1Dist_2"]""")
                district8 = district8.text
            except:
                pass
            try:
                state13 = self.driver.find_element_by_xpath(
                    """// *[ @ id = "ContentPlaceHolder1_GVWBranchDetails_lblb1State_2"]""")
                state13 = state13.text
            except:
                pass

            try:
                pin7 = self.driver.find_element_by_xpath(
                    """// *[ @ id = "ContentPlaceHolder1_GVWBranchDetails_lblb1Pin_2"]""")
                pin7 = pin7.text
            except:
                pass
            try:
                phoneNumber8 = self.driver.find_element_by_xpath(
                    """//*[@id="ContentPlaceHolder1_GVWBranchDetails_lblb1Phone_2"]""")
                phoneNumber8 = phoneNumber8.text
            except:
                pass
            try:
                mobileNumber8 = self.driver.find_element_by_xpath(
                    """//*[@id="ContentPlaceHolder1_GVWBranchDetails_lblb1Mobile_2"]""")
                mobileNumber8 = mobileNumber8.text
            except:
                pass
            try:
                email8 = self.driver.find_element_by_xpath(
                    """//*[@id="ContentPlaceHolder1_GVWBranchDetails_lblb1Email_2"]""")
                email8 = email8.text
            except:
                pass

            try:
                branchIncharge8 = self.driver.find_element_by_xpath(
                    """//*[@id="ContentPlaceHolder1_GVWBranchDetails_lblmemberInChargeOfHo_3"]""")
                branchIncharge8 = branchIncharge8.text
            except:
                pass
            try:
                address211 = self.driver.find_element_by_xpath(
                    """//*[@id="ContentPlaceHolder1_GVWBranchDetails_lblb1Add1_3"]""")
                address211 = address211.text
                address212 = self.driver.find_element_by_xpath(
                    """// *[ @ id = "ContentPlaceHolder1_GVWBranchDetails_lblb1Add2_3"]""")
                address212 = address212.text
                address213 = self.driver.find_element_by_xpath(
                    """//*[@id="ContentPlaceHolder1_GVWBranchDetails_lblb1Add3_3"]""")
                address213 = address213.text

                address214 = address211 + " " + address212 + " " + address213
                address214 = address214.replace('"', '')

            except:
                pass
            try:
                city9 = self.driver.find_element_by_xpath(
                    """//*[@id="ContentPlaceHolder1_GVWBranchDetails_lblb1City_3"]""")
                city9 = city9.text
            except:
                pass
            try:
                district9 = self.driver.find_element_by_xpath(
                    """//*[@id="ContentPlaceHolder1_GVWBranchDetails_lblb1Dist_3"]""")
                district9 = district9.text
            except:
                pass
            try:
                state14 = self.driver.find_element_by_xpath(
                    """// *[ @ id = "ContentPlaceHolder1_GVWBranchDetails_lblb1State_3"]""")
                state14 = state14.text
            except:
                pass

            try:
                pin8 = self.driver.find_element_by_xpath(
                    """// *[ @ id = "ContentPlaceHolder1_GVWBranchDetails_lblb1Pin_3"]""")
                pin8 = pin8.text
            except:
                pass
            try:
                phoneNumber9 = self.driver.find_element_by_xpath(
                    """//*[@id="ContentPlaceHolder1_GVWBranchDetails_lblb1Phone_3"]""")
                phoneNumber9 = phoneNumber9.text
            except:
                pass
            try:
                mobileNumber9 = self.driver.find_element_by_xpath(
                    """//*[@id="ContentPlaceHolder1_GVWBranchDetails_lblb1Mobile_3"]""")
                mobileNumber9 = mobileNumber9.text
            except:
                pass
            try:
                email9 = self.driver.find_element_by_xpath(
                    """//*[@id="ContentPlaceHolder1_GVWBranchDetails_lblb1Email_3"]""")
                email9 = email9.text
            except:
                pass

            try:
                branchIncharge9 = self.driver.find_element_by_xpath(
                    """//*[@id="ContentPlaceHolder1_GVWBranchDetails_lblmemberInChargeOfHo_4"]""")
                branchIncharge9 = branchIncharge9.text
            except:
                pass
            try:
                address251 = self.driver.find_element_by_xpath(
                    """//*[@id="ContentPlaceHolder1_GVWBranchDetails_lblb1Add1_4"]""")
                address251 = address251.text
                address252 = self.driver.find_element_by_xpath(
                    """// *[ @ id = "ContentPlaceHolder1_GVWBranchDetails_lblb1Add2_4"]""")
                address252 = address252.text
                address253 = self.driver.find_element_by_xpath(
                    """//*[@id="ContentPlaceHolder1_GVWBranchDetails_lblb1Add3_4"]""")
                address253 = address253.text

                address254 = address251 + " " + address252 + " " + address253
                address254 = address254.replace('"', '')

            except:
                pass
            try:
                city10 = self.driver.find_element_by_xpath(
                    """//*[@id="ContentPlaceHolder1_GVWBranchDetails_lblb1City_4"]""")
                city10 = city10.text
            except:
                pass
            try:
                district10 = self.driver.find_element_by_xpath(
                    """//*[@id="ContentPlaceHolder1_GVWBranchDetails_lblb1Dist_4"]""")
                district10 = district10.text
            except:
                pass
            try:
                state15 = self.driver.find_element_by_xpath(
                    """// *[ @ id = "ContentPlaceHolder1_GVWBranchDetails_lblb1State_4"]""")
                state15 = state15.text
            except:
                pass

            try:
                pin9 = self.driver.find_element_by_xpath(
                    """// *[ @ id = "ContentPlaceHolder1_GVWBranchDetails_lblb1Pin_4"]""")
                pin9 = pin9.text
            except:
                pass
            try:
                phoneNumber10 = self.driver.find_element_by_xpath(
                    """//*[@id="ContentPlaceHolder1_GVWBranchDetails_lblb1Phone_4"]""")
                phoneNumber10 = phoneNumber10.text
            except:
                pass
            try:
                mobileNumber10 = self.driver.find_element_by_xpath(
                    """//*[@id="ContentPlaceHolder1_GVWBranchDetails_lblb1Mobile_4"]""")
                mobileNumber10 = mobileNumber10.text
            except:
                pass
            try:
                email10 = self.driver.find_element_by_xpath(
                    """//*[@id="ContentPlaceHolder1_GVWBranchDetails_lblb1Email_4"]""")
                email10 = email10.text
            except:
                pass

            ##Member details information

            try:
                serialNumbermember9 = self.driver.find_element_by_xpath(
                    """//*[@id="ContentPlaceHolder1_GVWMemberDetails"]/tbody/tr[2]/td[1]""")
                serialNumbermember9 = serialNumbermember9.text
            except:
                pass

            try:
                memberNumber9 = self.driver.find_element_by_xpath(
                    """// *[ @ id = "ContentPlaceHolder1_GVWMemberDetails_lblmemNo_0"]""")
                memberNumber9 = memberNumber9.text
            except:
                pass

            try:
                memberName9 = self.driver.find_element_by_xpath(
                    """//*[@id="ContentPlaceHolder1_GVWMemberDetails_lblmemName_0"]""")
                memberName9 = memberName9.text
            except:
                pass

            try:
                addressmember9 = self.driver.find_element_by_xpath(
                    """//*[@id="ContentPlaceHolder1_GVWMemberDetails_lblmAdd1_0"]""")
                addressmember9 = addressmember9.text
            except:
                pass
            try:
                citymember9 = self.driver.find_element_by_xpath(
                    """// *[ @ id = "ContentPlaceHolder1_GVWMemberDetails_lblcity_0"]""")
                citymember9 = citymember9.text
            except:
                pass
            try:
                pinmember9 = self.driver.find_element_by_xpath(
                    """//*[@id="ContentPlaceHolder1_GVWMemberDetails_lblPin_0"]""")
                pinmember9 = pinmember9.text
            except:
                pass

            try:
                statemember9 = self.driver.find_element_by_xpath(
                    """// *[ @ id = "ContentPlaceHolder1_GVWMemberDetails_lblState_0"]""")
                statemember9 = statemember9.text
            except:
                pass

            try:
                serialNumbermember10 = self.driver.find_element_by_xpath(
                    """//*[@id="ContentPlaceHolder1_GVWMemberDetails"]/tbody/tr[3]/td[1]""")
                serialNumbermember10 = serialNumbermember10.text
            except:
                pass

            try:
                memberNumber10 = self.driver.find_element_by_xpath(
                    """// *[ @ id = "ContentPlaceHolder1_GVWMemberDetails_lblmemNo_1"]""")
                memberNumber10 = memberNumber10.text
            except:
                pass

            try:
                memberName10 = self.driver.find_element_by_xpath(
                    """//*[@id="ContentPlaceHolder1_GVWMemberDetails_lblmemName_1"]""")
                memberName10 = memberName10.text
            except:
                pass

            try:
                addressmember10 = self.driver.find_element_by_xpath(
                    """//*[@id="ContentPlaceHolder1_GVWMemberDetails_lblmAdd1_1"]""")
                addressmember10 = addressmember10.text
            except:
                pass
            try:
                citymember10 = self.driver.find_element_by_xpath(
                    """// *[ @ id = "ContentPlaceHolder1_GVWMemberDetails_lblcity_1"]""")
                citymember10 = citymember10.text
            except:
                pass
            try:
                pinmember10 = self.driver.find_element_by_xpath(
                    """// *[ @ id = "ContentPlaceHolder1_GVWMemberDetails_lblPin_1"]""")
                pinmember10 = pinmember10.text
            except:
                pass

            try:
                statemember10 = self.driver.find_element_by_xpath(
                    """// *[ @ id = "ContentPlaceHolder1_GVWMemberDetails_lblState_1"]""")
                statemember10 = statemember10.text
            except:
                pass

            try:
                serialNumbermember11 = self.driver.find_element_by_xpath(
                    """//*[@id="ContentPlaceHolder1_GVWMemberDetails"]/tbody/tr[4]/td[1]""")
                serialNumbermember11 = serialNumbermember11.text
            except:
                pass

            try:
                memberNumber11 = self.driver.find_element_by_xpath(
                    """// *[ @ id = "ContentPlaceHolder1_GVWMemberDetails_lblmemNo_2"]""")
                memberNumber11 = memberNumber11.text
            except:
                pass

            try:
                memberName11 = self.driver.find_element_by_xpath(
                    """//*[@id="ContentPlaceHolder1_GVWMemberDetails_lblmemName_2"]""")
                memberName11 = memberName11.text
            except:
                pass

            try:
                addressmember11 = self.driver.find_element_by_xpath(
                    """//*[@id="ContentPlaceHolder1_GVWMemberDetails_lblmAdd1_2"]""")
                addressmember11 = addressmember11.text
            except:
                pass
            try:
                citymember11 = self.driver.find_element_by_xpath(
                    """// *[ @ id = "ContentPlaceHolder1_GVWMemberDetails_lblcity_2"]""")
                citymember11 = citymember11.text
            except:
                pass
            try:
                pinmember11 = self.driver.find_element_by_xpath(
                    """// *[ @ id = "ContentPlaceHolder1_GVWMemberDetails_lblPin_2"]""")
                pinmember11 = pinmember11.text
            except:
                pass

            try:
                statemember11 = self.driver.find_element_by_xpath(
                    """// *[ @ id = "ContentPlaceHolder1_GVWMemberDetails_lblState_2"]""")
                statemember11 = statemember11.text
            except:
                pass

            try:
                serialNumbermember12 = self.driver.find_element_by_xpath(
                    """//*[@id="ContentPlaceHolder1_GVWMemberDetails"]/tbody/tr[5]/td[1]""")
                serialNumbermember12 = serialNumbermember12.text
            except:
                pass

            try:
                memberNumber12 = self.driver.find_element_by_xpath(
                    """// *[ @ id = "ContentPlaceHolder1_GVWMemberDetails_lblmemNo_3"]""")
                memberNumber12 = memberNumber12.text
            except:
                pass

            try:
                memberName12 = self.driver.find_element_by_xpath(
                    """//*[@id="ContentPlaceHolder1_GVWMemberDetails_lblmemName_3"]""")
                memberName12 = memberName12.text
            except:
                pass

            try:
                addressmember12 = self.driver.find_element_by_xpath(
                    """//*[@id="ContentPlaceHolder1_GVWMemberDetails_lblmAdd1_3"]""")
                addressmember12 = addressmember12.text
            except:
                pass
            try:
                citymember12 = self.driver.find_element_by_xpath(
                    """// *[ @ id = "ContentPlaceHolder1_GVWMemberDetails_lblcity_3"]""")
                citymember12 = citymember12.text
            except:
                pass
            try:
                pinmember12 = self.driver.find_element_by_xpath(
                    """// *[ @ id = "ContentPlaceHolder1_GVWMemberDetails_lblPin_3"]""")
                pinmember12 = pinmember12.text
            except:
                pass

            try:
                statemember12 = self.driver.find_element_by_xpath(
                    """// *[ @ id = "ContentPlaceHolder1_GVWMemberDetails_lblState_3"]""")
                statemember12 = statemember12.text
            except:
                pass




            try:
                action = ActionChains(self.driver)
                parent_level_menu = self.driver.find_element_by_xpath(
                    """//*[@id="form1"]/table/tbody/tr[2]/td/div/ul/li[6]/a""")
                action.move_to_element(parent_level_menu).perform()
                child_level_menu = self.driver.find_element_by_xpath(
                    """//*[@id="form1"]/table/tbody/tr[2]/td/div/ul/li[6]/ul/li[4]/a""")
                action.move_to_element(child_level_menu).perform()
                child_level_menu.click()
                self.driver.find_element_by_xpath("""// *[ @ id = "ContentPlaceHolder1_TextBox_Value"]""").click()
                self.driver.find_element_by_xpath("""// *[ @ id = "ContentPlaceHolder1_TextBox_Value"]""").send_keys(
                    licenseNumber)
                self.driver.find_element_by_xpath("""//*[@id="ContentPlaceHolder1_ButtonSearch"]""").click()
                time.sleep(3)
                self.driver.find_element_by_xpath("""// *[ @ id = "ContentPlaceHolder1_GRVCopMasterDet"] / tbody / tr[2] / td[13] / a / img""").click()

            except:
                pass
            try:
                self.driver.find_element_by_xpath(
                    """// *[ @ id = "ContentPlaceHolder1_GRVOfficeDet"] / tbody / tr[4] / td[10] / a / img""").click()
                time.sleep(2)
            except:
                pass
            try:
                firmNumber2 = self.driver.find_element_by_xpath("""//*[@id="ContentPlaceHolder1_TextBox_firmNo"]""")
                firmNumber2 = firmNumber2.text
            except:
                pass

            #print("dddddd ",constitutionDate2)
            try:
                reonstitutionDate2 = self.driver.find_element_by_xpath(
                    """// *[ @ id = "ContentPlaceHolder1_TextBox_reConDate"]""")
                reonstitutionDate2 = reonstitutionDate2.get_attribute("value")
                from datetime import datetime
                date_obj = datetime.strptime(reonstitutionDate2, '%d/%m/%Y')
                reonstitutionDate2 = date_obj.strftime('%d-%b-%Y')
            except:
                pass


            try:
                lDate2 = self.driver.find_element_by_xpath("""//*[@id="ContentPlaceHolder1_TextBox_ldt"]""")
                lDate2 = lDate2.get_attribute("value")
                from datetime import datetime
                date_obj = datetime.strptime(lDate2, '%d/%m/%Y')
                lDate2 = date_obj.strftime('%d-%b-%Y')
            except:
                pass
            try:
                address81 = self.driver.find_element_by_xpath("""//*[@id="ContentPlaceHolder1_TextBox_add1"]""")
                address81 = address81.get_attribute("value")
                address82 = self.driver.find_element_by_xpath("""//*[@id="ContentPlaceHolder1_TextBox_add2"]""")
                address82 = address82.get_attribute("value")
                address83 = self.driver.find_element_by_xpath("""//*[@id="ContentPlaceHolder1_TextBox_add3"]""")
                address83 = address83.get_attribute("value")
                try:
                    address9999 = self.driver.find_element_by_xpath("""//*[@id="ContentPlaceHolder1_TextBox_add4"]""")
                    address9999 = address9999.get_attribute("value")
                except:
                    address9999 = ""
                    pass
                address83 = address81 + " " + address82 + " " + address83 + " " + address9999
                address83 = address83.replace('"', '')


            except:
                pass
            try:
                telephoneMobileNumber2 = self.driver.find_element_by_xpath(
                    """//*[@id="ContentPlaceHolder1_TextBox_phone"]""")
                telephoneMobileNumber2 = telephoneMobileNumber2.get_attribute("value")
            except:
                pass
            try:
                mobileNumberh2 = self.driver.find_element_by_xpath(
                    """// *[ @ id = "ContentPlaceHolder1_TextBox_mobile"]""")
                mobileNumberh2 = mobileNumberh2.get_attribute('value')
            except:
                pass
            try:
                emailIdOfficial2 = self.driver.find_element_by_xpath("""//*[@id="ContentPlaceHolder1_TextBox_email"]""")
                emailIdOfficial2 = emailIdOfficial2.get_attribute("value")
            except:
                pass


            try:
                from selenium.webdriver.support.select import Select
                select = Select(self.driver.find_element_by_xpath("""// *[ @ id = "ContentPlaceHolder1_ddlState"]"""))
                selected_option = select.first_selected_option
                state80 = selected_option.text
                select = Select(self.driver.find_element_by_xpath("""//*[@id="ContentPlaceHolder1_ddlCity"]"""))
                selected_option1 = select.first_selected_option
                city80 = selected_option1.text
            except:
                pass
            try:
                district80 = self.driver.find_element_by_xpath("""//*[@id="ContentPlaceHolder1_TextBox_dist"]""")
                district80 = district80.get_attribute("value")
            except:
                pass
            try:
                pincode113 = self.driver.find_element_by_xpath("""//*[@id="ContentPlaceHolder1_TextBox_pin"]""")
                pincode113 = pincode113.get_attribute("value")
            except:
                pass

            ##Address of the branch

            try:
                branchIncharge10 = self.driver.find_element_by_xpath(
                    """// *[ @ id = "ContentPlaceHolder1_GVWBranchDetails_lblmemberInChargeOfHo_0"]""")
                branchIncharge10 = branchIncharge10.text
            except:
                pass
            try:
                address901 = self.driver.find_element_by_xpath(
                    """//*[@id="ContentPlaceHolder1_GVWBranchDetails_lblb1Add1_0"]""")
                address901 = address901.text
                address902 = self.driver.find_element_by_xpath(
                    """// *[ @ id = "ContentPlaceHolder1_GVWBranchDetails_lblb1Add2_0"]""")
                address902 = address902.text
                address903 = self.driver.find_element_by_xpath(
                    """//*[@id="ContentPlaceHolder1_GVWBranchDetails_lblb1Add3_0"]""")
                address903 = address903.text
                address904 = address901 + " " + address902 + " " + address903
                address904 = address904.replace('"', '')
            except:
                pass
            try:
                city11 = self.driver.find_element_by_xpath(
                    """//*[@id="ContentPlaceHolder1_GVWBranchDetails_lblb1City_0"]""")
                city11 = city11.text
            except:
                pass
            try:
                district11 = self.driver.find_element_by_xpath(
                    """//*[@id="ContentPlaceHolder1_GVWBranchDetails_lblb1Dist_0"]""")
                district11 = district11.text
            except:
                pass
            try:
                state16 = self.driver.find_element_by_xpath(
                    """// *[ @ id = "ContentPlaceHolder1_GVWBranchDetails_lblb1State_0"]""")
                state16 = state16.text
            except:
                pass

            try:
                pin10 = self.driver.find_element_by_xpath(
                    """// *[ @ id = "ContentPlaceHolder1_GVWBranchDetails_lblb1Pin_0"]""")
                pin10 = pin10.text
            except:
                pass
            try:
                phoneNumber11 = self.driver.find_element_by_xpath(
                    """//*[@id="ContentPlaceHolder1_GVWBranchDetails_lblb1Phone_0"]""")
                phoneNumber11 = phoneNumber11.text
            except:
                pass
            try:
                mobileNumber11 = self.driver.find_element_by_xpath(
                    """//*[@id="ContentPlaceHolder1_GVWBranchDetails_lblb1Mobile_0"]""")
                mobileNumber11 = mobileNumber11.text
            except:
                pass
            try:
                email11 = self.driver.find_element_by_xpath(
                    """//*[@id="ContentPlaceHolder1_GVWBranchDetails_lblb1Email_0"]""")
                email11 = email11.text
            except:
                pass

            try:
                branchIncharge11 = self.driver.find_element_by_xpath(
                    """//*[@id="ContentPlaceHolder1_GVWBranchDetails_lblmemberInChargeOfHo_1"]""")
                branchIncharge11 = branchIncharge11.text
            except:
                pass
            try:
                address161 = self.driver.find_element_by_xpath(
                    """//*[@id="ContentPlaceHolder1_GVWBranchDetails_lblb1Add1_1"]""")
                address161 = address161.text
                address162 = self.driver.find_element_by_xpath(
                    """// *[ @ id = "ContentPlaceHolder1_GVWBranchDetails_lblb1Add2_1"]""")
                address162 = address162.text
                address163 = self.driver.find_element_by_xpath(
                    """//*[@id="ContentPlaceHolder1_GVWBranchDetails_lblb1Add3_1"]""")
                address163 = address163.text
                address164 = address161 + " " + address162 + " " + address163
                address164 = address164.replace('"', '')
            except:
                pass
            try:
                city12 = self.driver.find_element_by_xpath(
                    """//*[@id="ContentPlaceHolder1_GVWBranchDetails_lblb1City_1"]""")
                city12 = city12.text
            except:
                pass
            try:
                district12 = self.driver.find_element_by_xpath(
                    """//*[@id="ContentPlaceHolder1_GVWBranchDetails_lblb1Dist_1"]""")
                district12 = district12.text
            except:
                pass
            try:
                state17 = self.driver.find_element_by_xpath(
                    """// *[ @ id = "ContentPlaceHolder1_GVWBranchDetails_lblb1State_1"]""")
                state17 = state17.text
            except:
                pass

            try:
                pin11 = self.driver.find_element_by_xpath(
                    """// *[ @ id = "ContentPlaceHolder1_GVWBranchDetails_lblb1Pin_1"]""")
                pin11 = pin11.text
            except:
                pass
            try:
                phoneNumber12 = self.driver.find_element_by_xpath(
                    """//*[@id="ContentPlaceHolder1_GVWBranchDetails_lblb1Phone_1"]""")
                phoneNumber12 = phoneNumber12.text
            except:
                pass
            try:
                mobileNumber12 = self.driver.find_element_by_xpath(
                    """//*[@id="ContentPlaceHolder1_GVWBranchDetails_lblb1Mobile_1"]""")
                mobileNumber12 = mobileNumber12.text
            except:
                pass
            try:
                email12 = self.driver.find_element_by_xpath(
                    """//*[@id="ContentPlaceHolder1_GVWBranchDetails_lblb1Email_1"]""")
                email12 = email12.text
            except:
                pass

            try:
                branchIncharge12 = self.driver.find_element_by_xpath(
                    """//*[@id="ContentPlaceHolder1_GVWBranchDetails_lblmemberInChargeOfHo_2"]""")
                branchIncharge12 = branchIncharge12.text
            except:
                pass
            try:
                address171 = self.driver.find_element_by_xpath(
                    """//*[@id="ContentPlaceHolder1_GVWBranchDetails_lblb1Add1_2"]""")
                address171 = address171.text
                address172 = self.driver.find_element_by_xpath(
                    """// *[ @ id = "ContentPlaceHolder1_GVWBranchDetails_lblb1Add2_2"]""")
                address172 = address172.text
                address173 = self.driver.find_element_by_xpath(
                    """//*[@id="ContentPlaceHolder1_GVWBranchDetails_lblb1Add3_2"]""")
                address173 = address173.text

                address174 = address171 + " " + address172 + " " + address173
                address174 = address174.replace('"', '')
            except:
                pass
            try:
                city13 = self.driver.find_element_by_xpath(
                    """//*[@id="ContentPlaceHolder1_GVWBranchDetails_lblb1City_2"]""")
                city13 = city13.text
            except:
                pass
            try:
                district13 = self.driver.find_element_by_xpath(
                    """//*[@id="ContentPlaceHolder1_GVWBranchDetails_lblb1Dist_2"]""")
                district13 = district13.text
            except:
                pass
            try:
                state17 = self.driver.find_element_by_xpath(
                    """// *[ @ id = "ContentPlaceHolder1_GVWBranchDetails_lblb1State_2"]""")
                state17 = state17.text
            except:
                pass

            try:
                pin12 = self.driver.find_element_by_xpath(
                    """// *[ @ id = "ContentPlaceHolder1_GVWBranchDetails_lblb1Pin_2"]""")
                pin12 = pin12.text
            except:
                pass
            try:
                phoneNumber13 = self.driver.find_element_by_xpath(
                    """//*[@id="ContentPlaceHolder1_GVWBranchDetails_lblb1Phone_2"]""")
                phoneNumber13 = phoneNumber13.text
            except:
                pass
            try:
                mobileNumber13 = self.driver.find_element_by_xpath(
                    """//*[@id="ContentPlaceHolder1_GVWBranchDetails_lblb1Mobile_2"]""")
                mobileNumber13 = mobileNumber13.text
            except:
                pass
            try:
                email13 = self.driver.find_element_by_xpath(
                    """//*[@id="ContentPlaceHolder1_GVWBranchDetails_lblb1Email_2"]""")
                email13 = email13.text
            except:
                pass

            try:
                branchIncharge13 = self.driver.find_element_by_xpath(
                    """//*[@id="ContentPlaceHolder1_GVWBranchDetails_lblmemberInChargeOfHo_3"]""")
                branchIncharge13 = branchIncharge13.text
            except:
                pass
            try:
                address121 = self.driver.find_element_by_xpath(
                    """//*[@id="ContentPlaceHolder1_GVWBranchDetails_lblb1Add1_3"]""")
                address121 = address121.text
                address122 = self.driver.find_element_by_xpath(
                    """// *[ @ id = "ContentPlaceHolder1_GVWBranchDetails_lblb1Add2_3"]""")
                address122 = address122.text
                address123 = self.driver.find_element_by_xpath(
                    """//*[@id="ContentPlaceHolder1_GVWBranchDetails_lblb1Add3_3"]""")
                address123 = address123.text

                address124 = address121 + " " + address122 + " " + address123
                address124 = address124.replace('"', '')
            except:
                pass
            try:
                city14 = self.driver.find_element_by_xpath(
                    """//*[@id="ContentPlaceHolder1_GVWBranchDetails_lblb1City_3"]""")
                city14 = city14.text
            except:
                pass
            try:
                district14 = self.driver.find_element_by_xpath(
                    """//*[@id="ContentPlaceHolder1_GVWBranchDetails_lblb1Dist_3"]""")
                district14 = district14.text
            except:
                pass
            try:
                state18 = self.driver.find_element_by_xpath(
                    """// *[ @ id = "ContentPlaceHolder1_GVWBranchDetails_lblb1State_3"]""")
                state18 = state18.text
            except:
                pass

            try:
                pin13 = self.driver.find_element_by_xpath(
                    """// *[ @ id = "ContentPlaceHolder1_GVWBranchDetails_lblb1Pin_3"]""")
                pin13 = pin13.text
            except:
                pass
            try:
                phoneNumber14 = self.driver.find_element_by_xpath(
                    """//*[@id="ContentPlaceHolder1_GVWBranchDetails_lblb1Phone_3"]""")
                phoneNumber14 = phoneNumber14.text
            except:
                pass
            try:
                mobileNumber14 = self.driver.find_element_by_xpath(
                    """//*[@id="ContentPlaceHolder1_GVWBranchDetails_lblb1Mobile_3"]""")
                mobileNumber14 = mobileNumber14.text
            except:
                pass
            try:
                email14 = self.driver.find_element_by_xpath(
                    """//*[@id="ContentPlaceHolder1_GVWBranchDetails_lblb1Email_3"]""")
                email14 = email14.text
            except:
                pass

            try:
                branchIncharge14 = self.driver.find_element_by_xpath(
                    """//*[@id="ContentPlaceHolder1_GVWBranchDetails_lblmemberInChargeOfHo_4"]""")
                branchIncharge14 = branchIncharge14.text
            except:
                pass
            try:
                address125 = self.driver.find_element_by_xpath(
                    """//*[@id="ContentPlaceHolder1_GVWBranchDetails_lblb1Add1_4"]""")
                address125 = address125.text
                address126 = self.driver.find_element_by_xpath(
                    """// *[ @ id = "ContentPlaceHolder1_GVWBranchDetails_lblb1Add2_4"]""")
                address126 = address126.text
                address127 = self.driver.find_element_by_xpath(
                    """//*[@id="ContentPlaceHolder1_GVWBranchDetails_lblb1Add3_4"]""")
                address127 = address127.text

                address128 = address125 + " " + address126 + " " + address127
                address128 = address128.replace('"', '')
            except:
                pass
            try:
                city15 = self.driver.find_element_by_xpath(
                    """//*[@id="ContentPlaceHolder1_GVWBranchDetails_lblb1City_4"]""")
                city15 = city15.text
            except:
                pass
            try:
                district15 = self.driver.find_element_by_xpath(
                    """//*[@id="ContentPlaceHolder1_GVWBranchDetails_lblb1Dist_4"]""")
                district15 = district15.text
            except:
                pass
            try:
                state19 = self.driver.find_element_by_xpath(
                    """// *[ @ id = "ContentPlaceHolder1_GVWBranchDetails_lblb1State_4"]""")
                state19 = state19.text
            except:
                pass

            try:
                pin14 = self.driver.find_element_by_xpath(
                    """// *[ @ id = "ContentPlaceHolder1_GVWBranchDetails_lblb1Pin_4"]""")
                pin14 = pin14.text
            except:
                pass
            try:
                phoneNumber15 = self.driver.find_element_by_xpath(
                    """//*[@id="ContentPlaceHolder1_GVWBranchDetails_lblb1Phone_4"]""")
                phoneNumber15 = phoneNumber15.text
            except:
                pass
            try:
                mobileNumber15 = self.driver.find_element_by_xpath(
                    """//*[@id="ContentPlaceHolder1_GVWBranchDetails_lblb1Mobile_4"]""")
                mobileNumber15 = mobileNumber15.text
            except:
                pass
            try:
                email15 = self.driver.find_element_by_xpath(
                    """//*[@id="ContentPlaceHolder1_GVWBranchDetails_lblb1Email_4"]""")
                email15 = email15.text
            except:
                pass

            ##Member details information

            try:
                serialNumbermember13 = self.driver.find_element_by_xpath(
                    """//*[@id="ContentPlaceHolder1_GVWMemberDetails"]/tbody/tr[2]/td[1]""")
                serialNumbermember13 = serialNumbermember13.text
            except:
                pass

            try:
                memberNumber13 = self.driver.find_element_by_xpath(
                    """// *[ @ id = "ContentPlaceHolder1_GVWMemberDetails_lblmemNo_0"]""")
                memberNumber13 = memberNumber13.text
            except:
                pass

            try:
                memberName13 = self.driver.find_element_by_xpath(
                    """//*[@id="ContentPlaceHolder1_GVWMemberDetails_lblmemName_0"]""")
                memberName13 = memberName13.text
            except:
                pass

            try:
                addressmember13 = self.driver.find_element_by_xpath(
                    """//*[@id="ContentPlaceHolder1_GVWMemberDetails_lblmAdd1_0"]""")
                addressmember13 = addressmember13.text
            except:
                pass
            try:
                citymember13 = self.driver.find_element_by_xpath(
                    """// *[ @ id = "ContentPlaceHolder1_GVWMemberDetails_lblcity_0"]""")
                citymember13 = citymember13.text
            except:
                pass
            try:
                pinmember13 = self.driver.find_element_by_xpath(
                    """//*[@id="ContentPlaceHolder1_GVWMemberDetails_lblPin_0"]""")
                pinmember13 = pinmember13.text
            except:
                pass

            try:
                statemember13 = self.driver.find_element_by_xpath(
                    """// *[ @ id = "ContentPlaceHolder1_GVWMemberDetails_lblState_0"]""")
                statemember13 = statemember13.text
            except:
                pass

            try:
                serialNumbermember14 = self.driver.find_element_by_xpath(
                    """//*[@id="ContentPlaceHolder1_GVWMemberDetails"]/tbody/tr[3]/td[1]""")
                serialNumbermember14 = serialNumbermember14.text
            except:
                pass

            try:
                memberNumber14 = self.driver.find_element_by_xpath(
                    """// *[ @ id = "ContentPlaceHolder1_GVWMemberDetails_lblmemNo_1"]""")
                memberNumber14 = memberNumber14.text
            except:
                pass

            try:
                memberName14 = self.driver.find_element_by_xpath(
                    """//*[@id="ContentPlaceHolder1_GVWMemberDetails_lblmemName_1"]""")
                memberName14 = memberName14.text
            except:
                pass

            try:
                addressmember14 = self.driver.find_element_by_xpath(
                    """//*[@id="ContentPlaceHolder1_GVWMemberDetails_lblmAdd1_1"]""")
                addressmember14 = addressmember14.text
            except:
                pass
            try:
                citymember14 = self.driver.find_element_by_xpath(
                    """// *[ @ id = "ContentPlaceHolder1_GVWMemberDetails_lblcity_1"]""")
                citymember14 = citymember14.text
            except:
                pass
            try:
                pinmember14 = self.driver.find_element_by_xpath(
                    """// *[ @ id = "ContentPlaceHolder1_GVWMemberDetails_lblPin_1"]""")
                pinmember14 = pinmember14.text
            except:
                pass

            try:
                statemember14 = self.driver.find_element_by_xpath(
                    """// *[ @ id = "ContentPlaceHolder1_GVWMemberDetails_lblState_1"]""")
                statemember14 = statemember14.text
            except:
                pass

            try:
                serialNumbermember15 = self.driver.find_element_by_xpath(
                    """//*[@id="ContentPlaceHolder1_GVWMemberDetails"]/tbody/tr[4]/td[1]""")
                serialNumbermember15 = serialNumbermember15.text
            except:
                pass

            try:
                memberNumber15 = self.driver.find_element_by_xpath(
                    """// *[ @ id = "ContentPlaceHolder1_GVWMemberDetails_lblmemNo_2"]""")
                memberNumber15 = memberNumber15.text
            except:
                pass

            try:
                memberName15 = self.driver.find_element_by_xpath(
                    """//*[@id="ContentPlaceHolder1_GVWMemberDetails_lblmemName_2"]""")
                memberName15 = memberName15.text
            except:
                pass

            try:
                addressmember15 = self.driver.find_element_by_xpath(
                    """//*[@id="ContentPlaceHolder1_GVWMemberDetails_lblmAdd1_2"]""")
                addressmember15 = addressmember15.text
            except:
                pass
            try:
                citymember15 = self.driver.find_element_by_xpath(
                    """// *[ @ id = "ContentPlaceHolder1_GVWMemberDetails_lblcity_2"]""")
                citymember15 = citymember15.text
            except:
                pass
            try:
                pinmember15 = self.driver.find_element_by_xpath(
                    """// *[ @ id = "ContentPlaceHolder1_GVWMemberDetails_lblPin_2"]""")
                pinmember15 = pinmember15.text
            except:
                pass

            try:
                statemember15 = self.driver.find_element_by_xpath(
                    """// *[ @ id = "ContentPlaceHolder1_GVWMemberDetails_lblState_2"]""")
                statemember15 = statemember15.text
            except:
                pass

            try:
                serialNumbermember15 = self.driver.find_element_by_xpath(
                    """//*[@id="ContentPlaceHolder1_GVWMemberDetails"]/tbody/tr[5]/td[1]""")
                serialNumbermember15 = serialNumbermember15.text
            except:
                pass

            try:
                memberNumber15 = self.driver.find_element_by_xpath(
                    """// *[ @ id = "ContentPlaceHolder1_GVWMemberDetails_lblmemNo_3"]""")
                memberNumber15 = memberNumber15.text
            except:
                pass

            try:
                memberName15 = self.driver.find_element_by_xpath(
                    """//*[@id="ContentPlaceHolder1_GVWMemberDetails_lblmemName_3"]""")
                memberName15 = memberName15.text
            except:
                pass

            try:
                addressmember15 = self.driver.find_element_by_xpath(
                    """//*[@id="ContentPlaceHolder1_GVWMemberDetails_lblmAdd1_3"]""")
                addressmember15 = addressmember15.text
            except:
                pass
            try:
                citymember15 = self.driver.find_element_by_xpath(
                    """// *[ @ id = "ContentPlaceHolder1_GVWMemberDetails_lblcity_3"]""")
                citymember15 = citymember15.text
            except:
                pass
            try:
                pinmember15 = self.driver.find_element_by_xpath(
                    """// *[ @ id = "ContentPlaceHolder1_GVWMemberDetails_lblPin_3"]""")
                pinmember15 = pinmember15.text
            except:
                pass

            try:
                statemember15 = self.driver.find_element_by_xpath(
                    """// *[ @ id = "ContentPlaceHolder1_GVWMemberDetails_lblState_3"]""")
                statemember15 = statemember15.text
            except:
                pass

            try:
                serialNumbermember16 = self.driver.find_element_by_xpath(
                    """//*[@id="ContentPlaceHolder1_GVWMemberDetails"]/tbody/tr[6]/td[1]""")
                serialNumbermember16 = serialNumbermember16.text
            except:
                pass

            try:
                memberNumber16 = self.driver.find_element_by_xpath(
                    """// *[ @ id = "ContentPlaceHolder1_GVWMemberDetails_lblmemNo_4"]""")
                memberNumber16 = memberNumber16.text
            except:
                pass

            try:
                memberName16 = self.driver.find_element_by_xpath(
                    """//*[@id="ContentPlaceHolder1_GVWMemberDetails_lblmemName_4"]""")
                memberName16 = memberName16.text
            except:
                pass

            try:
                addressmember16 = self.driver.find_element_by_xpath(
                    """//*[@id="ContentPlaceHolder1_GVWMemberDetails_lblmAdd1_4"]""")
                addressmember16 = addressmember16.text
            except:
                pass
            try:
                citymember16 = self.driver.find_element_by_xpath(
                    """// *[ @ id = "ContentPlaceHolder1_GVWMemberDetails_lblcity_4"]""")
                citymember16 = citymember16.text
            except:
                pass
            try:
                pinmember16 = self.driver.find_element_by_xpath(
                    """// *[ @ id = "ContentPlaceHolder1_GVWMemberDetails_lblPin_4"]""")
                pinmember16 = pinmember16.text
            except:
                pass

            try:
                statemember16 = self.driver.find_element_by_xpath(
                    """// *[ @ id = "ContentPlaceHolder1_GVWMemberDetails_lblState_4"]""")
                statemember16 = statemember16.text
            except:
                pass
            try:
                serialNumbermember16 = self.driver.find_element_by_xpath(
                    """//*[@id="ContentPlaceHolder1_GVWMemberDetails"]/tbody/tr[6]/td[1]""")
                serialNumbermember16 = serialNumbermember16.text
            except:
                pass

            try:
                memberNumber16 = self.driver.find_element_by_xpath(
                    """// *[ @ id = "ContentPlaceHolder1_GVWMemberDetails_lblmemNo_5"]""")
                memberNumber16 = memberNumber16.text
            except:
                pass

            try:
                memberName16 = self.driver.find_element_by_xpath(
                    """//*[@id="ContentPlaceHolder1_GVWMemberDetails_lblmemName_5"]""")
                memberName16 = memberName16.text
            except:
                pass

            try:
                addressmember16 = self.driver.find_element_by_xpath(
                    """//*[@id="ContentPlaceHolder1_GVWMemberDetails_lblmAdd1_5"]""")
                addressmember16 = addressmember16.text
            except:
                pass
            try:
                citymember16 = self.driver.find_element_by_xpath(
                    """// *[ @ id = "ContentPlaceHolder1_GVWMemberDetails_lblcity_5"]""")
                citymember16 = citymember16.text
            except:
                pass
            try:
                pinmember16 = self.driver.find_element_by_xpath(
                    """// *[ @ id = "ContentPlaceHolder1_GVWMemberDetails_lblPin_5"]""")
                pinmember16 = pinmember16.text
            except:
                pass

            try:
                statemember16 = self.driver.find_element_by_xpath(
                    """// *[ @ id = "ContentPlaceHolder1_GVWMemberDetails_lblState_5"]""")
                statemember16 = statemember16.text
            except:
                pass


            try:
                if len(firmNumber71) > 0:
                    Be1 = {}
                    Be1["memberNumber"] = memberNumber67
                    Be1["serialNumber"] = serialNumber1
                    Be1["firmNumber"] = firmNumber71
                    Be1["firmName"] = firmName
                    Be1["firmType"] = firmType
                    Be1["constitutionDate"] = constitutionDate
                    Be1["deedDate"] = deedDate
                    Be1["region"] = region
                    Be1["country"] = country
                    Be1["state"] = state
                else:
                    Be1 = {}
            except:
                Be1 = {}


            try:
                if len(firmNumber72) > 0:
                    Be2 = {}
                    Be2["memberNumber"] = memberNumber67
                    Be2["serialNumber"] = serialNumber2
                    Be2["firmNumber"] = firmNumber72
                    Be2["firmName"] = firmName1
                    Be2["firmType"] = firmType1
                    Be2["constitutionDate"] = constitutionDate1
                    Be2["deedDate"] = deedDate1
                    Be2["region"] = region1
                    Be2["country"] = country1
                    Be2["state"] = state1
                else:
                    Be2 = {}
            except:
                Be2 = {}

            try:

                if len(firmNumber73) > 0:
                    Be3 = {}
                    Be3["memberNumber"] = memberNumber67
                    Be3["serialNumber"] = serialNumber3
                    Be3["firmNumber"] = firmNumber73
                    Be3["firmName"] = firmName2
                    Be3["firmType"] = firmType2
                    Be3["constitutionDate"] = constitutionDate2
                    Be3["deedDate"] = deedDate2
                    Be3["region"] = region2
                    Be3["country"] = country2
                    Be3["state"] = state2
                else:
                    Be3 = {}
            except:
                Be3 = {}


            try:
                if len(firmNumber71) > 0:
                    Ne1 = {}
                    Ne1["firmNumber"] = firmNumber71
                    Ne1["reconstitutionDate"] = reonstitutionDate
                    Ne1["lDate"] = lDate59
                    Ne1["address"] = address8
                    Ne1["telephoneMobileNumber"] = telephoneMobileNumber
                    Ne1["mobileNumber"] = mobileNumberh
                    Ne1["emailId"] = emailIdOfficial
                    Ne1["state"] = state3
                    Ne1["city"] = city
                    Ne1["district"] = district
                    Ne1["pincode"] = pincode111
                else:
                    Ne1 = {}
            except:
                Ne1 = {}

            try:
                if len(firmNumber72) > 0:
                    Ne2 = {}
                    Ne2["firmNumber"] = firmNumber72
                    Ne2["reconstitutionDate"] = reonstitutionDate1
                    Ne2["lDate"] = lDate1
                    Ne2["address"] = address74
                    Ne2["telephoneMobileNumber"] = telephoneMobileNumber1
                    Ne2["mobileNumber"] = mobileNumberh1
                    Ne2["emailId"] = emailIdOfficial1
                    Ne2["state"] = state44
                    Ne2["city"] = city44
                    Ne2["district"] = district44
                    Ne2["pincode"] = pincode112


                else:
                    Ne2 = {}
            except:
                Ne2 = {}

            try:
                if len(firmNumber73) > 0:
                    Ne3 = {}
                    Ne3["firmNumber"] = firmNumber73
                    Ne3["reconstitutionDate"] = reonstitutionDate2
                    Ne3["lDate"] = lDate2
                    Ne3["address"] = address83
                    Ne3["telephoneMobileNumber"] = telephoneMobileNumber2
                    Ne3["mobileNumber"] = mobileNumberh2
                    Ne3["emailId"] = emailIdOfficial2
                    Ne3["state"] = state80
                    Ne3["city"] = city80
                    Ne3["district"] = district80
                    Ne3["pincode"] = pincode113
                else:
                    Ne3 = {}
            except:
                Ne3 = {}

            try:
                if len(branchIncharge) > 0:
                    Ge1 = {}
                    Ge1["firmNumber"] = firmNumber71
                    Ge1["branchIncharge"] = branchIncharge
                    Ge1["address"] = address96
                    Ge1["city"] = city1
                    Ge1["district"] = district1
                    Ge1["state"] = state4
                    Ge1["pin"] = pin
                    Ge1["phoneNumber"] = phoneNumber
                    Ge1["mobileNumber"] = mobileNumber
                    Ge1["email"] = email1
                else:
                    Ge1 = {}
            except:
                Ge1 = {}

            try:
                if len(branchIncharge1) > 0:
                    Ge2 = {}
                    Ge2["firmNumber"] = firmNumber71
                    Ge2["branchIncharge"] = branchIncharge1
                    Ge2["address"] = address114
                    Ge2["city"] = city2
                    Ge2["district"] = district2
                    Ge2["state"] = state5
                    Ge2["pin"] = pin1
                    Ge2["phoneNumber"] = phoneNumber1
                    Ge2["mobileNumber"] = mobileNumber1
                    Ge2["email"] = email2
                else:
                    Ge2 = {}
            except:
                Ge2 = {}

            try:

                if len(branchIncharge2) > 0:
                    Ge3 = {}
                    Ge3["firmNumber"] = firmNumber71
                    Ge3["branchIncharge"] = branchIncharge2
                    Ge3["address"] = address104
                    Ge3["city"] = city3
                    Ge3["district"] = district3
                    Ge3["state"] = state6
                    Ge3["pin"] = pin2
                    Ge3["phoneNumber"] = phoneNumber2
                    Ge3["mobileNumber"] = mobileNumber2
                    Ge3["email"] = email3
                else:
                    Ge3 = {}
            except:
                Ge3 = {}

            try:
                if len(branchIncharge3) > 0:
                    Ge4 = {}
                    Ge4["firmNumber"] = firmNumber71
                    Ge4["branchIncharge"] = branchIncharge3
                    Ge4["address"] = address214
                    Ge4["city"] = city4
                    Ge4["district"] = district4
                    Ge4["state"] = state7
                    Ge4["pin"] = pin3
                    Ge4["phoneNumber"] = phoneNumber3
                    Ge4["mobileNumber"] = mobileNumber3
                    Ge4["email"] = email4
                else:
                    Ge4 = {}
            except:
                Ge4 = {}

            try:
                if len(branchIncharge4) > 0:
                    Ge5 = {}
                    Ge5["firmNumber"] = firmNumber71
                    Ge5["branchIncharge"] = branchIncharge4
                    Ge5["address"] = address321
                    Ge5["city"] = city5
                    Ge5["district"] = district5
                    Ge5["state"] = state8
                    Ge5["pin"] = pin4
                    Ge5["phoneNumber"] = phoneNumber4
                    Ge5["mobileNumber"] = mobileNumber4
                    Ge5["email"] = email5
                else:
                    Ge5 = {}
            except:
                Ge5 = {}

            try:
                if len(branchIncharge5) > 0:
                    Ge6 = {}
                    Ge6["firmNumber"] = firmNumber72
                    Ge6["branchIncharge"] = branchIncharge5
                    Ge6["address"] = address52
                    Ge6["city"] = city6
                    Ge6["district"] = district6
                    Ge6["state"] = state11
                    Ge6["pin"] = pin5
                    Ge6["phoneNumber"] = phoneNumber5
                    Ge6["mobileNumber"] = mobileNumber5
                    Ge6["email"] = email6
                else:
                    Ge6 = {}
            except:
                Ge6 = {}

            try:
                if len(branchIncharge6) > 0:
                    Ge7 = {}
                    Ge7["firmNumber"] = firmNumber72
                    Ge7["branchIncharge"] = branchIncharge6
                    Ge7["address"] = address134
                    Ge7["city"] = city7
                    Ge7["district"] = district7
                    Ge7["state"] = state12
                    Ge7["pin"] = pin6
                    Ge7["phoneNumber"] = phoneNumber7
                    Ge7["mobileNumber"] = mobileNumber7
                    Ge7["email"] = email7
                else:
                    Ge7 = {}
            except:
                Ge7 = {}

            try:

                if len(branchIncharge7) > 0:
                    Ge8 = {}
                    Ge8["firmNumber"] = firmNumber72
                    Ge8["branchIncharge"] = branchIncharge7
                    Ge8["address"] = address144
                    Ge8["city"] = city8
                    Ge8["district"] = district8
                    Ge8["state"] = state13
                    Ge8["pin"] = pin7
                    Ge8["phoneNumber"] = phoneNumber8
                    Ge8["mobileNumber"] = mobileNumber8
                    Ge8["email"] = email8
                else:
                    Ge8 = {}
            except:
                Ge8 = {}

            try:
                if len(branchIncharge8) > 0:
                    Ge9 = {}
                    Ge9["firmNumber"] = firmNumber72
                    Ge9["branchIncharge"] = branchIncharge8
                    Ge9["address"] = address214
                    Ge9["city"] = city9
                    Ge9["district"] = district9
                    Ge9["state"] = state14
                    Ge9["pin"] = pin8
                    Ge9["phoneNumber"] = phoneNumber9
                    Ge9["mobileNumber"] = mobileNumber9
                    Ge9["email"] = email9
                else:
                    Ge9 = {}
            except:
                Ge9 = {}


            try:
                if len(branchIncharge9) > 0:
                    Ge10 = {}
                    Ge10["firmNumber"] = firmNumber72
                    Ge10["branchIncharge"] = branchIncharge9
                    Ge10["address"] = address254
                    Ge10["city"] = city10
                    Ge10["district"] = district10
                    Ge10["state"] = state15
                    Ge10["pin"] = pin9
                    Ge10["phoneNumber"] = phoneNumber10
                    Ge10["mobileNumber"] = mobileNumber10
                    Ge10["email"] = email10
                else:
                    Ge10 = {}
            except:
                Ge10 = {}

            try:
                if len(branchIncharge10) > 0:
                    Ge11 = {}
                    Ge11["firmNumber"] = firmNumber73
                    Ge11["branchIncharge"] = branchIncharge10
                    Ge11["address"] = address904
                    Ge11["city"] = city11
                    Ge11["district"] = district11
                    Ge11["state"] = state16
                    Ge11["pin"] = pin10
                    Ge11["phoneNumber"] = phoneNumber11
                    Ge11["mobileNumber"] = mobileNumber11
                    Ge11["email"] = email11
                else:
                    Ge11 = {}
            except:
                Ge11 = {}

            try:
                if len(branchIncharge11) > 0:
                    Ge12 = {}
                    Ge12["firmNumber"] = firmNumber73
                    Ge12["branchIncharge"] = branchIncharge11
                    Ge12["address"] = address164
                    Ge12["city"] = city12
                    Ge12["district"] = district12
                    Ge12["state"] = state17
                    Ge12["pin"] = pin11
                    Ge12["phoneNumber"] = phoneNumber12
                    Ge12["mobileNumber"] = mobileNumber12
                    Ge12["email"] = email12
                else:
                    Ge12 = {}
            except:
                Ge12 = {}

            try:

                if len(branchIncharge12) > 0:
                    Ge13 = {}
                    Ge13["firmNumber"] = firmNumber73
                    Ge13["branchIncharge"] = branchIncharge12
                    Ge13["address"] = address174
                    Ge13["city"] = city13
                    Ge13["district"] = district13
                    Ge13["state"] = state17
                    Ge13["pin"] = pin12
                    Ge13["phoneNumber"] = phoneNumber13
                    Ge13["mobileNumber"] = mobileNumber13
                    Ge13["email"] = email13
                else:
                    Ge13 = {}
            except:
                Ge13 = {}

            try:

                if len(branchIncharge13) > 0:
                    Ge14 = {}
                    Ge14["firmNumber"] = firmNumber73
                    Ge14["branchIncharge"] = branchIncharge13
                    Ge14["address"] = address124
                    Ge14["city"] = city14
                    Ge14["district"] = district14
                    Ge14["state"] = state18
                    Ge14["pin"] = pin13
                    Ge14["phoneNumber"] = phoneNumber14
                    Ge14["mobileNumber"] = mobileNumber14
                    Ge14["email"] = email14
                else:
                    Ge14 = {}
            except:
                Ge14 = {}

            try:

                if len(branchIncharge14) > 0:
                    Ge15 = {}
                    Ge15["firmNumber"] = firmNumber73
                    Ge15["branchIncharge"] = branchIncharge14
                    Ge15["address"] = address128
                    Ge15["city"] = city15
                    Ge15["district"] = district15
                    Ge15["state"] = state19
                    Ge15["pin"] = pin14
                    Ge15["phoneNumber"] = phoneNumber15
                    Ge15["mobileNumber"] = mobileNumber15
                    Ge15["email"] = email15
                else:
                    Ge15 = {}
            except:
                Ge15 = {}

            try:

                if len(memberNumber) > 0:
                    Me1 = {}
                    Me1["memberNumber"] = memberNumber
                    Me1["firmNumber"] = firmNumber71
                    Me1["serialNumber"] = serialNumbermember
                    Me1["memberName"] = memberName
                    Me1["address"] = addressmember
                    Me1["city"] = citymember
                    Me1["pin"] = pinmember
                    Me1["state"] = statemember
                else:
                    Me1 = {}
            except:
                Me1 = {}

            try:
                if len(memberNumber1) > 0:
                    Me2 = {}
                    Me2["memberNumber"] = memberNumber1
                    Me2["firmNumber"] = firmNumber71
                    Me2["serialNumber"] = serialNumbermember1
                    Me2["memberName"] = memberName1
                    Me2["address"] = addressmember1
                    Me2["city"] = citymember1
                    Me2["pin"] = pinmember1
                    Me2["state"] = statemember1
                else:
                    Me2 = {}
            except:
                Me2 = {}

            try:
                if len(memberNumber2) > 0:
                    Me3 = {}
                    Me3["memberNumber"] = memberNumber2
                    Me3["firmNumber"] = firmNumber71
                    Me3["serialNumber"] = serialNumbermember2
                    Me3["memberName"] = memberName2
                    Me3["address"] = addressmember2
                    Me3["city"] = citymember2
                    Me3["pin"] = pinmember2
                    Me3["state"] = statemember2
                else:
                    Me3 = {}
            except:
                Me3 = {}

            try:
                if len(memberNumber3) > 0:
                    Me4 = {}
                    Me4["memberNumber"] = memberNumber3
                    Me4["firmNumber"] = firmNumber71
                    Me4["serialNumber"] = serialNumbermember3
                    Me4["memberName"] = memberName3
                    Me4["address"] = addressmember3
                    Me4["city"] = citymember3
                    Me4["pin"] = pinmember3
                    Me4["state"] = statemember3
                else:
                    Me4 = {}
            except:
                Me4 = {}

            try:
                if len(memberNumber4) > 0:
                    Me5 = {}
                    Me5["memberNumber"] = memberNumber4
                    Me5["firmNumber"] = firmNumber71
                    Me5["serialNumber"] = serialNumbermember4
                    Me5["memberName"] = memberName4
                    Me5["address"] = addressmember4
                    Me5["city"] = citymember4
                    Me5["pin"] = pinmember4
                    Me5["state"] = statemember4
                else:
                    Me5 = {}
            except:
                Me5 = {}

            try:
                if len(memberNumber5) > 0:
                    Me6 = {}
                    Me6["memberNumber"] = memberNumber5
                    Me6["firmNumber"] = firmNumber71
                    Me6["serialNumber"] = serialNumbermember5
                    Me6["memberName"] = memberName5
                    Me6["address"] = addressmember5
                    Me6["city"] = citymember5
                    Me6["pin"] = pinmember5
                    Me6["state"] = statemember5
                else:
                    Me6 = {}
            except:
                Me6 = {}

            try:
                if len(memberNumber6) > 0:
                    Me7 = {}
                    Me7["memberNumber"] = memberNumber6
                    Me7["firmNumber"] = firmNumber71
                    Me7["serialNumber"] = serialNumbermember6
                    Me7["memberName"] = memberName6
                    Me7["address"] = addressmember6
                    Me7["city"] = citymember6
                    Me7["pin"] = pinmember6
                    Me7["state"] = statemember6
                else:
                    Me7 = {}
            except:
                Me7 = {}

            try:
                if len(memberNumber7) > 0:
                    Me8 = {}
                    Me8["memberNumber"] = memberNumber7
                    Me8["firmNumber"] = firmNumber71
                    Me8["serialNumber"] = serialNumbermember7
                    Me8["memberName"] = memberName7
                    Me8["address"] = addressmember7
                    Me8["city"] = citymember7
                    Me8["pin"] = pinmember7
                    Me8["state"] = statemember7
                else:
                    Me8 = {}
            except:
                Me8 = {}

            try:
                if len(memberNumber9) > 0:
                    Me9 = {}
                    Me9["memberNumber"] = memberNumber9
                    Me9["firmNumber"] = firmNumber72
                    Me9["serialNumber"] = serialNumbermember9
                    Me9["memberName"] = memberName9
                    Me9["address"] = addressmember9
                    Me9["city"] = citymember9
                    Me9["pin"] = pinmember9
                    Me9["state"] = statemember9
                else:
                    Me9 = {}
            except:
                Me9 = {}

            try:
                if len(memberNumber10) > 0:
                    Me10 = {}
                    Me10["memberNumber"] = memberNumber10
                    Me10["firmNumber"] = firmNumber72
                    Me10["serialNumber"] = serialNumbermember10
                    Me10["memberName"] = memberName10
                    Me10["address"] = addressmember10
                    Me10["city"] = citymember10
                    Me10["pin"] = pinmember10
                    Me10["state"] = statemember10
                else:
                    Me10 = {}
            except:
                Me10 = {}

            try:
                if len(memberNumber11) > 0:
                    Me11 = {}
                    Me11["memberNumber"] = memberNumber11
                    Me11["firmNumber"] = firmNumber72
                    Me11["serialNumber"] = serialNumbermember11
                    Me11["memberName"] = memberName11
                    Me11["address"] = addressmember11
                    Me11["city"] = citymember11
                    Me11["pin"] = pinmember11
                    Me11["state"] = statemember11
                else:
                    Me11 = {}
            except:
                Me11 = {}

            try:
                if len(memberNumber12) > 0:
                    Me12 = {}
                    Me12["memberNumber"] = memberNumber12
                    Me12["firmNumber"] = firmNumber72
                    Me12["serialNumber"] = serialNumbermember12
                    Me12["memberName"] = memberName12
                    Me12["address"] = addressmember12
                    Me12["city"] = citymember12
                    Me12["pin"] = pinmember12
                    Me12["state"] = statemember12
                else:
                    Me12 = {}
            except:
                Me12 = {}

            try:
                if len(memberNumber13) > 0:
                    Me13 = {}
                    Me13["memberNumber"] = memberNumber13
                    Me13["firmNumber"] = firmNumber73
                    Me13["serialNumber"] = serialNumbermember13
                    Me13["memberName"] = memberName13
                    Me13["address"] = addressmember13
                    Me13["city"] = citymember13
                    Me13["pin"] = pinmember13
                    Me13["state"] = statemember13
                else:
                    Me13 = {}
            except:
                Me13 = {}

            try:

                if len(memberNumber14) > 0:
                    Me14 = {}
                    Me14["memberNumber"] = memberNumber14
                    Me14["firmNumber"] = firmNumber73
                    Me14["serialNumber"] = serialNumbermember14
                    Me14["memberName"] = memberName14
                    Me14["address"] = addressmember14
                    Me14["city"] = citymember14
                    Me14["pin"] = pinmember14
                    Me14["state"] = statemember14
                else:
                    Me14 = {}
            except:
                Me14 = {}

            try:

                if len(memberNumber15) > 0:
                    Me15 = {}
                    Me15["memberNumber"] = memberNumber15
                    Me15["firmNumber"] = firmNumber73
                    Me15["serialNumber"] = serialNumbermember15
                    Me15["memberName"] = memberName15
                    Me15["address"] = addressmember15
                    Me15["city"] = citymember15
                    Me15["pin"] = pinmember15
                    Me15["state"] = statemember15
                else:
                    Me15 = {}
            except:
                Me15 = {}
            try:

                if len(memberNumber16) > 0:
                    Me16 = {}
                    Me16["memberNumber"] = memberNumber16
                    Me16["firmNumber"] = firmNumber73
                    Me16["serialNumber"] = serialNumbermember16
                    Me16["memberName"] = memberName16
                    Me16["address"] = addressmember16
                    Me16["city"] = citymember16
                    Me16["pin"] = pinmember16
                    Me16["state"] = statemember16
                else:
                    Me16 = {}
            except:
                Me16 = {}


            dic = {}
            dic["serialNumber"] = serialNumber
            dic["memberNumber"] = memberNumber67
            dic["memberName"] = memberName900
            dic["category"] = category
            dic["aquali"] = aquali
            dic["validDate"] = validDate
            dic["address"] = address
            dic["phone"] = phone
            dic["email"] = email
            dic["certificateOfPracticeAs"] = certificateOfPracticeAs
            dic["indexNumber"] = indexNumber
            a = [Be1, Be2, Be3]
            dic["firmDetails"] = [d for d in a if any(d.values())]
            b = [Ne1, Ne2, Ne3]
            dic["headOfficeAddress"] = [d for d in b if any(d.values())]
            c = [Ge1, Ge2, Ge3, Ge4, Ge5, Ge6, Ge7, Ge8, Ge9, Ge10, Ge11, Ge12, Ge13, Ge14, Ge15]
            dic["branchAddress"] = [d for d in c if any(d.values())]
            d = [Me1, Me2, Me3, Me4, Me5, Me6, Me7, Me8, Me9, Me10, Me11,Me12, Me13, Me14, Me15, Me16]
            dic["memberDetails"] = [d for d in d if any(d.values())]
            self.logStatus("info", "Scrapping completed", self.takeScreenshot())
            message = "Successfully Completed."
            code = "SRC001"
            dic = {"data": dic, "responseCode": code, "responseMessage": message}
            return dic

    def ICMAI_response(self,licenseNumber):

        dic = {}
        try:
            self.logStatus("info", "Opening webpage")
            dic = self.generate_icmai(licenseNumber)
        except Exception as e:
            print(e)
            self.logStatus("critical", "timeout error retrying")
            try:
                self.logStatus("info", "Opening webpage")
                dic = self.generate_icmai(licenseNumber)
            except Exception as e:
                print(e)
                self.logStatus("critical", "timeout error retrying")
                try:
                    self.logStatus("info", "Opening webpage")
                    dic = self.generate_icmai(licenseNumber)
                except Exception as e:
                    print(e)
                    self.logStatus("critical", "no data found")

                    message = 'No Information Found.'
                    code = 'ENI004'

                    dic = {'data': 'null', 'responseCode': code, 'responseMessage': message}
                    self.logStatus("info", "No Info Found")

        return dic




#if __name__ == '__main__':

 #   v = ICMAI(refid="testing2", env = 'prod')
  #  data = v.ICMAI_response(licenseNumber = '22200')
   # print(data)

