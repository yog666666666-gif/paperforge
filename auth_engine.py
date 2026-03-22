"""
auth_engine.py — WhatsApp OTP Authentication
=============================================
India-first. Everyone has WhatsApp.
No email required. Phone number = identity.
OTP via WhatsApp REST API (Meta Business).
Supabase stores users + sessions.
Zero dependency on email providers.
"""

import os, random, hashlib, datetime, time
import streamlit as st

# ── Supabase client ────────────────────────────────────────
def _sb():
    try:
        from supabase import create_client
        url = os.environ.get("SUPABASE_URL","")
        key = os.environ.get("SUPABASE_ANON_KEY","")
        if url and key:
            return create_client(url, key)
    except Exception:
        pass
    return None

# ── WhatsApp sender ────────────────────────────────────────
def _send_whatsapp_otp(phone: str, otp: str, name: str = "") -> bool:
    """Send OTP via WhatsApp Business API. Returns True on success."""
    key = os.environ.get("WHATSAPP_API_KEY","")
    pid = os.environ.get("WHATSAPP_PHONE_ID","")
    if not key or not pid:
        # Dev mode — show OTP in UI
        return False

    import requests
    clean = "".join(c for c in phone if c.isdigit())
    if len(clean) == 10:
        clean = "91" + clean
    if not clean.startswith("91"):
        clean = "91" + clean.lstrip("0")

    greeting = f"Hi {name.split()[0]}," if name else "Hi,"
    message  = (
        f"{greeting}\n\n"
        f"Your PaperForge AI verification code is:\n\n"
        f"*{otp}*\n\n"
        f"Valid for 10 minutes. Do not share this code.\n\n"
        f"If you did not request this, ignore this message.\n"
        f"— PaperForge AI, Pune"
    )

    try:
        r = requests.post(
            f"https://graph.facebook.com/v19.0/{pid}/messages",
            headers={"Authorization": f"Bearer {key}",
                     "Content-Type": "application/json"},
            json={"messaging_product": "whatsapp",
                  "to": clean, "type": "text",
                  "text": {"body": message}},
            timeout=10)
        return r.status_code == 200
    except Exception:
        return False


def _generate_otp() -> str:
    return str(random.randint(100000, 999999))


def _hash_phone(phone: str) -> str:
    clean = "".join(c for c in phone if c.isdigit())
    if len(clean) == 10:
        clean = "91" + clean
    return hashlib.sha256(clean.encode()).hexdigest()


def _save_otp(phone_hash: str, otp: str):
    """Store OTP with 10-minute expiry."""
    sb = _sb()
    expires = (datetime.datetime.utcnow() +
               datetime.timedelta(minutes=10)).isoformat() + "Z"
    if sb:
        try:
            sb.table("otp_store").upsert({
                "phone_hash": phone_hash,
                "otp":        hashlib.sha256(otp.encode()).hexdigest(),
                "expires_at": expires,
            }).execute()
        except Exception:
            pass
    # Also store in session for dev mode
    st.session_state["_dev_otp"]    = otp
    st.session_state["_otp_hash"]   = phone_hash
    st.session_state["_otp_expiry"] = time.time() + 600


def _verify_otp(phone_hash: str, otp_input: str) -> bool:
    """Verify OTP. Returns True if valid and not expired."""
    otp_hash = hashlib.sha256(otp_input.strip().encode()).hexdigest()
    sb = _sb()
    if sb:
        try:
            r = (sb.table("otp_store")
                 .select("otp,expires_at")
                 .eq("phone_hash", phone_hash)
                 .execute())
            if r.data:
                row = r.data[0]
                now = datetime.datetime.utcnow().isoformat() + "Z"
                if row["otp"] == otp_hash and row["expires_at"] > now:
                    # Delete after use
                    sb.table("otp_store")\
                      .delete().eq("phone_hash", phone_hash).execute()
                    return True
        except Exception:
            pass
    # Dev mode fallback
    dev_otp    = st.session_state.get("_dev_otp","")
    dev_expiry = st.session_state.get("_otp_expiry", 0)
    if dev_otp and time.time() < dev_expiry:
        return otp_input.strip() == dev_otp
    return False


def _get_or_create_user(phone: str, name: str,
                          plan: str, country: str = "India") -> dict:
    """Get existing user or create new one. Returns user dict."""
    phone_hash = _hash_phone(phone)
    clean      = "91" + "".join(c for c in phone if c.isdigit())[-10:]
    sb         = _sb()

    if sb:
        try:
            r = (sb.table("users")
                 .select("*")
                 .eq("phone_hash", phone_hash)
                 .execute())
            if r.data:
                user = r.data[0]
                # Update last login
                sb.table("users").update({
                    "last_login": datetime.datetime.utcnow().isoformat()+"Z"
                }).eq("phone_hash", phone_hash).execute()
                return user
        except Exception:
            pass

        # Create new user
        plan_prices = {"Basic": 999, "Medium": 1999, "Advanced": 4999}
        new_user = {
            "phone_hash":  phone_hash,
            "phone_last4": clean[-4:],
            "name":        name,
            "plan":        plan,
            "plan_price":  plan_prices.get(plan, 999),
            "country":     country,
            "created_at":  datetime.datetime.utcnow().isoformat()+"Z",
            "last_login":  datetime.datetime.utcnow().isoformat()+"Z",
            "msata_signed": False,
            "scaffolds_generated": 0,
            "scaffolds_remaining": 1,  # one per purchase
            "active": True,
        }
        try:
            r = sb.table("users").insert(new_user).execute()
            if r.data:
                return r.data[0]
        except Exception:
            pass

    # Memory fallback for dev
    return {
        "phone_hash": phone_hash,
        "name": name,
        "plan": plan,
        "scaffolds_remaining": 1,
        "msata_signed": False,
        "dev_mode": True,
    }


def _log_scaffold_use(phone_hash: str):
    """Decrement scaffold count and log use."""
    sb = _sb()
    if sb:
        try:
            r = (sb.table("users").select("scaffolds_remaining,scaffolds_generated")
                 .eq("phone_hash", phone_hash).execute())
            if r.data:
                remaining  = max(0, r.data[0].get("scaffolds_remaining", 1) - 1)
                generated  = r.data[0].get("scaffolds_generated", 0) + 1
                sb.table("users").update({
                    "scaffolds_remaining":  remaining,
                    "scaffolds_generated":  generated,
                    "last_scaffold_at": datetime.datetime.utcnow().isoformat()+"Z",
                }).eq("phone_hash", phone_hash).execute()
        except Exception:
            pass


# ══════════════════════════════════════════════════════════
# STREAMLIT AUTH COMPONENT
# ══════════════════════════════════════════════════════════

def render_auth_screen() -> bool:
    """
    Full auth flow: phone → OTP → plan selection → MSATA → enter app.
    Returns True when user is authenticated and ready to proceed.
    Sets st.session_state.user_id, user_name, user_plan, user_phone.
    """

    # Already authenticated this session
    if st.session_state.get("authenticated"):
        return True

    st.markdown(
        '<div style="text-align:center;padding:2rem 0 1rem">'
        '<div style="font-size:28px;font-weight:700;color:#3E2723">'
        'PaperForge AI</div>'
        '<div style="font-size:14px;color:#8D6E63;margin-top:4px">'
        'Academic Research Planner</div>'
        '</div>',
        unsafe_allow_html=True)

    auth_stage = st.session_state.get("auth_stage", "phone")

    # ── STAGE 1: Phone entry ─────────────────────────────────
    if auth_stage == "phone":
        st.markdown("### Sign In / Register")
        st.caption("Enter your WhatsApp number. We will send a 6-digit code.")

        with st.form("phone_form"):
            name  = st.text_input("Your Name *",
                                   placeholder="Dr. Priya Sharma",
                                   key="auth_name_input")
            phone = st.text_input("WhatsApp Number *",
                                   placeholder="98765 43210",
                                   key="auth_phone_input",
                                   help="10-digit Indian mobile number")
            plan  = st.selectbox("Select Your Plan *",
                                  ["Basic — ₹999 (1 scaffold)",
                                   "Medium — ₹1,999 (1 scaffold + diagrams)",
                                   "Advanced — ₹4,999 (1 scaffold, all features)"],
                                  key="auth_plan_input")
            country = st.selectbox("Country",
                                    ["India","UAE","USA","UK","Australia",
                                     "Canada","Singapore","Other"],
                                    key="auth_country_input")

            st.markdown(
                '<div style="background:#FFF8E7;border-left:3px solid #D97706;'
                'padding:0.6rem 1rem;border-radius:4px;font-size:12px;margin:0.5rem 0">'
                '⚖️ By proceeding you agree to be shown the MSATA agreement '
                'before your research scaffold is generated.</div>',
                unsafe_allow_html=True)

            submitted = st.form_submit_button(
                "Send WhatsApp OTP →", use_container_width=True)

        if submitted:
            clean_phone = "".join(c for c in phone if c.isdigit())
            if not name.strip():
                st.error("Please enter your name.")
            elif len(clean_phone) < 10:
                st.error("Enter a valid 10-digit mobile number.")
            else:
                otp        = _generate_otp()
                phone_hash = _hash_phone(clean_phone)
                sent       = _send_whatsapp_otp(clean_phone, otp, name)
                _save_otp(phone_hash, otp)

                plan_key = plan.split(" — ")[0]  # "Basic", "Medium", "Advanced"
                st.session_state["auth_name"]    = name.strip()
                st.session_state["auth_phone"]   = clean_phone
                st.session_state["auth_plan"]    = plan_key
                st.session_state["auth_country"] = country
                st.session_state["auth_stage"]   = "otp"

                if sent:
                    st.success(
                        f"OTP sent to WhatsApp +91{clean_phone[-10:]}. "
                        "Check your messages.")
                else:
                    # Dev mode — show OTP on screen
                    st.info(
                        f"WhatsApp API not configured. "
                        f"**Dev mode OTP: {otp}**  *(shown only in testing)*")
                st.rerun()

    # ── STAGE 2: OTP verification ────────────────────────────
    elif auth_stage == "otp":
        name  = st.session_state.get("auth_name","")
        phone = st.session_state.get("auth_phone","")
        plan  = st.session_state.get("auth_plan","Basic")

        st.markdown(f"### Verify Your WhatsApp")
        st.caption(
            f"OTP sent to +91{phone[-10:]}. "
            "Enter the 6-digit code below.")

        with st.form("otp_form"):
            otp_input = st.text_input(
                "6-Digit OTP *",
                max_chars=6,
                placeholder="Enter OTP",
                key="otp_input_field")
            col1, col2 = st.columns(2)
            verify_btn = col1.form_submit_button(
                "✅ Verify & Continue", use_container_width=True)
            resend_btn = col2.form_submit_button(
                "🔄 Resend OTP", use_container_width=True)

        if verify_btn:
            phone_hash = _hash_phone(phone)
            if _verify_otp(phone_hash, otp_input):
                # Create/fetch user
                country = st.session_state.get("auth_country","India")
                user    = _get_or_create_user(phone, name, plan, country)

                # Store in session
                st.session_state["authenticated"]  = True
                st.session_state["user_id"]        = user.get("phone_hash", phone_hash)
                st.session_state["user_name"]      = name
                st.session_state["user_phone"]     = phone
                st.session_state["user_plan"]      = plan
                st.session_state["user_country"]   = country
                st.session_state["msata_signed"]   = user.get("msata_signed", False)
                st.session_state["scaffolds_remaining"] = user.get("scaffolds_remaining", 1)
                st.session_state["auth_stage"]     = "done"
                st.session_state["tier"]           = plan

                # WhatsApp welcome
                _send_whatsapp_otp.__wrapped__ if hasattr(
                    _send_whatsapp_otp, '__wrapped__') else None
                _welcome_whatsapp(phone, name, plan)
                st.rerun()
            else:
                st.error("Invalid or expired OTP. Try again or resend.")

        if resend_btn:
            otp        = _generate_otp()
            phone_hash = _hash_phone(phone)
            sent       = _send_whatsapp_otp(phone, otp,
                                             st.session_state.get("auth_name",""))
            _save_otp(phone_hash, otp)
            if sent:
                st.success("OTP resent to WhatsApp.")
            else:
                st.info(f"Dev mode OTP: **{otp}**")

        if st.button("← Change number"):
            st.session_state["auth_stage"] = "phone"
            st.rerun()

    return st.session_state.get("authenticated", False)


def _welcome_whatsapp(phone: str, name: str, plan: str):
    """Send welcome message after successful login."""
    key = os.environ.get("WHATSAPP_API_KEY","")
    pid = os.environ.get("WHATSAPP_PHONE_ID","")
    if not key or not pid:
        return
    try:
        import requests
        clean = "91" + "".join(c for c in phone if c.isdigit())[-10:]
        plan_desc = {
            "Basic":    "1 Research Scaffold (Basic)",
            "Medium":   "1 Research Scaffold (Medium) with Diagrams",
            "Advanced": "1 Research Scaffold (Advanced) — Full Features",
        }.get(plan, plan)
        requests.post(
            f"https://graph.facebook.com/v19.0/{pid}/messages",
            headers={"Authorization": f"Bearer {key}",
                     "Content-Type": "application/json"},
            json={"messaging_product": "whatsapp",
                  "to": clean, "type": "text",
                  "text": {"body": (
                      f"Welcome to PaperForge AI, {name.split()[0]}!\n\n"
                      f"Your plan: {plan_desc}\n\n"
                      f"Zero hallucination policy. Real citations only. "
                      f"Start your research scaffold now.\n\n"
                      f"— PaperForge AI, Pune"
                  )}},
            timeout=8)
    except Exception:
        pass


def render_user_badge():
    """Show logged-in user in sidebar."""
    if st.session_state.get("authenticated"):
        name  = st.session_state.get("user_name","")
        plan  = st.session_state.get("user_plan","Basic")
        rem   = st.session_state.get("scaffolds_remaining",1)
        st.sidebar.markdown(
            f'<div style="background:#F5F0E8;border-radius:8px;'
            f'padding:10px 14px;margin-bottom:12px;font-size:13px">'
            f'👤 <strong>{name}</strong><br>'
            f'Plan: {plan} &nbsp;|&nbsp; Scaffolds left: {rem}</div>',
            unsafe_allow_html=True)
        if st.sidebar.button("Sign Out", key="signout_btn"):
            for k in ["authenticated","user_id","user_name","user_phone",
                      "user_plan","auth_stage","msata_signed",
                      "scaffolds_remaining"]:
                st.session_state.pop(k, None)
            st.rerun()


# ══════════════════════════════════════════════════════════
# SUPABASE TABLE SQL — run once in Supabase SQL editor
# ══════════════════════════════════════════════════════════
SUPABASE_SETUP_SQL = """
-- Run this once in your Supabase SQL editor

CREATE TABLE IF NOT EXISTS users (
    id                   UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    phone_hash           TEXT UNIQUE NOT NULL,
    phone_last4          TEXT,
    name                 TEXT,
    plan                 TEXT DEFAULT 'Basic',
    plan_price           INTEGER DEFAULT 999,
    country              TEXT DEFAULT 'India',
    created_at           TIMESTAMPTZ DEFAULT now(),
    last_login           TIMESTAMPTZ DEFAULT now(),
    last_scaffold_at     TIMESTAMPTZ,
    msata_signed         BOOLEAN DEFAULT false,
    msata_contract_id    TEXT,
    scaffolds_generated  INTEGER DEFAULT 0,
    scaffolds_remaining  INTEGER DEFAULT 1,
    active               BOOLEAN DEFAULT true
);

CREATE TABLE IF NOT EXISTS otp_store (
    phone_hash  TEXT PRIMARY KEY,
    otp         TEXT NOT NULL,
    expires_at  TIMESTAMPTZ NOT NULL,
    created_at  TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS scaffolds (
    id             UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id        TEXT REFERENCES users(phone_hash),
    topic          TEXT,
    plan           TEXT,
    word_count     INTEGER,
    domain         TEXT,
    methodology    TEXT,
    created_at     TIMESTAMPTZ DEFAULT now(),
    msata_contract TEXT,
    metadata       JSONB
);

CREATE TABLE IF NOT EXISTS msata_logs (
    id              UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id         TEXT,
    contract_id     TEXT UNIQUE,
    scaffold_topic  TEXT,
    ip_address      TEXT,
    signed_at       TIMESTAMPTZ DEFAULT now(),
    forensic_json   JSONB
);

-- Enable Row Level Security
ALTER TABLE users      ENABLE ROW LEVEL SECURITY;
ALTER TABLE otp_store  ENABLE ROW LEVEL SECURITY;
ALTER TABLE scaffolds  ENABLE ROW LEVEL SECURITY;
ALTER TABLE msata_logs ENABLE ROW LEVEL SECURITY;
"""
