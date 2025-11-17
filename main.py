import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from bson import ObjectId

from database import create_document, get_documents, db
from schemas import Lead

app = FastAPI(title="Investing Coach API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "Investing Coach API is running"}

@app.get("/test")
def test_database():
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }

    try:
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Configured"
            response["database_name"] = db.name if hasattr(db, 'name') else "✅ Connected"
            response["connection_status"] = "Connected"

            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️  Connected but Error: {str(e)[:50]}"
        else:
            response["database"] = "⚠️  Available but not initialized"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"

    import os
    response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
    response["database_name"] = "✅ Set" if os.getenv("DATABASE_NAME") else "❌ Not Set"

    return response

# Lead submission model for request body (optional override)
class LeadIn(BaseModel):
    name: str
    email: str
    phone: Optional[str] = None
    plan: Optional[str] = None
    message: Optional[str] = None

@app.post("/api/leads")
def create_lead(lead: LeadIn):
    try:
        lead_doc = Lead(
            name=lead.name,
            email=lead.email,
            phone=lead.phone,
            plan=lead.plan if lead.plan in ["Starter", "Pro", "Elite"] else None,
            message=lead.message,
            source="website"
        )
        inserted_id = create_document("lead", lead_doc)
        return {"success": True, "id": inserted_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/leads")
def list_leads(limit: int = 50):
    try:
        docs = get_documents("lead", limit=limit)
        # Convert ObjectId to str for JSON
        for d in docs:
            if d.get("_id"):
                d["_id"] = str(d["_id"])
            if d.get("created_at"):
                d["created_at"] = str(d["created_at"])  # naive serialization
            if d.get("updated_at"):
                d["updated_at"] = str(d["updated_at"])  # naive serialization
        return {"items": docs}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
