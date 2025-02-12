from fastapi import FastAPI, Query
import openai  # Replace with your LLM integration
import subprocess
import json
import sqlite3

app = FastAPI()

# Configure OpenAI API (replace with your key)
openai.api_key = "YOUR_OPENAI_API_KEY"

# Define available tasks
TASKS = {
    "A1": "Install uv and run datagen.py with the user's email.",
    "A2": "Format the contents of /data/format.md using prettier.",
    "A3": "Count Wednesdays in /data/dates.txt and write the count to /data/dates-wednesdays.txt.",
    "A4": "Sort contacts in /data/contacts.json and write to /data/contacts-sorted.json.",
    "A5": "Extract first lines of 10 most recent log files from /data/logs/ to /data/logs-recent.txt.",
    "A6": "Create an index.json mapping Markdown files to their titles.",
    "A7": "Extract the sender’s email from /data/email.txt and write to /data/email-sender.txt.",
    "A8": "Extract credit card number from /data/credit-card.png and write it to /data/credit-card.txt.",
    "A9": "Find the most similar pair of comments in /data/comments.txt and write them to /data/comments-similar.txt.",
    "A10": "Calculate total sales for 'Gold' tickets from /data/ticket-sales.db and write to /data/ticket-sales-gold.txt."
}

def classify_task(task_description):
    """Uses an LLM to classify a task description into A1–A10"""
    response = openai.ChatCompletion.create(
        model="gpt-4-turbo",
        messages=[{"role": "system", "content": "Classify the task into one of A1–A10 based on the description."},
                  {"role": "user", "content": task_description}],
        temperature=0.3
    )
    return response["choices"][0]["message"]["content"].strip()

# Task Functions
def run_task_A1():
    subprocess.run(["uv", "run", "datagen.py", "user@example.com"], check=True)

def run_task_A2():
    subprocess.run(["npx", "prettier@3.4.2", "--write", "/data/format.md"], check=True)

def run_task_A3():
    with open("/data/dates.txt") as f:
        dates = f.readlines()
    wednesdays = sum(1 for date in dates if "Wed" in date)
    with open("/data/dates-wednesdays.txt", "w") as f:
        f.write(str(wednesdays))

def run_task_A4():
    with open("/data/contacts.json") as f:
        contacts = json.load(f)
    contacts.sort(key=lambda x: (x["last_name"], x["first_name"]))
    with open("/data/contacts-sorted.json", "w") as f:
        json.dump(contacts, f)

def run_task_A5():
    import os
    logs = sorted(os.listdir("/data/logs"), key=lambda x: os.path.getmtime(f"/data/logs/{x}"), reverse=True)[:10]
    with open("/data/logs-recent.txt", "w") as f:
        for log in logs:
            with open(f"/data/logs/{log}") as log_file:
                f.write(log_file.readline())

def run_task_A10():
    conn = sqlite3.connect("/data/ticket-sales.db")
    cursor = conn.cursor()
    cursor.execute("SELECT SUM(price * units) FROM tickets WHERE type = 'Gold'")
    result = cursor.fetchone()[0]
    with open("/data/ticket-sales-gold.txt", "w") as f:
        f.write(str(result))
    conn.close()

TASK_FUNCTIONS = {
    "A1": run_task_A1,
    "A2": run_task_A2,
    "A3": run_task_A3,
    "A4": run_task_A4,
    "A5": run_task_A5,
    "A10": run_task_A10
}

@app.get("/run")
def run_task(task: str = Query(..., title="Task Description")):
    task_id = classify_task(task)
    if task_id in TASK_FUNCTIONS:
        TASK_FUNCTIONS[task_id]()
        return {"status": "success", "task": task_id}
    else:
        return {"status": "error", "message": "Task not recognized"}

