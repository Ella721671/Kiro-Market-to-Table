# Design Document: Market-to-Table

## Overview

**Market-to-Table** is a schedule-aware, market-responsive grocery and meal-planning web application built with Python, Streamlit, and Kiro's spec-driven workflow. The application solves two everyday household problems: rising supermarket prices and cooking fatigue during high-workload weeks.

The system connects three live data sources into a single weekly shopping workflow:
1. **Personal Schedule Load (`Calendar.py`)**: Reads weekly calendar event density (via Google Calendar API or built-in Demo presets) to classify the user's week into **Calm Week** (`from_scratch`) or **Burnout Week** (`minimal_prep`).
2. **Global Agricultural Commodity Futures (`Commodity-analyser.py`)**: Tracks 13 global food commodities via Yahoo Finance (`yfinance`) to classify each staple as `Surge`, `Bargain`, or `Stable` and generate 30-day price-history sparklines.
3. **UK Supermarket Product & Nutrition Resolution (`Shopping-planner.py`)**: Maps commodity trends and prep modes through a 52-rule `GROCERY_SWAP_MATRIX`, enriches items with live UK product names, NOVA processing groups, and Nutri-Scores via the **Open Food Facts UK API**, and powers an interactive Streamlit storefront (`app.py`) with 1-click budget optimization, standard-shop savings tracking, and dynamic meal suggestions.

---

## Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        Market-to-Table Application                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────┐  ┌─────────────────────┐  ┌─────────────────────┐  │
│  │    Calendar.py      │  │Commodity-analyser.py│  │ Shopping-planner.py │  │
│  │ (Stress & Schedule) │  │ (Futures Volatility)│  │ (UK Swap & API Res.)│  │
│  └──────────┬──────────┘  └──────────┬──────────┘  └──────────┬──────────┘  │
│             │                        │                        │             │
│             └────────────────────────┼────────────────────────┘             │
│                                      ▼                                      │
│                        ┌───────────────────────────┐                        │
│                        │          main.py          │                        │
│                        │  (Pipeline Orchestrator)  │                        │
│                        └─────────────┬─────────────┘                        │
│                                      │                                      │
│                                      ▼                                      │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                          Main/app.py (Streamlit UI)                   │  │
│  │  • Adaptive Theme Engine (Sage Olive vs. Warm Ochre)                  │  │
│  │  • Exact Decimal Checkout & Standard-Shop Savings Banner              │  │
│  │  • 1-Click "Auto-Fit to Budget" Optimizer                             │  │
│  │  • 30-Day Futures Sparkline Split View & Dynamic Meal Filter          │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                      │                                      │
└──────────────┬───────────────────────┬────────────────────────┬─────────────┘
               │                       │                        │
               ▼                       ▼                        ▼
   ┌───────────────────────┐ ┌───────────────────┐ ┌────────────────────────┐
   │  Google Calendar API  │ │   Yahoo Finance   │ │ Open Food Facts UK API │
   │  / Demo Week Presets  │ │   (yfinance =F)   │ │  (uk.openfoodfacts.org)│
   └───────────────────────┘ └───────────────────┘ └────────────────────────┘
```

### Component Responsibilities

1. **Schedule & Burnout Analyzer (`Calendar.py`)**: Fetches upcoming 7-day events from Google Calendar (or deterministic demo schedules), evaluates weekly event load, and outputs `stress_status` and `meal_prep_mode` (`from_scratch` or `minimal_prep`).
2. **Commodity Futures Analyzer (`Commodity-analyser.py`)**: Queries 13 agricultural futures tickers (`ZW=F`, `ZR=F`, `ZC=F`, `ZO=F`, `LE=F`, `HE=F`, `ZS=F`, `DC=F`, `KC=F`, `OJ=F`, `ZL=F`, `SB=F`, `CC=F`), computes price movements, and classifies each commodity as `Surge`, `Bargain`, or `Stable`.
3. **UK Grocery Swap & Product Resolver (`Shopping-planner.py`)**: Filters commodities using `CORE_WEEKLY_STAPLES`, resolves the target UK grocery item from `GROCERY_SWAP_MATRIX[commodity][trend_bucket][mode]`, queries Open Food Facts UK for live product metadata with an automatic fallback circuit breaker, and returns the structured weekly basket.
4. **Pipeline Orchestrator (`main.py`)**: Runs `Calendar.py` → `Commodity-analyser.py` → `Shopping-planner.py` sequentially via `run_market_to_table(calendar_name)` into a unified dictionary payload.
5. **Interactive Consumer Storefront (`Main/app.py`)**: Renders the adaptive editorial UI, manages session state, calculates `Decimal` totals and standard-shop savings, executes 1-click budget optimization, displays 30-day futures sparklines, and dynamically updates meal recipes as basket items are added or removed.
6. **Kiro Governance Layer (`.kiro/`)**: Enforces design tokens, `Decimal` currency rules, and asset-sync hooks across iterative AI-assisted development.

---

## Components and Interfaces

### Core Enumerations and Data Models

```python
from dataclasses import dataclass
from decimal import Decimal
from enum import Enum
from typing import Literal, Optional

class PrepMode(Enum):
    FROM_SCRATCH = "from_scratch"   # Calm Week (Sage Olive #838921)
    MINIMAL_PREP = "minimal_prep"   # Burnout Week (Warm Ochre #D99B21)

class MarketTrend(Enum):
    BARGAIN = "Bargain"
    STABLE = "Stable"
    SURGE = "Surge"

@dataclass
class SwapRule:
    query: str
    fallback_name: str
    fallback_brand: str
    price_gbp: float
    prep_mins: int
    nova: int          # NOVA food processing group (1 = unprocessed, 4 = ultra-processed)
    reason: str

@dataclass
class BasketItem:
    commodity: str
    market_status: str
    item_name: str
    brand: str
    estimated_price_gbp: float
    prep_time_mins: int
    nova_processing_group: int
    nutriscore: str
    swap_reason: str
    source: Literal["Open Food Facts UK (Live)", "Local UK Catalogue"]

@dataclass
class SavingsReport:
    standard_total: Decimal
    smart_total: Decimal
    money_saved: Decimal
    prep_time_saved: int
    surges_dodged: int

@dataclass
class MealRecipe:
    title: str
    mode: str
    commodities: list[str]
    prep_total_mins: int
    cook_time_mins: int
    steps: list[str]
```

### Shopping Planner Interfaces (`Shopping-planner.py`)

```python
def search_open_food_facts(query: str, timeout: float = 3.5) -> Optional[dict]:
    """
    Queries Open Food Facts UK ([https://uk.openfoodfacts.org/cgi/search.pl](https://uk.openfoodfacts.org/cgi/search.pl))
    for a matching UK supermarket product, returning product_name, brand,
    nova_group, and nutriscore, or None if unreachable/empty.
    """

def build_shopping_cart(
    commodity_analysis: list[dict],
    meal_prep_mode: str = "from_scratch",
    use_live_api: bool = True,
) -> dict:
    """
    Resolves commodity signals and schedule mode against GROCERY_SWAP_MATRIX
    and CORE_WEEKLY_STAPLES, returning summary totals and the basket list.
    """
```

### Storefront State & Optimization Interfaces (`Main/app.py`)

```python
def compute_checkout(
    basket: list[dict],
    session_state: dict,
    mode: str,
) -> tuple[Decimal, int, int]:
    """Returns (checkout_total_gbp, total_prep_mins, active_item_count)."""

def compute_savings_vs_standard(
    basket: list[dict],
    session_state: dict,
    mode: str,
) -> dict:
    """Computes GBP saved, prep minutes saved, and surges dodged vs. an unswapped shop."""

def _auto_fit_to_budget(basket: list[dict], mode: str) -> None:
    """
    1-click optimizer: reduces extra quantities first, then removes highest-cost
    Surge items before Stable/Bargain staples until checkout_total <= budget_limit.
    """

def render_meal_cards(
    active_ingredients: list[str],
    mode: str,
    excluded_ingredients: set[str],
) -> None:
    """Filters MEAL_LIBRARY by prep mode and active overlap while hiding meals using removed items."""
```

---

## Data Models

### 1. `GROCERY_SWAP_MATRIX` Structure
A nested dictionary covering all **13 commodities** × **2 market regimes** (`Bargain`, `Surge`) × **2 schedule modes** (`from_scratch`, `minimal_prep`) = **52 curated UK grocery rules**:

```python
GROCERY_SWAP_MATRIX: dict[str, dict[str, dict[str, dict]]] = {
    "<commodity_key>": {
        "Bargain": {
            "from_scratch": {
                "query": str,
                "fallback_name": str,
                "fallback_brand": str,
                "price_gbp": float,
                "prep_mins": int,
                "nova": int,
                "reason": str,
            },
            "minimal_prep": { ... },
        },
        "Surge": {
            "from_scratch": { ... },
            "minimal_prep": { ... },
        },
    }
}
```

### 2. Core Weekly Staples Set
```python
CORE_WEEKLY_STAPLES: set[str] = {"wheat", "beef", "dairy", "coffee"}
```
Commodities with `market_status == "Stable"` are skipped to keep the basket focused **unless** they belong to `CORE_WEEKLY_STAPLES`, ensuring every weekly shop includes foundational carbs, protein, dairy, and morning coffee/tea.

### 3. Pipeline Output Contract (`run_market_to_table`)
```json
{
  "stress_status": "Calm Week (4 events)",
  "meal_prep_mode": "from_scratch",
  "commodity_analysis": [
    {
      "item_name": "wheat",
      "market_status": "Bargain",
      "discount_percent": 6.4,
      "current_trading_price": 540.0
    }
  ],
  "grocery_basket": {
    "meal_prep_mode": "from_scratch",
    "summary": {
      "total_items": 4,
      "estimated_total_gbp": 10.49,
      "total_weekly_prep_mins": 39
    },
    "basket": [
      {
        "commodity": "wheat",
        "market_status": "Bargain (6.4% move)",
        "item_name": "Dried Fusilli Pasta (500g)",
        "brand": "Tesco",
        "estimated_price_gbp": 0.75,
        "prep_time_mins": 12,
        "nova_processing_group": 1,
        "nutriscore": "A",
        "swap_reason": "Wheat is down so we chose bulk dried pasta.",
        "source": "Open Food Facts UK (Live)"
      }
    ]
  }
}
```

### 4. Interactive Session State Schema
```json
{
  "calendar_mode_select": "Demo - Calm Week | Demo - Burnout Week | Live Google Calendar",
  "weekly_budget_slider": 25,
  "selected_commodity": "wheat | null",
  "{mode}_{commodity}_qty": 1,
  "{mode}_{commodity}_cupboard": false,
  "{mode}_removed_items": ["coffee"]
}
```

---

## Correctness Properties

A property is a formal behavior that must hold true across all valid executions of **Market-to-Table**, linking human-readable product requirements to verifiable software guarantees.

* **Property 1: Swap matrix completeness**
  For every commodity in the 13 tracked keys, `GROCERY_SWAP_MATRIX` must define both `"Bargain"` and `"Surge"` regimes, and each regime must define both `"from_scratch"` and `"minimal_prep"` entries with `price_gbp > 0` and `prep_mins >= 0`.
  *Validates: Requirements 1.1, 3.1*

* **Property 2: Schedule mode routing**
  For any input `meal_prep_mode` not equal to `"minimal_prep"`, `build_shopping_cart` must normalize `effective_mode` to `"from_scratch"`; when `meal_prep_mode == "minimal_prep"`, every returned basket item must originate from the `"minimal_prep"` branch of `GROCERY_SWAP_MATRIX`.
  *Validates: Requirements 1.2, 1.3*

* **Property 3: Stable commodity filtering with core-staple preservation**
  For any commodity entry with `market_status == "Stable"`, `build_shopping_cart` must include it if and only if `commodity_key in CORE_WEEKLY_STAPLES`, and must resolve it using the `"Bargain"` trend bucket.
  *Validates: Requirements 2.2, 3.2*

* **Property 4: Surge commodity substitution**
  For any commodity entry with `market_status == "Surge"`, `build_shopping_cart` must resolve the item from the `"Surge"` branch of `GROCERY_SWAP_MATRIX` rather than the `"Bargain"` branch.
  *Validates: Requirements 2.3, 3.3*

* **Property 5: Open Food Facts API circuit-breaker resilience**
  During a single `build_shopping_cart` execution, if `search_open_food_facts` fails or returns `None` on item $i$, `api_reachable` must transition to `False` so items $i+1 \dots n$ resolve immediately from the local UK catalogue without incurring additional network timeouts.
  *Validates: Requirements 3.4, 6.1*

* **Property 6: Exact `Decimal` checkout arithmetic**
  For any basket state, `checkout_total` must equal $\sum \text{Decimal}(\text{price}_i) \times \text{qty}_i$ over all active (non-removed) items where `in_cupboard == False` and `qty > 0`, with zero floating-point drift.
  *Validates: Requirements 4.1, 4.2*

* **Property 7: Cupboard items contribute zero cost**
  For any basket item where `{mode}_{commodity}_cupboard` is `True`, its contribution to `checkout_total` and `total_prep_mins` must be `Decimal("0.00")` and `0` respectively, while remaining available as an ingredient for meal matching.
  *Validates: Requirements 4.3, 5.2*

* **Property 8: Non-negative standard-shop savings invariant**
  For any valid basket configuration, `compute_savings_vs_standard` must satisfy `standard_total >= smart_total` and `money_saved == standard_total - smart_total >= Decimal("0.00")`.
  *Validates: Requirements 4.4*

* **Property 9: 1-Click Auto-Fit budget convergence**
  For any basket where the sum of `Bargain` items is within `budget_limit`, executing `_auto_fit_to_budget` must terminate with `checkout_total <= budget_limit`.
  *Validates: Requirements 4.5*

* **Property 10: Auto-Fit market-priority preservation**
  When `_auto_fit_to_budget` trims quantities or removes items, it must reduce all `qty > 1` counts before removing any single-quantity item, and within each pass must remove `"Surge"` items before `"Stable"` items, and `"Stable"` items before `"Bargain"` items.
  *Validates: Requirements 4.6*

* **Property 11: Strict meal exclusion on basket removal**
  For any meal in `MEAL_LIBRARY`, if any commodity in `meal["commodities"]` is present in `{mode}_removed_items` (or has `qty == 0` and `in_cupboard == False`), `render_meal_cards` must exclude that meal from displayed suggestions, and must restore it when the item is restored to the basket.
  *Validates: Requirements 5.1, 5.3*

* **Property 12: Burnout prep-time reduction**
  Across the 13 tracked commodities in `GROCERY_SWAP_MATRIX`, the mean `prep_mins` in `"minimal_prep"` mode must be strictly less than the mean `prep_mins` in `"from_scratch"` mode.
  *Validates: Requirements 1.4*

---

## Error Handling

### External API & Network Resilience
* **Open Food Facts UK API (`uk.openfoodfacts.org`)**: Uses a strict `3.5s` request timeout and custom `User-Agent` header. Any `requests.RequestException` or empty search result triggers a per-run circuit breaker (`api_reachable = False`) and falls back cleanly to `GROCERY_SWAP_MATRIX` UK supermarket defaults (`source = "Local UK Catalogue"`).
* **Yahoo Finance Futures (`yfinance`)**: Cached for 1 hour (`ttl=3600`). If rate-limited or offline, `fetch_commodity_sparkline` generates a deterministic 30-day curve anchored to the commodity's `Surge` (`+8.4%`), `Bargain` (`-7.6%`), or `Stable` (`+0.6%`) status so the split-screen chart always renders cleanly.
* **Google Calendar OAuth**: If `credentials.json` or `token.json` is missing or expired in Live mode, `Calendar.py` catches authentication exceptions and defaults safely to `"Calm Week"` (`from_scratch`).

### Asset & UI State Resilience
* **Missing Commodity Artwork (`Main/assets/*.png`)**: `get_base64_image` checks `.png`, `.jpg`, `.jpeg`, and `.svg` case-insensitively; if an asset is missing, the UI renders a styled 2-letter monogram badge (`WH`, `BE`, `CO`) and lists missing filenames in a subtle caption rather than crashing with `FileNotFoundError`.
* **Empty Basket Edge Cases**: If a user removes all basket items or sets all quantities to `0`, `compute_checkout` returns `(Decimal("0.00"), 0, 0)`, `build_shopping_list_txt` returns an empty string without crashing, and `render_basket_cards` displays a one-click **Restore All** bar.

---

## Testing Strategy

### Unit Testing (`pytest` / `unittest`)
1. **Swap Matrix & Planner Tests (`Shopping-planner.py`)**:
   * Verify all 13 commodities exist in `GROCERY_SWAP_MATRIX` with valid UK prices, NOVA groups (`1–4`), and non-empty swap reasons.
   * Verify `Stable` commodities outside `CORE_WEEKLY_STAPLES` are excluded, while `wheat`, `beef`, `dairy`, and `coffee` are retained.
   * Mock `requests.get` to verify live product enrichment and confirm the circuit breaker disables subsequent HTTP calls after a timeout.
2. **Financial & Optimizer Tests (`Main/app.py`)**:
   * Test `compute_checkout` with mixed quantities, `"Already in cupboard"` toggles, and removed items.
   * Test `_auto_fit_to_budget` to verify `Surge` items are removed before `Bargain` items when lowering the budget slider.
3. **Dynamic Meal Filtering Tests**:
   * Verify removing `"beef"` hides *"Beef Mince Bolognese with Fusilli"* and restoring `"beef"` brings it back.

### Property-Based Testing (`hypothesis`)
Property-based tests run a minimum of **100 iterations** per property using Python's `hypothesis` library, tagged with `# Feature: market-to-table, Property {N}: {property_text}`:
* **Swap Matrix Invariants (Properties 1–4, 12)**: Generate arbitrary lists of commodity analyses and modes; assert deterministic routing and lower mean prep time in `minimal_prep`.
* **Checkout & Savings Invariants (Properties 6–8)**: Generate random baskets, quantities (`0..10`), and cupboard booleans; assert exact `Decimal` equality and `money_saved >= 0`.
* **Budget Optimizer & Meal Filter Invariants (Properties 9–11)**: Generate random budget limits (`£10..£60`) and removal sets; assert budget convergence and zero leakage of removed ingredients into suggested meals.

### Integration & Manual Verification
* **End-to-End Pipeline Test**: Execute `run_market_to_table("Demo - Calm Week")` and `run_market_to_table("Demo - Burnout Week")` and validate schema compliance.
* **UI Walkthrough Verification**: Confirm theme transition from Sage Olive (`#838921`) to Warm Ochre (`#D99B21`), 50/50 split-view sparkline rendering, `.txt` shopping list download, and responsive card layout.

---

## Implementation Notes

### API Circuit-Breaker Optimization
Because `build_shopping_cart` processes up to 13 commodities sequentially, a slow or offline external API would otherwise multiply `timeout=3.5s` across every item (up to 45 seconds). Setting `api_reachable = False` on the first failed lookup caps worst-case network latency at `3.5s` while preserving instant offline usability.

### Currency Precision & Encoding Safety
All monetary totals in `Main/app.py` convert float prices via `Decimal(str(price))` before multiplication or summation, avoiding binary floating-point artifacts. GBP symbols are formatted via Unicode escape `\u00a3` in `format_gbp()` to guarantee clean UTF-8 downloads across Windows, macOS, and Linux.

### Caching Strategy
* `cached_pipeline(calendar_name)`: `@st.cache_data(ttl=300)` — caches backend pipeline outputs per calendar mode for 5 minutes so UI interactions (quantity steppers, cupboard toggles, item removals) rerun in `<50ms`.
* `fetch_commodity_sparkline(...)`: `@st.cache_data(ttl=3600)` — caches 30-day futures history for 1 hour.
* `get_base64_image(commodity_name)`: `@st.cache_data(ttl=30)` — caches base64-encoded asset URIs in memory.

### Kiro Spec-Driven Engineering Integration
* **Steering Rules (`.kiro/steering/`)**: Codify the Warm Sand (`#EEDFC7`), Sage Olive (`#838921`), and Warm Ochre (`#D99B21`) color tokens, `Decimal` financial arithmetic mandate, and Streamlit HTML component rules so AI-assisted iterations remain visually and structurally consistent.
* **Agent Hook (`.kiro/hooks/`)**: Watches `Main/assets/*.png` so adding a new commodity illustration automatically prompts registration in `COMMODITY_KEYS` and `GROCERY_SWAP_MATRIX`.

---

## File Structure

```text
Market-to-Table/
├── .kiro/
│   ├── hooks/
│   │   └── asset-sync.kiro.hook        # File-watcher hook for Main/assets/*.png
│   ├── specs/
│   │   └── market-to-table/
│   │       └── design.md               # System architecture, matrix & correctness spec
│   └── steering/
│       └── ui-and-theme.md             # Editorial color tokens & Decimal currency rules
├── Main/
│   ├── app.py                          # Streamlit consumer storefront & interactive UI
│   ├── main.py                         # 3-stage pipeline orchestrator
│   ├── Calendar.py                     # Google Calendar & Demo burnout stress analyzer
│   ├── Commodity-analyser.py           # Yahoo Finance agricultural futures analyzer
│   ├── Shopping-planner.py             # GROCERY_SWAP_MATRIX & Open Food Facts UK resolver
│   └── assets/                         # Custom 1:1 commodity illustrations (.png)
│       ├── wheat.png
│       ├── rice.png
│       ├── corn.png
│       ├── oats.png
│       ├── beef.png
│       ├── pork.png
│       ├── soy.png
│       ├── dairy.png
│       ├── coffee.png
│       ├── orange_juice.png
│       ├── cooking_oil.png
│       ├── sugar.png
│       └── cocoa.png
├── requirements.txt                    # streamlit, yfinance, requests, python-dotenv
└── README.md                           # Setup, demo walkthrough & judging guide
```