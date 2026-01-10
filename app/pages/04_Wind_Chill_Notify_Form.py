from datetime import datetime
import json
import os
import sys
import time

import pandas as pd
import streamlit as st
from utils.data_loader import load_rainbow_predictions

sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from pipelines.actions.telegram import TelegramBotSender
from src.config.settings import STATION_COORDS

SUBSCRIPTIONS_FILE = "data/telegram_id/telegram_subscriptions.json"
today = pd.to_datetime("today").normalize() - pd.DateOffset(years=1)
# Page configuration
st.set_page_config(page_title="Telegram Form", page_icon="📋", layout="centered")

# Application title
st.title("Daily Wind Chill Notification")

def load_subscriptions():
    """Loads subscriptions from the JSON file."""
    if os.path.exists(SUBSCRIPTIONS_FILE):
        try:
            with open(SUBSCRIPTIONS_FILE, encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            # If the file is corrupt or empty, return empty list
            return []
    return []

def save_subscriptions(subscriptions):
    """Saves subscriptions to the JSON file."""
    try:
        with open(SUBSCRIPTIONS_FILE, 'w', encoding='utf-8') as f:
            json.dump(subscriptions, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        st.error(f"Error saving subscriptions: {e}")
        return False

def add_subscription(telegram_id, station_code, station_name):
    """Adds or updates a subscription in the JSON file."""
    subscriptions = load_subscriptions()

    # Check if subscription already exists for this Telegram ID
    subscription_exists = False
    for sub in subscriptions:
        if sub['telegram_id'] == telegram_id:
            # Update existing subscription
            sub['station_code'] = station_code
            sub['station_name'] = station_name
            sub['updated_at'] = datetime.now().isoformat()
            subscription_exists = True
            break

    if not subscription_exists:
        # Create new subscription
        new_subscription = {
            'telegram_id': telegram_id,
            'station_code': station_code,
            'station_name': station_name,
            'active': True,
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        }
        subscriptions.append(new_subscription)

    # Save to file
    if save_subscriptions(subscriptions):
        return True, subscriptions
    return False, subscriptions

def _get_station_name(code: str) -> str:
    """Retrieves friendly name from settings."""
    return STATION_COORDS.get(code, {}).get("name", code)

df = load_rainbow_predictions()

if df is None:
    st.error("⚠️ Data not available. Run the pipeline first.")
    st.stop()

df["fecha_dt"] = pd.to_datetime(df["fecha"])
df_today = df[df["fecha_dt"] == today].copy()


# Initialize session state
if 'submitted_data' not in st.session_state:
    st.session_state.submitted_data = None
if 'subscriptions' not in st.session_state:
    st.session_state.subscriptions = []

# Function to handle form submission
def handle_submit():
    # Get values directly to avoid problems with session_state
    input_value = st.session_state.get('input_field', '')
    dropdown_value = st.session_state.get('dropdown_field', '')

    # Check that both fields are not empty
    if not input_value or not dropdown_value:
        st.error("⚠️ Please complete all fields")
        return

    # Get and clean data
    telegram_id = input_value.strip()
    station_code = dropdown_value
    station_name = _get_station_name(station_code)

    # Validate that Telegram ID contains only numbers
    if not telegram_id.isdigit():
        st.error("⚠️ Telegram ID must contain only numbers")
        return

    # Save subscription to JSON file
    success, updated_subscriptions = add_subscription(telegram_id, station_code, station_name)

    if success:
        # Update session state
        st.session_state.subscriptions = updated_subscriptions
        st.session_state.last_submitted = {
            'telegram_id': telegram_id,
            'station_code': station_code,
            'station_name': station_name,
            'timestamp': datetime.now().isoformat()
        }

        # Mark that submit is completed (to show button later)
        st.session_state.submit_completed = True
        st.session_state.redirect_link = "https://t.me/P3G3Bot"

        # Show success message immediately
        st.success("✅ Subscription saved successfully!")

        # Do NOT clear st.session_state.input_field here - do it later

        # Return True to indicate success
        return True
    else:
        st.error("❌ Error saving subscription")
        return False


# --- MAIN FORM ---
with st.form("mi_formulario"):
    st.subheader("Configure your daily notification")

    # Text input field
    input_text = st.text_input(
        "Telegram ID:",
        key="input_field",
        placeholder="0123456789",
        help="Your numerical Telegram ID (not your username)"
    )

    # Station dropdown
    station_options = {
        code: f"{code} - {_get_station_name(code)}"
        for code in df["indicativo"].unique()
    }

    selected_code = st.selectbox(
        "Select Station:",
        options=sorted(station_options.keys()),
        format_func=lambda x: station_options[x],
        key="dropdown_field",
        help="Choose the weather station for which you want to receive notifications"
    )

    # Submit button inside the form
    col1, col2 = st.columns([1, 1])
    with col1:
        submit_button = st.form_submit_button(
            "🚀 Subscribe",
            type="primary"
        )


# Process form submission
# Process form submission when submit is pressed
if submit_button:
    submit_success = handle_submit()

    # If successful and we want to clear the field, use a flag
    if submit_success:
        st.session_state.should_clear_input = True



# Show redirect button if submit is completed
if st.session_state.get('submit_completed', False):
    # Large and attractive button
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        link = st.session_state.get('redirect_link', "https://default-link.com")

        # Use markdown to create a redirect button
        st.markdown(
            f"""
            <div style="text-align: center; margin: 20px 0;">
                <a href="{link}" target="_blank">
                    <button style="
                        background-color: #0088cc;
                        color: white;
                        padding: 15px 30px;
                        border: none;
                        border-radius: 10px;
                        font-size: 18px;
                        font-weight: bold;
                        cursor: pointer;
                        transition: background-color 0.3s;
                    ">
                        🤖 Go to Telegram
                    </button>
                </a>
            </div>
            """,
            unsafe_allow_html=True
        )
        time.sleep(120)
        bot = TelegramBotSender()

        if bot.test_connection():
            with open(SUBSCRIPTIONS_FILE, encoding='utf-8') as f:
                subscriptions = json.load(f)
                if subscriptions:
                    last_subscription = subscriptions[-1]
                    last_telegram_id = last_subscription['telegram_id']
                    last_station_name = last_subscription['station_name']
                    filtered = df[(df['indicativo'] == last_subscription['station_code'])]
                row = filtered.iloc[0]
                success = bot.send_windchill_notification(
                    chat_id=last_telegram_id,
                    station_name=last_station_name,
                    windchill=row.get('pred_windchill'),
                    temperature=row.get('pred_tmed')
                )


# --- USAGE INSTRUCTIONS ---
st.markdown("---")
with st.expander("📱 How to get my Telegram ID?"):
    st.markdown("""
    ### Steps to get your Telegram ID:

    1. **Open Telegram** on your device
    2. **In the search bar**, type: `@userinfobot`
    3. **Open the chat** with the bot
    4. **Press the "Start" button**
    5. **The bot will reply** with your numerical user ID

    ⚠️ **Important:** You need your **numerical ID** (e.g., 123456789), not your @username

    ### Notification features:
    - 📅 **Daily:** You will receive a notification every day
    - ⏰ **Fixed time:** At 7:00 AM local time
    - 🌡️ **Content:** Wind chill and actual temperature
    - 📍 **Localized:** Only for the station you select
    """)

# Footer note
st.markdown("---")
st.caption("✨ Wind Chill Notification System | Version 1.0")
