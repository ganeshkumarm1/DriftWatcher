"""Command-line interface for Drift Watcher."""
import argparse
import sys
import os
import time
import signal
import subprocess
from pathlib import Path


def get_data_dir():
    """Get or create the data directory for Drift Watcher."""
    data_dir = Path.home() / ".drift-watcher"
    data_dir.mkdir(exist_ok=True)
    return data_dir


def is_server_running(host="127.0.0.1", port=3333):
    """Check if the event server is running."""
    import socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.connect((host, port))
        sock.close()
        return True
    except:
        return False


def start_server_background(host="127.0.0.1", port=3333):
    """Start the event server in the background."""
    data_dir = get_data_dir()
    
    # Start server as subprocess
    process = subprocess.Popen(
        [sys.executable, "-m", "drift_watcher.tracking.server"],
        cwd=str(data_dir),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True
    )
    
    # Wait for server to start
    for _ in range(10):
        if is_server_running(host, port):
            return process
        time.sleep(0.5)
    
    return process


def main():
    """Main entry point for drift-watcher command."""
    parser = argparse.ArgumentParser(
        description="Drift Watcher - Personal focus monitoring system"
    )
    parser.add_argument(
        "--goal",
        type=str,
        help="Set your focus goal"
    )
    parser.add_argument(
        "--config",
        type=str,
        default=None,
        help="Path to config file (default: ~/.drift-watcher/config.json)"
    )
    parser.add_argument(
        "--test-notification",
        action="store_true",
        help="Test notification system and exit"
    )
    parser.add_argument(
        "--no-server",
        action="store_true",
        help="Don't auto-start the event server"
    )
    parser.add_argument(
        "--keep-server",
        action="store_true",
        help="Keep server running after agent stops"
    )
    
    args = parser.parse_args()
    
    # Set default config path
    if args.config is None:
        data_dir = get_data_dir()
        args.config = str(data_dir / "config.json")
        
        # Create default config if it doesn't exist
        if not Path(args.config).exists():
            import json
            default_config = {
                "llm": {
                    "model_id": "anthropic.claude-3-5-sonnet-20240620-v1:0",
                    "region_name": "us-east-1"
                },
                "agent": {
                    "window_seconds": 30,
                    "drift_confidence_threshold": 0.7,
                    "log_retention_days": 7
                },
                "server": {
                    "host": "127.0.0.1",
                    "port": 3333
                }
            }
            with open(args.config, "w") as f:
                json.dump(default_config, f, indent=2)
            print(f"📋 Created config at {args.config}")
    
    # Test notification
    if args.test_notification:
        from .utils import Notifier
        notifier = Notifier()
        notifier.notify_drift("Test Goal", 0.95)
        print("✅ Test notification sent!")
        return
    
    # Auto-start server if not running
    server_process = None
    server_was_started = False
    if not args.no_server:
        if not is_server_running():
            print("🌐 Starting event server...")
            server_process = start_server_background()
            server_was_started = True
            if is_server_running():
                print("✅ Event server started")
            else:
                print("⚠️  Server may not have started. Check manually.")
        else:
            print("✅ Event server already running")
    
    # Setup cleanup handler
    def cleanup(signum=None, frame=None):
        """Clean up on exit."""
        print("\n\n🛑 Drift Watcher stopped")
        
        # Kill server if we started it and user didn't request to keep it
        if server_process and server_was_started and not args.keep_server:
            try:
                server_process.terminate()
                server_process.wait(timeout=2)
                print("🛑 Event server stopped")
            except:
                try:
                    server_process.kill()
                    print("🛑 Event server killed")
                except:
                    pass
        
        sys.exit(0)
    
    # Register signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, cleanup)
    signal.signal(signal.SIGTERM, cleanup)
    
    # Change to data directory for events.log
    os.chdir(get_data_dir())
    
    print("\n💡 Press Ctrl+C to stop Drift Watcher\n")
    
    try:
        # Run agent
        from .core.agent import run_agent_loop
        run_agent_loop(config_file=args.config, goal=args.goal)
    except KeyboardInterrupt:
        cleanup()
    except Exception as e:
        print(f"\n⚠️  Unexpected error: {e}")
        cleanup()


def server():
    """Entry point for drift-watcher-server command."""
    parser = argparse.ArgumentParser(
        description="Drift Watcher Event Server"
    )
    parser.add_argument(
        "--config",
        type=str,
        default=None,
        help="Path to config file (default: ~/.drift-watcher/config.json)"
    )
    parser.add_argument(
        "--host",
        type=str,
        default="127.0.0.1",
        help="Server host (default: 127.0.0.1)"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=3333,
        help="Server port (default: 3333)"
    )
    
    args = parser.parse_args()
    
    # Set default config path
    if args.config is None:
        data_dir = get_data_dir()
        args.config = str(data_dir / "config.json")
    
    # Change to data directory for events.log
    os.chdir(get_data_dir())
    
    # Run server
    from .tracking.server import EventServer
    server = EventServer(
        events_file="events.log",
        host=args.host,
        port=args.port
    )
    print(f"🌐 Event server starting on {args.host}:{args.port}")
    print(f"📁 Data directory: {get_data_dir()}")
    server.run()


def manage_goal():
    """Entry point for drift-watcher-goal command."""
    parser = argparse.ArgumentParser(
        description="Manage Drift Watcher goals"
    )
    parser.add_argument(
        "--set",
        type=str,
        help="Set a new goal"
    )
    
    args = parser.parse_args()
    
    data_dir = get_data_dir()
    os.chdir(data_dir)
    
    from .core.state_manager import StateManager
    
    state_manager = StateManager()
    
    if args.set:
        state = state_manager.reset_logs_on_goal_change(args.set)
        print(f"✓ Goal updated: {args.set}")
    else:
        state = state_manager.load()
        print("=" * 60)
        print("Current Focus Goal")
        print("=" * 60)
        print()
        print(f"🎯 {state.get('goal', 'No goal set')}")
        print()
        print(f"State: {state.get('focus_state', 'UNKNOWN')}")
        print(f"Confidence: {state.get('confidence', 0.0)}")
        print("=" * 60)

    if args.provider in ["openai", "anthropic"]:
        print(f"\n⚠️  Don't forget to add your API key to {args.config}")


if __name__ == "__main__":
    main()
