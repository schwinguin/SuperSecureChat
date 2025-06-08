#!/usr/bin/env python3
"""
P2P Chat Test Launcher
Alternative Python script to launch two instances for testing
"""

import subprocess
import sys
import time
import os
import platform
from pathlib import Path

def print_banner():
    print("🚀 P2P Chat Test Environment")
    print("=" * 40)
    print()
    print("This script will launch two chat instances:")
    print("1. Instance 1 (Chat Creator)")
    print("2. Instance 2 (Chat Joiner)")
    print()
    print("📋 Testing Flow:")
    print("   1️⃣  Instance 1: Click 'Create Chat' → Copy invite key")
    print("   2️⃣  Instance 2: Click 'Join Chat' → Paste invite key → Copy return key")
    print("   3️⃣  Instance 1: Paste return key → Click 'Connect'")
    print("   4️⃣  Start chatting! 💬")
    print()

def check_dependencies():
    """Check if required dependencies are installed"""
    try:
        import aiortc
        import pyee
        print("✅ Dependencies check passed")
        return True
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("Please run: pip install -r requirements.txt")
        return False

def launch_instance(instance_name, delay=0):
    """Launch a single instance of the P2P chat application"""
    if delay > 0:
        time.sleep(delay)
    
    print(f"📱 Launching {instance_name}...")
    
    # Get the current directory
    current_dir = Path.cwd()
    
    try:
        # Launch the application
        if platform.system() == "Windows":
            # Windows
            subprocess.Popen([
                sys.executable, "-m", "p2p_chat"
            ], cwd=current_dir, creationflags=subprocess.CREATE_NEW_CONSOLE)
        else:
            # Linux/macOS - try to launch in a new terminal
            terminal_commands = [
                # GNOME Terminal
                ["gnome-terminal", "--title", f"P2P Chat - {instance_name}", 
                 "--geometry", "80x30", "--", "python", "-m", "p2p_chat"],
                # XTerm
                ["xterm", "-title", f"P2P Chat - {instance_name}", 
                 "-geometry", "80x30", "-e", "python", "-m", "p2p_chat"],
                # Konsole (KDE)
                ["konsole", "--title", f"P2P Chat - {instance_name}", 
                 "-e", "python", "-m", "p2p_chat"],
                # MATE Terminal
                ["mate-terminal", "--title", f"P2P Chat - {instance_name}", 
                 "--geometry", "80x30", "-e", "python -m p2p_chat"],
                # Terminator
                ["terminator", "--title", f"P2P Chat - {instance_name}", 
                 "--geometry", "80x30", "-e", "python -m p2p_chat"],
            ]
            
            launched = False
            for cmd in terminal_commands:
                try:
                    subprocess.Popen(cmd, cwd=current_dir)
                    launched = True
                    break
                except FileNotFoundError:
                    continue
            
            if not launched:
                print(f"⚠️  Could not launch {instance_name} in a new terminal.")
                print("Launching in background instead...")
                subprocess.Popen([sys.executable, "-m", "p2p_chat"], cwd=current_dir)
        
        print(f"✅ {instance_name} launched successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Failed to launch {instance_name}: {e}")
        return False

def main():
    """Main function to launch both instances"""
    print_banner()
    
    # Check if we're in the right directory
    if not Path("p2p_chat").exists():
        print("❌ Error: p2p_chat package not found!")
        print("Make sure you're running this script from the p2p_chat directory")
        sys.exit(1)
    
    # Check dependencies
    if not check_dependencies():
        sys.exit(1)
    
    print()
    input("Press Enter to launch both instances...")
    print()
    
    # Launch instances
    success1 = launch_instance("Instance 1 (Creator)")
    time.sleep(2)  # Small delay between launches
    success2 = launch_instance("Instance 2 (Joiner)")
    
    if success1 and success2:
        print()
        print("🎉 Both instances launched successfully!")
        print()
        print("📋 Next Steps:")
        print("   1. In Instance 1: Click 'Create Chat'")
        print("   2. Copy the invite key from Instance 1")
        print("   3. In Instance 2: Click 'Join Chat' and paste the invite key")
        print("   4. Copy the return key from Instance 2")
        print("   5. Paste the return key in Instance 1 and click 'Connect'")
        print("   6. Start chatting securely! 🔒")
        print()
        print("Press Ctrl+C to exit this launcher (won't close chat windows)")
        
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n👋 Launcher exiting. Chat windows will remain open.")
    else:
        print("❌ Failed to launch one or both instances")
        sys.exit(1)

if __name__ == "__main__":
    main() 