import os

# Ensure runtime compatibility hooks are active before importing the Flask app.
import sitecustomize  # noqa: F401
import runtime_ai_patch  # noqa: F401
import ocr_patches  # noqa: F401
import runtime_exam_recognition_patch  # noqa: F401

from app import app
from ai_diagnostics import register_ai_diagnostics
from ocr_diagnostics import register_ocr_diagnostics
from recognition_diagnostics import register_recognition_diagnostics
from runtime_patches import apply_runtime_patches

apply_runtime_patches(app)
register_ocr_diagnostics(app)
register_ai_diagnostics(app)
register_recognition_diagnostics(app)

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5001))
    app.run(host='0.0.0.0', port=port)
