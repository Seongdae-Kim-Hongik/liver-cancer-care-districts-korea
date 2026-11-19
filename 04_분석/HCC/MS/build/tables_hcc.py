# tables_hcc.py — 원고 공통 도우미(초안 읽기·인용 변환·CDOE 문서 엔진·표 1·2 조립). 수치는 numbers_hcc에서만.
import os, re, json, subprocess
from docx.oxml.ns import qn
from jkms_engine import JKMS
import content_hcc as C
HERE = os.path.dirname(os.path.abspath(__file__)); MS = os.path.dirname(HERE); OUT = os.path.join(MS, "out"); os.makedirs(OUT, exist_ok=True)
N = C.N; REFS = json.load(open(os.path.join(HERE, "refs_hcc.json"), encoding="utf-8"))
DRAFT = os.path.join(MS, "draft", "01_manuscript.md")
TITLE = C.TITLE
ORCID = "0000-0002-1525-0091"
AI_STATEMENT = "The author used Claude (Anthropic) and ChatGPT (OpenAI) only for translation and English-language editing of the manuscript."
FUNDING = "This research did not receive any specific grant from funding agencies in the public, commercial, or not-for-profit sectors."

def read_draft():
    md = open(DRAFT, encoding="utf-8").read(); md = re.sub(r"<!--.*?-->", "", md, flags=re.S); S = {}; cur = None
    for line in md.split("\n"):
        m = re.match(r"^## (.+)$", line)
        if m: cur = m.group(1).strip(); S[cur] = []; continue
        if cur is not None: S[cur].append(line)
    return {k: [p.strip() for p in "\n".join(v).split("\n\n") if p.strip()] for k, v in S.items()}
def abstract_parts(D): return list(D["Abstract"])
def pandoc_cites(t): return re.sub(r"\s*\[(@[^\]]+)\]", lambda m: " {{" + ",".join(k.strip().lstrip("@") for k in m.group(1).split(";")) + "}}", t)
def strip(t): return re.sub(r"\{\{[^}]+\}\}|<[^>]+>", "", re.sub(r"\s*\[@[^\]]+\]", "", t))
def nwords(ps): return sum(len(strip(p).split()) for p in ps)

class CDOE(JKMS):   # 보충자료용 문서 엔진(1.5줄 간격)
    def save(self, path):
        from docx.oxml import OxmlElement
        st = self.doc.styles
        try: ln = st["Line Number"]
        except KeyError:
            from docx.enum.style import WD_STYLE_TYPE; ln = st.add_style("Line Number", WD_STYLE_TYPE.CHARACTER)
        ln.font.name = "Times New Roman"; ln.font.size = __import__("docx.shared", fromlist=["Pt"]).Pt(10)
        rpr = ln.element.get_or_add_rPr(); rf = rpr.find(qn("w:rFonts"))
        for k in ("w:ascii", "w:hAnsi", "w:cs", "w:eastAsia"): rf.set(qn(k), "Times New Roman")
        for sec in self.doc.sections:
            for r in sec.footer._element.iter(qn("w:r")):
                rp = r.find(qn("w:rPr"))
                if rp is None: rp = OxmlElement("w:rPr"); r.insert(0, rp)
                f = rp.find(qn("w:rFonts"))
                if f is None: f = OxmlElement("w:rFonts"); rp.insert(0, f)
                for k in ("w:ascii", "w:hAnsi", "w:cs", "w:eastAsia"): f.set(qn(k), "Times New Roman")
        from docx.enum.text import WD_LINE_SPACING as _LS
        for _p in self.doc.paragraphs:
            if _p.paragraph_format.line_spacing_rule == _LS.DOUBLE: _p.paragraph_format.line_spacing_rule = _LS.ONE_POINT_FIVE
        self.doc.styles['Normal'].paragraph_format.line_spacing_rule = _LS.ONE_POINT_FIVE
        return super().save(path)   # 위첨자는 마침표·쉼표 뒤, 음수는 U+2212(06 §10-B)
    raw = False
    def _emit(self, p, text, sz=12, bold=False, italic=False):
        if not self.raw:
            text = re.sub(r"(\{\{[^}]+\}\})([.,;:])", r"\2\1", text)
            text = re.sub(r"(^|[\s(])-(?=\d)", "\\1\u2212", text)
        return super()._emit(p, text, sz, bold, italic)

TAB1_COV = [("pop80_share", "Population aged 80 years or older, %"), ("urban_population_share", "Urban population share, %"), ("physicians_per_1000", "Physicians per 1,000"),
            ("high_risk_drinking_rate", "High-risk drinking, %"), ("screening_normalB_obesity_share", "Obesity management needed, %"), ("screening_normalB_liver_share", "Liver-function management needed, %"),
            ("medical_aid1_patients_per_100k", "Medical Aid type 1 beneficiaries treated§"), ("regular_employee_share", "Regular employment, %"),
            ("walking_practice_rate", "Walking practice, %"), ("public_sports_facilities_per_100k", "Public sports facilities§")]
def table1():
    T = N["T1"]; cols = ["W1_2011-15", "W2_2016-19", "W3_2020-24", "2011-2024"]
    rows = [["__H__", "Treated persons"],
            ["  District-years, No."] + [f"{T[c]['n']:,}" for c in cols],
            ["  Treated person-years, thousand"] + [f"{T[c]['cases']/1e3:,.0f}" for c in cols],
            ["  Person-years, million"] + [f"{T[c]['py']/1e6:.1f}" for c in cols],
            ["  Crude rate per 100,000"] + [f"{T[c]['crude']:.1f}" for c in cols],
            ["  Age-standardized rate per 100,000†"] + [f"{T[c]['asr']:.1f}" for c in cols],
            ["  District STR, median‡"] + [f"{T[c]['sir_med']:.2f}" for c in cols],
            ["  District STR, P10-P90‡"] + [f"{T[c]['sir_p10']:.2f}-{T[c]['sir_p90']:.2f}" for c in cols],
            ["__H__", "District characteristics, mean (SD)"]]
    for v, lab in TAB1_COV:
        mx = max(abs(T[c]['cov'][v][0]) for c in cols); dp = 0 if mx >= 100 else (2 if mx < 1 else 1)
        rows.append([f"  {lab}"] + [f"{T[c]['cov'][v][0]:,.{dp}f} ({T[c]['cov'][v][1]:,.{dp}f})" for c in cols])
    foot = (f"† Direct standardization to the 2015 national population in ten age groups. Crude and age-standardized window values are means of annual rates (crude {N['crude_2011']:.1f} in 2011 and {N['crude_2024']:.1f} in 2024; age-standardized {N['asr_2011']:.1f} and {N['asr_2024']:.1f}). "
            "‡ Observed over indirectly age-standardized expected counts summed over the window. § Per 100,000 population. Counts are rounded independently, so window values may not sum to the total. "
            "P10-P90, 10th-90th percentile; SD, standard deviation; STR, standardized treatment ratio.")
    return ("Table 1 People treated for liver cancer and district characteristics by calendar window, Korea, 2011-2024", ["Characteristic", "2011-2015", "2016-2019", "2020-2024", "2011-2024"], rows, [6.6, 2.5, 2.5, 2.5, 2.5], foot)

GROUPS = [("Behaviors", ["high_risk_drinking_rate", "current_smoking_rate"]),
          ("Metabolic and liver risk at screening", ["screening_normalB_obesity_share", "screening_normalB_diabetes_share", "screening_normalB_liver_share"]),
          ("Physical activity and environment", ["walking_practice_rate", "moderate_pa_rate", "public_sports_facilities_per_100k", "community_gyms_per_100k", "village_sports_facilities_per_100k"]),
          ("Social structure and deprivation", ["medical_aid1_patients_per_100k", "older_single_household_share", "old_housing_share", "regular_employee_share"]),
          ("Detection", ["screening_uptake"]),
          ("Forced controls", ["urban_population_share", "physicians_per_1000", "sex_ratio", "fiscal_independence", "pop80_share"])]
LABEL = {"high_risk_drinking_rate": "High-risk drinking", "current_smoking_rate": "Current smoking", "screening_normalB_obesity_share": "Obesity management needed",
         "screening_normalB_diabetes_share": "Diabetes management needed", "screening_normalB_liver_share": "Liver-function management needed",
         "walking_practice_rate": "Walking practice", "moderate_pa_rate": "Moderate or vigorous activity", "public_sports_facilities_per_100k": "Public sports facilities",
         "community_gyms_per_100k": "Public community gyms", "village_sports_facilities_per_100k": "Village sports facilities",
         "medical_aid1_patients_per_100k": "Medical Aid type 1 beneficiaries treated", "older_single_household_share": "Older-adult single-person households",
         "old_housing_share": "Old housing", "regular_employee_share": "Regular employment", "screening_uptake": "Health screening uptake",
         "urban_population_share": "Urban population share", "physicians_per_1000": "Physicians", "sex_ratio": "Sex ratio", "fiscal_independence": "Fiscal autonomy", "pop80_share": "Population aged 80 years or older"}
def table2():
    rows = []; assert sum(len(v) for g, v in GROUPS[:-1]) == N["n_hyp"] and set(LABEL) == set(N["main"])
    for g, vs in GROUPS:
        rows.append(["__H__", g])
        for v in vs:
            m = N["main"][v]; mv = N["mv"].get(v); k = N["s43"][("KH_typeIV", v)]
            rows.append([f"  {LABEL[v]}", f"{m['IRR']:.3f} ({m['lo']:.3f}-{m['hi']:.3f})", f"{100*mv['cred_frac']:.0f}" if mv else "NA", f"{k[0]:.3f} ({k[1]:.3f}-{k[2]:.3f})"])
    foot = (f"Rate ratios (RRs) per 1 standard deviation with 95% credible intervals (CrIs); intervals with a bound shown as 1.000 were classified from unrounded values. Principal model, Poisson model with a Besag-York-Mollié 2 (BYM2) district effect and random-walk and independent year effects (n = {N['n_rows']:,} district-years). "
            f"† Share of the 200 covariate-subset specifications containing the covariate in which its 95% CrI excluded 1; covariates credible in at least 75% with the same sign in at least 95% were classed as subset-stable. "
            f"‡ Principal model plus a Knorr-Held type IV space-time interaction, the best-fitting interaction model (difference in widely applicable information criterion, ΔWAIC, {C.dW('KH_typeIV'):,.0f}). NA, not applicable (forced controls were in every specification).")
    return ("Table 2 District correlates of age-standardized liver cancer treatment in the principal and space-time interaction models", ["Covariate", "Principal RR (95% CrI)", "Credible %†", "Type IV RR (95% CrI)‡"], rows, foot)

