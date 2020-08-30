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
    if post_attendance(formData["Name"],formData["SignedUp"]):
        return ("",200)
    else:
        return ("",400)


def post_attendance(full_name,registered):
    global connection
    connection.ping(reconnect=True)
    cursor = connection.cursor(cursor=pymysql.cursors.DictCursor)
    query = "insert into qrl_membership_db.attendance_record (full_name, registered) values (%s,%s);"
    try:
        cursor.execute(query, (full_name, registered))
        connection.commit()
        return True
    except Exception as e:
        print("Attendance Insert failed, Error:", e)
        return False

def downloadNames():
    parsed = []
    try:
        #############
        #SETUP
        #############
        SCOPES = config.nameListSheet.scopes
        SPREADSHEET_ID = config.nameListSheet.spreadsheet_id

        RangeName = config.nameListSheet.range_name
        creds = None

        # The file token.pickle stores the user's access and refresh tokens, and is
        # created automatically when the authorization flow completes for the first
        # time.
        if os.path.exists(config.nameListSheet.pickle_name):
            with open(config.nameListSheet.pickle_name, 'rb') as token:
                creds = pickle.load(token)
        # If there are no (valid) credentials available, let the user log in.
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    config.nameListSheet.credentials_name, SCOPES)
                creds = flow.run_local_server(port=0)
            # Save the credentials for the next run
            with open(config.nameListSheet.pickle_name, 'wb') as token:
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
        downloadNames()
    return parsed



print("Getting names from the Google Sheet")
listOfNames = downloadNames()
