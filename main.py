from fastmcp import FastMCP
import sqlite3
import os
from datetime import date

mcp = FastMCP(name = "ExpenseTracker")

DATABASE_PATH = os.path.join(os.path.dirname(__file__), "expense.db")
CATEGORIES_PATH = os.path.join(os.path.dirname(__file__), "categories.json")

def init_db():
    with sqlite3.connect(DATABASE_PATH) as c:
        c.execute("""
                  CREATE TABLE IF NOT EXISTS expenses(
                      id INTEGER PRIMARY KEY AUTOINCREMENT,
                      date TEXT NOT NULL,
                      amount REAL NOT NULL,
                      category TEXT NOT NULL,
                      subcategory TEXT NOT NULL,
                      note TEXT NOT NULL
                  )
                  """)


init_db()

@mcp.tool
def add_expense(date : date, amount : float, category : str, subcategory : str, note: str):
    """Add expense to the database with date, amount, category, subcategory, note"""
    with sqlite3.connect(DATABASE_PATH) as c:
        curr = c.execute("""
                  INSERT INTO expenses(date, amount, category, subcategory, note) VALUES(?,?,?,?,?)
                  """,
                  (date, amount, category, subcategory, note)
                  )
        return {"status" : "ok", "id" : curr.lastrowid}
    

@mcp.tool
def list_expenses():
    """List down the expenses"""
    with sqlite3.connect(DATABASE_PATH) as c:
        curr = c.execute("""
                         SELECT id, date, amount, category, subcategory, note FROM EXPENSES ORDER BY id ASC
                         """)
        cols = [d[0] for d in curr.description]
        
        return [dict(zip(cols,r)) for r in curr.fetchall()]
    
@mcp.tool
def list_expenses_by_date_range(start_date: date, end_date: date):
    """List down the expenses within a date range"""
    with sqlite3.connect(DATABASE_PATH) as c:
        curr = c.execute("""
                         SELECT id, date, amount, category, subcategory, note FROM EXPENSES WHERE date BETWEEN ? AND ? ORDER BY date ASC
                         """, (start_date, end_date))
        cols = [d[0] for d in curr.description]
        
        return [dict(zip(cols,r)) for r in curr.fetchall()]
    
@mcp.tool
def delete_expense(on_date: date, amount: float, note: str):
    """Delete the expense record by date, amount, and note"""
    with sqlite3.connect(DATABASE_PATH) as c:
        curr = c.execute("""
            DELETE FROM expenses
            WHERE date = ? AND amount = ? AND note = ?
        """, (on_date, amount, note))
        c.commit()
        return {"status": "ok", "deleted_rows": curr.rowcount}
    
@mcp.tool
def get_expense_summary_by_category(start_date: date, end_date: date, category: str = None):
    """
    Get expense summary by category within a date range.
    
    Parameters:
        start_date (date): Start date of the range.
        end_date (date): End date of the range.
        category (str, optional): If provided, only summarize expenses for this category.
    """
    with sqlite3.connect(DATABASE_PATH) as c:
        group_by_col = "category"
        if category:
            sql = f"""
                SELECT category, SUM(amount) as total_amount 
                FROM expenses 
                WHERE date BETWEEN ? AND ? AND category = ?
                GROUP BY {group_by_col}
            """
            curr = c.execute(sql, (start_date, end_date, category))
        else:
            sql = f"""
                SELECT category, SUM(amount) as total_amount 
                FROM expenses 
                WHERE date BETWEEN ? AND ? 
                GROUP BY {group_by_col}
            """
            curr = c.execute(sql, (start_date, end_date))
        cols = [d[0] for d in curr.description]
        
        return [dict(zip(cols, r)) for r in curr.fetchall()]

@mcp.resource("expense://categories", mime_type="application/json")
def categories():
    """Get the categories and subcategories from the JSON file"""
    with open(CATEGORIES_PATH, "r") as f:
        return f.read()

if __name__ == "__main__":
    mcp.run(transport="http", host="0.0.0.0", port = 8000)
