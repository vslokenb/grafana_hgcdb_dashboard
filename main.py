import os
import subprocess
import sys
from time import sleep

import yaml

from tool.helper import *

"""
This file does EVERYTHING for you.
    — from configuring Grafana to linking PostgreSQL and auto-generating dashboards.

Special thanks to Sindhu Murthy and Manami Kanemura for the amazing database this is built on.

I'm also sincerely thankful to the entire CMU HGCal MAC for trusting me with the responsibility of leading this project.
"""

cmu_hgc_mac_logo = """
 ▗▄▄▖▗▖  ▗▖▗▖ ▗▖    ▗▖ ▗▖ ▗▄▄▖ ▗▄▄▖    ▗▖  ▗▖ ▗▄▖  ▗▄▄▖
▐▌   ▐▛▚▞▜▌▐▌ ▐▌    ▐▌ ▐▌▐▌   ▐▌       ▐▛▚▞▜▌▐▌ ▐▌▐▌   
▐▌   ▐▌  ▐▌▐▌ ▐▌    ▐▛▀▜▌▐▌▝▜▌▐▌       ▐▌  ▐▌▐▛▀▜▌▐▌   
▝▚▄▄▖▐▌  ▐▌▝▚▄▞▘    ▐▌ ▐▌▝▚▄▞▘▝▚▄▄▖    ▐▌  ▐▌▐▌ ▐▌▝▚▄▄▖

"""

def main():
    print(cmu_hgc_mac_logo)

    run_times = int(gf_conn.get('GF_RUN_TIMES'))

    # Validate stored token before deciding to skip preSteps
    token_valid = client.validate_api_key()

    if not token_valid:
        print(" >> Auth check failed. Verify GF_SUPER_USER/GF_SUPER_PASS in gf_conn.yaml.\n")
        sys.exit(1)

    # Always ensure the PostgreSQL datasource is registered (idempotent — skips if already exists)
    subprocess.run([sys.executable, "./preSteps/add_dbsource.py"])

    # Everything Need To Generate
    subprocess.run([sys.executable, "create/create_folders.py"], check=True)
    sleep(0.5)    # wait for folders to be added
    subprocess.run([sys.executable, "create/create_dashboards.py"], check=True)
    subprocess.run([sys.executable, "create/create_static_dashboards.py"], check=True)
    # subprocess.run([sys.executable, "create/create_alerts.py"], check=True)

    # Add run times
    gf_conn.set('GF_RUN_TIMES', run_times + 1)
    gf_conn.save()
    print(" >>>> GF_RUN_TIMES updated!")

    # Done!!
    print("\n >>>>>> All done!")


# allow run
if __name__ == "__main__":
    main()
