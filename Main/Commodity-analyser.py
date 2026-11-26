import json
import yfinance as yf
from decimal import Decimal

commodities = {# grains & carbs
    "wheat": "ZW=F",
    "corn": "ZC=F",
    "oats": "ZO=F",
    "rice": "ZR=F",
    
    # proteins
    "beef": "LE=F",
    "feeder_cattle": "GF=F",
    "pork": "HE=F",
    "soybean_meal": "ZM=F",
    "soy": "ZS=F",
    
    # dairy and drinks
    "dairy": "DC=F",
    "coffee": "KC=F",
    "orange_juice": "OJ=F",
    
    # fats and sweets
    "cooking_oil": "ZL=F",
    "sugar": "SB=F",
    "cocoa": "CC=F"
}

#fetches data from yahoo finance over the last 30 days
def market_data() -> dict:
    data = {}
    
    for name, ticker in commodities.items():
        try:
            asset = yf.Ticker(ticker)
            # Fetches 1 month of historical trading days
            history = asset.history(period="1mo")
            
            if not history.empty:
                current_price = history['Close'].iloc[-1]
                average_price = history['Close'].mean()
                
                data[name] = {
                    "current_price": round(current_price, 4),
                    "avg_price": round(average_price, 4)
                }
        except Exception as e:
            print(f"Warning: Could not fetch data for {name} ({ticker})")
            
    return data

#compares the current prices to 30 day averages to see if the price is lower or higher than usual

def analyse_commodities(data: dict)-> dict:
    results = []
    for item_name, prices in data.items():
        current = Decimal(str(prices["current_price"]))
        avg = Decimal(str(prices["avg_price"]))
        
        # Calculate percentage change safely using Decimal
        change_pct = float(((current - avg) / avg) * Decimal("100"))
        
        if change_pct <= -5.0:
            status = "Bargain"
        elif change_pct >= 5.0:
            status = "Surge"
        else:
            status = "Stable"
            
        results.append({
            "item_name": item_name,
            "market_status": status,
            "discount_percent": round(abs(change_pct), 2),
            "current_trading_price": float(current)
        })
        
    return results

if __name__ == "__main__":
    # Test 
    live_data = market_data()
    analysis = analyse_commodities(live_data)
    print("Commodity analysis")
    print(json.dumps(analysis, indent=2))
