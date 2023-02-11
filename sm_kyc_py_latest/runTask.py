import datetime

import boto3
import json
from modules.LEI import LEI
from modules.Voter import Electoralsearch
from modules.shop_and_established import Shop
from modules.Shop_AND_Establishment import Shopestablished
from modules.RabbitMq import ProducerQueue
from modules.aadhaar_verification import AadharVerification
from modules.vehicleRegistration import VehicleRegistration
from modules.FDACOMPLETE import FDA
from modules.FSSAICOMPLETE import FSSAI
from modules.AadharUdyog import aadharudyog
from modules.DRIVINGLICENCECOMPLETE import DrivingLicenseVerification
from modules.ESICCOMPLETE import ESIC
from modules.itr import ItrAcknowledgementVerification
from modules.panverifier import panverifier
from modules.db import DB
from modules.CAMEMBERSHIP import CAMEMBERSHIP
from modules.ICSICOMPLETE import ICSI
from modules.ICMAICOMPLETE import ICMAI
import time
from modules.IEC import IEC
from modules.MCICOMPLETE import MCI
region_name = 'ap-south-1'
# Create SQS client
sqs = boto3.client('sqs', region_name=region_name)


#queue_url = 'https://sqs.ap-south-1.amazonaws.com/608990720610/kyc-quality-queue'
#queue_url = 'https://sqs.ap-south-1.amazonaws.com/608990720610/kyc-request-queue'
#queue_url = 'https://sqs.ap-south-1.amazonaws.com/608990720610/kyc-prod-queue'



def logStatus(refid, level, message, screenshot=None, env1='prod'):
    configFileName = f"config_{env1}.json"
    with open(configFileName, 'r') as confFile:
        config = json.load(confFile)
        dbConfig = config['dbConfig']
    myDBobj = DB(**dbConfig)
    if myDBobj is not None:
        from datetime import datetime, timedelta
        nine_hours_from_now = datetime.now()+ timedelta(hours=5.5)
        myDBobj.insertLog(refid, timestamp='{:%Y-%m-%d %H:%M:%S}'.format(nine_hours_from_now), level=level, log=message,
                          logType='runTask', devEnv=env1, screenshotPath=screenshot)
    print(f"{level}: {message}, screenshot: {screenshot}")

env1='prod'
configFileName1 = f"config_{env1}.json"
with open(configFileName1, 'r') as confFile:
    config1 = json.load(confFile)
print(config1)
queue_url = config1['queue_data']['queue_url']
host_rabbit = config1['queue_data']['host']
port_rabbit = config1['queue_data']['port']
vhost_rabbit = config1['queue_data']['vhost']
username_rabbit = config1['queue_data']['username']
password_rabbit =  config1['queue_data']['password']
exchange_name_rabbit = config1['queue_data']['exchange_name']




print(queue_url)


response = sqs.receive_message(
    QueueUrl=queue_url,
    AttributeNames=[
        'SentTimestamp'
    ],
    MaxNumberOfMessages=3,
    MessageAttributeNames=[
        'All'
    ],
    VisibilityTimeout=0,
    WaitTimeSeconds=0
)
print(json.dumps(response))

if 'Messages' in response:
    print(len(response['Messages']))
    for message in response['Messages']:
        #message = response['Messages'][0]
        task_type = message['MessageAttributes']['Task-Type']['StringValue']
        message_body = json.loads(message['Body'])
        receipt_handle = message['ReceiptHandle']
        result_queue = message['MessageAttributes']['Result-Queue']['StringValue']
        result_java_queue = {'clientId': message_body['clientId'], 'clientCode': message_body['clientCode'],
                             'api': message_body['api'], 'referenceId': message_body['referenceId']}

        refid = message_body['referenceId']

        logStatus(refid, level="info", message="Starting process")

        if task_type == 'internal/aadhaarverifier' or task_type == 'external/aadhaarverifier':
            my_class = AadharVerification(aadhaarnumber=message_body['aadhaarNumber'], refid=message_body['referenceId'],
                                          env='prod')
            data = my_class.exceptionhandling()
            result_java_queue.update(data)
            print(result_java_queue)

        elif task_type == 'internal/shopandestablishmentregistration1' or task_type == 'external/shopandestablishmentregistration1':
            v = Shop(refid=message_body['referenceId'], env='prod')
            data = v.Shop_response(shopEstablishmentName=message_body['establishmentName'], state=message_body['state'],
                                   category=message_body['category'], natureOfBusiness=message_body['natureOfBusiness'],CertificateNo = message_body['certificateNumber'])
            print(data)
            result_java_queue.update(data)

        elif task_type == 'internal/shopandestablishmentregistration' or task_type == 'external/shopandestablishmentregistration':
            v = Shopestablished(refid=message_body['referenceId'], env='prod')
            data = v.Shopestablished_response(licenseNumber=message_body['registrationNumberLicenseNumber'],
                                    state=message_body['state'])
            try:
                print(data)
            except:
                pass

            result_java_queue.update(data)

        elif task_type == 'internal/legalentityidentifier' or task_type == 'external/legalentityidentifier':
            v = LEI(refid=message_body['referenceId'], env='prod')
            data = v.LEI_response(legalEntityIdentifierNumber=message_body['legalEntityIdentifierNumber'])
           # print(data)
            result_java_queue.update(data)

            # elif task_type == 'internal/drivinglicense' or task_type == 'external/drivinglicense':
            # dobList = message_body['dateOfBirth']
            # x = datetime.datetime.strptime(dobList, '%d-%b-%Y')
            # my_class = DrivingLicenseVerification(license_number='UP80 20120008950', dob='21-11-1991',refid=message_body['referenceId'],env='prod')

            #result_java_queue.update(my_class.generate_response())
        elif task_type == 'internal/fdalicense' or task_type == 'external/fdalicense':
            v = FDA(refid=message_body['referenceId'], env='prod')
            data = v.FDA_response(message_body['licenseNumber'])
            print(data)
            result_java_queue.update(json.loads(data))

        elif task_type == 'internal/panverification' or task_type == 'external/panverification':
            v = panverifier(refid=message_body['referenceId'], env='prod')
            data = v.panverifier_response(panNumber=message_body['panNumber'], fullName=message_body['fullName'],
                                          dateOfBirth=message_body['dateOfBirth'], status=message_body['status'])
            print(data)
            result_java_queue.update(data)

        elif task_type == 'internal/icmaimembership' or task_type == 'external/icmaimembership':
            v = ICMAI(refid=message_body['referenceId'], env='prod')
            data = v.ICMAI_response(licenseNumber=message_body['membershipNumber'])
            print(data)
            result_java_queue.update(data)


        elif task_type == 'internal/fssailicense' or task_type == 'external/fssailicense':
            v = FSSAI(refid=message_body['referenceId'], env='prod')
            data = v.FSSAI_response(message_body['licenceNumber'])
            print(data)
            result_java_queue.update(json.loads(data))

        elif task_type == 'internal/votercardverifier' or task_type == 'external/votercardverifier':
            v = Electoralsearch(refid=message_body['referenceId'], env='prod')
            data = v.electoralsearch_response(message_body['epicNumber'])
            print(data)
            result_java_queue.update(data)
        elif task_type == 'internal/itrfilingstatus' or task_type == 'external/itrfilingstatus':
            v = ItrAcknowledgementVerification(pan=message_body['pan'],
                                               acknowledgementNumber=message_body['acknowledgementNumber'],
                                               refid=message_body['referenceId'], env='prod')
            data = v.ITR_response()
            print(data)
            result_java_queue.update(data)

        elif task_type == 'internal/icsimembership' or task_type == 'external/icsimembership':
            v = ICSI(refid=message_body['referenceId'], env='prod')
            data = v.ICSI_response(memberType = message_body['memberType'],membershipNumber= message_body['membershipNumber'])
            result_java_queue.update(data)

        elif task_type == 'internal/udyogaadharnumber' or task_type == 'external/udyogaadharnumber':
            v = aadharudyog(refid=message_body['referenceId'], env='prod')
            data = v.aadharUdyog_response(uamNumber = message_body['uamNumber'])
           # print(data)
            result_java_queue.update(data)

        elif task_type == 'internal/mcimembership' or task_type == 'external/mcimembership':
            v = MCI(refid=message_body['referenceId'], env='prod')
            data = v.MCIMembership(registrationNumber = message_body['registrationNumber'],yearOfRegistration= message_body['yearOfRegistration'],stateMedicalCouncil= message_body['stateMedicalCouncil'])
            print(data)
            result_java_queue.update(data)



        elif task_type == 'internal/drivinglicence' or task_type == 'external/drivinglicence':

            v = DrivingLicenseVerification(license_number=message_body['drivingLicenceNumber'],
                                           dob=message_body['dateOfBirth'], refid=message_body['referenceId'],
                                           env='prod')
            data = v.exceptionhandling()
            print(data)
            result_java_queue.update(data)

        elif task_type == 'internal/importexportcode' or task_type == 'external/importexportcode':
            v = IEC(refid=message_body['referenceId'], env='prod')
            data = v.IEC_response(iecNumber=message_body['iecNumber'], firmName=message_body['firmName'])
            print(data)
            result_java_queue.update(json.loads(data))
            print("result = ",result_java_queue)

        elif task_type == 'internal/camembership' or task_type == 'external/camembership':

            v = CAMEMBERSHIP(refid=message_body['referenceId'], env='prod')
            data = v.camember(caNumber=message_body['caNumber'])
            print(data)
            result_java_queue.update(data)

        elif task_type == 'internal/ESICCOMPLETE' or task_type == 'external/ESICCOMPLETE':

            v = ESIC(refid=message_body['referenceId'], env='prod')
            data = v.ESIF_response(insuranceNumber=message_body['insuranceNumber'])
            print(data)
            result_java_queue.update(json.loads(data))

        # elif task_type == 'internal/fssailicense' or task_type == 'external/fssailicense':
        # v = FSSAI(refid=message_body['referenceId'], env='prod')
        # data = v.FSSAI_response(1, message_body['licenceNumber'])
        # print(data)
        # result_java_queue.update(json.loads(data))

        # elif task_type == 'internal/fdalicense' or task_type == 'external/fdalicense':
        # v = FDA(refid=message_body['referenceId'], env='prod')
        # data = v.FDA_response(message_body['licenseNumber'])
        # print(data)
        # result_java_queue.update(json.loads(data))
        elif task_type == 'internal/vehicleregistration' or task_type == 'external/vehicleregistration':
            v = VehicleRegistration(refid=message_body['referenceId'], env='prod')
            data = v.vehicle_response(message_body['vehiclePart1'], message_body['vehiclePart2'])
            print(data)
            result_java_queue.update(data)
        # Delete received message from queue
        print('rohit')
        print(result_queue)
        #producer = ProducerQueue(host="reindeer.rmq.cloudamqp.com",
         #                        port="5672",
          #                       vhost="okeunydh",
            #                     username="okeunydh",
           #                      password="NsrgkWK6FDqRHVh_WbhJgDMm5kgw8tqP",
             #                    exchange_name="dacompany",
              #                   queue_name=result_queue)
        #prod queue
        #                        port="5672",
        #                       vhost="autvwjpw",
        #                      username="autvwjpw",
        #                     password="FO83Kt7t6XbZUj4IUQtwpF7ymmTchOG_",
        #                    exchange_name="dacompany",
        producer = ProducerQueue(host = host_rabbit,
                                 port = port_rabbit,
                                 vhost = vhost_rabbit,
                                 username = username_rabbit,
                                 exchange_name=exchange_name_rabbit,
                                 password = password_rabbit,
                                 queue_name=result_queue)
        producer.publish_message(json.dumps(result_java_queue))
        sqs_result = sqs.delete_message(
            QueueUrl=queue_url,
            ReceiptHandle=receipt_handle
        )

        print(sqs_result)
        print('deleted from sqs')
        logStatus(refid, level="info", message="process end")
