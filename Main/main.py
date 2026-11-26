import importlib
import json
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

calendar_mod = importlib.import_module("Calendar")
commodity_mod = importlib.import_module("Commodity-analyser")
shopping_mod = importlib.import_module("Shopping-planner")


def run_market_to_table(calendar_name: str = "Demo - Burnout Week") -> dict:
    """Runs the full Market-to-Table pipeline across all three modules."""
    # 1. Fetch live Yahoo Finance prices and classify Bargains vs Surges
    raw_prices = commodity_mod.market_data()
    commodity_analysis = commodity_mod.analyse_commodities(raw_prices)

    # 2. Analyse Google Calendar events for burnout level and prep mode
    burnout_report = calendar_mod.run_burnout_check(calendar_name=calendar_name)
    prep_mode = burnout_report["meal_prep_mode"]

    # 3. Build the UK supermarket shopping cart
    shopping_plan = shopping_mod.build_shopping_cart(
        commodity_analysis=commodity_analysis,
        meal_prep_mode=prep_mode,
    )

    active_movers = [
        item for item in commodity_analysis if item["market_status"] in ("Bargain", "Surge")
    ]

    return {
        "calendar": calendar_name,
        "stress_status": burnout_report["stress_status"],
        "meal_prep_mode": prep_mode,
        "meeting_hours": burnout_report["metrics"]["total_meeting_hours"],
        "active_market_movers": active_movers,
        "grocery_basket": shopping_plan,
    }


if __name__ == "__main__":
    for demo_calendar in ["Demo - Calm Week", "Demo - Burnout Week"]:
        print(f"\n{'=' * 55}")
        print(f"MARKET-TO-TABLE PIPELINE: {demo_calendar}")
        print(f"{'=' * 55}")
        output = run_market_to_table(demo_calendar)
        print(json.dumps(output, indent=2, ensure_ascii=False))