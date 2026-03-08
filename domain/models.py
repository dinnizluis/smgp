from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime


@dataclass
class Category:
    id: Optional[str]
    name: str
    created_at: Optional[str] = None


@dataclass
class Transaction:
    id: Optional[str]
    date: str  # ISO date YYYY-MM-DD
    description: str
    amount: float
    account_type: str = "checking"
    category_id: Optional[str] = None
    created_at: Optional[str] = None
