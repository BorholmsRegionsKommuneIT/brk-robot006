"""
Robot006
"""

# Libs
import datetime
import getpass

# what is this: from http.client import TEMPORARY_REDIRECT
import os

import time
from collections import defaultdict  # to dtype all vars at once
from pathlib import Path
import shutil

import brk_rpa_utils  # github
import numpy as np
import pandas as pd
from loguru import logger
from playwright.sync_api import Playwright, sync_playwright
from dotenv import load_dotenv
import pandas as pd
from helium import *
from selenium.webdriver import Edge, Chrome
import time
import os


# settings and initializations
logger.info("start")
user = getpass.getuser()
if user == 'robot006':
    load_dotenv()
folder_data = Path(os.getenv("FOLDER_DATA"))
sapshcut_path = Path(os.getenv("SAPSHCUT_PATH"))
pam_path = os.getenv("PAM_PATH")
ri_url = os.getenv("RI_URL")


bestillingsnavn = user + "_" + datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%d%H%M%S")
folder_data_session = Path(folder_data / bestillingsnavn)
session = brk_rpa_utils.start_opus(pam_path, user, sapshcut_path)


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


def generate_report(file_path: str):
    df = pd.read_csv(file_path)
    return df


if user == 'robot006':
    download_report(folder_data, bestillingsnavn, folder_data_session, session)
else:
    df = generate_report(file_path="https://raw.githubusercontent.com/dzgreen/datasets/main/starwars.csv")


def return_to_start_view() -> None:
    """
    Press Back 3 times to go to Vis personalestamdata, where data from the downloaded report, will we pasted in.
    """
    for _ in range(3):
        session.findById("wnd[0]/tbar[0]/btn[3]").press()
        time.sleep(0.5)

    session.findById("wnd[0]/usr/cntlIMAGE_CONTAINER/shellcont/shell/shellcont[0]/shell").doubleClickNode("F00004")


if user == 'robot006':
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
        df = df.dropna(axis=1, how='all')
        df.columns = df.columns.str.lower().str.replace('[-.,1æøå ]', '', regex=True)
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
df_obj = df.select_dtypes(['object'])
df[df_obj.columns] = df_obj.apply(lambda x: x.str.strip())

# ----------------------------------- TEMP ----------------------------------- #
df = df[:5]
# --------------------------------- END TEMP --------------------------------- #

# --------- Get df row count that must persist throughout the session -------- #

persistent_df_row_count = len(df)


def validate_dataframe(dataframe, col_count, row_count=None, dataframe_name="", manummer_column=""):
    cols = dataframe.shape[1]
    try:
        # Column count validation
        if cols != col_count:
            raise ValueError(f"{dataframe_name} has wrong number of columns: expected {col_count}, found {cols}")
        logger.info(f"Validation successful: {dataframe_name} has the expected number of columns: {col_count}")

        # Row count validation (only if row_count is provided)
        if row_count is not None:
            rows = len(dataframe)
            if rows != row_count:
                raise ValueError(f"{dataframe_name} has wrong number of rows: expected {row_count}, found {rows}")
            logger.info(f"Validation successful: {dataframe_name} has the expected number of rows: {row_count}")

        # Check if the manummer_column exists
        if manummer_column and manummer_column not in dataframe.columns:
            raise ValueError(f"{dataframe_name} must contain the '{manummer_column}' column.")

    except ValueError as e:
        logger.error(f"Validation failed: {e}")


validate_dataframe(
    dataframe=df, col_count=15, row_count=persistent_df_row_count, dataframe_name='df', manummer_column='manummer'
)


# ---------------------------------------------------------------------------- #
#                      Har medarbejder pension i forvejen                      #
# ---------------------------------------------------------------------------- #
def har_medarbejder_pension_i_forvejen(df: pd.DataFrame) -> pd.DataFrame:
    """
    Adds 2 boolean columns to 'DataFrame' indicating if the employee,
    identified by the 'manummer' column, is created with pension.

    Parameters:
    DataFrame (pd.DataFrame): The DataFrame containing employee data with 'pensberegnkode', 'samletpct', and 'manummer' columns.
    manummer_column (str): The name of the column in both DataFrames that contains employee IDs.

    Returns:
    pd.DataFrame: df with an added boolean column 'har_pension' and 'har_pension_0_pct'.
    """

    # Check if required columns exist in df
    if 'pensberegnkode' in df.columns and 'samletpct' in df.columns:
        df['har_pension'] = (df["pensberegnkode"] == "1") & (df["samletpct"] > 0.00)
        df['har_pension_0_pct'] = (df["pensberegnkode"] == "1") & (df["samletpct"] == 0.00)
    else:
        raise ValueError("The DataFrame must contain 'pensberegnkode' and 'samletpct' columns.")

    return df


df = har_medarbejder_pension_i_forvejen(df)

validate_dataframe(
    dataframe=df, col_count=17, row_count=persistent_df_row_count, dataframe_name='df', manummer_column='manummer'
)


# ---------------------------------------------------------------------------- #
#                            Er medarbejder under 21                           #
# ---------------------------------------------------------------------------- #
def _calculate_age(cpr: str) -> int:
    """
    Returns age from cpr number
    """
    fodselsdag_str = cpr[:6]
    fodselsdag = datetime.datetime.strptime(fodselsdag_str, "%d%m%y")
    today = datetime.datetime.today()
    if fodselsdag.year > today.year:
        fodselsdag = fodselsdag.replace(year=fodselsdag.year - 100)
    days_difference = (today - fodselsdag).days
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
    if 'cprnr' not in df.columns:
        raise ValueError("The DataFrame must contain the 'cprnr' column.")

    # Add 'er_under_21' column to df
    df['er_under_21'] = df['cprnr'].apply(_calculate_age) < 21

    return df


df = er_medarbejder_under_21(df)

validate_dataframe(
    dataframe=df, col_count=18, row_count=persistent_df_row_count, dataframe_name='df', manummer_column='manummer'
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


def download_all_ansforhold(
    df: pd.DataFrame,
    folder_data_session: Path,
    bestillingsnavn: str,
    session,
) -> None:
    manummer_list = (df["manummer"]).tolist()

    for manummer in manummer_list:
        try:
            # Download data for each manummer
            download_single_ansforhold(manummer, folder_data_session, bestillingsnavn, session)
        except Exception as e:
            logger.error(f"Error downloading ansforhold for manummer {manummer}: {e}")
        # Continue with the next iteration
        continue


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
        df_ansforhold.columns = df_ansforhold.columns.str.lower().str.replace('[-.,1æøå ]', '', regex=True)
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
def process_all_ansforhold(
    df: pd.DataFrame,
    result: pd.DataFrame,
    manummer_list: list,
    folder_data_session: Path,
    bestillingsnavn: str,
    manummer_column: str,
) -> pd.DataFrame:
    """
    loops over manummer_list and runs all the single functions
    """
    global all_rows
    all_rows = []  # List to store the single-row DataFrames, mostly for debugging purposes

    # Create a temporary DataFrame for the merge operation
    temp_df = df[[manummer_column]].copy()
    temp_df['oprettet_pension_maaned'] = False

    for manummer in manummer_list:
        try:
            # Read and process the downloaded data
            df_ansforhold = read_single_ansforhold(manummer, folder_data_session, bestillingsnavn)

            validate_dataframe(df_ansforhold, 20, 'df_ansforhold')

            # Filter and sort the DataFrame
            df_filtered = filter_df_ansforhold(df_ansforhold)
            df_sorted = sort_df_filtered(df_filtered)

            # Append the sorted DataFrame to the list
            if df_sorted.columns[0] is np.nan:
                df_sorted = df_sorted.drop(df_sorted.columns[0], axis=1)
            all_rows.append(df_sorted)

            bull = len(df_sorted) == 1
            # Append True or False to temp_df depending on if df_sorted has exactly one row
            temp_df.loc[temp_df[manummer_column] == manummer, 'oprettet_pension_maaned'] = bull

        except Exception as e:
            logger.error(f"Error processing manummer {manummer}: {e}")
            # Continue with the next iteration
            continue
    # Merge
    result = pd.merge(
        result,
        temp_df[['manummer', 'oprettet_pension_maaned']],
        on='manummer',
        how='left',
    )
    # Concatenate all single-row DataFrames into one DataFrame
    all_rows = pd.concat(all_rows, ignore_index=False)
    return result


def process_all_ansforhold(
    df: pd.DataFrame,
    folder_data_session: Path,
    bestillingsnavn: str,
) -> pd.DataFrame:
    """
    Loops over manummer_list and runs all the single functions.
    """
    global all_rows
    all_rows = []  # List to store the single-row DataFrames, mostly for debugging purposes
    manummer_list = (df["manummer"]).tolist()
    df['oprettet_pension_maaned'] = False  # Initialize the column in df

    for manummer in manummer_list:
        try:
            # Read and process the downloaded data
            df_ansforhold = read_single_ansforhold(manummer, folder_data_session, bestillingsnavn)

            validate_dataframe(
                dataframe=df_ansforhold,
                col_count=20,
                dataframe_name='df_ansforhold',
                manummer_column='manr',
            )
            # Filter and sort the DataFrame
            df_filtered = filter_df_ansforhold(df_ansforhold)
            df_sorted = sort_df_filtered(df_filtered)

            # Append the sorted DataFrame to the list
            if df_sorted.columns[0] is np.nan:
                df_sorted = df_sorted.drop(df_sorted.columns[0], axis=1)
            all_rows.append(df_sorted)

            bull = len(df_sorted) == 1
            # Update df directly depending on if df_sorted has exactly one row
            df.loc[df['manummer'] == manummer, 'oprettet_pension_maaned'] = bull

        except Exception as e:
            logger.error(f"Error processing manummer {manummer}: {e}")
            # Continue with the next iteration
            continue

    # Concatenate all single-row DataFrames into one DataFrame
    all_rows = pd.concat(all_rows, ignore_index=False)

    return df


df = process_all_ansforhold(
    df=df,
    folder_data_session=folder_data_session,
    bestillingsnavn=bestillingsnavn,
)

validate_dataframe(
    dataframe=df, col_count=19, row_count=persistent_df_row_count, dataframe_name='df', manummer_column='manummer'
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
def download_single_anshistorik_from_ri(cpr: str, folder_data_session: Path) -> None:
    """
    try https://github.com/mherrmann/helium
    """
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
            ri = brk_rpa_utils.start_ri(pam_path, user, ri_url, playwright)
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
                download_path = Path(folder_data_session / f"anshistorik_{cpr}.mhtml")
                download.save_as(download_path)

            except Exception as e:
                logger.error("An error occurred during page interactions", exc_info=True)
                print(f"An error occurred during page interactions: {e}")

            finally:
                if page:
                    page.close()
                if context:
                    context.close()
                if browser:
                    browser.close()

    except Exception as e:
        logger.error("An error occurred during playwright setup", exc_info=True)
        print(f"An error occurred during playwright setup: {e}")


def process_all_anshistorik(folder_data_session, df):
    """
    Mere end 12 -> True
    Mindre end 12 -> False
    """
    df['hourly_more_than_12_months'] = False  # Initialize the column in df

    for cpr in df['cprnr']:
        # download single
        download_single_anshistorik_from_ri(cpr, folder_data_session)

        # parse and read
        mhtml_path = Path(folder_data_session / f"anshistorik_{cpr}.mhtml")
        anshistorik = brk_rpa_utils.parse_ri_html_report_to_dataframe(mhtml_path)

        # create a new dataframe from anshistorik where rows are aggregated
        # into months and the antal column is summed pr month.
        anshistorik['year_month'] = anshistorik['date'].dt.to_period('M')
        anshistorik_grouped = anshistorik.groupby('year_month')['antal'].sum().reset_index()

        # Filter rows where antal > 34,67
        filtered_anshistorik_grouped = anshistorik_grouped[anshistorik_grouped['antal'] > 34.67]

        # boolean value
        hourly_more_than_12_months = len(filtered_anshistorik_grouped) > 12

        df.loc[df['cprnr'] == cpr, 'hourly_more_than_12_months'] = hourly_more_than_12_months

    return df


df = process_all_anshistorik(folder_data_session=folder_data_session, df=df)

df.to_csv(folder_data_session / "output.csv", index=False)


# download af historik for et enkelt cpr nummer
# load mhtml som dataframe
# gem som csv
# filter, groupby, summarise, count rows
# append row_count to result
# Kør forrige punkter i et loop for alle cpr numre
