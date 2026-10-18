"""
Shared declarative Base. Every model file imports Base from HERE,
never from another model file — this is what avoids circular imports
even though tables reference each other (relationship() uses class
names as strings, resolved later by SQLAlchemy's mapper registry).
"""

from sqlalchemy.orm import declarative_base

Base = declarative_base()

EMBEDDING_DIM = 384  # matches all-MiniLM-L6-v2 from sentence-transformers
