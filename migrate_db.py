import sqlite3

DB_PATH = "finance_manager.db"

def migrate():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # Check if user_id exists in income
    c.execute("PRAGMA table_info(income)")
    columns = [row[1] for row in c.fetchall()]
    if 'user_id' not in columns:
        print("Adding user_id to income table...")
        c.execute("ALTER TABLE income ADD COLUMN user_id INTEGER REFERENCES users(id)")
    
    # Check if user_id exists in expenses
    c.execute("PRAGMA table_info(expenses)")
    columns = [row[1] for row in c.fetchall()]
    if 'user_id' not in columns:
        print("Adding user_id to expenses table...")
        c.execute("ALTER TABLE expenses ADD COLUMN user_id INTEGER REFERENCES users(id)")
        
    # Check if user_id exists in category_budgets
    c.execute("PRAGMA table_info(category_budgets)")
    columns = [row[1] for row in c.fetchall()]
    if 'user_id' not in columns:
        print("Adding user_id to category_budgets table...")
        c.execute("ALTER TABLE category_budgets ADD COLUMN user_id INTEGER REFERENCES users(id)")
        
    conn.commit()
    conn.close()
    print("Migration complete.")

if __name__ == "__main__":
    migrate()
