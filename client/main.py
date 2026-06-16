from bluetooth_driver import BluetoothDriver
from key_manager import KeyManager
from log_config import initialize_logging
from ui.app import BlueClickerApp


def main() -> None:
    initialize_logging()

    driver: BluetoothDriver = BluetoothDriver()
    key_manager = KeyManager(driver)
    app: BlueClickerApp = BlueClickerApp(key_manager)

    app.run()


if __name__ == "__main__":
    main()
