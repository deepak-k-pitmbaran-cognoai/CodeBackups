from EasyChatApp.models import *
result_dict = {}
try:
    common_utils_obj = CommonUtilsFile.objects.filter(bot=Bot.objects.get(pk=1))
    exec(str(common_utils_obj[0].code), result_dict)
except Exception:
    pass
from EasyChatApp.utils import logger, get_secure_file_path
import sys
import uuid
import json
import requests
import datetime
import base64
from django.conf import settings
import shutil

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
    response['doc_show'] = result_dict['tech_error']()
    try:
        lob = '{/lob/}'
        LAN = '{/CustomerLAN/}'
        encrypted_lan = mod_aes_cbc_encrypt(LAN).decode("utf-8")
        mobile = '{/CustomerMobile/}'
        channel = '{/QueryChannel/}'
        doc_type = '{/DocType/}'
        response['print1'] = doc_type
        response['print2'] = str(type(doc_type))
        EasyChatChannel = '{/EasyChatChannel/}'
        response['data']['rec'] = result_dict['options'](lob)
        
        
        is_redirected = '{/is_redirected/}'
        
        if str(is_redirected) == "True":
            response['recommendations'] = result_dict['options'](lob)
            response['data']['is_redirected'] = 'False'
            response['status_code'] = '200'
            response['status_message'] = 'Success'
            return response
        
        
        user_id = '{/EasyChatUserID/}'
        logger.error('lob ------------------: %s',str(lob), extra={'AppName': 'EasyChat', 'user_id': 'None', 'source': 'None', 'channel': 'None', 'bot_id': 'None'})
        logger.error('LAN ------------------: %s',str(LAN), extra={'AppName': 'EasyChat', 'user_id': 'None', 'source': 'None', 'channel': 'None', 'bot_id': 'None'})
        logger.error('mobile ------------------: %s',str(mobile), extra={'AppName': 'EasyChat', 'user_id': 'None', 'source': 'None', 'channel': 'None', 'bot_id': 'None'})
        logger.error('channel ------------------: %s',str(channel), extra={'AppName': 'EasyChat', 'user_id': 'None', 'source': 'None', 'channel': 'None', 'bot_id': 'None'})
        logger.error('doc_type ------------------: %s',str(doc_type), extra={'AppName': 'EasyChat', 'user_id': 'None', 'source': 'None', 'channel': 'None', 'bot_id': 'None'})
        logger.error('USERID ------------------: %s',str(user_id), extra={'AppName': 'EasyChat', 'user_id': 'None', 'source': 'None', 'channel': 'None', 'bot_id': 'None'})
        today = datetime.datetime.now().strftime('%Y-%m-%d')
        
        email = ""

        #NOC count logic
        req_id = str(int(uuid.uuid4()))
        if channel.lower() == 'whatsapp':

            #            req_channel = 'CWABA'
            req_channel = 'CB'
            req_id = req_channel + req_id
            user_group = 'WSBOT'

        else:
            req_channel = 'CB'
            req_id = req_channel + req_id
            user_group = 'CSBOT'

        noc_count_url, noc_count_headers = result_dict['noc_generation_count_api']()

        noc_count_payload = {
            "lan_Id": encrypted_lan,
            "mobile_No": "NA",                                                  #"srId": req_id  -- commenting because client said it is of NO USE.
            "lob": lob
        }
        
        # commented this as NOC Doc count has been implemented in different way after production migration this can be depricated.
        response['API_REQUEST_PACKET']['NOC_Count_Req'] = {"url":noc_count_url,"headers":noc_count_headers,"data":noc_count_payload}
        logger.error('NOC Count payload ------------------: %s',str(noc_count_payload), extra={'AppName': 'EasyChat', 'user_id': 'None', 'source': 'None', 'channel': 'None', 'bot_id': 'None'})
        try:
            noc_count_response = requests.post(url = noc_count_url, data = json.dumps(noc_count_payload), headers = noc_count_headers, timeout = 20)
            response['API_RESPONSE_PACKET']['NOC_GEN_COUNT_Resp'] = {"response":str(noc_count_response.text)}
            logger.error('NOC Count response ------------------: %s',str(noc_count_response.text), extra={'AppName': 'EasyChat', 'user_id': 'None', 'source': 'None', 'channel': 'None', 'bot_id': 'None'})
            logger.error('NOC Count response status code------------------: %s',str(noc_count_response.status_code), extra={'AppName': 'EasyChat', 'user_id': 'None', 'source': 'None', 'channel': 'None', 'bot_id': 'None'})
        except Exception as E:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            logger.error('ApiTreeContent: %s at %s',str(E), str(exc_tb.tb_lineno), extra={'AppName': 'EasyChat', 'user_id': 'None', 'source': 'None', 'channel': 'None', 'bot_id': 'None'})
            response['status_code'] = result_dict['timeout_status']()
            response['status_message'] = 'ERROR :-  '+str(E)+ ' at line no: ' +str(exc_tb.tb_lineno)
            response['doc_show'] = result_dict['tech_error']()
            response['recommendations'] = result_dict['options'](lob)
            response['API_REQUEST_PACKET']['NOC_Count_Req'] = {"url":noc_count_url,"headers":noc_count_headers,"data":noc_count_payload}
            response['API_RESPONSE_PACKET']['NOC_GEN_COUNT_Resp'] = {"response":str(E)}
            return response
        
        response['API_RESPONSE_PACKET']['NOC_GEN_COUNT_Resp'] = {"response":noc_count_response.text}
        
        if noc_count_response.status_code == 200:
            noc_count_resp = noc_count_response.json()
            noc_generated_count_single = 0
            noc_generated_count_nocd = 0
            noc_generated_count_nocb = 0
            noc_generated_count_form35 = 0
            for noc_objects in noc_count_resp:
                if lob in ['Consumer Loan']:
                    logger.error('noc_objects ------------------: %s',str(noc_objects["status"]), extra={'AppName': 'EasyChat', 'user_id': 'None', 'source': 'None', 'channel': 'None', 'bot_id': 'None'})
                    if noc_objects["status"] == "SUCCESS":
                        noc_generated_count_single += 1
                else:
                    if noc_objects["status"] == "SUCCESS" and noc_objects["reportName"] == "NOCD":
                        noc_generated_count_nocd += 1
                    elif noc_objects["status"] == "SUCCESS" and noc_objects["reportName"] == "NOCB":
                        noc_generated_count_nocb += 1
                    elif noc_objects["status"] == "SUCCESS" and noc_objects["reportName"] == "FORM35D":
                        noc_generated_count_form35 += 1

            logger.error('noc_generated_count_single ------------------: %s',str(noc_generated_count_single), extra={'AppName': 'EasyChat', 'user_id': 'None', 'source': 'None', 'channel': 'None', 'bot_id': 'None'})
            logger.error('noc_generated_count_nocd ------------------: %s',str(noc_generated_count_nocd), extra={'AppName': 'EasyChat', 'user_id': 'None', 'source': 'None', 'channel': 'None', 'bot_id': 'None'})
            logger.error('noc_generated_count_nocb ------------------: %s',str(noc_generated_count_nocb), extra={'AppName': 'EasyChat', 'user_id': 'None', 'source': 'None', 'channel': 'None', 'bot_id': 'None'})
            logger.error('noc_generated_count_form35 ------------------: %s',str(noc_generated_count_form35), extra={'AppName': 'EasyChat', 'user_id': 'None', 'source': 'None', 'channel': 'None', 'bot_id': 'None'})

            if noc_generated_count_single >= 19 or noc_generated_count_nocd >= 19 or noc_generated_count_nocb >= 19 or noc_generated_count_form35 >= 19:
                noc_generation_allowed = False
            else:
                noc_generation_allowed = True
        else:
            noc_generation_allowed = False
            response['status_code'] = result_dict['timeout_status']()
            response['status_message'] = 'API Failure Status code: ' + str(noc_count_response.status_code)
            response['doc_show'] = result_dict['tech_error']()
            response['recommendations'] = result_dict['options'](lob)
            response['API_REQUEST_PACKET'] = {"url":url,"headers":headers,"data":payload}
            response['API_RESPONSE_PACKET']['NOC_GEN_COUNT_Resp'] = {"response":str(noc_count_response.text)}
            return response
            #NOC count logic
        

        URL, Headers = result_dict['noc_api']()


        if lob in ['Two Wheeler','Farm']:
            docs = [f'NOC{doc_type[-1]}',f'NDC{doc_type[-1]}',f'FORM35{doc_type[-1]}']
        else:
            docs = [f'NDC{doc_type[-1]}']

        cards = []

        doc_len = len(docs)
        doc_show = ""
        doc_ext = ""
        count = 0
        noc_doc_api_ctr = 0
        logger.error('docs ------------------: %s',str(docs), extra={'AppName': 'EasyChat', 'user_id': 'None', 'source': 'None', 'channel': 'None', 'bot_id': 'None'})
        logger.error('doc_len ------------------: %s',str(doc_len), extra={'AppName': 'EasyChat', 'user_id': 'None', 'source': 'None', 'channel': 'None', 'bot_id': 'None'})
        doc_show = f"Dear Customer,<br><br>As requested by you please find below the"
        if noc_generation_allowed:
            for doc in docs:
                logger.error('doc ------------------: %s',str(doc), extra={'AppName': 'EasyChat', 'user_id': 'None', 'source': 'None', 'channel': 'None', 'bot_id': 'None'})
    #                print(doc)
    
                req_id = str(int(uuid.uuid4()))
                if channel.lower() == 'whatsapp':
    
                    # req_channel = 'CWABA'
                    req_channel = 'CB'
                    req_id = req_channel + req_id
                    user_group = 'WSBOT'
                    origin = "Whatsapp Bot"
    
                else:
                    req_channel = 'CB'
                    req_id = req_channel + req_id
                    user_group = 'CSBOT'
                    origin = "CS Bot"
    
                payload = {
                    "userRole": req_channel,
                    "userIp": "3.7.75.224",
                    "userId": "CB",
                    # "userGroup": "Chatbot",
                    "userGroup": user_group,
                    "srId": req_id,
                    "serviceName": doc,
                    "lob": lob,
                    "level": "1",
                    "lanId": encrypted_lan,
                    # "fromDate": disbursement_date,
                    "channel": req_channel,
                    "authMode": "1"
                }
    #                response[f'doc_{doc}_payload'] = payload
                response['API_REQUEST_PACKET'][f'NOC_Req_{noc_doc_api_ctr}'] = {"url":URL,"headers":Headers,"data":payload}
                logger.error('NOC doc payload ------------------: %s',str(payload), extra={'AppName': 'EasyChat', 'user_id': 'None', 'source': 'None', 'channel': 'None', 'bot_id': 'None'})
                try:
                    resp = requests.post(url = URL, data = json.dumps(payload), headers = Headers, timeout = 20)
                except Exception as E:
                    exc_type, exc_obj, exc_tb = sys.exc_info()
                    logger.error('ApiTreeContent: %s at %s',str(E), str(exc_tb.tb_lineno), extra={'AppName': 'EasyChat', 'user_id': 'None', 'source': 'None', 'channel': 'None', 'bot_id': 'None'})
                    response['status_code'] = result_dict['timeout_status']()
                    response['status_message'] = 'ERROR :-  '+str(E)+ ' at line no: ' +str(exc_tb.tb_lineno)
                    response['doc_show'] = result_dict['tech_error']()
                    response['recommendations'] = result_dict['options'](lob)
                    response['API_REQUEST_PACKET'] = {"url":url,"headers":headers,"data":payload}
                    response['API_RESPONSE_PACKET']['NOC_Resp_{noc_doc_api_ctr'] = {"response":str(E)}
                    return response
    
    #                response[f'doc_{doc}_response']['NOC_Req'] = resp.text
                response['API_RESPONSE_PACKET'][f'NOC_Resp_{noc_doc_api_ctr}'] = {"response":resp.text}
                noc_doc_api_ctr += 1
                logger.error('NOC doc response ------------------: %s',str(resp.text), extra={'AppName': 'EasyChat', 'user_id': 'None', 'source': 'None', 'channel': 'None', 'bot_id': 'None'})
    
                if resp.status_code == 200:
                    resp = json.loads(resp.text)
    #                    response[f'doc_{doc}_response'] = resp
    #                    response['API_RESPONSE_PACKET'] = {"response":resp}
                    null = None
                    if resp['statusCode'] == '000':
                        document = resp['pdfDoc'] if resp['pdfDoc'] != null else ''
                        if document == '':
                            response['status_code'] = '500'
                            response['status_message'] = 'API pdfDoc null'
                            response['doc_show'] = result_dict['tech_error']()
                            response['recommendations'] = result_dict['options'](lob)
                            return response         # Instead of return we can use continue as loop is there.
                        else:
                            pass
                            # noc_generation_allowed = True
    
                            ######## Create Case API Calling Start ########
    
                            name_dict = {"NDC":"No Due Certificate","NOC":"NOC Related","FORM35":"Form 35"}
                            
                            ctst_document = name_dict[doc[:-1]]
    
                            access_token = result_dict['get_access_token_ctst']()
    
                            url = result_dict['create_case_ctst']
    
                            headers = {
                            'Authorization': 'Bearer ' + str(access_token),
                            'Content-Type': 'application/json'
                            }
                            
                            payload = json.dumps({
                            "loanAgreementNo": LAN,
                            "templateName": "Service Request",
                            "caseCategory": "Request-STP",
                            "category": ctst_document,
                            "subCategory": "Download",
                            "subSubCategory": "",
                            "subject": origin + " " + str(LAN),
                            "description": ctst_document + "(Download)",
                            "origin": origin,
                            "Status": "Closed",
                            "attachments": None,
                            "RequestedBy": "Customer",
                            "CustomerRequestReason": "Wants to get monthly statement",
                            "ChargesCollected": True,
                            "Comments": ""
                            })
    
                            response['API_REQUEST_PACKET']['CTST_Req'] = {"url":url,"headers":headers,"data":payload}
                            try:
                                resp = requests.request("POST", url, headers=headers, data=payload, timeout = 20)
                                logger.error('NOC CTST Response ------------------: %s',str(resp.text), extra={'AppName': 'EasyChat', 'user_id': 'None', 'source': 'None', 'channel': 'None', 'bot_id': 'None'})
                                resp = json.loads(resp.text)
                                if resp['StatusCode'] == "200":
                                    response['API_RESPONSE_PACKET']['CTST_Resp'] = {"response_ctst":resp}
                                else:
                                    response['status_code'] = "400"
                                    response['status_message'] = 'API FAILURE CTST'
                                    response['API_RESPONSE_PACKET']['CTST_Resp'] = {"response_ctst": str(resp)}
                                    response['doc_show'] = result_dict['tech_error']()
                                    try:
                                        response['recommendations'] = result_dict['options'](lob)
                                    except:
                                        response['recommendations'] = ['Main Menu']
                                    return response
                            except requests.Timeout as E:
                                response['API_RESPONSE_PACKET']['CTST_Resp'] = {"response_ctst": str(E)}
                                response['status_code'] = "400"
                                response['status_message'] = 'API TIMEOUT CTST'
                                response['doc_show'] = result_dict['tech_error']()
                                try:
                                    response['recommendations'] = result_dict['options'](lob)
                                except:
                                    response['recommendations'] = ['Main Menu']
                                return response
                            
                            except Exception as E:
                                response['API_RESPONSE_PACKET']['CTST_Resp'] = {"response_ctst": str(resp)}
                                response['doc_show'] = result_dict['tech_error']()
                                response['status_code'] = "400"
                                response['status_message'] = 'API FAILURE CTST'
                                try:
                                    response['recommendations'] = result_dict['options'](lob)
                                except:
                                    response['recommendations'] = ['Main Menu']
                                return response
    
                            ######## Create Case API Calling End ########
                        filename = str(LAN) + '-' + str(doc) + '.pdf'
                        QueryChannel = '{/QueryChannel/}'
                        logger.error('FileName################ %s', str(filename), extra={'AppName': 'EasyChat', 'user_id': 'None', 'source': 'None', 'channel': 'None', 'bot_id': 'None'})
                        secure = settings.SECURE_MEDIA_ROOT
                        secured_path = '/secured_files/EasyChatApp/reports_pdf/' + str(filename)
                        logger.error('file path################ %s', str(secured_path), extra={'AppName': 'EasyChat', 'user_id': 'None', 'source': 'None', 'channel': 'None', 'bot_id': 'None'})
                        secured_file = open('EasyChatApp/reports_pdf/' + str(filename), 'wb')
                        secured_file.write(base64.b64decode(document))
                        secured_file.close()
                        user_id = '{/EasyChatUserID/}'
                        if EasyChatChannel == 'Web':
                            secure_onetime_file_path = get_secure_file_path(file_path=secured_path, user_id=user_id, bot=Bot.objects.get(pk=1), is_authentication_required=True)
                        else:
                            media_root = settings.MEDIA_ROOT
                            shutil.copy(secure + 'EasyChatApp/reports_pdf/' + str(filename), media_root + "EasyChatApp/reports_pdf/" + str(filename))
                            secure_onetime_file_path = settings.EASYCHAT_HOST_URL + "/files/EasyChatApp/reports_pdf/" + str(filename)
                        logger.error('One time file path################ %s', str(secure_onetime_file_path), extra={'AppName': 'EasyChat', 'user_id': 'None', 'source': 'None', 'channel': 'None', 'bot_id': 'None'})
                        name_dict = {"NDC":"No Dues Certificate","NOC":"No Objection Certificate","FORM35":"Form 35"}
                        cards.append({'title':doc[:-1],'content':name_dict[doc[:-1]],"link":secure_onetime_file_path,"img_url": settings.EASYCHAT_HOST_URL+"/files/pdf.png", "caption": LAN + '-' + str(doc[:-1])})
    #                        if lob in ['Two Wheeler','Farm']:
    #                            doc_show = f"Dear Customer,<br><br>As requested by you please find below the NOC, NDC and Form 35 for your <b>Loan No: {LAN}</b>."
    #                        else:
    #                            doc_show = f"Dear Customer,<br><br>As requested by you please find below the NDC for your <b>Loan No. {LAN}</b>."
                        doc_show += " " + str(doc[:-1]) + ","
    #                        response['cards'] = cards
                        logger.error('doc_download_apitree_11 document fetched for user %s : %s', LAN, str(doc[:-1]), extra={'AppName': 'EasyChat', 'user_id': 'None', 'source': 'None', 'channel': 'None', 'bot_id': 'None'})
                    elif resp['statusCode'] == '300':
                        count += 1
                    elif resp['statusCode'] == '500':
                        count += 1
                        logger.error('FAILED doc_download_apitree_11 document fetched for user %s : %s', LAN, str(doc[:-1]), extra={'AppName': 'EasyChat', 'user_id': 'None', 'source': 'None', 'channel': 'None', 'bot_id': 'None'})
                    else:
                        response['status_code'] = '500'
                        response['status_message'] = 'API ERROR - ELSE'
                        response['doc_show'] = result_dict['tech_error']()
    #                        response['doc_show'] = resp['statusDesc']
                        response['recommendations'] = result_dict['options'](lob)
                        return response
                else:
                    response['status_code'] = '500'
                    response['status_message'] = 'API ERROR - ELSEEE'
                    #response['doc_show'] = result_dict['tech_error']()
                    response['doc_show'] = resp['statusDesc']
                    response['recommendations'] = result_dict['options'](lob)
                    return response
                    
                response['cards'] = cards
                doc_show = doc_show[:-1] + f" for your <b>Loan No: {LAN}</b>."
                if count != doc_len:
                    if lob == 'Two Wheeler' or lob == 'Farm':
                        doc_ext += "<br><br>The password to access the document is the last 6 digits of your Engine no."
                    else:
                        doc_ext += "<br><br>The password to access the file is your DOB in the format DDMMYYYY + Last 4 digits of your registered mobile no.<br>(E.g. If your DOB is 3rd January 1993 and registered number 1234567890, then your password will be 030119937890)"
    
                    doc_show = doc_show + doc_ext + '<br><br>Thank you for contacting L&T Finance.'
                    response['status_code'] = '200'
                else:
                    #doc_show = result_dict['tech_error']()
                    doc_show = resp['statusDesc']
                    response['status_code'] = '500'
        else:
            response['data']['loblatest'] = lob
            if lob in ['Two Wheeler', 'Consumer Loan']:
                doc_show = "Dear customer, You have exceeded the maximum limit of free NOC available for download.<br/><br/>"     #"If you still wish to download the NOC, a minimal amount of <b>Rs.295.00</b> to be paid as service charges. Click on the below link to proceed with the charges payment.<br/><br/>"
                doc_show += "Click here https://selfhelpuat.ltfs.com/SHO-Microsite/#/login?id=15 to pay a nominal fee of <b>Rs.295.00</b> and avail your NOC."
                response['recommendations'] = ['Main Menu']
                response['status_code'] = 200
            else:
                doc_show = "Dear customer, You have exceeded the maximum limit of free NOC available for download.<br/><br/>"     #"If you still wish to download the NOC, a minimal amount of <b>Rs.1180.00</b> to be paid as service charges. Click on the below link to proceed with the charges payment.<br/><br/>"
                doc_show += "Click here https://selfhelpuat.ltfs.com/SHO-Microsite/#/login?id=15 to pay a nominal fee of <b>Rs.1180.00</b> and avail your NOC."
                response['recommendations'] = ['Main Menu']
                response['status_code'] = 200

        response['doc_show'] = doc_show
        response['recommendations'] = result_dict['options'](lob)
        response['print'] = 'Hello world!'
        return response
    except Exception as E:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        logger.error('ApiTreeContent: %s at %s',str(E), str(exc_tb.tb_lineno), extra={'AppName': 'EasyChat', 'user_id': 'None', 'source': 'None', 'channel': 'None', 'bot_id': 'None'})
        response['status_code'] = 500
        response['status_message'] = 'ERROR :-  '+str(E)+ ' at line no: ' +str(exc_tb.tb_lineno)
        response['doc_show'] = result_dict['tech_error']()
        try:
            response['recommendations'] = result_dict['options'](lob)
        except:
            response['recommendations'] = ['Main Menu']
        return response
