"""
eprakruti_pdf.py — e-Prakruti PDF Generator v8.0
Dr. Prasanna Kulkarni | MD Ayurveda, MS Data Science
SKAMC, Bangalore

Provides two PDF generation functions:
  generate_pdf_report_api()   — Assessment report PDF
  generate_combined_pdf_api() — Assessment + AI diet plan PDF

Both return raw bytes suitable for HTTP streaming.
Requires: reportlab, pillow
"""

from eprakruti_core import (
    QUESTIONS, AHARA_DATA, DISEASE_PRONE_PDF, PRECAUTIONS_PDF,
    TRAITS, prakriti_type, calculate_questionnaire,
    score_anthropometric, combine_scores, bmi_category,
)

def generate_pdf_report_api(profile, trait_pct, quest_op, anthro_op, final_op,
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

def generate_combined_pdf_api(profile, trait_pct, quest_op, anthro_op,
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

