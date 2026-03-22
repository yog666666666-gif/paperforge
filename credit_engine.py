"""
credit_engine.py v3 — 10x Margin Credit System
================================================
1 credit = ₹5
₹999 = 200 credits (Starter pack)
Basic paper = 10 credits (₹50 revenue, ₹5 API cost = 10x)
"""

import os
from typing import Optional, Tuple, Dict
from datetime import datetime

# ── Credit costs ───────────────────────────────────────────
# 1 credit = ₹5. All costs tuned for 10x margin.
# 1 credit = ₹5. API cost × 10 = credits charged.
# Basic: ₹52 API → 104 credits → ₹520 revenue → 10x
CREDIT_COSTS = {
    "Basic":              104,  # ₹520 revenue | ₹52 API cost  | 10x
    "Medium":             160,  # ₹800 revenue | ₹80 API cost  | 10x
    "Advanced":           240,  # ₹1200 revenue| ₹120 API cost | 10x
    "Premium":            400,  # ₹2000 revenue| ₹200 API cost | 10x
    "Ultra":              600,  # ₹3000 revenue| ₹300 API cost | 10x
    "section_regen_free":   0,  # first 2 per paper free
    "section_regen_paid":  16,  # ₹80  | ₹8 API  | 10x
    "supervisor_unlock":   20,  # ₹100 | ₹2 API  | 50x (pure service)
    "extra_citations":      5,  # ₹25  | ₹0 API  | pure profit
    "stats_verify_csv":    10,  # ₹50  | ₹0 API  | pure profit
    "questionnaire":       16,  # ₹80  | ₹8 API  | 10x
    "diagrams_set":         5,  # ₹25  | ₹0 API  | pure profit
}

INR_PER_CREDIT = 5

CREDIT_PACKS = [
    {"id": "starter",     "credits": 200,   "price_inr": 999,
     "label": "Starter",
     "papers": "2 Basic papers",
     "note": "Taste it. No diagrams, no CSV.",
     "features": ["2 Basic papers (4,000w each)", "APA/SPPU formatting", "Verified citations"]},

    {"id": "value",       "credits": 700,   "price_inr": 2999,
     "label": "Value",
     "papers": "6 Basic OR 4 Medium",
     "note": "Most popular. Diagrams + CSV included.",
     "features": ["6 Basic OR 4 Medium papers", "Diagrams (auto-selected)", "Raw dataset CSV", "Supervisor review link"]},

    {"id": "pro",         "credits": 2000,  "price_inr": 7999,
     "label": "Pro",
     "papers": "19 Basic OR 12 Medium OR 8 Advanced",
     "note": "Serious researcher. Everything unlocked.",
     "features": ["19 Basic / 12 Medium / 8 Advanced", "Conference template matching", "Priority routing (Sonnet)", "All add-ons included"]},

    {"id": "institution", "credits": 7000,  "price_inr": 24999,
     "label": "Institution",
     "papers": "67 Basic OR 43 Medium OR 29 Advanced",
     "note": "For departments and research groups.",
     "features": ["67 Basic / 43 Medium / 29 Advanced", "Bulk coupon generation", "Team access", "Dedicated support"]},
]

LOW_CREDIT_THRESHOLD      = 15   # warn — less than 1.5 Basic papers
CRITICAL_CREDIT_THRESHOLD =  5   # red — less than half a Basic paper


def get_supabase_client():
    try:
        from supabase import create_client
        url = os.environ.get("SUPABASE_URL", "")
        key = os.environ.get("SUPABASE_ANON_KEY", "")
        if url and key:
            return create_client(url, key)
    except ImportError:
        pass
    return None


class CreditEngine:

    def __init__(self):
        self.sb       = get_supabase_client()
        self._memory: Dict[str, Dict] = {}

    def _live(self) -> bool:
        return self.sb is not None

    # ── Balance ──────────────────────────────────────────────

    def get_balance(self, user_id: str) -> float:
        if self._live():
            try:
                r = (self.sb.table("credits")
                     .select("balance")
                     .eq("user_id", user_id)
                     .single()
                     .execute())
                return float(r.data.get("balance", 0))
            except Exception:
                return 0.0
        return float(self._memory.get(user_id, {}).get("balance", 200.0))

    def set_balance(self, user_id: str, balance: float):
        if self._live():
            try:
                self.sb.table("credits").upsert({
                    "user_id": user_id,
                    "balance": round(balance, 1),
                    "updated_at": datetime.utcnow().isoformat(),
                }).execute()
            except Exception:
                pass
        else:
            self._memory.setdefault(user_id, {})
            self._memory[user_id]["balance"] = round(balance, 1)

    # ── Reserve / Confirm / Refund ────────────────────────────

    def reserve(self, user_id: str, cost: float,
                 paper_id: str = None) -> Tuple[bool, str]:
        balance = self.get_balance(user_id)
        if balance < cost:
            return False, (f"Insufficient credits. "
                           f"Balance: {balance:.0f}, Required: {cost:.0f}.")
        new_bal = round(balance - cost, 1)
        self.set_balance(user_id, new_bal)
        return True, f"Reserved {cost:.0f} credits. New balance: {new_bal:.0f}."

    def confirm(self, user_id: str, paper_id: str):
        pass  # reservation already committed in reserve()

    def refund(self, user_id: str, cost: float, paper_id: str = None):
        balance = self.get_balance(user_id)
        self.set_balance(user_id, balance + cost)

    # ── Regen tracking ────────────────────────────────────────

    def get_regen_used(self, user_id: str, paper_id: str) -> int:
        key = f"regen_{user_id}_{paper_id}"
        if self._live():
            try:
                r = (self.sb.table("paper_regens")
                     .select("count")
                     .eq("user_id", user_id)
                     .eq("paper_id", paper_id)
                     .single()
                     .execute())
                return int((r.data or {}).get("count", 0))
            except Exception:
                return 0
        return self._memory.get(key, 0)

    def use_regen(self, user_id: str, paper_id: str) -> Tuple[bool, float, str]:
        used = self.get_regen_used(user_id, paper_id)
        if used < 2:
            cost = 0
            msg  = f"Free regen ({used+1}/2 used)"
        else:
            cost = CREDIT_COSTS["section_regen_paid"]
            ok, msg = self.reserve(user_id, cost, paper_id)
            if not ok:
                return False, 0, msg
            msg = f"−{cost} credits (₹{cost * INR_PER_CREDIT})"

        key = f"regen_{user_id}_{paper_id}"
        if self._live():
            try:
                if used == 0:
                    self.sb.table("paper_regens").insert({
                        "user_id": user_id, "paper_id": paper_id, "count": 1
                    }).execute()
                else:
                    self.sb.table("paper_regens").update(
                        {"count": used + 1}
                    ).eq("user_id", user_id).eq("paper_id", paper_id).execute()
            except Exception:
                pass
        else:
            self._memory[key] = used + 1

        return True, cost, msg

    def check_max_regens(self, user_id: str, paper_id: str,
                          tier: str = "Basic") -> Tuple[bool, int]:
        used = self.get_regen_used(user_id, paper_id)
        max_t = {"Basic": 5, "Medium": 7, "Advanced": 10}.get(tier, 5)
        return (max_t - used) > 0, max_t - used

    # ── Warning ───────────────────────────────────────────────

    def low_credit_warning(self, user_id: str, tier: str) -> Optional[str]:
        bal  = self.get_balance(user_id)
        cost = CREDIT_COSTS.get(tier, 10)
        if bal < cost:
            return (f"🔴 Need {cost} credits to generate. "
                    f"You have {bal:.0f}. Top up now.")
        if bal <= CRITICAL_CREDIT_THRESHOLD:
            return f"🔴 Critical: {bal:.0f} credits left. Not enough for another paper. Top up now."
        if bal <= LOW_CREDIT_THRESHOLD:
            papers_left = int(bal // CREDIT_COSTS["Basic"])
            return (f"⚠️ Low credits: {bal:.0f} remaining. "
                    f"{'Enough for 1 more Basic paper.' if papers_left >= 1 else 'Not enough for another Basic paper.'} "
                    f"Top up soon.")
        return None

    # ── MSATA log ─────────────────────────────────────────────

    def log_msata(self, user_id: str, paper_id: str,
                   paper_title: str, ip: str, ua: str):
        if self._live():
            try:
                self.sb.table("msata_logs").insert({
                    "user_id":     user_id,
                    "paper_id":    paper_id,
                    "paper_title": paper_title[:200],
                    "ip_address":  ip,
                    "user_agent":  ua[:500],
                    "signed_at":   datetime.utcnow().isoformat(),
                }).execute()
            except Exception:
                pass


# ── Singleton ─────────────────────────────────────────────
_engine: Optional[CreditEngine] = None

def get_engine() -> CreditEngine:
    global _engine
    if _engine is None:
        _engine = CreditEngine()
    return _engine
