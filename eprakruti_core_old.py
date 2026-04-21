"""
eprakruti_core.py — e-Prakruti Scoring Engine v8.0
Dr. Prasanna Kulkarni | MD Ayurveda, MS Data Science
SKAMC, Bangalore

Pure Python — no Streamlit. Imported by eprakruti_api.py
"""
import re
from datetime import date
from typing import Dict, Any, Optional

# ────────────────────────────────────────────────────────────
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

# ────────────────────────────────────────────────────────────
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

# ────────────────────────────────────────────────────────────
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

# ────────────────────────────────────────────────────────────
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

# ────────────────────────────────────────────────────────────
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

# ────────────────────────────────────────────────────────────
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


def get_desha(state, district):
    geo = INDIA_GEO.get(state, {})
    dist_map = geo.get("districts", {})
    return dist_map.get(district) or geo.get("default", "Sadharana")


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


# ── Alias for API ──────────────────────────────────────────────────────────
def build_ai_prompt_core(prof, final_op, pname, desha, dietary_pref, meat_freq, responses):
    return build_ai_prompt(prof, final_op, pname, desha, dietary_pref, meat_freq, responses)

# ── Trait helpers ──────────────────────────────────────────────────────────
TRAITS      = ["Physical","Physiological","Psychological","Behavioral"]
TRAIT_ICONS = {"Physical":"🏃","Physiological":"⚙️","Psychological":"🧠","Behavioral":"🌿"}
TRAIT_Q     = {t:[q for q in QUESTIONS if q["trait"]==t] for t in TRAITS}

def build_mandatory_qs():
    mset = {1,3,4,5,7,16,17,18,19}
    for trait in ["Psychological","Behavioral"]:
        w3     = [q["id"] for q in TRAIT_Q[trait] if q.get("weight",2)==3]
        others = [q["id"] for q in TRAIT_Q[trait] if q["id"] not in w3]
        mset  |= set((w3+others)[:3])
    return mset

MANDATORY_QS = build_mandatory_qs()
