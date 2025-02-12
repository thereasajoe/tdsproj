from fastapi import FastAPI, Query
import openai  # For task classification
import subprocess
import json
import sqlite3
import os
import re

app = FastAPI()

# OpenAI API Key (Replace with yours)
openai.api_key = "YOUR_OPENAI_API_KEY"

# Task Descriptions
TASKS = {
    "A1": "Install uv (if required) and run datagen.py from GitHub with the user's email as the only argument.",
    "A2": "Format /data/format.md using prettier@3.4.2, updating the file in-place.",
    "A3": "Count Wednesdays in /data/dates.txt and write the count to /data/dates-wednesdays.txt.",
    "A4": "Sort contacts in /data/contacts.json by last_name, then first_name, and write to /data/contacts-sorted.json.",
    "A5": "Extract first lines of 10 most recent log files from /data/logs/ to /data/logs-recent.txt.",
    "A6": "Extract first H1 headings from Markdown files in /data/docs/ and create an index.json.",
    "A7": "Extract sender’s email from /data/email.txt using an LLM and write to /data/email-sender.txt.",
    "A8": "Extract credit card number from /data/credit-card.png using an LLM and write to /data/credit-card.txt.",
    "A9": "Find the most similar pair of comments in /data/comments.txt using embeddings and write them to /data/comments-similar.txt.",
    "A10": "Calculate total sales for 'Gold' tickets from /data/ticket-sales.db and write to /data/ticket-sales-gold.txt."
}

# Function to classify the task using LLM
def classify_task(task_description):
    """Uses an LLM to classify a task description into A1–A10"""
    response = openai.ChatCompletion.create(
        model="gpt-4-turbo",
        messages=[{"role": "system", "content": "Classify the task into one of A1–A10 based on the description."},
                  {"role": "user", "content": task_description}],
        temperature=0.3
    )
    return response["choices"][0]["message"]["content"].strip()

# **TASK FUNCTIONS**

def run_task_A1():
    """Install uv (if required) and run datagen.py from GitHub"""
    subprocess.run(["pip", "install", "uv"], check=True)  # Ensure uv is installed
    subprocess.run(["uv", "pip", "install", "requests"], check=True)  # Install requests if needed
    subprocess.run(["uv", "run", "python", "-m", "requests", "https://raw.githubusercontent.com/sanand0/tools-in-data-science-public/tds-2025-01/project-1/datagen.py", "user@example.com"], check=True)

def run_task_A2():
    """Format /data/format.md using Prettier"""
    subprocess.run(["npx", "prettier@3.4.2", "--write", "/data/format.md"], check=True)

def run_task_A3():
    """Count the number of Wednesdays in /data/dates.txt"""
    with open("/data/dates.txt") as f:
        dates = f.readlines()
    wednesdays = sum(1 for date in dates if "Wed" in date)
    with open("/data/dates-wednesdays.txt", "w") as f:
        f.write(str(wednesdays))

def run_task_A4():
    """Sort contacts in /data/contacts.json by last_name, then first_name"""
    with open("/data/contacts.json") as f:
        contacts = json.load(f)
    contacts.sort(key=lambda x: (x["last_name"], x["first_name"]))
    with open("/data/contacts-sorted.json", "w") as f:
        json.dump(contacts, f, indent=4)

def run_task_A5():
    """Write first lines of the 10 most recent .log files from /data/logs/ to /data/logs-recent.txt"""
    logs = sorted(os.listdir("/data/logs"), key=lambda x: os.path.getmtime(f"/data/logs/{x}"), reverse=True)[:10]
    with open("/data/logs-recent.txt", "w") as f:
        for log in logs:
            with open(f"/data/logs/{log}") as log_file:
                f.write(log_file.readline())

def run_task_A6():
    """Extract first H1 headings from Markdown files in /data/docs/ and create an index.json"""
    index = {}
    for file in os.listdir("/data/docs/"):
        if file.endswith(".md"):
            with open(f"/data/docs/{file}") as f:
                for line in f:
                    if line.startswith("# "):  # Find first H1 heading
                        index[file] = line.strip("# ").strip()
                        break
    with open("/data/docs/index.json", "w") as f:
        json.dump(index, f, indent=4)

def run_task_A7():
    """Extract sender’s email from /data/email.txt using LLM"""
    with open("/data/email.txt") as f:
        email_content = f.read()
    response = openai.ChatCompletion.create(
        model="gpt-4-turbo",
        messages=[{"role": "system", "content": "Extract the sender's email address from the given email text."},
                  {"role": "user", "content": email_content}],
        temperature=0.3
    )
    extracted_email = response["choices"][0]["message"]["content"].strip()
    with open("/data/email-sender.txt", "w") as f:
        f.write(extracted_email)

def run_task_A8():
    """Extract credit card number from /data/credit-card.png using LLM"""
    response = openai.ChatCompletion.create(
        model="gpt-4-turbo",
        messages=[{"role": "system", "content": "Extract the credit card number from the image: /data/credit-card.png."}],
        temperature=0.3
    )
    extracted_card = response["choices"][0]["message"]["content"].strip().replace(" ", "")
    with open("/data/credit-card.txt", "w") as f:
        f.write(extracted_card)

def run_task_A9():
    """Find the most similar pair of comments using embeddings"""
    with open("/data/comments.txt") as f:
        comments = f.readlines()
    response = openai.ChatCompletion.create(
        model="gpt-4-turbo",
        messages=[{"role": "system", "content": "Find the most similar comments from this list."},
                  {"role": "user", "content": "\n".join(comments)}],
        temperature=0.3
    )
    similar_comments = response["choices"][0]["message"]["content"].strip().split("\n")
    with open("/data/comments-similar.txt", "w") as f:
        f.writelines(similar_comments)

def run_task_A10():
    """Calculate total sales for 'Gold' tickets and write to /data/ticket-sales-gold.txt"""
    conn = sqlite3.connect("/data/ticket-sales.db")
    cursor = conn.cursor()
    cursor.execute("SELECT SUM(price * units) FROM tickets WHERE type = 'Gold'")
    result = cursor.fetchone()[0]
    with open("/data/ticket-sales-gold.txt", "w") as f:
        f.write(str(result))
    conn.close()

# Task mapping
TASK_FUNCTIONS = {
    "A1": run_task_A1,
    "A2": run_task_A2,
    "A3": run_task_A3,
    "A4": run_task_A4,
    "A5": run_task_A5,
    "A6": run_task_A6,
    "A7": run_task_A7,
    "A8": run_task_A8,
    "A9": run_task_A9,
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
