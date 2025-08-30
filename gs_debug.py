import re
import gspread
from google.oauth2.service_account import Credentials

# --- 1) Auth (use full Drive scope just for debugging) ---
SCOPE = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]
CREDS = Credentials.from_service_account_file(
    "pythonbattlefield-2a7d07648ac1.json")
print("Service account email:", CREDS.service_account_email)
CLIENT = gspread.authorize(CREDS.with_scopes(SCOPE))

# --- 2) Your sheet URL (exactly from the browser address bar) ---
URL = (
    "https://docs.google.com/spreadsheets/d/"
    "1QrsVmnaWtkZMZV8pu5HJkQnQXWFyk3LPyD9UdntkLI/edit#gid=0"
)

# --- 3) What can this service account see? ---
print("\nFiles visible to the service account:")
try:
    files = CLIENT.list_spreadsheet_files()
    if not files:
        print("  (none listed)")
    for f in files:
        print("  -", f.get("name"), f.get("id"))
except Exception as e:
    print("  list_spreadsheet_files failed:", repr(e))

# --- 4) Extract the key from URL and try open_by_key first ---
m = re.search(r"/d/([a-zA-Z0-9-_]+)", URL)
sheet_id = m.group(1) if m else None
print("\nExtracted sheet ID:", sheet_id)

try:
    sh = CLIENT.open_by_key(sheet_id)
    print("Opened by key. Tabs:", [ws.title for ws in sh.worksheets()])
except Exception as e:
    print("open_by_key failed:", repr(e))
    # Fallback: try open by URL too
    try:
        sh = CLIENT.open_by_url(URL)
        print("Opened by URL. Tabs:", [ws.title for ws in sh.worksheets()])
    except Exception as e2:
        print("open_by_url failed:", repr(e2))
        raise

# --- 5) If we got here, try read Heroes!A2 ---
try:
    heroes = sh.worksheet("Heroes")
    print("Heroes!A2 =", heroes.acell("A2").value)
except Exception as e:
    print("Reading Heroes!A2 failed:", repr(e))
