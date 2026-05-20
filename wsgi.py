import os

# Ensure runtime compatibility hooks are active before importing the Flask app.
import sitecustomize  # noqa: F401

from app import app

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5001))
    app.run(host='0.0.0.0', port=port)
