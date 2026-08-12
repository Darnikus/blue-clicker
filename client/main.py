from driver.bluetooth_driver import BluetoothDriver
from manager.api import TerminalApi
from manager.key_manager import KeyManager
from ui.app import BlueClickerApp
from utility.log_config import initialize_logging


def main() -> None:
    initialize_logging()

    driver: BluetoothDriver = BluetoothDriver()
    key_manager = KeyManager(driver)
    api: TerminalApi = TerminalApi(driver)
    app: BlueClickerApp = BlueClickerApp(key_manager, api)

    app.run()


if __name__ == "__main__":
    main()
