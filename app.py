from flask import *
import time
import pickle
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

import config

listOfNames = []
app = Flask(__name__, template_folder='HtmlPages/')
app.config['DEBUG'] = True
app.config['TEMPLATES_AUTO_RELOAD'] = True

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
    print("Form values:",(personName,signedUp))
    return ("",200)

def downloadNames():
    parsed = []
    try:
        #############
        #SETUP
        #############
        SCOPES = config.nameListSheet.SCOPES
        SPREADSHEET_ID = config.nameListSheet.SPREADSHEET_ID

        RangeName = config.nameListSheet.RANGE_NAME
        creds = None

        # The file token.pickle stores the user's access and refresh tokens, and is
        # created automatically when the authorization flow completes for the first
        # time.
        if os.path.exists(config.nameListSheet.PICKLE_NAME):
            with open(config.nameListSheet.PICKLE_NAME, 'rb') as token:
                creds = pickle.load(token)
        # If there are no (valid) credentials available, let the user log in.
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    config.nameListSheet.CREDENTIALS_NAME, SCOPES)
                creds = flow.run_local_server(port=0)
            # Save the credentials for the next run
            with open(config.nameListSheet.PICKLE_NAME, 'wb') as token:
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
