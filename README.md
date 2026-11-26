# Kiro Market to Table
**A cosy, user-friendly smart shopping list ("Market") and adaptive meal planner ("to the Table") built to save you time in the kitchen and money at the till.**

Market to Table removes the guesswork from weekly meal planning by connecting three different data streams into one application. The application combines a commodity anaylser (`Commodity-analyser.py`), your calendar app filled with your day to day schedule (`Calendar.py`), and a shopping cart and meal planner (`Shopping-planner.py`) into one Streamlit app (`Main/app.py`)

Dreading a week packed with back-to-back meetings and zero energy to cook? Market to Table detects the **time limitability and automatically pivots your basket** to 5-minute and pre-made pantry items. Have a calm weekend ahead while wheat or coffee futures are surging? It swaps **expensive staples for bargain alternatives** and ingredients that you can make meals from scratch with.



## Core Experience 

### 1. Calm Week functionality
When your calendar shows few activities in your itinerary, Market to Table shifts into **Sage Olive** market-stall styling and colouring and builds a `from_scratch` basket:
- Suggests rewarding, budget-friendly recipes like *Beef Mince Bolognese with Fusilli*, *Tofu Stir-Fry with Rice*, and *Orange Juice Overnight Oats*.
- Prioritises whole ingredients and bargain commodity staples to stretch your weekly budget further.

### 2. Burnout Week functionality
When your schedule is overloaded, the interface shifts into **Warm Ochre & Market Orange** styling and colouring and will switch to `minimal_prep` mode:
- Automatically swaps raw, high-prep ingredients for 3–5 minute assemblies like *Steamed Rice Pouch with Cooked Chicken*, *Pulled Pork Pitta Pockets*, and *Microwave Pasta with Grated Cheese*.
- Tracks both **money saved** and **prep minutes saved** compared to a standard unswapped supermarket shop.

### 3. Live Commodity Signals & Smart Basket 📈
- **13-Commodity Market Strip:** Inspect real-time **Surge**, **Bargain**, and **Stable** signals across 13 global agricultural futures (`yfinance` with deterministic fallback).
- **50/50 Split View:** Click **View** or **Inspect** on any ingredient to open a 30-day futures price area chart, the trend in price specifically highlighted for the user, basket shelf-price impact, and matching recipe ideas.
- **Interactive Budget Controls:** Adjust item quantities, check off **Already in cupboard** (`£0.00`), remove/restore items with live recipe updates, use **1-Click Auto-Fit to Budget**, and export a clean `shopping_list.txt` so the experience is tailored exactly for the user, taking into account what they already have and their individual budget to save money.

---

## Get Started with Market-to-Table

### 1. Clone and Open in Kiro IDE
```bash
git clone https://github.com/Ella721671/Kiro-Market-to-Table.git
cd Market-to-Table
```
Create a virtual environment and install the dependencies from `requirements.txt`:

```bash
# macOS / Linux
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Windows
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```
*(Optional)* To connect a live Google Calendar instead of using the built-in **Demo - Calm Week** and **Demo - Burnout Week** presets, create a `.env` file in the project root:
```env
GOOGLE_CALENDAR_API_KEY=your_api_key_here
CALM_CALENDAR_ID=your_calm_calendar_id
BURNOUT_CALENDAR_ID=your_burnout_calendar_id
```

### 2. Run the Application
Launch the Streamlit interface from the repository root:
```bash
streamlit run Main/app.py
```
Use the **Schedule Mode** dropdown at the top of the page to switch between **Demo - Calm Week**, **Demo - Burnout Week**, and **Live Google Calendar**.

### 3. Run the Verification and Property test suite
Market-to-Table uses `pytest` and `hypothesis` property-based testing to verify checkout math, budget auto-fitting, Base64 asset loading, and theme tokens:
```bash
pytest
```

### Utilising Kiro
This project was made within the **Kiro IDE** using a spec driven development and utilisng **Specs**, **Steering Docs**, **Hooks**, and **Property-Based Testing**—to coordinate a multi-API backend with a Streamlit frontend.

#### 📋 Spec-Driven Architecture (`.kiro/specs/`)
Rather than building from a single spec prompt, the application was decomposed into **four modular Kiro specs**, each containing traceable `requirements.md`, `design.md`, and `tasks.md` files:
1. **Calendar Burnout Detection (`Calendar.py`):** Reads your calendar and defines what constitutes as a **Calm** (`from_scratch` cooking) or **Burnout** (`minimal_prep` pantry rescues) week using the number of hours events take up the calendar and key words such as urgent or deadline.
2. **Commodity Analyser (`Commodity-analyser.py`):** Maps 13 everyday food items to Yahoo Finance agricultural futures tickers (`ZW=F`, `KC=F`, `LE=F`, etc.) and categorises 30-day price shifts into **Surge**, **Bargain**, or **Stable** signals.
3. **Smart Basket & Meal Planner (`Shopping-planner.py`):** Translates market signals and combines this with data from the calendar application to decide and execute supermarket swaps, calculating exact GBP savings (`Decimal` precision) and prep-time minutes saved against a standard unswapped shop, as well as specific brands to buy.
4. **Cottagecore Editorial UI (`Main/app.py`):** Connects all three backend modules into an interactive Streamlit interface featuring a dynamic market-stall styl application, a 13 commodity status strip, 50/50 split price history view, and automatic budgeting.

#### 🧭 Architectural Guardrails via Steering Docs (`.kiro/steering/`)
Persistent steering documents in `.kiro/steering/` gave Kiro continuous project context across every session without repetitive prompting:
* **Repository & Module Boundaries:** Enforced clean separation inside `Main/` between data-pipeline modules (`Calendar.py`, `Commodity-analyser.py`, `Shopping-planner.py`, `main.py`) and the cached Streamlit UI layer (`Main/app.py`).
* **Visual Identity & Theme Consistency:** Kept a cohesive and continued colour palette to give a sense of warmth with **Warm Sand (`#EEDFC7`)** as the background, **Sage Olive (`#838921`)** for Calm Mode, and **Warm Ochre (`#D99B21`)** for Burnout Mode, alongside implementing my own custom illustrations I designed in Procreate in `Main/assets/`.
* **API Resilience Standards:** Mandated deterministic offline fallbacks for both Google Calendar and `yfinance` so live network timeouts or rate limits never crash the user experience.

#### ⚡ Automated Workflows with Agent Hooks (`.kiro/hooks/`)
Kiro hooks in `.kiro/hooks/` automated quality checks during development:
* **Continuous Verification on Save:** Triggered automated test and validation checks whenever core pipeline or UI files inside `Main/` were updated.
* **Asset & State Integrity:** Verified Base64 asset resolution in `Main/assets/` and ensured interactive UI additions such as **Already in cupboard** toggles, item removal/restore chips, and dynamic recipe filtering which remained synchronised with checkout totals and removing items from the basket when necessary.

#### 🧪 Correctness-by-Construction (`pytest` & `hypothesis`)
Guided by Kiro’s spec task lists, the test suite pairs unit tests with **`hypothesis` property-based testing** to verify invariants across hundreds of randomized inputs:
* **Checkout & Savings Math:** Proves that basket totals, cupboard exclusions (`£0.00`), and standard shop savings remain accurate across item quantities and prices.
* **1 Click Budget Optimiser:** Verifies that `_auto_fit_to_budget` prioritises trimming `Surge` items first while preserving `Bargain` staples until the basket fits under the user's own personal `£10–£60` slider limit.
* **Theme & Asset Safety:** Confirms required colour tokens remain intact and missing asset files degrade cleanly to two-letter monograms.

## Commodities tracked 
Market-to-Table monitors 13 agricultural futures tickers to flag supermarket price surges and bargains:

| Commodity | Futures Ticker | Role in Smart Basket |
| :--- | :--- | :--- |
| **Wheat** | `ZW=F` | Pasta, flatbreads, pitta pockets, toast, whole bread |
| **Rice** | `ZR=F` | Basmati rice and 2-minute steamed pouches |
| **Corn** | `ZC=F` | Tortillas, polenta and sweetcorn sides |
| **Oats** | `ZO=F` | Porridge, overnight oats and flapjack bites |
| **Beef** | `LE=F` | Slow-simmered bolognese and cottage pie |
| **Pork** | `HE=F` | Medallions and ready made pulled pork |
| **Soy** | `ZS=F` | Tofu stir-fries and soy seasoning sachets |
| **Dairy** | `DC=F` | Milk, grated cheddar and three-cheese pasta bakes |
| **Coffee** | `KC=F` | Filter beans and instant granules |
| **Orange Juice** | `OJ=F` | Chilled breakfast juice and other juices |
| **Cooking Oil** | `ZL=F` | Pan searing and roasting staples |
| **Sugar** | `SB=F` | Baking ingredients and sweet breakfast toppings |
| **Cocoa** | `CC=F` | Dark chocolate and hot cocoa |
