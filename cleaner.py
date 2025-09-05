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

# We will now have tables
# - transactions_gold
# - insiders_gold done
# - companies_gold done

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
                        "is_purchase"	INTEGER,
                        "unit_price"	REAL,
                        "unit_quantity"	REAL,
                        "value"	        REAL,
                        PRIMARY KEY("id" AUTOINCREMENT),
                        FOREIGN KEY (company_id) REFERENCES companies_gold(id),
                        FOREIGN KEY (insider_id) REFERENCES insiders_gold(id)
                    )""")
    
    # populate transactions table
    cur.execute("SELECT trade_date, ticker, insider_name, trade_type, price, quantity, value, title FROM transactions_bronze;")
    transactions = cur.fetchall()
    
    for transaction in transactions:
        _dt = datetime.strptime(transaction[0], "%Y-%m-%d")
        trade_date = int(_dt.timestamp())
        cur.execute("SELECT id FROM companies_gold WHERE ticker=?", (transaction[1],))
        company_id = cur.fetchone()[0]
        cur.execute("SELECT id FROM insiders_gold WHERE name=?", (transaction[2],))
        insider_id = cur.fetchone()[0]
        is_purchase = transaction[3].lower()[0] == "p"
        unit_price = transaction[4]
        unit_quantity = transaction[5]
        value = transaction[6]
        
        params = (trade_date, company_id, insider_id, is_purchase, unit_price, unit_quantity, value)
        
        SQL = """INSERT INTO transactions_gold (trade_date, company_id, insider_id, is_purchase, unit_price, unit_quantity, value) VALUES (?, ?, ?, ?, ?, ?, ?)"""
        cur.execute(SQL, params)
        
        cur.execute("SELECT last_insert_rowid()")
        transaction_id = cur.fetchone()[0]
        
        _titles = [title.strip() for title in transaction[7].split(",")]
        for _title in _titles:
            cur.execute("INSERT INTO transactions_titles_gold (transaction_id, title, insider_id) VALUES(?, ? , ?)", (transaction_id, _title, insider_id,))
    conn.commit()
   
def create_transactions_titles_table(cur: sqlite3.Cursor, conn: sqlite3.Connection):
    cur.execute(""" CREATE TABLE "transactions_titles_gold" (
                        "id"	            INTEGER NOT NULL UNIQUE,
                        "transaction_id"	INTEGER,
                        "title"	            TEXT,
                        "insider_id"	    INTEGER,
                        PRIMARY KEY("id" AUTOINCREMENT),
                        FOREIGN KEY (transaction_id) REFERENCES transactions_gold(id),
                        FOREIGN KEY (insider_id) REFERENCES insiders_gold(id)
                    )""")
    conn.commit()
    
def main():
    conn = sqlite3.connect("insider_trades.db")
    cur = conn.cursor()
    
    
    cur.execute("DROP TABLE IF EXISTS transactions_titles_gold;")
    cur.execute("DROP TABLE IF EXISTS transactions_gold;")
    cur.execute("DROP TABLE IF EXISTS insiders_gold;")
    cur.execute("DROP TABLE IF EXISTS companies_gold;")
    
    create_transactions_titles_table(cur, conn)
    create_companies_table(cur, conn)
    create_insiders_table(cur, conn)
    create_gold_transactions_table(cur, conn)
    
    cur.execute("CREATE INDEX idx_transactions_titles_gold_id ON transactions_titles_gold(id);")
    
    cur.execute("CREATE INDEX idx_transactions_gold_company_id ON transactions_gold(company_id);")
    cur.execute("CREATE INDEX idx_transactions_gold_insider_id ON transactions_gold(insider_id);")
    
    cur.execute("CREATE INDEX idx_transactions_titles_gold_transaction_id ON transactions_titles_gold(transaction_id);")
    cur.execute("CREATE INDEX idx_transactions_titles_gold_insider_id ON transactions_titles_gold(insider_id);")
    conn.commit()

    conn.close()

if __name__ == "__main__":
    main()