#!/usr/bin/env python3
"""Entry point for fetching annotations."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from pipeline.retrieve import retrieve, tasks
from pipeline.is_ready import properties_adequate
from pipeline import log as logging


def run_all(force: bool = False):
    """
    Main entry point that validates and runs all tasks.
    
    Args:
        force: If True, skip validation and proceed anyway
    """
    logging.log("Going through experiment directories to verify our annotation sources")
    
    error, success = properties_adequate.main()
    
    if error and not force:
        logging.log("Failed validation - annotation sources not sufficient, see err")
        logging.err(error)
        sys.exit(1)
    else:
        if success:
            logging.log("Validated annotation sources contain the array designs we need")
        
        all_tasks = tasks.all_tasks()
        exit_code = retrieve.perform_biomart_tasks(all_tasks)
        sys.exit(exit_code)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Start annotation fetching pipeline')
    parser.add_argument('--force', action='store_true',
                        help='Force execution even if validation fails')
    
    args = parser.parse_args()
    
    run_all(force=args.force)
