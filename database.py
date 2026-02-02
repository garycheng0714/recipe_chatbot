from dotenv import load_dotenv

load_dotenv()

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

# 資料庫連線位置 (SQLite)
SQLALCHEMY_DATABASE_URL = f"postgresql://postgres:{os.getenv("OPENAI_API_KEY")}@localhost:5432/recipe_orm_db"

# 建立連線引擎
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    pool_size=10,        # pool_size: 池子裡基本的連線數量
    max_overflow=20,     # max_overflow: 當池子滿了，額外允許超支的連線數
    pool_recycle=3600    # pool_recycle: 連線過期時間（秒），防止資料庫端太久沒動靜主動斷線
)

# 建立一個 Session 類別，用來跟資料庫溝通
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 所有的資料表模型都會繼承這個 Base
Base = declarative_base()
