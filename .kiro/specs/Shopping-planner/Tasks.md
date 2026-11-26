**Implementation Plan: Shopping-Cart**


1. Set up project structure and core components

Create Main/Market-To-Table/Shopping-cart/ directory structure.

Initialize Grocery API Client (e.g., Instacart/Kroger SDK).

Create mock data for Commodity API and Calendar API inputs.

Requirements: 4.1



2. Implement Ingredient Mapper

Create IngredientMap dictionary for top 10 standard commodities.

Implement get_skus(base_ingredient) method.

Add fallback logic for missing convenience mappings.

Requirements: 1.1, 1.2

[ ] * 2.1 Write property test for mapping retrieval

Property 3: Every valid base ingredient returns a valid SKU.

Validates: Requirements 1.1



3. Implement Cart Logic (The Chimera Swap)

Create CartOrchestrator class.

Implement build_cart(base_ingredients, is_burnout_week) method.

Implement logic to select raw vs. convenience based on the flag.

Requirements: 2.1, 2.2, 3.1, 3.2

[ ] * 3.1 Write property test for Burnout Swap

Property 1: True burnout flag forces convenience SKUs.

Validates: Requirements 3.1, 3.2

[ ] * 3.2 Write property test for Healthy Week Raw Logic

Property 2: False burnout flag forces raw SKUs.

Validates: Requirements 2.1, 2.2



4. Integrate Grocery API Checkout

Implement push_to_grocery_api(final_cart) method.

Implement error handling for out-of-stock items (fallback to alternative SKU).

Return totalEstimatedCost and UI summary message.

Requirements: 4.1, 4.2

[ ] * 4.1 Write unit tests for API Client

Test successful cart push.

Test out-of-stock fallback handling.



5. Implement Kiro Hooks for Mid-Week Updates

Define Kiro hook onCalendarUpdate.

Connect hook to build_cart() to trigger an API overwrite if the burnout state changes.

Requirements: 5.1, 5.2

[ ] * 5.1 Write integration test for Kiro Hook trigger.

Property 4: Calendar state change triggers cart rebuild.

Validates: Requirements 5.1, 5.2