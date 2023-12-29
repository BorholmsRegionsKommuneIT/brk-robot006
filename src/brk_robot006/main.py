"""
Robot006
"""


import datetime
import getpass
import os

# import socket
import time
from collections import defaultdict  # to dtype all vars at once
from pathlib import Path

import brk_rpa_utils as login
import pandas as pd
from loguru import logger
from playwright.sync_api import sync_playwright
from dotenv import load_dotenv

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


def opus_report(folder_data, bestillingsnavn, folder_data_session, session):
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

    #  Press Back 3 times to go to "Vis personalestamdata", where data from the downloaded
    #  report will we pasted in.

    for _ in range(3):
        session.findById("wnd[0]/tbar[0]/btn[3]").press()
        time.sleep(0.5)

    session.findById("wnd[0]/usr/cntlIMAGE_CONTAINER/shellcont/shell/shellcont[0]/shell").doubleClickNode("F00004")

    return folder_data_session


opus_report(folder_data, bestillingsnavn, folder_data_session, session)


def pension_i_forvejen(folder_data_session, bestillingsnavn):
    """
    Har medarbejder pension i forvejen
    Er medarbejderen under 21 aar
    Er medarbejder oprettet med pension paa maanedsloen (performs a download and read of all ansaettelsesforloeb)
    """
    #  Define column names and data types
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
    data_types = {
        "Startdato": "string",
        "Stopdato": "string",
        "Manummer": "string",
        "Sagsbehandler": "string",
        "Orgkort": "string",
        "Orgbetegn": "string",
        "Cpr": "string",
        "Navn": "string",
        "Ansdato": "string",
        "Ansforhold": "string",
        "Makreds": "string",
        "Lonkls": "string",
        "Pensberegnkode": "object",
        "Penskassenr": "string",
        "Samletpct": "object",
    }

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

    #  Make a note column and fill out
    # "Har medarbejder pension i forvejen"
    # Add column "Note" to df with the value Nan, to write all the resutls to.
    df["Note"] = ""

    # If Pensberegnkode = "1" AND Samletpct > "0,00", then change value of Note to
    # ”Medarbejder er oprettet med pension”
    if df["Samletpct"].dtype == object:
        # If it's a string, replace commas with periods
        df["Samletpct"] = df["Samletpct"].str.replace(",", ".").astype(float)

    df.loc[(df["Pensberegnkode"] == "1") & (df["Samletpct"] > 0.00), "Note"] = "Medarbejder er oprettet med pension"

    # If Pensberegnkode = "1" AND Samletpct = "0,00", then change value of Note to
    # ”Medarbejder er allerede oprettet med pension men der indbetales 0 procent” else NaN
    df.loc[(df["Pensberegnkode"] == "1") & (df["Samletpct"] == 0.00), "Note"] = "0 pct pension oprettet"

    return df


df = pension_i_forvejen(folder_data_session, bestillingsnavn)


def find_alder(df):
    #  Create alder column
    # "Er medarbejderen under 21 aar"
    # Make a new column fodselsdag based on CPR.
    df["Fodselsdato"] = df["Cpr"].str[0:6]

    # function to calculate age from fodselsdag
    def calculate_age(fodselsdag_str):
        fodselsdag = datetime.datetime.strptime(fodselsdag_str, "%d%m%y")
        today = datetime.datetime.today()
        if fodselsdag.year > today.year:
            fodselsdag = fodselsdag.replace(year=fodselsdag.year - 100)
        days_difference = (today - fodselsdag).days
        age = days_difference // 365.25
        return age

    # apply the function
    df["Alder"] = df["Fodselsdato"].apply(calculate_age)

    #  If alder < 21, then change value of Note to ”Medarbejder er under 21 aar”
    # "Er medarbejderen under 21 aar"
    alder = 21
    df.loc[df["Alder"] < alder, "Note"] = "Medarbejder er under 21 aar"

    return df


df = find_alder(df)


def er_der_pension_paa_maanedsloen(bestillingsnavn, folder_data_session, df, session):
    #  "Er medarbejder oprettet med pension paa maanedsloen"

    # Download all ansaettelsesforloeb into files

    # Create a list of manummer to look up and strip whitespace
    manummer_list = [s.strip() for s in df.loc[df["Note"] == "", "Manummer"].tolist()]

    # temp
    manummer_list = manummer_list[:1]

    # Define a function that takes manummer as parameter and downloads ansaettelsesforloeb to
    # folder_data_session, with name Filename
    def download_ansforl(manummer):
        manummer = manummer.strip()
        session.findById("wnd[0]/usr/subSUBSCR_PERNR:SAPMP50A:0110/ctxtRP50G-PERNR").text = manummer
        # press ansaettelsesforloeb
        session.findById("wnd[0]/tbar[1]/btn[31]").press()
        ## Gem liste i fil
        # Click on lokal fil
        session.findById("wnd[0]/tbar[1]/btn[45]").press()
        # choose regneark
        session.findById(
            "wnd[1]/usr/subSUBSCREEN_STEPLOOP:SAPLSPO5:0150/sub:SAPLSPO5:0150/radSPOPLI-SELFLAG[1,0]"
        ).select()
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

    # Download everything
    for manummer in manummer_list:
        download_ansforl(manummer)
        time.sleep(1)

    # Read all data frame into a list
    # "Er medarbejder oprettet med pension paa maanedsloen"
    # define column names for the data frame to be read in next step
    ## Read the files into pandas data frames and store the data frames in a list

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

    df_manummer_dict = {}
    for manummer in manummer_list:
        report_ans_forlob = folder_data_session / f"{bestillingsnavn}_{manummer}.csv"

        df_ansforl = pd.read_csv(
            filepath_or_buffer=report_ans_forlob,
            sep="\t",
            header=None,
            names=column_names_df_manummer,
            encoding="windows-1252",
            skiprows=5,
            dtype=data_types,
        )

        df_ansforl.drop("Empty", axis=1, inplace=True)

        df_manummer_dict[manummer] = df_ansforl

    # test
    # df_manummer_dict["64569"].loc[6, "Penskassenr"] = 12345

    #  Filter all the df's
    # "Er medarbejder oprettet med pension paa maanedsloen" slide 11.

    # Filter all data frames in df_manummer_list,
    # so Ansforhold == 01 AND Penskassenr is different from NaN.
    # then find the row with earliest Startdato

    df_filtered_dict = {}

    for manummer, df_iter in df_manummer_dict.items():
        df_iter["Startdato"] = pd.to_datetime(df_iter["Startdato"], format="%d.%m.%Y")

        df_filtered = df_iter.loc[
            (df_iter["Ansforhold"] == "01")
            & (df_iter["Penskassenr"] != "30201")
            & (df_iter["Penskassenr"] != "30399")
            & (df_iter["Penskassenr"] != "30210")
            & (df_iter["Penskassenr"] != "39999")
            & (df_iter["Penskassenr"].notna())
        ].copy()  # The copy() function is used to create a new DataFrame instead of a view on the existing one.

        df_filtered = df_filtered.sort_values(by=["Startdato"])

        if not df_filtered.empty:
            df_filtered = df_filtered.iloc[0]

        df_filtered_dict[manummer] = df_filtered

    # For all filtered data frames in df_manummer_dict,
    # write "Medarbejder har maanedsloen med pension pr" under df["Note"], where
    # the key in df_manummer_dict match df["Manummer"]

    # Pesky little whitespace
    df["Manummer"] = df["Manummer"].str.strip()
    df_filtered_dict = {k.strip(): v for k, v in df_filtered_dict.items()}

    """
    for manummer, df_iter in df_filtered_dict.items():
        if not df_iter.empty:
            df.loc[
                df["Manummer"] == manummer, "Note"
            ] = "Medarbejder har maanedsloen med pension pr"
    """

    for manummer, df_iter in df_filtered_dict.items():
        if not df_iter.empty:
            df.loc[df["Manummer"] == manummer, "Note"] = "Medarbejder har maanedsloen med pension pr " + df_iter[
                "Startdato"
            ].strftime("%d.%m.%Y")
    return df


df = er_der_pension_paa_maanedsloen(bestillingsnavn, folder_data_session, df, session)


def get_report_from_ri():
    # initialize
    # hostname = socket.gethostname()

    # check if dev_mode
    # dev_mode = hostname.startswith("PCA")

    # Get current month and year in the format mm.yyyy
    current_month_year = datetime.datetime.now().strftime("%m.%Y")

    old_month_year = (datetime.datetime.now() - datetime.timedelta(days=365 * 8)).strftime("%m.%Y")

    # concat current month and year with old month and year
    date_interval = f"{old_month_year}-{current_month_year}"

    try:
        with sync_playwright() as playwright:
            result = login.start_ri(pam_path, robot_name, ri_url, playwright)
            if result is None:
                raise Exception("Failed to start RI")
            # tuple unpacking:
            page, context, browser = result

            # add actions to RI
            try:
                page.get_by_text("Lønsagsbehandling").click()

                with page.expect_popup() as page1_info:
                    page.frame_locator('iframe[name="contentAreaFrame"]').frame_locator(
                        'iframe[name="Rapporter til lønkontrol"]'
                    ).get_by_role("link", name="Udbetalte timer på timeløn").click()

                rapport_variabelinput = page1_info.value

                selector = "#DLG_VARIABLE_vsc_cvl_table_cid2x2 > table > tbody > tr > td:first-child > input"

                # click in date field
                # rapport_variabelinput.frame_locator(
                #    'iframe[name="iframe_Roundtrip_9223372036563636042"]'
                # ).locator("#DLG_VARIABLE_vsc_cvl_VAR_3_INPUT_inp").click()

                # input datointerval 8 aar tilbage, som 12.2015 - 11.2023
                rapport_variabelinput.frame_locator('iframe[name="iframe_Roundtrip_9223372036563636042"]').locator(
                    selector
                ).fill(date_interval)

                # cpr nummer
                # rapport_variabelinput.frame_locator(
                #    'iframe[name="iframe_Roundtrip_9223372036563636042"]'
                # ).locator("#DLG_VARIABLE_vsc_cvl_table_cid2x6").fill(cpr)

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


get_report_from_ri()
