from locust.env import Environment
from locust.log import setup_logging
from locust.stats import stats_printer, stats_history
import importlib.util
import gevent
import sys
import os


def start_locust_master(locustfile_path, host="http://example.com", web_port=8089, master_bind_host="0.0.0.0", master_bind_port=5557):
    setup_logging("INFO", None)

    # Dynamically load the locustfile module
    spec = importlib.util.spec_from_file_location("locustfile", locustfile_path)
    locustfile = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(locustfile)

    # Extract user classes from locustfile
    user_classes = [
        getattr(locustfile, attr) for attr in dir(locustfile)
        if isinstance(getattr(locustfile, attr), type)
        and hasattr(getattr(locustfile, attr), "tasks")
    ]

    # Setup Locust environment
    env = Environment(user_classes=user_classes, host=host, reset_stats=True)

    # Initialize master runner
    env.create_master_runner(master_bind_host=master_bind_host, master_bind_port=master_bind_port)

    # Create and start Locust Web UI
    env.create_web_ui(host="0.0.0.0", port=web_port)

    # Optional: print and log stats
    gevent.spawn(stats_printer(env.stats))
    gevent.spawn(stats_history(env.runner))

    print(f"✅ Locust master running! Access Web UI at: http://localhost:{web_port}")

    try:
        env.runner.greenlet.join()
    except KeyboardInterrupt:
        print("🛑 Stopping Locust master...")
        env.web_ui.stop()


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python locust_runner.py <path_to_locustfile.py>")
        sys.exit(1)

    locustfile_path = sys.argv[1]

    if not os.path.exists(locustfile_path):
        print(f"❌ File not found: {locustfile_path}")
        sys.exit(1)

    start_locust_master(locustfile_path)