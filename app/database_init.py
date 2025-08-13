import logging
from app.database import engine
from app.models.user import Base

logger = logging.getLogger(__name__)

def init_db():
    """Initialize database tables"""
    try:
        logger.info("Creating database tables...")
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully!")
    except Exception as e:
        logger.error(f"Error creating database tables: {e}")
        raise

def drop_db():
    """Drop all database tables"""
    try:
        logger.info("Dropping database tables...")
        Base.metadata.drop_all(bind=engine)
        logger.info("Database tables dropped successfully!")
    except Exception as e:
        logger.error(f"Error dropping database tables: {e}")
        raise

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    init_db() # pragma: no cover