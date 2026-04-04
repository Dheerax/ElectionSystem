import sys
import base64
print("Loading face_service...")
try:
    from face_service import get_face_app, extract_face_encoding
    
    # create a dummy blank image using PIL
    from PIL import Image
    from io import BytesIO
    img = Image.new('RGB', (640, 480), color = 'white')
    buffer = BytesIO()
    img.save(buffer, format="JPEG")
    b64_photo = "data:image/jpeg;base64," + base64.b64encode(buffer.getvalue()).decode()

    print("Extracting face encoding...")
    res = extract_face_encoding(b64_photo)
    print("Done. Result:", type(res))
except Exception as e:
    print("Exception caught:", e)
