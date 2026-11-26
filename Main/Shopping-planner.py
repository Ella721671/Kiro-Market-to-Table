import json
import requests

OPEN_FOOD_FACTS_URL = "https://uk.openfoodfacts.org/cgi/search.pl"
HEADERS = {"User-Agent": "MarketToTable-Hackathon/1.0 (student-project)"}

# Maps your Commodity-analyser.py item names + market statuses + burnout modes to UK groceries
GROCERY_SWAP_MATRIX = {
    "wheat": {
        "Bargain": {
            "from_scratch": {
                "query": "dried fusilli pasta",
                "fallback_name": "Dried Fusilli Pasta (500g)",
                "fallback_brand": "Tesco",
                "price_gbp": 0.75,
                "prep_mins": 12,
                "nova": 1,
                "reason": "Wheat is down so we chose bulk dried pasta.",
            },
            "minimal_prep": {
                "query": "microwave pasta ready meal",
                "fallback_name": "Tomato & Basil Pasta Ready Meal (400g)",
                "fallback_brand": "Tesco",
                "price_gbp": 2.25,
                "prep_mins": 3,
                "nova": 3,
                "reason": "Wheat bargain adapted for Burnout Week so we chose 3-minute microwave pasta.",
            },
        },
        "Surge": {
            "from_scratch": {
                "query": "white basmati rice",
                "fallback_name": "Basmati Rice (1kg)",
                "fallback_brand": "Aldi",
                "price_gbp": 1.45,
                "prep_mins": 15,
                "nova": 1,
                "reason": "Wheat surging so we swapped pasta for raw basmati rice.",
            },
            "minimal_prep": {
                "query": "microwave basmati rice pouch",
                "fallback_name": "Steamed Basmati Rice Pouch (250g)",
                "fallback_brand": "Tilda",
                "price_gbp": 1.10,
                "prep_mins": 2,
                "nova": 3,
                "reason": "Wheat surging and it is burnout week so we swapped to a 2-minute microwave rice pouch.",
            },
        },
    },
    "rice": {
        "Bargain": {
            "from_scratch": {
                "query": "long grain white rice",
                "fallback_name": "Long Grain White Rice (1kg)",
                "fallback_brand": "Sainsbury's",
                "price_gbp": 1.25,
                "prep_mins": 15,
                "nova": 1,
                "reason": "Rice prices dipped so we can buy dry long grain rice.",
            },
            "minimal_prep": {
                "query": "microwave egg fried rice",
                "fallback_name": "Microwave Egg Fried Rice Pouch (250g)",
                "fallback_brand": "Ben's Original",
                "price_gbp": 1.35,
                "prep_mins": 2,
                "nova": 3,
                "reason": "Rice bargain and burnout week so we swapped to ready-to-heat rice pouch.",
            },
        },
        "Surge": {
            "from_scratch": {
                "query": "baking potatoes",
                "fallback_name": "Maris Piper Potatoes (2kg)",
                "fallback_brand": "Tesco",
                "price_gbp": 1.60,
                "prep_mins": 25,
                "nova": 1,
                "reason": "Rice surging so we swapped to UK-grown potatoes for cheaper carbs.",
            },
            "minimal_prep": {
                "query": "microwave jacket potatoes",
                "fallback_name": "Ready Baked Jacket Potatoes (2 pack)",
                "fallback_brand": "McCain",
                "price_gbp": 2.00,
                "prep_mins": 5,
                "nova": 3,
                "reason": "Rice surging and a burnout week means we swapped to 5-minute microwave jacket potatoes.",
            },
        },
    },
    "corn": {
        "Bargain": {
            "from_scratch": {
                "query": "corn tortillas",
                "fallback_name": "Soft Corn Tortillas (8 pack)",
                "fallback_brand": "Old El Paso",
                "price_gbp": 1.50,
                "prep_mins": 10,
                "nova": 2,
                "reason": "Corn is cheap so we chose tortillas for weeknight tacos.",
            },
            "minimal_prep": {
                "query": "sweetcorn tin",
                "fallback_name": "Naturally Sweet Sweetcorn (325g)",
                "fallback_brand": "Green Giant",
                "price_gbp": 0.95,
                "prep_mins": 1,
                "nova": 1,
                "reason": "Corn bargain and burnout week so we switched to no-cook tinned sweetcorn adds instant veg to any meal.",
            },
        },
        "Surge": {
            "from_scratch": {
                "query": "plain flour",
                "fallback_name": "Plain White Flour (1.5kg)",
                "fallback_brand": "Aldi",
                "price_gbp": 0.85,
                "prep_mins": 15,
                "nova": 1,
                "reason": "Corn surging so we switched to wheat-based flatbreads instead of corn tortillas.",
            },
            "minimal_prep": {
                "query": "pitta bread",
                "fallback_name": "White Pitta Breads (6 pack)",
                "fallback_brand": "Tesco",
                "price_gbp": 0.65,
                "prep_mins": 1,
                "nova": 3,
                "reason": "Corn surging and a burnout week means we swithced to toaster-ready pitta breads.",
            },
        },
    },
    "oats": {
        "Bargain": {
            "from_scratch": {
                "query": "rolled porridge oats",
                "fallback_name": "Scottish Porridge Oats (1kg)",
                "fallback_brand": "Quaker",
                "price_gbp": 1.20,
                "prep_mins": 6,
                "nova": 1,
                "reason": "Oats are a bargain so raw rolled oats.",
            },
            "minimal_prep": {
                "query": "oat breakfast drink",
                "fallback_name": "Oat & Honey Breakfast Drink (330ml)",
                "fallback_brand": "Up&Go",
                "price_gbp": 1.65,
                "prep_mins": 0,
                "nova": 4,
                "reason": "Oats bargain and a burnout week means we switched to a grab-and-go oat drink.",
            },
        },
        "Surge": {
            "from_scratch": {
                "query": "cornflakes cereal",
                "fallback_name": "Classic Corn Flakes (500g)",
                "fallback_brand": "Kellogg's",
                "price_gbp": 1.80,
                "prep_mins": 1,
                "nova": 3,
                "reason": "Oats surging so we switched to corn cereal.",
            },
            "minimal_prep": {
                "query": "bananas",
                "fallback_name": "Loose Bananas (5 pack)",
                "fallback_brand": "Sainsbury's",
                "price_gbp": 0.95,
                "prep_mins": 0,
                "nova": 1,
                "reason": "Oats surging and a burnout week means we swapped to zero-prep fruit for breakfast.",
            },
        },
    },
    "beef": {
        "Bargain": {
            "from_scratch": {
                "query": "lean beef mince",
                "fallback_name": "5% Fat British Beef Mince (500g)",
                "fallback_brand": "Tesco",
                "price_gbp": 3.49,
                "prep_mins": 20,
                "nova": 1,
                "reason": "Beef prices dropped so we swapped to fresh beef mince.",
            },
            "minimal_prep": {
                "query": "beef lasagne ready meal",
                "fallback_name": "Classic Beef Lasagne (400g)",
                "fallback_brand": "Sainsbury's",
                "price_gbp": 2.75,
                "prep_mins": 4,
                "nova": 3,
                "reason": "Beef bargain and burnout week so we swapped to pre-made beef lasagne.",
            },
        },
        "Surge": {
            "from_scratch": {
                "query": "turkey breast mince",
                "fallback_name": "British Turkey Breast Mince (500g)",
                "fallback_brand": "Sainsbury's",
                "price_gbp": 2.65,
                "prep_mins": 18,
                "nova": 1,
                "reason": "Beef prices surging so we swapped to cheaper turkey mince for bolognese or chilli.",
            },
            "minimal_prep": {
                "query": "chicken pasta bake ready meal",
                "fallback_name": "Chicken & Bacon Pasta Bake (400g)",
                "fallback_brand": "Tesco",
                "price_gbp": 2.50,
                "prep_mins": 4,
                "nova": 3,
                "reason": "Beef prices surging and a burnout week so we swapped to a 4-minute microwave chicken pasta bake.",
            },
        },
    },
    "pork": {
        "Bargain": {
            "from_scratch": {
                "query": "pork loin steaks",
                "fallback_name": "British Pork Loin Steaks (480g)",
                "fallback_brand": "Aldi",
                "price_gbp": 2.89,
                "prep_mins": 15,
                "nova": 1,
                "reason": "Pork prices dropped so we chose fresh pork steaks.",
            },
            "minimal_prep": {
                "query": "pulled pork ready meal",
                "fallback_name": "Slow Cooked BBQ Pulled Pork (380g)",
                "fallback_brand": "Tesco",
                "price_gbp": 3.50,
                "prep_mins": 3,
                "nova": 3,
                "reason": "Pork bargain and burnout week so we swapped to pre-cooked pulled pork heats in 3 minutes.",
            },
        },
        "Surge": {
            "from_scratch": {
                "query": "chicken breast fillets",
                "fallback_name": "British Chicken Breast Fillets (600g)",
                "fallback_brand": "Aldi",
                "price_gbp": 3.69,
                "prep_mins": 18,
                "nova": 1,
                "reason": "Pork prices surging so we swapped pork steaks for versatile chicken breast fillets.",
            },
            "minimal_prep": {
                "query": "cooked chicken breast slices",
                "fallback_name": "Flamegrilled Chicken Breast Slices (180g)",
                "fallback_brand": "Tesco",
                "price_gbp": 2.25,
                "prep_mins": 0,
                "nova": 3,
                "reason": "Pork prices surging and a burnout week so we swapped to pre-cooked chicken slices.",
            },
        },
    },
    "soy": {
        "Bargain": {
            "from_scratch": {
                "query": "firm tofu",
                "fallback_name": "Organic Firm Tofu (280g)",
                "fallback_brand": "Cauldron",
                "price_gbp": 2.00,
                "prep_mins": 15,
                "nova": 2,
                "reason": "Soybeans down in price so plain tofu is an inexpensive protein base to marinate from scratch.",
            },
            "minimal_prep": {
                "query": "teriyaki tofu ready meal",
                "fallback_name": "Teriyaki Tofu & Noodle Bowl (380g)",
                "fallback_brand": "itso",
                "price_gbp": 3.25,
                "prep_mins": 3,
                "nova": 4,
                "reason": "Soy bargain and a burnout week means we switched to pre-cooked plant protein bowl.",
            },
        },
        "Surge": {
            "from_scratch": {
                "query": "free range eggs",
                "fallback_name": "Medium Free Range Eggs (6 pack)",
                "fallback_brand": "Tesco",
                "price_gbp": 1.65,
                "prep_mins": 8,
                "nova": 1,
                "reason": "Soy surging so we switched to eggs for protein.",
            },
            "minimal_prep": {
                "query": "egg mayo sandwich filler",
                "fallback_name": "Free Range Egg Mayonnaise Filler (250g)",
                "fallback_brand": "Sainsbury's",
                "price_gbp": 1.50,
                "prep_mins": 1,
                "nova": 3,
                "reason": "Soy surging and a buurnout week means we switched to pre-made egg filler.",
            },
        },
    },
    "dairy": {
        "Bargain": {
            "from_scratch": {
                "query": "mature cheddar cheese",
                "fallback_name": "British Mature Cheddar (350g)",
                "fallback_brand": "Cathedral City",
                "price_gbp": 2.75,
                "prep_mins": 2,
                "nova": 3,
                "reason": "Milk prices dipped so a block cheddar is great value for grating into homemade sauces.",
            },
            "minimal_prep": {
                "query": "grated cheddar cheese",
                "fallback_name": "Grated Mature Cheddar (250g)",
                "fallback_brand": "Tesco",
                "price_gbp": 2.25,
                "prep_mins": 0,
                "nova": 3,
                "reason": "Dairy bargain and a burnout Week means we swithced to pre-grated cheese which skips grating and washing up.",
            },
        },
        "Surge": {
            "from_scratch": {
                "query": "unsweetened soya milk",
                "fallback_name": "Unsweetened Soya Drink (1L)",
                "fallback_brand": "Alpro",
                "price_gbp": 1.35,
                "prep_mins": 0,
                "nova": 3,
                "reason": "Dairy surging so we swapped to shelf-stable plant milk.",
            },
            "minimal_prep": {
                "query": "unsweetened soya milk",
                "fallback_name": "Unsweetened Soya Drink (1L)",
                "fallback_brand": "Alpro",
                "price_gbp": 1.35,
                "prep_mins": 0,
                "nova": 3,
                "reason": "Dairy surging and a burnout week means long-life plant milk will prevent emergency shop runs.",
            },
        },
    },
    "coffee": {
        "Bargain": {
            "from_scratch": {
                "query": "roasted coffee beans",
                "fallback_name": "Medium Roast Whole Coffee Beans (227g)",
                "fallback_brand": "Taylor's of Harrogate",
                "price_gbp": 3.50,
                "prep_mins": 5,
                "nova": 1,
                "reason": "Coffee prices dipped so whole beans offer best flavour when you have relaxed mornings.",
            },
            "minimal_prep": {
                "query": "instant coffee granules",
                "fallback_name": "Rich Roast Instant Coffee (100g)",
                "fallback_brand": "Nescafé",
                "price_gbp": 2.75,
                "prep_mins": 1,
                "nova": 2,
                "reason": "Coffee bargain and a burnout week so we swithced to instant granules to save grinder cleanup.",
            },
        },
        "Surge": {
            "from_scratch": {
                "query": "english breakfast tea bags",
                "fallback_name": "Everyday Black Tea Bags (80 pack)",
                "fallback_brand": "Yorkshire Tea",
                "price_gbp": 2.80,
                "prep_mins": 3,
                "nova": 1,
                "reason": "Coffee surging so we swapped to black tea for affordable caffeine.",
            },
            "minimal_prep": {
                "query": "english breakfast tea bags",
                "fallback_name": "Everyday Black Tea Bags (80 pack)",
                "fallback_brand": "Yorkshire Tea",
                "price_gbp": 2.80,
                "prep_mins": 2,
                "nova": 1,
                "reason": "Coffee surging in price and a burnout week so we switched to quick-brew tea bags to avoid £4 coffee-shop impulse buys.",
            },
        },
    },
    "orange_juice": {
        "Bargain": {
            "from_scratch": {
                "query": "pure orange juice",
                "fallback_name": "100% Pure Squeezed Orange Juice (1L)",
                "fallback_brand": "Tropicana",
                "price_gbp": 2.00,
                "prep_mins": 0,
                "nova": 1,
                "reason": "Orange juice prices dropped so this is a great time to grab fresh juice for breakfast.",
            },
            "minimal_prep": {
                "query": "orange juice carton",
                "fallback_name": "Smooth Orange Juice Cartons (3x200ml)",
                "fallback_brand": "Tesco",
                "price_gbp": 1.40,
                "prep_mins": 0,
                "nova": 1,
                "reason": "Orange juice bargain and a burnout week means we switched to grab-and-go cartons for the mornings.",
            },
        },
        "Surge": {
            "from_scratch": {
                "query": "apple juice",
                "fallback_name": "Pressed British Apple Juice (1L)",
                "fallback_brand": "Copella",
                "price_gbp": 1.75,
                "prep_mins": 0,
                "nova": 1,
                "reason": "Orange juice surging in price so we switched to apple juice.",
            },
            "minimal_prep": {
                "query": "no added sugar squash",
                "fallback_name": "Double Strength Apple & Blackcurrant Squash (750ml)",
                "fallback_brand": "Robinsons",
                "price_gbp": 1.50,
                "prep_mins": 0,
                "nova": 4,
                "reason": "Orange juice surging and a burnout Week so squash will give 30+ drinks for £1.50.",
            },
        },
    },
    "cooking_oil": {
        "Bargain": {
            "from_scratch": {
                "query": "olive oil",
                "fallback_name": "Extra Virgin Olive Oil (500ml)",
                "fallback_brand": "Filippo Berio",
                "price_gbp": 4.25,
                "prep_mins": 0,
                "nova": 2,
                "reason": "Cooking oil dipped in price so we are stocking up on high quality oil for home roasting.",
            },
            "minimal_prep": {
                "query": "frylight spray",
                "fallback_name": "1 Cal Rapeseed Oil Cooking Spray (190ml)",
                "fallback_brand": "Frylight",
                "price_gbp": 2.00,
                "prep_mins": 0,
                "nova": 3,
                "reason": "Cooking oil decreasing in price and a burnout Week means we switched to mess-free spray oil that speeds up quick pan heating.",
            },
        },
        "Surge": {
            "from_scratch": {
                "query": "sunflower oil",
                "fallback_name": "British Sunflower Oil (1L)",
                "fallback_brand": "Aldi",
                "price_gbp": 1.85,
                "prep_mins": 0,
                "nova": 2,
                "reason": "Soybean oil surging in price means we switched to budget sunflower oil.",
            },
            "minimal_prep": {
                "query": "steamed vegetable medley",
                "fallback_name": "Microwave Steam Veg Bags (4 pack)",
                "fallback_brand": "Birds Eye",
                "price_gbp": 2.20,
                "prep_mins": 3,
                "nova": 1,
                "reason": "Oil surging in price and a burnout week means we can have a steam-bag of veggies that need zero oil or frying pans.",
            },
        },
    },
    "sugar": {
        "Bargain": {
            "from_scratch": {
                "query": "caster sugar",
                "fallback_name": "White Caster Sugar (1kg)",
                "fallback_brand": "Silver Spoon",
                "price_gbp": 1.15,
                "prep_mins": 10,
                "nova": 2,
                "reason": "Sugar down means we can ideally do some weekend baking during Calm Week.",
            },
            "minimal_prep": {
                "query": "flapjack bites",
                "fallback_name": "Oat Flapjack Bites Tub (20 pack)",
                "fallback_brand": "Tesco",
                "price_gbp": 2.00,
                "prep_mins": 0,
                "nova": 4,
                "reason": "Sugar decreasing in price and a burnout week means we swap to ready-made snacks instead of baking.",
            },
        },
        "Surge": {
            "from_scratch": {
                "query": "clear honey",
                "fallback_name": "Pure Clear Honey (340g)",
                "fallback_brand": "Rowse",
                "price_gbp": 2.10,
                "prep_mins": 0,
                "nova": 1,
                "reason": "Sugar increasing in price means we swapped to natural honey.",
            },
            "minimal_prep": {
                "query": "sweet clemetines",
                "fallback_name": "Easy Peeler Clementines (600g)",
                "fallback_brand": "Sainsbury's",
                "price_gbp": 1.35,
                "prep_mins": 0,
                "nova": 1,
                "reason": "Sugar increasing in price + a burnout week means we switch to naturally sweet fruit with zero prep.",
            },
        },
    },
    "cocoa": {
        "Bargain": {
            "from_scratch": {
                "query": "cocoa powder",
                "fallback_name": "100% Cocoa Baking Powder (250g)",
                "fallback_brand": "Green & Black's",
                "price_gbp": 2.50,
                "prep_mins": 5,
                "nova": 1,
                "reason": "Cocoa prices droppeing means this is great for homemade hot chocolate or brownies.",
            },
            "minimal_prep": {
                "query": "dark chocolate bar",
                "fallback_name": "70% Dark Chocolate Bar (100g)",
                "fallback_brand": "Lindt",
                "price_gbp": 2.20,
                "prep_mins": 0,
                "nova": 3,
                "reason": "Cocoa decreasing in price +  a burnout week means we have ready-to-eat stress-relief chocolate.",
            },
        },
        "Surge": {
            "from_scratch": {
                "query": "cinnamon powder",
                "fallback_name": "Ground Cinnamon (40g)",
                "fallback_brand": "Schwartz",
                "price_gbp": 1.25,
                "prep_mins": 1,
                "nova": 1,
                "reason": "Cocoa increasing in price means we swapped to spiced cinnamon oats/bakes.",
            },
            "minimal_prep": {
                "query": "digestive biscuits",
                "fallback_name": "Original Digestive Biscuits (400g)",
                "fallback_brand": "McVitie's",
                "price_gbp": 1.30,
                "prep_mins": 0,
                "nova": 4,
                "reason": "Cocoa price with a burnout week means we swap to plain biscuits to avoid the inflated chocolate prices.",
            },
        },
    },
}

# Core staples included so a weekly basket is always complete even if markets are 'Stable'
CORE_WEEKLY_STAPLES = {"wheat", "beef", "dairy", "coffee"}


def search_open_food_facts(query: str, timeout: float = 3.5) -> dict | None:
    """Queries Open Food Facts UK for a matching supermarket product."""
    params = {
        "search_terms": query,
        "search_simple": 1,
        "action": "process",
        "json": 1,
        "page_size": 3,
        "fields": "product_name,brands,nova_group,nutriscore_grade,quantity",
    }
    try:
        response = requests.get(OPEN_FOOD_FACTS_URL, params=params, headers=HEADERS, timeout=timeout)
        response.raise_for_status()
        products = response.json().get("products", [])
        for item in products:
            name = item.get("product_name", "").strip()
            if name:
                qty = item.get("quantity", "")
                display_name = f"{name} ({qty})" if qty and qty not in name else name
                return {
                    "product_name": display_name,
                    "brand": item.get("brands", "UK Supermarket").split(",")[0].strip(),
                    "nova_group": item.get("nova_group"),
                    "nutriscore": str(item.get("nutriscore_grade", "n/a")).upper(),
                }
    except requests.RequestException:
        return None
    return None


def build_shopping_cart(commodity_analysis: list, meal_prep_mode: str = "from_scratch", use_live_api: bool = True) -> dict:
    """Builds an optimised UK grocery basket from Commodity-analyser.py results and the calendar"""
    cart_items = []
    total_cost = 0.0
    total_prep_mins = 0
    api_reachable = use_live_api

    effective_mode = "minimal_prep" if meal_prep_mode == "minimal_prep" else "from_scratch"

    for entry in commodity_analysis:
        commodity_key = entry.get("item_name", "").lower()
        market_status = entry.get("market_status", "Stable")
        pct_change = entry.get("discount_percent", 0.0)

        if commodity_key not in GROCERY_SWAP_MATRIX:
            continue

        if market_status == "Stable" and commodity_key not in CORE_WEEKLY_STAPLES:
            continue

        trend_bucket = "Surge" if market_status == "Surge" else "Bargain"
        selected = GROCERY_SWAP_MATRIX[commodity_key][trend_bucket][effective_mode]

        live_product = search_open_food_facts(selected["query"]) if api_reachable else None
        if api_reachable and live_product is None:
            api_reachable = False

        item_name = live_product["product_name"] if live_product else selected["fallback_name"]
        brand = live_product["brand"] if live_product else selected["fallback_brand"]
        nova_group = (live_product.get("nova_group") if live_product else None) or selected["nova"]
        nutriscore = live_product["nutriscore"] if live_product else "B"

        total_cost += selected["price_gbp"]
        total_prep_mins += selected["prep_mins"]

        price_note = f" ({pct_change}% move)" if market_status != "Stable" else ""
        cart_items.append({
            "commodity": commodity_key,
            "market_status": f"{market_status}{price_note}",
            "item_name": item_name,
            "brand": brand,
            "estimated_price_gbp": round(selected["price_gbp"], 2),
            "prep_time_mins": selected["prep_mins"],
            "nova_processing_group": nova_group,
            "nutriscore": nutriscore,
            "swap_reason": selected["reason"],
            "source": "Open Food Facts UK (Live)" if live_product else "Local UK Catalogue",
        })

    return {
        "meal_prep_mode": meal_prep_mode,
        "summary": {
            "total_items": len(cart_items),
            "estimated_total_gbp": round(total_cost, 2),
            "total_weekly_prep_mins": total_prep_mins,
        },
        "basket": cart_items,
    }


if __name__ == "__main__":
    sample_analysis = [
        {"item_name": "wheat", "market_status": "Bargain", "discount_percent": 6.4, "current_trading_price": 540.0},
        {"item_name": "beef", "market_status": "Stable", "discount_percent": 1.2, "current_trading_price": 185.0},
        {"item_name": "dairy", "market_status": "Stable", "discount_percent": 0.8, "current_trading_price": 19.5},
        {"item_name": "coffee", "market_status": "Surge", "discount_percent": 8.1, "current_trading_price": 265.0},
    ]

    for mode in ["from_scratch", "minimal_prep"]:
        print(f"\n=== Shopping Cart ({mode}) ===")
        print(json.dumps(build_shopping_cart(sample_analysis, meal_prep_mode=mode), indent=2, ensure_ascii=False))