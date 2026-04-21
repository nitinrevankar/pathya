"""
e-Prakruti FastAPI Backend — v8.0
Dr. Prasanna Kulkarni | MD Ayurveda, MS Data Science
SKAMC, Bangalore

This API exposes all scoring, PDF, and prompt logic for use by the
CodeIgniter 4 web frontend. Run on localhost:8001.

Usage:
    pip install fastapi uvicorn reportlab pillow python-multipart
    uvicorn eprakruti_api:app --host 0.0.0.0 --port 8001 --reload

All heavy logic is imported from eprakruti_core.py
"""

from fastapi import FastAPI, HTTPException
from fastapi.responses import Response, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import sys, os

# ── Import all core logic ──────────────────────────────────────────────────
sys.path.insert(0, os.path.dirname(__file__))
from eprakruti_core import (
    calc_bmi, calc_bmr, calc_fat_pct, calc_whr, bmi_category, specific_bmr,
    score_anthropometric, combine_scores, calculate_questionnaire, prakriti_type,
    get_desha, check_conflicts, build_ai_prompt_core,
    QUESTIONS, AHARA_DATA, INDIA_GEO, CONFLICT_PAIRS,
    DISEASE_PRONE_PDF, PRECAUTIONS_PDF,
)

app = FastAPI(
    title="e-Prakruti API",
    description="Ayurvedic Prakriti assessment backend — SKAMC Bangalore",
    version="8.0",
)

# Allow CI4 frontend to call this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # Restrict to your CI4 domain in production
    allow_methods=["*"],
    allow_headers=["*"],
)


# ══════════════════════════════════════════════════════════════════════════════
#  REQUEST / RESPONSE MODELS
# ══════════════════════════════════════════════════════════════════════════════

class AnthroInput(BaseModel):
    name: str
    age: int
    gender: str                   # "Male" or "Female"
    height_cm: float
    weight_kg: float
    waist_cm: Optional[float] = 0
    hip_cm: Optional[float] = 0
    state: Optional[str] = "Karnataka"
    district: Optional[str] = "Bengaluru Urban"
    dietary_pref: Optional[str] = "Lacto-Vegetarian (plant + milk products)"
    meat_freq: Optional[int] = 3

class ScoreRequest(BaseModel):
    responses: Dict[str, Any]     # {"1": 0, "4": [0,2], ...}  key=qid, val=option index or list
    profile: AnthroInput

class PDFRequest(BaseModel):
    responses: Dict[str, Any]
    profile: AnthroInput
    ai_response: Optional[str] = ""   # For combined PDF only

class PromptRequest(BaseModel):
    responses: Dict[str, Any]
    profile: AnthroInput


# ══════════════════════════════════════════════════════════════════════════════
#  HELPER
# ══════════════════════════════════════════════════════════════════════════════

def _build_profile_dict(p: AnthroInput) -> dict:
    bmi   = calc_bmi(p.weight_kg, p.height_cm)
    bmr   = calc_bmr(p.weight_kg, p.height_cm, p.age, p.gender)
    fat   = calc_fat_pct(bmi, p.age, p.gender)
    sbmr  = specific_bmr(bmr, p.weight_kg)
    whr   = calc_whr(p.waist_cm, p.hip_cm) if p.waist_cm and p.hip_cm else None
    return {
        "name": p.name, "age": p.age, "gender": p.gender,
        "height_cm": p.height_cm, "weight_kg": p.weight_kg,
        "waist_cm": p.waist_cm, "hip_cm": p.hip_cm,
        "bmi": bmi, "bmi_category": bmi_category(bmi),
        "bmr": bmr, "fat_pct": fat, "specific_bmr": sbmr, "whr": whr,
        "state": p.state, "district": p.district,
        "dietary_pref": p.dietary_pref, "meat_freq": p.meat_freq,
    }

def _parse_responses(raw: dict) -> dict:
    """Convert JSON responses (string keys, list or int values) to proper types."""
    parsed = {}
    for k, v in raw.items():
        qid = int(k)
        q = next((x for x in QUESTIONS if x["id"] == qid), None)
        if q is None:
            continue
        if q["type"] == "single":
            parsed[qid] = int(v) if v is not None else None
        else:
            parsed[qid] = set(v) if isinstance(v, list) else set()
    return parsed


# ══════════════════════════════════════════════════════════════════════════════
#  ENDPOINTS
# ══════════════════════════════════════════════════════════════════════════════

@app.get("/", tags=["Health"])
def root():
    return {"status": "ok", "app": "e-Prakruti API v8.0", "institution": "SKAMC Bangalore"}


@app.get("/questions", tags=["Data"])
def get_questions():
    """Return full question database (stripped of SVG for API use)."""
    clean = []
    for q in QUESTIONS:
        clean.append({
            "id": q["id"], "trait": q["trait"], "type": q["type"],
            "weight": q.get("weight", 2), "question": q["question"],
            "guna": q["guna"], "reference": q["reference"],
            "learn_more": q["learn_more"],
            "options": [{"text": o["text"]} for o in q["options"]],
            "mandatory": q["id"] in _MANDATORY_QS,
        })
    return JSONResponse(clean)


@app.get("/ahara", tags=["Data"])
def get_ahara():
    """Return AHARA_DATA food database."""
    return JSONResponse(AHARA_DATA)


@app.get("/geo", tags=["Data"])
def get_geo():
    """Return India geography → Desha mapping."""
    return JSONResponse(INDIA_GEO)


@app.get("/conflicts", tags=["Data"])
def get_conflicts():
    """Return conflict pair definitions."""
    return JSONResponse(CONFLICT_PAIRS)


@app.post("/score", tags=["Assessment"])
def score(req: ScoreRequest):
    """
    Calculate VPK scores from questionnaire responses + anthropometrics.
    
    Returns:
        trait_pct     — per-trait VPK percentages
        quest_op      — questionnaire overall VPK
        anthro_op     — anthropometric VPK
        final_op      — weighted final VPK (80:20)
        prakriti_name — e.g. "Vata Pradhana Kapha Prakriti"
        prakriti_icon — emoji
        conflicts     — list of triggered conflict pairs
        desha         — Desha classification
        desha_desc    — Description of Desha
    """
    responses = _parse_responses(req.responses)
    prof      = _build_profile_dict(req.profile)
    
    trait_pct, quest_op = calculate_questionnaire(responses)
    anthro_op = score_anthropometric(prof)
    final_op  = combine_scores(quest_op, anthro_op)
    pname, picon, pcolor = prakriti_type(final_op)
    conflicts = check_conflicts(responses)
    desha     = get_desha(req.profile.state, req.profile.district)
    
    return {
        "trait_pct":      trait_pct,
        "quest_op":       quest_op,
        "anthro_op":      anthro_op,
        "final_op":       final_op,
        "prakriti_name":  pname,
        "prakriti_icon":  picon,
        "prakriti_color": pcolor,
        "conflicts":      conflicts,
        "desha":          desha,
        "profile":        prof,
        "disease_prone":  {
            "pradhana":    DISEASE_PRONE_PDF.get(
                           sorted([("Vata",final_op["V"]),("Pitta",final_op["P"]),
                                   ("Kapha",final_op["K"])], key=lambda x:-x[1])[0][0], []),
            "anupradhana": DISEASE_PRONE_PDF.get(
                           sorted([("Vata",final_op["V"]),("Pitta",final_op["P"]),
                                   ("Kapha",final_op["K"])], key=lambda x:-x[1])[1][0], []),
        },
        "precautions":    PRECAUTIONS_PDF.get(
                           sorted([("Vata",final_op["V"]),("Pitta",final_op["P"]),
                                   ("Kapha",final_op["K"])], key=lambda x:-x[1])[0][0], []),
    }


@app.post("/pdf/assessment", tags=["PDF"])
def pdf_assessment(req: PDFRequest):
    """
    Generate the e-Prakruti Assessment PDF report.
    Returns PDF bytes as application/pdf.
    CI4 should stream this directly to the user as a file download.
    """
    try:
        from eprakruti_pdf import generate_pdf_report_api
        responses = _parse_responses(req.responses)
        prof      = _build_profile_dict(req.profile)
        trait_pct, quest_op = calculate_questionnaire(responses)
        anthro_op = score_anthropometric(prof)
        final_op  = combine_scores(quest_op, anthro_op)
        pname, picon, pcolor = prakriti_type(final_op)
        pdf_bytes = generate_pdf_report_api(
            profile=prof, trait_pct=trait_pct, quest_op=quest_op,
            anthro_op=anthro_op, final_op=final_op,
            pname=pname, picon=picon, pcolor_hex=pcolor,
        )
        filename = f"ePrakruti_{req.profile.name.replace(' ','_')}.pdf"
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/pdf/combined", tags=["PDF"])
def pdf_combined(req: PDFRequest):
    """
    Generate combined PDF: Assessment + AI diet plan.
    Requires ai_response field to contain the pasted e-PathyaGPT output.
    """
    try:
        from eprakruti_pdf import generate_combined_pdf_api
        responses = _parse_responses(req.responses)
        prof      = _build_profile_dict(req.profile)
        trait_pct, quest_op = calculate_questionnaire(responses)
        anthro_op = score_anthropometric(prof)
        final_op  = combine_scores(quest_op, anthro_op)
        pname, picon, pcolor = prakriti_type(final_op)
        pdf_bytes = generate_combined_pdf_api(
            profile=prof, trait_pct=trait_pct, quest_op=quest_op,
            anthro_op=anthro_op, final_op=final_op, pname=pname,
            picon=picon, pcolor_hex=pcolor,
            ai_response=req.ai_response or "",
        )
        filename = f"ePrakruti_Complete_{req.profile.name.replace(' ','_')}.pdf"
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/prompt", tags=["AI"])
def generate_prompt(req: PromptRequest):
    """
    Generate the e-PathyaGPT prompt string.
    CI4 returns this to the browser; user copies and pastes into GPT.
    """
    responses = _parse_responses(req.responses)
    prof      = _build_profile_dict(req.profile)
    trait_pct, quest_op = calculate_questionnaire(responses)
    anthro_op = score_anthropometric(prof)
    final_op  = combine_scores(quest_op, anthro_op)
    pname, picon, pcolor = prakriti_type(final_op)
    desha = get_desha(req.profile.state, req.profile.district)
    
    prompt = build_ai_prompt_core(
        prof=prof, final_op=final_op, pname=pname,
        desha=desha,
        dietary_pref=req.profile.dietary_pref,
        meat_freq=req.profile.meat_freq,
        responses=responses,
    )
    return {"prompt": prompt, "char_count": len(prompt)}


# ── Compute mandatory questions set at startup ─────────────────────────────
_TRAITS      = ["Physical","Physiological","Psychological","Behavioral"]
_TRAIT_Q     = {t:[q for q in QUESTIONS if q["trait"]==t] for t in _TRAITS}
def _build_mandatory():
    mset = {1,3,4,5,7,16,17,18,19}
    for trait in ["Psychological","Behavioral"]:
        w3 = [q["id"] for q in _TRAIT_Q[trait] if q.get("weight",2)==3]
        others = [q["id"] for q in _TRAIT_Q[trait] if q["id"] not in w3]
        mset |= set((w3+others)[:3])
    return mset
_MANDATORY_QS = _build_mandatory()
