# Telegram Customer Reply Bot

A small FAQ auto-reply bot for a single business. Each business owner runs their own copy and connects a Telegram bot token. It uses Python's standard library, so there are no package installs.

## What it does

- Replies to customer messages using a simple keyword match against saved FAQs.
- Answers opening-hours and contact questions directly.
- Lets the owner add/remove FAQs and edit the business details in Telegram.
- Sends a configurable fallback when it cannot find an answer.
- Saves settings in `data.json` so they survive restarts.

This is a rules-based starter, not an AI chatbot. Owners should keep answers accurate and review customer conversations. For a hosted service serving many businesses, build a separate tenant-aware dashboard, billing, and isolated data storage rather than sharing one `data.json` between customers.

## Setup

1. In Telegram, message **@BotFather**, run `/newbot`, follow its prompts, and copy the token.
2. Find your numeric Telegram user ID using a trusted ID lookup bot or a small `getUpdates` check after messaging your new bot. Set this as the owner ID so only you can change FAQs and settings.
3. Copy `.env.example` to `.env` and fill in the token and owner ID.
4. Run:

   ```sh
   set -a
   . ./.env
   set +a
   python3 bot.py
   ```

Keep the process running on an always-on computer or deploy it to a small server. Do not share the bot token: it gives control of the bot. If a token is exposed, revoke it with BotFather and replace it.

## Owner commands

- `/addfaq question | answer` — add a frequently asked question.
- `/listfaqs` — show FAQ numbers.
- `/delfaq number` — remove an FAQ.
- `/setbusiness name | short description` — edit the greeting profile.
- `/sethours opening hours` — change the hours reply.
- `/setcontact contact details` — change the contact reply.
- `/setfallback message` — change the response for unmatched questions.
- `/hours`, `/contact`, `/faq` — customer shortcuts.

Only the configured owner ID can change settings. For robust production use, add monitoring, backups, human handoff, privacy terms, and stronger intent matching before selling this as a managed hosted service.

## Docker

Build the image with `docker build -t customer-reply-bot .`, then run it with persistent storage mounted at `/data` and pass `TELEGRAM_BOT_TOKEN` and `OWNER_TELEGRAM_ID` as environment variables. Keep `/data` mounted across redeploys so the business profile is retained.
# telegram-bot
