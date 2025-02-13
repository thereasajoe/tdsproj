from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
from fastapi.responses import FileResponse
import os
import subprocess
import json
from datetime import datetime
import sqlite3

# Initialize FastAPI app
app = FastAPI()

# Environment variable for AI Proxy Token
AI_PROXY_TOKEN = os.getenv("AIPROXY_TOKEN")

# Placeholder function to simulate LLM interaction
def call_llm(prompt: str) -> str:
    # Simulate LLM processing (replace with actual API call using AI_PROXY_TOKEN)
    return f"Simulated response for: {prompt}"

# Helper functions for task execution
def execute_task(task_description: str):
    try:
        if "install uv" in task_description.lower():
            subprocess.run(["pip", "install", "uv"], check=True)
            return {"message": "uv installed successfully"}
        
        elif "run datagen.py" in task_description.lower():
            email = task_description.split()[-1]
            subprocess.run(["python", "datagen.py", email], check=True)
            return {"message": f"datagen.py executed with email {email}"}
        
        elif "format.md" in task_description.lower():
            subprocess.run(["npx", "prettier@3.4.2", "--write", "/data/format.md"], check=True)
            return {"message": "/data/format.md formatted successfully"}
        
        elif "count wednesdays" in task_description.lower():
            with open("/data/dates.txt", "r") as file:
                dates = file.readlines()
            wednesdays = sum(1 for date in dates if datetime.strptime(date.strip(), "%Y-%m-%d").weekday() == 2)
            with open("/data/dates-wednesdays.txt", "w") as file:
                file.write(str(wednesdays))
            return {"message": f"{wednesdays} Wednesdays counted and written to /data/dates-wednesdays.txt"}
        
        elif "sort contacts" in task_description.lower():
            with open("/data/contacts.json", "r") as file:
                contacts = json.load(file)
            sorted_contacts = sorted(contacts, key=lambda x: (x["last_name"], x["first_name"]))
            with open("/data/contacts-sorted.json", "w") as file:
                json.dump(sorted_contacts, file, indent=2)
            return {"message": "/data/contacts.json sorted and saved to /data/contacts-sorted.json"}
        
        elif "recent logs" in task_description.lower():
            log_files = sorted([f for f in os.listdir("/data/logs/") if f.endswith(".log")], reverse=True)[:10]
            recent_lines = []
            for log_file in log_files:
                with open(f"/data/logs/{log_file}", "r") as file:
                    recent_lines.append(file.readline().strip())
            with open("/data/logs-recent.txt", "w") as file:
                file.write("\n".join(recent_lines))
            return {"message": "Recent log lines written to /data/logs-recent.txt"}
        
        elif "markdown index" in task_description.lower():
            md_files = [f for f in os.listdir("/data/docs/") if f.endswith(".md")]
            index = {}
            for md_file in md_files:
                with open(f"/data/docs/{md_file}", "r") as file:
                    for line in file:
                        if line.startswith("#"):
                            index[md_file] = line.strip("# ").strip()
                            break
            with open("/data/docs/index.json", "w") as file:
                json.dump(index, file, indent=2)
            return {"message": "/data/docs/index.json created successfully"}
        
        elif "extract sender email" in task_description.lower():
            with open("/data/email.txt", "r") as file:
                email_content = file.read()
            sender_email = call_llm(f"Extract the sender's email from this text: {email_content}")
            with open("/data/email-sender.txt", "w") as file:
                file.write(sender_email)
            return {"message": f"Sender's email extracted and written to /data/email-sender.txt"}
        
        elif "credit card number" in task_description.lower():
            # Simulate image processing via LLM (actual implementation would involve OCR + LLM)
            card_number = call_llm("Extract the credit card number from the provided image.")
            with open("/data/credit-card.txt", "w") as file:
                file.write(card_number.replace(" ", "").strip())
            return {"message": "Credit card number extracted and written to /data/credit-card.txt"}
        
        elif "similar comments" in task_description.lower():
            # Simulate embeddings-based similarity calculation (actual implementation would use an embedding model)
            with open("/data/comments.txt", "r") as file:
                comments = file.readlines()
            similar_pair = call_llm(f"Find the most similar pair of comments: {comments}")
            with open("/data/comments-similar.txt", "w") as file:
                file.write("\n".join(similar_pair))
            return {"message": f"Most similar comments written to /data/comments-similar.txt"}
        
        elif "gold ticket sales" in task_description.lower():
            conn = sqlite3.connect("/data/ticket-sales.db")
            cursor = conn.cursor()
            cursor.execute("SELECT SUM(units * price) FROM tickets WHERE type='Gold'")
            total_sales = cursor.fetchone()[0]
            conn.close()
            
            with open("/data/ticket-sales-gold.txt", "w") as file:
                file.write(str(total_sales))
            
            return {"message": f"Total sales for Gold tickets written to /data/ticket-sales-gold.txt"}
        
        else:
            raise HTTPException(status_code=400, detail="Task not recognized or unsupported.")
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# API Endpoints
@app.post("/run")
def run_task(task: str):
    result = execute_task(task)
    return result

@app.get("/read")
def read_file(path: str):
    try:
        with open(path, "r") as file:
            content = file.read()
        return content
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="File not found.")
@app.get("/")
def read_root():
    return {"message": "Welcome to the automation agent API"}


@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    return FileResponse("path/to/favicon.ico")
