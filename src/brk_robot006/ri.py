# Libs
import datetime
import getpass
import os

import time
from collections import defaultdict  # to dtype all vars at once
from pathlib import Path

import brk_rpa_utils as login
import numpy as np
import pandas as pd
from loguru import logger
from playwright.sync_api import sync_playwright
from dotenv import load_dotenv


# settings and initializations
logger.info("start")
load_dotenv()
folder_data = Path(os.getenv("FOLDER_DATA"))
sapshcut_path = Path(os.getenv("SAPSHCUT_PATH"))
pam_path = os.getenv("PAM_PATH")
ri_url = os.getenv("RI_URL")
robot_name = getpass.getuser()

# bestillingsnavn = robot_name + "_" + datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%d%H%M%S")
# bestillingsnavn = robot_name + "_" + datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%d")
folder_data_session = Path(folder_data / bestillingsnavn)

# ---------------------------------------------------------------------------- #
#                                      her                                     #
# ---------------------------------------------------------------------------- #

load_dotenv()
cpr = os.getenv("CPR")
download_single_anshistorik_from_ri(cpr=cpr)


# https://github.com/mherrmann/helium
