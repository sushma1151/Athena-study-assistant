"""
Calls Google's Gemini API (free tier, no credit card needed) to
generate real answers, summaries, and quizzes from retrieved PDF chunks.
Includes automatic retries since the free tier can hit temporary
"high demand" (503) errors.
"""
import os
import time
import requests

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-3.6-flash:generateContent"

MAX_RETRIES = 3
RETRY_DELAY_SECONDS = 3


def build_prompt(mode: str, question: str, context_chunks: list[str]) -> str:
    context = "\n\n---\n\n".join(context_chunks)

    if mode == "summarize":
        return (
            "Based only on the following text from a document, write a clear, "
            "concise summary covering the main points.\n\n"
            f"TEXT:\n{context}\n\n"
            f"Topic to focus the summary on (if given): {question}"
        )
    elif mode == "quiz":
        return (
            "Based only on the following text from a document, generate 5 quiz "
            "questions with answers to test understanding of this material. "
            "Format as a numbered list with the answer given right after each question.\n\n"
            f"TEXT:\n{context}"
        )
    else:
        return (
            "Answer the following question using only the information in the "
            "text below. If the answer isn't in the text, say so honestly.\n\n"
            f"TEXT:\n{context}\n\n"
            f"QUESTION: {question}"
        )


def generate_answer(mode: str, question: str, context_chunks: list[str]) -> str:
    if not GEMINI_API_KEY:
        return "GEMINI_API_KEY is not set. Set it as an environment variable and restart the server."

    prompt = build_prompt(mode, question, context_chunks)

    payload = {
        "contents": [
            {"parts": [{"text": prompt}]}
        ]
    }

    last_error = None

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = requests.post(
                f"{GEMINI_URL}?key={GEMINI_API_KEY}",
                json=payload,
                timeout=60
            )
        except requests.exceptions.Timeout:
            last_error = "Gemini took too long to respond."
            time.sleep(RETRY_DELAY_SECONDS)
            continue
        except requests.exceptions.RequestException as e:
            return f"Could not reach Gemini API: {str(e)}"

        if response.status_code == 503:
            last_error = "Gemini is temporarily overloaded (503)."
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_DELAY_SECONDS)
                continue
            else:
                return (
                    "Gemini's servers are experiencing high demand right now. "
                    "This is on Google's end, not your app - please try again in a moment."
                )

        if response.status_code != 200:
            return f"Error calling Gemini API: {response.status_code} - {response.text}"

        data = response.json()
        try:
            return data["candidates"][0]["content"]["parts"][0]["text"]
        except (KeyError, IndexError):
            return "Gemini API returned an unexpected response format."

    return f"Gemini API is currently unavailable after {MAX_RETRIES} attempts. Last error: {last_error}"