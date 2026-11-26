**Requirements Document**

**Introduction**

The Shopping Cart is the core of the chimera, acting as the bridge between the financial market data, the user schedule analysis, and the groceries. The application takes recommended cheap base ingredients (using the commodity analyser to see which goods are cheaper than usual) and a burnout indicator (from the calendar, where based on the user's daily schedule, items will be chosen based on how much effort is required to prepare them) to automatically construct a shopping cart via a Grocery API. It dyanmically swaps between raw and labour intensive ingredients and more convenient alternatives based on the user's anticipated stress levels for the upcoming week.


**Glossary**

**Shopping Cart System:** The module responsible for compiling and pushing the final grocery order.

**Base Ingredients:** The raw agricultural staples identified as cost-effective by the Commodity API.

**Raw Mapping:** The whole, unprocessed, cheapest SKU form of a Base Ingredient (e.g., dry rice, whole raw chicken).

**Convenience Mapping:** The pre-processed, easy-to-cook SKU form of a Base Ingredient (e.g., microwave rice pouches, frozen precooked chicken strips).

**Burnout Flag:** A boolean value provided by the Calendar/Chat API indicating a high-stress week.

**Final Cart:** The ultimate list of Grocery API Product IDs (SKUs) and estimated totals to be purchased.

**Kiro Hook:** An automated trigger in the Kiro framework used to rebuild the cart if schedule parameters change.


**Requirements**


**Requirement 1**
**User Story:** As a user, I want the system to switch between choosing to add raw ingredients and convenient processed ingredients to the shopping cart in order for meals to be created and adapted based on my energy levels.

**Acceptance Criteria:**
1. WHEN given a Base Ingredient, THEN the Cart Orchestrator System SHALL retrieve both a rawProductId and a convenienceProductId from the mapping dictionary.
2. IF a Base Ingredient lacks a convenience mapping, THEN the Cart Orchestrator System SHALL default to the raw mapping.


**Requirement 2**
**User Story:**  As a user, if I have a relaxing week ahead I would want the system to buy raw ingredients so that I am able to cook more complex meals that will save me money

**Acceptance Criteria:**
1. WHEN the Burnout Flag evaluates to false, THEN the Cart Orchestrator System SHALL populate the cart using only the rawProductId for all Base Ingredients.
2. WHEN the Raw Mapping is used, THEN the Cart Orchestrator System SHALL append supporting foundational items (e.g., spices, cooking oil) to the Final Cart.


**Requirement 3**
**User Story:** As a user with a high-stress week ahead, I want the system to automatically swap to convenient ingredients, so that I can actually eat the food I buy without burning out.

**Acceptance Criteria:**
1. WHEN the Burnout Flag evaluates to true, THEN the Cart Orchestrator System SHALL populate the cart using only the convenienceProductId for all Base Ingredients.
2. WHEN the swap occurs, THEN the Cart Orchestrator System SHALL flag the Final Cart with burnoutAdjustmentApplied = true.


**Requirement 4**
**User Story:** As a user, I want the system to automatically push my customised list to my grocery delivery account so that I can check out easily.

**Acceptance Criteria:**
1. WHEN the Final Cart is compiled, THEN the Cart Orchestrator System SHALL transmit the list of Product IDs to the connected Grocery API.
2. WHEN the Grocery API responds, THEN the Cart Orchestrator System SHALL display the final estimated total cost and a summary message explaining any burnout adjustments.


**Requirement 5**
**User Story:** As a user whose schedule changes frequently during the week, I want the system to automatically update my pending grocery cart if sudden meetings are scheduled in my day so that I won't be caught off guard by prepping something more complex.

**Acceptance Criteria:**
1. WHEN the Calendar API detects a mid-week schedule change that flips the Burnout Flag to true, THEN a Kiro Hook SHALL trigger the Cart Orchestrator System to rebuild the cart.
2. WHEN a mid-week rebuild occurs, THEN the Cart Orchestrator System SHALL replace pending raw items with convenience items via the Grocery API.