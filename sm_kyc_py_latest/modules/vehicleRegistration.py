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

class VehicleRegistration:

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
        self.FILE_NAME1 = "datad.png"
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

    def breakcaptcha(self):
        import io
        import os
        from google.cloud import vision
        import time
        import io
        self.driver.find_element_by_xpath("""/html/body/form/div[1]/div[3]/div[1]/div/div[2]/div[3]/div/div[2]/div/div[2]/table/tbody/tr/td[1]/img""").screenshot('captcha.png')
        with io.open(os.path.join(self.FOLDER_PATH, self.FILE_NAME), 'rb') as image_file:
            content = image_file.read()

        image = vision.types.Image(content=content)
        response = self.client.text_detection(image=image)
        texts = response.text_annotations

        for text in texts:
            z = ('"{}"'.format(text.description))
        h = str(z).split('"')
        k = h[1]

        self.makeDriverDirs()
        try:
            sname = str(k) + '.png'
            screenshotName = os.path.join(self.screenshotDir, f"{sname}")
            self.driver.find_element_by_xpath("""/html/body/form/div[1]/div[3]/div[1]/div/div[2]/div[3]/div/div[2]/div/div[2]/table/tbody/tr/td[1]/img""").screenshot(screenshotName)
            self.uploadToS3(os.path.join(screenshotName), 'Vehicle/' + sname)
        except:
            pass
        self.driver.find_element_by_xpath("""/html/body/form/div[1]/div[3]/div[1]/div/div[2]/div[3]/div/div[2]/div/div[2]/table/tbody/tr/td[3]/input""").click()
        self.driver.find_element_by_xpath("""/html/body/form/div[1]/div[3]/div[1]/div/div[2]/div[3]/div/div[2]/div/div[2]/table/tbody/tr/td[3]/input""").send_keys(k)
        self.driver.find_element_by_xpath("""/html/body/form/div[1]/div[3]/div[1]/div/div[2]/div[4]/div/button[1]/span""").click()


    def generate_vehicle(self,vehiclePart1, vehiclePart2):
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

        self.driver = webdriver.Chrome("/usr/local/bin/chromedriver",options=chrome_options)
        self.logStatus("info", "Vehicle page opened",self.takeScreenshot())
        self.logStatus("info", "Driver created")
        try:
            self.driver.get("https://parivahan.gov.in/rcdlstatus/?pur_cd=102")
            r = 1
            self.makeDriverDirs()
            self.logStatus("info", "Vehicle page opened",self.takeScreenshot())
            try:

                cantreach =  self.driver.find_element_by_xpath("""/html/body/form/div[1]/div[3]/div[1]/div/div[2]/div[2]/div/div[2]/label/label""")
                cantreach = cantreach.text

                if cantreach == cantreach:
                    r = 1
            except:
                r = 2
                pass

        except Exception as e:
            self.logStatus("critical", "Vehicle page could not open contact support")
            r = 2
        if r == 2:
            dic = {}
            message = "Unable To Process. Please Reach Out To Support."
            code = "EUP007"
            dic = {"data": "null", "responseCode": code, "responseMessage": message}
            return dic

        print(r)
        if r == 1:

            self.driver.find_element_by_xpath("""/html/body/form/div[1]/div[3]/div[1]/div/div[2]/div[2]/div/div[3]/input[1]""").click()
            self.driver.find_element_by_xpath("""/html/body/form/div[1]/div[3]/div[1]/div/div[2]/div[2]/div/div[3]/input[1]""").send_keys(vehiclePart1)
            self.driver.find_element_by_xpath("""/html/body/form/div[1]/div[3]/div[1]/div/div[2]/div[2]/div/div[3]/input[2]""").click()
            self.driver.find_element_by_xpath("""/html/body/form/div[1]/div[3]/div[1]/div/div[2]/div[2]/div/div[3]/input[2]""").send_keys(vehiclePart2)
            try:
                self.breakcaptcha()
                time.sleep(1)
                errorcode1 = self.driver.find_element_by_xpath("""/html/body/form/div[1]/div[3]/div[1]/div/div[2]/div[1]/div/ul/li/span[1]""")
                errorcode1 = errorcode1.text
                print(errorcode1)
                if errorcode1 == 'Verification code does not match.':
                    self.driver.find_element_by_xpath("""/html/body/form/div[1]/div[3]/div[1]/div/div[2]/div[3]/div/div[2]/div/div[2]/table/tbody/tr/td[3]/input""").clear()
                    self.breakcaptcha()
                    time.sleep(1)
                    errorcode2 = self.driver.find_element_by_xpath("""/html/body/form/div[1]/div[3]/div[1]/div/div[2]/div[1]/div/ul/li/span[1]""")
                    errorcode2 = errorcode2.text
                    if errorcode2 == 'Verification code does not match.':

                        self.driver.find_element_by_xpath("""/html/body/form/div[1]/div[3]/div[1]/div/div[2]/div[3]/div/div[2]/div/div[2]/table/tbody/tr/td[3]/input""").clear()
                        self.breakcaptcha()
                    else:
                        pass


            except Exception as e:
                pass
            time.sleep(3)
            try:
                import io
                import os
                from google.cloud import vision
                import time
                import io
                self.driver.find_element_by_xpath("""/html/body/div[2]/div[2]""").screenshot('datad.png')
                with io.open(os.path.join(self.FOLDER_PATH, self.FILE_NAME1), 'rb') as image_file:
                    content = image_file.read()

                image = vision.types.Image(content=content)
                response = self.client.text_detection(image=image)
                texts = response.text_annotations

                resp = str(texts)
                data = resp.split("description")[1].split('\n')[0]
                print("data ",data)
                data = data.replace('\\n',"")
                data = data.replace(":","")
                authorityComment = data.replace('"',"")
                if len(authorityComment)>3:
                    message = "Successfully Completed."
                    code = "SRC001"
                    chassisNumber = ""

                    engineNumber = ""
                    fitnessUpto = ""
                    fuelType = ""
                    fuelNorms = ""
                    insuranceUpto = ""
                    makerModel = ""
                    ownerName = ""
                    registrationNumber = ""
                    registrationAuthority = ""
                    registrationDate = ""
                    roadTaxPaidUpto = ""
                    vehicleClass = ""
                    nocDetail = ""
                    dic = {}
                    dic["chassisNumber"] = chassisNumber
                    dic["authorityComment"] = authorityComment
                    dic["engineNumber"] = engineNumber
                    dic["fitnessUpto"] = fitnessUpto
                    dic["fuelType"] = fuelType
                    dic["fuelNorms"] = fuelNorms
                    dic["insuranceUpto"] = insuranceUpto
                    dic["makerModel"] = makerModel
                    dic["ownerName"] = ownerName
                    dic["registrationNumber"] = registrationNumber
                    dic["registrationAuthority"] = registrationAuthority
                    dic["registrationDate"] = registrationDate
                    dic["roadTaxPaidUpto"] = roadTaxPaidUpto
                    dic["vehicleClass"] = vehicleClass
                    dic["nocDetail"] = nocDetail
                    dic["vehiclePart1"] = vehiclePart1
                    dic["vehiclePart2"] = vehiclePart2
                    dic = {"data": dic, "responseCode": code, "responseMessage": message}
                    return dic
                else:
                    x =7
            except:
                x = 7
                pass
            print(x)

            if x == 7:
                time.sleep(2)
                registrationNumber = self.driver.find_element_by_xpath(
                    """/html/body/form/div[1]/div[3]/div[1]/div/div[2]/div[4]/span/div/div/div/div/div/table/tbody/tr[1]/td[2]/span""")
                registrationNumber = registrationNumber.text
                registrationAuthority = self.driver.find_element_by_xpath(
                    """/html/body/form/div[1]/div[3]/div[1]/div/div[2]/div[4]/span/div/div/div/div/div/div[2]""")
                registrationAuthority = registrationAuthority.text
                registrationAuthority = registrationAuthority.split(":")[1]
                chassisNumber =  self.driver.find_element_by_xpath(
                    """/html/body/form/div[1]/div[3]/div[1]/div/div[2]/div[4]/span/div/div/div/div/div/table/tbody/tr[2]/td[2]""")
                chassisNumber = chassisNumber.text
                engineNumber =   self.driver.find_element_by_xpath(
                    """/html/body/form/div[1]/div[3]/div[1]/div/div[2]/div[4]/span/div/div/div/div/div/table/tbody/tr[2]/td[4]""")
                engineNumber = engineNumber.text
                vehicleClass = self.driver.find_element_by_xpath("""/html/body/form/div[1]/div[3]/div[1]/div/div[2]/div[4]/span/div/div/div/div/div/table/tbody/tr[2]/td[4]""")
                vehicleClass = vehicleClass.text
                roadTaxPaidUpto = self.driver.find_element_by_xpath("""/html/body/form/div[1]/div[3]/div[1]/div/div[2]/div[4]/span/div/div/div/div/div/table/tbody/tr[7]/td[4]""")
                roadTaxPaidUpto = roadTaxPaidUpto.text
                fuelType = self.driver.find_element_by_xpath("""/html/body/form/div[1]/div[3]/div[1]/div/div[2]/div[4]/span/div/div/div/div/div/table/tbody/tr[4]/td[4]""")
                fuelType = fuelType.text
                fuelNorms = self.driver.find_element_by_xpath("""/html/body/form/div[1]/div[3]/div[1]/div/div[2]/div[4]/span/div/div/div/div/div/table/tbody/tr[7]/td[2]""")
                fuelNorms = fuelNorms.text
                registrationDate = self.driver.find_element_by_xpath("""/html/body/form/div[1]/div[3]/div[1]/div/div[2]/div[4]/span/div/div/div/div/div/table/tbody/tr[1]/td[4]""")
                registrationDate = registrationDate.text
                ownerName = self.driver.find_element_by_xpath("""/html/body/form/div[1]/div[3]/div[1]/div/div[2]/div[4]/span/div/div/div/div/div/table/tbody/tr[3]/td[2]""")
                ownerName = ownerName.text
                makerModel =  self.driver.find_element_by_xpath("""/html/body/form/div[1]/div[3]/div[1]/div/div[2]/div[4]/span/div/div/div/div/div/table/tbody/tr[5]/td[2]""")
                makerModel = makerModel.text
                fitnessUpto = self.driver.find_element_by_xpath("""/html/body/form/div[1]/div[3]/div[1]/div/div[2]/div[4]/span/div/div/div/div/div/table/tbody/tr[6]/td[2]""")
                fitnessUpto = fitnessUpto.text
                insuranceUpto = self.driver.find_element_by_xpath("""/html/body/form/div[1]/div[3]/div[1]/div/div[2]/div[4]/span/div/div/div/div/div/table/tbody/tr[6]/td[4]""")
                insuranceUpto = insuranceUpto.text
                try:
                    nocDetail = self.driver.find_element_by_xpath("""/html/body/form/div[1]/div[3]/div[1]/div/div[2]/div[4]/span/div/div/div/div/div/table/tbody/tr[8]/td[2]/span""")
                    nocDetail = nocDetail.text
                except:
                    nocDetail = ""
                    pass
                message = "Successfully Completed."
                code = "SRC001"
                authorityComment = ""
                dic = {}
                dic["chassisNumber"] = chassisNumber
                dic["authorityComment"] = authorityComment
                dic["engineNumber"] = engineNumber
                dic["fitnessUpto"] = fitnessUpto
                dic["fuelType"] = fuelType
                dic["fuelNorms"] = fuelNorms
                dic["insuranceUpto"] = insuranceUpto
                dic["makerModel"] = makerModel
                dic["ownerName"] = ownerName
                dic["registrationNumber"] = registrationNumber
                dic["registrationAuthority"] = registrationAuthority
                dic["registrationDate"] = registrationDate
                dic["roadTaxPaidUpto"] = roadTaxPaidUpto
                dic["vehicleClass"] = vehicleClass
                dic["nocDetail"] = nocDetail
                dic["vehiclePart1"] = vehiclePart1
                dic["vehiclePart2"] = vehiclePart2
                dic = {"data": dic, "responseCode": code, "responseMessage": message}

                return dic

    def vehicle_response(self,vehiclePart1,vehiclePart2):

        dic = {}
        try:
            self.logStatus("info", "Opening webpage")
            dic = self.generate_vehicle(vehiclePart1,vehiclePart2)
        except Exception as e:
            print(e)
            self.logStatus("critical", "timeout error retrying")
            try:
                self.logStatus("info", "Opening webpage")
                dic = self.generate_vehicle(vehiclePart1,vehiclePart2)
            except Exception as e:
                print(e)
                self.logStatus("critical", "timeout error retrying")
                try:
                    self.logStatus("info", "Opening webpage")
                    dic = self.generate_vehicle(vehiclePart1,vehiclePart2)
                except Exception as e:
                    print(e)
                    try:
                        oo = self.driver.find_element_by_xpath("""/html/body/form/div[1]/div[3]/div[1]/div/div[2]/div[1]/div/ul/li/span[1]""").text
                        if oo == "Verification code does not match.":
                            dic = {}
                            message = 'Unable To Process. Please Reach Out To Support.'
                            code = 'EUP007'
                            dic = {'data': 'null', 'responseCode': code, 'responseMessage': message}
                            self.logStatus("info", "No Info Found")
                            return dic
                    except:
                        pass
                    print(e)
                    self.logStatus("critical", "no data found")

                    message = 'No Information Found.'
                    code = 'ENI004'

                    dic = {'data': 'null', 'responseCode': code, 'responseMessage': message}
                    self.logStatus("info", "No Info Found")

        return dic




if __name__ == '__main__':

     v = VehicleRegistration(refid="testing2",env = 'prod')
     data = v.vehicle_response(vehiclePart1 = "KA01A",vehiclePart2 = "1114")
     print(data)
    # v.close()
