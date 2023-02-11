from flask import Flask, jsonify, request, make_response

from modules.aadhaar_verification import AadharVerification
from modules.driving_licenses import DrivingLicenseVerification
from modules.fssai import FssaiVerification
from modules.electoral import ElectoralSearchVerification
from modules.itr import ItrAcknowledgementVerification
from modules.icsi import IcsiVerification
from modules.pan_verification import PanVerification
from modules.vehicle_registration import VehicleRegistrationVerification
from modules.import_export import ImportExport
from modules.ca_membership import CaMemberShip

from credentials import credential,api

app = Flask(__name__)



@app.route(f"/scrapper/api/{api['aadhaar']}",methods=['GET'])
def aadhaarVerification():
    if request.method == 'GET':
        aadhaar_no=request.args.get('aadhaar_number')
        print("^^^^^^^^^^^^^^^",aadhaar_no)
        aadhaar_obj=AadharVerification()
        try:
            output=aadhaar_obj.generate_response()
            status=output.pop('status')
            if status == "Aadhaar number entered is correct !":
                return make_response(jsonify({
                    "data": output,
                    "api":api['aadhaar'],
                    "responseCode":200,
                    "responseMessage":"Successfully Completed"
                }))
            elif status == "The Aadhaar number entered is incorrect !":
                 return make_response(jsonify({
                    "data": output,
                    "api":api['aadhaar'],
                    "responseCode":422,
                    "responseMessage":status
                }))

        except Exception as e:
            print(e)
            return jsonify({"message": "some error", "code": 666, "error": str(e)})  






@app.route(f"/scrapper/api/{api['drivingLicense']}",methods=['GET'])
def drivingLicenseVerification():
    if request.method == 'GET':
        # aadhaar_no=request.args.get('aadhaar_number')
        # print("^^^^^^^^^^^^^^^",aadhaar_no)
        driving_obj=DrivingLicenseVerification("UP-8020120008951","21-11-1991")
        try:
            output=driving_obj.generate_response()
            if output['data'] == 'No DL Details Found....':
                return make_response(jsonify({
                    "data": output['data'],
                    "api":api['aadhaar'],
                    "referenceId":"84a77af5-9826-4875-b31c-a01d6e77e91c",
                    "responseCode":200,
                    "responseMessage":"Successfully Completed."
                }))
            else:
                return make_response(jsonify({
                    "data": output['data'],
                    "api":api['aadhaar'],
                    "referenceId":"84a77af5-9826-4875-b31c-a01d6e77e91c",
                    "responseCode":200,
                    "responseMessage":"Successfully Completed."
                }))

        except Exception as e:
            print(e)
            return jsonify({"message": "some error", "code": 666, "error": str(e)})  




@app.route(f"/scrapper/api/{api['fssai']}",methods=['GET'])
def fssaiVerification():
    if request.method == 'GET':
        # vehicle_no=request.args.get('vehicle_number')
        # print("^^^^^^^^^^^^^^^",vehicle_no)


        fssai_obj=FssaiVerification()
        
        try:
            output=fssai_obj.fssai_scrapper("10014012000268")
            data_response=output['data']
            

            if len(data_response)==1:
                 return make_response(jsonify({
                    "data": "",
                    "api":api['fssai'],
                    "referenceId":"84a77af5-9826-4875-b31c-a01d6e77e91c",
                    "responseCode":422,
                    "responseMessage":"Request Completed Successfully with invalid license number."
                }))
            else:
                 return make_response(jsonify({
                    "data": output['data'],
                    "api":api['fssai'],
                    "referenceId":"84a77af5-9826-4875-b31c-a01d6e77e91c",
                    "responseCode":200,
                    "responseMessage":"Completed Successfully."
                }))


           
        except Exception as e:
            print(e)
            return jsonify({"message": "some error", "code": 666, "error": str(e)})  







@app.route(f"/scrapper/api/{api['electoralSearch']}",methods=['GET'])
def electoralSearchVerification():
    if request.method == 'GET':
        # vehicle_no=request.args.get('vehicle_number')
        # print("^^^^^^^^^^^^^^^",vehicle_no)


        electoral_obj=ElectoralSearchVerification("NEL397668")
        
        try:
            
            output=electoral_obj.generate_response()
            print("#############################",output)
            data=output['data']
            
            

            if len(data) == 0:
                 return make_response(jsonify({
                    "data": "",
                    "api":api['electoralSearch'],
                    "referenceId":"84a77af5-9826-4875-b31c-a01d6e77e91c",
                    "responseCode":422,
                    "responseMessage":"Request Completed Successfully with invalid epic number."
                }))
            else:
                 return make_response(jsonify({
                    "data": output['data'],
                    "api":api['electoralSearch'],
                    "referenceId":"84a77af5-9826-4875-b31c-a01d6e77e91c",
                    "responseCode":200,
                    "responseMessage":"Completed Successfully."
                }))


           
        except Exception as e:
            print(e)
            return jsonify({"message": "some error", "code": 666, "error": str(e)})  





@app.route(f"/scrapper/api/{api['itrAcknowledgement']}",methods=['GET'])
def itrAcknowledgementVerification():
    if request.method == 'GET':
        # vehicle_no=request.args.get('vehicle_number')
        # print("^^^^^^^^^^^^^^^",vehicle_no)


        itr_obj=ItrAcknowledgementVerification("ALGPJ6855K","601513250310318")
        output=itr_obj.generate_response()
        
        try:
            
            if output['itrStatus'] == 'Please enter a valid Acknowledgement Number.':
                 return make_response(jsonify({
                    "data": "",
                    "api":api['itrAcknowledgement'],
                    "referenceId":"84a77af5-9826-4875-b31c-a01d6e77e91c",
                    "responseCode":422,
                    "responseMessage":"Request Completed Successfully with invalid Acknowledgement Number."
                }))

            elif output['itrStatus'] == 'Invalid PAN. Please retry .':
                 return make_response(jsonify({
                    "data": "",
                    "api":api['itrAcknowledgement'],
                    "referenceId":"84a77af5-9826-4875-b31c-a01d6e77e91c",
                    "responseCode":422,
                    "responseMessage":"Request Completed Successfully with invalid pan number."
                }))     
            else:
                 return make_response(jsonify({
                    "data": output,
                    "api":api['itrAcknowledgement'],
                    "referenceId":"84a77af5-9826-4875-b31c-a01d6e77e91c",
                    "responseCode":200,
                    "responseMessage":"Completed Successfully."
                }))


           
        except Exception as e:
            print(e)
            return jsonify({"message": "some error", "code": 666, "error": str(e)})  






@app.route(f"/scrapper/api/{api['icsi']}",methods=['GET'])
def icsiVerification():
    if request.method == 'GET':
        # vehicle_no=request.args.get('vehicle_number')
        # print("^^^^^^^^^^^^^^^",vehicle_no)


        icsi_obj=IcsiVerification()
        output=icsi_obj.icsi_scrapper("ACS","96")
        
        try:
            
            if output['data'] == "":
                 return make_response(jsonify({
                    "data": "",
                    "api":api['icsi'],
                    "referenceId":"84a77af5-9826-4875-b31c-a01d6e77e91c",
                    "responseCode":422,
                    "responseMessage":"Request Completed Successfully with invalid input details."
                }))
  
            else:
                 return make_response(jsonify({
                    "data": output['data'],
                    "api":api['icsi'],
                    "referenceId":"84a77af5-9826-4875-b31c-a01d6e77e91c",
                    "responseCode":200,
                    "responseMessage":"Completed Successfully."
                }))

        except Exception as e:
            print(e)
            return jsonify({"message": "some error", "code": 666, "error": str(e)})  





@app.route(f"/scrapper/api/{api['pan']}",methods=['GET'])
def panVerification():
    if request.method == 'GET':
        # vehicle_no=request.args.get('vehicle_number')
        # print("^^^^^^^^^^^^^^^",vehicle_no)


        pan_obj=PanVerification()
        output=pan_obj.generate_response("FATPS1135L","Shashank Sharma","07/01/1992","'Individual'")
        try:
            
            if output['data'] == "":
                 return make_response(jsonify({
                    "data": "",
                    "api":api['pan'],
                    "referenceId":"84a77af5-9826-4875-b31c-a01d6e77e91c",
                    "responseCode":422,
                    "responseMessage":"Request Completed Successfully with invalid details"
                }))
   
            else:
                 return make_response(jsonify({
                    "data": output['data'],
                    "api":api['pan'],
                    "referenceId":"84a77af5-9826-4875-b31c-a01d6e77e91c",
                    "responseCode":200,
                    "responseMessage":"Completed Successfully."
                }))


           
        except Exception as e:
            print(e)
            return jsonify({"message": "some error", "code": 666, "error": str(e)})  






@app.route(f"/scrapper/api/{api['vehicleRegistration']}",methods=['GET'])
def vehicleRegistrationVerification():
    if request.method == 'GET':
        # vehicle_no=request.args.get('vehicle_number')
        # print("^^^^^^^^^^^^^^^",vehicle_no)


        vehicle_reg_obj=VehicleRegistrationVerification("H37","889")
        output=vehicle_reg_obj.generate_response()
       
        try:
            
            if output['data'] == "":
                 return make_response(jsonify({
                    "data": "",
                    "api":api['vehicleRegistration'],
                    "referenceId":"84a77af5-9826-4875-b31c-a01d6e77e91c",
                    "responseCode":200,
                    "responseMessage":"Registration number does not exist !! Please check the number."
                }))
     
            else:
                 return make_response(jsonify({
                    "data": output['data'],
                    "api":api['vehicleRegistration'],
                    "referenceId":"84a77af5-9826-4875-b31c-a01d6e77e91c",
                    "responseCode":200,
                    "responseMessage":"Completed Successfully."
                }))


           
        except Exception as e:
            print(e)
            return jsonify({"message": "some error", "code": 666, "error": str(e)})  




@app.route(f"/scrapper/api/{api['importExport']}",methods=['GET'])
def importExport():
    if request.method == 'GET':
        # vehicle_no=request.args.get('vehicle_number')
        # print("^^^^^^^^^^^^^^^",vehicle_no)


        import_export_obj=ImportExport("121212","")
        output=import_export_obj.import_export()
       
        try:
            
            if output['data'] == "":
                 return make_response(jsonify({
                    "data": "",
                    "api":api['importExport'],
                    "referenceId":"84a77af5-9826-4875-b31c-a01d6e77e91c",
                    "responseCode":422,
                    "responseMessage":"Invalid Credentials."
                }))
     
            else:
                 return make_response(jsonify({
                    "data": output['data'],
                    "api":api['importExport'],
                    "referenceId":"84a77af5-9826-4875-b31c-a01d6e77e91c",
                    "responseCode":200,
                    "responseMessage":"Completed Successfully."
                }))


           
        except Exception as e:
            print(e)
            return jsonify({"message": "some error", "code": 666, "error": str(e)})



@app.route(f"/scrapper/api/{api['caMembership']}",methods=['GET'])
def caMemberShip():
    if request.method == 'GET':
        # vehicle_no=request.args.get('vehicle_number')
        # print("^^^^^^^^^^^^^^^",vehicle_no)


        ca_membership_obj=CaMemberShip("")
        output=ca_membership_obj.ca_membership()
        print("$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$",output)
        try:
            
            if output['data'] == "":
                 return make_response(jsonify({
                    "data": "",
                    "api":api['caMembership'],
                    "referenceId":"84a77af5-9826-4875-b31c-a01d6e77e91c",
                    "responseCode":200,
                    "responseMessage":"No records found."
                }))
     
            else:
                 return make_response(jsonify({
                    "data": output['data'],
                    "api":api['caMembership'],
                    "referenceId":"84a77af5-9826-4875-b31c-a01d6e77e91c",
                    "responseCode":200,
                    "responseMessage":"Completed Successfully."
                }))


           
        except Exception as e:
            print(e)
            return jsonify({"message": "some error", "code": 666, "error": str(e)})  





  
