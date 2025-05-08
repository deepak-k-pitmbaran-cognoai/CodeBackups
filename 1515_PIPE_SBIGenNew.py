from EasyChatApp.models import * 
from EasyChatApp.utils_sbigen_functions import *
result_dict = {}
try:
    common_utils_obj = CommonUtilsFile.objects.filter(bot=Bot.objects.get(pk=1)) 
    exec(str(common_utils_obj[0].code), result_dict) 
except Exception:
    pass 
from EasyChatApp.utils import logger
import sys
import json
import requests
import xmltodict
import random,string
from datetime import datetime

def f(x):
    json_response = {}
    json_response['status_code'] = '500'
    json_response['status_message'] = 'Internal server error.'
    json_response['recur_flag'] = False
    json_response['message'] = 'testing'
    json_response['API_REQUEST_PACKET'] = {}
    json_response['API_RESPONSE_PACKET'] = {}
    json_response['data'] = {}
    global result_dict
    try:
        x = ''.join(random.choice(string.ascii_uppercase + string.ascii_lowercase + string.digits) for _ in range(16))
        x='GENIE'+str(x)
        json_response['data'] = {'tiecodeid':x}
        name="{/name/}"
        policy_number="{/policy_number/}"
        fromdate="{/eff_date/}"
        todate="{/to_date/}"
        MobileNumber="{/mob_num/}"
        accident_date="{/accident_date/}"
        accident_time="{/accident_time/}"
        
        old_datetime = accident_date+' '+accident_time
        json_response['old_datetime'] = old_datetime
        
        
        cache =datetime.strptime(old_datetime, '%d-%m-%Y %I:%M %p')

        new_datetime = cache.strftime('%d/%m/%Y %H:%M:%S')
        #new_datetime = cache.strftime('%m/%d/%Y %H:%M:%S')
        json_response['new_datetime'] = new_datetime
        
        
        registration_number="{/regno/}"
        driver_name="{/driver_name/}"
        loss_state="{/loss_state/}"
        loss_city="{/loss_city/}"
        branch_service_name="{/branch_name/}"
        garage_workshop_name="{/garage_workshop_name/}"
        place_of_survey="{/place_of_survey/}"
        cause="{/cause/}"
        loss_desciption="{/loss_desciption/}"
        
        token=GET_SBIGEN_TOKEN()
#        url=SBIGEN_HOST+"/customers/v1/chatbot/claimintimation"
        url=SBIGEN_HOST+"/customers/v1/motoveys/claimintimation"
        headers = {
            'Content-type': 'application/json',
            'X-IBM-Client-Id':CLIENT_ID,
            'X-IBM-Client-Secret':CLIENT_SECRET_KEY,
            'Authorization':token
            }
        payload = {
            "RequestHeader":
                {
                    "requestID": "123456",
                    "action": "claimIntimation",
                    "channel": "SBIG",
                    "transactionTimestamp": "01-Feb-2018-01:02:02"
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
                                    "AccidentDateandtime":new_datetime,
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
                                    "Others":"fd",
                                    "EstimatedClaimAmount": "12000"
                                }        
                        }   
                } 
            }
            
        json_response['API_REQUEST_PACKET'] = {"url": url, "headers": str(headers), "request_packet": str(payload)}
        json_response['payload_final'] = payload    
        r = requests.request('POST', url ,headers = headers, data = json.dumps(payload), timeout = 20)
        content = json.loads(r.text)
        json_response['final_content'] =  str(content)
        json_response['API_RESPONSE_PACKET']["response_packet"] = str(content)
        if str(r.status_code) == '200':
            if content == [] or content == {} or content == 'null' or content == 'None' or content is None:
                json_response['data']['claim_details_disp'] = 'We are not able to process your request at this point of time. Please try again after sometime'

            elif content != [] or content != {} or content != 'null' or content != 'None' or content is not None:    
                json_response['status_message'] = "Ok"
                json_response['data']['claim_details_disp'] = "Your Claim Number is: <b>"+content['responseBody'].split('<ClaimNo>')[1].split(
                    '</ClaimNo>')[0]+"</b><br><br>Please quote the claim number in all future correspondence."
                json_response['data']['claim_number'] = content['responseBody'].split('<ClaimNo>')[1].split('</ClaimNo>')[0]

            else:
                json_response['data']['claim_details_disp'] = 'We are not able to fetch your claim details, Kindly chat with expert.'
                json_response['status_message'] = "REDO"
        
        else:
            json_response['data']['claim_details_disp'] = 'We are not able to process your request at this point of time due to connectivity issues. Please try again after sometime'
            json_response['status_message'] = "API Error"

        return json_response
    
    except requests.Timeout as E:
        json_response['data']['claim_details_disp'] = 'We are not able to process your request due to connectivity failure. Please try again after sometime.'
        exc_type, exc_obj, exc_tb = sys.exc_info()
        logger.error('API Timeout: %s at %s',str(E), str(exc_tb.tb_lineno))
        json_response['status_message'] = 'ERROR :-  '+str(E)+ ' at line no: ' +str(exc_tb.tb_lineno)
        json_response['status_code'] = 200
        json_response['status_message'] = "API Failed"
        return json_response
    
    except Exception as E:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        logger.error('PipeProcessorContent: %s at %s',
                     str(E), str(exc_tb.tb_lineno))
        json_response['status_code'] = '500'
        json_response['status_message'] = 'ERROR :-  ' + \
            str(E) + ' at line no: ' + str(exc_tb.tb_lineno)
        return json_response