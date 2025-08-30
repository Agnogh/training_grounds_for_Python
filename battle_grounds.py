import gspread
from google.oauth2.service_account import Credentials

SCOPE = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive.file",
]

CREDS = Credentials.from_service_account_file(
    "pythonbattlefield-2a7d07648ac1.json"
    )
CLIENT = gspread.authorize(CREDS.with_scopes(SCOPE))

# Quick sanity: list spreadsheets this service account can see
for f in CLIENT.list_spreadsheet_files():
    print("Seen by service account ->", f.get("name"), f.get("id"))

# this is to use the correct ID (with the hyphen after the 1
# I was missing all this damn time)
SHEET_ID = (
    "1-QrsVmnaWtkZMZV8pu5HJkQnQXWFyk3L"
    "PyD9UdntkLI"
)

# Trying ot open the spreadsheet using the key
sh = CLIENT.open_by_key(SHEET_ID)
print("Tabs:", [ws.title for ws in sh.worksheets()])

# Open Heroes tab in worksheet and read A2 only
heroes_ws = sh.worksheet("Heroes")
cell_value = heroes_ws.acell("A2").value
print("Value in Heroes!A2:", cell_value)
