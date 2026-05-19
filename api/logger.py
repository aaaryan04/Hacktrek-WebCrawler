import json
import os

LOG_FILE = "database/scan_logs.json"

# ============================================
# CLEAR LOGS
# ============================================

def clear_logs():

    with open(LOG_FILE, "w") as file:

        json.dump([], file)

# ============================================
# ADD LOG
# ============================================

def add_log(message):

    logs = []

    if os.path.exists(LOG_FILE):

        with open(LOG_FILE, "r") as file:

            try:

                logs = json.load(file)

            except:

                logs = []

    logs.append(message)

    with open(LOG_FILE, "w") as file:

        json.dump(logs, file)

# ============================================
# GET LOGS
# ============================================

def get_logs():

    if not os.path.exists(LOG_FILE):

        return []

    with open(LOG_FILE, "r") as file:

        try:

            return json.load(file)

        except:

            return []