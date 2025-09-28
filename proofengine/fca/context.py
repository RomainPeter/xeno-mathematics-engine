"""
Formal Context structures for FCA.
Implements Context{G,M,I} with objects, attributes, and incidence relation.
"""

from typing import Set, List, Dict, Any, Iterator, Tuple
from dataclasses import dataclass, field


@dataclass(frozen=True)
class Object:
    """Formal object in FCA context."""

    name: str
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __str__(self) -> str:
        return self.name

    def __repr__(self) -> str:
        return f"Object('{self.name}')"


@dataclass(frozen=True)
class Attribute:
    """Formal attribute in FCA context."""

    name: str
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __str__(self) -> str:
        return self.name

    def __repr__(self) -> str:
        return f"Attribute('{self.name}')"


@dataclass(frozen=True)
class Intent:
    """Intent (set of attributes) in FCA."""

    attributes: Set[Attribute]

    def __post_init__(self):
        # Ensure attributes is a frozenset for immutability
        object.__setattr__(self, "attributes", frozenset(self.attributes))

    def __str__(self) -> str:
        attr_names = sorted([attr.name for attr in self.attributes])
        return f"{{{', '.join(attr_names)}}}"

    def __repr__(self) -> str:
        return f"Intent({self.attributes})"

    def __len__(self) -> int:
        return len(self.attributes)

    def __contains__(self, attribute: Attribute) -> bool:
        return attribute in self.attributes

    def __iter__(self) -> Iterator[Attribute]:
        return iter(self.attributes)

    def __eq__(self, other) -> bool:
        if not isinstance(other, Intent):
            return False
        return self.attributes == other.attributes

    def __hash__(self) -> int:
        return hash(self.attributes)

    def union(self, other: "Intent") -> "Intent":
        """Union of two intents."""
        return Intent(self.attributes | other.attributes)

    def intersection(self, other: "Intent") -> "Intent":
        """Intersection of two intents."""
        return Intent(self.attributes & other.attributes)

    def difference(self, other: "Intent") -> "Intent":
        """Difference of two intents."""
        return Intent(self.attributes - other.attributes)

    def is_subset(self, other: "Intent") -> bool:
        """Check if this intent is a subset of other."""
        return self.attributes.issubset(other.attributes)

    def is_superset(self, other: "Intent") -> bool:
        """Check if this intent is a superset of other."""
        return self.attributes.issuperset(other.attributes)


@dataclass(frozen=True)
class Extent:
    """Extent (set of objects) in FCA."""

    objects: Set[Object]

    def __post_init__(self):
        # Ensure objects is a frozenset for immutability
        object.__setattr__(self, "objects", frozenset(self.objects))

    def __str__(self) -> str:
        obj_names = sorted([obj.name for obj in self.objects])
        return f"{{{', '.join(obj_names)}}}"

    def __repr__(self) -> str:
        return f"Extent({self.objects})"

    def __len__(self) -> int:
        return len(self.objects)

    def __contains__(self, obj: Object) -> bool:
        return obj in self.objects

    def __iter__(self) -> Iterator[Object]:
        return iter(self.objects)

    def __eq__(self, other) -> bool:
        if not isinstance(other, Extent):
            return False
        return self.objects == other.objects

    def __hash__(self) -> int:
        return hash(self.objects)

    def union(self, other: "Extent") -> "Extent":
        """Union of two extents."""
        return Extent(self.objects | other.objects)

    def intersection(self, other: "Extent") -> "Extent":
        """Intersection of two extents."""
        return Extent(self.objects & other.objects)

    def difference(self, other: "Extent") -> "Extent":
        """Difference of two extents."""
        return Extent(self.objects - other.objects)

    def is_subset(self, other: "Extent") -> bool:
        """Check if this extent is a subset of other."""
        return self.objects.issubset(other.objects)

    def is_superset(self, other: "Extent") -> bool:
        """Check if this extent is a superset of other."""
        return self.objects.issuperset(other.objects)


class FormalContext:
    """Formal context G = (G, M, I) where G is objects, M is attributes, I is incidence."""

    def __init__(
        self,
        objects: List[Object],
        attributes: List[Attribute],
        incidence: Dict[Tuple[Object, Attribute], bool],
    ):
        self.objects = objects
        self.attributes = attributes
        self.incidence = incidence

        # Create reverse mappings for efficiency
        self._object_to_attributes: Dict[Object, Set[Attribute]] = {}
        self._attribute_to_objects: Dict[Attribute, Set[Object]] = {}

        # Build mappings
        for obj in objects:
            obj_attrs = set()
            for attr in attributes:
                if self.incidence.get((obj, attr), False):
                    obj_attrs.add(attr)
            self._object_to_attributes[obj] = obj_attrs

        for attr in attributes:
            attr_objects = set()
            for obj in objects:
                if self.incidence.get((obj, attr), False):
                    attr_objects.add(obj)
            self._attribute_to_objects[attr] = attr_objects

    def has_incidence(self, obj: Object, attr: Attribute) -> bool:
        """Check if object has attribute."""
        return self.incidence.get((obj, attr), False)

    def get_object_attributes(self, obj: Object) -> Set[Attribute]:
        """Get all attributes of an object."""
        return self._object_to_attributes.get(obj, set())

    def get_attribute_objects(self, attr: Attribute) -> Set[Object]:
        """Get all objects that have an attribute."""
        return self._attribute_to_objects.get(attr, set())

    def extent(self, intent: Intent) -> Extent:
        """Compute extent of an intent (all objects that have all attributes in intent)."""
        if not intent.attributes:
            return Extent(set(self.objects))

        # Start with objects that have the first attribute
        result_objects = self.get_attribute_objects(next(iter(intent.attributes)))

        # Intersect with objects that have each remaining attribute
        for attr in intent.attributes:
            result_objects = result_objects & self.get_attribute_objects(attr)

        return Extent(result_objects)

    def intent(self, extent: Extent) -> Intent:
        """Compute intent of an extent (all attributes shared by all objects in extent)."""
        if not extent.objects:
            return Intent(set(self.attributes))

        # Start with attributes of the first object
        result_attributes = self.get_object_attributes(next(iter(extent.objects)))

        # Intersect with attributes of each remaining object
        for obj in extent.objects:
            result_attributes = result_attributes & self.get_object_attributes(obj)

        return Intent(result_attributes)

    def closure(self, intent: Intent) -> Intent:
        """Compute closure of an intent: intent(extent(intent))."""
        extent = self.extent(intent)
        return self.intent(extent)

    def is_closed(self, intent: Intent) -> bool:
        """Check if an intent is closed (equal to its closure)."""
        return intent == self.closure(intent)

    def __str__(self) -> str:
        return f"FormalContext({len(self.objects)} objects, {len(self.attributes)} attributes)"

    def __repr__(self) -> str:
        return f"FormalContext(objects={len(self.objects)}, attributes={len(self.attributes)})"

    def to_dict(self) -> Dict[str, Any]:
        """Convert context to dictionary representation."""
        return {
            "objects": [obj.name for obj in self.objects],
            "attributes": [attr.name for attr in self.attributes],
            "incidence": {
                f"{obj.name}:{attr.name}": has_incidence
                for (obj, attr), has_incidence in self.incidence.items()
            },
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "FormalContext":
        """Create context from dictionary representation."""
        objects = [Object(name) for name in data["objects"]]
        attributes = [Attribute(name) for name in data["attributes"]]

        incidence = {}
        for key, has_incidence in data["incidence"].items():
            obj_name, attr_name = key.split(":")
            obj = next(o for o in objects if o.name == obj_name)
            attr = next(a for a in attributes if a.name == attr_name)
            incidence[(obj, attr)] = has_incidence

        return cls(objects, attributes, incidence)
