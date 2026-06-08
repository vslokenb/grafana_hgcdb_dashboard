import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from tool.helper import *

"""
Register PostgreSQL data sources in Grafana.
  - Primary (hgcdb):  mac-postgres-db  — used by all generated dashboards
  - PLC database:     grafana_postgresql_datasource_PLC — used by thermal_cycle dashboards
"""

gf_conn.reload()

datasource_name = gf_conn.get('GF_DATA_SOURCE_NAME')
datasource_uid  = gf_conn.get('GF_DATA_SOURCE_UID')

client.add_postgres_datasource(
    datasource_name, datasource_uid,
    DB_HOST, DB_PORT, DB_NAME,
    DB_USER, DB_PASSWORD
)

# PLC datasource (thermal cycle dashboards) — only registered if configured
PLC_HOST     = db_conn.get("plc_db_hostname")
PLC_PORT     = db_conn.get("plc_db_port", "5432")
PLC_DBNAME   = db_conn.get("plc_dbname")
PLC_USER     = db_conn.get("plc_user")
PLC_PASSWORD = db_conn.get("plc_password", "")
PLC_DS_UID   = "grafana_postgresql_datasource_PLC"

if PLC_HOST and PLC_DBNAME and PLC_USER:
    gf_conn.set("GF_PLC_DS_UID", PLC_DS_UID)
    gf_conn.save()
    client.add_postgres_datasource(
        "grafana-postgresql-datasource-PLC", PLC_DS_UID,
        PLC_HOST, PLC_PORT, PLC_DBNAME,
        PLC_USER, PLC_PASSWORD
    )
else:
    print("[Datasource] PLC datasource not configured — skipping. "
          "Set plc_db_hostname / plc_dbname / plc_user in db_conn.yaml to enable thermal_cycle dashboards.")
