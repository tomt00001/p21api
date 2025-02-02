from p21api.config import Config
from p21api.odata_client import ODataClient
from p21api.reports import do_reports

from gui import show_gui_dialog


def main():
    config = Config()

    if config.should_show_gui:
        data, save_clicked = show_gui_dialog(config=config)
        if not save_clicked or not data:
            return
        merged_data = {**config.model_dump(), **data}
        config = Config.from_gui_input(merged_data)

    if not config.has_login:
        raise ValueError("Username and password are required")

    client = ODataClient(config=config)

    do_reports(client, config)


if __name__ == "__main__":
    main()
