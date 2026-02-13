#!/usr/bin/env python3
"""Main retrieval module for BioMart data."""
import time
import sys
from pathlib import Path
from typing import List, Tuple, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from pipeline.retrieve import biomart, tasks, transform
from pipeline import paths, log as logging
from util import combinators


def line_ok(line: str) -> bool:
    """Check if a line is valid (non-empty first column)."""
    first_col = line.split('\t', 1)[0] if '\t' in line else line
    return len(first_col.strip()) > 0


def read_result(line: str) -> Tuple[Optional[str], Optional[Tuple[str, Optional[str]]]]:
    """
    Parse a result line.
    
    Returns:
        (None, (key, value)) on success
        (error_message, None) on invalid line
    """
    if not line_ok(line):
        return (None, None)  # Skip empty lines
    
    # Check for valid characters
    if not all(c.isprintable() or c in '\t\n' for c in line):
        return (f"Result contains invalid line: {line}", None)
    
    parts = line.split('\t')
    
    if len(parts) == 1:
        return (None, (parts[0], None))
    elif len(parts) >= 2:
        return (None, (parts[0], parts[1] if parts[1] else None))
    else:
        return (f"Result contains invalid line: {line}", None)


def perform_biomart_task(aux: dict, task: tasks.BioMartTask) -> Tuple[Optional[str], Optional[str]]:
    """
    Perform a single BioMart task.
    
    Returns:
        (None, message) on success
        (error_message, None) on failure
    """
    t0 = time.time()
    
    # Execute all queries for this task
    all_results = []
    all_errors = []
    
    for filters, attributes in task.queries:
        error, lines = biomart.fetch_from_biomart(aux, task.annotation_source, filters, attributes)
        
        if error:
            all_errors.append(error)
        else:
            # Parse each line
            for line in lines:
                error, result = read_result(line)
                if error:
                    all_errors.append(error)
                elif result:
                    all_results.append(result)
    
    # Transform results
    transformed = transform.transform(task, all_results)
    
    # Sort and deduplicate
    unique_results = sorted(set(transformed))
    
    # Format output lines
    output_lines = []
    for key, value in unique_results:
        if value is not None:
            output_lines.append(f"{key}\t{value}\n")
        else:
            output_lines.append(f"{key}\t\n")
    
    # Write results
    elapsed = time.time() - t0
    message = f"Retrieved data for {task} in {int(elapsed * 1000)} ms"
    
    # Ensure destination directory exists
    task.destination.parent.mkdir(parents=True, exist_ok=True)
    
    paths.write_result(
        destination=task.destination,
        result=iter(output_lines),
        has_errors=len(all_errors) > 0
    )
    
    if all_errors:
        error_msg = f"{message}\n ERRORS: \n" + "\n".join(all_errors)
        return (error_msg, None)
    else:
        return (None, message)


def validate_destinations_unique(tasks_list: List[tasks.BioMartTask]) -> Tuple[Optional[List[str]], Optional[bool]]:
    """Validate that all task destinations are unique."""
    dest_map = {}
    for task in tasks_list:
        dest = task.destination
        if dest not in dest_map:
            dest_map[dest] = []
        dest_map[dest].append(task)
    
    errors = []
    for dest, task_list in dest_map.items():
        if len(task_list) > 1:
            errors.append(f"Conflicting - same destinations: {', '.join(str(t) for t in task_list)}")
    
    if errors:
        return (errors, None)
    else:
        return (None, True)


def validate_attributes_present_in_biomart(tasks_list: List[tasks.BioMartTask]) -> Tuple[Optional[List[str]], Optional[bool]]:
    """Validate that all required attributes are present in BioMart."""
    # Group tasks by annotation source
    by_source = {}
    for task in tasks_list:
        source = task.annotation_source
        if source not in by_source:
            by_source[source] = set()
        by_source[source].update(task.ensembl_attributes_involved())
    
    errors = []
    for source, required_attrs in by_source.items():
        error, attributes = biomart.lookup_attributes(source)
        
        if error:
            errors.append(error)
        else:
            available_attrs = {attr.property_name for attr in attributes}
            missing = required_attrs - available_attrs
            
            if missing:
                errors.append(
                    f"Validation error, properties for annotationSource {source} not found in BioMart as valid attributes: {', '.join(missing)}"
                )
    
    if errors:
        return (errors, None)
    else:
        return (None, True)


def validate(tasks_list: List[tasks.BioMartTask]) -> Tuple[Optional[List[str]], Optional[bool]]:
    """Validate tasks before execution."""
    validations = [
        validate_destinations_unique(tasks_list),
        validate_attributes_present_in_biomart(tasks_list)
    ]
    
    all_errors = []
    for error, _ in validations:
        if error:
            all_errors.extend(error)
    
    if all_errors:
        return (all_errors, None)
    else:
        return (None, True)


def simply_validate():
    """Just validate tasks without executing them."""
    tasks_to_validate = tasks.all_tasks()
    error, _ = validate(tasks_to_validate)
    
    if error:
        logging.err(error)
        sys.exit(1)
    else:
        logging.log(f"Validated {len(tasks_to_validate)} tasks")


def perform_biomart_tasks(tasks_list: List[tasks.BioMartTask]) -> int:
    """
    Perform all BioMart tasks.
    
    Returns:
        0 on success, error count on failure
    """
    # Filter out already completed tasks
    tasks_to_complete = [t for t in tasks_list if not t.seems_done()]
    
    if len(tasks_to_complete) < len(tasks_list):
        logging.log(f"Skipped tasks that seem completed, remaining {len(tasks_to_complete)} tasks")
    
    logging.log(f"Validating {len(tasks_to_complete)} tasks")
    
    error, _ = validate(tasks_to_complete)
    if error:
        logging.err(error)
        return 1
    
    logging.log(f"Validated {len(tasks_to_complete)} tasks")
    
    # Get auxiliary info for all annotation sources
    sources = list(set(t.annotation_source for t in tasks_to_complete))
    error, auxiliary_info = biomart.BiomartAuxiliaryInfo.get_map(sources)
    
    if error:
        logging.err("Failed retrieving auxiliary info:")
        logging.err(error)
        return 1
    
    logging.log(f"Retrieved auxiliary info of {len(auxiliary_info)} items")
    
    # Execute tasks in parallel
    error_count = 0
    
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = {
            executor.submit(perform_biomart_task, auxiliary_info, task): task
            for task in tasks_to_complete
        }
        
        for future in as_completed(futures):
            task = futures[future]
            try:
                error, message = future.result()
                if error:
                    logging.err(error)
                    error_count += 1
                else:
                    logging.log(message)
            except Exception as e:
                logging.err(f"Task {task} generated an exception: {e}")
                error_count += 1
    
    logging.log("Finished!")
    return error_count


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Retrieve BioMart annotations')
    parser.add_argument('--validate-only', action='store_true',
                        help='Only validate, do not execute tasks')
    
    args = parser.parse_args()
    
    if args.validate_only:
        simply_validate()
    else:
        all_tasks_list = tasks.all_tasks()
        exit_code = perform_biomart_tasks(all_tasks_list)
        sys.exit(exit_code)
