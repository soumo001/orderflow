import time

from app.database.session import SessionLocal
from app.modules.events import process_pending_events


def run() -> None:
    while True:
        with SessionLocal() as db:
            process_pending_events(db)
        time.sleep(2)


if __name__ == "__main__":
    run()
