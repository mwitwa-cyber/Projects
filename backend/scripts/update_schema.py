
import sqlalchemy
from sqlalchemy import create_engine, text
from app.core.config import settings
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def update_schema():
    logger.info("Starting schema update for TOTP columns...")
    
    engine = create_engine(settings.DATABASE_URL)
    
    with engine.connect() as conn:
        # Check if columns exist
        result = conn.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name='users'"))
        columns = [row[0] for row in result.fetchall()]
        
        if 'totp_secret' not in columns:
            logger.info("Adding totp_secret column...")
            conn.execute(text("ALTER TABLE users ADD COLUMN totp_secret VARCHAR"))
            conn.commit()
        else:
            logger.info("totp_secret already exists.")
            
        if 'totp_enabled' not in columns:
            logger.info("Adding totp_enabled column...")
            # Default to false (0 for boolean in postgres usually works, but safer to specify default)
            conn.execute(text("ALTER TABLE users ADD COLUMN totp_enabled BOOLEAN DEFAULT FALSE"))
            conn.commit()
        else:
            logger.info("totp_enabled already exists.")
            
    logger.info("Schema update complete.")

if __name__ == "__main__":
    update_schema()
