"""
Structure model for AIDE-X
"""

from datetime import datetime
from typing import Optional, Dict, Any
from extensions import db

class Structure(db.Model):
    """構成テンプレートモデル"""
    __tablename__ = "structures"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    content = db.Column(db.JSON)
    is_final = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __init__(
        self,
        user_id: int,
        title: str,
        description: str,
        content: Dict[str, Any],
        is_final: bool = False
    ):
        self.user_id = user_id
        self.title = title
        self.description = description
        self.content = content
        self.is_final = is_final

    def to_dict(self) -> Dict[str, Any]:
        """モデルを辞書に変換"""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "title": self.title,
            "description": self.description,
            "content": self.content,
            "is_final": self.is_final,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }

    def __repr__(self) -> str:
        return f"<Structure {self.title}>" 