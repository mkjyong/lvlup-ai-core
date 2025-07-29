"""Package entrypoint: `python -m data_ingest` → starts the ingest daemon."""

from data_ingest.daemon import main

if __name__ == "__main__":
    main() 