"""
face_service.py — ArcFace face encoding and verification via API.

This version proxy image data to a Hugging Face Space (or external API)
to offload memory-heavy AI processing from Render's free tier.
"""

import base64
import logging
import numpy as np
import requests
import os

logger = logging.getLogger(__name__)

# Fallback fake URL so the code doesn't crash on boot
HF_API_URL = os.environ.get("HUGGINGFACE_API_URL", "https://your-space-name.hf.space")

def extract_face_encoding(b64_image):
    """
    Given a base64 image string, detect a face and return its 512-d ArcFace embedding
    by querying the Hugging Face API.
    """
    if "your-space-name" in HF_API_URL:
        logger.error("HUGGINGFACE_API_URL environment variable is not set!")
        return None

    try:
        req_url = f"{HF_API_URL}/encode"
        # Ensure correct protocol if omitted
        if not req_url.startswith("http"):
            req_url = "https://" + req_url
            
        logger.info(f"Sending face to Hugging Face API: {req_url}")
        res = requests.post(req_url, json={"b64_image": b64_image}, timeout=30)
        res.raise_for_status()
        data = res.json()
        
        if data.get("success"):
            embedding_list = data.get("embedding")
            return np.array(embedding_list, dtype=np.float32)
        else:
            logger.warning(f"Face API failed: {data.get('error')}")
            return None
    except Exception as e:
        logger.error(f"Failed to communicate with Face API: {e}")
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
    Compare a stored face encoding (b64) against a live captured image (b64) via API.
    """
    if not stored_b64_encoding:
        logger.warning("No stored face encoding for this voter.")
        return False, None

    stored_enc = b64_to_encoding(stored_b64_encoding)
    if stored_enc is None:
        return False, None

    live_enc = extract_face_encoding(live_b64_image)
    if live_enc is None:
        return False, None  # No face detected in live image or api failed

    # Cosine similarity (both are L2-normalised → dot product = cosine)
    similarity = float(np.dot(stored_enc, live_enc))
    matched = similarity >= threshold
    logger.info(f"Face verification: similarity={similarity:.3f}, matched={matched}")
    return matched, round(similarity, 3)

def get_face_app():
    # Backwards compatibility for app.py imports, does nothing
    pass
