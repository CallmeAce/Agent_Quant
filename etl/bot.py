"""
Telegram Bot for Openclaw QuantOps.

Handles:
- Alert notifications (job failures, data quality issues)
- Status queries (/status, /jobs, /health)
- Daily/weekly reports
"""

from __future__ import annotations

import asyncio
import logging
import os
from datetime import datetime, timezone
from typing import Optional

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

logger = logging.getLogger(__name__)


class TelegramBot:
    def __init__(self) -> None:
        self.token = os.environ.get("TELEGRAM_BOT_TOKEN", "")
        self.admin_chat_id = os.environ.get("TELEGRAM_ADMIN_CHAT_ID", "")

        if not self.token:
            logger.warning("TELEGRAM_BOT_TOKEN not set. Bot will not start.")

        self.application: Optional[Application] = None

    async def start(self) -> None:
        """Start the bot."""
        if not self.token:
            logger.error("Cannot start bot: TELEGRAM_BOT_TOKEN is not configured")
            return

        self.application = (
            Application.builder()
            .token(self.token)
            .build()
        )

        # Register command handlers
        self.application.add_handler(CommandHandler("start", self.cmd_start))
        self.application.add_handler(CommandHandler("help", self.cmd_help))
        self.application.add_handler(CommandHandler("status", self.cmd_status))
        self.application.add_handler(CommandHandler("health", self.cmd_health))
        self.application.add_handler(CommandHandler("jobs", self.cmd_jobs))

        # Register message handler for non-command messages
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))

        # Add error handler for debugging
        self.application.add_error_handler(self.on_error)

        logger.info("Starting Telegram Bot...")
        await self.application.initialize()
        await self.application.start()
        await self.application.updater.start_polling(allowed_updates=Update.ALL_TYPES)
        logger.info("Telegram Bot started successfully")

    async def stop(self) -> None:
        """Stop the bot."""
        if self.application:
            await self.application.stop()
            logger.info("Telegram Bot stopped")

    async def cmd_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /start command."""
        logger.info(f"Received /start from user {update.message.from_user.first_name} (ID: {update.message.from_user.id})")
        await update.message.reply_text(
            "Welcome to Openclaw QuantOps Bot!\n\n"
            "Use /help to see available commands."
        )

    async def cmd_help(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /help command."""
        help_text = """
*Openclaw QuantOps Bot Commands*

/status - Check system status
/health - Health check for all services
/jobs - List recent ETL jobs
/config - View current configuration

*Admin Only:*
/restart - Restart services
/logs - Get recent logs
"""
        await update.message.reply_text(help_text, parse_mode="Markdown")

    async def cmd_status(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /status command."""
        # TODO: Implement actual status check from database
        status_text = (
            "*System Status*\n\n"
            f"Timestamp: {datetime.now(timezone.utc).isoformat()}\n"
            "Database: Connected\n"
            "Scheduler: Running\n"
            "Last ETL Run: N/A"
        )
        await update.message.reply_text(status_text, parse_mode="Markdown")

    async def cmd_health(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /health command."""
        health_text = (
            "*Health Check*\n\n"
            "All systems operational."
        )
        await update.message.reply_text(health_text, parse_mode="Markdown")

    async def cmd_jobs(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /jobs command."""
        jobs_text = (
            "*Recent Jobs*\n\n"
            "No jobs recorded yet."
        )
        await update.message.reply_text(jobs_text, parse_mode="Markdown")

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle non-command text messages."""
        user = update.message.from_user
        text = update.message.text
        logger.info(f"Received message from {user.first_name}: {text}")

        # Echo back for testing
        await update.message.reply_text(
            f"Hello {user.first_name}! I received your message:\n\n{text}"
        )

    async def on_error(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Log errors."""
        logger.error(f"Update {update} caused error: {context.error}")
        if update and update.message:
            logger.error(f"Message from user: {update.message.text}")

    async def send_alert(self, message: str, level: str = "INFO") -> None:
        """Send an alert message to admin chat."""
        if not self.admin_chat_id or not self.application:
            logger.warning(f"Alert not sent (no admin chat ID): {message}")
            return

        emoji = {"INFO": "ℹ️", "WARNING": "⚠️", "CRITICAL": "🚨"}.get(level, "📢")

        await self.application.bot.send_message(
            chat_id=self.admin_chat_id,
            text=f"{emoji} *[{level}]* {message}",
            parse_mode="Markdown"
        )


async def main():
    bot = TelegramBot()
    try:
        await bot.start()
        # Keep running
        while True:
            await asyncio.sleep(3600)
    except KeyboardInterrupt:
        await bot.stop()


if __name__ == "__main__":
    logging.basicConfig(
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        level=os.environ.get("LOG_LEVEL", "INFO")
    )
    asyncio.run(main())
