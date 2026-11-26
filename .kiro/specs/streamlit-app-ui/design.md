Markdown
# Design Document

## Overview

`Main/app.py` is a single-file Streamlit application that wraps the existing three-module pipeline (`Calendar.py`, `Commodity-analyser.py`, `Shopping-planner.py`) behind an editorial consumer grocery interface. The app takes the dictionary returned by `run_market_to_table(calendar_name)` and renders an interactive shopping experience featuring standard-shop savings analytics, a 13-commodity single-row showcase with a 50/50 30-day futures sparkline split view, an interactive basket with quantity, cupboard, remove/restore, and 1-click Auto-Fit budget controls, dynamic recipe filtering, and a downloadable shopping list.

The design is organised around two parallel concerns:

1. **Data flow & state management** — cached pipeline and market-history calls populate session state without redundant API hits; every subsequent widget interaction (stepper click, cupboard toggle, item removal/restoration, budget drag, or 1-click Auto-Fit) reacts in-process in milliseconds.
2. **Visual theming** — a single CSS injection at render time switches the entire colour palette between Calm Mode (Sage Olive) and Burnout Mode (Warm Ochre) depending on `meal_prep_mode`.

The file is structured as 13 clearly separated sections so individual render functions and pure-logic helpers can be read, tested, and maintained without touching the Streamlit entry point.

---

## Architecture

### Component Interaction Diagram

```mermaid
flowchart TD
    A[User: select schedule mode] --> B[cached_pipeline\n@st.cache_data ttl=300]
    B --> C[run_market_to_table\nMain/main.py]
    C --> D[Calendar.py]
    C --> E[Commodity-analyser.py]
    C --> F[Shopping-planner.py]
    C --> G[Pipeline dict result]
    G --> H[inject_theme_css\nprimary / deep]
    G --> I[render_banner_and_controls\nHeader + Savings + Budget + Auto-Fit]
    G --> J{selected_commodity?}
    J -- Yes --> K[render_split_detail_view\n50/50 Hero + 30d Sparkline]
    G --> L[render_commodity_grid\n13-col Single-Row Strip]
    G --> M[View Tabs]
    M --> N[render_basket_cards\nSteppers + Cupboard + Remove/Restore]
    M --> O[render_meal_cards\nFilters out excluded_ingredients]
    N --> P[st.session_state\nqty + cupboard + removed_items]
    O --> P
    P --> Q[compute_checkout &\ncompute_savings_vs_standard]
    Q --> R[render_summary_bar]
    R --> S[build_shopping_list_txt\nUTF-8 .txt download]
```

### Data Flow Summary

1. `main()` calls `cached_pipeline(calendar_name)` — the sole entry point into the backend pipeline.
2. The returned dict is destructured into `stress_status`, `meal_prep_mode`, and `grocery_basket`.
3. `compute_checkout` and `compute_savings_vs_standard` compute initial `Decimal` totals and savings metrics from `st.session_state`, excluding any commodity in `"{mode}_removed_items"`.
4. `render_banner_and_controls` invokes `inject_theme_css(primary, deep)` and renders the editorial banner, the 3-metric standard-shop savings card, the schedule selector, the budget slider/progress bar, and the 1-click **Auto-Fit to Budget** button when over budget.
5. If `st.session_state["selected_commodity"]` is set, `render_split_detail_view` renders an animated 50/50 split panel with a 30-day futures area chart (`fetch_commodity_sparkline`) above the 13-commodity strip.
6. Inside `st.tabs(["Shopping Basket", "What's on the Table?"])`, `render_basket_cards` manages per-item quantities, cupboard checkboxes, and remove/restore actions, while `render_meal_cards` filters `MEAL_LIBRARY` to strictly hide any recipe requiring a removed ingredient.
7. `main()` recomputes checkout and savings totals after basket interactions and passes them into `render_summary_bar`.

### Caching Strategy

```text
cached_pipeline(calendar_name: str) -> dict
    @st.cache_data(ttl=300, show_spinner=False)

fetch_commodity_sparkline(commodity: str, status_word: str, fallback_pct: float | None) -> dict
    @st.cache_data(ttl=3600, show_spinner=False)

get_base64_image(commodity_name: str) -> str | None
    @st.cache_data(ttl=30, show_spinner=False)
```

Streamlit's `@st.cache_data` decorator serialises pipeline results by calendar name for 300 seconds, 30-day Yahoo Finance futures histories for 3,600 seconds, and base64-encoded asset URIs for 30 seconds. Local basket interactions never trigger a cache miss.

---

## Components and Interfaces

### Public Function Signatures

```python
# Section 1: Constants
COLOUR_TOKENS: dict[str, str]              # design-system hex values
COMMODITY_KEYS: list[str]                  # 13 commodity keys in display order
COMMODITY_TICKERS: dict[str, str]          # commodity key -> Yahoo Finance futures ticker
SHORT_LABELS: dict[str, str]               # compact strip labels ("OJ", "Oil")
EXTRA_RECIPE_HEADINGS: dict[str, list[str]]# fallback recipe titles for split detail view
MEAL_LIBRARY: list[dict]                   # 12 static meal definitions (6 per mode)
PREP_DELTA_LOOKUP: dict[str, dict[str, int]] # per-commodity prep minutes by mode

# Section 2: Image, History & State Callbacks
def _norm_key(val: str) -> str:
    """Normalise commodity names to lowercase snake_case keys."""

@st.cache_data(ttl=30, show_spinner=False)
def get_base64_image(commodity_name: str) -> str | None:
    """Search Main/assets/ case-insensitively for .png/.jpg/.jpeg/.svg.
    Return data:image/...;base64,... URI string, or None."""

@st.cache_data(ttl=3600, show_spinner=False)
def fetch_commodity_sparkline(
    commodity: str,
    status_word: str,
    fallback_pct: float | None,
) -> dict[str, Any]:
    """Fetch 30-day futures closing prices via yfinance, with deterministic fallback curve."""

def _dec_qty(qty_key: str) -> None: ...
def _inc_qty(qty_key: str) -> None: ...
def _select_commodity(commodity: str) -> None: ...
def _close_split_view() -> None: ...
def _remove_basket_item(mode: str, commodity: str) -> None: ...
def _restore_single_item(mode: str, commodity: str) -> None: ...
def _restore_basket_items(mode: str) -> None: ...
def _status_trim_priority(status: str) -> int: ...
def _auto_fit_to_budget(basket: list[dict], mode: str) -> None:
    """1-click optimizer: trims extra quantities first, then removes Surge/expensive items."""

# Section 3: CSS Theming
def inject_theme_css(primary: str, deep: str) -> None:
    """Build full editorial CSS block and call st.markdown(..., unsafe_allow_html=True)."""

# Section 4: Pipeline Cache
@st.cache_data(ttl=300, show_spinner=False)
def cached_pipeline(calendar_name: str) -> dict:
    """Import main via importlib.util, call run_market_to_table, return result dict.
    On exception return {"error": str(exc)}."""

# Section 5: Checkout & Standard-Shop Comparison Logic
def get_active_basket(basket: list[dict], session_state: Any, mode: str) -> list[dict]:
    """Return basket items that have not been removed by the user."""

def compute_checkout(
    basket: list[dict],
    session_state: Any,
    mode: str,
) -> tuple[Decimal, int, int]:
    """Return (checkout_total_decimal, total_prep_mins, active_item_count).
    Excludes removed items, cupboard items, and qty == 0 items."""

def compute_savings_vs_standard(
    basket: list[dict],
    session_state: Any,
    mode: str,
) -> dict[str, Any]:
    """Compare smart basket against a standard unswapped supermarket shop.
    Returns standard_total, smart_total, money_saved, prep_time_saved, surges_dodged."""

# Section 6: Shopping List Text
def build_shopping_list_txt(
    basket: list[dict],
    session_state: Any,
    mode: str,
) -> str:
    """Return newline-separated lines for active items with qty > 0 and cupboard False.
    Format per line: '{qty}x {item_name} ({brand}) - £{price:.2f}'."""

# Section 7: Prominent Banner, Savings Highlight & Top Controls
def render_banner_and_controls(
    data: dict,
    checkout_total: Decimal,
    savings: dict[str, Any],
    basket: list[dict],
    default_budget: int = 25,
) -> None:
    """Render header banner, Total Saved highlight card, schedule selectbox, budget slider,
    progress bar, and 1-click Auto-Fit button when over budget."""

# Section 8: Single-Row Commodity Strip
def render_commodity_grid(data: dict, basket: list[dict]) -> None:
    """Render all 13 commodities in a single horizontal 13-column strip with View buttons."""

# Section 9: Basket Cards
def render_basket_cards(basket: list[dict], mode: str) -> None:
    """Render restore bar for removed items and Basket_Cards with steppers, cupboard toggle,
    Inspect, and Remove buttons."""

# Section 10: Meal Cards
def render_meal_cards(
    active_ingredients: list[str],
    mode: str,
    excluded_ingredients: set[str],
) -> None:
    """Filter MEAL_LIBRARY by mode and active_ingredients overlap while strictly hiding meals
    requiring any ingredient in excluded_ingredients."""

# Section 11: Summary Bar
def format_gbp(value: Decimal) -> str:
    """Return '£{value:.2f}' using Unicode escape \\u00a3."""

def render_summary_bar(
    checkout_total: Decimal,
    prep_mins: int,
    item_count: int,
    savings: dict[str, Any],
    basket: list[dict],
    session_state: Any,
    mode: str,
) -> None:
    """Render fixed bottom bar with savings pill, totals, and UTF-8 download button."""

# Section 12: Split Detail View
def render_split_detail_view(
    commodity: str,
    data: dict,
    basket: list[dict],
    mode: str,
) -> None:
    """Render 50/50 split screen with hero artwork, 30-day futures sparkline, shelf price
    impact, and up to 3 recipe headings."""

# Section 13: Entry Point
def main() -> None:
    """Streamlit entry point. Wire all render functions together."""
```

### Session State Key Convention

| Key pattern | Type | Default | Resets on mode change? |
|---|---|---|---|
| `"{mode}_{commodity}_qty"` | `int` | `1` | Yes — scoped by mode prefix |
| `"{mode}_{commodity}_cupboard"` | `bool` | `False` | Yes — scoped by mode prefix |
| `"{mode}_removed_items"` | `list[str]` | `[]` | Yes — scoped by mode prefix |
| `"{mode}_autofit_note"` | `str \| None` | `None` | Yes — scoped by mode prefix |
| `"selected_commodity"` | `str \| None` | `None` | Shared across views; cleared on close or item removal |
| `"calendar_mode_select"` | `str` | `"Demo - Calm Week"` | Global schedule mode selector |
| `"weekly_budget_slider"` | `int` | `25` | Global weekly budget limit (`£10–£60`) |

Initialisation runs inside `render_basket_cards` before any widget is rendered (`if key not in st.session_state`), preventing `KeyError` on first load.

---

## Data Models

### Colour Token Constants

```python
COLOUR_TOKENS: dict[str, str] = {
    "warm_sand":         "#EEDFC7",
    "pure_white":        "#FFFFFF",
    "riso_sky":          "#D4E2E8",
    "darker_sand":       "#DFC9A6",
    "darker_sand_hover": "#D2B78C",
    "warm_slate":        "#6E6559",
    # Calm Mode (from_scratch)
    "sage_olive":        "#838921",
    "deep_forest":       "#3A3D0E",
    # Burnout Mode (minimal_prep)
    "warm_ochre":        "#D99B21",
    "deep_roasted":      "#5A3E0A",
}
```

### Commodity Keys & Futures Tickers

```python
COMMODITY_KEYS: list[str] = [
    "wheat", "rice", "corn", "oats", "beef",
    "pork", "soy", "dairy", "coffee",
    "orange_juice", "cooking_oil", "sugar", "cocoa",
]

COMMODITY_TICKERS: dict[str, str] = {
    "wheat": "ZW=F", "rice": "ZR=F", "corn": "ZC=F", "oats": "ZO=F",
    "beef": "LE=F", "pork": "HE=F", "soy": "ZS=F", "dairy": "DC=F",
    "coffee": "KC=F", "orange_juice": "OJ=F", "cooking_oil": "ZL=F",
    "sugar": "SB=F", "cocoa": "CC=F",
}
```

### Meal Library Entry Schema

```python
{
    "title":           str,          # <= 60 chars
    "mode":            str,          # "from_scratch" | "minimal_prep"
    "commodities":     list[str],    # commodity keys used as primary ingredients
    "prep_total_mins": int,          # total prep + cook time
    "cook_time_mins":  int,          # subset of prep_total_mins involving heat
    "steps":           list[str],    # 2-3 sequential instruction strings
}
```

#### Meal Library (12 entries, 6 per mode)

```python
MEAL_LIBRARY: list[dict] = [
    # --- from_scratch ---
    {
        "title": "Beef Mince Bolognese with Fusilli",
        "mode": "from_scratch",
        "commodities": ["wheat", "beef", "cooking_oil"],
        "prep_total_mins": 35,
        "cook_time_mins": 25,
        "steps": [
            "Brown 500g beef mince in a drizzle of oil over medium heat for 8 mins.",
            "Stir in tomato paste and stock and simmer for 15 mins while fusilli cooks in salted water.",
            "Drain pasta, combine with sauce, and top with grated cheddar.",
        ],
    },
    {
        "title": "Porridge with Honey and Cinnamon",
        "mode": "from_scratch",
        "commodities": ["oats", "dairy", "sugar"],
        "prep_total_mins": 8,
        "cook_time_mins": 6,
        "steps": [
            "Combine 50g oats with 300ml milk in a saucepan over medium heat.",
            "Stir continuously for 5–6 mins until thick and creamy.",
            "Spoon into a bowl, drizzle with honey, and dust with cinnamon.",
        ],
    },
    {
        "title": "Tofu Stir-Fry with Rice",
        "mode": "from_scratch",
        "commodities": ["rice", "soy", "cooking_oil"],
        "prep_total_mins": 25,
        "cook_time_mins": 15,
        "steps": [
            "Rinse 150g basmati rice and simmer in 300ml water for 12 mins.",
            "Press and cube tofu, fry in oil 3–4 mins each side until golden.",
            "Toss rice with tofu and soy sauce; season and serve hot with your choice of veg.",
        ],
    },
    {
        "title": "Corn Tortilla Tacos with Chicken",
        "mode": "from_scratch",
        "commodities": ["corn", "pork", "dairy"],
        "prep_total_mins": 25,
        "cook_time_mins": 18,
        "steps": [
            "Pan-fry chicken or pork strips in a dry skillet for 5 mins per side with your choice of spices.",
            "Warm tortillas directly on the hob flame for 30 seconds each.",
            "Fill with meat, shredded cheese, and squeeze of lime or lemon.",
        ],
    },
    {
        "title": "Filter Coffee and Cheddar Toast",
        "mode": "from_scratch",
        "commodities": ["coffee", "wheat", "dairy"],
        "prep_total_mins": 15,
        "cook_time_mins": 5,
        "steps": [
            "Grind 18g beans and brew filter coffee for 4 mins.",
            "Toast two slices of bread until golden, then top with sliced cheddar.",
            "Grill under medium heat for 2 mins until cheese melts.",
        ],
    },
    {
        "title": "Orange Juice Overnight Oats",
        "mode": "from_scratch",
        "commodities": ["oats", "orange_juice", "dairy"],
        "prep_total_mins": 20,
        "cook_time_mins": 0,
        "steps": [
            "Combine 60g oats, 100ml orange juice, and 100ml milk in a jar.",
            "Stir well, seal, and refrigerate overnight (minimum 8 hours).",
            "Serve cold topped with fresh fruit or a drizzle of honey.",
        ],
    },

    # --- minimal_prep ---
    {
        "title": "Microwave Pasta with Grated Cheese",
        "mode": "minimal_prep",
        "commodities": ["wheat", "dairy"],
        "prep_total_mins": 4,
        "cook_time_mins": 0,
        "steps": [
            "Pierce microwave pasta pouch and heat on full power for 3 mins.",
            "Tear open and tip into a bowl; scatter pre-grated cheddar on top.",
        ],
    },
    {
        "title": "Instant Coffee and Flapjack Bites",
        "mode": "minimal_prep",
        "commodities": ["coffee", "oats", "sugar"],
        "prep_total_mins": 3,
        "cook_time_mins": 0,
        "steps": [
            "Add 1 heaped tsp instant granules to a mug of just-boiled water and stir.",
            "Open flapjack bites tub and portion 3–4 pieces into a small bowl.",
        ],
    },
    {
        "title": "Steamed Rice Pouch with Cooked Chicken",
        "mode": "minimal_prep",
        "commodities": ["rice", "pork"],
        "prep_total_mins": 3,
        "cook_time_mins": 0,
        "steps": [
            "Microwave basmati rice pouch for 2 mins per pack instructions.",
            "Slice pre-cooked chicken breast and arrange over the rice.",
            "Drizzle with soy sauce from a sachet and serve immediately.",
        ],
    },
    {
        "title": "Pulled Pork Pitta Pockets",
        "mode": "minimal_prep",
        "commodities": ["pork", "corn"],
        "prep_total_mins": 5,
        "cook_time_mins": 0,
        "steps": [
            "Toast pitta breads in a toaster for 1–2 mins until puffed.",
            "Spoon BBQ pulled pork from the sachet into each pitta.",
            "Top with sweetcorn from a drained tin and serve.",
        ],
    },
    {
        "title": "Orange Juice, Banana, and Oat Drink",
        "mode": "minimal_prep",
        "commodities": ["orange_juice", "oats"],
        "prep_total_mins": 3,
        "cook_time_mins": 0,
        "steps": [
            "Pour chilled OJ into a glass over ice.",
            "Peel a banana and open one oat breakfast drink pouch.",
            "Serve together as a no-cook breakfast set.",
        ],
    },
    {
        "title": "Dark Chocolate and Clementines",
        "mode": "minimal_prep",
        "commodities": ["cocoa", "sugar"],
        "prep_total_mins": 3,
        "cook_time_mins": 0,
        "steps": [
            "Break two squares of dark chocolate onto a small plate.",
            "Peel two clementines and segment them alongside the chocolate.",
        ],
    },
]
```

### Standard-Shop Savings Return Shape

```python
{
    "standard_total":  Decimal,  # unswapped supermarket baseline total (quantized 0.01)
    "smart_total":     Decimal,  # actual active basket total (quantized 0.01)
    "money_saved":     Decimal,  # max(0.00, standard_total - smart_total)
    "prep_time_saved": int,      # minutes saved vs. baseline prep
    "surges_dodged":   int,      # count of active items with market_status starting "Surge"
}
```

---

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system — essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Checkout Total Round-Trip Precision

For any basket of active items with arbitrary `estimated_price_gbp` floats and arbitrary integer quantities, `compute_checkout` SHALL produce a `Decimal` total that matches the sum of `Decimal(str(price)) * qty` for all active purchasable items to within `£0.01`.

**Validates: Requirements 11.1, 11.2**

### Property 2: Cupboard Exclusion Invariant

For any basket state and any item, if that item's `Cupboard_State` is `True`, then `compute_checkout` SHALL return a total that excludes that item's price and prep-time contribution, regardless of its `Quantity_State`.

**Validates: Requirements 8.4, 11.1**

### Property 3: Zero Quantity & Removed Item Exclusion Invariant

For any basket state and any item, if that item's `Quantity_State` is `0` OR its commodity key is present in `"{mode}_removed_items"`, then `compute_checkout` SHALL exclude that item's price contribution.

**Validates: Requirements 8.3, 8.5, 10.2**

### Property 4: Quantity Stepper Bounds

For any item and any sequence of `_inc_qty` (`"+"`) and `_dec_qty` (`"-"`) callback invocations, `Quantity_State` SHALL remain within the closed interval `[0, 99]` after every activation.

**Validates: Requirements 8.3**

### Property 5: Shopping List Excludes Cupboard, Zero-Qty, and Removed Items

For any basket state, `build_shopping_list_txt` SHALL return a string containing no line for any item where `Cupboard_State` is `True`, `Quantity_State` is `0`, or the commodity is in `"{mode}_removed_items"`.

**Validates: Requirements 8.5, 10.4**

### Property 6: Shopping List Format Invariant

For any active basket item included in `build_shopping_list_txt`, the generated line SHALL match the pattern `"{qty}x {item_name} ({brand}) - £{price:.2f}"` and use standard ASCII hyphen-minus separators (`-`).

**Validates: Requirements 10.4, 11.2**

### Property 7: Meal Cards Mode Filter

For any set of active ingredients and any `mode`, `render_meal_cards` SHALL display only meals whose `mode` field matches `meal_prep_mode`, never mixing `from_scratch` meals into `minimal_prep` renders or vice versa.

**Validates: Requirements 9.1**

### Property 8: Meal Cards Ingredient Overlap Requirement

For any set of active ingredients, every displayed Meal_Card SHALL share at least 2 commodity keys with the active ingredient set.

**Validates: Requirements 9.1**

### Property 9: Strict Meal Exclusion on Basket Removal & Restoration

For any meal in `MEAL_LIBRARY`, if any commodity in `meal["commodities"]` is present in `excluded_ingredients` (items in `"{mode}_removed_items"` or items with `qty == 0` and `in_cupboard == False`), `render_meal_cards` SHALL exclude that meal from displayed suggestions, and SHALL restore it once the item is restored to the basket.

**Validates: Requirements 9.3, 9.4**

### Property 10: Base64 Image Round-Trip Integrity

For any commodity name that has a corresponding file in `Main/assets/`, `get_base64_image(commodity_name)` SHALL return a non-None string beginning with `"data:image/"` whose payload can be base64-decoded without error.

**Validates: Requirements 5.3, 5.5**

### Property 11: Theme CSS Colour Token Consistency

For any call to `inject_theme_css(primary, deep)`, the injected CSS string SHALL contain the passed `primary` and `deep` hex values and SHALL NOT contain the hex values belonging to the opposing mode (`#838921`/`#3A3D0E` vs. `#D99B21`/`#5A3E0A`).

**Validates: Requirements 2.2, 2.3**

### Property 12: GBP Format Invariant

For any `Decimal` value passed to `format_gbp(value)` or formatted in `build_shopping_list_txt`, the resulting string SHALL match `r"^£\d+\.\d{2}$"` using the literal `£` glyph (`\u00a3`).

**Validates: Requirements 11.2, 11.3**

### Property 13: Non-Negative Standard-Shop Savings Invariant

For any valid basket configuration, `compute_savings_vs_standard` SHALL satisfy `standard_total >= smart_total` and `money_saved == standard_total - smart_total >= Decimal("0.00")`.

**Validates: Requirements 3.3**

### Property 14: 1-Click Auto-Fit Budget Convergence and Priority Order

For any basket where the sum of `Bargain` items is less than or equal to `budget_limit`, executing `_auto_fit_to_budget(basket, mode)` SHALL terminate with `checkout_total <= budget_limit`, reducing all `qty > 1` counts before removing single-quantity items and removing `"Surge"` items before `"Stable"` and `"Bargain"` staples.

**Validates: Requirements 4.5**

---

## Error Handling

### Pipeline Failure

`cached_pipeline` wraps `run_market_to_table` inside `try/except Exception` and returns `{"error": str(exc)}` on failure. `main()` checks `"error" in data` before rendering data-dependent sections:

- Renders the header banner with `"Status unavailable"` and keeps top controls functional.
- Displays `st.error("Could not load market data. Please try again shortly.")`.
- Skips commodity strip, basket cards, meal cards, and summary bar rendering.

### Missing Assets

`get_base64_image` returns `None` when no matching file exists in `Main/assets/`. All call sites (`render_commodity_grid`, `render_basket_cards`, `render_meal_cards`, `render_split_detail_view`) fall back to a themed 2-letter Monogram_Fallback badge, and `render_commodity_grid` lists missing filenames in a subtle `st.caption`.

### Sparkline & External API Fallbacks

`fetch_commodity_sparkline` wraps `yfinance` calls in `try/except Exception` and falls back to a smooth deterministic 30-day curve anchored to `status_word` (`+8.4%` for `Surge`, `-7.6%` for `Bargain`, `+0.6%` for `Stable`) so the 50/50 split view always renders even offline.

### Empty Basket & Full Removal States

When a user removes every item from the basket or sets all quantities to `0`, `get_active_basket` returns `[]`, `compute_checkout` returns `(Decimal("0.00"), 0, 0)`, `render_basket_cards` displays the one-click **Restore** bar with an informational prompt, and `render_meal_cards` hides recipes requiring removed ingredients.

### Invalid `meal_prep_mode` Values

`render_banner_and_controls` and render helpers treat any `meal_prep_mode` other than `"minimal_prep"` as Calm Mode (`"from_scratch"`), safely handling `"balanced_prep"` emitted during Moderate stress weeks.

---

## Testing Strategy

The pure-logic helpers (`compute_checkout`, `compute_savings_vs_standard`, `build_shopping_list_txt`, `get_base64_image`, `inject_theme_css`, `_auto_fit_to_budget`, `format_gbp`, and meal filtering) are decoupled from Streamlit DOM rendering and tested in isolation via unit and property-based tests.

### Unit Tests (example-based)

- `test_compute_checkout_excludes_cupboard`: Verify items with `Cupboard_State=True` contribute `Decimal("0")` to total.
- `test_compute_checkout_excludes_zero_qty_and_removed`: Verify items with `qty=0` or in `"{mode}_removed_items"` contribute `Decimal("0")`.
- `test_compute_savings_vs_standard`: Verify `standard_total >= smart_total` and `surges_dodged` count.
- `test_auto_fit_to_budget_trims_surge_first`: Verify `_auto_fit_to_budget` reduces `qty > 1` first and removes `Surge` items before `Bargain` items.
- `test_build_shopping_list_txt_format`: Verify output line format `"{qty}x {item_name} ({brand}) - £{price:.2f}"` and exclusion of cupboard/removed items.
- `test_get_base64_image_missing_and_present`: Verify `None` when missing and valid `data:image/` URI when present.
- `test_inject_theme_css_tokens`: Verify Calm Mode (`#838921`, `#3A3D0E`) and Burnout Mode (`#D99B21`, `#5A3E0A`) CSS isolation.
- `test_meal_filtering_excludes_removed_ingredients`: Verify removing `"beef"` hides `"Beef Mince Bolognese with Fusilli"` and restoring `"beef"` brings it back.

### Property-Based Tests (Hypothesis)

**Library:** [Hypothesis](https://hypothesis.readthedocs.io/) — minimum 100 iterations per property (`@settings(max_examples=100)`), tagged with `# Feature: streamlit-app-ui, Property {N}: {property_text}`:

| Property | Test approach |
|---|---|
| **Property 1** (checkout precision) | Generate lists of `(float price, int qty, bool cupboard)` tuples; compare `compute_checkout` against `sum(Decimal(str(p))*q for p,q,c in items if not c)` |
| **Property 2 & 3** (cupboard, zero-qty & removal exclusion) | Generate baskets with mixed cupboard flags, zero quantities, and removed keys; assert excluded items contribute `0` |
| **Property 4** (qty stepper bounds) | Generate sequences of `_inc_qty` and `_dec_qty` calls; assert `0 <= qty <= 99` after every step |
| **Property 5 & 6** (shopping list filtering & format) | Generate mixed baskets; verify excluded items are omitted and included lines match `r"^\d+x .+ \(.+\) - £\d+\.\d{2}$"` \vert{} \vert{} **Property 7, 8 & 9** (meal mode, overlap & removal exclusion) \vert{} Generate subsets of `COMMODITY_KEYS` and `excluded_ingredients`; assert matching `mode`, `>= 2` active overlap, and zero overlap with `excluded_ingredients` \vert{} \vert{} **Property 10** (base64 round-trip) \vert{} Verify `get_base64_image` returns a decodable `data:image/` URI for every asset file in `Main/assets/` \vert{} \vert{} **Property 11** (CSS token consistency) \vert{} Generate `(primary, deep)` pairs from Calm and Burnout palettes; verify opposing palette hex codes are absent \vert{} \vert{} **Property 12** (GBP format) \vert{} Generate arbitrary `Decimal` values; verify `format_gbp(value)` matches `r"^£\d+\.\d{2}$"` |
| **Property 13** (non-negative savings) | Generate random baskets and modes; assert `standard_total >= smart_total` and `money_saved >= Decimal("0.00")` |
| **Property 14** (Auto-Fit convergence & priority) | Generate over-budget baskets with mixed `Surge`, `Stable`, and `Bargain` items; assert `checkout_total <= budget_limit` and `Surge` removal priority |