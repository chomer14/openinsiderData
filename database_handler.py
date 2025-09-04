import sqlite3

class insider_trading_db_handler:
    def __init__(self, table_name: str, db_location: str):
        self.db_location = db_location
        self.connection = sqlite3.connect(db_location)
        self.cursor = self.connection.cursor()
        self.uncommitted_backlog = 0
        self.max_backlog_size = 100
        self.table_name = table_name
        self.cursor.execute(f"DROP TABLE IF EXISTS {table_name};")
        self.cursor.execute(f"""
                            CREATE TABLE "{table_name}" (
                            "id"	INTEGER NOT NULL UNIQUE,
                            "filing_date"	TEXT,
                            "trade_date"	TEXT,
                            "ticker"	TEXT,
                            "company_name"	TEXT,
                            "insider_name"	TEXT,
                            "title"	TEXT,
                            "trade_type"	TEXT,
                            "price"	REAL,
                            "quantity"	REAL,
                            "owned"	REAL,
                            "dOwnedPc"	REAL,
                            "value"	REAL,
                            "X"	TEXT,
                            PRIMARY KEY("id" AUTOINCREMENT)
                        );
                        """)
        self.commit()

    def close(self):
        self.commit()
        self.cursor.close()
        self.connection.close()

    def write_to_db(self, column_names: list[str], data: tuple[object]):
        assert len(column_names) == len(data)
        sql_statement = f"INSERT INTO {self.table_name} ({','.join(column_names)}) VALUES ({', '.join(['?' for _ in range(len(column_names))])})"
        # print(sql_statement)
        self.cursor.execute(sql_statement, tuple(data))
        self.uncommitted_backlog += 1
        if self.uncommitted_backlog == self.max_backlog_size:
            self.commit()

    def commit(self):
        self.connection.commit()
        # print(f"Commited {self.uncommitted_backlog} uncommited backlog items to DB.")
        self.uncommitted_backlog = 0

def main():
    # db_handler = insider_trading_db_handler("db.db")
    # db_handler.write_to_db("test", ["name", "age"], ("Charlie", 19,))
    # db_handler.commit()
    # db_handler.close()

    # with open("data/insider_trades.csv") as f:
    #     f.
    pass

if __name__ == "__main__":
    main()