"""
model_router.py — PaperForge Cost-Optimized Router v2
======================================================
RULE: Only paper WRITING uses Sonnet/Opus.
ALL prep calls use DeepSeek V3 → Groq → Haiku fallback.
This cuts cost from ₹520 to ~₹185 per Basic paper.

Cost table (1 USD = ₹100):
  DeepSeek V3:  $0.27/$1.10 per M tokens → ~₹0.05 per prep call
  Groq Llama:   Free tier  → ₹0
  Haiku:        $0.80/$4.00 per M tokens → ~₹0.80 per prep call
  Sonnet:       $3.00/$15.0 per M tokens → ~₹45 per writing call
  Opus:         $15.0/$75.0 per M tokens → ~₹225 per heavy call
"""

import os
import time
from typing import Optional

GROQ_BASE      = "https://api.groq.com/openai/v1"
DEEPSEEK_BASE  = "https://api.deepseek.com"
FIREWORKS_BASE = "https://api.fireworks.ai/inference/v1"

MODEL_ID_MAP = {
    "deepseek-v3":   "deepseek-chat",
    "deepseek-r1":   "deepseek-reasoner",
    "gpt-oss-120b":  "accounts/fireworks/models/gpt-oss-120b",
    "gpt-oss-20b":   "accounts/fireworks/models/gpt-oss-20b",
    "llama-70b":     "llama-3.3-70b-versatile",
}

# ── Model tiers ────────────────────────────────────────────
# PREP calls (domain, objectives, structure, stats, narratives)
PREP_CHAIN = [
    ("deepseek-v3",               "deepseek"),   # ₹0.05/call — cheapest
    ("llama-3.3-70b-versatile",   "groq"),        # free tier
    ("claude-haiku-4-5-20251001", "anthropic"),   # ₹0.80/call — last resort
]

# WRITING models by tier
WRITER_MODELS = {
    "Basic":    "claude-haiku-4-5-20251001",  # ₹4/call  — good enough for Basic
    "Medium":   "claude-sonnet-4-6",           # ₹45/call — quality
    "Advanced": "claude-sonnet-4-6",           # ₹45/call
    "Premium":  "claude-sonnet-4-6",           # ₹45/call
    "Ultra":    "claude-sonnet-4-6",           # ₹45/call — Opus only for heavy sections
}

# HEAVY sections (SEM, CFA, patent depth) — Opus only on Premium/Ultra
HEAVY_MODELS = {
    "Basic":    "claude-haiku-4-5-20251001",
    "Medium":   "claude-sonnet-4-6",
    "Advanced": "claude-sonnet-4-6",
    "Premium":  "claude-opus-4-6",
    "Ultra":    "claude-opus-4-6",
}

# AUDIT chain — never Claude
AUDIT_CHAIN = [
    ("accounts/fireworks/models/gpt-oss-20b", "fireworks"),
    ("llama-3.3-70b-versatile",               "groq"),
    ("claude-haiku-4-5-20251001",             "anthropic"),   # last resort
]


def get_provider(model_name: str) -> str:
    name = model_name.lower().strip()
    if name.startswith("claude"):                    return "anthropic"
    if "gpt-oss" in name or "fireworks" in name:    return "fireworks"
    if name.startswith("gpt") or name.startswith("o1"): return "openai"
    if any(name.startswith(p) for p in ["llama","mixtral","kimi","qwen"]): return "groq"
    if name.startswith("deepseek"):                  return "deepseek"
    if name.startswith("gemini"):                    return "google"
    return "anthropic"


def _resolve(model_name: str) -> str:
    return MODEL_ID_MAP.get(model_name, model_name)


def _get_api_keys() -> dict:
    return {
        "anthropic": os.environ.get("ANTHROPIC_API_KEY", ""),
        "deepseek":  os.environ.get("DEEPSEEK_API_KEY", ""),
        "groq":      os.environ.get("GROQ_API_KEY", ""),
        "fireworks": os.environ.get("FIREWORKS_API_KEY", ""),
        "openai":    os.environ.get("OPENAI_API_KEY", ""),
    }


def call_model(model_name: str, messages: list, max_tokens: int,
               system: str = None, api_keys: dict = None) -> str:
    if api_keys is None:
        api_keys = _get_api_keys()
    provider  = get_provider(model_name)
    api_model = _resolve(model_name)

    if provider == "anthropic":
        return _anthropic(api_model, messages, max_tokens, system,
                          api_keys.get("anthropic") or os.environ.get("ANTHROPIC_API_KEY",""))
    if provider in ("fireworks","groq","deepseek","openai"):
        base = {"fireworks": FIREWORKS_BASE, "groq": GROQ_BASE,
                "deepseek": DEEPSEEK_BASE, "openai": None}[provider]
        key  = api_keys.get(provider, "")
        return _openai_compat(api_model, messages, max_tokens, system, key, base)
    if provider == "google":
        return _google(api_model, messages, max_tokens, system, api_keys.get("google",""))
    raise ValueError(f"Unknown provider: {provider}")


def call_prep(messages: list, system: str, max_tokens: int = 1500,
              api_keys: dict = None) -> str:
    """
    PREP call — DeepSeek → Groq → Haiku.
    Cost: ~₹0.05 per call instead of ₹45 with Sonnet.
    """
    if api_keys is None:
        api_keys = _get_api_keys()
    for model, provider in PREP_CHAIN:
        key = api_keys.get(provider, "")
        if not key and provider != "groq":
            continue
        try:
            result = call_model(model, messages, max_tokens, system, api_keys)
            if result and len(result.strip()) > 20:
                return result
        except Exception as e:
            print(f"[PrepRouter] {model} failed: {e}. Next...")
            time.sleep(0.3)
    # Absolute fallback
    return call_model("claude-haiku-4-5-20251001", messages, max_tokens, system, api_keys)


def call_audit(messages: list, system: str, max_tokens: int = 1200,
               api_keys: dict = None) -> str:
    """
    AUDIT call — Fireworks → Groq → Haiku.
    NEVER returns Claude auditing its own output if avoidable.
    """
    if api_keys is None:
        api_keys = _get_api_keys()
    for model, provider in AUDIT_CHAIN:
        key = api_keys.get(provider, "")
        if not key and provider not in ("groq",):
            continue
        try:
            result = call_model(model, messages, max_tokens, system, api_keys)
            if result and len(result.strip()) > 20:
                return result
        except Exception as e:
            print(f"[AuditRouter] {model} failed: {e}. Next...")
            time.sleep(0.3)
    return call_model("claude-haiku-4-5-20251001", messages, max_tokens, system, api_keys)


def call_writer(tier: str, messages: list, system: str,
                max_tokens: int = 6000, heavy: bool = False,
                api_keys: dict = None) -> str:
    """
    WRITING call — model selected by tier.
    Basic: Haiku (₹4). Medium+: Sonnet (₹45). Premium/Ultra heavy: Opus.
    """
    if api_keys is None:
        api_keys = _get_api_keys()
    model = HEAVY_MODELS.get(tier, "claude-sonnet-4-6") if heavy \
            else WRITER_MODELS.get(tier, "claude-sonnet-4-6")
    return call_model(model, messages, max_tokens, system, api_keys)


# ── Provider implementations ───────────────────────────────

def _anthropic(model: str, messages: list, max_tokens: int,
                system: str, api_key: str) -> str:
    import anthropic
    client = anthropic.Anthropic(api_key=api_key)
    kwargs = {"model": model, "max_tokens": max_tokens, "messages": messages}
    if system:
        kwargs["system"] = system
    resp = client.messages.create(**kwargs)
    return resp.content[0].text


def _openai_compat(model: str, messages: list, max_tokens: int,
                    system: str, api_key: str, base_url: str) -> str:
    from openai import OpenAI
    kw = {"api_key": api_key or "placeholder"}
    if base_url:
        kw["base_url"] = base_url
    client = OpenAI(**kw)
    chat_messages = []
    if system:
        chat_messages.append({"role": "system", "content": system})
    chat_messages.extend(messages)
    resp = client.chat.completions.create(
        model=model, max_tokens=max_tokens, messages=chat_messages)
    return resp.choices[0].message.content


def _google(model: str, messages: list, max_tokens: int,
             system: str, api_key: str) -> str:
    import google.generativeai as genai
    genai.configure(api_key=api_key)
    gm = genai.GenerativeModel(model)
    parts = [system] if system else []
    parts.extend(m["content"] for m in messages)
    resp = gm.generate_content("\n\n".join(parts))
    return resp.text
