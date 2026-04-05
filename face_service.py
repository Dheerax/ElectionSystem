"""
face_service.py — ArcFace face encoding and verification using InsightFace.

On first use, InsightFace downloads the `buffalo_sc` model (~85 MB) into
~/.insightface/models/. Subsequent calls use the cached model.
"""

import base64
import logging
import numpy as np
from io import BytesIO
from PIL import Image

logger = logging.getLogger(__name__)

_face_app = None  # Lazy-loaded singleton


def get_face_app():
    """Lazy-load the InsightFace ArcFace model (buffalo_sc for speed)."""
    global _face_app
    if _face_app is None:
        try:
            import os
            os.environ['OMP_NUM_THREADS'] = '1'
            import insightface
            from insightface.app import FaceAnalysis
            model_path = os.path.join(os.path.dirname(__file__), 'insightface_model')
            app = FaceAnalysis(name='buffalo_sc', root=model_path, allowed_modules=['detection', 'recognition'], providers=['CPUExecutionProvider'])
            app.prepare(ctx_id=0, det_size=(320, 320))
            _face_app = app
            logger.info("InsightFace ArcFace model loaded successfully from local directory.")
        except Exception as e:
            logger.error(f"Failed to load InsightFace model: {e}")
            _face_app = None
    return _face_app


def _base64_to_cv2(b64_string):
    """Convert base64 image string (data:image/...;base64,...) to numpy BGR array."""
    import cv2
    try:
        if ',' in b64_string:
            b64_string = b64_string.split(',', 1)[1]
        img_bytes = base64.b64decode(b64_string)
        pil_img = Image.open(BytesIO(img_bytes)).convert('RGB')
        
        # --- RESIZE IMAGE TO SAVE MASSIVE MEMORY ON RENDER ---
        # 640x640 is plenty for face recognition, but stops 1080p+ webcams from 
        # blowing out the 512MB RAM limit during ONNX inference pyramids
        pil_img.thumbnail((640, 640), Image.Resampling.LANCZOS)
        
        img_np = np.array(pil_img)
        # PIL is RGB, convert to BGR for cv2/InsightFace
        img_bgr = img_np[:, :, ::-1].copy()
        return img_bgr
    except Exception as e:
        logger.error(f"base64_to_cv2 failed: {e}")
        return None


def extract_face_encoding(b64_image):
    """
    Given a base64 image string, detect a face and return its 512-d ArcFace embedding.
    Returns:
        numpy array (512,) if face found
        None if no face detected or model unavailable
    """
    app = get_face_app()
    if app is None:
        logger.warning("ArcFace model not available; skipping encoding.")
        return None

    img = _base64_to_cv2(b64_image)
    if img is None:
        return None

    try:
        faces = app.get(img)
        if not faces:
            logger.info("No face detected in image.")
            return None
        # Use the face with the largest detection bbox
        face = max(faces, key=lambda f: (f.bbox[2] - f.bbox[0]) * (f.bbox[3] - f.bbox[1]))
        return face.normed_embedding  # 512-d L2-normalised vector
    except Exception as e:
        logger.error(f"Face encoding extraction failed: {e}")
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

    Returns:
        (True, similarity)  — face matched
        (False, similarity) — face did not match or could not be extracted
        (False, None)       — model unavailable or no face in live image
    """
    if not stored_b64_encoding:
        logger.warning("No stored face encoding for this voter.")
        return False, None

    stored_enc = b64_to_encoding(stored_b64_encoding)
    if stored_enc is None:
        return False, None

    live_enc = extract_face_encoding(live_b64_image)
    if live_enc is None:
        return False, None  # No face detected in live image

    # Cosine similarity (both are L2-normalised → dot product = cosine)
    similarity = float(np.dot(stored_enc, live_enc))
    matched = similarity >= threshold
    logger.info(f"Face verification: similarity={similarity:.3f}, matched={matched}")
    return matched, round(similarity, 3)
