#!/bin/bash
cd /home/andre/Documents/GitHub/SuperSecureChat/p2p_chat
export PYTHONPATH=/home/andre/Documents/GitHub/SuperSecureChat/p2p_chat/venv/lib/python3.11/site-packages
echo "🚀 Starting P2P Chat Application..."
echo "✅ Virtual environment: $(./venv/bin/python --version)"
echo "📁 Working directory: $(pwd)"
echo "🔧 Starting application..."
./venv/bin/python -m p2p_chat
