# Design Document: Calendar & Burnout Workload Analyser (`Calendar.py`)

## Overview

**Calendar & Burnout Workload Analyser (`Calendar.py`)** is the schedule-intelligence and stress-detection engine for **Market-to-Table**. Rather than relying on manual user self-reporting, the module objectively measures weekly cognitive and time load by correlating two real-world data streams: upcoming **Google Calendar** commitments and recent **Discord** work-chat urgency signals.

By quantifying total meeting hours, late-evening schedule encroachment (meetings ending at or after `18:00`), and urgency keyword density across both schedules and team chat, `Calendar.py` classifies the user's upcoming week into one of three stress regimes—**Relaxing**, **Moderate**, or **Burnout**—and outputs a deterministic `meal_prep_mode` (`from_scratch`, `balanced_prep`, or `minimal_prep`) that dynamically reshapes the downstream UK grocery basket and recipe recommendations.

---

## Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                   Calendar & Burnout Workload Analyser                      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│                      ┌───────────────────────────────┐                      │
│                      │      run_burnout_check()      │                      │
│                      │    (Entry Point & Env Loader) │                      │
│                      └───────┬───────────────┬───────┘                      │
│                              │               │                              │
│              ┌───────────────▼───┐       ┌───▼────────────────┐             │
│              │  fetch_google_    │       │  fetch_discord_    │             │
│              │  calendar_events()│       │  chat_messages()   │             │
│              └─────────┬─────────┘       └─────────┬──────────┘             │
│                        │ (Fallback on              │                        │
│                        │  missing key/error)       │                        │
│                        ▼                           │                        │
│              ┌───────────────────┐                 │                        │
│              │  _get_sample_     │                 │                        │
│              │  calendar_events()│                 │                        │
│              └─────────┬─────────┘                 │                        │
│                        │                           │                        │
│                        └─────────────┬─────────────┘                        │
│                                      ▼                                      │
│                      ┌───────────────────────────────┐                      │
│                      │       analyse_burnout()       │                      │
│                      │  • Duration & Evening Scanner │                      │
│                      │  • Keyword Urgency Matcher    │                      │
│                      │  • Threshold Classifier       │                      │
│                      └───────────────┬───────────────┘                      │
│                                      │                                      │
└──────────────────────────────────────┼──────────────────────────────────────┘
                                       ▼
                     ┌───────────────────────────────────┐
                     │    Structured Burnout Report      │
                     │  (stress_status, meal_prep_mode,  │
                     │   metrics, flagged_triggers)      │
                     └───────────────────────────────────┘
```

### Component Responsibilities

1. **Configuration & Preset Registry (`DEMO_CALENDARS`, `BURNOUT_KEYWORDS`)**: Maps human-readable calendar modes (`"Demo - Burnout Week"`, `"Demo - Calm Week"`) to environment variable keys and defines the 15-term urgency lexicon scanned across calendar events and work messages.
2. **Google Calendar Ingestion (`fetch_google_calendar_events`)**: Queries the Google Calendar REST API v3 over a rolling 7-day UTC window (`singleEvents=true`, `orderBy=startTime`), automatically falling back to offline sample events when API keys or network access are unavailable.
3. **Discord Work-Chat Ingestion (`fetch_discord_chat_messages`)**: Queries the Discord REST API v10 (`/channels/{channel_id}/messages`) using a read-only Bot Token to detect real-time workplace crunch signals outside formal calendar invites.
4. **Offline Resilience Provider (`_get_sample_calendar_events`)**: Generates deterministic, timezone-aware UTC events anchored to the current day (`09:00 UTC`) so demos and automated tests run reliably offline.
5. **Burnout & Prep-Mode Classifier (`analyse_burnout`)**: Computes meeting duration totals, counts evening disruptions (`hour >= 18`), extracts matched urgency triggers, and maps the combined workload metrics to `stress_status` and `meal_prep_mode`.
6. **Module Orchestrator (`run_burnout_check`)**: Loads `.env` secrets via `python-dotenv`, resolves target calendar and Discord channel IDs, executes both ingestion pipelines, and returns the unified JSON-serializable report.

---

## Components and Interfaces

### Enumerations and Data Models

```python
from dataclasses import dataclass, field
from enum import Enum
from typing import Literal, Optional

class StressStatus(Enum):
    RELAXING = "Relaxing"
    MODERATE = "Moderate"
    BURNOUT = "Burnout"

class MealPrepMode(Enum):
    FROM_SCRATCH = "from_scratch"     # Relaxing schedule -> full home cooking
    BALANCED_PREP = "balanced_prep"   # Moderate schedule -> mixed prep
    MINIMAL_PREP = "minimal_prep"     # Burnout schedule  -> <= 5 min convenience/no-cook

@dataclass
class CalendarEvent:
    summary: str
    description: str
    start_iso: str
    end_iso: str

@dataclass
class ChatMessage:
    author: str
    content: str
    timestamp: str

@dataclass
class FlaggedTrigger:
    source: Literal["calendar", "work_chat"]
    text: str
    keywords: list[str]
    author: Optional[str] = None

@dataclass
class BurnoutMetrics:
    total_meeting_hours: float
    late_evening_meetings: int
    calendar_keyword_hits: int
    chat_keyword_hits: int
    total_events_analysed: int
    total_messages_analysed: int

@dataclass
class BurnoutReport:
    selected_calendar: str
    stress_status: str
    meal_prep_mode: str
    metrics: BurnoutMetrics
    flagged_triggers: list[FlaggedTrigger] = field(default_factory=list)
```

### Core Module Interfaces (`Calendar.py`)

```python
def fetch_google_calendar_events(
    calendar_name: str,
    api_key: str,
    days_ahead: int = 7,
) -> list[dict]:
    """
    Fetches expanded single events for the next `days_ahead` days from Google
    Calendar API v3. Raises ValueError if `calendar_name` is not in DEMO_CALENDARS.
    Falls back to _get_sample_calendar_events() on missing credentials or HTTP error.
    """

def fetch_discord_chat_messages(
    channel_id: str,
    bot_token: str,
    limit: int = 50,
) -> list[dict]:
    """
    Fetches up to `limit` recent messages from a Discord channel using a Bot Token.
    Filters out empty messages and returns [] on missing credentials or HTTP error.
    """

def _get_sample_calendar_events(calendar_name: str) -> list[dict]:
    """
    Returns deterministic UTC sample calendar events for 'Demo - Calm Week'
    or 'Demo - Burnout Week' anchored to today at 09:00 UTC.
    """

def analyse_burnout(
    calendar_name: str,
    calendar_events: list[dict],
    chat_messages: list[dict],
) -> dict:
    """
    Aggregates meeting hours, evening disruptions, and urgency keyword hits across
    calendar events and chat messages to classify stress_status and meal_prep_mode.
    """

def run_burnout_check(calendar_name: str = "Demo - Burnout Week") -> dict:
    """
    Loads environment variables via dotenv and executes the end-to-end burnout
    analysis pipeline for the selected calendar preset.
    """
```

---

## Data Models

### 1. Calendar Preset Registry (`DEMO_CALENDARS`)
```python
DEMO_CALENDARS: dict[str, dict[str, str]] = {
    "Demo - Burnout Week": {
        "calendar_id_env": "BURNOUT_CALENDAR_ID",
        "discord_channel_env": "BURNOUT_DISCORD_CHANNEL_ID",
    },
    "Demo - Calm Week": {
        "calendar_id_env": "CALM_CALENDAR_ID",
        "discord_channel_env": "CALM_DISCORD_CHANNEL_ID",
    },
}
```

### 2. Urgency & Burnout Lexicon (`BURNOUT_KEYWORDS`)
15 lowercase trigger tokens scanned case-insensitively across `event.summary + " " + event.description` and `msg.content`:
```python
BURNOUT_KEYWORDS: list[str] = [
    "urgent", "asap", "deadline", "emergency", "critical",
    "overtime", "crunch", "escalation", "crisis", "late",
    "review", "hotfix", "blocker", "broken", "tonight",
]
```

### 3. Stress & Meal-Prep Classification Matrix

| Priority | Condition (`OR` logic) | `stress_status` | `meal_prep_mode` |
| :--- | :--- | :--- | :--- |
| **1 (Highest)** | `total_meeting_hours >= 20.0` **OR** `total_keyword_hits >= 5` **OR** `late_evening_meetings >= 3` | `"Burnout"` | `"minimal_prep"` |
| **2** | `total_meeting_hours >= 10.0` **OR** `total_keyword_hits >= 2` | `"Moderate"` | `"balanced_prep"` |
| **3 (Default)** | Otherwise (`hours < 10.0`, `hits < 2`, `evening_meetings < 3`) | `"Relaxing"` | `"from_scratch"` |

### 4. Output JSON Contract (`analyse_burnout` Return Schema)
```json
{
  "selected_calendar": "Demo - Burnout Week",
  "stress_status": "Burnout",
  "meal_prep_mode": "minimal_prep",
  "metrics": {
    "total_meeting_hours": 6.5,
    "late_evening_meetings": 1,
    "calendar_keyword_hits": 8,
    "chat_keyword_hits": 0,
    "total_events_analysed": 2,
    "total_messages_analysed": 0
  },
  "flagged_triggers": [
    {
      "source": "calendar",
      "text": "URGENT: Q4 Production Sprint Planning",
      "keywords": ["urgent", "deadline", "critical", "review"]
    },
    {
      "source": "calendar",
      "text": "Client Escalation & Hotfix Sync",
      "keywords": ["asap", "escalation", "hotfix", "tonight"]
    }
  ]
}
```

---

## Correctness Properties

A property is a formal invariant that must hold true across all valid executions of `Calendar.py`, connecting product intent to machine-verifiable guarantees.

* **Property 1: Unknown calendar validation**
  For any `calendar_name` string not present in `DEMO_CALENDARS`, `fetch_google_calendar_events` must raise a `ValueError` listing the supported calendar keys.
  *Validates: Requirements 1.1*

* **Property 2: Offline fallback determinism for demo presets**
  When `api_key` or `calendar_id` is empty (or the Google Calendar HTTP request raises `RequestException`), `fetch_google_calendar_events("Demo - Calm Week", ...)` must return events that classify as `"Relaxing"` (`"from_scratch"`), and `fetch_google_calendar_events("Demo - Burnout Week", ...)` must return events that classify as `"Burnout"` (`"minimal_prep"`).
  *Validates: Requirements 1.2, 6.1*

* **Property 3: Rolling 7-day UTC query window**
  For any valid live Google Calendar request with default `days_ahead=7`, `timeMax - timeMin` must equal exactly `datetime.timedelta(days=7)` in UTC ISO-8601 format, with `singleEvents="true"` and `orderBy="startTime"`.
  *Validates: Requirements 1.3*

* **Property 4: Empty-content Discord message filtering**
  For any list of Discord API message objects returned by `fetch_discord_chat_messages`, every output dictionary must have a non-empty `"content"` string, and any message with missing or empty `"content"` must be excluded.
  *Validates: Requirements 2.2*

* **Property 5: All-day event safe skipping**
  For any calendar event missing either `start.dateTime` or `end.dateTime` (such as all-day `date`-only events), `analyse_burnout` must skip the event without raising `KeyError` or `ValueError`, while still recording `total_events_analysed == len(calendar_events)`.
  *Validates: Requirements 3.1, 6.2*

* **Property 6: Exact meeting duration accumulation and rounding**
  For any list of timed events, `metrics["total_meeting_hours"]` must equal $\text{round}\left(\sum \frac{\text{end\_dt}_i - \text{start\_dt}_i}{3600}, 2\right)$.
  *Validates: Requirements 3.2*

* **Property 7: Late-evening cooking disruption boundary (`18:00`)**
  For any timed calendar event, `late_evening_meetings` must increment if and only if `end_dt.hour >= 18` (e.g.,an event ending at `17:59` increments by `0`, whereas an event ending at `18:00` or `19:30` increments by `1`).
  *Validates: Requirements 3.3*

* **Property 8: Case-insensitive urgency keyword matching**
  For any calendar event (`summary` + `description`) or Discord message (`content`), keyword matching against `BURNOUT_KEYWORDS` must be case-insensitive, and `calendar_keyword_hits + chat_keyword_hits` must equal the sum of `len(trigger["keywords"])` across all entries in `flagged_triggers`.
  *Validates: Requirements 3.4, 3.5*

* **Property 9: Burnout classification precedence**
  Whenever `total_meeting_hours >= 20.0` OR `total_keyword_hits >= 5` OR `late_evening_meetings >= 3`, `analyse_burnout` must return `stress_status == "Burnout"` and `meal_prep_mode == "minimal_prep"`, regardless of whether moderate thresholds are also met.
  *Validates: Requirements 4.1*

* **Property 10: Moderate classification boundary**
  Whenever the Burnout condition is False AND (`total_meeting_hours >= 10.0` OR `total_keyword_hits >= 2`), `analyse_burnout` must return `stress_status == "Moderate"` and `meal_prep_mode == "balanced_prep"`.
  *Validates: Requirements 4.2*

* **Property 11: Relaxing default classification**
  Whenever `total_meeting_hours < 10.0` AND `total_keyword_hits < 2` AND `late_evening_meetings < 3`, `analyse_burnout` must return `stress_status == "Relaxing"` and `meal_prep_mode == "from_scratch"`.
  *Validates: Requirements 4.3*

* **Property 12: Stress-status to meal-prep-mode bijection**
  Across all outputs of `analyse_burnout`, the pair `(stress_status, meal_prep_mode)` must strictly belong to `{("Burnout", "minimal_prep"), ("Moderate", "balanced_prep"), ("Relaxing", "from_scratch")}`.
  *Validates: Requirements 4.4*

---

## Error Handling

### External API & Credential Failures
* **Missing Environment Secrets (`GOOGLE_CALENDAR_API_KEY`, `CALM_CALENDAR_ID`, `BURNOUT_CALENDAR_ID`)**: Detected prior to network dispatch; logs an informational message and seamlessly returns `_get_sample_calendar_events(calendar_name)` so the app works out-of-the-box for hackathon judges with zero `.env` configuration.
* **Google Calendar HTTP / Timeout Errors**: All requests enforce `timeout=10` and call `response.raise_for_status()`. Any `requests.RequestException` is caught and downgraded gracefully to `_get_sample_calendar_events(calendar_name)`.
* **Discord Bot Token / Channel Failures**: If `DISCORD_BOT_TOKEN` or the channel ID is unset, or if Discord returns `401`/`403`/`429`/timeout, `fetch_discord_chat_messages` returns `[]` so calendar analysis proceeds uninterrupted.

### Input & Timestamp Parsing Guards
* **Invalid Calendar Preset Name**: `fetch_google_calendar_events` raises an explicit `ValueError` for unrecognized calendar names, while `run_burnout_check` safely defaults unknown preset lookups in `DEMO_CALENDARS` to `"Demo - Burnout Week"`.
* **UTC `"Z"` Suffix Normalization**: ISO timestamps ending in `"Z"` are normalized via `.replace("Z", "+00:00")` prior to `datetime.datetime.fromisoformat()` to ensure compatibility across Python 3.10+ runtimes.
* **All-Day Events**: Events lacking `start.dateTime` or `end.dateTime` are skipped safely without crashing duration arithmetic.

---

## Testing Strategy

### Unit Testing (`pytest` / `unittest`)
1. **Preset & Offline Fallback Tests**:
   * Verify `run_burnout_check("Demo - Calm Week")` returns `stress_status == "Relaxing"` and `meal_prep_mode == "from_scratch"` when no `.env` keys are set.
   * Verify `run_burnout_check("Demo - Burnout Week")` returns `stress_status == "Burnout"` and `meal_prep_mode == "minimal_prep"` when no `.env` keys are set.
   * Verify `fetch_google_calendar_events("Invalid Name", "key")` raises `ValueError`.
2. **Threshold Boundary Tests (`analyse_burnout`)**:
   * Test exact boundaries: `9.99h` vs `10.0h` (`Moderate`), `19.99h` vs `20.0h` (`Burnout`), `1` vs `2` vs `5` keyword hits, and `2` vs `3` late-evening meetings ending at `17:59` vs `18:00`.
3. **Mocked API Resilience Tests**:
   * Mock `requests.get` to simulate `requests.Timeout` and HTTP `500` responses for both Google Calendar and Discord APIs and verify graceful degradation.

### Property-Based Testing (`hypothesis`)
Property-based tests run a minimum of **100 iterations** per property using Python's `hypothesis` library, tagged with `# Feature: calendar-burnout-analyser, Property {N}: {property_text}`:
* **Duration & Evening Boundary Properties (Properties 5–7)**: Generate random lists of timed and all-day events across 24 hours; verify exact hour sums and `end_dt.hour >= 18` counting.
* **Keyword Scanner Properties (Properties 4, 8)**: Generate random mixed-case strings with injected `BURNOUT_KEYWORDS` across calendar descriptions and Discord messages; verify exact trigger counts and author attribution.
* **Classification Partition Properties (Properties 9–12)**: Generate arbitrary `(hours, keyword_hits, late_evening_meetings)` tuples and verify mutually exclusive, exhaustive mapping into the three `(stress_status, meal_prep_mode)` pairs.

### Integration & Manual Verification
* **Downstream Pipeline Integration (`main.py` -> `Shopping-planner.py`)**: Confirm `meal_prep_mode` values produced by `Calendar.py` map cleanly into `Shopping-planner.py` (`minimal_prep` activates convenience swaps; `from_scratch` and `balanced_prep` activate home-cooking staples).
* **Live Credential Smoke Test**: Populate `.env` with valid Google Calendar API and Discord Bot credentials and confirm `flagged_triggers` captures real-time events and chat messages.

---

## Implementation Notes

### Multi-Signal Burnout Detection
Traditional calendar tools only count meeting hours, missing the stress of last-minute crunch messages or late-night releases. Combining quantitative hours (`>= 20.0h`), evening cooking-window collisions (`end_dt.hour >= 18`), and qualitative urgency keywords (`urgent`, `hotfix`, `escalation`, `tonight`) across both Calendar and Discord provides high-precision burnout detection even on weeks with fewer, high-stakes meetings.

### Downstream Compatibility with `Shopping-planner.py`
`analyse_burnout` distinguishes three granular states (`from_scratch`, `balanced_prep`, `minimal_prep`), while `Shopping-planner.py` normalizes non-`minimal_prep` modes to `"from_scratch"` so the UI and grocery swap matrix remain cleanly two-state (`Calm` vs `Burnout`) while preserving `Moderate` telemetry in `metrics` and status badges.

### Zero-Configuration Demo Readiness
Because `_get_sample_calendar_events` anchors event timestamps dynamically to `datetime.datetime.now(datetime.timezone.utc)`, sample events never expire or appear in the past regardless of when a judge runs the application.

---

## File Structure

```text
Market-to-Table/
├── .kiro/
│   └── specs/
│       ├── calendar-burnout-analyser/
│       │   └── design.md               # This design specification
│       └── market-to-table/
│           └── design.md               # Full-stack system & storefront specification
├── Main/
│   ├── Calendar.py                     # Schedule & Discord burnout workload analyser
│   ├── Commodity-analyser.py           # Yahoo Finance agricultural futures analyser
│   ├── Shopping-planner.py             # UK grocery swap matrix & Open Food Facts resolver
│   ├── main.py                         # 3-stage pipeline orchestrator
│   └── app.py                          # Streamlit consumer storefront UI
├── .env.example                        # Template for GOOGLE_CALENDAR_API_KEY & DISCORD_BOT_TOKEN
└── requirements.txt                    # streamlit, yfinance, requests, python-dotenv
```