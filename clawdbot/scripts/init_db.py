import sqlite3
import os

# 作者: paddyyang
# 最後修改日期: 2026-03-11

def initialize_database():
    db_path = os.path.join(os.path.dirname(__file__), "../data/brain.db")
    print(f"🚀 正在初始化資料庫: {db_path}")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 建立 raw_crawls 表
    # url: 唯一索引 (UNIQUE), 用於防止重複獵取
    # content_md: 轉換後的 Markdown 文本
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS raw_crawls (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        url TEXT NOT NULL UNIQUE,
        content_md TEXT,
        title TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    # 建立 memories 表 (智庫精華)
    # is_star: 是否標記為精華 (0 或 1)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS memories (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        original_url TEXT,
        content TEXT NOT NULL,
        is_star INTEGER DEFAULT 0,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (original_url) REFERENCES raw_crawls(url)
    )
    """)
    
    conn.commit()
    conn.close()
    print("✅ 資料庫初始化完成 (raw_crawls, memories)")

if __name__ == "__main__":
    initialize_database()
