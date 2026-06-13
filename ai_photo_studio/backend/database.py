"""
Database setup — SQLAlchemy with async SQLite.
"""

import logging
from datetime import datetime
from sqlalchemy import create_engine, Column, String, Float, Integer, Text, DateTime, Boolean, JSON
from sqlalchemy.orm import DeclarativeBase, sessionmaker, Session

from backend.config import get_settings

logger = logging.getLogger(__name__)


class Base(DeclarativeBase):
    pass


class JobRecord(Base):
    """Persistent job history."""

    __tablename__ = "jobs"

    id = Column(String(8), primary_key=True)
    plugin = Column(String(50), nullable=False, index=True)
    status = Column(String(20), nullable=False, index=True)
    progress = Column(Float, default=0.0)
    message = Column(Text, default="")
    input_files = Column(JSON, default=list)
    output_files = Column(JSON, default=list)
    params = Column(JSON, default=dict)
    error = Column(Text, nullable=True)
    is_batch = Column(Boolean, default=False)
    batch_total = Column(Integer, default=0)
    batch_completed = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)


class Preset(Base):
    """Saved processing presets."""

    __tablename__ = "presets"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    plugin = Column(String(50), nullable=False, index=True)
    category = Column(String(50), default="custom")
    description = Column(Text, default="")
    params = Column(JSON, nullable=False)
    is_builtin = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class AppSettingsRecord(Base):
    """Persistent app settings (key-value)."""

    __tablename__ = "app_settings"

    key = Column(String(100), primary_key=True)
    value = Column(JSON, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# Database engine and session factory
_engine = None
_session_factory = None


def get_engine():
    """Get or create the database engine."""
    global _engine
    if _engine is None:
        settings = get_settings()
        db_path = settings.storage.db_dir / "photo_studio.db"
        db_url = f"sqlite:///{db_path}"
        _engine = create_engine(db_url, echo=False)
        logger.info("Database engine created: %s", db_path)
    return _engine


def get_session() -> Session:
    """Get a database session."""
    global _session_factory
    if _session_factory is None:
        _session_factory = sessionmaker(bind=get_engine())
    return _session_factory()


def init_db():
    """Create all tables if they don't exist."""
    engine = get_engine()
    Base.metadata.create_all(engine)
    logger.info("Database tables initialized")

    # Seed built-in presets
    _seed_presets()


def _seed_presets():
    """Add built-in presets if they don't exist."""
    session = get_session()
    try:
        existing = session.query(Preset).filter(Preset.is_builtin.is_(True)).count()
        if existing > 0:
            return

        builtin_presets = [
            # Color grading presets
            Preset(
                name="Golden Hour",
                plugin="color_grading",
                category="cinematic",
                description="Warm golden tones with lifted shadows",
                params={
                    "temperature": 30,
                    "saturation": 15,
                    "brightness": 5,
                    "contrast": 10,
                    "shadows_lift": 15,
                    "highlights_warmth": 20,
                },
                is_builtin=True,
            ),
            Preset(
                name="Cinematic",
                plugin="color_grading",
                category="cinematic",
                description="Teal and orange color split with crushed blacks",
                params={
                    "temperature": 10,
                    "teal_orange": 40,
                    "contrast": 20,
                    "blacks_crush": 15,
                    "saturation": -5,
                },
                is_builtin=True,
            ),
            Preset(
                name="K-Drama",
                plugin="color_grading",
                category="cinematic",
                description="Soft pastel tones with cool highlights",
                params={
                    "temperature": -10,
                    "saturation": -15,
                    "brightness": 10,
                    "contrast": -5,
                    "pastel_strength": 30,
                    "skin_smoothing": 20,
                },
                is_builtin=True,
            ),
            Preset(
                name="Bollywood",
                plugin="color_grading",
                category="cinematic",
                description="Rich saturated colors with warm tones",
                params={
                    "temperature": 20,
                    "saturation": 30,
                    "contrast": 15,
                    "vibrance": 25,
                    "highlights_warmth": 15,
                },
                is_builtin=True,
            ),
            Preset(
                name="Wedding Classic",
                plugin="color_grading",
                category="wedding",
                description="Soft, airy, and romantic",
                params={
                    "temperature": 5,
                    "saturation": -10,
                    "brightness": 15,
                    "contrast": -10,
                    "pastel_strength": 20,
                    "fade": 10,
                },
                is_builtin=True,
            ),
            Preset(
                name="Moody Wedding",
                plugin="color_grading",
                category="wedding",
                description="Deep tones with dramatic shadows",
                params={
                    "temperature": -5,
                    "saturation": -5,
                    "contrast": 25,
                    "blacks_crush": 10,
                    "highlights_warmth": -10,
                },
                is_builtin=True,
            ),
        ]

        session.add_all(builtin_presets)
        session.commit()
        logger.info("Seeded %d built-in presets", len(builtin_presets))
    except Exception as e:
        session.rollback()
        logger.error("Failed to seed presets: %s", e)
    finally:
        session.close()
