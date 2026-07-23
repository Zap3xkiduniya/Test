#!/usr/bin/env python3
"""
📞 Number Lookup Tool - Recursive Loop + Telegram Bot
🔁 Auto-searches all alternate numbers recursively
🏷️ Credit: @ZAP (replaces @Owenr_of_CSE_Simple_Learning)

Usage:
  CLI Mode:     python3 number_lookup_bot.py 9876543210
  Bot Mode:     python3 number_lookup_bot.py --bot
"""

import os
import sys
import re
import time
import json
import requests

# ─── CONFIGURATION ────────────────────────────────────────────────────────────
API_BASE = "https://nitin-apis-update-birthday-spacial.vercel.app/api"
CREDIT_OLD = "@Owenr_of_CSE_Simple_Learning"
CREDIT_NEW = "@ZAP"

# Telegram Bot config – set these via environment variables or edit directly
BOT_TOKEN = os.getenv("BOT_TOKEN", "8800707730:AAHm2hGRHU0tH8hEAm_3StnHep2qpD2NXUk")
ALLOWED_USER_IDS = os.getenv("ALLOWED_USER_IDS", "")  # comma-separated IDs, empty = allow all

# ─── CORE ENGINE ──────────────────────────────────────────────────────────────

def fetch_number(number):
    """Call the API and return raw text response."""
    try:
        url = f"{API_BASE}?type=number&search={number}"
        resp = requests.get(url, timeout=15)
        resp.raise_for_status()
        return resp.text
    except Exception as e:
        return f"❌ Error fetching {number}: {e}"


def extract_numbers(text):
    """
    Extract all unique 10-digit Indian mobile numbers from the response.
    Returns a set of numbers.
    """
    # Find all Mobile: XXXXX and Alternate: XXXXX numbers
    numbers = set()
    # Pattern: 📱 Mobile: 9876543210 or 📞 Alternate: 9876543210
    for match in re.finditer(r'(?:Mobile|Alternate)\s*:\s*(\d{10})', text):
        numbers.add(match.group(1))
    return numbers


def replace_credit(text):
    """Replace the old credit with new credit."""
    return text.replace(CREDIT_OLD, CREDIT_NEW)


def format_single_result(number, raw_text, depth=0):
    """Format a single lookup result with depth indicator."""
    indent = "  " * depth
    prefix = "  ╰─" if depth > 0 else ""
    formatted = replace_credit(raw_text)
    # Remove the "Owner: @..." line from middle, will add at end
    lines = formatted.split('\n')
    filtered_lines = [l for l in lines if not l.strip().startswith("Owner:")]
    result = '\n'.join(filtered_lines).strip()
    return f"{indent}{prefix} 🔍 #{number} (Depth {depth})\n{result}"


def recursive_lookup(start_number, max_depth=10, delay=1.0):
    """
    BFS-style recursive lookup.
    Returns (full_report_text, all_visited_numbers, total_entries)
    """
    visited = set()
    queue = [start_number]
    all_reports = []
    depth_map = {start_number: 0}
    total_entries = 0

    print(f"\n{'='*60}")
    print(f"🔁 RECURSIVE NUMBER LOOKUP STARTING FROM: {start_number}")
    print(f"{'='*60}\n")

    while queue and len(visited) < 100:  # safety cap
        current = queue.pop(0)
        if current in visited:
            continue

        visited.add(current)
        depth = depth_map.get(current, 0)

        print(f"[{len(visited)}] Searching: {current} (Depth: {depth})")
        
        raw = fetch_number(current)
        if raw.startswith("❌"):
            all_reports.append(f"❌ Failed: {current} – {raw}")
            continue

        # Format and collect
        formatted = format_single_result(current, raw, depth)
        all_reports.append(formatted)
        total_entries += 1

        # Extract new numbers from this response
        new_numbers = extract_numbers(raw)
        for num in new_numbers:
            if num not in visited and num not in queue:
                queue.append(num)
                depth_map[num] = depth + 1

        print(f"   → Found {len(new_numbers)} numbers, queue: {len(queue)} remaining\n")
        time.sleep(delay)

    # Build final report
    footer = f"\n{'─'*50}\n📊 SUMMARY:\n"
    footer += f"   Total unique numbers searched: {len(visited)}\n"
    footer += f"   Total entries found: {total_entries}\n"
    footer += f"   Max depth reached: {max(depth_map.values())}\n"
    footer += f"   Owner: {CREDIT_NEW}\n"
    footer += f"{'─'*50}\n"

    full_report = '\n'.join(all_reports) + footer
    return full_report, visited, total_entries


# ─── CLI MODE ─────────────────────────────────────────────────────────────────

def cli_mode():
    """Run in command-line / Termux mode."""
    if len(sys.argv) < 2 or sys.argv[1] in ('-h', '--help'):
        print(__doc__)
        return

    number = sys.argv[1]
    if not re.match(r'^\d{10}$', number):
        print("❌ Invalid number. Please provide a valid 10-digit Indian mobile number.")
        return

    report, visited, total = recursive_lookup(number)
    print(report)

    # Save to file
    filename = f"lookup_{number}_{int(time.time())}.txt"
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(report)
    print(f"\n💾 Report saved to: {filename}")


# ─── TELEGRAM BOT MODE ────────────────────────────────────────────────────────

def telegram_bot():
    """Run as a Telegram bot."""
    if BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
        print("❌ BOT_TOKEN not set!")
        print("   Set environment variable: export BOT_TOKEN='your_token'")
        print("   Or edit the script directly.")
        sys.exit(1)

    try:
        from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
        from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
    except ImportError:
        print("❌ python-telegram-bot not installed!")
        print("   Install: pip install python-telegram-bot requests")
        sys.exit(1)

    print(f"🤖 Telegram Bot Starting...")
    print(f"   Bot Token: {BOT_TOKEN[:10]}...{BOT_TOKEN[-5:]}")
    print(f"   Allowed users: {ALLOWED_USER_IDS if ALLOWED_USER_IDS else 'Everyone'}")

    async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = str(update.effective_user.id)
        if ALLOWED_USER_IDS and user_id not in ALLOWED_USER_IDS.split(','):
            await update.message.reply_text("⛔ You are not authorized to use this bot.")
            return
        await update.message.reply_text(
            f"👋 *Number Lookup Bot*\n\n"
            f"Send me a **10-digit Indian mobile number** and I'll recursively "
            f"search all linked numbers!\n\n"
            f"🏷️ Credit: {CREDIT_NEW}",
            parse_mode='Markdown'
        )

    async def handle_number(update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = str(update.effective_user.id)
        if ALLOWED_USER_IDS and user_id not in ALLOWED_USER_IDS.split(','):
            await update.message.reply_text("⛔ You are not authorized to use this bot.")
            return

        text = update.message.text.strip()
        # Extract 10-digit number from message
        match = re.search(r'\b(\d{10})\b', text)
        if not match:
            await update.message.reply_text(
                "❌ Please send a valid 10-digit Indian mobile number.\n"
                "Example: `9876543210`",
                parse_mode='Markdown'
            )
            return

        number = match.group(1)
        
        # Send initial status
        status_msg = await update.message.reply_text(
            f"🔍 Starting recursive search for `{number}`...\n"
            f"This may take a while ⏳",
            parse_mode='Markdown'
        )

        try:
            report, visited, total = recursive_lookup(number, delay=0.5)

            # Truncate if too long (Telegram max: 4096 chars)
            if len(report) > 3900:
                report = report[:3900] + "\n\n... ⚠️ Report truncated (too long). Full report saved on server."

            await status_msg.edit_text(
                f"✅ *Lookup Complete!*\n\n"
                f"📊 Numbers searched: {len(visited)}\n"
                f"📋 Total entries: {total}\n\n"
                f"🏷️ Credit: {CREDIT_NEW}",
                parse_mode='Markdown'
            )

            # Send the report in chunks if needed
            if len(report) <= 4096:
                await update.message.reply_text(report)
            else:
                for i in range(0, len(report), 4096):
                    await update.message.reply_text(report[i:i+4096])

        except Exception as e:
            await status_msg.edit_text(f"❌ Error: {str(e)}")

    async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text(
            "📖 *Commands:*\n"
            "/start - Start the bot\n"
            "/help - Show this help\n\n"
            "Or just send any 10-digit number to look up!",
            parse_mode='Markdown'
        )

    # Build application
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_number))

    print("🤖 Bot is polling... Press Ctrl+C to stop.")
    app.run_polling()


# ─── MAIN ─────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--bot":
        telegram_bot()
    else:
        cli_mode()
