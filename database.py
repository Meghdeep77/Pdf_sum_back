from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# SQLite database URL
# Using a relative path: "./test.db"
# This will create a file named 'test.db' in the current working directory
DATABASE_URL = "sqlite:///./database.db"

# Database engine for SQLite
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

# Session for database interaction
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()

print("Database initialized successfully!")
