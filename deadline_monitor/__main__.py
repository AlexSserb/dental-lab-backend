import logging

from deadline_monitor.worker import handler

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
print(handler({}, None))
