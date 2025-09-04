# Generate table of insiders with [id | name] (SELECT DISTINCT insider_name FROM transactions_bronze)
# Generate table of companies with [id | ticker | name]
# Explore solutions to what role each user plays in a company
# - Potentially another table that relates [transaction id | personnal role]
# - Would require another table of possible roles (E.g. CFO, CEO, 10%...)

# Remove X, filing date, ticker, company name, insider name, dOwnedPc
# replace trade type with boolean
# add columns to relate insiders and companies
import sqlite3
from datetime import datetime
def create_companies_table(cur: sqlite3.Cursor, conn: sqlite3.Connection):
    cur.execute(""" CREATE TABLE "companies_gold" (
                        "id"	    INTEGER NOT NULL UNIQUE,
                        "ticker"	TEXT,
                        "name"	    TEXT,
                        PRIMARY KEY("id" AUTOINCREMENT)
                    )""")
    
    # populate companies table
    cur.execute("SELECT DISTINCT ticker FROM transactions_bronze")
    tickers = cur.fetchall()
    
    for ticker in tickers:
        ticker_symbol = ticker[0]
        cur.execute("SELECT company_name FROM transactions_bronze WHERE ticker=?", (ticker_symbol,))
        company_name = cur.fetchone()[0]
        cur.execute("INSERT INTO companies_gold (ticker, name) VALUES (?, ?)", (ticker_symbol, company_name,))
    conn.commit()

def create_insiders_table(cur: sqlite3.Cursor, conn: sqlite3.Connection):
    cur.execute(""" CREATE TABLE "insiders_gold" (
                        "id"	INTEGER NOT NULL UNIQUE,
                        "name"	TEXT,
                        PRIMARY KEY("id" AUTOINCREMENT)
                    )""")
    # populate insider table
    cur.execute("SELECT DISTINCT insider_name FROM transactions_bronze")
    insiders = cur.fetchall()
    
    for insider in insiders:
        name = insider[0]
        cur.execute("INSERT INTO insiders_gold (name) VALUES (?)", (name,))
    conn.commit()
    
def create_gold_transactions_table(cur: sqlite3.Cursor, conn: sqlite3.Connection):
    cur.execute(""" CREATE TABLE "transactions_gold" (
                        "id"	        INTEGER NOT NULL UNIQUE,
                        "trade_date"	INTEGER,
                        "company_id"	INTEGER,
                        "insider_id"	INTEGER,
                        "title"	        TEXT,
                        "is_purchase"	INTEGER,
                        "unit_price"	REAL,
                        "unit_quantity"	REAL,
                        "value"	        REAL,
                        PRIMARY KEY("id" AUTOINCREMENT)
                    )""")
    
    # populate transactions table
    cur.execute("SELECT trade_date, ticker, insider_name, title, trade_type, price, quantity, value FROM transactions_bronze;")
    transactions = cur.fetchall()
    
    for transaction in transactions:
        _dt = datetime.strptime(transaction[0], "%Y-%m-%d")
        trade_date = int(_dt.timestamp())
        cur.execute("SELECT id FROM companies_gold WHERE ticker=?", (transaction[1],))
        company_id = cur.fetchone()[0]
        cur.execute("SELECT id FROM insiders_gold WHERE name=?", (transaction[2],))
        insider_id = cur.fetchone()[0]
        title = transaction[3]
        is_purchase = transaction[4].lower()[0] == "p"
        unit_price = transaction[5]
        unit_quantity = transaction[6]
        value = unit_price * unit_quantity
        
        params = (trade_date, company_id, insider_id, title, is_purchase, unit_price, unit_quantity, value)
        
        SQL = """INSERT INTO transactions_gold (trade_date, company_id, insider_id, title, is_purchase, unit_price, unit_quantity, value) VALUES (?, ?, ?, ?, ?, ?, ?, ?)"""
        cur.execute(SQL, params)
    conn.commit()
