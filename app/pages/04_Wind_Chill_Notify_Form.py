"""
Streamlit page for the Wind Chill Notification Form.
Allows users to subscribe to daily Telegram alerts.
"""

from datetime import datetime
import json
import os
import time

import pandas as pd
import streamlit as st
from utils.data_loader import apply_custom_css, load_rainbow_predictions

from pipelines.actions.telegram import TelegramBotSender
from src.config.settings import STATION_COORDS, TELEGRAM_REDIRECT, FileNames, Paths

SUBSCRIPTIONS_PATH = Paths.TELEGRAM / FileNames.SUBSCRIPTIONS_FILE
today = pd.to_datetime("today").normalize() - pd.DateOffset(years=1)

# Page configuration
st.set_page_config(page_title="Telegram Form", page_icon="📋", layout="centered")
apply_custom_css()

# --- GATEKEEPER LOGIC ---
# Check if valid data exists before rendering the form.
df = load_rainbow_predictions()
has_data = False

if df is not None:
    df["fecha_dt"] = pd.to_datetime(df["fecha"])
    # Check if there is data for the target date
    if not df[df["fecha_dt"] == today].empty:
        has_data = True

if not has_data:
    st.error("⛔ **Service Unavailable**")
    st.warning(
        "The Wind Chill Notification service is currently disabled because "
        "there is no forecast data available for the current date."
    )
    if st.button("⬅️ Back to Dashboard"):
        st.switch_page("main.py")
    st.stop()  # Stops execution here if no data

# --- DATA IS AVAILABLE, RENDER FORM ---

st.title("Daily Wind Chill Notification")


def load_subscriptions():
    """Loads subscriptions from the JSON file."""
    if os.path.exists(SUBSCRIPTIONS_PATH):
        try:
            with open(SUBSCRIPTIONS_PATH, encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return []
    return []


def save_subscriptions(subscriptions):
    """Saves subscriptions to the JSON file."""
    try:
        with open(SUBSCRIPTIONS_PATH, "w", encoding="utf-8") as f:
            json.dump(subscriptions, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        st.error(f"Error saving subscriptions: {e}")
        return False


def add_subscription(telegram_id, station_code, station_name):
    """Adds or updates a subscription in the JSON file."""
    subscriptions = load_subscriptions()
    subscription_exists = False

    for sub in subscriptions:
        if sub["telegram_id"] == telegram_id:
            sub["station_code"] = station_code
            sub["station_name"] = station_name
            sub["updated_at"] = datetime.now().isoformat()
            subscription_exists = True
            break

    if not subscription_exists:
        new_subscription = {
            "telegram_id": telegram_id,
            "station_code": station_code,
            "station_name": station_name,
            "active": True,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
        }
        subscriptions.append(new_subscription)

    if save_subscriptions(subscriptions):
        return True, subscriptions
    return False, subscriptions


def _get_station_name(code: str) -> str:
    """Retrieves friendly name from settings."""
    return STATION_COORDS.get(code, {}).get("name", code)


# Initialize session state
if "submitted_data" not in st.session_state:
    st.session_state.submitted_data = None
if "subscriptions" not in st.session_state:
    st.session_state.subscriptions = []


def handle_submit():
    """Validates and processes the form submission."""
    input_value = st.session_state.get("input_field", "")
    dropdown_value = st.session_state.get("dropdown_field", "")

    if not input_value or not dropdown_value:
        st.error("⚠️ Please complete all fields")
        return False

    telegram_id = input_value.strip()
    station_code = dropdown_value
    station_name = _get_station_name(station_code)

    if not telegram_id.isdigit():
        st.error("⚠️ Telegram ID must contain only numbers")
        return False

    success, updated_subscriptions = add_subscription(
        telegram_id, station_code, station_name
    )

    if success:
        st.session_state.subscriptions = updated_subscriptions
        st.session_state.last_submitted = {
            "telegram_id": telegram_id,
            "station_code": station_code,
            "station_name": station_name,
            "timestamp": datetime.now().isoformat(),
        }
        st.session_state.submit_completed = True
        st.session_state.redirect_link = TELEGRAM_REDIRECT
        st.success("✅ Subscription saved successfully!")
        return True
    else:
        st.error("❌ Error saving subscription")
        return False


# --- FORM UI ---
with st.form("subscription_form"):
    st.subheader("Configure your daily notification")

    st.text_input(
        "Telegram ID:",
        key="input_field",
        placeholder="0123456789",
        help="Your numerical Telegram ID (not your username)",
    )

    station_options = {
        code: f"{code} - {_get_station_name(code)}"
        for code in df["indicativo"].unique()
    }

    st.selectbox(
        "Select Station:",
        options=sorted(station_options.keys()),
        format_func=lambda x: station_options[x],
        key="dropdown_field",
        help="Choose the weather station for which you want to receive notifications",
    )

    if st.form_submit_button("🚀 Subscribe", type="primary"):
        submit_success = handle_submit()
        if submit_success:
            st.session_state.should_clear_input = True

# --- POST SUBMISSION ACTIONS ---
if st.session_state.get("submit_completed", False):
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        link = st.session_state.get("redirect_link", TELEGRAM_REDIRECT)
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
            unsafe_allow_html=True,
        )

        # NOTE: Sending the notification immediately might slow down the UI.
        # Ideally, this should be handled by a background worker.
        time.sleep(1)  # Small delay for UX
        bot = TelegramBotSender()

        if bot.test_connection():
            # Retrieve the last added subscription to verify/test
            with open(SUBSCRIPTIONS_PATH, encoding="utf-8") as f:
                subscriptions = json.load(f)
                if subscriptions:
                    last_sub = subscriptions[-1]

                    # Filter data for the subscribed station
                    filtered = df[df["indicativo"] == last_sub["station_code"]]

                    if not filtered.empty:
                        row = filtered.iloc[0]
                        bot.send_windchill_notification(
                            chat_id=last_sub["telegram_id"],
                            station_name=last_sub["station_name"],
                            windchill=row.get("pred_windchill"),
                            temperature=row.get("pred_tmed"),
                        )

st.markdown("---")
with st.expander("📱 How to get my Telegram ID?"):
    st.markdown("""
    1. Open Telegram.
    2. Search for `@userinfobot`.
    3. Start the chat to receive your **numerical ID**.
    """)

st.caption("✨ Wind Chill Notification System | Version 1.0")
