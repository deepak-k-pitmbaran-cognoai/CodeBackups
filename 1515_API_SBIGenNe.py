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
import base64

def call_eClaimForm_API(processor_dict, **kwargs):
    try:
        token = GET_SBIGEN_TOKEN()

        url = processor_dict["API_REQUEST_PACKET"]["url"] = f"{SBIGEN_HOST}/custportal/v1/eclaim-form" #"https://172.18.233.97:8443/custportal/v1/eclaim-form" #"https://uatweb.sbigeneral.in/cp-api/api/eclaim/claimintimation-url"

        headers =  {
            "Content-Type": "application/json",
            "X-IBM-Client-Id": CLIENT_ID,
            "X-IBM-Client-Secret": CLIENT_SECRET_KEY,
            "Authorization": f"Bearer {token}"
        }
        
        processor_dict["API_REQUEST_PACKET"]["headers"] = str(headers)

        payload =  {
                "ClaimNo": kwargs.get("claim_number"),
                "PolicyNo": kwargs.get("policy_number"),
                "Name": kwargs.get("name"),
                "Address": "",
                "City": "",
                "State": "",
                "PinCode": "",
                "Phone": "",
                "Mobile": kwargs.get("MobileNumber"),
                "Email": "",
                "PAN": "",
                "RegistrationNo": "",
                "Engine": "",
                "Chassis": "",
                "OccurrenceDate": "",
                "OccurrenceTime": "",
                "LossDescription": "",
                "EstimatedLossAmount": "",
                "AadharNo": ""
            }
        processor_dict["API_REQUEST_PACKET"]["payload"] = str(payload)
        
        # encrypting the payload
        enc = EncryptionHelper()
        encrypted_data = enc.encrypt(json.dumps(payload))
        enc_str = base64.b64encode(encrypted_data).decode('utf-8')\
        
        processor_dict["print_dec_enc_str"] = enc.decrypt(encrypted_data)

        payload = json.dumps({
            "ciphertext":enc_str
            })
        
        processor_dict["API_REQUEST_PACKET"]["enc_payload"] = payload 

        api_response = requests.request("POST", url, headers=headers, data=payload, timeout=20)

        processor_dict['API_RESPONSE_PACKET']["response"] = api_response.text

        if str(api_response.status_code) not in ["200", "201"]:
            raise requests.RequestException(f"API Failed with status code {api_response.status_code}")
        
        content = api_response.json()
#        enc_resp = json.loads(api_response.text)
#
#        ciphertext = enc_resp.get('ciphertext')
#
#        if not ciphertext:
#            raise requests.RequestException(f"API Failed ciphertext in response not found")
#
#        encrypted_bytes = base64.b64decode(ciphertext)
#        
#        decrypted_resp = enc.decrypt(encrypted_bytes)
#        processor_dict['API_RESPONSE_PACKET']["decryptedCipherText"] = decrypted_resp
#        content = json.loads(decrypted_resp)

        return str(api_response.status_code), content
    
    except requests.RequestException as e:
        processor_dict['API_RESPONSE_PACKET']["requestError"] = str(e)
        raise requests.RequestException(str(e))

    except Exception as e:
        raise Exception(str(e))




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
        claim_number = "{/claim_number/}"
        name = "{/name/}"
        policy_number = "{/policy_number/}"
        MobileNumber = "{/mob_num/}"
        claim_details_disp = "{/claim_details_disp/}"
        
        response['claim_details_disp'] = claim_details_disp
        response['status_code'] = "200"
        
        if str(claim_number).lower() == "none":
            response["status_message"] = "Claim number not generated or API Failed in Pipe processor"
            return response
        
        status_code, content = call_eClaimForm_API(response, claim_number=claim_number,
                                                   name=name,
                                                   policy_number=policy_number,
                                                   MobileNumber=MobileNumber)
        
        form_url = content.get("Url")
        ref_num = content.get("RefNo", "N/A")

        if not form_url:
            raise requests.RequestException("Form URL is not present in the API Response")
        
        resp_text = (f"Your Claim Number is: <b>{claim_number}</b><br>"
            "Please click on the link below to submit the E-Claim form, which is mandatory to proceed with processing your Claim Intimation request")
        resp_text += f"<br><br>{form_url}"
        response['claim_details_disp'] = resp_text
        response['status_message'] = "Success!"
        return response

    except requests.RequestException as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        response['status_code'] = "400"
        response['status_message'] = 'ERROR :-  '+str(e)+ ' at line no: ' +str(exc_tb.tb_lineno)
        logger.error(f'check PostProcessorContent: API Failed! {response["API_REQUEST_PACKET"]} response {response["API_RESPONSE_PACKET"]}', extra=extra_param)
        response['claim_details_disp'] = 'We are not able to process your request due to connectivity failure. Please try again after sometime.'
        return response
    
    except Exception as E:
        response['claim_details_disp']='Some internal issues:...'
        exc_type, exc_obj, exc_tb = sys.exc_info()
        logger.error('PostProcessorContent: %s at %s',str(E), str(exc_tb.tb_lineno))
        response['status_code'] = '500'
        response['status_message'] = 'ERROR :-  '+str(E)+ ' at line no: ' +str(exc_tb.tb_lineno)
        return response
