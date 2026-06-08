import os
import sys
import json
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tool.helper import *

"""
Upload pre-built dashboard JSON files from static_dashboards/ to Grafana.
Each subdirectory becomes a Grafana folder. Datasource UIDs are remapped to
the locally-configured values so dashboards work regardless of origin site.
"""

STATIC_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "static_dashboards")

# Map source datasource UIDs → local configured UIDs
DS_UID_MAP = {
    "mac_postgres_db":                    GF_DS_UID,
    "grafana_postgresql_datasource_PLC":  gf_conn.get("GF_PLC_DS_UID", "grafana_postgresql_datasource_PLC"),
}


def remap_datasource_uids(obj, uid_map: dict):
    """Recursively replace datasource UIDs throughout a dashboard JSON."""
    if isinstance(obj, dict):
        if "uid" in obj and obj.get("type") in (None, "grafana-postgresql-datasource", "postgres"):
            obj["uid"] = uid_map.get(obj["uid"], obj["uid"])
        return {k: remap_datasource_uids(v, uid_map) for k, v in obj.items()}
    if isinstance(obj, list):
        return [remap_datasource_uids(v, uid_map) for v in obj]
    return obj


def create_static_folder(folder_name: str) -> str:
    """Create (or verify) a Grafana folder for a static dashboard set."""
    folder_uid = create_uid(folder_name)
    uid = client.create_or_get_folder(folder_name, folder_uid)
    gf_conn.set(f"GF_FOLDER_UIDS.{folder_name}", uid)
    gf_conn.save()
    print(f"[Folder] Ready: '{folder_name}' (uid={uid})")
    return uid


def upload_dashboards(folder_uid: str, json_dir: str):
    """Upload all JSON files from json_dir into the given Grafana folder."""
    for filename in sorted(os.listdir(json_dir)):
        if not filename.endswith(".json"):
            continue
        filepath = os.path.join(json_dir, filename)
        with open(filepath, "r") as fh:
            dashboard = json.load(fh)

        dashboard.pop("id", None)
        dashboard = remap_datasource_uids(dashboard, DS_UID_MAP)
        client.upload_dashboard_json(dashboard, folder_uid)


if not os.path.isdir(STATIC_DIR):
    print("[Static] No static_dashboards/ directory found — skipping.")
    sys.exit(0)

for folder_name in sorted(os.listdir(STATIC_DIR)):
    folder_path = os.path.join(STATIC_DIR, folder_name)
    if not os.path.isdir(folder_path):
        continue
    folder_uid = create_static_folder(folder_name)
    upload_dashboards(folder_uid, folder_path)

print("\n >>>> Static dashboards uploaded!")
