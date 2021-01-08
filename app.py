from flask import *

import time
import datetime
import pickle
import os.path
import jsonschema
import random
import uuid


from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

import pymysql

import config

listOfNames = []
app = Flask(__name__, template_folder='HtmlPages/')
# app.config['DEBUG'] = True
app.config['TEMPLATES_AUTO_RELOAD'] = True

# Connection info for database
connection = pymysql.connect(
    host=config.sqlServer.host,
    user=config.sqlServer.user,
    password=config.sqlServer.password,
    port=config.sqlServer.port,
    database=config.sqlServer.database,
    client_flag= pymysql.constants.CLIENT.MULTI_STATEMENTS,
)

def validateJson(jsonSting,Schema):
    jsonData = jsonSting
    try:
        jsonschema.validate(instance=jsonData, schema=Schema)
    except jsonschema.exceptions.ValidationError as err:
        return False
    return jsonData

def generateAccessToken(): return str(uuid.uuid4())

@app.route('/', methods=['GET'])
def home():
    return render_template("home.html")

@app.route('/getnames', methods=['GET'])
def getNames():
    # print("Getting names from the Google Sheet")
    # print("Downloading youth names...")
    # listOfNames = downloadYouthNames()
    # print("Downloading facilitator names...")
    # listOfNames += downloadFacilitatorsNames()
    # print("Name retrival complete.")
    return jsonify(listOfNames)

@app.route('/signin',methods=['POST'])
def signIn():
    print("Data: ",request.json)
    formData = json.loads(request.data)
    personName = formData["Name"]
    signedUp = formData["SignedUp"]

    #Backup sign in to csv
    if (os.path.exists(config.backupCSV.fileName)):
        backUpCSVFile = open(config.backupCSV.fileName,'a')
    else:
        backUpCSVFile = open(config.backupCSV.fileName,'w')
    backUpCSVFile.write("\n"+formData["Name"]+","+str(formData["SignedUp"])+","+datetime.datetime.now().isoformat())
    backUpCSVFile.close()
    print("Form values:",(personName,signedUp,datetime.datetime.now().isoformat()))
    # attendedToday =  False if formData["Force"] else check_attendance(personName)
    # if attendedToday != False:
    #     print("Person allready attended")
    #     return (jsonify(attendedToday),200)
    # attendanceId = sql_insert_attendance(formData["Name"],formData["SignedUp"])
    attendanceId = 3
    if attendanceId != False:
        return (jsonify(attendanceId),200)
    else:
        return ("",400)

@app.route('/deleteattendance', methods=['DELETE'])
def undo_attendance():
    print("Data: ",request.json)
    formData = json.loads(request.data)
    attendanceId = formData["id"]
    if (sql_delete_attendance(attendanceId)):
        return ("",200)
    else:
        return ("",400)

@app.route('/argolia/create-account',methods=['POST'])
def argolia_create_account():
    accountInfo = validateJson(
        request.get_json(),
        {
            "username": {
                "type":"string",
                "minLength": 3,
                "maxLength": 16
                },
            "full_name": {
                "type":"string"
                },
            "required": ["username","full_name"]
        }   
    )
    if accountInfo:
        pin = str(random.randrange(0,999999)).zfill(6) 
        access_token = generateAccessToken()
        return sql_argolia_create_account(accountInfo["full_name"],accountInfo["username"],pin,access_token)
    else:
        print("Invalid Json {}".format(request.get_json()))
        return ("Invalid Json {}".format(request.get_json()),400)

@app.route('/argolia/check-username',methods=['POST'])
def argolia_check_username():
    username = validateJson(
        request.get_json(),
        {
            "username": {"type":"string"},
            "required": ["username"]
        }   
    )
    if username:
        return sql_argolia_check_username(username["username"])
    else:
        return ("Invalid Json {}".format(request.data),400)

@app.route('/argolia/update-token',methods=['POST'])
def argolia_update_token():
    data = validateJson(
        request.get_json(),
        {
            "old-token": {"type":"string"},
            "account-id":  {"type":"string"},
            "required": ["old-token","account-id"]
        }   
    )
    if data:
        return sql_argolia_update_token(data["old-token"],data["account-id"])
    else:
        return ("Invalid Json {}".format(request.data),400)

@app.route('/argolia/sign-in',methods=['POST'])
def argolia_sign_in():
    creds = validateJson(
        request.get_json(),
        {
            "username": {"type":"string"},
            "pin": {"type":"string"},
        }   
    )
    if creds:
        return sql_argolia_sign_in(creds["username"],creds["pin"])
    else:
        return ("Invalid Json {}".format(request.data),400)

@app.route('/argolia/validate-access-token',methods=['POST'])
def argolia_validate_access_token():
    creds = validateJson(
        request.get_json(),
        {
            "token": {"type":"string"},
            "account-id":  {"type":"string"},
            "required": ["old-token","account-id"]
        }   
    )
    if creds:
        return sql_argolia_validate_access_token(creds["token"],creds["account-id"])
    else:
        return ("Invalid Json {}".format(request.data),400)


def sql_delete_attendance(id):
    global connection
    connection.ping(reconnect=True)
    cursor = connection.cursor(cursor=pymysql.cursors.DictCursor)
    query = "Delete from attendance_record where attendance_id = (%s);"
    try:
        cursor.execute(query, (id))
        connection.commit()
        return True
    except Exception as e:
        print("Attendance delete failed, Error:", e)
        return False

def sql_insert_attendance(full_name,registered):
    global connection
    connection.ping(reconnect=True)
    cursor = connection.cursor(cursor=pymysql.cursors.DictCursor)
    query = "insert into qrl_membership_db.attendance_record (full_name, registered) values (%s,%s)"
    
    try:
        cursor.execute(query, (full_name, registered))
        connection.commit()
        id = cursor.lastrowid
        print("Attendance:",id)
        return {
            "id": id,
            "attendance_warning": False
            }
    except Exception as e:
        print("Attendance Insert failed, Error:", e)
        return False

def sql_argolia_create_account(full_name,username,pin,access_token):
    global connection
    connection.ping(reconnect=True)
    cursor = connection.cursor(cursor=pymysql.cursors.DictCursor)
    query = "insert into qrl_membership_db.argolia_accounts (account_id, full_name, minecraft_username, minecraft_pin, access_token) values (%s,%s,%s,%s,%s)"
    
    try:
        cursor.execute(query, (get_uuid(username),full_name, username, pin, access_token))
        connection.commit()
        id = cursor.lastrowid
        print("Account ID:",id)
        return (
            json.dumps({"pin":pin}),
            200
        )
    except Exception as e:
        print("Account Insert failed, Error:", e)
        return ("Failed to create account",500)

def sql_argolia_sign_in(username, pin):
    global connection
    connection.ping(reconnect=True)
    cursor = connection.cursor(cursor=pymysql.cursors.DictCursor)
    query = "select access_token,account_id from argolia_accounts where minecraft_username=%s and minecraft_pin=%s"
    
    try:
        cursor.execute(query, (username,pin,))
        result = cursor.fetchone()
        print("Check attendance result:",result)
        if result is not None:
            return sql_argolia_update_token(result)
    except Exception as e:
        print("Attendance Insert failed, Error:", e)
        return False

def sql_argolia_update_token(old_token, account_id):
    global connection
    connection.ping(reconnect=True)
    cursor = connection.cursor(cursor=pymysql.cursors.DictCursor)
    query = "update argolia_accounts set access_token=%s where account_id=%s and access_token=%s;"
    
    try:
        cursor.execute(query, (generateAccessToken(),account_id,old_token))
        connection.commit()
        if cursor.rowcount > 0:
            return (json.dumps({"token":cursor.fetchone(),"account_id":account_id,"success": True}),200)
        else:
            return (json.dumps({"success": False}),200)
            
    except Exception as e:
        print("sql_argolia_update_token failed, Error:", e)
        return (json.dumps({"success": False}),200)

def sql_argolia_check_username(username):
    global connection
    connection.ping(reconnect=True)
    cursor = connection.cursor()
    query = "SELECT COUNT(minecraft_username) FROM argolia_accounts WHERE minecraft_username=%s;"
    
    try:
        cursor.execute(query, (username,))
        data = cursor.fetchone()[0]
        return (json.dumps({"available":data==0,"success": True}),200)
            
    except Exception as e:
        print("sql_argolia_check_username failed, Error:", e)
        return (json.dumps({"success": False}),200)

def sql_argolia_validate_access_token(account_id, access_token):
    global connection
    connection.ping(reconnect=True)
    cursor = connection.cursor(cursor=pymysql.cursors.DictCursor)
    query = "select access_token,account_id from argolia_accounts where account_id=%s and access_token=%s"
    
    try:
        cursor.execute(query, (account_id,access_token,))
        result = cursor.fetchone()
        print("Check attendance result:",result)
        if result is not None:
            return sql_argolia_update_token(result)
    except Exception as e:
        print("Attendance Insert failed, Error:", e)
        return False

def check_attendance(full_name):
    global connection
    connection.ping(reconnect=True)
    cursor = connection.cursor(cursor=pymysql.cursors.DictCursor)
    query = "select * from attendance_record where arrival_time >= DATE_ADD(CURDATE(), INTERVAL -1 DAY) and full_name = %s order by arrival_time DESC;"
    
    try:
        cursor.execute(query, (full_name))
        result = cursor.fetchone()
        print("Check attendance result:",result)
        if result is not None:
            seconds_since_midnight = (datetime.datetime.now() - datetime.datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)).total_seconds()
            seconds_since_midnight_arrival = (result["arrival_time"] - result["arrival_time"].replace(hour=0, minute=0, second=0, microsecond=0)).total_seconds()
            if seconds_since_midnight < seconds_since_midnight_arrival:
                # Impossible situation, stops the un-needed warnings here
                return False
            return {
                "id": result["attendance_id"],
                "full_name": result["full_name"],
                "previous_time": result["arrival_time"].strftime("%I:%M %p"),
                "attendance_warning": True
            }
        else:
            return False
    except Exception as e:
        print("Attendance Insert failed, Error:", e)
        return False

def get_uuid(username):
        """
          Get the UUID of the player.
          Parameters
          ----------
          username : Minecraft username
        """

        http_conn = http.client.HTTPSConnection("api.mojang.com");
        http_conn.request("GET", "/users/profiles/minecraft/" + username,
            headers={'User-Agent':'Minecraft Username -> UUID', 'Content-Type':'application/json'});
        response = http_conn.getresponse().read().decode("utf-8")

        if (not response): # No response & no timestamp
            return uuid.uuid4()

        json_data = json.loads(response)
        try:
            playerUuid = json_data['id']
        except KeyError as e:
            print("KeyError raised:", e)
            playerUuid = uuid.uuid4()

        return playerUuid

def downloadYouthNames():
    parsed = []
    try:
        #############
        #SETUP
        #############
        SCOPES = config.youthNameSheet.scopes
        SPREADSHEET_ID = config.youthNameSheet.spreadsheet_id

        RangeName = config.youthNameSheet.range_name
        creds = None

        # The file token.pickle stores the user's access and refresh tokens, and is
        # created automatically when the authorization flow completes for the first
        # time.
        if os.path.exists(config.youthNameSheet.pickle_name):
            with open(config.youthNameSheet.pickle_name, 'rb') as token:
                creds = pickle.load(token)
        # If there are no (valid) credentials available, let the user log in.
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    config.youthNameSheet.credentials_name, SCOPES)
                creds = flow.run_local_server(port=0)
            # Save the credentials for the next run
            with open(config.youthNameSheet.pickle_name, 'wb') as token:
                pickle.dump(creds, token)
        service = build('sheets', 'v4', credentials=creds)
        # Call the Sheets API
        sheet = service.spreadsheets()
        result = sheet.values().get(spreadsheetId=SPREADSHEET_ID,range=RangeName).execute()["values"]
        parsed = []
        print(result)
        for name in result: 
            if len(name) > 0: 
                parsed.append(name[0])
    except Exception as e:
        print("Failed to get google sheet, trying again in 5 seconds, error:",e)
        time.sleep(5)
        downloadYouthNames()
    return parsed

def downloadFacilitatorsNames():
    parsed = []
    try:
        #############
        #SETUP
        #############
        SCOPES = config.facilitatorsNameSheet.scopes
        SPREADSHEET_ID = config.facilitatorsNameSheet.spreadsheet_id

        RangeName = config.facilitatorsNameSheet.range_name
        creds = None

        # The file token.pickle stores the user's access and refresh tokens, and is
        # created automatically when the authorization flow completes for the first
        # time.
        if os.path.exists(config.facilitatorsNameSheet.pickle_name):
            with open(config.facilitatorsNameSheet.pickle_name, 'rb') as token:
                creds = pickle.load(token)
        # If there are no (valid) credentials available, let the user log in.
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    config.facilitatorsNameSheet.credentials_name, SCOPES)
                creds = flow.run_local_server(port=0)
            # Save the credentials for the next run
            with open(config.facilitatorsNameSheet.pickle_name, 'wb') as token:
                pickle.dump(creds, token)
        service = build('sheets', 'v4', credentials=creds)
        # Call the Sheets API
        sheet = service.spreadsheets()
        result = sheet.values().get(spreadsheetId=SPREADSHEET_ID,range=RangeName).execute()["values"]
        parsed = []
        for name in result: 
            if len(name) > 0: 
                parsed.append(name[0])
    except Exception:
        print("Failed to get google sheet, trying again in 5 seconds")
        time.sleep(5)
        downloadFacilitatorsNames()
    return parsed

print("Getting names from the Google Sheet")
print("Downloading youth names...")
listOfNames = downloadYouthNames()
print("Downloading facilitator names...")
listOfNames += downloadFacilitatorsNames()
print("Name retrival complete.")

if __name__ == "__main__":
    app.run(port=5000)
