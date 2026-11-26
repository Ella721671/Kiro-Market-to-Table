---
inclusion: fileMatch
fileMatchPattern: "**/*.py"
---

# Python Coding & Resilience Standards

## 1. Module Imports & Signatures
- Always use `importlib.import_module()` when importing `Commodity-analyser` or `Shopping-planner` because their filenames contain hyphens.
- Preserve existing public function signatures across modules:
  - `Calendar.py`: `run_burnout_check(calendar_name: str) -> dict`
  - `Commodity-analyser.py`: `market_data() -> dict` and `analyse_commodities(data: dict) -> list`
  - `Shopping-planner.py`: `build_shopping_cart(commodity_analysis: list, meal_prep_mode: str, use_live_api: bool = True) -> dict`
  - `main.py`: `run_market_to_table(calendar_name: str) -> dict`

## 2. API Resilience & Fallbacks
- All external HTTP requests (`requests.get`) must include an explicit `timeout` (maximum `5.0` seconds) and catch `requests.RequestException`.
- Never allow a slow or offline third-party API (Google Calendar, Yahoo Finance, or Open Food Facts) to crash the app; always fall back gracefully to local sample/catalogue data.

## 3. Data Types & Formatting
- Use `decimal.Decimal` for financial percentage calculations before converting to `float` for JSON or UI display.
- Always pass `ensure_ascii=False` when serializing JSON strings with `json.dumps()`.
- Format all consumer-facing currency in GBP (`£0.00`).
- Use standard ASCII hyphens (`-`) rather than Unicode em-dashes in user-facing strings.