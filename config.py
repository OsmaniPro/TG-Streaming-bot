import os
from os import getenv
from dotenv import load_dotenv

if os.path.exists("local.env"):
    load_dotenv("local.env")
CONFIG = False
load_dotenv()
ADMINS = admins
admins = {}

SESSION = getenv("SESSION_NAME", "session")
TOKEN = getenv("BOT_TOKEN")
API_ID = int(getenv("API_ID"))
API_HASH = getenv("API_HASH")
CHAT_ID = getenv("GROUP_SUPPORT", "osmanigroupbot)
