# Requirements Document: Market-to-Table

## Introduction

**Market-to-Table** is a schedule-aware, market-responsive grocery and meal-planning web application that helps households save money and cooking time. By combining personal schedule and workload signals (`Calendar.py`), live agricultural commodity futures (`Commodity-analyser.py`), and UK supermarket product swaps (`Shopping-planner.py`), the Streamlit storefront (`Main/app.py`) builds a tailored weekly shopping basket, tracks savings against a standard unswapped shop, and adapts recipe ideas to the user's available energy and ingredients.

---

## Glossary

- **Market-to-Table System**: The complete end-to-end Python pipeline and Streamlit web application (`Calendar.py`, `Commodity-analyser.py`, `Shopping-planner.py`, `main.py`, and `Main/app.py`).
- **User**: The shopper interacting with the Market-to-Table storefront to plan weekly groceries and meals.
- **Schedule Mode**: The active workload preset selected by the User (`Demo - Calm Week`, `Demo - Burnout Week`, or `Live Google Calendar`).
- **Calm Week (`from_scratch`)**: A low-stress schedule state (`Relaxing`) that prioritises home-cooked recipes and base ingredients, styled with the Sage Olive (`#838921`) editorial theme.
- **Burnout Week (`minimal_prep`)**: A high-workload schedule state (`Burnout`) triggered by heavy meeting hours, late-evening meetings, or urgency keywords, switching to convenience/no-cook items (≤ 5 mins prep) and the Warm Ochre (`#D99B21`) theme.
- **Tracked Commodity**: One of the 13 global agricultural staples monitored by the system (`wheat`, `rice`, `corn`, `oats`, `beef`, `pork`, `soy`, `dairy`, `coffee`, `orange_juice`, `cooking_oil`, `sugar`, `cocoa`).
- **Market Status**: The volatility classification assigned to a Tracked Commodity (`Bargain`, `Stable`, or `Surge`).
- **Grocery Swap Matrix**: The 52-rule lookup table mapping each Tracked Commodity, Market Status, and Schedule Mode to a specific UK supermarket product.
- **Core Weekly Staples**: The foundational commodity set (`wheat`, `beef`, `dairy`, `coffee`) retained in the basket even when their Market Status is `Stable`.
- **Smart Basket**: The interactive list of recommended UK grocery items with quantity steppers, cupboard toggles, and remove/restore controls.
- **Cupboard Toggle**: The `"Already in cupboard"` checkbox that sets an item's purchase cost to `£0.00` while keeping it available as a recipe ingredient.
- **Auto-Fit Optimizer**: The 1-click budget solver that trims extra quantities and removes `Surge` items first until the basket total fits within the User's weekly budget limit.
- **30-Day Price Sparkline**: The interactive area chart displayed in the 50/50 split view showing a commodity's 30-day futures price trend.

---

## Requirements

### Requirement 1: Schedule & Burnout Workload Detection
**User Story:** As a busy shopper, I want the app to detect whether my upcoming week is calm or high-stress from my calendar and work chat, so that my shopping basket matches my available cooking time and energy.

#### Acceptance Criteria
1. WHEN a Schedule Mode is selected THEN the Market-to-Table System SHALL fetch upcoming 7-day calendar events and recent work-chat messages to calculate total meeting hours, late-evening meetings (ending at or after `18:00`), and urgency keyword hits.
2. WHEN total meeting hours are `>= 20.0`, urgency keyword hits are `>= 5`, or late-evening meetings are `>= 3` THEN the Market-to-Table System SHALL classify the week as `Burnout` and set `meal_prep_mode` to `minimal_prep`.
3. WHEN workload metrics fall below burnout thresholds THEN the Market-to-Table System SHALL route the basket to `from_scratch` home-cooking mode.
4. WHEN `meal_prep_mode` switches between `from_scratch` and `minimal_prep` THEN the Market-to-Table System SHALL shift the interface palette between Sage Olive (`#838921`) and Warm Ochre (`#D99B21`) and reduce average weekly meal prep time.

---

### Requirement 2: Global Commodity Futures Volatility Analysis
**User Story:** As a budget-conscious shopper, I want the app to track real-time global food commodity prices, so that I can avoid price spikes and take advantage of market dips.

#### Acceptance Criteria
1. WHEN the market analysis pipeline runs THEN the Market-to-Table System SHALL evaluate all 13 Tracked Commodities via Yahoo Finance futures tickers and classify each as `Bargain`, `Stable`, or `Surge`.
2. WHEN a Tracked Commodity has a `Stable` Market Status THEN the Market-to-Table System SHALL exclude it from the Smart Basket unless it belongs to the Core Weekly Staples (`wheat`, `beef`, `dairy`, `coffee`).
3. WHEN a Tracked Commodity has a `Surge` Market Status THEN the Market-to-Table System SHALL flag the price spike and trigger a lower-cost UK supermarket substitute.
4. WHEN the User clicks `View` or `Inspect` on any Tracked Commodity THEN the Market-to-Table System SHALL open a 50/50 split view displaying its 30-Day Price Sparkline, percentage shift, shelf price impact, and matching recipe titles.

---

### Requirement 3: UK Grocery Swap & Open Food Facts Resolution
**User Story:** As a UK supermarket shopper, I want commodity signals translated into real UK grocery items with nutrition metadata, so that I get an actionable shopping list rather than raw financial data.

#### Acceptance Criteria
1. THE Market-to-Table System SHALL maintain a Grocery Swap Matrix covering all 13 Tracked Commodities across both `Bargain` and `Surge` regimes and both `from_scratch` and `minimal_prep` modes.
2. WHEN resolving a `Bargain` or `Stable` Core Weekly Staple THEN the Market-to-Table System SHALL select the corresponding value item from the `Bargain` branch of the Grocery Swap Matrix.
3. WHEN resolving a `Surge` commodity THEN the Market-to-Table System SHALL select the cost-saving substitute from the `Surge` branch of the Grocery Swap Matrix.
4. WHEN building the Smart Basket THEN the Market-to-Table System SHALL query the Open Food Facts UK API for live product names, brands, NOVA groups, and Nutri-Scores, falling back immediately to the local UK catalogue for remaining items if the API is unreachable.

---

### Requirement 4: Interactive Basket, Exact Budgeting & Auto-Fit Optimizer
**User Story:** As a shopper managing a weekly budget, I want to adjust item quantities, mark items I already own, see how much I am saving, and automatically trim my basket if it goes over budget.

#### Acceptance Criteria
1. THE Market-to-Table System SHALL calculate all basket totals and savings figures using exact `Decimal` arithmetic formatted in GBP (`£`).
2. WHEN the User increments (`+`) or decrements (`-`) an item's quantity THEN the Market-to-Table System SHALL update the line price, checkout total, and budget progress bar immediately.
3. WHEN the User checks the Cupboard Toggle (`"Already in cupboard"`) on an item THEN the Market-to-Table System SHALL set that item's checkout cost and prep time contribution to `£0.00` and `0` minutes.
4. WHILE the Smart Basket is displayed THEN the Market-to-Table System SHALL render a `"Total Saved vs. Standard Shop"` banner comparing the Smart Basket cost against an unswapped supermarket shop alongside prep minutes saved and surges dodged.
5. WHEN the basket checkout total exceeds the User's Weekly Grocery Budget slider THEN the Market-to-Table System SHALL display a 1-click `"Auto-Fit to Budget"` button.
6. WHEN the User clicks `"Auto-Fit to Budget"` THEN the Market-to-Table System SHALL reduce duplicate quantities (`qty > 1`) first and then remove `Surge` items before `Stable` or `Bargain` items until the checkout total is less than or equal to the budget limit.

---

### Requirement 5: Dynamic Meal Suggestions & Recipe Filtering
**User Story:** As a home cook, I want meal recipes that match both my schedule energy and the exact items currently in my basket, so that I never see recipes requiring ingredients I removed.

#### Acceptance Criteria
1. WHEN rendering the `"What's on the Table?"` tab THEN the Market-to-Table System SHALL display up to 3 recipes matching the active `meal_prep_mode` that share at least 2 active ingredients from the Smart Basket or cupboard.
2. WHEN a recipe ingredient is marked `"Already in cupboard"` THEN the Market-to-Table System SHALL retain that ingredient for recipe matching and label it `"In cupboard"`.
3. WHEN the User removes an item from the Smart Basket (or reduces its quantity to `0` without marking it in the cupboard) THEN the Market-to-Table System SHALL immediately hide any recipe requiring that removed ingredient and restore the recipe if the item is restored to the basket.

---

### Requirement 6: Offline Resilience, Visual Artwork & Shopping List Export
**User Story:** As a user or hackathon judge running the app in any environment, I want reliable offline fallbacks, clean custom illustrations, and a downloadable shopping list so the app works smoothly end-to-end.

#### Acceptance Criteria
1. WHEN Google Calendar, Discord, Yahoo Finance, or Open Food Facts UK credentials or network connections are unavailable THEN the Market-to-Table System SHALL fall back to deterministic demo schedules, 30-day trend curves, and local UK product data without crashing.
2. WHEN rendering Tracked Commodities and Smart Basket cards THEN the Market-to-Table System SHALL load matching 1:1 illustrations from `Main/assets/` and display a styled 2-letter monogram fallback if an image file is absent.
3. WHEN the User clicks `"Download Shopping List"` in the bottom summary bar THEN the Market-to-Table System SHALL export a UTF-8 `.txt` file containing only active, non-cupboard basket items with quantities greater than `0`.