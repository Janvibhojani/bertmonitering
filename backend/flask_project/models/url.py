# models/url.py
from datetime import datetime
from bson import ObjectId

class urls:
    def __init__(self, name=None, _id=None,domain=None, target=None, mode=None, scrap_from=None, only_on_change=False, interval_ms=0, created_at=None, updated_at=None):
        
        self._id = _id
        self.name = name
        self.domain = domain or []
        self.target = target
        self.mode = mode
        self.scrap_from = scrap_from
        self.only_on_change = only_on_change
        self.interval_ms = interval_ms
        self.created_at = created_at or datetime.utcnow()
        self.updated_at = updated_at or datetime.utcnow()

    def to_dict(self):
        return {
            "_id": str(self._id) if self._id else None,
            "name": self.name,
            "domain": self.domain,
            "target": self.target,
            "mode": self.mode,
            "scrap_from": self.scrap_from,
            "only_on_change": self.only_on_change,
            "interval_ms": self.interval_ms,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }
       
      
    @classmethod
    def from_dict(cls, data):
        return cls(
            id=data.get("id"),
            name=data.get("name"),
            domain=data.get("domain"),
            target=data.get("target"),
            mode=data.get("mode"),
            scrap_from=data.get("scrap_from"),
            only_on_change=data.get("only_on_change", False),
            interval_ms=data.get("interval_ms", 0),
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at")
        )
        
        