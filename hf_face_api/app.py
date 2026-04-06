import base64
import numpy as np
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import insightface
from insightface.app import FaceAnalysis
import cv2
from io import BytesIO
from PIL import Image
import os
import uvicorn
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app_hf = FastAPI()

# Prepare FaceAnalysis model
try:
    logger.info("Initializing InsightFace model...")
    face_app = FaceAnalysis(name='buffalo_sc', allowed_modules=['detection', 'recognition'], providers=['CPUExecutionProvider'])
    face_app.prepare(ctx_id=0, det_size=(320, 320))
    logger.info("Model loaded successfully.")
except Exception as e:
    logger.error(f"Failed to load model: {e}")
    face_app = None

class ImagePayload(BaseModel):
    b64_image: str

@app_hf.post("/encode")
def encode_face(payload: ImagePayload):
    if face_app is None:
        raise HTTPException(status_code=500, detail="AI Model failed to initialize")
        
    try:
        b64_string = payload.b64_image
        if ',' in b64_string:
            b64_string = b64_string.split(',', 1)[1]
            
        img_bytes = base64.b64decode(b64_string)
        pil_img = Image.open(BytesIO(img_bytes)).convert('RGB')
        
        # Max resolution to prevent local memory issues just in case
        pil_img.thumbnail((640, 640), Image.Resampling.LANCZOS)
        
        img_np = np.array(pil_img)
        img_bgr = img_np[:, :, ::-1].copy()
        
        faces = face_app.get(img_bgr)
        if not faces:
            return {"success": False, "error": "No face detected"}
            
        # Get the largest face if multiple
        faces = sorted(faces, key=lambda x: (x.bbox[2]-x.bbox[0]) * (x.bbox[3]-x.bbox[1]), reverse=True)
        face = faces[0]
        
        # Convert NumPy embedding to standard list for JSON serialization
        embedding_list = face.embedding.tolist()
        return {"success": True, "embedding": embedding_list}
        
    except Exception as e:
        logger.error(f"Face encoding error: {e}")
        return {"success": False, "error": str(e)}

@app_hf.post("/verify")
def verify_face(payload: dict):
    # Accepts 'embedding1' and 'embedding2' (both list of floats)
    # This can be used if you want the API to do the math, but your
    # Render server currently computes cosine similarity itself beautifully.
    pass

@app_hf.get("/")
def read_root():
    return {"status": "Smart Election Face API is running", "memory": os.popen('free -m').read() if os.name != 'nt' else "Windows"}

if __name__ == "__main__":
    uvicorn.run("app:app_hf", host="0.0.0.0", port=7860)
