from fastapi import FastAPI, Query
import subprocess
import json
import os
import datetime
import sqlite3

app = FastAPI()

DATA_DIR = "/data"  # Root directory for generated files

@app.get("/run")
def run_task(task: str):
    try:
        if task.startswith("Install uv"):
            return {"message": "Skipping manual installation. Run manually if needed."}

        elif "datagen.py" in task:
            email = task.split("with ")[-1].split(" as")[0]
            cmd = f"uv run datagen.py {email}"
            subprocess.run(cmd, shell=True, check=True)
            return {"message": "Data generation completed."}

        elif "format.md" in task:
            cmd = "npx prettier@3.4.2 --write /data/format.md"
            subprocess.run(cmd, shell=True, check=True)
            return {"message": "Markdown formatted."}

        elif "dates-wednesdays.txt" in task:
            count = 0
            with open(os.path.join(DATA_DIR, "dates.txt"), "r") as f:
                for line in f:
                    date_obj = datetime.datetime.strptime(line.strip(), "%Y-%m-%d")
                    if date_obj.weekday() == 2:
                        count += 1
            with open(os.path.join(DATA_DIR, "dates-wednesdays.txt"), "w") as f:
                f.write(str(count))
            return {"message": f"Wednesdays count: {count}"}

        elif "contacts-sorted.json" in task:
            with open(os.path.join(DATA_DIR, "contacts.json"), "r") as f:
                contacts = json.load(f)
            contacts.sort(key=lambda x: (x["last_name"], x["first_name"]))
            with open(os.path.join(DATA_DIR, "contacts-sorted.json"), "w") as f:
                json.dump(contacts, f, indent=2)
            return {"message": "Contacts sorted."}

        elif "logs-recent.txt" in task:
            log_files = sorted(os.listdir(os.path.join(DATA_DIR, "logs")), reverse=True)[:10]
            first_lines = []
            for log in log_files:
                with open(os.path.join(DATA_DIR, "logs", log), "r") as f:
                    first_lines.append(f.readline().strip())
            with open(os.path.join(DATA_DIR, "logs-recent.txt"), "w") as f:
                f.write("\n".join(first_lines))
            return {"message": "Recent log lines extracted."}

        elif "docs/index.json" in task:
            index = {}
            for root, _, files in os.walk(os.path.join(DATA_DIR, "docs")):
                for file in files:
                    if file.endswith(".md"):
                        with open(os.path.join(root, file), "r") as f:
                            for line in f:
                                if line.startswith("# "):
                                    index[file] = line.strip("# ").strip()
                                    break
            with open(os.path.join(DATA_DIR, "docs/index.json"), "w") as f:
                json.dump(index, f, indent=2)
            return {"message": "Docs indexed."}

        elif "email-sender.txt" in task:
            with open(os.path.join(DATA_DIR, "email.txt"), "r") as f:
                for line in f:
                    if line.startswith("From: "):
                        email_address = line.split("<")[1].split(">")[0]
                        break
            with open(os.path.join(DATA_DIR, "email-sender.txt"), "w") as f:
                f.write(email_address)
            return {"message": f"Extracted sender email: {email_address}"}

        elif "credit-card.txt" in task:
            return {"message": "Credit card OCR task requires an LLM (implement separately)."}

        elif "comments-similar.txt" in task:
            return {"message": "Embeddings task requires an LLM (implement separately)."}

        elif "ticket-sales-gold.txt" in task:
            conn = sqlite3.connect(os.path.join(DATA_DIR, "ticket-sales.db"))
            cursor = conn.cursor()
            cursor.execute("SELECT SUM(units * price) FROM tickets WHERE type='Gold'")
            total_sales = cursor.fetchone()[0]
            conn.close()
            with open(os.path.join(DATA_DIR, "ticket-sales-gold.txt"), "w") as f:
                f.write(str(total_sales))
            return {"message": f"Total Gold ticket sales: {total_sales}"}

        else:
            return {"error": "Unknown task."}

    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
