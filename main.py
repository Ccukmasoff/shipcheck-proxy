import os, base64, json
from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
import httpx

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
MODEL_NAME = os.getenv("OPENAI_VISION_MODEL", "gpt-4o-mini")
ALLOWED_ORIGINS = [o.strip() for o in os.getenv("ALLOWED_ORIGINS", "*").split(",")]

app = FastAPI(title="ShipCheckAI Proxy", version="1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

SYSTEM_PROMPT = (
    "You are ShipCheckAI. Analyze a single photo from a vessel inspection. "
    "Output strict JSON with fields: status(one of GREEN,YELLOW,RED), "
    "description, recommendation. Use maritime safety best practices (SOLAS/ISM). "
    "Be concise and actionable."
)

async def analyze_image_bytes(client: httpx.AsyncClient, image_bytes: bytes):
    b64 = base64.b64encode(image_bytes).decode("utf-8")
    payload = {
        "model": MODEL_NAME,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": [
                    {"type": "input_text", "text": "Analyze this photo and respond with the JSON."},
                    {"type": "input_image", "image_url": f"data:image/jpeg;base64,{b64}"},
                ],
            },
        ],
        "temperature": 0.2,
    }
    r = await client.post(
        "https://api.openai.com/v1/chat/completions",
        headers={"Authorization": f"Bearer {OPENAI_API_KEY}"},
        json=payload,
        timeout=60.0,
    )
    r.raise_for_status()
    data = r.json()
    text = data["choices"][0]["message"]["content"]

    # Try to extract JSON block
    try:
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1:
            text = text[start:end+1]
        parsed = json.loads(text)
        status = str(parsed.get("status","")).upper()
        if status not in ["GREEN","YELLOW","RED"]:
            status = "YELLOW"
        return {
            "status": status,
            "description": parsed.get("description",""),
            "recommendation": parsed.get("recommendation",""),
        }
    except Exception:
        return {
            "status": "YELLOW",
            "description": text.strip()[:1000],
            "recommendation": "Provide corrective actions per SOLAS/ISM and re-inspect.",
        }

@app.post("/api/health")
async def health():
    return {"ok": True, "model": MODEL_NAME}

@app.post("/api/analyze")
async def analyze(file: UploadFile = File(...)):
    if not OPENAI_API_KEY:
        return {"error": "OPENAI_API_KEY is not set"}
    content = await file.read()
    async with httpx.AsyncClient() as client:
        result = await analyze_image_bytes(client, content)
    return {"filename": file.filename, **result}

@app.post("/api/analyze/batch")
async def analyze_batch(files: list[UploadFile] = File(...)):
    if not OPENAI_API_KEY:
        return {"error": "OPENAI_API_KEY is not set"}
    out = []
    async with httpx.AsyncClient() as client:
        for f in files:
            content = await f.read()
            result = await analyze_image_bytes(client, content)
            out.append({"filename": f.filename, **result})
    return {"results": out}
