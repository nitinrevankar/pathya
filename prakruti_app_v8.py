"""
e-Prakruti Assessment Tool — Version 6.0
Dr. Prasanna Kulkarni | MD Ayurveda, MS Data Science
Sri Kalabyraveshwara Swamy Ayurvedic Medical College, Bangalore

Classical Basis:
  Charaka Samhita  — Vimana Sthana 8/96-98; Sharira Sthana 4/34-36; Sutrasthana 26/43
  Sushruta Samhita — Sharira Sthana 4/62-73
  Ashtanga Hridaya — Sharira Sthana 3/83-89; Sutrasthana 2/10, 10/17

v6.0 Features:
  ✦ Anthropometric tab (BMI, BMR, Body Fat%, WHR) as first tab
  ✦ 80:20 weighting — Questionnaire (80%) + Anthropometric (20%) → Final Prakriti
  ✦ SVG illustrations (click-to-reveal per question and per option)
  ✦ All critical question fixes from audit
  ✦ Classical Samhita references only (Charaka / Sushruta / Ashtanga Hridaya)

Run: streamlit run prakruti_app_v3.py
Deps: streamlit, pandas  (no plotly / matplotlib)
"""

import streamlit as st
import pandas as pd
import os
from datetime import date
from io import BytesIO
from PIL import Image as PILImage

# ── ReportLab (PDF generation) ─────────────────────────────────────────────────
try:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.units import mm
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
        HRFlowable, Flowable
    )
    from reportlab.lib.colors import HexColor as RLHexColor
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False

# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="e-Prakruti | Ayurvedic Constitutional Analysis",
    page_icon="🌿", layout="wide",
    initial_sidebar_state="collapsed"
)

# ══════════════════════════════════════════════════════════════════════════════
#  GLOBAL CSS
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,600;1,400&family=Source+Sans+3:wght@300;400;600&display=swap');

.stApp { background: #faf5ec; }

/* ── Header ── */
.main-header {
    background: linear-gradient(135deg,#3d1a06 0%,#7a3210 50%,#b84e14 100%);
    color:white; padding:28px 36px 22px; border-radius:18px; margin-bottom:20px;
    box-shadow: 0 12px 40px rgba(100,30,0,.30);
    border-top: 5px solid #d4a017;
    position: relative; overflow: hidden;
}
.main-header::before {
    content:''; position:absolute; top:0; right:0; width:260px; height:100%;
    background: radial-gradient(ellipse at 80% 50%, rgba(212,160,23,.15), transparent 70%);
}
.main-header h1 {
    font-family:'Playfair Display',Georgia,serif;
    font-size:1.95em; margin:0 0 6px; letter-spacing:.5px;
}
.shloka {
    font-family:'Playfair Display',Georgia,serif;
    font-style:italic; font-size:.9em; opacity:.88;
    border-left:3px solid #d4a017; padding-left:14px;
    margin:14px 0 4px; line-height:1.8;
}
.shloka-src { font-size:.76em; opacity:.65; margin-left:17px; }

/* ── Trait header ── */
.trait-header {
    background: linear-gradient(90deg,#6b2e0a,#b84e14);
    color:white; padding:10px 20px; border-radius:10px;
    font-family:'Playfair Display',Georgia,serif;
    font-size:1.08em; font-weight:600; margin:16px 0 14px;
    border-left:5px solid #d4a017;
}

/* ── Anthro header ── */
.anthro-header {
    background: linear-gradient(90deg,#0d4a6e,#1a7aad);
    color:white; padding:10px 20px; border-radius:10px;
    font-family:'Playfair Display',Georgia,serif;
    font-size:1.08em; font-weight:600; margin:16px 0 14px;
    border-left:5px solid #64c8f0;
}

/* ── Cards ── */
.question-card {
    background:white; border-left:4px solid #b84e14;
    padding:16px 20px; border-radius:10px; margin:10px 0;
    box-shadow: 0 2px 12px rgba(0,0,0,.06);
}
.anthro-card {
    background:white; border-left:4px solid #1a7aad;
    padding:16px 20px; border-radius:10px; margin:10px 0;
    box-shadow: 0 2px 12px rgba(0,0,0,.06);
}
.result-card {
    background:white; padding:20px; border-radius:14px;
    box-shadow: 0 4px 18px rgba(0,0,0,.08); margin:10px 0;
}
.prakriti-banner {
    text-align:center; font-size:2em; font-weight:bold;
    padding:24px; border-radius:14px; margin:16px 0;
    font-family:'Playfair Display',Georgia,serif;
    letter-spacing:.5px;
}

/* ── Question number ── */
.q-num {
    background:#8B4513; color:white; border-radius:50%;
    width:26px; height:26px; display:inline-flex;
    align-items:center; justify-content:center;
    font-size:.8em; font-weight:bold; margin-right:8px;
    vertical-align:middle; flex-shrink:0;
}
.q-title { font-size:1.01em; font-weight:600; color:#2d1a08; }

/* ── Metric cards ── */
.metric-box {
    background: linear-gradient(135deg,#f8f4ee,#efe8d8);
    border:1px solid #d4a017; border-radius:10px;
    padding:12px 16px; text-align:center; margin:4px;
}
.metric-val { font-size:1.55em; font-weight:700; color:#6b2e0a; }
.metric-lbl { font-size:.78em; color:#888; margin-top:2px; }
.metric-sub { font-size:.82em; color:#555; margin-top:3px; font-style:italic; }

/* ── Score comparison table ── */
.score-row {
    display:flex; align-items:center; padding:10px 14px;
    border-radius:8px; margin:5px 0; font-size:.93em;
}
.score-label { width:220px; font-weight:600; color:#444; flex-shrink:0; }
.score-bar-wrap { flex:1; display:flex; align-items:center; gap:10px; }

/* ── Dosha bars ── */
.bar-wrap { margin:7px 0; }
.bar-label { font-size:.87em; font-weight:600; margin-bottom:3px; }
.bar-track {
    background:#ede4d3; border-radius:8px;
    height:26px; overflow:hidden; width:100%;
}
.bar-fill {
    height:26px; border-radius:8px;
    display:flex; align-items:center;
    padding-left:12px; color:white;
    font-weight:700; font-size:.85em;
}
.vata-fill  { background: linear-gradient(90deg,#1a4f96,#4a90d9); }
.pitta-fill { background: linear-gradient(90deg,#9e2a0a,#e05c2e); }
.kapha-fill { background: linear-gradient(90deg,#0d5c30,#2e8b57); }

/* ── Classical badge ── */
.badge {
    display:inline-block; background:#fdf0e0;
    border:1px solid #b84e14; border-radius:5px;
    padding:2px 8px; font-size:.74em; color:#6b2e0a;
    margin:2px 3px 6px;
}

/* ── Shloka box in results ── */
.shloka-box {
    background:#fdf5e6; border-left:4px solid #d4a017;
    padding:14px 18px; border-radius:8px; margin:10px 0;
}
.shloka-text {
    font-family:'Playfair Display',Georgia,serif;
    font-style:italic; font-size:1.05em; color:#4a2008;
}
.shloka-ref { font-size:.78em; color:#999; margin-top:6px; }

/* ── Adjustment box ── */
.adj-box {
    background: linear-gradient(135deg,#e8f4fd,#d0eafa);
    border:1px solid #1a7aad; border-radius:10px;
    padding:14px 18px; margin:12px 0; font-size:.9em;
}
.adj-title { font-weight:700; color:#0d4a6e; margin-bottom:6px; }

/* ── WHR optional note ── */
.optional-note {
    background:#f0f9ff; border:1px dashed #64c8f0;
    border-radius:8px; padding:10px 14px;
    font-size:.85em; color:#0d4a6e; margin:8px 0;
}

/* ── Floating progress circle ── */
.progress-float {
    position: fixed;
    bottom: 28px;
    right: 28px;
    z-index: 9999;
    width: 76px;
    height: 76px;
    border-radius: 50%;
    background: white;
    box-shadow: 0 4px 20px rgba(0,0,0,0.18);
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    cursor: default;
    transition: box-shadow .2s;
}
.progress-float:hover { box-shadow: 0 6px 28px rgba(0,0,0,0.28); }
.progress-float svg { position:absolute; top:0; left:0; }
.progress-float .pf-inner {
    display:flex; flex-direction:column;
    align-items:center; justify-content:center;
    z-index:1;
}
.progress-float .pf-pct {
    font-size:15px; font-weight:800;
    color:#3D1A06; line-height:1;
}
.progress-float .pf-lbl {
    font-size:7px; color:#888;
    font-weight:600; letter-spacing:.4px;
    margin-top:1px;
}

/* ── Mobile responsiveness ── */
@media (max-width: 768px) {
    .stApp { padding: 4px !important; }
    .main-header { padding: 16px 14px 14px; }
    .main-header h1 { font-size: 1.25em; }
    .main-header::before { display: none; }
    .progress-float { bottom:10px; right:10px; width:56px; height:56px; }
    .progress-float .pf-pct { font-size:11px; }
    .progress-float .pf-lbl { font-size:6px; }
    .metric-val { font-size:1.1em; }
    .metric-lbl { font-size:.72em; }
    .score-label { width:120px; font-size:.80em; }
    .prakriti-banner { font-size:1.4em; padding:16px; }
    .question-card { padding:12px 14px; }
    .result-card { padding:14px; }
    .badge { font-size:.68em; }
    .q-num { width:22px; height:22px; font-size:.75em; }
    .anthro-header, .trait-header { font-size:.95em; padding:8px 14px; }
}
</style>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
#  SVG ILLUSTRATIONS  (inline — no external files needed)
# ══════════════════════════════════════════════════════════════════════════════
SVGS = {

# ─────────────────────────────────────────────────────────────────────────────
# DESIGN STANDARD (Medical Illustration):
#   • linearGradient/radialGradient fills — no flat cartoon colors
#   • feDropShadow filters for depth
#   • Correct anatomical proportions
#   • Dosha palette: Vata=#1A4F96, Pitta=#9E2A0A, Kapha=#0D5C30
#   • Sanskrit Guna label + English on every illustration
#   • White/cream background, 400-600px viewBox
#   • Arial 10-11px text — legible at small display sizes
# ─────────────────────────────────────────────────────────────────────────────

"body_builds": """<svg viewBox="0 0 620 260" xmlns="http://www.w3.org/2000/svg"
  style="width:100%;max-width:620px;display:block;margin:auto;border-radius:12px">
  <defs>
    <linearGradient id="bg_bb" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="#fdf8f0"/><stop offset="100%" stop-color="#f5ede0"/>
    </linearGradient>
    <linearGradient id="vata_g" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="#6baed6"/><stop offset="100%" stop-color="#1A4F96"/>
    </linearGradient>
    <linearGradient id="pitta_g" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="#fc8d59"/><stop offset="100%" stop-color="#9E2A0A"/>
    </linearGradient>
    <linearGradient id="kapha_g" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="#74c476"/><stop offset="100%" stop-color="#0D5C30"/>
    </linearGradient>
    <filter id="sh"><feDropShadow dx="0" dy="2" stdDeviation="2" flood-opacity=".15"/></filter>
  </defs>
  <rect width="620" height="260" fill="url(#bg_bb)" rx="12" stroke="#e8d5b0" stroke-width="1"/>
  <text x="310" y="20" text-anchor="middle" fill="#4a2008" font-size="12" font-weight="bold"
        font-family="Arial">Shareera Akriti — Body Constitution Reference</text>
  <text x="310" y="34" text-anchor="middle" fill="#888" font-size="9" font-family="Arial"
        font-style="italic">Charaka Vimana Sthana 8/96-98 | Apachita · Madhyama · Upachita</text>

  <!-- Figure helper macro: head, torso, arms, legs -->
  <!-- 1. Very Lean (Vata) -->
  <g filter="url(#sh)" transform="translate(42,50)">
    <ellipse cx="0" cy="0" rx="13" ry="14" fill="url(#vata_g)" opacity=".9"/>
    <!-- neck -->
    <rect x="-4" y="13" width="8" height="8" rx="2" fill="url(#vata_g)" opacity=".85"/>
    <!-- torso narrow -->
    <rect x="-9" y="21" width="18" height="45" rx="6" fill="url(#vata_g)" opacity=".8"/>
    <!-- arms -->
    <rect x="-18" y="23" width="8" height="38" rx="4" fill="url(#vata_g)" opacity=".7"/>
    <rect x="10" y="23" width="8" height="38" rx="4" fill="url(#vata_g)" opacity=".7"/>
    <!-- legs -->
    <rect x="-10" y="66" width="8" height="52" rx="4" fill="url(#vata_g)" opacity=".75"/>
    <rect x="2"  y="66" width="8" height="52" rx="4" fill="url(#vata_g)" opacity=".75"/>
  </g>
  <text x="42" y="188" text-anchor="middle" fill="#1A4F96" font-size="9" font-weight="bold" font-family="Arial">Very Lean</text>
  <text x="42" y="199" text-anchor="middle" fill="#1A4F96" font-size="8" font-family="Arial">Apachita</text>
  <text x="42" y="210" text-anchor="middle" fill="#555" font-size="8" font-family="Arial" font-style="italic">Vata — Ruksha</text>

  <!-- 2. Lean (Vata) -->
  <g filter="url(#sh)" transform="translate(148,50)">
    <ellipse cx="0" cy="0" rx="14" ry="15" fill="url(#vata_g)" opacity=".9"/>
    <rect x="-5" y="14" width="10" height="8" rx="2" fill="url(#vata_g)" opacity=".85"/>
    <rect x="-12" y="22" width="24" height="48" rx="7" fill="url(#vata_g)" opacity=".8"/>
    <rect x="-21" y="24" width="9" height="40" rx="4" fill="url(#vata_g)" opacity=".7"/>
    <rect x="12"  y="24" width="9" height="40" rx="4" fill="url(#vata_g)" opacity=".7"/>
    <rect x="-13" y="70" width="10" height="52" rx="5" fill="url(#vata_g)" opacity=".75"/>
    <rect x="3"   y="70" width="10" height="52" rx="5" fill="url(#vata_g)" opacity=".75"/>
  </g>
  <text x="148" y="188" text-anchor="middle" fill="#1A4F96" font-size="9" font-weight="bold" font-family="Arial">Lean</text>
  <text x="148" y="199" text-anchor="middle" fill="#1A4F96" font-size="8" font-family="Arial">Laghu Shareera</text>
  <text x="148" y="210" text-anchor="middle" fill="#555" font-size="8" font-family="Arial" font-style="italic">Vata tendency</text>

  <!-- 3. Moderate (Pitta) -->
  <g filter="url(#sh)" transform="translate(262,46)">
    <ellipse cx="0" cy="0" rx="17" ry="18" fill="url(#pitta_g)" opacity=".9"/>
    <rect x="-6" y="17" width="12" height="9" rx="3" fill="url(#pitta_g)" opacity=".85"/>
    <rect x="-17" y="26" width="34" height="52" rx="8" fill="url(#pitta_g)" opacity=".8"/>
    <rect x="-27" y="28" width="10" height="44" rx="5" fill="url(#pitta_g)" opacity=".7"/>
    <rect x="17"  y="28" width="10" height="44" rx="5" fill="url(#pitta_g)" opacity=".7"/>
    <rect x="-17" y="78" width="13" height="54" rx="6" fill="url(#pitta_g)" opacity=".75"/>
    <rect x="4"   y="78" width="13" height="54" rx="6" fill="url(#pitta_g)" opacity=".75"/>
  </g>
  <text x="262" y="188" text-anchor="middle" fill="#9E2A0A" font-size="9" font-weight="bold" font-family="Arial">Moderate</text>
  <text x="262" y="199" text-anchor="middle" fill="#9E2A0A" font-size="8" font-family="Arial">Madhyama</text>
  <text x="262" y="210" text-anchor="middle" fill="#555" font-size="8" font-family="Arial" font-style="italic">Pitta — Teekshna</text>

  <!-- 4. Heavy (Kapha) -->
  <g filter="url(#sh)" transform="translate(390,44)">
    <ellipse cx="0" cy="0" rx="22" ry="22" fill="url(#kapha_g)" opacity=".9"/>
    <rect x="-8" y="21" width="16" height="10" rx="3" fill="url(#kapha_g)" opacity=".85"/>
    <ellipse cx="0" cy="52" rx="28" ry="35" fill="url(#kapha_g)" opacity=".8"/>
    <rect x="-38" y="32" width="11" height="48" rx="5" fill="url(#kapha_g)" opacity=".7"/>
    <rect x="27"  y="32" width="11" height="48" rx="5" fill="url(#kapha_g)" opacity=".7"/>
    <rect x="-22" y="85" width="16" height="50" rx="8" fill="url(#kapha_g)" opacity=".75"/>
    <rect x="6"   y="85" width="16" height="50" rx="8" fill="url(#kapha_g)" opacity=".75"/>
  </g>
  <text x="390" y="188" text-anchor="middle" fill="#0D5C30" font-size="9" font-weight="bold" font-family="Arial">Heavy</text>
  <text x="390" y="199" text-anchor="middle" fill="#0D5C30" font-size="8" font-family="Arial">Upachita</text>
  <text x="390" y="210" text-anchor="middle" fill="#555" font-size="8" font-family="Arial" font-style="italic">Kapha — Sandra·Guru</text>

  <!-- 5. Very Heavy (Kapha) -->
  <g filter="url(#sh)" transform="translate(540,42)">
    <ellipse cx="0" cy="0" rx="25" ry="25" fill="url(#kapha_g)" opacity=".95"/>
    <rect x="-9" y="24" width="18" height="10" rx="3" fill="url(#kapha_g)" opacity=".9"/>
    <ellipse cx="0" cy="62" rx="40" ry="42" fill="url(#kapha_g)" opacity=".85"/>
    <rect x="-52" y="36" width="13" height="52" rx="6" fill="url(#kapha_g)" opacity=".7"/>
    <rect x="39"  y="36" width="13" height="52" rx="6" fill="url(#kapha_g)" opacity=".7"/>
    <rect x="-28" y="100" width="20" height="45" rx="10" fill="url(#kapha_g)" opacity=".8"/>
    <rect x="8"   y="100" width="20" height="45" rx="10" fill="url(#kapha_g)" opacity=".8"/>
  </g>
  <text x="540" y="188" text-anchor="middle" fill="#0D5C30" font-size="9" font-weight="bold" font-family="Arial">Very Heavy</text>
  <text x="540" y="199" text-anchor="middle" fill="#0D5C30" font-size="8" font-family="Arial">Sthula Shareera</text>
  <text x="540" y="210" text-anchor="middle" fill="#555" font-size="8" font-family="Arial" font-style="italic">Kapha — Medovriddhi</text>

  <!-- Dividers -->
  <line x1="95"  y1="45" x2="95"  y2="175" stroke="#e0c8a0" stroke-width="1" stroke-dasharray="4 3"/>
  <line x1="205" y1="45" x2="205" y2="175" stroke="#e0c8a0" stroke-width="1" stroke-dasharray="4 3"/>
  <line x1="325" y1="45" x2="325" y2="175" stroke="#e0c8a0" stroke-width="1" stroke-dasharray="4 3"/>
  <line x1="462" y1="45" x2="462" y2="175" stroke="#e0c8a0" stroke-width="1" stroke-dasharray="4 3"/>

  <!-- Legend bar -->
  <rect x="20" y="228" width="18" height="8" rx="2" fill="url(#vata_g)"/>
  <text x="42" y="236" fill="#1A4F96" font-size="9" font-family="Arial">Vata Prakriti</text>
  <rect x="200" y="228" width="18" height="8" rx="2" fill="url(#pitta_g)"/>
  <text x="222" y="236" fill="#9E2A0A" font-size="9" font-family="Arial">Pitta Prakriti</text>
  <rect x="360" y="228" width="18" height="8" rx="2" fill="url(#kapha_g)"/>
  <text x="382" y="236" fill="#0D5C30" font-size="9" font-family="Arial">Kapha Prakriti</text>
  <text x="540" y="236" fill="#888" font-size="8" font-family="Arial" font-style="italic">CS Vim 8/96-98</text>
</svg>""",

"skin_complexion": """<svg viewBox="0 0 580 210" xmlns="http://www.w3.org/2000/svg"
  style="width:100%;max-width:580px;display:block;margin:auto;border-radius:12px">
  <defs>
    <linearGradient id="bg_sc" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="#fdf8f0"/><stop offset="100%" stop-color="#f0e8d8"/>
    </linearGradient>
    <filter id="sh2"><feDropShadow dx="1" dy="2" stdDeviation="3" flood-opacity=".2"/></filter>
    <!-- Skin tone gradients — realistic -->
    <radialGradient id="s1" cx="45%" cy="35%" r="60%">
      <stop offset="0%" stop-color="#FFE8D6"/><stop offset="100%" stop-color="#F5CBA7"/>
    </radialGradient>
    <radialGradient id="s2" cx="45%" cy="35%" r="60%">
      <stop offset="0%" stop-color="#F5CBA7"/><stop offset="100%" stop-color="#E8A87C"/>
    </radialGradient>
    <radialGradient id="s3" cx="45%" cy="35%" r="60%">
      <stop offset="0%" stop-color="#D4A574"/><stop offset="100%" stop-color="#C08050"/>
    </radialGradient>
    <radialGradient id="s4" cx="45%" cy="35%" r="60%">
      <stop offset="0%" stop-color="#A0714F"/><stop offset="100%" stop-color="#7A5030"/>
    </radialGradient>
    <radialGradient id="s5" cx="45%" cy="35%" r="60%">
      <stop offset="0%" stop-color="#6B3A22"/><stop offset="100%" stop-color="#4A2010"/>
    </radialGradient>
    <radialGradient id="s6" cx="45%" cy="35%" r="60%">
      <stop offset="0%" stop-color="#3B1A0A"/><stop offset="100%" stop-color="#1A0800"/>
    </radialGradient>
  </defs>
  <rect width="580" height="210" fill="url(#bg_sc)" rx="12" stroke="#e8d5b0" stroke-width="1"/>
  <text x="290" y="20" text-anchor="middle" fill="#4a2008" font-size="12" font-weight="bold"
        font-family="Arial">Skin Complexion — Varna Pariksha</text>
  <text x="290" y="33" text-anchor="middle" fill="#888" font-size="9" font-family="Arial"
        font-style="italic">Charaka Vimana Sthana 8/96-98 | Sushruta Sharira Sthana 4/62</text>

  <!-- 6 face ovals with realistic skin gradients -->
  <!-- Face helper: oval + eyes + lips -->
  <!-- Face 1: Very Fair (Kapha) -->
  <g filter="url(#sh2)" transform="translate(48,48)">
    <ellipse cx="0" cy="30" rx="32" ry="40" fill="url(#s1)"/>
    <!-- hair -->
    <ellipse cx="0" cy="-5" rx="33" ry="18" fill="#C8A870" opacity=".9"/>
    <!-- eyes -->
    <ellipse cx="-11" cy="22" rx="7" ry="5" fill="white"/>
    <circle cx="-10" cy="22" r="3.5" fill="#5A3820"/>
    <circle cx="-9"  cy="21" r="1" fill="white"/>
    <ellipse cx="11" cy="22" rx="7" ry="5" fill="white"/>
    <circle cx="12"  cy="22" r="3.5" fill="#5A3820"/>
    <circle cx="13"  cy="21" r="1" fill="white"/>
    <!-- nose -->
    <ellipse cx="0" cy="34" rx="4" ry="5" fill="#E8B890" opacity=".6"/>
    <!-- lips -->
    <path d="M-9 44 Q0 50 9 44" stroke="#C07060" stroke-width="2" fill="none" stroke-linecap="round"/>
    <!-- luster glow -->
    <ellipse cx="-8" cy="10" rx="6" ry="4" fill="white" opacity=".25"/>
  </g>
  <text x="48" y="165" text-anchor="middle" fill="#0D5C30" font-size="10" font-weight="bold" font-family="Arial">Very Fair</text>
  <text x="48" y="176" text-anchor="middle" fill="#0D5C30" font-size="8" font-family="Arial">Gaur · Padma</text>
  <text x="48" y="187" text-anchor="middle" fill="#888" font-size="8" font-family="Arial" font-style="italic">Kapha — Snigdha</text>

  <!-- Face 2: Fair-Yellowish (Pitta) -->
  <g filter="url(#sh2)" transform="translate(148,48)">
    <ellipse cx="0" cy="30" rx="32" ry="40" fill="url(#s2)"/>
    <ellipse cx="0" cy="-5" rx="33" ry="18" fill="#A08040" opacity=".9"/>
    <ellipse cx="-11" cy="22" rx="7" ry="5" fill="white"/>
    <circle cx="-10" cy="22" r="3.5" fill="#6A4420"/>
    <circle cx="-9"  cy="21" r="1" fill="white"/>
    <ellipse cx="11" cy="22" rx="7" ry="5" fill="white"/>
    <circle cx="12"  cy="22" r="3.5" fill="#6A4420"/>
    <circle cx="13"  cy="21" r="1" fill="white"/>
    <ellipse cx="0"  cy="34" rx="4" ry="5" fill="#D4A070" opacity=".6"/>
    <path d="M-9 44 Q0 50 9 44" stroke="#C06050" stroke-width="2" fill="none" stroke-linecap="round"/>
    <!-- slight yellow overlay -->
    <ellipse cx="0" cy="30" rx="30" ry="38" fill="#FFE080" opacity=".08"/>
    <ellipse cx="-8" cy="10" rx="6" ry="4" fill="white" opacity=".2"/>
  </g>
  <text x="148" y="165" text-anchor="middle" fill="#9E2A0A" font-size="10" font-weight="bold" font-family="Arial">Fair-Yellowish</text>
  <text x="148" y="176" text-anchor="middle" fill="#9E2A0A" font-size="8" font-family="Arial">Gaur-Pitanga</text>
  <text x="148" y="187" text-anchor="middle" fill="#888" font-size="8" font-family="Arial" font-style="italic">Pitta — Ushna</text>

  <!-- Face 3: Medium/Wheatish (neutral) -->
  <g filter="url(#sh2)" transform="translate(248,48)">
    <ellipse cx="0" cy="30" rx="32" ry="40" fill="url(#s3)"/>
    <ellipse cx="0" cy="-5" rx="33" ry="18" fill="#7A5020" opacity=".9"/>
    <ellipse cx="-11" cy="22" rx="7" ry="5" fill="white"/>
    <circle cx="-10" cy="22" r="3.5" fill="#3A2010"/>
    <circle cx="-9"  cy="21" r="1" fill="white"/>
    <ellipse cx="11" cy="22" rx="7" ry="5" fill="white"/>
    <circle cx="12"  cy="22" r="3.5" fill="#3A2010"/>
    <circle cx="13"  cy="21" r="1" fill="white"/>
    <ellipse cx="0"  cy="34" rx="4" ry="5" fill="#C09060" opacity=".6"/>
    <path d="M-9 44 Q0 50 9 44" stroke="#A05040" stroke-width="2" fill="none" stroke-linecap="round"/>
  </g>
  <text x="248" y="165" text-anchor="middle" fill="#555" font-size="10" font-weight="bold" font-family="Arial">Medium</text>
  <text x="248" y="176" text-anchor="middle" fill="#555" font-size="8" font-family="Arial">Wheatish</text>
  <text x="248" y="187" text-anchor="middle" fill="#888" font-size="8" font-family="Arial" font-style="italic">Mixed / Neutral</text>

  <!-- Face 4: Dusky/Olive (Vata) -->
  <g filter="url(#sh2)" transform="translate(348,48)">
    <ellipse cx="0" cy="30" rx="32" ry="40" fill="url(#s4)"/>
    <ellipse cx="0" cy="-5" rx="33" ry="18" fill="#4A2808" opacity=".9"/>
    <ellipse cx="-11" cy="22" rx="7" ry="5" fill="white" opacity=".9"/>
    <circle cx="-10" cy="22" r="3.5" fill="#1A0800"/>
    <circle cx="-9"  cy="21" r="1" fill="white"/>
    <ellipse cx="11" cy="22" rx="7" ry="5" fill="white" opacity=".9"/>
    <circle cx="12"  cy="22" r="3.5" fill="#1A0800"/>
    <circle cx="13"  cy="21" r="1" fill="white"/>
    <ellipse cx="0"  cy="34" rx="4" ry="5" fill="#906040" opacity=".6"/>
    <path d="M-9 44 Q0 50 9 44" stroke="#804030" stroke-width="2" fill="none" stroke-linecap="round"/>
  </g>
  <text x="348" y="165" text-anchor="middle" fill="#1A4F96" font-size="10" font-weight="bold" font-family="Arial">Dusky / Olive</text>
  <text x="348" y="176" text-anchor="middle" fill="#1A4F96" font-size="8" font-family="Arial">Dhusara</text>
  <text x="348" y="187" text-anchor="middle" fill="#888" font-size="8" font-family="Arial" font-style="italic">Vata — Ruksha</text>

  <!-- Face 5: Dark (Vata) -->
  <g filter="url(#sh2)" transform="translate(448,48)">
    <ellipse cx="0" cy="30" rx="32" ry="40" fill="url(#s5)"/>
    <ellipse cx="0" cy="-5" rx="33" ry="18" fill="#2A1000" opacity=".9"/>
    <ellipse cx="-11" cy="22" rx="7" ry="5" fill="white" opacity=".95"/>
    <circle cx="-10" cy="22" r="3.5" fill="#0A0400"/>
    <circle cx="-9"  cy="21" r="1" fill="white"/>
    <ellipse cx="11" cy="22" rx="7" ry="5" fill="white" opacity=".95"/>
    <circle cx="12"  cy="22" r="3.5" fill="#0A0400"/>
    <circle cx="13"  cy="21" r="1" fill="white"/>
    <ellipse cx="0"  cy="34" rx="4" ry="5" fill="#702810" opacity=".6"/>
    <path d="M-9 44 Q0 50 9 44" stroke="#C09080" stroke-width="2" fill="none" stroke-linecap="round"/>
  </g>
  <text x="448" y="165" text-anchor="middle" fill="#1A4F96" font-size="10" font-weight="bold" font-family="Arial">Dark</text>
  <text x="448" y="176" text-anchor="middle" fill="#1A4F96" font-size="8" font-family="Arial">Krishna</text>
  <text x="448" y="187" text-anchor="middle" fill="#888" font-size="8" font-family="Arial" font-style="italic">Vata — deep Ruksha</text>
  <text x="540" y="200" text-anchor="middle" fill="#999" font-size="8" font-family="Arial" font-style="italic">CS Vim 8/96-98</text>
</svg>""",

"skin_texture": """<svg viewBox="0 0 560 200" xmlns="http://www.w3.org/2000/svg"
  style="width:100%;max-width:560px;display:block;margin:auto;border-radius:12px">
  <defs>
    <linearGradient id="bg_st" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="#fdf8f0"/><stop offset="100%" stop-color="#f0e8d8"/>
    </linearGradient>
    <filter id="sh3"><feDropShadow dx="0" dy="2" stdDeviation="3" flood-opacity=".15"/></filter>
    <pattern id="dry_p" x="0" y="0" width="8" height="8" patternUnits="userSpaceOnUse">
      <line x1="0" y1="0" x2="8" y2="8" stroke="#C09070" stroke-width=".8" opacity=".5"/>
      <line x1="8" y1="0" x2="0" y2="8" stroke="#C09070" stroke-width=".4" opacity=".3"/>
    </pattern>
    <radialGradient id="oily_g" cx="40%" cy="35%" r="65%">
      <stop offset="0%" stop-color="#C8E8B0"/><stop offset="100%" stop-color="#74c476"/>
    </radialGradient>
    <radialGradient id="warm_g" cx="40%" cy="35%" r="65%">
      <stop offset="0%" stop-color="#FDB090"/><stop offset="100%" stop-color="#E05030"/>
    </radialGradient>
    <radialGradient id="norm_g" cx="40%" cy="35%" r="65%">
      <stop offset="0%" stop-color="#F5D5B0"/><stop offset="100%" stop-color="#D4A070"/>
    </radialGradient>
  </defs>
  <rect width="560" height="200" fill="url(#bg_st)" rx="12" stroke="#e8d5b0" stroke-width="1"/>
  <text x="280" y="18" text-anchor="middle" fill="#4a2008" font-size="12" font-weight="bold"
        font-family="Arial">Skin Texture Types — Tvak Pariksha</text>
  <text x="280" y="30" text-anchor="middle" fill="#888" font-size="9" font-family="Arial"
        font-style="italic">Snigdha · Ruksha · Ushna (CS Vim 8/96-98 | AH Sha 3/83-85)</text>

  <!-- Panel 1: Dry (Vata-Ruksha) -->
  <g filter="url(#sh3)">
    <rect x="18" y="40" width="120" height="110" rx="10" fill="#F0D8B8"/>
    <rect x="18" y="40" width="120" height="110" rx="10" fill="url(#dry_p)"/>
    <!-- crack lines -->
    <path d="M40 70 Q60 90 50 110" stroke="#A07040" stroke-width="1.5" fill="none" stroke-linecap="round"/>
    <path d="M70 60 Q80 85 75 115" stroke="#A07040" stroke-width="1.2" fill="none" stroke-linecap="round"/>
    <path d="M95 75 Q108 95 100 120" stroke="#A07040" stroke-width="1.3" fill="none" stroke-linecap="round"/>
    <path d="M120 65 Q128 88 118 108" stroke="#A07040" stroke-width="1" fill="none" stroke-linecap="round"/>
    <path d="M50 110 Q65 108 75 115" stroke="#A07040" stroke-width=".8" fill="none"/>
    <!-- label -->
    <rect x="18" y="40" width="120" height="22" rx="10" fill="#1A4F96" opacity=".85"/>
    <text x="78" y="55" text-anchor="middle" fill="white" font-size="10" font-weight="bold" font-family="Arial">Dry / Ruksha</text>
  </g>
  <text x="78" y="165" text-anchor="middle" fill="#1A4F96" font-size="9" font-weight="bold" font-family="Arial">Vata — Ruksha Guna</text>
  <text x="78" y="176" text-anchor="middle" fill="#555" font-size="8" font-family="Arial" font-style="italic">Sphutita Tvak</text>

  <!-- Panel 2: Oily (Kapha-Snigdha) -->
  <g filter="url(#sh3)">
    <rect x="158" y="40" width="120" height="110" rx="10" fill="url(#oily_g)"/>
    <!-- shine blobs -->
    <ellipse cx="195" cy="72" rx="14" ry="8" fill="white" opacity=".35"/>
    <ellipse cx="240" cy="90" rx="10" ry="6" fill="white" opacity=".3"/>
    <ellipse cx="210" cy="118" rx="12" ry="7" fill="white" opacity=".28"/>
    <ellipse cx="258" cy="68" rx="8" ry="5" fill="white" opacity=".25"/>
    <rect x="158" y="40" width="120" height="22" rx="10" fill="#0D5C30" opacity=".85"/>
    <text x="218" y="55" text-anchor="middle" fill="white" font-size="10" font-weight="bold" font-family="Arial">Oily / Snigdha</text>
  </g>
  <text x="218" y="165" text-anchor="middle" fill="#0D5C30" font-size="9" font-weight="bold" font-family="Arial">Kapha — Snigdha Guna</text>
  <text x="218" y="176" text-anchor="middle" fill="#555" font-size="8" font-family="Arial" font-style="italic">Snigdha · Shlakshna Tvak</text>

  <!-- Panel 3: Warm/Pitta -->
  <g filter="url(#sh3)">
    <rect x="298" y="40" width="120" height="110" rx="10" fill="url(#warm_g)" opacity=".8"/>
    <!-- pimples/freckles pattern -->
    <circle cx="322" cy="70" r="4" fill="#A03010" opacity=".7"/>
    <circle cx="345" cy="60" r="3" fill="#C05020" opacity=".6"/>
    <circle cx="368" cy="75" r="4.5" fill="#A03010" opacity=".65"/>
    <circle cx="390" cy="62" r="3" fill="#C04010" opacity=".55"/>
    <circle cx="330" cy="100" r="3.5" fill="#A03010" opacity=".6"/>
    <circle cx="358" cy="95" r="4" fill="#C04010" opacity=".65"/>
    <circle cx="385" cy="108" r="3" fill="#A03010" opacity=".55"/>
    <circle cx="310" cy="120" r="4" fill="#C05020" opacity=".6"/>
    <circle cx="400" cy="130" r="3.5" fill="#A03010" opacity=".6"/>
    <rect x="298" y="40" width="120" height="22" rx="10" fill="#9E2A0A" opacity=".85"/>
    <text x="358" y="55" text-anchor="middle" fill="white" font-size="10" font-weight="bold" font-family="Arial">Warm / Ushna</text>
  </g>
  <text x="358" y="165" text-anchor="middle" fill="#9E2A0A" font-size="9" font-weight="bold" font-family="Arial">Pitta — Ushna Guna</text>
  <text x="358" y="176" text-anchor="middle" fill="#555" font-size="8" font-family="Arial" font-style="italic">Pidaka · Vyanga</text>

  <!-- Panel 4: Normal -->
  <g filter="url(#sh3)">
    <rect x="438" y="40" width="104" height="110" rx="10" fill="url(#norm_g)"/>
    <!-- smooth texture lines -->
    <path d="M455 70 Q490 72 528 70" stroke="#C09060" stroke-width=".8" fill="none" opacity=".4"/>
    <path d="M452 90 Q488 93 530 90" stroke="#C09060" stroke-width=".8" fill="none" opacity=".4"/>
    <path d="M455 110 Q490 113 528 110" stroke="#C09060" stroke-width=".8" fill="none" opacity=".4"/>
    <rect x="438" y="40" width="104" height="22" rx="10" fill="#555" opacity=".8"/>
    <text x="490" y="55" text-anchor="middle" fill="white" font-size="10" font-weight="bold" font-family="Arial">Normal</text>
  </g>
  <text x="490" y="165" text-anchor="middle" fill="#555" font-size="9" font-weight="bold" font-family="Arial">Balanced / Sama</text>
  <text x="490" y="176" text-anchor="middle" fill="#888" font-size="8" font-family="Arial" font-style="italic">Shlakshna Tvak</text>
</svg>""",

"hair_types": """<svg viewBox="0 0 520 200" xmlns="http://www.w3.org/2000/svg"
  style="width:100%;max-width:520px;display:block;margin:auto;border-radius:12px">
  <defs>
    <linearGradient id="bg_ht" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="#fdf8f0"/><stop offset="100%" stop-color="#f0e8d8"/>
    </linearGradient>
    <linearGradient id="hair_k" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="#4A3820"/><stop offset="100%" stop-color="#2A1800"/>
    </linearGradient>
    <linearGradient id="hair_p" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="#9B6E3A"/><stop offset="100%" stop-color="#704820"/>
    </linearGradient>
    <linearGradient id="hair_v" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="#888"/><stop offset="100%" stop-color="#555"/>
    </linearGradient>
    <filter id="sh4"><feDropShadow dx="0" dy="2" stdDeviation="2" flood-opacity=".15"/></filter>
  </defs>
  <rect width="520" height="200" fill="url(#bg_ht)" rx="12" stroke="#e8d5b0" stroke-width="1"/>
  <text x="260" y="18" text-anchor="middle" fill="#4a2008" font-size="12" font-weight="bold"
        font-family="Arial">Hair Types — Kesha Prakriti Reference</text>
  <text x="260" y="30" text-anchor="middle" fill="#888" font-size="9" font-family="Arial"
        font-style="italic">Ghana·Snigdha (Kapha) · Kapila·Mridu (Pitta) · Ruksha·Parusha (Vata)</text>

  <!-- Hair 1: Straight Dense (Kapha) -->
  <g filter="url(#sh4)">
    <rect x="20" y="42" width="90" height="105" rx="8" fill="#F8F0E4" stroke="#E0C898" stroke-width="1"/>
    <rect x="20" y="42" width="90" height="20" rx="8" fill="#0D5C30" opacity=".85"/>
    <text x="65" y="56" text-anchor="middle" fill="white" font-size="9" font-weight="bold" font-family="Arial">Straight·Dense</text>
    <!-- Hair strands — thick, straight, dark, lustrous -->
    <line x1="34" y1="68" x2="34" y2="140" stroke="url(#hair_k)" stroke-width="4" stroke-linecap="round"/>
    <line x1="42" y1="66" x2="42" y2="142" stroke="#3A2810" stroke-width="3.5" stroke-linecap="round"/>
    <line x1="50" y1="66" x2="50" y2="142" stroke="url(#hair_k)" stroke-width="4" stroke-linecap="round"/>
    <line x1="58" y1="65" x2="58" y2="142" stroke="#3A2810" stroke-width="3.5" stroke-linecap="round"/>
    <line x1="66" y1="65" x2="66" y2="142" stroke="url(#hair_k)" stroke-width="4" stroke-linecap="round"/>
    <line x1="74" y1="66" x2="74" y2="142" stroke="#3A2810" stroke-width="3.5" stroke-linecap="round"/>
    <line x1="82" y1="67" x2="82" y2="142" stroke="url(#hair_k)" stroke-width="4" stroke-linecap="round"/>
    <line x1="90" y1="68" x2="90" y2="141" stroke="#3A2810" stroke-width="3" stroke-linecap="round"/>
    <!-- sheen highlights -->
    <line x1="38" y1="70" x2="38" y2="95" stroke="white" stroke-width="1.2" opacity=".4"/>
    <line x1="62" y1="68" x2="62" y2="90" stroke="white" stroke-width="1" opacity=".35"/>
  </g>
  <text x="65" y="160" text-anchor="middle" fill="#0D5C30" font-size="9" font-weight="bold" font-family="Arial">Kapha Prakriti</text>
  <text x="65" y="171" text-anchor="middle" fill="#555" font-size="8" font-family="Arial" font-style="italic">Ghana · Snigdha</text>
  <text x="65" y="182" text-anchor="middle" fill="#888" font-size="7.5" font-family="Arial">Thick · Oily · Lustrous</text>

  <!-- Hair 2: Soft Reddish (Pitta) -->
  <g filter="url(#sh4)">
    <rect x="130" y="42" width="90" height="105" rx="8" fill="#F8F0E4" stroke="#E0C898" stroke-width="1"/>
    <rect x="130" y="42" width="90" height="20" rx="8" fill="#9E2A0A" opacity=".85"/>
    <text x="175" y="56" text-anchor="middle" fill="white" font-size="9" font-weight="bold" font-family="Arial">Soft · Reddish</text>
    <!-- soft fine reddish-brown strands — slight wave -->
    <path d="M144 68 Q145 95 144 122 Q143 138 144 145" stroke="url(#hair_p)" stroke-width="2.5" fill="none" stroke-linecap="round"/>
    <path d="M152 67 Q154 94 152 120 Q151 136 152 145" stroke="#8B5A2B" stroke-width="2" fill="none" stroke-linecap="round"/>
    <path d="M160 66 Q162 93 160 120 Q159 137 160 145" stroke="url(#hair_p)" stroke-width="2.5" fill="none" stroke-linecap="round"/>
    <path d="M168 67 Q170 94 168 121 Q167 137 168 145" stroke="#9B6E3A" stroke-width="2" fill="none" stroke-linecap="round"/>
    <path d="M176 66 Q178 93 176 121 Q175 138 176 145" stroke="url(#hair_p)" stroke-width="2.5" fill="none" stroke-linecap="round"/>
    <path d="M184 67 Q186 94 184 120 Q183 137 184 145" stroke="#8B5A2B" stroke-width="2" fill="none" stroke-linecap="round"/>
    <path d="M192 68 Q194 95 192 122 Q191 138 192 145" stroke="url(#hair_p)" stroke-width="2.3" fill="none" stroke-linecap="round"/>
    <path d="M200 68 Q202 95 200 123 Q199 138 200 145" stroke="#9B6E3A" stroke-width="2" fill="none" stroke-linecap="round"/>
  </g>
  <text x="175" y="160" text-anchor="middle" fill="#9E2A0A" font-size="9" font-weight="bold" font-family="Arial">Pitta Prakriti</text>
  <text x="175" y="171" text-anchor="middle" fill="#555" font-size="8" font-family="Arial" font-style="italic">Mridu · Kapila</text>
  <text x="175" y="182" text-anchor="middle" fill="#888" font-size="7.5" font-family="Arial">Soft · Fine · Reddish</text>

  <!-- Hair 3: Dry Frizzy (Vata) -->
  <g filter="url(#sh4)">
    <rect x="240" y="42" width="90" height="105" rx="8" fill="#F8F0E4" stroke="#E0C898" stroke-width="1"/>
    <rect x="240" y="42" width="90" height="20" rx="8" fill="#1A4F96" opacity=".85"/>
    <text x="285" y="56" text-anchor="middle" fill="white" font-size="9" font-weight="bold" font-family="Arial">Dry · Frizzy</text>
    <!-- erratic frizzy strands -->
    <path d="M254 68 Q248 80 256 92 Q248 104 255 116 Q249 128 256 145" stroke="url(#hair_v)" stroke-width="2" fill="none" stroke-linecap="round"/>
    <path d="M262 67 Q270 79 262 93 Q270 107 263 120 Q270 133 262 145" stroke="#777" stroke-width="1.8" fill="none" stroke-linecap="round"/>
    <path d="M270 66 Q263 80 272 94 Q264 108 272 120 Q264 134 271 145" stroke="url(#hair_v)" stroke-width="2" fill="none" stroke-linecap="round"/>
    <path d="M280 67 Q288 81 279 95 Q288 109 279 121 Q287 135 279 145" stroke="#777" stroke-width="1.8" fill="none" stroke-linecap="round"/>
    <path d="M290 66 Q282 82 291 96 Q282 110 291 122 Q282 136 290 145" stroke="url(#hair_v)" stroke-width="2" fill="none" stroke-linecap="round"/>
    <path d="M300 68 Q308 82 300 96 Q308 110 300 122 Q308 135 300 145" stroke="#777" stroke-width="1.8" fill="none" stroke-linecap="round"/>
    <path d="M310 68 Q302 82 311 96 Q303 110 311 122 Q303 136 311 145" stroke="url(#hair_v)" stroke-width="1.8" fill="none" stroke-linecap="round"/>
    <!-- split end marks -->
    <line x1="254" y1="140" x2="250" y2="148" stroke="#666" stroke-width="1"/>
    <line x1="254" y1="140" x2="258" y2="148" stroke="#666" stroke-width="1"/>
    <line x1="280" y1="140" x2="276" y2="148" stroke="#666" stroke-width="1"/>
    <line x1="280" y1="140" x2="284" y2="148" stroke="#666" stroke-width="1"/>
  </g>
  <text x="285" y="160" text-anchor="middle" fill="#1A4F96" font-size="9" font-weight="bold" font-family="Arial">Vata Prakriti</text>
  <text x="285" y="171" text-anchor="middle" fill="#555" font-size="8" font-family="Arial" font-style="italic">Ruksha · Parusha</text>
  <text x="285" y="182" text-anchor="middle" fill="#888" font-size="7.5" font-family="Arial">Dry · Rough · Split ends</text>

  <!-- Hair 4: Scanty Thin (Vata-Pitta) -->
  <g filter="url(#sh4)">
    <rect x="350" y="42" width="150" height="105" rx="8" fill="#F8F0E4" stroke="#E0C898" stroke-width="1"/>
    <rect x="350" y="42" width="150" height="20" rx="8" fill="#7B3990" opacity=".85"/>
    <text x="425" y="56" text-anchor="middle" fill="white" font-size="9" font-weight="bold" font-family="Arial">Premature Grey · Scanty</text>
    <!-- sparse strands with grey -->
    <line x1="368" y1="68" x2="366" y2="145" stroke="#B0A098" stroke-width="2.5" stroke-linecap="round"/>
    <line x1="385" y1="67" x2="384" y2="145" stroke="#888" stroke-width="2" stroke-linecap="round"/>
    <line x1="400" y1="68" x2="402" y2="144" stroke="#B0A098" stroke-width="2.2" stroke-linecap="round"/>
    <line x1="418" y1="68" x2="416" y2="145" stroke="#777" stroke-width="1.8" stroke-linecap="round"/>
    <line x1="435" y1="67" x2="436" y2="144" stroke="#B0A098" stroke-width="2" stroke-linecap="round"/>
    <line x1="452" y1="68" x2="450" y2="145" stroke="#888" stroke-width="1.8" stroke-linecap="round"/>
    <line x1="468" y1="68" x2="470" y2="144" stroke="#B0A098" stroke-width="2" stroke-linecap="round"/>
    <!-- wide gaps = scanty -->
    <text x="425" y="130" text-anchor="middle" fill="#AAA" font-size="8" font-family="Arial" font-style="italic">— sparse —</text>
  </g>
  <text x="425" y="160" text-anchor="middle" fill="#7B3990" font-size="9" font-weight="bold" font-family="Arial">Pitta · Vata Mix</text>
  <text x="425" y="171" text-anchor="middle" fill="#555" font-size="8" font-family="Arial" font-style="italic">Akalapalita · Alpakesha</text>
  <text x="425" y="182" text-anchor="middle" fill="#888" font-size="7.5" font-family="Arial">Premature grey · Scanty</text>
</svg>""",

"veins_tendons": """<svg viewBox="0 0 220 200" xmlns="http://www.w3.org/2000/svg"
  style="width:100%;max-width:220px;display:block;margin:auto;border-radius:12px">
  <defs>
    <linearGradient id="bg_vt" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="#fdf8f0"/><stop offset="100%" stop-color="#f0e8d8"/>
    </linearGradient>
    <radialGradient id="skin_vt" cx="45%" cy="40%" r="60%">
      <stop offset="0%" stop-color="#F5CBA7"/><stop offset="100%" stop-color="#D4A070"/>
    </radialGradient>
    <filter id="sh5"><feDropShadow dx="1" dy="2" stdDeviation="3" flood-opacity=".2"/></filter>
  </defs>
  <rect width="220" height="200" fill="url(#bg_vt)" rx="12" stroke="#e8d5b0" stroke-width="1"/>
  <rect x="0" y="0" width="220" height="24" rx="12" fill="#1A4F96"/>
  <rect x="12" y="24" width="196" height="0" fill="none"/>
  <text x="110" y="16" text-anchor="middle" fill="white" font-size="10" font-weight="bold" font-family="Arial">Prominent Veins · Tendons</text>
  <text x="110" y="190" text-anchor="middle" fill="#1A4F96" font-size="8.5" font-family="Arial" font-style="italic">Vata — Bahu·Sira·Snayu (CS 8/98)</text>

  <!-- Realistic hand/forearm with visible veins -->
  <!-- Forearm -->
  <rect x="75" y="30" width="70" height="100" rx="20" fill="url(#skin_vt)" filter="url(#sh5)"/>
  <!-- Hand -->
  <rect x="68" y="118" width="84" height="55" rx="16" fill="url(#skin_vt)"/>
  <!-- Fingers suggested -->
  <rect x="72" y="148" width="14" height="22" rx="7" fill="#E0B888"/>
  <rect x="90" y="144" width="14" height="26" rx="7" fill="#E0B888"/>
  <rect x="108" y="143" width="14" height="27" rx="7" fill="#E0B888"/>
  <rect x="126" y="146" width="13" height="24" rx="6" fill="#E0B888"/>

  <!-- Prominent raised veins — thick blue-green lines -->
  <path d="M110 32 Q108 55 110 80 Q112 110 108 135 Q104 148 100 158"
        stroke="#3060B0" stroke-width="4" fill="none" stroke-linecap="round" opacity=".75"/>
  <path d="M118 34 Q116 58 118 85 Q120 115 116 138 Q112 150 109 160"
        stroke="#4070C0" stroke-width="3" fill="none" stroke-linecap="round" opacity=".65"/>
  <path d="M102 35 Q100 60 102 88 Q104 118 100 140 Q96 152 92 162"
        stroke="#3060B0" stroke-width="3.5" fill="none" stroke-linecap="round" opacity=".7"/>
  <!-- Branching veins on hand -->
  <path d="M108 135 Q104 142 96 152 Q90 158 82 162"
        stroke="#3060B0" stroke-width="2.5" fill="none" stroke-linecap="round" opacity=".6"/>
  <path d="M110 138 Q112 146 114 155"
        stroke="#3060B0" stroke-width="2" fill="none" stroke-linecap="round" opacity=".55"/>
  <path d="M114 140 Q118 148 122 158"
        stroke="#4070C0" stroke-width="2" fill="none" stroke-linecap="round" opacity=".55"/>
  <!-- Tendon ridges on back of hand -->
  <path d="M80 130 Q85 125 90 132 Q95 128 100 135"
        stroke="#B08050" stroke-width="1.5" fill="none" opacity=".4"/>

  <!-- Annotation -->
  <line x1="132" y1="70" x2="160" y2="65" stroke="#1A4F96" stroke-width="1" stroke-dasharray="3 2"/>
  <text x="163" y="60" fill="#1A4F96" font-size="8" font-family="Arial">Bahu Sira</text>
  <text x="163" y="70" fill="#1A4F96" font-size="8" font-family="Arial">(veins)</text>
  <line x1="138" y1="130" x2="162" y2="130" stroke="#B08050" stroke-width="1" stroke-dasharray="3 2"/>
  <text x="163" y="125" fill="#8B5020" font-size="8" font-family="Arial">Snayu</text>
  <text x="163" y="135" fill="#8B5020" font-size="8" font-family="Arial">(tendons)</text>
</svg>""",

"lax_muscle": """<svg viewBox="0 0 220 200" xmlns="http://www.w3.org/2000/svg"
  style="width:100%;max-width:220px;display:block;margin:auto;border-radius:12px">
  <defs>
    <linearGradient id="bg_lm" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="#fdf8f0"/><stop offset="100%" stop-color="#f0e8d8"/>
    </linearGradient>
    <radialGradient id="skin_lm" cx="40%" cy="35%" r="65%">
      <stop offset="0%" stop-color="#F5CBA7"/><stop offset="100%" stop-color="#C89060"/>
    </radialGradient>
    <filter id="sh6"><feDropShadow dx="1" dy="2" stdDeviation="3" flood-opacity=".2"/></filter>
  </defs>
  <rect width="220" height="200" fill="url(#bg_lm)" rx="12" stroke="#e8d5b0" stroke-width="1"/>
  <rect x="0" y="0" width="220" height="24" rx="12" fill="#9E2A0A"/>
  <text x="110" y="16" text-anchor="middle" fill="white" font-size="10" font-weight="bold" font-family="Arial">Lax Muscles · Shithila Mamsa</text>
  <text x="110" y="190" text-anchor="middle" fill="#9E2A0A" font-size="8.5" font-family="Arial" font-style="italic">Pitta — Drava·Shithila Guna (CS 8/97)</text>

  <!-- Upper arm showing lax/soft tissue -->
  <!-- Shoulder area -->
  <ellipse cx="110" cy="55" rx="45" ry="22" fill="url(#skin_lm)" filter="url(#sh6)"/>
  <!-- Upper arm — soft drooping shape -->
  <path d="M68 52 Q55 75 58 110 Q62 135 75 150 Q90 162 110 164 Q130 162 145 150 Q158 135 162 110 Q165 75 152 52"
        fill="url(#skin_lm)" filter="url(#sh6)"/>
  <!-- Loose tissue hanging on sides (lax indicator) -->
  <path d="M68 52 Q52 68 50 95 Q48 115 58 110"
        fill="#E8B888" stroke="none" opacity=".7"/>
  <path d="M152 52 Q168 68 170 95 Q172 115 162 110"
        fill="#E8B888" stroke="none" opacity=".7"/>
  <!-- Soft tissue fold lines -->
  <path d="M62 80 Q56 95 60 108" stroke="#C09060" stroke-width="1.5" fill="none" opacity=".6"/>
  <path d="M158 80 Q164 95 160 108" stroke="#C09060" stroke-width="1.5" fill="none" opacity=".6"/>
  <!-- Muscle definition absent — faint soft lines only -->
  <path d="M82 100 Q110 95 138 100" stroke="#D0A878" stroke-width="1" fill="none" opacity=".4" stroke-dasharray="4 3"/>
  <!-- Pinch test indicator -->
  <path d="M85 75 Q80 80 82 86 Q80 80 88 76 Z" fill="#C08040" opacity=".5"/>
  <line x1="78" y1="78" x2="68" y2="68" stroke="#9E2A0A" stroke-width="1" stroke-dasharray="3 2"/>
  <text x="62" y="65" text-anchor="middle" fill="#9E2A0A" font-size="8" font-family="Arial">Soft /</text>
  <text x="62" y="74" text-anchor="middle" fill="#9E2A0A" font-size="8" font-family="Arial">Lax tissue</text>
</svg>""",

"well_built": """<svg viewBox="0 0 220 200" xmlns="http://www.w3.org/2000/svg"
  style="width:100%;max-width:220px;display:block;margin:auto;border-radius:12px">
  <defs>
    <linearGradient id="bg_wb" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="#fdf8f0"/><stop offset="100%" stop-color="#f0e8d8"/>
    </linearGradient>
    <radialGradient id="skin_wb" cx="40%" cy="30%" r="65%">
      <stop offset="0%" stop-color="#D4A070"/><stop offset="100%" stop-color="#A07040"/>
    </radialGradient>
    <radialGradient id="muscle_wb" cx="38%" cy="28%" r="60%">
      <stop offset="0%" stop-color="#C8E8B0"/><stop offset="100%" stop-color="#0D5C30"/>
    </radialGradient>
    <filter id="sh7"><feDropShadow dx="1" dy="2" stdDeviation="3" flood-opacity=".2"/></filter>
  </defs>
  <rect width="220" height="200" fill="url(#bg_wb)" rx="12" stroke="#e8d5b0" stroke-width="1"/>
  <rect x="0" y="0" width="220" height="24" rx="12" fill="#0D5C30"/>
  <text x="110" y="16" text-anchor="middle" fill="white" font-size="10" font-weight="bold" font-family="Arial">Well-Built Muscles · Sama Mamsa</text>
  <text x="110" y="190" text-anchor="middle" fill="#0D5C30" font-size="8.5" font-family="Arial" font-style="italic">Kapha — Sara·Sthira Guna (CS 8/96)</text>

  <!-- Flexed arm showing defined bicep -->
  <!-- Upper arm base -->
  <path d="M62 52 Q50 70 52 105 Q58 140 75 155 Q92 165 110 165 Q128 165 145 155 Q162 140 168 105 Q170 70 158 52"
        fill="url(#skin_wb)" filter="url(#sh7)"/>
  <!-- Bicep peak — defined, rounded, compact -->
  <ellipse cx="88" cy="88" rx="32" ry="38" fill="url(#muscle_wb)" opacity=".85"/>
  <ellipse cx="132" cy="88" rx="32" ry="38" fill="url(#muscle_wb)" opacity=".85"/>
  <!-- Muscle separation groove -->
  <path d="M110 58 Q110 90 110 130" stroke="#0D5C30" stroke-width="2" fill="none" opacity=".5"/>
  <!-- Sheen highlight on bicep peak -->
  <ellipse cx="82" cy="74" rx="12" ry="8" fill="white" opacity=".3"/>
  <ellipse cx="126" cy="74" rx="12" ry="8" fill="white" opacity=".25"/>
  <!-- Definition lines -->
  <path d="M70 105 Q90 115 110 112 Q130 115 150 105" stroke="#0A4A28" stroke-width="1.5" fill="none" opacity=".5"/>
  <path d="M72 118 Q92 126 110 124 Q128 126 148 118" stroke="#0A4A28" stroke-width="1" fill="none" opacity=".4"/>
  <!-- Annotation -->
  <line x1="58" y1="85" x2="38" y2="80" stroke="#0D5C30" stroke-width="1" stroke-dasharray="3 2"/>
  <text x="35" y="72" text-anchor="middle" fill="#0D5C30" font-size="8" font-family="Arial">Compact</text>
  <text x="35" y="82" text-anchor="middle" fill="#0D5C30" font-size="8" font-family="Arial">Defined</text>
</svg>""",

"calf_muscle": """<svg viewBox="0 0 220 210" xmlns="http://www.w3.org/2000/svg"
  style="width:100%;max-width:220px;display:block;margin:auto;border-radius:12px">
  <defs>
    <linearGradient id="bg_cm" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="#fdf8f0"/><stop offset="100%" stop-color="#f0e8d8"/>
    </linearGradient>
    <radialGradient id="skin_cm" cx="42%" cy="30%" r="62%">
      <stop offset="0%" stop-color="#D4A070"/><stop offset="100%" stop-color="#A07040"/>
    </radialGradient>
    <radialGradient id="calf_g" cx="38%" cy="25%" r="62%">
      <stop offset="0%" stop-color="#A0D080"/><stop offset="100%" stop-color="#0D5C30"/>
    </radialGradient>
    <filter id="sh8"><feDropShadow dx="1" dy="2" stdDeviation="3" flood-opacity=".2"/></filter>
  </defs>
  <rect width="220" height="210" fill="url(#bg_cm)" rx="12" stroke="#e8d5b0" stroke-width="1"/>
  <rect x="0" y="0" width="220" height="24" rx="12" fill="#0D5C30"/>
  <text x="110" y="16" text-anchor="middle" fill="white" font-size="10" font-weight="bold" font-family="Arial">Charu Jangha · Calf Muscles</text>
  <text x="110" y="200" text-anchor="middle" fill="#0D5C30" font-size="8.5" font-family="Arial" font-style="italic">Kapha — Sara Guna (CS Vim 8/96; SS Sha 4/74)</text>

  <!-- Lower leg with prominent defined calf -->
  <!-- Shin -->
  <rect x="84" y="28" width="52" height="85" rx="16" fill="url(#skin_cm)" filter="url(#sh8)"/>
  <!-- Calf bulge — prominent, well-formed -->
  <ellipse cx="75" cy="80" rx="28" ry="42" fill="url(#calf_g)" filter="url(#sh8)" opacity=".88"/>
  <ellipse cx="145" cy="80" rx="28" ry="42" fill="url(#calf_g)" filter="url(#sh8)" opacity=".88"/>
  <!-- Sheen highlight -->
  <ellipse cx="66" cy="62" rx="10" ry="7" fill="white" opacity=".3"/>
  <ellipse cx="136" cy="62" rx="10" ry="7" fill="white" opacity=".25"/>
  <!-- Separation groove -->
  <path d="M110 34 Q110 80 110 112" stroke="#0A4828" stroke-width="2" fill="none" opacity=".4"/>
  <!-- Ankle tapering -->
  <rect x="90" y="112" width="40" height="30" rx="10" fill="url(#skin_cm)"/>
  <!-- Foot suggestion -->
  <ellipse cx="110" cy="155" rx="38" ry="16" fill="url(#skin_cm)"/>
  <!-- Annotation -->
  <line x1="45" y1="80" x2="30" y2="75" stroke="#0D5C30" stroke-width="1" stroke-dasharray="3 2"/>
  <text x="28" y="66" text-anchor="end" fill="#0D5C30" font-size="8" font-family="Arial">Well-formed</text>
  <text x="28" y="76" text-anchor="end" fill="#0D5C30" font-size="8" font-family="Arial">Charu</text>
  <text x="28" y="86" text-anchor="end" fill="#0D5C30" font-size="8" font-family="Arial">Jangha</text>
</svg>""",

"freckles": """<svg viewBox="0 0 220 210" xmlns="http://www.w3.org/2000/svg"
  style="width:100%;max-width:220px;display:block;margin:auto;border-radius:12px">
  <defs>
    <linearGradient id="bg_fr" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="#fdf8f0"/><stop offset="100%" stop-color="#f0e8d8"/>
    </linearGradient>
    <radialGradient id="face_fr" cx="45%" cy="35%" r="58%">
      <stop offset="0%" stop-color="#F5D5B0"/><stop offset="100%" stop-color="#D4A070"/>
    </radialGradient>
    <filter id="sh9"><feDropShadow dx="1" dy="2" stdDeviation="3" flood-opacity=".2"/></filter>
  </defs>
  <rect width="220" height="210" fill="url(#bg_fr)" rx="12" stroke="#e8d5b0" stroke-width="1"/>
  <rect x="0" y="0" width="220" height="24" rx="12" fill="#9E2A0A"/>
  <text x="110" y="16" text-anchor="middle" fill="white" font-size="10" font-weight="bold" font-family="Arial">Freckles · Vyanga (Pitta)</text>
  <text x="110" y="200" text-anchor="middle" fill="#9E2A0A" font-size="8.5" font-family="Arial" font-style="italic">Pitta — Ushna·Teekshna Guna (CS 8/97)</text>

  <!-- Face with realistic freckle distribution -->
  <!-- Face oval -->
  <ellipse cx="110" cy="110" rx="72" ry="82" fill="url(#face_fr)" filter="url(#sh9)"/>
  <!-- Hair -->
  <ellipse cx="110" cy="36" rx="74" ry="30" fill="#8B6030" opacity=".85"/>
  <!-- Eyes -->
  <ellipse cx="82" cy="92" rx="14" ry="10" fill="white"/>
  <circle cx="85"  cy="92" r="6" fill="#5A3010"/>
  <circle cx="87"  cy="90" r="2" fill="white"/>
  <ellipse cx="138" cy="92" rx="14" ry="10" fill="white"/>
  <circle cx="141" cy="92" r="6" fill="#5A3010"/>
  <circle cx="143" cy="90" r="2" fill="white"/>
  <!-- Eyebrows -->
  <path d="M70 80 Q82 76 94 79" stroke="#7A5020" stroke-width="2" fill="none" stroke-linecap="round"/>
  <path d="M126 79 Q138 76 150 80" stroke="#7A5020" stroke-width="2" fill="none" stroke-linecap="round"/>
  <!-- Nose -->
  <path d="M104 102 Q108 118 112 118 Q116 118 116 102" stroke="#C09060" stroke-width="1.5" fill="none" opacity=".6"/>
  <!-- Mouth -->
  <path d="M92 140 Q110 150 128 140" stroke="#C07050" stroke-width="2" fill="none" stroke-linecap="round"/>

  <!-- Freckle clusters — realistic irregular dots -->
  <!-- Left cheek cluster -->
  <circle cx="66" cy="108" r="3.5" fill="#B06828" opacity=".7"/>
  <circle cx="74" cy="104" r="2.8" fill="#C07830" opacity=".65"/>
  <circle cx="70" cy="116" r="3" fill="#A05818" opacity=".7"/>
  <circle cx="61" cy="118" r="2.5" fill="#B06828" opacity=".6"/>
  <circle cx="78" cy="112" r="2" fill="#C07830" opacity=".55"/>
  <circle cx="65" cy="126" r="2.5" fill="#A05818" opacity=".6"/>
  <!-- Right cheek cluster -->
  <circle cx="154" cy="108" r="3.5" fill="#B06828" opacity=".7"/>
  <circle cx="146" cy="104" r="2.8" fill="#C07830" opacity=".65"/>
  <circle cx="150" cy="116" r="3" fill="#A05818" opacity=".7"/>
  <circle cx="159" cy="118" r="2.5" fill="#B06828" opacity=".6"/>
  <circle cx="142" cy="112" r="2" fill="#C07830" opacity=".55"/>
  <circle cx="155" cy="126" r="2.5" fill="#A05818" opacity=".6"/>
  <!-- Nose bridge freckles -->
  <circle cx="104" cy="84" r="2" fill="#B06828" opacity=".55"/>
  <circle cx="116" cy="84" r="2" fill="#C07830" opacity=".5"/>
  <circle cx="110" cy="80" r="1.8" fill="#A05818" opacity=".5"/>
  <!-- Forehead scattered -->
  <circle cx="90"  cy="64" r="2" fill="#B06828" opacity=".45"/>
  <circle cx="130" cy="62" r="1.8" fill="#C07830" opacity=".4"/>
  <circle cx="110" cy="60" r="1.5" fill="#A05818" opacity=".4"/>

  <!-- Annotation -->
  <line x1="158" y1="112" x2="178" y2="105" stroke="#9E2A0A" stroke-width="1" stroke-dasharray="3 2"/>
  <text x="182" y="100" fill="#9E2A0A" font-size="8" font-family="Arial">Vyanga</text>
  <text x="182" y="110" fill="#9E2A0A" font-size="8" font-family="Arial">(freckles)</text>
</svg>""",

"broad_forehead": """<svg viewBox="0 0 220 210" xmlns="http://www.w3.org/2000/svg"
  style="width:100%;max-width:220px;display:block;margin:auto;border-radius:12px">
  <defs>
    <linearGradient id="bg_bf" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="#fdf8f0"/><stop offset="100%" stop-color="#f0e8d8"/>
    </linearGradient>
    <radialGradient id="face_bf" cx="45%" cy="38%" r="58%">
      <stop offset="0%" stop-color="#E8D0A8"/><stop offset="100%" stop-color="#C4A070"/>
    </radialGradient>
    <filter id="sh10"><feDropShadow dx="1" dy="2" stdDeviation="3" flood-opacity=".2"/></filter>
  </defs>
  <rect width="220" height="210" fill="url(#bg_bf)" rx="12" stroke="#e8d5b0" stroke-width="1"/>
  <rect x="0" y="0" width="220" height="24" rx="12" fill="#0D5C30"/>
  <text x="110" y="16" text-anchor="middle" fill="white" font-size="10" font-weight="bold" font-family="Arial">Broad Forehead · Maha-Lalata</text>
  <text x="110" y="200" text-anchor="middle" fill="#0D5C30" font-size="8.5" font-family="Arial" font-style="italic">Kapha — Sandra·Guru Guna (AH Sha 3/97)</text>

  <!-- Face with prominently broad forehead -->
  <!-- Broad upper skull -->
  <ellipse cx="110" cy="80" rx="82" ry="60" fill="#C4A888" filter="url(#sh10)"/>
  <!-- Face lower -->
  <ellipse cx="110" cy="125" rx="62" ry="68" fill="url(#face_bf)" filter="url(#sh10)"/>
  <!-- Hair — sits high, exposing broad forehead -->
  <ellipse cx="110" cy="32" rx="84" ry="24" fill="#2A1800" opacity=".9"/>
  <!-- Hairline sits high showing broad forehead area -->
  <path d="M28 62 Q55 48 110 44 Q165 48 192 62" stroke="#2A1800" stroke-width="3" fill="none"/>

  <!-- Broad forehead area highlighted with subtle warm glow -->
  <ellipse cx="110" cy="75" rx="74" ry="28" fill="#E8C890" opacity=".4"/>

  <!-- Eyes — lower on face -->
  <ellipse cx="82"  cy="112" rx="13" ry="9" fill="white"/>
  <circle cx="85"   cy="112" r="5.5" fill="#3A2010"/>
  <circle cx="87"   cy="110" r="1.8" fill="white"/>
  <ellipse cx="138" cy="112" rx="13" ry="9" fill="white"/>
  <circle cx="141"  cy="112" r="5.5" fill="#3A2010"/>
  <circle cx="143"  cy="110" r="1.8" fill="white"/>
  <!-- Dense lashes (Kapha Pakshmal) -->
  <path d="M70 106 Q76 100 94 106" stroke="#1A0800" stroke-width="2" fill="none"/>
  <path d="M126 106 Q142 100 152 106" stroke="#1A0800" stroke-width="2" fill="none"/>

  <!-- Nose -->
  <ellipse cx="110" cy="132" rx="10" ry="12" fill="#C4986A" opacity=".5"/>
  <!-- Mouth -->
  <path d="M92 156 Q110 168 128 156" stroke="#A06040" stroke-width="2" fill="none" stroke-linecap="round"/>

  <!-- Width annotation arrows -->
  <line x1="28"  y1="68" x2="28"  y2="82" stroke="#0D5C30" stroke-width="1.5"/>
  <line x1="192" y1="68" x2="192" y2="82" stroke="#0D5C30" stroke-width="1.5"/>
  <line x1="28"  y1="75" x2="192" y2="75" stroke="#0D5C30" stroke-width="1.5" marker-start="url(#arr)" marker-end="url(#arr)"/>
  <text x="110" y="72" text-anchor="middle" fill="#0D5C30" font-size="9" font-weight="bold" font-family="Arial">Maha-Lalata</text>
  <!-- bracket lines -->
  <line x1="28"  y1="68" x2="40"  y2="68" stroke="#0D5C30" stroke-width="1.2"/>
  <line x1="180" y1="68" x2="192" y2="68" stroke="#0D5C30" stroke-width="1.2"/>
  <line x1="28"  y1="82" x2="40"  y2="82" stroke="#0D5C30" stroke-width="1.2"/>
  <line x1="180" y1="82" x2="192" y2="82" stroke="#0D5C30" stroke-width="1.2"/>
</svg>""",

"excess_teeth": """<svg viewBox="0 0 220 200" xmlns="http://www.w3.org/2000/svg"
  style="width:100%;max-width:220px;display:block;margin:auto;border-radius:12px">
  <defs>
    <linearGradient id="bg_et" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="#fdf8f0"/><stop offset="100%" stop-color="#f0e8d8"/>
    </linearGradient>
    <filter id="sh11"><feDropShadow dx="1" dy="2" stdDeviation="2" flood-opacity=".15"/></filter>
  </defs>
  <rect width="220" height="200" fill="url(#bg_et)" rx="12" stroke="#e8d5b0" stroke-width="1"/>
  <rect x="0" y="0" width="220" height="24" rx="12" fill="#1A4F96"/>
  <text x="110" y="16" text-anchor="middle" fill="white" font-size="10" font-weight="bold" font-family="Arial">Adhika / Sukshma Danta · Vata</text>
  <text x="110" y="190" text-anchor="middle" fill="#1A4F96" font-size="8.5" font-family="Arial" font-style="italic">Vata — Ruksha·Sukshma Guna (CS Vim 8/98)</text>

  <!-- Mouth open showing teeth -->
  <!-- Lips -->
  <path d="M42 95 Q110 72 178 95 Q165 115 110 120 Q55 115 42 95 Z" fill="#D07060" filter="url(#sh11)"/>
  <!-- Upper lip highlight -->
  <path d="M42 95 Q110 72 178 95" stroke="#A05040" stroke-width="2" fill="none"/>
  <!-- Mouth interior dark -->
  <ellipse cx="110" cy="108" rx="60" ry="18" fill="#3A1A10"/>
  <!-- Gum ridge upper -->
  <path d="M52 100 Q110 86 168 100" fill="#E8A0A0" stroke="none"/>
  <!-- Gum ridge lower -->
  <ellipse cx="110" cy="117" rx="52" ry="7" fill="#E8A0A0"/>

  <!-- Upper teeth — crowded, uneven, extra tooth -->
  <rect x="56"  y="95"  width="12" height="18" rx="3" fill="#F8F4EC" stroke="#DDD" stroke-width=".8"/>
  <rect x="67"  y="93"  width="11" height="20" rx="3" fill="#F0EEE8" stroke="#DDD" stroke-width=".8"/>
  <!-- Extra rotated tooth (crowded) -->
  <g transform="rotate(-8, 79, 100)">
    <rect x="75"  y="91"  width="10" height="21" rx="3" fill="#F8F4EC" stroke="#DDD" stroke-width=".8"/>
  </g>
  <rect x="84"  y="92"  width="11" height="19" rx="3" fill="#F0EEE8" stroke="#DDD" stroke-width=".8"/>
  <rect x="94"  y="91"  width="12" height="20" rx="3" fill="#F8F4EC" stroke="#DDD" stroke-width=".8"/>
  <rect x="105" y="92"  width="11" height="19" rx="3" fill="#F0EEE8" stroke="#DDD" stroke-width=".8"/>
  <rect x="115" y="91"  width="12" height="20" rx="3" fill="#F8F4EC" stroke="#DDD" stroke-width=".8"/>
  <g transform="rotate(7, 128, 100)">
    <rect x="125" y="92" width="10" height="19" rx="3" fill="#F0EEE8" stroke="#DDD" stroke-width=".8"/>
  </g>
  <rect x="134" y="93"  width="11" height="18" rx="3" fill="#F8F4EC" stroke="#DDD" stroke-width=".8"/>
  <rect x="144" y="95"  width="12" height="17" rx="3" fill="#F0EEE8" stroke="#DDD" stroke-width=".8"/>
  <!-- Stain on one tooth -->
  <rect x="84"  y="98" width="5"  height="6" rx="1" fill="#C8A860" opacity=".6"/>

  <!-- Lower teeth — smaller, uneven -->
  <rect x="62"  y="112" width="11" height="14" rx="3" fill="#F8F4EC" stroke="#DDD" stroke-width=".7"/>
  <rect x="73"  y="111" width="10" height="15" rx="3" fill="#F0EEE8" stroke="#DDD" stroke-width=".7"/>
  <rect x="83"  y="110" width="11" height="15" rx="3" fill="#F8F4EC" stroke="#DDD" stroke-width=".7"/>
  <rect x="94"  y="111" width="12" height="14" rx="3" fill="#F0EEE8" stroke="#DDD" stroke-width=".7"/>
  <rect x="106" y="111" width="11" height="14" rx="3" fill="#F8F4EC" stroke="#DDD" stroke-width=".7"/>
  <rect x="117" y="110" width="11" height="15" rx="3" fill="#F0EEE8" stroke="#DDD" stroke-width=".7"/>
  <rect x="128" y="111" width="11" height="14" rx="3" fill="#F8F4EC" stroke="#DDD" stroke-width=".7"/>
  <rect x="139" y="112" width="10" height="13" rx="3" fill="#F0EEE8" stroke="#DDD" stroke-width=".7"/>

  <!-- annotation arrow for crowding -->
  <line x1="75" y1="85" x2="68" y2="72" stroke="#1A4F96" stroke-width="1" stroke-dasharray="3 2"/>
  <text x="65" y="66" text-anchor="middle" fill="#1A4F96" font-size="8" font-family="Arial">Adhika</text>
  <text x="65" y="75" text-anchor="middle" fill="#1A4F96" font-size="8" font-family="Arial">(extra/</text>
  <text x="65" y="84" text-anchor="middle" fill="#1A4F96" font-size="8" font-family="Arial">crowded)</text>
</svg>""",

}  # end SVGS

# ── SVG display helper ─────────────────────────────────────────────────────────
def show_svg(key, label="🖼️ View Reference Illustration", use_expander=True):
    """Hybrid: prefers real photo from images/ folder, falls back to SVG."""
    IMG_FILE_MAP = {
        "body_builds":     "q01_body_build.jpg",
        "skin_complexion": "q03_skin_complexion.jpg",
        "skin_texture":    "q04_skin_texture.jpg",
        "hair_types":      "q05_hair_types.jpg",
        "veins_tendons":   "q09_veins_tendons.jpg",
        "lax_muscle":      "q09_lax_muscle.jpg",
        "well_built":      "q09_well_built.jpg",
        "freckles":        "q09_freckles.jpg",
        "broad_forehead":  "q09_broad_forehead.jpg",
        "calf_muscle":     "q09_calf_muscles.jpg",
        "excess_teeth":    "q11_teeth_crowded.jpg",
        "white_teeth":     "q11_teeth_white.jpg",
    }
    def _render():
        fname = IMG_FILE_MAP.get(key)
        if fname:
            p = os.path.join("images", fname)
            if os.path.exists(p) and os.path.getsize(p) > 500:
                try:
                    # Consistent height: wide images fill width, tall images capped
                    img = PILImage.open(p)
                    w, h = img.size
                    aspect = w / h
                    # Wide panels (body build, skin, hair): full width, auto height
                    # Tall/square images (teeth, calves, cracked sole): cap to 280px
                    if aspect >= 1.8:
                        st.image(p, use_container_width=True)
                    else:
                        st.image(p, width=280)
                    return
                except Exception:
                    pass
        if key in SVGS:
            st.markdown(f'<div style="padding:8px 0;">{SVGS[key]}</div>',
                        unsafe_allow_html=True)
    if use_expander:
        with st.expander(label):
            _render()
    else:
        _render()

# ── Bar helpers ────────────────────────────────────────────────────────────────
def bar(label, pct, css, color):
    w = max(round(pct), 4)
    return (f'<div class="bar-wrap">'
            f'<div class="bar-label" style="color:{color};">{label} — {pct}%</div>'
            f'<div class="bar-track"><div class="bar-fill {css}" style="width:{w}%;">{pct}%</div></div>'
            f'</div>')

def three_bars(p):
    return (bar("🌬️ Vata",  p["V"], "vata-fill",  "#1a4f96") +
            bar("🔥 Pitta", p["P"], "pitta-fill", "#9e2a0a") +
            bar("🌊 Kapha", p["K"], "kapha-fill", "#0d5c30"))

# ══════════════════════════════════════════════════════════════════════════════
#  ANTHROPOMETRIC FUNCTIONS
# ══════════════════════════════════════════════════════════════════════════════
def calc_bmi(weight_kg, height_cm):
    h = height_cm / 100
    return round(weight_kg / (h * h), 2)

def calc_bmr(weight_kg, height_cm, age, gender):
    """Mifflin-St Jeor equation"""
    if gender == "Male":
        return round(10*weight_kg + 6.25*height_cm - 5*age + 5, 1)
    else:
        return round(10*weight_kg + 6.25*height_cm - 5*age - 161, 1)

def calc_fat_pct(bmi, age, gender):
    """Deurenberg formula (1991)"""
    sex = 1 if gender == "Male" else 0
    fat = (1.20 * bmi) + (0.23 * age) - (10.8 * sex) - 5.4
    return round(max(fat, 0), 1)

def calc_whr(waist_cm, hip_cm):
    if hip_cm and hip_cm > 0:
        return round(waist_cm / hip_cm, 3)
    return None

def bmi_category(bmi):
    if bmi < 18.5: return "Underweight"
    elif bmi < 23:  return "Normal"
    elif bmi < 25:  return "Normal-High"
    elif bmi < 30:  return "Overweight"
    else:           return "Obese"

def specific_bmr(bmr, weight_kg):
    """BMR per kg — reflects metabolic rate (Agni strength)"""
    return round(bmr / weight_kg, 1) if weight_kg else 0

def score_anthropometric(profile):
    """
    Returns raw VPK scores from objective anthropometric parameters.
    Higher score = stronger Dosha expression.
    Normalized to % in calling function.
    """
    V, P, K = 0, 0, 0

    bmi     = profile.get("bmi", 22)
    fat_pct = profile.get("fat_pct", 20)
    sbmr    = profile.get("specific_bmr", 22)   # kcal/kg
    age     = profile.get("age", 30)
    gender  = profile.get("gender", "Male")
    whr     = profile.get("whr")                  # optional

    # ── BMI → primary body composition signal ─────────────────────────────
    if   bmi < 16.0: V += 3
    elif bmi < 18.5: V += 2
    elif bmi < 23.0: V += 1; P += 2
    elif bmi < 25.0:          P += 2; K += 1
    elif bmi < 27.5:          P += 1; K += 2
    elif bmi < 30.0:                  K += 3
    else:                             K += 3

    # ── Body Fat % → Medodhatu assessment ─────────────────────────────────
    if gender == "Male":
        if   fat_pct < 10:  V += 3
        elif fat_pct < 18:  V += 1; P += 2
        elif fat_pct < 25:           P += 2; K += 1
        elif fat_pct < 30:                   K += 2
        else:                                K += 3
    else:  # Female
        if   fat_pct < 18:  V += 3
        elif fat_pct < 25:  V += 1; P += 2
        elif fat_pct < 32:           P += 2; K += 1
        elif fat_pct < 38:                   K += 2
        else:                                K += 3

    # ── Specific BMR → Agni strength (Pitta = high, Kapha = low) ──────────
    if   sbmr > 27:  P += 3          # Very high Agni — Teekshna Pitta
    elif sbmr > 24:  P += 2
    elif sbmr > 21:  P += 1; K += 1
    elif sbmr > 18:           K += 2  # Manda Agni — Kapha
    else:                     K += 3  # Very low Agni

    # ── Age → Trividha Kala (Charaka Sharira Sthana 4/34) ─────────────────
    if   age > 60:  V += 2            # Vata kala
    elif age > 16:  P += 1            # Pitta kala
    else:           K += 1            # Kapha kala (childhood)

    # ── WHR (optional) → Central obesity / Medovriddhi ────────────────────
    if whr is not None:
        if gender == "Male":
            if   whr >= 1.0:   K += 3
            elif whr >= 0.90:  K += 2
        else:
            if   whr >= 0.90:  K += 3
            elif whr >= 0.80:  K += 2

    total = V + P + K
    if total == 0: total = 1
    return {
        "V": round(V/total*100, 1),
        "P": round(P/total*100, 1),
        "K": round(K/total*100, 1)
    }

def combine_scores(quest_op, anthro_op, w_quest=0.80, w_anthro=0.20):
    """Weighted combination. Both inputs are already %."""
    raw = {d: quest_op[d]*w_quest + anthro_op[d]*w_anthro for d in "VPK"}
    total = sum(raw.values())
    return {d: round(raw[d]/total*100, 1) for d in "VPK"} if total else raw

# ══════════════════════════════════════════════════════════════════════════════
#  QUESTIONNAIRE SCORING
# ══════════════════════════════════════════════════════════════════════════════
TRAITS      = ["Physical","Physiological","Psychological","Behavioral"]
TRAIT_ICONS = {"Physical":"🏃","Physiological":"⚙️","Psychological":"🧠","Behavioral":"🌿"}

def calculate_questionnaire(responses):
    raw = {t:{"V":0,"P":0,"K":0} for t in TRAITS}
    for q in QUESTIONS:
        sel    = responses.get(q["id"])
        if sel is None: continue
        opts   = q["options"]
        wt     = q.get("weight", 2)          # differential weight: 1 / 2 / 3
        if q["type"] == "single":
            if isinstance(sel, int) and sel < len(opts):
                for d in "VPK":
                    raw[q["trait"]][d] += opts[sel].get(d, 0) * wt
        else:
            for i in (sel or []):
                if i < len(opts):
                    for d in "VPK":
                        raw[q["trait"]][d] += opts[i].get(d, 0) * wt

    trait_pct = {}
    for t in TRAITS:
        tot = sum(raw[t].values())
        trait_pct[t] = ({d: round(raw[t][d]/tot*100, 1) for d in "VPK"}
                        if tot else {"V":33.3,"P":33.3,"K":33.4})

    all_raw = {"V":0,"P":0,"K":0}
    for t in TRAITS:
        for d in "VPK": all_raw[d] += raw[t][d]
    tot_o = sum(all_raw.values())
    op = ({d: round(all_raw[d]/tot_o*100, 1) for d in "VPK"}
          if tot_o else {"V":33.3,"P":33.3,"K":33.4})
    return trait_pct, op

def prakriti_type(op):
    """
    Always returns Dwandwaja (dual Dosha) Prakriti.
    The Dosha with higher % is Pradhana (primary), second is Anupradhana.
    Vata Pradhana Pitta ≠ Pitta Pradhana Vata — order is preserved.
    Classical basis: CS Sharira Sthana 4/38-39 — Dwandwaja Prakriti.
    """
    pairs = sorted([("Vata",op["V"]),("Pitta",op["P"]),("Kapha",op["K"])],
                   key=lambda x:-x[1])
    pradhana   = pairs[0][0]   # highest %
    anupradhana = pairs[1][0]  # second %
    p_pct  = pairs[0][1]
    ap_pct = pairs[1][1]
    t_pct  = pairs[2][1]       # third Dosha

    icons  = {"Vata":"🌬️","Pitta":"🔥","Kapha":"🌊"}
    colors = {"Vata":"#1a4f96","Pitta":"#9e2a0a","Kapha":"#0d5c30"}
    blend  = {("Vata","Pitta"):"#6b2080",("Vata","Kapha"):"#136b48",
              ("Pitta","Kapha"):"#9e5010",("Pitta","Vata"):"#7a2a1a",
              ("Kapha","Vata"):"#1a5a3a",("Kapha","Pitta"):"#8a4a10"}

    name  = f"{pradhana} Pradhana {anupradhana} Prakriti"
    icon  = icons[pradhana]
    color = colors[pradhana]
    return name, icon, color

# ══════════════════════════════════════════════════════════════════════════════
#  QUESTION DATABASE  — 45 questions, classical refs only
# ══════════════════════════════════════════════════════════════════════════════
QUESTIONS = [

    # ════ PHYSICAL (12) ══════════════════════════════════════════════════════

    {"id":1,"weight":3,"trait":"Physical","type":"single",
     "question":"My body build / physique is",
     "svg":"body_builds",
     "guna":"Apachita (Ruksha-Laghu-Vata) / Madhyama (Pitta) / Upachita (Sandra-Guru-Kapha)",
     "reference":"Charaka Vimana Sthana 8/96-98; Ashtanga Hridaya Sharira Sthana 3/83",
     "learn_more":"Vata's Ruksha (dry) and Laghu (light) Gunas produce lean, thin, underdeveloped frame — Apachita Shareera. Pitta's balanced Gunas produce well-proportioned moderate frame. Kapha's Sandra (dense) and Guru (heavy) Gunas produce well-built, heavy, well-nourished frame — Upachita Shareera — the most admired physique in classical texts.",
     "options":[
         {"text":"Very lean and thin","V":3,"P":1,"K":0},
         {"text":"Lean","V":2,"P":0,"K":0},
         {"text":"Moderate, well-proportioned","V":0,"P":2,"K":1},
         {"text":"Heavy built — tend to gain weight easily","V":0,"P":0,"K":3},
         {"text":"Very heavy — very difficult to lose weight","V":0,"P":0,"K":3}]},

    {"id":2,"weight":3,"trait":"Physical","type":"single",
     "question":"My height compared to others of similar age is",
     "svg":None,
     "guna":"Hrasva/Deergha Akriti (Ruksha-Vata) / Madhyama (Pitta) / Ghana (Kapha)",
     "reference":"Charaka Vimana Sthana 8/96; Ashtanga Hridaya Sharira Sthana 3/83",
     "learn_more":"Both extremes — Hrasva (very short) and Dirgha (very tall) — are Vata expressions. Ruksha, Laghu, and Bahu Gunas influence skeletal development in both directions. Average height is a Pitta attribute. Kapha individuals tend toward broad, sturdy frames rather than extreme height. This dual Vata expression is explicitly described in Charaka Vimana Sthana 8/96.",
     "options":[
         {"text":"Very short","V":2,"P":0,"K":0},
         {"text":"Short","V":2,"P":0,"K":0},
         {"text":"Average height","V":0,"P":1,"K":0},
         {"text":"Tall","V":2,"P":0,"K":0},
         {"text":"Broad and sturdy (any height)","V":0,"P":0,"K":2}]},

    {"id":3,"weight":3,"trait":"Physical","type":"single",
     "question":"My natural skin complexion is",
     "svg":"skin_complexion",
     "guna":"Gaur Varna (Mridu-Snigdha-Kapha) / Gaur-Pitanga (Ushna-Pitta) / Krishna/Dhusara (Ruksha-Vata)",
     "reference":"Charaka Vimana Sthana 8/96; Sushruta Sharira Sthana 4/62-63",
     "learn_more":"Kapha's Mridu and Snigdha Gunas produce Gaur (fair, lotus-like, lustrous) complexion — described as Padma-Patra-Sadrisha in Sushruta. Pitta's Ushna Guna gives fair with yellowish or reddish tinge (Pitta-Gaura). Vata's Ruksha Guna produces Dhusara (dusky) or Krishna (dark) complexion due to dryness of skin tissues.",
     "options":[
         {"text":"Very fair — lotus-like, lustrous","V":0,"P":0,"K":3},
         {"text":"Fair with yellowish or reddish tinge","V":0,"P":2,"K":1},
         {"text":"Medium / wheatish","V":0,"P":1,"K":0},
         {"text":"Dusky / olive","V":2,"P":0,"K":0},
         {"text":"Dark / very dark","V":3,"P":0,"K":0}]},

    {"id":4,"weight":3,"trait":"Physical","type":"multi",
     "question":"My skin texture — select all that apply",
     "svg":"skin_texture",
     "guna":"Snigdha/Shlakshna (Kapha) / Ruksha/Vishada (Vata) / Ushna/Teekshna (Pitta)",
     "reference":"Charaka Vimana Sthana 8/96; Ashtanga Hridaya Sharira Sthana 3/83-85",
     "learn_more":"Kapha's Snigdha and Shlakshna Gunas produce naturally moisturised, glowing, soft skin. Vata's Ruksha Guna causes chronic dryness (Rooksha Tvak) and palmar-plantar cracking (Paada-Hasta Sphutana). Pitta's Ushna and Teekshna Gunas cause skin warmth, acne (Pidaka), freckles (Vyanga), and early wrinkle formation. Each feature is independently listed in Charaka Vimana Sthana 8/96.",
     "options":[
         {"text":"Naturally oily / moisturised without products","V":0,"P":0,"K":3},
         {"text":"Smooth and very soft to touch","V":0,"P":0,"K":2},
         {"text":"Dry — needs moisturiser regularly","V":3,"P":0,"K":0},
         {"text":"Cracks on palms and soles","V":3,"P":0,"K":0},
         {"text":"Freckles or moles over skin (Vyanga)","V":0,"P":2,"K":0},
         {"text":"Pimples or acne tendency (Pidaka)","V":0,"P":3,"K":0},
         {"text":"Early appearance of wrinkles","V":0,"P":2,"K":0},
         {"text":"Skin warm or hot to touch","V":0,"P":3,"K":0},
         {"text":"Frequent mouth ulcers / aphthous ulcers","V":0,"P":2,"K":0}]},

    {"id":5,"weight":3,"trait":"Physical","type":"single",
     "question":"My hair texture and density is",
     "svg":"hair_types",
     "guna":"Ghana/Snigdha Kesha (Sandra-Kapha) / Ruksha/Parusha (Vata) / Mridu/Kapila (Ushna-Pitta)",
     "reference":"Charaka Vimana Sthana 8/96; Ashtanga Hridaya Sharira Sthana 3/83-85",
     "learn_more":"Kapha's Snigdha and Ghana Gunas produce thick, dense, lustrous, oily hair — Ghana-Snigdha-Kesha. Vata's Ruksha Guna produces dry, rough, brittle hair prone to split ends. Pitta's Ushna Guna produces soft, fine hair — often reddish-brown (Kapila) or lighter in colour, reflecting heat's effect on melanin.",
     "options":[
         {"text":"Thick, dense, lustrous and naturally oily","V":0,"P":0,"K":3},
         {"text":"Straight, black and dense","V":0,"P":0,"K":2},
         {"text":"Wavy or curly and dense","V":0,"P":0,"K":2},
         {"text":"Soft, fine, reddish-brown or light coloured","V":0,"P":3,"K":0},
         {"text":"Dry, rough, frizzy with split ends","V":3,"P":0,"K":0},
         {"text":"Scanty and thin","V":2,"P":1,"K":0}]},

    {"id":6,"weight":2,"trait":"Physical","type":"multi",
     "question":"Other hair features — select all that apply",
     "svg":None,
     "guna":"Akalapalita / Khalitya (Ushna-Pitta) / Sthira Kesha (Sthira-Kapha)",
     "reference":"Charaka Vimana Sthana 8/96; Sushruta Sharira Sthana 4/62",
     "learn_more":"Premature greying (Akalapalita) and early baldness (Khalitya) are classic Pitta expressions — Ushna Guna depletes pigment (Ranjaka Pitta) and damages follicles. Rough, split-end, dull-coloured hair indicates Vata's Ruksha-Vishada Gunas. Minimal hair fall and stable density (Sthira Kesha) is a hallmark Kapha quality.",
     "options":[
         {"text":"Premature greying (before age 35)","V":0,"P":3,"K":0},
         {"text":"Early hair loss / baldness","V":0,"P":3,"K":0},
         {"text":"Rough / split ends / dull coloured hair","V":2,"P":0,"K":0},
         {"text":"Minimal hair fall, stable density over years","V":0,"P":0,"K":2},
         {"text":"None of the above","V":0,"P":0,"K":0}]},

    {"id":7,"weight":3,"trait":"Physical","type":"multi",
     "question":"My eyes — select all that apply",
     "svg":None,
     "guna":"Vishalaksha/Pakshmal (Sandra-Kapha) / Tanulochana/Chala (Ruksha-Vata) / Tamranayana (Ushna-Pitta)",
     "reference":"Charaka Vimana Sthana 8/96; Sushruta Sharira Sthana 4/62-63",
     "learn_more":"Kapha's Sandra Guna produces Vishalaksha — large, beautiful, steady eyes with dense eyelashes (Pakshmal) — considered most auspicious. Vata's Chala Guna produces small (Tanu), dry, unsteady eyes — Chala Drishti. Pitta's Ushna and Teekshna Gunas produce coppery (Tamra) reddened eyes that flush with anger or sun.",
     "options":[
         {"text":"Large, attractive and steady gaze","V":0,"P":0,"K":3},
         {"text":"Small, dry, with unsteady or restless gaze","V":3,"P":0,"K":0},
         {"text":"Coppery / reddish tinge in the eyes","V":0,"P":3,"K":0},
         {"text":"Eyes redden with anger or sun exposure","V":0,"P":2,"K":0},
         {"text":"Dull / slightly sunken appearance","V":2,"P":0,"K":0},
         {"text":"Milky white, clearly visible sclera","V":0,"P":0,"K":2}]},

    {"id":8,"weight":2,"trait":"Physical","type":"single",
     "question":"My eyelashes are",
     "svg":None,
     "guna":"Pakshmalaksha (Sandra-Kapha) / Alpa Pakshma (Ushna-Pitta)",
     "reference":"Charaka Vimana Sthana 8/96; Ashtanga Hridaya Sharira Sthana 3/84",
     "learn_more":"Kapha's Sandra and Guru Gunas produce thick, long, dense, attractive eyelashes — Pakshmalaksha — a hallmark Kapha beauty feature and sign of excellent Rasa Dhatu nourishment. Pitta's Ushna Guna causes thin, scanty eyelashes (Alpa Pakshma) due to thermal depletion of hair follicles.",
     "options":[
         {"text":"Thick, long, dense and attractive","V":0,"P":0,"K":3},
         {"text":"Thin / scanty","V":0,"P":2,"K":0},
         {"text":"Average","V":0,"P":0,"K":0}]},

    {"id":9,"weight":2,"trait":"Physical","type":"multi",
     "question":"My body features — select all that apply",
     "svg":None,
     "guna":"Bahu-Kandara (Bahu-Vata) / Shithila Mamsa (Drava-Pitta) / Samamamsa/Charu-Jangha (Sara-Kapha)",
     "reference":"Charaka Vimana Sthana 8/96-98; Sushruta Sharira Sthana 4/62-63",
     "learn_more":"Vata's Bahu Guna produces prominently visible veins and tendons (Bahu-Sira-Snayu). Pitta's Drava Guna produces lax, soft muscles (Shithila Mamsa). Kapha's Sara Guna produces well-built, compact muscles (Sama Mamsa) and beautiful well-formed calf muscles (Charu Jangha) — highly valued in classical texts. Pitta's Ushna Guna also causes freckles (Vyanga).",
     "options":[
         {"text":"Prominently visible veins and tendons on limbs",
          "V":3,"P":0,"K":0,"svg":"veins_tendons"},
         {"text":"Lax, soft muscles — tissue feels soft/flabby",
          "V":0,"P":2,"K":0,"svg":"lax_muscle"},
         {"text":"Well-built, compact and uniform muscles",
          "V":0,"P":0,"K":3,"svg":"well_built"},
         {"text":"Prominent, well-formed calf muscles (Charu Jangha)",
          "V":0,"P":0,"K":2,"svg":"calf_muscle"},
         {"text":"Overall dry body (Ruksha Shareera)",
          "V":2,"P":0,"K":0},
         {"text":"Freckles or black patches on face / body",
          "V":0,"P":3,"K":0,"svg":"freckles"},
         {"text":"Broad forehead (Maha-Lalata)",
          "V":0,"P":0,"K":2,"svg":"broad_forehead"}]},

    {"id":10,"weight":3,"trait":"Physical","type":"multi",
     "question":"My joints — select all that apply",
     "svg":None,
     "guna":"Anavasthita/Sashabda Sandhi (Chala-Vata) / Sushlishta Sandhi (Sandra-Kapha)",
     "reference":"Charaka Vimana Sthana 8/96-98; Ashtanga Hridaya Sharira Sthana 3/83",
     "learn_more":"Vata's Chala Guna produces unstable, hypermobile joints (Anavasthita Sandhi). Vata's Vishada Guna causes crepitus — Sashabda Sandhi (joints cracking on movement). Both can coexist in the same individual. Kapha's Sandra Guna produces compact, stable, noiseless joints (Sushlishta Sandhi).",
     "options":[
         {"text":"Produce sounds / cracking (Crepitus) on movement","V":3,"P":0,"K":0},
         {"text":"Unstable — cannot sit still, constantly moving joints","V":3,"P":0,"K":0},
         {"text":"Compact, strong and stable — no sounds","V":0,"P":0,"K":3},
         {"text":"Loose / hypermobile beyond normal range","V":0,"P":2,"K":0}]},

    {"id":11,"weight":2,"trait":"Physical","type":"multi",
     "question":"My teeth — select all that apply",
     "svg":None,
     "guna":"Ruksha-Danta (Ruksha-Vata) / Danta-Vishuddha (Pitta) / Dridha-Danta (Sara-Kapha)",
     "reference":"Charaka Vimana Sthana 8/96; Sushruta Sharira Sthana 4/62",
     "learn_more":"Vata's Ruksha Guna produces rough, dry, uneven, or small teeth and excessive teeth (Adhika Danta). Pitta's Ushna and Teekshna Gunas produce white, clean, lustrous teeth (Danta-Vishuddha). Kapha's Sara Guna produces well-formed, strong, proportionate, firmly rooted teeth (Dridha-Danta).",
     "options":[
         {"text":"Rough / dry","V":2,"P":0,"K":0},
         {"text":"Small and uneven","V":2,"P":0,"K":0},
         {"text":"Excess / overcrowded teeth","V":1,"P":0,"K":0,"svg":"excess_teeth"},
         {"text":"White, clean and lustrous","V":0,"P":2,"K":0,"svg":"white_teeth"},
         {"text":"With stains / discolouration","V":1,"P":0,"K":0},
         {"text":"Well-formed, strong and proportionate","V":0,"P":0,"K":2,"svg":"white_teeth"}]},

    {"id":12,"weight":2,"trait":"Physical","type":"multi",
     "question":"My nails — select all that apply",
     "svg":None,
     "guna":"Alpanakha/Rukshanakha (Ruksha-Vata) / Tamranakha (Ushna-Pitta) / Deerghanakha (Sandra-Kapha)",
     "reference":"Charaka Vimana Sthana 8/96; Ashtanga Hridaya Sharira Sthana 3/84",
     "learn_more":"Vata's Ruksha Guna gives small, thin, dry, brittle nails that break easily. Pitta's Ushna Guna produces coppery or pinkish-copper nail beds (Tamra Nakha) — a distinctive Pitta marker. Kapha's Sandra Guna produces long, well-formed, lustrous, strong nails (Deergha-Snigdha Nakha).",
     "options":[
         {"text":"Small, thin, dry or brittle — break easily","V":3,"P":0,"K":0},
         {"text":"Long, well-formed, lustrous and strong","V":0,"P":0,"K":3},
         {"text":"Coppery / pinkish-copper coloured nail beds","V":0,"P":2,"K":0},
         {"text":"Grow excessively fast","V":1,"P":0,"K":0}]},

    # ════ PHYSIOLOGICAL (10) ═════════════════════════════════════════════════

    {"id":13,"weight":2,"trait":"Physiological","type":"single",
     "question":"My walking style / gait is",
     "svg":None,
     "guna":"Drutagati/Laghugati (Laghu-Shighra-Vata) / Saaragati (Guru-Sthira-Kapha) / Madhyagati (Pitta)",
     "reference":"Charaka Vimana Sthana 8/96-97; Ashtanga Hridaya Sharira Sthana 3/83-87",
     "learn_more":"Vata's Laghu and Shighra Gunas produce fast, inconsistent gait — Druta Gati. Kapha's Guru and Sthira Gunas produce steady, firm, deliberate gait — described as Gaja-Gati (elephant-like) in classical texts. Pitta individuals walk with purpose at moderate speed — neither rushing nor leisurely.",
     "options":[
         {"text":"Fast / quick — outpace most people","V":3,"P":0,"K":0},
         {"text":"Inconsistent — speed and style keeps changing","V":2,"P":0,"K":0},
         {"text":"Purposeful, moderate speed, precise steps","V":0,"P":2,"K":0},
         {"text":"Steady, consistent and firm — even-paced","V":0,"P":0,"K":3},
         {"text":"Slow and relaxed — never in a hurry","V":0,"P":0,"K":2}]},

    {"id":14,"weight":2,"trait":"Physiological","type":"single",
     "question":"My general activities and task initiation are",
     "svg":None,
     "guna":"Laghu-Chesta/Shighra-Arambha (Vata) / Manda-Chesta/Deergha-Arambha (Kapha) / Teekshna (Pitta)",
     "reference":"Charaka Vimana Sthana 8/97; Ashtanga Hridaya Sharira Sthana 3/83-87",
     "learn_more":"Vata's Shighra Guna drives rapid initiation — quick to start, often inconsistent in completion. Kapha's Manda Guna causes slow delayed initiation (Deergha-Arambha) but steady, persistent, thorough execution. Pitta's Teekshna Guna produces precise, orderly, goal-directed actions with excellent follow-through.",
     "options":[
         {"text":"Very quick — initiate and complete tasks fast","V":3,"P":0,"K":0},
         {"text":"Quick to initiate but inconsistent in completing","V":2,"P":0,"K":0},
         {"text":"Precise, orderly and systematic in all actions","V":0,"P":2,"K":0},
         {"text":"Slow to start but persistent and thorough once begun","V":0,"P":0,"K":3},
         {"text":"Very slow and relaxed in all activities","V":0,"P":0,"K":2}]},

    {"id":15,"weight":2,"trait":"Physiological","type":"multi",
     "question":"My voice and speech quality — select all that apply",
     "svg":None,
     "guna":"Ruksha/Sanna Swara (Ruksha-Vata) / Gambhira-Snigdha Swara (Snigdha-Kapha) / Teekshna (Pitta)",
     "reference":"Charaka Vimana Sthana 8/96-97; Sushruta Sharira Sthana 4/62",
     "learn_more":"Vata's Ruksha Guna produces rough (Parusha), feeble (Kshama), broken, or stammering voice — Sanna Swara. Kapha's Snigdha Guna produces deep (Gambhira), pleasant, melodious, resonant voice — one of the most prized Kapha qualities. Pitta speaks with speed, force, and clarity — Teekshna Vak — often dominating conversations.",
     "options":[
         {"text":"Deep, pleasant and melodious","V":0,"P":0,"K":3},
         {"text":"Clear and well-modulated","V":0,"P":0,"K":2},
         {"text":"Feeble / low-pitched","V":2,"P":0,"K":0},
         {"text":"Rough / hoarse / unpleasant","V":2,"P":0,"K":0},
         {"text":"Stammering / broken / unclear","V":2,"P":0,"K":0},
         {"text":"Fast, high-pitched or inconsistent","V":2,"P":0,"K":0}]},

    {"id":16,"weight":3,"trait":"Physiological","type":"single",
     "question":"My hunger pattern and eating speed",
     "svg":None,
     "guna":"Teekshna-Kshudha/Bahubhuja (Teekshna-Pitta) / Vishama Kshudha (Vata) / Manda Kshudha (Manda-Kapha)",
     "reference":"Charaka Vimana Sthana 8/97; Ashtanga Hridaya Sharira Sthana 3/85",
     "learn_more":"Pitta's Teekshna and Ushna Gunas produce intense, frequent hunger (Teekshna Kshudha) — skipping meals causes significant irritability. Called Bahubhuja (eating much) in classical texts. Vata shows irregular, variable hunger (Vishama Kshudha). Kapha's Manda Guna produces slow, moderate hunger — comfortably skip meals (Kshut-Sahishnu).",
     "options":[
         {"text":"Intense — very uncomfortable/irritable if I skip a meal","V":0,"P":3,"K":0},
         {"text":"Fast eater with irregular meal timing","V":2,"P":1,"K":0},
         {"text":"Irregular hunger — varies significantly day to day","V":2,"P":0,"K":0},
         {"text":"Slow eater with moderate, regular hunger","V":0,"P":0,"K":2},
         {"text":"Less hunger — can comfortably skip meals","V":0,"P":0,"K":3}]},

    {"id":17,"weight":3,"trait":"Physiological","type":"single",
     "question":"My thirst pattern is",
     "svg":None,
     "guna":"Prabhuta-Pana/Teekshna-Trishna (Ushna-Pitta) / Alpa-Pana (Sheeta-Kapha) / Vishama (Vata)",
     "reference":"Charaka Vimana Sthana 8/97; Ashtanga Hridaya Sharira Sthana 3/85",
     "learn_more":"Pitta's Ushna and Teekshna Gunas create intense, frequent thirst (Teekshna Trishna) — Pitta individuals drink large quantities. Kapha's Sheeta Guna reduces thirst — often forget to drink water (Alpa Trishna). Vata shows irregular, unpredictable thirst patterns (Vishama Trishna).",
     "options":[
         {"text":"Intense — drink large quantities, frequently thirsty","V":0,"P":3,"K":0},
         {"text":"Moderate and regular thirst","V":0,"P":1,"K":0},
         {"text":"Irregular — unpredictably thirsty","V":2,"P":0,"K":0},
         {"text":"Less — often forget to drink water","V":0,"P":0,"K":3}]},

    {"id":18,"weight":2,"trait":"Physiological","type":"single",
     "question":"My bowel and urine habits are",
     "svg":None,
     "guna":"Prabhuta-Srishta (Drava-Sara-Pitta) / Vibandha (Ruksha-Vata) / Manda (Manda-Kapha)",
     "reference":"Charaka Vimana Sthana 8/97; Ashtanga Hridaya Sharira Sthana 3/83-85",
     "learn_more":"Pitta's Drava and Sara Gunas produce regular, easy, sometimes excessive bowel evacuation — Prabhuta-Srishta Mala. Vata's Ruksha Guna causes constipation, hard stools (Vibandha). Kapha produces regular but slow, heavy, well-formed stools (Manda Mala Pravritti).",
     "options":[
         {"text":"Regular, easy and satisfactory bowel movement","V":0,"P":2,"K":1},
         {"text":"Loose stools / excess stool / frequent urination","V":0,"P":3,"K":0},
         {"text":"Constipation — hard or difficult stools frequently","V":3,"P":0,"K":0},
         {"text":"Irregular — alternates between loose and constipated","V":2,"P":0,"K":0},
         {"text":"Regular but slow, heavy and well-formed","V":0,"P":0,"K":2}]},

    {"id":19,"weight":3,"trait":"Physiological","type":"single",
     "question":"My sweating pattern is",
     "svg":None,
     "guna":"Prabhuta Sweda (Drava-Pitta) / Alpa Sweda (Sheeta-Kapha) / Vishama Sweda (Vata)",
     "reference":"Charaka Vimana Sthana 8/97; Ashtanga Hridaya Sharira Sthana 3/85",
     "learn_more":"Pitta's Drava Guna produces profuse sweating — Prabhuta Sweda — often triggered by mild activity or warmth. Kapha's Sheeta Guna suppresses sweating — very little even during vigorous exercise (Alpa Sweda). Vata shows Vishama Sweda — irregular, inconsistent sweating with no predictable pattern.",
     "options":[
         {"text":"Profuse sweating — even with mild activity or heat","V":0,"P":3,"K":0},
         {"text":"Noticeable sweating during regular exertion","V":0,"P":2,"K":0},
         {"text":"Moderate, normal sweating","V":0,"P":1,"K":0},
         {"text":"Less sweating even during exercise or hot weather","V":0,"P":0,"K":3},
         {"text":"Irregular and inconsistent — no set pattern","V":2,"P":0,"K":0}]},

    {"id":20,"weight":2,"trait":"Physiological","type":"multi",
     "question":"My sleep pattern — select all that apply",
     "svg":None,
     "guna":"Jagaruka/Alpanidra (Ruksha-Vata) / Nidrapriya/Guru-Nidra (Guru-Snigdha-Kapha) / Madhya-Nidra (Pitta)",
     "reference":"Charaka Vimana Sthana 8/97; Ashtanga Hridaya Sharira Sthana 3/83-87",
     "learn_more":"Kapha's Guru and Snigdha Gunas promote deep, prolonged, sound sleep — Guru Nidra. Vata's Ruksha and Laghu Gunas produce light, insufficient, easily disturbed sleep (Alpanidra / Jagaruka). Pitta individuals have moderate, good-quality sleep with vivid, intense dreams (Teekshna Swapna) — a reflection of active Agni.",
     "options":[
         {"text":"Sound, deep sleep — very difficult to wake","V":0,"P":0,"K":3},
         {"text":"I love sleeping / tend to oversleep","V":0,"P":0,"K":2},
         {"text":"Moderate sleep 6-7 hrs, vivid or intense dreams","V":0,"P":2,"K":0},
         {"text":"Light sleep — awakened by small sounds","V":3,"P":0,"K":0},
         {"text":"Less sleep — 5-6 hours feels sufficient","V":2,"P":0,"K":0},
         {"text":"Difficulty falling asleep","V":2,"P":0,"K":0},
         {"text":"Irregular sleeping habits — no fixed schedule","V":2,"P":0,"K":0}]},

    {"id":21,"weight":2,"trait":"Physiological","type":"single",
     "question":"My talking habit is",
     "svg":None,
     "guna":"Vachala (Chala-Bahu-Vata) / Pragalbha Vakta (Teekshna-Pitta) / Mitvak (Mridu-Manda-Kapha)",
     "reference":"Charaka Vimana Sthana 8/97; Ashtanga Hridaya Sharira Sthana 3/83-85",
     "learn_more":"Vata's Bahu and Chala Gunas produce talkative, rapid, sometimes wandering, repetitive speech — Vachala. Pitta's Teekshna Guna produces forceful, dominant, eloquent speech — Pragalbha Vakta. Kapha's Mridu and Manda Gunas produce soft-spoken, limited but meaningful, thoughtful speech — Mitvak.",
     "options":[
         {"text":"Talkative — talk a lot, sometimes wander off-topic","V":3,"P":0,"K":0},
         {"text":"Eloquent and dominant — forcefully establish my views","V":0,"P":3,"K":0},
         {"text":"Soft spoken, limited but meaningful and thoughtful","V":0,"P":0,"K":3},
         {"text":"Moderate talker","V":0,"P":1,"K":0}]},

    {"id":22,"weight":1,"trait":"Physiological","type":"multi",
     "question":"My dreams are usually about — select all that apply",
     "svg":None,
     "guna":"Vata Swapna (Akasha-Vayu) / Pitta Swapna (Agni-Tejas) / Kapha Swapna (Jala-Prithvi)",
     "reference":"Charaka Indriya Sthana 5/14-15; Charaka Sutrasthana 21/25-30",
     "learn_more":"Dreams (Swapna Vichara) are a classical Prakriti indicator. Vata dreams involve flying, mountains, dried rivers, restless movement — Akasha and Vayu expressions. Pitta dreams involve fire, conflict, lightning, red/gold colours — Agni and Tejas expressions. Kapha dreams involve serene water bodies, lotus, romantic and sentimental themes — Jala and Prithvi expressions.",
     "options":[
         {"text":"Flying, walking in sky / mountains / open spaces","V":2,"P":0,"K":0},
         {"text":"Searching, being lost or feeling restless","V":2,"P":0,"K":0},
         {"text":"Fighting, conflict or frightening nightmares","V":0,"P":2,"K":0},
         {"text":"Fire, lightning, gold or red colours","V":0,"P":2,"K":0},
         {"text":"Water bodies — oceans, rivers, lakes","V":0,"P":0,"K":2},
         {"text":"Romantic, sentimental or deeply peaceful themes","V":0,"P":0,"K":2},
         {"text":"Rarely remember dreams","V":0,"P":0,"K":0}]},

    # ════ PSYCHOLOGICAL (11) ═════════════════════════════════════════════════

    {"id":23,"weight":3,"trait":"Psychological","type":"single",
     "question":"My memory and recall ability is",
     "svg":None,
     "guna":"Alpa-Smriti/Chala-Smriti (Shighra-Chala-Vata) / Teekshna-Smriti (Pitta) / Smritimaan (Sthira-Kapha)",
     "reference":"Charaka Vimana Sthana 8/98; Ashtanga Hridaya Sharira Sthana 3/83-87",
     "learn_more":"Kapha's Sthira Guna produces excellent, reliable, long-term memory — Smritimaan — retaining information for years. Vata's Shighra Guna allows quick initial grasp but Chala Guna causes rapid forgetting (Chala Smriti). Pitta gives sharp, selective, focused memory — strong recall of relevant facts.",
     "options":[
         {"text":"Excellent long-term memory — retain things for years","V":0,"P":0,"K":3},
         {"text":"Sharp, selective memory for important things","V":0,"P":2,"K":0},
         {"text":"Quick to grasp but forget soon after","V":2,"P":0,"K":0},
         {"text":"Unstable — forget important things frequently","V":3,"P":0,"K":0},
         {"text":"Average memory","V":0,"P":1,"K":0}]},

    {"id":24,"weight":3,"trait":"Psychological","type":"single",
     "question":"My grasping / comprehension ability is",
     "svg":None,
     "guna":"Shrutagrahi (Shighra-Vata) / Nipunamati/Medhavi (Teekshna-Pitta) / Chiragrahi (Manda-Kapha)",
     "reference":"Charaka Vimana Sthana 8/97-98; Ashtanga Hridaya Sharira Sthana 3/86",
     "learn_more":"Vata's Shighra Guna gives very quick initial comprehension — Shrutagrahi. Pitta's Teekshna Guna gives deep analytical intelligence — Medhavi — finding patterns and implications. Kapha's Manda Guna causes slow initial comprehension (Chiragrahi) but information once understood is permanently and accurately retained.",
     "options":[
         {"text":"Very quick — grasp concepts almost instantly","V":3,"P":0,"K":0},
         {"text":"Analytical — understand deeply, find patterns","V":0,"P":3,"K":0},
         {"text":"Slow but thorough — takes time but retains permanently","V":0,"P":0,"K":3},
         {"text":"Moderate — average comprehension speed","V":0,"P":1,"K":0}]},

    {"id":25,"weight":3,"trait":"Psychological","type":"single",
     "question":"My anger and temperament pattern is",
     "svg":None,
     "guna":"Krodhi/Kshipra-Kopa (Teekshna-Ushna-Pitta) / Alpa-Krodha (Staimitya-Kapha) / Avasada (Vata)",
     "reference":"Charaka Vimana Sthana 8/97; Ashtanga Hridaya Sharira Sthana 3/85",
     "learn_more":"Pitta's Ushna and Teekshna Gunas produce quick anger (Kshipra Kopa) but also quick cooling (Kshipra Prasaada). Kapha's Staimitya Guna makes them very slow to anger (Alpa Krodha) but when angry, they hold grudges long (Chirodvega). Vata individuals experience agitation and restlessness (Avasada) rather than true anger.",
     "options":[
         {"text":"Short-tempered — angry quickly and cool down quickly","V":0,"P":3,"K":0},
         {"text":"Get irritable easily but forget about it soon","V":1,"P":2,"K":0},
         {"text":"Calm and patient — rarely lose temper","V":0,"P":0,"K":3},
         {"text":"Get agitated or restless when things go wrong","V":2,"P":0,"K":0},
         {"text":"Slow to anger but hold grudges for a long time","V":0,"P":0,"K":2},
         {"text":"Balanced, moderate temper","V":0,"P":0,"K":1}]},

    {"id":26,"weight":2,"trait":"Psychological","type":"multi",
     "question":"My mind is usually — select all that apply",
     "svg":None,
     "guna":"Chala/Bahu/Shighra Manas (Vata) / Teekshna Manas (Pitta) / Sthira Manas (Kapha)",
     "reference":"Charaka Vimana Sthana 8/96-98; Ashtanga Hridaya Sharira Sthana 3/83-87",
     "learn_more":"Vata's Chala, Bahu, and Shighra Gunas produce active, restless, imaginative, anxiety-prone minds — difficulty sustaining focus. Pitta's Teekshna Guna gives analytical, critical, ambitious, perfectionistic minds. Kapha's Sthira Guna gives deeply stable, calm, composed mental states — highly resistant to disturbance.",
     "options":[
         {"text":"Very active and imaginative","V":2,"P":0,"K":0},
         {"text":"Restless — difficult to focus for long","V":3,"P":0,"K":0},
         {"text":"Anxious or worried frequently","V":3,"P":0,"K":0},
         {"text":"Analytical and critical — examine everything","V":0,"P":2,"K":0},
         {"text":"Calm, stable and composed","V":0,"P":0,"K":3},
         {"text":"Moods keep changing frequently","V":2,"P":0,"K":0}]},

    {"id":27,"weight":3,"trait":"Psychological","type":"single",
     "question":"My weather and temperature tolerance is",
     "svg":None,
     "guna":"Sheeta-Asahishnu (Sheeta-Vata) / Ushna-Asahishnu/Sheetabhilashi (Ushna-Pitta) / Sarva-Sahishnu (Kapha)",
     "reference":"Charaka Vimana Sthana 8/97; Ashtanga Hridaya Sharira Sthana 3/83-85",
     "learn_more":"Vata's Sheeta Guna makes individuals highly sensitive to cold — Sheeta-Asahishnu. Pitta's Ushna Guna makes them intolerant of heat — always seeking cool environments (Sheetabhilashi). Kapha's Sthira and Sheeta Gunas make them tolerant of most weather conditions — Sarva-Sahishnu.",
     "options":[
         {"text":"Cannot tolerate cold — always prefer warmth","V":3,"P":0,"K":0},
         {"text":"Cannot tolerate heat — always prefer cool/cold","V":0,"P":3,"K":0},
         {"text":"Fatigue easily in hot weather / sun","V":0,"P":2,"K":0},
         {"text":"Sensitive to both extremes of temperature","V":2,"P":0,"K":0},
         {"text":"Generally tolerant of most weather conditions","V":0,"P":0,"K":2}]},

    {"id":28,"weight":2,"trait":"Psychological","type":"single",
     "question":"My lifestyle regularity is",
     "svg":None,
     "guna":"Niyamita/Sthira-Dinacharya (Sthira-Kapha) / Vishama/Aniyamita (Chala-Vata) / Madhyama (Pitta)",
     "reference":"Charaka Vimana Sthana 8/97; Ashtanga Hridaya Sharira Sthana 3/83",
     "learn_more":"Kapha's Sthira Guna produces highly regular, disciplined, stable daily routines. Vata's Chala Gunas produce erratic, inconsistent, frequently changing routines (Vishama Dinacharya) — starting many routines but maintaining none. Pitta individuals are goal-focused and moderately regular.",
     "options":[
         {"text":"Very regular — same routine every single day","V":0,"P":0,"K":3},
         {"text":"Moderately regular with some planned variation","V":0,"P":2,"K":0},
         {"text":"Somewhat erratic — routines change frequently","V":2,"P":0,"K":0},
         {"text":"Very erratic — no fixed routine at all","V":3,"P":0,"K":0}]},

    {"id":29,"weight":2,"trait":"Psychological","type":"single",
     "question":"My decision making is",
     "svg":None,
     "guna":"Anavasthita Atma/Chala-Mati (Chala-Vata) / Teekshna-Nischaya (Pitta) / Dridha-Nischaya (Sthira-Kapha)",
     "reference":"Charaka Vimana Sthana 8/97; Ashtanga Hridaya Sharira Sthana 3/83-87",
     "learn_more":"Vata's Chala Mati causes indecisiveness (Anavasthita-Chitta) — frequent reversals. Pitta's Teekshna Guna gives quick, confident, often dogmatic decisions — Teekshna Nischaya. Kapha's Sthira Guna gives slow but extremely firm decisions (Dridha Nischaya) — rarely ever reversed.",
     "options":[
         {"text":"Very indecisive — change my mind frequently","V":3,"P":0,"K":0},
         {"text":"Quick and confident — sometimes impulsive","V":0,"P":3,"K":0},
         {"text":"Slow but very firm — rarely change once decided","V":0,"P":0,"K":3},
         {"text":"Moderate — thoughtful but timely","V":0,"P":1,"K":0}]},

    {"id":30,"weight":2,"trait":"Psychological","type":"single",
     "question":"My friendship and relationship patterns are",
     "svg":None,
     "guna":"Adridha-Sauhrida/Shighra-Sauhrida (Shighra-Vata) / Sthira-Sauhrida (Sthira-Kapha) / Teekshna (Pitta)",
     "reference":"Charaka Vimana Sthana 8/97; Ashtanga Hridaya Sharira Sthana 3/85-87",
     "learn_more":"Vata's Shighra Guna creates friendships quickly but they are unstable and transient (Adridha Sauhrida). Kapha's Sthira Guna produces few but deeply loyal, lifelong, unwavering friendships — Dridha-Mitra. Pitta cultivates selective, purpose-aligned friendships with high expectations.",
     "options":[
         {"text":"Many friends — make friends quickly but they change often","V":2,"P":0,"K":0},
         {"text":"Friendships are fickle — change very frequently","V":3,"P":0,"K":0},
         {"text":"Few but deeply loyal, lifelong friendships","V":0,"P":0,"K":3},
         {"text":"Selective — quality-focused, high expectations","V":0,"P":2,"K":0}]},

    {"id":31,"weight":2,"trait":"Psychological","type":"single",
     "question":"My self-control and discipline are",
     "svg":None,
     "guna":"Alaulupa (Sthira-Kapha) / Ajitendriya (Shighra-Vata) / Teekshna-Niyama (Pitta)",
     "reference":"Charaka Vimana Sthana 8/97; Ashtanga Hridaya Sharira Sthana 3/85",
     "learn_more":"Kapha's Sthira Guna gives excellent natural ability to resist temptations (Alaulupa) — self-control comes naturally. Vata's Shighra Guna causes impulsive behaviour and poor Indriya restraint (Ajitendriya). Pitta's discipline is goal-oriented and ambitious — excellent when motivated.",
     "options":[
         {"text":"Excellent — very disciplined, rarely give in to temptation","V":0,"P":0,"K":3},
         {"text":"Good — disciplined with consistent conscious effort","V":0,"P":2,"K":0},
         {"text":"Poor — frequently give in to impulses","V":3,"P":0,"K":0},
         {"text":"Variable — depends heavily on the situation","V":2,"P":0,"K":0}]},

    {"id":32,"weight":3,"trait":"Psychological","type":"single",
     "question":"My intelligence type is best described as",
     "svg":None,
     "guna":"Nipunamati/Medhavi (Teekshna-Pitta) / Buddhiyukta (Sthira-Kapha) / Chala-Buddhi (Shighra-Vata)",
     "reference":"Charaka Vimana Sthana 8/97-98; Ashtanga Hridaya Sharira Sthana 3/86",
     "learn_more":"Pitta's Teekshna Guna gives sharp, analytical, pattern-finding intelligence — Medhavi. Kapha's Sthira Guna gives deep, wise, profound intelligence — Buddhiyukta — slow in acquisition but producing comprehensive understanding. Vata's Laghu Guna gives creative, versatile, broad intelligence (Chala Buddhi) — curious but sometimes scattered.",
     "options":[
         {"text":"Sharp and analytical — find patterns and connections quickly","V":0,"P":3,"K":0},
         {"text":"Deep and wise — thorough, comprehensive understanding","V":0,"P":0,"K":3},
         {"text":"Creative and versatile — broad interests, many ideas","V":2,"P":0,"K":0},
         {"text":"Average — moderate overall","V":0,"P":1,"K":0}]},

    {"id":33,"weight":2,"trait":"Psychological","type":"multi",
     "question":"My fear and courage response — select all that apply",
     "svg":None,
     "guna":"Teekshna-Parakrama/Shoora (Teekshna-Pitta) / Hinasattva/Bhiru (Shighra-Vata) / Sthira (Sthira-Kapha)",
     "reference":"Charaka Vimana Sthana 8/97; Ashtanga Hridaya Sharira Sthana 3/83-85",
     "learn_more":"Pitta's Teekshna Guna produces natural courage (Shoora) — refusal to surrender under fear (Teekshna Parakrama). Vata's Shighra Guna causes fearfulness (Bhiru) and easily startled response (Hinasattva). Classical texts distinguish Bhaya (fear response) from Udvega (panic) — both Vata expressions. Kapha's Sthira Guna produces calm, unshakeable stability in adversity.",
     "options":[
         {"text":"Very brave — stand for values regardless of opposition","V":0,"P":3,"K":0},
         {"text":"Brave when needed, composed in adversity","V":0,"P":1,"K":1},
         {"text":"Get frightened easily in unfamiliar or adverse situations","V":2,"P":0,"K":0},
         {"text":"Tend to panic — lose composure under strong pressure","V":3,"P":0,"K":0},
         {"text":"Have experienced sudden panic attacks without obvious trigger","V":3,"P":0,"K":0},
         {"text":"Stable and unshakeable — rarely feel fear or panic","V":0,"P":0,"K":3}]},

    # ════ BEHAVIORAL (12) ════════════════════════════════════════════════════

    {"id":34,"weight":3,"trait":"Behavioral","type":"multi",
     "question":"My natural food taste preferences — select your top 2 to 3",
     "svg":None,
     "guna":"Madhura/Amla/Lavana (Vata-sahaja) / Tikta/Kashaya (Pitta-sahaja) / Katu/Tikta (Kapha-sahaja)",
     "reference":"Charaka Sutrasthana 26/43; Charaka Vimana Sthana 8/97",
     "learn_more":"Prakriti influences natural taste preferences (Ruchi) through constitutional Guna alignment. Vata individuals naturally gravitate toward Madhura (sweet), Amla (sour), and Lavana (salty) — the three Vata-balancing Rasas. Pitta prefers Tikta (bitter) and Kashaya (astringent). Kapha naturally craves Katu (pungent) and Tikta — the Kapha-stimulating Rasas.",
     "options":[
         {"text":"Sweet / Madhura","V":2,"P":0,"K":0},
         {"text":"Sour / tangy — Amla","V":2,"P":0,"K":0},
         {"text":"Salty — Lavana","V":2,"P":0,"K":0},
         {"text":"Bitter — Tikta","V":0,"P":2,"K":0},
         {"text":"Astringent — Kashaya","V":0,"P":2,"K":0},
         {"text":"Pungent / spicy — Katu","V":0,"P":0,"K":2}]},

    {"id":35,"weight":2,"trait":"Behavioral","type":"single",
     "question":"My food and drink temperature preference is",
     "svg":None,
     "guna":"Ushna-Annapana-Kanksha (Sheeta-Vata) / Sheeta-Abhilashi (Ushna-Pitta) / Ushna-Laghu (Kapha)",
     "reference":"Charaka Sutrasthana 26; Ashtanga Hridaya Sutrasthana 10/17",
     "learn_more":"Vata's Sheeta Guna makes individuals strongly prefer hot or warm food and drinks (Ushna Annapana Kanksha). Pitta's Ushna Guna creates preference for cool or cold foods (Sheeta Abhilashi). Kapha benefits constitutionally from warm, light foods.",
     "options":[
         {"text":"Hot / warm food and drinks always — cold is uncomfortable","V":3,"P":0,"K":0},
         {"text":"Cold / cool food and drinks — prefer strongly","V":0,"P":3,"K":0},
         {"text":"Moderately warm — not too hot or cold","V":0,"P":0,"K":2},
         {"text":"No strong preference","V":0,"P":0,"K":0}]},

    {"id":36,"weight":1,"trait":"Behavioral","type":"single",
     "question":"My exercise and physical activity habits are",
     "svg":None,
     "guna":"Vyayama-Sheela (Sthira-Kapha) / Chapala-Vyayama (Chala-Vata) / Teekshna-Vyayama (Pitta)",
     "reference":"Charaka Sutrasthana 7/31-32; Ashtanga Hridaya Sutrasthana 2/10",
     "learn_more":"Kapha's Sthira Guna gives excellent exercise endurance and consistent, habitual physical activity (Vyayama Sheela). Vata individuals start enthusiastically but are inconsistent (Chapala) — cycles of intensity followed by long breaks. Pitta exercises with intensity and competitive goal orientation (Teekshna Vyayama).",
     "options":[
         {"text":"Regular, consistent — exercise without fail daily","V":0,"P":0,"K":3},
         {"text":"Intense when I do it, but sometimes skip","V":0,"P":2,"K":0},
         {"text":"Irregular — enthusiastic phases then long inactive periods","V":3,"P":0,"K":0},
         {"text":"Prefer rest / minimal physical activity","V":0,"P":0,"K":2}]},

    {"id":37,"weight":1,"trait":"Behavioral","type":"multi",
     "question":"My hobbies and interests — select all that apply",
     "svg":None,
     "guna":"Shastra-Priya (Sthira-Kapha) / Yatra-Priya (Chala-Vata) / Teekshna-Kriya (Pitta)",
     "reference":"Charaka Vimana Sthana 8/97; Ashtanga Hridaya Sharira Sthana 3/83-87",
     "learn_more":"Kapha individuals prefer stable, nurturing, knowledge-based activities — reading, gardening (Shastra Priya). Vata prefer variety, movement, novelty — travel, dance, creative arts (Yatra Priya). Pitta prefer goal-oriented, challenging, competitive activities.",
     "options":[
         {"text":"Travelling to new places","V":2,"P":0,"K":0},
         {"text":"Reading / studying / classical knowledge","V":0,"P":0,"K":2},
         {"text":"Music, singing or listening","V":1,"P":0,"K":1},
         {"text":"Gardening / nurturing nature","V":0,"P":0,"K":2},
         {"text":"Adventure, challenge, competitive activities","V":0,"P":2,"K":0},
         {"text":"Dancing / creative performing arts","V":2,"P":0,"K":0},
         {"text":"Comfortable, luxurious lifestyle activities","V":0,"P":0,"K":1}]},

    {"id":38,"weight":1,"trait":"Behavioral","type":"multi",
     "question":"About myself — I feel that (select all that apply)",
     "svg":None,
     "guna":"Multiple Prakriti-based personality expressions — Charaka Vimana Sthana 8/97",
     "reference":"Charaka Vimana Sthana 8/97; Ashtanga Hridaya Sharira Sthana 3/83-87",
     "learn_more":"Pitta individuals identify with efficiency, organisation, and perfectionism (Teekshna Guna expressions). Kapha individuals are patient listeners and good team players (Mridu and Sthira Guna expressions). Vata individuals love freedom, resist fixed commitments, and frequently change plans (Chala Guna expression).",
     "options":[
         {"text":"I like to be free and unattached — dislike rigid structure","V":2,"P":0,"K":0},
         {"text":"I am efficient, organised and capable","V":0,"P":2,"K":0},
         {"text":"I am a perfectionist about details","V":0,"P":2,"K":0},
         {"text":"I cannot accept disagreement or opposition easily","V":0,"P":2,"K":0},
         {"text":"I am a patient listener","V":0,"P":0,"K":2},
         {"text":"I am a good follower / team player","V":0,"P":0,"K":2},
         {"text":"I frequently change my plans, goals or interests","V":2,"P":0,"K":0}]},

    {"id":39,"weight":2,"trait":"Behavioral","type":"multi",
     "question":"My values and moral character — select all that apply",
     "svg":None,
     "guna":"Suchi/Satyavadi (Teekshna-Pitta) / Vineeta/Gurumanayita (Snigdha-Sthira-Kapha)",
     "reference":"Charaka Vimana Sthana 8/97; Charaka Sharira Sthana 1/101",
     "learn_more":"Pitta's Teekshna Guna produces purity orientation (Suchi) and absolute truthfulness (Satyavadi). Kapha's Snigdha and Sthira Gunas produce natural politeness (Vineeta), humility, and deep respect for elders and teachers (Gurumanayita). Kapha individuals are naturally affectionate toward dependents (Poshya-Vatsala).",
     "options":[
         {"text":"Very particular about purity and cleanliness","V":0,"P":2,"K":0},
         {"text":"Truthful even when it is difficult or uncomfortable","V":0,"P":2,"K":1},
         {"text":"Polite and humble with everyone","V":0,"P":0,"K":3},
         {"text":"Deep respect for elders and teachers","V":0,"P":0,"K":2},
         {"text":"Affectionate and caring towards dependents","V":0,"P":0,"K":2}]},

    {"id":40,"weight":1,"trait":"Behavioral","type":"multi",
     "question":"My self-concept — I identify with (select all that apply)",
     "svg":None,
     "guna":"Abhimani/Stutipriya (Teekshna-Pitta) / Gambhira/Sulajjo (Sthira-Kapha)",
     "reference":"Charaka Vimana Sthana 8/97; Ashtanga Hridaya Sharira Sthana 3/85-87",
     "learn_more":"Pitta's Teekshna Guna produces competitive spirit (Spardha) and fondness for recognition (Stutipriya / Abhimani). Kapha's Sthira Guna produces stable, dignified, secure self-concept (Gambhira) and genuine humility (Sulajjo). Vata individuals have variable, inconsistent self-image.",
     "options":[
         {"text":"I have a strong competitive spirit","V":0,"P":2,"K":0},
         {"text":"I like to be praised and recognised","V":0,"P":2,"K":0},
         {"text":"I have a dignified, stable sense of identity","V":0,"P":0,"K":3},
         {"text":"I am genuinely modest and humble","V":0,"P":0,"K":2},
         {"text":"My self-image keeps changing frequently","V":2,"P":0,"K":0}]},

    {"id":41,"weight":1,"trait":"Behavioral","type":"single",
     "question":"My generosity and giving nature is",
     "svg":None,
     "guna":"Pariganya Chirat Pradadati Bahu (Sthira-Snigdha-Kapha) / Vishama Dana (Vata) / Kritadana (Pitta)",
     "reference":"Charaka Vimana Sthana 8/97; Ashtanga Hridaya Sharira Sthana 3/87",
     "learn_more":"Kapha's Snigdha and Sthira Gunas produce genuinely generous, judiciously giving nature — Pradadati Bahu — described as one of Kapha's most admirable behavioral qualities. Pitta gives competitively or when it reflects well on them (Kritadana). Vata is inconsistent (Vishama Dana).",
     "options":[
         {"text":"Genuinely generous — give freely and thoughtfully","V":0,"P":0,"K":3},
         {"text":"Generous when I see genuine need","V":0,"P":1,"K":1},
         {"text":"Give but like to be acknowledged for it","V":0,"P":2,"K":0},
         {"text":"Inconsistent — sometimes generous, sometimes not","V":2,"P":0,"K":0}]},

    {"id":42,"weight":1,"trait":"Behavioral","type":"single",
     "question":"My faith and belief system is",
     "svg":None,
     "guna":"Aastika/Dridha-Dharma (Sthira-Kapha) / Dharmatma (Pitta) / Nastika/Chala-Dharma (Chala-Vata)",
     "reference":"Charaka Vimana Sthana 8/97; Ashtanga Hridaya Sharira Sthana 3/83-87",
     "learn_more":"Kapha's Sthira Guna produces deep, unwavering, traditional faith (Dridha Dharma / Aastika). Pitta individuals are principled and ethically strong (Dharmatma) but may be rigid about beliefs. Vata's Chala Guna produces skepticism or frequently changing belief systems (Nastika / Chala Dharma).",
     "options":[
         {"text":"Deep, unwavering faith — follow traditions strongly","V":0,"P":0,"K":3},
         {"text":"Principled and truthful — strong ethical/moral stance","V":0,"P":2,"K":1},
         {"text":"Moderate — questioning but respectful","V":0,"P":1,"K":0},
         {"text":"Skeptical or frequently changing beliefs","V":2,"P":0,"K":0}]},

    {"id":43,"weight":2,"trait":"Behavioral","type":"single",
     "question":"My body odour is",
     "svg":None,
     "guna":"Swedo-Durgandha/Visra-Guna (Ushna-Pitta) / Alpa-Gandha (Sheeta-Kapha)",
     "reference":"Charaka Vimana Sthana 8/97; Sushruta Sharira Sthana 4/62-63",
     "learn_more":"Pitta's Visra Guna (raw-flesh smell) produces characteristically strong body odour from armpits (Kaksha), scalp (Shira), and mouth (Mukha) — one of the most reliably identified Pitta features. Called Puti Gandha in classical texts. Kapha individuals have minimal, pleasant body odour (Alpa Gandha). Vata shows variable body odour.",
     "options":[
         {"text":"Strong — others have noticed or commented","V":0,"P":3,"K":0},
         {"text":"Moderate / normal perspiration smell","V":0,"P":1,"K":0},
         {"text":"Minimal body odour","V":0,"P":0,"K":2},
         {"text":"Variable — depends on day / activity / diet","V":1,"P":0,"K":0}]},

    {"id":44,"weight":2,"trait":"Behavioral","type":"single",
     "question":"My physical endurance and strength is",
     "svg":None,
     "guna":"Balavan (Sara-Kapha) / Alpa-Bala (Ruksha-Vata) / Madhyabala (Pitta)",
     "reference":"Charaka Vimana Sthana 8/96-97; Ashtanga Hridaya Sharira Sthana 3/83-87",
     "learn_more":"Kapha's Sara Guna gives naturally great, sustained endurance, physical stamina, and strength (Balavan) — Kapha Sara is the highest expression of physical nourishment. Vata's Ruksha and Laghu Gunas produce less physical strength (Alpa Bala) — quick fatigue. Pitta has moderate strength (Madhyabala) with strong competitive drive.",
     "options":[
         {"text":"Very strong — excellent endurance and sustained stamina","V":0,"P":0,"K":3},
         {"text":"Moderate — average physical strength and endurance","V":0,"P":2,"K":0},
         {"text":"Less — fatigue easily, not very strong physically","V":3,"P":0,"K":0},
         {"text":"Strong in spurts but tires quickly","V":2,"P":0,"K":0}]},

    {"id":45,"weight":1,"trait":"Behavioral","type":"single",
     "question":"My sexual desire compared to others of similar age is",
     "svg":None,
     "guna":"Madhura/Bahu-Shukra (Snigdha-Guru-Kapha) / Teekshna-Kama (Ushna-Pitta) / Alpa/Vishama (Ruksha-Vata)",
     "reference":"Charaka Vimana Sthana 8/96-97; Charaka Sharira Sthana 4/34; Ashtanga Hridaya Sharira Sthana 3/87",
     "learn_more":"Kapha's Snigdha and Guru Gunas produce naturally high, sustained sexual desire with good reproductive capacity — Bahu Shukra (excellent Shukra Dhatu nourishment). Pitta's Teekshna Guna produces intense but sometimes inconsistent desire. Vata's Ruksha Guna reduces both desire (Alpa Shukra) and capacity, or makes them highly irregular (Vishama).",
     "options":[
         {"text":"High and consistent","V":0,"P":0,"K":3},
         {"text":"Moderate and normal","V":0,"P":1,"K":1},
         {"text":"Intense but variable","V":0,"P":2,"K":0},
         {"text":"Low or irregular","V":2,"P":0,"K":0},
         {"text":"Prefer not to answer","V":0,"P":0,"K":0}]},
]

TRAIT_Q = {t:[q for q in QUESTIONS if q["trait"]==t] for t in TRAITS}

# ══════════════════════════════════════════════════════════════════════════════
#  MANDATORY QUESTIONS  (min 3-5 per trait — highest diagnostic weight)
#  Physical: Q1 Body build · Q3 Complexion · Q4 Skin texture · Q5 Hair · Q7 Eyes
#  Physiological: Q16 Hunger · Q17 Thirst · Q18 Bowel · Q19 Sweating
#  Psychological & Behavioral: top 3 weight:3 questions per trait (auto-selected)
# ══════════════════════════════════════════════════════════════════════════════
def _build_mandatory_qs():
    mset = {1, 3, 4, 5, 7, 16, 17, 18, 19}   # Physical + Physiological
    for trait in ["Psychological", "Behavioral"]:
        w3 = [q["id"] for q in TRAIT_Q[trait] if q.get("weight", 2) == 3]
        others = [q["id"] for q in TRAIT_Q[trait] if q["id"] not in w3]
        chosen = (w3 + others)[:3]
        mset |= set(chosen)
    return mset

MANDATORY_QS = _build_mandatory_qs()

# ══════════════════════════════════════════════════════════════════════════════
#  AHARA DATA  — Pathya & Apathya per category
#  Source: Dr. Prasanna Kulkarni — CCRAS / Classical reference list
#  Keys: VP=Vata Pathya  VA=Vata Apathya  PP=Pitta Pathya
#        PA=Pitta Apathya  KP=Kapha Pathya  KA=Kapha Apathya
# ══════════════════════════════════════════════════════════════════════════════
AHARA_DATA = {
    "Cereals (Dhanya)": [
        {"name":"Rakta Shali",             "VP":1,"VA":0,"PP":1,"PA":0,"KP":1,"KA":0},
        {"name":"Godhuma (Wheat)",          "VP":1,"VA":0,"PP":1,"PA":0,"KP":0,"KA":1},
        {"name":"Yava (Barley)",            "VP":0,"VA":1,"PP":1,"PA":0,"KP":1,"KA":0},
    ],
    "Pulses (Shimbi Dhanya)": [
        {"name":"Mudga (Green Gram)",       "VP":0,"VA":1,"PP":1,"PA":0,"KP":1,"KA":0},
        {"name":"Masha (Black Gram)",       "VP":1,"VA":0,"PP":0,"PA":0,"KP":1,"KA":0},
        {"name":"Masura (Red Lentil)",      "VP":0,"VA":1,"PP":1,"PA":0,"KP":1,"KA":0},
        {"name":"Kulattha (Horse Gram)",    "VP":1,"VA":0,"PP":0,"PA":1,"KP":1,"KA":0},
        {"name":"Sarshapa (Mustard Seed)",  "VP":1,"VA":0,"PP":0,"PA":1,"KP":1,"KA":0},
        {"name":"Adhaki (Pigeon Pea)",      "VP":0,"VA":1,"PP":1,"PA":0,"KP":1,"KA":0},
        {"name":"Kalaya (Garden Pea)",      "VP":0,"VA":1,"PP":1,"PA":0,"KP":1,"KA":0},
        {"name":"Nishpava (Flat Bean)",     "VP":0,"VA":1,"PP":0,"PA":1,"KP":1,"KA":0},
        {"name":"Chanaka (Chickpea)",       "VP":0,"VA":1,"PP":1,"PA":0,"KP":1,"KA":0},
        {"name":"Tila (Sesame Seed)",       "VP":1,"VA":0,"PP":0,"PA":1,"KP":0,"KA":1},
        {"name":"Atasi (Linseed)",          "VP":1,"VA":0,"PP":0,"PA":1,"KP":0,"KA":1},
    ],
    "Shaka (Vegetables & Spices)": [
        {"name":"Ardraka (Ginger)",         "VP":1,"VA":0,"PP":0,"PA":0,"KP":1,"KA":0},
        {"name":"Shigru (Drumstick)",       "VP":1,"VA":0,"PP":0,"PA":0,"KP":0,"KA":0},
        {"name":"Dhanyaka (Coriander)",     "VP":1,"VA":0,"PP":1,"PA":0,"KP":1,"KA":0},
        {"name":"Ela (Cardamom)",           "VP":1,"VA":0,"PP":0,"PA":0,"KP":1,"KA":0},
        {"name":"Ervaruka (Cucumber)",      "VP":0,"VA":1,"PP":0,"PA":0,"KP":1,"KA":0},
        {"name":"Hingu (Asafoetida)",       "VP":0,"VA":1,"PP":0,"PA":0,"KP":1,"KA":0},
        {"name":"Karavellaka (Bitter Gourd)","VP":0,"VA":1,"PP":1,"PA":0,"KP":1,"KA":0},
        {"name":"Kushmanda (Ash Gourd)",    "VP":0,"VA":0,"PP":1,"PA":0,"KP":1,"KA":0},
        {"name":"Karkotaka",               "VP":0,"VA":1,"PP":1,"PA":0,"KP":1,"KA":0},
        {"name":"Lashuna (Garlic)",         "VP":1,"VA":0,"PP":0,"PA":1,"KP":1,"KA":0},
        {"name":"Mulaka (Radish)",          "VP":1,"VA":0,"PP":1,"PA":0,"KP":1,"KA":0},
        {"name":"Methika (Fenugreek)",      "VP":1,"VA":0,"PP":0,"PA":1,"KP":1,"KA":0},
        {"name":"Patola (Snake Gourd)",     "VP":1,"VA":0,"PP":1,"PA":0,"KP":1,"KA":0},
        {"name":"Phalandu (Onion)",         "VP":1,"VA":0,"PP":1,"PA":0,"KP":0,"KA":1},
        {"name":"Palakya (Spinach)",        "VP":0,"VA":1,"PP":1,"PA":0,"KP":1,"KA":0},
        {"name":"Patra",                    "VP":1,"VA":0,"PP":0,"PA":0,"KP":1,"KA":0},
        {"name":"Potaki",                   "VP":1,"VA":0,"PP":1,"PA":0,"KP":0,"KA":1},
        {"name":"Tanduliyaka (Amaranth)",   "VP":0,"VA":0,"PP":1,"PA":0,"KP":1,"KA":0},
        {"name":"Trapusha (Cucumber/Gourd)","VP":0,"VA":0,"PP":1,"PA":0,"KP":0,"KA":0},
        {"name":"Twak (Cinnamon)",          "VP":1,"VA":0,"PP":0,"PA":0,"KP":1,"KA":0},
        {"name":"Upakunchika",              "VP":1,"VA":0,"PP":0,"PA":1,"KP":1,"KA":0},
        {"name":"Vartaka (Brinjal)",        "VP":1,"VA":0,"PP":0,"PA":0,"KP":1,"KA":0},
        {"name":"Vastuka",                  "VP":1,"VA":0,"PP":1,"PA":0,"KP":1,"KA":0},
        {"name":"Varahi",                   "VP":1,"VA":0,"PP":0,"PA":1,"KP":1,"KA":0},
    ],
    "Mamsa (Meat)": [
        {"name":"Aja (Goat)",               "VP":1,"VA":0,"PP":1,"PA":0,"KP":1,"KA":0},
        {"name":"Avi (Sheep)",              "VP":0,"VA":0,"PP":0,"PA":1,"KP":0,"KA":1},
        {"name":"Kukkuta (Chicken)",        "VP":1,"VA":0,"PP":0,"PA":0,"KP":0,"KA":1},
        {"name":"Varaha (Pork)",            "VP":1,"VA":0,"PP":0,"PA":1,"KP":0,"KA":1},
        {"name":"Shasha (Rabbit)",          "VP":0,"VA":1,"PP":1,"PA":0,"KP":0,"KA":0},
        {"name":"Kapota (Pigeon)",          "VP":1,"VA":0,"PP":0,"PA":0,"KP":0,"KA":0},
        {"name":"Matsya (Fish)",            "VP":1,"VA":0,"PP":0,"PA":1,"KP":0,"KA":1},
        {"name":"Anupa Mamsa (Water animals)","VP":0,"VA":0,"PP":0,"PA":0,"KP":0,"KA":1},
        {"name":"Jangala Mamsa (Forest animals)","VP":0,"VA":1,"PP":1,"PA":0,"KP":1,"KA":0},
        {"name":"Anda (Eggs)",              "VP":1,"VA":0,"PP":0,"PA":0,"KP":0,"KA":0},
    ],
    "Dugdha (Dairy)": [
        {"name":"Go Ksheera (Cow Milk)",      "VP":1,"VA":0,"PP":1,"PA":0,"KP":0,"KA":0},
        {"name":"Mahisha Ksheera (Buffalo Milk)","VP":0,"VA":1,"PP":0,"PA":0,"KP":0,"KA":1},
        {"name":"Aja Ksheera (Goat Milk)",    "VP":1,"VA":0,"PP":1,"PA":0,"KP":1,"KA":0},
        {"name":"Avi Ksheera (Sheep Milk)",   "VP":0,"VA":0,"PP":0,"PA":1,"KP":0,"KA":1},
        {"name":"Ustra Ksheera (Camel Milk)", "VP":1,"VA":0,"PP":0,"PA":0,"KP":1,"KA":0},
        {"name":"Dadhi (Yogurt / Curd)",      "VP":1,"VA":0,"PP":0,"PA":1,"KP":0,"KA":1},
        {"name":"Takra (Buttermilk)",         "VP":1,"VA":0,"PP":0,"PA":0,"KP":1,"KA":0},
        {"name":"Go Ghrita (Cow Ghee)",       "VP":1,"VA":0,"PP":1,"PA":0,"KP":1,"KA":0},
        {"name":"Mahisha Ghrita (Buffalo Ghee)","VP":1,"VA":0,"PP":1,"PA":0,"KP":0,"KA":1},
        {"name":"Purana Ghrita (Old Ghee)",   "VP":1,"VA":0,"PP":1,"PA":0,"KP":1,"KA":0},
    ],
    "Taila (Oils)": [
        {"name":"Tila Taila (Sesame Oil)",    "VP":1,"VA":0,"PP":0,"PA":1,"KP":0,"KA":1},
        {"name":"Sarshapa Taila (Mustard Oil)","VP":1,"VA":0,"PP":0,"PA":1,"KP":1,"KA":0},
        {"name":"Eranda Taila (Castor Oil)",  "VP":1,"VA":0,"PP":0,"PA":0,"KP":0,"KA":1},
        {"name":"Atasi Taila (Linseed Oil)",  "VP":1,"VA":0,"PP":0,"PA":1,"KP":0,"KA":1},
        {"name":"Kusumba Taila (Safflower Oil)","VP":0,"VA":1,"PP":0,"PA":1,"KP":0,"KA":1},
    ],
    "Madhu & Ikshu (Sweeteners)": [
        {"name":"Madhu (Honey)",        "VP":0,"VA":1,"PP":1,"PA":0,"KP":1,"KA":0},
        {"name":"Ikshu (Sugarcane)",    "VP":1,"VA":0,"PP":1,"PA":0,"KP":0,"KA":1},
        {"name":"Sharkara (Sugar)",     "VP":1,"VA":0,"PP":1,"PA":0,"KP":0,"KA":0},
        {"name":"Guda (Jaggery)",       "VP":1,"VA":0,"PP":0,"PA":0,"KP":0,"KA":1},
    ],
    "Phala (Fruits)": [
        {"name":"Draksha (Grapes)",         "VP":1,"VA":0,"PP":1,"PA":0,"KP":0,"KA":0},
        {"name":"Kadali (Banana)",          "VP":0,"VA":0,"PP":1,"PA":0,"KP":0,"KA":1},
        {"name":"Dadima (Pomegranate)",     "VP":1,"VA":0,"PP":1,"PA":0,"KP":1,"KA":0},
        {"name":"Kola (Jujube)",            "VP":1,"VA":0,"PP":0,"PA":1,"KP":0,"KA":1},
        {"name":"Amra Apakwa (Raw Mango)",  "VP":0,"VA":1,"PP":0,"PA":1,"KP":0,"KA":0},
        {"name":"Amra Pakwa (Ripe Mango)",  "VP":1,"VA":0,"PP":0,"PA":0,"KP":0,"KA":1},
        {"name":"Panasa (Jackfruit)",       "VP":1,"VA":0,"PP":1,"PA":0,"KP":0,"KA":1},
        {"name":"Lakucha",                  "VP":0,"VA":1,"PP":0,"PA":1,"KP":0,"KA":1},
        {"name":"Guvaka (Areca Nut)",       "VP":0,"VA":0,"PP":1,"PA":0,"KP":1,"KA":0},
        {"name":"Tala (Palm Fruit)",        "VP":0,"VA":0,"PP":0,"PA":1,"KP":0,"KA":1},
        {"name":"Khajura (Dates)",          "VP":1,"VA":0,"PP":0,"PA":0,"KP":1,"KA":0},
        {"name":"Bijapura (Citron)",        "VP":1,"VA":0,"PP":0,"PA":0,"KP":1,"KA":0},
        {"name":"Jambira (Lime/Lemon)",     "VP":1,"VA":0,"PP":0,"PA":0,"KP":1,"KA":0},
    ],
}

# ══════════════════════════════════════════════════════════════════════════════
#  SESSION STATE
# ══════════════════════════════════════════════════════════════════════════════
for k,v in [("responses",{}),("show_results",False),("profile",{}),
            ("research_saved",False),
            ("dietary_pref","Lacto-Vegetarian (plant + milk products)"),
            ("meat_freq",3),("state","Karnataka"),("district","Bengaluru Urban"),
            ("desha","Sadharana"),("conflict_overrides",set()),
            ("ai_prompt",None),("ai_response","")]:
    if k not in st.session_state: st.session_state[k] = v

# ══════════════════════════════════════════════════════════════════════════════
#  UTILITY FUNCTIONS  — v4.0 additions
# ══════════════════════════════════════════════════════════════════════════════
def check_mandatory_answered():
    """Returns list of mandatory question IDs not yet answered."""
    missing = []
    for qid in sorted(MANDATORY_QS):
        q = next((x for x in QUESTIONS if x["id"]==qid), None)
        if q is None: continue
        r = st.session_state.responses.get(qid)
        if q["type"]=="single" and not isinstance(r, int):
            missing.append(qid)
        elif q["type"]=="multi" and not r:
            missing.append(qid)
    return missing

def append_research_row(profile, responses, trait_pct, quest_op, anthro_op, final_op, pname):
    """Appends one participant row to research_data.csv (creates file if needed)."""
    import csv, os
    fname = "research_data.csv"
    # Build header list once
    q_hdrs = [f"Q{q['id']}_ans" for q in QUESTIONS]
    base_hdrs = ["timestamp","participant_name","age","gender",
                 "height_cm","weight_kg","waist_cm","hip_cm",
                 "bmi","bmi_category","bmr_kcal","fat_pct","specific_bmr","whr"]
    trait_hdrs = []
    trait_abbr = {"Physical":"Phys","Physiological":"Phyio","Psychological":"Psych","Behavioral":"Behav"}
    for t in TRAITS:
        for d in ["V","P","K"]:
            trait_hdrs.append(f"{trait_abbr[t]}_{d}_pct")
    score_hdrs = ["Quest_V%","Quest_P%","Quest_K%",
                  "Anthro_V%","Anthro_P%","Anthro_K%",
                  "Final_V%","Final_P%","Final_K%","Prakriti"]
    all_hdrs = base_hdrs + q_hdrs + trait_hdrs + score_hdrs

    write_header = not os.path.exists(fname) or os.path.getsize(fname) == 0
    with open(fname, "a", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        if write_header:
            w.writerow(all_hdrs)
        # Build row
        from datetime import datetime
        row = [
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            profile.get("name",""), profile.get("age",""), profile.get("gender",""),
            profile.get("height_cm",""), profile.get("weight_kg",""),
            profile.get("waist_cm",""), profile.get("hip_cm",""),
            profile.get("bmi",""), profile.get("bmi_category",""),
            profile.get("bmr",""), profile.get("fat_pct",""),
            profile.get("specific_bmr",""), profile.get("whr",""),
        ]
        for q in QUESTIONS:
            r = responses.get(q["id"])
            if q["type"]=="single":
                opts = q["options"]
                row.append(opts[r]["text"] if isinstance(r,int) and r < len(opts) else "")
            else:
                opts = q["options"]
                selected = [opts[i]["text"] for i in sorted(r or []) if i < len(opts)]
                row.append(" | ".join(selected))
        for t in TRAITS:
            p = trait_pct[t]
            row += [p["V"], p["P"], p["K"]]
        row += [quest_op["V"], quest_op["P"], quest_op["K"],
                anthro_op["V"], anthro_op["P"], anthro_op["K"],
                final_op["V"], final_op["P"], final_op["K"], pname]
        w.writerow(row)

# ── Ahara tab display ─────────────────────────────────────────────────────────
def generate_combined_pdf(profile, trait_pct, quest_op, anthro_op,
                          final_op, pname, picon, pcolor_hex, ai_response):
    """
    Generate a two-part combined PDF:
    Part A — e-Prakruti Assessment results (calls existing generate_pdf_report)
    Part B — AI-generated Ahara & Vihara plan (parsed and styled from pasted text)
    """
    from io import BytesIO
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable, PageBreak
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.units import mm
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_LEFT, TA_CENTER
    from reportlab.lib.colors import HexColor as RLHexColor
    from datetime import date

    buf = BytesIO()
    W   = A4[0] - 28*mm
    doc = SimpleDocTemplate(buf, pagesize=A4,
                             leftMargin=14*mm, rightMargin=14*mm,
                             topMargin=14*mm, bottomMargin=14*mm)

    # All colour constants needed in this function
    C_DARK    = RLHexColor("#3d1a06")
    C_GOLD    = RLHexColor("#d4a017")
    C_GREEN   = RLHexColor("#0d5c30")
    C_LGREY   = RLHexColor("#f5f5f5")
    C_MGREY   = RLHexColor("#cccccc")
    C_CREAM   = RLHexColor("#fdf5e6")
    C_VATA    = RLHexColor("#1a4f96")
    C_PITTA   = RLHexColor("#9e2a0a")
    C_KAPHA   = RLHexColor("#0d5c30")
    C_MID     = RLHexColor("#7a3210")
    C_PRAKRITI = RLHexColor(f"#{pcolor_hex.lstrip('#')}" if pcolor_hex.startswith('#') else pcolor_hex)

    base = getSampleStyleSheet()
    def ps(name, **kw):
        return ParagraphStyle(name, parent=base["Normal"], **kw)

    S = {
        "h1":   ps("h1", fontSize=14, textColor=colors.white, fontName="Helvetica-Bold",
                   spaceAfter=4, leading=18),
        "h2":   ps("h2", fontSize=11, textColor=C_DARK, fontName="Helvetica-Bold",
                   spaceAfter=3, leading=14),
        "body": ps("body", fontSize=9, leading=13, spaceAfter=4),
        "note": ps("note", fontSize=8, textColor=colors.grey, leading=11, fontStyle="italic"),
        "disc": ps("disc", fontSize=7.5, textColor=colors.grey, leading=10),
    }

    story = []
    today = date.today().strftime("%d / %m / %Y")

    # ── PART A HEADER ─────────────────────────────────────────────────────────
    from reportlab.platypus import Table, TableStyle
    from reportlab.lib.units import mm

    hdr = Table([[
        Paragraph("🌿 e-Prakruti Complete Health Report", S["h1"]),
        Paragraph(f"Dr. Prasanna Kulkarni  |  MD Ayurveda · MS Data Science", S["note"]),
        Paragraph("Sri Kalabyraveshwara Swamy Ayurvedic Medical College, Bangalore", S["note"]),
        Paragraph(f"Date: {today}", S["note"]),
    ]], colWidths=[W])
    hdr.setStyle(TableStyle([
        ("BACKGROUND",(0,0),(-1,-1), C_DARK),
        ("LINEABOVE",(0,0),(-1,0), 4, C_GOLD),
        ("TOPPADDING",(0,0),(-1,-1), 8),
        ("BOTTOMPADDING",(0,0),(-1,-1), 10),
        ("LEFTPADDING",(0,0),(-1,-1), 12),
    ]))
    story += [hdr, Spacer(1, 4*mm)]

    name = profile.get("name","")
    story.append(Paragraph(
        f"<b>Health Seeker:</b> {name} &nbsp;|&nbsp; "
        f"<b>Age:</b> {profile.get('age','—')} yrs &nbsp;|&nbsp; "
        f"<b>Gender:</b> {profile.get('gender','—')} &nbsp;|&nbsp; "
        f"<b>Prakriti:</b> {picon} {pname}", S["body"]))
    story.append(Spacer(1, 3*mm))

    # ── PART A: Assessment summary (scores only — keep combined PDF lighter) ──
    def sec(title, color):
        t = Table([[Paragraph(title, S["h1"])]], colWidths=[W])
        t.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,-1),color),
                                ("TOPPADDING",(0,0),(-1,-1),5),
                                ("BOTTOMPADDING",(0,0),(-1,-1),5),
                                ("LEFTPADDING",(0,0),(-1,-1),10)]))
        return t

    story.append(sec("📊 Part A — Prakriti Assessment Summary", C_DARK))
    story.append(Spacer(1,3*mm))

    # Score table
    dmap = {"V":"Vata","P":"Pitta","K":"Kapha"}
    TRAITS_LIST = ["Physical","Physiological","Psychological","Behavioral"]
    T_ABR       = {"Physical":"🏃 Physical","Physiological":"⚙️ Physiological",
                   "Psychological":"🧠 Psychological","Behavioral":"🌿 Behavioral"}
    score_rows = [["Trait","Vata %","Pitta %","Kapha %","Dominant"]]
    for t in TRAITS_LIST:
        p = trait_pct[t]
        score_rows.append([T_ABR[t], f"{p['V']}%", f"{p['P']}%", f"{p['K']}%",
                           dmap[max(p,key=p.get)]])
    score_rows.append(["📝 Questionnaire (80%)",
                       f"{quest_op['V']}%",f"{quest_op['P']}%",f"{quest_op['K']}%",
                       dmap[max(quest_op,key=quest_op.get)]])
    score_rows.append(["📏 Anthropometric (20%)",
                       f"{anthro_op['V']}%",f"{anthro_op['P']}%",f"{anthro_op['K']}%",
                       dmap[max(anthro_op,key=anthro_op.get)]])
    score_rows.append([f"🌿 FINAL PRAKRITI",
                       f"{final_op['V']}%",f"{final_op['P']}%",f"{final_op['K']}%",
                       dmap[max(final_op,key=final_op.get)]])

    sc_t = Table([[Paragraph(c, ParagraphStyle("th", fontName="Helvetica-Bold",
                  fontSize=8, textColor=colors.white)) for c in score_rows[0]]],
                 colWidths=[W*0.36,W*0.13,W*0.13,W*0.13,W*0.25])
    sc_rows_fmt = [score_rows[0]]
    for r in score_rows[1:]:
        sc_rows_fmt.append([Paragraph(c, ParagraphStyle("tc",fontSize=8,leading=11))
                            for c in r])
    sc_full = Table(sc_rows_fmt,
                    colWidths=[W*0.36,W*0.13,W*0.13,W*0.13,W*0.25],
                    spaceBefore=2*mm)
    sc_full.setStyle(TableStyle([
        ("BACKGROUND",(0,0),(-1,0), RLHexColor("#7a3210")),
        ("TEXTCOLOR",(0,0),(-1,0), colors.white),
        ("FONTNAME",(0,0),(-1,0),"Helvetica-Bold"),
        ("FONTSIZE",(0,0),(-1,-1),8),
        ("ALIGN",(1,0),(-1,-1),"CENTER"),
        ("ROWBACKGROUNDS",(0,1),(-1,-4),[RLHexColor("#fdf5e6"),colors.white]),
        ("BACKGROUND",(0,-1),(-1,-1), RLHexColor("#e8f4e8")),
        ("FONTNAME",(0,-1),(-1,-1),"Helvetica-Bold"),
        ("TOPPADDING",(0,0),(-1,-1),3),("BOTTOMPADDING",(0,0),(-1,-1),3),
        ("LEFTPADDING",(0,0),(-1,-1),5),
        ("BOX",(0,0),(-1,-1),0.5,RLHexColor("#cccccc")),
        ("INNERGRID",(0,0),(-1,-1),0.3,RLHexColor("#cccccc")),
    ]))
    story += [sc_full, Spacer(1,4*mm)]

    # ── DISEASE PRONENESS (both Doshas) in combined PDF ───────────────────────
    # Derive dominant and secondary Dosha names
    _pairs = sorted([("Vata",final_op["V"]),("Pitta",final_op["P"]),
                     ("Kapha",final_op["K"])], key=lambda x:-x[1])
    _dname1 = _pairs[0][0]
    _dname2 = _pairs[1][0]

    story.append(sec(f"⚕️ Health Tendency Profile — {pname}", C_PITTA))
    story.append(Spacer(1,2*mm))
    story.append(Paragraph(
        "<i>Conditions this constitution is susceptible to — not certainties. "
        "Consistent dietary and lifestyle adherence significantly reduces risk. "
        "This information is for awareness and prevention only.</i>",
        ParagraphStyle("comb_note", fontSize=7.5, textColor=colors.grey,
                       fontStyle="italic", leading=10)))
    story.append(Spacer(1,2*mm))

    _d1_dis = DISEASE_PRONE_PDF.get(_dname1, [])
    _d2_dis = DISEASE_PRONE_PDF.get(_dname2, [])
    _max_r  = max(len(_d1_dis), len(_d2_dis), 1)

    _dp_hdr = [
        Paragraph(f"<b>{_dname1} Prakriti Susceptibility</b>",
                  ParagraphStyle("dph", fontName="Helvetica-Bold", fontSize=8,
                                 textColor=colors.white)),
        Paragraph(f"<b>{_dname2} Prakriti Susceptibility</b>",
                  ParagraphStyle("dph2", fontName="Helvetica-Bold", fontSize=8,
                                 textColor=colors.white)),
    ]
    _dp_rows = [_dp_hdr]
    for _i in range(_max_r):
        _r1 = f"• {_d1_dis[_i]}" if _i < len(_d1_dis) else ""
        _r2 = f"• {_d2_dis[_i]}" if _i < len(_d2_dis) else ""
        _dp_rows.append([
            Paragraph(_r1, ParagraphStyle("dpb", fontSize=8, leading=11)),
            Paragraph(_r2, ParagraphStyle("dpb2", fontSize=8, leading=11)),
        ])
    _dp_t = Table(_dp_rows, colWidths=[W/2, W/2])
    _dp_t.setStyle(TableStyle([
        ("BACKGROUND",(0,0),(-1,0), C_PITTA),
        ("BACKGROUND",(0,1),(-1,-1), RLHexColor("#fdf0ef")),
        ("FONTSIZE",(0,0),(-1,-1),8),
        ("TOPPADDING",(0,0),(-1,-1),3), ("BOTTOMPADDING",(0,0),(-1,-1),3),
        ("LEFTPADDING",(0,0),(-1,-1),5), ("VALIGN",(0,0),(-1,-1),"TOP"),
        ("BOX",(0,0),(-1,-1),0.4,C_MGREY), ("INNERGRID",(0,0),(-1,-1),0.2,C_MGREY),
    ]))
    story += [_dp_t, Spacer(1,4*mm)]

    # ── PAGE BREAK to Part B ───────────────────────────────────────────────────
    story.append(PageBreak())

    # ── PART B HEADER ────────────────────────────────────────────────────────
    story.append(sec("🥗 Part B — Personalised Ahara & Vihara Plan", C_GREEN))
    story.append(Spacer(1,3*mm))
    story.append(Paragraph(
        f"<i>AI-generated dietary and lifestyle plan for <b>{name}</b> · "
        f"Prakriti: {pname} · Generated via e-PathyaGPT by PraKul</i>", S["note"]))
    story.append(Paragraph(
        "The following plan was generated by an AI assistant using the structured Prakriti "
        "assessment prompt from e-Prakruti v6.0. Validate with your Vaidya before clinical application.",
        S["note"]))
    story.append(Spacer(1,4*mm))

    # ── Parse and style the AI response ──────────────────────────────────────
    import re

    def _md_to_rl(text):
        """Convert markdown bold/italic to ReportLab XML tags, strip stray asterisks."""
        t = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', text)
        t = re.sub(r'\*(.+?)\*',     r'<i>\1</i>', t)
        # Remove any remaining stray asterisks that weren't part of valid markdown
        t = re.sub(r'\*+', '', t)
        return t

    lines_ai = ai_response.strip().splitlines()
    section_pat = re.compile(
        r'^(\d+[\.\)]\s+[A-Z]|[A-Z][A-Z\s\(\)&—–\-]{6,}$|#+\s+|={3,}|-{3,})')

    for raw_line in lines_ai:
        line = raw_line.strip()
        if not line:
            story.append(Spacer(1, 2*mm))
            continue
        # Detect section header
        if (section_pat.match(line) or
            (line.isupper() and len(line) > 4) or
            (line.startswith(("1.","2.","3.","4.","5.","6.","7.","8.","9.")) and
             len(line) > 6 and line[2:].strip()[:1].isupper())):
            clean = re.sub(r'^[#=\-\*\s]+|[#=\-\*\s]+$', '', line).strip()
            clean = _md_to_rl(clean)
            if clean:
                story.append(Spacer(1,3*mm))
                story.append(Paragraph(clean,
                    ParagraphStyle("ah2", fontName="Helvetica-Bold", fontSize=10,
                                   textColor=C_GREEN, leading=14,
                                   borderPad=3, spaceAfter=2)))
        elif line.startswith(("- ","• ","* ","· ")):
            bullet_text = _md_to_rl(line[2:].strip())
            story.append(Paragraph(
                f"&nbsp;&nbsp;&nbsp;• {bullet_text}",
                ParagraphStyle("abul", fontSize=8.5, leading=12, spaceAfter=2)))
        elif re.match(r'^\d+[\.\)]\s', line):
            story.append(Paragraph(_md_to_rl(line),
                ParagraphStyle("anum", fontSize=8.5, leading=12, spaceAfter=2,
                               leftIndent=10)))
        elif line.startswith("═") or line.startswith("─") or line.startswith("="):
            story.append(HRFlowable(width=W, thickness=0.5,
                                     color=RLHexColor("#cccccc")))
        else:
            story.append(Paragraph(_md_to_rl(line),
                ParagraphStyle("abody", fontSize=8.5, leading=13, spaceAfter=2)))

    story.append(Spacer(1,4*mm))
    story.append(HRFlowable(width=W, thickness=0.5, color=C_GOLD))
    story.append(Spacer(1,2*mm))
    story.append(Paragraph(
        "<b>DISCLAIMER:</b> This combined report contains: (A) an objective Prakriti assessment "
        "based on validated questionnaire responses and anthropometric measurements, and "
        "(B) an AI-generated dietary plan based on classical Ayurvedic principles. "
        "Part B is advisory and should be validated by a qualified Vaidya before clinical application. "
        "This report is not a substitute for professional medical advice.",
        S["disc"]))
    story.append(Spacer(1,2*mm))
    story.append(Paragraph(
        f"Generated by: e-Prakruti v6.0 · SKAMC, Bangalore · "
        f"Dr. Prasanna Kulkarni MD (Ayu), MS Data Science · Date: {today}",
        S["disc"]))

    doc.build(story)
    buf.seek(0)
    return buf.read()


def show_ahara_tab(final_op, pname, pcolor):
    """Render Pathya-Apathya food guide based on final Prakriti scores,
    filtered by dietary preference."""
    dom   = max(final_op, key=final_op.get)
    sec   = sorted(final_op, key=final_op.get)[-2]
    pkeys = {"V":("VP","VA"), "P":("PP","PA"), "K":("KP","KA")}
    dnames = {"V":"Vata","P":"Pitta","K":"Kapha"}
    dcolors= {"V":"#1a4f96","P":"#9e2a0a","K":"#0d5c30"}
    if final_op[sec] >= 30:
        doshas = [dom, sec]
    else:
        doshas = [dom]

    # Point 7 — determine which categories to show based on dietary pref
    dietary_pref = st.session_state.get("dietary_pref","Lacto-Vegetarian (plant + milk products)")
    _skip_cats = set()
    if dietary_pref == "Vegan (plant-based only)":
        _skip_cats = {"Mamsa (Meat)", "Dugdha (Dairy)"}
    elif dietary_pref in ("Lacto-Vegetarian (plant + milk products)", "Ovo-Vegetarian (plant + eggs)"):
        _skip_cats = {"Mamsa (Meat)"}
    # For Ovo-Vegetarian: Anda (eggs) item kept — handled per-item below
    _is_ovo = dietary_pref == "Ovo-Vegetarian (plant + eggs)"

    st.markdown(
        f'<div style="background:{pcolor}18;border-left:5px solid {pcolor};'
        f'border-radius:10px;padding:14px 20px;margin-bottom:16px;">'
        f'<b style="color:{pcolor};font-size:1.05em;">🥗 Ahara Guide for {pname}</b><br>'
        f'<span style="font-size:.88em;color:#555;">Based on Charaka Sutrasthana 26/43 · '
        f'Ashtanga Hridaya Sutrasthana 10/17. Pathya = Beneficial · Apathya = Avoid.</span>'
        f'</div>', unsafe_allow_html=True)

    if len(doshas) == 2:
        st.info(f"Dual Prakriti detected ({dnames[doshas[0]]}–{dnames[doshas[1]]}). "
                f"Items shown for both Doshas. Items marked ⚠️ are Apathya for "
                f"at least one Dosha — use with caution.")

    if _skip_cats:
        st.caption(f"🌱 Dietary preference: **{dietary_pref}** — "
                   f"{', '.join(_skip_cats)} categories hidden.")

    # Per-dosha legend
    for d in doshas:
        col = dcolors[d]
        st.markdown(
            f'<span style="display:inline-block;background:{col};color:white;'
            f'border-radius:5px;padding:3px 10px;font-size:.8em;margin:3px 4px 8px;">'
            f'{dnames[d]} Pathya ✅</span>'
            f'<span style="display:inline-block;background:#c0392b;color:white;'
            f'border-radius:5px;padding:3px 10px;font-size:.8em;margin:3px 4px 8px;">'
            f'{dnames[d]} Apathya ❌</span>', unsafe_allow_html=True)

    for cat, items in AHARA_DATA.items():
        # Skip entire category if dietary preference excludes it
        if cat in _skip_cats:
            continue
        # Filter items within Mamsa for Ovo — keep only Anda (eggs)
        if cat == "Mamsa (Meat)" and _is_ovo:
            items = [i for i in items if "Anda" in i["name"] or "Egg" in i["name"]]
            if not items:
                continue

        with st.expander(f"📦 {cat} ({len(items)} items)", expanded=False):
            favour, moderate, avoid = [], [], []
            for item in items:
                is_pathya  = any(item[pkeys[d][0]] for d in doshas)
                is_apathya = any(item[pkeys[d][1]] for d in doshas)
                name = item["name"]
                dosha_badges = ""
                for d in doshas:
                    if item[pkeys[d][0]]:
                        dosha_badges += f'<span style="color:{dcolors[d]};font-weight:700;">{dnames[d][0]}</span>✅ '
                    if item[pkeys[d][1]]:
                        dosha_badges += f'<span style="color:#c0392b;font-weight:700;">{dnames[d][0]}</span>❌ '
                entry = f'<span style="font-size:.9em;">{name}</span> <span style="font-size:.78em;">{dosha_badges}</span>'
                if is_pathya and not is_apathya:
                    favour.append(entry)
                elif is_apathya and not is_pathya:
                    avoid.append(entry)
                else:
                    moderate.append(entry)

            c1, c2, c3 = st.columns(3)
            with c1:
                st.markdown("##### 🟢 Favour")
                if favour:
                    for e in favour:
                        st.markdown(f"• {e}", unsafe_allow_html=True)
                else:
                    st.caption("—")
            with c2:
                st.markdown("##### 🟡 Moderate / Neutral")
                if moderate:
                    for e in moderate:
                        st.markdown(f"• {e}", unsafe_allow_html=True)
                else:
                    st.caption("—")
            with c3:
                st.markdown("##### 🔴 Avoid")
                if avoid:
                    for e in avoid:
                        st.markdown(f"• {e}", unsafe_allow_html=True)
                else:
                    st.caption("—")

    st.markdown("---")
    st.caption("*Items marked Moderate may suit specific conditions — consult a qualified Vaidya.*")

# ══════════════════════════════════════════════════════════════════════════════
#  INDIA GEOGRAPHY — States → Districts → Desha (Ayurvedic classification)
#  Desha types: Anupa · Jangala · Sadharana · Sadharana-Anupa · Sadharana-Jangala
#  Ref: Charaka Sutrasthana 27/16-17; Ashtanga Hridaya Sutrasthana 1/7
# ══════════════════════════════════════════════════════════════════════════════
# Structure: state → {"default": desha, "districts": {dist: desha or None=use default}}
INDIA_GEO = {
    "Andhra Pradesh": {
        "default": "Sadharana",
        "districts": {
            "Srikakulam":"Anupa","Vizianagaram":"Sadharana-Anupa",
            "Visakhapatnam":"Anupa","East Godavari":"Anupa",
            "West Godavari":"Anupa","Krishna":"Anupa","Guntur":"Sadharana-Anupa",
            "Prakasam":"Sadharana","Nellore":"Sadharana-Anupa",
            "Kurnool":"Sadharana-Jangala","Kadapa":"Sadharana-Jangala",
            "Anantapur":"Sadharana-Jangala","Chittoor":"Sadharana",
        }},
    "Arunachal Pradesh": {"default":"Sadharana-Anupa","districts":{
        "Anjaw":"Anupa","Changlang":"Anupa","Dibang Valley":"Anupa",
        "East Kameng":"Sadharana-Anupa","East Siang":"Sadharana-Anupa",
        "Kurung Kumey":"Sadharana","Lohit":"Sadharana-Anupa",
        "Lower Dibang Valley":"Anupa","Lower Siang":"Sadharana-Anupa",
        "Papum Pare":"Sadharana","Tawang":"Sadharana","Tirap":"Anupa",
        "Upper Siang":"Sadharana","West Kameng":"Sadharana","West Siang":"Sadharana",
    }},
    "Assam": {"default":"Anupa","districts":{
        "Barpeta":"Anupa","Bongaigaon":"Anupa","Cachar":"Sadharana-Anupa",
        "Dhubri":"Anupa","Dibrugarh":"Sadharana-Anupa","Goalpara":"Anupa",
        "Golaghat":"Sadharana-Anupa","Hailakandi":"Sadharana-Anupa",
        "Jorhat":"Sadharana-Anupa","Kamrup":"Anupa","Kamrup Metro":"Anupa",
        "Karbi Anglong":"Sadharana","Karimganj":"Sadharana-Anupa",
        "Kokrajhar":"Anupa","Lakhimpur":"Anupa","Morigaon":"Anupa",
        "Nagaon":"Anupa","Nalbari":"Anupa","Sivasagar":"Sadharana-Anupa",
        "Sonitpur":"Anupa","Tinsukia":"Sadharana-Anupa","Udalguri":"Anupa",
    }},
    "Bihar": {"default":"Sadharana","districts":{
        "Araria":"Sadharana-Anupa","Arwal":"Sadharana","Aurangabad":"Sadharana",
        "Banka":"Sadharana","Begusarai":"Sadharana-Anupa","Bhagalpur":"Sadharana-Anupa",
        "Bhojpur":"Sadharana","Buxar":"Sadharana","Darbhanga":"Sadharana-Anupa",
        "East Champaran":"Sadharana-Anupa","Gaya":"Sadharana",
        "Gopalganj":"Sadharana-Anupa","Jamui":"Sadharana","Jehanabad":"Sadharana",
        "Kaimur":"Sadharana","Katihar":"Sadharana-Anupa","Khagaria":"Sadharana-Anupa",
        "Kishanganj":"Sadharana-Anupa","Lakhisarai":"Sadharana",
        "Madhepura":"Sadharana-Anupa","Madhubani":"Sadharana-Anupa",
        "Munger":"Sadharana","Muzaffarpur":"Sadharana-Anupa","Nalanda":"Sadharana",
        "Nawada":"Sadharana","Patna":"Sadharana","Purnia":"Sadharana-Anupa",
        "Rohtas":"Sadharana","Saharsa":"Sadharana-Anupa","Samastipur":"Sadharana-Anupa",
        "Saran":"Sadharana-Anupa","Sheikhpura":"Sadharana","Sheohar":"Sadharana-Anupa",
        "Sitamarhi":"Sadharana-Anupa","Siwan":"Sadharana-Anupa",
        "Supaul":"Sadharana-Anupa","Vaishali":"Sadharana-Anupa",
        "West Champaran":"Sadharana-Anupa",
    }},
    "Chhattisgarh": {"default":"Sadharana","districts":{
        "Bastar":"Sadharana-Anupa","Bijapur":"Sadharana-Anupa",
        "Bilaspur":"Sadharana","Dantewada":"Sadharana-Anupa",
        "Dhamtari":"Sadharana","Durg":"Sadharana","Gariaband":"Sadharana-Anupa",
        "Janjgir-Champa":"Sadharana","Jashpur":"Sadharana-Anupa",
        "Kabirdham":"Sadharana","Kanker":"Sadharana-Anupa",
        "Kondagaon":"Sadharana-Anupa","Korba":"Sadharana-Jangala",
        "Koriya":"Sadharana","Mahasamund":"Sadharana","Mungeli":"Sadharana",
        "Narayanpur":"Sadharana-Anupa","Raigarh":"Sadharana","Raipur":"Sadharana",
        "Rajnandgaon":"Sadharana","Sukma":"Sadharana-Anupa","Surajpur":"Sadharana",
        "Surguja":"Sadharana",
    }},
    "Goa": {"default":"Anupa","districts":{"North Goa":"Anupa","South Goa":"Anupa"}},
    "Gujarat": {
        "default": "Sadharana-Jangala",
        "districts": {
            "Ahmedabad":"Sadharana","Amreli":"Sadharana-Jangala",
            "Anand":"Sadharana","Aravalli":"Sadharana",
            "Banaskantha":"Jangala","Bharuch":"Sadharana","Bhavnagar":"Sadharana-Jangala",
            "Botad":"Sadharana-Jangala","Chhota Udaipur":"Sadharana",
            "Dahod":"Sadharana","Dang":"Sadharana-Anupa",
            "Devbhoomi Dwarka":"Sadharana-Jangala","Gandhinagar":"Sadharana",
            "Gir Somnath":"Sadharana-Jangala","Jamnagar":"Sadharana-Jangala",
            "Junagadh":"Sadharana-Jangala","Kheda":"Sadharana",
            "Kutch":"Jangala","Mahisagar":"Sadharana","Mehsana":"Sadharana",
            "Morbi":"Sadharana-Jangala","Narmada":"Sadharana-Anupa",
            "Navsari":"Sadharana-Anupa","Panchmahal":"Sadharana",
            "Patan":"Jangala","Porbandar":"Sadharana-Jangala",
            "Rajkot":"Sadharana-Jangala","Sabarkantha":"Sadharana",
            "Surat":"Sadharana-Anupa","Surendranagar":"Jangala",
            "Tapi":"Sadharana-Anupa","Vadodara":"Sadharana",
            "Valsad":"Sadharana-Anupa","Diu":"Sadharana-Jangala",
            "Dadra and Nagar Haveli":"Sadharana-Anupa",
        }},
    "Haryana": {"default":"Jangala","districts":{
        "Ambala":"Sadharana","Bhiwani":"Jangala","Charkhi Dadri":"Jangala",
        "Faridabad":"Sadharana","Fatehabad":"Jangala","Gurugram":"Sadharana",
        "Hisar":"Jangala","Jhajjar":"Jangala","Jind":"Jangala","Kaithal":"Jangala",
        "Karnal":"Sadharana","Kurukshetra":"Sadharana","Mahendragarh":"Jangala",
        "Nuh":"Jangala","Palwal":"Jangala","Panchkula":"Sadharana",
        "Panipat":"Sadharana","Rewari":"Jangala","Rohtak":"Jangala",
        "Sirsa":"Jangala","Sonipat":"Sadharana","Yamunanagar":"Sadharana",
    }},
    "Himachal Pradesh": {"default":"Sadharana","districts":{
        "Bilaspur":"Sadharana","Chamba":"Sadharana-Anupa","Hamirpur":"Sadharana",
        "Kangra":"Sadharana-Anupa","Kinnaur":"Sadharana","Kullu":"Sadharana-Anupa",
        "Lahaul and Spiti":"Jangala","Mandi":"Sadharana","Shimla":"Sadharana",
        "Sirmaur":"Sadharana","Solan":"Sadharana","Una":"Sadharana",
    }},
    "Jharkhand": {"default":"Sadharana","districts":{
        "Bokaro":"Sadharana","Chatra":"Sadharana","Deoghar":"Sadharana",
        "Dhanbad":"Sadharana","Dumka":"Sadharana-Anupa","East Singhbhum":"Sadharana-Anupa",
        "Garhwa":"Sadharana","Giridih":"Sadharana","Godda":"Sadharana",
        "Gumla":"Sadharana-Anupa","Hazaribagh":"Sadharana","Jamtara":"Sadharana",
        "Khunti":"Sadharana-Anupa","Koderma":"Sadharana","Latehar":"Sadharana-Anupa",
        "Lohardaga":"Sadharana","Pakur":"Sadharana-Anupa","Palamu":"Sadharana",
        "Ramgarh":"Sadharana","Ranchi":"Sadharana","Sahibganj":"Sadharana-Anupa",
        "Seraikela Kharsawan":"Sadharana","Simdega":"Sadharana-Anupa",
        "West Singhbhum":"Sadharana-Anupa",
    }},
    "Karnataka": {
        "default": "Sadharana",
        "districts": {
            # Coastal (Anupa)
            "Dakshina Kannada":"Anupa","Udupi":"Anupa",
            "Uttara Kannada":"Sadharana-Anupa",
            # Western Ghats (Sadharana-Anupa)
            "Kodagu":"Sadharana-Anupa","Chikkamagaluru":"Sadharana-Anupa",
            "Hassan":"Sadharana-Anupa","Shivamogga":"Sadharana-Anupa",
            # Deccan interior (Sadharana)
            "Bengaluru Urban":"Sadharana","Bengaluru Rural":"Sadharana",
            "Mysuru":"Sadharana","Mandya":"Sadharana","Tumakuru":"Sadharana",
            "Chamarajanagara":"Sadharana","Ramanagara":"Sadharana",
            "Kolar":"Sadharana","Chikkaballapura":"Sadharana",
            "Chitradurga":"Sadharana-Jangala","Davangere":"Sadharana",
            # Northern dry (Sadharana-Jangala)
            "Dharwad":"Sadharana","Belagavi":"Sadharana","Haveri":"Sadharana",
            "Vijayapura":"Sadharana-Jangala","Bagalkote":"Sadharana-Jangala",
            "Raichur":"Sadharana-Jangala","Ballari":"Sadharana-Jangala",
            "Koppal":"Sadharana-Jangala","Gadag":"Sadharana-Jangala",
            "Yadgir":"Sadharana-Jangala","Kalaburagi":"Sadharana-Jangala",
            "Bidar":"Sadharana",
        }},
    "Kerala": {"default":"Anupa","districts":{
        "Alappuzha":"Anupa","Ernakulam":"Anupa","Idukki":"Sadharana-Anupa",
        "Kannur":"Anupa","Kasaragod":"Anupa","Kollam":"Anupa",
        "Kottayam":"Anupa","Kozhikode":"Anupa","Malappuram":"Anupa",
        "Palakkad":"Sadharana-Anupa","Pathanamthitta":"Sadharana-Anupa",
        "Thiruvananthapuram":"Anupa","Thrissur":"Anupa","Wayanad":"Sadharana-Anupa",
    }},
    "Madhya Pradesh": {"default":"Sadharana","districts":{
        "Agar Malwa":"Sadharana","Alirajpur":"Sadharana-Anupa","Anuppur":"Sadharana-Anupa",
        "Ashoknagar":"Sadharana","Balaghat":"Sadharana-Anupa","Barwani":"Sadharana-Anupa",
        "Betul":"Sadharana-Anupa","Bhind":"Sadharana-Jangala","Bhopal":"Sadharana",
        "Burhanpur":"Sadharana-Anupa","Chhatarpur":"Sadharana-Jangala",
        "Chhindwara":"Sadharana-Anupa","Damoh":"Sadharana","Datia":"Sadharana-Jangala",
        "Dewas":"Sadharana","Dhar":"Sadharana","Dindori":"Sadharana-Anupa",
        "Guna":"Sadharana","Gwalior":"Sadharana-Jangala","Harda":"Sadharana-Anupa",
        "Hoshangabad":"Sadharana","Indore":"Sadharana","Jabalpur":"Sadharana-Anupa",
        "Jhabua":"Sadharana","Katni":"Sadharana","Khandwa":"Sadharana-Anupa",
        "Khargone":"Sadharana-Anupa","Mandla":"Sadharana-Anupa","Mandsaur":"Sadharana",
        "Morena":"Sadharana-Jangala","Narsinghpur":"Sadharana","Neemuch":"Sadharana",
        "Niwari":"Sadharana","Panna":"Sadharana-Jangala","Raisen":"Sadharana",
        "Rajgarh":"Sadharana","Ratlam":"Sadharana","Rewa":"Sadharana",
        "Sagar":"Sadharana","Satna":"Sadharana","Sehore":"Sadharana",
        "Seoni":"Sadharana-Anupa","Shahdol":"Sadharana-Anupa","Shajapur":"Sadharana",
        "Sheopur":"Sadharana-Jangala","Shivpuri":"Sadharana-Jangala",
        "Sidhi":"Sadharana","Singrauli":"Sadharana","Tikamgarh":"Sadharana-Jangala",
        "Ujjain":"Sadharana","Umaria":"Sadharana-Anupa","Vidisha":"Sadharana",
    }},
    "Maharashtra": {
        "default": "Sadharana",
        "districts": {
            # Konkan coast (Anupa)
            "Mumbai City":"Anupa","Mumbai Suburban":"Anupa","Thane":"Anupa",
            "Raigad":"Anupa","Ratnagiri":"Anupa","Sindhudurg":"Anupa",
            # Western Maharashtra (Sadharana)
            "Pune":"Sadharana","Nashik":"Sadharana","Satara":"Sadharana",
            "Sangli":"Sadharana","Kolhapur":"Sadharana-Anupa","Solapur":"Sadharana-Jangala",
            # Marathwada (drier)
            "Aurangabad":"Sadharana-Jangala","Jalna":"Sadharana-Jangala",
            "Beed":"Sadharana-Jangala","Osmanabad":"Sadharana-Jangala",
            "Latur":"Sadharana-Jangala","Nanded":"Sadharana-Jangala",
            "Hingoli":"Sadharana","Parbhani":"Sadharana-Jangala",
            # Vidarbha (semi-arid)
            "Nagpur":"Sadharana-Jangala","Wardha":"Sadharana-Jangala",
            "Yavatmal":"Sadharana-Jangala","Akola":"Sadharana-Jangala",
            "Amravati":"Sadharana-Jangala","Washim":"Sadharana-Jangala",
            "Buldhana":"Sadharana-Jangala","Chandrapur":"Sadharana-Anupa",
            "Gadchiroli":"Sadharana-Anupa","Gondia":"Sadharana-Anupa",
            "Bhandara":"Sadharana","Dhule":"Sadharana","Nandurbar":"Sadharana-Anupa",
            "Jalgaon":"Sadharana","Ahmednagar":"Sadharana",
        }},
    "Manipur": {"default":"Sadharana-Anupa","districts":{
        "Bishnupur":"Sadharana-Anupa","Chandel":"Sadharana-Anupa",
        "Churachandpur":"Sadharana-Anupa","Imphal East":"Sadharana-Anupa",
        "Imphal West":"Sadharana-Anupa","Jiribam":"Anupa","Kakching":"Sadharana-Anupa",
        "Kamjong":"Sadharana","Kangpokpi":"Sadharana","Noney":"Anupa",
        "Pherzawl":"Sadharana-Anupa","Senapati":"Sadharana-Anupa",
        "Tamenglong":"Anupa","Tengnoupal":"Sadharana-Anupa","Thoubal":"Sadharana-Anupa",
        "Ukhrul":"Sadharana",
    }},
    "Meghalaya": {"default":"Anupa","districts":{
        "East Garo Hills":"Anupa","East Jaintia Hills":"Anupa","East Khasi Hills":"Anupa",
        "North Garo Hills":"Anupa","Ri Bhoi":"Sadharana-Anupa","South Garo Hills":"Anupa",
        "South West Garo Hills":"Anupa","South West Khasi Hills":"Anupa",
        "West Garo Hills":"Anupa","West Jaintia Hills":"Anupa","West Khasi Hills":"Anupa",
    }},
    "Mizoram": {"default":"Sadharana-Anupa","districts":{
        "Aizawl":"Sadharana-Anupa","Champhai":"Sadharana-Anupa","Kolasib":"Anupa",
        "Lawngtlai":"Anupa","Lunglei":"Anupa","Mamit":"Anupa",
        "Saiha":"Sadharana-Anupa","Serchhip":"Sadharana-Anupa",
    }},
    "Nagaland": {"default":"Sadharana-Anupa","districts":{
        "Dimapur":"Sadharana-Anupa","Kiphire":"Sadharana","Kohima":"Sadharana-Anupa",
        "Longleng":"Sadharana-Anupa","Mokokchung":"Sadharana-Anupa",
        "Mon":"Sadharana-Anupa","Peren":"Sadharana-Anupa","Phek":"Sadharana-Anupa",
        "Tuensang":"Sadharana-Anupa","Wokha":"Sadharana-Anupa","Zunheboto":"Sadharana-Anupa",
    }},
    "Odisha": {
        "default": "Sadharana",
        "districts": {
            # Coastal (Anupa)
            "Balasore":"Anupa","Bhadrak":"Anupa","Cuttack":"Anupa",
            "Jagatsinghpur":"Anupa","Kendrapara":"Anupa","Khordha":"Anupa",
            "Puri":"Anupa","Ganjam":"Anupa","Gajapati":"Sadharana-Anupa",
            # Interior (Sadharana)
            "Angul":"Sadharana","Balangir":"Sadharana","Bargarh":"Sadharana",
            "Boudh":"Sadharana","Deogarh":"Sadharana","Dhenkanal":"Sadharana",
            "Jharsuguda":"Sadharana","Kalahandi":"Sadharana","Kandhamal":"Sadharana-Anupa",
            "Kendujhar":"Sadharana-Anupa","Koraput":"Sadharana-Anupa",
            "Malkangiri":"Sadharana-Anupa","Mayurbhanj":"Sadharana-Anupa",
            "Nabarangpur":"Sadharana","Nayagarh":"Sadharana","Nuapada":"Sadharana",
            "Rayagada":"Sadharana-Anupa","Sambalpur":"Sadharana",
            "Sonepur":"Sadharana","Sundargarh":"Sadharana-Anupa",
        }},
    "Punjab": {"default":"Jangala","districts":{
        "Amritsar":"Jangala","Barnala":"Jangala","Bathinda":"Jangala",
        "Faridkot":"Jangala","Fatehgarh Sahib":"Jangala","Fazilka":"Jangala",
        "Ferozepur":"Jangala","Gurdaspur":"Sadharana","Hoshiarpur":"Sadharana",
        "Jalandhar":"Jangala","Kapurthala":"Jangala","Ludhiana":"Jangala",
        "Mansa":"Jangala","Moga":"Jangala","Pathankot":"Sadharana",
        "Patiala":"Jangala","Rupnagar":"Sadharana","Sangrur":"Jangala",
        "SAS Nagar (Mohali)":"Sadharana","Shaheed Bhagat Singh Nagar":"Sadharana",
        "Sri Muktsar Sahib":"Jangala","Tarn Taran":"Jangala",
    }},
    "Rajasthan": {"default":"Jangala","districts":{
        "Ajmer":"Jangala","Alwar":"Sadharana-Jangala","Banswara":"Sadharana",
        "Baran":"Sadharana","Barmer":"Jangala","Bharatpur":"Sadharana-Jangala",
        "Bhilwara":"Jangala","Bikaner":"Jangala","Bundi":"Sadharana",
        "Chittorgarh":"Sadharana","Churu":"Jangala","Dausa":"Sadharana-Jangala",
        "Dholpur":"Sadharana-Jangala","Dungarpur":"Sadharana","Hanumangarh":"Jangala",
        "Jaipur":"Sadharana-Jangala","Jaisalmer":"Jangala","Jalore":"Jangala",
        "Jhalawar":"Sadharana","Jhunjhunu":"Jangala","Jodhpur":"Jangala",
        "Karauli":"Sadharana-Jangala","Kota":"Sadharana","Nagaur":"Jangala",
        "Pali":"Jangala","Pratapgarh":"Sadharana","Rajsamand":"Jangala",
        "Sawai Madhopur":"Sadharana-Jangala","Sikar":"Jangala","Sirohi":"Jangala",
        "Sri Ganganagar":"Jangala","Tonk":"Sadharana-Jangala","Udaipur":"Sadharana",
    }},
    "Sikkim": {"default":"Sadharana-Anupa","districts":{
        "East Sikkim":"Sadharana-Anupa","North Sikkim":"Sadharana",
        "South Sikkim":"Sadharana-Anupa","West Sikkim":"Sadharana-Anupa",
    }},
    "Tamil Nadu": {
        "default": "Sadharana",
        "districts": {
            # Coastal
            "Chennai":"Anupa","Nagapattinam":"Anupa","Ramanathapuram":"Sadharana-Anupa",
            "Thanjavur":"Sadharana-Anupa","Thiruvarur":"Anupa","Cuddalore":"Anupa",
            "Kancheepuram":"Sadharana-Anupa","Villupuram":"Sadharana",
            # Interior
            "Coimbatore":"Sadharana","Erode":"Sadharana","Salem":"Sadharana",
            "Tiruppur":"Sadharana","Namakkal":"Sadharana","Dharmapuri":"Sadharana",
            "Krishnagiri":"Sadharana","Vellore":"Sadharana","Tiruvannamalai":"Sadharana",
            "Tiruvallur":"Sadharana","Ranipet":"Sadharana",
            # Dry/arid
            "Madurai":"Sadharana-Jangala","Dindigul":"Sadharana-Jangala",
            "Virudhunagar":"Sadharana-Jangala","Sivaganga":"Sadharana-Jangala",
            "Tirunelveli":"Sadharana-Jangala","Tenkasi":"Sadharana-Anupa",
            "Thoothukudi":"Sadharana-Jangala","Karur":"Sadharana",
            "Tiruchirapalli":"Sadharana","Ariyalur":"Sadharana",
            "Perambalur":"Sadharana","Pudukottai":"Sadharana-Jangala",
            # Nilgiris (hill)
            "Nilgiris":"Sadharana-Anupa","Kanyakumari":"Anupa",
            "Theni":"Sadharana-Jangala",
        }},
    "Telangana": {"default":"Sadharana","districts":{
        "Adilabad":"Sadharana-Jangala","Bhadradri Kothagudem":"Sadharana-Anupa",
        "Hyderabad":"Sadharana","Jagtial":"Sadharana","Jangaon":"Sadharana",
        "Jayashankar Bhupalpally":"Sadharana-Anupa","Jogulamba Gadwal":"Sadharana-Jangala",
        "Kamareddy":"Sadharana","Karimnagar":"Sadharana","Khammam":"Sadharana-Anupa",
        "Kumuram Bheem Asifabad":"Sadharana-Anupa","Mahabubabad":"Sadharana-Anupa",
        "Mahabubnagar":"Sadharana-Jangala","Mancherial":"Sadharana","Medak":"Sadharana",
        "Medchal-Malkajgiri":"Sadharana","Mulugu":"Sadharana-Anupa",
        "Nagarkurnool":"Sadharana-Jangala","Nalgonda":"Sadharana",
        "Narayanpet":"Sadharana-Jangala","Nirmal":"Sadharana-Jangala",
        "Nizamabad":"Sadharana","Peddapalli":"Sadharana","Rajanna Sircilla":"Sadharana",
        "Rangareddy":"Sadharana","Sangareddy":"Sadharana","Siddipet":"Sadharana",
        "Suryapet":"Sadharana","Vikarabad":"Sadharana","Wanaparthy":"Sadharana-Jangala",
        "Warangal Rural":"Sadharana","Warangal Urban":"Sadharana","Yadadri Bhuvanagiri":"Sadharana",
    }},
    "Tripura": {"default":"Anupa","districts":{
        "Dhalai":"Sadharana-Anupa","Gomati":"Anupa","Khowai":"Sadharana-Anupa",
        "North Tripura":"Sadharana-Anupa","Sepahijala":"Anupa","Sipahijala":"Anupa",
        "South Tripura":"Anupa","Unakoti":"Sadharana-Anupa","West Tripura":"Anupa",
    }},
    "Uttar Pradesh": {"default":"Sadharana","districts":{
        "Agra":"Sadharana-Jangala","Aligarh":"Sadharana-Jangala","Ambedkar Nagar":"Sadharana",
        "Amethi":"Sadharana","Amroha":"Sadharana","Auraiya":"Sadharana",
        "Azamgarh":"Sadharana","Baghpat":"Sadharana-Jangala","Bahraich":"Sadharana-Anupa",
        "Ballia":"Sadharana-Anupa","Balrampur":"Sadharana-Anupa","Banda":"Sadharana-Jangala",
        "Barabanki":"Sadharana","Bareilly":"Sadharana","Basti":"Sadharana",
        "Bhadohi":"Sadharana","Bijnor":"Sadharana","Budaun":"Sadharana",
        "Bulandshahr":"Sadharana-Jangala","Chandauli":"Sadharana","Chitrakoot":"Sadharana-Jangala",
        "Deoria":"Sadharana-Anupa","Etah":"Sadharana-Jangala","Etawah":"Sadharana-Jangala",
        "Farrukhabad":"Sadharana","Fatehpur":"Sadharana","Firozabad":"Sadharana-Jangala",
        "Gautam Buddha Nagar":"Sadharana","Ghaziabad":"Sadharana","Ghazipur":"Sadharana-Anupa",
        "Gonda":"Sadharana-Anupa","Gorakhpur":"Sadharana-Anupa","Hamirpur":"Sadharana-Jangala",
        "Hapur":"Sadharana","Hardoi":"Sadharana","Hathras":"Sadharana-Jangala",
        "Jalaun":"Sadharana-Jangala","Jaunpur":"Sadharana","Jhansi":"Sadharana-Jangala",
        "Kannauj":"Sadharana","Kanpur Dehat":"Sadharana","Kanpur Nagar":"Sadharana",
        "Kasganj":"Sadharana-Jangala","Kaushambi":"Sadharana","Kheri":"Sadharana-Anupa",
        "Kushinagar":"Sadharana-Anupa","Lalitpur":"Sadharana-Jangala",
        "Lucknow":"Sadharana","Maharajganj":"Sadharana-Anupa","Mahoba":"Sadharana-Jangala",
        "Mainpuri":"Sadharana-Jangala","Mathura":"Sadharana-Jangala","Mau":"Sadharana",
        "Meerut":"Sadharana","Mirzapur":"Sadharana","Moradabad":"Sadharana",
        "Muzaffarnagar":"Sadharana","Pilibhit":"Sadharana-Anupa","Pratapgarh":"Sadharana",
        "Prayagraj":"Sadharana","Rae Bareli":"Sadharana","Rampur":"Sadharana",
        "Saharanpur":"Sadharana","Sambhal":"Sadharana","Sant Kabir Nagar":"Sadharana",
        "Shahjahanpur":"Sadharana","Shamli":"Sadharana-Jangala","Shravasti":"Sadharana-Anupa",
        "Siddharthnagar":"Sadharana-Anupa","Sitapur":"Sadharana-Anupa","Sonbhadra":"Sadharana",
        "Sultanpur":"Sadharana","Unnao":"Sadharana","Varanasi":"Sadharana",
    }},
    "Uttarakhand": {"default":"Sadharana","districts":{
        "Almora":"Sadharana","Bageshwar":"Sadharana-Anupa","Chamoli":"Sadharana-Anupa",
        "Champawat":"Sadharana","Dehradun":"Sadharana","Haridwar":"Sadharana",
        "Nainital":"Sadharana-Anupa","Pauri Garhwal":"Sadharana",
        "Pithoragarh":"Sadharana","Rudraprayag":"Sadharana-Anupa",
        "Tehri Garhwal":"Sadharana-Anupa","Udham Singh Nagar":"Sadharana","Uttarkashi":"Sadharana",
    }},
    "West Bengal": {
        "default": "Sadharana-Anupa",
        "districts": {
            "Alipurduar":"Sadharana-Anupa","Bankura":"Sadharana",
            "Birbhum":"Sadharana","Cooch Behar":"Anupa","Dakshin Dinajpur":"Sadharana-Anupa",
            "Darjeeling":"Sadharana-Anupa","Hooghly":"Anupa","Howrah":"Anupa",
            "Jalpaiguri":"Anupa","Jhargram":"Sadharana","Kalimpong":"Sadharana-Anupa",
            "Kolkata":"Anupa","Malda":"Sadharana-Anupa","Murshidabad":"Sadharana-Anupa",
            "Nadia":"Anupa","North 24 Parganas":"Anupa","Paschim Bardhaman":"Sadharana",
            "Paschim Medinipur":"Sadharana","Purba Bardhaman":"Sadharana-Anupa",
            "Purba Medinipur":"Anupa","Purulia":"Sadharana","South 24 Parganas":"Anupa",
            "Uttar Dinajpur":"Sadharana-Anupa",
        }},
    # Union Territories
    "Delhi": {"default":"Sadharana-Jangala","districts":{
        "Central Delhi":"Sadharana-Jangala","East Delhi":"Sadharana-Jangala",
        "New Delhi":"Sadharana-Jangala","North Delhi":"Sadharana-Jangala",
        "North East Delhi":"Sadharana-Jangala","North West Delhi":"Sadharana-Jangala",
        "Shahdara":"Sadharana-Jangala","South Delhi":"Sadharana-Jangala",
        "South East Delhi":"Sadharana-Jangala","South West Delhi":"Sadharana-Jangala",
        "West Delhi":"Sadharana-Jangala",
    }},
    "Jammu and Kashmir": {"default":"Sadharana","districts":{
        "Anantnag":"Sadharana","Bandipora":"Sadharana-Anupa","Baramulla":"Sadharana-Anupa",
        "Budgam":"Sadharana","Doda":"Sadharana","Ganderbal":"Sadharana-Anupa",
        "Jammu":"Sadharana","Kathua":"Sadharana","Kishtwar":"Sadharana",
        "Kulgam":"Sadharana","Kupwara":"Sadharana-Anupa","Poonch":"Sadharana",
        "Pulwama":"Sadharana","Rajouri":"Sadharana","Ramban":"Sadharana",
        "Reasi":"Sadharana","Samba":"Sadharana","Shopian":"Sadharana",
        "Srinagar":"Sadharana-Anupa","Udhampur":"Sadharana",
    }},
    "Ladakh": {"default":"Jangala","districts":{"Kargil":"Jangala","Leh":"Jangala"}},
    "Puducherry": {"default":"Anupa","districts":{
        "Karaikal":"Anupa","Mahe":"Anupa","Puducherry":"Anupa","Yanam":"Anupa",
    }},
    "Chandigarh": {"default":"Sadharana","districts":{"Chandigarh":"Sadharana"}},
    "Andaman and Nicobar Islands": {"default":"Anupa","districts":{
        "Nicobar":"Anupa","North and Middle Andaman":"Anupa","South Andaman":"Anupa",
    }},
    "Lakshadweep": {"default":"Anupa","districts":{"Lakshadweep":"Anupa"}},
}

DESHA_DESCRIPTIONS = {
    "Anupa":            "🌊 Anupa Desha (Marshy/Coastal) — Kleda & Snigdha dominant environment. Kapha-aggravating terrain. Laghu-Ruksha-Ushna Ahara recommended. Ref: CS Su 27/16",
    "Jangala":          "🌵 Jangala Desha (Arid/Dry/Forest) — Ruksha & Vishada dominant. Vata-aggravating terrain. Snigdha-Ushna-Guru Ahara recommended. Ref: CS Su 27/17",
    "Sadharana":        "⚖️ Sadharana Desha (Balanced) — Neither Kleda nor Ruksha dominant. Suitable for all Prakritis with seasonal variation. Ref: CS Su 27/18",
    "Sadharana-Anupa":  "🌿 Sadharana-Anupa Desha (Mildly Wet) — Moderate Kleda. Slight Kapha tendency. Moderate Laghu-Ushna adjustments advised.",
    "Sadharana-Jangala":"🏔️ Sadharana-Jangala Desha (Mildly Dry) — Moderate Ruksha. Slight Vata tendency. Moderate Snigdha-Ushna adjustments advised.",
}

def get_desha(state, district):
    geo = INDIA_GEO.get(state, {})
    dist_map = geo.get("districts", {})
    return dist_map.get(district) or geo.get("default", "Sadharana")

# ══════════════════════════════════════════════════════════════════════════════
#  CONFLICT PAIRS — 12 inter/intra question logical inconsistencies
#  Each dict: id, type (intra/cross), qa, qb, opt_a, opt_b,
#             severity (strong/moderate/advisory), message
# ══════════════════════════════════════════════════════════════════════════════
CONFLICT_PAIRS = [
    # ── C1 — Q4 intra: oily + dry (same question multi-select) ─────────────
    {"id":"C1","severity":"strong","type":"intra","qa":4,"qb":4,
     "opt_a":0,"opt_b":2,   # index 0=oily, index 2=dry
     "msg":"Q4 — You selected both 'Naturally oily / moisturised' (Kapha-Snigdha) and "
           "'Dry — needs moisturiser regularly' (Vata-Ruksha). "
           "Snigdha and Ruksha Tvak are opposite Gunas and cannot coexist. "
           "Please select only the one that truly describes your skin."},
    # ── C2 — Q4 intra: oily + cracks ───────────────────────────────────────
    {"id":"C2","severity":"strong","type":"intra","qa":4,"qb":4,
     "opt_a":0,"opt_b":3,   # 0=oily, 3=cracks
     "msg":"Q4 — 'Naturally oily / moisturised skin' (Kapha-Snigdha) and "
           "'Cracks on palms and soles' (Vata-Ruksha Paada Sphutana) are contradictory. "
           "Snigdha Tvak does not develop Paada Sphutana. Please review."},
    # ── C3 — Q7 intra: large steady eyes + small dry restless ──────────────
    {"id":"C3","severity":"strong","type":"intra","qa":7,"qb":7,
     "opt_a":0,"opt_b":1,   # 0=large/Kapha, 1=small/Vata
     "msg":"Q7 — 'Large, attractive and steady gaze' (Kapha-Vishalaksha) and "
           "'Small, dry, unsteady / restless gaze' (Vata-Tanu Chala Lochana) are classical opposites. "
           "Ref: CS Vim 8/96. Please select the option that genuinely matches your eyes."},
    # ── C4 — Q20 intra: deep sound sleep + light sleep ─────────────────────
    {"id":"C4","severity":"strong","type":"intra","qa":20,"qb":20,
     "opt_a":0,"opt_b":3,   # 0=sound deep, 3=light sleep
     "msg":"Q20 — 'Sound, deep sleep — very difficult to wake' (Kapha-Guru Nidra) and "
           "'Light sleep — awakened by small sounds' (Vata-Alpanidra) are opposite Guna expressions. "
           "Ref: CS Vim 8/97. Please keep only the one that matches your usual sleep."},
    # ── C5 — Q20 intra: loves sleeping + difficulty falling asleep ──────────
    {"id":"C5","severity":"strong","type":"intra","qa":20,"qb":20,
     "opt_a":1,"opt_b":5,   # 1=loves sleeping, 5=difficulty falling asleep
     "msg":"Q20 — 'I love sleeping / tend to oversleep' (Kapha) and "
           "'Difficulty falling asleep' (Vata) are contradictory sleep patterns. Please review."},
    # ── C6 — Q5 & Q6: thick oily hair + premature greying ──────────────────
    {"id":"C6","severity":"moderate","type":"cross","qa":5,"qb":6,
     "opt_a":0,"opt_b":0,   # Q5 idx0=thick oily (K), Q6 idx0=premature greying (P)
     "msg":"Q5 & Q6 — 'Thick, dense, lustrous, naturally oily hair' (Kapha-Ghana-Snigdha Kesha) "
           "alongside 'Premature greying before age 35' (Pitta-Akalapalita) is an unusual combination. "
           "These are typically seen in different Doshas. Please confirm this truly describes you."},
    # ── C7 — Q13 & Q14: very fast gait + very slow activity ────────────────
    {"id":"C7","severity":"moderate","type":"cross","qa":13,"qb":14,
     "opt_a":0,"opt_b":4,   # Q13 idx0=fast/V, Q14 idx4=very slow/K
     "msg":"Q13 & Q14 — 'Very fast gait — outpace most people' (Vata-Druta Gati) with "
           "'Very slow and relaxed in all activities' (Kapha-Manda Chesta) is inconsistent. "
           "Gait speed and general activity pace are usually aligned. Please review."},
    # ── C8 — Q16 & Q17: intense hunger + forgets to drink ──────────────────
    {"id":"C8","severity":"moderate","type":"cross","qa":16,"qb":17,
     "opt_a":0,"opt_b":3,   # Q16 idx0=intense hunger/P, Q17 idx3=forgets water/K
     "msg":"Q16 & Q17 — 'Intense hunger — very uncomfortable if I skip a meal' (Pitta-Teekshna Agni) "
           "and 'Less thirst — often forget to drink water' (Kapha-Alpa Trishna) is unusual. "
           "Teekshna Agni (Pitta) typically generates both strong Kshudha AND Trishna. Please confirm."},
    # ── C9 — Q1 & Q44: very lean + excellent endurance ─────────────────────
    {"id":"C9","severity":"moderate","type":"cross","qa":1,"qb":44,
     "opt_a":0,"opt_b":0,   # Q1 idx0=very lean/V, Q44 idx0=excellent stamina/K
     "msg":"Q1 & Q44 — 'Very lean and thin' body build (Vata-Apachita Shareera) with "
           "'Very strong — excellent endurance and sustained stamina' (Kapha-Balavan) is atypical. "
           "Low Mamsa-Medodhatu (Vata) does not usually support sustained Bala. Please review."},
    # ── C10 — Q24 & Q23: instant grasp + excellent long-term memory ─────────
    {"id":"C10","severity":"advisory","type":"cross","qa":24,"qb":23,
     "opt_a":0,"opt_b":0,   # Q24 idx0=instant grasp/V, Q23 idx0=excellent memory/K
     "msg":"Q24 & Q23 — 'Very quick — grasp concepts almost instantly' (Vata-Shrutagrahi) "
           "with 'Excellent long-term memory — retain for years' (Kapha-Smritimaan) is unusual. "
           "Classical pattern: Vata = quick grasp + weak retention; Kapha = slow grasp + strong retention. "
           "Please confirm — this combination, though rare, can occur."},
    # ── C11 — Q3 & Q4: very fair + severely dry skin ────────────────────────
    {"id":"C11","severity":"advisory","type":"cross","qa":3,"qb":4,
     "opt_a":0,"opt_b":2,   # Q3 idx0=very fair/K, Q4 idx2=dry/V
     "msg":"Q3 & Q4 — 'Very fair — lotus-like, lustrous complexion' (Kapha-Gaur Varna-Snigdha) "
           "with 'Dry skin — needs moisturiser regularly' (Vata-Ruksha Tvak) is an uncommon combination. "
           "Fair lustrous skin is inherently Snigdha in nature. Please verify."},
    # ── C12 — Q28 & Q29: very regular routine + very indecisive ────────────
    {"id":"C12","severity":"advisory","type":"cross","qa":28,"qb":29,
     "opt_a":0,"opt_b":0,   # Q28 idx0=very regular/K, Q29 idx0=very indecisive/V
     "msg":"Q28 & Q29 — 'Very regular — same routine every single day' (Kapha-Sthira Dinacharya) "
           "and 'Very indecisive — change my mind frequently' (Vata-Anavasthita Chitta) are opposing "
           "Guna expressions (Sthira vs Chala). Please confirm both truly describe you."},
    # ── C13 — Q20 intra: loves sleeping + light sleep (awakened by sounds) ─
    {"id":"C13","severity":"strong","type":"intra","qa":20,"qb":20,
     "opt_a":1,"opt_b":3,   # idx1=loves sleeping/K, idx3=light sleep awakened by sounds/V
     "msg":"Q20 — 'I love sleeping / tend to oversleep' (Kapha-Guru Nidra) and "
           "'Light sleep — awakened by small sounds' (Vata-Alpanidra) are contradictory sleep patterns. "
           "Kapha individuals sleep deeply and heavily; Vata individuals sleep lightly. "
           "Please select only the one that truly describes your usual sleep quality."},
    # ── C14 — Q6 intra: early hair loss + minimal hair fall ─────────────────
    {"id":"C14","severity":"moderate","type":"intra","qa":6,"qb":6,
     "opt_a":1,"opt_b":3,   # idx1=early hair loss/P, idx3=minimal hair fall/K
     "msg":"Q6 — 'Early hair loss / baldness' (Pitta-Khalitya) and "
           "'Minimal hair fall, stable density over years' (Kapha-Sthira Kesha) are directly contradictory. "
           "These are opposite Dosha expressions for hair stability. "
           "Please select only the one that matches your actual hair condition."},
]

def check_conflicts(responses):
    """
    Returns list of triggered conflict dicts from CONFLICT_PAIRS.
    Checks only pairs where both Qs are answered.
    """
    triggered = []
    for cp in CONFLICT_PAIRS:
        qa_id, qb_id = cp["qa"], cp["qb"]
        ra = responses.get(qa_id)
        rb = responses.get(qb_id)
        if ra is None or rb is None:
            continue
        # Get answer indices
        if cp["type"] == "intra":
            # Both opts are in the same multi-select question
            if isinstance(ra, set) and cp["opt_a"] in ra and cp["opt_b"] in ra:
                triggered.append(cp)
        else:
            # Cross-question: check if each Q has selected the conflicting option
            q_a = next((q for q in QUESTIONS if q["id"]==qa_id), None)
            q_b = next((q for q in QUESTIONS if q["id"]==qb_id), None)
            if q_a and q_b:
                a_hit = (q_a["type"]=="single" and ra == cp["opt_a"]) or \
                        (q_a["type"]=="multi"  and cp["opt_a"] in (ra or set()))
                b_hit = (q_b["type"]=="single" and rb == cp["opt_b"]) or \
                        (q_b["type"]=="multi"  and cp["opt_b"] in (rb or set()))
                if a_hit and b_hit:
                    triggered.append(cp)
    return triggered

# ── Prompt builder ──────────────────────────────────────────────────────────
def build_ai_prompt(prof, final_op, pname, desha, dietary_pref, meat_freq, responses):
    """Build a comprehensive structured prompt for e-PathyaGPT / Custom GPT."""
    from datetime import date as _date

    # Ritu (season) from current month
    month = _date.today().month
    ritu_map = {12:"Hemanta Ritu (Early Winter)",1:"Hemanta Ritu (Early Winter)",
                2:"Shishira Ritu (Late Winter)",3:"Shishira Ritu (Late Winter)",
                4:"Vasanta Ritu (Spring)",5:"Vasanta Ritu (Spring)",
                6:"Grishma Ritu (Summer)",7:"Grishma Ritu (Summer)",
                8:"Varsha Ritu (Monsoon)",9:"Varsha Ritu (Monsoon)",
                10:"Sharad Ritu (Autumn)",11:"Sharad Ritu (Autumn)"}
    ritu = ritu_map.get(month, "Sharad Ritu (Autumn)")
    kala = "Vata Kala (>60 yrs)" if prof.get("age",30)>60 else \
           "Pitta Kala (16–60 yrs)" if prof.get("age",30)>16 else "Kapha Kala (<16 yrs)"

    # Both Doshas for Dwandwaja
    sorted_doshas = sorted([("Vata",final_op["V"]),("Pitta",final_op["P"]),
                             ("Kapha",final_op["K"])], key=lambda x:-x[1])
    dom_name = sorted_doshas[0][0]
    sec_name = sorted_doshas[1][0]
    dom_key  = {"Vata":"V","Pitta":"P","Kapha":"K"}[dom_name]
    sec_key  = {"Vata":"V","Pitta":"P","Kapha":"K"}[sec_name]
    pkeys    = {"Vata":("VP","VA"),"Pitta":("PP","PA"),"Kapha":("KP","KA")}

    # Pathya for BOTH Doshas
    pathya_d1, apathya_d1, pathya_d2, apathya_d2 = [], [], [], []
    pk1, ak1 = pkeys[dom_name]
    pk2, ak2 = pkeys[sec_name]
    for cat, items in AHARA_DATA.items():
        for item in items:
            n = item["name"]
            if item[pk1]: pathya_d1.append(n)
            if item[ak1]: apathya_d1.append(n)
            if item[pk2] and n not in pathya_d1: pathya_d2.append(n)
            if item[ak2] and n not in apathya_d2: apathya_d2.append(n)

    name      = prof.get("name", "the health seeker")
    state_val = prof.get("state", st.session_state.get("state","India"))
    dist_val  = prof.get("district", st.session_state.get("district",""))
    location  = f"{dist_val}, {state_val}" if dist_val else state_val

    diet_note = dietary_pref
    if dietary_pref == "Mixed (Non-vegetarian)":
        diet_note += f" — {meat_freq} non-veg meals per week"

    bmi_str  = f"{prof.get('bmi','N/A')} ({prof.get('bmi_category','')})" if prof.get('bmi') else "Not provided"
    bmr_str  = f"{prof.get('bmr','N/A')} kcal/day" if prof.get('bmr') else "Not provided"
    sbmr_str = f"{prof.get('specific_bmr','N/A')} kcal/kg" if prof.get('specific_bmr') else "Not provided"
    fat_str  = f"{prof.get('fat_pct','N/A')}%" if prof.get('fat_pct') else "Not provided"

    prompt = f"""IMPORTANT INSTRUCTION TO THE GPT:
- Address the health seeker as {name} throughout your response (use their name at least 4 times).
- DO NOT quote, generate, cite, or reconstruct any Sanskrit shlokas, verses, or classical text passages. This is a strict prohibition — AI-generated shloka citations are unreliable.
- Apply Ayurvedic principles from your knowledge but express them in clear clinical prose only.
- All food recommendations MUST reference locally available foods in {location}. Use local names alongside Sanskrit names.
- Always address BOTH Doshas — this is a Dwandwaja ({pname}) constitution.
- End your response with a disclaimer that this is not a substitute for consultation with a qualified Ayurvedic physician.

═══════════════════════════════════════════════════════
HEALTH SEEKER PROFILE — e-Prakruti Assessment
Generated by: e-Prakruti v6.0 | SKAMC, Bangalore
Author: Dr. Prasanna Kulkarni MD (Ayu), MS Data Science
═══════════════════════════════════════════════════════
Health Seeker   : {name}
Age             : {prof.get('age','N/A')} years
Gender          : {prof.get('gender','N/A')}
Jeevanakala     : {kala}

═══════════════════════════════════════════════════════
PRAKRITI ASSESSMENT RESULTS (Dwandwaja)
═══════════════════════════════════════════════════════
Prakriti Type       : {pname}
Pradhana Dosha      : {dom_name} ({final_op[dom_key]}%) — Primary constitution
Anupradhana Dosha   : {sec_name} ({final_op[sec_key]}%) — Secondary modifying Dosha
Third Dosha         : {sorted_doshas[2][0]} ({sorted_doshas[2][1]}%)
Scoring method      : Questionnaire (80%) + Anthropometric measurements (20%)

═══════════════════════════════════════════════════════
ANTHROPOMETRIC & METABOLIC DATA
═══════════════════════════════════════════════════════
BMI             : {bmi_str}
BMR             : {bmr_str}
Body Fat %      : {fat_str}
Specific BMR    : {sbmr_str}
WHR             : {prof.get('whr','Not measured')}

═══════════════════════════════════════════════════════
GEOGRAPHICAL & SEASONAL CONTEXT
═══════════════════════════════════════════════════════
Location        : {location}
Desha           : {desha}
Current Ritu    : {ritu}
Dietary Pattern : {diet_note}

═══════════════════════════════════════════════════════
PATHYA FOR {dom_name.upper()} (Pradhana Dosha)
═══════════════════════════════════════════════════════
{", ".join(pathya_d1[:30])}

APATHYA FOR {dom_name.upper()} (Pradhana Dosha)
{", ".join(apathya_d1[:20])}

═══════════════════════════════════════════════════════
PATHYA FOR {sec_name.upper()} (Anupradhana Dosha)
═══════════════════════════════════════════════════════
{", ".join(pathya_d2[:20])}

APATHYA FOR {sec_name.upper()} (Anupradhana Dosha)
{", ".join(apathya_d2[:20])}

═══════════════════════════════════════════════════════
PLEASE PROVIDE THE FOLLOWING FOR {name.upper()}:
═══════════════════════════════════════════════════════

1. PERSONALISED OPENING
   - Address {name} warmly by name
   - Summarise their {pname} constitution in 3-4 friendly, plain-language sentences
   - Mention the significance of living in {location} ({desha} Desha)

2. AHARA NIYAMA (Dietary Principles)
   - Which food Gunas to emphasise for {pname} in {desha} Desha
   - How to balance the needs of {dom_name} (Pradhana) vs {sec_name} (Anupradhana)
   - Seasonal adjustments for {ritu}

3. DAILY MEAL PLAN (1 sample day — all foods locally available in {location})
   - Breakfast / Praatah Bhojan (~7:30-8:30 AM) with calorie estimate
   - Lunch / Madhyahna Bhojan (~12:30-1:30 PM, main meal) with calorie estimate
   - Evening snack / Sayam if appropriate
   - Dinner / Ratri Bhojan (before 8 PM) with calorie estimate
   - Total calories vs target (BMR {bmr_str} × appropriate activity factor)
   - For each food: Sanskrit name (local name in {state_val}) — brief rationale

4. AHARA VIDHI (Rules of Eating)
   - Meal timing for {name}'s Prakriti
   - 3-4 key Viruddha Ahara (food incompatibilities) most relevant for this constitution
   - Specific regional foods from {location} that are Apathya — name them explicitly

5. VIHARA (Lifestyle)
   - Exercise: type, duration, intensity for this Prakriti and BMI ({bmi_str})
   - Sleep guidance
   - 5 key Dinacharya points for {name}
   - Ritucharya adjustments for {ritu}

6. CALORIC GUIDANCE
   - Daily caloric target based on BMR {bmr_str}
   - Meal distribution (breakfast/lunch/dinner/snack percentages)
   - Digestive capacity note for {pname}

7. LOCALLY AVAILABLE PATHYA FOODS in {location}
   THIS SECTION IS MANDATORY. List 8-10 Pathya foods that are:
   - Appropriate for {pname}
   - Readily and commonly available in {dist_val if dist_val else state_val}
   - Format: Sanskrit name (local name / market name) — why beneficial — seasonal note

8. SPECIAL CONSIDERATIONS for {name}
   - Key disease susceptibilities for {pname} to prevent through diet
   - Age {prof.get('age','N/A')} years ({kala}) adjustments
   - Gender-specific dietary notes ({prof.get('gender','N/A')})

9. CLOSING
   - Address {name} by name
   - One warm, motivating paragraph
   - Mandatory disclaimer: "This guidance is based on your Ayurvedic Prakriti assessment
     and is intended for health promotion and disease prevention. It is not a substitute
     for personalised consultation with a qualified Ayurvedic physician."

Write in a warm, conversational clinical tone — like an experienced Vaidya speaking
directly to {name}. Be practical, specific to {location}, and accessible.
"""
    return prompt

# ══════════════════════════════════════════════════════════════════════════════
#  HEADER
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("""
<div class="main-header">
  <h1>🌿 e-Prakruti Assessment</h1>
  <div class="shloka">
    प्रकृतिस्तु खलु शरीरं स्वभावः<br>
    <em>"The natural constitution of the body is one's inherent Prakriti"</em>
  </div>
  <div class="shloka-src">— Charaka Sharira Sthana 4/36</div>
  <p style="margin:14px 0 0;font-size:.97em;opacity:.88;">
    Personalised Ayurvedic Constitutional Analysis &nbsp;·&nbsp; 45 Questions + Anthropometric Scoring &nbsp;·&nbsp; ~15 minutes<br>
    <small>Classical basis: Charaka Samhita · Sushruta Samhita · Ashtanga Hridaya · Ashtanga Sangraha</small>
  </p>
</div>
""", unsafe_allow_html=True)

answered = len([
    q["id"] for q in QUESTIONS
    if (q["type"]=="single" and isinstance(st.session_state.responses.get(q["id"]), int))
    or (q["type"]=="multi"  and len(st.session_state.responses.get(q["id"], set())) > 0)
])
st.progress(answered / len(QUESTIONS))
st.caption(f"✅ {answered} of {len(QUESTIONS)} questions answered")

# ── Floating progress circle (fixed bottom-right, scrolls with page) ──────────
_pct      = int(round(answered / len(QUESTIONS) * 100))
_total    = len(QUESTIONS)
_r        = 34          # circle radius
_cx = _cy = 38          # centre of 76×76 SVG
_circ     = 2 * 3.14159 * _r
_dash     = round(_circ * _pct / 100, 1)
_gap      = round(_circ - _dash, 1)
# colour: red→amber→green based on completion
if _pct < 30:   _clr = "#9E2A0A"
elif _pct < 70: _clr = "#D4A017"
else:           _clr = "#0D5C30"

st.markdown(f"""
<div class="progress-float" title="{answered} of {_total} questions answered">
  <svg width="76" height="76">
    <!-- background track -->
    <circle cx="{_cx}" cy="{_cy}" r="{_r}"
            fill="none" stroke="#E0E0E0" stroke-width="5"/>
    <!-- progress arc — starts at 12 o'clock (-90 deg rotate) -->
    <circle cx="{_cx}" cy="{_cy}" r="{_r}"
            fill="none" stroke="{_clr}" stroke-width="5"
            stroke-dasharray="{_dash} {_gap}"
            stroke-linecap="round"
            transform="rotate(-90 {_cx} {_cy})"/>
  </svg>
  <div class="pf-inner">
    <span class="pf-pct">{_pct}%</span>
    <span class="pf-lbl">DONE</span>
  </div>
</div>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
#  MAIN LAYOUT — 6 TABS
# ══════════════════════════════════════════════════════════════════════════════

DISEASE_PRONE_PDF = {
    "Vata": ["Neurological disorders","Anxiety & panic disorders","Insomnia",
              "Constipation & bloating","Arthritis & joint disorders","Osteoporosis",
              "Sciatica","Parkinson's disease","Tremors & spasms","Tachycardia",
              "Dry eczema","Emaciation","Numbness in limbs","Back pain"],
    "Pitta": ["Hyperacidity & peptic ulcers","Psoriasis & skin rashes",
               "Conjunctivitis & eye inflammation","Jaundice & liver disorders",
               "Stomatitis & mouth ulcers","Hypertension","Migraines",
               "Premature greying & baldness","Inflammatory bowel disease",
               "Fever & infectious diseases","Hemorrhagic conditions","Hyperthyroidism"],
    "Kapha": ["Obesity & Metabolic syndrome","Type 2 Diabetes","Asthma & Bronchitis",
               "Congestion & sinusitis","Hypothyroidism","Oedema","Atherosclerosis",
               "Goitre","Depression & drowsiness","Excessive sleep disorders",
               "Chronic fatigue","Calf muscle cramps","Lymphatic disorders"],
}

PRECAUTIONS_PDF = {
    "Vata": [
        "Maintain a very regular Dinacharya — fixed meal and sleep times",
        "Daily warm oil Abhyanga (sesame or almond oil)",
        "Avoid cold, dry, raw, and stale foods",
        "Avoid excessive travel, fasting, and screen time at night",
        "Prefer warm, oily, sweet, sour and salty foods",
        "Gentle exercise — Yoga, walking, swimming (not vigorous)",
        "Warm baths, warm environments, adequate warmth in clothing",
        "Minimum 7–8 hours sleep — early to bed is essential",
    ],
    "Pitta": [
        "Avoid excessive heat, direct sun, and spicy-fried-fermented foods",
        "Prefer cool, sweet, bitter and astringent foods",
        "Coconut oil, ghee and bitter vegetables are very beneficial",
        "Cooling Pranayama (Sheetali, Sheetkari) daily",
        "Avoid skipping meals — intense hunger destabilises Pitta",
        "Moderate exercise avoiding overheating",
        "Meditation and cooling practices for anger management",
        "Limit alcohol and caffeine — both aggravate Pitta strongly",
    ],
    "Kapha": [
        "Regular vigorous exercise daily (minimum 45 minutes)",
        "Avoid daytime sleeping and oversleeping",
        "Avoid heavy, oily, cold, sweet and excessive foods",
        "Prefer light, warm, pungent, bitter and astringent foods",
        "Ginger, black pepper, honey and periodic fasting are beneficial",
        "Seek variety, stimulation and social engagement",
        "Avoid sedentary lifestyle at all costs",
        "Morning exercise before breakfast is especially beneficial",
    ],
}

FOOD_TABLE_PDF = {
    "Vata": {
        "headers": ["Category","Prefer (Pathya)","Limit / Avoid (Apathya)"],
        "rows": [
            ["Cereals","Wheat, Rice (warm cooked), Oats","Dry crackers, Cold cereal, Barley"],
            ["Pulses","Mung dal (well-cooked), Red lentils","Raw beans, Chickpeas, Rajma"],
            ["Dairy","Warm cow milk, Ghee, Butter","Cold milk, Ice cream, Frozen curd"],
            ["Fruits","Banana, Mango, Dates, Figs, Sweet grapes","Dry fruits (raw), Cranberries"],
            ["Vegetables","Cooked root veg, Carrot, Sweet potato","Raw veg, Broccoli, Cabbage"],
            ["Spices","Ginger, Cumin, Cardamom, Cinnamon, Fennel","Excess chilli, Dry spices"],
            ["Oils","Sesame, Ghee, Almond oil","Canola oil, Dry or cold oils"],
            ["Tastes","Sweet · Sour · Salty (Madhura · Amla · Lavana)","Bitter · Astringent · Pungent (excess)"],
        ]
    },
    "Pitta": {
        "headers": ["Category","Prefer (Pathya)","Limit / Avoid (Apathya)"],
        "rows": [
            ["Cereals","Wheat, Oats, Barley, White rice","Brown rice, Corn, Millet (heating)"],
            ["Pulses","Mung bean, Chickpeas, Kidney bean, Tofu","Red lentils (heating), Fermented soy"],
            ["Dairy","Cool milk, Ghee (cooling), Butter, Sweet lassi","Sour cream, Salted cheese, Curd at night"],
            ["Fruits","Sweet grapes, Pomegranate, Coconut, Sweet mango","Sour fruits, Tamarind, Grapefruit"],
            ["Vegetables","Leafy greens, Cucumber, Zucchini, Broccoli","Tomatoes, Garlic, Onion (raw), Chilli"],
            ["Spices","Coriander, Fennel, Cardamom, Saffron, Turmeric","Chilli, Mustard seeds, Fenugreek (excess)"],
            ["Oils","Coconut oil, Ghee, Sunflower oil","Sesame oil (heating), Corn oil"],
            ["Tastes","Sweet · Bitter · Astringent (Madhura · Tikta · Kashaya)","Sour · Salty · Pungent (excess)"],
        ]
    },
    "Kapha": {
        "headers": ["Category","Prefer (Pathya)","Limit / Avoid (Apathya)"],
        "rows": [
            ["Cereals","Ragi, Barley, Corn, Millet, Old rice","Wheat, White rice, Oats (heavy)"],
            ["Pulses","Split chickpeas, Horse gram, Toor dal","Black gram (Urad), Kidney bean, Soy"],
            ["Dairy","Warm skimmed milk, Goat milk (small qty)","Buffalo milk, Cheese, Curd, Ice cream"],
            ["Fruits","Pomegranate, Apple, Pear, Papaya, Guava","Banana, Mango, Avocado, Dates, Coconut"],
            ["Vegetables","Leafy greens, Bitter gourd, Radish, Drumstick","Sweet potato, Potato, Avocado"],
            ["Spices","Ginger, Black pepper, Mustard, Turmeric, Asafoetida","Excess salt, Sweet spices (excess)"],
            ["Oils","Mustard oil, Corn oil, Sunflower oil (small qty)","Sesame oil, Ghee (excess), Coconut oil"],
            ["Tastes","Pungent · Bitter · Astringent (Katu · Tikta · Kashaya)","Sweet · Sour · Salty (excess)"],
        ]
    },
}

DESC_PDF = {
    "Vata": {
        "ov": ("Vata Prakriti individuals are governed by Akasha and Vayu — naturally creative, "
               "enthusiastic, quick-thinking, highly communicative, and spontaneous. "
               "They initiate rapidly and adapt easily to change."),
        "ph": ("Lean/thin build (Apachita) | Dry skin (Ruksha Tvak) | Rough hair | "
               "Prominent veins and tendons | Variable appetite | Light insufficient sleep | "
               "Constipation (Vibandha) | Cold extremities | Cracking joints (Sashabda Sandhi)"),
        "ps": ("Quick grasping but weak long-term retention | Creative and imaginative mind | "
               "Tendency toward anxiety (Bhaya-Udvega) | Indecisive (Anavasthita Chitta) | "
               "Frequent mood changes"),
    },
    "Pitta": {
        "ov": ("Pitta Prakriti individuals are governed by Agni and Jala — naturally intelligent, "
               "organised, purposeful, and passionately driven. They transform ideas into results "
               "with focused intensity."),
        "ph": ("Medium well-proportioned build | Fair/yellowish complexion | "
               "Soft skin prone to rashes and freckles (Vyanga-Pidaka) | Early greying tendency | "
               "Profuse sweating (Prabhuta Sweda) | Intense hunger and thirst | "
               "Regular bowel evacuation (Srishta Mala)"),
        "ps": ("Sharp analytical mind (Medhavi) | Excellent comprehension | "
               "Short-tempered but quick to cool (Kshipra Kopa) | Perfectionist | "
               "Competitive | Principled | Strong convictions"),
    },
    "Kapha": {
        "ov": ("Kapha Prakriti individuals are governed by Prithvi and Jala — naturally calm, "
               "patient, deeply affectionate, remarkably enduring, and profoundly loyal. "
               "They provide the stability that sustains all endeavours."),
        "ph": ("Heavy well-built frame (Upachita Shareera) | Fair lustrous skin (Gaur Tvak) | "
               "Thick dense hair (Ghana Kesha) | Big beautiful steady eyes (Vishalaksha) | "
               "Deep sound sleep | Slow metabolism (Manda Agni) | "
               "Excellent physical endurance (Balavan)"),
        "ps": ("Slow but excellent long-term memory (Smritimaan) | Calm temperament | "
               "Very stable relationships (Sthira Sauhrida) | Patient and generous (Vadanya) | "
               "Deeply loyal | Strong self-control (Alaulupa)"),
    },
}


class _DoshaBarPDF(Flowable):
    def __init__(self, label, pct, color, width):
        super().__init__()
        self._label = label
        self._pct   = pct
        self._color = color
        self._width = width
    def wrap(self, *args):
        return self._width, 9*mm
    def draw(self):
        c = self.canv
        y, bar_w = 1.5*mm, self._width - 52*mm
        fill_w = max(bar_w * self._pct / 100, 4*mm)
        c.setFont("Helvetica-Bold", 8.5)
        c.setFillColor(self._color)
        c.drawString(0, y+1*mm, self._label)
        c.setFillColor(RLHexColor("#EDE4D3"))
        c.roundRect(44*mm, y, bar_w, 5*mm, 2.5*mm, fill=1, stroke=0)
        c.setFillColor(self._color)
        c.roundRect(44*mm, y, fill_w, 5*mm, 2.5*mm, fill=1, stroke=0)
        if fill_w > 12*mm:
            c.setFillColor(colors.white)
            c.setFont("Helvetica-Bold", 7.5)
            c.drawString(46*mm, y+1.2*mm, f"{self._pct}%")
        c.setFillColor(self._color)
        c.setFont("Helvetica-Bold", 9)
        c.drawRightString(self._width, y+1*mm, f"{self._pct}%")


def _sec_hdr(text, bg, W):
    p = Paragraph(f"<b>{text}</b>",
                  ParagraphStyle("sh", fontName="Helvetica-Bold",
                                 fontSize=10, textColor=colors.white))
    t = Table([[p]], colWidths=[W])
    t.setStyle(TableStyle([
        ("BACKGROUND",(0,0),(-1,-1), bg),
        ("TOPPADDING",(0,0),(-1,-1), 5), ("BOTTOMPADDING",(0,0),(-1,-1), 5),
        ("LEFTPADDING",(0,0),(-1,-1), 8), ("RIGHTPADDING",(0,0),(-1,-1), 8),
    ]))
    return t


def generate_pdf_report(profile, trait_pct, quest_op, anthro_op, final_op,
                        pname, picon, pcolor_hex):
    """Generate e-Prakruti PDF report. Returns bytes."""
    if not PDF_AVAILABLE:
        return None

    buf = BytesIO()
    W   = A4[0] - 40*mm
    doc = SimpleDocTemplate(buf, pagesize=A4,
                            leftMargin=20*mm, rightMargin=20*mm,
                            topMargin=15*mm, bottomMargin=15*mm)

    # Colours
    C_DARK   = RLHexColor("#3D1A06")
    C_MID    = RLHexColor("#7A3210")
    C_GOLD   = RLHexColor("#D4A017")
    C_VATA   = RLHexColor("#1A4F96")
    C_PITTA  = RLHexColor("#9E2A0A")
    C_KAPHA  = RLHexColor("#0D5C30")
    C_CREAM  = RLHexColor("#FDF5E6")
    C_LGREY  = RLHexColor("#F5F5F5")
    C_MGREY  = RLHexColor("#E0E0E0")
    C_PRAKRITI = RLHexColor(pcolor_hex)

    def ps(name, **kw):
        base = dict(fontName="Helvetica", fontSize=9,
                    textColor=colors.black, leading=13)
        base.update(kw)
        return ParagraphStyle(name, **base)

    S = {
        "title":    ps("t", fontName="Helvetica-Bold", fontSize=18,
                        textColor=colors.white, alignment=TA_CENTER),
        "sub":      ps("s", fontSize=8.5, textColor=RLHexColor("#FFD580"),
                        alignment=TA_CENTER),
        "shloka":   ps("sl", fontSize=8.5, textColor=RLHexColor("#FFE080"),
                        fontName="Helvetica-Oblique", alignment=TA_CENTER),
        "body":     ps("b", spaceAfter=3*mm),
        "bullet":   ps("bu", leftIndent=8*mm, firstLineIndent=-5*mm,
                        spaceAfter=1.5*mm, fontSize=8.5),
        "prakriti": ps("pk", fontName="Helvetica-Bold", fontSize=22,
                        textColor=colors.white, alignment=TA_CENTER),
        "mv":       ps("mv", fontName="Helvetica-Bold", fontSize=13,
                        textColor=C_DARK, alignment=TA_CENTER),
        "ml":       ps("ml", fontSize=7.5, textColor=RLHexColor("#888888"),
                        alignment=TA_CENTER),
        "note":     ps("n", fontName="Helvetica-Oblique", fontSize=8,
                        textColor=RLHexColor("#666666"), spaceAfter=3*mm),
        "disc":     ps("di", fontName="Helvetica-Oblique", fontSize=7.5,
                        textColor=RLHexColor("#777777"), leading=11),
        "th":       ps("thh", fontName="Helvetica-Bold", fontSize=8,
                        textColor=colors.white, alignment=TA_CENTER),
        "tc":       ps("tcc", fontSize=7.5, leading=10),
        "footer":   ps("ft", fontSize=7.5, textColor=RLHexColor("#4A2008"), leading=10),
        "footerr":  ps("ftr", fontSize=7.5, textColor=RLHexColor("#4A2008"),
                        leading=10, alignment=TA_RIGHT),
    }

    dom   = max(final_op, key=final_op.get)  # "V","P","K"
    dname = {"V":"Vata","P":"Pitta","K":"Kapha"}[dom]
    today = date.today().strftime("%d / %m / %Y")
    story = []

    # ─── HEADER ───────────────────────────────────────────────────────────────
    hdr = Table([[
        Paragraph("🌿  e-Prakruti Assessment Report  |  v6.0", S["title"]),
        Paragraph("Dr. Prasanna Kulkarni  |  MD Ayurveda · MS Data Science", S["sub"]),
        Paragraph("SKAMC — Sri Kalabyraveshwara Swamy Ayurvedic Medical College, Bangalore",
                  S["sub"]),
        Paragraph(
            "प्रकृतिस्तु खलु शरीरं स्वभावः  —  "
            "<i>The natural constitution is one's inherent Prakriti</i>",
            S["shloka"]),
        Paragraph("Charaka Sharira Sthana 4/36", S["sub"]),
    ]], colWidths=[W])
    hdr.setStyle(TableStyle([
        ("BACKGROUND",(0,0),(-1,-1), C_DARK),
        ("TOPPADDING",(0,0),(-1,-1), 8), ("BOTTOMPADDING",(0,0),(-1,-1), 10),
        ("LEFTPADDING",(0,0),(-1,-1), 12), ("RIGHTPADDING",(0,0),(-1,-1), 12),
        ("LINEABOVE",(0,0),(-1,0), 4, C_GOLD),
    ]))
    story += [hdr, Spacer(1, 4*mm)]

    # ─── GREETING ─────────────────────────────────────────────────────────────
    name = profile.get("name","")
    story.append(Paragraph(
        f"Namaste <b>{name}</b>," if name else "Assessment Results,", S["body"]))
    story.append(Paragraph(
        "Thank you for completing the e-Prakruti Constitutional Assessment. "
        "Your personalised report is presented below.", S["body"]))

    # ─── ANTHROPOMETRIC METRIC BOXES ─────────────────────────────────────────
    if profile.get("bmi"):
        metrics = [
            (str(profile.get("bmi","—")),  "BMI",        profile.get("bmi_category","")),
            (f"{profile.get('fat_pct','—')}%", "Body Fat %","Medodhatu"),
            (f"{profile.get('bmr','—')} kcal","BMR",      "Daily energy"),
            (f"{profile.get('age','—')} yrs","Age",       "Trividha Kala"),
        ]
        metric_cells = []
        for val, lbl, sub in metrics:
            c = Table([[Paragraph(val, S["mv"])],
                       [Paragraph(lbl, S["ml"])],
                       [Paragraph(sub, S["ml"])]],
                      colWidths=[W/4 - 3*mm])
            c.setStyle(TableStyle([
                ("BACKGROUND",(0,0),(-1,-1), C_CREAM),
                ("TOPPADDING",(0,0),(-1,-1), 4), ("BOTTOMPADDING",(0,0),(-1,-1), 4),
                ("BOX",(0,0),(-1,-1), 0.5, C_GOLD), ("ALIGN",(0,0),(-1,-1), "CENTER"),
            ]))
            metric_cells.append(c)
        mt = Table([metric_cells], colWidths=[W/4]*4, spaceBefore=2*mm, spaceAfter=2*mm)
        mt.setStyle(TableStyle([("ALIGN",(0,0),(-1,-1),"CENTER"),
                                 ("VALIGN",(0,0),(-1,-1),"MIDDLE")]))
        story.append(mt)

    story.append(Spacer(1, 2*mm))

    # ─── TRAIT SUMMARY TABLE ──────────────────────────────────────────────────
    story.append(_sec_hdr("📐 Dosha Dominance — Trait-wise Summary", C_MID, W))
    TRAIT_LIST = ["Physical","Physiological","Psychological","Behavioral"]
    T_ICONS    = {"Physical":"🏃","Physiological":"⚙️",
                  "Psychological":"🧠","Behavioral":"🌿"}
    dmap = {"V":"Vata","P":"Pitta","K":"Kapha"}

    trows = [["Trait","Vata %","Pitta %","Kapha %","Dominant"]]
    for t in TRAIT_LIST:
        p = trait_pct[t]
        trows.append([f"{T_ICONS[t]} {t}",
                      f"{p['V']}%", f"{p['P']}%", f"{p['K']}%",
                      dmap[max(p, key=p.get)]])
    trows.append(["📝 Questionnaire (80%)",
                  f"{quest_op['V']}%", f"{quest_op['P']}%", f"{quest_op['K']}%",
                  dmap[max(quest_op, key=quest_op.get)]])
    trows.append(["📏 Anthropometric (20%)",
                  f"{anthro_op['V']}%", f"{anthro_op['P']}%", f"{anthro_op['K']}%",
                  dmap[max(anthro_op, key=anthro_op.get)]])
    trows.append(["🌿 Your Prakriti",
                  f"{final_op['V']}%", f"{final_op['P']}%", f"{final_op['K']}%",
                  dmap[dom]])

    tt = Table(trows, colWidths=[W*0.35, W*0.13, W*0.13, W*0.13, W*0.26], spaceBefore=2*mm)
    ts_tt = TableStyle([
        ("BACKGROUND",(0,0),(-1,0), C_MID), ("TEXTCOLOR",(0,0),(-1,0), colors.white),
        ("FONTNAME",(0,0),(-1,0), "Helvetica-Bold"),
        ("FONTSIZE",(0,0),(-1,-1), 8.5),
        ("ALIGN",(1,0),(-1,-1),"CENTER"), ("ALIGN",(0,0),(0,-1),"LEFT"),
        ("VALIGN",(0,0),(-1,-1),"MIDDLE"),
        ("TOPPADDING",(0,0),(-1,-1),4), ("BOTTOMPADDING",(0,0),(-1,-1),4),
        ("LEFTPADDING",(0,0),(-1,-1),6), ("RIGHTPADDING",(0,0),(-1,-1),6),
        ("ROWBACKGROUNDS",(0,1),(-1,-1), [C_CREAM, colors.white]),
        ("BOX",(0,0),(-1,-1),0.5,C_MGREY), ("INNERGRID",(0,0),(-1,-1),0.3,C_MGREY),
        ("BACKGROUND",(0,-1),(-1,-1), RLHexColor(pcolor_hex+"22")),
        ("FONTNAME",(0,-1),(-1,-1),"Helvetica-Bold"),
    ])
    tt.setStyle(ts_tt)
    story += [tt, Spacer(1, 3*mm)]

    # ─── PRAKRITI BANNER ──────────────────────────────────────────────────────
    banner = Table([[
        Paragraph(f"{picon}  {pname}", S["prakriti"]),
        Paragraph("Your Ayurvedic Constitutional Type", S["sub"]),
    ]], colWidths=[W])
    banner.setStyle(TableStyle([
        ("BACKGROUND",(0,0),(-1,-1), C_PRAKRITI),
        ("TOPPADDING",(0,0),(-1,-1),8), ("BOTTOMPADDING",(0,0),(-1,-1),8),
        ("ALIGN",(0,0),(-1,-1),"CENTER"),
        ("LINEABOVE",(0,0),(-1,0),3,C_GOLD),
    ]))
    story += [banner, Spacer(1, 4*mm)]

    # ─── DOSHA BARS ───────────────────────────────────────────────────────────
    story.append(_sec_hdr("📊 Final Dosha Distribution (Questionnaire 80% + Anthropometric 20%)",
                           C_MID, W))
    story.append(Spacer(1, 2*mm))
    story.append(_DoshaBarPDF("🌬️  Vata",  final_op["V"], C_VATA,  W))
    story.append(Spacer(1, 1.5*mm))
    story.append(_DoshaBarPDF("🔥  Pitta", final_op["P"], C_PITTA, W))
    story.append(Spacer(1, 1.5*mm))
    story.append(_DoshaBarPDF("🌊  Kapha", final_op["K"], C_KAPHA, W))
    story.append(Spacer(1, 3*mm))

    # ─── PRAKRITI DESCRIPTION (Dual Dosha) ───────────────────────────────────
    story.append(_sec_hdr(f"🌿 Understanding Your {pname}", C_PRAKRITI, W))
    # Pradhana (dominant) Dosha
    d_prad = DESC_PDF[dname]
    story += [Spacer(1, 2*mm),
        Paragraph(f"<b>Pradhana Dosha — {dname}:</b>", S["body"]),
        Paragraph(d_prad["ov"], S["body"]),
        Paragraph("<b>Physical Tendencies:</b>", S["body"]),
        Paragraph(d_prad["ph"], S["body"]),
        Paragraph("<b>Psychological Tendencies:</b>", S["body"]),
        Paragraph(d_prad["ps"], S["body"]),
        Spacer(1, 2*mm),
    ]
    # Anupradhana (secondary) Dosha — always present in Dwandwaja
    pairs_sorted = sorted([("Vata",final_op["V"]),("Pitta",final_op["P"]),
                            ("Kapha",final_op["K"])], key=lambda x:-x[1])
    sec_name = pairs_sorted[1][0]
    if sec_name != dname:
        d_sec = DESC_PDF.get(sec_name, {})
        story += [
            Paragraph(f"<b>Anupradhana Dosha — {sec_name} "
                      f"({final_op[{'Vata':'V','Pitta':'P','Kapha':'K'}[sec_name]]}%):</b>", S["body"]),
            Paragraph(d_sec.get("ov",""), S["body"]),
            Spacer(1, 2*mm),
        ]
    # Combined Dwandwaja insight
    combo_key = (dname, sec_name)
    combo_insights = {
        ("Vata","Pitta"): "Vata-Pitta constitution requires warm, mildly unctuous diet. "
                          "Ghee balances both Doshas. Avoid spicy (Pitta) AND cold/dry (Vata) foods.",
        ("Pitta","Vata"): "Pitta-Vata constitution needs cooling yet nourishing diet. "
                          "Regular meal timing is non-negotiable — addresses both Pitta hunger and Vata irregularity.",
        ("Vata","Kapha"): "Vata-Kapha constitution: avoid cold foods (aggravates both). "
                          "Warm + mildly unctuous + light foods. Digestive spices essential.",
        ("Kapha","Vata"): "Kapha-Vata constitution: reduce quantity (Kapha) but maintain warmth and regularity (Vata). "
                          "Vigorous exercise essential; avoid cold and heavy foods.",
        ("Pitta","Kapha"): "Pitta-Kapha constitution: cooling AND light foods. "
                           "Avoid fried, fermented, heavy foods. Bitter-astringent tastes most beneficial.",
        ("Kapha","Pitta"): "Kapha-Pitta constitution: light, warm diet with moderate spicing. "
                           "Reduce sweet, oily, fermented foods. Exercise is essential.",
    }
    insight = combo_insights.get(combo_key, "")
    if insight:
        story += [Paragraph(f"<b>Dwandwaja Management Principle:</b>", S["body"]),
                  Paragraph(insight, S["body"]), Spacer(1, 3*mm)]

    # ─── DISEASE PRONENESS (Both Doshas) ──────────────────────────────────────
    story.append(_sec_hdr(f"⚕️ Disease Susceptibility — {pname}", C_PITTA, W))
    story.append(Spacer(1, 2*mm))
    story.append(Paragraph(
        "<i>Conditions this Prakriti type is constitutionally susceptible to — not certainties. "
        "Consistent dietary and lifestyle adherence significantly reduces risk.</i>", S["note"]))

    d1_dis = DISEASE_PRONE_PDF.get(dname, [])
    d2_dis = DISEASE_PRONE_PDF.get(sec_name, []) if sec_name != dname else []

    # Two-column table: Pradhana diseases | Secondary diseases
    dis_hdr = [Paragraph(f"<b>{dname} Prakriti Susceptibility</b>", S["th"]),
               Paragraph(f"<b>{sec_name} Prakriti Susceptibility</b>", S["th"])]
    max_rows = max(len(d1_dis), len(d2_dis), 1)
    dis_rows = [dis_hdr]
    for i in range(max_rows):
        c1 = f"• {d1_dis[i]}" if i < len(d1_dis) else ""
        c2 = f"• {d2_dis[i]}" if i < len(d2_dis) else ""
        dis_rows.append([Paragraph(c1, S["bullet"]), Paragraph(c2, S["bullet"])])
    dt2 = Table(dis_rows, colWidths=[W/2, W/2])
    dt2.setStyle(TableStyle([
        ("BACKGROUND",(0,0),(-1,0), C_PITTA), ("TEXTCOLOR",(0,0),(-1,0), colors.white),
        ("FONTNAME",(0,0),(-1,0),"Helvetica-Bold"), ("FONTSIZE",(0,0),(-1,-1),8),
        ("BACKGROUND",(0,1),(-1,-1), C_LGREY),
        ("TOPPADDING",(0,0),(-1,-1),3), ("BOTTOMPADDING",(0,0),(-1,-1),3),
        ("LEFTPADDING",(0,0),(-1,-1),5), ("VALIGN",(0,0),(-1,-1),"TOP"),
        ("BOX",(0,0),(-1,-1),0.4,C_MGREY), ("INNERGRID",(0,0),(-1,-1),0.2,C_MGREY),
    ]))
    story += [dt2, Spacer(1, 3*mm)]

    # ─── PRECAUTIONS ─────────────────────────────────────────────────────────
    story.append(_sec_hdr(f"⚖️ Precautions & Lifestyle — {dname} Prakriti",
                           C_KAPHA, W))
    story.append(Spacer(1, 2*mm))
    for p in PRECAUTIONS_PDF.get(dname, []):
        story.append(Paragraph(f"• {p}", S["bullet"]))
    story.append(Spacer(1, 3*mm))

    # ─── FOOD TABLE from AHARA_DATA (classical names, dual-Dosha filtered) ───
    story.append(_sec_hdr("🥗 Pathya & Apathya — Classical Ahara Guide",
                           C_VATA, W))
    story.append(Spacer(1, 2*mm))
    story.append(Paragraph(
        f"Based on your {pname}, foods are classified per Dosha from the "
        "classical Ayurvedic Pathya-Apathya framework. "
        "Ref: Charaka Sutrasthana 26/43 · Ashtanga Hridaya Sutrasthana 10/17.", S["body"]))
    story.append(Spacer(1, 1*mm))

    # Build AHARA_DATA-based table
    pkey_map = {"Vata":"VP","Pitta":"PP","Kapha":"KP"}
    akey_map = {"Vata":"VA","Pitta":"PA","Kapha":"KA"}
    pk1, ak1 = pkey_map[dname],  akey_map[dname]
    pk2, ak2 = pkey_map[sec_name], akey_map[sec_name]

    ahara_rows = [[
        Paragraph("<b>Category</b>", S["th"]),
        Paragraph(f"<b>Pathya — Favour</b>", S["th"]),
        Paragraph(f"<b>Apathya — Reduce/Avoid</b>", S["th"]),
    ]]
    for cat, items in AHARA_DATA.items():
        favour = [i["name"] for i in items if i[pk1] or i[pk2]]
        avoid  = [i["name"] for i in items if i[ak1] or i[ak2]]
        if favour or avoid:
            # Mark items appearing in BOTH columns with † (favour for Pradhana, avoid for Anupradhana)
            both   = set(favour) & set(avoid)
            favour_str = ", ".join(
                (n + "†" if n in both else n) for n in favour) if favour else "—"
            avoid_str  = ", ".join(
                (n + "†" if n in both else n) for n in avoid)  if avoid  else "—"
            cat_short  = cat.split("(")[0].strip()
            ahara_rows.append([
                Paragraph(cat_short, S["tc"]),
                Paragraph(favour_str, S["tc"]),
                Paragraph(avoid_str,  S["tc"]),
            ])
    aft = Table(ahara_rows, colWidths=[W*0.18, W*0.44, W*0.38], repeatRows=1)
    aft.setStyle(TableStyle([
        ("BACKGROUND",(0,0),(-1,0), C_VATA), ("TEXTCOLOR",(0,0),(-1,0), colors.white),
        ("FONTNAME",(0,0),(-1,0),"Helvetica-Bold"),
        ("FONTSIZE",(0,0),(-1,-1),7.5),
        ("ALIGN",(0,0),(-1,-1),"LEFT"), ("VALIGN",(0,0),(-1,-1),"TOP"),
        ("TOPPADDING",(0,0),(-1,-1),3), ("BOTTOMPADDING",(0,0),(-1,-1),3),
        ("LEFTPADDING",(0,0),(-1,-1),4),
        ("ROWBACKGROUNDS",(0,1),(-1,-1), [C_CREAM, colors.white]),
        ("BOX",(0,0),(-1,-1),0.5,C_MGREY), ("INNERGRID",(0,0),(-1,-1),0.3,C_MGREY),
    ]))
    story += [aft, Spacer(1, 2*mm)]
    story.append(Paragraph(
        "<i>† Beneficial for Pradhana Dosha but reduce for Anupradhana Dosha — "
        "use in moderation and prefer seasonal availability.</i>",
        ParagraphStyle("note_sm", fontSize=7, textColor=colors.grey,
                       fontStyle="italic", leading=9)))
    story.append(Spacer(1, 3*mm))

    # ─── GUNA REFERENCE ───────────────────────────────────────────────────────
    story.append(_sec_hdr("📚 Dosha Guna Reference — Classical Basis", C_MID, W))
    story.append(Spacer(1, 2*mm))
    grow = [
        ["Dosha","Key Gunas (Properties)","Source"],
        ["🌬️ Vata","Ruksha · Laghu · Chala · Shighra · Sheeta · Parusha · Vishada","CS Vim 8/98"],
        ["🔥 Pitta","Ushna · Teekshna · Drava · Visra · Amla · Katuka","CS Vim 8/97"],
        ["🌊 Kapha","Snigdha · Shlakshna · Mridu · Sandra · Manda · Guru · Sheeta","CS Vim 8/96"],
    ]
    gt = Table(grow, colWidths=[W*0.15, W*0.60, W*0.25])
    gt.setStyle(TableStyle([
        ("BACKGROUND",(0,0),(-1,0),C_MID), ("TEXTCOLOR",(0,0),(-1,0),colors.white),
        ("FONTNAME",(0,0),(-1,0),"Helvetica-Bold"),
        ("FONTSIZE",(0,0),(-1,-1),8.5),
        ("ALIGN",(0,0),(-1,-1),"LEFT"), ("VALIGN",(0,0),(-1,-1),"MIDDLE"),
        ("TOPPADDING",(0,0),(-1,-1),4), ("BOTTOMPADDING",(0,0),(-1,-1),4),
        ("LEFTPADDING",(0,0),(-1,-1),6),
        ("ROWBACKGROUNDS",(0,1),(-1,-1),
         [RLHexColor("#D6E4F7"), RLHexColor("#FAE0D6"), RLHexColor("#D4EEE0")]),
        ("BOX",(0,0),(-1,-1),0.5,C_MGREY), ("INNERGRID",(0,0),(-1,-1),0.3,C_MGREY),
    ]))
    story += [gt, Spacer(1, 4*mm)]

    # ─── DISCLAIMER + FOOTER ─────────────────────────────────────────────────
    story.append(HRFlowable(width=W, thickness=0.5, color=C_GOLD))
    story.append(Spacer(1, 2*mm))
    story.append(Paragraph(
        "<b>DISCLAIMER:</b> This report provides an indicative Deha Prakriti profile based on "
        "self-reported information and objective anthropometric parameters. Final scores integrate "
        "questionnaire responses (80%) with anthropometric measurements (20%). "
        "This report is <b>not a substitute for professional medical advice</b>. "
        "For clinical application in disease management or treatment planning, "
        "validation by a qualified Vaidya is essential. "
        "Disease proneness indicates susceptibility — not certainty.",
        S["disc"]))
    story.append(Spacer(1, 2*mm))

    ftr = Table([[
        Paragraph(
            f"<b>Generated by:</b> e-Prakruti v6.0 | SKAMC, Bangalore<br/>"
            f"<b>Author:</b> Dr. Prasanna Kulkarni — MD Ayurveda, MS Data Science<br/>"
            f"<b>Institution:</b> Sri Kalabyraveshwara Swamy AMC, Bangalore",
            S["footer"]),
        Paragraph(
            f"<b>Date:</b> {today}<br/>"
            f"<b>Research:</b> RGUHS Grant-in-Aid Project 2024-25<br/>"
            f"<b>Classical Basis:</b> Charaka · Sushruta · AH",
            S["footerr"]),
    ]], colWidths=[W*0.6, W*0.4])
    ftr.setStyle(TableStyle([
        ("BACKGROUND",(0,0),(-1,-1),C_CREAM),
        ("TOPPADDING",(0,0),(-1,-1),5), ("BOTTOMPADDING",(0,0),(-1,-1),5),
        ("LEFTPADDING",(0,0),(-1,-1),8), ("RIGHTPADDING",(0,0),(-1,-1),8),
        ("VALIGN",(0,0),(-1,-1),"MIDDLE"),
        ("BOX",(0,0),(-1,-1),0.5,C_GOLD),
    ]))
    story.append(ftr)

    doc.build(story)
    buf.seek(0)
    return buf.read()



if not st.session_state.show_results:

    # ── Warn before reload / tab close ───────────────────────────────────────
    import streamlit.components.v1 as _cmp
    _cmp.html("""<script>
    window.addEventListener('beforeunload', function(e) {
        e.preventDefault();
        e.returnValue = 'Your assessment responses will be lost if you reload or close. Are you sure?';
        return e.returnValue;
    });
    </script>""", height=0)

    tab_labels = (["📏 Anthropometric"] +
                  [f"{TRAIT_ICONS[t]} {t}" for t in TRAITS] +
                  ["🍽️ Ahara & Desha", "📊 View Results"])
    tabs = st.tabs(tab_labels)
    # tab indices: 0=Anthro, 1=Physical, 2=Physiological, 3=Psychological, 4=Behavioral, 5=Ahara, 6=Results

    # ─────────────────────────────────────────────────────────────────────────
    #  TAB 0 — ANTHROPOMETRIC
    # ─────────────────────────────────────────────────────────────────────────
    with tabs[0]:
        st.markdown('<div class="anthro-header">📏 Anthropometric Assessment — Shareera Mana</div>',
                    unsafe_allow_html=True)
        st.markdown(
            "*Objective body measurements that contribute 20% to your final Prakriti determination. "
            "Based on Charaka Sharira Sthana 4/34-36 — Shareera Saara (tissue excellence) principles.*")

        st.markdown('<div class="anthro-card">', unsafe_allow_html=True)
        st.markdown("#### 👤 Personal Information")
        c1, c2, c3 = st.columns(3)
        with c1:
            name = st.text_input("Full Name *", value=st.session_state.profile.get("name",""),
                                  placeholder="Dr. / Mr. / Ms. — Required")
            if not st.session_state.profile.get("name","") and not name:
                st.caption("🔴 Name is required to personalise your report and AI prompt.")
        with c2:
            dob = st.date_input("Date of Birth",
                                value=st.session_state.profile.get("dob", date(1990,1,1)),
                                min_value=date(1920,1,1), max_value=date.today())
            age = date.today().year - dob.year - (
                (date.today().month, date.today().day) < (dob.month, dob.day))
            st.caption(f"Age: **{age} years** — "
                       f"{'Vata Kala (>60)' if age>60 else 'Pitta Kala (16-60)' if age>16 else 'Kapha Kala (<16)'}")
        with c3:
            gender = st.selectbox("Gender", ["Male","Female"],
                                  index=["Male","Female"].index(
                                      st.session_state.profile.get("gender","Male")))
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<div class="anthro-card">', unsafe_allow_html=True)
        st.markdown("#### 📐 Body Measurements")
        m1, m2 = st.columns(2)
        with m1:
            height = st.number_input("Height (cm)", min_value=100.0, max_value=250.0,
                                      value=float(st.session_state.profile.get("height_cm",165)),
                                      step=0.5)
        with m2:
            weight = st.number_input("Weight (kg)", min_value=20.0, max_value=300.0,
                                      value=float(st.session_state.profile.get("weight_kg",65)),
                                      step=0.5)

        # Live calculations
        if height > 0 and weight > 0:
            bmi    = calc_bmi(weight, height)
            bmr    = calc_bmr(weight, height, age, gender)
            fat    = calc_fat_pct(bmi, age, gender)
            sbmr   = specific_bmr(bmr, weight)
            bmi_cat = bmi_category(bmi)

            st.markdown("##### 📊 Calculated Parameters")
            mc = st.columns(4)
            with mc[0]:
                st.markdown(f'<div class="metric-box"><div class="metric-val">{bmi}</div>'
                            f'<div class="metric-lbl">BMI (kg/m²)</div>'
                            f'<div class="metric-sub">{bmi_cat}</div></div>',
                            unsafe_allow_html=True)
            with mc[1]:
                st.markdown(f'<div class="metric-box"><div class="metric-val">{bmr}</div>'
                            f'<div class="metric-lbl">BMR (kcal/day)</div>'
                            f'<div class="metric-sub">Daily energy need</div></div>',
                            unsafe_allow_html=True)
            with mc[2]:
                st.markdown(f'<div class="metric-box"><div class="metric-val">{fat}%</div>'
                            f'<div class="metric-lbl">Body Fat %</div>'
                            f'<div class="metric-sub">Medodhatu assessment</div></div>',
                            unsafe_allow_html=True)
            with mc[3]:
                st.markdown(f'<div class="metric-box"><div class="metric-val">{sbmr}</div>'
                            f'<div class="metric-lbl">Specific BMR (kcal/kg)</div>'
                            f'<div class="metric-sub">Agni strength indicator</div></div>',
                            unsafe_allow_html=True)

            # Ayurvedic interpretation
            st.markdown("##### 🌿 Ayurvedic Interpretation")
            interp = []
            if bmi < 18.5:
                interp.append("🌬️ **BMI < 18.5** — Apachita Shareera. Indicates Vata dominance (Ruksha, Laghu Gunas). Low Medodhatu.")
            elif bmi < 25:
                interp.append("🔥 **BMI 18.5–24.9** — Madhyama Shareera. Indicates balanced Pitta tendency. Optimal Mamsa and Medodhatu.")
            elif bmi < 30:
                interp.append("🌊 **BMI 25–29.9** — Upachita tendency. Indicates Kapha influence. Medodhatu moderately elevated.")
            else:
                interp.append("🌊 **BMI ≥ 30** — Sthula Shareera. Strong Kapha dominance. Medovriddhi (excess Medodhatu).")

            if sbmr > 25:
                interp.append("🔥 **High Specific BMR** — Teekshna Agni. Pitta metabolic strength.")
            elif sbmr < 19:
                interp.append("🌊 **Low Specific BMR** — Manda Agni. Kapha metabolic pattern.")

            if age > 60:
                interp.append("🌬️ **Age > 60** — Vata Kala (Charaka Sharira Sthana 4/34). Natural Vata increase with aging.")

            for i in interp:
                st.markdown(f"- {i}")

        st.markdown('</div>', unsafe_allow_html=True)

        # Optional WHR
        st.markdown('<div class="anthro-card">', unsafe_allow_html=True)
        st.markdown(
            '<div class="optional-note">⚪ <strong>Optional:</strong> Waist-Hip Ratio (WHR) '
            '— improves central obesity / Medovriddhi assessment. '
            'Measure at navel level (waist) and widest point of hips.</div>',
            unsafe_allow_html=True)
        w1, w2 = st.columns(2)
        with w1:
            waist = st.number_input("Waist circumference (cm) — optional",
                                     min_value=0.0, max_value=200.0,
                                     value=float(st.session_state.profile.get("waist_cm",0)),
                                     step=0.5)
        with w2:
            hip = st.number_input("Hip circumference (cm) — optional",
                                    min_value=0.0, max_value=200.0,
                                    value=float(st.session_state.profile.get("hip_cm",0)),
                                    step=0.5)
        if waist > 0 and hip > 0:
            whr = calc_whr(waist, hip)
            risk = ("High risk" if (gender=="Male" and whr>=1.0) or (gender=="Female" and whr>=0.90)
                    else "Moderate risk" if (gender=="Male" and whr>=0.90) or (gender=="Female" and whr>=0.80)
                    else "Normal")
            st.metric("WHR", f"{whr}", f"{risk} — {'Medovriddhi' if 'High' in risk else 'Moderate Meda' if 'Mod' in risk else 'Normal Medodhatu'}")
        else:
            whr = None
        st.markdown('</div>', unsafe_allow_html=True)

        # Save profile
        if st.button("💾 Save Anthropometric Data", type="primary", use_container_width=True):
            if not name.strip():
                st.error("🚫 **Name is required.** Please enter your full name before saving.")
            elif height > 0 and weight > 0:
                bmi_  = calc_bmi(weight, height)
                bmr_  = calc_bmr(weight, height, age, gender)
                fat_  = calc_fat_pct(bmi_, age, gender)
                sbmr_ = specific_bmr(bmr_, weight)
                whr_  = calc_whr(waist, hip) if waist > 0 and hip > 0 else None
                st.session_state.profile = {
                    "name":       name,
                    "dob":        dob,
                    "age":        age,
                    "gender":     gender,
                    "height_cm":  height,
                    "weight_kg":  weight,
                    "waist_cm":   waist,
                    "hip_cm":     hip,
                    "bmi":        bmi_,
                    "bmr":        bmr_,
                    "fat_pct":    fat_,
                    "specific_bmr": sbmr_,
                    "whr":        whr_,
                }
                st.success(f"✅ Profile saved for **{name or 'User'}** | "
                           f"BMI: {bmi_} | BMR: {bmr_} kcal | Body Fat: {fat_}%")
            else:
                st.warning("Please enter Height and Weight to save.")

    # ─────────────────────────────────────────────────────────────────────────
    #  TABS 1–4 — QUESTION TRAITS
    # ─────────────────────────────────────────────────────────────────────────
    for tidx, trait in enumerate(TRAITS):
        qs = TRAIT_Q[trait]
        with tabs[tidx + 1]:
            # Point 4 FIX: compute count fresh every render cycle
            answered_t = sum(
                1 for q in qs
                if (q["type"]=="single" and isinstance(st.session_state.responses.get(q["id"]), int))
                or (q["type"]=="multi"  and len(st.session_state.responses.get(q["id"], set())) > 0)
            )
            total_t = len(qs)
            st.markdown(
                f'<div class="trait-header">{TRAIT_ICONS[trait]} {trait} Trait'
                f' &nbsp;|&nbsp; {total_t} Questions'
                f' &nbsp;|&nbsp; ✅ {answered_t} / {total_t} answered</div>',
                unsafe_allow_html=True)

            for q in qs:
                qid  = q["id"]
                opts = q["options"]
                lbls = [o["text"] for o in opts]

                st.markdown('<div class="question-card">', unsafe_allow_html=True)

                multi_tag = (' <span style="font-size:.78em;color:#8B4513;font-style:italic;">'
                             '(select all that apply)</span>') if q["type"] == "multi" else ""
                mand_tag  = (' <span style="color:#c0392b;font-weight:900;font-size:1em;" '
                             'title="Mandatory question">*</span>') if qid in MANDATORY_QS else ""
                st.markdown(
                    f'<div class="q-title">'
                    f'<span class="q-num">{qid}</span>'
                    f'{q["question"]}{multi_tag}{mand_tag}</div>',
                    unsafe_allow_html=True)

                ecol1, ecol2 = st.columns([1,1])
                with ecol1:
                    if q.get("svg"):
                        show_svg(q["svg"], "🖼️ View Reference Illustration")
                with ecol2:
                    with st.expander("📖 Learn More — Guna & Classical Reference"):
                        st.markdown(f'<span class="badge">🏷️ {q["guna"]}</span>',
                                    unsafe_allow_html=True)
                        st.markdown(f'<span class="badge">📚 {q["reference"]}</span>',
                                    unsafe_allow_html=True)
                        st.markdown("")
                        st.markdown(q["learn_more"])

                if q["type"] == "single":
                    cur = st.session_state.responses.get(qid, None)
                    idx = cur if isinstance(cur, int) else None
                    ch  = st.radio("", lbls, index=idx, key=f"q{qid}",
                                   label_visibility="collapsed")
                    if ch is not None:
                        st.session_state.responses[qid] = lbls.index(ch)
                else:
                    cs = st.session_state.responses.get(qid, set())
                    ns = set()
                    for i, opt in enumerate(opts):
                        checked = st.checkbox(opt["text"], value=(i in cs), key=f"q{qid}_{i}")
                        if checked: ns.add(i)
                        if opt.get("svg"):
                            show_svg(opt["svg"],
                                     f"🖼️ See: {opt['text'][:35]}...",
                                     use_expander=True)
                    st.session_state.responses[qid] = ns

                # Point 5 — Inline conflict check for intra-question conflicts
                _intra = [c for c in CONFLICT_PAIRS
                          if c["type"]=="intra" and c["qa"]==qid
                          and c["id"] not in st.session_state.conflict_overrides]
                for _c in _intra:
                    _r = st.session_state.responses.get(qid, set())
                    if isinstance(_r, set) and _c["opt_a"] in _r and _c["opt_b"] in _r:
                        st.warning(f"⚠️ **Consistency note — Q{qid}:** {_c['msg']}")
                        if st.button(f"✅ I confirm — both apply to me ({_c['id']})",
                                     key=f"inline_ovr_{_c['id']}"):
                            st.session_state.conflict_overrides.add(_c["id"])
                            st.rerun()

                st.markdown('</div>', unsafe_allow_html=True)
                st.markdown("")


            # Bottom navigation — use JS to directly click Streamlit's tab buttons
            # Tab indices in UI: 0=Anthro, 1=Physical, 2=Physio, 3=Psych, 4=Behavioral, 5=Ahara, 6=Results
            _ui_idx       = tidx + 1          # this tab's UI index
            _prev_ui_idx  = _ui_idx - 1       # previous tab
            _next_ui_idx  = _ui_idx + 1       # next tab

            if tidx < len(TRAITS)-1:
                _next_label = f"{TRAIT_ICONS[TRAITS[tidx+1]]} {TRAITS[tidx+1]}"
            else:
                _next_label = "🍽️ Ahara & Desha"

            _prev_label = (f"{TRAIT_ICONS[TRAITS[tidx-1]]} {TRAITS[tidx-1]}"
                           if tidx > 0 else "📏 Anthropometric")

            import streamlit.components.v1 as _cv1_nav
            _cv1_nav.html(f"""
<style>
.nav-wrap {{display:flex;gap:8px;margin:8px 0;width:100%;}}
.nav-btn {{flex:1;padding:10px 14px;border:none;border-radius:8px;
           font-size:13px;font-weight:600;cursor:pointer;transition:background .2s;}}
.nav-prev {{background:#f0e8d8;color:#3d1a06;}}
.nav-prev:hover {{background:#e0d0b0;}}
.nav-next {{background:#3d1a06;color:white;}}
.nav-next:hover {{background:#6b2e0a;}}
.nav-mid  {{flex:2;background:transparent;border:1px solid #ddd;
            color:#888;font-size:12px;text-align:center;}}
</style>
<div class="nav-wrap">
  {'<button class="nav-btn nav-prev" onclick="goTab(' + str(_prev_ui_idx) + ')">← ' + _prev_label + '</button>' if _ui_idx > 0 else '<div style="flex:1"></div>'}
  <button class="nav-btn nav-mid" disabled>✅ {answered_t}/{total_t} answered</button>
  <button class="nav-next nav-btn" onclick="goTab({_next_ui_idx})">{_next_label} →</button>
</div>
<script>
function goTab(idx) {{
  var tabs = window.parent.document.querySelectorAll('button[data-baseweb="tab"]');
  if (tabs && tabs[idx]) {{
    tabs[idx].click();
    window.parent.scrollTo({{top: 0, behavior: 'smooth'}});
  }}
}}
</script>
""", height=58)


    # ─────────────────────────────────────────────────────────────────────────
    #  TAB 5 — AHARA & DESHA (dedicated tab)
    # ─────────────────────────────────────────────────────────────────────────
    with tabs[5]:
        st.markdown('<div class="anthro-header">🍽️ Ahara Preferences & Desha — Dietary Context</div>',
                    unsafe_allow_html=True)
        st.markdown(
            "*These inputs personalise your AI-generated dietary recommendations and filter "
            "food suggestions based on your dietary practice. "
            "Ref: Charaka Sutrasthana 27/16-18 — Desha Vibhaga.*")

        st.markdown('<div class="anthro-card">', unsafe_allow_html=True)
        st.markdown("#### 🥗 Dietary Preference")
        dp_opts = ["Vegan (plant-based only)",
                   "Lacto-Vegetarian (plant + milk products)",
                   "Ovo-Vegetarian (plant + eggs)",
                   "Mixed (Non-vegetarian)"]
        cur_dp  = st.session_state.get("dietary_pref","Lacto-Vegetarian (plant + milk products)")
        dp_idx  = dp_opts.index(cur_dp) if cur_dp in dp_opts else 1
        dietary_sel = st.selectbox("Select your dietary pattern", dp_opts,
                                    index=dp_idx, key="dp_sel")
        st.session_state.dietary_pref = dietary_sel

        if dietary_sel == "Mixed (Non-vegetarian)":
            mf = st.slider("Number of non-vegetarian meals per week",
                           min_value=1, max_value=7,
                           value=st.session_state.get("meat_freq",3), key="mf_sel")
            st.session_state.meat_freq = mf
            st.caption(f"Selected: **{mf} non-veg meals/week**")

        # Show which categories will be shown/hidden
        if dietary_sel == "Vegan (plant-based only)":
            st.info("🌱 Mamsa (meat) and Dugdha (dairy) categories will be hidden from Ahara recommendations.")
        elif dietary_sel == "Lacto-Vegetarian (plant + milk products)":
            st.info("🥛 Mamsa (meat) category will be hidden. Dairy products shown.")
        elif dietary_sel == "Ovo-Vegetarian (plant + eggs)":
            st.info("🥚 Mamsa (meat, except eggs) will be hidden. Eggs (Anda) shown.")
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<div class="anthro-card">', unsafe_allow_html=True)
        st.markdown("#### 📍 Location — Desha Classification")
        st.caption("Your location determines the Ayurvedic Desha type which modifies dietary recommendations.")
        all_states = sorted(INDIA_GEO.keys())
        cur_state  = st.session_state.get("state","Karnataka")
        s_idx = all_states.index(cur_state) if cur_state in all_states else 0
        sel_state = st.selectbox("State / Union Territory", all_states,
                                  index=s_idx, key="st_sel")
        st.session_state.state = sel_state

        dist_list = sorted(INDIA_GEO.get(sel_state,{}).get("districts",{}).keys())
        cur_dist  = st.session_state.get("district","")
        if dist_list:
            d_idx = dist_list.index(cur_dist) if cur_dist in dist_list else 0
            sel_dist = st.selectbox("District", dist_list, index=d_idx, key="dist_sel")
        else:
            sel_dist = st.text_input("District", value=cur_dist, key="dist_sel")
        st.session_state.district = sel_dist

        auto_desha = get_desha(sel_state, sel_dist)
        st.session_state.desha = auto_desha
        st.markdown(
            f'<div class="adj-box"><div class="adj-title">🗺️ Desha (Auto-determined)</div>'
            f'{DESHA_DESCRIPTIONS.get(auto_desha, auto_desha)}</div>',
            unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

        st.success("✅ Dietary preference and location saved automatically. "
                   "Proceed to **📊 View Results** when you have completed all questions.")

        # Nav buttons for Ahara tab (tab index 5 → prev=4 Behavioral, next=6 Results)
        import streamlit.components.v1 as _cv1_ahara_nav
        _cv1_ahara_nav.html("""
<style>
.nav-wrap2{display:flex;gap:8px;margin:12px 0;width:100%;}
.nav-btn2{flex:1;padding:10px 14px;border:none;border-radius:8px;
          font-size:13px;font-weight:600;cursor:pointer;transition:background .2s;}
.nav-prev2{background:#f0e8d8;color:#3d1a06;}
.nav-prev2:hover{background:#e0d0b0;}
.nav-next2{background:#3d1a06;color:white;}
.nav-next2:hover{background:#6b2e0a;}
</style>
<div class="nav-wrap2">
  <button class="nav-btn2 nav-prev2" onclick="goTabA(4)">← 🌿 Behavioral</button>
  <button class="nav-btn2 nav-next2" onclick="goTabA(6)">📊 View Results →</button>
</div>
<script>
function goTabA(idx){
  var tabs=window.parent.document.querySelectorAll('button[data-baseweb="tab"]');
  if(tabs&&tabs[idx]){tabs[idx].click();window.parent.scrollTo({top:0,behavior:'smooth'});}
}
</script>
""", height=58)

    # ─────────────────────────────────────────────────────────────────────────
    #  TAB 6 — VIEW RESULTS
    # ─────────────────────────────────────────────────────────────────────────
    with tabs[6]:
        done = len([
            q["id"] for q in QUESTIONS
            if (q["type"]=="single" and isinstance(st.session_state.responses.get(q["id"]), int))
            or (q["type"]=="multi"  and len(st.session_state.responses.get(q["id"], set())) > 0)
        ])
        min_q        = int(len(QUESTIONS) * 0.70)
        has_ht       = st.session_state.profile.get("height_cm",0) > 0
        has_wt       = st.session_state.profile.get("weight_kg",0) > 0
        missing_mand = check_mandatory_answered()
        conflicts    = check_conflicts(st.session_state.responses)
        strong_conf  = [c for c in conflicts if c["severity"]=="strong"
                        and c["id"] not in st.session_state.conflict_overrides]
        mod_conf     = [c for c in conflicts if c["severity"] in ("moderate","advisory")
                        and c["id"] not in st.session_state.conflict_overrides]

        st.markdown(f"**📊 Progress:** {done}/{len(QUESTIONS)} questions answered")
        st.progress(done / len(QUESTIONS))

        if conflicts:
            st.markdown("### ⚠️ Consistency Checks")
            for c in strong_conf:
                st.warning(f"🔴 **[{c['id']}] Strong conflict:** {c['msg']}")
                if st.button(f"✅ I confirm this is correct ({c['id']})", key=f"ovr_{c['id']}"):
                    st.session_state.conflict_overrides.add(c["id"])
                    st.rerun()
            for c in mod_conf:
                st.info(f"🟡 **[{c['id']}] Advisory:** {c['msg']}")
                if st.button(f"✅ Confirmed ({c['id']})", key=f"ovr_{c['id']}"):
                    st.session_state.conflict_overrides.add(c["id"])
                    st.rerun()

        if missing_mand:
            mand_q_text = ", ".join([
                f"Q{qid} ({next((q['question'][:35] for q in QUESTIONS if q['id']==qid), '')}…)"
                for qid in sorted(missing_mand)
            ])
            st.error(f"🚫 **Mandatory questions not answered:**\n\n{mand_q_text}\n\nPlease complete these.")
        elif done < min_q:
            st.warning(f"⚠️ Please answer at least {min_q} questions. Currently: {done}/{len(QUESTIONS)}")
        elif strong_conf:
            st.error("🚫 Please resolve or confirm the strong conflicts above before proceeding.")
        else:
            st.success(f"✅ {done}/{len(QUESTIONS)} questions answered · All checks complete.")
            if not (has_ht and has_wt):
                st.info("ℹ️ Height & Weight not saved — Anthropometric scoring will use balanced defaults.")
            if not st.session_state.profile.get("name","").strip():
                st.warning("⚠️ **Name not saved yet.** Please go to the 📏 Anthropometric tab, "
                           "enter your name and click Save — your name is required to personalise "
                           "your report and AI prompt.")
            else:
                if st.button("🌿 Calculate My Prakriti", type="primary", use_container_width=True):
                    st.session_state.show_results   = True
                    st.session_state.research_saved = False
                    st.rerun()
# ══════════════════════════════════════════════════════════════════════════════
# ══════════════════════════════════════════════════════════════════════════════
#  RESULTS PAGE
# ══════════════════════════════════════════════════════════════════════════════
else:
    prof = st.session_state.profile
    has_anthro = prof.get("height_cm",0) > 0 and prof.get("weight_kg",0) > 0

    # ── Compute all scores ────────────────────────────────────────────────────
    trait_pct, quest_op = calculate_questionnaire(st.session_state.responses)

    if has_anthro:
        anthro_op = score_anthropometric(prof)
    else:
        anthro_op = {"V":33.3,"P":33.3,"K":33.4}   # neutral default

    final_op  = combine_scores(quest_op, anthro_op, 0.80, 0.20)
    pname, picon, pcolor = prakriti_type(final_op)

    # ── Header ────────────────────────────────────────────────────────────────
    name_str = prof.get("name","")
    if name_str:
        st.markdown(f"## 📊 Prakriti Assessment Results — *{name_str}*")
    else:
        st.markdown("## 📊 Your Prakriti Assessment Results")

    st.markdown(
        f'<div class="prakriti-banner" '
        f'style="background:{pcolor}18;border:3px solid {pcolor};color:{pcolor};">'
        f'{picon} {pname}</div>',
        unsafe_allow_html=True)

    if has_anthro:
        st.markdown(
            f'<div class="adj-box"><div class="adj-title">📏 Anthropometric Factors Considered</div>'
            f'BMI: <b>{prof["bmi"]}</b> ({bmi_category(prof["bmi"])}) &nbsp;|&nbsp; '
            f'Body Fat: <b>{prof["fat_pct"]}%</b> &nbsp;|&nbsp; '
            f'BMR: <b>{prof["bmr"]} kcal/day</b> &nbsp;|&nbsp; '
            f'Specific BMR: <b>{prof["specific_bmr"]} kcal/kg</b> &nbsp;|&nbsp; '
            f'Age: <b>{prof["age"]} yrs</b>'
            + (f' &nbsp;|&nbsp; WHR: <b>{prof["whr"]}</b>' if prof.get("whr") else '')
            + '</div>', unsafe_allow_html=True)

    st.markdown("---")

    # ── Results sub-tabs ──────────────────────────────────────────────────────
    res_tab1, res_tab2, res_tab3, res_tab4 = st.tabs([
        "📊 Assessment Results",
        "🥗 Ahara Guide — Pathya & Apathya",
        "📥 Research Data Export",
        "🤖 AI Prompt Generator",
    ])

    # ════════════════════════════════════════════════════════════════════════
    with res_tab1:

        # ── Prakriti Result Card (clean, no methodology labels) ──────────────
        dom_pct  = final_op[{"Vata":"V","Pitta":"P","Kapha":"K"}[
                   {"Vata Pradhana":"Vata","Pitta Pradhana":"Pitta","Kapha Pradhana":"Kapha"}.get(
                   pname.split(" ")[0]+" "+pname.split(" ")[1] if len(pname.split())>1 else "Vata","Vata")]]
        # Simpler: just get the highest dosha
        dom_letter = max(final_op, key=final_op.get)
        dom_full   = {"V":"Vata","P":"Pitta","K":"Kapha"}[dom_letter]

        st.markdown(
            f'<div class="result-card" style="border-left:5px solid {pcolor};">'
            f'<div style="display:flex;align-items:center;gap:16px;flex-wrap:wrap;">'
            f'<div style="flex:1;min-width:200px;">'
            f'<div style="font-size:.82em;color:#888;margin-bottom:4px;font-weight:600;">YOUR PRAKRITI</div>'
            f'<div style="font-family:Georgia,serif;font-size:1.6em;font-weight:700;color:{pcolor};">'
            f'{picon} {pname}</div>'
            f'</div>'
            f'<div style="flex:2;min-width:240px;">'
            + three_bars(final_op) +
            f'</div></div></div>',
            unsafe_allow_html=True)

        st.markdown("")

        # ── Detailed breakdown in expander (for reference / research) ────────
        with st.expander("📊 See detailed Dosha breakdown", expanded=False):
            sc1, sc2 = st.columns(2)
            with sc1:
                st.markdown('<div class="result-card">', unsafe_allow_html=True)
                st.markdown("##### 📝 Questionnaire")
                st.markdown(three_bars(quest_op), unsafe_allow_html=True)
                q1,q2,q3 = st.columns(3)
                q1.metric("🌬️ Vata",  f"{quest_op['V']}%")
                q2.metric("🔥 Pitta", f"{quest_op['P']}%")
                q3.metric("🌊 Kapha", f"{quest_op['K']}%")
                st.markdown('</div>', unsafe_allow_html=True)
            with sc2:
                st.markdown('<div class="result-card">', unsafe_allow_html=True)
                st.markdown("##### 📏 Anthropometric")
                if has_anthro:
                    st.markdown(three_bars(anthro_op), unsafe_allow_html=True)
                    a1,a2,a3 = st.columns(3)
                    a1.metric("🌬️ Vata",  f"{anthro_op['V']}%")
                    a2.metric("🔥 Pitta", f"{anthro_op['P']}%")
                    a3.metric("🌊 Kapha", f"{anthro_op['K']}%")
                else:
                    st.info("No anthropometric data — add in the 📏 tab.")
                st.markdown('</div>', unsafe_allow_html=True)

        st.markdown("---")

        # ── Trait-wise breakdown ──────────────────────────────────────────────────
        st.markdown("### 📐 Dosha Expression Across All 4 Traits")
        c_left, c_right = st.columns(2)
        for i, trait in enumerate(TRAITS):
            with (c_left if i%2==0 else c_right):
                p = trait_pct[trait]
                st.markdown('<div class="result-card">', unsafe_allow_html=True)
                st.markdown(f"**{TRAIT_ICONS[trait]} {trait} Trait**")
                st.markdown(three_bars(p), unsafe_allow_html=True)
                t1,t2,t3 = st.columns(3)
                t1.metric("Vata",  f"{p['V']}%")
                t2.metric("Pitta", f"{p['P']}%")
                t3.metric("Kapha", f"{p['K']}%")
                st.markdown('</div>', unsafe_allow_html=True)
                st.markdown("")

        # ── Trait summary table ───────────────────────────────────────────────────
        st.markdown("### 📋 Trait Summary")
        rows = []
        for t in TRAITS:
            p = trait_pct[t]
            dom = {"V":"Vata","P":"Pitta","K":"Kapha"}[max(p, key=p.get)]
            rows.append({"Trait":f"{TRAIT_ICONS[t]} {t}",
                         "Vata %":p["V"],"Pitta %":p["P"],"Kapha %":p["K"],"Dominant":dom})
        rows.append({"Trait":"🌿 Your Prakriti",
                     "Vata %":final_op["V"],"Pitta %":final_op["P"],"Kapha %":final_op["K"],
                     "Dominant":{"V":"Vata","P":"Pitta","K":"Kapha"}[max(final_op,key=final_op.get)]})
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

        st.markdown("---")

        # ── Prakriti Description ──────────────────────────────────────────────────
        dom_name = {"V":"Vata","P":"Pitta","K":"Kapha"}[max(final_op, key=final_op.get)]
        DESCS = {
            "Vata":{
                "shloka":"रूक्षो लघुश्चलः शीघ्रः शीतो बहुसूक्ष्म एव च",
                "shloka_src":"Charaka Vimana Sthana 8/96 — Gunas of Vata",
                "ov":"Vata Prakriti individuals are governed by Akasha and Vayu — naturally creative, enthusiastic, quick-thinking, highly communicative, and spontaneous. They initiate rapidly and adapt easily to change.",
                "ph":"Lean / thin build (Apachita) · Dry skin (Ruksha Tvak) · Rough hair · Prominent veins and tendons · Variable appetite · Light, insufficient sleep · Constipation (Vibandha) · Cold extremities · Cracking joints",
                "ps":"Quick grasping but weak long-term retention (Chala Smriti) · Creative and imaginative mind · Tendency toward anxiety and worry (Bhaya-Udvega) · Indecisive (Anavasthita Chitta) · Frequent mood changes",
                "di":"Warm, oily, sweet, sour, and salty foods (Ushna-Snigdha Ahara). Regular mealtimes essential — never skip meals. Avoid cold, dry, raw, and stale foods. Daily Abhyanga (warm oil self-massage) highly beneficial.",
                "ls":"Establish a very regular Dinacharya (daily routine). Adequate rest (7-8 hours). Avoid excessive travel, prolonged fasting, and late-night activity. Gentle, consistent exercise — Yoga and walking preferred."},
            "Pitta":{
                "shloka":"तीक्ष्णोष्णं लघु विस्रं च द्रवं चलं च पित्तकम्",
                "shloka_src":"Charaka Vimana Sthana 8/96 — Gunas of Pitta",
                "ov":"Pitta Prakriti individuals are governed by Agni and Jala — naturally intelligent, organised, purposeful, and passionately driven. They transform ideas into results with focused intensity.",
                "ph":"Medium well-proportioned build · Fair/yellowish complexion · Soft skin prone to rashes and freckles · Early greying tendency · Profuse sweating (Prabhuta Sweda) · Intense hunger and thirst · Regular bowel evacuation",
                "ps":"Sharp analytical mind (Medhavi) · Excellent comprehension · Short-tempered but quick to cool (Kshipra Kopa / Kshipra Prasaada) · Perfectionist · Competitive · Principled · Strong convictions",
                "di":"Cool, sweet, bitter, and astringent foods (Sheeta-Madhura Ahara). Avoid spicy, sour, fried, and fermented foods. Coconut, ghee, and bitter vegetables are beneficial. Never skip meals — intense hunger destabilises Pitta.",
                "ls":"Avoid excessive heat and sun exposure. Moderate, non-competitive exercise to prevent overheating. Cooling Pranayama (Sheetali, Sheetkari). Meditation for anger management. Regular leisure time is essential."},
            "Kapha":{
                "shloka":"स्निग्धः शीतो गुरुर्मन्दः श्लक्ष्णो मृत्स्नः स्थिरः कफः",
                "shloka_src":"Charaka Vimana Sthana 8/96 — Gunas of Kapha",
                "ov":"Kapha Prakriti individuals are governed by Prithvi and Jala — naturally calm, patient, deeply affectionate, remarkably enduring, and profoundly loyal. They provide the stability that sustains all endeavours.",
                "ph":"Heavy well-built frame (Upachita Shareera) · Fair lustrous skin (Gaur Tvak) · Thick dense hair · Big beautiful steady eyes (Vishalaksha) · Deep sound sleep · Slow metabolism (Manda Agni) · Excellent physical endurance (Balavan)",
                "ps":"Slow but excellent long-term memory (Smritimaan) · Calm temperament · Very stable relationships (Sthira Sauhrida) · Patient and generous · Deeply loyal · Strong self-control (Alaulupa) · Resistant to change",
                "di":"Light, warm, pungent, bitter, and astringent foods (Laghu-Ushna-Tikta Ahara). Avoid heavy, oily, sweet, cold, and excessive foods. Ginger, black pepper, honey, and periodic fasting are beneficial.",
                "ls":"Regular vigorous exercise (45+ min daily) — essential, not optional. Seek variety and new stimulation. Avoid sedentary lifestyle, daytime sleeping, and oversleeping. Social engagement and new challenges are important."}
        }
        d = DESCS[dom_name]
        st.markdown(f"### 🌿 Understanding Your {pname}")
        st.markdown(
            f'<div class="shloka-box">'
            f'<div class="shloka-text">{d["shloka"]}</div>'
            f'<div class="shloka-ref">— {d["shloka_src"]}</div>'
            f'</div>', unsafe_allow_html=True)

        dl, dr = st.columns(2)
        with dl:
            st.markdown('<div class="result-card">', unsafe_allow_html=True)
            st.markdown("#### 📋 Overview"); st.info(d["ov"])
            st.markdown("#### 💪 Physical Tendencies"); st.markdown(d["ph"])
            st.markdown("#### 🧠 Psychological Tendencies"); st.markdown(d["ps"])
            st.markdown('</div>', unsafe_allow_html=True)
        with dr:
            st.markdown('<div class="result-card">', unsafe_allow_html=True)
            st.markdown("#### 🥗 Dietary Guidance"); st.success(d["di"])
            st.markdown("#### 🌅 Lifestyle Recommendations"); st.markdown(d["ls"])
            st.markdown("---")
            st.info(
                "⚕️ **Clinical Note:** This assessment provides an indicative Deha Prakriti profile "
                "based on self-reported information and objective anthropometric parameters. "
                "Final scores integrate questionnaire responses (80%) with anthropometric measurements (20%). "
                "For clinical application in disease management or treatment planning, "
                "validation by a qualified Vaidya is essential.\n\n"
                "*Developed by Sri Kalabyraveshwara Swamy AMC*\n"
                "*Dr. Prasanna Kulkarni — MD Ayurveda, MS Data Science*\n"
                "*Sri Kalabyraveshwara Swamy Ayurvedic Medical College, Bangalore*"
            )
            st.markdown('</div>', unsafe_allow_html=True)

        st.markdown("---")

        # ── PDF Download ──────────────────────────────────────────────────────────
        st.markdown("### 📥 Download Your Report")
        if PDF_AVAILABLE:
            with st.spinner("Generating your personalised PDF report..."):
                try:
                    pdf_bytes = generate_pdf_report(
                        profile    = prof,
                        trait_pct  = trait_pct,
                        quest_op   = quest_op,
                        anthro_op  = anthro_op,
                        final_op   = final_op,
                        pname      = pname,
                        picon      = picon,
                        pcolor_hex = pcolor,
                    )
                    fname = f"ePrakruti_{prof.get('name','Report').replace(' ','_')}.pdf"
                    st.download_button(
                        label     = "⬇️ Download PDF Report",
                        data      = pdf_bytes,
                        file_name = fname,
                        mime      = "application/pdf",
                        type      = "primary",
                        use_container_width = True,
                    )
                    st.caption(
                        "📄 Report includes: Dosha distribution · Trait summary · "
                        "Disease proneness · Precautions · Food recommendations · "
                        "Classical references (Charaka · Sushruta · AH)")
                except Exception as e:
                    st.error(f"PDF generation error: {e}")
        else:
            st.warning("PDF generation requires reportlab. Run: `pip install reportlab`")



    # ════════════════════════════════════════════════════════════════════════
    with res_tab2:
        show_ahara_tab(final_op, pname, pcolor)

    # ════════════════════════════════════════════════════════════════════════
    with res_tab3:
        st.markdown("### 📥 Research Data Export")
        st.markdown(
            "*Each completed assessment is automatically appended to `research_data.csv` "
            "on the server. Download the cumulative file below for analysis.*")

        # Auto-save this session once
        if not st.session_state.get("research_saved", False):
            try:
                prof_export = dict(prof)
                prof_export["bmi_category"] = bmi_category(prof.get("bmi", 22))
                append_research_row(
                    profile   = prof_export,
                    responses = st.session_state.responses,
                    trait_pct = trait_pct,
                    quest_op  = quest_op,
                    anthro_op = anthro_op,
                    final_op  = final_op,
                    pname     = pname,
                )
                st.session_state.research_saved = True
                st.success("✅ This participant's data has been saved to **research_data.csv**.")
            except Exception as e:
                st.error(f"Export error: {e}")
        else:
            st.info("✅ Data for this session already saved.")

        # Summary metrics
        import os, csv
        fname_csv = "research_data.csv"
        if os.path.exists(fname_csv):
            with open(fname_csv, encoding="utf-8") as f:
                rows = list(csv.reader(f))
            n_participants = max(len(rows) - 1, 0)

            st.markdown("---")
            ec1, ec2, ec3 = st.columns(3)
            ec1.metric("👥 Total Participants", n_participants)
            ec2.metric("📋 Data Columns", len(rows[0]) if rows else 0)
            ec3.metric("📁 File", fname_csv)

            if n_participants > 0:
                # Prakriti distribution from saved data
                try:
                    prak_col = rows[0].index("Prakriti")
                    prak_vals = [r[prak_col] for r in rows[1:] if len(r) > prak_col]
                    from collections import Counter
                    dist = Counter(prak_vals)
                    st.markdown("#### 📊 Prakriti Distribution (All Participants)")
                    dist_rows = [{"Prakriti Type": k, "Count": v,
                                  "Percentage": f"{v/n_participants*100:.1f}%"}
                                 for k, v in sorted(dist.items(), key=lambda x: -x[1])]
                    import pandas as pd
                    st.dataframe(pd.DataFrame(dist_rows), use_container_width=True,
                                 hide_index=True)
                except Exception:
                    pass

                st.markdown("#### ⬇️ Download Options")
                dl1, dl2 = st.columns(2)

                # Full CSV download
                with open(fname_csv, "rb") as f:
                    csv_bytes = f.read()
                with dl1:
                    st.download_button(
                        label="📥 Download Full Dataset (CSV)",
                        data=csv_bytes,
                        file_name="ePrakruti_research_data.csv",
                        mime="text/csv",
                        type="primary",
                        use_container_width=True,
                    )
                    st.caption("All columns: Profile · 45 Q responses · "
                               "Trait VPK% · Final Prakriti")

                # Scores-only CSV (lighter, for quick analysis)
                with dl2:
                    score_hdrs = ["timestamp","participant_name","age","gender",
                                  "bmi","bmi_category","fat_pct",
                                  "Physical_V_pct","Physical_P_pct","Physical_K_pct",
                                  "Physio_V_pct","Physio_P_pct","Physio_K_pct",
                                  "Psych_V_pct","Psych_P_pct","Psych_K_pct",
                                  "Behav_V_pct","Behav_P_pct","Behav_K_pct",
                                  "Quest_V%","Quest_P%","Quest_K%",
                                  "Anthro_V%","Anthro_P%","Anthro_K%",
                                  "Final_V%","Final_P%","Final_K%","Prakriti"]
                    if rows:
                        hdr = rows[0]
                        col_idx = []
                        for sh in score_hdrs:
                            try: col_idx.append(hdr.index(sh))
                            except ValueError: pass
                        import io
                        sbuf = io.StringIO()
                        sw = csv.writer(sbuf)
                        sw.writerow([hdr[i] for i in col_idx])
                        for r in rows[1:]:
                            sw.writerow([r[i] if i < len(r) else "" for i in col_idx])
                        st.download_button(
                            label="📊 Download Scores Only (CSV)",
                            data=sbuf.getvalue().encode("utf-8"),
                            file_name="ePrakruti_scores_only.csv",
                            mime="text/csv",
                            type="secondary",
                            use_container_width=True,
                        )
                        st.caption("Condensed: Scores + Prakriti only (no raw Q answers)")
        else:
            st.info("No research data yet — complete and submit the first assessment to begin.")

        st.markdown("---")
        st.markdown(
            "📌 **For Researchers:** `research_data.csv` is saved in the same folder as the app. "
            "Each row = one participant. Column order: Personal Profile → "
            "Anthropometrics → Q1–Q45 raw answers → Trait VPK% → "
            "Quest/Anthro/Final VPK% → Prakriti label. "
            "Suitable for direct import into SPSS, R, or Excel for analysis.")

        if st.button("🔄 New Assessment (Reset)", type="secondary",
                     use_container_width=True):
            st.session_state.responses     = {}
            st.session_state.show_results  = False
            st.session_state.research_saved = False
            st.rerun()

    # ════════════════════════════════════════════════════════════════════════
    #  RES TAB 4 — AI PROMPT GENERATOR
    # ════════════════════════════════════════════════════════════════════════
    with res_tab4:
        st.markdown("### 🤖 AI Prompt Generator — e-PathyaGPT")

        st.markdown(
            '<div style="background:#e8f5e9;border-left:5px solid #2e7d32;'
            'border-radius:10px;padding:14px 18px;margin-bottom:16px;">'
            '<b style="color:#1b5e20;font-size:1.02em;">📋 How to use</b><br>'
            '<ol style="margin:8px 0 0 16px;padding:0;font-size:.9em;color:#333;">'
            '<li>Click <b>Generate My Personalised Prompt</b> below</li>'
            '<li>Copy or download the prompt text</li>'
            '<li>Paste into <b>e-PathyaGPT by PraKul</b> (Custom GPT) or any AI assistant</li>'
            '<li>Copy the AI response back here → Generate your <b>Combined PDF</b></li>'
            '</ol>'
            '<div style="margin-top:8px;font-size:.82em;color:#555;">'
            '✅ <b>Zero API cost</b> — No keys required &nbsp;·&nbsp; '
            '✅ All variables auto-filled (Prakriti · Desha · Ritu · BMR · Pathya · Name)'
            '</div>'
            '</div>', unsafe_allow_html=True)

        dp_state = st.session_state.get("dietary_pref", "")
        mf_state = st.session_state.get("meat_freq", 3)
        st_state = st.session_state.get("state", "")
        di_state = st.session_state.get("district", "")
        de_state = st.session_state.get("desha", "Sadharana")

        pc1, pc2, pc3, pc4 = st.columns(4)
        pc1.metric("🌿 Prakriti", pname.replace(" Prakriti","")[:20] if " Prakriti" in pname else pname[:20])
        _diet_short = {"Vegan (plant-based only)":"Vegan",
                       "Lacto-Vegetarian (plant + milk products)":"Lacto-Veg",
                       "Ovo-Vegetarian (plant + eggs)":"Ovo-Veg",
                       "Mixed (Non-vegetarian)":f"Mixed ({st.session_state.get('meat_freq',3)}×/wk)"}
        pc2.metric("🍽️ Diet", _diet_short.get(dp_state, dp_state[:12] if dp_state else "Not set"))
        pc3.metric("🗺️ Desha",  de_state or "Not set")
        pc4.metric("🌾 Season", {1:"Hemanta",2:"Shishira",3:"Shishira",4:"Vasanta",
            5:"Vasanta",6:"Grishma",7:"Grishma",8:"Varsha",9:"Varsha",
            10:"Sharad",11:"Sharad",12:"Hemanta"}.get(
                __import__('datetime').date.today().month,"Sharad"))

        if not dp_state:
            st.warning("⚠️ Go to the **🍽️ Ahara & Desha** tab → "
                       "fill in Dietary Preference & Location before generating.")
        st.markdown("---")

        st.markdown("#### Step 1 — Generate Your Prompt")
        if st.button("🤖 Generate My Personalised Prompt", type="primary",
                     use_container_width=True, key="gen_prompt_main"):
            with st.spinner("Building your personalised prompt…"):
                try:
                    prompt_text = build_ai_prompt(
                        prof=prof, final_op=final_op, pname=pname,
                        desha=de_state or "Sadharana",
                        dietary_pref=dp_state or "Not specified",
                        meat_freq=mf_state,
                        responses=st.session_state.responses,
                    )
                    st.session_state.ai_prompt = prompt_text
                    st.session_state.ai_response = ""
                except Exception as e:
                    st.error(f"Prompt generation error: {e}")

        if st.session_state.get("ai_prompt"):
            prompt_text = st.session_state.ai_prompt
            st.success(f"✅ Prompt ready — {len(prompt_text):,} characters")
            st.text_area("📋 Your prompt — select all and copy, or use the button below",
                         value=prompt_text, height=380, key="prompt_display")

            # M4 — One-click JS copy button
            # Strategy: embed the full prompt as a JS string inside the iframe component
            # This avoids cross-origin DOM access issues with Streamlit's sandboxed iframes
            import streamlit.components.v1 as _cv1
            import json as _json
            # json.dumps handles all escaping: newlines, quotes, backslashes, unicode
            _js_prompt = _json.dumps(prompt_text)  # produces a safely escaped JS string literal
            _cv1.html(f"""
<button id="copybtn" onclick="
  var txt = {_js_prompt};
  if (navigator.clipboard && window.isSecureContext) {{
    navigator.clipboard.writeText(txt).then(function() {{
      document.getElementById('copybtn').innerText = '✅ Copied! Now open e-PathyaGPT and paste';
      document.getElementById('copybtn').style.background = '#27ae60';
      setTimeout(function() {{
        document.getElementById('copybtn').innerText = '📋 Copy Prompt to Clipboard';
        document.getElementById('copybtn').style.background = '#0d5c30';
      }}, 3000);
    }}).catch(function() {{ fallbackCopy(txt); }});
  }} else {{ fallbackCopy(txt); }}
  function fallbackCopy(text) {{
    var ta = document.createElement('textarea');
    ta.value = text;
    ta.style.position = 'fixed';
    ta.style.opacity = '0';
    document.body.appendChild(ta);
    ta.focus(); ta.select();
    try {{
      document.execCommand('copy');
      document.getElementById('copybtn').innerText = '✅ Copied! Now open e-PathyaGPT and paste';
      document.getElementById('copybtn').style.background = '#27ae60';
      setTimeout(function() {{
        document.getElementById('copybtn').innerText = '📋 Copy Prompt to Clipboard';
        document.getElementById('copybtn').style.background = '#0d5c30';
      }}, 3000);
    }} catch(e) {{
      document.getElementById('copybtn').innerText = '⚠️ Copy failed — use Ctrl+A, Ctrl+C in box above';
    }}
    document.body.removeChild(ta);
  }}"
style="background:#0d5c30;color:white;border:none;border-radius:8px;
padding:12px 22px;font-size:14px;font-weight:600;cursor:pointer;
width:100%;margin:6px 0;transition:background 0.3s;">
📋 Copy Prompt to Clipboard
</button>""", height=56)

            # M5 — e-PathyaGPT URL button
            st.markdown(
                '<a href="https://chatgpt.com/g/g-69baa07cd554819189c01f8b5bf19866-e-pathyagpt-by-prakul" '
                'target="_blank" '
                'style="display:block;background:#10a37f;color:white;text-align:center;'
                'padding:13px 20px;border-radius:8px;font-weight:700;font-size:15px;'
                'text-decoration:none;margin:8px 0;letter-spacing:.3px;">'
                '🤖 Click here to open e-PathyaGPT by PraKul &nbsp;→&nbsp; paste your prompt in the message box'
                '</a>', unsafe_allow_html=True)

            dl1, dl2 = st.columns(2)
            with dl1:
                st.download_button("⬇️ Download Prompt (.txt)",
                    data=prompt_text.encode("utf-8"),
                    file_name=f"ePrakruti_prompt_{prof.get('name','').replace(' ','_')}.txt",
                    mime="text/plain", type="secondary", use_container_width=True)
            with dl2:
                if st.button("🔄 Regenerate Prompt", use_container_width=True, key="regen_p"):
                    st.session_state.ai_prompt = None
                    st.session_state.ai_response = ""
                    st.rerun()

            st.markdown("---")
            st.markdown("#### Step 2 — Paste AI Response Here")
            st.markdown(
                '<div class="adj-box">'
                '<div class="adj-title">📌 After getting your diet plan from e-PathyaGPT:</div>'
                '1. Select all AI response text &nbsp;|&nbsp; 2. Copy &nbsp;|&nbsp; '
                '3. Paste below &nbsp;|&nbsp; 4. Click <b>Generate Combined PDF</b>'
                '</div>', unsafe_allow_html=True)

            ai_resp = st.text_area(
                "Paste AI-generated Ahara & Vihara plan here",
                value=st.session_state.get("ai_response",""),
                height=320,
                placeholder="Paste the full response from e-PathyaGPT here…",
                key="ai_resp_input"
            )
            st.session_state.ai_response = ai_resp

            if ai_resp.strip():
                st.markdown("#### Step 3 — Generate Combined PDF")
                st.info(f"AI response ready: {len(ai_resp):,} characters · "
                        f"{len(ai_resp.splitlines())} lines")
                if st.button("📄 Generate Combined PDF (Assessment + Diet Plan)",
                             type="primary", use_container_width=True,
                             key="gen_combined_pdf"):
                    with st.spinner("Building combined PDF…"):
                        try:
                            combined_pdf = generate_combined_pdf(
                                profile=prof, trait_pct=trait_pct,
                                quest_op=quest_op, anthro_op=anthro_op,
                                final_op=final_op, pname=pname,
                                picon=picon, pcolor_hex=pcolor,
                                ai_response=ai_resp,
                            )
                            cname = f"ePrakruti_Complete_{prof.get('name','Report').replace(' ','_')}.pdf"
                            st.download_button(
                                label="⬇️ Download Complete Report PDF",
                                data=combined_pdf, file_name=cname,
                                mime="application/pdf", type="primary",
                                use_container_width=True)
                            st.success("✅ Combined PDF ready — Part A: Assessment + Part B: AI Diet Plan")
                        except Exception as e:
                            st.error(f"Combined PDF error: {e}")
            else:
                st.info("👆 Paste your AI diet plan response above to unlock Combined PDF.")

            st.markdown("---")
            st.markdown("#### 💡 Tips")
            for t in [
                f"**For e-PathyaGPT**: Paste the entire prompt as your first message",
                f"**7-day meal plan**: After first response ask: *'Give me a 7-day rotating meal plan using locally available foods in {st_state or 'my region'}'*",
                "**Jwara advice**: Ask: *'I have fever (Jwara). Adjust this diet plan for Jwara management'*",
                "**Re-use**: Download the prompt; update the Ritu line every ~2 months when season changes",
            ]:
                st.markdown(f"- {t}")

        st.markdown("---")
        st.caption("📚 *Prompt grounded in Charaka Sutrasthana 26-27 · "
                   "Ashtanga Hridaya Sutrasthana 2 · Charaka Vimana Sthana 8/96-98. "
                   "Recommendations are advisory — validate with a qualified Vaidya.*")
