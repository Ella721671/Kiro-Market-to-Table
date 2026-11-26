import datetime
import json
import os
from dotenv import load_dotenv
import requests

load_dotenv()

# Maps your exact Google Calendar display names to their environment variable keys
DEMO_CALENDARS = {
    "Demo - Burnout Week": {
        "calendar_id_env": "BURNOUT_CALENDAR_ID",
        "discord_channel_env": "BURNOUT_DISCORD_CHANNEL_ID",
    },
    "Demo - Calm Week": {
        "calendar_id_env": "CALM_CALENDAR_ID",
        "discord_channel_env": "CALM_DISCORD_CHANNEL_ID",
    },
}

# Stress and urgency indicators scanned across both calendar events and work chat
BURNOUT_KEYWORDS = [
    "urgent", "asap", "deadline", "emergency", "critical",
    "overtime", "crunch", "escalation", "crisis", "late",
    "review", "hotfix", "blocker", "broken", "tonight"
]


def fetch_google_calendar_events(calendar_name: str, api_key: str, days_ahead: int = 7) -> list:
    """Fetches upcoming events from 'Demo - Burnout Week' or 'Demo - Calm Week'."""
    config = DEMO_CALENDARS.get(calendar_name)
    if not config:
        raise ValueError(f"Unknown calendar '{calendar_name}'. Choose from: {list(DEMO_CALENDARS.keys())}")

    calendar_id = os.getenv(config["calendar_id_env"], "")

    if not calendar_id or not api_key:
        print(f"Info: Missing API key or Calendar ID for '{calendar_name}'. Using sample data.")
        return _get_sample_calendar_events(calendar_name)

    now = datetime.datetime.now(datetime.timezone.utc)
    end_of_week = now + datetime.timedelta(days=days_ahead)

    url = f"https://www.googleapis.com/calendar/v3/calendars/{calendar_id}/events"
    params = {
        "key": api_key,
        "timeMin": now.isoformat(),
        "timeMax": end_of_week.isoformat(),
        "singleEvents": "true",
        "orderBy": "startTime",
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        return response.json().get("items", [])
    except requests.RequestException as error:
        print(f"Warning: Google Calendar API error for '{calendar_name}' ({error}). Using sample data.")
        return _get_sample_calendar_events(calendar_name)


def fetch_discord_chat_messages(channel_id: str, bot_token: str, limit: int = 50) -> list:
    """Fetches recent messages from a work Discord channel using a read-only Bot Token."""
    if not channel_id or not bot_token:
        return []

    url = f"https://discord.com/api/v10/channels/{channel_id}/messages"
    headers = {"Authorization": f"Bot {bot_token}"}
    params = {"limit": limit}

    try:
        response = requests.get(url, headers=headers, params=params, timeout=10)
        response.raise_for_status()
        return [
            {
                "author": msg.get("author", {}).get("username", "teammate"),
                "content": msg.get("content", ""),
                "timestamp": msg.get("timestamp", "")
            }
            for msg in response.json()
            if msg.get("content")
        ]
    except requests.RequestException as error:
        print(f"Warning: Discord API request failed ({error}).")
        return []


def _get_sample_calendar_events(calendar_name: str) -> list:
    """Provides offline fallback events tailored to the selected demo calendar."""
    base = datetime.datetime.now(datetime.timezone.utc).replace(hour=9, minute=0, second=0, microsecond=0)

    if calendar_name == "Demo - Calm Week":
        return [
            {
                "summary": "Weekly Team Catch-up",
                "description": "Casual sync on upcoming tasks for the week.",
                "start": {"dateTime": (base + datetime.timedelta(days=1, hours=1)).isoformat()},
                "end": {"dateTime": (base + datetime.timedelta(days=1, hours=2)).isoformat()},
            },
            {
                "summary": "Design Brainstorm",
                "description": "Exploring creative ideas for next month's sprint.",
                "start": {"dateTime": (base + datetime.timedelta(days=2, hours=5)).isoformat()},
                "end": {"dateTime": (base + datetime.timedelta(days=2, hours=6, minutes=30)).isoformat()},
            },
        ]

    return [
        {
            "summary": "URGENT: Q4 Production Sprint Planning",
            "description": "Critical deadline review with stakeholders",
            "start": {"dateTime": (base + datetime.timedelta(days=1)).isoformat()},
            "end": {"dateTime": (base + datetime.timedelta(days=1, hours=4)).isoformat()},
        },
        {
            "summary": "Client Escalation & Hotfix Sync",
            "description": "ASAP fix required before tonight's release window",
            "start": {"dateTime": (base + datetime.timedelta(days=1, hours=8)).isoformat()},
            "end": {"dateTime": (base + datetime.timedelta(days=1, hours=10, minutes=30)).isoformat()},
        },
    ]


def analyse_burnout(calendar_name: str, calendar_events: list, chat_messages: list) -> dict:
    """Analyses calendar workload and work-chat urgency to determine meal prep mode."""
    total_meeting_hours = 0.0
    late_evening_meetings = 0
    calendar_keyword_hits = 0
    chat_keyword_hits = 0
    flagged_triggers = []

    for event in calendar_events:
        start_str = event.get("start", {}).get("dateTime")
        end_str = event.get("end", {}).get("dateTime")

        if not start_str or not end_str:
            continue

        start_dt = datetime.datetime.fromisoformat(start_str.replace("Z", "+00:00"))
        end_dt = datetime.datetime.fromisoformat(end_str.replace("Z", "+00:00"))

        duration_hours = (end_dt - start_dt).total_seconds() / 3600.0
        total_meeting_hours += duration_hours

        # Meetings finishing at or after 18:00 directly disrupt evening cooking
        if end_dt.hour >= 18:
            late_evening_meetings += 1

        title = event.get("summary", "")
        description = event.get("description", "")
        combined_text = f"{title} {description}".lower()

        matched = [kw for kw in BURNOUT_KEYWORDS if kw in combined_text]
        if matched:
            calendar_keyword_hits += len(matched)
            flagged_triggers.append({
                "source": "calendar",
                "text": title,
                "keywords": matched
            })

    for msg in chat_messages:
        content = msg.get("content", "")
        matched = [kw for kw in BURNOUT_KEYWORDS if kw in content.lower()]
        if matched:
            chat_keyword_hits += len(matched)
            flagged_triggers.append({
                "source": "work_chat",
                "author": msg.get("author", "unknown"),
                "text": content,
                "keywords": matched
            })

    total_meeting_hours = round(total_meeting_hours, 2)
    total_keyword_hits = calendar_keyword_hits + chat_keyword_hits

    if total_meeting_hours >= 20.0 or total_keyword_hits >= 5 or late_evening_meetings >= 3:
        stress_status = "Burnout"
        meal_prep_mode = "minimal_prep"
    elif total_meeting_hours >= 10.0 or total_keyword_hits >= 2:
        stress_status = "Moderate"
        meal_prep_mode = "balanced_prep"
    else:
        stress_status = "Relaxing"
        meal_prep_mode = "from_scratch"

    return {
        "selected_calendar": calendar_name,
        "stress_status": stress_status,
        "meal_prep_mode": meal_prep_mode,
        "metrics": {
            "total_meeting_hours": total_meeting_hours,
            "late_evening_meetings": late_evening_meetings,
            "calendar_keyword_hits": calendar_keyword_hits,
            "chat_keyword_hits": chat_keyword_hits,
            "total_events_analysed": len(calendar_events),
            "total_messages_analysed": len(chat_messages),
        },
        "flagged_triggers": flagged_triggers,
    }


def run_burnout_check(calendar_name: str = "Demo - Burnout Week") -> dict:
    """Runs the burnout check for either 'Demo - Burnout Week' or 'Demo - Calm Week'."""
    api_key = os.getenv("GOOGLE_CALENDAR_API_KEY", "")
    discord_token = os.getenv("DISCORD_BOT_TOKEN", "")

    config = DEMO_CALENDARS.get(calendar_name, DEMO_CALENDARS["Demo - Burnout Week"])
    channel_id = os.getenv(config["discord_channel_env"], "")

    events = fetch_google_calendar_events(calendar_name, api_key)
    messages = fetch_discord_chat_messages(channel_id, discord_token)
    return analyse_burnout(calendar_name, events, messages)


if __name__ == "__main__":
    for name in ["Demo - Calm Week", "Demo - Burnout Week"]:
        report = run_burnout_check(calendar_name=name)
        print(f"\n--- {name} ---")
        print(json.dumps(report, indent=2))