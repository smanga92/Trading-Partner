"""
Trading Partner Bot - Your Pre-Trade Accountability System
A professional Telegram bot for disciplined trading decisions

Author: Custom Trading Bot
Version: 1.0.0
"""

import logging
import json
import os
from datetime import datetime
from typing import Dict, List, Optional
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ConversationHandler,
    ContextTypes,
    filters
)
from PIL import Image, ImageDraw, ImageFont
import textwrap

# ═══════════════════════════════════════════════════════════════════════════════
#                           CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════════

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Bot states for conversation flow
(
    SETUP_PAIRS,
    SETUP_QUESTIONS,
    ANSWERING,
    VERDICT_SELECTION
) = range(4)

# Data storage file
DATA_FILE = "bot_data.json"

# Image styling constants
IMAGE_WIDTH = 1200
IMAGE_PADDING = 60
HEADER_HEIGHT = 180
ROW_HEIGHT = 70
FOOTER_HEIGHT = 50

# Professional color scheme (Dark elegant theme)
COLORS = {
    'background': '#0A0E27',      # Deep navy blue
    'header': '#1A1F3A',          # Slightly lighter navy
    'accent': '#00D9FF',          # Bright cyan accent
    'accent_secondary': '#7B61FF', # Purple accent
    'text_primary': '#FFFFFF',    # White
    'text_secondary': '#B8C5D6',  # Light blue-gray
    'border': '#2D3548',          # Subtle border
    'row_alt': '#111628',         # Alternate row color
    'verdict_buy': '#00FF94',     # Green
    'verdict_sell': '#FF4757',    # Red
    'verdict_standby': '#FFB800', # Amber
}


# ═══════════════════════════════════════════════════════════════════════════════
#                           DATA MANAGEMENT
# ═══════════════════════════════════════════════════════════════════════════════

def load_user_data() -> Dict:
    """Load user data from JSON file"""
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            logger.warning("Corrupted data file, creating new one")
            return {}
    return {}


def save_user_data(data: Dict) -> None:
    """Save user data to JSON file"""
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=2)


def get_user_config(user_id: int) -> Optional[Dict]:
    """Get configuration for specific user"""
    data = load_user_data()
    return data.get(str(user_id))


def save_user_config(user_id: int, config: Dict) -> None:
    """Save configuration for specific user"""
    data = load_user_data()
    data[str(user_id)] = config
    save_user_data(data)


# ═══════════════════════════════════════════════════════════════════════════════
#                           IMAGE GENERATION
# ═══════════════════════════════════════════════════════════════════════════════

def get_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    """Get font with fallback options"""
    font_options = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
    ]
    
    for font_path in font_options:
        if os.path.exists(font_path):
            try:
                return ImageFont.truetype(font_path, size)
            except:
                continue
    
    # Fallback to default
    return ImageFont.load_default()


def wrap_text(text: str, font: ImageFont.FreeTypeFont, max_width: int) -> List[str]:
    """Wrap text to fit within max_width"""
    words = text.split()
    lines = []
    current_line = []
    
    for word in words:
        test_line = ' '.join(current_line + [word])
        bbox = font.getbbox(test_line)
        width = bbox[2] - bbox[0]
        
        if width <= max_width:
            current_line.append(word)
        else:
            if current_line:
                lines.append(' '.join(current_line))
            current_line = [word]
    
    if current_line:
        lines.append(' '.join(current_line))
    
    return lines if lines else [text]


def generate_trading_snapshot(
    pairs: List[str],
    questions: List[str],
    answers: Dict[str, List[str]],
    timestamp: str
) -> str:
    """
    Generate a professional trading snapshot image
    
    Args:
        pairs: List of trading pairs
        questions: List of question labels
        answers: Dictionary mapping pairs to their answers
        timestamp: Formatted timestamp string
    
    Returns:
        Path to generated image file
    """
    
    # Calculate image dimensions
    num_rows = len(pairs)
    table_height = HEADER_HEIGHT + (num_rows * ROW_HEIGHT) + FOOTER_HEIGHT + (IMAGE_PADDING * 2)
    
    # Create image
    img = Image.new('RGB', (IMAGE_WIDTH, table_height), COLORS['background'])
    draw = ImageDraw.Draw(img)
    
    # Load fonts
    font_title = get_font(36, bold=True)
    font_subtitle = get_font(18)
    font_header = get_font(16, bold=True)
    font_cell = get_font(15)
    font_timestamp = get_font(14)
    
    current_y = IMAGE_PADDING
    
    # ═══════════════════════════════════════════════════════════════════════════
    # HEADER SECTION
    # ═══════════════════════════════════════════════════════════════════════════
    
    # Draw header background with gradient effect
    for i in range(HEADER_HEIGHT):
        alpha = int(255 * (1 - i / HEADER_HEIGHT * 0.3))
        color = tuple(int(COLORS['header'].lstrip('#')[j:j+2], 16) for j in (0, 2, 4))
        draw.rectangle(
            [IMAGE_PADDING, current_y + i, IMAGE_WIDTH - IMAGE_PADDING, current_y + i + 1],
            fill=color
        )
    
    # Draw accent line at top of header
    draw.rectangle(
        [IMAGE_PADDING, current_y, IMAGE_WIDTH - IMAGE_PADDING, current_y + 4],
        fill=COLORS['accent']
    )
    
    # Title
    title_y = current_y + 30
    draw.text(
        (IMAGE_WIDTH // 2, title_y),
        "TRADING PLAN SNAPSHOT",
        font=font_title,
        fill=COLORS['text_primary'],
        anchor="mm"
    )
    
    # Subtitle with timestamp
    subtitle_y = title_y + 50
    draw.text(
        (IMAGE_WIDTH // 2, subtitle_y),
        timestamp,
        font=font_subtitle,
        fill=COLORS['accent'],
        anchor="mm"
    )
    
    # Accent decoration
    accent_width = 100
    accent_y = subtitle_y + 25
    draw.rectangle(
        [IMAGE_WIDTH // 2 - accent_width // 2, accent_y, 
         IMAGE_WIDTH // 2 + accent_width // 2, accent_y + 2],
        fill=COLORS['accent_secondary']
    )
    
    current_y += HEADER_HEIGHT
    
    # ═══════════════════════════════════════════════════════════════════════════
    # TABLE HEADER
    # ═══════════════════════════════════════════════════════════════════════════
    
    # Calculate column widths
    num_cols = len(questions) + 1  # +1 for pair column
    pair_col_width = 180
    remaining_width = IMAGE_WIDTH - (IMAGE_PADDING * 2) - pair_col_width
    question_col_width = remaining_width // len(questions)
    
    # Draw table header background
    draw.rectangle(
        [IMAGE_PADDING, current_y, IMAGE_WIDTH - IMAGE_PADDING, current_y + ROW_HEIGHT],
        fill=COLORS['header']
    )
    
    # Draw column headers
    col_x = IMAGE_PADDING + 20
    
    # Pair column header
    draw.text(
        (col_x, current_y + ROW_HEIGHT // 2),
        "PAIR",
        font=font_header,
        fill=COLORS['accent'],
        anchor="lm"
    )
    col_x += pair_col_width
    
    # Question column headers
    for question in questions:
        # Wrap text if needed
        max_text_width = question_col_width - 20
        wrapped_lines = wrap_text(question.upper(), font_header, max_text_width)
        
        if len(wrapped_lines) == 1:
            draw.text(
                (col_x, current_y + ROW_HEIGHT // 2),
                wrapped_lines[0],
                font=font_header,
                fill=COLORS['accent'],
                anchor="lm"
            )
        else:
            # Multi-line header
            line_height = 18
            start_y = current_y + (ROW_HEIGHT - len(wrapped_lines) * line_height) // 2
            for i, line in enumerate(wrapped_lines):
                draw.text(
                    (col_x, start_y + i * line_height),
                    line,
                    font=font_header,
                    fill=COLORS['accent'],
                    anchor="lm"
                )
        
        # Draw vertical separator
        draw.rectangle(
            [col_x - 10, current_y + 15, col_x - 8, current_y + ROW_HEIGHT - 15],
            fill=COLORS['border']
        )
        
        col_x += question_col_width
    
    current_y += ROW_HEIGHT
    
    # ═══════════════════════════════════════════════════════════════════════════
    # TABLE ROWS
    # ═══════════════════════════════════════════════════════════════════════════
    
    for row_idx, pair in enumerate(pairs):
        # Alternate row background
        if row_idx % 2 == 0:
            draw.rectangle(
                [IMAGE_PADDING, current_y, IMAGE_WIDTH - IMAGE_PADDING, current_y + ROW_HEIGHT],
                fill=COLORS['row_alt']
            )
        
        # Draw border line
        draw.rectangle(
            [IMAGE_PADDING, current_y, IMAGE_WIDTH - IMAGE_PADDING, current_y + 1],
            fill=COLORS['border']
        )
        
        col_x = IMAGE_PADDING + 20
        
        # Pair name
        draw.text(
            (col_x, current_y + ROW_HEIGHT // 2),
            pair,
            font=font_cell,
            fill=COLORS['text_primary'],
            anchor="lm"
        )
        col_x += pair_col_width
        
        # Answers
        pair_answers = answers.get(pair, [])
        for q_idx, answer in enumerate(pair_answers):
            # Special styling for verdict column
            if q_idx == len(questions) - 1:  # Last column is verdict
                verdict_lower = answer.lower()
                if 'buy' in verdict_lower:
                    text_color = COLORS['verdict_buy']
                    symbol = "▲"
                elif 'sell' in verdict_lower:
                    text_color = COLORS['verdict_sell']
                    symbol = "▼"
                else:
                    text_color = COLORS['verdict_standby']
                    symbol = "■"
                
                draw.text(
                    (col_x, current_y + ROW_HEIGHT // 2),
                    f"{symbol} {answer}",
                    font=font_cell,
                    fill=text_color,
                    anchor="lm"
                )
            else:
                # Wrap text if needed
                max_text_width = question_col_width - 20
                wrapped_lines = wrap_text(answer, font_cell, max_text_width)
                
                if len(wrapped_lines) == 1:
                    draw.text(
                        (col_x, current_y + ROW_HEIGHT // 2),
                        wrapped_lines[0],
                        font=font_cell,
                        fill=COLORS['text_secondary'],
                        anchor="lm"
                    )
                else:
                    # Multi-line cell
                    line_height = 16
                    start_y = current_y + (ROW_HEIGHT - len(wrapped_lines) * line_height) // 2
                    for i, line in enumerate(wrapped_lines[:2]):  # Max 2 lines
                        text = line if i < len(wrapped_lines) - 1 or len(wrapped_lines) <= 2 else line + "..."
                        draw.text(
                            (col_x, start_y + i * line_height),
                            text,
                            font=font_cell,
                            fill=COLORS['text_secondary'],
                            anchor="lm"
                        )
            
            # Draw vertical separator
            if q_idx < len(questions) - 1:
                draw.rectangle(
                    [col_x - 10, current_y + 15, col_x - 8, current_y + ROW_HEIGHT - 15],
                    fill=COLORS['border']
                )
            
            col_x += question_col_width
        
        current_y += ROW_HEIGHT
    
    # ═══════════════════════════════════════════════════════════════════════════
    # FOOTER
    # ═══════════════════════════════════════════════════════════════════════════
    
    # Bottom border line
    draw.rectangle(
        [IMAGE_PADDING, current_y, IMAGE_WIDTH - IMAGE_PADDING, current_y + 2],
        fill=COLORS['accent']
    )
    
    current_y += 30
    
    # Footer text
    draw.text(
        (IMAGE_WIDTH // 2, current_y),
        "Trade with discipline. Protect your capital. Trust your process.",
        font=font_timestamp,
        fill=COLORS['text_secondary'],
        anchor="mm"
    )
    
    # ═══════════════════════════════════════════════════════════════════════════
    # SAVE IMAGE
    # ═══════════════════════════════════════════════════════════════════════════
    
    output_path = f"trading_snapshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
    img.save(output_path, quality=95, optimize=True)
    
    logger.info(f"Generated snapshot image: {output_path}")
    return output_path


# ═══════════════════════════════════════════════════════════════════════════════
#                           BOT COMMAND HANDLERS
# ═══════════════════════════════════════════════════════════════════════════════

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start command - either setup or begin session"""
    user_id = update.effective_user.id
    config = get_user_config(user_id)
    
    if config is None:
        # First time setup
        await update.message.reply_text(
            "🎯 *Welcome to Your Trading Partner Bot*\n\n"
            "I'll help you maintain discipline and clarity before every trading session.\n\n"
            "Let's set up your trading framework.\n\n"
            "📊 *Step 1: Trading Pairs*\n"
            "Enter your trading pairs (comma-separated).\n\n"
            "*Example:* `EURUSD, GBPUSD, XAUUSD, USDJPY`",
            parse_mode='Markdown'
        )
        return SETUP_PAIRS
    else:
        # Start trading session
        context.user_data['pairs'] = config['pairs']
        context.user_data['questions'] = config['questions']
        context.user_data['answers'] = {}
        context.user_data['current_pair_index'] = 0
        context.user_data['current_question_index'] = 0
        
        await update.message.reply_text(
            "✅ *Session Started*\n\n"
            f"Analyzing {len(config['pairs'])} pairs with your framework.\n"
            "Answer each question thoughtfully.\n\n"
            "_Remember: If you're rushing, that's your signal to pause._",
            parse_mode='Markdown'
        )
        
        return await ask_next_question(update, context)


async def setup_pairs(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle pairs setup"""
    pairs_text = update.message.text.strip()
    pairs = [p.strip().upper() for p in pairs_text.split(',') if p.strip()]
    
    if not pairs:
        await update.message.reply_text(
            "❌ Please enter at least one trading pair.\n\n"
            "*Example:* `EURUSD, GBPUSD`",
            parse_mode='Markdown'
        )
        return SETUP_PAIRS
    
    context.user_data['pairs'] = pairs
    
    await update.message.reply_text(
        f"✅ *Pairs Configured:* {', '.join(pairs)}\n\n"
        "📋 *Step 2: Checklist Questions*\n\n"
        "Enter your 4 analysis questions (one per line).\n\n"
        "*Example:*\n"
        "`Daily Bias\n"
        "Order Flow\n"
        "M15 SMS\n"
        "Verdict`\n\n"
        "_The last question will be your Buy/Sell/Stand by decision._",
        parse_mode='Markdown'
    )
    return SETUP_QUESTIONS


async def setup_questions(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle questions setup"""
    questions_text = update.message.text.strip()
    questions = [q.strip() for q in questions_text.split('\n') if q.strip()]
    
    if len(questions) != 4:
        await update.message.reply_text(
            f"❌ Please enter exactly 4 questions (you entered {len(questions)}).\n\n"
            "*Example:*\n"
            "`Daily Bias\n"
            "Order Flow\n"
            "M15 SMS\n"
            "Verdict`",
            parse_mode='Markdown'
        )
        return SETUP_QUESTIONS
    
    # Save configuration
    user_id = update.effective_user.id
    config = {
        'pairs': context.user_data['pairs'],
        'questions': questions
    }
    save_user_config(user_id, config)
    
    await update.message.reply_text(
        "🎉 *Setup Complete!*\n\n"
        f"*Pairs:* {', '.join(config['pairs'])}\n"
        f"*Questions:* {len(questions)} configured\n\n"
        "Your framework is now saved.\n\n"
        "Ready to start? Use /start to begin your first session.\n\n"
        "_You can always edit your setup with /edit\\_pairs or /edit\\_questions_",
        parse_mode='Markdown'
    )
    return ConversationHandler.END


async def ask_next_question(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Ask the next question in sequence"""
    pairs = context.user_data['pairs']
    questions = context.user_data['questions']
    pair_idx = context.user_data['current_pair_index']
    q_idx = context.user_data['current_question_index']
    
    # Check if we're done
    if pair_idx >= len(pairs):
        return await generate_snapshot(update, context)
    
    current_pair = pairs[pair_idx]
    current_question = questions[q_idx]
    
    # Check if this is the verdict question (last question)
    if q_idx == len(questions) - 1:
        keyboard = [['Buy', 'Sell', 'Stand by']]
        reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
        
        await update.message.reply_text(
            f"💡 *{current_pair}*\n\n"
            f"*{current_question}*\n\n"
            "_Select your decision:_",
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
        return VERDICT_SELECTION
    else:
        await update.message.reply_text(
            f"💡 *{current_pair}*\n\n"
            f"*{current_question}:*",
            parse_mode='Markdown',
            reply_markup=ReplyKeyboardRemove()
        )
        return ANSWERING


async def handle_answer(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle user's answer to current question"""
    answer = update.message.text.strip()
    
    if not answer:
        await update.message.reply_text("❌ Please provide an answer.")
        return ANSWERING
    
    # Store answer
    pairs = context.user_data['pairs']
    questions = context.user_data['questions']
    pair_idx = context.user_data['current_pair_index']
    q_idx = context.user_data['current_question_index']
    current_pair = pairs[pair_idx]
    
    if current_pair not in context.user_data['answers']:
        context.user_data['answers'][current_pair] = []
    
    context.user_data['answers'][current_pair].append(answer)
    
    # Move to next question or pair
    q_idx += 1
    if q_idx >= len(questions):
        # Move to next pair
        pair_idx += 1
        q_idx = 0
        context.user_data['current_pair_index'] = pair_idx
        context.user_data['current_question_index'] = q_idx
        
        if pair_idx < len(pairs):
            await update.message.reply_text(
                f"✓ {current_pair} complete\n\n"
                f"→ Moving to {pairs[pair_idx]}",
                parse_mode='Markdown'
            )
    else:
        context.user_data['current_question_index'] = q_idx
    
    return await ask_next_question(update, context)


async def handle_verdict(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle verdict selection"""
    verdict = update.message.text.strip()
    
    if verdict not in ['Buy', 'Sell', 'Stand by']:
        await update.message.reply_text("❌ Please select Buy, Sell, or Stand by.")
        return VERDICT_SELECTION
    
    # Store verdict
    pairs = context.user_data['pairs']
    pair_idx = context.user_data['current_pair_index']
    current_pair = pairs[pair_idx]
    
    context.user_data['answers'][current_pair].append(verdict)
    
    # Move to next pair
    pair_idx += 1
    context.user_data['current_pair_index'] = pair_idx
    context.user_data['current_question_index'] = 0
    
    if pair_idx < len(pairs):
        await update.message.reply_text(
            f"✓ {current_pair} complete\n\n"
            f"→ Moving to {pairs[pair_idx]}",
            parse_mode='Markdown',
            reply_markup=ReplyKeyboardRemove()
        )
        return await ask_next_question(update, context)
    else:
        return await generate_snapshot(update, context)


async def generate_snapshot(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Generate and send the trading snapshot image"""
    await update.message.reply_text(
        "✅ *Checklist Completed*\n\n"
        "Generating your trading snapshot...",
        parse_mode='Markdown',
        reply_markup=ReplyKeyboardRemove()
    )
    
    # Get data
    pairs = context.user_data['pairs']
    questions = context.user_data['questions']
    answers = context.user_data['answers']
    
    # Generate timestamp
    now = datetime.now()
    timestamp = now.strftime("%d %b %Y | %H:%M")
    
    # Generate image
    try:
        image_path = generate_trading_snapshot(pairs, questions, answers, timestamp)
        
        # Send image
        with open(image_path, 'rb') as photo:
            await update.message.reply_photo(
                photo=photo,
                caption="📸 *Your Trading Plan Snapshot*\n\n"
                        "_Review carefully before placing any trades._\n\n"
                        "Use /start to begin a new session.",
                parse_mode='Markdown'
            )
        
        # Clean up
        if os.path.exists(image_path):
            os.remove(image_path)
        
    except Exception as e:
        logger.error(f"Error generating image: {e}")
        await update.message.reply_text(
            "❌ Error generating snapshot image. Please try again with /start"
        )
    
    return ConversationHandler.END


async def edit_pairs(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Edit configured pairs"""
    user_id = update.effective_user.id
    config = get_user_config(user_id)
    
    if config is None:
        await update.message.reply_text(
            "❌ You haven't set up your bot yet. Use /start to begin setup."
        )
        return ConversationHandler.END
    
    await update.message.reply_text(
        f"*Current pairs:* {', '.join(config['pairs'])}\n\n"
        "Enter your new trading pairs (comma-separated):",
        parse_mode='Markdown'
    )
    
    context.user_data['editing_pairs'] = True
    return SETUP_PAIRS


async def edit_questions(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Edit configured questions"""
    user_id = update.effective_user.id
    config = get_user_config(user_id)
    
    if config is None:
        await update.message.reply_text(
            "❌ You haven't set up your bot yet. Use /start to begin setup."
        )
        return ConversationHandler.END
    
    current_questions = '\n'.join(f"{i+1}. {q}" for i, q in enumerate(config['questions']))
    
    await update.message.reply_text(
        f"*Current questions:*\n{current_questions}\n\n"
        "Enter your 4 new questions (one per line):",
        parse_mode='Markdown'
    )
    
    context.user_data['pairs'] = config['pairs']
    context.user_data['editing_questions'] = True
    return SETUP_QUESTIONS


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send help message"""
    help_text = """
🎯 *Trading Partner Bot - Help*

*Available Commands:*
/start - Begin new trading session or initial setup
/edit\\_pairs - Change your trading pairs
/edit\\_questions - Modify your checklist questions
/help - Show this help message
/cancel - Cancel current operation

*How It Works:*
1. Set up your pairs and questions (first time only)
2. Use /start before each trading session
3. Answer questions for each pair
4. Receive a professional snapshot image
5. Download and reference during trading

*Philosophy:*
This bot enforces discipline, not entries.
If you rush through questions, don't trade.

*Pro Tips:*
• Previous sessions remain visible in chat history
• "Stand by" is a valid decision
• The snapshot is your commitment
• Review it before placing any trade
    """
    
    await update.message.reply_text(help_text, parse_mode='Markdown')


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancel current operation"""
    await update.message.reply_text(
        "❌ Operation cancelled.\n\n"
        "Use /start to begin a new session.",
        reply_markup=ReplyKeyboardRemove()
    )
    return ConversationHandler.END


# ═══════════════════════════════════════════════════════════════════════════════
#                           MAIN APPLICATION
# ═══════════════════════════════════════════════════════════════════════════════

def main() -> None:
    """Start the bot"""
    
    # Get bot token from environment variable or file
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    
    if not token:
        # Try to load from config file
        if os.path.exists('bot_token.txt'):
            with open('bot_token.txt', 'r') as f:
                token = f.read().strip()
    
    if not token:
        print("❌ ERROR: Bot token not found!")
        print("\nPlease either:")
        print("1. Set TELEGRAM_BOT_TOKEN environment variable")
        print("2. Create 'bot_token.txt' file with your token")
        print("\nGet your token from @BotFather on Telegram")
        return
    
    # Create application
    application = Application.builder().token(token).build()
    
    # Setup conversation handler
    conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler('start', start),
            CommandHandler('edit_pairs', edit_pairs),
            CommandHandler('edit_questions', edit_questions),
        ],
        states={
            SETUP_PAIRS: [MessageHandler(filters.TEXT & ~filters.COMMAND, setup_pairs)],
            SETUP_QUESTIONS: [MessageHandler(filters.TEXT & ~filters.COMMAND, setup_questions)],
            ANSWERING: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_answer)],
            VERDICT_SELECTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_verdict)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )
    
    application.add_handler(conv_handler)
    application.add_handler(CommandHandler('help', help_command))
    
    # Start the bot
    print("🤖 Trading Partner Bot is running...")
    print("Press Ctrl+C to stop\n")
    
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    main()
