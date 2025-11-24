# app/database.py

from sqlalchemy import create_engine
import os
import urllib.parse

DB_USERNAME = os.getenv("DB_USERNAME")
DB_PASSWORD = urllib.parse.quote(os.getenv("DB_PASSWORD", ""))
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "3306")
DB_NAME = os.getenv("DB_NAME")

# Example for MySQL / MariaDB


DATABASE_URL = f"mysql+pymysql://{DB_USERNAME}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
print("DEBUG DATABASE_URL:", DATABASE_URL)
# Example for PostgreSQL (uncomment to use)
# DATABASE_URL = f"postgresql+psycopg2://{DB_USERNAME}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20
)
