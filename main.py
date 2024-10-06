from os import getenv

from dotenv import load_dotenv
from gui import show_date_picker_dialog
from p21api.config import Config
from p21api.odata_client import ODataClient
from p21api.reports import do_reports


def main():
    load_dotenv()

    config = Config(start_date=getenv("START_DATE"))

    if config.debug:
        print("*** Debug mode ***")

    if True:
        data, save_clicked = show_date_picker_dialog(config=config)
        if not save_clicked or not data:
            return
        config.from_gui_input(data)

    if not config.has_login:
        raise ValueError("Username and password are required")

    if not config.start_date:
        raise ValueError("Start date is required")

    client = ODataClient(config=config)

    do_reports(client, config)


if __name__ == "__main__":
    main()
