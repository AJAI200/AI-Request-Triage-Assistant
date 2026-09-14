#!/usr/bin/env bash
# Exit immediately if a command exits with a non-zero status
set -o errexit

echo "Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

echo "Building React Frontend bundle..."
npm --prefix frontend install
npm --prefix frontend run build

echo "Build completed successfully!"
