#!/usr/bin/env python
# coding: utf-8
# !/usr/bin/env python
# coding: utf-8

# In[120]:


import time
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
import pickle
from webdriver_manager.chrome import ChromeDriverManager
import urllib.request
import pandas as pd
import numpy as np
import pickle
import os
import subprocess
from datetime import datetime, timedelta
import cv2
import numpy as np
import pytesseract
import pyautogui as pag

# In[ ]:


# In[ ]:


############ LOGIN TO WEBSITE TO FETCH DATA


driver = webdriver.Chrome(ChromeDriverManager().install())
# driver.implicitly_wait(30)
driver.maximize_window()
driver.get("https://www.dgft.gov.in/CP/")
time.sleep(2)
driver.get("https://www.dgft.gov.in/CP/?opt=view-any-ice")
time.sleep(2)
pag.click(250, 650, 1, 1, "left")

time.sleep(1)
pag.click(666, 345, 1, 1, "left")

pag.typewrite("0388031964", 0.001)

time.sleep(1)
pag.click(657, 449, 1, 1, "left")

pag.typewrite("TATA CONSULTANCY SERVICES LIMITED", 0.001)

driver.save_screenshot("screenshot.png")

image1 = cv2.imread('screenshot.png')
image = image1[320:380, 600:730]

image = cv2.blur(image, (3, 3))
ret, image = cv2.threshold(image, 90, 255, cv2.THRESH_BINARY);

image = cv2.dilate(image, np.ones((2, 1), np.uint8))
image = cv2.erode(image, np.ones((1, 2), np.uint8))

cap = pytesseract.image_to_string(image)

if "?" in cap:
    cap = cap.replace("?", "2")
    cap = cap.split("\n")[0]
if "/" in cap:
    cap = cap.replace("/", "7")
    cap = cap.split("\n")[0]
time.sleep(1)
pag.click(660, 565, 1, 1, "left")
pag.typewrite(cap, 0.001)

pag.click(674, 614, 1, 1, "left")
time.sleep(2)

with open("table_page.html", "w") as f:
    f.write(driver.page_source)

driver.close()

# In[ ]:


# In[190]:


################## FETCH ALL DATA FROM HTML PAGE


from openpyxl import Workbook
from openpyxl.styles import Font, Color, Alignment, Border, Side, colors
import re

#### IEC DETAILS

from pyquery import PyQuery

html = open("table_page.html", 'r').read()  # local html

query = PyQuery(html)

pattern = '<label for="email" class="font-12 font-weight-semi-bold">'

dict1 = {}
list1 = re.split(pattern, html, 14)

for i in range(1, len(list1)):
    x1 = list1[i].split("<")[0]

    x1 = x1.replace('\n', '')
    x1 = x1.replace('\t', '')

    y1 = list1[i].split('">')[1].split("<")[0]

    y1 = y1.replace('\n', '')
    y1 = y1.replace('\t', '')

    dict1[x1] = y1

## BRANCK DETAILS

from bs4 import BeautifulSoup

soup = BeautifulSoup(open("table_page.html"), "html.parser")
table = soup.find("table", attrs={"class": "table table-hover custom-datatable dataTable no-footer"})

# table table-hover custom-datatable dataTable no-footer

# table table-hover custom-datatable

# The first tr contains the field names.
headings = [th.get_text() for th in table.find("tr").find_all("th")]

datasets = []
for row in table.find_all("tr")[1:]:
    dataset = zip(headings, (td.get_text() for td in row.find_all("td")))
    datasets.append(dataset)

dict2 = {"Branch Code": "Branch Address"}

list2 = []

for dataset in datasets:

    dict2 = {}
    for field in dataset:
        x1 = field[0]
        y1 = field[1].replace('\n', '')
        y1 = y1.replace('\t', '')
        #             print("{0:<16}: {1}".format(x1, y1))

        dict2[x1] = y1
    list2.append(dict2)

#     print(dict2)
#     print("")


############RCMC DETAILS

from bs4 import BeautifulSoup

soup = BeautifulSoup(open("table_page.html"), "html.parser")
table = soup.find("table", attrs={"class": "table table-hover custom-datatable"})

# table table-hover custom-datatable dataTable no-footer

# table table-hover custom-datatable

# The first tr contains the field names.
headings = [th.get_text() for th in table.find("tr").find_all("th")]

datasets = []
for row in table.find_all("tr")[1:]:
    dataset = zip(headings, (td.get_text() for td in row.find_all("td")))
    datasets.append(dataset)

list3 = []

for dataset in datasets:
    dict3 = {}
    for field in dataset:
        x1 = field[0]
        y1 = field[1].replace('\n', '')
        y1 = y1.replace('\t', '')

        dict3[x1] = y1
    #         print("{0:<16}: {1}".format(x1, y1))

    list3.append(dict3)

from pyquery import PyQuery

html = open("table_page.html", 'r').read()  # local html

query = PyQuery(html)

pan_table_data = query("table").eq(1).text().split("\n")

pan_table_data = [pan_table_data[i:i + 3] for i in range(0, len(pan_table_data), 3)]

list4 = []

for i in range(len(pan_table_data)):
    if i > 0:
        dict4 = {}
        #         print(pan_table_data[i])

        dict4['Sl. No.'] = pan_table_data[i][0]
        dict4['Name'] = pan_table_data[i][1]
        dict4['PAN Number'] = pan_table_data[i][2]

        list4.append(dict4)

    # In[ ]:

# In[ ]:


################# SAVE ALL DATA IN EXCEL FILE

workbook = Workbook()
sheet = workbook.active


class style:
    BOLD = '\050[1m'
    END = '\050[0m'


row_number = 1

bold_font1 = Font(bold=True, size=14)
bold_font2 = Font(bold=True)

sheet["A" + str(row_number)] = "INPUT"
sheet["A" + str(row_number)].font = bold_font1
row_number += 1

sheet["A" + str(row_number)] = "Enter Importer/Exporter Code"
sheet["A" + str(row_number)].font = bold_font2
sheet["B" + str(row_number)] = "0388031964"
sheet["B" + str(row_number)] = "TATA CONSULTANCY SERVICES LIMITED"
row_number += 1

sheet["A" + str(row_number)] = "Enter Firm Name"
sheet["A" + str(row_number)].font = bold_font2
row_number += 1

sheet["A" + str(row_number)] = "OUTPUT"
sheet["A" + str(row_number)].font = bold_font1
row_number += 1

sheet["A" + str(row_number)] = "IEC DETAILS"
sheet["A" + str(row_number)].font = bold_font1
row_number += 1

for key, value in dict1.items():

    sheet["A" + str(row_number)] = key
    sheet["A" + str(row_number)].font = bold_font2

    if value == "":
        sheet["B" + str(row_number)] = "-"
    else:
        sheet["B" + str(row_number)] = value

    row_number += 1

sheet["A" + str(row_number)] = "BRANCH DETAILS"
sheet["A" + str(row_number)].font = bold_font1
row_number += 1

sheet["A" + str(row_number)] = "Branch Code"
sheet["B" + str(row_number)] = "GSTIN"
sheet["C" + str(row_number)] = "Branch Address"
sheet["A" + str(row_number)].font = bold_font2
sheet["B" + str(row_number)].font = bold_font2
sheet["C" + str(row_number)].font = bold_font2
row_number += 1

for i in list2:

    sheet["A" + str(row_number)] = i["Branch Code"]
    try:
        sheet["B" + str(row_number)] = i["GSTIN"]
    except:
        pass
    sheet["C" + str(row_number)] = i["Branch Address"]

    row_number += 1

sheet["A" + str(row_number)] = "DETAILS OF PROPRIETOR/PARTNER/DIRECTOR/KARTA/MANAGING TRUSTEE"
sheet["A" + str(row_number)].font = bold_font1
row_number += 1

sheet["A" + str(row_number)] = "Sl. No."
sheet["B" + str(row_number)] = "Name"
sheet["C" + str(row_number)] = "Pan Number"
sheet["A" + str(row_number)].font = bold_font2
sheet["B" + str(row_number)].font = bold_font2
sheet["C" + str(row_number)].font = bold_font2
row_number += 1

for i in list4:
    sheet["A" + str(row_number)] = i["Sl. No."]
    sheet["B" + str(row_number)] = i["Name"]

    sheet["C" + str(row_number)] = i["PAN Number"]

    row_number += 1

sheet["A" + str(row_number)] = "RCMC"
sheet["A" + str(row_number)].font = bold_font1
row_number += 1

sheet["A" + str(row_number)] = "Sl. No."
sheet["B" + str(row_number)] = "RCMC Number"
sheet["C" + str(row_number)] = "Issue Date"
sheet["D" + str(row_number)] = "Issue Authority"
sheet["E" + str(row_number)] = "Products For Which Registered"
sheet["F" + str(row_number)] = "Expiry Date"
sheet["G" + str(row_number)] = "Status"
sheet["H" + str(row_number)] = "Exporter Type"
sheet["I" + str(row_number)] = "Validity Period"
sheet["J" + str(row_number)] = "Status From EPC"

sheet["A" + str(row_number)].font = bold_font2
sheet["B" + str(row_number)].font = bold_font2
sheet["C" + str(row_number)].font = bold_font2
sheet["D" + str(row_number)].font = bold_font2
sheet["E" + str(row_number)].font = bold_font2
sheet["F" + str(row_number)].font = bold_font2
sheet["G" + str(row_number)].font = bold_font2
sheet["H" + str(row_number)].font = bold_font2
sheet["I" + str(row_number)].font = bold_font2
sheet["J" + str(row_number)].font = bold_font2
row_number += 1

for i in list3:
    sheet["A" + str(row_number)] = i["Sl. No."]
    sheet["B" + str(row_number)] = i["RCMC Number"]
    sheet["C" + str(row_number)] = i["Issue Date"]
    sheet["D" + str(row_number)] = i["Issue Authority"]
    sheet["E" + str(row_number)] = i["Products For Which Registered"]
    sheet["F" + str(row_number)] = i["Expiry Date"]
    sheet["G" + str(row_number)] = i["Status"]
    sheet["H" + str(row_number)] = i["Exporter Type"]
    sheet["I" + str(row_number)] = i["Validity Period"]
    sheet["J" + str(row_number)] = i["Status From EPC"]

    row_number += 1

########################################################

workbook.save(filename="IEC.xlsx")

xl_file = pd.ExcelFile("IEC.xlsx")

dfs = {sheet_name: xl_file.parse(sheet_name)
       for sheet_name in xl_file.sheet_names}

# In[ ]:


# In[237]:


##### MAKE JSON FILE

allInOneDict = dict1.copy()
allInOneDict["importExportBranchDetails"] = list2
allInOneDict["importExportDirectorDetails"] = list4
allInOneDict["importExportRcmcDetails"] = list3

last_dict = {"api": "/kyc/internal/importexportcode", "data": allInOneDict}

last_dict["clientId"] = ""
last_dict["clientCode"] = ""
last_dict["referenceId"] = ""
last_dict["responseCode"] = ""
last_dict["responseMessage"] = ""

# In[ ]:


# In[241]:


import json

json_object = json.dumps(last_dict, indent=4)

# Writing to sample.json
with open("iec.json", "w") as outfile:
    outfile.write(json_object)

