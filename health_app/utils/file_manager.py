# health_app/utils/file_manager.py
import json
from typing import List, Dict, Any
from pathlib import Path
import logging # Added for consistency if we want to log from here

logger = logging.getLogger(__name__)

class FileManager:
    """
    Manages reading from and writing to a specific JSON file.
    This class provides a low-level interface for JSON data persistence.
    """

    def __init__(self, file_path: str | Path):
        """
        Initializes the FileManager with the path to a specific JSON file.

        Args:
            file_path (str | Path): The path to the JSON file that this instance will manage.
        """
        self.file_path = Path(file_path)
        self._ensure_file_exists()

    def _ensure_file_exists(self):
        """
        Ensures that the directory for the JSON file exists, and if the file itself
        doesn't exist, it creates an empty JSON file (with an empty list).
        """
        try:
            self.file_path.parent.mkdir(parents=True, exist_ok=True)
            if not self.file_path.exists():
                with open(self.file_path, 'w', encoding='utf-8') as f:
                    json.dump([], f)
        except OSError as e:
            logger.error(f"Error ensuring file/directory exists at {self.file_path}: {e}")
            # Depending on the severity, you might want to raise this or handle it.
            # For now, logging it. If mkdir or open fails, subsequent operations will likely fail.
            raise # Re-raise to make the caller aware of a critical setup failure


    def read_data(self) -> List[Dict[str, Any]]:
        """
        Reads all data from the associated JSON file.

        Returns:
            List[Dict[str, Any]]: A list of dictionaries. Returns empty list on error/empty file.
        """
        if not self.file_path.exists() or self.file_path.stat().st_size == 0:
            return []
        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if not isinstance(data, list):
                    logger.warning(f"Data in {self.file_path} is not a list. Returning empty list.")
                    # Optionally, you could re-initialize the file here if it's considered corrupted.
                    # with open(self.file_path, 'w', encoding='utf-8') as fix_f:
                    #     json.dump([], fix_f)
                    return []
                return data
        except json.JSONDecodeError:
            logger.error(f"JSONDecodeError in {self.file_path}. File might be corrupted. Returning empty list.")
            return []
        except FileNotFoundError: # Should be caught by the initial check.
            logger.error(f"FileNotFoundError for {self.file_path} during read. Returning empty list.")
            return []
        except Exception as e:
            logger.error(f"Unexpected error reading data from {self.file_path}: {e}")
            return []

    def write_data(self, data: List[Dict[str, Any]]):
        """
        Writes the entire provided dataset to the JSON file, overwriting existing content.

        Args:
            data (List[Dict[str, Any]]): A list of dictionaries to write.
        """
        try:
            with open(self.file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4, default=str) # default=str for non-serializable types like datetime
        except IOError as e:
            logger.error(f"IOError writing to {self.file_path}: {e}")
            raise # Re-raise to make the caller aware of the failure.
        except Exception as e:
            logger.error(f"Unexpected error writing data to {self.file_path}: {e}")
            raise

