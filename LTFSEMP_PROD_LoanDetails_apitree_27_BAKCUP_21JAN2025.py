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
        LAN = '{/CustomerLan/}'
        mobile = '{/CustomerMobile/}'
        lob = '{/lob/}'
        channel = '{/MessageChannel/}'
        email = '{/CustomerEmail/}'
        account_status = '{/AccountStatus/}'
        emi = '{/CustomerEmi/}'        
        #lob_reverse_dict = {'Two Wheeler':'Two-Wheeler Loan','Farm':'Farm/Tractor Loan','Consumer Loan':'Consumer Loan','Home Loan':'Home Loan'}
        #intent = lob_reverse_dict[lob]
        
        if email.lower() == 'na' or email.lower == '' or email == 'None':
            email = ""
        
        url, headers = result_dict['service_api']()
        
        loan_show = f"Please find the requested details:-<br><br>1. Account Status: <b>{account_status.capitalize()}</b><br>"
        
        for service in ["COREAPI_SV3","COREAPI_SV4"]:
            req_id = str(int(uuid.uuid4()))
            if channel.lower() == 'whatsapp':
                
                req_channel = 'CWABA'
                req_id = req_channel + req_id
                 
            else:
                req_channel = 'CB'
                req_id = req_channel + req_id
            
            payload = {
                "userRole": req_channel, 
                "userIp": "3.7.75.224", 
#                "userId": "prashantjadhav@ltfs.com.ltfs", 
                "userId": req_channel,
                "userGroup": "ESBOT", 
                "toDate": "",
                "srId": req_id,
                "serviceName": service,
                "mobileNo": mobile,
                "lob": str(lob),
                "level": "1",
                "lanId": LAN,
                "fromDate": "",
                "emailId": "",
                "closureDate": "", 
                "channel": req_channel, 
                "authMode": "1", 
                "assessmentYear": ""
            }
            response[f'loan_{service}_payload'] = payload
            response['API_REQUEST_PACKET'] = {"url":url,"headers":headers,"data":payload} 
            try:
                resp = requests.post(url = url, data = json.dumps(payload), headers = headers, timeout = 15)
            except Exception as E:
                exc_type, exc_obj, exc_tb = sys.exc_info()
                logger.error('ApiTreeContent: %s at %s',str(E), str(exc_tb.tb_lineno), extra={'AppName': 'EasyChat', 'user_id': 'None', 'source': 'None', 'channel': 'None', 'bot_id': 'None'})
                response['status_code'] = result_dict['timeout_status']()
                response['status_message'] = 'ERROR :-  '+str(E)+ ' at line no: ' +str(exc_tb.tb_lineno)
                response['API_RESPONSE_PACKET'] = {"response":str(E)}
                response['loan_show'] = result_dict['tech_error']()
                response['recommendations'] = result_dict['options'](lob)
                return response                
            response[f'loan_{service}_response'] = resp.text
            response['API_RESPONSE_PACKET'] = {"response":resp.text}             
    
            if resp.status_code == 200:
                resp = json.loads(resp.text)                    
                response[f'loan_{service}_response'] = resp 
                response['API_RESPONSE_PACKET'] = {"response":resp}
                null = None        
                if resp['statusCode'] == '200':

                    if service == "COREAPI_SV3":
                        try:
                            tenure = resp['asset_Details']['tenure']
                            installments = resp['asset_Details']['noInstl']
                            roi = resp['asset_Details']['roi']
                            balance_tenure = resp['asset_Details']['reNoInstl']
                        except:
                            response['status_code'] = 500
                            response['status_message'] = f'RESPONSE {service} ERROR 1'
                            response['loan_show'] = result_dict['tech_error']()
                            response['recommendations'] = result_dict['options'](lob)
                            return resopnse
                    else:
                        try:
#                            last_emi = datetime.datetime.strptime(resp['mandate_Details']['last_Payment_Date'],'%Y-%m-%d %H:%M:%S').strftime('%d-%m-%Y') if resp['mandate_Details']['last_Payment_Date'] != "" else ""
#                            next_emi = datetime.datetime.strptime(resp['mandate_Details']['next_Emi_Date'],'%Y-%m-%d %H:%M:%S').strftime('%d-%m-%Y') if resp['mandate_Details']['next_Emi_Date'] != "" else ""                           
                            try:
                                last_emi = resp['mandate_Details']['last_Payment_Date'] if resp['mandate_Details']['last_Payment_Date'] != "" else "N/A"
                                next_emi = resp['mandate_Details']['next_Emi_Date'] if resp['mandate_Details']['next_Emi_Date'] != "" else "N/A"
                            except:
                                last_emi = datetime.datetime.strptime(resp['mandate_Details']['last_Payment_Date'],'%Y-%m-%d %H:%M:%S').strftime('%d-%m-%Y') if resp['mandate_Details']['last_Payment_Date'] != "" else "N/A"
                                next_emi = datetime.datetime.strptime(resp['mandate_Details']['next_Emi_Date'],'%Y-%m-%d %H:%M:%S').strftime('%d-%m-%Y') if resp['mandate_Details']['next_Emi_Date'] != "" else "N/A"                           
                        except Exception as E:
                            response['status_code'] = 500
                            response['status_message'] = f'RESPONSE {service} ERROR 2'
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
                        
        emi_amount = format_currency(emi, 'INR', locale='en_IN') if emi != null and float(emi) > 0.0 else format_currency(0, 'INR', locale='en_IN')                        
        loan_show += "2. EMI Amount: <b>" + emi_amount + "</b><br>"
        loan_show += "3. Last payment date: <b>" + last_emi + "</b><br>"
        loan_show += "4. Next EMI date: <b>" + next_emi + "</b><br>"
        loan_show += "5. No. of Installments: <b>" + installments + "</b><br>"
        loan_show += "6. ROI: <b>" + str(round(float(roi), 2)) + " %</b><br>"
        loan_show += "7. Tenure: <b>" + tenure + " Months</b><br>"
        loan_show += "8. Balance Tenure: <b>" + balance_tenure + " Months</b><br>"
        loan_show += "$$$Please select below option to proceed further:"
            
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
        response['status_message'] = 'ERROR :-  '+str(E)+ ' at line no: ' +str(exc_tb.tb_lineno)
        response['loan_show'] = result_dict['tech_error']()
        try:
            response['recommendations'] = result_dict['options'](lob)
        except:
            response['recommendations'] = ['Main Menu']
        return response
