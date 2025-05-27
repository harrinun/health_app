from typing import Generic, TypeVar, List, Optional, Type, Dict, Any
from uuid import UUID
from datetime import datetime, timezone
from pydantic import BaseModel
import logging

# Assuming TimestampMixin is in models.base, adjust if necessary
from ..models.base import TimestampMixin 
from ..utils.file_manager import FileManager # <--- CORRECTED IMPORT

logger = logging.getLogger(__name__)

ModelType = TypeVar('ModelType', bound=BaseModel)


class BaseRepository(Generic[ModelType]):
    """
    Generic base repository providing CRUD operations for Pydantic models
    stored in JSON files via a FileManager.

    This repository assumes that the models it manages will have:
    - An 'id: UUID' field for unique identification.
    - 'date_updated: datetime' and 'date_deleted: Optional[datetime]' fields
      if soft delete and restore functionalities are to be used. These typically
      come from inheriting a mixin like TimestampMixin.
    """

    def __init__(self, file_manager: FileManager, model_class: Type[ModelType]):
        """
        Initializes the BaseRepository.

        Args:
            file_manager (FileManager): An instance of FileManager configured for the
                                        specific JSON file this repository will manage.
            model_class (Type[ModelType]): The Pydantic model class (e.g., PatientModel)
                                           that this repository operates on.
        """
        self.file_manager = file_manager
        self.model_class = model_class

    def _load_data(self) -> List[ModelType]:
        """
        Loads raw data from the JSON file using FileManager and converts each
        item into an instance of self.model_class.

        Returns:
            List[ModelType]: A list of Pydantic model instances.
                             Returns an empty list if the file is empty or data is invalid.
        """
        raw_data = self.file_manager.read_data()
        hydrated_data: List[ModelType] = []
        for record_dict in raw_data:
            try:
                hydrated_data.append(self.model_class(**record_dict))
            except Exception as e:
                logger.error(f"Error hydrating record into {self.model_class.__name__}: {e}. Record: {record_dict}")
        return hydrated_data

    def _save_data(self, data: List[ModelType]) -> None:
        """
        Converts a list of Pydantic model instances into a list of dictionaries
        suitable for JSON serialization and writes it to the file using FileManager.

        Args:
            data (List[ModelType]): A list of Pydantic model instances to save.
        """
        serializable_data = [item.model_dump(mode='json') for item in data]
        self.file_manager.write_data(serializable_data)

    def _find_item_index(self, item_id: UUID, data: List[ModelType]) -> Optional[int]:
        """
        Helper method to find the index of an item by its ID in a list of model instances.

        Args:
            item_id (UUID): The ID of the item to find.
            data (List[ModelType]): The list of model instances to search within.

        Returns:
            Optional[int]: The index of the item if found, otherwise None.
        """
        for index, item in enumerate(data):
            # We assume all model instances will have an 'id' attribute.
            if hasattr(item, 'id') and item.id == item_id:
                return index
        return None

    def get_all(self, skip: int = 0, limit: Optional[int] = None, include_deleted: bool = False) -> List[ModelType]:
        """
        Retrieves records, optionally skipping soft-deleted ones, with pagination.

        Args:
            skip (int): The number of records to skip (for pagination). Defaults to 0.
            limit (Optional[int]): The maximum number of records to return.
                                   Defaults to None (no limit, returns all matching).
            include_deleted (bool): Whether to include soft-deleted records.
                                    Defaults to False.

        Returns:
            List[ModelType]: A list of model instances.
        """
        all_items = self._load_data()
        
        if not include_deleted:
            # Filter out items that are soft-deleted, assuming 'date_deleted' attribute exists.
            processed_items = [
                item for item in all_items
                if not (hasattr(item, 'date_deleted') and getattr(item, 'date_deleted') is not None)
            ]
        else:
            processed_items = all_items

        # Apply pagination
        if limit is None:
            return processed_items[skip:]
        else:
            return processed_items[skip : skip + limit]

    def get_by_id(self, item_id: UUID, include_deleted: bool = False) -> Optional[ModelType]:
        """
        Retrieves a single record by its ID.

        Args:
            item_id (UUID): The ID of the item to retrieve.
            include_deleted (bool): Whether to include soft-deleted records.
                                    Defaults to False.

        Returns:
            Optional[ModelType]: The model instance if found and matches deletion criteria,
                                 otherwise None.
        """
        all_items = self._load_data() # Load all data first
        
        for item in all_items:
            if hasattr(item, 'id') and item.id == item_id:
                # Found the item, now check deletion status
                if include_deleted:
                    return item # Return item regardless of deletion status
                else:
                    # Return item only if it's not soft-deleted
                    if not (hasattr(item, 'date_deleted') and getattr(item, 'date_deleted') is not None):
                        return item
                    else:
                        # Item found but is soft-deleted and active ones are requested
                        logger.debug(f"Item with ID {item_id} found but is soft-deleted; not returned as include_deleted=False.")
                        return None 
        logger.debug(f"Item with ID {item_id} not found in the dataset.")
        return None

    def add(self, item_to_add: ModelType) -> ModelType:
        """
        Adds a new item to the dataset. The item should be a fully formed
        Pydantic model instance. Timestamps like 'date_created' and 'date_updated'
        are expected to be set by the model's default factories upon instantiation.

        Args:
            item_to_add (ModelType): The Pydantic model instance to add.
                                     Must have an 'id' attribute.

        Returns:
            ModelType: The added model instance.

        Raises:
            ValueError: If the item to add does not have an 'id' or if an item
                        with the same ID already exists.
        """
        if not hasattr(item_to_add, 'id') or item_to_add.id is None:
            logger.error("Attempted to add an item without a valid 'id'.")
            raise ValueError("Item to add must have a valid 'id'.")

        all_items = self._load_data()
        
        # Check for existing ID to maintain uniqueness.
        # Use internal _find_item_index to check presence regardless of soft_delete status.
        if self._find_item_index(item_to_add.id, all_items) is not None:
            logger.error(f"Attempted to add an item with an existing ID: {item_to_add.id}")
            raise ValueError(f"Item with ID {item_to_add.id} already exists.")

        all_items.append(item_to_add)
        self._save_data(all_items)
        logger.info(f"Item with ID {item_to_add.id} added successfully.")
        return item_to_add

    def update(self, item_id: UUID, update_data_dict: Dict[str, Any]) -> Optional[ModelType]:
        """
        Updates an existing non-soft-deleted item identified by item_id.
        If the model has 'date_updated', it will be set to the current UTC time.

        Args:
            item_id (UUID): The ID of the item to update.
            update_data_dict (Dict[str, Any]): A dictionary containing the fields to update.
                                             Keys should correspond to model field names.

        Returns:
            Optional[ModelType]: The updated model instance if found and updated,
                                 otherwise None (e.g., if item not found or is soft-deleted).
        """
        all_items = self._load_data()
        item_index = self._find_item_index(item_id, all_items)

        if item_index is None:
            logger.warning(f"Update failed: Item with ID {item_id} not found.")
            return None

        item_to_update = all_items[item_index]

        # Prevent updating if already soft-deleted by this generic method.
        if hasattr(item_to_update, 'date_deleted') and getattr(item_to_update, 'date_deleted') is not None:
            logger.warning(f"Update failed: Item with ID {item_id} is soft-deleted. Use restore first or a specific method to update soft-deleted items.")
            return None
            
        # Prepare values for update, including 'date_updated' if applicable
        current_time_utc = datetime.now(timezone.utc)
        update_payload = update_data_dict.copy()
        
        if hasattr(item_to_update, 'date_updated'):
            update_payload['date_updated'] = current_time_utc
        else:
            logger.debug(f"Model {self.model_class.__name__} does not have 'date_updated' field. Timestamp not explicitly set during update.")

        # Create an updated model instance using Pydantic's model_copy
        try:
            updated_item = item_to_update.model_copy(update=update_payload)
        except Exception as e: # More specific PydanticValidationError if possible
            logger.error(f"Error creating updated model copy for ID {item_id}: {e}. Update payload: {update_payload}")
            return None 
        
        all_items[item_index] = updated_item
        self._save_data(all_items)
        logger.info(f"Item with ID {item_id} updated successfully.")
        return updated_item

    def soft_delete(self, item_id: UUID) -> Optional[ModelType]:
        """
        Soft deletes an item by setting its 'date_deleted' and 'date_updated' fields.
        The item remains in the file. Assumes the model has these fields from TimestampMixin.

        Args:
            item_id (UUID): The ID of the item to soft delete.

        Returns:
            Optional[ModelType]: The soft-deleted model instance if found and not already
                                 soft-deleted, otherwise None.
        """
        all_items = self._load_data()
        item_index = self._find_item_index(item_id, all_items)

        if item_index is None:
            logger.warning(f"Soft delete failed: Item with ID {item_id} not found.")
            return None

        item_to_delete = all_items[item_index]

        # Ensure model has the required timestamp fields for soft delete.
        if not hasattr(item_to_delete, 'date_deleted') or not hasattr(item_to_delete, 'date_updated'):
            logger.error(f"Soft delete failed: Model {self.model_class.__name__} lacks 'date_deleted' or 'date_updated' fields for item ID {item_id}.")
            return None 

        # Prevent re-deleting if already soft-deleted
        if getattr(item_to_delete, 'date_deleted') is not None:
            logger.info(f"Item with ID {item_id} is already soft-deleted.")
            return item_to_delete # Return the item as is, no changes made

        current_time_utc = datetime.now(timezone.utc)
        update_values = {
            'date_deleted': current_time_utc,
            'date_updated': current_time_utc # Also update 'date_updated' on soft delete
        }
        
        try:
            deleted_item_version = item_to_delete.model_copy(update=update_values)
        except Exception as e:
            logger.error(f"Error creating soft-deleted model copy for ID {item_id}: {e}")
            return None
        
        all_items[item_index] = deleted_item_version
        self._save_data(all_items)
        logger.info(f"Item with ID {item_id} soft-deleted successfully.")
        return deleted_item_version

    def restore(self, item_id: UUID) -> Optional[ModelType]:
        """
        Restores a soft-deleted item by setting its 'date_deleted' to None
        and updating 'date_updated'. Assumes the model has these fields from TimestampMixin.

        Args:
            item_id (UUID): The ID of the item to restore.

        Returns:
            Optional[ModelType]: The restored model instance if found and was soft-deleted,
                                 otherwise None.
        """
        all_items = self._load_data()
        item_index = self._find_item_index(item_id, all_items)

        if item_index is None:
            logger.warning(f"Restore failed: Item with ID {item_id} not found.")
            return None

        item_to_restore = all_items[item_index]

        # Ensure model has the required timestamp fields for restore.
        if not hasattr(item_to_restore, 'date_deleted') or not hasattr(item_to_restore, 'date_updated'):
            logger.error(f"Restore failed: Model {self.model_class.__name__} lacks 'date_deleted' or 'date_updated' fields for item ID {item_id}.")
            return None

        # Only restore if it was actually soft-deleted
        if getattr(item_to_restore, 'date_deleted') is None:
            logger.info(f"Item with ID {item_id} is not soft-deleted. No restore action taken.")
            return item_to_restore # Return the item as is, no changes made

        update_values = {
            'date_deleted': None, # Set to None to indicate it's not deleted
            'date_updated': datetime.now(timezone.utc) # Update 'date_updated' on restore
        }
        
        try:
            restored_item_version = item_to_restore.model_copy(update=update_values)
        except Exception as e:
            logger.error(f"Error creating restored model copy for ID {item_id}: {e}")
            return None
        
        all_items[item_index] = restored_item_version
        self._save_data(all_items)
        logger.info(f"Item with ID {item_id} restored successfully.")
        return restored_item_version
