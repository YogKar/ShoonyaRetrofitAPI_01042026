#!/bin/bash

# Configuration
REPO_URL="https://github.com/YogKar/ShoonyaRetrofitAPI_01042026.git"
FOLDER_NAME="ShoonyaRetrofit_Live"

echo "=== Starting Shoonya API Installation ==="

# 1. Clone repository
if [ -d "$FOLDER_NAME" ]; then
    echo "Removing existing folder..."
    rm -rf "$FOLDER_NAME"
fi

git clone "$REPO_URL" "$FOLDER_NAME"
cd "$FOLDER_NAME" || exit

# 2. Install Wheel and Dependencies
echo "Installing NorenRestApiPy and dependencies..."
py -m pip install *.whl pandas
if [ -f "requirements.txt" ]; then
    py -m pip install -r requirements.txt
fi

# 3. Finalize
echo "=================================================="
echo "INSTALLATION COMPLETE!"
echo "To run the test, use:"
echo "py Test_Noren_API.py"
echo "=================================================="
