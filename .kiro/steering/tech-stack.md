# Technical Architecture & Rules
- Core backend lives in `my_apps/market-to-table/main/`.
- Modules with hyphens (`Commodity-analyser.py`, `Shopping-planner.py`) MUST be imported using `importlib.import_module()`, never standard `import` statements.
- `main.py` exposes `run_market_to_table(calendar_name: str) -> dict` as the single entry point for the UI.
- Web interface must be built in **Streamlit** (`my_apps/market-to-table/main/app.py`) using UK currency (`£` / GBP) and UK supermarket terminology.
- Never hardcode API keys; always rely on `.env` via `python-dotenv`.

