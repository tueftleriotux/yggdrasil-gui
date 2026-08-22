from os import getenv
from hjson import loads, dumps
from nicegui.ui import notify


def show_error(error_string: str) -> None:
    """Display error messages as a toast notification at the bottom

    of the page and log them to the console.
    """
    print(error_string)
    notify(error_string, type="negative", timeout=20_000)


class HJSON_CONFIG_FILE:
    """Handles reading, writing, and parsing of HJSON configuration files."""

    def __init__(self) -> None:
        # Fetch the configuration file path from environment variables, defaulting to "N/A"
        self.CONFIG_FILE_PATH = getenv("YGG_CONFIG_FILE_PATH", "N/A")
        # Internal cache for the raw file content
        self.config_file_content = None

    def read_config_raw(self) -> str:
        """Read the raw configuration file content as a string.

        Returns cached content if it has already been loaded.
        """
        if self.config_file_content is not None:
            return self.config_file_content
        try:
            with open(self.CONFIG_FILE_PATH, "r", encoding="utf-8") as config_file:
                file_contents = config_file.read()
                self.config_file_content = file_contents
                return file_contents
        except Exception as error:
            show_error(
                f"[CONFIG_FILE] Error reading config file at: {self.CONFIG_FILE_PATH}, {error}"
            )
            return ""

    def read_config_hjson(self) -> object:
        """Read the configuration file and parse it into a Python object/dictionary."""
        try:
            file_contents = self.read_config_raw()
            return loads(file_contents)
        except Exception as error:
            show_error(
                f"[CONFIG_FILE] Error parsing config file at: {self.CONFIG_FILE_PATH}, {error}"
            )

    def write_config_raw(self, file_contents) -> None:
        """Write raw string content directly to the configuration file."""
        try:
            with open(self.CONFIG_FILE_PATH, "w", encoding="utf-8") as config_file:
                config_file.write(file_contents)
                self.config_file_content = file_contents
        except Exception as error:
            show_error(
                f"[CONFIG_FILE] Error writing config file at: {self.CONFIG_FILE_PATH}, {error}"
            )

    def write_config_hjson(self, hjson_content) -> None:
        """Serialize a Python dictionary into HJSON format

        (using 4 spaces indentation) and save it to disk.
        """
        try:
            # Format Python data structure into an HJSON string
            file_contents = dumps(hjson_content, indent=4)
            self.write_config_raw(file_contents)
        except Exception as error:
            show_error(
                f"[CONFIG_FILE] Error converting config file to HJSON at: {self.CONFIG_FILE_PATH}, {error}"
            )
