import json
import logging
import re
import threading

import requests
from django.conf import settings

logger = logging.getLogger(__name__)
_generation_slot = threading.BoundedSemaphore(value=1)


def deterministic_answer(shops, language):
    if not shops:
        return "Δεν βρέθηκαν σχετικά καταστήματα στην περιοχή." if language == "el" else "No matching shops were found in the selected area."
    names = ", ".join(f"[{shop['reference']}] {shop['name']}" for shop in shops[:3])
    prefix = "Οι καλύτερες διαθέσιμες επιλογές είναι" if language == "el" else "The strongest available options are"
    return f"{prefix}: {names}."


def build_prompt(question, language, shops):
    records = json.dumps(shops, ensure_ascii=False)
    return (
        "You are a local shop recommendation assistant. Answer only from the supplied records. "
        "Cite every recommended shop using its exact [S<number>] reference. Never invent facts, "
        "opening hours, amenities, or shops. If the records do not establish a requested feature, "
        "say so. Be concise. Reply in Greek when language=el and English when language=en. /no_think\n"
        f"language={language}\nquestion={question}\nrecords={records}"
    )


def _valid_answer(answer, shops):
    allowed = {shop["reference"] for shop in shops}
    cited = set(re.findall(r"\[(S\d+)\]", answer))
    return bool(answer.strip()) and (not shops or bool(cited)) and cited.issubset(allowed)


def generate_answer(question, language, shops):
    if not shops or not _generation_slot.acquire(blocking=False):
        return deterministic_answer(shops, language)
    try:
        response = requests.post(
            f"{settings.OLLAMA_URL}/api/generate",
            json={
                "model": settings.OLLAMA_MODEL,
                "prompt": build_prompt(question, language, shops[:8]),
                "stream": False,
                "options": {"temperature": 0.2, "num_ctx": 4096},
            },
            timeout=(3, settings.OLLAMA_TIMEOUT),
        )
        response.raise_for_status()
        answer = response.json().get("response", "").strip()
        return answer if _valid_answer(answer, shops) else deterministic_answer(shops, language)
    except requests.RequestException:
        logger.info("Ollama unavailable; using deterministic answer")
        return deterministic_answer(shops, language)
    finally:
        _generation_slot.release()


def stream_answer(question, language, shops):
    if not shops or not _generation_slot.acquire(blocking=False):
        yield deterministic_answer(shops, language)
        return
    emitted = []
    try:
        with requests.post(
            f"{settings.OLLAMA_URL}/api/generate",
            json={
                "model": settings.OLLAMA_MODEL,
                "prompt": build_prompt(question, language, shops[:8]),
                "stream": True,
                "options": {"temperature": 0.2, "num_ctx": 4096},
            },
            stream=True,
            timeout=(3, settings.OLLAMA_TIMEOUT),
        ) as response:
            response.raise_for_status()
            for line in response.iter_lines():
                if not line:
                    continue
                chunk = json.loads(line).get("response", "")
                emitted.append(chunk)
                if chunk:
                    yield chunk
    except (requests.RequestException, ValueError):
        if not emitted:
            yield deterministic_answer(shops, language)
    finally:
        _generation_slot.release()
