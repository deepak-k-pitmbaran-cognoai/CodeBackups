"""
Important: This webhook includes custom modifications. 
Please ensure a backup is taken before making any changes.

Custom Changes (Tags):
    1. [CUSTOM] WhatsAppFlow Integration
"""

from EasyChatApp.azure_gpt_helper.utils_azure_search import get_whatsapp_azure_pdf_response
from EasyChatApp.utils import check_and_send_broken_bot_mail, logger, save_chatgpt_response_in_mis_dashboard
from EasyChatApp.utils_pdf_search import save_chatgpt_token_audit_trail
from EasyChatApp.utils_bot import process_response_based_on_language
from CampaignApp.utils_lambda import exotel_push_delivery_packets, exotel_push_reply_packets
from DeveloperConsoleApp.utils import initialize_logger
from EasyChatApp.utils_whatsapp_payments import payment_status_handler
from EasyChatApp.utils_whatsapp_flow import save_flow_response


from django.conf import settings
import time
import json
import sys
import requests
import mimetypes
from django.utils import timezone as timezone
from EasyChatApp.utils_execute_query import execute_query, get_encrypted_message, is_this_language_supported_by_bot, set_user
from EasyChatApp.whatsapp_utils import *
from urllib.parse import urlparse
import requests
import urllib
import datetime

log_param = {'AppName': 'EasyChat', 'user_id': 'None', 'source': 'None', 'channel': 'WhatsApp', 'bot_id': 'None'}

webhook_logger = initialize_logger("exotel_webhook_logger", "log/whatsapp_webhook.log", True)


# ====================================== [CUSTOM] WhatsAppFlow Integration ================================
def process_flow_data(flow_data):
    import re
    data = flow_data
    try:
        data = json.loads(data.replace("'", '"'))
    except:
        logger.error("=== process_flow_data  Data : %s", str(data), extra=log_param)
        
        fixed_flow_data = re.sub(r"'", '"', data)
        fixed_flow_data = fixed_flow_data.replace("True", "true").replace("False", "false")
        data = json.loads(fixed_flow_data)

    return data

def save_data_to_flow_endpoint(flow_token, flow_id, data):
    
    try:
        logger.info(f"Into  save_data_to_flow_endpoint.. Args: flow_token={flow_token}, flow_id={flow_id}, data={data}", extra=log_param)
        
        data = process_flow_data(data)

        url = f"https://wa-flow.allincall.in/flow/save-data/?flow_id={flow_id}&flow_token={flow_token}"

        headers = {
                'Content-Type': 'application/json'
                }
                
        logger.info(f"save_data_to_flow_endpoint.. before dump Data: {data}", extra=log_param)
        
        payload = json.dumps(data)
        
        logger.info(f"save_data_to_flow_endpoint.. URL: {url}", extra=log_param)
        logger.info(f"save_data_to_flow_endpoint.. PAYLOAD: {payload} TYPE: {type(payload)}", extra=log_param)
        logger.info(f"save_data_to_flow_endpoint.. HEADERS: {headers}", extra=log_param)

        api_response = requests.request("POST", url=url, headers=headers ,data=payload, timeout=10)
        
        

        logger.info(f"save_data_to_flow_endpoint.. Request: {api_response.request.__dict__}", extra=log_param)
        
        logger.info(f"save_data_to_flow_endpoint.. status_code: {api_response.status_code}", extra=log_param)
        
        logger.info(f"save_data_to_flow_endpoint.. response: {json.loads(api_response.text)}", extra=log_param)
        
    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        logger.error("save_data_to_flow_endpoint API Failed: %s at %s", str(
            e), str(exc_tb.tb_lineno), extra=log_param)
        pass


#   WHATSAPP SEND SESSION BASED Form MESSAGE API:
def sendWhatsAppFormMessage(exotel_api_key, exotel_api_token, exotel_number, exotal_account_sid, exotel_subdomain, message_head, flow_params,message_body, message_foot, phone_number, extra="None", lang="en", recipient_type="individual"):
    log_param = {'AppName': 'EasyChat', 'user_id': 'None',
                 'source': 'None', 'channel': 'WhatsApp', 'bot_id': 'None'}
    try:
        
        logger.error("=== sendWhatsAppFormMessage Flow Data: %s", str(type(flow_params["data"])), extra=log_param)
        
        if phone_number[:2] != '91':
            phone_number = '+' + phone_number
        
        custom_log = {}
        url = "https://"+exotel_api_key+":"+exotel_api_token + \
            exotel_subdomain+"/v2/accounts/"+exotal_account_sid+"/messages"

        headers = {
            "Content-Type": "application/json"
        }

        payload = {
            "whatsapp": {
                "messages": [
                        {
                            "from": exotel_number,
                            "to": phone_number,
                            "content": {
                                "type": "interactive",
                                "interactive": {
                                    "type": "flow",
#                                    "header": {
#                                        "type": "text",
#                                        "text": message_head
#                                    },
                                    "body": {
                                        "text": message_body
                                    },
#                                    "footer": {
#                                        "text": message_foot
#                                    },
                                    "action": {
                                        "name": "flow",
                                        "parameters": {
                                            "mode": flow_params.get("mode") if str(flow_params.get("mode")).lower() != "none" else "published"  ,#"draft",
                                            "flow_message_version": "3",
                                            "flow_id": flow_params['flow_id'],#"1580516186084933",
                                            "flow_token": flow_params["flow_token"],
                                            "flow_cta": flow_params["flow_cta"],
                                            "flow_action": flow_params["flow_action"]
                                        }
                                    }
                                }
                            }
                        }
                ]
            }
        }
        
        flow_action_payload = {}
        if flow_params['flow_action'] == "navigate":
            flow_action_payload["screen"] = flow_params["screen"]
            
#            payload["whatsapp"]["messages"][0]["content"]["interactive"]["action"]["parameters"]["flow_action_payload"] = {"screen": flow_params["screen"]}
            if flow_params.get("data") != None and flow_params.get("data") not in ["none", "None"]:
                flow_action_payload["data"] = process_flow_data(flow_params["data"])

                # flow_action_payload["data"] = json.loads(json.dumps(flow_params["data"].replace('"','"')))
                logger.error("=== sendWhatsAppFormMessage Dump FLow Data : %s", str(flow_action_payload["data"]), extra=log_param)

#                payload["whatsapp"]["messages"][0]["content"]["interactive"]["action"]["parameters"]["flow_action_payload"]["data"] = flow_params["data"]
            payload["whatsapp"]["messages"][0]["content"]["interactive"]["action"]["parameters"]["flow_action_payload"] = flow_action_payload
            # webhook_logger.error("chk flow action paylaod: %s", str(
            # flow_action_payload), extra=log_param)
        

        # webhook_logger.error("chk Send WA Session Based Flow Message API Headers: %s", str(
        #     headers), extra=log_param)
        # webhook_logger.error("chk Send WA Session Based Flow Message API Request: %s", str(
        #     payload), extra=log_param)
        logger.error("=== sendWhatsAppFormMessage Payload: %s", str(payload), extra=log_param)
        
        save_data_to_flow_endpoint(flow_id=flow_params['flow_id'], flow_token=flow_params['flow_token'], data=flow_params["data"])
        
        r = requests.request("POST", url, headers=headers,
                             data=json.dumps(payload), timeout=20, verify=True)
        content = json.dumps(r.text)
        logger.error("=== sendWhatsAppFormMessage Response: %s", str(content), extra=log_param)
        # webhook_logger.error("chk Send WA Session Based Flow Message API Response: %s", str(
        #     content), extra=log_param)
        custom_log["payload"] = payload
        custom_log["api_response"] = r.text
        if str(r.status_code) == "200" or str(r.status_code) == "201" or str(r.status_code) == "202":
            logger.error("=== sendWhatsAppFormMessage sent successfully ====", extra=log_param)
            # webhook_logger.error("chk Flow message sent succesfully",
            #             extra=log_param)
            return True, custom_log
        else:
            logger.error("Failed to Send Flow Message.",
                         extra=log_param)
            return False, custom_log
    except requests.Timeout as RT:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        logger.error("sendWhatsAppFormMessage API Timeout error: %s at %s", str(
            RT), str(exc_tb.tb_lineno), extra=log_param)

        return False, custom_log
    except Exception as E:
        custom_log["err"] = str(E)
        exc_type, exc_obj, exc_tb = sys.exc_info()
        logger.error("sendWhatsAppFormMessage API Failed: %s at %s", str(
            E), str(exc_tb.tb_lineno), extra=log_param)
        return False, custom_log

# =========================================================================================================





def save_file_from_remote_server_to_local(remote_url, local_path, max_file_size_mb=5.0):
    is_saved = False
    try:
        start_time = time.time()
        response = requests.get(url=remote_url, timeout=10)
        response_time = response.elapsed.total_seconds()
        logger.info("save_file_from_remote_server_to_local: API response time: %s secs", str(
            response_time), extra=log_param)
        raw_data = response.content
        file_to_save = open(local_path, "wb")
        file_to_save.write(raw_data)
        file_to_save.close()
        end_time = time.time()
        response_time = end_time - start_time
        logger.info("save_file_from_remote_server_to_local: Total response time: %s secs", str(
            response_time), extra=log_param)
        file_size = os.path.getsize(local_path)/(1024*1024)
        is_saved = True
        if file_size > max_file_size_mb:
            os.remove(local_path)
            logger.info("save_file_from_remote_server_to_local: File Size Exceeded, Max Allowed: %s", str(
                max_file_size_mb), extra=log_param)
            is_saved = False
    except Exception as E:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        logger.error("save_file_from_remote_server_to_local: %s at %s", str(
            E), str(exc_tb.tb_lineno), extra=log_param)
    return is_saved


def get_whatsapp_file_attachment(attachment_packet, max_attachment_size_allowed, allowed_file_types=None):
    attachment_path = None
    is_saved = False
    try:
        o = urlparse(attachment_packet, allow_fragments=False)
        remote_url = attachment_packet
        file_name = o.path.split("/")[-1]
        ext = "." + file_name.split(".")[1]
        file_name = file_name.replace(" ", "-")
        if not os.path.exists(settings.SECURE_MEDIA_ROOT + 'WhatsAppMedia'):
            os.makedirs(settings.SECURE_MEDIA_ROOT + 'WhatsAppMedia')
        file_path = settings.SECURE_MEDIA_ROOT + "WhatsAppMedia/" + file_name
        file_path_rel = "secured_files/WhatsAppMedia/" + file_name
        EasyChatAppFileAccessManagement.objects.create(file_path="/" + file_path_rel, is_public=True, is_customer_attachment=True)
        logger.info(file_path_rel)
        if allowed_file_types and ext not in allowed_file_types:
            return file_path, False

        is_saved = save_file_from_remote_server_to_local(remote_url, file_path)
        attachment_path = settings.EASYCHAT_HOST_URL+"/"+file_path_rel
        logger.info("is_whatsapp_file_attachment: Filename %s",
                    file_name, extra=log_param)
        logger.info("is_whatsapp_file_attachment: Filepath %s",
                    attachment_path, extra=log_param)
    except Exception as E:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        logger.error("save_file_from_remote_server_to_local: %s at %s", str(
            E), str(exc_tb.tb_lineno), extra=log_param)
    return attachment_path, is_saved


def send_whatsapp_text_message(exotel_api_key, exotel_api_token, exotel_number, exotal_account_sid, exotel_subdomain, message, phone_number, preview_url=False, recipient_type="individual"):
    log_param = {'AppName': 'EasyChat', 'user_id': 'None',
                 'source': 'None', 'channel': 'WhatsApp', 'bot_id': 'None'}
    try:
        phone_number = "+" + phone_number
        if message.strip() == "":
            return False
        logger.info(message)
        logger.info("=== Inside Send WA Text Message API ===", extra=log_param)

        url = "https://"+exotel_api_key+":"+exotel_api_token + \
            exotel_subdomain+"/v2/accounts/"+exotal_account_sid+"/messages"
        headers = {
            "Content-Type": "application/json"

        }

        payload = {
            "whatsapp": {
                "messages": [
                    {
                        "from": exotel_number,
                        "to": phone_number,
                        "content": {
                            "type": "text",
                            "text": {
                                "body": message
                            }
                        }
                    }
                ]
            }
        }

        if preview_url == True:
            payload["whatsapp"]["messages"][0]["content"]["text"]["preview_url"] = True

        logger.info("Send WA Text API URL: %s", str(url), extra=log_param)
        logger.info("Send WA Text API Headers: %s",
                    str(headers), extra=log_param)
        logger.info("Send WA Text API Request: %s",
                    str(payload), extra=log_param)
        r = requests.request("POST", url, headers=headers,
                             data=json.dumps(payload), timeout=20, verify=True)
        logger.info("Send WA Text API Response: %s",
                    str(r.text), extra=log_param)
        if str(r.status_code) == "200" or str(r.status_code) == "201" or str(r.status_code) == "202":
            content = json.loads(r.text)
            logger.info("Text message sent succesfully", extra=log_param)
            return True
        else:
            logger.error("Failed to Send Text Message.", extra=log_param)
            logger.error("Send WA Text API Response: %s",
                         str(r.text), extra=log_param)
            return False
    except requests.Timeout as RT:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        logger.error("SendWhatsAppText API Timeout error: %s at %s",
                     str(RT), str(exc_tb.tb_lineno), extra=log_param)
        return False
    except Exception as E:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        logger.error("SendWhatsAppText API Failed: %s at %s",
                     str(E), str(exc_tb.tb_lineno), extra=log_param)
    return False


# WHATSAPP SEND MEDIA MESSAGE API:
def sendWhatsAppMediaMessage(exotel_api_key, exotel_api_token, exotel_number, exotal_account_sid, exotel_subdomain, media_type, media_url, phone_number, caption=None, recipient_type="individual"):
    try:
        phone_number = "+" + phone_number
        logger.info("=== Inside Send WA Media Message API ===",
                    extra=log_param)

        logger.info("Media Type: %s", media_type, extra=log_param)

        if caption == None:
            caption = ""

        url = "https://"+exotel_api_key+":"+exotel_api_token + \
            exotel_subdomain+"/v2/accounts/"+exotal_account_sid+"/messages"

        headers = {
            "Content-Type": "application/json"
        }

        contentType = mimetypes.guess_type(media_url)
        payload = {
            "whatsapp": {
                "messages": [
                    {
                        "from": exotel_number,
                        "to": phone_number,
                        "content": {
                            "type": media_type,
                            media_type: {
                                "link": media_url,
                                "caption": caption
                            }
                        }
                    }
                ]
            }
        }
        
        media_name = media_url.split("/")[-1]
        if media_type == "document":
            if media_name != "":
                payload["whatsapp"]["messages"][0]["content"][media_type]["filename"] = urllib.parse.unquote(media_name)

        logger.info("Send WA "+media_type.upper() +
                    " API Request: %s", str(payload), extra=log_param)
        r = requests.request("POST", url, headers=headers,
                             data=json.dumps(payload), timeout=20, verify=True)
        logger.info("Send WA "+media_type.upper() +
                    " API Response: %s", str(r.text), extra=log_param)
        if str(r.status_code) == "200" or str(r.status_code) == "201" or str(r.status_code) == "202":
            content = json.loads(r.text)
            logger.info(media_type.upper() +
                        " message sent successfully", extra=log_param)
            return True
        else:
            logger.error("Failed to send "+media_type.upper() +
                         " message", extra=log_param)
            return False
    except requests.Timeout as RT:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        logger.error("SendWhatsAppMediaMessage Timeout error: %s at %s", str(
            RT), str(exc_tb.tb_lineno), extra=log_param)
        return False
    except Exception as E:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        logger.error("SendWhatsAppMediaMessage Failed: %s at %s",
                     str(E), str(exc_tb.tb_lineno), extra=log_param)
    return False


#   WHATSAPP SEND SESSION BASED QUICK REPLY MESSAGE API:
def sendWhatsAppQuickReplyMessage(exotel_api_key, exotel_api_token, exotel_number, exotal_account_sid, exotel_subdomain, reply_buttons, message_head, message_body, message_foot, phone_number, media_type="text", media_link=None, extra="None", lang="en", recipient_type="individual"):
    log_param = {'AppName': 'EasyChat', 'user_id': 'None',
                 'source': 'None', 'channel': 'WhatsApp', 'bot_id': 'None'}
    try:
        phone_number = "+" + phone_number
        url = "https://"+exotel_api_key+":"+exotel_api_token + \
            exotel_subdomain+"/v2/accounts/"+exotal_account_sid+"/messages"

        headers = {
            "Content-Type": "application/json"
        }
        if len(reply_buttons) == 0 or len(reply_buttons) > 3:
            return False

        payload = {
            "whatsapp": {
                "messages": [
                        {
                            "from": exotel_number,
                            "to": phone_number,
                            "content": {
                                "type": "interactive",
                                "interactive": {
                                    "type": "button",
                                    "body": {
                                        "text": message_body
                                    },

                                    "action": {

                                    }
                                }
                            }
                        }
                ]
            }
        }
        # uncomment to add header and footer
        # if message_foot != " " and message_foot != "":
        #     footer={
        #             "text": message_foot
        #             }
        #     payload["whatsapp"]["messages"][0]["content"]["interactive"]["footer"]=footer
        #     interactive_header = {"type": "text", media_type: message_head}

        interactive_header = {}
        if message_head != " " and message_head != "":
            if media_type != "text":
                medianame = media_link.split("/")[-1]
                interactive_header = {
                    media_type: {
                        "link": media_link,
                        "provider": {
                            "name": ""
                        }
                    }
                }
                if media_type == "document":
                    interactive_header[media_type]["filename"] = medianame
            if interactive_header != {}:
                payload["whatsapp"]["messages"][0]["content"]["interactive"]["header"] = interactive_header

        interactive_action = {"buttons": []}
        count = 1

        # If reply_button is a Dictionary, keys will be treated as button ID and value as button Title
        # If reply_button is an Array, button ID will be count variable and value will be Array Items.
        is_reply_button_dict = isinstance(reply_buttons, dict)

        for button in reply_buttons:
            button_dict = {}
            button_dict["type"] = "reply"
            button_dict["reply"] = {
                "id": button if is_reply_button_dict else str(count),
                "title": reply_buttons[button] if is_reply_button_dict else str(button)
            }
            interactive_action["buttons"].append(button_dict)
            count += 1
        payload["whatsapp"]["messages"][0]["content"]["interactive"]["action"] = interactive_action
        logger.info("Send WA Session Based Quick Reply Message API Headers: %s", str(
            headers), extra=log_param)
        logger.info("Send WA Session Based Quick Reply Message API Request: %s", str(
            payload), extra=log_param)
        r = requests.request("POST", url, headers=headers,
                             data=json.dumps(payload), timeout=20, verify=True)
        content = json.dumps(r.text)
        logger.info("Send WA Session Based Quick Reply Message API Response: %s", str(
            content), extra=log_param)
        if str(r.status_code) == "200" or str(r.status_code) == "201" or str(r.status_code) == "202":
            logger.info("Quick Reply message sent succesfully",
                        extra=log_param)
            return True
        else:
            logger.error("Failed to Send Quick Reply Message.",
                         extra=log_param)
            return False
    except requests.Timeout as RT:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        logger.error("sendWhatsAppQuickReplyMessage API Timeout error: %s at %s", str(
            RT), str(exc_tb.tb_lineno), extra=log_param)

        return False
    except Exception as E:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        logger.error("sendWhatsAppQuickReplyMessage API Failed: %s at %s", str(
            E), str(exc_tb.tb_lineno), extra=log_param)
        return False

#   WHATSAPP SEND MENU LIST MESSAGE API:


def sendWhatsAppInteractiveListMessage(exotel_api_key, exotel_api_token, exotel_number, exotal_account_sid, exotel_subdomain, list_title, reply_buttons, message_head, message_body, message_foot, phone_number, menu_button_text="Select", extra="None", lang="en", recipient_type="individual"):
    log_param = {'AppName': 'EasyChat', 'user_id': 'None',
                 'source': 'None', 'channel': 'WhatsApp', 'bot_id': 'None'}
    try:
        logger.info(
            "=== Inside Send WA Session Based Interactive List Message API data test ===", extra=log_param)
        phone_number = "+" + phone_number
        url = "https://"+exotel_api_key+":"+exotel_api_token + \
            exotel_subdomain+"/v2/accounts/"+exotal_account_sid+"/messages"
        headers = {
            "Content-Type": "application/json"
        }
        if len(reply_buttons) == 0 or len(reply_buttons) > 10:
            return False

        payload = {
            "whatsapp": {
                "messages": [
                        {
                            "from": exotel_number,
                            "to": phone_number,
                            "content": {
                                "type": "interactive",
                                "interactive": {
                                    "type": "list",
                                    "body": {
                                        "type": "text",
                                        "text": message_body
                                    },
                                    "action": {
                                        "button": list_title,
                                        "sections": [
                                            {
                                                "title": list_title,
                                                "rows": []
                                            }
                                        ]
                                    }
                                }
                            }
                        }
                ]
            }
        }
        count = 1
        final_dict = {}
        if message_head != " ":
            header = {"type": "text",
                      "text": message_head
                      }
            payload["whatsapp"]["messages"][0]["content"]["interactive"]["header"] = header
        if message_foot != " " and message_foot != "":
            footer = {
                "text": message_foot
            }
            payload["whatsapp"]["messages"][0]["content"]["interactive"]["footer"] = footer

        for button in reply_buttons:
            button_dict = {}
            button_dict["id"] = str(count)
            if "$$$" in str(button):
                button_dict["title"] = str(button).split("$$$")[0]
                button_dict["description"] = str(button).split("$$$")[1]
            else:
                button_dict["id"] = str(count)
                button_dict["title"] = str(button)
            count += 1
            payload["whatsapp"]["messages"][0]["content"]["interactive"]["action"]["sections"][0]["rows"].append(
                button_dict)
        logger.info("Send WA Session Based Interactive List Message API Request: %s", str(
            payload), extra=log_param)
        r = requests.request("POST", url, headers=headers,
                             data=json.dumps(payload), timeout=20, verify=True)
        content = json.dumps(r.text)
        logger.info("Send WA Session Based Interactive List Message API Response: %s", str(
            content), extra=log_param)
        logger.info("Send WA Session Based Interactive List Message API Status Code: %s", str(
            r.status_code), extra=log_param)
        if str(r.status_code) == "200" or str(r.status_code) == "201" or str(r.status_code) == "202":
            logger.info("Interactive List message sent succesfully",
                        extra=log_param)
            return True
        else:
            logger.error(
                "Failed to Send Interactive List Message.", extra=log_param)
            return False
    except requests.Timeout as RT:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        logger.error("sendWhatsAppInteractiveListMessage API Timeout error: %s", str(
            RT), str(exc_tb.tb_lineno), extra=log_param)
        return False
    except Exception as E:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        logger.error("sendWhatsAppInteractiveListMessage API Failed: %s", str(
            E), str(exc_tb.tb_lineno), extra=log_param)
        return False


def send_sectioned_whatsapp_interactive_list(exotel_api_key, exotel_api_token, exotel_number, exotal_account_sid, exotel_subdomain, list_title, sectioned_reply_buttons, message_head, message_body, message_foot, phone_number, menu_button_text="Select", extra="None", lang="en", recipient_type="individual"):
    log_param = {'AppName': 'EasyChat', 'user_id': 'None',
                 'source': 'None', 'channel': 'WhatsApp', 'bot_id': 'None'}
    try:
        logger.info(
            "=== Inside Send WA Session Based Interactive List Message API data test1 ===", extra=log_param)
        
        phone_number = "+" + phone_number

        url = "https://"+exotel_api_key+":"+exotel_api_token + \
            exotel_subdomain+"/v2/accounts/"+exotal_account_sid+"/messages"
        headers = {
            "Content-Type": "application/json"
        }

        payload = {
            "whatsapp": {
                "messages": [
                        {
                            "from": exotel_number,
                            "to": phone_number,
                            "content": {
                                "type": "interactive",
                                "interactive": {
                                    "type": "list",
                                    "body": {
                                        "type": "text",
                                        "text": message_body
                                    },
                                    "action": {}
                                }
                            }
                        }
                ]
            }
        }
        count = 1
        final_dict = {}
        if message_head != " ":
            header = {"type": "text",
                      "text": message_head
                      }
            payload["whatsapp"]["messages"][0]["content"]["interactive"]["header"] = header
        if message_foot != " " and message_foot != "":
            footer = {
                "text": message_foot
            }
            payload["whatsapp"]["messages"][0]["content"]["interactive"]["footer"] = footer

        interactive_action = {
            "button": menu_button_text,
        }
        count = 1

        reverse_mapping_dict = {}
        recommendation_list = []

        for section in sectioned_reply_buttons:
            section_dict = {}
            section_dict["title"] = section["section_title"]
            section_dict["rows"] = []

            for button in section["buttons"]:
                button_dict = {}
                button_dict["id"] = str(count)
                if type(button) == dict:
                    button_dict["title"] = button["name"]
                    button_dict["description"] = button["description"]
                    recommendation_list.append(button["name"])
                else:
                    button_dict["title"] = button
                    button_dict["description"] = ""
                    recommendation_list.append(button)

                if type(button) == dict and "full_name" in button:
                    reverse_mapping_dict[str(count)] = button["full_name"]
                elif type(button) == dict and "name" in button and "id" not in button:
                    reverse_mapping_dict[str(count)] = button["name"]
                else:
                    reverse_mapping_dict[str(count)] = button

                section_dict["rows"].append(button_dict)
                count += 1

            interactive_action["sections"].append(section_dict)

        payload["whatsapp"]["messages"][0]["content"]["interactive"]["action"] = interactive_action

        logger.info("Send WA Session Based Interactive List Message API Request: %s", str(
            payload), extra=log_param)

        r = requests.request("POST", url, headers=headers,
                             data=json.dumps(payload), timeout=20, verify=True)
        content = json.dumps(r.text)

        logger.info("Send WA Session Based Interactive List Message API Response: %s", str(
            content), extra=log_param)
        logger.info("Send WA Session Based Interactive List Message API Status Code: %s", str(
            r.status_code), extra=log_param)

        if str(r.status_code) == "200" or str(r.status_code) == "201" or str(r.status_code) == "202":
            logger.info("Interactive List message sent succesfully",
                        extra=log_param)
            return True, [], reverse_mapping_dict
        else:
            logger.error(
                "Failed to Send Interactive List Message.", extra=log_param)
            return False, recommendation_list, {}
    except Exception as E:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        logger.error("send_sectioned_whatsapp_interactive_list API Failed: %s", str(
            E), str(exc_tb.tb_lineno), extra=log_param)
        return False, recommendation_list, {}


# This catalog main API
def send_whatsapp_catalog(user_obj, exotel_api_key, exotel_api_token, exotel_number, exotal_account_sid, exotel_subdomain, phone_number, catalogue_metadata, bot_id, catalogue_sections, recipient_type="individual"):
    log_param = {'AppName': 'EasyChat', 'user_id': 'None',
                 'source': 'None', 'channel': 'WhatsApp', 'bot_id': 'None'}
    try:
        logger.info("=== Inside Send Catalog Text Message API ===",
                    extra=log_param)

        phone_number = "+" + phone_number
        url = "https://"+exotel_api_key+":"+exotel_api_token + \
            exotel_subdomain+"/v2/accounts/"+exotal_account_sid+"/messages"

        headers = {
            "Content-Type": "application/json"
        }
        payload = get_whatsapp_catalogue_payload(
            user_obj, recipient_type, exotel_number, phone_number, catalogue_metadata['catalogue_type'], catalogue_metadata, bot_id, catalogue_sections)
        logger.info("Catalogue Payload: %s", str(payload), extra=log_param)
        r = requests.request("POST", url, headers=headers,
                             data=json.dumps(payload), timeout=20, verify=True)

        logger.info("Send WA catalog: %s - %s", str(r.status_code),
                    str(r.text), extra=log_param)
        content = json.loads(r.text)
        if "errors" in content:
            error_message_dump = content["errors"]
            check_and_send_broken_bot_mail(
                bot_id, "WhatsApp", "", error_message_dump)
        if str(r.status_code) == "200" or str(r.status_code) == "201" or str(r.status_code) == "202":
            return True
        else:
            logger.error("SendWhatAppProductCatalogue Response: %s",
                         str(r.text), extra=log_param)
            return False
    except requests.Timeout as RT:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        logger.error("SendWhatAppProductCatalogue API Timeout error: %s at %s", str(
            RT), str(exc_tb.tb_lineno), extra=log_param)
        return False
    except Exception as E:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        logger.error("SendWhatAppProductCatalogue API Failed: %s at %s", str(
            E), str(exc_tb.tb_lineno), extra=log_param)
    return False


# here we are creating catalog pay load for both (single product and multi product)
def get_whatsapp_catalogue_payload(user_obj, recipient_type, exotel_number, phone_number, catalogue_type, catalogue_metadata, bot_id, sections_selected):
    try:
        phone_number = "+" + phone_number
        user_language = user_obj.selected_language
        language_tuned_bot_obj = LanguageTunedBot.objects.filter(
            bot__pk=bot_id, language=user_language).first()
        is_catalogue_tuned = False
        if language_tuned_bot_obj and language_tuned_bot_obj.whatsapp_catalogue_data != "{}":
            catalogue_metadata = json.loads(
                language_tuned_bot_obj.whatsapp_catalogue_data)
            is_catalogue_tuned = True
        user_language = user_language.lang if user_language else "en"
        body_text = catalogue_metadata["body_text"]
        if not is_catalogue_tuned:
            body_text = get_translated_text(
                body_text, user_language, EasyChatTranslationCache)
        if len(body_text) > 1024:
            body_text = body_text[:1023]
        session_id, _, _ = get_session_id_based_on_user_session(
            user_obj.user_id, bot_id)
        catalogue_payload = {
            "whatsapp": {
                "messages": [
                            {
                                "from": exotel_number,
                                "to": phone_number,
                                "content": {
                                    "type": "interactive",
                                    "interactive": {
                                        "type": "product_list" if catalogue_type == "multiple_product" else "product",
                                        "body": {
                                            "text": whatsappify_text(body_text)
                                        }
                                    }
                                }
                            }
                ]
            }
        }
        if "footer_text" in catalogue_metadata:
            footer_text = catalogue_metadata["footer_text"]
        if not is_catalogue_tuned:
            footer_text = get_translated_text(
                footer_text, user_language, EasyChatTranslationCache)
        if len(footer_text) > 60:
            footer_text = footer_text[:59]
        if footer_text != "":
            catalogue_payload["whatsapp"]["messages"][0]["content"]["interactive"]["footer"] = {
                "text": footer_text
            }
        if catalogue_type == "single_product":
            catalogue_payload["whatsapp"]["messages"][0]["content"]["interactive"]["action"] = {
                "catalog_id": catalogue_metadata["catalogue_id"],
                "product_retailer_id": catalogue_metadata["product_id"]
            }
            catalogue_message = "Catalogue ID: " + \
                catalogue_metadata["catalogue_id"] + " Product: "
            item_obj = WhatsappCatalogueItems.objects.filter(
                catalogue_id=catalogue_metadata["catalogue_id"], retailer_id=catalogue_metadata["product_id"]).first()
            if item_obj:
                item_name = item_obj.item_name
            else:
                item_name = catalogue_metadata["product_id"]
            catalogue_message += item_name
        else:
            header_text = catalogue_metadata["header_text"]
            if not is_catalogue_tuned:
                header_text = get_translated_text(
                    header_text, user_language, EasyChatTranslationCache)
            if len(header_text) > 60:
                header_text = header_text[:59]
            if header_text != "":
                catalogue_payload["whatsapp"]["messages"][0]["content"]["interactive"]["header"] = {
                    "type": "text",
                    "text": header_text
                }
            catalogue_sections = []
            catalogue_message = "Catalogue ID: " + \
                catalogue_metadata["catalogue_id"]
            for section_id in catalogue_metadata["section_ordering"]:
                if sections_selected is not None and section_id not in sections_selected:
                    continue
                section_details = {}
                section_details['title'] = catalogue_metadata["sections"][section_id]["section_title"]
                if not is_catalogue_tuned:
                    section_details['title'] = get_translated_text(
                        section_details['title'], user_language, EasyChatTranslationCache)
                if len(section_details['title']) > 24:
                    section_details['title'] = str(
                        section_details['title'])[:24]
                section_details['product_items'] = []
                catalogue_message += " " + section_details['title'] + ": "
                product_ids = []
                for product_id in catalogue_metadata["sections"][section_id]["product_ids"]:
                    section_details['product_items'].append(
                        {"product_retailer_id": product_id})
                    item_obj = WhatsappCatalogueItems.objects.filter(
                        catalogue_id=catalogue_metadata["catalogue_id"], retailer_id=product_id).first()
                    if item_obj:
                        item_name = item_obj.item_name
                    else:
                        item_name = product_id
                    product_ids.append(item_name)
                catalogue_message += ", ".join(product_ids)
                catalogue_sections.append(section_details)
            catalogue_action = {
                "catalog_id": catalogue_metadata["catalogue_id"],
                "sections": catalogue_sections
            }
            catalogue_payload["whatsapp"]["messages"][0]["content"]["interactive"]["action"] = catalogue_action

        mis_obj = MISDashboard.objects.filter(creation_date=datetime.datetime.now().date(), user_id=user_obj.user_id, session_id=session_id, selected_language=user_obj.selected_language, channel_name="WhatsApp").first()
        catalogue_message = mis_obj.get_bot_response_with_html_tags_intact() + "$$$" + catalogue_message
        mis_obj.bot_response = get_encrypted_message(catalogue_message, user_obj.bot, user_language, user_obj.channel.name, user_obj.user_id, False)
        mis_obj.save(update_fields=["bot_response"])
        return catalogue_payload
    except Exception as E:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        response["status_message"] = str(E) + str(exc_tb.tb_lineno)
        logger.error("exotal catalogue payload CallBack: %s at %s", str(
            E), str(exc_tb.tb_lineno), extra=log_param)
        return {}


#   MAIN FUNCTION
def whatsapp_webhook(request_packet):
    log_param = {'AppName': 'EasyChat', 'user_id': 'None',
                 'source': 'None', 'channel': 'WhatsApp', 'bot_id': 'None'}
    send_status = False
    response = {}
    response["status_code"] = 500
    response["status_message"] = "Internal server issues"
    response["mobile_number"] = ""
    try:
        #   WEBHOOK INIT
        logger.info("INSIDE Exotel WA WEBHOOK", extra=log_param)
        webhook_logger.error("Exotel WA WEBHOOK INCOMING_REQUEST_PACKET: %s",
                    str(request_packet), extra=log_param)
        # Block Check
        if "bot_id" in request_packet:
            BOT_ID = request_packet["bot_id"]
        if "messages" in request_packet["whatsapp"] and "from" in request_packet["whatsapp"]["messages"][0]:
            sender = str(request_packet["whatsapp"]["messages"][0]["from"])
            if sender[0] == "+":
                sender = sender[1:]
            mobile = sender
            session_id, is_session_started, is_business_initiated_session = get_session_id_based_on_user_session(
                mobile, BOT_ID)
            user_id = sender

            bot_obj = Bot.objects.filter(
                pk=int(BOT_ID), is_deleted=False).first()
            if bot_obj:
                bot_channel_obj = BotChannel.objects.get(
                    bot=bot_obj, channel=Channel.objects.get(name="WhatsApp"))
                if bot_channel_obj and bot_channel_obj.mobile_number_masking_enabled and bot_obj.masking_enabled:
                    user_id = hashlib.md5(sender.encode()).hexdigest()
            set_profile_obj = Profile.objects.filter(
                user_id=str(user_id), bot=bot_obj)
            profile_obj = set_profile_obj.first()
            if profile_obj and session_id:
                block_config_obj = BlockConfig.objects.filter(
                    bot=bot_obj).first()
                user_session_health_obj = UserSessionHealth.objects.filter(
                    session_id=session_id).last()

                if not block_config_obj:
                    block_config_obj = BlockConfig.objects.create(
                        bot=bot_obj)

                if not user_session_health_obj:
                    user_session_health_obj = UserSessionHealth.objects.create(
                        bot=bot_obj, profile=profile_obj, session_id=session_id)

                if user_session_health_obj.is_blocked:
                    if timezone.now() >= user_session_health_obj.unblock_time:
                        user_session_health_obj = UserSessionHealth.objects.create(
                            bot=bot_obj, profile=profile_obj, session_id=session_id)
                    else:
                        return

        #   EXOTEL DELIVERY STATUS:
        if 'whatsapp' in request_packet and 'messages' in request_packet['whatsapp'] and 'content' in request_packet['whatsapp']['messages'][0] and 'context' in request_packet['whatsapp']['messages'][0]['content']:
            exotel_push_reply_packets(request_packet)

        if "exo_status_code" in request_packet['whatsapp']['messages'][0] or "exo_detailed_status" in request_packet['whatsapp']['messages'][0]:
            return exotel_push_delivery_packets(request_packet)
        # whatsapp payment status response handling
        if (
            "statuses" in request_packet.keys()
            and "payment" in request_packet["statuses"][0]
        ):
            if "status" in request_packet["statuses"][0]:
                try:
                    user_id = request_packet["statuses"][0]["from"]
                    bot_obj = Bot.objects.filter(
                        pk=int(BOT_ID), is_deleted=False
                    ).first()
                    first_time_user = False
                    check_user = Profile.objects.filter(
                        user_id=str(user_id), bot=bot_obj
                    ).first()
                    if not check_user:
                        first_time_user = True
                        check_user = Profile.objects.create(
                            user_id=str(user_id), bot=bot_obj
                        )
                        if bot_channel_obj.return_initial_query_response:
                            check_user.selected_language = Language.objects.filter(
                                lang="en"
                            ).first()
                            check_user.save()

                    default_user_obj = check_user

                    status = request_packet["statuses"][0]["status"]
                    reference_id = request_packet["statuses"][0]["payment"][
                        "reference_id"
                    ]
                    to_number = request_packet["statuses"][0]["from"]

                    payment_status_handler(BOT_ID, default_user_obj, status, reference_id, to_number)

                except Exception as e:
                    exc_type, exc_obj, exc_tb = sys.exc_info()
                    logger.error(
                        "send_payment_status_error: %s at %s",
                        str(e),
                        str(exc_tb.tb_lineno),
                        extra=log_param,
                    )
                    return

    # == CREDENTIALS AND DETAILS: ==============================================
        exotel_apikey = ''
        exotel_number = request_packet["whatsapp"]["messages"][0]["to"]
        exotel_apitoken = ''
        exotel_sid = ''
        exotel_subdomain = ''
        sender = str(request_packet["whatsapp"]["messages"][0]["from"])
        if sender[0] == "+":
            sender = sender[1:]
        receiver = str(request_packet["whatsapp"]["messages"][0]["to"])
        if receiver[0] == "+":
            receiver = receiver[1:]
        BOT_ID = request_packet["bot_id"]
        DEFAULT_BOT_ID = request_packet["bot_id"]
        default_bot_obj = Bot.objects.get(
            pk=int(DEFAULT_BOT_ID), is_deleted=False)
        mobile = sender
        response["mobile_number"] = sender
        log_param["user_id"] = sender
        log_param["bot_id"] = BOT_ID
        logger.info("Sender: %s", str(sender), extra=log_param)
        logger.info("Reciever: %s", str(receiver), extra=log_param)
        whatsapp_mobile_number = receiver
        vendor_object = None

        session_id, is_session_started, is_business_initiated_session = get_session_id_based_on_user_session(
            mobile, BOT_ID)
        whatsapp_credentials_obj = cache.get(
            "WhatsappCredentialsConfig-" + str(DEFAULT_BOT_ID))
        if not whatsapp_credentials_obj:
            whatsapp_credentials_obj = WhatsappCredentialsConfig.objects.filter(
                bot=bot_obj).first()
            cache.set("WhatsappCredentialsConfig-" + str(DEFAULT_BOT_ID),
                      whatsapp_credentials_obj, settings.CACHE_TIME)
        if whatsapp_credentials_obj:
            exotel_apikey = whatsapp_credentials_obj.api_key
            exotel_apitoken = whatsapp_credentials_obj.api_token
            exotel_sid = whatsapp_credentials_obj.sid
            exotel_subdomain = whatsapp_credentials_obj.subdomain
        else:
            check_and_send_broken_bot_mail(BOT_ID, "WhatsApp", "", {
                                           "error": "WhatsApp Credentials (exotel_apikey, exotel_apitoken, exotel_sid) are not added / saved properly."})
        bot_channel_obj = BotChannel.objects.get(
            bot=bot_obj, channel=Channel.objects.get(name="WhatsApp"))

        session_id, is_session_started, is_business_initiated_session = get_session_id_based_on_user_session(
            mobile, BOT_ID)

        user_id = sender
        if bot_channel_obj.mobile_number_masking_enabled and bot_obj.masking_enabled:
            user_id = hashlib.md5(sender.encode()).hexdigest()

    #   CHECK FOR NEW USER:
        first_time_user = False
        check_user = set_profile_obj.first()
        if not check_user:
            first_time_user = True
            check_user = Profile.objects.create(
                user_id=str(user_id), bot=bot_obj)
            if bot_channel_obj.return_initial_query_response:
                check_user.selected_language = Language.objects.filter(
                    lang="en").first()
                check_user.save()

        default_user_obj = check_user
        logger.info("Is New User: %s", first_time_user, extra=log_param)

        #   GET PREVIOUS BOT ID
        user_obj = set_profile_obj
        if user_obj:
            user_obj = user_obj[0]
            data_obj = Data.objects.filter(
                user=user_obj, variable="bot_id")
            data_obj = data_obj.first()
            if data_obj:
                BOT_ID = json.loads(data_obj.get_value())
                bot_obj = Bot.objects.get(pk=int(BOT_ID), is_deleted=False)
                logger.info("Bot id " + str(BOT_ID), extra=log_param)
                log_param["bot_id"] = BOT_ID
                session_id, is_session_started, is_business_initiated_session = get_session_id_based_on_user_session(mobile, BOT_ID)

    #   CHECK USER MESSAGE TYPE: text, image, document, voice, location
        message_type = request_packet["whatsapp"]["messages"][0]["content"]["type"]
        logger.info("Message Type data: %s", message_type, extra=log_param)
        logger.info("data check")
    #   GLOBAL CONFIGURATION VARIABLES:
        MESSAGE_HEADER = "BOT"    # e.g bot name 'Maya :'
        MESSAGE_FOOTER = "BOT"    # e.g '© Kotak Securities Limited.'
        LIST_HEADER_FOOTER_VISIBLE = False
        send_default_quick_reply = False
        send_default_list_options = True
        list_interactive_menu_button_text = "Select"
        list_interactive_options_title = "Options"
        main_menu_intent_name = "Main Menu"
        max_attachment_size_allowed = 5.0  # In MBs
        # intent to be triggered during outflow attachment. e.g Collect User Attachment
        outflow_attachment_intent_name = "Collect User Attachment"
        save_outflow_attachment = False  # Whether to save outflow attachments or not
        invalid_attachment_notification = get_emojized_message(
            ":warning: *Failed to send file attachment!* \nYour file is either invalid or greater than "+str(max_attachment_size_allowed)+" MB.")
        trigger_outflow_attachment_intent = False
        # recommendation that will be appended as options when flow ends
        sticky_recommendations = []
        sticky_choices = []    # choices that will be appended as options when flow ends
        is_compact_recommendations_choices = True  # Single new line after each option
        # max bubble size after which options will be appended in new bubble(s)
        max_choices_recommendations_bubble_size = 5
        choices_recommendations_header = "To select from the below option(s), enter the *option number*:\n\n"
        choices_recommendations_footer = ""
        # max bubble size for cards after which it will append new bubble(s).
        max_cards_bubble_size = 20
        go_back_text = "Go Back"
        feedback_question = "Was this helpful?"
        feedback_option_yes = get_emojized_message(":thumbs_up:")+" Yes"
        feedback_option_no = get_emojized_message(":thumbs_down:") + " No"
        customer_ends_livechat_text = "LiveChat Session has ended."
        customer_ends_livechat_err_text = "Failed to end the session due to some connectivity issue. Please type 'end chat' again."
        helpful_intent_name = "Helpful"
        unhelpful_intent_name = "Unhelpful"
        ask_to_enter_text = "Please type"
        livechat_terminate_message = "end chat"
        recommendations_after_language_change = []
        # Add the name of authentication intents to avoid looping when the same is called direclty.
        authentication_intent_names = []
        greeting_intent_names = []
        language_change_query_list = [
            "change language", "change the language", "language change", "switch language"]

    #   GET USER ATTACHMENTS AND MESSAGES:
        selected_language = "en"
        is_location = True
        is_attachement = True
        is_attachment_saved = False
        is_failure_response_required = False
        message = None
        filepath = None
        is_suggestion = False
        file_caption = None
        REVERSE_WHATSAPP_MESSAGE_DICT = {}
        is_feedback_required = False
        is_go_back_enabled = False
        reverse_mapping_index = 0
        attachment_type = ""

        message_id = None
        is_whatsapp_attachment_required, allowed_file_types = check_is_attachment_required(
            user_id, bot_obj)

        if message_type == "text" or message_type == "button" or message_type == "interactive" or message_type == "order" or message_type == "csat":
            is_attachement = False
            is_location = False
        if is_attachement:
            # image, document, voice
            if message_type.strip().lower() == "unknown":
                attachment_type = "unknown"
                attachment_packet = {}
            else:
                attachment_type = message_type
                attachment_packet = request_packet["whatsapp"]["messages"][0]["content"][attachment_type]
            logger.info(" Whatsapp attachment packet: %s",
                        str(attachment_packet), extra=log_param)

            if "caption" in attachment_packet and attachment_packet["caption"]:
                file_caption = attachment_packet["caption"]

            livechat_user = Profile.objects.filter(user_id=str(user_id), bot=bot_obj).first()
            if is_whatsapp_attachment_required == True or save_outflow_attachment == True:
                if attachment_type == "unknown":
                    is_attachment_saved = False
                else:
                    filepath, is_attachment_saved = get_whatsapp_file_attachment(
                        request_packet["whatsapp"]["messages"][0]["content"][str(attachment_type)]["url"], max_attachment_size_allowed, allowed_file_types)

                    if not is_attachment_saved:
                        send_status = send_whatsapp_text_message(
                            exotel_apikey, exotel_apitoken, exotel_number, exotel_sid, exotel_subdomain, get_translated_text(invalid_attachment_notification, default_user_obj.selected_language, EasyChatTranslationCache), str(mobile), preview_url=False)
                        if send_status:
                            logger.info("Invalid Attachment Notifcation Sent:",
                                        extra=log_param)
                            response["status_code"] = 200
                            response["status_message"] = "Request processed successfully."
                            return response

            elif first_time_user == False and livechat_user and livechat_user.livechat_connected:
                if attachment_type == "unknown":
                    is_attachment_saved = False
                else:
                    # need to check

                    filepath, is_attachment_saved = get_whatsapp_file_attachment(
                        request_packet["whatsapp"]["messages"][0]["content"][str(attachment_type)]["url"], max_attachment_size_allowed)
            else:
                is_failure_response_required = True
            message = "attachment"
        else:
            #   Regular Message:
            if message_type == "text" or message_type == "csat":
                message = request_packet["whatsapp"]["messages"][0]["content"]["text"]["body"]
                logger.info("User message reply: %s",
                            str(message))
            #   Quick Reply Message:
            elif message_type == "button":
                message = request_packet['whatsapp']['messages'][0]['content']['button']['text']
                logger.info("User quick reply: %s",
                            str(message), extra=log_param)
            #   Interactive List Reply Message:
            elif message_type == "interactive":
                if "button_reply" in request_packet["whatsapp"]["messages"][0]["content"]["interactive"]:
                    message = request_packet["whatsapp"]["messages"][0]["content"]["interactive"]["button_reply"]["title"]
                    message_id = request_packet["whatsapp"]["messages"][0]["content"]["interactive"]["button_reply"]["id"]
                    logger.info("User quick reply: %s",
                                str(message), extra=log_param)
                elif "list_reply" in request_packet["whatsapp"]["messages"][0]["content"]["interactive"]:
                    message = request_packet["whatsapp"]["messages"][0]["content"]["interactive"]["list_reply"]["title"]
                    message_id = request_packet["whatsapp"]["messages"][0]["content"]["interactive"]["list_reply"]["id"]
                    logger.info("User list reply: %s",
                                str(message), extra=log_param)
                    
                # >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> [CUSTOM] WhatsAppFlow Integration >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
                # USER FORM REPLY        
                elif "nfm_reply" in request_packet["whatsapp"]["messages"][0]["content"]["interactive"]:
                    message = request_packet["whatsapp"]["messages"][0]["content"]["interactive"]["nfm_reply"]["body"]
                    webhook_logger.info("=== chk User message form reply: %s",
                                 str(message), extra=log_param)
                    message_form_data = request_packet["whatsapp"]["messages"][0]["content"]["interactive"]["nfm_reply"]["response_json"]
                    webhook_logger.info("=== chk User form reply: %s",
                                 str(message_form_data), extra=log_param)
                # <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<

                # whatsapp flow submitted response trigger
                # elif "nfm_reply" in request_packet["whatsapp"]["messages"][0]["content"]["interactive"]:
                #     try:
                #         flow_form_packet = request_packet["whatsapp"]["messages"][0]["content"]
                #         message_id = flow_form_packet["context"]["sid"]
                #         response_json = flow_form_packet["interactive"]["nfm_reply"]["response_json"]
                #         response_json = response_json.replace('\\"', '"')
                #         response_json = json.loads(response_json)
                #         user_id = flow_form_packet.get("from", None)
                #         if user_id is None:
                #             user_id = request_packet["whatsapp"]["messages"][0]["from"]
                #         user_id = user_id.replace("+", "")
                #         save_flow_response(BOT_ID, user_id, message_id, response_json)

                #         return
                #     except Exception as e:
                #         exc_type, exc_obj, exc_tb = sys.exc_info()
                #         logger.error("flow_response_save failed: %s at %s", str(e), str(exc_tb.tb_lineno), extra=log_param)
                #         return

            elif message_type == "order":
                catalogue_obj = WhatsappCatalogueDetails.objects.filter(
                    bot=bot_obj, is_catalogue_enabled=True).first()
                order_packet = request_packet["whatsapp"]["messages"][0]['content']["order"]
                catalog_id_data = json.loads(catalogue_obj.catalogue_id)
                order_packet["catalog_id"] = str(catalog_id_data)
                cart_obj = WhatsappCatalogueCart.objects.filter(
                    user=default_user_obj, bot=bot_obj, is_purchased=False).last()
                if not cart_obj:
                    cart_obj = WhatsappCatalogueCart.objects.create(
                        user=default_user_obj, bot=bot_obj, is_purchased=False)
                if catalogue_obj:
                    catalogue_metadata = json.loads(
                        catalogue_obj.catalogue_metadata)
                    if "merge_cart_enabled" in catalogue_metadata and catalogue_metadata["merge_cart_enabled"] == "true":
                        previous_order_packet = check_if_items_in_cart_exists(
                            bot_obj, user_id)
                        if previous_order_packet:
                            previous_order_packet["catalog_id"] = str(
                                catalog_id_data)
                            cart_obj.pending_cart_packet = json.dumps(
                                order_packet)
                            cart_obj.cart_update_time = timezone.now()
                            cart_obj.save(
                                update_fields=['pending_cart_packet', 'cart_update_time'])
                            text_message, cart_options = send_merge_cart_message(
                                bot_obj, default_user_obj, order_packet, previous_order_packet, catalogue_metadata)
                            send_status = sendWhatsAppQuickReplyMessage(
                                exotel_apikey, exotel_apitoken, exotel_number, exotel_sid, exotel_subdomain, cart_options, MESSAGE_HEADER, text_message, MESSAGE_FOOTER, mobile, lang=selected_language)
                            response["status_code"] = 200
                            response["status_message"] = "Request processed successfully."
                            return response
                cart_obj.current_cart_packet = json.dumps(order_packet)
                cart_obj.cart_update_time = timezone.now()
                message = "Catalogue ID: " + order_packet["catalog_id"]
                item_names = []
                cart_total = 0
                for product_item in order_packet["product_items"]:
                    item_obj = WhatsappCatalogueItems.objects.filter(
                        catalogue_id=order_packet["catalog_id"], retailer_id=product_item["product_retailer_id"]).first()
                    if item_obj:
                        item_name = item_obj.item_name
                    else:
                        item_name = product_item["product_retailer_id"]
                    message += " " + item_name + " X " + \
                        str(product_item["quantity"])
                    parsed_item_name = str(product_item["quantity"]) + " x " + item_name
                    item_names.append(parsed_item_name)
                    cart_total += product_item["quantity"] * \
                        product_item["item_price"]
                    currency = product_item["currency"]
                parsed_cart_message = ", ".join(item_names)
                currency_obj = CurrencyCodes()
                currency_symbol = currency_obj.get_symbol(currency)
                cart_total = str(currency_symbol) + str(cart_total)
                cart_obj.cart_total = cart_total
                cart_obj.parsed_cart_packet = parsed_cart_message
                cart_obj.save(
                    update_fields=['current_cart_packet', 'cart_update_time', 'cart_total', 'parsed_cart_packet'])

            is_catalogue_message, text_message, cart_items, user_message = check_for_whatsapp_catalogue_message_exotel(
                request_packet, message, message_type, default_user_obj, default_bot_obj)
            if is_catalogue_message:
                user_language = default_user_obj.selected_language
                user_language = user_language.lang if user_language else "en"
                if user_language != "en":
                    text_message = get_translated_text(
                        text_message, user_language, EasyChatTranslationCache)
                send_status = send_whatsapp_text_message(
                    exotel_apikey, exotel_apitoken, exotel_number, exotel_sid, exotel_subdomain, text_message, str(mobile), preview_url=False)
                create_mis_for_catalogue_message(
                    bot_obj, user_obj, text_message, None, user_message)
                message = cart_items

            reverse_message = None

            if message_id:
                reverse_message, is_suggestion = get_message_from_reverse_whatsapp_mapping(
                    message_id, user_id, default_bot_obj)

            if not reverse_message:
                reverse_message, is_suggestion = get_message_from_reverse_whatsapp_mapping(
                    message, user_id, default_bot_obj)

            if reverse_message != None:
                message = reverse_message
            else:
                is_suggestion = False

            if message_type == "csat":
                is_suggestion = True

            logger.info("User Message: %s", str(message), extra=log_param)

            #   Intent Level Feedback Check
            message = check_intent_level_feedback(user_id, message, bot_obj)

            #   Go Back Check
            if first_time_user == False:
                user = Profile.objects.filter(user_id=str(user_id), bot=bot_obj).first()
                check_go_back_enabled = Data.objects.filter(
                    user=user, variable="is_go_back_enabled")
                if len(check_go_back_enabled) > 0 and str(check_go_back_enabled[0].value) == 'true':
                    is_go_back_enabled = True

        logger.info("User Message(final): %s", str(message), extra=log_param)

        bot_channel_obj = BotChannel.objects.get(
            bot=bot_obj, channel=Channel.objects.get(name="WhatsApp"))

        if bot_channel_obj.mobile_number_masking_enabled and bot_obj.masking_enabled:
            user_id = hashlib.md5(sender.encode()).hexdigest()

        languages_supported = bot_channel_obj.languages_supported.all()

    #   CHECK IF CHANGE LANGUAGE WAS TRIGGERED
        if is_change_language_triggered(user_id, default_bot_obj) and not user_obj.livechat_connected:
            logger.info("is_change_language_triggered: True", extra=log_param)
            try:
                is_supported = False
                lang_codes = list(languages_supported.values('lang'))
                for code in lang_codes:
                    if code["lang"].strip().lower() == message.strip().lower():
                        is_supported = True
                        break
                if is_supported:
                    lang_obj = Language.objects.filter(lang=message).first()
                    profile_obj = set_profile_obj.first()
                    profile_obj.selected_language = lang_obj
                    profile_obj.save(update_fields=["selected_language"])
                    text_message = "You have selected " + \
                        str(lang_obj.display) + \
                        ". If you want to change your language again please type"
                    text_message = get_translated_text(
                        text_message, lang_obj.lang, EasyChatTranslationCache)
                    text_message = text_message + ' "Change Language"'
                    if recommendations_after_language_change:

                        language_script_type = lang_obj.language_script_type

                        hand_emoji_direction = ":point_right:"
                        if language_script_type == "rtl":
                            hand_emoji_direction = ":point_left:"

                        translated_recommendations_after_language_change = []
                        if lang_obj.lang != "en":
                            for item in recommendations_after_language_change:
                                option_name = get_translated_text(
                                    str(item), lang_obj.lang, EasyChatTranslationCache)
                                translated_recommendations_after_language_change.append(
                                    option_name)
                            recommendations_after_language_change = translated_recommendations_after_language_change
                        empty_recommendations = False
                        if send_default_quick_reply or send_default_list_options:
                            total_options_count = len(
                                recommendations_after_language_change)
                            TEMP_REVERSE_WHATSAPP_MESSAGE_DICT = {}
                            BUTTON_DISPLAY_NAMES = []
                            if send_default_quick_reply == True:
                                if total_options_count <= 3 and len(text_message) < 1024:
                                    if check_interative_capability_for_quick_reply(options=recommendations_after_language_change, options_type="recommendations"):
                                        for recommendation in recommendations_after_language_change:
                                            if recommendation not in BUTTON_DISPLAY_NAMES:
                                                option_name = recommendation
                                                BUTTON_DISPLAY_NAMES.append(
                                                    option_name)
                                                TEMP_REVERSE_WHATSAPP_MESSAGE_DICT[recommendation] = recommendation

                                        empty_recommendations = True
                                        sendWhatsAppQuickReplyMessage(
                                            exotel_apikey, exotel_apitoken, exotel_number, exotel_sid, exotel_subdomain, BUTTON_DISPLAY_NAMES, MESSAGE_HEADER, text_message, MESSAGE_FOOTER, mobile, "text", None, lang=lang_obj.lang)
                                        is_send = sendWhatsAppInteractiveListMessage(exotel_apikey, exotel_apitoken, exotel_number, exotel_sid, exotel_subdomain, list_interactive_options_title, BUTTON_DISPLAY_NAMES,
                                                                                     BUTTON_HEADER, message, BUTTON_FOOTER, mobile, menu_button_text=list_interactive_menu_button_text, extra="None")
                                
                                        REVERSE_WHATSAPP_MESSAGE_DICT = TEMP_REVERSE_WHATSAPP_MESSAGE_DICT
                            if send_default_list_options == True:
                                if total_options_count > 3 and total_options_count < 11 and len(text_message) < 1024:
                                    if check_interative_capability_for_list(options=recommendations_after_language_change, options_type="recommendations"):
                                        if lang_obj.lang != "en":
                                            list_interactive_menu_button_text = get_translated_text(
                                                list_interactive_menu_button_text, selected_language, EasyChatTranslationCache)
                                            list_interactive_options_title = get_translated_text(
                                                list_interactive_options_title, selected_language, EasyChatTranslationCache)
                                        for recommendation in recommendations_after_language_change:
                                            if recommendation not in BUTTON_DISPLAY_NAMES:
                                                option_name = recommendation
                                                BUTTON_DISPLAY_NAMES.append(
                                                    option_name)
                                                TEMP_REVERSE_WHATSAPP_MESSAGE_DICT[recommendation] = recommendation
                                        BUTTON_HEADER = MESSAGE_HEADER
                                        BUTTON_FOOTER = MESSAGE_FOOTER
                                        if LIST_HEADER_FOOTER_VISIBLE == False:
                                            BUTTON_HEADER = " "
                                            BUTTON_FOOTER = " "
                                        is_send = sendWhatsAppInteractiveListMessage(exotel_apikey, exotel_apitoken, exotel_number, exotel_sid, exotel_subdomain, list_interactive_options_title, BUTTON_DISPLAY_NAMES,
                                                                                     BUTTON_HEADER, message, BUTTON_FOOTER, mobile, menu_button_text=list_interactive_menu_button_text, extra="None")
                                        empty_recommendations = True
                                        REVERSE_WHATSAPP_MESSAGE_DICT = TEMP_REVERSE_WHATSAPP_MESSAGE_DICT
                        if empty_recommendations == False:
                            send_status = send_whatsapp_text_message(
                                exotel_apikey, exotel_apitoken, exotel_number, exotel_sid, exotel_subdomain, text_message, mobile, preview_url=False)
                            if lang_obj.lang != "en":
                                ask_to_enter_text = get_translated_text(
                                    ask_to_enter_text, lang_obj.lang, EasyChatTranslationCache)
                                choices_recommendations_header = get_translated_text(
                                    choices_recommendations_header, lang_obj.lang, EasyChatTranslationCache) + "\n"
                                choices_recommendations_footer = get_translated_text(
                                    choices_recommendations_footer, lang_obj.lang, EasyChatTranslationCache)
                            recommendation_str = ""
                            for index in range(len(recommendations_after_language_change)):
                                if index % max_choices_recommendations_bubble_size == 0 and index != 0:
                                    recommendation_str += "$$$"
                                option_name = get_translated_text(str(
                                    recommendations_after_language_change[index]), lang_obj.lang, EasyChatTranslationCache)
                                REVERSE_WHATSAPP_MESSAGE_DICT[str(
                                    index+1)] = str(option_name)
                                recommendation_str += ask_to_enter_text+" *" + \
                                    str(index+1)+"* " + hand_emoji_direction + "  " + \
                                    str(option_name)+"\n"
                                if is_compact_recommendations_choices == False:
                                    recommendation_str = +"\n"
                            recommendation_str = choices_recommendations_header + "\n" + \
                                recommendation_str + choices_recommendations_footer
                            recommendation_str = get_emojized_message(
                                recommendation_str)
                            send_status = send_whatsapp_text_message(
                                exotel_apikey, exotel_apitoken, exotel_number, exotel_sid, exotel_subdomain, recommendation_str, mobile, preview_url=False)

                        logger.info("REVERSE_WHATSAPP_MESSAGE_DICT: %s", str(
                            REVERSE_WHATSAPP_MESSAGE_DICT), extra=log_param)
                        save_data(default_user_obj, json_data={
                                  "REVERSE_WHATSAPP_MESSAGE_DICT": REVERSE_WHATSAPP_MESSAGE_DICT},  src="None", channel="WhatsApp", bot_id=DEFAULT_BOT_ID,  is_cache=True)

                    else:
                        send_status = send_whatsapp_text_message(
                            exotel_apikey, exotel_apitoken, exotel_number, exotel_sid, exotel_subdomain, text_message, mobile, preview_url=False)
                    response["status_code"] = 200
                    response["status_message"] = "Request processed successfully."
                    return response
            except Exception as e:
                logger.error("is_change_language_triggered: %s",
                             str(e), extra=log_param)

        user_obj = Profile.objects.filter(user_id=str(user_id), bot=bot_obj)
        if languages_supported.count() == 1 and user_obj.count() > 0 and user_obj[0].selected_language == None:
            user_obj[0].selected_language = languages_supported[0]
        if languages_supported.count() > 1 and user_obj.count() > 0 and user_obj[0].selected_language == None:
            user_obj[0].selected_language = languages_supported.filter(lang="en")[
                0]
        
        is_livechat_whatsapp_reinitiated, livechat_whatsapp_reinitiation_keyword = check_if_livechat_whatsapp_reinitiation_triggered(
            message, user_obj[0])

    #   CHECK IF CHANGE LANGUAGE IS CALLED
        lang_message = re.sub(' +', ' ', message)
        language_change_query_list += list(EasyChatTranslationCache.objects.filter(
            input_text__iexact="change language").values_list('translated_data', flat=True).distinct())
        if isinstance(lang_message, str) and lang_message.lower().strip() in language_change_query_list and user_obj.count() > 0 and not user_obj[0].livechat_connected:
            REVERSE_WHATSAPP_MESSAGE_DICT = {}
            language_str, REVERSE_WHATSAPP_MESSAGE_DICT = get_language_change_response(
                str(user_id), BOT_ID, REVERSE_WHATSAPP_MESSAGE_DICT)
            if language_str != "":
                language_str = get_emojized_message(language_str)
                send_status = send_whatsapp_text_message(
                    exotel_apikey, exotel_apitoken, exotel_number, exotel_sid, exotel_subdomain, language_str, str(sender), preview_url=False)
                logger.info("Is change language response sent: %s",
                            str(send_status), extra=log_param)

                user = set_user(str(sender), message,
                                "None", "WhatsApp", BOT_ID)
                save_data(default_user_obj, json_data={
                          "CHANGE_LANGUAGE_TRIGGERED": True}, src="None", channel="WhatsApp", bot_id=DEFAULT_BOT_ID, is_cache=True)

                logger.info("REVERSE_WHATSAPP_MESSAGE_DICT: %s", str(
                    REVERSE_WHATSAPP_MESSAGE_DICT), extra=log_param)
                save_data(default_user_obj, json_data={
                          "REVERSE_WHATSAPP_MESSAGE_DICT": REVERSE_WHATSAPP_MESSAGE_DICT}, src="None", channel="WhatsApp", bot_id=DEFAULT_BOT_ID, is_cache=True)

                response["status_code"] = 200
                response["status_message"] = "Request processed successfully."
                return response

    #   GET LANGUAGE SELECTED BY USER
        try:
            selected_language = Profile.objects.filter(
                user_id=str(user_id), bot=bot_obj).first().selected_language

            if not selected_language:
                selected_language = "en"
            else:
                selected_language = selected_language.lang
                languages_supported = Bot.objects.get(
                    pk=int(BOT_ID), is_deleted=False).languages_supported
                languages_supported = languages_supported.filter(
                    lang=selected_language)

                if not languages_supported:
                    selected_language = "en"
        except Exception:
            selected_language = 'en'
            user = set_user(str(sender), message, "None", "WhatsApp", BOT_ID)
            languages_supported = Language.objects.get(lang="en")
            if user.selected_language == None:
                user.selected_language = languages_supported
                user.save(update_fields=["selected_language"])

        mobile = str(sender)  # User mobile
        waNumber = str(receiver)  # Bot Whatsapp Number
        is_feedback_request = False
        message_request_id = request_packet.get("messages", [{}])
        if len(message_request_id) > 0:
            message_request_id = str(message_request_id[0].get("id", ''))
        if message_request_id == WHATSAPP_CSAT_FEEDBACK_ID:
            is_feedback_request = True

    #   WEBHOOK EXECUTE FUNCTION CALL
        channel_params = {"user_mobile": mobile, "bot_wa_number": waNumber, "attached_file_path": filepath, "whatsapp_file_caption": file_caption, "is_new_user": first_time_user, "QueryChannel": "WhatsApp", "is_feedback_request": is_feedback_request,
                          "is_go_back_enabled": is_go_back_enabled, "entered_suggestion": is_suggestion, "session_id": session_id, "is_session_started": is_session_started, "is_business_initiated_session": is_business_initiated_session, "is_failure_response_required": is_failure_response_required,
                          "is_attachment_saved": is_attachment_saved, "is_livechat_whatsapp_reinitiated": is_livechat_whatsapp_reinitiated, "livechat_whatsapp_reinitiation_keyword": livechat_whatsapp_reinitiation_keyword, "attachment_type": attachment_type}
        
        # >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> [CUSTOM] WhatsAppFlow Integration >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
        if message_form_data: # storing form data WA
            channel_params["whatsapp_form_data"] = json.loads(message_form_data)
        webhook_logger.info("whatsapp_form_data CHK : %s",str(channel_params),extra=log_param)
        
        # <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
        
        
        logger.info("EXOTELCallBack Channel params:  %s",
                    str(channel_params), extra=log_param)
        logger.info("Bot id " + str(BOT_ID), extra=log_param)
        if "response" in request_packet:
            whatsapp_response = request_packet["response"]
        else:
            whatsapp_response = execute_query(user_id, BOT_ID, "uat", str(
                message), selected_language, "WhatsApp", json.dumps(channel_params), message)
        logger.info("EXOTELCallBack execute_query response %s and selected_language : %s", str(
            whatsapp_response), str(selected_language), extra=log_param)

        try:
            if whatsapp_response["response"].get("pdf_search_results") and whatsapp_response["response"].get("pdf_search_type") == "2" or whatsapp_response["response"].get("is_azure_based_chatpdf_enabled"):
                if(whatsapp_response["response"].get("is_azure_based_chatpdf_enabled", False)):
                    user_data = {"bot_pk": BOT_ID, "mobile": mobile, "chat_history": whatsapp_response["response"].get(
                        "pdf_search_prompt", ''), "user_query": message, "user_language": whatsapp_response["response"].get("user_language", '')}
                    chatgpt_message, sources_list, show_pdf_references, recommendations = get_whatsapp_azure_pdf_response(
                        user_data, Profile)
                    
                    if recommendations:
                        send_sectioned_whatsapp_interactive_list(exotel_apikey, exotel_apitoken, exotel_number, exotel_sid, exotel_subdomain, [], sources_list, "", chatgpt_message, "Generate By AI", str(mobile))
                    else:
                        send_whatsapp_text_message(
                            exotel_apikey, exotel_apitoken, exotel_number, exotel_sid, exotel_subdomain, chatgpt_message, str(mobile), preview_url=False)

                    pdf_cards = []
                    if show_pdf_references:
                        for pdf_name in sources_list:
                            pdf_file_url = f"{settings.EASYCHAT_HOST_URL}/chat/view-information-source/{BOT_ID}/{pdf_name}"
                            pdf_cards.append({
                                "content": "",
                                "page_number": "",
                                "link": pdf_file_url,
                                "title": pdf_name,
                                "pattern": "",
                                "pdf_search_id": ""
                            })
                            _ = sendWhatsAppMediaMessage(
                            exotel_apikey, exotel_apitoken, exotel_number, exotel_sid, exotel_subdomain, "document", str(pdf_file_url), str(mobile), caption=None)

                    chatgpt_response_data = {"bot_id": BOT_ID, "user_id": whatsapp_response["user_id"], "session_id": session_id,
                                             "channel": "WhatsApp", "src": selected_language, "chatgpt_response": chatgpt_message, "bot_obj": bot_obj, 
                                             "pdf_cards": pdf_cards}

                    save_chatgpt_response_in_mis_dashboard(
                        chatgpt_response_data, MISDashboard)
                    save_chatgpt_token_audit_trail(
                        bot_obj, chatgpt_response_data["chatgpt_response"], False)

                    response["status_code"] = 200
                    response["status_message"] = "Request processed successfully."
                    return response
        except Exception as E:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            logger.error("get_whatsapp_azure_pdf_response error : %s at %s",
                         str(E), str(exc_tb.tb_lineno), extra=log_param)
        
        
        if "status_message" in whatsapp_response and whatsapp_response["status_message"] == "malicious file":
            send_status = send_whatsapp_text_message(
                exotel_apikey, exotel_apitoken, exotel_number, exotel_sid, exotel_subdomain, invalid_attachment_notification, str(mobile), preview_url=False)
            if send_status:
                logger.info(
                    "Invalid LiveChat Attachment Notifcation Sent:", extra=log_param)
                response["status_code"] = 200
                response["status_message"] = "Request processed successfully."
                return response

        #   Invalid Attachment Notifcation:
        is_invalid_attachment_and_block = False
        if is_attachement and is_attachment_saved == False:
            if whatsapp_response.get("intent_name") in [
                "User query warning response",
                "User query block response",
                "Keyword warning response",
                "Keyword block response"
            ]:
                is_invalid_attachment_and_block = True
            if not is_invalid_attachment_and_block and not is_failure_response_required:
                send_status = send_whatsapp_text_message(
                    exotel_apikey, exotel_apitoken, exotel_number, exotel_sid, exotel_subdomain, invalid_attachment_notification, str(mobile), preview_url=False)
                if send_status:
                    logger.info("Invalid Attachment Notifcation Sent:",
                                extra=log_param)
                    response["status_code"] = 200
                    response["status_message"] = "Request processed successfully."
                    return response

        #   Check LiveChat:
        if "is_livechat" in whatsapp_response and whatsapp_response["is_livechat"] == "true":
            if selected_language != "en":
                livechat_terminate_message = get_translated_text(
                    livechat_terminate_message, selected_language, EasyChatTranslationCache)
            if message.lower() == "end chat" or message.lower() == livechat_terminate_message:
                livechat_notification = customer_ends_livechat_text
                send_status = send_whatsapp_text_message(
                    exotel_apikey, exotel_apitoken, exotel_number, exotel_sid, exotel_subdomain, livechat_notification, str(mobile), preview_url=False)
            return whatsapp_response
        
        if "is_external_query_search" in whatsapp_response["response"] and whatsapp_response["response"]["is_external_query_search"]:
            response["status_code"] = 200
            response["status_message"] = "Request processed successfully."
            return response

        if whatsapp_response.get("intent_name", "") == "Spam user":
            return

        if "whatsapp_list_message_header" in whatsapp_response["response"]:
            list_interactive_menu_button_text = whatsapp_response[
                "response"]["whatsapp_list_message_header"]
            if selected_language != "en":
                list_interactive_menu_button_text = get_translated_text(
                    list_interactive_options_title, selected_language, EasyChatTranslationCache)

        if 'bot_id' in whatsapp_response:
            bot_id = whatsapp_response['bot_id']

            default_bot_obj = Bot.objects.get(
                pk=int(DEFAULT_BOT_ID), is_deleted=False)
            profile_obj = set_profile_obj

            if profile_obj and bot_id != "":
                save_data(profile_obj[0], {
                          "LAST_SELECTED_BOT": bot_id}, "None", "WhatsApp", bot_id, is_cache=True)

                save_data(profile_obj[0], {"bot_id": str(bot_id)},
                          "None", "WhatsApp", bot_id, is_cache=True)

                bot_obj = Bot.objects.get(pk=bot_id, is_deleted=False)

        if "is_bot_switched" in whatsapp_response and whatsapp_response["is_bot_switched"]:
            profile_obj = Profile.objects.filter(
                user_id=user_id, bot=bot_obj).first()
            profile_obj.selected_language = Language.objects.filter(
                lang="en").first()
            profile_obj.save(update_fields=["selected_language"])
            selected_language = "en"

    #   Change Response based on language selected:
        # for language auto detection
        if "language_src" in whatsapp_response["response"]:
            selected_language = whatsapp_response["response"]["language_src"]
            user_obj = user_obj[0]
            user_obj.selected_language = Language.objects.filter(
                lang=selected_language).first()
            user_obj.save(update_fields=["selected_language"])

        #   Change default texts based on language selected
        if selected_language != "en":
            main_menu_intent_name = get_translated_text(
                main_menu_intent_name, selected_language, EasyChatTranslationCache)
            outflow_attachment_intent_name = get_translated_text(
                outflow_attachment_intent_name, selected_language, EasyChatTranslationCache)
            invalid_attachment_notification = get_translated_text(
                invalid_attachment_notification, selected_language, EasyChatTranslationCache)
            choices_recommendations_header = get_translated_text(
                choices_recommendations_header, selected_language, EasyChatTranslationCache) + "\n"
            choices_recommendations_footer = get_translated_text(
                choices_recommendations_footer, selected_language, EasyChatTranslationCache) + "\n"
            go_back_text = get_translated_text(
                go_back_text, selected_language, EasyChatTranslationCache)
            feedback_question = get_translated_text(
                feedback_question, selected_language, EasyChatTranslationCache)
            feedback_option_yes = get_translated_text(
                feedback_option_yes, selected_language, EasyChatTranslationCache)
            feedback_option_no = get_translated_text(
                feedback_option_no, selected_language, EasyChatTranslationCache)
            customer_ends_livechat_text = get_translated_text(
                customer_ends_livechat_text, selected_language, EasyChatTranslationCache)
            customer_ends_livechat_err_text = get_translated_text(
                customer_ends_livechat_err_text, selected_language, EasyChatTranslationCache)
            helpful_intent_name = get_translated_text(
                helpful_intent_name, selected_language, EasyChatTranslationCache)
            unhelpful_intent_name = get_translated_text(
                unhelpful_intent_name, selected_language, EasyChatTranslationCache)
            ask_to_enter_text = get_translated_text(
                ask_to_enter_text, selected_language, EasyChatTranslationCache)
            list_interactive_menu_button_text = get_translated_text(
                list_interactive_menu_button_text, selected_language, EasyChatTranslationCache)
            list_interactive_options_title = get_translated_text(
                list_interactive_options_title, selected_language, EasyChatTranslationCache)
            #   From Bot Language Template:
            bot_language_template = RequiredBotTemplate.objects.filter(bot=Bot.objects.get(
                pk=BOT_ID, is_deleted=False), language=Language.objects.get(lang=selected_language))
            if bot_language_template.count() > 0:
                go_back_text = bot_language_template[0].go_back_text

        is_whatsapp_welcome_response = False
        if "is_whatsapp_welcome_response" in whatsapp_response["response"]:
            is_whatsapp_welcome_response = whatsapp_response["response"]["is_whatsapp_welcome_response"]

        is_response_to_be_language_processed = True

        if "is_response_to_be_language_processed" in whatsapp_response["response"]:
            is_response_to_be_language_processed = whatsapp_response[
                "response"]["is_response_to_be_language_processed"]

        if selected_language != "en" and is_response_to_be_language_processed:
            whatsapp_response = process_response_based_on_language(
                whatsapp_response, selected_language, EasyChatTranslationCache)
            if "whatsapp_spam_response" in whatsapp_response:
                whatsapp_response["whatsapp_spam_response"] = process_response_based_on_language(
                    whatsapp_response["whatsapp_spam_response"], selected_language, EasyChatTranslationCache)

    #   USER OBJECT:
        user = Profile.objects.filter(user_id=str(user_id), bot=bot_obj).first()
        # user.is_session_exp_msg_sent = False
        # user.save()

        language_script_type = user.selected_language.language_script_type if user.selected_language else "ltr"

        hand_emoji_direction = ":point_right:"
        if language_script_type == "rtl":
            hand_emoji_direction = ":point_left:"

    #   Auto Trigger Last Intent after Authentication:
        try:
            if whatsapp_response != {}:
                if str(whatsapp_response['status_code']) == '200' and whatsapp_response['response'] != {}:
                    if 'modes' in whatsapp_response['response']["text_response"] and whatsapp_response['response']["text_response"]['modes'] != {}:
                        if 'auto_trigger_last_intent' in whatsapp_response['response']["text_response"]['modes'] and whatsapp_response['response']["text_response"]['modes']['auto_trigger_last_intent'] == 'true':
                            if 'last_identified_intent_name' in whatsapp_response['response'] and whatsapp_response['response']['last_identified_intent_name'] != '':
                                auth_message = whatsappify_text(
                                    whatsapp_response["response"]["text_response"]["text"])
                                send_status = send_whatsapp_text_message(
                                    exotel_apikey, exotel_apitoken, exotel_number, exotel_sid, exotel_subdomain, auth_message, mobile, preview_url=False)
                                message = whatsapp_response['response']['last_identified_intent_name']
                                if message not in authentication_intent_names:
                                    channel_params["is_hidden_query"] = True
                                    whatsapp_response = execute_query(user_id, BOT_ID, "uat", str(
                                        message), selected_language, "WhatsApp", json.dumps(channel_params), message)
                                    logger.info("EXOTELCallBack: execute_query after Auth response %s", str(
                                        whatsapp_response), extra=log_param)
                                    is_response_to_be_language_processed = True

                                    if "is_response_to_be_language_processed" in whatsapp_response["response"]:
                                        is_response_to_be_language_processed = whatsapp_response[
                                            "response"]["is_response_to_be_language_processed"]

                                    if selected_language != "en" and is_response_to_be_language_processed:
                                        whatsapp_response = process_response_based_on_language(
                                            whatsapp_response, selected_language, EasyChatTranslationCache)
                                        if "whatsapp_spam_response" in whatsapp_response:
                                            whatsapp_response["whatsapp_spam_response"] = process_response_based_on_language(
                                                whatsapp_response["whatsapp_spam_response"], selected_language, EasyChatTranslationCache)
        except Exception as E:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            logger.error("Cannot identify Last Intent: %s at %s",
                         str(E), str(exc_tb.tb_lineno), extra=log_param)

    #   Check OutFlow Attachment:
        # Attachments which are received when user is not in attachment required flow and livechat session is off.
        logger.info("ExotelCallBack is_whatsapp_attachment not required:  %s", str(
            is_whatsapp_attachment_required == False), extra=log_param)
        logger.info("ExotelCallBack Is LiveChat OFF :  %s", str(
            user.livechat_connected == False), extra=log_param)
        logger.info("ExotelCallBack Is Attachment Recieved :  %s",
                    str(is_attachement), extra=log_param)
        logger.info("ExotelCallBack trigger_outflow_attachment_intent :  %s", str(
            trigger_outflow_attachment_intent), extra=log_param)
        if is_whatsapp_attachment_required == False and is_attachement == True and user.livechat_connected == False and trigger_outflow_attachment_intent == True:
            message = outflow_attachment_intent_name
            logger.info("ExotelCallBack OutFlow Attachment Detected and Query Selected:  %s", str(
                message), extra=log_param)
            whatsapp_response = execute_query(user_id, BOT_ID, "uat", str(
                message), selected_language, "WhatsApp", json.dumps(channel_params), message)
            logger.info("ExotelCallBack execute_query After OutFlow attachment %s", str(
                whatsapp_response), extra=log_param)
        if "is_attachment_required" in whatsapp_response:
            save_data(user, json_data={
                      "is_whatsapp_attachment_required": whatsapp_response["is_attachment_required"]},  src="en", channel="WhatsApp", bot_id=BOT_ID,  is_cache=True)
        else:
            save_data(user, json_data={"is_whatsapp_attachment_required": False},
                      src="en", channel="WhatsApp", bot_id=BOT_ID,  is_cache=True)

        if "choosen_file_type" in whatsapp_response:
            save_data(user, json_data={
                      "choosen_file_type": whatsapp_response["choosen_file_type"]},  src="en", channel="WhatsApp", bot_id=BOT_ID,  is_cache=True)
        else:
            Data.objects.filter(
                user=user, variable="choosen_file_type").delete()

    #   BOT RESPONSES: images, videos, pdfs, cards, choices, recommendations
        message = whatsapp_response["response"]["text_response"]["text"]
        modes = whatsapp_response["response"]["text_response"]["modes"]
        modes_param = whatsapp_response["response"]["text_response"]["modes_param"]
        recommendations = whatsapp_response["response"]["recommendations"]
        images = whatsapp_response["response"]["images"]
        videos = whatsapp_response["response"]["videos"]
        cards = whatsapp_response["response"]["cards"]
        pdfs = whatsapp_response["response"]["pdfs"]
        choices = whatsapp_response["response"]["choices"]
        is_flow_ended = whatsapp_response["response"]["is_flow_ended"]
        cleaned_recommendations = []
        for recm in recommendations:
            if isinstance(recm, dict) and "name" in recm:
                cleaned_recommendations.append(recm["name"])
            else:
                cleaned_recommendations.append(recm)
        recommendations = cleaned_recommendations

        cleaned_choices = []
        for choice in choices:
            if choice["display"] == helpful_intent_name or choice["display"] == unhelpful_intent_name:
                continue
            else:
                cleaned_choices.append(choice)
        choices = cleaned_choices

        logger.info("recommendations: %s", str(
            recommendations), extra=log_param)
        logger.info("choices: %s", str(choices), extra=log_param)
        logger.info("modes: %s", str(modes), extra=log_param)

    #   TEXT FORMATTING AND EMOJIZING:
        logger.info("Bot Message(Original): %s", str(message), extra=log_param)
        message = whatsappify_text(message)
        choices_recommendations_header = whatsappify_text(
            choices_recommendations_header)
        choices_recommendations_footer = whatsappify_text(
            choices_recommendations_footer)
        logger.info("Bot Message(Formatted): %s",
                    str(message), extra=log_param)

    # Empty message check:
        if message is None or message == "":
            message = "None"

        logger.info("message to be sent  %s", str(message), extra=log_param)
    #   Push Message Responses:
        if "template message was sent" in message.lower():
            message = ""
            recommendations = []
            choices = []

        if "whatsapp_menu_sections" in whatsapp_response["response"]:
            small_messages = message.split("$$$")
            BUTTON_HEADER = MESSAGE_HEADER
            BUTTON_FOOTER = MESSAGE_FOOTER
            if LIST_HEADER_FOOTER_VISIBLE == False:
                BUTTON_HEADER = " "
                BUTTON_FOOTER = " "
            for index, small_message in enumerate(small_messages):
                if index == (len(small_messages) - 1):
                    send_status, recommendations, REVERSE_WHATSAPP_MESSAGE_DICT = send_sectioned_whatsapp_interactive_list(exotel_apikey, exotel_apitoken, exotel_number, exotel_sid, exotel_subdomain, list_interactive_options_title, whatsapp_response[
                                                                                                                           "response"]["whatsapp_menu_sections"], BUTTON_HEADER, small_message.strip(), BUTTON_FOOTER, mobile, menu_button_text=list_interactive_menu_button_text, extra="None")
                    choices = []
                    if send_status:
                        message = ""
                    else:
                        message = small_message
                else:
                    send_whatsapp_text_message(
                        exotel_apikey, exotel_apitoken, exotel_number, exotel_sid, exotel_subdomain, small_message.strip(), mobile)

    #   Check FeedBack Required:
        if "is_feedback_required" in whatsapp_response["response"]:
            is_feedback_required = whatsapp_response["response"]["is_feedback_required"]

    #   Modes & Modes Params Based Actions:
        if "hide_bot_response" in modes.keys() and modes['hide_bot_response'] == "true":
            message = ""

        if "is_drop_down" in modes.keys() and modes['is_drop_down'] == "true":
            if "drop_down_choices" in modes_param and modes_param["drop_down_choices"] != [] and recommendations == []:
                for item in modes_param["drop_down_choices"]:
                    recommendations.append(item)

    #   OPERATIONS WHEN WHEN FLOW IS ENDED:
        logger.info("is_flow_ended: %s", str(is_flow_ended), extra=log_param)
        logger.info("last_identified_intent_name: %s", str(
            whatsapp_response["response"].get("last_identified_intent_name")), extra=log_param)
        if is_flow_ended:
            # Append Sticky Recommendations and choices
            #  when flow is ended.
            if "last_identified_intent_name" in whatsapp_response["response"] and whatsapp_response["response"]["last_identified_intent_name"] != None and whatsapp_response["response"]["last_identified_intent_name"] not in greeting_intent_names:
                for sticky_choice in sticky_choices:
                    if sticky_choice not in choices and sticky_choice not in recommendations and sticy_choice != whatsapp_response["response"]["last_identified_intent_name"]:
                        choices.append(
                            {"display": sticky_choice, "value": sticky_choice})
                for sticky_recommendation in sticky_recommendations:
                    if sticky_recommendation not in choices and sticky_recommendation not in recommendations and sticky_recommendations != whatsapp_response["response"]["last_identified_intent_name"]:
                        recommendations.append(sticky_recommendation)

    # Go Back Check
        is_go_back_enabled = False
        if "is_go_back_enabled" in whatsapp_response["response"]:
            is_go_back_enabled = whatsapp_response["response"]["is_go_back_enabled"]
            save_data(user, json_data={"is_go_back_enabled": is_go_back_enabled},
                      src="None", channel="WhatsApp", bot_id=BOT_ID, is_cache=True)
            if is_go_back_enabled:
                recommendations.append(go_back_text)

    #   Sending Interactive List for Custom Cards
        if "is_custom_cards" in modes and modes["is_custom_cards"] == "true":
            list_title = list_interactive_options_title
            if "custom_cards_title" in modes_param:
                list_title = modes_param["custom_cards_title"]
            if "custom_cards" in modes_param:
                custom_cards = modes_param["custom_cards"]
                reply_buttons = []
                TEMP_REVERSE_WHATSAPP_MESSAGE_DICT = {}
                for custom_card in custom_cards:
                    choices.append(
                        {"display": custom_card["comment"], "value": custom_card["click"]})
                    TEMP_REVERSE_WHATSAPP_MESSAGE_DICT[custom_card["comment"]
                                                       ] = custom_card["click"]
                    reply_buttons.append(custom_card["comment"])
                total_options_count = len(reply_buttons)
                is_interactive_sent = False
                if total_options_count <= 3 and len(message) < 1024:
                    if check_interative_capability_for_quick_reply(options=reply_buttons, options_type="recommendations"):
                        # check data
                        sendWhatsAppQuickReplyMessage(exotel_apikey, exotel_apitoken, exotel_number, exotel_sid, exotel_subdomain, reply_buttons, MESSAGE_HEADER,
                                                      message, MESSAGE_FOOTER, mobile, "text", None, lang=selected_language)
                        total_options_count = 0
                        is_interactive_sent = True
                if total_options_count > 3 and total_options_count < 11 and len(message) < 1024:
                    if check_interative_capability_for_list(options=reply_buttons, options_type="recommendations"):
                        BUTTON_HEADER = MESSAGE_HEADER
                        BUTTON_FOOTER = MESSAGE_FOOTER
                        if LIST_HEADER_FOOTER_VISIBLE == False:
                            BUTTON_HEADER = " "
                            BUTTON_FOOTER = " "
                        sendWhatsAppInteractiveListMessage(exotel_apikey, exotel_apitoken, exotel_number, exotel_sid, exotel_subdomain, list_title, reply_buttons, BUTTON_HEADER,
                                                           message, BUTTON_FOOTER, mobile, menu_button_text=list_interactive_menu_button_text, extra="None")
                        total_options_count = 0
                        is_interactive_sent = True
                if is_interactive_sent:
                    choices = []
                    recommendations = []
                    message = ""
                    REVERSE_WHATSAPP_MESSAGE_DICT = TEMP_REVERSE_WHATSAPP_MESSAGE_DICT
                    TEMP_REVERSE_WHATSAPP_MESSAGE_DICT = {}

        # >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> [CUSTOM] WhatsAppFlow Integration >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    #   Sending Interactive Flow messages
        # webhook_logger.error("chk is_flow_message: %s",str(modes.get("is_flow_message")), extra=log_param)
        if modes.get("is_flow_message") == "true" and modes_param.get("flow_params"):
            # webhook_logger.error("chk: flow_params%s",str(modes_param.get("flow_params")), extra=log_param)
            flow_params = modes_param["flow_params"]
            #webhook_logger.error("chk flow params: %s",str(flow_params), extra=log_param)
            send_status, custom_log = sendWhatsAppFormMessage(exotel_apikey, exotel_apitoken, exotel_number, exotel_sid, exotel_subdomain, MESSAGE_HEADER, flow_params,
                                                  message, MESSAGE_FOOTER, mobile, lang=selected_language)
#            custom_small_message = f"send_status: {send_status}, flow_params: {flow_params}, custom_log: {custom_log}"
#            send_status = send_whatsapp_text_message(
#                                exotel_apikey, exotel_apitoken, exotel_number, exotel_sid, exotel_subdomain, custom_small_message, mobile, preview_url=False)
            response["status_code"] = 200
            response["status_message"] = "Request processed successfully."
            # webhook_logger.error("chk EXOTELCallBack sendWhatsAppFormMessage: %s", str(response), extra=log_param)
            return response
    # <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<

    #   Sending default Quick reply Buttons and Lists:
        if send_default_quick_reply == False or send_default_list_options == True:
            total_options_count = len(choices) + len(recommendations)
            total_media = len(images) + len(videos)
            TEMP_REVERSE_WHATSAPP_MESSAGE_DICT = {}
            BUTTON_DISPLAY_NAMES = []
            empty_choices = False
            empty_recommendations = False
            logger.error("find you total_options_count: %s",
                         str(total_options_count))
            #   QUICK REPL BUTTONS
            if send_default_quick_reply == False:
                if int(total_options_count) <= 3 and len(message) < 1024:
                    if check_interative_capability_for_quick_reply(options=choices, options_type="choices") and check_interative_capability_for_quick_reply(options=recommendations, options_type="recommendations"):
                        for choice in choices:
                            if choice["display"] not in BUTTON_DISPLAY_NAMES and len(choice["display"]):
                                BUTTON_DISPLAY_NAMES.append(choice["display"])
                                TEMP_REVERSE_WHATSAPP_MESSAGE_DICT[choice["display"]
                                                                   ] = choice["value"]
                            empty_choices = True
                        for recommendation in recommendations:
                            if recommendation not in BUTTON_DISPLAY_NAMES:
                                BUTTON_DISPLAY_NAMES.append(recommendation)
                                TEMP_REVERSE_WHATSAPP_MESSAGE_DICT[recommendation] = recommendation
                            empty_recommendations = True
                    elif check_interative_capability_for_quick_reply(options=choices, options_type="choices") and recommendations == []:
                        for choice in choices:
                            if choice["display"] not in BUTTON_DISPLAY_NAMES and len(choice["display"]):
                                BUTTON_DISPLAY_NAMES.append(choice["display"])
                                TEMP_REVERSE_WHATSAPP_MESSAGE_DICT[choice["display"]
                                                                   ] = choice["value"]
                            empty_choices = True
                    elif check_interative_capability_for_quick_reply(options=recommendations, options_type="recommendations") and choices == []:
                        for recommendation in recommendations:
                            if recommendation not in BUTTON_DISPLAY_NAMES and len(recommendation):
                                BUTTON_DISPLAY_NAMES.append(recommendation)
                                TEMP_REVERSE_WHATSAPP_MESSAGE_DICT[recommendation] = recommendation
                            empty_recommendations = True
                    if BUTTON_DISPLAY_NAMES != []:
                        #   Check for Media:
                        button_media_available = False
                        button_media_type = "text"
                        button_media_link = None
                        if total_media == 1:
                            if len(images) == 1 and isinstance(images[0], str) and check_valid_image_url(images[0]):
                                button_media_type = "image"
                                button_media_link = images[0]
                                button_media_available = True
                            elif len(videos) == 1 and isinstance(videos[0], str) and check_valid_video_url(videos[0]):
                                button_media_type = "video"
                                button_media_link = videos[0]
                                button_media_available = True
                        
                        text_messages = message.split("$$$")
                        if len(text_messages) > 1:
                            for small_message in text_messages[:-1]:
                                if small_message != "":
                                    send_status = send_whatsapp_text_message(
                                exotel_apikey, exotel_apitoken, exotel_number, exotel_sid, exotel_subdomain, small_message, mobile, preview_url=False)
                                time.sleep(0.07)
                        message_body = text_messages[-1]
                        
                        is_send = sendWhatsAppQuickReplyMessage(exotel_apikey, exotel_apitoken, exotel_number, exotel_sid, exotel_subdomain, BUTTON_DISPLAY_NAMES, MESSAGE_HEADER,
                                                                message_body, MESSAGE_FOOTER, mobile, button_media_type, button_media_link, lang=selected_language)
                        if is_send:
                            REVERSE_WHATSAPP_MESSAGE_DICT = TEMP_REVERSE_WHATSAPP_MESSAGE_DICT
                            if empty_choices == True:
                                choices = []
                            if empty_recommendations == True:
                                recommendations = []
                            message = ""

            #   List Interactive Buttons
            if send_default_list_options == True:
                if total_options_count > 3 and total_options_count < 11 and len(message) < 1024:
                    if check_interative_capability_for_list(options=choices, options_type="choices") and check_interative_capability_for_list(options=recommendations, options_type="recommendations"):
                        for choice in choices:
                            if choice["display"] not in BUTTON_DISPLAY_NAMES and len(choice["display"]):
                                BUTTON_DISPLAY_NAMES.append(choice["display"])
                                TEMP_REVERSE_WHATSAPP_MESSAGE_DICT[choice["display"]
                                                                   ] = choice["value"]
                            empty_choices = True
                        for recommendation in recommendations:
                            if recommendation not in BUTTON_DISPLAY_NAMES:
                                BUTTON_DISPLAY_NAMES.append(recommendation)
                                TEMP_REVERSE_WHATSAPP_MESSAGE_DICT[recommendation] = recommendation
                            empty_recommendations = True
                    elif check_interative_capability_for_list(options=choices, options_type="choices") and recommendations == []:
                        for choice in choices:
                            if choice["display"] not in BUTTON_DISPLAY_NAMES and len(choice["display"]):
                                BUTTON_DISPLAY_NAMES.append(choice["display"])
                                TEMP_REVERSE_WHATSAPP_MESSAGE_DICT[choice["display"]
                                                                   ] = choice["value"]
                            empty_choices = True
                    elif check_interative_capability_for_list(options=recommendations, options_type="recommendations") and choices == []:
                        for recommendation in recommendations:
                            if recommendation not in BUTTON_DISPLAY_NAMES and len(recommendation):
                                BUTTON_DISPLAY_NAMES.append(recommendation)
                                TEMP_REVERSE_WHATSAPP_MESSAGE_DICT[recommendation] = recommendation
                            empty_recommendations = True
                    if BUTTON_DISPLAY_NAMES != []:
                        BUTTON_HEADER = MESSAGE_HEADER
                        BUTTON_FOOTER = MESSAGE_FOOTER
                        if LIST_HEADER_FOOTER_VISIBLE == False:
                            BUTTON_HEADER = " "
                            BUTTON_FOOTER = " "
                        
                        text_messages = message.split("$$$")
                        if len(text_messages) > 1:
                            for small_message in text_messages[:-1]:
                                if small_message != "":
                                    send_status = send_whatsapp_text_message(
                                exotel_apikey, exotel_apitoken, exotel_number, exotel_sid, exotel_subdomain, small_message, mobile, preview_url=False)
                                time.sleep(0.07)
                        message_body = text_messages[-1]
                        
                        is_send = sendWhatsAppInteractiveListMessage(exotel_apikey, exotel_apitoken, exotel_number, exotel_sid, exotel_subdomain, list_interactive_options_title, BUTTON_DISPLAY_NAMES, BUTTON_HEADER,
                                                                     message_body, BUTTON_FOOTER, mobile, menu_button_text=list_interactive_menu_button_text, extra="None", lang=selected_language)
                        if is_send:
                            REVERSE_WHATSAPP_MESSAGE_DICT = TEMP_REVERSE_WHATSAPP_MESSAGE_DICT
                            if empty_choices == True:
                                choices = []
                            if empty_recommendations == True:
                                recommendations = []
                            message = ""

    #   CHOICES:
        choice_dict = {}
        choice_display_list = []
        for choice in choices:
            choice_dict[choice["display"]] = choice["value"]
            choice_display_list.append(choice["display"])
        choice_str = ""
        if choice_display_list != []:
            for index in range(len(choice_display_list)):
                if index % max_choices_recommendations_bubble_size == 0 and index != 0:
                    choice_str += "$$$"
                REVERSE_WHATSAPP_MESSAGE_DICT[str(
                    index+1)] = str(choice_dict[choice_display_list[index]])
                choice_str += ask_to_enter_text+" *" + \
                    str(index+1)+"* " + hand_emoji_direction + "  " + \
                    str(choice_display_list[index])+"\n"
                if is_compact_recommendations_choices == False:
                    choice_str = +"\n"
            choice_str = whatsappify_text(choice_str)
            reverse_mapping_index = len(choice_display_list)
        logger.info("Choices: %s", str(choice_str), extra=log_param)

    #   RECOMMENDATIONS:

        recommendation_str = ""
        if recommendations != []:
            cleaned_recommendations = []
            for recm in recommendations:
                if isinstance(recm, dict) and "name" in recm:
                    cleaned_recommendations.append(recm["name"])
                else:
                    cleaned_recommendations.append(recm)
            recommendations = cleaned_recommendations
            if choice_str != "":
                for index in range(len(recommendations)):
                    if index % max_choices_recommendations_bubble_size == 0:
                        recommendation_str += "$$$"
                    REVERSE_WHATSAPP_MESSAGE_DICT[str(
                        reverse_mapping_index+index+1)] = str(recommendations[index])
                    recommendation_str += ask_to_enter_text+" *" + \
                        str(reverse_mapping_index+index+1) + \
                        "* " + hand_emoji_direction + "  " + \
                        str(recommendations[index])+"\n"
                    if is_compact_recommendations_choices == False:
                        recommendation_str = +"\n"
            else:
                for index in range(len(recommendations)):
                    if index % max_choices_recommendations_bubble_size == 0 and index != 0:
                        recommendation_str += "$$$"
                    REVERSE_WHATSAPP_MESSAGE_DICT[str(
                        index+1)] = str(recommendations[index])
                    recommendation_str += ask_to_enter_text+" *" + \
                        str(index+1)+"* " + hand_emoji_direction + "  " + \
                        str(recommendations[index])+"\n"
                    if is_compact_recommendations_choices == False:
                        recommendation_str = +"\n"
            recommendation_str = get_emojized_message(recommendation_str)

        logger.info("Recommendations: %s", str(
            recommendation_str), extra=log_param)
        logger.info("Choices: %s", str(choice_str), extra=log_param)
        logger.info("Reverse Mapper: %s", str(
            REVERSE_WHATSAPP_MESSAGE_DICT), extra=log_param)

    #   RESPONSE MODES:
    #   1.SANDWICH CHOICES: sending choices in between to small texts in a single bubble:
        is_sandwich_choice = False  # is sandwich choice sent flag:
        if "is_sandwich_choice" in modes.keys() and modes['is_sandwich_choice'] == "true":
            choice_position = "1"  # 2nd position
            is_single_message = True
            is_sandwich_choice = True
        else:
            choice_position = ""
            is_single_message = False

    #   2.STICKY CHOICES: sending choices and message in same bubble.
        message_with_choice = False
        if "message_with_choice" in modes.keys() and modes["message_with_choice"] == "true":
            message_with_choice = True
        if recommendation_str == "" and choice_str == "":
            message_with_choice = False

    #   3. BOT LINK CARDS: sending cards containing urls/links
        if "card_for_links" in modes.keys() and modes["card_for_links"] == "true":
            card_text = ""
            for card in cards:
                redirect_url = str(
                    card["link"]) if card["link"] is not None else ""
                title = str(card["title"] if card["title"] is not None else "")
                card_text += " " + hand_emoji_direction + " *"+title+"* \n   "
                card_text += " :link: "+redirect_url+"$$$"
            message += get_emojized_message("$$$" + card_text)
            cards = []

    #   SEND SINGLE BUBBLE TEXT:
        final_text_message = ""
        for count, small_message in enumerate(message.split("$$$"), 0):
            if str(choice_position) != "" and str(choice_position) == str(count):
                # 1. Sandwich choices text:
                if len(choice_str) > 0 and len(recommendation_str) > 0:
                    final_text_message += choice_str + recommendation_str
                    choice_str = ""
                    recommendation_str = ""
                if len(choice_str) > 0:
                    final_text_message += choices_recommendations_header + "\n" + \
                        choice_str + choices_recommendations_footer
                if len(recommendation_str) > 0:
                    final_text_message += choices_recommendations_header + "\n" + \
                        recommendation_str + choices_recommendations_footer
                final_text_message += small_message + "$$$"
            else:
                final_text_message += small_message + "$$$"
        if is_single_message:
            final_text_message = final_text_message.replace("$$$", "")
            if final_text_message != "":
                if "http://" in final_text_message or "https://" in final_text_message:
                    final_text_message = youtube_link_formatter(
                        final_text_message)
                    send_status = send_whatsapp_text_message(
                        exotel_apikey, exotel_apitoken, exotel_number, exotel_sid, exotel_subdomain, final_text_message, str(mobile), preview_url=True)
                    is_sandwich_choice = True
                else:
                    send_status = send_whatsapp_text_message(
                        exotel_apikey, exotel_apitoken, exotel_number, exotel_sid, exotel_subdomain, final_text_message, str(mobile), preview_url=False)
                    is_sandwich_choice = True
                recommendation_str = ""
                choice_str = ""
        else:
            if message_with_choice == True:
                # 2. Sticky choices text:

                final_text_message = message.replace("$$$", "")
                if len(choice_display_list) > 0 and len(recommendations) > 0:
                    final_text_message = final_text_message.strip("\n") + "\n\n" + choices_recommendations_header + "\n" + choice_str.replace(
                        "$$$",  "").strip("\n") + recommendation_str.replace("$$$", "").strip("\n") + choices_recommendations_footer
                    choice_display_list = []
                    recommendations = []
                    logger.info("Sticky choices + recommendations : %s",
                                str(final_text_message), extra=log_param)
                if len(choice_display_list) > 0:
                    final_text_message = final_text_message.strip(
                        "\n") + "\n\n" + choices_recommendations_header + "\n" + choice_str.replace("$$$",  "").strip("\n") + choices_recommendations_footer
                    logger.info("Sticky choices: %s", str(
                        final_text_message), extra=log_param)

                if len(recommendations) > 0:
                    final_text_message = final_text_message.strip(
                        "\n") + "\n\n" + choices_recommendations_header + "\n" + recommendation_str.replace("$$$", "").strip("\n") + choices_recommendations_footer
                    final_text_message = final_text_message.replace(
                        "\n\n\n", "\n")
                    logger.info("Sticky recommendations: %s", str(
                        final_text_message), extra=log_param)

                if len(choice_display_list) > 0:
                    final_text_message = final_text_message + \
                        choice_str.replace("$$$",  "")
                    logger.info("Sticky choices: %s", str(
                        final_text_message), extra=log_param)

                if "http://" in final_text_message or "https://" in final_text_message:
                    final_text_message = youtube_link_formatter(
                        final_text_message)
                    send_status = send_whatsapp_text_message(
                        exotel_apikey, exotel_apitoken, exotel_number, exotel_sid, exotel_subdomain, final_text_message, str(mobile), preview_url=True)
                else:
                    send_status = send_whatsapp_text_message(
                        exotel_apikey, exotel_apitoken, exotel_number, exotel_sid, exotel_subdomain, final_text_message, str(mobile), preview_url=False)
                recommendation_str = ""
                choice_str = ""
            else:
                # 3. Regular single text:
                logger.info("Regular Small Text: %s", str(
                    final_text_message), extra=log_param)
                for small_message in final_text_message.split("$$$"):
                    if small_message != "":
                        if "http://" in small_message or "https://" in small_message:
                            small_message = youtube_link_formatter(
                                small_message)
                            send_status = send_whatsapp_text_message(
                                exotel_apikey, exotel_apitoken, exotel_number, exotel_sid, exotel_subdomain, small_message, str(mobile), preview_url=True)
                        else:
                            send_status = send_whatsapp_text_message(
                                exotel_apikey, exotel_apitoken, exotel_number, exotel_sid, exotel_subdomain, small_message, str(mobile), preview_url=False)
                        time.sleep(0.07)

    #   SENDING CARDS, IMAGES, VIDEOS, PDFS:
        logger.info("Cards: %s", str(cards), extra=log_param)
        logger.info("Images: %s", str(images), extra=log_param)
        logger.info("Videos: %s", str(videos), extra=log_param)
        logger.info("Pdfs: %s", str(pdfs), extra=log_param)

        if len(cards) > 0:
            # Cards with documnet links:  Use 'card_with_document:true' in modes
            if "card_with_document" in modes.keys() and modes["card_with_document"] == "true":
                logger.info("Inside Cards with documents", extra=log_param)
                for card in cards:
                    doc_caption = str(card["title"])
                    doc_url = str(card["link"])
                    logger.info("DOCUMENT NAME: %s", str(
                        doc_caption), extra=log_param)
                    logger.info("DOCUMENT URL: %s", str(
                        doc_url), extra=log_param)
                    try:
                        send_status = sendWhatsAppMediaMessage(
                            exotel_apikey, exotel_apitoken, exotel_number, exotel_sid, exotel_subdomain, "document", str(doc_url), str(mobile), caption=None)
                        logger.info("Is Card sent: %s", str(
                            send_status), extra=log_param)
                    except Exception as E:
                        logger.error("Cannot send card with document: %s", str(
                            E), extra=log_param)
            else:
                # Cards with text, link or images
                card_str = ""
                for index, card in enumerate(cards):
                    logger.info("Inside Regular Card", extra=log_param)
                    title = str(card["title"])
                    content = str(
                        "\n" + card["content"] + "\n") if card["content"] != "" else ""
                    image_url = str(card["img_url"])
                    redirect_url = youtube_link_formatter(str(card["link"]))
                    caption = "*" + title + "* " + content + " " + redirect_url
                    if image_url != "":
                        logger.info("Card Image available", extra=log_param)
                        if "https:" in caption and "/?" in caption:
                            send_status = sendWhatsAppMediaMessage(
                                exotel_apikey, exotel_apitoken, exotel_number, exotel_sid, exotel_subdomain, "image", str(image_url), str(mobile), caption=caption)
                            logger.info("Is Card with image sent: %s", str(
                                send_status), extra=log_param)
                            if send_status == False:
                                send_status = sendWhatsAppMediaMessage(
                                    exotel_apikey, exotel_apitoken, exotel_number, exotel_sid, exotel_subdomain, 'image', str(image_url), mobile, caption=None)
                                logger.info("Is Card with image sent: %s", str(
                                    send_status), extra=log_param)
                                send_status = send_whatsapp_text_message(exotel_apikey, exotel_apitoken, exotel_number, exotel_sid, exotel_subdomain, str(
                                    get_emojized_message(caption)), mobile, preview_url=True)
                                logger.info("Is Card with image 's caption sent: %s", str(
                                    send_status), extra=log_param)
                        else:
                            send_status = sendWhatsAppMediaMessage(
                                exotel_apikey, exotel_apitoken, exotel_number, exotel_sid, exotel_subdomain, 'image', str(image_url), mobile, caption=caption)
                            logger.info("Is Card with image sent: %s", str(
                                send_status), extra=log_param)
                    else:
                        if index % max_cards_bubble_size == 0:
                            card_str += "$$$"
                        card_str += caption + "\n\n"
                        logger.info("Is Card with link sent: %s",
                                    str(send_status), extra=log_param)
                if card_str != "":
                    time.sleep(0.05)
                    for card_bubble in card_str.split("$$$"):
                        if card_bubble.strip() == "":
                            continue
                        send_status = send_whatsapp_text_message(exotel_apikey, exotel_apitoken, exotel_number, exotel_sid, exotel_subdomain, str(
                            get_emojized_message(card_bubble)), str(mobile), preview_url=True)

        if len(videos) > 0:
            logger.info("== Inside Videos ==", extra=log_param)
            for i in range(len(videos)):
                logger.info("== Inside Videos ==", extra=log_param)
                if isinstance(videos[i], dict) and 'video_link' in str(videos[i]):
                    video_url = str(videos[i]['video_link'])
                    video_caption = None
                    if 'content' in videos[i] and videos[i]["content"] != "":
                        logger.info("== Video with caption ==",
                                    extra=log_param)
                        video_caption = videos[i]["content"]
                    if check_valid_video_url(video_url):
                        send_status = sendWhatsAppMediaMessage(exotel_apikey, exotel_apitoken, exotel_number, exotel_sid, exotel_subdomain, 'video', str(
                            video_url), mobile, caption=video_caption)
                    else:
                        video_url = youtube_link_formatter(video_url)
                        video_link_with_caption = video_caption + "\n\n" + \
                            video_url if video_caption != None else video_url
                        send_status = send_whatsapp_text_message(
                            exotel_apikey, exotel_apitoken, exotel_number, exotel_sid, exotel_subdomain, video_link_with_caption, mobile, preview_url=True)
                    logger.info("Is Video sent: %s", str(
                        send_status), extra=log_param)
                else:
                    video_url = youtube_link_formatter(str(videos[i]))
                    send_status = send_whatsapp_text_message(
                        exotel_apikey, exotel_apitoken, exotel_number, exotel_sid, exotel_subdomain, video_url, str(mobile), preview_url=True)
                    logger.info("Is Video sent: %s", str(
                        send_status), extra=log_param)

        if len(images) > 0:
            logger.info("== Inside Images ==", extra=log_param)
            for i in range(len(images)):
                if isinstance(images[i], dict) and 'img_url' in images[i]:
                    image_url = images[i]["img_url"]
                    image_caption = None
                    if 'content' in images[i] and images[i]["content"] != "":
                        logger.info("== Image with caption ==",
                                    extra=log_param)
                        image_caption = images[i]["content"]
                    send_status = sendWhatsAppMediaMessage(exotel_apikey, exotel_apitoken, exotel_number, exotel_sid, exotel_subdomain, 'image', str(
                        image_url), mobile, caption=image_caption)
                    logger.info("Is Image sent: %s", str(
                        send_status), extra=log_param)
                else:
                    logger.info("== Image without caption ==")
                    send_status = sendWhatsAppMediaMessage(
                        exotel_apikey, exotel_apitoken, exotel_number, exotel_sid, exotel_subdomain, 'image', str(images[i]), mobile, caption=None)
                    logger.info("Is Image sent: %s", str(
                        send_status), extra=log_param)
        
        if len(pdfs) > 0:
            logger.info("== Inside PDFs ==", extra=log_param)
            for pdf in pdfs:
                pdf_name = str(pdf["pdf_name"])
                pdf_url = str(pdf["pdf_url"])
                logger.info("PDF NAME: %s", str(
                    pdf_name), extra=log_param)
                logger.info("PDF URL: %s", str(
                    pdf_url), extra=log_param)
                try:
                    send_status = sendWhatsAppMediaMessage(
                        exotel_apikey, exotel_apitoken, exotel_number, exotel_sid, exotel_subdomain, "document", str(pdf_url), str(mobile), caption=None)
                    logger.info("Is PDF sent: %s", str(
                        send_status), extra=log_param)
                    time.sleep(0.4)
                except Exception as E:
                    logger.error("Cannot send pdfs : %s", str(
                        E), extra=log_param)

    #   SENDING CHOICES AND RECOMMENDATIONS BOTH:
        if len(choice_str) > 0 and len(recommendation_str) > 0:
            mixed_choice = choice_str+""+recommendation_str
            time.sleep(0.05)
            send_status = send_whatsapp_text_message(exotel_apikey, exotel_apitoken, exotel_number, exotel_sid, exotel_subdomain, mixed_choice.replace(
                "\n\n\n", "").replace("$$$", ""), str(mobile), preview_url=False)
            logger.info("Is Mixed Choices sent: %s",
                        str(send_status), extra=log_param)
            choice_str = ""
            recommendation_str = ""

    #   SENDING CHOICES:
        if len(choice_str) > 0:
            choice_str = choices_recommendations_header + "\n" + \
                choice_str + choices_recommendations_footer
            if "$$$" in choice_str:
                for bubble in choice_str.split("$$$"):
                    if bubble.strip() == "":
                        continue
                    time.sleep(0.07)
                    send_status = send_whatsapp_text_message(
                        exotel_apikey, exotel_apitoken, exotel_number, exotel_sid, exotel_subdomain, bubble, str(mobile), preview_url=False)
                logger.info("Is choices sent: %s", str(
                    send_status), extra=log_param)
            else:
                time.sleep(0.07)
                send_status = send_whatsapp_text_message(
                    exotel_apikey, exotel_apitoken, exotel_number, exotel_sid, exotel_subdomain, choice_str, str(mobile), preview_url=False)
                logger.info("Is choices sent: %s", str(
                    send_status), extra=log_param)

    #   SENDING RECOMMENDATIONS:
        if len(recommendation_str) > 0:
            recommendation_str = choices_recommendations_header + "\n" + \
                recommendation_str + choices_recommendations_footer
            if "$$$" in recommendation_str:
                for bubble in recommendation_str.split("$$$"):
                    if bubble.strip() == "":
                        continue
                    time.sleep(0.05)
                    send_status = send_whatsapp_text_message(
                        exotel_apikey, exotel_apitoken, exotel_number, exotel_sid, exotel_subdomain, bubble, str(mobile), preview_url=False)
                    logger.info("Is recommendations sent: %s",
                                str(send_status), extra=log_param)
            else:
                time.sleep(0.05)
                send_status = send_whatsapp_text_message(
                    exotel_apikey, exotel_apitoken, exotel_number, exotel_sid, exotel_subdomain, recommendation_str, str(mobile), preview_url=False)
                logger.info("Is recommendations sent: %s",
                            str(send_status), extra=log_param)

        if "is_catalogue_added" in modes and modes["is_catalogue_added"] == "true":
            catalogue_obj = WhatsappCatalogueDetails.objects.filter(bot=Bot.objects.get(
                pk=BOT_ID, is_deleted=False), is_catalogue_enabled=True).first()
            if catalogue_obj:
                if "selected_catalogue_sections" in modes_param:
                    catalogue_sections = modes_param["selected_catalogue_sections"]
                    if not catalogue_sections:
                        catalogue_sections = None
                else:
                    catalogue_sections = None
                catalogue_metadata = json.loads(
                    catalogue_obj.catalogue_metadata)
                send_status = send_whatsapp_catalog(
                    user, exotel_apikey, exotel_apitoken, exotel_number, exotel_sid, exotel_subdomain, str(mobile), catalogue_metadata, BOT_ID, catalogue_sections, "individual")
                logger.info("Is Catalogue sent: %s",
                            str(send_status), extra=log_param)

    #   CHECK IF LANGUAGE RESPONSE REQUIRED
        if change_language_response_required(user_id, BOT_ID, bot_obj, is_whatsapp_welcome_response):
            language_str, REVERSE_WHATSAPP_MESSAGE_DICT = get_language_change_response(
                str(user_id), BOT_ID, REVERSE_WHATSAPP_MESSAGE_DICT)
            logger.info("change_language_response_required: " +
                        str(language_str), extra=log_param)
            logger.info("change_language_response_required: " +
                        str(REVERSE_WHATSAPP_MESSAGE_DICT), extra=log_param)
            if language_str != "":
                language_str = get_emojized_message(language_str)
                send_status = send_whatsapp_text_message(
                    exotel_apikey, exotel_apitoken, exotel_number, exotel_sid, exotel_subdomain, language_str, str(mobile), preview_url=False)
                logger.info("Is change language response sent: %s",
                            str(send_status), extra=log_param)
                save_data(user, json_data={"CHANGE_LANGUAGE_TRIGGERED": True},
                          src="None", channel="WhatsApp", bot_id=BOT_ID, is_cache=True)

    #   SENDING Helpful_Unhelpful_Choices:
        if is_feedback_required:
            helpful = helpful_intent_name
            unhelpful = unhelpful_intent_name

            # get_emojized_message("Enter :thumbs_up: for "+helpful+"\n\nEnter :thumbs_down: for "+unhelpful)
            feedback_str = feedback_question
            feedback_buttons = [feedback_option_yes, feedback_option_no]
            time.sleep(1)
            is_send = sendWhatsAppQuickReplyMessage(
                exotel_apikey, exotel_apitoken, exotel_number, exotel_sid, exotel_subdomain, feedback_buttons, MESSAGE_HEADER, feedback_str, MESSAGE_FOOTER, mobile, lang=selected_language)
            if is_send:
                REVERSE_WHATSAPP_MESSAGE_DICT[feedback_option_yes] = helpful
                REVERSE_WHATSAPP_MESSAGE_DICT[feedback_option_no] = unhelpful
                feedback_dict = {"is_intent_feedback_asked": True}
                save_data(user, json_data=feedback_dict,  src="None",
                          channel="WhatsApp", bot_id=BOT_ID,  is_cache=True)

    #   SENDING WARNING IN CASE OF WELCOME MESSAGE
        if is_whatsapp_welcome_response and "whatsapp_spam_response" in whatsapp_response:
            send_status = send_whatsapp_text_message(
                exotel_apikey, exotel_apitoken, exotel_number, exotel_sid, exotel_subdomain,
                whatsapp_response["whatsapp_spam_response"]["response"]["text_response"]["text"],
                str(mobile), preview_url=False)
            logger.info("Warning message sent: %s",
                        str(send_status), extra=log_param)

        logger.info("REVERSE_WHATSAPP_MESSAGE_DICT: %s", str(
            REVERSE_WHATSAPP_MESSAGE_DICT), extra=log_param)
        save_data(default_user_obj, json_data={"REVERSE_WHATSAPP_MESSAGE_DICT": REVERSE_WHATSAPP_MESSAGE_DICT},
                  src="None", channel="WhatsApp", bot_id=DEFAULT_BOT_ID,  is_cache=True)

        response["status_code"] = 200
        response["status_message"] = "Request processed successfully."
        logger.info("EXOTELCallBack: %s", str(response), extra=log_param)
        return response

    except Exception as E:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        response["status_message"] = str(E) + str(exc_tb.tb_lineno)
        logger.error("ExotalCallBack: %s at %s", str(
            E), str(exc_tb.tb_lineno), extra=log_param)
        return response


def check_for_whatsapp_catalogue_message_exotel(request_packet, message, message_type, user_obj, bot_obj):
    try:
        is_merge_cart_triggered = is_merge_cart_message_triggered(
            user_obj, bot_obj)
        if is_merge_cart_triggered and message_type == "interactive":
            button_id = request_packet["whatsapp"]["messages"][0]["content"]["interactive"]["button_reply"]["id"]
            if button_id == "merge_cart":
                merge_cart_message = "Merge Cart"
                user_language = user_obj.selected_language
                user_language = user_language.lang if user_language else "en"
                if user_language != "en":
                    merge_cart_message = get_translated_text(
                        merge_cart_message, user_language, EasyChatTranslationCache)
                cart_merged, cart_total, cart_items = merge_whatsapp_catalogue_cart(
                    user_obj, bot_obj)
                if cart_merged:
                    text_message = "Okay, I have merged your cart successfully 👍.\n*The total value of your cart is " + \
                        str(cart_total) + "*"
                    return True, text_message, cart_items, merge_cart_message
            if button_id == "continue_cart":
                continue_cart_message = "Continue"
                user_language = user_obj.selected_language
                user_language = user_language.lang if user_language else "en"
                if user_language != "en":
                    continue_cart_message = get_translated_text(
                        continue_cart_message, user_language, EasyChatTranslationCache)
                cart_updated, cart_total, cart_items = update_whatsapp_catalogue_cart(
                    user_obj, bot_obj)
                if cart_updated:
                    text_message = "Okay, I have updated your cart successfully 👍.\n*The total value of your cart is " + \
                        str(cart_total) + "*"
                    return True, text_message, cart_items, continue_cart_message
        if is_merge_cart_triggered and message_type == "text":
            original_message = message
            message = translate_given_text_to_english(message).strip().lower()
            if message == "merge cart":
                cart_merged, cart_total, cart_items = merge_whatsapp_catalogue_cart(
                    user_obj, bot_obj)
                if cart_merged:
                    text_message = "Okay, I have merged your cart successfully 👍.\n*The total value of your cart is " + \
                        str(cart_total) + "*"
                    return True, text_message, cart_items, original_message
            if message == "continue":
                cart_merged, cart_total, cart_items = update_whatsapp_catalogue_cart(
                    user_obj, bot_obj)
                if cart_merged:
                    text_message = "Okay, I have updated your cart successfully 👍.\n*The total value of your cart is " + \
                        str(cart_total) + "*"
                    return True, text_message, cart_items, original_message
    except Exception as E:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        logger.error("check_for_whatsapp_catalogue_message_exotel %s at %s", str(
            E), str(exc_tb.tb_lineno), extra=log_param)

    return False, "", "", ""
