# Implementation Plan: Market-to-Table

- [x] 1. Set up project structure, Kiro specs, and visual assets
  - Create `Main/` application directory (`Calendar.py`, `Commodity-analyser.py`, `Shopping-planner.py`, `main.py`, `app.py`) and `.kiro/` spec structure
  - Add 1:1 custom commodity illustrations (`.png`) for all 13 tracked staples in `Main/assets/`
  - Implement `get_base64_image()` with `@st.cache_data(ttl=30)` and styled 2-letter monogram fallbacks for missing assets
  - Requirements: 6.2

- [x] 2. Implement Schedule & Burnout Workload Analyser (`Calendar.py`)
  - Define `DEMO_CALENDARS` (`"Demo - Calm Week"`, `"Demo - Burnout Week"`) and the 15-term `BURNOUT_KEYWORDS` urgency lexicon
  - Implement `fetch_google_calendar_events()` over a rolling 7-day UTC window with `_get_sample_calendar_events()` offline fallback
  - Implement `fetch_discord_chat_messages()` to scan team chat urgency signals with graceful empty-list fallback
  - Implement `analyse_burnout()` and `run_burnout_check()` to compute meeting hours, late-evening disruptions (`hour >= 18`), and keyword hits, routing to `from_scratch`, `balanced_prep`, or `minimal_prep`
  - Requirements: 1.1, 1.2, 1.3, 6.1

- [ ]* 2.1 Write property test for schedule mode routing and prep-time reduction
  - Property 2: Schedule mode routing (`minimal_prep` vs. `from_scratch` normalization)
  - Property 12: Burnout prep-time reduction (mean `minimal_prep` minutes < mean `from_scratch` minutes)
  - Validates: Requirements 1.2, 1.3, 1.4

- [x] 3. Implement Global Commodity Futures Volatility Analyser (`Commodity-analyser.py`)
  - Configure `COMMODITY_KEYS` and `COMMODITY_TICKERS` (`ZW=F`, `ZR=F`, `ZC=F`, `ZO=F`, `LE=F`, `HE=F`, `ZS=F`, `DC=F`, `KC=F`, `OJ=F`, `ZL=F`, `SB=F`, `CC=F`)
  - Fetch agricultural futures prices via `yfinance` and classify each staple as `Bargain`, `Stable`, or `Surge`
  - Implement `fetch_commodity_sparkline()` (`@st.cache_data(ttl=3600)`) with a deterministic 30-day fallback curve when offline
  - Requirements: 2.1, 2.3, 6.1

- [x] 4. Implement UK Grocery Swap Matrix & Open Food Facts Resolver (`Shopping-planner.py`)
  - Build `GROCERY_SWAP_MATRIX` covering all 13 commodities × 2 market regimes (`Bargain`, `Surge`) × 2 schedule modes (`from_scratch`, `minimal_prep`)
  - Define `CORE_WEEKLY_STAPLES = {"wheat", "beef", "dairy", "coffee"}` so essential weekly staples are retained even when `Stable`
  - Implement `search_open_food_facts()` (`timeout=3.5s`) to fetch live UK product names, brands, NOVA groups, and Nutri-Scores
  - Implement `build_shopping_cart()` with a per-run API circuit breaker (`api_reachable = False` on first failure) falling back to local UK catalogue defaults
  - Requirements: 3.1, 3.2, 3.3, 3.4, 6.1

- [ ]* 4.1 Write property test for swap matrix completeness
  - Property 1: Swap matrix completeness across all 13 commodities, regimes, and modes
  - Validates: Requirements 1.1, 3.1

- [ ]* 4.2 Write property test for stable staple filtering and surge substitution
  - Property 3: Stable commodity filtering with core-staple preservation
  - Property 4: Surge commodity substitution
  - Validates: Requirements 2.2, 2.3, 3.2, 3.3

- [ ]* 4.3 Write property test for Open Food Facts API circuit-breaker resilience
  - Property 5: Open Food Facts API circuit-breaker resilience disables subsequent HTTP timeouts after a failure
  - Validates: Requirements 3.4, 6.1

- [x] 5. Build Pipeline Orchestrator (`main.py`)
  - Implement `run_market_to_table(calendar_name)` to connect `Calendar.py` → `Commodity-analyser.py` → `Shopping-planner.py` into a unified payload
  - Wrap pipeline execution in `cached_pipeline()` (`@st.cache_data(ttl=300)`) inside `Main/app.py` for instant UI interactions
  - Requirements: 1.1, 2.1, 3.1

- [x] 6. Implement Editorial Theme Engine & Storefront Header (`Main/app.py`)
  - Define `COLOUR_TOKENS` (`#EEDFC7` Warm Sand, `#838921` Sage Olive, `#D99B21` Warm Ochre, `#D4E2E8` Riso Sky)
  - Implement `inject_theme_css()` to switch palettes dynamically between Calm Week (`from_scratch`) and Burnout Week (`minimal_prep`)
  - Implement `render_banner_and_controls()` with Schedule Mode selector and Weekly Grocery Budget slider (`£10–£60`)
  - Requirements: 1.4

- [x] 7. Implement Exact `Decimal` Checkout & Standard-Shop Savings Banner
  - Implement `compute_checkout()` using `Decimal(str(price))` arithmetic and `format_gbp()` (`\u00a3`) formatting
  - Exclude items marked `"Already in cupboard"` or with `qty == 0` from checkout cost and prep minutes
  - Implement `compute_savings_vs_standard()` and render the `"Total Saved vs. Standard Shop"` highlight banner and fixed bottom `render_summary_bar()`
  - Requirements: 4.1, 4.2, 4.3, 4.4

- [ ]* 7.1 Write property test for exact `Decimal` checkout and cupboard zero-cost invariant
  - Property 6: Exact `Decimal` checkout arithmetic
  - Property 7: Cupboard items contribute zero cost and zero prep time
  - Validates: Requirements 4.1, 4.2, 4.3, 5.2

- [ ]* 7.2 Write property test for non-negative standard-shop savings invariant
  - Property 8: Non-negative standard-shop savings invariant (`standard_total >= smart_total`)
  - Validates: Requirements 4.4

- [x] 8. Implement 1-Click "Auto-Fit to Budget" Optimizer
  - Display the `"⚡ Auto-Fit to Budget"` button automatically whenever `checkout_total > budget_val`
  - Implement `_auto_fit_to_budget()` and `_status_trim_priority()` to reduce duplicate quantities (`qty > 1`) first, then remove `Surge` items before `Stable` and `Bargain` staples until within budget
  - Display an inline summary caption explaining which items or quantities were adjusted
  - Requirements: 4.5, 4.6

- [ ]* 8.1 Write property test for Auto-Fit budget convergence and priority preservation
  - Property 9: 1-Click Auto-Fit budget convergence (`checkout_total <= budget_limit`)
  - Property 10: Auto-Fit market-priority preservation (`Surge` trimmed/removed before `Stable` and `Bargain`)
  - Validates: Requirements 4.5, 4.6

- [x] 9. Implement Interactive Basket Cards, 30-Day Sparkline Split View & Shopping List Export
  - Implement `render_commodity_grid()` horizontal strip and 50/50 `render_split_detail_view()` with 30-day area sparkline, shelf impact, and recipe headings
  - Implement `render_basket_cards()` with `+`/`-` quantity steppers, `"Already in cupboard"` checkbox, `"✕ Remove"` button, and individual/full `"Restore"` controls
  - Implement `build_shopping_list_txt()` and UTF-8 `shopping_list.txt` download button
  - Requirements: 2.4, 4.2, 4.3, 6.2, 6.3

- [x] 10. Implement Dynamic Meal Suggestions & Removal Filtering
  - Populate `MEAL_LIBRARY` with `from_scratch` and `minimal_prep` recipes mapped to tracked commodity keys
  - Implement `render_meal_cards()` to match active basket and cupboard ingredients while strictly hiding any recipe requiring a removed basket item (and restoring it when the item is restored)
  - Requirements: 5.1, 5.2, 5.3

- [ ]* 10.1 Write property test for strict meal exclusion on basket removal
  - Property 11: Strict meal exclusion on basket removal and restoration on re-add
  - Validates: Requirements 5.1, 5.3

- [x] 11. Checkpoint - Verify end-to-end integration and tests
  - Verify `Demo - Calm Week`, `Demo - Burnout Week`, and offline API fallbacks work end-to-end with zero unhandled exceptions.

- [ ]* 12. Create README and Hackathon Presentation Documentation
  - Document installation (`pip install -r requirements.txt`), `streamlit run Main/app.py`, and `.env` setup for Google Calendar and Discord
  - Document the 3-stage pipeline architecture, Kiro spec files, and end-to-end demo walkthrough