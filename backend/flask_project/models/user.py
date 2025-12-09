# models/user.py
from datetime import datetime
from bson import ObjectId

class User:
    def __init__(self, username, email, password=None, role="user", is_active=True, last_login=None, created_at=None, updated_at=None, _id=None,urls=None,
                 start_date=None,end_date=None):
        self._id = _id
        self.username = username
        self.email = email
        self.password = password
        self.role = role
        self.is_active = is_active
        self.urls = [] or urls
        self.start_date = start_date
        self.end_date = end_date
        self.last_login = last_login
        self.created_at = created_at or datetime.utcnow()
        self.updated_at = updated_at or datetime.utcnow()
        
        

    def to_dict(self):
        data= {
            "_id": str(self._id) if self._id else None,
            "username": self.username,
            "email": self.email,
            "password": self.password,
            "role": self.role,
            "is_active": self.is_active,
            "urls": self.urls,
            "start_date": self._convert_datetime(self.start_date),
            "end_date": self._convert_datetime(self.end_date),
            "last_login": self.last_login,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }
        if getattr(self, "_id", None):
            data["_id"] = self._id
        return data

    @classmethod
    def from_dict(cls, data):
        return cls(
            _id=data.get("_id"),
            username=data.get("username"),
            email=data.get("email"),
            password=data.get("password"),
            role=data.get("role", "user"),
            is_active=data.get("is_active", False),
            urls=data.get("urls", []),
            start_date=data.get("start_date"),
            end_date=data.get("end_date"),
            last_login=data.get("last_login"),
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at")
        )
    @staticmethod
    def _convert_datetime(value):
        """Ensure datetime is serialized properly."""
        if isinstance(value, datetime):
            return value.isoformat()
        return value