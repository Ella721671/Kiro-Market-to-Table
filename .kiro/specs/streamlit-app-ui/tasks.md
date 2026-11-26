# Implementation Plan: Streamlit App UI

## Overview

Build `Main/app.py` as a single-file Streamlit application with 13 clearly separated sections that wrap the existing `Calendar.py`, `Commodity-analyser.py`, and `Shopping-planner.py` pipeline behind an editorial consumer grocery interface. Tests live in `tests/test_app.py` covering all 14 correctness properties via Hypothesis and all named example-based unit tests.

## Tasks

- [x] 1. Scaffold file structure and constants
  - Create `Main/app.py` with the full module docstring and section-comment skeleton (`# --- Section N: ... ---`)
  - Define `COLOUR_TOKENS`, `COMMODITY_KEYS`, `COMMODITY_TICKERS`, `SHORT_LABELS`, `EXTRA_RECIPE_HEADINGS`, `MEAL_LIBRARY` (all 12 entries, 6 per mode), and the `PREP_DELTA_LOOKUP` table (per-commodity `from_scratch` vs. `minimal_prep` prep-minute deltas)
  - Add the `Main/assets/` directory creation guard: `(Path(__file__).resolve().parent / "assets").mkdir(parents=True, exist_ok=True)`
  - Create `tests/` directory and `tests/test_app.py` test suite
  - _Requirements: 1.1, 2.1, 5.1_

- [x] 2. Implement `get_base64_image`, `fetch_commodity_sparkline`, and `inject_theme_css`
  - [x] 2.1 Implement `get_base64_image(commodity_name: str) -> str | None`
    - Cache with `@st.cache_data(ttl=30, show_spinner=False)`
    - Search `Main/assets/` case-insensitively for `.png`, `.jpg`, `.jpeg`, `.svg` using `pathlib.Path`
    - Return a `data:image/...;base64,...` URI string on match, `None` otherwise
    - _Requirements: 5.5_

  - [ ] 2.2 Write property test for `get_base64_image` round-trip integrity
    - **Property 10: Base64 Image Round-Trip Integrity**
    - **Validates: Requirements 5.3, 5.5**
    - For each commodity name that has a file in `Main/assets/`, assert the return value starts with `"data:image/"` and can be base64-decoded without error
    - `# Feature: streamlit-app-ui, Property 10: Base64 Image Round-Trip Integrity`

  - [x] 2.3 Implement `fetch_commodity_sparkline(commodity: str, status_word: str, fallback_pct: float | None) -> dict`
    - Cache with `@st.cache_data(ttl=3600, show_spinner=False)`
    - Fetch 30-day futures closing prices via `yfinance` for the commodity's ticker (`COMMODITY_TICKERS`), with a deterministic 30-day fallback curve anchored to `status_word` when offline
    - _Requirements: 6.3_

  - [x] 2.4 Implement `inject_theme_css(primary: str, deep: str) -> None`
    - Build the full CSS block covering all themed surface elements (header banner, savings card border, badges, `1:1` artwork frames, progress bars, tabs, and fixed summary bar) using the passed `primary` and `deep` hex values
    - Apply Warm Sand (`#EEDFC7`) background and Pure White (`#FFFFFF`) elevated-card styling unconditionally
    - Call `st.markdown(..., unsafe_allow_html=True)`
    - _Requirements: 2.1, 2.2, 2.3, 2.6_

  - [ ] 2.5 Write property test for CSS token consistency
    - **Property 11: Theme CSS Colour Token Consistency**
    - **Validates: Requirements 2.2, 2.3**
    - Generate `(primary, deep)` pairs from the Calm Mode and Burnout Mode token sets; verify injected CSS contains the passed tokens and not the opposing mode's tokens
    - `# Feature: streamlit-app-ui, Property 11: Theme CSS Colour Token Consistency`

  - [ ] 2.6 Write unit tests for `inject_theme_css`
    - `test_inject_theme_css_calm_tokens`: Sage Olive (`#838921`, `#3A3D0E`) tokens present, Warm Ochre tokens absent
    - `test_inject_theme_css_burnout_tokens`: Warm Ochre (`#D99B21`, `#5A3E0A`) tokens present, Sage Olive tokens absent
    - _Requirements: 2.2, 2.3_

- [x] 3. Implement `cached_pipeline`, `compute_checkout`, and `compute_savings_vs_standard`
  - [x] 3.1 Implement `cached_pipeline(calendar_name: str) -> dict`
    - Use `@st.cache_data(ttl=300, show_spinner=False)`
    - Import `main` via `importlib.util.spec_from_file_location()` and call `run_market_to_table(calendar_name)`
    - On any exception return `{"error": str(exc)}`
    - _Requirements: 1.1, 1.2, 1.3_

  - [x] 3.2 Implement `get_active_basket` and `compute_checkout(basket, session_state, mode) -> tuple[Decimal, int, int]`
    - Filter out any item present in `"{mode}_removed_items"` via `get_active_basket`
    - Return `(checkout_total_decimal, total_prep_mins, active_item_count)` using `Decimal(str(price))` arithmetic; exclude items where cupboard flag is `True` or `qty == 0`
    - _Requirements: 8.4, 8.5, 11.1_

  - [x] 3.3 Implement `compute_savings_vs_standard(basket, session_state, mode) -> dict`
    - Compare the active smart basket against a standard unswapped supermarket shop
    - Return `standard_total`, `smart_total`, `money_saved` (`max(0.00, standard_total - smart_total)`), `prep_time_saved`, and `surges_dodged`
    - _Requirements: 3.3, 11.1_

  - [ ] 3.4 Write property test for checkout precision
    - **Property 1: Checkout Total Round-Trip Precision**
    - **Validates: Requirements 11.1, 11.2**
    - Generate lists of `(float price, int qty, bool cupboard)` tuples; compare `compute_checkout` result against manual `sum(Decimal(str(p))*q for p,q,c in items if not c)`
    - `# Feature: streamlit-app-ui, Property 1: Checkout Total Round-Trip Precision`

  - [ ] 3.5 Write property test for cupboard exclusion
    - **Property 2: Cupboard Exclusion Invariant**
    - **Validates: Requirements 8.4, 11.1**
    - Generate basket with at least one cupboard item; assert total equals total with that item removed
    - `# Feature: streamlit-app-ui, Property 2: Cupboard Exclusion Invariant`

  - [ ] 3.6 Write property test for zero-quantity and removed-item exclusion
    - **Property 3: Zero Quantity & Removed Item Exclusion Invariant**
    - **Validates: Requirements 8.3, 8.5, 10.2**
    - Generate basket with zero-qty items and items in `"{mode}_removed_items"`; assert total is unaffected
    - `# Feature: streamlit-app-ui, Property 3: Zero Quantity & Removed Item Exclusion Invariant`

  - [ ] 3.7 Write property test for non-negative standard-shop savings
    - **Property 13: Non-Negative Standard-Shop Savings Invariant**
    - **Validates: Requirements 3.3**
    - Generate random baskets and modes; assert `standard_total >= smart_total` and `money_saved >= Decimal("0.00")`
    - `# Feature: streamlit-app-ui, Property 13: Non-Negative Standard-Shop Savings Invariant`

  - [ ] 3.8 Write unit tests for `compute_checkout` and `compute_savings_vs_standard`
    - `test_compute_checkout_excludes_cupboard`
    - `test_compute_checkout_excludes_zero_qty_and_removed`
    - `test_compute_savings_vs_standard`
    - _Requirements: 3.3, 8.4, 8.5, 11.1_

- [x] 4. Implement `build_shopping_list_txt`, stepper/remove/restore state callbacks, and 1-click Auto-Fit optimizer
  - [x] 4.1 Implement `build_shopping_list_txt(basket, session_state, mode) -> str`
    - Return newline-separated lines for active, non-removed items with `qty > 0` and cupboard `False`
    - Format per line: `'{qty}x {item_name} ({brand}) - £{price:.2f}'` using standard ASCII hyphen-minus separators (`-`)
    - _Requirements: 8.5, 10.4, 11.2, 11.3_

  - [x] 4.2 Implement quantity stepper, cupboard, and remove/restore state callbacks
    - `_inc_qty` increments qty up to `99` and clamps; `_dec_qty` decrements down to `0` and clamps
    - `_remove_basket_item`, `_restore_single_item`, and `_restore_basket_items` manage `"{mode}_removed_items"` and clear `selected_commodity` if the inspected item is removed
    - Keys follow `"{mode}_{commodity}_qty"`, `"{mode}_{commodity}_cupboard"`, and `"{mode}_removed_items"`; defaults initialised inside `render_basket_cards` before widgets render
    - _Requirements: 8.3, 8.5, 8.6, 8.7_

  - [x] 4.3 Implement `_status_trim_priority` and `_auto_fit_to_budget(basket, mode) -> None`
    - First decrement extra quantities (`qty > 1`) across active items before removing any single-quantity item
    - Within each pass, prioritise removing `"Surge"` items before `"Stable"` and `"Bargain"` staples (highest price first) until `checkout_total <= budget`
    - Record a human-readable adjustment note in `"{mode}_autofit_note"`
    - _Requirements: 4.5, 11.1_

  - [ ] 4.4 Write property test for shopping list exclusion
    - **Property 5: Shopping List Excludes Cupboard, Zero-Qty, and Removed Items**
    - **Validates: Requirements 8.5, 10.4**
    - Generate basket with mixed cupboard, zero-qty, and removed items; verify excluded items never appear in `build_shopping_list_txt` output
    - `# Feature: streamlit-app-ui, Property 5: Shopping List Excludes Cupboard, Zero-Qty, and Removed Items`

  - [ ] 4.5 Write property test for shopping list format invariant
    - **Property 6: Shopping List Format Invariant**
    - **Validates: Requirements 10.4, 11.2**
    - Generate valid basket items; verify each line matches `r"^\d+x .+ \(.+\) - £\d+\.\d{2}$"` and uses ASCII hyphens
    - `# Feature: streamlit-app-ui, Property 6: Shopping List Format Invariant`

  - [ ] 4.6 Write property test for quantity stepper bounds
    - **Property 4: Quantity Stepper Bounds**
    - **Validates: Requirements 8.3**
    - Generate sequences of `_inc_qty` and `_dec_qty` invocations; assert qty always stays in `[0, 99]`
    - `# Feature: streamlit-app-ui, Property 4: Quantity Stepper Bounds`

  - [ ] 4.7 Write property test for 1-click Auto-Fit convergence and priority order
    - **Property 14: 1-Click Auto-Fit Budget Convergence and Priority Order**
    - **Validates: Requirements 4.5**
    - Generate over-budget baskets with mixed `Surge`, `Stable`, and `Bargain` items; assert `checkout_total <= budget_limit` and `Surge` removal priority
    - `# Feature: streamlit-app-ui, Property 14: 1-Click Auto-Fit Budget Convergence and Priority Order`

  - [ ] 4.8 Write unit tests for `build_shopping_list_txt` and `_auto_fit_to_budget`
    - `test_build_shopping_list_txt_format`
    - `test_auto_fit_to_budget_trims_surge_first`
    - _Requirements: 4.5, 8.5, 10.4_

- [~] 5. Checkpoint — Verify pure-logic helpers pass all tests
  - Ensure all unit and property-based tests pass for tasks 2–4, ask the user if questions arise.

- [x] 6. Implement `render_banner_and_controls` and `render_commodity_grid`
  - [x] 6.1 Implement `render_banner_and_controls(data, checkout_total, savings, basket, default_budget=25) -> None`
    - Call `inject_theme_css` with resolved Calm Mode or Burnout Mode primary/deep colours
    - Render the editorial header banner with `"Market-to-Table"` title and pill-shaped `stress_status` badge (`"Status unavailable"` when absent)
    - Render the 3-metric `Savings_Banner` (`Total Saved vs. Standard Shop`, `Prep Time Saved`, `Market Protection`)
    - Render the 3-option Schedule Mode `st.selectbox`, `Budget_Slider` (£10–£60, default £25), visual budget progress bar, over-budget alert, and 1-click `"⚡ Auto-Fit to £{budget} Budget"` button
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 3.1, 3.2, 3.3, 3.4, 3.5, 4.1, 4.2, 4.3, 4.4, 4.5, 4.6_

  - [x] 6.2 Implement `render_commodity_grid(data: dict, basket: list[dict]) -> None`
    - Render all 13 commodities in a single horizontal `st.columns(13)` strip
    - Each tile: `68×68 px` (`1:1` square) `Art_Print_Frame` with `get_base64_image` or 2-letter `Monogram_Fallback`, concise display label (`"OJ"`, `"Oil"`), colour-coded status badge (`Bargain` = green, `Surge` = red, `Stable` = neutral), and `"View"` button
    - Display helper caption listing missing asset filenames when any `get_base64_image` call returns `None`
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5_

- [x] 7. Implement `render_split_detail_view` and `render_basket_cards`
  - [x] 7.1 Implement `render_split_detail_view(commodity, data, basket, mode) -> None`
    - Render an animated 50/50 split screen when `st.session_state["selected_commodity"]` is set
    - Left 50%: `215×215 px` (`1:1` square) hero `Art_Print_Frame` (or `Monogram_Fallback`), `market_status` pill, product/commodity title, brand, and swap rationale
    - Right 50%: `"✕ Close Split View"` button, 30-day percentage move headline, futures start-to-end prices, shelf price impact, `st.area_chart` 30-day sparkline from `fetch_commodity_sparkline`, and up to 3 recipe headings
    - _Requirements: 6.1, 6.2, 6.3, 6.4_

  - [x] 7.2 Implement `render_basket_cards(basket: list[dict], mode: str) -> None`
    - Render individual `"↩ Restore <Item>"` buttons and a `"Restore All"` button whenever `"{mode}_removed_items"` is non-empty
    - Render one white rounded `Basket_Card` (`border-radius: 20px`) per active item with a `118×118 px` (`1:1` square) `Art_Print_Frame`, middle details (`item_name`, `brand`, prep-time pill, `swap_reason`), and right-aligned line price (`£0.00`) and `market_status` badge
    - Render the interactive control row below each card (`Inspect`, `-`, qty, `+`, `Already in cupboard` `st.checkbox`, and `✕ Remove`)
    - Apply `opacity: 0.55` and `"In Cupboard - £0.00"` badge when cupboard flag is `True`
    - _Requirements: 7.2, 8.1, 8.2, 8.3, 8.4, 8.5, 8.6, 8.7_

- [x] 8. Implement `render_meal_cards` with dynamic removal exclusion
  - [x] 8.1 Implement `render_meal_cards(active_ingredients: list[str], mode: str, excluded_ingredients: set[str]) -> None`
    - Filter `MEAL_LIBRARY` to meals whose `mode` matches `meal_prep_mode` and that share ≥ 2 commodity keys with `active_ingredients`, while strictly excluding any meal containing an ingredient in `excluded_ingredients`
    - Display up to 3 matching `Meal_Card`s with `58×58 px` (`1:1` square) `Art_Print_Frame` thumbnails, prep/cook time pills, `"In basket"` / `"In cupboard"` tags, and numbered preparation steps
    - Display a caption noting how many recipes are hidden due to removed items, and restore meals immediately when removed items are restored
    - _Requirements: 7.3, 9.1, 9.2, 9.3, 9.4, 9.5_

  - [ ] 8.2 Write property test for meal cards mode filter
    - **Property 7: Meal Cards Mode Filter**
    - **Validates: Requirements 9.1**
    - Generate active ingredient sets; call meal-filter logic with each mode; assert all returned meals have matching `mode` field
    - `# Feature: streamlit-app-ui, Property 7: Meal Cards Mode Filter`

  - [ ] 8.3 Write property test for meal ingredient overlap
    - **Property 8: Meal Cards Ingredient Overlap Requirement**
    - **Validates: Requirements 9.1**
    - Generate subsets of `COMMODITY_KEYS`; call meal-filter logic; assert each result shares ≥ 2 keys with the active set
    - `# Feature: streamlit-app-ui, Property 8: Meal Cards Ingredient Overlap Requirement`

  - [ ] 8.4 Write property test for strict meal exclusion on basket removal and restoration
    - **Property 9: Strict Meal Exclusion on Basket Removal & Restoration**
    - **Validates: Requirements 9.3, 9.4**
    - Generate active and excluded commodity sets; assert zero displayed meals require any excluded ingredient, and verify restoration brings matching meals back
    - `# Feature: streamlit-app-ui, Property 9: Strict Meal Exclusion on Basket Removal & Restoration`

- [x] 9. Implement `render_summary_bar` and GBP formatting
  - [x] 9.1 Implement `format_gbp(value: Decimal) -> str` helper
    - Return `f"\u00a3{value:.2f}"` formatted to two decimal places with literal `£` glyph
    - _Requirements: 11.2, 11.3_

  - [x] 9.2 Implement `render_summary_bar(checkout_total, prep_mins, item_count, savings, basket, session_state, mode) -> None`
    - Render a fixed-bottom bar in deep contrast colour with white text (`position: fixed; bottom: 0; z-index: 999`)
    - Display `Impact_Callout` pill (`"Saved £{money_saved:.2f} · {prep_saved} min saved"`), `Checkout_Total` as `£0.00`, total prep minutes, and active item count
    - Include `st.download_button` styled Darker Sand exporting UTF-8 `shopping_list.txt` via `build_shopping_list_txt`
    - _Requirements: 10.1, 10.2, 10.3, 10.4, 11.3_

  - [ ] 9.3 Write property test for GBP format invariant
    - **Property 12: GBP Format Invariant**
    - **Validates: Requirements 11.2, 11.3**
    - Generate arbitrary `Decimal` values; verify `format_gbp(value)` matches `r"^£\d+\.\d{2}$"`
    - `# Feature: streamlit-app-ui, Property 12: GBP Format Invariant`

  - [ ] 9.4 Write unit test for meal library schema
    - `test_meal_library_schema`: verify every entry has required keys, `title` ≤ 60 chars, and valid `mode` and `steps`
    - _Requirements: 9.1, 9.2_

- [x] 10. Implement `main()` and wire all sections together
  - [x] 10.1 Implement `main() -> None` as the Streamlit entry point
    - Set `st.set_page_config(page_title="Market-to-Table", layout="wide")`
    - Call `cached_pipeline(calendar_name)`; check for `"error"` key and show `st.error(...)` while keeping the header banner and controls active
    - Compute initial `checkout_total` and `savings`, call `render_banner_and_controls`, render `render_split_detail_view` when `selected_commodity` is set, and call `render_commodity_grid`
    - Render `st.tabs(["Shopping Basket", "What's on the Table?"])` with `render_basket_cards` and `render_meal_cards` (passing `excluded_ingredients`), recompute totals, and render `render_summary_bar`
    - _Requirements: 1.1, 1.3, 2.4, 2.5, 6.1, 7.1, 7.2, 7.3, 7.4_

  - [ ] 10.2 Write AppTest unit test for header stress pill
    - `test_render_header_stress_pill`: verify stress status pill text matches pipeline `stress_status` using `streamlit.testing.v1.AppTest`
    - _Requirements: 3.1, 3.2_

- [~] 11. Final checkpoint — Ensure all tests pass
  - Ensure all unit and property-based tests pass in `tests/test_app.py`, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements from `requirements.md` for traceability
- Property tests use Hypothesis (`@settings(max_examples=100)`); each is tagged with `# Feature: streamlit-app-ui, Property N: ...`
- `render_basket_cards` must initialise session state keys (`qty`, `cupboard`, `removed_items`) before creating any widget to prevent `KeyError` on first render
- `render_banner_and_controls` and render helpers must treat any `meal_prep_mode` other than `"minimal_prep"` as `"from_scratch"` (Calm Mode default)
- Use `Decimal(str(price))` arithmetic throughout; never `float` for checkout totals, savings comparisons, or Auto-Fit trimming

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1"] },
    { "id": 1, "tasks": ["2.1", "2.3", "2.4", "3.1", "3.2"] },
    { "id": 2, "tasks": ["2.2", "2.5", "2.6", "3.3", "3.4", "3.5", "3.6", "4.1", "4.2", "4.3"] },
    { "id": 3, "tasks": ["3.7", "3.8", "4.4", "4.5", "4.6", "4.7", "4.8", "6.1", "6.2"] },
    { "id": 4, "tasks": ["7.1", "7.2"] },
    { "id": 5, "tasks": ["8.1", "9.1"] },
    { "id": 6, "tasks": ["8.2", "8.3", "8.4", "9.2", "9.3", "9.4"] },
    { "id": 7, "tasks": ["10.1"] },
    { "id": 8, "tasks": ["10.2"] }
  ]
}
```