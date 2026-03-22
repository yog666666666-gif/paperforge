"""
otp_engine.py — OTP Verification for MSATA
===========================================
Primary: MSG91 (Indian SMS OTP - cheapest, most reliable)
Fallback: Email OTP via SMTP
Cost: MSG91 ~₹0.15 per SMS. Email free.
"""

import os
import random
import string
import hashlib
import time
from typing import Tuple, Optional
import streamlit as st

OTP_EXPIRY_SECONDS = 300  # 5 minutes
OTP_LENGTH = 6


def generate_otp() -> str:
    return ''.join(random.choices(string.digits, k=OTP_LENGTH))


def hash_otp(otp: str, salt: str) -> str:
    return hashlib.sha256(f"{otp}{salt}".encode()).hexdigest()


def send_sms_otp_msg91(phone: str, otp: str) -> Tuple[bool, str]:
    """Send OTP via MSG91. Requires MSG91_API_KEY and MSG91_TEMPLATE_ID in secrets."""
    try:
        import requests
        api_key     = os.environ.get("MSG91_API_KEY", "")
        template_id = os.environ.get("MSG91_TEMPLATE_ID", "")
        if not api_key:
            return False, "MSG91 key not configured"

        # Clean phone number
        phone_clean = phone.strip().replace(" ", "").replace("-", "")
        if not phone_clean.startswith("91"):
            phone_clean = "91" + phone_clean.lstrip("0+")

        payload = {
            "template_id": template_id,
            "mobile":      phone_clean,
            "authkey":     api_key,
            "otp":         otp,
        }
        r = requests.post(
            "https://control.msg91.com/api/v5/otp",
            json=payload, timeout=10
        )
        if r.status_code == 200:
            return True, "OTP sent via SMS"
        return False, f"MSG91 error: {r.text[:100]}"
    except Exception as e:
        return False, str(e)


def send_email_otp(email: str, otp: str, user_name: str = "") -> Tuple[bool, str]:
    """Send OTP via email. Requires SMTP_HOST, SMTP_USER, SMTP_PASS in secrets."""
    try:
        import smtplib
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart

        host = os.environ.get("SMTP_HOST", "smtp.gmail.com")
        port = int(os.environ.get("SMTP_PORT", "587"))
        user = os.environ.get("SMTP_USER", "")
        pwd  = os.environ.get("SMTP_PASS", "")

        if not user or not pwd:
            return False, "SMTP not configured"

        msg = MIMEMultipart()
        msg['From']    = f"PaperForge AI <{user}>"
        msg['To']      = email
        msg['Subject'] = f"PaperForge AI — Your OTP: {otp}"

        body = f"""Dear {user_name or 'Researcher'},

Your OTP for PaperForge AI MSATA verification is:

    {otp}

This OTP is valid for 5 minutes.

Do not share this OTP with anyone.

— PaperForge AI Team
Pune, Maharashtra

This is an automated message. Do not reply."""

        msg.attach(MIMEText(body, 'plain'))
        with smtplib.SMTP(host, port) as server:
            server.starttls()
            server.login(user, pwd)
            server.send_message(msg)
        return True, "OTP sent via email"
    except Exception as e:
        return False, str(e)


def send_otp(contact: str, otp: str, method: str = "auto",
              user_name: str = "") -> Tuple[bool, str]:
    """
    Send OTP via best available method.
    method: "sms" | "email" | "auto"
    auto: tries SMS first, falls back to email
    """
    is_phone = contact.replace("+","").replace(" ","").replace("-","").isdigit()
    is_email = "@" in contact

    if method == "sms" or (method == "auto" and is_phone):
        ok, msg = send_sms_otp_msg91(contact, otp)
        if ok:
            return True, msg
        # Fallback to email if phone given but SMS failed
        if is_email:
            return send_email_otp(contact, otp, user_name)
        return False, f"SMS failed: {msg}. No email fallback available."

    if method == "email" or (method == "auto" and is_email):
        return send_email_otp(contact, otp, user_name)

    return False, "Could not determine contact method (provide phone or email)"


def render_otp_verification(contact: str, user_name: str = "",
                              session_key: str = "msata_otp") -> bool:
    """
    Render OTP verification UI.
    Returns True if verified successfully.
    """
    otp_state = st.session_state.get(session_key, {})

    # Not sent yet
    if not otp_state.get("sent"):
        method = "SMS" if contact.replace("+","").replace(" ","").isdigit() else "Email"

        st.markdown(f"**Verify your {method}:** `{contact}`")

        if st.button(f"📱 Send OTP to {contact}", use_container_width=True):
            otp      = generate_otp()
            salt     = os.urandom(16).hex()
            otp_hash = hash_otp(otp, salt)

            ok, msg = send_otp(contact, otp, user_name=user_name)

            if ok:
                st.session_state[session_key] = {
                    "sent":      True,
                    "hash":      otp_hash,
                    "salt":      salt,
                    "expires":   time.time() + OTP_EXPIRY_SECONDS,
                    "attempts":  0,
                    "verified":  False,
                    "contact":   contact,
                }
                st.success(f"✅ OTP sent! Check your {method}.")
                st.rerun()
            else:
                # DEV MODE: show OTP if sending fails (remove in production)
                dev_mode = not os.environ.get("MSG91_API_KEY") and not os.environ.get("SMTP_USER")
                if dev_mode:
                    st.session_state[session_key] = {
                        "sent":     True,
                        "hash":     otp_hash,
                        "salt":     salt,
                        "expires":  time.time() + OTP_EXPIRY_SECONDS,
                        "attempts": 0,
                        "verified": False,
                        "contact":  contact,
                        "dev_otp":  otp,
                    }
                    st.warning(f"⚠️ DEV MODE (OTP service not configured): Your OTP is **{otp}**")
                    st.rerun()
                else:
                    st.error(f"Failed to send OTP: {msg}")
        return False

    # Already sent
    state = st.session_state[session_key]

    if state.get("verified"):
        st.markdown('<div class="ok-box">✅ Contact verified successfully.</div>',
                    unsafe_allow_html=True)
        return True

    # Check expiry
    if time.time() > state.get("expires", 0):
        st.error("OTP expired. Please request a new one.")
        if st.button("🔄 Request New OTP"):
            del st.session_state[session_key]
            st.rerun()
        return False

    # Show dev OTP if in dev mode
    if state.get("dev_otp"):
        st.info(f"🔧 DEV MODE — OTP: **{state['dev_otp']}**")

    remaining = int(state["expires"] - time.time())
    st.markdown(f"OTP sent to `{state['contact']}`. Expires in **{remaining}s**.")

    col1, col2 = st.columns([3, 1])
    otp_input = col1.text_input("Enter OTP", max_chars=6,
                                  placeholder="6-digit code",
                                  label_visibility="collapsed")

    if col2.button("Verify", use_container_width=True):
        attempts = state.get("attempts", 0) + 1
        st.session_state[session_key]["attempts"] = attempts

        if attempts > 5:
            st.error("Too many failed attempts. Request a new OTP.")
            del st.session_state[session_key]
            st.rerun()

        entered_hash = hash_otp(otp_input.strip(), state["salt"])
        if entered_hash == state["hash"]:
            st.session_state[session_key]["verified"] = True
            st.success("✅ Verified!")
            st.rerun()
        else:
            st.error(f"Incorrect OTP. {5 - attempts} attempts remaining.")

    if st.button("🔄 Resend OTP"):
        del st.session_state[session_key]
        st.rerun()

    return False
