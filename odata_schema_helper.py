"""
OData Schema Helper

Provides functions to load and query the OData schema summary JSON for AI agent or
script use.

Usage:
    from odata_schema_helper import ODataSchema
    schema = ODataSchema.load_from_file('odata_schema/odata_schema_summary.json')
    entity_names = schema.list_entities()
    props = schema.get_properties('p21_view_customer')
    navs = schema.get_navigation_properties('p21_view_customer')
"""

import json
from typing import Dict, List, Optional


class ODataSchema:
    def __init__(self, entity_sets: List[Dict]):
        self.entity_sets = entity_sets
        self._entity_map = {e["name"]: e for e in entity_sets}

    @classmethod
    def load_from_file(cls, path: str) -> "ODataSchema":
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return cls(data["entitySets"])

    def list_entities(self) -> List[str]:
        """Return a list of all entity set names."""
        return list(self._entity_map.keys())

    def get_properties(self, entity_name: str) -> Optional[List[Dict]]:
        """Return a list of properties (name/type) for the given entity set name."""
        entity = self._entity_map.get(entity_name)
        if entity:
            return entity.get("properties", [])
        return None

    def get_navigation_properties(self, entity_name: str) -> Optional[List[Dict]]:
        """Return a list of navigation properties for the given entity set name."""
        entity = self._entity_map.get(entity_name)
        if entity:
            return entity.get("navigationProperties", [])
        return None

    def is_incomplete(self, entity_name: str) -> bool:
        """Return True if the entity set is flagged as incomplete."""
        entity = self._entity_map.get(entity_name)
        if entity:
            return entity.get("incomplete", False)
        return False
