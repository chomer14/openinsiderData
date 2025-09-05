import yfinance as yf

def score_stocks(tickers: list[str]) -> dict:
    results = {}
    
    for ticker in tickers:
        try:
            stock = yf.Ticker(ticker)

            # Financial data
            fin = stock.financials
            bs = stock.balance_sheet
            info = stock.info

            metrics = {}

            # 1. Profitability (Net Income / Revenue)
            try:
                ni = fin.loc["Net Income"].iloc[0]
                rev = fin.loc["Total Revenue"].iloc[0]
                metrics["profit_margin"] = ni / rev if rev else 0
            except Exception:
                metrics["profit_margin"] = None

            # 2. Revenue Growth (YoY)
            try:
                rev_now = fin.loc["Total Revenue"].iloc[0]
                rev_prev = fin.loc["Total Revenue"].iloc[1]
                metrics["revenue_growth"] = (rev_now - rev_prev) / rev_prev if rev_prev else None
            except Exception:
                metrics["revenue_growth"] = None

            # 3. Debt-to-Equity
            try:
                total_debt = bs.loc["Total Debt"].iloc[0]
                total_equity = bs.loc["Total Stockholder Equity"].iloc[0]
                metrics["de_ratio"] = total_debt / total_equity if total_equity else None
            except Exception:
                metrics["de_ratio"] = None

            # 4. Valuation proxy: P/E ratio
            try:
                metrics["pe_ratio"] = info.get("trailingPE", None)
            except Exception:
                metrics["pe_ratio"] = None

            # ---- Scoring ----
            score = 0

            # Profitability
            if metrics["profit_margin"] is not None:
                if metrics["profit_margin"] > 0.1: score += 20
                elif metrics["profit_margin"] > 0: score += 10

            # Growth
            if metrics["revenue_growth"] is not None:
                if metrics["revenue_growth"] > 0.1: score += 25
                elif metrics["revenue_growth"] > 0.05: score += 15

            # Debt ratio
            if metrics["de_ratio"] is not None:
                if metrics["de_ratio"] < 1: score += 20
                elif metrics["de_ratio"] < 2: score += 10

            # Valuation (P/E)
            if metrics["pe_ratio"] is not None:
                if 5 <= metrics["pe_ratio"] <= 25: score += 20
                elif 0 < metrics["pe_ratio"] <= 40: score += 10

            results[ticker] = {
                "score": min(score, 100),
                "metrics": metrics
            }

        except Exception as e:
            results[ticker] = {
                "score": None,
                "metrics": {},
                "error": str(e)
            }
    
    return results

def main():
    tickers = ["NVDA", "MSFT", "AAPL", "AMZN", "META", "AVGO", "GOOGL", "GOOG", "TSLA", "NFLX", "COST", "PLTR", "ASML", "TMUS", "CSCO", "AMD", "AZN", "LIN", "PEP", "SHOP", "INTU", "BKNG", "PDD", "QCOM", "TXN", "APP", "ISRG", "AMGN", "ADBE", "ARM", "MU", "GILD", "HON", "PANW", "LRCX", "AMAT", "CMCSA", "MELI", "ADP", "ADI", "KLAC", "SNPS", "INTC", "DASH", "CRWD", "VRTX", "SBUX", "CEG", "CDNS", "MSTR", "ORLY", "CTAS", "TRI", "MDLZ", "ABNB", "MAR", "ADSK", "PYPL", "MNST", "WDAY", "CSX", "REGN", "FTNT", "AEP", "AXON", "NXPI", "ROP", "FAST", "MRVL", "PCAR", "IDXX", "ROST", "PAYX", "CPRT", "DDOG", "BKR", "TTWO", "TEAM", "EXC", "XEL", "EA", "ZS", "FANG", "KDP", "CCEP", "CSGP", "VRSK", "CHTR", "MCHP", "CTSH", "GEHC", "KHC", "DXCM", "ODFL", "WBD", "TTD", "CDW", "BIIB", "LULU", "ON", "GFS"]
    scores = score_stocks(tickers)
    print(scores)

if __name__ == "__main__":
    main()