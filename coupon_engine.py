"""
coupon_engine.py — Simple Coupon Token System
==============================================
No credits. No arithmetic. One coupon = one use.
Coupons stored in Supabase. Admin adds them directly.
Tiers: Basic (₹999), Medium (₹1,999), Advanced (₹4,999)
"""

import os, hashlib, datetime
import streamlit as st

TIER_PRICES = {"Basic": 999, "Medium": 1999, "Advanced": 4999}
MAX_REGENS  = 2  # per section, all tiers

# What each tier can see
TIER_VISIBILITY = {
    "Basic": {
        "stats_levels":    ["Basic"],
        "diagram_toggle":  False,
        "csv_download":    False,
        "advanced_tab":    False,
        "patent_engine":   False,
        "section_regens":  2,
        "word_limit":      4000,
        "label":           "Basic",
    },
    "Medium": {
        "stats_levels":    ["Basic", "Medium"],
        "diagram_toggle":  True,
        "csv_download":    True,
        "advanced_tab":    False,
        "patent_engine":   False,
        "section_regens":  2,
        "word_limit":      5500,
        "label":           "Medium",
    },
    "Advanced": {
        "stats_levels":    ["Basic", "Medium", "Advanced"],
        "diagram_toggle":  True,
        "csv_download":    True,
        "advanced_tab":    True,
        "patent_engine":   True,
        "section_regens":  2,
        "word_limit":      7000,
        "label":           "Advanced",
    },
}


def _sb():
    try:
        from supabase import create_client
        url = os.environ.get("SUPABASE_URL", "")
        key = os.environ.get("SUPABASE_ANON_KEY", "")
        if url and key:
            return create_client(url, key)
    except Exception:
        pass
    return None


def validate_coupon(code: str) -> dict:
    """
    Validate a coupon code.
    Returns: {valid, tier, price, message, coupon_id}
    """
    code = code.strip().upper()
    if not code:
        return {"valid": False, "message": "Enter a coupon code."}

    sb = _sb()
    if sb:
        try:
            r = (sb.table("coupons")
                 .select("*")
                 .eq("code", code)
                 .eq("used", False)
                 .eq("active", True)
                 .execute())
            if r.data:
                c = r.data[0]
                # Check expiry
                if c.get("expires_at"):
                    exp = datetime.datetime.fromisoformat(
                        c["expires_at"].replace("Z",""))
                    if exp < datetime.datetime.utcnow():
                        return {"valid": False,
                                "message": "This coupon has expired."}
                return {
                    "valid":     True,
                    "tier":      c["tier"],
                    "price":     c["price"],
                    "coupon_id": c["id"],
                    "code":      code,
                    "message":   f"✅ Valid {c['tier']} coupon (₹{c['price']})",
                }
            return {"valid": False,
                    "message": "Invalid or already used coupon code."}
        except Exception as e:
            pass

    # Dev mode — accept hardcoded test codes
    dev_codes = {
        "BASIC001":    {"tier": "Basic",    "price": 999},
        "MEDIUM001":   {"tier": "Medium",   "price": 1999},
        "ADVANCED001": {"tier": "Advanced", "price": 4999},
        "YOGESH9999":  {"tier": "Advanced", "price": 0},
    }
    if code in dev_codes:
        d = dev_codes[code]
        return {
            "valid":     True,
            "tier":      d["tier"],
            "price":     d["price"],
            "coupon_id": f"dev_{code}",
            "code":      code,
            "message":   f"✅ Dev mode: {d['tier']} access granted",
        }
    return {"valid": False,
            "message": "Invalid coupon code."}


def mark_coupon_used(coupon_id: str, user_phone: str = "",
                      topic: str = ""):
    """Mark coupon as used after generation confirmed."""
    if coupon_id.startswith("dev_"):
        return  # dev mode
    sb = _sb()
    if sb:
        try:
            sb.table("coupons").update({
                "used":       True,
                "used_at":    datetime.datetime.utcnow().isoformat() + "Z",
                "used_by":    user_phone,
                "used_for":   topic[:100],
            }).eq("id", coupon_id).execute()
        except Exception:
            pass


def get_tier_config(tier: str) -> dict:
    return TIER_VISIBILITY.get(tier, TIER_VISIBILITY["Basic"])


def render_coupon_gate() -> dict:
    """
    Render the coupon entry screen.
    Returns validated coupon dict when valid, empty dict otherwise.
    """
    # Already validated this session
    if st.session_state.get("coupon_validated"):
        return st.session_state.get("coupon_data", {})

    st.markdown(
        '<div style="max-width:440px;margin:3rem auto;'
        'background:#fff;border:1px solid #E8E0D4;border-radius:12px;'
        'padding:2rem 2.5rem;box-shadow:0 2px 16px rgba(0,0,0,0.08)">'
        '<div style="font-family:Georgia,serif;font-size:24px;'
        'font-weight:600;color:#3E2723;margin-bottom:6px">🔬 Shodhak</div>'
        '<div style="font-size:13px;color:#8D6E63;margin-bottom:1.5rem;'
        'font-style:italic">'
        'The research supervisor that 95% of Indian researchers never had.'
        '</div>',
        unsafe_allow_html=True)

    code = st.text_input(
        "Enter your access coupon",
        placeholder="e.g. BASIC001 or ADVANCED001",
        key="coupon_input_field",
        help="Purchase coupons at shodhak.in").strip().upper()

    if st.button("→ Activate", use_container_width=True,
                 key="coupon_activate_btn"):
        result = validate_coupon(code)
        if result["valid"]:
            st.session_state["coupon_validated"] = True
            st.session_state["coupon_data"]      = result
            st.session_state["tier"]             = result["tier"]
            st.session_state["coupon_id"]        = result["coupon_id"]
            tier_cfg = get_tier_config(result["tier"])
            st.session_state["tier_config"]      = tier_cfg
            st.rerun()
        else:
            st.error(result["message"])

    st.markdown(
        '<div style="margin-top:1rem;font-size:12px;color:#aaa;'
        'text-align:center">No coupon? '
        '<a href="https://shodhak.in" style="color:#8B0000">'
        'Get one at shodhak.in</a></div>'
        '</div>',
        unsafe_allow_html=True)

    return {}


# ── Supabase SQL to run once ────────────────────────────────
COUPON_SQL = """
-- Run in Supabase SQL Editor

CREATE TABLE IF NOT EXISTS coupons (
    id          UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    code        TEXT UNIQUE NOT NULL,
    tier        TEXT NOT NULL CHECK (tier IN ('Basic','Medium','Advanced')),
    price       INTEGER NOT NULL,
    active      BOOLEAN DEFAULT true,
    used        BOOLEAN DEFAULT false,
    used_at     TIMESTAMPTZ,
    used_by     TEXT,
    used_for    TEXT,
    created_at  TIMESTAMPTZ DEFAULT now(),
    expires_at  TIMESTAMPTZ
);

-- Insert 50 Basic coupons (₹999)
INSERT INTO coupons (code, tier, price)
SELECT
    'BASIC' || LPAD(generate_series::text, 3, '0'),
    'Basic', 999
FROM generate_series(1, 50);

-- Insert 50 Medium coupons (₹1,999)
INSERT INTO coupons (code, tier, price)
SELECT
    'MEDIUM' || LPAD(generate_series::text, 3, '0'),
    'Medium', 1999
FROM generate_series(1, 50);

-- Insert 50 Advanced coupons (₹4,999)
INSERT INTO coupons (code, tier, price)
SELECT
    'ADVANCED' || LPAD(generate_series::text, 3, '0'),
    'Advanced', 4999
FROM generate_series(1, 50);

-- Your personal admin coupon
INSERT INTO coupons (code, tier, price) VALUES
    ('YOGESH9999', 'Advanced', 0);

-- View all unused coupons
-- SELECT code, tier, price, used FROM coupons ORDER BY tier, code;
"""
