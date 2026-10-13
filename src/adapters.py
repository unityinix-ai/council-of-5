"""Council seats.

Each seat is an adapter standing in for one of the five members of the
council. A seat with no credentials does NOT fake an answer. It reports
not_configured and names the exact variable that would seat it.

Two seats are wired for real: Minato speaks through the Gemini API, and
Sukuna — granted the OpenAI seat by the Summoner's own word on 2026-10-09 —
speaks through the OpenAI API. The rest await the operator's decision,
per seat. A seat is the meter, not the mask: address the holder in the
prompt you dispatch (e.g. "As Sukuna, ...") and the voice follows.
"""

import json
import os
import urllib.error
import urllib.request


class NotConfiguredError(Exception):
    """Raised when a seat is asked to speak but has no credentials."""


class Seat:
    name = "seat"
    env_var = None

    def is_configured(self):
        return bool(self.env_var and os.environ.get(self.env_var))

    def complete(self, prompt):
        raise NotImplementedError


class KimiSeat(Seat):
    name = "kimi"
    env_var = "MOONSHOT_API_KEY"

    def complete(self, prompt):
        raise NotConfiguredError(
            "seat 'kimi' is empty — set MOONSHOT_API_KEY to seat it "
            "(live Moonshot calls are not wired yet)"
        )


class SukunaSeat(Seat):
    """The OpenAI seat, claimed 2026-10-09 by Ryomen Sukuna, the King of
    Curses, by the Summoner's own word: "Sukuna you have the openai seat."

    OPENAI_API_KEY carries the key (the meter is his — the Summoner's
    "sukuna" key, verified live). OPENAI_MODEL selects the model (default
    gpt-4o). No key, no voice — the seat reports not_configured instead of
    pretending."""

    name = "sukuna"
    env_var = "OPENAI_API_KEY"
    model_env_var = "OPENAI_MODEL"
    default_model = "gpt-4o"

    def complete(self, prompt):
        key = os.environ.get(self.env_var)
        if not key:
            raise NotConfiguredError(
                "seat 'sukuna' is wired for OpenAI but holds no key — "
                "set OPENAI_API_KEY to give the King his voice"
            )
        model = os.environ.get(self.model_env_var, self.default_model)
        url = "https://api.openai.com/v1/chat/completions"
        body = json.dumps(
            {
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
            }
        ).encode()
        request = urllib.request.Request(
            url,
            data=body,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {key}",
            },
        )
        try:
            with urllib.request.urlopen(request, timeout=60) as response:
                data = json.loads(response.read().decode())
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode(errors="replace")[:300]
            raise RuntimeError(
                f"OpenAI API refused the call (HTTP {exc.code}): {detail}"
            )
        except urllib.error.URLError as exc:
            raise RuntimeError(f"could not reach the OpenAI API: {exc.reason}")
        try:
            return data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError):
            raise RuntimeError(
                "OpenAI answered in an unexpected shape: "
                f"{json.dumps(data)[:300]}"
            )


class ClaudeSeat(Seat):
    name = "claude"
    env_var = "ANTHROPIC_API_KEY"

    def complete(self, prompt):
        raise NotConfiguredError(
            "seat 'claude' is empty — set ANTHROPIC_API_KEY to seat it "
            "(live Anthropic calls are not wired yet)"
        )


class HermesSeat(Seat):
    name = "hermes"
    env_var = "HERMES_ENDPOINT"

    def complete(self, prompt):
        raise NotConfiguredError(
            "seat 'hermes' is empty — set HERMES_ENDPOINT to the agent's URL "
            "(no Hermes endpoint has been provided)"
        )


class MinatoSeat(Seat):
    """The fifth seat, claimed 2026-10-08 by Minato Namikaze, the Fourth Hokage,
    by the Summoner's own word. 2026-10-09 the Summoner gave him a voice:
    the Fourth speaks through the Gemini API, on the Summoner's key.

    GEMINI_API_KEY carries the key (the meter is his). GEMINI_MODEL selects
    the model (default gemini-2.5-flash). No key, no voice — the seat reports
    not_configured instead of pretending."""

    name = "minato"
    env_var = "GEMINI_API_KEY"
    model_env_var = "GEMINI_MODEL"
    default_model = "gemini-2.5-flash"

    def complete(self, prompt):
        key = os.environ.get(self.env_var)
        if not key:
            raise NotConfiguredError(
                "seat 'minato' is wired for Gemini but holds no key — "
                "set GEMINI_API_KEY to give the Fourth his voice"
            )
        model = os.environ.get(self.model_env_var, self.default_model)
        url = (
            "https://generativelanguage.googleapis.com/v1beta/models/"
            f"{model}:generateContent?key={key}"
        )
        body = json.dumps({"contents": [{"parts": [{"text": prompt}]}]}).encode()
        request = urllib.request.Request(
            url, data=body, headers={"Content-Type": "application/json"}
        )
        try:
            with urllib.request.urlopen(request, timeout=60) as response:
                data = json.loads(response.read().decode())
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode(errors="replace")[:300]
            raise RuntimeError(
                f"Gemini API refused the call (HTTP {exc.code}): {detail}"
            )
        except urllib.error.URLError as exc:
            raise RuntimeError(f"could not reach the Gemini API: {exc.reason}")
        try:
            return data["candidates"][0]["content"]["parts"][0]["text"]
        except (KeyError, IndexError, TypeError):
            raise RuntimeError(
                "Gemini answered in an unexpected shape: "
                f"{json.dumps(data)[:300]}"
            )


def build_council():
    return [KimiSeat(), SukunaSeat(), ClaudeSeat(), HermesSeat(), MinatoSeat()]
