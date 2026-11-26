"""
Market-to-Table — Streamlit UI
================================
Single-file Streamlit application wrapping the three-module pipeline
(Calendar.py, Commodity-analyser.py, Shopping-planner.py) behind an
editorial consumer grocery interface.
"""

from __future__ import annotations

import base64
import importlib.util
import math
import re
import sys
from decimal import Decimal
from pathlib import Path
from typing import Any
import streamlit as st

def apply_cottagecore_theme(is_stressed: bool = False) -> None:
    """Applies the complete Market-to-Table cottagecore UI styling."""
    if is_stressed:
        awning_stripe = "#D97724"   # Warm market-stall orange for stressed week
        awning_trim = "#D99B21"     # Warm Ochre trim
        badge_bg = "rgba(217, 155, 33, 0.18)"
    else:
        awning_stripe = "#838921"   # Sage Olive green for relaxing week
        awning_trim = "#6B701A"     # Deep herb-leaf trim
        badge_bg = "rgba(131, 137, 33, 0.16)"

    st.markdown(
        f"""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Lora:ital,wght@0,600;0,700;1,500&family=Nunito:wght@400;600;700&display=swap');

        /* Make Streamlit's top bar transparent so the stall awning shows at the very top */
        [data-testid="stHeader"] {{
            background: transparent !important;
        }}

        /* Warm Sand parchment background with subtle handmade-paper grain */
        .stApp,
        [data-testid="stAppViewContainer"] {{
            background-color: #EEDFC7 !important;
            background-image: radial-gradient(rgba(59, 47, 47, 0.045) 1px, transparent 0) !important;
            background-size: 18px 18px !important;
            color: #3B2F2F;
            font-family: 'Nunito', sans-serif;
        }}

        /* Attach the striped awning to stMain so it stays at the top and scrolls with the banner */
        [data-testid="stMain"],
        .main {{
            position: relative;
        }}

        [data-testid="stMain"]::before,
        .main::before {{
            content: "";
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 168px;
            box-sizing: border-box;
            background-image:
                linear-gradient(
                    180deg,
                    rgba(59, 47, 47, 0.08) 0%,
                    transparent 22%,
                    transparent 82%,
                    rgba(59, 47, 47, 0.10) 100%
                ),
                repeating-linear-gradient(
                    90deg,
                    {awning_stripe} 0px,
                    {awning_stripe} 28px,
                    #FAF5EB 28px,
                    #FAF5EB 56px
                );
            z-index: 0;
            pointer-events: none;
        }}

        /* Scalloped fabric valance edge hanging below the striped awning */
        [data-testid="stMain"]::after,
        .main::after {{
            content: "";
            position: absolute;
            top: 168px;
            left: 0;
            width: 100%;
            height: 16px;
            background-image:
                radial-gradient(circle at 14px 0, {awning_stripe} 12px, {awning_trim} 12px, {awning_trim} 14px, transparent 14.5px),
                radial-gradient(circle at 42px 0, #FAF5EB 12px, {awning_trim} 12px, {awning_trim} 14px, transparent 14.5px);
            background-size: 56px 16px;
            background-repeat: repeat-x;
            filter: drop-shadow(0 4px 6px rgba(59, 47, 47, 0.12));
            z-index: 0;
            pointer-events: none;
        }}

        /* Keep your banner, text, and cards layered cleanly IN FRONT of the awning */
        [data-testid="stMainBlockContainer"],
        .main .block-container {{
            position: relative;
            z-index: 1;
        }}

        /* Cookbook-style serif headings */
        h1, h2, h3, h4, .mtt-section-title {{
            font-family: 'Lora', Georgia, serif !important;
            letter-spacing: -0.01em;
        }}

        /* Keep dark header and bottom summary bar text crisp white */
        .mtt-header, .mtt-header div, .mtt-header span:not(.mtt-badge),
        .mtt-summary-bar, .mtt-summary-bar span,
        .mtt-impact-pill {{
            color: #FFFFFF !important;
        }}

        /* Pressed-linen card styling */
        .mtt-card, .mtt-savings-banner {{
            background-color: #FAF5EB !important;
            border: 1px solid #C8B69E !important;
            box-shadow: 0 4px 12px rgba(59, 47, 47, 0.06) !important;
        }}

        /* Vintage recipe box index-card border for meal suggestions */
        .mtt-recipe-card {{
            border-radius: 14px !important;
            padding: 1.45rem 1.65rem !important;
            outline: 1.5px dashed #C8B69E !important;
            outline-offset: -8px !important;
        }}

        .mtt-recipe-card-title {{
            font-family: 'Lora', Georgia, serif !important;
            border-bottom: 1.5px solid rgba(217, 155, 33, 0.45);
            padding-bottom: 6px;
        }}

        /* Tactile rounded buttons matching the active week's stall color */
        div[data-testid="stButton"] > button {{
            border-radius: 999px !important;
            border: 1px solid {awning_trim} !important;
            transition: transform 0.15s ease, filter 0.15s ease;
        }}

        div[data-testid="stButton"] > button:hover {{
            filter: brightness(1.05);
            transform: translateY(-1px);
        }}

        /* Replace Streamlit's coral-red sliders & checkboxes with active stall colors */
        input[type="checkbox"],
        [data-testid="stCheckbox"] {{
            accent-color: {awning_stripe} !important;
        }}

        [data-testid="stCheckbox"] label span[role="checkbox"][aria-checked="true"],
        [data-baseweb="checkbox"] input:checked + div {{
            background-color: {awning_stripe} !important;
            border-color: {awning_trim} !important;
        }}

        [data-baseweb="slider"] [role="slider"] {{
            background-color: {awning_stripe} !important;
            border: 2px solid #FAF5EB !important;
            box-shadow: 0 2px 6px rgba(59, 47, 47, 0.25) !important;
        }}

        [data-baseweb="slider"] div[data-testid="stThumbValue"] {{
            color: #3B2F2F !important;
            font-family: 'Lora', Georgia, serif !important;
            font-weight: 700 !important;
        }}

        [data-baseweb="slider"] > div > div > div:nth-child(2) {{
            background-color: {awning_stripe} !important;
        }}

        /* Style tabs like protruding manila recipe-box index dividers */
        .stTabs [data-baseweb="tab-list"] {{
            background-color: transparent !important;
            border-bottom: 2px solid #C8B69E !important;
            border-radius: 0 !important;
            gap: 8px !important;
            padding: 0 4px !important;
        }}

        .stTabs [data-baseweb="tab"] {{
            background-color: #E6D3B5 !important;
            color: #3B2F2F !important;
            border: 1px solid #C8B69E !important;
            border-bottom: none !important;
            border-radius: 12px 12px 0 0 !important;
            padding: 0.5rem 1.25rem !important;
            font-family: 'Lora', Georgia, serif !important;
            font-weight: 600 !important;
        }}

        .stTabs [aria-selected="true"] {{
            background-color: #FAF5EB !important;
            color: #3B2F2F !important;
            border-top: 3px solid {awning_stripe} !important;
            font-weight: 700 !important;
        }}

        .stTabs [data-baseweb="tab-highlight"] {{
            background-color: transparent !important;
        }}

        /* Hand-stamped market crate badges */
        .mtt-badge {{
            border-radius: 6px !important;
            letter-spacing: 0.04em !important;
            text-transform: uppercase !important;
            font-weight: 700 !important;
            color: #FAF5EB !important;
            border: 1.5px solid rgba(59, 47, 47, 0.28) !important;
            outline: 1px dashed rgba(250, 245, 235, 0.65) !important;
            outline-offset: -3px !important;
            box-shadow: 0 2px 4px rgba(59, 47, 47, 0.12) !important;
            transform: rotate(-2deg);
        }}

        .mtt-badge-bargain {{
            background-color: #5A6E28 !important; /* Muted herb-leaf green ink */
        }}

        .mtt-badge-surge {{
            background-color: #B84A39 !important; /* Muted terracotta clay ink */
        }}

        .mtt-badge-stable {{
            background-color: #7A6A58 !important; /* Warm sepia ink */
        }}

        /* Botanical plate & apothecary framing on ingredient illustrations */
        .mtt-strip-frame,
        .mtt-strip-mono,
        .mtt-art-frame,
        .mtt-monogram,
        .mtt-hero-frame,
        .mtt-hero-monogram {{
            border: 2px solid {awning_trim} !important;
            outline: 1px solid rgba(59, 47, 47, 0.28) !important;
            outline-offset: -5px !important;
            box-shadow:
                inset 0 2px 6px rgba(59, 47, 47, 0.16),
                0 3px 8px rgba(59, 47, 47, 0.08) !important;
        }}

        /* Botanical section divider */
        .botanical-divider {{
            text-align: center;
            color: #6B5B4B;
            font-family: 'Lora', serif;
            font-size: 0.95rem;
            letter-spacing: 0.25em;
            margin: 1.2rem 0;
            opacity: 0.85;
        }}

        /* Inked pantry stamp pill */
        .pantry-stamp {{
            display: inline-block;
            background-color: {badge_bg};
            border: 1.5px dashed {awning_trim};
            color: #3B2F2F !important;
            font-weight: 700;
            font-size: 0.85rem;
            padding: 4px 12px;
            border-radius: 999px;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def botanical_divider(icon: str = "🌿") -> None:
    """Renders a cozy cottagecore divider between sections."""
    st.markdown(
        f'<div class="botanical-divider">── {icon} ──</div>',
        unsafe_allow_html=True,
    )



def botanical_divider(icon: str = "🌿") -> None:
    """Renders a cozy cottagecore divider between sections."""
    st.markdown(
        f'<div class="botanical-divider">── {icon} ──</div>',
        unsafe_allow_html=True,
    )
def botanical_divider(icon: str = "🌿") -> None:
    """Renders a cozy cottagecore divider between sections."""
    st.markdown(
        f'<div class="botanical-divider">── {icon} ──</div>',
        unsafe_allow_html=True,
    )

# ---------------------------------------------------------------------------
# --- Section 1: Constants ---
# ---------------------------------------------------------------------------

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

COMMODITY_KEYS: list[str] = [
    "wheat", "rice", "corn", "oats", "beef",
    "pork", "soy", "dairy", "coffee",
    "orange_juice", "cooking_oil", "sugar", "cocoa",
]

COMMODITY_TICKERS: dict[str, str] = {
    "wheat":        "ZW=F",
    "rice":         "ZR=F",
    "corn":         "ZC=F",
    "oats":         "ZO=F",
    "beef":         "LE=F",
    "pork":         "HE=F",
    "soy":          "ZS=F",
    "dairy":        "DC=F",
    "coffee":       "KC=F",
    "orange_juice": "OJ=F",
    "cooking_oil":  "ZL=F",
    "sugar":        "SB=F",
    "cocoa":        "CC=F",
}

SHORT_LABELS: dict[str, str] = {
    "orange_juice": "OJ",
    "cooking_oil": "Oil",
}

EXTRA_RECIPE_HEADINGS: dict[str, list[str]] = {
    "wheat": [
        "Garlic & Herb Flatbreads",
        "One-Pot Tomato & Basil Penne",
    ],
    "rice": [
        "Egg Fried Rice with Spring Onions",
        "Coconut & Lime Steamed Rice Bowl",
    ],
    "corn": [
        "Charred Sweetcorn & Black Bean Salad",
        "Crispy Polenta Wedges",
    ],
    "oats": [
        "Baked Apple & Oat Crumble",
        "Savoury Cheddar & Chive Oatcakes",
    ],
    "beef": [
        "Classic Cottage Pie with Mash",
        "Ginger & Garlic Beef Stir-Fry",
    ],
    "pork": [
        "Honey Mustard Pork Medallions",
        "Slow-Cooked Pulled Pork Rice Bowl",
    ],
    "soy": [
        "Sesame Glazed Tofu Noodles",
        "Miso & Soy Roasted Aubergine",
    ],
    "dairy": [
        "Three-Cheese Cauliflower Bake",
        "Creamy Garlic Mushroom Tagliatelle",
    ],
    "coffee": [
        "Espresso Tiramisu Pots",
        "Mocha Overnight Chia Pudding",
    ],
    "orange_juice": [
        "Citrus Glazed Roast Carrots",
        "Zesty Orange & Olive Oil Loaf",
    ],
    "cooking_oil": [
        "Crispy Rosemary Roast Potatoes",
        "Pan-Seared Courgette & Pepper Medley",
    ],
    "sugar": [
        "Caramelised Banana Toast",
        "Classic Shortbread Biscuits",
    ],
    "cocoa": [
        "Rich Hot Cocoa with Cinnamon",
        "Dark Chocolate & Oat Energy Bites",
    ],
}

MEAL_LIBRARY: list[dict] = [
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

PREP_DELTA_LOOKUP: dict[str, dict[str, int]] = {
    "wheat":        {"from_scratch": 12, "minimal_prep": 3},
    "rice":         {"from_scratch": 15, "minimal_prep": 2},
    "corn":         {"from_scratch": 10, "minimal_prep": 1},
    "oats":         {"from_scratch": 6,  "minimal_prep": 0},
    "beef":         {"from_scratch": 20, "minimal_prep": 4},
    "pork":         {"from_scratch": 15, "minimal_prep": 3},
    "soy":          {"from_scratch": 15, "minimal_prep": 3},
    "dairy":        {"from_scratch": 2,  "minimal_prep": 0},
    "coffee":       {"from_scratch": 5,  "minimal_prep": 1},
    "orange_juice": {"from_scratch": 0,  "minimal_prep": 0},
    "cooking_oil":  {"from_scratch": 0,  "minimal_prep": 0},
    "sugar":        {"from_scratch": 10, "minimal_prep": 0},
    "cocoa":        {"from_scratch": 5,  "minimal_prep": 0},
}


# ---------------------------------------------------------------------------
# --- Section 2: Image, History & State Callbacks (Cached for Zero Lag) ---
# ---------------------------------------------------------------------------

def _norm_key(val: str) -> str:
    return val.strip().lower().replace(" ", "_")


@st.cache_data(ttl=30, show_spinner=False)
def get_base64_image(commodity_name: str) -> str | None:
    """Cached lookup of Main/assets/ so images load instantly across reruns."""
    assets_dir = Path(__file__).resolve().parent / "assets"
    name_lower = commodity_name.lower()
    mime_map = {
        ".png":  "image/png",
        ".jpg":  "image/jpeg",
        ".jpeg": "image/jpeg",
        ".svg":  "image/svg+xml",
    }
    for ext, mime in mime_map.items():
        candidate = assets_dir / f"{name_lower}{ext}"
        if candidate.exists():
            encoded = base64.b64encode(candidate.read_bytes()).decode("ascii")
            return f"data:{mime};base64,{encoded}"
    if assets_dir.exists():
        for f in assets_dir.iterdir():
            if f.stem.lower() == name_lower and f.suffix.lower() in mime_map:
                mime = mime_map[f.suffix.lower()]
                encoded = base64.b64encode(f.read_bytes()).decode("ascii")
                return f"data:{mime};base64,{encoded}"
    return None


@st.cache_data(ttl=3600, show_spinner=False)
def fetch_commodity_sparkline(
    commodity: str,
    status_word: str,
    fallback_pct: float | None,
) -> dict[str, Any]:
    """Fetch 30-day futures closing prices via yfinance, with smooth deterministic fallback."""
    ticker = COMMODITY_TICKERS.get(_norm_key(commodity), "")
    if ticker:
        try:
            import yfinance as yf  # type: ignore[import-untyped]

            hist = yf.Ticker(ticker).history(period="1mo", interval="1d")
            if hist is not None and not hist.empty and "Close" in hist.columns:
                closes = [float(x) for x in hist["Close"].dropna().tolist()]
                dates = [idx.strftime("%d %b") for idx in hist["Close"].dropna().index]
                if len(closes) >= 5:
                    start_px = closes[0]
                    end_px = closes[-1]
                    pct_30d = ((end_px - start_px) / start_px) * 100.0 if start_px > 0 else 0.0
                    return {
                        "prices": closes,
                        "dates": dates,
                        "start_price": round(start_px, 2),
                        "end_price": round(end_px, 2),
                        "pct_30d": round(pct_30d, 1),
                        "ticker": ticker,
                        "is_live": True,
                    }
        except Exception:  # noqa: BLE001
            pass

    if fallback_pct is not None and fallback_pct != 0:
        target_pct = fallback_pct
    elif status_word == "Surge":
        target_pct = 8.4
    elif status_word == "Bargain":
        target_pct = -7.6
    else:
        target_pct = 0.6

    base_val = 100.0
    end_val = base_val * (1.0 + target_pct / 100.0)
    points: list[float] = []
    labels: list[str] = []
    seed = sum(ord(c) for c in commodity)
    for i in range(30):
        t = i / 29.0
        wave = math.sin((i + seed) * 0.55) * 1.15
        val = base_val + (end_val - base_val) * (t ** 1.15) + wave * (1.0 - abs(2 * t - 1))
        points.append(round(val, 2))
        labels.append(f"Day {i + 1}")

    return {
        "prices": points,
        "dates": labels,
        "start_price": round(points[0], 2),
        "end_price": round(points[-1], 2),
        "pct_30d": round(target_pct, 1),
        "ticker": ticker or commodity.upper(),
        "is_live": False,
    }


def _dec_qty(qty_key: str) -> None:
    if st.session_state.get(qty_key, 1) > 0:
        st.session_state[qty_key] -= 1


def _inc_qty(qty_key: str) -> None:
    if st.session_state.get(qty_key, 1) < 99:
        st.session_state[qty_key] += 1


def _select_commodity(commodity: str) -> None:
    st.session_state["selected_commodity"] = commodity


def _close_split_view() -> None:
    st.session_state["selected_commodity"] = None


def _remove_basket_item(mode: str, commodity: str) -> None:
    rem_key = f"{mode}_removed_items"
    removed = list(st.session_state.get(rem_key, []))
    if commodity not in removed:
        removed.append(commodity)
    st.session_state[rem_key] = removed
    if st.session_state.get("selected_commodity") == commodity:
        st.session_state["selected_commodity"] = None


def _restore_single_item(mode: str, commodity: str) -> None:
    rem_key = f"{mode}_removed_items"
    st.session_state[rem_key] = [
        c for c in st.session_state.get(rem_key, []) if c != commodity
    ]
    qty_key = f"{mode}_{commodity}_qty"
    if st.session_state.get(qty_key, 1) == 0:
        st.session_state[qty_key] = 1
    st.session_state.pop(f"{mode}_autofit_note", None)


def _restore_basket_items(mode: str) -> None:
    removed = list(st.session_state.get(f"{mode}_removed_items", []))
    for commodity in removed:
        qty_key = f"{mode}_{commodity}_qty"
        if st.session_state.get(qty_key, 1) == 0:
            st.session_state[qty_key] = 1
    st.session_state[f"{mode}_removed_items"] = []
    st.session_state.pop(f"{mode}_autofit_note", None)


def _status_trim_priority(status: str) -> int:
    """Lower number = trim/remove first (Surge first, Stable second, Bargain last)."""
    if status.startswith("Surge"):
        return 0
    if status.startswith("Bargain"):
        return 2
    return 1


def _auto_fit_to_budget(basket: list[dict], mode: str) -> None:
    """1-click optimizer: trims extra quantities first, then removes Surge/expensive items."""
    budget_limit = Decimal(str(st.session_state.get("weekly_budget_slider", 25)))
    rem_key = f"{mode}_removed_items"
    removed = list(st.session_state.get(rem_key, []))

    # Build working list of billable basket items
    billable: list[dict[str, Any]] = []
    current_total = Decimal("0")
    for item in basket:
        commodity = item.get("commodity", "")
        if commodity in removed:
            continue
        qty_key = f"{mode}_{commodity}_qty"
        cup_key = f"{mode}_{commodity}_cupboard"
        qty = int(st.session_state.get(qty_key, 1))
        in_cup = bool(st.session_state.get(cup_key, False))
        price = Decimal(str(item.get("estimated_price_gbp", 0.0)))
        if in_cup or qty <= 0 or price <= 0:
            continue
        current_total += price * qty
        billable.append({
            "commodity": commodity,
            "name": item.get("item_name") or commodity.replace("_", " ").title(),
            "price": price,
            "status": item.get("market_status", ""),
            "qty_key": qty_key,
            "qty": qty,
        })

    if current_total <= budget_limit:
        return

    trimmed_qty_count = 0
    removed_names: list[str] = []

    # Step 1: Trim quantities > 1 first (Surge -> Stable -> Bargain, highest price first)
    while current_total > budget_limit:
        multi_items = [b for b in billable if b["qty"] > 1]
        if not multi_items:
            break
        multi_items.sort(
            key=lambda x: (_status_trim_priority(x["status"]), -x["price"])
        )
        target = multi_items[0]
        target["qty"] -= 1
        st.session_state[target["qty_key"]] = target["qty"]
        current_total -= target["price"]
        trimmed_qty_count += 1

    # Step 2: If still over budget, remove single items (Surge -> Stable -> Bargain, highest price first)
    while current_total > budget_limit:
        remaining_items = [b for b in billable if b["qty"] > 0]
        if not remaining_items:
            break
        remaining_items.sort(
            key=lambda x: (_status_trim_priority(x["status"]), -x["price"])
        )
        target = remaining_items[0]
        current_total -= target["price"] * target["qty"]
        target["qty"] = 0
        if target["commodity"] not in removed:
            removed.append(target["commodity"])
        removed_names.append(target["name"])

    st.session_state[rem_key] = removed
    if st.session_state.get("selected_commodity") in removed:
        st.session_state["selected_commodity"] = None

    actions: list[str] = []
    if trimmed_qty_count:
        actions.append(f"reduced {trimmed_qty_count} extra quantit{'y' if trimmed_qty_count == 1 else 'ies'}")
    if removed_names:
        actions.append(f"removed {', '.join(removed_names)}")

    summary = " and ".join(actions) if actions else "adjusted items"
    st.session_state[f"{mode}_autofit_note"] = (
        f"Auto-fit to £{budget_limit:.0f}: {summary} (kept Bargain staples prioritized)."
    )


# ---------------------------------------------------------------------------
# --- Section 3: CSS theming ---
# ---------------------------------------------------------------------------

def inject_theme_css(primary: str, deep: str) -> None:
    """Inject clean, balanced editorial CSS theme."""
    warm_sand   = COLOUR_TOKENS["warm_sand"]
    pure_white  = COLOUR_TOKENS["pure_white"]
    riso_sky    = COLOUR_TOKENS["riso_sky"]
    darker_sand = COLOUR_TOKENS["darker_sand"]
    warm_slate  = COLOUR_TOKENS["warm_slate"]

    css = f"""
<style>
/* ---- Editorial Canvas & Generous Spacing ---- */
.stApp {{
background-color: {warm_sand};
}}
.block-container {{
max-width: 1240px !important;
padding-top: 1.25rem !important;
padding-bottom: 5.5rem !important;
}}
.mtt-section-gap {{
height: 1.15rem;
}}
.mtt-section-title {{
font-size: 1.15rem;
font-weight: 800;
color: {deep};
margin: 0 0 0.65rem 0;
letter-spacing: -0.2px;
}}

/* ---- Prominent Editorial Header Banner ---- */
.mtt-header {{
background-color: {deep};
color: {pure_white};
padding: 1.35rem 2rem;
border-radius: 18px;
margin-bottom: 1rem;
display: flex;
align-items: center;
justify-content: space-between;
box-shadow: 0 4px 14px rgba(0,0,0,0.10);
}}

/* ---- Total Saved vs Standard Shop Banner ---- */
.mtt-savings-banner {{
background-color: {pure_white};
border: 2px solid {primary};
border-radius: 16px;
padding: 0.95rem 1.4rem;
margin-bottom: 1.1rem;
display: flex;
flex-wrap: wrap;
align-items: center;
justify-content: space-between;
gap: 1rem;
box-shadow: 0 3px 10px rgba(0,0,0,0.05);
}}
.mtt-savings-stat {{
display: flex;
flex-direction: column;
}}
.mtt-savings-label {{
font-size: 0.72rem;
font-weight: 700;
text-transform: uppercase;
letter-spacing: 0.5px;
color: {warm_slate};
}}
.mtt-savings-value {{
font-size: 1.35rem;
font-weight: 800;
color: {deep};
line-height: 1.2;
}}
.mtt-savings-sub {{
font-size: 0.78rem;
color: {warm_slate};
}}

/* ---- Category / status badges ---- */
.mtt-badge {{
display: inline-block;
padding: 3px 11px;
border-radius: 999px;
font-size: 0.75rem;
font-weight: 600;
background-color: {primary};
color: {pure_white};
}}
.mtt-badge-bargain {{
background-color: #3A7D44;
color: {pure_white};
}}
.mtt-badge-surge {{
background-color: #C0392B;
color: {pure_white};
}}
.mtt-badge-stable {{
background-color: {warm_slate};
color: {pure_white};
}}

/* ---- Single-Row Commodity Strip Tiles (1:1 Square) ---- */
.mtt-strip-tile {{
display: flex;
flex-direction: column;
align-items: center;
text-align: center;
padding: 4px 2px;
}}
.mtt-strip-frame {{
width: 68px;
height: 68px;
aspect-ratio: 1 / 1;
border-radius: 14px;
border: 2px solid {primary};
background-color: {riso_sky};
background-image: repeating-linear-gradient(
135deg,
{primary}22 0px,
{primary}22 2px,
transparent 2px,
transparent 9px
);
display: flex;
align-items: center;
justify-content: center;
padding: 5px;
transition: transform 0.25s cubic-bezier(0.22, 1, 0.36, 1);
}}
.mtt-strip-frame:hover {{
transform: scale(1.06);
}}
.mtt-strip-frame img {{
width: 100%;
height: 100%;
object-fit: contain;
border-radius: 8px;
}}
.mtt-strip-mono {{
width: 68px;
height: 68px;
aspect-ratio: 1 / 1;
border-radius: 14px;
border: 2px solid {primary};
background-color: {riso_sky};
display: flex;
align-items: center;
justify-content: center;
font-size: 1.15rem;
font-weight: 700;
color: {primary};
}}
.mtt-strip-label {{
margin: 6px 0 3px 0;
font-size: 0.75rem;
font-weight: 700;
color: {deep};
white-space: nowrap;
overflow: hidden;
text-overflow: ellipsis;
max-width: 100%;
}}

/* ---- Basket Card Square Frame (1:1 Square) ---- */
.mtt-art-frame {{
width: 118px;
height: 118px;
aspect-ratio: 1 / 1;
border-radius: 16px;
border: 2.5px solid {primary};
background-color: {riso_sky};
background-image: repeating-linear-gradient(
135deg,
{primary}22 0px,
{primary}22 2px,
transparent 2px,
transparent 10px
);
overflow: hidden;
display: flex;
align-items: center;
justify-content: center;
flex-shrink: 0;
padding: 7px;
transition: transform 0.28s cubic-bezier(0.22, 1, 0.36, 1);
}}
.mtt-art-frame:hover {{
transform: scale(1.04);
}}
.mtt-art-frame img {{
width: 100%;
height: 100%;
object-fit: contain;
border-radius: 10px;
}}
.mtt-monogram {{
width: 118px;
height: 118px;
aspect-ratio: 1 / 1;
border-radius: 16px;
border: 2.5px solid {primary};
background-color: {riso_sky};
display: flex;
align-items: center;
justify-content: center;
font-size: 2rem;
font-weight: 700;
color: {primary};
flex-shrink: 0;
}}

/* ---- Clean, non-wrapping buttons ---- */
div[data-testid="stButton"] > button {{
white-space: nowrap !important;
padding: 0.28rem 0.55rem !important;
min-height: 2rem !important;
font-size: 0.78rem !important;
border-radius: 9px !important;
}}

/* ---- PowerPoint Morph-style Split Animations ---- */
@keyframes mttExpandLeft {{
0% {{
opacity: 0.2;
transform: scale(0.88) translateX(-20px);
}}
100% {{
opacity: 1;
transform: scale(1) translateX(0);
}}
}}
@keyframes mttHeroZoom {{
0% {{
transform: scale(0.7);
opacity: 0.3;
}}
100% {{
transform: scale(1);
opacity: 1;
}}
}}
@keyframes mttSlideRight {{
0% {{
opacity: 0;
transform: translateX(30px);
}}
100% {{
opacity: 1;
transform: translateX(0);
}}
}}

.mtt-split-left {{
animation: mttExpandLeft 0.42s cubic-bezier(0.22, 1, 0.36, 1) forwards;
}}
.mtt-split-right {{
animation: mttSlideRight 0.46s cubic-bezier(0.22, 1, 0.36, 1) forwards;
}}
.mtt-hero-frame {{
width: 215px;
height: 215px;
aspect-ratio: 1 / 1;
border-radius: 22px;
border: 3px solid {primary};
background-color: {riso_sky};
background-image: repeating-linear-gradient(
135deg,
{primary}22 0px,
{primary}22 2px,
transparent 2px,
transparent 10px
);
display: flex;
align-items: center;
justify-content: center;
padding: 12px;
margin: 0 auto 1rem auto;
animation: mttHeroZoom 0.46s cubic-bezier(0.22, 1, 0.36, 1) forwards;
}}
.mtt-hero-frame img {{
width: 100%;
height: 100%;
object-fit: contain;
border-radius: 14px;
}}
.mtt-hero-monogram {{
width: 215px;
height: 215px;
aspect-ratio: 1 / 1;
border-radius: 22px;
border: 3px solid {primary};
background-color: {riso_sky};
display: flex;
align-items: center;
justify-content: center;
font-size: 3.2rem;
font-weight: 700;
color: {primary};
margin: 0 auto 1rem auto;
animation: mttHeroZoom 0.46s cubic-bezier(0.22, 1, 0.36, 1) forwards;
}}

/* ---- Elevated Editorial Cards ---- */
.mtt-card {{
background-color: {pure_white};
border-radius: 20px;
box-shadow: 0 3px 12px rgba(0,0,0,0.06);
padding: 1.15rem 1.4rem;
margin-bottom: 0.65rem;
}}
.mtt-item-spacer {{
height: 1.1rem;
}}

.mtt-metric-box {{
background-color: {warm_sand};
border-radius: 14px;
padding: 0.85rem 1.05rem;
border-left: 4px solid {primary};
margin-bottom: 0.85rem;
}}

.mtt-recipe-heading-pill {{
background-color: {riso_sky};
color: {deep};
border-radius: 10px;
padding: 0.55rem 0.95rem;
font-weight: 700;
font-size: 0.9rem;
margin-bottom: 0.45rem;
border-left: 4px solid {primary};
}}

/* ---- Progress bar ---- */
.mtt-progress-track {{
background-color: {darker_sand};
border-radius: 999px;
height: 11px;
width: 100%;
overflow: hidden;
}}
.mtt-progress-fill {{
height: 100%;
border-radius: 999px;
background-color: {primary};
transition: width 0.25s ease;
}}
.mtt-progress-fill-over {{
height: 100%;
border-radius: 999px;
background-color: {COLOUR_TOKENS["warm_ochre"]};
width: 100%;
}}

/* ---- Summary bar ---- */
.mtt-summary-bar {{
position: fixed;
bottom: 0;
left: 0;
right: 0;
background-color: {deep};
color: {pure_white};
padding: 0.75rem 2rem;
display: flex;
align-items: center;
gap: 1.5rem;
z-index: 999;
border-radius: 16px 16px 0 0;
}}

.mtt-impact-pill {{
display: inline-block;
background-color: {primary};
color: {pure_white};
border-radius: 999px;
padding: 4px 13px;
font-size: 0.8rem;
font-weight: 600;
white-space: nowrap;
}}

/* ---- Tabs ---- */
.stTabs [data-baseweb="tab-list"] {{
background-color: {darker_sand};
border-radius: 12px;
gap: 6px;
padding: 4px;
margin-bottom: 0.75rem;
}}
.stTabs [aria-selected="true"] {{
background-color: {primary} !important;
color: {pure_white} !important;
border-radius: 9px;
}}
</style>
"""
    st.markdown(css, unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# --- Section 4: Pipeline cache ---
# ---------------------------------------------------------------------------

@st.cache_data(ttl=300, show_spinner=False)
def cached_pipeline(calendar_name: str) -> dict:
    """Import main via importlib, call run_market_to_table, return result dict."""
    try:
        main_path = Path(__file__).resolve().parent / "main.py"
        spec = importlib.util.spec_from_file_location("main", main_path)
        main_mod = importlib.util.module_from_spec(spec)  # type: ignore[arg-type]
        sys.modules.setdefault("main", main_mod)
        spec.loader.exec_module(main_mod)  # type: ignore[union-attr]
        return main_mod.run_market_to_table(calendar_name)
    except Exception as exc:  # noqa: BLE001
        return {"error": str(exc)}


# ---------------------------------------------------------------------------
# --- Section 5: Checkout & Standard-Shop Comparison Logic ---
# ---------------------------------------------------------------------------

def get_active_basket(basket: list[dict], session_state: Any, mode: str) -> list[dict]:
    """Return basket items that have not been removed by the user."""
    removed = set(session_state.get(f"{mode}_removed_items", []))
    return [item for item in basket if item.get("commodity", "") not in removed]


def compute_checkout(
    basket: list[dict],
    session_state: Any,
    mode: str,
) -> tuple[Decimal, int, int]:
    """Return (checkout_total_decimal, total_prep_mins, active_item_count)."""
    total = Decimal("0")
    prep_mins = 0
    item_count = 0

    for item in get_active_basket(basket, session_state, mode):
        commodity = item.get("commodity", "")
        qty_key = f"{mode}_{commodity}_qty"
        cup_key = f"{mode}_{commodity}_cupboard"

        qty = session_state.get(qty_key, 1)
        in_cup = session_state.get(cup_key, False)

        if in_cup or qty == 0:
            continue

        price = Decimal(str(item.get("estimated_price_gbp", 0.0)))
        total += price * qty
        prep_mins += item.get("prep_time_mins", 0)
        item_count += 1

    return total, prep_mins, item_count


def compute_savings_vs_standard(
    basket: list[dict],
    session_state: Any,
    mode: str,
) -> dict[str, Any]:
    """Compare smart basket against a standard unswapped supermarket shop."""
    active_items = get_active_basket(basket, session_state, mode)
    standard_total = Decimal("0")
    smart_total = Decimal("0")
    prep_saved = 0
    surges_dodged = 0

    for item in active_items:
        commodity = item.get("commodity", "")
        qty_key = f"{mode}_{commodity}_qty"
        cup_key = f"{mode}_{commodity}_cupboard"

        qty = session_state.get(qty_key, 1)
        in_cup = session_state.get(cup_key, False)
        if qty == 0:
            continue

        price = Decimal(str(item.get("estimated_price_gbp", 0.0)))
        status = item.get("market_status", "")

        if status.startswith("Surge"):
            surges_dodged += 1
            unswapped_unit = price * Decimal("1.28")
        elif status.startswith("Bargain"):
            unswapped_unit = price * Decimal("1.16")
        else:
            unswapped_unit = price * Decimal("1.06")

        standard_total += unswapped_unit * qty
        if not in_cup:
            smart_total += price * qty

            deltas = PREP_DELTA_LOOKUP.get(commodity, {})
            fs_mins = deltas.get("from_scratch", 0)
            mp_mins = deltas.get("minimal_prep", 0)
            if mode == "minimal_prep":
                prep_saved += max(0, fs_mins - mp_mins)
            else:
                prep_saved += 3 if status.startswith(("Surge", "Bargain")) else 0

    money_saved = max(Decimal("0.00"), standard_total - smart_total)
    return {
        "standard_total": standard_total.quantize(Decimal("0.01")),
        "smart_total": smart_total.quantize(Decimal("0.01")),
        "money_saved": money_saved.quantize(Decimal("0.01")),
        "prep_time_saved": prep_saved,
        "surges_dodged": surges_dodged,
    }


# ---------------------------------------------------------------------------
# --- Section 6: Shopping list text ---
# ---------------------------------------------------------------------------

def build_shopping_list_txt(
    basket: list[dict],
    session_state: Any,
    mode: str,
) -> str:
    """Return newline-separated lines for active items with qty > 0 and cupboard False."""
    lines: list[str] = []

    for item in get_active_basket(basket, session_state, mode):
        commodity = item.get("commodity", "")
        qty_key = f"{mode}_{commodity}_qty"
        cup_key = f"{mode}_{commodity}_cupboard"

        qty = session_state.get(qty_key, 1)
        in_cup = session_state.get(cup_key, False)

        if in_cup or qty == 0:
            continue

        name = item.get("item_name", "")
        brand = item.get("brand", "")
        price = float(item.get("estimated_price_gbp", 0.0))
        lines.append(f"{qty}x {name} ({brand}) - £{price:.2f}")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# --- Section 7: Prominent Banner, Savings Highlight & Top Controls ---
# ---------------------------------------------------------------------------

def render_banner_and_controls(
    data: dict,
    checkout_total: Decimal,
    savings: dict[str, Any],
    basket: list[dict],
    default_budget: int = 25,
) -> None:
    """Render the Market-to-Table banner, Total Saved highlight card, and top controls."""
    stress_status = data.get("stress_status", "")
    meal_prep_mode = data.get("meal_prep_mode", "from_scratch")

    is_burnout = meal_prep_mode == "minimal_prep"
    primary = COLOUR_TOKENS["warm_ochre"] if is_burnout else COLOUR_TOKENS["sage_olive"]
    deep = COLOUR_TOKENS["deep_roasted"] if is_burnout else COLOUR_TOKENS["deep_forest"]

    inject_theme_css(primary=primary, deep=deep)
    apply_cottagecore_theme(is_stressed=is_burnout)


    badge_text = stress_status if stress_status else "Status unavailable"
    st.markdown(
        f'<div class="mtt-header">'
        f'<div>'
        f'<div style="font-size:1.75rem;font-weight:800;letter-spacing:-0.5px;line-height:1.15;">Market-to-Table</div>'
        f'<div style="font-size:0.88rem;opacity:0.88;margin-top:4px;">Schedule-aware grocery planner powered by live commodity signals</div>'
        f'</div>'
        f'<span class="mtt-badge" style="font-size:0.82rem;padding:6px 14px;">{badge_text}</span>'
        f'</div>',
        unsafe_allow_html=True,
    )

    money_saved = savings.get("money_saved", Decimal("0.00"))
    standard_total = savings.get("standard_total", Decimal("0.00"))
    smart_total = savings.get("smart_total", Decimal("0.00"))
    prep_saved = savings.get("prep_time_saved", 0)
    surges_dodged = savings.get("surges_dodged", 0)

    st.markdown(
        f'<div class="mtt-savings-banner">'
        f'<div class="mtt-savings-stat">'
        f'<span class="mtt-savings-label">Total Saved vs. Standard Shop</span>'
        f'<span class="mtt-savings-value">£{money_saved:.2f} saved</span>'
        f'<span class="mtt-savings-sub">Standard shop: £{standard_total:.2f} → Smart basket: £{smart_total:.2f}</span>'
        f'</div>'
        f'<div class="mtt-savings-stat">'
        f'<span class="mtt-savings-label">Prep Time Saved</span>'
        f'<span class="mtt-savings-value">{prep_saved} mins</span>'
        f'<span class="mtt-savings-sub">Tailored to your weekly schedule</span>'
        f'</div>'
        f'<div class="mtt-savings-stat">'
        f'<span class="mtt-savings-label">Market Protection</span>'
        f'<span class="mtt-savings-value">{surges_dodged} surge{"s" if surges_dodged != 1 else ""} dodged</span>'
        f'<span class="mtt-savings-sub">Swapped to stable or bargain staples</span>'
        f'</div>'
        f'</div>',
        unsafe_allow_html=True,
    )

    col_mode, col_budget = st.columns([1, 1.35], gap="large")

    with col_mode:
        st.markdown(
            f'<p style="margin:0 0 6px 0;font-size:0.82rem;font-weight:700;color:{deep};'
            f'text-transform:uppercase;letter-spacing:0.5px;">Schedule Mode</p>',
            unsafe_allow_html=True,
        )
        calendar_options = [
            "Demo - Calm Week",
            "Demo - Burnout Week",
            "Live Google Calendar",
        ]
        st.selectbox(
            "Select calendar mode",
            options=calendar_options,
            key="calendar_mode_select",
            label_visibility="collapsed",
        )

    with col_budget:
        budget_val: int = st.slider(
            "Weekly Grocery Budget",
            min_value=10,
            max_value=60,
            value=st.session_state.get("weekly_budget_slider", default_budget),
            step=1,
            format="£%d",
            key="weekly_budget_slider",
        )
        ratio = float(checkout_total) / budget_val if budget_val > 0 else 0.0
        ratio = min(ratio, 1.0)
        pct = int(ratio * 100)
        over = float(checkout_total) > budget_val

        fill_class = "mtt-progress-fill-over" if over else "mtt-progress-fill"
        over_html = (
            f'<span style="color:{COLOUR_TOKENS["warm_ochre"]};font-size:0.82rem;font-weight:700;">'
            f'Over budget by £{float(checkout_total) - budget_val:.2f}</span>'
            if over else
            f'<span style="color:{COLOUR_TOKENS["warm_slate"]};font-size:0.8rem;">Within weekly budget</span>'
        )
        st.markdown(
            f'<div style="display:flex;justify-content:space-between;margin-bottom:5px;font-size:0.84rem;">'
            f'<span>Basket Total: <strong>£{float(checkout_total):.2f}</strong> / £{budget_val}</span>'
            f'{over_html}'
            f'</div>'
            f'<div class="mtt-progress-track">'
            f'<div class="{fill_class}" style="width:{pct}%;"></div>'
            f'</div>',
            unsafe_allow_html=True,
        )

        if over and basket:
            st.markdown('<div style="height:6px;"></div>', unsafe_allow_html=True)
            st.button(
                f"⚡ Auto-Fit to £{budget_val} Budget",
                key=f"autofit_btn_{meal_prep_mode}",
                on_click=_auto_fit_to_budget,
                args=(basket, meal_prep_mode),
                type="primary",
                use_container_width=True,
            )

        autofit_note = st.session_state.get(f"{meal_prep_mode}_autofit_note")
        if autofit_note:
            st.caption(autofit_note)


# ---------------------------------------------------------------------------
# --- Section 8: Single-Row Commodity Strip ---
# ---------------------------------------------------------------------------

def _build_commodity_lookup(data: dict) -> dict[str, dict]:
    """Index all commodity status & price dicts regardless of key formatting."""
    lookup: dict[str, dict] = {}
    candidate_lists = [
        data.get("active_market_movers", []),
        data.get("commodity_analysis", []),
        data.get("market_analysis", []),
    ]
    for entries in candidate_lists:
        if not isinstance(entries, list):
            continue
        for entry in entries:
            if not isinstance(entry, dict):
                continue
            for field in ("commodity", "item_name", "name", "key"):
                raw_val = entry.get(field)
                if isinstance(raw_val, str) and raw_val.strip():
                    lookup[_norm_key(raw_val)] = entry
                    break
    return lookup


def render_commodity_grid(data: dict, basket: list[dict]) -> None:
    """Render all 13 commodities in ONE clean, well-spaced horizontal row."""
    st.markdown('<p class="mtt-section-title">Tracked Commodities</p>', unsafe_allow_html=True)

    lookup = _build_commodity_lookup(data)
    basket_status_map = {
        _norm_key(item.get("commodity", "")): item.get("market_status", "")
        for item in basket
    }

    missing_assets: list[str] = []
    cols = st.columns(len(COMMODITY_KEYS), gap="small")

    for col, commodity in zip(cols, COMMODITY_KEYS):
        with col:
            img_uri = get_base64_image(commodity)
            entry = lookup.get(commodity, {})
            raw_status = (
                entry.get("market_status")
                or basket_status_map.get(commodity)
                or "Stable"
            )
            status_word = raw_status.split()[0] if raw_status else "Stable"

            if status_word == "Bargain":
                badge_class = "mtt-badge-bargain"
            elif status_word == "Surge":
                badge_class = "mtt-badge-surge"
            else:
                badge_class = "mtt-badge-stable"

            if img_uri:
                frame_html = (
                    f'<div class="mtt-strip-frame">'
                    f'<img src="{img_uri}" alt="{commodity}" />'
                    f'</div>'
                )
            else:
                monogram = commodity[:2].upper()
                frame_html = f'<div class="mtt-strip-mono">{monogram}</div>'
                missing_assets.append(f"{commodity}.png")

            short_name = SHORT_LABELS.get(commodity, commodity.replace("_", " ").title())
            st.markdown(
                f'<div class="mtt-strip-tile">'
                f'{frame_html}'
                f'<p class="mtt-strip-label" title="{commodity.replace("_", " ").title()}">{short_name}</p>'
                f'<span class="mtt-badge {badge_class}" style="font-size:0.66rem;padding:2px 7px;margin-bottom:4px;">{status_word}</span>'
                f'</div>',
                unsafe_allow_html=True,
            )
            st.button(
                "View",
                key=f"grid_inspect_{commodity}",
                on_click=_select_commodity,
                args=(commodity,),
                use_container_width=True,
            )

    if missing_assets:
        st.caption(f"Missing artwork: {', '.join(dict.fromkeys(missing_assets))}")


# ---------------------------------------------------------------------------
# --- Section 9: Basket cards (with Remove & Individual/Full Restore) ---
# ---------------------------------------------------------------------------

def render_basket_cards(basket: list[dict], mode: str) -> None:
    """Render spacious Basket_Cards with steppers, cupboard toggle, and Remove/Restore."""
    removed_list = st.session_state.get(f"{mode}_removed_items", [])
    if removed_list:
        name_lookup = {
            item.get("commodity", ""): item.get("item_name") or item.get("commodity", "").replace("_", " ").title()
            for item in basket
        }
        st.caption("Removed from basket (click to restore and update meal ideas):")
        restore_cols = st.columns(len(removed_list) + 1, gap="small")
        for idx, rem_comm in enumerate(removed_list):
            with restore_cols[idx]:
                label = name_lookup.get(rem_comm, rem_comm.replace("_", " ").title())
                st.button(
                    f"↩ {label}",
                    key=f"restore_one_{mode}_{rem_comm}",
                    on_click=_restore_single_item,
                    args=(mode, rem_comm),
                    use_container_width=True,
                )
        with restore_cols[-1]:
            st.button(
                "Restore All",
                key=f"restore_all_{mode}",
                on_click=_restore_basket_items,
                args=(mode,),
                use_container_width=True,
            )

    active_basket = get_active_basket(basket, st.session_state, mode)
    if not active_basket:
        st.info("All items have been removed from your basket. Restore an item above to see basket items and meal ideas.")
        return

    for item in active_basket:
        commodity = item.get("commodity", "")
        qty_key = f"{mode}_{commodity}_qty"
        cup_key = f"{mode}_{commodity}_cupboard"

        if qty_key not in st.session_state:
            st.session_state[qty_key] = 1
        if cup_key not in st.session_state:
            st.session_state[cup_key] = False

        in_cup = st.session_state[cup_key]
        qty = st.session_state[qty_key]
        price = item.get("estimated_price_gbp", 0.0)
        name = item.get("item_name", "")
        brand = item.get("brand", "")
        prep = item.get("prep_time_mins", 0)
        reason = item.get("swap_reason", "")
        mstatus = item.get("market_status", "")
        line_price = price * qty

        img_uri = get_base64_image(commodity)
        if img_uri:
            art_html = (
                f'<div class="mtt-art-frame" style="opacity:{"0.55" if in_cup else "1"};">'
                f'<img src="{img_uri}" alt="{commodity}" /></div>'
            )
        else:
            monogram = commodity[:2].upper()
            art_html = (
                f'<div class="mtt-monogram" style="opacity:{"0.55" if in_cup else "1"};">'
                f'{monogram}</div>'
            )

        cup_badge = (
            '<span style="font-size:0.76rem;color:#6E6559;display:block;margin-top:4px;">'
            'In Cupboard - £0.00</span>'
            if in_cup else ""
        )
        card_opacity = "0.55" if in_cup else "1.0"

        is_burnout = mode == "minimal_prep"
        deep = COLOUR_TOKENS["deep_roasted"] if is_burnout else COLOUR_TOKENS["deep_forest"]

        st.markdown(
            f'<div class="mtt-card" style="opacity:{card_opacity};display:flex;gap:20px;align-items:center;">'
            f'{art_html}'
            f'<div style="flex:1;min-width:0;">'
            f'<p style="margin:0;font-size:1.08rem;font-weight:700;color:{deep};'
            f'white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">{name}</p>'
            f'<p style="margin:2px 0 0 0;font-size:0.84rem;color:{COLOUR_TOKENS["warm_slate"]};">{brand}</p>'
            f'<span class="mtt-badge" style="margin:6px 0;display:inline-block;">{prep} mins</span>'
            f'<p style="margin:3px 0 0 0;font-size:0.82rem;color:{COLOUR_TOKENS["warm_slate"]};">{reason}</p>'
            f'{cup_badge}'
            f'</div>'
            f'<div style="text-align:right;min-width:100px;">'
            f'<p style="margin:0;font-size:1.15rem;font-weight:700;color:{deep};">£{line_price:.2f}</p>'
            f'<span class="mtt-badge">{mstatus.split("(")[0].strip()}</span>'
            f'</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

        col_inspect, col_minus, col_qty, col_plus, col_cup, col_remove, _col_pad = st.columns(
            [1.05, 0.42, 0.42, 0.42, 2.15, 1.15, 2.39],
            gap="small",
        )
        with col_inspect:
            st.button(
                "Inspect",
                key=f"basket_inspect_{mode}_{commodity}",
                on_click=_select_commodity,
                args=(commodity,),
                use_container_width=True,
            )
        with col_minus:
            st.button(
                "-",
                key=f"minus_{mode}_{commodity}",
                on_click=_dec_qty,
                args=(qty_key,),
                use_container_width=True,
            )
        with col_qty:
            st.markdown(
                f'<p style="text-align:center;font-weight:700;margin:0;padding-top:5px;font-size:0.95rem;">'
                f'{st.session_state[qty_key]}</p>',
                unsafe_allow_html=True,
            )
        with col_plus:
            st.button(
                "+",
                key=f"plus_{mode}_{commodity}",
                on_click=_inc_qty,
                args=(qty_key,),
                use_container_width=True,
            )
        with col_cup:
            st.checkbox(
                "Already in cupboard",
                key=cup_key,
            )
        with col_remove:
            st.button(
                "✕ Remove",
                key=f"remove_{mode}_{commodity}",
                on_click=_remove_basket_item,
                args=(mode, commodity),
                use_container_width=True,
            )

        st.markdown('<div class="mtt-item-spacer"></div>', unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# --- Section 10: Meal cards (Dynamically excludes removed basket items) ---
# ---------------------------------------------------------------------------

def render_meal_cards(
    active_ingredients: list[str],
    mode: str,
    excluded_ingredients: set[str],
) -> None:
    """Filter MEAL_LIBRARY by active ingredients while strictly hiding meals using removed items."""
    if len(active_ingredients) < 2:
        st.info("Add or restore items in your basket to see matching meal ideas.")
        return

    matched: list[dict] = []
    hidden_due_to_removal: list[str] = []

    for meal in MEAL_LIBRARY:
        if meal["mode"] != mode:
            continue
        meal_commodities = set(meal["commodities"])
        overlap = meal_commodities & set(active_ingredients)
        if len(overlap) < 2:
            continue

        if meal_commodities & excluded_ingredients:
            hidden_due_to_removal.append(meal["title"])
            continue

        matched.append(meal)
        if len(matched) == 3:
            break

    if not matched:
        if hidden_due_to_removal:
            removed_names = ", ".join(
                c.replace("_", " ").title() for c in sorted(excluded_ingredients)
            )
            st.info(
                f"Meal ideas using removed items ({removed_names}) are hidden. "
                "Restore those items in your Shopping Basket to bring their recipes back."
            )
        else:
            st.info(
                "No meals matched your current basket. "
                "Try adding more items or adjusting your selections."
            )
        return

    is_burnout = mode == "minimal_prep"
    deep = COLOUR_TOKENS["deep_roasted"] if is_burnout else COLOUR_TOKENS["deep_forest"]

    for meal in matched:
        thumbs_html = ""
        for commodity in meal["commodities"]:
            img_uri = get_base64_image(commodity)
            if img_uri:
                thumbs_html += (
                    f'<div class="mtt-art-frame" style="width:58px;height:58px;">'
                    f'<img src="{img_uri}" alt="{commodity}" /></div>'
                )
            else:
                monogram = commodity[:2].upper()
                thumbs_html += (
                    f'<div class="mtt-monogram" style="width:58px;height:58px;font-size:1.1rem;">'
                    f'{monogram}</div>'
                )

        steps_html = "".join(
            f'<li style="font-size:0.84rem;margin-bottom:5px;">{step}</li>'
            for step in meal["steps"]
        )

        ingredient_tags_html = ""
        for commodity in meal["commodities"]:
            if commodity in active_ingredients:
                label = "In basket"
                bg = "#3A7D44"
            else:
                label = "In cupboard"
                bg = COLOUR_TOKENS["warm_slate"]
            ingredient_tags_html += (
                f'<span style="background:{bg};color:#FFF;border-radius:999px;'
                f'padding:3px 9px;font-size:0.74rem;margin-right:5px;">'
                f'{commodity.replace("_", " ").title()} - {label}</span>'
            )

        st.markdown(
            f'<div class="mtt-card mtt-recipe-card" style="margin-bottom:1.1rem;">'
            f'<p class="mtt-recipe-card-title" style="margin:0 0 6px 0;font-size:1.1rem;font-weight:700;color:{deep};">{meal["title"]}</p>'
            f'<p style="margin:0 0 10px 0;font-size:0.8rem;color:{COLOUR_TOKENS["warm_slate"]};">'
            f'{meal["prep_total_mins"]} min total &nbsp;|&nbsp; {meal["cook_time_mins"]} min cook</p>'
            f'<div style="display:flex;gap:10px;flex-wrap:wrap;margin-bottom:10px;">{thumbs_html}</div>'
            f'<div style="margin-bottom:10px;">{ingredient_tags_html}</div>'
            f'<ol style="padding-left:1.25rem;margin:0;">{steps_html}</ol>'
            f'</div>',
            unsafe_allow_html=True,
        )

    if hidden_due_to_removal:
        removed_names = ", ".join(
            c.replace("_", " ").title() for c in sorted(excluded_ingredients)
        )
        st.caption(
            f"Hiding {len(hidden_due_to_removal)} meal suggestion(s) that include removed basket items: {removed_names}."
        )


# ---------------------------------------------------------------------------
# --- Section 11: Summary bar ---
# ---------------------------------------------------------------------------

def format_gbp(value: Decimal) -> str:
    """Return ``£{value:.2f}`` using only ASCII-compatible characters."""
    return f"\u00a3{value:.2f}"


def render_summary_bar(
    checkout_total: Decimal,
    prep_mins: int,
    item_count: int,
    savings: dict[str, Any],
    basket: list[dict],
    session_state: Any,
    mode: str,
) -> None:
    """Render the fixed bottom Summary_Bar."""
    money_saved = savings.get("money_saved", Decimal("0.00"))
    prep_saved = savings.get("prep_time_saved", 0)
    total_str = format_gbp(checkout_total)

    impact_text = f"Saved £{money_saved:.2f} · {prep_saved} min saved"

    st.markdown(
        f'<div class="mtt-summary-bar">'
        f'<span class="mtt-impact-pill">{impact_text}</span>'
        f'<span style="font-size:1.15rem;font-weight:700;">{total_str}</span>'
        f'<span style="font-size:0.88rem;">{prep_mins} min prep</span>'
        f'<span style="font-size:0.88rem;">{item_count} item{"s" if item_count != 1 else ""}</span>'
        f'</div>'
        f'<div style="height:72px;"></div>',
        unsafe_allow_html=True,
    )

    shopping_txt = build_shopping_list_txt(basket, session_state, mode)
    st.download_button(
        label="Download Shopping List",
        data=shopping_txt.encode("utf-8"),
        file_name="shopping_list.txt",
        mime="text/plain",
    )

# ---------------------------------------------------------------------------
# --- Section 12: Split detail view (50/50 PowerPoint-style + Sparkline) ---
# ---------------------------------------------------------------------------

def _extract_pct_change(mover_entry: dict, basket_entry: dict, raw_status: str) -> float | None:
    """Extract numeric percentage shift from explicit keys, text strings, or price pairs."""
    numeric_keys = (
        "pct_change", "percent_change", "percentage_change",
        "change_pct", "move_pct", "price_change_pct", "delta_pct", "change",
    )
    for source in (mover_entry, basket_entry):
        for k in numeric_keys:
            val = source.get(k)
            if isinstance(val, (int, float)) and val != 0:
                return float(val)
            if isinstance(val, str):
                m = re.search(r"([+-]?\d+(?:\.\d+)?)", val)
                if m and float(m.group(1)) != 0:
                    return float(m.group(1))

    for text in (raw_status, basket_entry.get("swap_reason", "")):
        if isinstance(text, str):
            m = re.search(r"([+-]?\d+(?:\.\d+)?)\s*%", text)
            if m and float(m.group(1)) != 0:
                return float(m.group(1))

    curr = mover_entry.get("current_price") or mover_entry.get("latest_price") or mover_entry.get("price")
    prev = mover_entry.get("previous_price") or mover_entry.get("prev_price") or mover_entry.get("baseline_price")
    if isinstance(curr, (int, float)) and isinstance(prev, (int, float)) and prev > 0:
        calc = ((float(curr) - float(prev)) / float(prev)) * 100.0
        if round(calc, 2) != 0:
            return calc

    return None


def render_split_detail_view(
    commodity: str,
    data: dict,
    basket: list[dict],
    mode: str,
) -> None:
    """Render a 50/50 split screen with 30-day price sparkline and recipe headings."""
    is_burnout = mode == "minimal_prep"
    primary = COLOUR_TOKENS["warm_ochre"] if is_burnout else COLOUR_TOKENS["sage_olive"]
    deep = COLOUR_TOKENS["deep_roasted"] if is_burnout else COLOUR_TOKENS["deep_forest"]

    lookup = _build_commodity_lookup(data)
    mover_entry = lookup.get(_norm_key(commodity), {})

    basket_entry: dict = {}
    for item in basket:
        if _norm_key(item.get("commodity", "")) == _norm_key(commodity):
            basket_entry = item
            break

    raw_status = (
        mover_entry.get("market_status")
        or basket_entry.get("market_status")
        or "Stable"
    )
    status_word = raw_status.split()[0] if raw_status else "Stable"

    extracted_pct = _extract_pct_change(mover_entry, basket_entry, raw_status)
    spark = fetch_commodity_sparkline(commodity, status_word, extracted_pct)

    pct_val = extracted_pct if extracted_pct is not None else spark["pct_30d"]
    if status_word == "Bargain" and pct_val > 0:
        pct_val = -pct_val
    elif status_word == "Surge" and pct_val < 0:
        pct_val = abs(pct_val)

    shelf_price = float(basket_entry.get("estimated_price_gbp", 0.0))
    if shelf_price > 0 and (1.0 + pct_val / 100.0) > 0:
        prev_shelf_price = shelf_price / (1.0 + pct_val / 100.0)
        shelf_diff = shelf_price - prev_shelf_price
    else:
        prev_shelf_price = shelf_price
        shelf_diff = 0.0

    recipe_headings: list[str] = []
    for meal in MEAL_LIBRARY:
        if commodity in meal.get("commodities", []):
            if meal["title"] not in recipe_headings:
                recipe_headings.append(meal["title"])
    for extra_title in EXTRA_RECIPE_HEADINGS.get(commodity, []):
        if len(recipe_headings) >= 3:
            break
        if extra_title not in recipe_headings:
            recipe_headings.append(extra_title)

    left_col, right_col = st.columns([1, 1], gap="large")

    # --- Left 50%: Expanded Square Image & Product Card ---
    with left_col:
        img_uri = get_base64_image(commodity)
        if img_uri:
            hero_html = (
                f'<div class="mtt-hero-frame">'
                f'<img src="{img_uri}" alt="{commodity}" />'
                f'</div>'
            )
        else:
            hero_html = f'<div class="mtt-hero-monogram">{commodity[:2].upper()}</div>'

        display_title = basket_entry.get("item_name") or commodity.replace("_", " ").title()
        brand_line = basket_entry.get("brand", "Tracked Global Commodity")
        swap_note = basket_entry.get("swap_reason", f"Market signal: {raw_status}")

        st.markdown(
            f'<div class="mtt-card mtt-split-left" style="padding:1.65rem;text-align:center;">'
            f'{hero_html}'
            f'<span class="mtt-badge" style="margin-bottom:8px;">{raw_status}</span>'
            f'<h3 style="margin:6px 0 4px 0;color:{deep};">{display_title}</h3>'
            f'<p style="margin:0 0 10px 0;font-size:0.9rem;color:{COLOUR_TOKENS["warm_slate"]};">{brand_line}</p>'
            f'<p style="margin:0;font-size:0.86rem;color:{COLOUR_TOKENS["warm_slate"]};">{swap_note}</p>'
            f'</div>',
            unsafe_allow_html=True,
        )

    # --- Right 50%: Price Change Numbers, 30-Day Sparkline & Recipe Headings ---
    with right_col:
        st.button(
            "✕ Close Split View",
            key="close_split_view_btn",
            on_click=_close_split_view,
        )

        sign_pct = "+" if pct_val > 0 else ""
        headline_metric = f"{sign_pct}{pct_val:.1f}% 30-Day Move ({status_word})"

        futures_line = (
            f'<p style="margin:4px 0 0 0;font-size:0.86rem;color:{COLOUR_TOKENS["warm_slate"]};">'
            f'Futures ({spark["ticker"]}): '
            f'<strong>{spark["start_price"]}</strong> → <strong>{spark["end_price"]}</strong></p>'
        )

        shelf_line = ""
        if shelf_price > 0:
            sign = "+" if shelf_diff > 0 else ""
            shelf_line = (
                f'<p style="margin:6px 0 0 0;font-size:0.9rem;color:{deep};">'
                f'Basket Shelf Impact: <strong>£{prev_shelf_price:.2f}</strong> → '
                f'<strong>£{shelf_price:.2f}</strong> ({sign}£{shelf_diff:.2f} per item)</p>'
            )

        st.markdown(
            f'<div class="mtt-card mtt-split-right" style="padding:1.35rem 1.5rem 0.75rem 1.5rem;">'
            f'<h3 style="margin:0 0 10px 0;color:{deep};">30-Day Price History</h3>'
            f'<div class="mtt-metric-box">'
            f'<p style="margin:0;font-size:1.2rem;font-weight:700;color:{deep};">{headline_metric}</p>'
            f'{futures_line}'
            f'{shelf_line}'
            f'</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

        chart_data = {"Price": spark["prices"]}
        st.area_chart(
            chart_data,
            height=155,
            color=primary,
            use_container_width=True,
        )
        source_caption = (
            f"30-day closing futures trend ({spark['ticker']} via Yahoo Finance)"
            if spark["is_live"]
            else f"30-day commodity trend ({spark['ticker']})"
        )
        st.caption(source_caption)

        headings_html = "".join(
            f'<div class="mtt-recipe-heading-pill">{title}</div>'
            for title in recipe_headings[:3]
        )
        st.markdown(
            f'<div class="mtt-card mtt-split-right" style="padding:1.1rem 1.5rem;">'
            f'<h4 style="margin:0 0 8px 0;color:{deep};">Recipe Ideas</h4>'
            f'{headings_html}'
            f'</div>',
            unsafe_allow_html=True,
        )


# ---------------------------------------------------------------------------
# --- Section 13: Entry point ---
# ---------------------------------------------------------------------------

def main() -> None:
    """Streamlit entry point. Wire all render functions together."""
    st.set_page_config(page_title="Market-to-Table", layout="wide")

    if "selected_commodity" not in st.session_state:
        st.session_state["selected_commodity"] = None

    selected_cal = st.session_state.get("calendar_mode_select", "Demo - Calm Week")
    data = cached_pipeline(selected_cal)

    if "error" in data:
        empty_savings = {
            "standard_total": Decimal("0.00"),
            "smart_total": Decimal("0.00"),
            "money_saved": Decimal("0.00"),
            "prep_time_saved": 0,
            "surges_dodged": 0,
        }
        render_banner_and_controls(
            {"stress_status": "", "meal_prep_mode": "from_scratch"},
            checkout_total=Decimal("0"),
            savings=empty_savings,
            basket=[],
        )
        st.error("Could not load market data. Please try again shortly.")
        return

    meal_prep_mode = data.get("meal_prep_mode", "from_scratch")
    grocery_basket = data.get("grocery_basket", {})
    basket = grocery_basket.get("basket", [])

    checkout_total, prep_mins, item_count = compute_checkout(
        basket, st.session_state, meal_prep_mode
    )
    savings = compute_savings_vs_standard(basket, st.session_state, meal_prep_mode)

    # Prominent Banner + Total Saved Highlight + Schedule & Budget Controls
    render_banner_and_controls(
        data,
        checkout_total=checkout_total,
        savings=savings,
        basket=basket,
        default_budget=25,
    )

    st.markdown('<div class="mtt-section-gap"></div>', unsafe_allow_html=True)

    # Smooth 50/50 split view when a commodity is selected
    selected = st.session_state.get("selected_commodity")
    if selected:
        render_split_detail_view(
            commodity=selected,
            data=data,
            basket=basket,
            mode=meal_prep_mode,
        )
        st.markdown('<div class="mtt-section-gap"></div>', unsafe_allow_html=True)

    # Single-line Commodities strip
    render_commodity_grid(data, basket)

    st.markdown('<div class="mtt-section-gap"></div>', unsafe_allow_html=True)

    # Shopping Basket & Meal Ideas tabs
    tab_basket, tab_meals = st.tabs(["Shopping Basket", "What's on the Table?"])

    with tab_basket:
        if basket:
            render_basket_cards(basket, meal_prep_mode)
        else:
            st.info("Your basket is empty.")

    with tab_meals:
        removed_set = set(st.session_state.get(f"{meal_prep_mode}_removed_items", []))
        excluded_ingredients: set[str] = set(removed_set)
        active_ingredients: list[str] = []

        for item in basket:
            commodity = item.get("commodity", "")
            if commodity in removed_set:
                continue
            qty_key = f"{meal_prep_mode}_{commodity}_qty"
            cup_key = f"{meal_prep_mode}_{commodity}_cupboard"
            qty = st.session_state.get(qty_key, 1)
            in_cup = st.session_state.get(cup_key, False)
            if qty > 0 or in_cup:
                active_ingredients.append(commodity)
            else:
                excluded_ingredients.add(commodity)

        render_meal_cards(active_ingredients, meal_prep_mode, excluded_ingredients)

    # Recompute after potential basket card interactions
    checkout_total, prep_mins, item_count = compute_checkout(
        basket, st.session_state, meal_prep_mode
    )
    savings = compute_savings_vs_standard(basket, st.session_state, meal_prep_mode)
    render_summary_bar(
        checkout_total=checkout_total,
        prep_mins=prep_mins,
        item_count=item_count,
        savings=savings,
        basket=basket,
        session_state=st.session_state,
        mode=meal_prep_mode,
    )


if __name__ == "__main__":
    main()