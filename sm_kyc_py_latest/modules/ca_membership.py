import time
import json
from selenium import webdriver
from selenium.common.exceptions import UnexpectedAlertPresentException


class CaMemberShip:
    
    def __init__(self,membership_number):

        options = webdriver.ChromeOptions()
        options.add_experimental_option("excludeSwitches", ['enable-automation'])
        options.add_argument("--incognito")
        options.add_argument("--start-maximized")
        options.add_argument("--disable-infobars")
        options.add_argument("--disable-extension")
        self.browser = webdriver.Chrome(executable_path="/usr/local/bin/chromedriver",options=options)
        self.membership_number=membership_number
        




    def ca_membership(self):
        
        self.browser.get("http://112.133.194.254/lom.asp")
        time.sleep(2)
        input_element=self.browser.find_element_by_xpath('.//input[@name = "t1"]')
        time.sleep(1)
        input_element.send_keys(self.membership_number)
        time.sleep(2)
        self.browser.find_element_by_xpath('.//input[@type = "Submit"]').click()
        time.sleep(2)


        final_dict_to_send={}

        try:

            form=self.browser.find_elements_by_xpath('.//form[@name = "frm"]')
            if len(form)>0:
                all_tables=form[0].find_elements_by_tag_name("table")
                data=[]
                print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
                

                if len(all_tables) > 1:
                    
                    print("@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@")
                    try:
                        output_data_table=all_tables[1]
                        for j,v in enumerate(output_data_table.find_elements_by_xpath('.//td[@width = "47%"]')):
                            if v.text != '':
                                data.append(v.text)
                        
                        for j,v in enumerate(output_data_table.find_elements_by_xpath('.//td[@width = "34%"]')):
                            if v.text != '':
                                data.append(v.text)
                
                        print(len(data))
                        print(data)

                        membership_number=self.membership_number
                        name=data.pop(0)
                        gender=data.pop(0)
                        qualification=data.pop(0)
                        address_foreign_section=data.pop(1)
                        fellow_year=data.pop(-1)
                        associate_year=data.pop(-1)
                        cop_status=data.pop(-1)
                        address="".join(data)
                        address=address.replace("    ","")
                        address=address.strip()
                        
                        dict_to_send={}
                        dict_to_send['name']=name
                        dict_to_send['gender']=gender
                        dict_to_send['membershipNumber']=membership_number
                        dict_to_send['qualification']=qualification
                        dict_to_send['foreignSectionAddress']=address_foreign_section
                        dict_to_send['address']=address
                        dict_to_send['associateYear']=associate_year
                        dict_to_send['copStatus']=cop_status
                        dict_to_send['fellowYear']=fellow_year
                        dict_to_send['foreignSectionRegionInIndia']=""

                        final_dict_to_send["data"]=dict_to_send
                        return final_dict_to_send
                    
                    except UnexpectedAlertPresentException:
                        print("invalid input^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^")
                        final_dict_to_send["data"]=""
                        return final_dict_to_send

                else:
                    final_dict_to_send["data"]=""
                    return final_dict_to_send

        except UnexpectedAlertPresentException:
            print("invalid input^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^")
            final_dict_to_send["data"]=""
            return final_dict_to_send
my_class = CaMemberShip('055426')
print(json.dumps(my_class.ca_membership()))