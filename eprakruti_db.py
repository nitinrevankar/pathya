"""
eprakruti_db.py  —  MySQL persistence layer for e-Prakruti v8.0
Dr. Prasanna Kulkarni | MD Ayurveda, MS Data Science | SKAMC, Bangalore

Targets your three live tables:
  health_seekers   ← personal info + all anthropometrics
  prakriti_scores  ← VPK % per trait + final prakriti label
  responses        ← per-question answers (single & multi)

Public API (same signatures as before — eprakruti_api.py needs ZERO changes):
    load_lookup_maps()
    upsert_user(name, age, gender, state, district, email, mobile)  → seeker_id
    save_assessment(user_id, profile, responses, …)                 → result dict
    get_session(session_id)
    get_user_sessions(user_id)

Extra helpers:
    streamlit_save(...)          all-in-one for prakruti_app_v8.py
    get_seeker_by_token(token)   retrieve result by session token
    get_all_responses(seeker_id) raw response rows for a seeker
    configure_from_streamlit_secrets()

Install:
    pip install mysql-connector-python

Set these env vars (or edit DB_CONFIG, or use secrets.toml):
    EPRAKRUTI_DB_HOST  EPRAKRUTI_DB_PORT  EPRAKRUTI_DB_USER
    EPRAKRUTI_DB_PASS  EPRAKRUTI_DB_NAME
"""

from __future__ import annotations

import hashlib
import os
import time
from typing import Any, Dict, List, Optional

import mysql.connector
from mysql.connector import pooling

# ─────────────────────────────────────────────────────────────────────────────
#  DB CONFIG
# ─────────────────────────────────────────────────────────────────────────────

DB_CONFIG: Dict[str, Any] = {
    "host":      os.getenv("EPRAKRUTI_DB_HOST", "localhost"),
    "port":      int(os.getenv("EPRAKRUTI_DB_PORT", 3306)),
    "user":      os.getenv("EPRAKRUTI_DB_USER", "wzwejtmd_userfll"),
    "password":  os.getenv("EPRAKRUTI_DB_PASS", "iyFa4ojSqwXG#]=i"),
    "database":  os.getenv("EPRAKRUTI_DB_NAME", "wzwejtmd_eprakruti_schema"),
    "charset":   "utf8mb4",
    "autocommit": False,
}

_pool: Optional[pooling.MySQLConnectionPool] = None


# ─────────────────────────────────────────────────────────────────────────────
#  INTERNAL HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def _get_conn():
    """Return a pooled connection, or a direct one if pool not yet created."""
    if _pool:
        return _pool.get_connection()
    return mysql.connector.connect(**DB_CONFIG)


def _make_token(name: str, age: int, gender: str) -> str:
    """32-char hex token — unique per person per second."""
    raw = f"{name}|{age}|{gender}|{int(time.time())}"
    return hashlib.md5(raw.encode()).hexdigest()


def _r(val, default: float = 0.0) -> float:
    """Safe round-2 float cast."""
    try:
        return round(float(val), 2)
    except Exception:
        return default


def _option_text(question_id: int, sel) -> str:
    """
    Convert a selection (int index or set of indices) to human-readable text.
    Uses QUESTIONS from eprakruti_core; falls back to raw string if unavailable.
    """
    try:
        from eprakruti_core import QUESTIONS
        q = next((x for x in QUESTIONS if x["id"] == question_id), None)
        if q is None:
            return str(sel)
        opts = q["options"]
        if isinstance(sel, int):
            return opts[sel]["text"] if sel < len(opts) else str(sel)
        parts = [opts[i]["text"] for i in sorted(sel) if i < len(opts)]
        return " | ".join(parts)
    except Exception:
        return str(sel)


def _per_question_scores(responses: Dict[int, Any]) -> Dict[int, Dict[str, int]]:
    """
    Compute raw VPK points earned per question.
    Returns { question_number : {"V": int, "P": int, "K": int} }
    """
    try:
        from eprakruti_core import QUESTIONS
    except ImportError:
        return {}

    out: Dict[int, Dict[str, int]] = {}
    for q in QUESTIONS:
        qid = q["id"]
        sel = responses.get(qid)
        if sel is None:
            continue
        opts = q["options"]
        wt   = q.get("weight", 2)
        V = P = K = 0
        if q["type"] == "single":
            if isinstance(sel, int) and 0 <= sel < len(opts):
                V = opts[sel].get("V", 0) * wt
                P = opts[sel].get("P", 0) * wt
                K = opts[sel].get("K", 0) * wt
        else:
            for i in (sel or set()):
                if 0 <= i < len(opts):
                    V += opts[i].get("V", 0) * wt
                    P += opts[i].get("P", 0) * wt
                    K += opts[i].get("K", 0) * wt
        out[qid] = {"V": V, "P": P, "K": K}
    return out


# ─────────────────────────────────────────────────────────────────────────────
#  PUBLIC API
# ─────────────────────────────────────────────────────────────────────────────

def load_lookup_maps() -> None:
    """
    Called at FastAPI startup (app.on_event("startup")).
    Creates the connection pool and does a quick connectivity ping.
    No lookup maps needed for this schema — question numbers ARE question_ids.
    """
    global _pool
    if _pool is not None:
        return  # already created
    _pool = pooling.MySQLConnectionPool(
        pool_name="eprakruti",
        pool_size=10,
        pool_reset_session=True,
        **DB_CONFIG,
    )
    conn = _get_conn()
    conn.ping(reconnect=True)
    conn.close()


def upsert_user(
    name:     str,
    age:      int,
    gender:   str,
    state:    str = "",
    district: str = "",
    email:    Optional[str] = None,   # kept for API signature compat (not in table)
    mobile:   Optional[str] = None,   # kept for API signature compat (not in table)
) -> int:
    """
    Find or create a health_seekers row.

    Dedup order:
      1. full_name + age + gender + state  →  return existing id
      2. Otherwise insert fresh row

    Returns health_seekers.id (int).
    """
    conn = _get_conn()
    try:
        cur = conn.cursor(dictionary=True)

        # Try to find existing
        cur.execute(
            """
            SELECT id FROM health_seekers
            WHERE full_name = %s AND age = %s AND gender = %s AND state = %s
            ORDER BY created_at DESC LIMIT 1
            """,
            (name, age, gender, state),
        )
        row = cur.fetchone()
        if row:
            cur.close()
            return int(row["id"])

        # Insert new seeker (anthropometrics back-filled later by save_assessment)
        token = _make_token(name, age, gender)
        cur.execute(
            """
            INSERT INTO health_seekers
                (full_name, age, gender, state, district, dietary_pref,
                 session_token, token, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NOW())
            """,
            (name, age, gender, state, district or "", "Not set", token, token),
        )
        conn.commit()
        new_id = cur.lastrowid
        cur.close()
        return int(new_id)

    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def save_assessment(
    user_id:   int,              # health_seekers.id
    profile:   Dict[str, Any],  # full dict from _build_profile_dict in eprakruti_api.py
    responses: Dict[int, Any],  # { question_number: int_idx | set(int_idx) }
    trait_pct: Dict[str, Dict[str, float]],
    quest_op:  Dict[str, float],   # { "V": %, "P": %, "K": % }  questionnaire only
    anthro_op: Dict[str, float],   # anthropometric only
    final_op:  Dict[str, float],   # blended final (80% quest + 20% anthro)
    pname:     str,
    picon:     str = "",
    pcolor:    str = "#888888",
) -> Dict[str, Any]:
    """
    Persist a complete assessment in a single transaction:

      1. UPDATE health_seekers  — back-fills BMI / BMR / desha / dietary etc.
      2. INSERT prakriti_scores — all 12 VPK trait columns + final label (upsert)
      3. INSERT responses       — one row per answered question (upsert)

    Returns:
        { "user_id": int, "session_id": int, "session_token": str }
        session_id == user_id == health_seekers.id  (one seeker, one assessment)
    """
    seeker_id = user_id
    conn = _get_conn()

    try:
        cur = conn.cursor(dictionary=True)

        # ── Step 1: back-fill health_seekers ─────────────────────────────────
        desha_raw = profile.get("desha") or ""
        if isinstance(desha_raw, dict):
            desha_str = desha_raw.get("desha", desha_raw.get("type", "Sadharana"))
        else:
            desha_str = str(desha_raw).strip() or None

        cur.execute(
            """
            UPDATE health_seekers SET
                height_cm    = %s,
                weight_kg    = %s,
                waist_cm     = %s,
                hip_cm       = %s,
                bmi          = %s,
                bmi_category = %s,
                bmr_kcal     = %s,
                fat_pct      = %s,
                specific_bmr = %s,
                whr          = %s,
                district     = %s,
                desha        = %s,
                dietary_pref = %s,
                meat_freq    = %s
            WHERE id = %s
            """,
            (
                _r(profile.get("height_cm"))     or None,
                _r(profile.get("weight_kg"))     or None,
                _r(profile.get("waist_cm"))      or None,
                _r(profile.get("hip_cm"))        or None,
                _r(profile.get("bmi"))           or None,
                profile.get("bmi_category")      or None,
                _r(profile.get("bmr"))           or None,  # bmr_kcal column
                _r(profile.get("fat_pct"))       or None,
                _r(profile.get("specific_bmr"))  or None,
                _r(profile.get("whr"))           or None,
                profile.get("district", ""),
                desha_str,
                profile.get("dietary_pref", "Not set"),
                int(profile.get("meat_freq", 3)),
                seeker_id,
            ),
        )

        # Retrieve the token we'll return
        cur.execute("SELECT token FROM health_seekers WHERE id = %s", (seeker_id,))
        tok_row = cur.fetchone()
        token   = tok_row["token"] if tok_row else _make_token(
            profile.get("name", ""), int(profile.get("age", 0)), profile.get("gender", ""))

        # ── Step 2: prakriti_scores (upsert on unique seeker_id) ─────────────
        def tp(trait: str, d: str) -> float:
            return _r(trait_pct.get(trait, {}).get(d, 0.0))

        cur.execute(
            """
            INSERT INTO prakriti_scores
                (seeker_id,
                 phys_v,   phys_p,   phys_k,
                 physio_v, physio_p, physio_k,
                 psych_v,  psych_p,  psych_k,
                 behav_v,  behav_p,  behav_k,
                 quest_v,  quest_p,  quest_k,
                 anthro_v, anthro_p, anthro_k,
                 final_v,  final_p,  final_k,
                 prakriti_name, prakriti_icon, prakriti_color,
                 scored_at)
            VALUES
                (%s,
                 %s, %s, %s,   %s, %s, %s,   %s, %s, %s,   %s, %s, %s,
                 %s, %s, %s,   %s, %s, %s,   %s, %s, %s,
                 %s, %s, %s,   NOW())
            ON DUPLICATE KEY UPDATE
                 phys_v        = VALUES(phys_v),
                 phys_p        = VALUES(phys_p),
                 phys_k        = VALUES(phys_k),
                 physio_v      = VALUES(physio_v),
                 physio_p      = VALUES(physio_p),
                 physio_k      = VALUES(physio_k),
                 psych_v       = VALUES(psych_v),
                 psych_p       = VALUES(psych_p),
                 psych_k       = VALUES(psych_k),
                 behav_v       = VALUES(behav_v),
                 behav_p       = VALUES(behav_p),
                 behav_k       = VALUES(behav_k),
                 quest_v       = VALUES(quest_v),
                 quest_p       = VALUES(quest_p),
                 quest_k       = VALUES(quest_k),
                 anthro_v      = VALUES(anthro_v),
                 anthro_p      = VALUES(anthro_p),
                 anthro_k      = VALUES(anthro_k),
                 final_v       = VALUES(final_v),
                 final_p       = VALUES(final_p),
                 final_k       = VALUES(final_k),
                 prakriti_name  = VALUES(prakriti_name),
                 prakriti_icon  = VALUES(prakriti_icon),
                 prakriti_color = VALUES(prakriti_color),
                 scored_at      = NOW()
            """,
            (
                seeker_id,
                tp("Physical", "V"),      tp("Physical", "P"),      tp("Physical", "K"),
                tp("Physiological", "V"), tp("Physiological", "P"), tp("Physiological", "K"),
                tp("Psychological", "V"), tp("Psychological", "P"), tp("Psychological", "K"),
                tp("Behavioral", "V"),    tp("Behavioral", "P"),    tp("Behavioral", "K"),
                _r(quest_op.get("V")),    _r(quest_op.get("P")),    _r(quest_op.get("K")),
                _r(anthro_op.get("V")),   _r(anthro_op.get("P")),   _r(anthro_op.get("K")),
                _r(final_op.get("V")),    _r(final_op.get("P")),    _r(final_op.get("K")),
                pname, picon, pcolor,
            ),
        )

        # ── Step 3: responses (one row per question, upsert) ──────────────────
        try:
            from eprakruti_core import QUESTIONS
            qtype_map = {q["id"]: q["type"] for q in QUESTIONS}
        except ImportError:
            qtype_map = {}

        for qnum, sel in responses.items():
            qnum  = int(qnum)
            qtype = qtype_map.get(qnum, "single" if isinstance(sel, int) else "multi")

            if qtype == "single":
                ans_index   = int(sel) if isinstance(sel, int) else None
                ans_indices = None
            else:
                idx_list    = sorted(sel) if isinstance(sel, (set, list)) else []
                ans_index   = None
                ans_indices = ",".join(str(i) for i in idx_list) if idx_list else None

            ans_text = _option_text(qnum, sel)

            cur.execute(
                """
                INSERT INTO responses
                    (seeker_id, question_id, question_type,
                     answer_index, answer_indices, answer_text,
                     created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, NOW(), NOW())
                ON DUPLICATE KEY UPDATE
                    question_type   = VALUES(question_type),
                    answer_index    = VALUES(answer_index),
                    answer_indices  = VALUES(answer_indices),
                    answer_text     = VALUES(answer_text),
                    updated_at      = NOW()
                """,
                (seeker_id, qnum, qtype, ans_index, ans_indices, ans_text),
            )

        conn.commit()
        cur.close()

        return {
            "user_id":       seeker_id,
            "session_id":    seeker_id,
            "session_token": token,
        }

    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


# ─────────────────────────────────────────────────────────────────────────────
#  READ HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def get_session(session_id: int) -> Optional[Dict[str, Any]]:
    """
    Fetch a seeker's full joined result (health_seekers + prakriti_scores).
    session_id == health_seekers.id in this schema.
    """
    conn = _get_conn()
    try:
        cur = conn.cursor(dictionary=True)
        cur.execute(
            """
            SELECT
                hs.id              AS session_id,
                hs.full_name,
                hs.age,
                hs.gender,
                hs.state,
                hs.district,
                hs.desha,
                hs.height_cm,
                hs.weight_kg,
                hs.bmi,
                hs.bmi_category,
                hs.bmr_kcal,
                hs.fat_pct,
                hs.specific_bmr,
                hs.whr,
                hs.dietary_pref,
                hs.meat_freq,
                hs.created_at,
                hs.token           AS session_token,
                ps.phys_v,    ps.phys_p,    ps.phys_k,
                ps.physio_v,  ps.physio_p,  ps.physio_k,
                ps.psych_v,   ps.psych_p,   ps.psych_k,
                ps.behav_v,   ps.behav_p,   ps.behav_k,
                ps.quest_v,   ps.quest_p,   ps.quest_k,
                ps.anthro_v,  ps.anthro_p,  ps.anthro_k,
                ps.final_v    AS overall_vata_pct,
                ps.final_p    AS overall_pitta_pct,
                ps.final_k    AS overall_kapha_pct,
                ps.prakriti_name,
                ps.prakriti_icon,
                ps.prakriti_color,
                ps.scored_at
            FROM health_seekers hs
            LEFT JOIN prakriti_scores ps ON ps.seeker_id = hs.id
            WHERE hs.id = %s
            LIMIT 1
            """,
            (session_id,),
        )
        row = cur.fetchone()
        cur.close()
        if row:
            import decimal
            return {k: (float(v) if isinstance(v, decimal.Decimal) else v)
                    for k, v in row.items()}
        return None
    finally:
        conn.close()


def get_user_sessions(user_id: int) -> List[Dict[str, Any]]:
    """
    All assessments for a seeker (prakriti_scores has UNIQUE on seeker_id,
    so this returns a list of 0 or 1 item). Kept as list for API compat.
    """
    result = get_session(user_id)
    return [result] if result else []


def get_seeker_by_token(token: str) -> Optional[Dict[str, Any]]:
    """Retrieve a full result row using the session token."""
    conn = _get_conn()
    try:
        cur = conn.cursor(dictionary=True)
        cur.execute(
            "SELECT id FROM health_seekers WHERE token = %s OR session_token = %s LIMIT 1",
            (token, token),
        )
        row = cur.fetchone()
        cur.close()
        return get_session(int(row["id"])) if row else None
    finally:
        conn.close()


def get_all_responses(seeker_id: int) -> List[Dict[str, Any]]:
    """Return all saved responses for a seeker, ordered by question_id."""
    conn = _get_conn()
    try:
        cur = conn.cursor(dictionary=True)
        cur.execute(
            "SELECT * FROM responses WHERE seeker_id = %s ORDER BY question_id",
            (seeker_id,),
        )
        rows = cur.fetchall()
        cur.close()
        return rows
    finally:
        conn.close()


# ─────────────────────────────────────────────────────────────────────────────
#  STREAMLIT ALL-IN-ONE HELPER
# ─────────────────────────────────────────────────────────────────────────────

def streamlit_save(
    prof:      Dict[str, Any],
    responses: Dict[int, Any],
    trait_pct: Dict[str, Dict[str, float]],
    quest_op:  Dict[str, float],
    anthro_op: Dict[str, float],
    final_op:  Dict[str, float],
    pname:     str,
    picon:     str = "",
    pcolor:    str = "#888888",
) -> Dict[str, Any]:
    """
    All-in-one save for prakruti_app_v8.py.  Paste this block into your
    results tab after scores are computed:

        import eprakruti_db as db
        # — call once at top of app —
        # db.configure_from_streamlit_secrets()

        if st.button("💾 Save Assessment"):
            result = db.streamlit_save(
                prof      = prof,
                responses = st.session_state.responses,
                trait_pct = trait_pct,
                quest_op  = quest_op,
                anthro_op = anthro_op,
                final_op  = final_op,
                pname     = pname,
                picon     = picon,
                pcolor    = pcolor,
            )
            if result["db_saved"]:
                st.success(f"Saved ✓  seeker_id = {result['seeker_id']}")
            else:
                st.error(f"DB error: {result['db_error']}")

    Returns:
        { "seeker_id": int|None, "session_token": str|None,
          "db_saved": bool, "db_error": str|None }
    """
    try:
        load_lookup_maps()
    except Exception:
        pass   # falls back to direct connections

    try:
        seeker_id = upsert_user(
            name     = prof.get("name", ""),
            age      = int(prof.get("age", 0)),
            gender   = prof.get("gender", "Male"),
            state    = prof.get("state", ""),
            district = prof.get("district", ""),
        )
        result = save_assessment(
            user_id   = seeker_id,
            profile   = prof,
            responses = responses,
            trait_pct = trait_pct,
            quest_op  = quest_op,
            anthro_op = anthro_op,
            final_op  = final_op,
            pname     = pname,
            picon     = picon,
            pcolor    = pcolor,
        )
        return {
            "seeker_id":     seeker_id,
            "session_token": result["session_token"],
            "db_saved":      True,
            "db_error":      None,
        }
    except Exception as exc:
        return {
            "seeker_id":     None,
            "session_token": None,
            "db_saved":      False,
            "db_error":      str(exc),
        }


# ─────────────────────────────────────────────────────────────────────────────
#  STREAMLIT SECRETS HELPER
# ─────────────────────────────────────────────────────────────────────────────

def configure_from_streamlit_secrets() -> None:
    """
    Read DB credentials from .streamlit/secrets.toml.

    Add this to secrets.toml:
        [mysql]
        host     = "127.0.0.1"
        port     = 3306
        user     = "root"
        password = "your_password"
        database = "eprakruti_schema"

    Then call this once at the very top of prakruti_app_v8.py (before any DB call):
        import eprakruti_db as db
        db.configure_from_streamlit_secrets()
    """
    try:
        import streamlit as st
        cfg = st.secrets["mysql"]
        DB_CONFIG.update({
            "host":     cfg["host"],
            "port":     int(cfg.get("port", 3306)),
            "user":     cfg["user"],
            "password": cfg["password"],
            "database": cfg["database"],
        })
    except Exception as e:
        raise RuntimeError(
            f"Could not read [mysql] from secrets.toml: {e}\n"
            "Add a [mysql] section or set EPRAKRUTI_DB_* environment variables."
        )


# ─────────────────────────────────────────────────────────────────────────────
#  SELF-TEST   →   python eprakruti_db.py
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("e-Prakruti DB — self-test")
    print(f"Target: {DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}")

    load_lookup_maps()
    print("Pool OK ✓")

    sid = upsert_user(
        name="Test Patient DB", age=32, gender="Female",
        state="Karnataka", district="Bengaluru Urban",
    )
    print(f"Seeker id : {sid}")

    fake_trait = {
        "Physical":      {"V": 40.0, "P": 30.0, "K": 30.0},
        "Physiological": {"V": 35.0, "P": 35.0, "K": 30.0},
        "Psychological": {"V": 30.0, "P": 40.0, "K": 30.0},
        "Behavioral":    {"V": 25.0, "P": 35.0, "K": 40.0},
    }
    fake_final  = {"V": 42.5, "P": 33.0, "K": 24.5}
    fake_anthro = {"V": 20.0, "P": 50.0, "K": 30.0}
    fake_resp   = {1: 2, 4: {0, 2}, 5: 0, 16: 1}

    res = save_assessment(
        user_id   = sid,
        profile   = {
            "name": "Test Patient DB", "age": 32, "gender": "Female",
            "height_cm": 162, "weight_kg": 58, "waist_cm": 70, "hip_cm": 92,
            "bmi": 22.1, "bmi_category": "Normal", "bmr": 1380,
            "fat_pct": 24, "specific_bmr": 23.8, "whr": 0.76,
            "state": "Karnataka", "district": "Bengaluru Urban",
            "dietary_pref": "Lacto-Vegetarian (plant + milk products)",
            "meat_freq": 3,
        },
        responses = fake_resp,
        trait_pct = fake_trait,
        quest_op  = fake_final,
        anthro_op = fake_anthro,
        final_op  = fake_final,
        pname     = "Vata Pradhana Pitta Prakriti",
        picon     = "🌬️",
        pcolor    = "#1a4f96",
    )
    print(f"Assessment: {res}")

    row  = get_session(sid)
    resp = get_all_responses(sid)
    print(f"Fetched   : {row['full_name']}  →  {row['prakriti_name']}")
    print(f"Responses : {len(resp)} rows saved")
    print("\nSelf-test PASSED ✓")