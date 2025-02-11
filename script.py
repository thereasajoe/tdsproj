import os
import glob

# Define correct log directory and output file path
log_dir = "/workspaces/tdsproj/data_output/logs/"
output_file = "/workspaces/tdsproj/data_output/logs-recent.txt"

# Check if the log directory exists
if not os.path.exists(log_dir):
    print(f"Log directory {log_dir} not found.")
    exit(1)

# Get the most recent 10 log files sorted by modification time
log_files = sorted(glob.glob(os.path.join(log_dir, "*.log")), key=os.path.getmtime, reverse=True)[:10]

# Write first lines of these logs to the output file
with open(output_file, "w") as out_f:
    for log_file in log_files:
        with open(log_file, "r") as f:
            first_line = f.readline().strip()
            out_f.write(first_line + "\n")

print(f"First lines of the 10 most recent .log files written to {output_file}")

