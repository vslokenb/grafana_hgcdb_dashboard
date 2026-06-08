import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from tool.helper import *

"""
Promote GF_USER to Org Admin using GF_SUPER_USER credentials.
Required so that GF_USER can create folders and upload dashboards.
"""

success = client.ensure_org_admin_role(GF_USER, GF_SUPER_USER, GF_SUPER_PASS)
if not success:
    print("[Role] Warning: could not verify Org Admin role for GF_USER.")
    print("[Role] If GF_USER already has Org Admin, this warning can be ignored.")
    print("[Role] Otherwise set GF_SUPER_USER/GF_SUPER_PASS in gf_conn.yaml.")
