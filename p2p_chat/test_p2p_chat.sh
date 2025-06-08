#!/bin/bash

# P2P Chat Test Script
# This script launches two instances of the P2P chat application for testing

echo "🚀 Starting P2P Chat Test Environment..."
echo ""
echo "Instructions:"
echo "1. Instance 1 will open first - Click 'Create Chat' and copy the invite key"
echo "2. Instance 2 will open second - Click 'Join Chat' and paste the invite key"
echo "3. Copy the return key from Instance 2"
echo "4. Paste the return key in Instance 1 and click 'Connect'"
echo "5. Start chatting securely!"
echo ""
echo "Press any key to continue..."
read -n 1 -s

# Check if we're in a virtual environment
if [[ "$VIRTUAL_ENV" == "" ]]; then
    echo "⚠️  Warning: No virtual environment detected."
    echo "Make sure you've activated the venv: source venv/bin/activate"
    echo ""
fi

# Function to check if application can run
check_requirements() {
    if ! python -c "import aiortc, pyee" 2>/dev/null; then
        echo "❌ Missing dependencies. Please run: pip install -r requirements.txt"
        exit 1
    fi
}

# Check if we can run the application
check_requirements

echo "✅ Dependencies check passed"
echo ""

# Try different terminal emulators
launch_terminal() {
    local title="$1"
    local command="$2"
    
    if command -v gnome-terminal &> /dev/null; then
        gnome-terminal --title="$title" --geometry=80x30 -- bash -c "$command; read -p 'Press Enter to close...'"
    elif command -v xterm &> /dev/null; then
        xterm -title "$title" -geometry 80x30 -e bash -c "$command; read -p 'Press Enter to close...'" &
    elif command -v konsole &> /dev/null; then
        konsole --title "$title" -e bash -c "$command; read -p 'Press Enter to close...'" &
    elif command -v mate-terminal &> /dev/null; then
        mate-terminal --title="$title" --geometry=80x30 -e "bash -c '$command; read -p \"Press Enter to close...\"'" &
    elif command -v terminator &> /dev/null; then
        terminator --title="$title" --geometry=80x30 -e "bash -c '$command; read -p \"Press Enter to close...\"'" &
    else
        echo "❌ No supported terminal emulator found!"
        echo "Please install one of: gnome-terminal, xterm, konsole, mate-terminal, or terminator"
        exit 1
    fi
}

echo "🔧 Launching P2P Chat instances..."

# Launch first instance (Chat Creator)
echo "📱 Opening Instance 1 (Chat Creator)..."
launch_terminal "P2P Chat - Instance 1 (Creator)" "cd '$(pwd)' && python -m p2p_chat"

# Wait a moment before launching second instance
sleep 2

# Launch second instance (Chat Joiner)  
echo "📱 Opening Instance 2 (Chat Joiner)..."
launch_terminal "P2P Chat - Instance 2 (Joiner)" "cd '$(pwd)' && python -m p2p_chat"

echo ""
echo "✅ Both instances launched!"
echo ""
echo "📋 Testing Instructions:"
echo "   1️⃣  In Instance 1: Click 'Create Chat'"
echo "   2️⃣  Copy the invite key from Instance 1"
echo "   3️⃣  In Instance 2: Click 'Join Chat'"
echo "   4️⃣  Paste the invite key in Instance 2"
echo "   5️⃣  Copy the return key from Instance 2"
echo "   6️⃣  Paste the return key in Instance 1 and click 'Connect'"
echo "   7️⃣  Start chatting! 💬"
echo ""
echo "🔒 Your communication will be end-to-end encrypted via WebRTC!"
echo ""
echo "Press Ctrl+C to exit this script (won't close the chat windows)"

# Keep script running so user can see instructions
while true; do
    sleep 1
done 