# Requirements Document

## Introduction

The Streamlit App UI is a sleek, editorial consumer grocery web application at `Main/app.py`. It connects to the existing `run_market_to_table()` pipeline to display live commodity-aware grocery recommendations, a standard-shop savings highlight banner, a 13-commodity single-row showcase with a 50/50 30-day price-history split view, an interactive shopping basket with quantity, cupboard, remove/restore, and 1-click Auto-Fit budget controls, dynamic meal inspiration that hides recipes requiring removed ingredients, and a downloadable shopping list — all rendered within a dual-mode visual theme that shifts between Calm Week (Sage Olive) and Burnout Week (Warm Ochre) palettes.

## Glossary

- **App**: The Streamlit web application running at `Main/app.py`.
- **Pipeline**: The `run_market_to_table(calendar_name: str) -> dict` function imported from `Main/main.py` via `importlib.util.spec_from_file_location()`.
- **Calm_Mode**: The UI theme and behaviour active when `meal_prep_mode` is `"from_scratch"` (Sage Olive palette, `#838921` / `#3A3D0E`).
- **Burnout_Mode**: The UI theme and behaviour active when `meal_prep_mode` is `"minimal_prep"` (Warm Ochre palette, `#D99B21` / `#5A3E0A`).
- **Active_Theme**: The colour set currently applied — either Calm_Mode or Burnout_Mode — determined by the selected calendar mode.
- **Savings_Banner**: The top highlight card displaying total GBP saved vs. a standard unswapped shop, prep minutes saved, and market surges dodged.
- **Commodity_Strip**: The single-row horizontal showcase displaying all 13 tracked commodities with square artwork frames, status badges, and `"View"` buttons.
- **Split_Detail_View**: The animated 50/50 split-screen panel opened when inspecting a commodity, displaying a hero artwork card alongside a 30-day futures sparkline, shelf price impact, and recipe headings.
- **Basket_Item**: A single grocery product entry returned inside `grocery_basket.basket[]` by the Pipeline.
- **Basket_Card**: The horizontal white rounded card rendering one active Basket_Item with a `1:1` square art-print frame, product details, and price, paired with an interactive control row (`Inspect`, `-`, qty, `+`, `Already in cupboard`, `✕ Remove`).
- **Art_Print_Frame**: A `1:1` square Muted Risograph Sky (`#D4E2E8`) image container (`68×68 px` in Commodity_Strip, `118×118 px` in Basket_Card, `215×215 px` in Split_Detail_View, `58×58 px` in Meal_Card) with theme-coloured border and risograph-stripe accents.
- **Quantity_State**: The per-item integer quantity stored in `st.session_state` (`"{mode}_{commodity}_qty"`), minimum `0`, maximum `99`, default `1`.
- **Cupboard_State**: The per-item boolean `in_cupboard` flag stored in `st.session_state` (`"{mode}_{commodity}_cupboard"`); `True` when the user marks an item as already owned.
- **Removed_Items_State**: The per-mode list of removed commodity keys stored in `st.session_state` (`"{mode}_removed_items"`).
- **Checkout_Total**: The exact `Decimal` sum of `estimated_price_gbp × quantity` for all active (non-removed) Basket_Items where `Cupboard_State` is `False` and `Quantity_State > 0`.
- **Budget_Slider**: The `st.slider` control for the user's weekly grocery budget (£10–£60, default £25).
- **Auto_Fit_Optimizer**: The 1-click budget solver (`_auto_fit_to_budget`) that reduces duplicate quantities first and removes `Surge` items before `Stable` and `Bargain` staples until `Checkout_Total <= Budget_Slider`.
- **Meal_Card**: A Pure White (`#FFFFFF`) recipe card generated from active basket and cupboard ingredients, adapted for the current mode and strictly excluding any recipe requiring a removed ingredient.
- **Assets_Dir**: The `Main/assets/` directory containing commodity illustrations (`.png`, `.jpg`, `.jpeg`, `.svg`).
- **Base64_Image**: A `data:image/...;base64,...` URI produced by `get_base64_image(commodity_name: str) -> str | None`.
- **Monogram_Fallback**: A minimalist themed 2-letter badge displayed when no image exists in Assets_Dir for a commodity.
- **Impact_Callout**: A single-line pill in the bottom summary bar displaying `"Saved £{money_saved:.2f} · {prep_saved} min saved"`.
- **Summary_Bar**: The fixed high-contrast rounded bottom bar showing Impact_Callout, Checkout_Total, total prep minutes, active item count, and the shopping list download button.

---

## Requirements

### Requirement 1: Pipeline Integration and Caching

**User Story:** As a user, I want the app to load live market and calendar data quickly without redundant API calls, so that the interface feels responsive.

#### Acceptance Criteria

1. WHEN the App starts or the selected calendar changes, THE App SHALL fetch market and calendar data by invoking the Pipeline with the selected calendar name as the sole input.
2. WHEN the App fetches pipeline data for a given calendar name and the same calendar name is requested again within 300 seconds, THE App SHALL return the previously fetched result without invoking the Pipeline again.
3. IF the Pipeline raises an exception or returns an `"error"` key during data fetch, THEN THE App SHALL display an error message indicating that market data could not be loaded, and THE App SHALL keep the header banner and UI controls functional.

---

### Requirement 2: Dynamic CSS Theming

**User Story:** As a user, I want the entire app to shift colour palette based on my stress mode, so that the visual design communicates how the week looks at a glance.

#### Acceptance Criteria

1. THE App SHALL apply the Warm Sand (`#EEDFC7`) base theme background canvas on every page load, regardless of the value of `meal_prep_mode`.
2. WHEN `meal_prep_mode` is `"from_scratch"`, THE App SHALL apply Calm_Mode colours — using Sage Olive (`#838921`) as the primary accent and Deep Forest (`#3A3D0E`) as the deep contrast — to all themed surface elements: the page header, savings banner border, category badges, artwork frames, progress bars, tabs, and the Summary_Bar.
3. WHEN `meal_prep_mode` is `"minimal_prep"`, THE App SHALL apply Burnout_Mode colours — using Warm Ochre (`#D99B21`) as the primary accent and Deep Roasted (`#5A3E0A`) as the deep contrast — to all themed surface elements.
4. IF `meal_prep_mode` is absent or holds a value other than `"from_scratch"` or `"minimal_prep"`, THEN THE App SHALL apply Calm_Mode as the default theme.
5. WHEN `meal_prep_mode` changes value, THE App SHALL update all themed surface elements to reflect the new palette without requiring the user to navigate away from or manually refresh the current page.
6. THE App SHALL render elevated cards with a Pure White (`#FFFFFF`) background, rounded corners (`20px`), and a soft drop shadow that separates them from the Warm Sand canvas.

---

### Requirement 3: Top Header Banner, Savings Highlight & Mode Controls

**User Story:** As a user, I want a clear header showing my schedule stress status, how much money and prep time I am saving compared to a standard shop, and a schedule mode selector.

#### Acceptance Criteria

1. THE App SHALL render a top editorial header banner styled with the Active_Theme deep contrast background colour, displaying the `"Market-to-Table"` title, subtitle, and a pill-shaped `stress_status` badge.
2. IF the Pipeline returns no `stress_status` value or raises an exception, THEN THE App SHALL display a badge with the text `"Status unavailable"`.
3. DIRECTLY below the header banner, THE App SHALL render the Savings_Banner displaying three metrics: `"Total Saved vs. Standard Shop"` (`£{money_saved:.2f} saved` with standard vs. smart basket comparison), `"Prep Time Saved"` (`{prep_saved} mins`), and `"Market Protection"` (`{surges_dodged} surge(s) dodged`).
4. THE App SHALL display a 3-option Schedule Mode selector (`"Demo - Calm Week"`, `"Demo - Burnout Week"`, `"Live Google Calendar"`) using `st.selectbox` alongside the weekly budget controls.
5. WHEN a Schedule Mode is selected, THE App SHALL invoke the cached Pipeline call with the selected calendar name and refresh the stress badge, savings banner, basket cards, and meal plan section.

---

### Requirement 4: Weekly Budget Slider, Progress Bar & 1-Click Auto-Fit Optimizer

**User Story:** As a user, I want to set a weekly grocery budget, see how close my basket is to that limit, and trim my basket with one click if I go over budget.

#### Acceptance Criteria

1. THE App SHALL render a Budget_Slider using `st.slider` with a minimum of `£10`, maximum of `£60`, default of `£25`, and step of `£1`, labelled `"Weekly Grocery Budget"`.
2. THE App SHALL display a visual progress bar showing `min(Checkout_Total / Budget_Slider, 1.0)` as the filled proportion, capping the bar at full width when `Checkout_Total` exceeds `Budget_Slider`.
3. WHILE `Checkout_Total` is less than or equal to the Budget_Slider value, THE App SHALL fill the progress bar with the Active_Theme primary colour and display `"Within weekly budget"`.
4. WHEN `Checkout_Total` exceeds the Budget_Slider value, THE App SHALL fill the progress bar with `Warm_Ochre` (`#D99B21`), display `"Over budget by £X.XX"`, and render a 1-click `"⚡ Auto-Fit to £{budget} Budget"` button directly below the progress bar.
5. WHEN the user clicks `"⚡ Auto-Fit to £{budget} Budget"`, THE App SHALL first decrement extra quantities (`Quantity_State > 1`) and then remove single items — prioritising `"Surge"` items before `"Stable"` and `"Bargain"` staples (highest price first) — until `Checkout_Total <= Budget_Slider`, and display a summary caption of the adjustments made.
6. THE App SHALL update the progress bar, over-budget alert, and Auto-Fit button visibility on every widget interaction.

---

### Requirement 5: Tracked Commodities Single-Row Strip

**User Story:** As a user, I want to see all 13 tracked commodities in one clean horizontal row with their artwork, market status, and inspect trigger, so that I can scan market movements at a glance.

#### Acceptance Criteria

1. THE App SHALL render a single horizontal row (`st.columns(13)`) containing tiles for all 13 commodities: `wheat`, `rice`, `corn`, `oats`, `beef`, `pork`, `soy`, `dairy`, `coffee`, `orange_juice`, `cooking_oil`, `sugar`, `cocoa`.
2. WHEN each commodity tile renders, THE App SHALL display a `68×68 px` (`1:1` square) Art_Print_Frame, a concise display label (using `"OJ"` for `orange_juice` and `"Oil"` for `cooking_oil`), a colour-coded status badge (`Bargain` in green `#3A7D44`, `Surge` in red `#C0392B`, `Stable` in Warm Slate `#6E6559`), and a `"View"` button.
3. WHEN a commodity tile or basket card renders, THE App SHALL call `get_base64_image(commodity_name)` and embed the returned value as a `data:image/...;base64,...` URI inside the Art_Print_Frame.
4. IF `get_base64_image(commodity_name)` returns `None`, THEN THE App SHALL render a Monogram_Fallback badge using the commodity name's first two uppercase characters styled in the Active_Theme primary colour, and display a helper caption listing missing asset filenames.
5. THE `get_base64_image` function SHALL search `Main/assets/` case-insensitively for `.png`, `.jpg`, `.jpeg`, or `.svg` files using `pathlib.Path` and cache results with `@st.cache_data(ttl=30)`.

---

### Requirement 6: 50/50 Commodity Split Detail View & 30-Day Price Sparkline

**User Story:** As a user, I want to inspect any commodity to see its 30-day futures price chart, shelf price impact, and matching recipe ideas in a split-screen view.

#### Acceptance Criteria

1. WHEN the user clicks `"View"` on a Commodity_Strip tile or `"Inspect"` on a Basket_Card, THE App SHALL set `st.session_state["selected_commodity"]` and render an animated 50/50 Split_Detail_View above the Commodity_Strip.
2. THE left 50% column SHALL display a `215×215 px` (`1:1` square) hero Art_Print_Frame (or Monogram_Fallback), the `market_status` badge, product/commodity title, brand, and swap rationale.
3. THE right 50% column SHALL display a `"✕ Close Split View"` button, the 30-day percentage move headline, futures start-to-end prices, basket shelf price impact (when the item is in the basket), a 30-day area sparkline chart (`st.area_chart`) fetched via `yfinance` (with a deterministic 30-day fallback curve when offline), and up to 3 matching recipe headings.
4. WHEN the user clicks `"✕ Close Split View"` (or removes the currently inspected item from the basket), THE App SHALL clear `selected_commodity` and hide the Split_Detail_View.

---

### Requirement 7: View Toggle

**User Story:** As a user, I want to switch between my shopping basket and meal inspiration views, so that I can plan both my shop and my cooking from one screen.

#### Acceptance Criteria

1. THE App SHALL render a two-tab view selector (`st.tabs`) with options `"Shopping Basket"` and `"What's on the Table?"`, with `"Shopping Basket"` selected by default on first render.
2. WHEN `"Shopping Basket"` is selected, THE App SHALL display active Basket_Cards (and any removed-item restore buttons); IF all items have been removed or the basket is empty, THEN THE App SHALL display an empty-state info message.
3. WHEN `"What's on the Table?"` is selected, THE App SHALL display filtered Meal_Cards; IF no matching Meal_Cards are available, THEN THE App SHALL display an informative empty-state message.
4. THE App SHALL style the tab list using Darker Sand (`#DFC9A6`) and apply the Active_Theme primary colour to the active tab indicator.

---

### Requirement 8: Basket Cards with Quantity Stepper, Cupboard Toggle & Remove/Restore

**User Story:** As a user, I want to adjust quantities, mark items I already own, and remove or restore items from my basket, so that my shopping list and meal suggestions reflect only what I want.

#### Acceptance Criteria

1. THE App SHALL render one Basket_Card per active (non-removed) entry in `grocery_basket.basket` as a horizontal rounded white (`#FFFFFF`) card (`border-radius: 20px`) containing a `118×118 px` (`1:1` square) Art_Print_Frame, product details (`item_name`, `brand`, prep-time badge, `swap_reason`), and right-aligned line price (`£0.00`) and `market_status` badge.
2. DIRECTLY below each Basket_Card, THE App SHALL render an interactive control row containing `"Inspect"`, `"-"`, the current Quantity_State (`0–99`), `"+"`, `"Already in cupboard"` (`st.checkbox`), and `"✕ Remove"` buttons.
3. WHEN `"+"` is clicked and `Quantity_State < 99`, THE App SHALL increment `Quantity_State` by `1`; when `"-"` is clicked and `Quantity_State > 0`, THE App SHALL decrement `Quantity_State` by `1`.
4. WHEN `Cupboard_State` is `True`, THE App SHALL dim the Basket_Card to `opacity: 0.55`, display an `"In Cupboard - £0.00"` badge, and exclude the item from `Checkout_Total` and weekly prep minutes while retaining it as an ingredient for meal matching.
5. WHEN `"✕ Remove"` is clicked on a Basket_Card, THE App SHALL append that commodity to `Removed_Items_State` (`"{mode}_removed_items"`), hide its Basket_Card, and exclude it from `Checkout_Total`, `Savings_Banner`, and `shopping_list.txt`.
6. WHILE `Removed_Items_State` is non-empty, THE App SHALL render individual `"↩ Restore <Item>"` buttons plus a `"Restore All"` button at the top of the `"Shopping Basket"` tab; clicking a restore button SHALL return the item to the active basket (resetting `Quantity_State` to `1` if it was `0`).
7. THE App SHALL scope all quantity, cupboard, and removed-item session state keys by `meal_prep_mode` so switching schedule modes preserves each mode's basket independently.

---

### Requirement 9: Meal Cards & Dynamic Exclusion on Removal

**User Story:** As a user, I want to see up to 3 tailored meal ideas built from my active basket, and have recipes automatically hidden if I remove one of their ingredients.

#### Acceptance Criteria

1. WHEN rendering `"What's on the Table?"`, THE App SHALL filter `MEAL_LIBRARY` to recipes matching the active `meal_prep_mode` (`"from_scratch"` or `"minimal_prep"`) that share at least 2 active ingredients from the basket or cupboard, displaying up to 3 Meal_Cards.
2. EACH Meal_Card SHALL display the meal title, total time and cook time in minutes, `58×58 px` (`1:1` square) Art_Print_Frame thumbnails, per-ingredient status pills (`"In basket"` or `"In cupboard"`), and numbered preparation steps.
3. WHEN any ingredient required by a meal is present in `Removed_Items_State` (or has `Quantity_State == 0` and `Cupboard_State == False`), THE App SHALL strictly exclude that meal from the displayed Meal_Cards and show a caption noting how many recipes are hidden due to removed items.
4. WHEN a removed ingredient is restored to the basket, THE App SHALL immediately restore matching Meal_Cards in `"What's on the Table?"`.
5. IF fewer than 2 active ingredients exist, THEN THE App SHALL display `"Add or restore items in your basket to see matching meal ideas."`.

---

### Requirement 10: Bottom Summary Bar and Download

**User Story:** As a user, I want a persistent summary of my basket's value and savings plus a quick way to export my list, so that I can take my plan to the supermarket.

#### Acceptance Criteria

1. THE App SHALL render a Summary_Bar fixed to the bottom of the viewport (`position: fixed; bottom: 0; z-index: 999`), styled with the Active_Theme deep contrast colour as background and white text.
2. THE Summary_Bar SHALL display the Impact_Callout pill (`"Saved £{money_saved:.2f} · {prep_saved} min saved"`), the `Checkout_Total` formatted as `£0.00`, total prep minutes, and the active item count (where active items are non-removed items with `Quantity_State > 0` and `Cupboard_State == False`).
3. IF no active purchasable items remain, THEN THE Summary_Bar SHALL display `£0.00`, `0 min prep`, and `0 items`.
4. WHEN the user clicks `"Download Shopping List"`, THE App SHALL export a UTF-8 `shopping_list.txt` file containing only active, non-removed items where `Quantity_State > 0` and `Cupboard_State` is `False`, formatted as `"{quantity}x {item_name} ({brand}) - £{price:.2f}"`.

---

### Requirement 11: Currency Formatting and Data Integrity

**User Story:** As a user, I want all prices displayed and calculated accurately in GBP, so that I can trust every financial figure shown.

#### Acceptance Criteria

1. THE App SHALL compute all basket totals, savings comparisons, and budget-trimming steps using Python `Decimal` arithmetic converted from stringified unit prices (`Decimal(str(price))`).
2. THE App SHALL format every price, line item, savings figure, and checkout total as a GBP value prefixed with `£` (`\u00a3`) to exactly two decimal places (e.g. `£10.49`).
3. WHEN exporting `shopping_list.txt`, THE App SHALL encode the output as UTF-8 bytes so the `£` glyph renders cleanly across operating systems.