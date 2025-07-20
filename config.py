import os
from dotenv import load_dotenv

load_dotenv()

host_stage = os.getenv("URL_STAGE")
SPREADSHEET_ID = os.getenv("SPREADSHEET_ID")
host_stage_second = os.getenv("URL_STAGE_SECOND")