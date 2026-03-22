"""
notify.py — Genzybrains WhatsApp notification endpoint
Add this to your Railway app alongside shodhak_app.py
Run as a separate process or import into shodhak_app.py

Endpoint: POST /notify
Body: {"name": "Dr. Priya", "phone": "9876543210", "plan": "Basic"}
Returns: {"ok": true} or {"ok": false, "error": "..."}
"""

import os
import json
import requests
from http.server import HTTPServer, BaseHTTPRequestHandler

GENZY_TOKEN    = os.environ.get("GENZYBRAINS_API_KEY", "")
GENZY_INSTANCE = os.environ.get("GENZYBRAINS_INSTANCE_ID", "")
# Your own WhatsApp number — you get notified when someone requests a coupon
OWNER_PHONE    = os.environ.get("OWNER_WHATSAPP", "")


def send_whatsapp(to_phone: str, message: str) -> bool:
    """Send WhatsApp message via Genzybrains API."""
    if not GENZY_TOKEN or not GENZY_INSTANCE:
        print("Genzybrains not configured")
        return False

    # Clean phone number
    clean = "".join(c for c in to_phone if c.isdigit())
    if len(clean) == 10:
        clean = "91" + clean
    if not clean.startswith("91"):
        clean = "91" + clean.lstrip("0")

    try:
        r = requests.post(
            "https://cloud.genzybrains.com/api/send",
            json={
                "number":      clean,
                "type":        "text",
                "message":     message,
                "instance_id": GENZY_INSTANCE,
                "access_token": GENZY_TOKEN,
            },
            timeout=10
        )
        return r.status_code == 200
    except Exception as e:
        print(f"WhatsApp send error: {e}")
        return False


def handle_coupon_request(name: str, phone: str, plan: str) -> dict:
    """
    1. Send confirmation to user
    2. Notify owner (you) on WhatsApp
    """
    plan_prices = {"Basic": "₹999", "Medium": "₹1,999", "Advanced": "₹4,999"}
    price = plan_prices.get(plan, "₹999")

    # Message to user
    user_msg = (
        f"Hi {name.split()[0]}!\n\n"
        f"Thank you for your interest in Shodhak — शोधक.\n\n"
        f"Plan requested: *{plan}* ({price})\n\n"
        f"Your coupon code will be sent to this number within 2 hours "
        f"after payment confirmation.\n\n"
        f"Payment details will follow shortly.\n\n"
        f"— Shodhak Team, Pune"
    )

    # Notification to owner
    owner_msg = (
        f"🔔 *New Coupon Request — Shodhak*\n\n"
        f"Name: {name}\n"
        f"Phone: {phone}\n"
        f"Plan: {plan} ({price})\n\n"
        f"Reply with coupon code to send."
    )

    user_sent  = send_whatsapp(phone, user_msg)
    owner_sent = send_whatsapp(OWNER_PHONE, owner_msg) if OWNER_PHONE else False

    return {
        "ok":         True,
        "user_sent":  user_sent,
        "owner_sent": owner_sent,
    }


class NotifyHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        if self.path != "/notify":
            self.send_response(404)
            self.end_headers()
            return

        # CORS headers — allow Lovable frontend
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

        try:
            length = int(self.headers.get("Content-Length", 0))
            body   = json.loads(self.rfile.read(length))
            name   = body.get("name", "Researcher")
            phone  = body.get("phone", "")
            plan   = body.get("plan", "Basic")

            if not phone:
                self.wfile.write(json.dumps(
                    {"ok": False, "error": "Phone required"}).encode())
                return

            result = handle_coupon_request(name, phone, plan)
            self.wfile.write(json.dumps(result).encode())

        except Exception as e:
            self.wfile.write(json.dumps(
                {"ok": False, "error": str(e)}).encode())

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def log_message(self, format, *args):
        pass  # suppress access logs


if __name__ == "__main__":
    port = int(os.environ.get("NOTIFY_PORT", 5001))
    print(f"Notify endpoint running on port {port}")
    HTTPServer(("0.0.0.0", port), NotifyHandler).serve_forever()
