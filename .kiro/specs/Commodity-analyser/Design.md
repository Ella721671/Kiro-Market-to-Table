**Design Document: Commodity Analyser**


**Overview**
The Commodity Analyser is a Python based script utilising the yfinance library to bridge the global financial market with local shopping planning. It uses a dictionary of Yahoo Finance ticker symbols mapped to generic food categories (grains, proteins, dairy, fats) and processes these via panda DataFrames and utilises Python's decimal library to ensure the financial calculations are accurate, before passing JSON compatible data to the Meal Planner's core logic.

**Architecture**

High-Level Architecture

┌─────────────────────────────────────────────────────────────┐
│                 Commodity Analyser Module                   │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐   │
│  │ yfinance API │───▶│ Data Fetcher │───▶│ Trend Engine │   │
│  └──────────────┘    └──────────────┘    └──────────────┘   │
│                             │                   │           │
│                             ▼                   ▼           │
│                      ┌──────────────┐    ┌──────────────┐   │
│                      │ Error Logger │    │ JSON Output  │   │
│                      └──────────────┘    └──────────────┘   │
└─────────────────────────────────────────────────────────────┘

**Components and Interfaces**


**1. Data Fetcher (market_data)**

**Responsibilities:**

Define the dictionary of supported commodities and their tickers.

Iterate through tickers to fetch 30 day historical data.

Calculate the mean and extract the final closing price.

Handle network or ticker-not-found exceptions gracefully.

**2. Trend Engine (analyse_commodities)**

**Responsibilities:**

Accept the raw pricing dictionary from the Data Fetcher.

Convert float prices to Decimal for precise calculation.

Determine the threshold categorisation (Bargain/Surge/Stable).

Structure the final output list.

**Source Code Implementation (Commodity-analyser)**

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
    "canola": "RS=F",
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


**Correctness Properties**

*A property is a characteristic or behavior that should hold true across all valid executions of a system, it is a statement about what the system should do. Properties act as the communication between human-readable specifications and machine-verifiable correctness guarantees.*

**Property 1: Precision Preservation:** For any valid price inputs, the percentage change calculation MUST use Decimal types, preventing floating point rounding errors before the threshold comparison. (Validates Req 2.1)

**Property 2: Bargain Threshold Categorisation:** For any calculated percentage change <= - 5%, the assigned market status MUST strictly evaluate to "Bargain". (Validates Req 2.2)

**Property 3: Surge Threshold Categorisation:** For any calculated percentage change >= 5%, the assigned market status MUST strictly evaluate to "Surge". (Validates Req 2.3)

**Property 4: Stable Threshold Categorisation:** For any calculated percentage change -5% < x < 5%, the assigned market status MUST strictly evaluate to "Stable". (Validates Req 2.4)

**Property 5: Absolute Discount Value:** For any negative percentage change (a drop in price), the outputted discount_percent MUST be a positive absolute value (Validates Req 3.2)

**Property 6: Fault Tolerance:** For any invalid ticker symbol or network timeout during the fetch loop, the function MUST NOT raise an unhandled exception, and MUST return the successfully fetched items. (Validates Req 1.5)


**Error Handling**

**Network Timeout:** If yfinance times out, catch the exception, log it, and skip the item to ensure the rest of the market data can be evaluated.
**Missing Data:** If a ticker returns an empty DataFrame (no trading data for the month), skip the ticker gracefully rather than attempting to calculate a mean on an empty set.


**Testing Strategy**

**Unit Testing (pytest):** Test the math logic for threshold boundaries (-5.0, 5.0, 0.0) by injecting mocked price dictionaries.

**Property-Based Testing (Hypothesis):** Generate random floats for current_price and avg_price to ensure the percentage categorisation always mathematically aligns with the resulting labels.

**Integration Testing:** Test the live connection to Yahoo Finance to ensure the API structure matches the expected DataFrame format.


