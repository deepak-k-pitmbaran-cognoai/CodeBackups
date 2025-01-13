republic_day_time = "24-08"
        today = datetime.now().strftime("%d-%m")
        response['today'] = today
        logger.error('Hi apitree : today and republic day %s ------------%s-' , str(today),str(republic_day_time), extra={'AppName': 'EasyChat', 'user_id': 'None', 'source': 'None', 'channel': 'None', 'bot_id': 'None'})
        rec = ['Continue', 'Select Language']
        
        dussera = ["23-10","24-10"]
        dhanteras = ["09-11"]
        diwali = ["06-11"]
        christmas = ["23-12", "24-12", "25-12"]
        newyear = ["28-12","29-12","30-12","31-12","01-01"]
        republic_day = ["23-01","24-01","25-01","26-01"]
        easter = ["06-04", "07-04", "08-04"]
#        eid = ["08-05", "09-05", "10-05", "11-05", "12-05", "13-05", "14-05", "15-05", "16-05", "17-05", "18-05", "19-05", "20-05" , "21-05", "22-05", "23-05", "24-05", "25-05", "26-05", "27-05", "28-05", "29-05", "30-05", "31-05", "12-06", "15-06", "16-06", "17-06", "18-06", "19-06", "20-06", "21-06", "22-06", "23-06", "24-06", "25-06"]
        eid = ["10-04"]
        holi = ["23-03"]
        
        independance_day = ["09-08", "10-08", "11-08", "12-08", "13-08", "14-08", "15-08"]
        response['print_today'] = today
        if today in dussera:
            response['images'] = ["https://ltfs-uat.allincall.in/files/1f05b0e1-7c80-4cdc-8011-81ba7a47c10e_compressed.png"]
            
        elif today in diwali:
            response['images'] = ["https://ltfs-uat.allincall.in/files/47c2517a-f88b-4b2e-a45d-d07a4e59b06c_compressed.jpg"]
        
        elif today in dhanteras:
            response['images'] = ["https://ltfs-uat.allincall.in/files/EasyChatApp/LTF_Dhanteras_R2.jpg"]
            
        elif today in christmas:
            response['images'] = ["https://ltfs-uat.allincall.in/files/75391eaa-374a-44cd-a112-4e9a9b08be41_compressed.jpeg"]
            
        elif today in newyear:
            response['images'] = ["https://static.allincall.in/app.getcogno.ai/1530/8w4Y0g6Ezy_NewyearChatBot.jpeg"]
            
        elif today in republic_day:
            response['images'] = ["https://static.allincall.in/app.getcogno.ai/3245/DHfXrirfV2_75thRepublicDay.jpeg"]
        
        elif today in easter:
            #response['images'] = ["https://ltfs-uat.allincall.in/files/easterweb.jpg"]
            response['images'] = ["https://ltfs-uat.allincall.in/files/easterwhatsapp.jpg"]
        
        elif today in eid:
            response['images'] = ["https://ltfs-uat.allincall.in/files/LTFS-Eid.jpg"]
        elif today in independance_day:
            response['images'] = ["https://ltfs-uat.allincall.in/files/independance_day_2024.jpg"]
        elif today in holi:
            response['images'] = ["https://ltfs-uat.allincall.in/files/LTFS_Holi_Re.jpg"]