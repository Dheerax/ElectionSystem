"""
face_service.py — ArcFace face encoding and verification via HuggingFace API.

Handles cold-start delays: HF free Spaces go to sleep and can take 20-40 seconds
to wake up. We retry up to 3 times with increasing delays.
"""

import base64
import logging
import time
import numpy as np
import requests
import os

logger = logging.getLogger(__name__)

HF_API_URL = os.environ.get("HUGGINGFACE_API_URL", "https://your-space-name.hf.space")

_MAX_RETRIES = 3
_RETRY_DELAYS = [5, 10, 15]   # seconds between retries


def extract_face_encoding(b64_image):
    """
    Given a base64 image string, detect a face and return its 512-d ArcFace embedding
    by querying the Hugging Face API. Retries on network/timeout errors to handle
    HF Space cold-start delays.
    """
    if "your-space-name" in HF_API_URL:
        logger.error("HUGGINGFACE_API_URL environment variable is not set!")
        return None

    req_url = HF_API_URL.rstrip("/") + "/encode"
    if not req_url.startswith("http"):
        req_url = "https://" + req_url

    for attempt in range(1, _MAX_RETRIES + 1):
        try:
            logger.info(f"Sending face to HF API (attempt {attempt}/{_MAX_RETRIES}): {req_url}")
            res = requests.post(
                req_url,
                json={"b64_image": b64_image},
                timeout=45,   # HF cold starts can take ~30s
            )
            res.raise_for_status()
            data = res.json()

            if data.get("success"):
                embedding_list = data.get("embedding")
                logger.info("Face encoding received successfully from HF API.")
                return np.array(embedding_list, dtype=np.float32)
            else:
                logger.warning(f"Face API returned failure: {data.get('error')}")
                return None   # Definitive API error — no point retrying
        except requests.exceptions.Timeout:
            logger.warning(f"HF API timed out on attempt {attempt}.")
        except requests.exceptions.ConnectionError as e:
            logger.warning(f"HF API connection error on attempt {attempt}: {e}")
        except Exception as e:
            logger.error(f"Unexpected error on attempt {attempt}: {e}")
            return None

        if attempt < _MAX_RETRIES:
            delay = _RETRY_DELAYS[attempt - 1]
            logger.info(f"Retrying in {delay}s...")
            time.sleep(delay)

    logger.error("All HF API attempts failed — face encoding returned None.")
    return None


def encoding_to_b64(embedding):
    """Serialize numpy embedding to base64 string for DB storage."""
    if embedding is None:
        return None
    return base64.b64encode(embedding.astype(np.float32).tobytes()).decode('utf-8')


def b64_to_encoding(b64_str):
    """Deserialize base64 string back to numpy embedding."""
    if not b64_str:
        return None
    try:
        raw = base64.b64decode(b64_str)
        return np.frombuffer(raw, dtype=np.float32).copy()
    except Exception as e:
        logger.error(f"b64_to_encoding failed: {e}")
        return None


def verify_face(stored_b64_encoding, live_b64_image, threshold=0.40):
    """
    Compare a stored face encoding (b64) against a live captured image (b64).
    Returns (matched: bool, similarity: float | None).
    """
    if not stored_b64_encoding:
        logger.warning("No stored face encoding for this voter.")
        return False, None

    stored_enc = b64_to_encoding(stored_b64_encoding)
    if stored_enc is None:
        return False, None

    live_enc = extract_face_encoding(live_b64_image)
    if live_enc is None:
        return False, None   # HF API unreachable or no face detected

    # Cosine similarity (both embeddings are L2-normalised → dot product = cosine)
    similarity = float(np.dot(stored_enc, live_enc))
    matched = similarity >= threshold
    logger.info(f"Face verification: similarity={similarity:.3f}, matched={matched}")
    return matched, round(similarity, 3)


def get_face_app():
    """Backwards compatibility shim — does nothing."""
    pass
