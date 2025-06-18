from drive_sync import DriveSync, DriveConfig
import argparse
import logging
import time
import signal
import sys

def parse_arguments():
    parser = argparse.ArgumentParser(description='Google Drive File Sync Tool')
    parser.add_argument('--folder-name', default='CodeSync',
                       help='Name of the folder in Google Drive')
    parser.add_argument('--file-types', default='.py',
                       help='Comma-separated file extensions to sync (e.g., .py,.txt)')
    parser.add_argument('--interval', type=int, default=120,
                       help='Sync interval in seconds')
    parser.add_argument('--changelog-dir', default='changelogs',
                       help='Directory to store changelogs')
    parser.add_argument('--debug', action='store_true',
                       help='Enable debug logging')
    parser.add_argument('--view-changes', type=str,
                       help='View changelog for specific file')
    return parser.parse_args()

def signal_handler(signum, frame):
    """Handle interrupt signals"""
    print("\nShutting down gracefully... (Press Ctrl+C again to force)")
    if hasattr(signal_handler, 'triggered'):
        print("\nForce quitting...")
        sys.exit(1)
    signal_handler.triggered = True
    if 'sync' in globals() and sync is not None:
        sync.stop_sync()
    sys.exit(0)

def main():
    args = parse_arguments()
    config = DriveConfig(
        folder_name=args.folder_name,
        file_types=tuple(args.file_types.split(',')),
        sync_interval=args.interval,
        changelog_dir=args.changelog_dir,
        log_level=logging.DEBUG if args.debug else logging.INFO
    )

    # Set up signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    global sync  # Make sync accessible to signal handler
    sync = DriveSync(config)

    try:
        sync.start_sync(interval=config.sync_interval)
        print(f"Drive Sync started with configuration:")
        print(f"- Folder: {config.folder_name}")
        print(f"- File types: {', '.join(config.file_types)}")
        print(f"- Interval: {config.sync_interval} seconds")
        print("Press Ctrl+C to stop")
        
        # Main loop with better signal handling
        while sync.running:
            time.sleep(1)
            
    except Exception as e:
        logging.error(f"Error: {str(e)}")
        sync.stop_sync()
        sys.exit(1)

if __name__ == "__main__":
    main()