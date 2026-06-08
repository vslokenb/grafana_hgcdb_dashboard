import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from collections import defaultdict
import requests

from tool.helper import *

"""
One-shot cleanup: find every Grafana folder that the dashboard builder manages,
group dashboards by title, and delete all but the newest copy of each title.

Run this once after pulling the duplicate-fix branch, then re-run main.py to
get a clean single copy of every dashboard.
"""

DRY_RUN = "--dry-run" in sys.argv   # pass --dry-run to preview without deleting

def search_dashboards_in_folder(folder_uid: str) -> list:
    """Return all dashboard stubs inside a folder (or the General folder if folder_uid='')."""
    params = {"type": "dash-db", "limit": 500}
    if folder_uid:
        params["folderUIDs"] = folder_uid
    else:
        params["folderUIDs"] = "general"

    resp = requests.get(f"{GF_URL}/api/search", headers=client.headers, params=params)
    resp.raise_for_status()
    return resp.json()


def get_dashboard_version(uid: str) -> int:
    """Fetch the current version number of a dashboard by UID."""
    resp = requests.get(f"{GF_URL}/api/dashboards/uid/{uid}", headers=client.headers)
    if resp.status_code == 200:
        return resp.json().get("dashboard", {}).get("version", 0)
    return 0


def delete_dashboard(uid: str, title: str):
    resp = requests.delete(f"{GF_URL}/api/dashboards/uid/{uid}", headers=client.headers)
    if resp.status_code in (200, 204):
        print(f"  [DELETED] '{title}' (uid={uid})")
    else:
        print(f"  [ERROR]   '{title}' (uid={uid}) → {resp.status_code}: {resp.text}")


# Collect all folder UIDs we care about (everything in GF_FOLDER_UIDS + General)
folder_map = gf_conn.get("GF_FOLDER_UIDS", {})
folders_to_check = {"General": ""}   # name → uid
for name, uid in folder_map.items():
    if uid:
        folders_to_check[name] = uid

total_deleted = 0

for folder_name, folder_uid in sorted(folders_to_check.items()):
    dashboards = search_dashboards_in_folder(folder_uid)

    # Group by title
    by_title = defaultdict(list)
    for d in dashboards:
        by_title[d["title"]].append(d)

    duplicates_in_folder = {t: copies for t, copies in by_title.items() if len(copies) > 1}

    if not duplicates_in_folder:
        print(f"[Folder] '{folder_name}' — no duplicates.")
        continue

    print(f"\n[Folder] '{folder_name}' — {len(duplicates_in_folder)} title(s) with duplicates:")

    for title, copies in sorted(duplicates_in_folder.items()):
        # Fetch version for each copy so we can keep the newest
        versioned = []
        for d in copies:
            v = get_dashboard_version(d["uid"])
            versioned.append((v, d["uid"], d["title"]))
            print(f"  uid={d['uid']}  version={v}")

        versioned.sort(reverse=True)   # highest version = newest
        keep_uid = versioned[0][1]
        print(f"  → keeping uid={keep_uid} (version {versioned[0][0]})")

        for version, uid, t in versioned[1:]:
            if DRY_RUN:
                print(f"  [DRY-RUN] would delete '{t}' (uid={uid}, version={version})")
            else:
                delete_dashboard(uid, t)
                total_deleted += 1

if DRY_RUN:
    print(f"\nDry run complete — no dashboards deleted.")
else:
    print(f"\nDone. Deleted {total_deleted} duplicate dashboard(s).")
    print("Run 'python main.py' to recreate all dashboards cleanly.")
