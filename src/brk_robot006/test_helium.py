# ---------------------------------------------------------------------------- #
#     Har den timelønnede været ansat mindre end 12 måneder indenfor 8 år?     #
# ---------------------------------------------------------------------------- #
def start_ri():
    # driver = Edge()
    # set_driver(driver)
    start_chrome(headless=True)
    go_to('https://portal.kmd.dk/irj/portal')
    username, password = brk_rpa_utils.get_credentials(pam_path, user, fagsystem="rollebaseretindgang")
    write(username, into='Brugernavn')
    write(password, into='Password')
    click('Log på')
    wait_until(Text('Lønsagsbehandling').exists)
    time.sleep(1)
    click('Lønsagsbehandling')
    time.sleep(1)
    wait_until(Link('Udbetalte timer på timeløn').exists)
    click('Udbetalte timer på timeløn')


start_ri()

# -------------------------------- Date and cpr input -------------------------------- #
# Get current month and year in the format mm.yyyy
current_month_year = datetime.datetime.now().strftime("%m.%Y")
old_month_year = (datetime.datetime.now() - datetime.timedelta(days=365 * 8)).strftime("%m.%Y")
# concat current month and year with old month and year
date_interval = f"{old_month_year} - {current_month_year}"
# selector_date_interval = "#DLG_VARIABLE_vsc_cvl_table_cid2x2 > table > tbody > tr > td:first-child > input"


def download_single_anshistorik_from_ri(cpr: str, folder_data_session: Path):
    write(text=date_interval, into=TextField(to_right_of="Måneder/år"))
    write(text=cpr, into=TextField(to_right_of="Vælg cpr-nr."))
    click('OK')
    # ------------------------ Download and move the file ------------------------ #
    wait_until(Text('Excel uden topinfo').exists)
    click('Excel uden topinfo')

    source_path = Path("~/Downloads/YKMD_STD.xls").expanduser()

    timeout = 5
    start_time = time.time()
    while not os.path.exists(source_path):
        if time.time() - start_time >= timeout:
            logger.error("File does not exist after 5 seconds")
            exit(1)
        time.sleep(1)

    destination_path = Path(folder_data_session / f"anshistorik_{cpr}.mhtml")
    try:
        shutil.move(source_path, destination_path)
    except Exception as e:
        logger.info(f"Error occurred while moving the file: {e}")
        exit(1)
    # -------------------------- Return to Variabelskærm ------------------------- #
    click('Variabelskærm')


# kill_browser()


# from inspect import getsource
# print(getsource(brk_rpa_utils.parse_ri_html_report_to_dataframe))


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
