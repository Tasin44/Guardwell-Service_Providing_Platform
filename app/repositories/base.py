"""
================================================================================
ARCHITECTURE & DESIGN PATTERN:
1. Generic Repository Pattern (Generics & TypeVar):
   - TypeVar(ModelType) ব্যবহার করে একটি একক বেস ক্লাস তৈরি করা হয়েছে যা যেকোনো
     SQLAlchemy মডেলের সাথে কাজ করতে পারে।
2. DRY & Reusability:
   - get, get_multi, create, update, delete-এর মতো মৌলিক ডাটাবেজ অপারেশনগুলো
     বারবার না লিখে Generic ক্লাসে সেন্ট্রালাইজ করা হয়েছে।
3. Separation of Concerns (SoC):
   - বিজনেস লজিক সার্ভিস লেয়ারে থাকে, সার্ভিস লেয়ার কোনো Raw SQL বা কুয়েরি ডুপ্লিকেট না করে
     রিপোজিটরি লেয়ারের মাধ্যমে ডাটাবেজের সাথে যোগাযোগ করে।
================================================================================
"""

from typing import Generic, TypeVar, Type, Optional, List, Any, Dict, Union
from sqlalchemy.orm import Session
from app.core.database import Base

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    """
    Base generic repository implementing common CRUD operations.
    """
    def __init__(self, model: Type[ModelType]):
        """
        Initializes repository with the specific SQLAlchemy model.
        """
        self.model = model

    def get(self, db: Session, id: Any) -> Optional[ModelType]:
        """Fetch a single record by primary key."""
        return db.query(self.model).filter(self.model.id == id).first()

    def get_multi(self, db: Session, *, skip: int = 0, limit: int = 100) -> List[ModelType]:
        """Fetch multiple records with pagination."""
        return db.query(self.model).offset(skip).limit(limit).all()

    def create(self, db: Session, *, obj_in: Union[Dict[str, Any], Any]) -> ModelType:
        """Create and persist a new record."""
        if isinstance(obj_in, dict):
            db_obj = self.model(**obj_in)
        else:
            obj_data = obj_in.model_dump() if hasattr(obj_in, "model_dump") else obj_in.dict()
            db_obj = self.model(**obj_data)
            
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def update(
        self,
        db: Session,
        *,
        db_obj: ModelType,
        obj_in: Union[Dict[str, Any], Any]
    ) -> ModelType:
        """Update an existing record."""
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.model_dump(exclude_unset=True) if hasattr(obj_in, "model_dump") else obj_in.dict(exclude_unset=True)

        for field, value in update_data.items():
            if hasattr(db_obj, field):
                setattr(db_obj, field, value)

        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def remove(self, db: Session, *, id: int) -> Optional[ModelType]:
        """Delete a record by primary key."""
        obj = db.query(self.model).get(id)
        if obj:
            db.delete(obj)
            db.commit()
        return obj
