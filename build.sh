#!/bin/bash
# Build script for Render.com

set -o errexit

echo "Installing requirements..."
pip install -r requirements.txt

echo "Running migrations / seeding database..."
python -m app.seed

echo "Build complete."
