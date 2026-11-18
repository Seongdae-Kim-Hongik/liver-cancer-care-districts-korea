# esm_ms_hcc.py — Supporting Information(이중 익명: 저자·소속 없음)(보충 방법·표 S1-S5·그림 S1) + STROBE/RECORD 점검표 별도 파일. 수치는 결과 CSV에서만.
#  서식은 원고와 같게(여백 1인치·2줄 간격·3선 표). 줄번호는 본문 원고만(플레이북 06 §9-E) → 이 문서는 끈다.
import os, subprocess, pandas as pd
from docx.oxml.ns import qn
from jkms_engine import JKMS
import content_hcc as C
from tables_hcc import LABEL, GROUPS, CDOE
from build_ms_hcc import TITLE as DTITLE
from numbers_hcc import ROB
HERE = os.path.dirname(os.path.abspath(__file__)); IJ = os.path.dirname(HERE); OUT = os.path.join(IJ, "out"); B = os.path.dirname(IJ)
N = C.N
SHORT = {"medical_aid1_patients_per_100k": "Medical Aid", "screening_normalB_diabetes_share": "Diabetes management", "screening_normalB_liver_share": "Liver-function management", "screening_normalB_obesity_share": "Obesity management", "regular_employee_share": "Regular employment"}
ORD = ["medical_aid1_patients_per_100k", "screening_normalB_diabetes_share", "screening_normalB_liver_share", "screening_normalB_obesity_share", "regular_employee_share"]
assert set(ORD) == set(ROB)
SRC = {"kchs": "KCHS", "chk": "NHIS statistics", "pop": "Statistics Korea", "fac": "MCST facility survey", "vil": "MCST village survey", "eloc": "KOSIS", "ext": "Resident registration", "kosis": "KOSIS", "nhis": "NHIS statistics"}
f3 = lambda t: f"{t[0]:.3f} ({t[1]:.3f}-{t[2]:.3f})"   # 표 안 유의성 별표 금지(메모리 no-bold-in-tables 8/12)
def TF(doc, title, header, rows, widths, foot="", fs=9, split=None, **k):   # 06 §17: 세로 고정, 글꼴 티어·열 폭 자동(widths는 무시); split = 열 묶음(§17-A 표 나누기, 각주는 마지막 부분에)
    if not split: return doc.table_fit(title, header, rows, foot, fs_max=min(fs, 8), **k)
    m = __import__("re").match(r"^(Table S\d+)\. (.*)$", title); sb = k.pop('split_break', True)
    for i, cols in enumerate(split):
        sub = [[r[c] for c in cols] if (r and r[0] != "__H__") else r for r in rows]
        t = f"{m.group(1)} (part {'AB'[i]}). {m.group(2)}"
        if i > 0 and sb: doc.page_break()
        elif i > 0: doc.para(" ", before=12)   # 같은 쪽 part B 제목이 part A 아래 선에 붙지 않게
        doc.table_fit(t, [header[c] for c in cols], sub, foot if i == len(split) - 1 else "", fs_max=min(fs, 8), **k)
J = CDOE(cite="sup"); d = J.doc
for s in d.sections:
    ln = s._sectPr.find(qn("w:lnNumType"))
    if ln is not None: s._sectPr.remove(ln)
J.para("<b>Supporting Information</b>"); J.para(f"<b>{DTITLE}</b>")
J.para("Contents. Supplementary Methods, additional results, list of persistent hot spots, Tables S1-S5, and Figure S1. The STROBE and RECORD checklist is provided as a separate file for peer review.", before=6)
J.head("Supplementary Methods", 1)
SM = [("Outcome.", "Annual numbers of unique persons treated with a principal diagnosis of liver cancer (International Classification of Diseases, 10th revision [ICD-10] C22, malignant neoplasm of liver and intrahepatic bile ducts) under National Health Insurance or Medical Aid, by district of residence, from the Regional Medical Care Utilization Statistics of the National Health Insurance Service (NHIS; major diseases by district). Counts are by date of care and are attributed to the district of residence of the insured person, not to the location of the treating facility."),
      ("Expected counts.", "National age-specific treatment rates for the same diagnoses in ten groups (0-9 to 50-59 years in 10-year groups, 60-64, 65-69, 70-74, and 75 years or older) came from the national disease-classification statistics of the NHIS, divided by the national population in each age group. District age structures came from resident registration statistics by 5-year group, aggregated to the same groups. Expected counts were rescaled each year so that their national sum equaled the observed sum. National tables are not published by sex. In the 2023 resident registration file, the age block of Changwon duplicated the 2022 block; the 2023 total was replaced with the official total (1,009,038) and the age distribution was reconstructed from the national residual."),
      ("Covariates.", "Each covariate was standardized across all district-years. Missing years were filled within districts by linear interpolation where neighboring years existed and otherwise by the district mean, and by the national mean of the same year for the few districts without any observation of a covariate; Table S1 lists the source, observed years, prespecified direction, and filled cells. The share of the population aged 80 years or older was forced into every model because the oldest standardization group (75 years or older) cannot capture differences in very old age."),
      ("Models.", "Software. R 4.6.0 with R-INLA 25.10.19 (fixed effects with vague normal priors); Python 3.9 for data preparation, emerging hot spot analysis, and figures. Poisson likelihood, chosen because its widely applicable information criterion (WAIC) for the forced-controls model was lower than that of a negative binomial likelihood (27,603 vs 27,663); log expected counts as offset, Besag-York-Mollié 2 (BYM2) district effect with penalized-complexity priors (P(σ > 0.5) = 0.01; P(φ < 0.5) = 2/3), and first-order random-walk and independent year effects. District adjacency was defined by shared boundaries (593 edges); six island districts were linked to their nearest neighbor, and Jeju Island (two districts) formed a separate connected component; the BYM2 structured effect was scaled on each component (generalized variance), and sum-to-zero constraints were applied per component, so the two Jeju districts share one degree of freedom in the structured effect while each retains its unstructured effect. Covariate-subset analysis. Two hundred random subsets of the hypothesis covariates, each fitted with all forced controls. Knorr-Held interactions were added with Kronecker-product structure matrices (type I: independent; II: first-order random walk [RW1] in time × independent districts; III: independent years × intrinsic conditional autoregressive [ICAR] structure in space; IV: RW1 × ICAR), with sum-to-zero constraints defined separately for each connected component of the graph. The Spatial+-type method regressed each standardized covariate on the 23 lowest-frequency eigenvectors of the graph Laplacian, skipping all zero eigenvalues, and used the residuals. Emerging hot spot analysis applied Getis-Ord Gi* to annual empirical Bayes-smoothed ratios with Mann-Kendall trend tests of the Gi* z-scores, following the 17 standard categories."),
      ("Sensitivity analyses.", "Table S3 lists the alternative specifications reported in this manuscript with WAIC and the five subset-stable covariates. Imputed values were perturbed 20 times with normal noise of the within-district observed standard deviation and pooled by Rubin's rules; this is a perturbation of imputed values, not model-based multiple imputation, and the pooled intervals are sensitivity summaries rather than posterior credible intervals. Filled cells were 28.9% each of older-adult single-person households and old housing (926 of 3,206 district-years), 42.0% of regular employment (1,346), and 0.6% of liver-function management (20, including all years of Sejong, which lacked screening findings); early years were filled with district values, which suppresses early temporal variation. Variance shares in Table S4 are variances of each linear-predictor component divided by the variance of the full linear predictor; they are not additive because components are correlated. Comparison outcomes (treated gastric cancer, C16; treated arthritis, M00-M19 and M22-M25) used the same covariates with their own age-standardized expected counts.")]
for h, t in SM: J.para(f"<b>{h}</b> {t}")
_T1 = N["T1"]; _eh = N["ehsa"]
_lc = lambda v: LABEL[v] if LABEL[v].startswith("Medical Aid") else LABEL[v][0].lower() + LABEL[v][1:]
def _chg(t): return [v for v in N["main"] if N["s43"][(t, v)][3] and not N["main"][v]["cred"]], [v for v in N["main"] if not N["s43"][(t, v)][3] and N["main"][v]["cred"]]
_n4, _l4 = _chg("KH_typeIV"); _s2 = [v for v in N["sens_main"]["s2"] if v in N["main"] and N["sens_main"]["s2"][v][3] and not N["main"][v]["cred"]]
_tc = N["type_class"]
J.para("<b>Additional results.</b> " + f"The 10th-90th percentile range of district standardized treatment ratios was {_T1['W1_2011-15']['sir_p10']:.2f}-{_T1['W1_2011-15']['sir_p90']:.2f} in 2011-2015, {_T1['W2_2016-19']['sir_p10']:.2f}-{_T1['W2_2016-19']['sir_p90']:.2f} in 2016-2019, and {_T1['W3_2020-24']['sir_p10']:.2f}-{_T1['W3_2020-24']['sir_p90']:.2f} in 2020-2024. Annual Moran's I ranged from {C._r2(N['moran_year_min'])} to {C._r2(N['moran_year_max'])}. "
       + "Full-period hot spots were mainly in " + C.sidos(N['hot_by_sido'], 5) + ", and cold spots mainly in " + C.sidos(N['cold_by_sido'], 5) + f"; hot spots comprised {_tc['hotspot']['city']} cities, {_tc['hotspot']['county']} rural counties, and {_tc['hotspot']['ward']} urban wards, and cold spots {_tc['coldspot']['county']} counties, {_tc['coldspot']['city']} cities, and {_tc['coldspot']['ward']} wards. "
       + f"Emerging hot spot analysis classified {_eh['Intensifying hot']} districts as intensifying, {_eh['Consecutive hot']} as consecutive, and {_eh['Persistent hot']} as persistent hot spots, and {_eh['Persistent cold']} as persistent, {_eh['Intensifying cold']} as intensifying, and {_eh['Consecutive cold']} as consecutive cold spots; the remaining {229 - _eh['Intensifying hot'] - _eh['Consecutive hot'] - _eh['Persistent hot'] - _eh['Persistent cold'] - _eh['Intensifying cold'] - _eh['Consecutive cold'] - _eh['No pattern']} were sporadic, diminishing, or new hot or cold spots, and {_eh['No pattern']} showed no pattern (Fig. S1). "
       + "In the type IV interaction model, " + C.roman([_lc(v) for v in _n4]) + " became credible, and " + C.roman([_lc(v) for v in _l4]) + " were no longer credible. "
       + ("Without the share aged 80 years or older, " + C.roman([_lc(v) for v in _s2]) + " became credible. " if _s2 else "Omitting the share aged 80 years or older made no further covariate credible. ")
       + f"Of the {N['n_hyp']} covariate interactions with the COVID-19 period, {N['covid_nint']} were credible. Posterior predictive intervals covered {100*N['ppc']['coverage95']:.1f}% (95%) and {100*N['ppc']['coverage50']:.1f}% (50%) of district-years, and probability integral transform values departed from uniformity.")
import unicodedata
WM = pd.read_csv(os.path.join(B, "results_std3", "S4b_window_spatialRR.csv"), encoding="utf-8-sig"); WM["fbd_region"] = WM.fbd_region.map(lambda x: unicodedata.normalize("NFC", x))
nh = WM[WM["class"] == "hotspot"].groupby("sigungu_cd").size(); allhot = sorted(nh[nh == 3].index.astype(str)); assert len(allhot) == N["hot_all_windows"]
NM = pd.read_csv(os.path.join(B, "results_std3", "S6_spatial_RR.csv"), dtype={"sigungu_cd": str}).set_index("sigungu_cd").fbd_region.map(lambda x: unicodedata.normalize("NFC", x))
PROV = {"서울시": "Seoul", "부산시": "Busan", "대구시": "Daegu", "인천시": "Incheon", "광주시": "Gwangju", "대전시": "Daejeon", "울산시": "Ulsan", "세종시": "Sejong", "경기도": "Gyeonggi", "강원도": "Gangwon", "충청북도": "North Chungcheong",
        "충청남도": "South Chungcheong", "전라북도": "North Jeolla", "전라남도": "South Jeolla", "경상북도": "North Gyeongsang", "경상남도": "South Gyeongsang", "제주도": "Jeju"}
J.para(f"<b>Persistent hot spots.</b> The {len(allhot)} districts that were hot spots in all three windows, by province and district code (sigungu code of the Korean Statistical Information Service [KOSIS]): "
       + "; ".join(f"{p} ({', '.join(c for c in allhot if NM[c].startswith(k))})" for k, p in PROV.items() if any(NM[c].startswith(k) for c in allhot)) + ". District names for each code are available from the KOSIS district code list.")
# Table S1
M = pd.read_csv(os.path.join(B, "panel_META_HCC_std3.csv"), encoding="utf-8-sig").set_index("variable")
rows = []
for g, vs in GROUPS:
    rows.append(["__H__", g])
    for v in vs:
        m = M.loc[v]; pre = str(m.source_column).split("__")[0]; imp = int(m.n_imputed_interp + m.n_imputed_sgg_mean + m.n_imputed_year_mean)
        unit = (lambda l: "Std. rate, %" if "(SR %)" in l else ("per 100,000" if "per 100k" in l else ("per 1,000" if "per 1000" in l else ("%" if "(%)" in l else ("Men/100 women" if "per 100 women" in l else "index")))))(str(m.label_en))
        rows.append([f"  {LABEL[v]}", unit, SRC.get(pre, pre), f"{int(m.obs_year_min)}-{int(m.obs_year_max)}", ("NA" if m.role == "forced" else str(m.expected_direction).replace("-", "−")), f"{imp:,}"] if v != "screening_normalB_liver_share" else [f"  {LABEL[v]}", "%", "NHIS statistics", "2011-2024", "+", "20"])
J.page_break(); TF(J, "Table S1. Source, observed years, prespecified direction, and filled cells (of 3,206 district-years) for each covariate", ["Covariate", "Unit", "Source", "Years", "Direction", "Filled"], rows, [4.2, 2.8, 3.4, 1.8, 1.6, 1.6],
        "KCHS, Community Health Survey of the Korea Disease Control and Prevention Agency; MCST, Ministry of Culture, Sports and Tourism (public sports facility and village sports facility surveys); KOSIS, Korean Statistical Information Service; NHIS, National Health Insurance Service; NA, no direction prespecified (forced control); Std. rate, age-standardized rate; Filled, filled cells of 3,206 district-years. Densities are per 100,000 population; screening measures are shares of screened adults. Supporting literature for each direction is in the code repository.", fs=7.5)
# Table S2
LO = pd.read_csv(os.path.join(B, "results_std3", "S41_leaveout_ranges.csv")).set_index(["set", "cov"])
rows = []
for v in ORD:
    mv = N["mv"][v]; rt = dict(zip(("kept", "n_specs"), N["ret14"][v])); rb = N["rubin"][v]; ev = N["evalue"][v]
    rows.append([SHORT[v], f"{100*mv['cred_frac']:.0f} / {100*mv['sign_agree']:.0f}", f"{rt['kept']}/{rt['n_specs']}; {LO.loc[('province', v), 'n_cred_same_sign']}/17; {LO.loc[('year', v), 'n_cred_same_sign']}/14",
                 f"{rb['IRR_pooled']:.3f} ({rb['lo']:.3f}-{rb['hi']:.3f}); {int(rb['n_cred'])}/20", f3(N["bw"][v + "__within"]), f3(N["bw"][v + "__between"]), f"{ev['E_point']:.2f} / {ev['E_limit']:.2f}"])
J.page_break()
TF(J, "Table S2. Covariate-subset results, retention, perturbed imputed values, within-district and between-district components, and E-values for the subset-stable covariates", ["Covariate", "Credible / same sign, %", "Retained in Table S3, province, and year fits", "Perturbation-pooled RR (95% interval); replicates with CrI excluding 1", "Within-district RR (95% CrI)", "Between-district RR (95% CrI)", "E-value point / limit"], rows,
        [3.2, 2.6, 3.3, 3.7, 3.7, 3.7, 2.6],
        "SD, standard deviation; RW2, second-order random walk; AR1, first-order autoregressive. Credible and same-sign shares among the 200 covariate-subset specifications containing the covariate (all converged). Retained = credible with the principal-model sign in the 14 alternative specifications within the principal structure (forced controls smoothed; Poisson with observation-level effect; RW2 year effect; AR1 year effect; province-by-year effect; Spatial+-type adjustment; no lag from 2012 and from 2013; covariates lagged 1 and 2 years; extreme district-years excluded; survey covariates averaged over 3 years; odd and even years only), in the 17 leave-one-province fits, and in the 14 leave-one-year fits. Perturbed imputation: 20 replicates pooled by Rubin's rules. Within = two-way-centered deviation (district and year means removed); between = district mean. E-values per 1 SD for the point estimate and the credible limit closer to 1. RR, rate ratio; CrI, credible interval. Intervals with a bound shown as 1.000 were classified from unrounded values.", fs=9, split=[[0, 1, 2, 3], [0, 4, 5, 6]], split_break=False)
# Table S3
NAMES = {"main_queen": "Principal model (refit)", "iid_only": "Independent district effect", "icar_besag": "ICAR district effect", "no_spatial": "No district effect", "pc_phi_flat": "BYM2, neutral prior on φ", "pc_relaxA": "BYM2, relaxed prior A", "pc_relaxB": "BYM2, relaxed prior B",
         "knn3": "3 nearest neighbors", "knn4": "4 nearest neighbors", "knn5": "5 nearest neighbors", "KH_typeI": "Knorr-Held type I", "KH_typeII": "Knorr-Held type II", "KH_typeIII": "Knorr-Held type III", "KH_typeIV": "Knorr-Held type IV",
         "C1_poisson_lognormal": "Poisson, observation-level effect", "C2_rw2_year": "RW2 year effect", "C3_ar1_year": "AR1 year effect", "C4_sido_year_iid": "Province-by-year effect", "B3_smooth_forced": "Forced controls smoothed",
         "D1_spatial_plus": "Spatial+-type adjustment", "E0_nolag_from2012": "No lag, from 2012", "E0_nolag_from2013": "No lag, from 2013", "E1_lag1": "Covariates lagged 1 year", "E2_lag2": "Covariates lagged 2 years",
         "F3_extreme_R7": "Extreme district-years omitted", "G1_kchs_ma3": "Survey covariates, 3-y mean", "H4_odd_years": "Odd years only", "H4_even_years": "Even years only",
         "s577": "Uncorrected graph", "s8": "Eight-group expected counts", "s2": "Share aged 80+ omitted"}
S = {**N["s43"], **N["s41"]}; WA = {**N["s43_waic"], **N["s41_waic"]}
for v in ("s577", "s2", "s8"):
    S.update({(v, c): t for c, t in N["sens_main"][v].items()})
    WA[v] = float(pd.read_csv(os.path.join(B, f"results_{v}", "S3_main_fit.csv")).WAIC.iloc[0])
def cell(a, v):
    t = S.get((a, v)); return "-" if t is None else f"{t[0]:.3f} ({t[1]:.3f}-{t[2]:.3f})"
rows = [[NAMES[a], f"{WA[a]:,.0f}"] + [cell(a, v) for v in ORD] for a in NAMES if a in WA]
J.page_break()
TF(J, "Table S3. WAIC and rate ratios per 1 SD for the five subset-stable covariates in alternative specifications", ["Specification", "WAIC"] + [SHORT[v] for v in ORD], rows, [5.6, 1.8] + [2.6] * 5,
        f"WAIC, widely applicable information criterion; SD, standard deviation; BYM2, Besag-York-Mollié 2; φ, BYM2 mixing parameter; ICAR, intrinsic conditional autoregressive; RW2, second-order random walk; AR1, first-order autoregressive; RR, rate ratio; CrI, credible interval. Principal model WAIC {N['waic_main']:,.1f}; the refit in the first row differs only by numerical approximation, and no covariate changed credibility. Intervals with a bound shown as 1.000 were classified from unrounded values. WAIC values are comparable only within the same years, outcome, and expected counts. Leave-one-province and leave-one-year fits and perturbation replicates are summarized in Table S2. ", fs=7, split=[[0, 1, 2, 3, 4], [0, 1, 5, 6]])
# Table S4
LONG = {v: LABEL[v] for v in ORD}
rows = [[LONG[v], f3((N["main"][v]["IRR"], N["main"][v]["lo"], N["main"][v]["hi"], N["main"][v]["cred"])), f3(N["nco"][("GCA", v)]), f3(N["nco"][("ARTH", v)])] for v in ORD]
NC = {"hit_and_run_rate": "Negative control: hit-and-run accidents", "traffic_culture_index": "Negative control: traffic culture index", "fires_per_10000": "Negative control: fires"}
J.page_break()
TF(J, "Table S4. Comparison outcomes for the five subset-stable covariates, with negative-control exposures and model checks in the footnote", ["Covariate", "Liver cancer, principal model", "Gastric cancer", "Arthritis"], rows, [6.0, 5.6, 5.6, 5.6],
        "RR, rate ratio; SD, standard deviation; PIT, probability integral transform. Gastric cancer, ICD-10 C16; arthritis, ICD-10 M00 to M19 and M22 to M25 (International Classification of Diseases, 10th revision). Rate ratios per 1 SD (95% credible interval) for the five subset-stable covariates; each comparison outcome was fitted with the same covariates and its own age-standardized expected counts. "
        + "Negative-control exposures added one at a time to the principal model: " + "; ".join(f"{NC[k].split(': ')[1]} {v['IRR']:.3f} ({v['lo']:.3f}-{v['hi']:.3f})" for k, v in N["negctl"].items()) + ". "
        + f"COVID-19 period (2020 onward) main effect RR {N['covid_main'][0]:.3f} ({N['covid_main'][1]:.3f}-{N['covid_main'][2]:.3f}); credible covariate-by-period interactions {N['covid_nint']} of {N['n_hyp']} (" + ", ".join((LABEL[c] if LABEL[c].startswith("Medical") else LABEL[c][0].lower() + LABEL[c][1:]) for c in N["covid_int_cov"]) + "). "
        + f"Model checks: 95% posterior predictive coverage {100*N['ppc']['coverage95']:.1f}% (50%: {100*N['ppc']['coverage50']:.1f}%; PIT Kolmogorov-Smirnov <i>P</i> {'< 0.001' if N['ppc']['pit_ks_p'] < 0.001 else '= ' + format(N['ppc']['pit_ks_p'], '.3f')}); held-out 2024 coverage conditional on national totals {100*N['oos']['coverage95']:.0f}%; residual Moran's I {N['moran_resid']:.2f} (permutation <i>P</i> = {N['moran_resid_p']:.3f}); "
        + f"structured spatial, unstructured spatial, all covariates jointly (hypothesis covariates {100*N['varpart']['fixed_hypothesis']['share_of_linear_predictor_var']:.1f}%, forced controls {100*N['varpart']['fixed_forced_controls']['share_of_linear_predictor_var']:.1f}%), and year components {100*N['varpart']['spatial_structured']['share_of_linear_predictor_var']:.1f}%, {100*N['varpart']['spatial_unstructured']['share_of_linear_predictor_var']:.1f}%, {100*N['varpart']['fixed_covariates']['share_of_linear_predictor_var']:.1f}%, and {100*N['varpart']['year_effects']['share_of_linear_predictor_var']:.1f}% of linear predictor variance. Intervals with a bound shown as 1.000 were classified from unrounded values.", fs=9)
WI = pd.read_csv(os.path.join(B, "results_std3", "S4_window_IRR.csv")).set_index(["cov", "window"])
rows = []
for g, vs in GROUPS[:-1]:
    rows.append(["__H__", g])
    for v in vs:
        rows.append([f"  {LABEL[v]}"] + [f3(tuple(WI.loc[(v, w), ["IRR", "lo", "hi", "cred"]])) for w in ("W1_2011-15", "W2_2016-19", "W3_2020-24")])
J.page_break()
TF(J, "Table S5. Rate ratios per 1 SD for the hypothesis covariates in the principal model refitted in each calendar window", ["Covariate", "2011-2015", "2016-2019", "2020-2024"], rows, [6.0, 3.6, 3.6, 3.6],
        "SD, standard deviation; RR, rate ratio. Rate ratios (95% credible intervals) from the principal model structure fitted separately to each window with all forced controls. Intervals with a bound shown as 1.000 were classified from unrounded values.", fs=9)
from docx.shared import Cm
J.page_break(); J.para(" ")
from docx.enum.text import WD_LINE_SPACING as _LS
_pp = J.doc.paragraphs[-1]; _pp.paragraph_format.line_spacing_rule = _LS.SINGLE; _pp.add_run().add_picture(os.path.join(HERE, "figs", "FigS1.png"), width=Cm(14))
J.para("<b>Figure S1</b> Persistence of the district pattern. (A) Emerging hot spot analysis of empirical Bayes-smoothed standardized treatment ratios, 2011-2024 (Getis-Ord Gi* with Mann-Kendall trend); numbers of districts in parentheses. (B) Number of calendar windows (2011-2015, 2016-2019, 2020-2024) in which each district was a hot or cold spot in the principal model refitted in each window.")
# STROBE / RECORD
CK = [("Title and abstract", "1", "Title page; Abstract"), ("Background/rationale", "2", "Introduction"), ("Objectives", "3", "Introduction, final paragraph"), ("Study design", "4", "Methods, Data sources and outcome"), ("Setting", "5", "Methods, Data sources and outcome"),
      ("Participants", "6", "Methods, Data sources and outcome (district populations; ecological)"), ("Variables", "7", "Methods, Age standardization; Covariates; Table S1"), ("Data sources/measurement", "8", "Methods; Supporting Information, Supplementary Methods"),
      ("Bias", "9", "Methods, Sensitivity analyses and reporting; Tables S2-S5"), ("Study size", "10", "Methods, Data sources and outcome (all 229 districts)"), ("Quantitative variables", "11", "Methods, Covariates"),
      ("Statistical methods", "12", "Methods, Statistical analysis; Sensitivity analyses and reporting"), ("Descriptive data", "14", "Results, Treated people and trends; Table 1"), ("Outcome data", "15", "Results, Treated people and trends"),
      ("Main results", "16", "Results, Spatial pattern and persistence; District correlates in the principal model; Table 2"), ("Other analyses", "17", "Results, Space-time interaction and other sensitivity analyses; Figure 2; Supporting Information, Tables S2-S5"),
      ("Key results", "18", "Discussion, Fewer treated after age adjustment, a stable southern concentration"), ("Limitations", "19", "Discussion, Strengths and limitations"), ("Interpretation", "20", "Discussion"), ("Generalizability", "21", "Discussion, Strengths and limitations; Implications"),
      ("Funding", "22", "Title page, Funding"), ("Codes/algorithms", "R6.1", "Methods, Data sources and outcome (C22 principal diagnosis)"), ("Codes for variables", "R7.1", "Supporting Information, Table S1"),
      ("Type of data", "R1.1", "Title page; Abstract (national insurance claims statistics)"), ("Region and time frame", "R1.2", "Title (Korea); Abstract (229 districts, 2011-2024)"), ("Databases linked", "R1.3", "Abstract; Methods (aggregate public statistics merged by district code)"), ("Validation of codes", "R6.2", "Not applicable (published aggregate disease group); limitation stated in Discussion"), ("Linkage", "R6.3", "District-level merging by district code; no person-level linkage"), ("Selection of population", "R13.1", "All 229 districts and 14 years; no exclusions"), ("Limitations of routine data", "R19.1", "Discussion, Strengths and limitations (claims measure care, residence attribution, outcome grouping)"), ("Data access", "R12.1", "Only published aggregate statistics were used"), ("Data cleaning", "R12.2", "Supporting Information, Supplementary Methods (boundaries, filled cells, Changwon 2023)"),
      ("Data linkage", "R12.3", "District-level merging by district code; no person-level linkage"), ("Data access statement", "R22.1", "Title page, Data availability statement")]
for s in d.sections:   # 가로 섹션이 줄번호를 다시 넣으므로 저장 전에 모두 끈다
    ln = s._sectPr.find(qn("w:lnNumType"))
    if ln is not None: s._sectPr.remove(ln)
p = os.path.join(OUT, "Supporting_Information_HCC.docx"); J.doc_title = "Supporting Information"; J.save(p)
K = CDOE(cite="sup")
for s_ in K.doc.sections:
    ln = s_._sectPr.find(qn("w:lnNumType"))
    if ln is not None: s_._sectPr.remove(ln)
K.para(f"<b>{DTITLE}</b>")
TF(K, "STROBE and RECORD checklist for this ecological study of routinely collected data", ["Item", "No.", "Where reported"], [[a, b, c] for a, b, c in CK], [5.6, 1.6, 7.8], "Item 13 (participant flow) is not applicable to aggregate district data.", fs=8)
pk = os.path.join(OUT, "STROBE_RECORD_Checklist_HCC.docx"); K.doc_title = "STROBE and RECORD checklist"; K.save(pk)
subprocess.run(["/opt/homebrew/bin/soffice", "--headless", "-env:UserInstallation=file:///tmp/lo_hcc_esm_jg", "--convert-to", "pdf", "--outdir", OUT, pk], check=True, capture_output=True)
subprocess.run(["/opt/homebrew/bin/soffice", "--headless", "-env:UserInstallation=file:///tmp/lo_hcc_esm_jg", "--convert-to", "pdf", "--outdir", OUT, p], check=True, capture_output=True)
print("saved", p, len(rows))
