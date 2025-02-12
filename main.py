from fastapi import FastAPI, HTTPException
import os
import subprocess

app = FastAPI()

DATA_DIR = "./data_output"  # Ensure operations are limited to this directory 

@app.post("/run")
async def run_task(task: str):
    try:
        if "format" in task.lower():
            file_path = f"{DATA_DIR}/format.md"
            subprocess.run(["npx", "prettier", "--write", file_path], check=True)
            return {"message": "File formatted successfully"}

        return {"error": "Task not recognized"}, 400
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/read")
async def read_file(path: str):
    full_path = os.path.join(DATA_DIR, path)
    if not os.path.exists(full_path):
        raise HTTPException(status_code=404, detail="File not found")
    
    with open(full_path, "r") as f:
        content = f.read()
    return {"content": content}

@app.get("/")
def read_root():
    return {"message": "Hello, FastAPI is running!"}
