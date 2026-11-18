# build_refs_hcc.py — 간암 원고 참고문헌 메타데이터 캐시(refs_hcc.json). 네트워크는 이 스크립트에서만.
#  키 = 원고 원천(draft md + content_hcc.py)의 [@key]. manifest(ALL_refs.csv) PMID → PubMed esummary, 없으면 DOI → Crossref. 웹 문헌은 WEB 사전.
import os, re, json, time, urllib.request, urllib.parse, glob
import pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); CE = os.path.dirname(HERE)
man = pd.read_csv(os.path.join(CE, "refs", "manifest", "ALL_refs.csv"), dtype=str).fillna("")
man["pmid"] = man.pmid.str.replace(r"\.0$", "", regex=True); M = man.set_index("key")
src = open(os.path.join(HERE, "content_hcc.py"), encoding="utf-8").read() + "".join(open(f, encoding="utf-8").read() for f in glob.glob(os.path.join(CE, "draft", "*.md")))
src = re.sub(r"<!--.*?-->", "", src, flags=re.S); src = re.sub(r"(?m)^\s*#.*$", "", src)
keys = sorted({k.strip().lstrip("@") for g in re.findall(r"\[(@[^\]]+)\]", src) for k in g.split(";")})
WEB = {
 "web:nhis2026regional": dict(type="web", authors="National Health Insurance Service", title="Regional medical care utilization statistics: number of persons treated for major diseases by district of residence, liver cancer (C22), 2011-2024", url="https://kosis.kr", year=2026, accessed="October 20, 2026"),
 "web:rcore2026": dict(type="web", authors="R Core Team", title="R: a language and environment for statistical computing. Version 4.6.0. Vienna: R Foundation for Statistical Computing; 2026", url="https://www.R-project.org/", year=2026, accessed="October 20, 2026"),
 "web:mois2026population": dict(type="web", authors="Ministry of the Interior and Safety", title="Resident registration population by district, sex, and 5-year age group, 2011-2024", url="https://jumin.mois.go.kr", year=2026, accessed="October 20, 2026"),
}
JABBR = {"Political Science Research and Methods": "Polit. Sci. Res. Methods", "Journal of Hydrology": "J. Hydrol.", "Geographical Analysis": "Geogr. Anal.", "Econometrica": "Econometrica", "Statistical Science": "Stat. Sci.", "Statistics and Computing": "Stat. Comput."}
out = {}
miss = [k for k in keys if not k.startswith("web:") and k not in M.index]; assert not miss, miss
pm = [k for k in keys if not k.startswith("web:") and M.loc[k, "pmid"]]
for i in range(0, len(pm), 150):
    ids = ",".join(M.loc[k, "pmid"] for k in pm[i:i + 150])
    d = json.load(urllib.request.urlopen("https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi?db=pubmed&retmode=json&id=" + ids, timeout=60))["result"]
    for k in pm[i:i + 150]:
        r = d[M.loc[k, "pmid"]]
        au = [a["name"] for a in r["authors"] if a.get("authtype", "Author") == "Author"] or [a["name"] for a in r["authors"]]
        au = [{"Cheol Seong S": "Seong SC", "Heon Park J": "Park JH"}.get(a, a) for a in au]   # 2026-11-07: PubMed 저자명 뒤집힘 교정
        doi = next((a["value"] for a in r["articleids"] if a["idtype"] == "doi"), "") or M.loc[k, "doi"]
        pages = r.get("pages", "") or (r.get("elocationid", "").replace("pii: ", "").split(" doi")[0] if r.get("elocationid", "").startswith("pii:") else "")
        out[k] = dict(type="journal", authors=au, title=r["title"].rstrip("."), journal=r["source"], year=int(r["pubdate"][:4]), vol=r.get("volume", ""), issue=r.get("issue", ""), pages=pages, doi=doi, pmid=M.loc[k, "pmid"], verified="PubMed esummary " + time.strftime("%Y-%m-%d"))
    time.sleep(0.4)
for k in keys:
    if k.startswith("web:"): out[k] = WEB[k]; continue
    if k in out: continue
    doi = M.loc[k, "doi"]; assert doi, k
    m = json.load(urllib.request.urlopen(urllib.request.Request("https://api.crossref.org/works/" + urllib.parse.quote(doi), headers={"User-Agent": "research (mailto:kimsd@hongik.ac.kr)"}), timeout=60))["message"]
    au = [f"{a.get('family','')} {''.join(x[0] for x in re.split(r'[ -]', a.get('given','')) if x)}".strip() for a in m.get("author", [])]
    jt = (m.get("short-container-title") or m.get("container-title") or [""])[0]; jt = JABBR.get((m.get("container-title") or [""])[0], jt)
    yr = (m.get("published-print") or m.get("published-online") or m.get("issued"))["date-parts"][0][0]
    out[k] = dict(type="journal", authors=au, title=re.sub(r"<[^>]+>", "", (m.get("title") or [""])[0]), journal=jt, year=int(yr), vol=m.get("volume", ""), issue=m.get("issue", ""), pages=m.get("page", "") or m.get("article-number", ""), doi=doi, verified="Crossref " + time.strftime("%Y-%m-%d"))
    time.sleep(0.3)
# 서식 통일: 학술지 NLM 약어(마침표 없음), 쪽 범위 전체 표기, 대문자 제목 문장형, 누락 쪽
JN = {"Polit. Sci. Res. Methods": "Polit Sci Res Methods", "Geogr. Anal.": "Geogr Anal", "The American Statistician": "Am Stat", "Stat. Sci.": "Stat Sci",
      "Journal of the Royal Statistical Society Series B: Statistical Methodology": "J R Stat Soc Series B Stat Methodol"}
FIXY = {"filgueiras2023assessment": 2022}   # Crossref 권 36(2022) e0125
FIXP = {"mann1945nonparametric": "245-259", "choi2026degree": "2594"}
def fullp(p):
    m = re.match(r"^(\d+)-(\d+)$", str(p))
    if not m: return p
    a, b = m.groups(); return p if len(b) >= len(a) else f"{a}-{a[:len(a)-len(b)]+b}"
for k, v in out.items():
    if v.get("type") != "journal": continue
    v["journal"] = JN.get(v["journal"], v["journal"]).replace(".", "")
    v["pages"] = FIXP.get(k, fullp(v.get("pages", ""))); v["year"] = FIXY.get(k, v["year"])
    if v["title"].isupper(): v["title"] = v["title"].capitalize()

# AMA 문장형 제목(DME, /플레이북 대조 11/5): 제목형 대소문자 문헌만 직접 지정(고유명사 유지)
SENT = {
 "cheolseong2017data": "Data resource profile: the National Health Information Database of the National Health Insurance Service in South Korea",
 "cho2019chasms": "Chasms in achievement of recommended diabetes care among geographic regions in Korea",
 "jang2024prevalence": "Prevalence, awareness, treatment, and control of type 2 diabetes in South Korea (1998 to 2022): nationwide cross-sectional study",
 "kang2015korea": "Korea Community Health Survey data profiles",
 "min2019risk": "Risk factors for underdiagnosis of diabetes based on the Korean National Health and Nutrition Examination Survey 2013-2015",
 "park2025diabetes": "Diabetes fact sheets in Korea 2024",
 "steegen2016increasing": "Increasing transparency through a multiverse analysis",
 "vanderweele2017sensitivity": "Sensitivity analysis in observational research: introducing the E-value",
 "bell2015explaining": "Explaining fixed effects: random effects modeling of time-series cross-sectional and panel data",
 "rue2009approximate": "Approximate Bayesian inference for latent Gaussian models by using integrated nested Laplace approximations"}
SENT.update({
 "ferreira2019physical": "Physical activity reduces the prevalence of periodontal disease: systematic review and meta-analysis",
 "jang2017utilization": "Utilization of preventive dental services before and after health insurance covered dental scaling in Korea",
 "kim2015dental": "Dental care utilization for examination and regional deprivation",
 "kim2023did": "Did dental insurance expansion improve dental care needs among Korean adults? Difference in difference analysis",
 "leite2018effect": "Effect of smoking on periodontitis: a systematic review and meta-regression",
 "lim2025effect": "Effect of regional deprivation and dental care resources on the unmet dental care needs due to cost of older individuals in South Korea"})
for k, t in SENT.items():
    if k in out: out[k]["title"] = t
for k, v in out.items():   # 콜론 뒤 첫 글자 소문자(고유명사·약어 제외)
    if v.get("type") == "journal":
        v["title"] = re.sub(r":\s+([A-Z][a-z]*)\b", lambda m: ": " + (m.group(1) if m.group(1) in ("Insight", "Korea", "Korean", "South", "Bayesian", "Spatial", "E") else m.group(1).lower()), v["title"])
        v["title"] = v["title"].replace("(Insight from", "(insight from")
json.dump(out, open(os.path.join(HERE, "refs_hcc.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(len(keys), "keys;", sum(v["type"] == "journal" for v in out.values()), "journal,", sum(v["type"] == "web" for v in out.values()), "web")
