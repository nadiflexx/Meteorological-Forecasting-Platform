"""
Streamlit page for the Thermal Comfort / Clothing Recommendation Form.
Allows users to subscribe to daily Telegram alerts based on Real Feel temperature.
"""

from datetime import datetime
import json
import os
import time

import pandas as pd
import streamlit as st
from utils.data_loader import (
    apply_custom_css,
    inject_page_css,
    load_rainbow_predictions,
)

from pipelines.actions.telegram import TelegramBotSender
from src.config.settings import STATION_COORDS, TELEGRAM_REDIRECT, FileNames, Paths

SUBSCRIPTIONS_PATH = Paths.TELEGRAM / FileNames.SUBSCRIPTIONS_FILE
today = pd.to_datetime("today").normalize() - pd.DateOffset(years=1)

# Page configuration
st.set_page_config(
    page_title="What Should I Wear?",
    page_icon=Paths.ASSETS / FileNames.LOGO,
    layout="centered",
)


# --- 1. AUXILIARY FUNCTIONS ---
def load_subscriptions():
    if os.path.exists(SUBSCRIPTIONS_PATH):
        try:
            with open(SUBSCRIPTIONS_PATH, encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return []
    return []


def save_subscriptions(subscriptions):
    try:
        with open(SUBSCRIPTIONS_PATH, "w", encoding="utf-8") as f:
            json.dump(subscriptions, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        st.error(f"Error saving subscriptions: {e}")
        return False


def add_subscription(telegram_id, station_code, station_name):
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
    return STATION_COORDS.get(code, {}).get("name", code)


def clear_form_state():
    """Clears session state to reset the form."""
    if "submitted_data" in st.session_state:
        del st.session_state.submitted_data
    if "submit_completed" in st.session_state:
        del st.session_state.submit_completed


# --- 2. Streamlit CSS & Setup ---
apply_custom_css()
inject_page_css()

# --- 3. GATEKEEPER LOGIC ---
df = load_rainbow_predictions()
has_data = False

if df is not None:
    df["fecha_dt"] = pd.to_datetime(df["fecha"])
    if not df[df["fecha_dt"] == today].empty:
        has_data = True

if not has_data:
    st.markdown("<br><br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.error("⛔ **Service Unavailable**")
        st.info(
            "The clothing recommendation service is temporarily paused "
            "because there is no forecast data available for today."
        )
        if st.button("⬅️ Back to Dashboard"):
            st.switch_page("main.py")
    st.stop()

# --- 4. STATE MANAGEMENT ---
if "submitted_data" not in st.session_state:
    st.session_state.submitted_data = None


def handle_submit():
    input_value = st.session_state.get("input_field", "")
    dropdown_value = st.session_state.get("dropdown_field", "")

    if not input_value or not dropdown_value:
        st.warning("⚠️ Please complete all fields.")
        return False

    telegram_id = input_value.strip()
    station_code = dropdown_value
    station_name = _get_station_name(station_code)

    if not telegram_id.isdigit():
        st.warning("⚠️ Telegram ID must contain only numbers.")
        return False

    success, updated_subscriptions = add_subscription(
        telegram_id, station_code, station_name
    )

    if success:
        st.session_state.subscriptions = updated_subscriptions
        st.session_state.submit_completed = True
        st.session_state.redirect_link = TELEGRAM_REDIRECT
        return True
    else:
        st.error("❌ Error saving subscription.")
        return False


# --- 5. UI LAYOUT ---

# Main Title
st.markdown(
    "<h1 style='text-align: center;'>🧥 What Should I Wear Today?</h1>",
    unsafe_allow_html=True,
)
st.markdown(
    "<p style='text-align: center; color: #555; font-size: 1.1em;'>"
    "Get daily clothing recommendations based on the <b>Real Feel</b> temperature, "
    "calculated from wind, humidity, and forecast."
    "</p>",
    unsafe_allow_html=True,
)

st.markdown("---")

# Weather sensation cards
st.markdown("#### 🤖 How the Bot Helps You")

col_cold, col_mild, col_hot = st.columns(3)

with col_cold:
    st.markdown(
        """
        <div class="weather-card card-cold">
            <span class="emoji-icon">❄️</span>
            <span class="card-title">Wind Chill</span>
            <span class="card-desc">
                When it's windy & cold.<br>
                <b>Bot says:</b> "Bundle up!" or "Wear a jacket."
            </span>
        </div>
    """,
        unsafe_allow_html=True,
    )

with col_mild:
    st.markdown(
        """
        <div class="weather-card card-mild">
            <span class="emoji-icon">😊</span>
            <span class="card-title">Pleasant</span>
            <span class="card-desc">
                When conditions are ideal.<br>
                <b>Bot says:</b> "Enjoy the weather!"
            </span>
        </div>
    """,
        unsafe_allow_html=True,
    )

with col_hot:
    st.markdown(
        """
        <div class="weather-card card-hot">
            <span class="emoji-icon">🥵</span>
            <span class="card-title">Heat Index</span>
            <span class="card-desc">
                When humidity rises.<br>
                <b>Bot says:</b> "Stay hydrated & cool."
            </span>
        </div>
    """,
        unsafe_allow_html=True,
    )

st.markdown("<br>", unsafe_allow_html=True)

# Two-column Layout: Instructions (Left) and Form (Right)
col_info, col_form = st.columns([1, 1.5], gap="large")

with col_info:
    st.subheader("📱 Setup Instructions")

    st.markdown(
        """
    <div class="info-box">
        <b>1. Get your ID:</b><br>
        Open Telegram and search for <code>@userinfobot</code>. It will give you a number.<br><br>
        <b>2. Subscribe below:</b><br>
        Enter that number and choose your city.<br><br>
        <b>3. Receive Advice:</b><br>
        Every morning at 07:00 AM, we calculate the <i>Real Feel</i> and tell you what to wear.
    </div>
    """,
        unsafe_allow_html=True,
    )

    st.markdown("<br>", unsafe_allow_html=True)
    st.info(
        "💡 We use **Wind Speed** for cold days and **Humidity** for hot days to calculate the perfect thermal sensation."
    )


with col_form:
    st.subheader("🔔 Subscribe")

    # Form Container
    with st.container():
        with st.form("subscription_form", clear_on_submit=False):
            st.text_input(
                "🆔 Telegram ID",
                key="input_field",
                placeholder="e.g. 123456789",
                help="The number you got from @userinfobot",
            )

            # Create options (Name first, code second)
            station_options = {
                code: f"{_get_station_name(code)} ({code})"
                for code in df["indicativo"].unique()
            }

            st.selectbox(
                "📍 Select Location",
                options=sorted(
                    station_options.keys(), key=lambda x: station_options[x]
                ),
                format_func=lambda x: station_options[x],
                key="dropdown_field",
                help="Select the weather station closest to you.",
            )

            st.markdown("<br>", unsafe_allow_html=True)
            submitted = st.form_submit_button(
                "🧥 Activate Daily Recommendations", type="primary"
            )

        if submitted:
            handle_submit()

# --- 6. POST SUBMISSION ACTIONS ---
if st.session_state.get("submit_completed", False):
    st.markdown("---")

    # Success container
    with st.container():
        col_ok_1, col_ok_2, col_ok_3 = st.columns([1, 2, 1])
        with col_ok_2:
            st.success("✅ Subscription Successful!")
            st.balloons()

            link = st.session_state.get("redirect_link", TELEGRAM_REDIRECT)

            # Stylized HTML Button for Telegram
            st.markdown(
                f"""
                <div style="text-align: center; margin-top: 20px;">
                    <p style="margin-bottom: 10px; color: #555;">
                        Click below to open the bot and verify the connection:
                    </p>
                    <a href="{link}" target="_blank" style="text-decoration: none;">
                        <button style="
                            background-color: #0088cc;
                            color: white;
                            padding: 14px 30px;
                            border: none;
                            border-radius: 50px;
                            font-size: 16px;
                            font-weight: bold;
                            cursor: pointer;
                            box-shadow: 0 4px 10px rgba(0, 136, 204, 0.3);
                            display: flex; align-items: center; justify-content: center; margin: 0 auto; gap: 10px;
                            transition: transform 0.2s;
                        ">
                            <span style="font-size: 20px;">🤖</span> Open Telegram Bot
                        </button>
                    </a>
                </div>
                """,
                unsafe_allow_html=True,
            )

            # --- BOT NOTIFICATION LOGIC ---
            # We use a secondary spinner.
            # NOTE: We check if we already sent the test to avoid loops on refresh
            # But since user wants to "clean data", we provide a reset button below.

            with st.spinner("Sending a test notification..."):
                time.sleep(1)  # UX Delay
                bot = TelegramBotSender()

                # Only try to send if we have a successful connection
                if bot.test_connection():
                    with open(SUBSCRIPTIONS_PATH, encoding="utf-8") as f:
                        subscriptions = json.load(f)
                        if subscriptions:
                            current_id = st.session_state.get("input_field", "").strip()
                            # Find the subscription we just made
                            my_sub = next(
                                (
                                    s
                                    for s in reversed(subscriptions)
                                    if s["telegram_id"] == current_id
                                ),
                                None,
                            )

                            if my_sub:
                                filtered = df[
                                    df["indicativo"] == my_sub["station_code"]
                                ]
                                if not filtered.empty:
                                    row = filtered.iloc[0]

                                    # Send the message
                                    bot.send_windchill_notification(
                                        chat_id=my_sub["telegram_id"],
                                        station_name=my_sub["station_name"],
                                        windchill=row.get("pred_windchill"),
                                        temperature=row.get("pred_tmed"),
                                        date=datetime.now().strftime("%d/%m/%Y"),
                                    )

            st.markdown("<br>", unsafe_allow_html=True)

            # --- RESET BUTTON ---
            # This allows the user to clear the form and state manually
            if st.button("🔄 Add Another / Clear Form"):
                clear_form_state()
                st.rerun()

st.markdown(
    "<br><br><div style='text-align: center; color: #aaa; font-size: 0.8rem;'>"
    "✨ Thermal Comfort Engine | v2.2"
    "</div>",
    unsafe_allow_html=True,
)
