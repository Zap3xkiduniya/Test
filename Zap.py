import sys
import re
import requests

# Set your Telegram Bot Token here (if running in Telegram mode)
BOT_TOKEN = "8800707730:AAHm2hGRHU0tH8hEAm_3StnHep2qpD2NXUk"

API_URL = "https://nitin-apis-update-birthday-spacial.vercel.app/api?type=number&search="

def redact_sensitive_info(text: str) -> str:
    """Mask sensitive Aadhaar numbers and replace target credit text."""
    # Replace specified owner credit
    text = re.sub(r"@Owenr_of_CSE_Simple_Learning", "@ZAP", text, flags=re.IGNORECASE)
    
    # Redact 12-digit Aadhaar numbers for privacy compliance
    text = re.sub(r"(🪪\s*Aadhaar:\s*)\d{12}", r"\1[Aadhaar Redacted]", text)
    text = re.sub(r"\b\d{12}\b", "[Aadhaar Redacted]", text)
    
    return text

def extract_phone_numbers(text: str) -> list:
    """Extract all 10-digit mobile numbers from the result text."""
    # Matches Mobile: or Alternate: numbers
    numbers = re.findall(r"(?:Mobile|Alternate):\s*(\d{10})", text)
    return list(set(numbers))

def recursive_number_search(initial_number: str, max_depth: int = 5) -> str:
    """Recursively search primary and alternate numbers up to max_depth."""
    visited = set()
    queue = [initial_number]
    full_output = []

    while queue and len(visited) < max_depth:
        current_num = queue.pop(0)
        
        if current_num in visited:
            continue
            
        visited.add(current_num)
        
        try:
            response = requests.get(f"{API_URL}{current_num}", timeout=10)
            if response.status_code == 200:
                raw_data = response.text
                
                # Sanitize response
                processed_data = redact_sensitive_info(raw_data)
                full_output.append(f"=== RESULT FOR: {current_num} ===\n" + processed_data)
                
                # Find new alternate numbers to query
                found_numbers = extract_phone_numbers(raw_data)
                for num in found_numbers:
                    if num not in visited and num not in queue:
                        queue.append(num)
            else:
                full_output.append(f"❌ Failed to fetch data for {current_num} (HTTP {response.status_code})")
        except Exception as e:
            full_output.append(f"❌ Error fetching {current_num}: {str(e)}")

    return "\n\n".join(full_output)

# ----------------- CLI / Termux Mode ----------------- #
def run_cli():
    print("=" * 50)
    print("      NUMBER LOOKUP TOOL (Termux / CLI Mode)")
    print("=" * 50)
    
    number = input("Enter Mobile Number: ").strip()
    if not number.isdigit() or len(number) != 10:
        print("❌ Invalid 10-digit mobile number.")
        return
        
    print(f"\n🔍 Processing recursive search for {number}...\n")
    results = recursive_number_search(number)
    print(results)

# ----------------- Telegram Bot Mode ----------------- #
def run_telegram_bot():
    try:
        import telebot
    except ImportError:
        print("❌ 'pyTelegramBotAPI' library is required. Install it using: pip install pyTelegramBotAPI")
        sys.exit(1)

    if BOT_TOKEN == "YOUR_TELEGRAM_BOT_TOKEN_HERE":
        print("❌ Please set a valid BOT_TOKEN in the code before running Telegram Bot mode.")
        sys.exit(1)

    bot = telebot.TeleBot(BOT_TOKEN)

    @bot.message_handler(commands=['start', 'help'])
    def send_welcome(message):
        bot.reply_to(message, "👋 Send a 10-digit mobile number to initiate recursive search.")

    @bot.message_handler(func=lambda msg: True)
    def handle_search(message):
        text = message.text.strip()
        if not text.isdigit() or len(text) != 10:
            bot.reply_to(message, "⚠️ Please provide a valid 10-digit phone number.")
            return

        status_msg = bot.reply_to(message, f"🔍 Searching recursively for `{text}`...", parse_mode="Markdown")
        results = recursive_number_search(text)
        
        # Send long output in chunks if needed
        if len(results) > 4000:
            for chunk in [results[i:i+4000] for i in range(0, len(results), 4000)]:
                bot.send_message(message.chat.id, chunk)
        else:
            bot.edit_message_text(results, chat_id=status_msg.chat.id, message_id=status_msg.message_id)

    print("🤖 Telegram Bot started listening...")
    bot.infinity_polling()

# ----------------- Entry Point ----------------- #
if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--bot":
        run_telegram_bot()
    else:
        run_cli()

