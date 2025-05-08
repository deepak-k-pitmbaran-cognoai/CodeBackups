# second child API Tree

from EasyChatApp.utils_sbigen_functions import *
result_dict = {}
try:
    common_utils_obj = CommonUtilsFile.objects.filter(bot=Bot.objects.get(pk=1))
    exec(str(common_utils_obj[0].code), result_dict) 
except Exception:
    pass 
from EasyChatApp.utils import logger
import json
import requests
import xmltodict
import sys
import random,string
from datetime import datetime

def f():
    response = {}
    response['status_code'] = 500
    response['status_message'] = 'Internal server error.'
    response['data'] = {}
    response['cards'] = []
    response['choices'] = []
    response['images'] = []
    response['videos'] = []
    response['recommendations'] = []
    response['API_REQUEST_PACKET'] = {}
    response['API_RESPONSE_PACKET'] = {}
    global result_dict
    try:
        x = ''.join(random.choice(string.ascii_uppercase + string.ascii_lowercase + string.digits) for _ in range(16))
        x='GENIE'+str(x)
        response['data'] = {'tiecodeid':x}
        name="{/name/}"
        policy_number="{/policy_number/}"
        MobileNumber="{/mob_num/}"
        accident_date="{/accident_date/}"
        accident_time="{/accident_time/}"
        
        old_datetime = accident_date+' '+accident_time
        response['old_datetime'] = old_datetime
        
        
        cache =datetime.strptime(old_datetime, '%d-%m-%Y %I:%M %p')

        new_datetime = cache.strftime('%d/%m/%Y %H:%M:%S')
        response['new_datetime'] = new_datetime
        
        
        registration_number="{/regno/}"
        driver_name="{/driver_name/}"
        loss_state="{/loss_state/}"
        loss_city="{/loss_city/}"
        branch_service_name="{/branch_name/}"
        garage_workshop_name="{/garage_workshop_name/}"
        place_of_survey="{/place_of_survey/}"
        cause="{/cause/}"
        loss_desciption="{/loss_desciption/}"
        timestamp = datetime.now().strftime("%d-%b-%Y-%H:%M:%S")
        
        token=GET_SBIGEN_TOKEN()
        url="https://devapi.sbigeneral.in/customers/v1/chatbot/claimintimation"
#        https://devapi.sbigeneral.in/customers/v1/chatbot/claimintimation

        #url=SBIGEN_HOST+"/customers/v1/motoveys/claimintimation"
        headers = {
            'Content-type': 'application/json',
            'X-IBM-Client-Id': "f2faa1e4-df23-4d6c-b218-3f431b5efcfb",
            'X-IBM-Client-Secret': "iY5lJ0bG2xI1rG2kJ2qG5iC3qY7gE3bY3qS3hU1nO8wO4nL2hC",
            'Authorization':token
            }
        payload = {
            "RequestHeader":
                {
                    "requestID": "123456",
                    "action": "claimIntimation",
                    "channel": "SBIG",
                    "transactionTimestamp": timestamp #"01-Feb-2018-01:02:02"
                },    
            "RequestBody":
                {
                    "Claims": 
                        {
                            "ServiceType": "Intimation",
                            "TieUpClaimId": x,
                            "UserId": "20063258",
                            "InsuranceComapany": "UATAICI",
                            "Claim": 
                                {
                                    "PolicyNumber":policy_number ,
                                    "RegistrationNumber": registration_number,
                                    "ContactName": name,
                                    "ClaimServicingbranch": branch_service_name,
                                    "ContactNumber": MobileNumber,
                                    "emailID": "abc@gmail.com",
                                    "AccidentDateandtime": new_datetime, # old_datetime,#"10/02/2018 12:00:00",#new_datetime,
                                    "AccidentAddress": place_of_survey,
                                    "AccidentCity": loss_city,
                                    "AccidentState": loss_state,
                                    "VehicleInspectionAddress":place_of_survey,
                                    "CityName": loss_city, 
                                    "StateName": loss_state,
                                    "InspectionSpotLocation": place_of_survey,
                                    "DriverName":driver_name , 
                                    "isInsured": "Y",  
                                    "ClaimIntimatedBy": "Insured", 
                                    "CauseOfLoss": cause, 
                                    "Others": 'chatbot',
                                    "EstimatedClaimAmount": "12000"
                                }        
                        }   
                } 
            }
            
        response['payload_final'] = str(payload)
        r = requests.request('POST', url ,headers = headers, data = json.dumps(payload), timeout = 20)
        content = json.loads(r.text)
        response['final_content'] =  str(content)
        response['API_REQUEST_PACKET'] = {"url": url, "headers": str(headers), "request_packet": str(payload)}
        response['API_RESPONSE_PACKET'] = {"response_packet": str(content)}
        if str(r.status_code) == '200':
            if content == [] or content == {} or content == 'null' or content == 'None' or content is None:
            	json_response['claim_details_disp'] = 'We are not able to process your request at this point of time. Please try again after sometime'

            elif content != [] or content != {} or content != 'null' or content != 'None' or content is not None:
                response['status_code'] = 200
                response['status_message'] = "Ok"
                response['claim_details_disp'] = "Your Claim Number is: <b>"+content['responseBody'].split('<ClaimNo>')[1].split('</ClaimNo>')[0]+"</b>.<br><br>Please quote the claim number in all future correspondence."
                
            else:
                response['claim_details_disp'] = 'We are not able to fetch your claim details, Kindly chat with expert.'
                response['status_code'] = 308
                response['status_message'] = "REDO"
            
        else:
            response['claim_details_disp'] = 'We are not able to process your request at this point of time due to connectivity issues. Please try again after sometime'
            response['status_code'] = str(r.status_code)
            response['status_message'] = "API Error"
        return response
    except requests.Timeout as E:
        response['claim_details_disp'] = 'We are not able to process your request due to connectivity failure. Please try again after sometime.'
        exc_type, exc_obj, exc_tb = sys.exc_info()
        logger.error('API Timeout: %s at %s',str(E), str(exc_tb.tb_lineno))
        response['status_code'] = 500
        response['status_message'] = 'ERROR :-  '+str(E)+ ' at line no: ' +str(exc_tb.tb_lineno)
        response['status_code'] = 200
        response['status_message'] = "Ok"
        return response

    except Exception as E:
        response['claim_details_disp']='Some internal issues:'
        exc_type, exc_obj, exc_tb = sys.exc_info()
        logger.error('PostProcessorContent: %s at %s',str(E), str(exc_tb.tb_lineno))
        response['status_code'] = '500'
        response['status_message'] = 'ERROR :-  '+str(E)+ ' at line no: ' +str(exc_tb.tb_lineno)
        return response
