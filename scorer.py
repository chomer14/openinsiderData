
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import sqlite3
import time
from scorer2 import score_stock

def get_growth_and_de(ticker_symbol: str):
    ticker = yf.Ticker(ticker_symbol)

    # ---- Revenue Growth (YoY) ----
    financials = ticker.financials
    if "Total Revenue" not in financials.index:
        revenue_growth = None
    else:
        revenue = financials.loc["Total Revenue"]
        if len(revenue) < 2:
            revenue_growth = None
        else:
            revenue_growth = ((revenue.iloc[0] - revenue.iloc[1]) / revenue.iloc[1]) * 100

    # ---- Debt to Equity ----
    balance_sheet = ticker.balance_sheet
    idx = balance_sheet.index

    # Try multiple debt labels
    debt_labels = ["Long Term Debt", "Short Long Term Debt", "Current Debt", "Short Term Debt"]
    total_debt = 0
    for lbl in debt_labels:
        if lbl in idx:
            total_debt += balance_sheet.loc[lbl].iloc[0]

    # Try multiple equity labels
    equity_labels = ["Total Stockholder Equity", "Stockholders Equity"]
    total_equity = None
    for lbl in equity_labels:
        if lbl in idx:
            total_equity = balance_sheet.loc[lbl].iloc[0]
            break

    de_ratio = (total_debt / total_equity) if (total_equity and total_equity != 0) else None

    return (revenue_growth, de_ratio)
 
def create_sql_query(requiredRoles:list[str]=["CEO", "CFO"], minimumInsiders:int=2, minimumInvestmentValue:float|int=50_000, slidingWindowDays:float|int=30) -> str:
    query = f"""
        SELECT DISTINCT c.ticker, MAX(t.trade_date)
        FROM transactions_gold t
        JOIN insiders_gold i 
            ON i.id = t.insider_id
        JOIN companies_gold c 
            ON c.id = t.company_id
        JOIN transactions_titles_gold tt 
            ON tt.transaction_id = t.id AND tt.insider_id = i.id
        WHERE t.is_purchase = 1
            AND EXISTS (
                    -- Check that both CEO and CFO invested in same company within 30 days
                    SELECT 1
                    FROM transactions_gold t2
                    JOIN transactions_titles_gold tt2 
                        ON tt2.transaction_id = t2.id AND tt2.insider_id = t2.insider_id
                    WHERE t2.company_id = t.company_id
                    AND t2.is_purchase = 1
                    AND ABS(t2.trade_date - t.trade_date) <= {slidingWindowDays}*24*60*60 
                    {f"AND tt2.title IN ({", ".join([f"'{title}'" for title in requiredRoles])})" if len(requiredRoles) > 0 else ""}
                    GROUP BY t2.company_id
                    HAVING COUNT(DISTINCT tt2.title) >= {len(requiredRoles)}
            )
            AND EXISTS (
                    -- Ensure more than 1 insider bought within 30 days
                    SELECT 1
                    FROM transactions_gold t3
                    WHERE t3.company_id = t.company_id
                    AND t3.is_purchase = 1
                    AND ABS(t3.trade_date - t.trade_date) <= {slidingWindowDays}*24*60*60
                    GROUP BY t3.company_id
                    HAVING COUNT(DISTINCT t3.insider_id) >= {minimumInsiders}
            )
            AND EXISTS (
                    -- Ensure at least one transaction > 50k in that window
                    SELECT 1
                    FROM transactions_gold t4
                    WHERE t4.company_id = t.company_id
                    AND t4.is_purchase = 1
                    AND ABS(t4.trade_date - t.trade_date) <= {slidingWindowDays}*24*60*60
                    AND t4.value > {minimumInvestmentValue}
            )
            GROUP BY c.ticker;
    """
    return query

def score(ticker_symbol: str):
    revenue_growth, de_ratio = get_growth_and_de(ticker_symbol)
    
    score = 0
    
    try:
        revenue_growth = float(revenue_growth)
        de_ratio = float(de_ratio)
        
        if revenue_growth > 0 and de_ratio < 2:
            score += 1
            
        if revenue_growth > 5 and de_ratio < 1:
            score += 1
    except:
        pass
            
    return score

import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta

def backtest_one(ticker: str, entry_date):
    """
    12M total return using yfinance with adjusted prices via auto_adjust=True.
    entry_date can be 'YYYY-MM-DD' or epoch seconds.
    """
    # Parse entry date
    if isinstance(entry_date, (int, float)):
        entry_dt = datetime.utcfromtimestamp(entry_date)
    else:
        entry_dt = datetime.strptime(entry_date, "%Y-%m-%d")

    exit_dt = entry_dt + timedelta(days=365)

    # Pull adjusted data
    hist = yf.Ticker(ticker).history(
        start=entry_dt - timedelta(days=7),
        end=exit_dt + timedelta(days=7),
        interval="1d",
        auto_adjust=True,
        actions=False
    )

    if hist.empty or "Close" not in hist.columns:
        return {"ticker": ticker, "error": "No price data"}

    # Ensure index is tz-naive
    prices = hist["Close"].dropna().sort_index()
    if prices.index.tz is not None:
        prices.index = prices.index.tz_convert(None)

    # Helper: next available trading day price on/after target
    def on_or_after(ts):
        ts = pd.Timestamp(ts).tz_localize(None)  # force tz-naive
        pos = prices.index.searchsorted(ts)
        if pos >= len(prices):
            return None
        return float(prices.iloc[pos]), prices.index[pos].date()

    entry_result = on_or_after(entry_dt)
    if entry_result is None:
        return {"ticker": ticker, "error": "No price on/after entry date"}
    entry_price, entry_used = entry_result

    exit_result = on_or_after(exit_dt)
    matured = True
    if exit_result is None:
        matured = False
        exit_price = float(prices.iloc[-1])
        exit_used = prices.index[-1].date()
    else:
        exit_price, exit_used = exit_result

    ret_pct = (exit_price - entry_price) / entry_price * 100.0

    return {
        "ticker": ticker,
        "entry_date": str(entry_dt.date()),
        "exit_date_target": str(exit_dt.date()),
        "entry_price_used": round(entry_price, 4),
        "exit_price_used": round(exit_price, 4),
        "entry_trade_date_used": str(entry_used),
        "exit_trade_date_used": str(exit_used),
        "return_pct_12m": round(ret_pct, 2),
        "matured_window": matured
    }


def main():
    conn = sqlite3.connect("insider_trades.db")
    cur = conn.cursor()
    
    cur.execute("DROP TABLE IF EXISTS watchlist_companies_gold")
    cur.execute(""" CREATE TABLE "watchlist_companies_gold" (
                        "id"	    INTEGER NOT NULL UNIQUE,
                        "ticker"	TEXT,
                        "score"	    REAL,
                        "timestamp"	TEXT,
                        PRIMARY KEY("id" AUTOINCREMENT)
                    );""")
    conn.commit()
    
    cur.execute(create_sql_query())
    goodTransactions = cur.fetchall()
    returns: list[float] = []
    
    for i, importantTransaction in enumerate(goodTransactions):
        print(i, len(goodTransactions))
        ticker, timestamp = importantTransaction
        timestamp = datetime.fromtimestamp(timestamp)
        if time.time() - timestamp.timestamp() < 3*30*24*60*60:
            s_score = score_stock(ticker)["score"]
            date = timestamp.isoformat().split("T")[0]
            cur.execute("INSERT INTO watchlist_companies_gold (ticker, score, timestamp) VALUES (?, ?, ?)", (ticker, s_score, timestamp,))
    conn.commit()
    conn.close()    
        # try:
        #     returns.append(backtest_one(ticker, timestamp.timestamp())["return_pct_12m"])
        # except:
        #     pass
    print(returns)

main()
