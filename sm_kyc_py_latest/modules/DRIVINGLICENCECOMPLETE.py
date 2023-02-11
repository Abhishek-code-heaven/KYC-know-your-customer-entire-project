import io
import json
import os
import sys
import time
import uuid
from pprint import pprint

import boto3
import pandas as pd
from botocore.exceptions import ClientError
from google.cloud import vision
from selenium import webdriver

from modules.db import DB
from modules.utils import GcpOcr
from datetime import datetime
#from webdriver_manager.chrome import ChromeDriverManager

class DrivingLicenseVerification:

    def __init__(self, license_number, dob, refid, env='prod'):
        date_obj = datetime.strptime(dob, '%d-%b-%Y')
        dob = date_obj.strftime('%d-%m-%Y')
        os.environ[
            "GOOGLE_APPLICATION_CREDENTIALS"] = "vision_api_token.json"

        self.client = vision.ImageAnnotatorClient()
        options = webdriver.ChromeOptions()
        options.add_experimental_option("excludeSwitches", ['enable-automation'])
        options.add_argument("--incognito")
        options.add_argument("--headless")
        options.headless = True
        options.add_argument("--disable-extension")
        options.add_argument("no-sandbox")
        options.add_argument("--disable-extensions")

        #self.driver = webdriver.Chrome("/usr/local/bin/chromedriver", options=options)
        self.driver = webdriver.Chrome('/usr/local/bin/chromedriver', options=options)
        self.FILE_NAME = "captcha.png"
        self.FOLDER_PATH = os.getcwd()
        self.license_number = license_number
        #from datetime import datetime
        self.dob = dob
        #print(self.dob)
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
                                 'DrivingLicence', self.env, screenshot)
        print(f"{level}: {message}, screenshot: {screenshot}")

    def driving_scrapper(self, license_number, dob):
        try:
            self.makeDriverDirs()
            self.driver.get("https://parivahan.gov.in/rcdlstatus/?pur_cd=101")
            self.logStatus("info", "Driving Licence page opened", self.takeScreenshot())
        except:

            message = "Unable To Process. Please Reach Out To Support."
            code = "EUP007"
            dict_to_send = {}
            dict_to_send['currentStatus'] = 'null'
            dict_to_send['holderName'] = 'null'
            dict_to_send['issueDate'] = 'null'
            dict_to_send['lastTransaction'] = 'null'
            dict_to_send['oldNewDlNumber'] = 'null'
            dict_to_send['nonTransportFrom'] = 'null'
            dict_to_send['nonTransportTo'] = 'null'
            dict_to_send['transportFrom'] = 'null'
            dict_to_send['transportTo'] = 'null'
            dict_to_send['hazardousValidTill'] = 'null'
            dict_to_send['hillValidTill'] = 'null'
            dict_to_send['classOfVehicleDetails'] = 'null'
            dict_to_send['licenseNumber'] = self.license_number
            date_obj = datetime.strptime(self.dob, '%d-%m-%Y')
            self.dob = date_obj.strftime('%d-%b-%Y')
            dict_to_send['dateOfBirth'] = self.dob
            dict_to_send_final = {'data': dict_to_send, "responseCode": code, "responseMessage": message}
            return dict_to_send_final
            sys.exit()

        date_of_birth = self.driver.find_element_by_id("form_rcdl:tf_dob_input")
        time.sleep(1)
        date_of_birth.send_keys(dob)
        driving_license_number = self.driver.find_element_by_id("form_rcdl:tf_dlNO")
        time.sleep(1)
        driving_license_number.send_keys(license_number)



        #self.driver.find_element_by_id("form_rcdl:rcdl_pnl_header").click()

        time.sleep(2)

        #self.driver.find_element_by_id("form_rcdl:j_idt32:j_idt38").screenshot("captcha.png")
        self.driver.find_element_by_xpath("""/html/body/form/div[1]/div[3]/div[1]/div/div[2]/div[3]/div/div[2]/div/div[2]/table/tbody/tr/td[1]/img""").screenshot('captcha.png')

        with io.open(os.path.join(self.FOLDER_PATH, self.FILE_NAME), 'rb') as image_file:
            content = image_file.read()

        image = vision.types.Image(content=content)
        response = self.client.text_detection(image=image)
        texts = response.text_annotations
        print("wait for output it takes about 30 seconds")
        self.logStatus("info", "Retrying Captcha")
        # print(texts)

        df = pd.DataFrame(columns=['locale', 'description'])

        for text in texts:
            df = df.append(dict(
                locale=text.locale,
                description=text.description
            ),
                ignore_index=True
            )
        # print("this is dataframe", df)
        if not df.empty:
            captcha_text = df.iloc[[0], [1]]

            data = str(captcha_text["description"][0])

            info = "".join(data.split())

            info = info + 'extra'

            # captcha_text=df['description'][0]
            try:
                sname = str(info) + '.png'
                screenshotName = os.path.join(self.screenshotDir, f"{sname}")
                self.driver.find_element_by_xpath("""/html/body/form/div[1]/div[3]/div[1]/div/div[2]/div[3]/div/div[2]/div/div[2]/table/tbody/tr/td[1]/img""").screenshot(screenshotName)
                self.uploadToS3(os.path.join(screenshotName), 'DRIVINGLICENCE/' + sname)
            except:
                pass
            self.driver.find_element_by_xpath('/html/body/form/div[1]/div[3]/div[1]/div/div[2]/div[3]/div/div[2]/div/div[2]/table/tbody/tr/td[3]/input').click()
            self.driver.find_element_by_xpath('/html/body/form/div[1]/div[3]/div[1]/div/div[2]/div[3]/div/div[2]/div/div[2]/table/tbody/tr/td[3]/input').send_keys(info)
            #ip_element = self.driver.find_element_by_id("form_rcdl:j_idt32:CaptchaID")
            #ip_element.send_keys(info)
            time.sleep(1)


        time.sleep(2)

        self.driver.find_element_by_xpath('/html/body/form/div[1]/div[3]/div[1]/div/div[2]/div[4]/div/button[1]/span').click()

        time.sleep(2)
        elements = self.driver.find_elements_by_xpath('.//div[@class = "ui-messages-error ui-corner-all"]')
        # print(len(elements))
        a = None
        # print(elements)
        if len(elements) > 0:
            a = elements[0].text
            # print(a)
        return a

    def generate_response(self):

        a = self.driving_scrapper(self.license_number, self.dob)

        while a == "Verification code does not match.Verification code does not match." or a == "Verification code is missing.Verification code is missing.":

            a = self.driving_scrapper(self.license_number, self.dob)

        answer = []
        next_page_elements = self.driver.find_elements_by_tag_name("td")

        for i in next_page_elements:
            if len(i.text) != 0:
                answer.append(i.text)

        if len(answer) > 1:
            list_of_class_of_vehicle_details_to_send = []
            ind = answer.index("Hill Valid Till:")
            print("this is ind", ind)
            class_of_vehicle_list = answer[ind + 2:]
            print(class_of_vehicle_list)
            if len(class_of_vehicle_list) == 3:
                class_of_vehicle_dict = {"covCategory": class_of_vehicle_list[0],
                                         "classOfVehicle": class_of_vehicle_list[1],
                                         "covIssueDate": class_of_vehicle_list[2]}
                list_of_class_of_vehicle_details_to_send.append(class_of_vehicle_dict)
            elif len(class_of_vehicle_list) == 6:
                class_of_vehicle_dict = {"covCategory": class_of_vehicle_list[0],
                                         "classOfVehicle": class_of_vehicle_list[1],
                                         "covIssueDate": class_of_vehicle_list[2]}
                list_of_class_of_vehicle_details_to_send.append(class_of_vehicle_dict)
                class_of_vehicle_dict = {"covCategory": class_of_vehicle_list[3],
                                         "classOfVehicle": class_of_vehicle_list[4],
                                         "covIssueDate": class_of_vehicle_list[5]}
                list_of_class_of_vehicle_details_to_send.append(class_of_vehicle_dict)
            elif len(class_of_vehicle_list) == 9:
                class_of_vehicle_dict = {"covCategory": class_of_vehicle_list[0],
                                         "classOfVehicle": class_of_vehicle_list[1],
                                         "covIssueDate": class_of_vehicle_list[2]}
                list_of_class_of_vehicle_details_to_send.append(class_of_vehicle_dict)
                class_of_vehicle_dict = {"covCategory": class_of_vehicle_list[3],
                                         "classOfVehicle": class_of_vehicle_list[4],
                                         "covIssueDate": class_of_vehicle_list[5]}
                list_of_class_of_vehicle_details_to_send.append(class_of_vehicle_dict)
                class_of_vehicle_dict = {"covCategory": class_of_vehicle_list[6],
                                         "classOfVehicle": class_of_vehicle_list[7],
                                         "covIssueDate": class_of_vehicle_list[8]}
                list_of_class_of_vehicle_details_to_send.append(class_of_vehicle_dict)
            elif len(class_of_vehicle_list) == 12:
                class_of_vehicle_dict = {"covCategory": class_of_vehicle_list[0],
                                         "classOfVehicle": class_of_vehicle_list[1],
                                         "covIssueDate": class_of_vehicle_list[2]}
                list_of_class_of_vehicle_details_to_send.append(class_of_vehicle_dict)
                class_of_vehicle_dict = {"covCategory": class_of_vehicle_list[3],
                                         "classOfVehicle": class_of_vehicle_list[4],
                                         "covIssueDate": class_of_vehicle_list[5]}
                list_of_class_of_vehicle_details_to_send.append(class_of_vehicle_dict)
                class_of_vehicle_dict = {"covCategory": class_of_vehicle_list[6],
                                         "classOfVehicle": class_of_vehicle_list[7],
                                         "covIssueDate": class_of_vehicle_list[8]}
                list_of_class_of_vehicle_details_to_send.append(class_of_vehicle_dict)
                class_of_vehicle_dict = {"covCategory": class_of_vehicle_list[9],
                                         "classOfVehicle": class_of_vehicle_list[10],
                                         "covIssueDate": class_of_vehicle_list[11]}
                list_of_class_of_vehicle_details_to_send.append(class_of_vehicle_dict)

            current_status = answer[1]
            holders_name = answer[3]
            date_of_issue = answer[5]
            last_transaction_at = answer[7]
            old_new_dlno = answer[9]
            non_transport_valid_from = answer[11]
            non_transport_valid_to = answer[12]
            transport_valid_from = answer[14]
            transport_valid_to = answer[15]
            hazardous_valid_till = answer[17]
            hill_valid_till = answer[19]

            a = transport_valid_from.split(":")
            transport_valid_from = a[1].strip()
            b = transport_valid_to.split(":")
            transport_valid_to = b[1].strip()

            c = non_transport_valid_from.split(":")
            non_transport_valid_from = c[1].strip()
            d = non_transport_valid_to.split(":")
            non_transport_valid_to = d[1].strip()
            message = "Successfully Completed."
            code = "SRC001"
            dict_to_send = {}
            dict_to_send['currentStatus'] = current_status
            dict_to_send['holderName'] = holders_name
            dict_to_send['issueDate'] = date_of_issue
            dict_to_send['lastTransaction'] = last_transaction_at
            dict_to_send['oldNewDlNumber'] = old_new_dlno
            dict_to_send['nonTransportFrom'] = non_transport_valid_from
            dict_to_send['nonTransportTo'] = non_transport_valid_to
            dict_to_send['transportFrom'] = transport_valid_from
            dict_to_send['transportTo'] = transport_valid_to
            dict_to_send['hazardousValidTill'] = hazardous_valid_till
            dict_to_send['hillValidTill'] = hill_valid_till
            dict_to_send['classOfVehicleDetails'] = list_of_class_of_vehicle_details_to_send
            dict_to_send['licenseNumber'] = self.license_number
            date_obj = datetime.strptime(self.dob, '%d-%m-%Y')
            self.dob = date_obj.strftime('%d-%b-%Y')
            dict_to_send['dateOfBirth'] = self.dob
            dict_to_send_final = {'data': dict_to_send, "responseCode": code, "responseMessage": message}
            self.makeDriverDirs()
            self.logStatus("info", "Driving Licence Scapping completed", self.takeScreenshot())
            return dict_to_send_final

        else:
            self.logStatus("info", "No Information found")
            message = "No Information Found."
            code = "ENI004"
            dict_to_send = {}
            dict_to_send['currentStatus'] = 'null'
            dict_to_send['holderName'] = 'null'
            dict_to_send['issueDate'] = 'null'
            dict_to_send['lastTransaction'] = 'null'
            dict_to_send['oldNewDlNumber'] = 'null'
            dict_to_send['nonTransportFrom'] = 'null'
            dict_to_send['nonTransportTo'] = 'null'
            dict_to_send['transportFrom'] = 'null'
            dict_to_send['transportTo'] = 'null'
            dict_to_send['hazardousValidTill'] = 'null'
            dict_to_send['hillValidTill'] = 'null'
            dict_to_send['classOfVehicleDetails'] = 'null'
            dict_to_send['licenseNumber'] = self.license_number
            dict_to_send['dateOfBirth'] = self.dob
            dict_to_send_final = {'data': dict_to_send, "responseCode": code, "responseMessage": message}
            return dict_to_send_final

    def exceptionhandling(self):

        dic = {}
        try:
            self.logStatus("info", "Opening webpage")
            dic = self.generate_response()
        except Exception as e:

            self.logStatus("critical", "Captcha error")
            try:
                self.logStatus("info", "Opening webpage")
                dic = self.generate_response()
            except Exception as e:

                self.logStatus("critical", "Captcha error")
                try:
                    self.logStatus("info", "Opening webpage")
                    dic = self.generate_response()
                except Exception as e:

                    self.logStatus("critical", "no data found")
                    dic = {}
                    message = 'No Information Found.'
                    code = 'ENI004'
                    dic1 = 'null'

                    dic = {'data': dic1, 'responseCode': code, 'responseMessage': message}
                    self.logStatus("info", "No Info Found")

        return dic





# def lambda_landler(event,context):
#     my_class = DrivingLicenseVerification(event['DL'], event['DOB'],event['refid'],event['env'])
#     result = my_class.generate_response()
#
#
#     print(result)
#     return result
#     result_java_queue.update(data)
#
# lambda_landler({'DL': 'UP80 20120008950', 'DOB': '21-11-1991','refid':'', 'env' : 'quality'}, '')
#if __name__ == '__main__':
    #v = DrivingLicenseVerification(license_number = 'HR-1220090012812',dob = '15-Feb-1998',refid="testing2", env='quality')
 #   data = v.exceptionhandling()
   #  print(data)