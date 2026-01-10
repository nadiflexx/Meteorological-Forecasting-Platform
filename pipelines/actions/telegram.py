from datetime import datetime
import json
import logging
import os

from dotenv import load_dotenv  # Make sure you have python-dotenv installed
import requests


class TelegramBotSender:
    """Class for handling message sending through a Telegram bot."""

    def __init__(self, token: str = None):
        """
        Initializes the Telegram bot.

        Args:
            token: Telegram bot token (optional, will be loaded from .env if not provided)
        """
        # Load environment variables from .env file
        load_dotenv()

        self.token = token or os.getenv('TELEGRAM_BOT_TOKEN')
        self.base_url = "https://api.telegram.org/bot"
        self.logger = self._setup_logger()

        # Verify we have a token
        if not self.token:
            self.logger.warning("Bot token not configured. Use TELEGRAM_BOT_TOKEN in your .env file")

    def _setup_logger(self) -> logging.Logger:
        """Configures the logger for the class."""
        logger = logging.getLogger(__name__)
        logger.setLevel(logging.INFO)

        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)

        return logger

    def _make_request(self, method: str, params: dict = None) -> dict | None:
        """Makes a request to the Telegram API."""
        if not self.token:
            self.logger.error("Bot token not configured. Add TELEGRAM_BOT_TOKEN to your .env")
            return None

        url = f"{self.base_url}{self.token}/{method}"

        try:
            response = requests.post(url, json=params, timeout=10)
            response.raise_for_status()
            result = response.json()

            if not result.get('ok'):
                self.logger.error(f"Telegram API error: {result.get('description')}")
                return None

            return result.get('result')

        except requests.exceptions.RequestException as e:
            self.logger.error(f"HTTP request error: {e}")
            return None
        except json.JSONDecodeError as e:
            self.logger.error(f"Error decoding JSON response: {e}")
            return None

    def send_windchill_notification(self, chat_id: str, station_name: str,
                                   windchill: float, temperature: float,
                                   date: str = None) -> bool:
        """
        Sends a wind chill notification.

        Args:
            chat_id: User ID
            station_name: Weather station name
            windchill: Wind chill in °C
            temperature: Actual temperature in °C
            date: Forecast date (optional)

        Returns:
            bool: True if sent successfully
        """
        if date is None:
            date = datetime.now().strftime("%d/%m/%Y")

        # Determine emoji based on wind chill
        if windchill < 5:
            emoji = "❄️"
            advice = "Bundle up, it's very cold!"
        elif windchill < 15:
            emoji = "🌬️"
            advice = "Wear a jacket, it's chilly."
        elif windchill < 25:
            emoji = "😊"
            advice = "Pleasant weather, enjoy it!"
        else:
            emoji = "🔥"
            advice = "It's hot, stay hydrated!"

        # Format differences
        difference = windchill - temperature
        diff_text = f"{difference:+.1f}°C" if difference != 0 else "same"

        # Create formatted message
        message = f"""
            <b>🌡️ Wind Chill Notification</b>

            📍 <b>Station:</b> {station_name}
            📅 <b>Date:</b> {date}
            🕗 <b>Time:</b> 07:00 AM

            🌡️ <b>Actual temperature:</b> {temperature:.1f}°C
            🎚️ <b>Wind chill:</b> {windchill:.1f}°C {emoji}
            📊 <b>Difference:</b> {diff_text}

            💡 <b>Tip:</b> {advice}

            <i>Automated notification from the weather system.</i>
        """

        return self.send_message(chat_id, message)

    def get_bot_info(self) -> dict | None:
        """Gets information about the bot."""
        return self._make_request('getMe')

    def test_connection(self) -> bool:
        """Tests connection with the Telegram API."""
        info = self.get_bot_info()
        if info:
            bot_name = info.get('first_name', 'Unknown')
            bot_username = info.get('username', 'Unknown')
            self.logger.info(f"✅ Successful connection with bot: {bot_name} (@{bot_username})")
            return True
        else:
            self.logger.error("❌ Could not connect to Telegram bot")
            return False

    def send_message(self, chat_id: str, text: str, parse_mode: str = "HTML") -> bool:
        params = {
            'chat_id': chat_id,
            'text': text,
            'parse_mode': parse_mode
        }

        result = self._make_request('sendMessage', params)
        return result is not None
