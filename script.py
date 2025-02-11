import os
import glob

# Define paths
log_dir = "/data_output/logs/"
output_file = "logs-recent.txt"  # Save in current directory

# Get a list of .log files sorted by modification time (most recent first)
log_files = sorted(glob.glob(os.path.join(log_dir, "*.log")), key=os.path.getmtime, reverse=True)

# Take the 10 most recent log files
recent_logs = log_files[:10]

# Read first lines and write to the output file
with open(output_file, "w") as out_f:
    for log_file in recent_logs:
        with open(log_file, "r") as f:
            first_line = f.readline().strip()
            out_f.write(first_line + "\n")

print(f"First lines of the 10 most recent .log files written to {output_file}")

