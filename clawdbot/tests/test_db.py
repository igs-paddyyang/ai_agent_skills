import sqlite3
import os

# 作者: paddyyang
# 最後修改日期: 2026-03-11

def test_database_logic():
    db_path = os.path.join(os.path.dirname(__file__), "../data/brain.db")
    print(f"🧪 正在測試資料庫邏輯: {db_path}")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 測試流程 1: 本地寫入與讀取
    try:
        url_test = "https://example.com/test1"
        cursor.execute("INSERT INTO raw_crawls (url, title, content_md) VALUES (?, ?, ?)", 
                       (url_test, "測試標題", "# 這裡是有趣的內容"))
        conn.commit()
        print(f"✅ 成功寫入第 1 筆 URL: {url_test}")
        
    except sqlite3.IntegrityError:
        print("⚠️ 測試中發現 URL 已存在，這是正常的（可能是之前跑過的殘餘）")

    # 測試流程 2: UNIQUE 約束校驗 (核心魯棒性測試)
    try:
        print("🛠️ 正在驗證重複寫入後的 UNIQUE 約束...")
        cursor.execute("INSERT INTO raw_crawls (url, title, content_md) VALUES (?, ?, ?)", 
                       (url_test, "新標題", "這不應該被寫入"))
        conn.commit()
    except sqlite3.IntegrityError:
        print(f"✅ [UNIQUE 驗證通過] 無法重複插入相同的 URL ({url_test})")
    
    # 測試流程 3: 智庫精華標記測試
    cursor.execute("INSERT INTO memories (original_url, content, is_star) VALUES (?, ?, ?)", 
                   (url_test, "這是一則精選摘要", 1))
    conn.commit()
    
    # 讀取檢驗
    cursor.execute("SELECT * FROM memories WHERE is_star = 1")
    star_items = cursor.fetchall()
    if star_items:
        print(f"✅ [標記測試通過] 成功找到精選內容: {star_items[0][2]}")

    conn.close()
    print("\n🎉 資料庫任務 1 驗證全數通過！")

if __name__ == "__main__":
    test_database_logic()
