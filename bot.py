#!/usr/bin/env python3
"""A small, configurable Telegram FAQ bot. Uses only Python's standard library."""

import json
import os
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path


ROOT = Path(__file__).resolve().parent
DATA_FILE = Path(os.getenv("DATA_FILE", ROOT / "data.json"))
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
OWNER_ID = os.getenv("OWNER_TELEGRAM_ID", "").strip()
API = f"https://api.telegram.org/bot{TOKEN}/"
DEFAULT_DATA = {
    "business_name": "Our business",
    "description": "",
    "hours": "Please contact us for our opening hours.",
    "contact": "Please contact us directly for help.",
    "fallback": "Thanks for your message! I couldn't find an answer to that. A team member will get back to you soon.",
    "faqs": [
        {"question": "What are your opening hours?", "answer": "Please contact us for our opening hours."},
        {"question": "How can I contact you?", "answer": "Please contact us directly for help."},
    ],
}


def load_data():
    if not DATA_FILE.exists():
        save_data(DEFAULT_DATA)
    try:
        data = json.loads(DATA_FILE.read_text(encoding="utf-8"))
        for key, value in DEFAULT_DATA.items():
            data.setdefault(key, value)
        return data
    except (OSError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"Cannot read {DATA_FILE}: {exc}") from exc


def save_data(data):
    DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    tmp = DATA_FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    tmp.replace(DATA_FILE)


def api(method, payload=None):
    body = json.dumps(payload or {}).encode()
    request = urllib.request.Request(API + method, data=body,
                                     headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(request, timeout=40) as response:
            result = json.loads(response.read())
        if not result.get("ok"):
            raise RuntimeError(result.get("description", "Telegram API error"))
        return result["result"]
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Telegram request failed: {exc}") from exc


def send(chat_id, text):
    # Telegram messages have a 4096 character limit.
    api("sendMessage", {"chat_id": chat_id, "text": text[:4000]})


def is_owner(user_id):
    return bool(OWNER_ID) and str(user_id) == OWNER_ID


def words(text):
    return set(re.findall(r"[a-z0-9]+", text.lower()))


def answer_for(text, data):
    query = words(text)
    best, score = None, 0
    for faq in data["faqs"]:
        key_words = words(faq["question"])
        if not key_words:
            continue
        overlap = len(query & key_words)
        # Require a useful match; shorter matches are weighted more strictly.
        ratio = overlap / len(key_words)
        if overlap >= 2 and ratio > score:
            best, score = faq["answer"], ratio
    if best and score >= 0.4:
        return best
    text_lower = text.lower()
    if any(word in text_lower for word in ("hour", "open", "close", "when")):
        return data["hours"]
    if any(word in text_lower for word in ("contact", "phone", "email", "address", "where")):
        return data["contact"]
    return data["fallback"]


def help_text(owner=False):
    text = (
        "Send a message and I'll try to answer using our business FAQs.\n"
        "Use /hours or /contact for quick details, or /faq to browse common questions."
    )
    if owner:
        text += (
            "\n\nOwner commands:\n"
            "/addfaq question | answer\n/delfaq number\n"
            "/setbusiness name | short description\n"
            "/sethours your opening hours\n/setcontact contact details\n"
            "/setfallback message shown when no answer matches\n"
            "/listfaqs"
        )
    return text


def handle(message):
    chat = message.get("chat", {}).get("id")
    user = message.get("from", {})
    text = (message.get("text") or "").strip()
    if not chat or not text or user.get("is_bot"):
        return
    data = load_data()
    owner = is_owner(user.get("id"))
    command = text.split()[0].split("@")[0].lower() if text.startswith("/") else ""
    arg = text[len(text.split()[0]):].strip() if command else ""

    if command in ("/start", "/help"):
        send(chat, f"Welcome to {data['business_name']}!\n\n" + help_text(owner))
    elif command == "/hours":
        send(chat, data["hours"])
    elif command == "/contact":
        send(chat, data["contact"])
    elif command == "/faq":
        send(chat, "Frequently asked questions:\n" + "\n".join(
            f"• {faq['question']}" for faq in data["faqs"]))
    elif command == "/listfaqs" and owner:
        send(chat, "\n".join(f"{i}. {faq['question']}" for i, faq in enumerate(data["faqs"], 1)) or "No FAQs yet.")
    elif command == "/addfaq" and owner:
        parts = arg.split("|", 1)
        if len(parts) != 2 or not all(part.strip() for part in parts):
            send(chat, "Use: /addfaq question | answer")
        else:
            data["faqs"].append({"question": parts[0].strip(), "answer": parts[1].strip()})
            save_data(data)
            send(chat, "FAQ added.")
    elif command == "/delfaq" and owner:
        try:
            index = int(arg) - 1
            removed = data["faqs"].pop(index)
            save_data(data)
            send(chat, f"Removed: {removed['question']}")
        except (ValueError, IndexError):
            send(chat, "Use /listfaqs to see numbers, then /delfaq number")
    elif command == "/setbusiness" and owner:
        parts = arg.split("|", 1)
        if len(parts) != 2 or not all(part.strip() for part in parts):
            send(chat, "Use: /setbusiness business name | short description")
        else:
            data["business_name"], data["description"] = (p.strip() for p in parts)
            save_data(data)
            send(chat, "Business profile updated.")
    elif command in ("/sethours", "/setcontact", "/setfallback") and owner:
        if not arg:
            send(chat, f"Add the new text after {command}.")
        else:
            field = {"/sethours": "hours", "/setcontact": "contact", "/setfallback": "fallback"}[command]
            data[field] = arg
            save_data(data)
            send(chat, "Updated.")
    elif command and owner:
        send(chat, help_text(True))
    elif command:
        send(chat, "Sorry, I don't recognize that command. Send /help to see what I can do.")
    else:
        send(chat, answer_for(text, data))


def main():
    if not TOKEN:
        raise SystemExit("Set TELEGRAM_BOT_TOKEN in your environment before starting the bot.")
    try:
        me = api("getMe")
        print(f"Running as @{me.get('username')} for {load_data()['business_name']}", flush=True)
    except Exception as exc:
        raise SystemExit(f"Startup failed: {exc}")

    offset = None
    while True:
        try:
            payload = {"timeout": 30, "allowed_updates": ["message"]}
            if offset is not None:
                payload["offset"] = offset
            for update in api("getUpdates", payload):
                offset = update["update_id"] + 1
                try:
                    handle(update.get("message", {}))
                except Exception as exc:
                    # Keep polling if one malformed message or temporary send error occurs.
                    print(f"Message handling error: {exc}", flush=True)
        except KeyboardInterrupt:
            print("\nStopped.")
            return
        except Exception as exc:
            print(f"Polling error: {exc}; retrying in 3 seconds", flush=True)
            time.sleep(3)


if __name__ == "__main__":
    main()
