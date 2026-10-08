"""No-key, in-memory receptionist demo for a browser or GitHub Codespace."""

from __future__ import annotations

import json
import os
import re
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit


WEB_DIR = Path(__file__).parent / "web"
MAX_REQUEST_BYTES = 16_384
SESSIONS: dict[str, dict[str, str]] = {}


def handle_message(state: dict[str, str], message: str) -> str:
    """Respond to a message using local, scripted conversation rules."""
    text = message.strip()
    lowered = text.casefold()
    if not text:
        return "Please type or say a message, and I'll do my best to help."

    if re.search(r"\b(emergency|can't breathe|cannot breathe|uncontrolled bleeding)\b", lowered):
        return (
            "If this may be a life-threatening emergency, contact your local "
            "emergency services now. I can't assess symptoms."
        )
    if re.search(r"\b(diagnos(?:e|is|ing)?|what is wrong|what's wrong|treatment|cure)\b", lowered):
        return (
            "I can't diagnose symptoms or recommend treatment. Please contact a "
            "qualified dental or medical professional for advice."
        )

    if state.get("step") == "name":
        if len(text) > 100 or any(character.isdigit() for character in text):
            return "I didn't catch the name. Please enter just the caller's name."
        state["name"] = text
        state["step"] = "phone"
        return "Thanks. What phone number should the clinic use to contact you?"

    if state.get("step") == "phone":
        digits = sum(character.isdigit() for character in text)
        if not 7 <= digits <= 15:
            return "That number doesn't look complete. Please repeat a phone number with 7 to 15 digits."
        state["phone"] = text
        state["step"] = "confirm"
        return (
            f"I heard {state['name']} and {state['phone']}. Is that correct? "
            "Please say yes or no. This demo keeps it only in memory."
        )

    if state.get("step") == "confirm":
        if lowered in {"yes", "yes that's right", "correct", "right", "that's correct"}:
            state["step"] = "date"
            return "What date would you prefer for the appointment?"
        if lowered in {"no", "no that's wrong", "incorrect", "wrong"}:
            state.pop("name", None)
            state.pop("phone", None)
            state["step"] = "name"
            return "No problem. Let's try again. What name should I use?"
        return "Please confirm the details with a simple yes or no."

    if state.get("step") == "date":
        state["date"] = text
        state["step"] = "time"
        return "What time would you prefer?"

    if state.get("step") == "time":
        state["time"] = text
        state.pop("step", None)
        return (
            f"I noted an appointment request for {state['name']} at "
            f"{state['phone']}, on {state['date']} at {state['time']}. "
            "This stays in memory for this demo only. It was not sent to the "
            "clinic and is not a confirmed appointment."
        )

    if re.search(r"\b(appointment|book|booking|schedule|checkup|cleaning)\b", lowered):
        if state.get("name") and state.get("phone"):
            state["step"] = "date"
            return "I have your contact details for this session. What date would you prefer?"
        state["step"] = "name"
        return (
            "I can take an appointment request, but I can't check availability "
            "or confirm a booking. What name should I use?"
        )

    if re.search(r"\b(hours|open|close|closing|address|location|insurance|price|cost|available)\b", lowered):
        return (
            "I don't have this clinic's hours, address, prices, insurance details, "
            "or live availability. Please contact the clinic directly."
        )

    if re.search(r"\b(bring|prepare|preparation|first visit|first appointment)\b", lowered):
        return (
            "For a visit, you may want to bring photo ID, insurance information "
            "if applicable, and a list of medicines you take. Check with the "
            "clinic about anything specific."
        )

    if re.search(r"\b(hello|hi|hey|help)\b", lowered):
        return (
            "Hello! I can answer a few general visit questions or take an "
            "unconfirmed appointment request. Try asking what to bring or say "
            "'I'd like to request an appointment.' Type 'help' to see this again."
        )

    return (
        "I'm a small offline demo, not a general-purpose AI. I can answer a few "
        "general visit questions or take an unconfirmed appointment request. "
        "For clinic-specific details, please contact the clinic."
    )


class DemoHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        if urlsplit(self.path).path not in {"/", "/index.html"}:
            self.send_error(404)
            return
        page = (WEB_DIR / "index.html").read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(page)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(page)

    def do_POST(self) -> None:
        if urlsplit(self.path).path != "/api/chat":
            self.send_error(404)
            return

        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            self.send_error(400, "Invalid Content-Length")
            return
        if not 0 < length <= MAX_REQUEST_BYTES:
            self.send_error(413, "Request body must be between 1 and 16384 bytes")
            return

        try:
            payload = json.loads(self.rfile.read(length))
        except (json.JSONDecodeError, UnicodeDecodeError):
            self.send_error(400, "Expected a JSON request")
            return
        if not isinstance(payload, dict):
            self.send_error(400, "Expected a JSON object")
            return

        session_id = payload.get("session_id")
        message = payload.get("message")
        if not isinstance(session_id, str) or not 1 <= len(session_id) <= 80:
            self.send_error(400, "Invalid session_id")
            return
        if not isinstance(message, str) or not 1 <= len(message.strip()) <= 1000:
            self.send_error(400, "Message must contain between 1 and 1000 characters")
            return

        response = handle_message(SESSIONS.setdefault(session_id, {}), message)
        result = json.dumps({"reply": response}).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(result)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(result)

    def log_message(self, format: str, *args: object) -> None:
        # Avoid logging request contents or browser session identifiers.
        print(f"{self.address_string()} - {format % args}")


def main() -> None:
    port = int(os.getenv("PORT", "8000"))
    host = "0.0.0.0"
    server = ThreadingHTTPServer((host, port), DemoHandler)
    print(f"Free local demo is listening on {host}:{port}. Stop it with Ctrl+C.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping the demo.")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
