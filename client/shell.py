import asyncio
import logging
import random
import time
from prompt_toolkit.application import Application
from prompt_toolkit.filters import Condition
from prompt_toolkit.layout.containers import ConditionalContainer, HSplit, VerticalAlign
from prompt_toolkit.layout.layout import Layout
from prompt_toolkit.widgets import TextArea

from bluetooth_driver import BluetoothDriver


logger = logging.getLogger(__name__)

class TextAreaHandler(logging.Handler):
    """Sends logs to UI widget instead of stdout"""
    
    def __init__(self, text_area: TextArea) -> None:
        super().__init__()
        self._text_area = text_area
    
    def emit(self, record: logging.LogRecord) -> None:
        message = self.format(record)

        if self._text_area.text == "":
            self._text_area.text = message
        else:
            self._text_area.text += "\n" + message

        # Auto-scroll
        self._text_area.buffer.cursor_position = len(self._text_area.text)

class SessionShell():
    
    def __init__(self) -> None:
        #TODO Move it to Manager class maybe
        self.sending_flag: bool = False

        # Widjets
        self._log_field: TextArea = TextArea(
            read_only=True,
            scrollbar=False,
            height=None,
            dont_extend_height=True
        )
        self._input_field: TextArea = TextArea(
            height=1,
            prompt=">> ",
            multiline=False,
            wrap_lines=False
        )

        # Logger configuration
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.INFO)
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)
        
        ui_handler = TextAreaHandler(self._log_field)
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        ui_handler.setFormatter(formatter)
        root_logger.addHandler(ui_handler)
       
        self._input_field.accept_handler = self._handle_command

        # UI Container
        self._root_container: HSplit = HSplit([
            ConditionalContainer(
                content=self._log_field,
                filter=Condition(lambda: len(self._log_field.text) > 0)
            ),
            self._input_field
        ], align=VerticalAlign.TOP)

        self._app: Application = Application(
            layout=Layout(self._root_container, focused_element=self._input_field),
            full_screen=False
        )

    def _handle_command(self, buffer):
        command = self._input_field.text.strip().lower()
        match command:
            case "+":
                self.sending_flag = True
                logger.info("Sending Resumed")
            case "-":
                self.sending_flag = False
                logger.info("Sending Paused")
            case "exit":
                self._app.exit()
            case _:
                logger.info(f"Printed {command} ")
        
        self._input_field.text = "" # This clears input field
    
    async def run(self):
        await asyncio.gather(
            self._app.run_async(),
            self.send_message(BluetoothDriver())
        )

    async def send_message(self, driver: BluetoothDriver) -> None:
        last_heartbeat = time.time()
        while True:
            try:
                message = "a"
                if self.sending_flag:
                    if not await driver.send_data(message):
                        logger.error("Could not send data. Waiting for next cycle...")
                        await asyncio.sleep(3)
                        continue
                    
                    # If you don't receive data, the script won't know the 
                    # socket is dead until the next .send() call fails.
                    await asyncio.sleep(4 + random.randint(0, 200) / 1000)
                
                elif time.time() - last_heartbeat > 5:
                    await driver.send_data('\n')
                    last_heartbeat = time.time()
                    await asyncio.sleep(0.1)
                
                else:
                    await asyncio.sleep(0.01)

            except KeyboardInterrupt:
                logger.error("\nUser stopped script.")
                driver.disconnect()
                break
