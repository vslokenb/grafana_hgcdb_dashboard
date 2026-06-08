import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from tool.helper import *

"""
One-shot cleanup: delete the MMTS IV Tests folder and its dashboards from Grafana.
Run this once, then re-run main.py to recreate everything with correct UIDs.
"""

FOLDER_TITLE = "MMTS IV Tests"
FOLDER_UID   = create_uid(FOLDER_TITLE)   # "mmts-iv-tests"

# Also try any UID stored in gf_conn (may differ if folder was created manually)
stored_uid = gf_conn.get(f"GF_FOLDER_UIDS.{FOLDER_TITLE}", "")

for uid in {FOLDER_UID, stored_uid} - {""}:
    client.delete_folder(uid)

# Remove stale UID from config so create_folders.py writes it fresh
gf_conn.set(f"GF_FOLDER_UIDS.{FOLDER_TITLE}", "")
gf_conn.save()

print(f"\nDone. Run 'python main.py' to recreate the folder and upload dashboards.")
