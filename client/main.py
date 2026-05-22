from app import BlueClickerApp
from bluetooth_driver import BluetoothDriver
from log_config import initialize_logging


def main() -> None:
    initialize_logging()

    driver: BluetoothDriver = BluetoothDriver()
    app: BlueClickerApp = BlueClickerApp(driver)

    app.run()


if __name__ == "__main__":
    main()
