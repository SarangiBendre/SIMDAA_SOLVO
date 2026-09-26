"""
AI Assistant / Knowledge Base matching service.

Two layers:

1. Similarity engine (always available, zero dependencies): a
   bag-of-words cosine similarity over question titles + descriptions.
   This powers the "Before you post, here's what we already have"
   Knowledge Base search and the "related questions" suggestions -
   works with no configuration at all.

2. Real AI-generated suggestion (optional, recommended): set
   AI_PROVIDER in .env to turn on an actual LLM that reads the related
   Knowledge Base entries and drafts a short suggested answer. Three
   providers are supported:

     AI_PROVIDER=openai   -> OPENAI_API_KEY (+ optional OPENAI_MODEL)
     AI_PROVIDER=gemini   -> GEMINI_API_KEY (+ optional GEMINI_MODEL)
     AI_PROVIDER=ollama   -> OLLAMA_HOST + OLLAMA_MODEL (self-hosted, free)
     AI_PROVIDER=none     -> (default) heuristic-only, no LLM call

   If AI_PROVIDER is set but the call fails (bad key, no network, model
   not pulled yet, etc.) we log the reason and fall back to the
   heuristic template so the endpoint always returns something useful
   instead of erroring out.
"""

import os
import re
import math
import base64
import mimetypes
import logging
from collections import Counter

from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger("simdaa.ai")

AI_PROVIDER = os.getenv("AI_PROVIDER", "none").lower().strip()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
# Google GA'd Gemini 3.5 Flash in May 2026 and it's the current
# recommended default (gemini-2.5-flash still works but is deprecated,
# scheduled to shut down October 2026). If this ever 404s again, check
# https://ai.google.dev/gemini-api/docs/models for the current list -
# Google renames/retires these fairly often.
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.5-flash")

OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3")

STOPWORDS = {
    "a", "an", "the", "is", "are", "was", "were", "be", "been", "being",
    "to", "of", "in", "on", "at", "for", "with", "and", "or", "but", "if",
    "so", "as", "it", "this", "that", "these", "those", "i", "we", "you",
    "he", "she", "they", "my", "our", "your", "not", "do", "does", "did",
    "how", "what", "why", "when", "where", "can", "could", "should",
    "would", "will", "have", "has", "had", "am", "get", "getting", "im",
}

_TOKEN_RE = re.compile(r"[a-zA-Z0-9']+")


def _tokenize(text: str) -> Counter:
    tokens = [t.lower() for t in _TOKEN_RE.findall(text or "")]
    tokens = [t for t in tokens if t not in STOPWORDS and len(t) > 1]
    return Counter(tokens)


def _cosine_similarity(a: Counter, b: Counter) -> float:
    if not a or not b:
        return 0.0
    common = set(a) & set(b)
    dot = sum(a[t] * b[t] for t in common)
    norm_a = math.sqrt(sum(v * v for v in a.values()))
    norm_b = math.sqrt(sum(v * v for v in b.values()))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


def rank_similar_questions(query_title: str, query_description: str, candidates: list, top_n: int = 5):
    """candidates: list of dicts with QuestionID, Title, Description, ... (already fetched from DB).
    Returns candidates sorted by similarity score, annotated with a MatchScore (0-100),
    only including reasonably relevant matches."""

    query_vec = _tokenize(f"{query_title} {query_description}")
    scored = []

    for candidate in candidates:
        candidate_vec = _tokenize(f"{candidate.get('Title', '')} {candidate.get('Description', '')}")
        score = _cosine_similarity(query_vec, candidate_vec)
        if score > 0.08:  # ignore near-zero noise matches
            item = dict(candidate)
            item["MatchScore"] = round(score * 100, 1)
            scored.append(item)

    scored.sort(key=lambda c: c["MatchScore"], reverse=True)
    return scored[:top_n]


def _fallback_suggestion(top_matches: list) -> str:
    if not top_matches:
        return (
            "No closely related solved questions were found in the Knowledge Base yet. "
            "You're likely the first to ask this - once a mentor answers, it will help "
            "future students automatically."
        )

    best = top_matches[0]
    lines = [
        f"This looks similar to an existing question: \"{best.get('Title')}\" "
        f"({best.get('MatchScore')}% match).",
    ]
    if best.get("AcceptedAnswerText"):
        lines.append("Accepted answer on that question:")
        lines.append(best["AcceptedAnswerText"][:500])
    else:
        lines.append("That question doesn't have an accepted answer yet, but it may still help as context.")
    return "\n".join(lines)


def _build_prompt(query_title: str, query_description: str, top_matches: list) -> str:
    context_blocks = []
    for m in top_matches[:3]:
        block = f"Q: {m.get('Title')}\n{m.get('Description', '')[:400]}"
        if m.get("AcceptedAnswerText"):
            block += f"\nAccepted answer: {m['AcceptedAnswerText'][:400]}"
        context_blocks.append(block)

    context = "\n\n".join(context_blocks) if context_blocks else "(no related questions found)"

    return (
        "You are an assistant on an internal engineering Q&A platform. "
        "A student is about to ask a new question. Using ONLY the related "
        "questions/answers below as context, suggest a short, helpful answer "
        "or say clearly if none of them apply. Keep it under 120 words.\n\n"
        f"New question: {query_title}\n{query_description}\n\n"
        f"Related knowledge base entries:\n{context}"
    )


def _call_openai(prompt: str, image: dict | None = None) -> str:
    import requests

    if not OPENAI_API_KEY:
        raise RuntimeError("OPENAI_API_KEY is not set")

    if image:
        content = [
            {"type": "text", "text": prompt},
            {"type": "image_url", "image_url": {
                "url": f"data:{image['mime_type']};base64,{image['base64']}"
            }},
        ]
    else:
        content = prompt

    response = requests.post(
        "https://api.openai.com/v1/chat/completions",
        headers={"Authorization": f"Bearer {OPENAI_API_KEY}"},
        json={
            "model": OPENAI_MODEL,
            "messages": [{"role": "user", "content": content}],
            "max_tokens": 350,
            "temperature": 0.4,
        },
        timeout=30,
    )
    response.raise_for_status()
    return response.json()["choices"][0]["message"]["content"].strip()


def _call_gemini(prompt: str, image: dict | None = None) -> str:
    import requests

    if not GEMINI_API_KEY:
        raise RuntimeError("GEMINI_API_KEY is not set")

    parts = [{"text": prompt}]
    if image:
        parts.append({"inline_data": {"mime_type": image["mime_type"], "data": image["base64"]}})

    # IMPORTANT: send the key via the x-goog-api-key header, not the old
    # ?key=... query parameter. Google's newer "Auth key" format
    # (keys starting with "AQ." - the default for all keys issued from
    # AI Studio since mid-2026) returns a 404/401 when passed as a query
    # param; the header works for both the new AQ. keys and legacy
    # AIzaSy... keys. See https://ai.google.dev/api for the current auth docs.
    response = requests.post(
        f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent",
        headers={"x-goog-api-key": GEMINI_API_KEY, "Content-Type": "application/json"},
        json={"contents": [{"parts": parts}]},
        timeout=30,
    )
    response.raise_for_status()
    return response.json()["candidates"][0]["content"]["parts"][0]["text"].strip()


def _call_ollama(prompt: str, image: dict | None = None) -> str:
    import requests

    payload = {"model": OLLAMA_MODEL, "prompt": prompt, "stream": False}
    if image:
        # Only works if OLLAMA_MODEL is a vision-capable model (e.g. llava).
        payload["images"] = [image["base64"]]

    response = requests.post(
        f"{OLLAMA_HOST}/api/generate",
        json=payload,
        timeout=30,
    )
    response.raise_for_status()
    return response.json().get("response", "").strip()


_PROVIDERS = {
    "openai": _call_openai,
    "gemini": _call_gemini,
    "ollama": _call_ollama,
}


def _is_rate_limit_error(exc: Exception) -> bool:
    """True if the exception looks like a 429 Too Many Requests from the
    provider - i.e. a free-tier quota was hit, not a real failure."""
    status = getattr(getattr(exc, "response", None), "status_code", None)
    return status == 429 or "429" in str(exc) or "too many requests" in str(exc).lower()


def get_ai_suggestion(query_title: str, query_description: str, top_matches: list) -> dict:
    """Returns {"source": "openai"|"gemini"|"ollama"|"heuristic", "suggestion": str}"""

    provider_fn = _PROVIDERS.get(AI_PROVIDER)

    if provider_fn:
        try:
            prompt = _build_prompt(query_title, query_description, top_matches)
            text = provider_fn(prompt)
            if text:
                return {"source": AI_PROVIDER, "suggestion": text}
        except Exception as exc:
            if _is_rate_limit_error(exc):
                logger.warning("AI_PROVIDER=%s hit a rate limit - falling back to heuristic", AI_PROVIDER)
            else:
                logger.warning(
                    "AI_PROVIDER=%s suggestion call failed, falling back to heuristic: %s",
                    AI_PROVIDER, exc,
                )
    elif AI_PROVIDER != "none":
        logger.warning("Unknown AI_PROVIDER '%s' - falling back to heuristic", AI_PROVIDER)

    return {"source": "heuristic", "suggestion": _fallback_suggestion(top_matches)}


# ============================================================
# General-purpose AI Assistant chat (separate from the Knowledge Base
# duplicate-check above). Always available in the app via the AI
# Assistant page - for concept explanations, error debugging, code help.
# ============================================================

def _build_chat_prompt(message: str, history: list) -> str:
    lines = [
        "You are the AI Assistant on SIMDAA SOLVO, an internal engineering "
        "Q&A platform. Help with concept explanations, debugging errors, "
        "and code questions. Be concise and practical.",
        "",
    ]
    for role, content in history[-10:]:
        speaker = "User" if role == "user" else "Assistant"
        lines.append(f"{speaker}: {content}")
    lines.append(f"User: {message}")
    lines.append("Assistant:")
    return "\n".join(lines)


def get_ai_chat_reply(message: str, history: list, image: dict | None = None) -> str:
    provider_fn = _PROVIDERS.get(AI_PROVIDER)

    if provider_fn:
        try:
            prompt = _build_chat_prompt(message, history)
            text = provider_fn(prompt, image)
            if text:
                return text
        except Exception as exc:
            if _is_rate_limit_error(exc):
                logger.warning("AI_PROVIDER=%s hit a rate limit on chat", AI_PROVIDER)
                return (
                    "The AI Assistant is getting a lot of requests right now and hit "
                    "its free-tier rate limit. This isn't a bug - just wait a minute "
                    "and try again."
                )
            logger.warning("AI_PROVIDER=%s chat call failed: %s", AI_PROVIDER, exc)
        return (
            "Sorry, I couldn't get a response just now. This usually clears up "
            "on its own - please try again in a moment. If it keeps happening, "
            "let an admin know."
        )

    return (
        "The AI Assistant isn't connected to a real language model yet. "
        "Set AI_PROVIDER=openai, gemini, or ollama in backend/.env (plus the "
        "matching API key) to enable real answers here."
    )


def load_image_as_base64(upload_dir: str, attachment_path: str) -> dict | None:
    """Reads a previously-uploaded attachment (e.g. "/uploads/abc.png")
    off disk and returns {"base64": ..., "mime_type": ...} for feeding to
    a vision-capable AI call. Returns None if the file can't be read."""

    if not attachment_path:
        return None

    filename = attachment_path.rsplit("/", 1)[-1]
    filepath = os.path.join(upload_dir, filename)

    try:
        with open(filepath, "rb") as f:
            data = f.read()
        mime_type = mimetypes.guess_type(filename)[0] or "image/png"
        return {"base64": base64.b64encode(data).decode("ascii"), "mime_type": mime_type}
    except Exception as exc:
        logger.warning("Could not read attachment %s for AI vision input: %s", attachment_path, exc)
        return None
