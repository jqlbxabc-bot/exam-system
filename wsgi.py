import os

# Ensure runtime compatibility hooks are active before importing the Flask app.
import sitecustomize  # noqa: F401
import ocr_patches  # noqa: F401

from app import app
from ocr_diagnostics import register_ocr_diagnostics
from runtime_patches import apply_runtime_patches

apply_runtime_patches(app)
register_ocr_diagnostics(app)

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5001))
    app.run(host='0.0.0.0', port=port)
