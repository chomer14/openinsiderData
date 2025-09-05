import yfinance as yf
import numpy as np

def score_stock(ticker: str) -> dict:
    """
    Returns a 0-100 score for a stock based on fundamentals from yfinance.
    """
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        bs = stock.balance_sheet
        cf = stock.cashflow
        fin = stock.financials
    except Exception as e:
        return {"ticker": ticker, "error": str(e)}
    
    # Helper function to safely get values
    def safe(val):
        return float(val) if val is not None else np.nan

    # -------------------- Metrics --------------------
    metrics = {}

    # Profitability
    metrics["gross_margin"] = safe(info.get("grossMargins"))       # 0-1
    metrics["operating_margin"] = safe(info.get("operatingMargins")) # 0-1
    metrics["net_margin"] = safe(info.get("profitMargins"))        # 0-1
    metrics["roe"] = safe(info.get("returnOnEquity"))              # 0-1
    metrics["roa"] = safe(info.get("returnOnAssets"))              # 0-1

    # Growth
    metrics["revenue_growth"] = safe(info.get("revenueGrowth"))    # 0-1
    metrics["eps_growth"] = safe(info.get("earningsQuarterlyGrowth")) # 0-1

    # Leverage / Risk
    metrics["de_ratio"] = safe(info.get("debtToEquity"))           # lower better
    metrics["current_ratio"] = safe(info.get("currentRatio"))      # higher better

    # Valuation (lower P/E, P/B better)
    metrics["pe_ratio"] = safe(info.get("trailingPE"))
    metrics["pb_ratio"] = safe(info.get("priceToBook"))

    # -------------------- Normalize --------------------
    score_components = []

    # Profitability 30%
    for key in ["gross_margin", "operating_margin", "net_margin", "roe", "roa"]:
        val = metrics.get(key, 0)
        if np.isnan(val):
            val = 0
        val = max(0, min(val, 0.5)) / 0.5  # cap to 50% for normalization
        score_components.append(val * 6)   # each ~6% of total

    # Growth 20%
    for key in ["revenue_growth", "eps_growth"]:
        val = metrics.get(key, 0)
        if np.isnan(val):
            val = 0
        val = max(0, min(val, 0.3)) / 0.3  # cap to 30%
        score_components.append(val * 10)  # each ~10% of total

    # Leverage / risk 20%
    # Lower DE ratio is better
    de = metrics.get("de_ratio", np.nan)
    if np.isnan(de):
        de_score = 0.5
    else:
        de_score = max(0, min(2, 2 - de)) / 2  # 0->2 mapped inversely
    score_components.append(de_score * 10)  

    cr = metrics.get("current_ratio", np.nan)
    if np.isnan(cr):
        cr_score = 0.5
    else:
        cr_score = max(0, min(3, cr)) / 3
    score_components.append(cr_score * 10)

    # Valuation 30%
    pe = metrics.get("pe_ratio", np.nan)
    if np.isnan(pe) or pe <= 0:
        pe_score = 0.5
    else:
        pe_score = max(0, min(50, 50 - pe)) / 50  # lower P/E better
    score_components.append(pe_score * 15)

    pb = metrics.get("pb_ratio", np.nan)
    if np.isnan(pb) or pb <= 0:
        pb_score = 0.5
    else:
        pb_score = max(0, min(10, 10 - pb)) / 10  # lower P/B better
    score_components.append(pb_score * 15)

    total_score = sum(score_components)
    total_score = max(0, min(100, total_score))

    return {
        "ticker": ticker,
        "score": round(total_score, 2),
        "metrics": metrics
    }
