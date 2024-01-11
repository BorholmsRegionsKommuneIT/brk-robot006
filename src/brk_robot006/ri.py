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


def get_report_from_ri(
    cpr: str, df: pd.DataFrame, result: pd.DataFrame, manummer_column: str, folder_data_session: Path
) -> None:
    # initialize
    # hostname = socket.gethostname()

    # check if dev_mode
    # dev_mode = hostname.startswith("PCA")

    # Get current month and year in the format mm.yyyy
    current_month_year = datetime.datetime.now().strftime("%m.%Y")

    old_month_year = (datetime.datetime.now() - datetime.timedelta(days=365 * 8)).strftime("%m.%Y")

    # concat current month and year with old month and year
    date_interval = f"{old_month_year} - {current_month_year}"

    # ansforhold = '03'
    # hovedlonart = '0100; 0140; 0395; 0469; 0516; 0517'

    try:
        with sync_playwright() as playwright:
            ri = login.start_ri(pam_path, robot_name, ri_url, playwright)
            if ri is None:
                raise Exception("Failed to start RI")
            # tuple unpacking:
            page, context, browser = ri

            # add actions to RI
            try:
                page.get_by_text("Lønsagsbehandling").click()

                with page.expect_popup() as page1_info:
                    page.frame_locator('iframe[name="contentAreaFrame"]').frame_locator(
                        'iframe[name="Rapporter til lønkontrol"]'
                    ).get_by_role("link", name="Udbetalte timer på timeløn").click()

                page1 = page1_info.value

                selector_date_interval = (
                    "#DLG_VARIABLE_vsc_cvl_table_cid2x2 > table > tbody > tr > td:first-child > input"
                )

                selector_cvr = "#DLG_VARIABLE_vsc_cvl_table_cid2x6 > table > tbody > tr > td:first-child > input"

                # click in date field
                # rapport_variabelinput.frame_locator(
                #    'iframe[name="iframe_Roundtrip_9223372036563636042"]'
                # ).locator("#DLG_VARIABLE_vsc_cvl_VAR_3_INPUT_inp").click()

                # input datointerval 8 aar tilbage, som 12.2015 - 11.2023
                page1.frame_locator('iframe[name="iframe_Roundtrip_9223372036563636042"]').locator(
                    selector_date_interval
                ).fill(date_interval)

                # cpr nummer
                page1.frame_locator('iframe[name="iframe_Roundtrip_9223372036563636042"]').locator(selector_cvr).fill(
                    cpr
                )

                # Click OK
                page1.frame_locator("iframe[name=\"iframe_Roundtrip_9223372036563636042\"]").get_by_role(
                    "link", name="OK"
                ).click()

                # Donwload
                with page1.expect_download() as download_info:
                    with page1.expect_popup() as page4_info:
                        page1.frame_locator("iframe[name=\"iframe_Roundtrip_9223372036563636042\"]").get_by_role(
                            "link", name="Excel uden topinfo"
                        ).click()
                    page4 = page4_info.value
                download = download_info.value

                download.save_as(Path(folder_data_session / "test.xls"))

            except Exception as e:
                logger.error("An error occurred during page interactions", exc_info=True)
                print(f"An error occurred during page interactions: {e}")

            finally:
                time.sleep(5)
                if page:
                    page.close()
                if context:
                    context.close()
                if browser:
                    browser.close()

    except Exception as e:
        logger.error("An error occurred during playwright setup", exc_info=True)
        print(f"An error occurred during playwright setup: {e}")


load_dotenv()
cpr = os.getenv("CPR")
get_report_from_ri(cpr=cpr)


# https://github.com/mherrmann/helium
