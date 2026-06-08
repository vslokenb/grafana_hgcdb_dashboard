import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from collections import defaultdict
import requests

from tool.helper import *

"""
One-shot cleanup: query Grafana directly for every folder and dashboard,
group dashboards by title within each folder, and delete all but the
newest copy of each title.

Usage:
    python delete/delete_duplicate_dashboards.py            # delete for real
    python delete/delete_duplicate_dashboards.py --dry-run  # preview only
"""

DRY_RUN = "--dry-run" in sys.argv


def get_all_folders() -> list:
    """Return all Grafana folders (does not include the General / root folder)."""
    resp = requests.get(f"{GF_URL}/api/folders", headers=client.headers, params={"limit": 500})
    resp.raise_for_status()
    return resp.json()   # list of {uid, title, ...}


def search_dashboards(folder_uid: str = None) -> list:
    """Return all dashboard stubs in a folder (or root if folder_uid is None)."""
    params = {"type": "dash-db", "limit": 500}
    if folder_uid:
        params["folderUIDs"] = folder_uid
    else:
        params["folderUIDs"] = "general"
    resp = requests.get(f"{GF_URL}/api/search", headers=client.headers, params=params)
    resp.raise_for_status()
    return resp.json()


def get_version(uid: str) -> int:
    resp = requests.get(f"{GF_URL}/api/dashboards/uid/{uid}", headers=client.headers)
    if resp.status_code == 200:
        return resp.json().get("dashboard", {}).get("version", 0)
    return 0


def delete_dashboard(uid: str, title: str):
    resp = requests.delete(f"{GF_URL}/api/dashboards/uid/{uid}", headers=client.headers)
    if resp.status_code in (200, 204):
        print(f"    [DELETED] '{title}'  uid={uid}")
    else:
        print(f"    [ERROR]   '{title}'  uid={uid}  → {resp.status_code}: {resp.text}")


def process_folder(folder_name: str, folder_uid: str = None):
    dashboards = search_dashboards(folder_uid)
    if not dashboards:
        return

    by_title = defaultdict(list)
    for d in dashboards:
        by_title[d["title"]].append(d)

    dupes = {t: c for t, c in by_title.items() if len(c) > 1}
    if not dupes:
        print(f"[Folder] '{folder_name}' — no duplicates.")
        return

    print(f"\n[Folder] '{folder_name}' — {len(dupes)} title(s) with duplicates:")
    global total_deleted

    for title, copies in sorted(dupes.items()):
        versioned = [(get_version(d["uid"]), d["uid"]) for d in copies]
        versioned.sort(reverse=True)

        print(f"  Title: '{title}'")
        for v, uid in versioned:
            print(f"    uid={uid}  version={v}")

        keep_uid = versioned[0][1]
        print(f"    → keeping uid={keep_uid}  (version {versioned[0][0]})")

        for v, uid in versioned[1:]:
            if DRY_RUN:
                print(f"    [DRY-RUN] would delete uid={uid}  version={v}")
            else:
                delete_dashboard(uid, title)
                total_deleted += 1


# ── main ──────────────────────────────────────────────────────────────────────
total_deleted = 0

# Root / General folder
process_folder("General", folder_uid=None)

# Every named folder Grafana knows about
for folder in get_all_folders():
    process_folder(folder["title"], folder["uid"])

if DRY_RUN:
    print("\nDry run complete — nothing deleted.")
else:
    print(f"\nDone. {total_deleted} duplicate(s) deleted.")
    if total_deleted:
        print("Run 'python main.py' to recreate dashboards cleanly.")
