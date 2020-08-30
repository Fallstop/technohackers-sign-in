class nameListSheet:
    # If modifying these scopes, delete the PICKLE_NAME file
    SCOPES = ["https://www.googleapis.com/auth/spreadsheets.readonly"]
    SPREADSHEET_ID = ""
    RANGE_NAME = "NameOfYouth"
    PICKLE_NAME = "nameListSheet.pickle"
    CREDENTIALS_NAME = "GSheetCredentials.json"

class sqlServer:
    # SQL server credentials to collate the sign in data
    URL = ""
    PORT = 3306
    USERNAME = ""
    PASSWORD = ""
    DATABASE = ""
    TABLE = ""

class backupCSV:
    fileName = "signInBackup.csv"
