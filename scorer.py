import yfinance as yf

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

def score(ticker_symbol: str):
    revenue_growth, de_ratio = get_growth_and_de(ticker_symbol)
    
    score = 0
    
    try:
        revenue_growth = float(revenue_growth)
        de_ratio = float(de_ratio)
        
        print(revenue_growth, de_ratio)
        if revenue_growth > 0 and de_ratio < 2:
            score += 1
            
        if revenue_growth > 5 and de_ratio < 1:
            score += 1
            
    except Exception as e:
        print(e)
        
    return score
        

print(score("AAPL"))