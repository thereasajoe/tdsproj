import os
import re
import json
import datetime
import sqlite3
import subprocess
import requests
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from PIL import Image
import pytesseract
from sentence_transformers import SentenceTransformer, util
import torch

app = FastAPI()

# Use the AIPROXY_TOKEN environment variable
AIPROXY_TOKEN = os.environ["AIPROXY_TOKEN"]

# AI Proxy URL for GPT-4o-Mini
AIPROXY_URL = "https://api.aiproxy.openai.azure.com/v1/completions"

class TaskRequest(BaseModel):
    task: str

class TaskResponse(BaseModel):
    result: str

def call_llm(prompt):
    headers = {
        "Authorization": f"Bearer {AIPROXY_TOKEN}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "gpt-4o-mini",
        "prompt": prompt,
        "max_tokens": 150,
        "temperature": 0.7
    }
    response = requests.post(AIPROXY_URL, headers=headers, json=data)
    response.raise_for_status()
    return response.json()["choices"][0]["text"].strip()

def parse_task_description(task_description):
    input_file_pattern = r"/data/\S+\.\w+"
    output_file_pattern = r"(?:into|to) (/data/\S+\.\w+)"
    operation_pattern = r"(Install|Format|Count|Sort|Write|Find|Extract|Calculate)\s[\w\s]+"

    input_file_match = re.search(input_file_pattern, task_description)
    input_file = input_file_match.group(0) if input_file_match else None

    output_file_match = re.search(output_file_pattern, task_description)
    output_file = output_file_match.group(1) if output_file_match else None

    operation_match = re.search(operation_pattern, task_description, re.IGNORECASE)
    operation = operation_match.group(0) if operation_match else None

    return {
        "input_file": input_file,
        "output_file": output_file,
        "operation": operation
    }

def interpret_task_with_llm(task_description):
    prompt = f"Interpret the following task and provide the operation, input file, and output file:\n{task_description}\n\nOperation:\nInput File:\nOutput File:"
    
    interpretation = call_llm(prompt)
    
    lines = interpretation.strip().split('\n')
    llm_interpretation = {
        "operation": lines[0].split(':')[1].strip() if len(lines) > 0 else None,
        "input_file": lines[1].split(':')[1].strip() if len(lines) > 1 else None,
        "output_file": lines[2].split(':')[1].strip() if len(lines) > 2 else None
    }
    
    return llm_interpretation

def task_a1_install_uv_and_run_datagen():
    subprocess.run(["pip", "install", "uv"], check=True)
    datagen_url = "https://raw.githubusercontent.com/sanand0/tools-in-data-science-public/tds-2025-01/project-1/datagen.py"
    response = requests.get(datagen_url)
    with open("datagen.py", "wb") as file:
        file.write(response.content)
    subprocess.run(["python", "datagen.py", os.getenv("USER_EMAIL")], check=True)
    return "UV installed and datagen.py executed successfully."

def task_a2_format_markdown(input_file):
    subprocess.run(["npx", "prettier@3.4.2", "--write", input_file], check=True)
    return f"File {input_file} formatted successfully using prettier@3.4.2."

def task_a3_count_weekday(input_file, output_file, day):
    day_mapping = {"monday": 0, "tuesday": 1, "wednesday": 2, "thursday": 3, "friday": 4, "saturday": 5, "sunday": 6}
    with open(input_file, "r") as file:
        dates = file.readlines()
    count = sum(1 for date in dates if datetime.datetime.strptime(date.strip(), "%Y-%m-%d").weekday() == day_mapping[day])
    with open(output_file, "w") as file:
        file.write(str(count))
    return f"Counted {count} {day.capitalize()}s and wrote to {output_file}."

def task_a4_sort_contacts(input_file, output_file):
    with open(input_file, "r") as file:
        contacts = json.load(file)
    sorted_contacts = sorted(contacts, key=lambda x: (x["last_name"], x["first_name"]))
    with open(output_file, "w") as file:
        json.dump(sorted_contacts, file, indent=4)
    return f"Contacts sorted and written to {output_file}."

def task_a5_recent_log_lines(input_file, output_file):
    log_dir = os.path.dirname(input_file)
    log_files = sorted([f for f in os.listdir(log_dir) if f.endswith(".log")], key=lambda x: os.path.getmtime(os.path.join(log_dir, x)), reverse=True)[:10]
    with open(output_file, "w") as file:
        for log_file in log_files:
            with open(os.path.join(log_dir, log_file), "r") as lf:
                file.write(lf.readline())
    return f"First lines of 10 most recent log files written to {output_file}."

def task_a6_create_markdown_index(input_file, output_file):
    docs_dir = os.path.dirname(input_file)
    md_files = [f for f in os.listdir(docs_dir) if f.endswith(".md")]
    index = {}
    for md_file in md_files:
        with open(os.path.join(docs_dir, md_file), "r") as file:
            for line in file:
                if line.startswith("# "):
                    index[md_file] = line.strip("# ").strip()
                    break
    with open(output_file, "w") as file:
        json.dump(index, file, indent=4)
    return f"Markdown index created at {output_file}."

def task_a7_extract_email(input_file, output_file):
    with open(input_file, "r") as file:
        email_content = file.read()
    prompt = f"Extract the sender's email address from the following email:\n{email_content}"
    sender_email = call_llm(prompt)
    with open(output_file, "w") as file:
        file.write(sender_email.strip())
    return f"Sender's email extracted and written to {output_file}."

def task_a8_extract_credit_card(input_file, output_file):
    image = Image.open(input_file)
    card_number = pytesseract.image_to_string(image).replace(" ", "").strip()
    with open(output_file, "w") as file:
        file.write(card_number)
    return f"Credit card number extracted and written to {output_file}."

def task_a9_find_similar_comments(input_file, output_file):
    model = SentenceTransformer('all-MiniLM-L6-v2')
    with open(input_file, "r") as file:
        comments = file.readlines()
    embeddings = model.encode(comments, convert_to_tensor=True)
    cos_sim = util.pytorch_cos_sim(embeddings, embeddings)
    max_sim = torch.max(cos_sim - torch.eye(cos_sim.shape[0]))
    max_indices = torch.where(cos_sim == max_sim)
    pair = (comments[max_indices[0][0]], comments[max_indices[1][0]])
    with open(output_file, "w") as file:
        file.writelines(pair)
    return f"Most similar comments written to {output_file}."

def task_a10_calculate_gold_ticket_sales(input_file, output_file):
    conn = sqlite3.connect(input_file)
    cursor = conn.cursor()
    cursor.execute("SELECT SUM(units * price) FROM tickets WHERE type = 'Gold'")
    total_sales = cursor.fetchone()[0]
    conn.close()
    with open(output_file, "w") as file:
        file.write(str(total_sales))
    return f"Total sales of Gold tickets ({total_sales}) written to {output_file}."

def execute_task(parsed_task):
    operation = parsed_task['operation'].lower()
    input_file = parsed_task['input_file']
    output_file = parsed_task['output_file']

    if "install uv" in operation and "datagen.py" in operation:
        return task_a1_install_uv_and_run_datagen()
    elif "format" in operation and "prettier" in operation:
        return task_a2_format_markdown(input_file)
    elif any(day in operation for day in ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]):
        day = next(day for day in ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"] if day in operation)
        return task_a3_count_weekday(input_file, output_file, day)
    elif "sort" in operation and "contacts" in operation:
        return task_a4_sort_contacts(input_file, output_file)
    elif "recent" in operation and "log" in operation:
        return task_a5_recent_log_lines(input_file, output_file)
    elif "markdown" in operation and "index" in operation:
        return task_a6_create_markdown_index(input_file, output_file)
    elif "extract" in operation and "email" in operation:
        return task_a7_extract_email(input_file, output_file)
    elif "credit card" in operation and "extract" in operation:
        return task_a8_extract_credit_card(input_file, output_file)
    elif "similar" in operation and "comments" in operation:
        return task_a9_find_similar_comments(input_file, output_file)
    elif "total sales" in operation and "gold" in operation:
        return task_a10_calculate_gold_ticket_sales(input_file, output_file)
    else:
        return "Task not recognized or not implemented."

def run_task(task_description):
    regex_parsed = parse_task_description(task_description)
    llm_interpreted = interpret_task_with_llm(task_description)
    
    final_task = {
        "input_file": regex_parsed["input_file"] or llm_interpreted["input_file"],
        "output_file": regex_parsed["output_file"] or llm_interpreted["output_file"],
        "operation": regex_parsed["operation"] or llm_interpreted["operation"]
    }
    
    result = execute_task(final_task)
    return result

@app.post("/run", response_model=TaskResponse)
async def api_run_task(task_request: TaskRequest):
    try:
        result = run_task(task_request.task)
        return TaskResponse(result=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
