import os
import sys

# Add backend directory to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text, inspect
from app.core.config import settings
from app.core.database import SessionLocal, engine

def test_pg_connection():
    print(f"[+] Testing PostgreSQL Connection to: {settings.DATABASE_URL}")
    db = SessionLocal()
    try:
        res = db.execute(text("SELECT version();"))
        ver = res.fetchone()
        print(f"[+] PostgreSQL Ping SUCCESSful!")
        print(f"    Version Info: {ver[0] if ver else 'Connected'}")
        
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        print(f"[+] Current Database Tables ({len(tables)}): {tables}")
        return True, tables, None
    except Exception as e:
        print(f"[-] PostgreSQL Connection FAILED: {e}")
        return False, [], str(e)
    finally:
        db.close()

if __name__ == "__main__":
    test_pg_connection()
