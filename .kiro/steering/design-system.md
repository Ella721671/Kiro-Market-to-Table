# Product & UI Design System (Market-to-Table)

## 1. Visual Aesthetic & Dual-Mode Colour System
- **App Style:** Sleek, warm, editorial consumer grocery interface built in Streamlit (`Main/app.py`) using custom CSS.
- **Neutrals & Surfaces:**
  - **Main Background Canvas:** Warm Sand (`#EEDFC7`)
  - **Elevated Cards:** Pure White (`#FFFFFF`) with `border-radius: 20px` and soft shadow (`0 4px 16px rgba(58, 61, 14, 0.06)`)
  - **Art-Print Card Surface:** Muted Risograph Sky (`#D4E2E8`) — cool dusty blue canvas inside every portrait art frame so cream, green, orange/yellow, and brown illustrations stand out cleanly.
  - **Secondary Buttons & Controls:** Darker Sand (`#DFC9A6`, hover `#D2B78C`) with dark theme text
  - **Secondary Subtitles:** Muted Warm Slate (`#6E6559`) for brands, weights, and helper labels
- **Dynamic Mode Themes (Switch Entire UI Palette on Toggle):**
  - **Calm Week (`from_scratch`):**
    - **Primary Brand Accent:** Sage Olive (`#838921`) — used for top header banner splash, active badges, risograph card borders, progress bars within budget, and `Bargain` tags.
    - **Deep Contrast Shade:** Deep Forest Olive (`#3A3D0E`) — used for primary headings, item titles, prices, and the bottom checkout/summary bar (paired with `#FFFFFF` text).
  - **Burnout Week (`minimal_prep`):**
    - **Primary Brand Accent:** Warm Ochre (`#D99B21`) — replaces Sage Olive across the top header banner splash, active badges, risograph card borders, over-budget alerts, and `Surge` tags.
    - **Deep Contrast Shade:** Deep Roasted Ochre (`#5A3E0A`) — replaces Deep Forest Olive for primary headings, item titles, prices, and the bottom checkout/summary bar (paired with `#FFFFFF` text).

## 2. Layout, Interactive Features & Components
- **Top Header Banner:** Clean typographic banner styled with the active theme's primary colour (`#838921` in Calm Week, `#D99B21` in Burnout Week), no hero character illustrations, housing the **Market-to-Table** title, a 3-option mode selector (`Demo - Calm Week`, `Demo - Burnout Week`, and `Live Google Calendar` connected to `Main/Calendar.py`), and active stress status pill.
- **Weekly Budget & Prep-Time Bar:** Include a compact budget slider (`st.slider` for Weekly Grocery Budget in GBP, default `£25.00`, range `£10.00–£60.00`) paired with a visual progress bar showing `Current Checkout Spend / Weekly Budget`. Fill the bar in Sage Olive (`#838921`) when on or under budget, and shift to Warm Ochre (`#D99B21`) with a clear alert label if spend exceeds the user's limit.
- **Tracked Commodities Visual Grid:** A compact 13-item showcase grid displaying all tracked commodities with their Muted Risograph Sky (`#D4E2E8`) art card and live Yahoo Finance status (`Bargain`, `Surge`, or `Stable`) so 100% of the user's custom artwork is visible on every page load.
- **View Switcher (`Shopping Basket` vs. `What's on the Table?`):** Provide a Darker Sand (`#DFC9A6`) segmented control or tab toggle allowing users to switch smoothly between their interactive grocery list and curated meal cards.
- **Grocery Card Layout, Quantity Stepper & "In Cupboard" Toggle:** Render each basket item as a horizontal rounded white card (`#FFFFFF`) with three zones:
  1. **Left Art-Print Frame:** Portrait risograph-style card (`76px x 94px`) in Muted Risograph Sky (`#D4E2E8`) holding the custom commodity illustration.
  2. **Middle Details:** Deep contrast (`#3A3D0E` or `#5A3E0A`) bold product title, UK supermarket brand + weight subtitle, prep-time pill (`e.g. 3 mins`), concise `swap_reason`, and an **"Already in cupboard"** checkbox (`st.checkbox`). When checked, visually dim the card (`opacity: 0.55`), show an `"In Cupboard - £0.00"` badge, deduct its cost from the checkout total and budget bar, and omit it from the `.txt` shopping list while keeping it available as an ingredient for meal cards.
  3. **Right Price, Signal & Stepper:** Line-item GBP price (`£0.00` if in cupboard, otherwise `unit_price * quantity`), market-signal pill (`Bargain`, `Surge`, or `Stable`), and a compact **`-  qty  +`** stepper styled with Darker Sand (`#DFC9A6`) buttons (minimum quantity `0`, defaulting to `1`).
- **"What's on the Table?" Meal Cards:** Dynamically display 2–3 tailored UK meal cards generated from the user's active ingredients (items with `qty > 0` or checked as `in_cupboard`) and current mode (`from_scratch` recipes in Calm Week vs. `minimal_prep` 3–10 minute assemblies in Burnout Week). Each meal card sits on Pure White (`#FFFFFF`, `border-radius: 20px`) displaying meal title, prep + cook minutes pill, mini Muted Risograph Sky (`#D4E2E8`) thumbnails of matching custom artwork, ingredient status tags (in cupboard vs. in basket), and 2–3 concise preparation steps.
- **Live State & Performance Rule:** Cache `run_market_to_table()` results with `@st.cache_data(ttl=300)` and store item quantities and `in_cupboard` booleans per calendar mode inside `st.session_state` so toggling checkboxes or clicking `+` / `-` updates totals and meal cards instantly without re-running API calls.
- **Bottom Summary Bar & Impact Callout:** High-contrast rounded bar in the active deep contrast shade (`#3A3D0E` for Calm Week, `#5A3E0A` for Burnout Week) displaying:
  - A concise **Impact Callout** pill highlighting real-world value (e.g., cooking time saved compared to scratch prep and any commodity price surges dodged).
  - Dynamically summed checkout GBP cost (`£0.00` excluding cupboard items), total weekly prep minutes, and items-to-buy count.
  - A Darker Sand (`#DFC9A6`) download `.txt` shopping list button exporting only items still needed (`qty > 0` and not in cupboard).

## 3. Risograph Art-Print Frames & 100% Custom Artwork Pipeline (`Main/assets/`)
- **Directory Setup:** Automatically ensure `Main/assets/` exists relative to `Main/app.py` at startup (`(Path(__file__).resolve().parent / "assets").mkdir(parents=True, exist_ok=True)`).
- **Editorial Art-Print Styling:** Render every commodity artwork inside a portrait Muted Risograph Sky (`#D4E2E8`) frame (`76px x 94px`, `border-radius: 12px`) outlined with a `2.5px` solid border in the active theme colour (`#838921` or `#D99B21`) and decorative striped top/bottom accent notches (using CSS `repeating-linear-gradient` in the active theme colour alternating with `#D4E2E8`).
- **Mandatory Local Artwork:** Every grocery item card, commodity badge, and meal card thumbnail MUST render the user's custom illustrations from `Main/assets/`. Do NOT replace custom artwork with emojis when an image file exists.
- **Required Asset Filenames (13 Commodities):**
  - `wheat.png`, `rice.png`, `corn.png`, `oats.png`, `beef.png`, `pork.png`, `soy.png`, `dairy.png`, `coffee.png`, `orange_juice.png`, `cooking_oil.png`, `sugar.png`, `cocoa.png`
  - Support `.png`, `.jpg`, `.jpeg`, and `.svg` extensions case-insensitively using `pathlib.Path`.
- **Streamlit HTML Rendering Rule:** Embed local images using Python's `base64` module (`get_base64_image(commodity_name: str) -> str | None`) as `data:image/...;base64,...` URIs inside the `#D4E2E8` portrait art frame (`object-fit: contain; padding: 6px;`).
- **Safety Guard:** Fall back cleanly to a minimalist themed monogram badge if a file is not in `Main/assets/` yet, and display a subtle helper caption listing any missing filenames so the user knows where to drop their drawings.