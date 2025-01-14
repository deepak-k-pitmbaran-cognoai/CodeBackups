from EasyChatApp.models import * 
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
import uuid
from babel.numbers import format_currency
import datetime

from base64 import b64encode, b64decode
from Crypto.Cipher import AES

def b64encoding(strng):
    return b64encode(strng)

def b64decoding(strng):
    return b64decode(strng)

def mod_aes_cbc_encrypt(plain_text):
    key = "TFRGUzAxMjM0NTY3ODkwMTIzNDU2Nzg5MDEyMzQ1Njc="
    iv = "9ubhEWR9INlAX2vp"
    plain_text = plain_text.encode('utf-8')
    len_plain_text = len(plain_text)
    plain_text = plain_text.decode('utf-8')
    BLOCK_SIZE = 16
    pad = lambda s: s + (BLOCK_SIZE - len_plain_text % BLOCK_SIZE) * chr(BLOCK_SIZE - len_plain_text % BLOCK_SIZE)
    plain_text = pad(plain_text)
    plain_text = plain_text.encode('utf-8')
    key = b64decoding(key)
    iv = iv.encode('utf-8')
    aes = AES.new(key, AES.MODE_CBC, iv)
    encrypted_message = aes.encrypt(plain_text)
    encrypted_message = b64encoding(iv + encrypted_message)
    return encrypted_message
    
def mod_aes_cbc_decrypt(encrypted_message):
    key = "TFRGUzAxMjM0NTY3ODkwMTIzNDU2Nzg5MDEyMzQ1Njc="
    encrypted_message = b64decoding(encrypted_message)
    iv_encrypted = encrypted_message[0:16]
    message = encrypted_message[16:]
    key = b64decoding(key)
    iv = iv_encrypted
    aes = AES.new(key, AES.MODE_CBC, iv)
    plain_text = aes.decrypt(message)
    unpad = lambda s: s[:-ord(s[len(s) - 1:])]
    plain_text = unpad(plain_text)
    plain_text = plain_text.decode('utf-8')
    return plain_text
    

def f():
    response = {}
    response['status_code'] = 500
    response['status_message'] = 'Internal server error.'
    response['data'] = {}
    response['cards'] = []
    response['choices'] = []
    response['images'] = []
    response['videos'] = []
    response['recommendations'] = ['Main Menu']
    response['API_REQUEST_PACKET'] = {}
    response['API_RESPONSE_PACKET'] = {}
    global result_dict
    response['loan_show'] = result_dict['tech_error']()
    try:
        #write your code here
        LAN = '{/CustomerLAN/}'
        mobile = '{/CustomerMobile/}'
        lob = '{/lob/}'
        channel = '{/QueryChannel/}'
        email = '{/CustomerEmail/}'
        account_status = '{/AccountStatus/}'
        null = None
        emi = '{/CustomerEmi/}'        
        encrypted_lan = mod_aes_cbc_encrypt(LAN).decode("utf-8")
        #lob_reverse_dict = {'Two Wheeler':'Two-Wheeler Loan','Farm':'Farm/Tractor Loan','Consumer Loan':'Consumer Loan','Home Loan':'Home Loan'}
        #intent = lob_reverse_dict[lob]
        loan_show = f"Please find the requested details:-<br><br>1. Account Status: <b>{account_status.title()}</b><br>"
        
        if email.lower() == 'na' or email.lower == '' or email == 'None':
            email = ""
        
        url, headers = result_dict['service_api']()
        
        
        service = "COREAPI_SV2"
        
        req_id = str(int(uuid.uuid4()))
        if channel.lower() == 'whatsapp':
            
#            req_channel = 'CWABA'
            req_channel = 'CB'
            req_id = req_channel + req_id
            user_group = 'WSBOT'
             
        else:
            req_channel = 'CB'
            req_id = req_channel + req_id
            # user_group = 'CSBOT' #as asked by client on 6 dec 2024  to change it to cb
            user_group = 'CB'
        
        payload = {
                "userRole": req_channel, 
                "userIp": "3.7.75.224", 
#                "userId": "prashantjadhav@ltfs.com.ltfs", 
                'userId': 'CB', 
#                "userGroup": "System Administrator", 
                "userGroup": user_group,
                "toDate": "",
                "srId": req_id,
                "serviceName": "COREAPI_SV2",
                "mobileNo": mobile,
                "lob": str(lob),
                "level": "1",
                "lanId": encrypted_lan,
                "fromDate": "",
                "emailId": "",
                "closureDate": "", 
                "channel": req_channel, 
                "authMode": "1", 
                "assessmentYear": ""
            }
            
        response[f'loan_sv2_payload'] = payload
        
        roi = "None"
        response['API_REQUEST_PACKET']["COREAPI_SV2"] = {"url":url,"headers":headers,"data":payload}
        resp = requests.post(url = url, data = json.dumps(payload), headers = headers, timeout = 15)
        resp_content = json.loads(resp.text)
        response['API_RESPONSE_PACKET']["COREAPI_SV2"] = {"response": resp_content}
        if resp.status_code == 200 and resp_content["statusCode"] == "200" and "cust_Details" in resp_content:
            roi = resp_content['cust_Details']['effRate']
            response['effRate'] = roi
            
            loan_amount = resp_content['cust_Details']['disbursAmount']
            response['loan_amount'] = loan_amount
        
        for service in ["COREAPI_SV3","COREAPI_SV4"]:
            req_id = str(int(uuid.uuid4()))
            if channel.lower() == 'whatsapp':
                
    #            req_channel = 'CWABA'
                req_channel = 'CB'
                req_id = req_channel + req_id
                user_group = 'WSBOT'
                 
            else:
                req_channel = 'CB'
                req_id = req_channel + req_id
                # user_group = 'CSBOT' #as asked by client on 6 dec 2024  to change it to cb
                user_group = 'CB'
            payload["serviceName"] = service
            payload["srId"]  = req_id
            response[f'loan_{service}_payload'] = payload
            response['API_REQUEST_PACKET'][service] = {"url":url,"headers":headers,"data":payload} 
            try:
                resp = requests.post(url = url, data = json.dumps(payload), headers = headers, timeout = 15)
            except Exception as E:
                exc_type, exc_obj, exc_tb = sys.exc_info()
                logger.error('ApiTreeContent: %s at %s',str(E), str(exc_tb.tb_lineno), extra={'AppName': 'EasyChat', 'user_id': 'None', 'source': 'None', 'channel': 'None', 'bot_id': 'None'})
                response['status_code'] = result_dict['timeout_status']()
                response['status_message'] = 'ERROR :-  '+str(E)+ ' at line no: ' +str(exc_tb.tb_lineno)
                response['API_RESPONSE_PACKET'][service] = {"response":str(E)}
                response['loan_show'] = result_dict['tech_error']()
                response['recommendations'] = result_dict['options'](lob)
                return response                
            response[f'loan_{service}_response'] = resp.text
            response['API_RESPONSE_PACKET'][service] = {"response":resp.text}             
    
            if resp.status_code == 200:
                resp = json.loads(resp.text)                    
                response[f'loan_{service}_response'] = resp 
                response['API_RESPONSE_PACKET'][service] = {"response":resp}
                null = None        
                if resp['statusCode'] == '200':

                    # if service == "COREAPI_SV3":
                    if service == "COREAPI_SV3":
                        try:
                            tenure = resp['asset_Details']['tenure']
                            installments = resp['asset_Details']['noInstl']
                            balance_tenure = resp['asset_Details']['reNoInstl']
                        except Exception as e:
                            response['status_code'] = 500
                            response['API_RESPONSE_PACKET']['Proc_Err'] = response['status_message'] = f'RESPONSE {service} ERROR 1 {str(e)}'
                            response['loan_show'] = result_dict['tech_error']()
                            response['recommendations'] = result_dict['options'](lob)
                            return response
                    else:
                        try:
#                            last_emi = datetime.datetime.strptime(resp['mandate_Details']['last_Payment_Date'],'%Y-%m-%d %H:%M:%S').strftime('%d-%m-%Y') if resp['mandate_Details']['last_Payment_Date'] != "" else ""
#                            next_emi = datetime.datetime.strptime(resp['mandate_Details']['next_Emi_Date'],'%Y-%m-%d %H:%M:%S').strftime('%d-%m-%Y') if resp['mandate_Details']['next_Emi_Date'] != "" else ""                           
                            try:
                                last_emi = resp['mandate_Details']['last_Payment_Date'] if resp['mandate_Details']['last_Payment_Date'] != "" and resp['mandate_Details']['last_Payment_Date'] != None else "N/A"
                                next_emi = resp['mandate_Details']['next_Emi_Date'] if resp['mandate_Details']['next_Emi_Date'] != "" else "N/A"
                                principle_os = resp['mandate_Details']['principle_os']if resp['mandate_Details']['principle_os'] != "" else null
                            except:
                                last_emi = datetime.datetime.strptime(resp['mandate_Details']['last_Payment_Date'],'%Y-%m-%d %H:%M:%S').strftime('%d-%m-%Y') if resp['mandate_Details']['last_Payment_Date'] != "" and resp['mandate_Details']['last_Payment_Date'] != None else "N/A"
                                next_emi = datetime.datetime.strptime(resp['mandate_Details']['next_Emi_Date'],'%Y-%m-%d %H:%M:%S').strftime('%d-%m-%Y') if resp['mandate_Details']['next_Emi_Date'] != "" else "N/A"                           
                                principle_os = resp['mandate_Details']['principle_os']if resp['mandate_Details']['principle_os'] != "" else "N/A"
                        except Exception as E:
                            response['status_code'] = 500
                            response['API_RESPONSE_PACKET']['Proc_Err'] = response['status_message'] = f'RESPONSE {service} ERROR 2'
                            exc_type, exc_obj, exc_tb = sys.exc_info()
                            logger.error('RESPONSE {service} ERROR 2: %s at %s',str(E), str(exc_tb.tb_lineno), extra={'AppName': 'EasyChat', 'user_id': 'None', 'source': 'None', 'channel': 'None', 'bot_id': 'None'})
                            response['loan_show'] = result_dict['tech_error']()
                            response['recommendations'] = result_dict['options'](lob)
                            return response                            
                else:
                    response['status_code'] = 500
                    response['status_message'] = f'RESPONSE {service} ERROR 3'
                    response['loan_show'] = result_dict['tech_error']()
                    response['recommendations'] = result_dict['options'](lob)
                    return response                                                
                        
        # formatting currencies
        
        emi_amount = format_currency(emi, 'INR', locale='en_IN') if emi != null and float(emi) > 0.0 else format_currency(0, 'INR', locale='en_IN')
        
        principle_outstanding = format_currency(principle_os, 'INR', locale='en_IN')  if principle_os != null  and float(principle_os) > 0.0 else format_currency(0, 'INR', locale='en_IN')
        
        formatted_loan_amount = format_currency(loan_amount, 'INR', locale='en_IN')  if loan_amount != null and float(loan_amount) > 0.0 else format_currency(0, 'INR', locale='en_IN')
        
        details = {
                "EMI Amount: ": emi_amount,
                "Last payment date:": last_emi,
                "Next EMI date: ": next_emi,
                "No. of Installments: ": installments,
                "ROI: ": f"{round(float(roi), 2):.2f}%" if roi != "None" else "None",
                "Tenure: ": f"{tenure} months" if tenure != "None" else "None",
                "Balance Tenure: ": f"{balance_tenure} months" if balance_tenure not in ["None"] else "None",
                "Principle Outstanding: ": principle_outstanding,
                # "Loan Amount: ": formatted_loan_amount,  # Uncomment if loan amount needs to be included
            }
            
        count = 1
        
        for label, value in details.items():
            if value != "None":
                count += 1
                loan_show += f"{count}. {label}<b>{value}</b><br>"
                
        
        try:
            logger.error('Into push case api-------------', extra={'AppName': 'EasyChat', 'user_id': 'None', 'source': 'None', 'channel': 'None', 'bot_id': 'None'})
            push_case_status = result_dict['pushCase'](service_name='LoanDetails', lan_number=LAN)
            
            logger.error('Into push case api status-------------%s',str(push_case_status), extra={'AppName': 'EasyChat', 'user_id': 'None', 'source': 'None', 'channel': 'None', 'bot_id': 'None'})
            
        except Exception as E:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            logger.error('ApiTreeContent: %s at %s',str(E), str(exc_tb.tb_lineno), extra={'AppName': 'EasyChat', 'user_id': 'None', 'source': 'None', 'channel': 'None', 'bot_id': 'None'})
            response['status_code'] = 500
            response['API_RESPONSE_PACKET']['Proc_Err'] = response['status_message'] = 'ERROR :-  '+str(E)+ ' at line no: ' +str(exc_tb.tb_lineno)
            response['loan_show'] = result_dict['tech_error']()
            
        response['status_code'] = '200'
        response['status_message'] = 'SUCCESS'
        response['recommendations'] = result_dict['options'](lob)
        response['loan_show'] = loan_show                
        response['print'] = 'Hello world!'
        return response
    except Exception as E:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        logger.error('ApiTreeContent: %s at %s',str(E), str(exc_tb.tb_lineno), extra={'AppName': 'EasyChat', 'user_id': 'None', 'source': 'None', 'channel': 'None', 'bot_id': 'None'})
        response['status_code'] = 500
        response['API_RESPONSE_PACKET']['Proc_Err'] = response['status_message'] = 'ERROR :-  '+str(E)+ ' at line no: ' +str(exc_tb.tb_lineno)
        response['loan_show'] = result_dict['tech_error']()
        try:
            response['recommendations'] = result_dict['options'](lob)
        except:
            response['recommendations'] = ['Main Menu']
        return response
