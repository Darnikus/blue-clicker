from bluetooth_driver import BluetoothDriver
from manager.key_manager import KeyManager
from ui.app import BlueClickerApp
from utility.log_config import initialize_logging


def main() -> None:
    initialize_logging()

    driver: BluetoothDriver = BluetoothDriver()
    key_manager = KeyManager(driver)
    app: BlueClickerApp = BlueClickerApp(key_manager)

    app.run()


if __name__ == "__main__":
    main()
