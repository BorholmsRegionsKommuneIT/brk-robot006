"""
Robot006
"""

# ----------------------------------- Libs ----------------------------------- #
import getpass

# what is this: from http.client import TEMPORARY_REDIRECT
import io
import json
import os
import re

# import shutil
import time
from collections import defaultdict  # to dtype all vars at once
from pathlib import Path

import brk_rpa_utils
import html5lib
import numpy as np
import pandas as pd
import pendulum
from bs4 import BeautifulSoup  # BeautifulSoup4
from dotenv import load_dotenv
from loguru import logger
from playwright.sync_api import sync_playwright

server_name = os.environ["COMPUTERNAME"]
user = getpass.getuser()
load_dotenv()
server_prefix = os.getenv("SERVER_PREFIX")
folder_data = Path(os.getenv("FOLDER_DATA"))
sapshcut_path = Path(os.getenv("SAPSHCUT_PATH"))
pam_path = os.getenv("PAM_PATH")
ri_url = os.getenv("RI_URL")
log_path = os.getenv("LOG_PATH")
logger.add(log_path, format="{time} {level} {message}", level="DEBUG")

# Right now devmode has no real use.

downloadmode = 0  # Don't download unless running on server with server_prefix
if server_name.startswith(server_prefix):
    devmode = 0
    downloadmode = 1  # 0 / 1
else:
    devmode = 1  # (0 / 1)

if devmode == 1 & downloadmode == 1:
    logger.info("starting in devmode with report generation and download")
if devmode == 1 & downloadmode == 0:
    logger.info("starting in devmode without any downloads")
if devmode == 0:
    logger.info("starting in production with report generation and download")

if downloadmode == 0:
    bestillingsnavn = user + "_" + "persistent_dev_data"
else:
    bestillingsnavn = user + "_" + pendulum.now().strftime("%Y%m%d%H%M%S")

folder_data_session = Path(folder_data / bestillingsnavn)

if downloadmode == 1:
    session = brk_rpa_utils.start_opus(pam_path=pam_path, user=user, sapshcut_path=sapshcut_path)


# ---------------------------------------------------------------------------- #
#                                Rapport trækkes                               #
# ---------------------------------------------------------------------------- #
def download_report(folder_data, bestillingsnavn, folder_data_session, session) -> None:
    """
    This function downloads a report from OPUS and saves it in a folder named after the current date and time.
    """

    # Click bestilling af fleksibel rapport
    # Rapport Traekkes
    session.Children(0).FindById("wnd[0]").Maximize()
    session.findById("wnd[0]/usr/cntlIMAGE_CONTAINER/shellcont/shell/shellcont[0]/shell").doubleClickNode("F00002")
    time.sleep(0.5)

    # Hent variant
    session.findById("wnd[0]/tbar[1]/btn[17]").press()
    time.sleep(0.5)

    # Click Udfor
    session.findById("wnd[1]/tbar[0]/btn[8]").press()
    time.sleep(0.5)

    # create directory in folder_data named bestillingsnavn
    Path(folder_data / bestillingsnavn).mkdir(parents=True, exist_ok=True)

    # Enter the bestillingsnavn in the text field
    session.findById("wnd[0]/usr/txtP_BESTIL").text = bestillingsnavn
    time.sleep(0.5)

    # Click Udfor
    session.findById("wnd[0]/tbar[1]/btn[8]").press()
    time.sleep(0.5)

    #  Click tilbage
    session.findById("wnd[0]/tbar[0]/btn[3]").press()
    time.sleep(0.5)

    #  Click oversigt over fleksible rapporter
    session.findById("wnd[0]/usr/cntlIMAGE_CONTAINER/shellcont/shell/shellcont[0]/shell").selectedNode = "F00003"

    session.findById("wnd[0]/usr/cntlIMAGE_CONTAINER/shellcont/shell/shellcont[0]/shell").doubleClickNode("F00003")
    time.sleep(0.5)

    #  Enter bestillingsnavn and press udfor
    session.findById("wnd[0]/usr/txtP_BESTIL").text = bestillingsnavn
    session.findById("wnd[0]/usr/txtP_BESTIL").setFocus()
    session.findById("wnd[0]/usr/txtP_BESTIL").caretPosition = 15
    session.findById("wnd[0]/tbar[1]/btn[8]").press()
    time.sleep(0.5)

    # Wait for report to be generated and show it

    # Defines helper function to check if an element exists
    def element_exists(session, element_id):
        """Check if an element exists by its id css selector."""
        try:
            session.findById(element_id)
            return True
        except Exception:  # Catch all exceptions to be more robust
            return False

    # Check if either of the two id's exists and have the text "Igang"
    while True:
        if (
            element_exists(session, "wnd[0]/usr/lbl[100,3]")
            and session.findById("wnd[0]/usr/lbl[100,3]").Text == "Igang"
        ) or (
            element_exists(session, "wnd[0]/usr/lbl[100,2]")
            and session.findById("wnd[0]/usr/lbl[100,2]").Text == "Igang"
        ):
            time.sleep(3)
            # refresh window
            session.findById("wnd[0]").sendVKey(5)
        else:
            break

    # Click on the report line to show it.
    time.sleep(1)
    session.findById("wnd[0]").sendVKey(2)
    time.sleep(0.5)

    #  Click on local file popup
    session.findById("wnd[0]/tbar[1]/btn[45]").press()
    session.findById("wnd[1]/usr/subSUBSCREEN_STEPLOOP:SAPLSPO5:0150/sub:SAPLSPO5:0150/radSPOPLI-SELFLAG[1,0]").select()
    session.findById(
        "wnd[1]/usr/subSUBSCREEN_STEPLOOP:SAPLSPO5:0150/sub:SAPLSPO5:0150/radSPOPLI-SELFLAG[1,0]"
    ).setFocus()
    session.findById("wnd[1]/tbar[0]/btn[0]").press()
    time.sleep(0.5)

    #  Insert Directory and Filename into popup and download the report.
    session.findById("wnd[1]/usr/ctxtDY_PATH").text = str(folder_data_session)
    session.findById("wnd[1]/usr/ctxtDY_FILENAME").text = bestillingsnavn + ".csv"
    session.findById("wnd[1]/usr/ctxtDY_FILENAME").caretPosition = 15
    session.findById("wnd[1]/tbar[0]/btn[0]").press()
    time.sleep(0.5)


if downloadmode == 1:
    download_report(folder_data, bestillingsnavn, folder_data_session, session)


def return_to_start_view() -> None:
    """
    Press Back 3 times to go to Vis personalestamdata, where data from the downloaded report, will we pasted in.
    """
    for _ in range(3):
        session.findById("wnd[0]/tbar[0]/btn[3]").press()
        time.sleep(0.5)

    session.findById("wnd[0]/usr/cntlIMAGE_CONTAINER/shellcont/shell/shellcont[0]/shell").doubleClickNode("F00004")


if downloadmode == 1:
    return_to_start_view()


def read_report(folder_data_session: Path, bestillingsnavn: str) -> pd.core.frame.DataFrame:
    try:
        data_types = defaultdict(lambda: "str")

        #  Read the report into a dataframe
        report_path = folder_data_session / f"{bestillingsnavn}.csv"

        df = pd.read_csv(
            filepath_or_buffer=report_path,
            sep="\t",
            header=None,
            encoding="windows-1252",
            skiprows=12,
            dtype=data_types,
            # usecols=[1, *range(3, 17)],
        )
        df.columns = df.iloc[0]
        df = df.drop(df.index[0])
        df = df.dropna(axis=1, how="all")
        df.columns = df.columns.str.lower().str.replace("[-.,1æøå ]", "", regex=True)
        df["samletpct"] = df["samletpct"].str.replace(",", ".").astype(float)
        logger.info(f"Successfully read ansforhold data from {report_path}")
        return df

    except Exception as e:
        # Optionally log the error or handle it in a way that's suitable for your application
        logger.error(f"An error occurred: {e}")
        return pd.DataFrame()


df = read_report(folder_data_session=folder_data_session, bestillingsnavn=bestillingsnavn)

# ------------------------------- Rens rapport ------------------------------- #
# Fjern whitespace fra objects-columns
df_obj = df.select_dtypes(["object"])
df[df_obj.columns] = df_obj.apply(lambda x: x.str.strip())

# ----------------------------------- TEMP ----------------------------------- #
if devmode == 1:
    df = df[:10]
# --------------------------------- END TEMP --------------------------------- #

# --------- Get df row count that must persist throughout the session -------- #

persistent_df_row_count = len(df)


def validate_dataframe(dataframe, col_count, row_count=None, dataframe_name="", manummer_column=""):
    cols = dataframe.shape[1]
    try:
        # Column count validation
        if cols != col_count:
            error_message = f"{dataframe_name} has wrong number of columns: expected {col_count}, found {cols}"
            raise ValueError(error_message)
        logger.info(f"Validation successful: {dataframe_name} has the expected number of columns: {col_count}")

        # Row count validation (only if row_count is provided)
        if row_count is not None:
            rows = len(dataframe)
            if rows != row_count:
                error_message = f"{dataframe_name} has wrong number of rows: expected {row_count}, found {rows}"
                raise ValueError(error_message)
            logger.info(f"Validation successful: {dataframe_name} has the expected number of rows: {row_count}")

        # Check if the manummer_column exists
        if manummer_column and manummer_column not in dataframe.columns:
            error_message = f"{dataframe_name} must contain the '{manummer_column}' column."
            raise ValueError(error_message)

    except ValueError as e:
        logger.error(f"Validation failed: {e}")


validate_dataframe(
    dataframe=df, col_count=15, row_count=persistent_df_row_count, dataframe_name="df", manummer_column="manummer"
)


# ---------------------------------------------------------------------------- #
#                      Har medarbejder pension i forvejen                      #
# ---------------------------------------------------------------------------- #
def har_medarbejder_pension_i_forvejen(df: pd.DataFrame) -> pd.DataFrame:
    """
    Adds 2 boolean columns to 'DataFrame' indicating if the employee,
    identified by the 'manummer' column, is created with pension.

    Parameters:
    DataFrame (pd.DataFrame): The DataFrame containing employee data with 'pensberegnkode',
    'samletpct', and 'manummer' columns.
    manummer_column (str): The name of the column in both DataFrames that contains employee IDs.

    Returns:
    pd.DataFrame: df with an added boolean column 'har_pension' and 'har_pension_0_pct'.
    """

    # Check if required columns exist in df
    if "pensberegnkode" in df.columns and "samletpct" in df.columns:
        zero = 0.00
        df["har_pension"] = (df["pensberegnkode"] == "1") & (df["samletpct"] > zero)
        df["har_pension_0_pct"] = (df["pensberegnkode"] == "1") & (df["samletpct"] == zero)
    else:
        msg = "The DataFrame must contain 'pensberegnkode' and 'samletpct' columns."
        raise ValueError(msg)

    return df


df = har_medarbejder_pension_i_forvejen(df)

validate_dataframe(
    dataframe=df, col_count=17, row_count=persistent_df_row_count, dataframe_name="df", manummer_column="manummer"
)


# ---------------------------------------------------------------------------- #
#                            Er medarbejder under 21                           #
# ---------------------------------------------------------------------------- #
def _calculate_age(cpr: str) -> int:
    """
    Returns age from cpr number
    """
    fodselsdag_str = cpr[:6]
    fodselsdag = pendulum.from_format(fodselsdag_str, "DDMMYY").in_tz("UTC")
    today = pendulum.now("UTC")
    if fodselsdag.year > today.year:
        fodselsdag = fodselsdag.subtract(years=100)
    days_difference = (today - fodselsdag).in_days()
    age = days_difference // 365.25
    return age


def er_medarbejder_under_21(df: pd.DataFrame) -> pd.DataFrame:
    """
    Adds a boolean column to the DataFrame indicating if the employee,
    identified by the 'manummer' column, is under the age of 21.

    Parameters:
    df (pd.DataFrame): The DataFrame containing employee data with 'cprnr' and 'manummer' columns.

    Returns:
    pd.DataFrame: The 'df' DataFrame with an added boolean column 'er_under_21'.
    """
    if "cprnr" not in df.columns:
        msg = "The DataFrame must contain the 'cprnr' column."
        raise ValueError(msg)

    # Add 'er_under_21' column to df
    age_threshhold = 21
    df["er_under_21"] = df["cprnr"].apply(_calculate_age) < age_threshhold

    return df


df = er_medarbejder_under_21(df)

validate_dataframe(
    dataframe=df, col_count=18, row_count=persistent_df_row_count, dataframe_name="df", manummer_column="manummer"
)


# ---------------------------------------------------------------------------- #
#               Er medarbejder oprettet med pension på månedsløn               #
# ---------------------------------------------------------------------------- #


def download_single_ansforhold(manummer: str, folder_data_session: Path, bestillingsnavn: str, session) -> None:
    """
    Function to download ansaettelsesforloeb for a given manummer.
    """
    try:
        # Enter manummer
        session.findById("wnd[0]/usr/subSUBSCR_PERNR:SAPMP50A:0110/ctxtRP50G-PERNR").text = manummer

        # Press ansaettelsesforloeb
        session.findById("wnd[0]/tbar[1]/btn[31]").press()

        # Click on lokal fil
        session.findById("wnd[0]/tbar[1]/btn[45]").press()

        # Choose regneark
        session.findById(
            "wnd[1]/usr/subSUBSCREEN_STEPLOOP:SAPLSPO5:0150/sub:SAPLSPO5:0150/radSPOPLI-SELFLAG[1,0]"
        ).select()
        session.findById(
            "wnd[1]/usr/subSUBSCREEN_STEPLOOP:SAPLSPO5:0150/sub:SAPLSPO5:0150/radSPOPLI-SELFLAG[1,0]"
        ).setFocus()

        # Click checkmark
        session.findById("wnd[1]/tbar[0]/btn[0]").press()

        time.sleep(0.5)  # Waiting for the process to complete

        # Insert folder_data_session in Directory field
        session.findById("wnd[1]/usr/ctxtDY_PATH").text = str(folder_data_session)
        # define filename var
        filename = f"{bestillingsnavn}_{manummer}.csv"
        # Insert filename into Filnavn
        session.findById("wnd[1]/usr/ctxtDY_FILENAME").text = str(filename)

        # Click Erstat. Not generer in case the file exist. Nor Udvid it will append to file.
        session.findById("wnd[1]/tbar[0]/btn[11]").press()

        # Click back to "Vis personalestamdata"
        session.findById("wnd[0]/tbar[0]/btn[3]").press()

    except Exception as e:
        # Handle any exception that might occur and return a meaningful message
        logger.error(f"An error occurred: {e}")


def download_all_ansforhold(df: pd.DataFrame, folder_data_session: Path, bestillingsnavn: str, session) -> None:
    manummer_list = (df["manummer"]).tolist()

    for manummer in manummer_list:
        try:
            # Download data for each manummer
            download_single_ansforhold(manummer, folder_data_session, bestillingsnavn, session)
        except Exception as e:
            logger.error(f"Error downloading ansforhold for manummer {manummer}: {e}")
        # Continue with the next iteration
        continue


if downloadmode == 1:
    download_all_ansforhold(
        df=df, folder_data_session=folder_data_session, bestillingsnavn=bestillingsnavn, session=session
    )


def read_single_ansforhold(manummer: str, folder_data_session: Path, bestillingsnavn: str) -> pd.DataFrame:
    """
    Funktion til at læse ansættelsesforløb
    """
    try:
        data_types = defaultdict(lambda: "str")

        path_csv_ansforhold = Path(folder_data_session / f"{bestillingsnavn}_{manummer}.csv")

        df_ansforhold = pd.read_csv(
            filepath_or_buffer=path_csv_ansforhold,
            sep="\t",
            header=None,
            encoding="windows-1252",
            skiprows=[0, 1, 2, 3, 5],
            dtype=data_types,
        )
        df_ansforhold.columns = df_ansforhold.iloc[0]
        df_ansforhold = df_ansforhold.drop(df_ansforhold.index[0])
        df_ansforhold.columns = df_ansforhold.columns.str.lower().str.replace("[-.,1æøå ]", "", regex=True)
        logger.info(f"Successfully read ansforhold data from {path_csv_ansforhold}")
        return df_ansforhold

    except Exception as e:
        # Optionally log the error or handle it in a way that's suitable for your application
        logger.error(f"An error occurred: {e}")
        return pd.DataFrame()


# ----------- Funktion til at filtrere et enkelt ansættelsesforløb ----------- #
def filter_df_ansforhold(df_ansforhold) -> pd.DataFrame:
    try:
        df_filtered = df_ansforhold.loc[
            (df_ansforhold["ansfh"] == "01")
            & (df_ansforhold["penskasn"] != "30201")
            & (df_ansforhold["penskasn"] != "30399")
            & (df_ansforhold["penskasn"] != "30210")
            & (df_ansforhold["penskasn"] != "39999")
            & (df_ansforhold["penskasn"].notna())
        ].copy()

        return df_filtered

    except Exception as e:
        logger.error(f"Error in filter_df_ansforhold: {e}")
        return pd.DataFrame()


# ---------------- beregning_timeantal_maan_ans er fra slide 15 --------------- #
# -------- funktionen kører på df_ansforhold, derfor skal den med her, -------- #
# ---- selvom den først er beskrevet under sektion "beregning af timeantal pr måned" --- #
def beregning_timeantal_maan_ans(df_ansforhold) -> pd.DataFrame:
    try:
        df_timeantal_maan_ans = df_ansforhold.loc[
            (df_ansforhold["ansfh"] == "01") & (df_ansforhold["penskasn"].notna())
        ].copy()

        return df_timeantal_maan_ans

    except Exception as e:
        logger.error(f"Error in filter_df_ansforhold: {e}")
        return pd.DataFrame()


# --------- Funktion til at sortere og udvælge den ældste ansættelse --------- #
def sort_df_filtered(df_filtered) -> pd.DataFrame:
    try:
        df_filtered["startdato"] = pd.to_datetime(df_filtered["startdato"], format="%d.%m.%Y")
        df_sorted = df_filtered.sort_values(by=["startdato"])

        if not df_sorted.empty:
            df_sorted = df_sorted.iloc[[0]]
        return df_sorted

    except Exception as e:
        logger.error(f"Error in sort_df_ansforhold: {e}")
        return pd.DataFrame()


# --- Kør de 3 funktioner (read, filter, sort) i et loop over alle manumre --- #
# ---- Hvis medarbejder har en linje, svarer det til en True value i result --- #
# ---------- all_rows indeholder alle df_sorted samlet i et datarame --------- #
def process_all_ansforhold(df: pd.DataFrame, folder_data_session: Path, bestillingsnavn: str) -> pd.DataFrame:
    """
    Loops over manummer_list and runs all the single functions.
    """
    # global all_rows
    # all_rows = []  # List to store the single-row DataFrames, mostly for debugging purposes
    manummer_list = (df["manummer"]).tolist()
    df["oprettet_pension_maaned"] = False  # Initialize the column in df

    for manummer in manummer_list:
        try:
            # Read and process the downloaded data
            df_ansforhold = read_single_ansforhold(manummer, folder_data_session, bestillingsnavn)

            validate_dataframe(
                dataframe=df_ansforhold,
                col_count=20,
                dataframe_name="df_ansforhold",
                manummer_column="manr",
            )
            # Filter and sort the DataFrame
            df_filtered = filter_df_ansforhold(df_ansforhold)
            df_sorted = sort_df_filtered(df_filtered)

            # Append the sorted DataFrame to the list
            if df_sorted.columns[0] is np.nan:
                df_sorted = df_sorted.drop(df_sorted.columns[0], axis=1)
            # all_rows.append(df_sorted)

            bull = len(df_sorted) == 1
            # Update df directly depending on if df_sorted has exactly one row
            df.loc[df["manummer"] == manummer, "oprettet_pension_maaned"] = bull

        except Exception as e:
            logger.error(f"Error processing manummer {manummer}: {e}")
            # Continue with the next iteration
            continue

    # Concatenate all single-row DataFrames into one DataFrame
    # all_rows = pd.concat(all_rows, ignore_index=False)

    return df


df = process_all_ansforhold(
    df=df,
    folder_data_session=folder_data_session,
    bestillingsnavn=bestillingsnavn,
)

validate_dataframe(
    dataframe=df, col_count=19, row_count=persistent_df_row_count, dataframe_name="df", manummer_column="manummer"
)


# --------------------------------- debugging -------------------------------- #
# df_ansforhold_59433 = read_single_ansforhold('59433', folder_data_session, bestillingsnavn)
# df_filtered_59433 = filter_df_ansforhold(df_ansforhold_59433)
# df_sorted_59433 = sort_df_filtered(df_filtered_59433)

# oprettet_pension_maaned.to_csv(
#    path_or_buf=Path(folder_data_session / "oprettet_pension_maaned.csv"), index=False, encoding='utf-8'
# )


# ---------------------------------------------------------------------------- #
#     Har den timelønnede været ansat mindre end 12 måneder indenfor 8 år?     #
# ---------------------------------------------------------------------------- #
def get_credentials(pam_path, user, fagsystem) -> None:
    """
    Internal function to retrieve credentials.

    pam_path = os.getenv("PAM_PATH")

    Define pam_path in an .env file in the root of your project. Add paths like so:
    SAPSHCUT_PATH=C:/Program Files (x86)/SAP/FrontEnd/SAPgui/sapshcut.exe

    user = getpass.getuser()

    Under the pam_path uri der should be a user.json file with the structure:

    {
    "ad": { "username": "robot00X", "password": "x" },
    "opus": { "username": "jrrobot00X", "password": "x" },
    "rollebaseretindgang": { "username": "jrrobot00X", "password": "x" }
    }
    """
    pass_file = Path(pam_path) / user / f"{user}.json"

    try:
        with open(pass_file) as file:
            json_string = json.load(file)

        username = json_string[fagsystem]["username"]
        password = json_string[fagsystem]["password"]

        return username, password

    except FileNotFoundError:
        logger.error("File not found", exc_info=True)
    except json.JSONDecodeError:
        logger.error("Invalid JSON in file", exc_info=True)
    except Exception:
        logger.error("An error occurred:", exc_info=True)

    return None


def download_all_anshistorik_from_ri(df: pd.DataFrame, folder_data_session: Path) -> None:
    # initialize
    # hostname = socket.gethostname()

    # check if dev_mode
    # dev_mode = hostname.startswith("PCA")

    # Get current month and year in the format mm.yyyy
    current_month_year = pendulum.now().in_tz("UTC").format("MM.YYYY")

    old_month_year = pendulum.now().in_tz("UTC").subtract(years=8).format("MM.YYYY")

    # concat current month and year with old month and year
    date_interval = f"{old_month_year} - {current_month_year}"

    # ansforhold = '03'
    # hovedlonart = '0100; 0140; 0395; 0469; 0516; 0517'
    username, password = get_credentials(pam_path, user, fagsystem="rollebaseretindgang")

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=False, slow_mo=50)
        context = browser.new_context(viewport={"width": 2560, "height": 1440})
        page = context.new_page()
        page.goto(ri_url)
        page.get_by_placeholder("Brugernavn").click()
        page.get_by_placeholder("Brugernavn").fill(username)
        page.get_by_placeholder("Brugernavn").press("Tab")
        page.get_by_placeholder("Password").click()
        page.get_by_placeholder("Password").fill(password)
        page.get_by_role("button", name="Log på").click()
        page.get_by_text("Lønsagsbehandling").click()

        with page.expect_popup() as page1_info:
            page.frame_locator('iframe[name="contentAreaFrame"]').frame_locator(
                'iframe[name="Rapporter til lønkontrol"]'
            ).get_by_role("link", name="Udbetalte timer på timeløn").click()
        page1 = page1_info.value

        selector_date_interval = "#DLG_VARIABLE_vsc_cvl_table_cid2x2 > table > tbody > tr > td:first-child > input"

        selector_cvr = "#DLG_VARIABLE_vsc_cvl_table_cid2x6 > table > tbody > tr > td:first-child > input"

        # click in date field
        # rapport_variabelinput.frame_locator(
        #    'iframe[name="iframe_Roundtrip_9223372036563636042"]'
        # ).locator("#DLG_VARIABLE_vsc_cvl_VAR_3_INPUT_inp").click()

        # input datointerval 8 aar tilbage, som 12.2015 - 11.2023
        page1.frame_locator('iframe[name="iframe_Roundtrip_9223372036563636042"]').locator(selector_date_interval).fill(
            date_interval
        )

        for cpr in df["cprnr"]:
            page1.frame_locator('iframe[name="iframe_Roundtrip_9223372036563636042"]').locator(selector_cvr).fill(cpr)

            # Click OK
            page1.frame_locator('iframe[name="iframe_Roundtrip_9223372036563636042"]').get_by_role(
                "link", name="OK"
            ).click()

            # Donwload
            with page1.expect_download() as download_info:
                with page1.expect_popup():
                    page1.frame_locator('iframe[name="iframe_Roundtrip_9223372036563636042"]').get_by_role(
                        "link", name="Excel uden topinfo"
                    ).click()
            download = download_info.value
            download_path = Path(folder_data_session / f"anshistorik_{cpr}.mhtml")
            download.save_as(download_path)

            # back to variabelskærm
            page1.frame_locator('iframe[name="iframe_Roundtrip_9223372036563636042"]').get_by_role(
                "link", name="Variabelskærm"
            ).click()

        if page:
            page.close()
        if context:
            context.close()
        if browser:
            browser.close()


if downloadmode == 1:
    download_all_anshistorik_from_ri(df=df, folder_data_session=folder_data_session)


def parse_ri_html_report_to_dataframe(mhtml_path) -> None:
    """
    Parses an mhtml file downloaded from Rollobaseret Indgang.
    The default download calls the file xls, but it is a kind of html file.

    ## Usage
    mhtml_path = Path(folder_data_session / 'test.html')

    df_mhtml = parse_ri_html_report_to_dataframe(mhtml_path)
    """
    # Read MHTML file
    with open(mhtml_path, encoding="utf-8") as file:
        content = file.read()

    # Find the HTML part of the file
    matches = re.search(r"<html.*<\/html>", content, re.DOTALL)
    if not matches:
        msg = "No HTML content found in the file"
        raise ValueError(msg)
    html_content = matches.group(0)

    # Parse the HTML content using BeautifulSoup
    soup = BeautifulSoup(html_content, features="html.parser")  # "html.parser"

    # Find all tables within the parsed HTML
    tables = soup.find_all("table")
    if not tables:
        msg = "No tables found in the HTML content"
        raise ValueError(msg)

    last_table = tables[-1]

    if "Ingen data fundet til visning" in str(last_table):
        return pd.DataFrame()
    # Convert the largest HTML table to a pandas DataFrame
    try:
        # returns a list of DataFrames
        df_mhtml = pd.read_html(io.StringIO(str(last_table)), decimal=",", thousands=".", header=None)
    except Exception:
        msg = "Failed to parse the last table into a DataFrame"
        logger.error(msg, exc_info=True)

    df_mhtml = df_mhtml[0]
    df_mhtml.columns = df_mhtml.iloc[0]
    df_mhtml = df_mhtml.drop(0)
    df_mhtml.reset_index(drop=True, inplace=True)
    df_mhtml.rename(columns={"Slut F-periode": "date", "Lønart": "lonart", "Antal": "antal"}, inplace=True)

    # Convert 'date' column to datetime
    df_mhtml["date"] = pd.to_datetime(df_mhtml["date"], format="%d%m%Y")
    df_mhtml["antal"] = pd.to_numeric(df_mhtml["antal"])
    return df_mhtml


def process_all_anshistorik(folder_data_session, df):
    """
    Mere end 12 -> True
    Mindre end 12 -> False
    """
    df["hourly_more_than_12_months"] = ""  # Initialize the column in df. TODO: test with empty string init.

    for cpr in df["cprnr"]:
        # parse and read
        mhtml_path = Path(folder_data_session / f"anshistorik_{cpr}.mhtml")
        anshistorik = parse_ri_html_report_to_dataframe(mhtml_path)

        if anshistorik is not None and not anshistorik.empty:
            # create a new dataframe from anshistorik where rows are aggregated
            # into months and the antal column is summed pr month.
            anshistorik["year_month"] = anshistorik["date"].dt.to_period("M")
            anshistorik_grouped = anshistorik.groupby("year_month")["antal"].sum().reset_index()

            # Filter rows where antal > 34,67
            monthly_hour_threshhold = 34.67
            filtered_anshistorik_grouped = anshistorik_grouped[anshistorik_grouped["antal"] > monthly_hour_threshhold]

            # boolean value
            eight_year_month_threshhold = 12
            hourly_more_than_12_months = len(filtered_anshistorik_grouped) > eight_year_month_threshhold

            df.loc[df["cprnr"] == cpr, "hourly_more_than_12_months"] = hourly_more_than_12_months
        else:
            df.loc[df["cprnr"] == cpr, "hourly_more_than_12_months"] = False

    return df


df = process_all_anshistorik(folder_data_session=folder_data_session, df=df)


load_dotenv(override=True)
cpr = os.getenv("CPR")


# ---------------------------------------------------------------------------- #
#                       Beregning af timeantal pr. måned                       #
# ---------------------------------------------------------------------------- #

# -------------- Beregning af timeantal - månedslønsansættelser -------------- #
# SLide 15
# Bruger df_ansforhold (opus) - komplet ift docs

# --------------- Beregning af timeantal - timelønsansættelser --------------- #
# Slide 16
# Bruger anshistorik (RI) - mangelful ift docs
