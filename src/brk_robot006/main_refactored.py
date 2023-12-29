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


def download_rapport(folder_data, bestillingsnavn, folder_data_session, session) -> None:
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


download_rapport(folder_data, bestillingsnavn, folder_data_session, session)


def return_to_start_view() -> None:
    """
    Press Back 3 times to go to Vis personalestamdata, where data from the downloaded report, will we pasted in.
    """
    for _ in range(3):
        session.findById("wnd[0]/tbar[0]/btn[3]").press()
        time.sleep(0.5)

    session.findById("wnd[0]/usr/cntlIMAGE_CONTAINER/shellcont/shell/shellcont[0]/shell").doubleClickNode("F00004")


return_to_start_view()


def import_rapport(folder_data_session: Path, bestillingsnavn: str) -> pd.core.frame.DataFrame:
    column_names = [
        "Startdato",
        "Stopdato",
        "Manummer",
        "Sagsbehandler",
        "Orgkort",
        "Orgbetegn",
        "Cpr",
        "Navn",
        "Ansdato",
        "Ansforhold",
        "Makreds",
        "Lonkls",
        "Pensberegnkode",
        "Penskassenr",
        "Samletpct",
    ]
    data_types = defaultdict(lambda: "str")

    #  Read the report into a dataframe
    report_path = folder_data_session / f"{bestillingsnavn}.csv"

    df = pd.read_csv(
        filepath_or_buffer=report_path,
        sep="\t",
        header=None,
        names=column_names,
        encoding="windows-1252",
        dtype=data_types,
        skiprows=15,
        usecols=[1, *range(3, 17)],
    )

    df["Samletpct"] = df["Samletpct"].str.replace(",", ".").astype(float)

    return df


df = import_rapport(folder_data_session=folder_data_session, bestillingsnavn=bestillingsnavn)


def er_medarbejder_oprettet_med_pension(manummer_series: pd.core.series.Series) -> pd.Series.bool:
    """
    er_medarbejder_oprettet_med_pension(df['Manummer'])
    Returns a boolean series with True if the employee is created with pension.
    """
    oprettet_med_pension = (df["Pensberegnkode"] == "1") & (df["Samletpct"] > 0.00)
    return oprettet_med_pension


oprettet_med_pension = er_medarbejder_oprettet_med_pension(df['Manummer'])


def er_medarbejder_oprettet_med_0_pct_pension(manummer_series: pd.core.series.Series) -> pd.Series.bool:
    """
    er_medarbejder_oprettet_med_0_pct_pension(df['Manummer'])
    Returns a boolean series with True if the employee is created with 0 pct pension.
    """
    oprettet_med_0_pct_pension = (df["Pensberegnkode"] == "1") & (df["Samletpct"] == 0.00)
    return oprettet_med_0_pct_pension


oprettet_med_0_pct_pension = er_medarbejder_oprettet_med_0_pct_pension(df['Manummer'])


def _calculate_age(fodselsdag_str):
    fodselsdag = datetime.datetime.strptime(fodselsdag_str, "%d%m%y")
    today = datetime.datetime.today()
    if fodselsdag.year > today.year:
        fodselsdag = fodselsdag.replace(year=fodselsdag.year - 100)
    days_difference = (today - fodselsdag).days
    age = days_difference // 365.25
    return age


def er_medarbejder_under_21(manummer_series: pd.core.series.Series) -> bool:
    df["Fodselsdato"] = df["Cpr"].str[0:6]

    df["Alder"] = df["Fodselsdato"].apply(_calculate_age)

    max_alder = 21

    er_under_21 = df["Alder"] < max_alder

    return er_under_21


er_under_21 = er_medarbejder_under_21(df['Manummer'])


def _download_ansforhold(manummer: str, folder_data_session: Path, bestillingsnavn: str, session):
    """
    function to download ansaettelsesforloeb for a given manummer
    """
    session.findById("wnd[0]/usr/subSUBSCR_PERNR:SAPMP50A:0110/ctxtRP50G-PERNR").text = manummer
    # press ansaettelsesforloeb
    session.findById("wnd[0]/tbar[1]/btn[31]").press()
    ## Gem liste i fil
    # Click on lokal fil
    session.findById("wnd[0]/tbar[1]/btn[45]").press()
    # choose regneark
    session.findById("wnd[1]/usr/subSUBSCREEN_STEPLOOP:SAPLSPO5:0150/sub:SAPLSPO5:0150/radSPOPLI-SELFLAG[1,0]").select()
    session.findById(
        "wnd[1]/usr/subSUBSCREEN_STEPLOOP:SAPLSPO5:0150/sub:SAPLSPO5:0150/radSPOPLI-SELFLAG[1,0]"
    ).setFocus()
    # click checkmark
    session.findById("wnd[1]/tbar[0]/btn[0]").press()
    time.sleep(0.5)
    # Save in folder_data_session
    # dir
    session.findById("wnd[1]/usr/ctxtDY_PATH").text = str(folder_data_session)
    # Filename
    filename = bestillingsnavn + "_" + manummer + ".csv"
    session.findById("wnd[1]/usr/ctxtDY_FILENAME").text = str(filename)
    # generer
    session.findById("wnd[1]/usr/ctxtDY_FILENAME").caretPosition = 15
    session.findById("wnd[1]/tbar[0]/btn[0]").press()
    # click back to "Vis personalestamdata"
    session.findById("wnd[0]/tbar[0]/btn[3]").press()


manummer_list = (df["Manummer"]).str.strip().tolist()
manummer_list = manummer_list[:1]


def download_ansforhold_for_all_medarbejdere(manummer_list: list) -> None:
    for manummer in manummer_list:
        _download_ansforhold(manummer)
        time.sleep(1)


download_ansforhold_for_all_medarbejdere(manummer_list)


def read_ansforhold(folder_data_session: Path, manummer: str, bestillingsnavn: str) -> pd.core.frame.DataFrame:
    column_names_df_manummer = [
        "Empty",
        "Manummer",
        "Startdato",
        "Stopdato",
        "Reduktionskode",
        "Stilling",
        "Aktivitetsorgsbet",
        "Orgpla",
        "Ansforhold",
        "Medbkreds",
        "Taeller",
        "Lonkls",
        "Lonklbet",
        "Erfadato",
        "Lonancdato",
        "Penskassenr",
        "Tiltkon",
        "Datftilt",
        "Grundltrin",
        "Berlontrin",
        "Betaktart",
    ]

    data_types = defaultdict(lambda: "str")

    report_ans_forlob = folder_data_session / f"{bestillingsnavn}_{manummer}.csv"

    df_ansforhold = pd.read_csv(
        filepath_or_buffer=report_ans_forlob,
        sep="\t",
        header=None,
        names=column_names_df_manummer,
        encoding="windows-1252",
        skiprows=5,
        dtype=data_types,
    )

    df_ansforhold.drop("Empty", axis=1, inplace=True)

    return df_ansforhold


def filter_df_ansforhold(df):
    pass


# Filter data frames in df_manummer_list,
# so Ansforhold == 01 AND Penskassenr is different from NaN.
# then find the row with earliest Startdato

for manummer in manummer_list:
    read_ansforhold(folder_data_session, manummer, bestillingsnavn)
    # filter_df_ansforhold()
    # sort()


def er_medarbejder_oprettet_med_pension_paa_maanedsloen(manummer) -> bool:
    pass
