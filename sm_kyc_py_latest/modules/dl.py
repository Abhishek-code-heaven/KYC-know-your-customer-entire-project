import pandas as pd
from google.cloud import vision
from selenium import webdriver
import os
import io
import time
import sys
from webdriver_manager.chrome import ChromeDriverManager
class DrivingLicenseVerification:

    def __init__(self, license_number = 'UP80 20120008950', dob ='21-11-1991'):

        os.environ[
            "GOOGLE_APPLICATION_CREDENTIALS"] = "vision_api_token.json"

        self.client = vision.ImageAnnotatorClient()
        options = webdriver.ChromeOptions()
        options.add_experimental_option("excludeSwitches", ['enable-automation'])
        options.add_argument("--incognito")
        options.headless = True
        options.add_argument("--disable-extension")
        options.add_argument("no-sandbox")
        options.add_argument("--disable-extensions")
        options.add_argument("--headless")
        self.browser = webdriver.Chrome(ChromeDriverManager().install(), options=options)
        self.FILE_NAME = "captcha.png"
        self.FOLDER_PATH = os.getcwd()
        self.license_number = license_number
        self.dob = dob

    def driving_scrapper(self, license_number, dob):
        try:
            self.browser.get("https://parivahan.gov.in/rcdlstatus/?pur_cd=101")
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
            dict_to_send['dateOfBirth'] = self.dob
            dict_to_send_final = {'data': dict_to_send, "responseCode": code, "responseMessage": message}
            return dict_to_send_final
            sys.exit()

        driving_license_number = self.browser.find_element_by_id("form_rcdl:tf_dlNO")
        time.sleep(1)
        driving_license_number.send_keys(license_number)

        date_of_birth = self.browser.find_element_by_id("form_rcdl:tf_dob_input")
        time.sleep(1)
        date_of_birth.send_keys(dob)

        #self.browser.find_element_by_id("form_rcdl:rcdl_pnl_header").click()

        time.sleep(2)
        self.browser.find_element_by_id("form_rcdl:j_idt32:j_idt38").screenshot("captcha.png")

        with io.open(os.path.join(self.FOLDER_PATH, self.FILE_NAME), 'rb') as image_file:
            content = image_file.read()

        image = vision.types.Image(content=content)
        response = self.client.text_detection(image=image)
        texts = response.text_annotations
        print("wait for output it takes about 30 seconds")
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
            ip_element = self.browser.find_element_by_id("form_rcdl:j_idt32:CaptchaID")
            ip_element.send_keys(info)
            time.sleep(1)

        time.sleep(2)

        self.browser.find_element_by_id("form_rcdl:j_idt43").click()

        time.sleep(2)
        elements = self.browser.find_elements_by_xpath('.//div[@class = "ui-messages-error ui-corner-all"]')
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
        next_page_elements = self.browser.find_elements_by_tag_name("td")

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
            dict_to_send['dateOfBirth'] = self.dob
            dict_to_send_final = {'data': dict_to_send, "responseCode": code, "responseMessage": message}
            return dict_to_send_final

        else:
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


#def lambda_landler(event, context):
    #my_class = DrivingLicenseVerification(event['DL'], event['DOB'])
    #result = my_class.generate_response()

    #print(result)
    #return result


#lambda_landler({'DL': 'UP80 20120008950', 'DOB': '21-11-1991'}, '')

if __name__ == '__main__':
    v = DrivingLicenseVerification(license_number='UP80 20120008950', dob='21-11-1991')
    data = v.generate_response()
    print(data)