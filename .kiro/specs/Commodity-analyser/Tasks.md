**Implementation Plan: Commodity Analyser**

**1. Set up project structure and dependencies**

Initialsze my_apps/market-to-table/Main/Commodity-analyser/ directory.

Create requirements.txt and add yfinance and pandas.

Create Commodity-analyser.py entry point.


**2. Implement Data Fetcher (market_data)**

Define the commodities dictionary mapping ingredients to Yahoo Finance tickers.

Implement the market_data() function loop using yfinance.

Add yf.Ticker(ticker).history(period="1mo") call to extract 1 month of trading days.

Extract iloc[-1] for current price and .mean() for average price.

Implement try/except block for error logging on failed ticker fetches.

Requirements: 1.1, 1.2, 1.3, 1.4, 1.5


**3. Implement trend engine (analyse_commodities)**

Implement the analyse_commodities(data) function.

Add Decimal string casting for current and average prices.

Implement the percentage change formula: $change = \frac{current - avg}{avg} \times 100$.

Implement if/elif/else logic for -5.0 and 5.0 thresholds.

Format the output dictionary with abs() and round() functions.

Requirements: 2.1, 2.2, 2.3, 2.4, 3.1, 3.2, 3.3

[ ] * 3.1 Write property test for Bargain Threshold

Property 2: Bargain Threshold Categorisation

Validates: Requirement 2.2

[ ] * 3.2 Write property test for Surge Threshold

Property 3: Surge Threshold Categorisation

Validates: Requirement 2.3

[ ] * 3.3 Write property test for Stable Threshold

Property 4: Stable Threshold Categorisation

Validates: Requirement 2.4

[ ] * 3.4 Write property test for Absolute Discount

Property 5: Absolute Discount Value

Validates: Requirement 3.2


**4. Final Integration and Polish**

Create __main__ block to execute the script and print the JSON output.

Verify live internet connection and test against Yahoo Finance endpoints.

Format terminal output using json.dumps(..., indent=2).