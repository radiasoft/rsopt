import pandas as pd
import re
from typing import List, Dict, Any, Optional
from ruamel.yaml import YAML
from pathlib import Path
import glob

# Global variable for simulation directory formatting
SIM_DIR_WIDTH = 4

def parse_worker_line(line: str) -> Dict[str, Any]:
    """
    Parses a single worker line from the log file into a dictionary.

    Args:
        line: A string representing a single worker log line.

    Returns:
        A dictionary containing the parsed data from the line.
    """
    # capture the main components of the worker line.
    main_pattern = re.compile(
        r"Worker\s+(?P<Worker>\d+):\s+"
        r"sim_id\s+(?P<sim_id>\d+):\s+"
        r"sim Time:\s+(?P<sim_Time>[\d\.]+)\s+"
        r"Start:\s+(?P<Start>[\d\-:\s\.]+)\s+"
        r"End:\s+(?P<End>[\d\-:\s\.]+)"
    )
    
    # finds all occurrences of Task data in the line.
    task_pattern = re.compile(
        r"Task\s+(?P<task_id>\d+):\s+(?P<task_time>[\d\.]+)\s+"
        r"Tstart:\s+(?P<Tstart>[\d\-:\s\.]+)\s+"
        r"Tend:\s+(?P<Tend>[\d\-:\s\.]+)"
    )

    # final status message.
    status_pattern = re.compile(r"Status:\s+(?P<Status>.+?)$")

    data = {}
    
    # Extract main worker data
    main_match = main_pattern.search(line)
    if main_match:
        # Convert numerical fields to appropriate types
        main_data = main_match.groupdict()
        data['Worker'] = int(main_data['Worker'])
        data['sim_id'] = int(main_data['sim_id'])
        data['sim_Time'] = float(main_data['sim_Time'])
        data['Start'] = main_data['Start'].strip()
        data['End'] = main_data['End'].strip()

    # Extract all task data
    task_matches = task_pattern.finditer(line)
    for match in task_matches:
        task_data = match.groupdict()
        task_id = task_data['task_id']
        data[f'Task_{task_id}_Time'] = float(task_data['task_time'])
        data[f'Task_{task_id}_Tstart'] = task_data['Tstart'].strip()
        data[f'Task_{task_id}_Tend'] = task_data['Tend'].strip()
        
    # Extract status
    status_match = status_pattern.search(line)
    if status_match:
        data['Status'] = status_match.group('Status').strip()

    return data

def parse_libe_log_to_dataframes(filepath: str) -> List[pd.DataFrame]:
    """
    Parses a libEnsemble log file and segments it into runs.

    Each run is defined by the text between 'starting ensemble' and 
    'exiting ensemble'. Manager and generator timing lines are discarded.

    Args:
        filepath: The path to the libEnsemble log file.

    Returns:
        A list of pandas DataFrames, where each DataFrame represents one run.
    """
    try:
        with open(filepath, 'r') as f:
            lines = f.readlines()
    except FileNotFoundError:
        print(f"Error: The file '{filepath}' was not found.")
        return []

    all_runs_dataframes = []
    current_run_lines = []
    is_in_run_block = False

    for line in lines:
        line_lower = line.lower()

        # Detect the start of a new run
        if "starting ensemble" in line_lower:
            is_in_run_block = True
            current_run_lines = []  # Clear lines from any previous run
            continue
        
        # Detect the end of a run
        if "exiting ensemble" in line_lower:
            if is_in_run_block and current_run_lines:
                # Process all collected lines for the completed run
                parsed_run_data = [parse_worker_line(l) for l in current_run_lines]
                if parsed_run_data:
                    df = pd.DataFrame(parsed_run_data)
                    all_runs_dataframes.append(df)
            is_in_run_block = False
            continue

        # Collect relevant worker lines within a run block
        if is_in_run_block:
            line_stripped = line.strip()
            # Filter out Manager and Gen timing lines
            if line_stripped.startswith("Worker") and "Gen no" not in line_stripped:
                current_run_lines.append(line_stripped)
    
    return all_runs_dataframes

def print_failed_log(config_path: Optional[str] = None, 
                     libe_stats_path: Optional[str] = None, 
                     run_number: Optional[int] = None):
    """
    Finds the first failed simulation in a specific run and prints its error logs.

    Args:
        config_path: Path to the rsopt YAML config file. If None, finds the first
                     .yml file in the current directory.
        libe_stats_path: Path to the libEnsemble stats file. If None, defaults to
                         'libE_stats.txt'.
        run_number: The run number to inspect (1-based). If None, defaults to the
                    last run in the log file.
    """
    if libe_stats_path is None:
        libe_stats_path = 'libE_stats.txt'
    
    if config_path is None:
        # Find the first .yml file in the current directory
        yml_files = glob.glob('*.yml')
        if not yml_files:
            print("Error: No .yml config file found in the current directory.")
            return
        config_path = yml_files[0]
        print(f"Using config file: {config_path}")

    # Parse YAML config for run_dir
    run_dir = Path('./ensemble') # Default value
    yaml = YAML(typ='safe')
    try:
        with open(config_path, 'r') as f:
            config = yaml.load(f)
            config_options = config.get('options', {})
            if config_options and 'run_dir' in config_options:
                run_dir = Path(config_options['run_dir'])
                print(f"Found run_dir in config: {run_dir}")
            else:
                print(f"Warning: 'run_dir' not found in config file options. Using default '{run_dir}'.")

    except FileNotFoundError:
        print(f"Warning: Config file '{config_path}' not found. Using default run_dir '{run_dir}'.")
    except Exception as e:
        print(f"Error parsing YAML file '{config_path}': {e}")
        return

    # Parse libE_stats.txt
    runs = parse_libe_log_to_dataframes(libe_stats_path)
    if not runs:
        print(f"No runs found in '{libe_stats_path}'.")
        return

    # Select the correct run
    if run_number is None:
        selected_run_df = runs[-1]
        run_number = len(runs)
    else:
        if 1 <= run_number <= len(runs):
            selected_run_df = runs[run_number - 1]
        else:
            print(f"Error: Run number {run_number} is out of bounds. Log file contains {len(runs)} runs.")
            return

    # Find the first failed simulation
    failed_sims = selected_run_df[selected_run_df['Status'].str.startswith('Task Failed', na=False)]
    
    if failed_sims.empty:
        print(f"No failed simulations found in run {run_number}.")
        return

    first_failed_sim = failed_sims.iloc[0]
    sim_id = int(first_failed_sim['sim_id'])
    worker_id = int(first_failed_sim['Worker'])

    print(f"Found failed sim_id: {sim_id} on Worker: {worker_id} in run {run_number}.")

    # Construct path to sim directory
    sim_id_str = f"sim{sim_id:0{SIM_DIR_WIDTH}d}"
    worker_str = f"worker{worker_id}"
    sim_dir = run_dir / worker_str / sim_id_str
    
    print(f"Searching for error logs in: {sim_dir}")

    # Find and print non-empty error logs
    if not sim_dir.is_dir():
        print(f"Error: Simulation directory not found: {sim_dir}")
        return

    error_logs = list(sim_dir.glob('libe_*.err'))
    
    if not error_logs:
        print("No 'libe_*.err' files found in the simulation directory.")
        return
        
    found_non_empty_log = False
    for log_file in error_logs:
        if log_file.stat().st_size > 0:
            found_non_empty_log = True
            print(f"\n--- Contents of {log_file.name} ---")
            with open(log_file, 'r') as f:
                print(f.read())
            print(f"--- End of {log_file.name} ---\n")
    
    if not found_non_empty_log:
        print("Found error log files, but they are all empty.")


if __name__ == '__main__':
    # NOTE: This example assumes 'libE_stats.txt' and 'rsopt_config.yml' 
    # are in the same directory. You will need to create the `ensemble`
    # directory structure for the test to fully pass.
    
    # Test the new function for the last run in the log
    print("--- Testing print_failed_log for the last run ---")
    # This will use 'rsopt_config.yml' found in the directory
    # and 'libE_stats.txt' by default.
    print_failed_log()
    
    print("\n" + "="*50 + "\n")
    
    # Test for a specific run number
    print("--- Testing print_failed_log for run 1 ---")
    print_failed_log(run_number=1)
