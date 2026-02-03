from dotenv import load_dotenv

load_dotenv()

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine
import os


# 資料庫連線位置 (SQLite)
POSTGRES_URL = f"postgresql+asyncpg://postgres:{os.getenv("OPENAI_API_KEY")}@localhost:5432/recipe_orm_db"
ES_URL = os.getenv("ES_URL", "http://localhost:9200")
QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")

# 建立連線引擎
engine = create_async_engine(
    POSTGRES_URL,
    pool_size=10,        # pool_size: 池子裡基本的連線數量
    max_overflow=20,     # max_overflow: 當池子滿了，額外允許超支的連線數
    pool_recycle=3600    # pool_recycle: 連線過期時間（秒），防止資料庫端太久沒動靜主動斷線
)

# 建立一個 Session 類別，用來跟資料庫溝通
AsyncSessionLocal = async_sessionmaker(bind=engine, expire_on_commit=False)

# 所有的資料表模型都會繼承這個 Base
Base = declarative_base()