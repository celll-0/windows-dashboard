from io import TextIOWrapper
import json
import threading

from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
from typing import Any, Dict, List

from loguru import logger
from ..constants import TIMEZONE, STORE_TABLES
from dash.paths import DB_PATH


class JsonPersistenceClient:
    # currently a path to a temp json string
    _store_db: Path
    # prevent multiple threads accessing the store at the same time
    _store_lock = threading.Lock()

    def __init__(self, store_path: str | Path):
        if isinstance(store_path, str):
            store_path = Path(store_path)
        elif not isinstance(store_path, Path):
            raise TypeError("store_path must be a str or Path object")
        
        # Otherwise, store_path is a Path object, so we can use it directly
        self._store_db = store_path
        logger.info("Initialized local store client: {}", self._store_db)

    def update(self, data: Dict[str, Any], table_name: str) -> None:
        if table_name not in STORE_TABLES:
            raise ValueError(f"Invalid table name '{table_name}'.")
        with self._store_lock:
            if not self._is_empty_store():
                with open(self._store_db, 'r+') as sf:
                    store: Dict[str, Any] = json.load(sf)#
                    # ensure the table exists in the store, then unpack and update fields.
                    # Raise exception if check fails on invalid table name
                    if table_name in store:
                        store[table_name].update(data)
                        self._json_dump_into_store(store, sf, table_name)
                    else:
                        raise RuntimeError(
                            "Persistence Error - Table does not exist in store. Check for invalid table name or json store is set up correctly"
                        )
            else:
                # Create the store object if json file does not already exist
                store = {table: {} for table in STORE_TABLES}
                store[table_name].update(data)
                with open(self._store_db, 'w+') as sf:
                    self._json_dump_into_store(store, sf, table_name, trunc_pos=0)


    def _json_dump_into_store(self,
        store: Dict[str, Any],
        store_file: TextIOWrapper,
        updated_table: str,
        trunc_pos: int | None = None
    ) -> None:
        # requires store to be a non-empty dict, otherwise raises ValueError
        if not store:
            raise ValueError("Cannot dump empty store into file")
        # add the timestamp for the updated table to the store before dumping to file
        store_file.seek(0)
        store_file.truncate(trunc_pos)
        json.dump(store, store_file)


    def _populate_fields_from_tuples(
        self, store: Dict[str, Any], fields: List[tuple], table: str
    ) -> Dict[str, Any] | None:
        if fields is None:
            return None
        for field, value in fields:
            store[table][field] = value if value is not None else store[table][field]
        store[f'{table}_timestamp'] = datetime.now(ZoneInfo(TIMEZONE)).isoformat()
        return store



    def get_from_table(self, table_name: str) -> Dict[str, Any]:
        with self._store_lock:
            if self._is_empty_store():
                raise RuntimeError(
                    "Persistence Error - Store is empty. Check that the store is set up correctly"
                )
            
            with open(self._store_db, 'r') as sf:
                store = json.load(sf)
                # check that the table exists in the store if so return.
                # If not throw an error
                data = store.get(table_name)
                if data and data is not None:
                    return data
                else:
                    raise RuntimeError(
                        "Persistence Error - Table does not exist in store. Check for invalid table name or json store is set up correctly"
                    )


    def _is_empty_store(self) -> bool:
        if self._store_db.is_file() and self._store_db.stat().st_size > 0:
            with open(self._store_db, 'r') as sf:
                store = json.load(sf)
                return not bool(store)
        return True


PersistenceService = JsonPersistenceClient(store_path=DB_PATH)