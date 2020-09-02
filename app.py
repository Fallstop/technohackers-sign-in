from flask import *
import time
import datetime
import pickle
import os.path

from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

import pymysql

import config

listOfNames = []
app = Flask(__name__, template_folder='HtmlPages/')
app.config['DEBUG'] = True
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

@app.route('/', methods=['GET'])
def home():
    return render_template("home.html")

@app.route('/getnames', methods=['GET'])
def getNames():
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
    attendedToday =  False if formData["Force"] else check_attendance(personName)
    if attendedToday != False:
        print("Person allready attended")
        return (jsonify(attendedToday),200)
    attendanceId = sql_insert_attendance(formData["Name"],formData["SignedUp"])
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
        for name in result: parsed.append(name[0])
    except Exception:
        print("Failed to get google sheet, trying again in 5 seconds")
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
        for name in result: parsed.append(name[0])
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
