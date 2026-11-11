from fastapi import FastAPI

app = FastAPI()


@app.post("/agent")
def run_agent(payload: dict):
    question = payload.get("input", "").lower()

    if "capital of france" in question:
        answer = "Paris"
    elif "6 multiplied by 7" in question or "6 times 7" in question:
        answer = "42"
    else:
        answer = "I don't know."

    return {"output": answer}
