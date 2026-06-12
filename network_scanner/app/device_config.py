from dataclasses import dataclass


@dataclass
class DeviceConfig:
    name: str = ""
    saved: bool = False
    tracked: bool = False

    @classmethod
    def from_json(cls, value):
        # Oud formaat: "Samsung Galaxy Tab S8"
        if isinstance(value, str):
            return cls(
                name=value,
                saved=True,
                tracked=False,
            )

        # Nieuw formaat
        if isinstance(value, dict):
            return cls(
                name=value.get("name", ""),
                saved=value.get("saved", False) is True,
                tracked=value.get("tracked", False) is True,
            )

        # Ontbrekend of ongeldig
        return cls()

    def to_json(self):
        return {
            "name": self.name,
            "saved": self.saved,
            "tracked": self.tracked,
        }