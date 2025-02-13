import json
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
import os
from dotenv import load_dotenv
import openai
from openai import OpenAI
from datetime import datetime
import base64
import numpy as np
import sqlite3
import glob
import re
import subprocess
import sys
# Load environment variables
load_dotenv("secret.env")
AIPROXY_TOKEN = os.getenv("AIPROXY_TOKEN")
client = OpenAI(api_key=AIPROXY_TOKEN)
if not AIPROXY_TOKEN:
    raise ValueError("⚠️ AIPROXY_TOKEN is missing! Check your secret.env file.")


client = openai.OpenAI(api_key=AIPROXY_TOKEN, base_url="https://aiproxy.sanand.workers.dev/openai/v1")
print(f"✅ AIPROXY_TOKEN loaded successfully: {AIPROXY_TOKEN[:5]}******")  # Masked for security

# Initialize FastAPI app
app = FastAPI()

# Set OpenAI API key and base URL for AI Proxy
# TODO: The 'openai.api_base' option isn't read in the client API. You will need to pass it when you instantiate the client, e.g. 'OpenAI(base_url="https://aiproxy.sanand.workers.dev/openai/v1")'
# openai.api_base = "https://aiproxy.sanand.workers.dev/openai/v1"

# Define base data directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")

class TaskRequest(BaseModel):
    task: str


def run_datagen(email):
    """Run datagen.py with the provided email as an argument."""
    script_url = "https://raw.githubusercontent.com/sanand0/tools-in-data-science-public/tds-2025-01/project-1/datagen.py"
    try:
        subprocess.run(["curl", "-sSL", script_url, "|", "python", "-", email], check=True, shell=True)
        return "✅ Successfully ran datagen.py with provided email"
    except subprocess.CalledProcessError as e:
        raise HTTPException(status_code=500, detail=f"Failed to run datagen.py: {str(e)}")

def format_markdown():
    """Format /data/format.md using prettier@3.4.2."""
    input_path = os.path.join(DATA_DIR, "format.md")
    if not os.path.exists(input_path):
        raise HTTPException(status_code=404, detail="format.md not found")
    
    try:
        subprocess.run(["uv", "pip", "install", "prettier==3.4.2"], check=True)
        subprocess.run(["npx", "prettier", "--write", input_path], check=True)
        return f"✅ Successfully formatted {input_path} using prettier@3.4.2"
    except subprocess.CalledProcessError as e:
        raise HTTPException(status_code=500, detail=f"Failed to format markdown: {str(e)}")

def sort_contacts():
    """Reads, sorts, and saves contacts in /data/contacts.json"""
    input_path = os.path.join(DATA_DIR, "contacts.json")
    output_path = os.path.join(DATA_DIR, "contacts-sorted.json")

    if not os.path.exists(input_path):
        raise HTTPException(status_code=404, detail="contacts.json not found")

    try:
        with open(input_path, "r", encoding="utf-8") as file:
            contacts = json.load(file)

        sorted_contacts = sorted(contacts, key=lambda x: (x["last_name"], x["first_name"]))

        with open(output_path, "w", encoding="utf-8") as file:
            json.dump(sorted_contacts, file, indent=4)

        return f"✅ Contacts sorted and saved to {output_path}"

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def count_wednesdays():
    """Reads /data/dates.txt, counts Wednesdays, and saves the result."""
    input_path = os.path.join(DATA_DIR, "dates.txt")
    output_path = os.path.join(DATA_DIR, "dates-wednesdays.txt")

    if not os.path.exists(input_path):
        raise HTTPException(status_code=404, detail="dates.txt not found")

    try:
        with open(input_path, "r", encoding="utf-8") as file:
            dates = file.readlines()

        # Convert each line to a date and count Wednesdays
        date_formats = [
            "%Y-%m-%d",
            "%b %d, %Y",
            "%d-%b-%Y",
            "%Y/%m/%d %H:%M:%S"
        ]

        wednesday_count = 0
        for date_str in dates:
            date_str = date_str.strip()
            for date_format in date_formats:
                try:
                    date_obj = datetime.strptime(date_str, date_format)
                    if date_obj.weekday() == 2:  # Wednesday is 2 in Python's weekday() method
                        wednesday_count += 1
                    break
                except ValueError:
                    continue
            else:
                raise ValueError(f"Unable to parse date: {date_str}")

        #wednesday_count = sum(1 for date in dates if datetime.strptime(date.strip(), "%Y-%m-%d").weekday() == 2)

        # Save the result
        with open(output_path, "w", encoding="utf-8") as file:
            file.write(str(wednesday_count))

        return f"✅ Found {wednesday_count} Wednesdays. Result saved to {output_path}"

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def extract_email():
    """Reads /data/email.txt, extracts sender's email using LLM, and saves it."""
    input_path = os.path.join(DATA_DIR, "email.txt")
    output_path = os.path.join(DATA_DIR, "email-sender.txt")

    if not os.path.exists(input_path):
        raise HTTPException(status_code=404, detail="email.txt not found")

    try:
        with open(input_path, "r", encoding="utf-8") as file:
            email_content = file.read()

        # Use GPT-4o-mini to extract the sender's email
        response = client.chat.completions.create(model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are an email processing assistant. Extract only the sender's email address."},
            {"role": "user", "content": email_content}
        ])

        sender_email = response.choices[0].message.content.strip()

        # Save the extracted email
        with open(output_path, "w", encoding="utf-8") as file:
            file.write(sender_email)

        return f"✅ Extracted email: {sender_email}. Saved to {output_path}"

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def extract_credit_card():
    """Reads /data/credit-card.png, extracts credit card number using OpenAI Vision API, and saves it."""
    input_path = os.path.join(DATA_DIR, "credit_card.png")
    output_path = os.path.join(DATA_DIR, "credit-card.txt")

    if not os.path.exists(input_path):
        raise HTTPException(status_code=404, detail="credit-card.png not found")

    try:
        # Convert the image to a base64 string
        with open(input_path, "rb") as image_file:
            base64_image = base64.b64encode(image_file.read()).decode("utf-8")

        # Use OpenAI Vision API to analyze the image
        response = client.chat.completions.create(model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are an OCR assistant. Extract only the credit card number from the image."},
            {"role": "user", "content": [
                {"type": "text", "text": "Extract the credit card number from this image:"},
                {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{base64_image}"}}
            ]}
        ])

        card_number = response.choices[0].message.content.strip().replace(" ", "")

        # Save the extracted number
        with open(output_path, "w", encoding="utf-8") as file:
            file.write(card_number)

        return f"✅ Extracted credit card number: {card_number}. Saved to {output_path}"

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def find_similar_comments():
    """Reads /data/comments.txt, finds the most similar pair using embeddings, and saves the result."""
    input_path = os.path.join(DATA_DIR, "comments.txt")
    output_path = os.path.join(DATA_DIR, "comments-similar.txt")

    if not os.path.exists(input_path):
        raise HTTPException(status_code=404, detail="comments.txt not found")

    try:
        # Read comments from file
        with open(input_path, "r", encoding="utf-8") as file:
            comments = [line.strip() for line in file.readlines() if line.strip()]

        if len(comments) < 2:
            raise HTTPException(status_code=400, detail="Not enough comments to compare.")

        # Get embeddings for all comments
        response = client.embeddings.create(model="text-embedding-3-small",
        input=comments)

        embeddings = np.array([item.embedding for item in response.data])

        # Compute cosine similarity
        similarity_matrix = np.dot(embeddings, embeddings.T)
        np.fill_diagonal(similarity_matrix, -1)  # Ignore self-similarity

        # Find the most similar pair
        max_index = np.unravel_index(np.argmax(similarity_matrix), similarity_matrix.shape)
        comment1, comment2 = comments[max_index[0]], comments[max_index[1]]

        # Save the most similar comments
        with open(output_path, "w", encoding="utf-8") as file:
            file.write(f"{comment1}\n{comment2}")

        return f"✅ Most similar comments saved to {output_path}"

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def calculate_gold_ticket_sales():
    """Reads /data/ticket-sales.db, calculates total sales for 'Gold' tickets, and saves the result."""
    db_path = os.path.join(DATA_DIR, "ticket-sales.db")
    output_path = os.path.join(DATA_DIR, "ticket-sales-gold.txt")

    if not os.path.exists(db_path):
        raise HTTPException(status_code=404, detail="ticket-sales.db not found")

    try:
        # Connect to SQLite database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Query total sales for "Gold" ticket type
        cursor.execute("SELECT SUM(units * price) FROM tickets WHERE type = 'Gold'")
        total_sales = cursor.fetchone()[0] or 0  # Handle NULL case

        conn.close()

        # Save the result
        with open(output_path, "w", encoding="utf-8") as file:
            file.write(str(total_sales))

        return f"✅ Total sales for 'Gold' tickets: {total_sales}. Saved to {output_path}"

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def extract_recent_log_lines():
    """Extracts the first line of the 10 most recent .log files in /data/logs/ and saves to /data/logs-recent.txt"""
    logs_path = os.path.join(DATA_DIR, "logs", "*.log")
    output_path = os.path.join(DATA_DIR, "logs-recent.txt")

    # Find all .log files
    log_files = glob.glob(logs_path)

    if not log_files:
        raise HTTPException(status_code=404, detail="No log files found in /data/logs/")

    try:
        # Sort log files by modification time (newest first)
        log_files.sort(key=os.path.getmtime, reverse=True)

        # Read first line from up to 10 most recent logs
        recent_logs = []
        for log_file in log_files[:10]:
            with open(log_file, "r", encoding="utf-8") as file:
                first_line = file.readline().strip()
                recent_logs.append(first_line)

        # Save extracted lines to /data/logs-recent.txt
        with open(output_path, "w", encoding="utf-8") as file:
            file.write("\n".join(recent_logs))

        return f"✅ Extracted first lines from {len(recent_logs)} log files. Saved to {output_path}"

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def extract_markdown_headers():
    """Finds all Markdown (.md) files in /data/docs/, extracts H1 headers, and saves to /data/docs/index.json"""
    docs_path = os.path.join(DATA_DIR, "docs")
    output_path = os.path.join(docs_path, "index.json")

    if not os.path.exists(docs_path):
        raise HTTPException(status_code=404, detail="docs directory not found")

    headers_dict = {}

    try:
        # Recursively find all Markdown files in subdirectories
        md_files = []
        for subdir, dirs, files in os.walk(docs_path):
            for file in files:
                if file.endswith(".md"):
                    md_files.append(os.path.join(subdir, file))

        if not md_files:
            raise HTTPException(status_code=404, detail="No Markdown files found in /data/docs/")

        # Extract the first H1 header from each Markdown file
        for md_file in md_files:
            with open(md_file, "r", encoding="utf-8") as file:
                for line in file:
                    match = re.match(r"^# (.+)", line.strip())  # Find the first H1 header
                    if match:
                        # Remove /data/docs/ prefix and add to the dictionary
                        relative_file_path = os.path.relpath(md_file, docs_path)
                        headers_dict[relative_file_path] = match.group(1)
                        break  # Stop after the first H1

        # Save extracted headers to index.json
        with open(output_path, "w", encoding="utf-8") as file:
            json.dump(headers_dict, file, indent=4)

        return f"✅ Extracted H1 headers from {len(headers_dict)} Markdown files. Saved to {output_path}"

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
@app.get("/")
async def root():
    return JSONResponse(content={"message": "Welcome to the API root"})

@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    return FileResponse("path/to/your/favicon.ico")

@app.post("/run")
async def run_task(task: str = Query(..., description="Plain-English task description")):
    """Executes a task based on natural language input."""
    if "run datagen" in task.lower():
        email = task.split()[-1]  # Assume the email is the last word in the task description
        return {"task": task, "output": run_datagen(email)}
    elif "format markdown" in task.lower():
        return {"task": task, "output": format_markdown()}
    elif "sort contacts" in task.lower():
        return {"task": task, "output": sort_contacts()}
    elif "count wednesdays" in task.lower():
        return {"task": task, "output": count_wednesdays()}
    elif "extract email" in task.lower():
        return {"task": task, "output": extract_email()}
    elif "extract credit card" in task.lower():
        return {"task": task, "output": extract_credit_card()}
    elif "find similar comments" in task.lower():
        return {"task": task, "output": find_similar_comments()}
    elif "calculate gold ticket sales" in task.lower():
        return {"task": task, "output": calculate_gold_ticket_sales()}
    elif "extract recent logs" in task.lower():
        return {"task": task, "output": extract_recent_log_lines()}
    elif "extract markdown headers" in task.lower():  # ✅ New Task A6 added here
        return {"task": task, "output": extract_markdown_headers()}

    # If task is not predefined, call the LLM
    try:
        response = client.chat.completions.create(model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are an automation assistant."},
            {"role": "user", "content": task}
        ])
        task_output = response.choices[0].message.content
        return {"task": task, "output": task_output}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    

