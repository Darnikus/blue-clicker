import logging

from bluetooth_driver import BluetoothDriver
from shell import BlueClickerApp

# Get a logger instance
logger = logging.getLogger(__name__)


def main() -> None:
    driver: BluetoothDriver = BluetoothDriver()
    app: BlueClickerApp = BlueClickerApp(driver)

    app.run()


if __name__ == "__main__":
    main()
