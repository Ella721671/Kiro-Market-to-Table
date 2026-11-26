**Requirements Document**

**Introduction**
The Commodity analyser will fetch data from yahoo finance and will calculate commodity changes and whether or not a product is a good bargain . It will retrieve live data for raw food commodities over a 30 day period and calculate price fluctuations. The module will compate current closing prices to a 30 day average and will categorise each ingredient as a "Bargain", "Surge", or "Stable", informing the user which ingredients are cheapest globally and hence will communicate with the shopping cart to add them to the basket.

**Glossary**

**Commodity Ticker:** The Yahoo Finance symbol representing a specific raw ingredient contract (e.g., "ZW=F" for Wheat).
**Current Price:** The most recent daily closing price of the commodity.
**Average Price:** The mean closing price of the commodity over the 30 day period.
**Percentage Change:** The relative difference between the Current Price and Average Price.
**Market Status:** The categorisation of a commodity's price trend (Bargain, Surge, or Stable).

**Requirements**

**Requirement 1**
**User Story:** As the system itself, I want to fetch the last 30 days of market data for specific food commodities so I can establish a baseline price for each ingredient.

**Acceptance Criteria**
1. WHEN the module executes, THEN the system SHALL query Yahoo Finance for 30 days of historical trading data for all predefined commodity tickers.
2. WHEN the historical data is retrieved, THEN the system SHALL extract the most recent closing price as the "Current Price".
3. WHEN the historical data is retrieved, THEN the system SHALL calculate the mean of all closing prices in that period as the "Average Price".
4. WHEN calculating prices, THEN the system SHALL round the Current Price and Average Price to 4 decimal places.
5. WHEN a ticker fails to return data, THEN the system SHALL catch the exception, log a warning, and skip that commodity without crashing.


**Requirement 2**
**User Story:** As the meal planner I want to analyse the price differences so that I can identify which ingredients are currently cheap (bargains) and which are expensive (surges).

**Acceptance Criteria:**
1. WHEN given the current and average price, THEN the system SHALL calculate the percentage change using high-precision decimal arithmetic to prevent floating-point errors.
2. WHEN the percentage change is less than or equal to -5.0%, THEN the system SHALL classify the market status as "Bargain".
3. WHEN the percentage change is greater than or equal to 5.0%, THEN the system SHALL classify the market status as "Surge".
4. WHEN the percentage change is strictly between -5.0% and 5.0%, THEN the system SHALL classify the market status as "Stable".


**Requirement 3**
**User Story:** As a downstream application, I need the analysis results in a structured format so that I can map these trends to grocery store equivalents.

**Acceptance Criteria:**
1. WHEN the analysis is complete, THEN the system SHALL output a list of dictionaries containing the item name, market status, discount percent, and current trading price.
2. WHEN outputting the discount percent, THEN the system SHALL provide the absolute value rounded to 2 decimal places.
3. WHEN outputting the current trading price, THEN the system SHALL provide it as a standard float.





