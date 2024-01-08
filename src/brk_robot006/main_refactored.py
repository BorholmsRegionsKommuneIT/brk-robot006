"""
Robot006
"""

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

bestillingsnavn = robot_name + "_" + datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%d%H%M%S")
folder_data_session = Path(folder_data / bestillingsnavn)
session = login.start_opus(pam_path, robot_name, sapshcut_path)


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


download_report(folder_data, bestillingsnavn, folder_data_session, session)


def return_to_start_view() -> None:
    """
    Press Back 3 times to go to Vis personalestamdata, where data from the downloaded report, will we pasted in.
    """
    for _ in range(3):
        session.findById("wnd[0]/tbar[0]/btn[3]").press()
        time.sleep(0.5)

    session.findById("wnd[0]/usr/cntlIMAGE_CONTAINER/shellcont/shell/shellcont[0]/shell").doubleClickNode("F00004")


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
df = df[:20]
# --------------------------------- END TEMP --------------------------------- #


def validate_dataframe_col_number(dataframe, col_number, dataframe_name):
    cols = dataframe.shape[1]
    try:
        if cols != col_number:
            raise ValueError(f"{dataframe_name} has wrong number of columns: expected {col_number}, found {cols}")
        logger.info(f"Validation successful: {dataframe_name} has the expected number of columns: {col_number}")
    except ValueError as e:
        logger.error(f"Validation failed: {e}")


validate_dataframe_col_number(df, 15, 'df')

# Creating the result DataFrame, which will contain all Boolean vectors corresponding to the questions in the documentation flowchart
result = df[['manummer']].copy()


# ---------------------------------------------------------------------------- #
#                      Har medarbejder pension i forvejen                      #
# ---------------------------------------------------------------------------- #
def har_medarbejder_pension_i_forvejen(df: pd.DataFrame, result: pd.DataFrame, manummer_column: str) -> pd.DataFrame:
    """
    Adds a boolean column to the 'result' DataFrame indicating if the employee,
    identified by the 'manummer' column, is created with pension. This is based
    on conditions in the provided DataFrame 'df'.

    Parameters:
    df (pd.DataFrame): The DataFrame containing employee data with 'pensberegnkode', 'samletpct', and 'manummer' columns.
    result (pd.DataFrame): The DataFrame to which the new column will be added.
    manummer_column (str): The name of the column in both DataFrames that contains employee IDs.

    Returns:
    pd.DataFrame: The 'result' DataFrame with an added boolean column 'har_pension'.
    """
    # Ensure both DataFrames contain the manummer column
    if manummer_column not in df.columns or manummer_column not in result.columns:
        raise ValueError(f"The DataFrame must contain the '{manummer_column}' column.")

    # Check if required columns exist in df
    if 'pensberegnkode' in df.columns and 'samletpct' in df.columns:
        # Create a temporary DataFrame for the merge operation
        temp_df = df[[manummer_column, 'pensberegnkode', 'samletpct']].copy()
        temp_df['har_pension'] = (temp_df["pensberegnkode"] == "1") & (temp_df["samletpct"] > 0.00)
        temp_df['har_pension_0_pct'] = (temp_df["pensberegnkode"] == "1") & (temp_df["samletpct"] == 0.00)

        # Merge the result DataFrame with the calculated column from the temporary DataFrame
        result = result.merge(temp_df[[manummer_column, 'har_pension']], on=manummer_column, how='left')
        result = result.merge(temp_df[[manummer_column, 'har_pension_0_pct']], on=manummer_column, how='left')
    else:
        raise ValueError("The DataFrame must contain 'pensberegnkode' and 'samletpct' columns.")

    return result


result = har_medarbejder_pension_i_forvejen(df, result, 'manummer')


# ---------------------------------------------------------------------------- #
#                            Er medarbejder under 21                           #
# ---------------------------------------------------------------------------- #
def _calculate_age(fodselsdag_str):
    fodselsdag = datetime.datetime.strptime(fodselsdag_str, "%d%m%y")
    today = datetime.datetime.today()
    if fodselsdag.year > today.year:
        fodselsdag = fodselsdag.replace(year=fodselsdag.year - 100)
    days_difference = (today - fodselsdag).days
    age = days_difference // 365.25
    return age


# Use new approach
def er_medarbejder_under_21(df: pd.DataFrame, result: pd.DataFrame, manummer_column: str) -> pd.DataFrame:
    """
    Adds a boolean column to the 'result' DataFrame indicating if the employee,
    identified by the 'manummer' column, is under the age of 21.

    Parameters:
    df (pd.DataFrame): The DataFrame containing employee data with 'cprnr' column.
    result (pd.DataFrame): The DataFrame to which the new column will be added.
    manummer_column (str): The name of the column in both DataFrames that contains employee IDs.

    Returns:
    pd.DataFrame: The 'result' DataFrame with an added boolean column 'er_under_21'.
    """
    # Create a temporary DataFrame to avoid modifying the original df
    temp_df = df[[manummer_column, 'cprnr']].copy()

    # Convert CPR number to birthdate and calculate age in the temp_df
    temp_df["fodselsdato"] = temp_df["cprnr"].str[0:6]
    temp_df["alder"] = temp_df["fodselsdato"].apply(_calculate_age)  # Assuming _calculate_age is a predefined function

    # Add 'er_under_21' column to temp_df
    temp_df['er_under_21'] = temp_df["alder"] < 21

    # Merge the result DataFrame with the calculated column from temp_df
    result = result.merge(temp_df[[manummer_column, 'er_under_21']], on=manummer_column, how='left')

    return result


result = er_medarbejder_under_21(df, result, 'manummer')


# ---------------------------------------------------------------------------- #
#               Er medarbejder oprettet med pension på månedsløn               #
# ---------------------------------------------------------------------------- #

# ----------- Download individuelle ansættelsesforløb som csv filer ---------- #


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


manummer_list = (df["manummer"]).tolist()


def download_all_ansforhold(manummer_list: list, folder_data_session: Path, bestillingsnavn: str, session) -> None:
    for manummer in manummer_list:
        try:
            # Download data for each manummer
            download_single_ansforhold(manummer, folder_data_session, bestillingsnavn, session)
        except Exception as e:
            logger.error(f"Error downloading ansforhold for manummer {manummer}: {e}")
            # Continue with the next iteration
            continue


download_all_ansforhold(manummer_list, folder_data_session, bestillingsnavn, session)


# ------------------ Funktion til at læse ansættelsesforløb ------------------ #
def read_single_ansforhold(manummer: str, folder_data_session: Path, bestillingsnavn: str) -> pd.DataFrame:
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

    for manummer in manummer_list:
        try:
            # Read and process the downloaded data
            df_ansforhold = read_single_ansforhold(manummer, folder_data_session, bestillingsnavn)

            validate_dataframe_col_number(df_ansforhold, 20, 'df_ansforhold')

            # Filter and sort the DataFrame
            df_filtered = filter_df_ansforhold(df_ansforhold)
            df_sorted = sort_df_filtered(df_filtered)
            # Append the sorted DataFrame to the list
            if df_sorted.columns[0] is np.nan:
                df_sorted = df_sorted.drop(df_sorted.columns[0], axis=1)
            all_rows.append(df_sorted)

            # Create a temporary DataFrame for the merge operation
            temp_df = df[[manummer_column]].copy()

            # Append True or False to temp_df depending on if df_sorted has exactly one row
            temp_df['oprettet_pension_maaned'] = len(df_sorted) == 1

        except Exception as e:
            logger.error(f"Error processing manummer {manummer}: {e}")
            # Continue with the next iteration
            continue
    # Merge
    result = pd.merge(result, temp_df[['manummer', 'oprettet_pension_maaned']], on='manummer', how='left')
    # Concatenate all single-row DataFrames into one DataFrame
    all_rows = pd.concat(all_rows, ignore_index=False)
    return result


result = process_all_ansforhold(
    df=df,
    result=result,
    manummer_list=manummer_list,
    folder_data_session=folder_data_session,
    bestillingsnavn=bestillingsnavn,
    manummer_column='manummer',
)


# --------------------------------- debugging -------------------------------- #
# df_ansforhold_59433 = read_single_ansforhold('59433', folder_data_session, bestillingsnavn)
# df_filtered_59433 = filter_df_ansforhold(df_ansforhold)
# df_sorted_59433 = sort_df_filtered(df_filtered)

# oprettet_pension_maaned.to_csv(
#    path_or_buf=Path(folder_data_session / "oprettet_pension_maaned.csv"), index=False, encoding='utf-8'
# )
