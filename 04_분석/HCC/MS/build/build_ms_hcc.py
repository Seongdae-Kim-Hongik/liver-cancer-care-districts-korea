# build_ms_hcc.py — 간암 진료 원고 조립(이중 익명 Original Article, 2026-11-19).
#  사용: python3 figs_hcc.py → python3 build_ms_hcc.py → python3 esm_ms_hcc.py → python3 cover_hcc_letter.py → python3 finalize_ms.py → python3 check_ms_hcc.py
#  규정(저널 Author Guidelines, 2026-11-19 확인): 이중 익명 → 본문에 저자·소속 없음, 제목면은 별도 Word 파일.
#   본문 순서 = 제목·초록·키워드 → 본문(Introduction/Methods/Results/Discussion, 번호 없음) → 참고문헌 → 표(범례 위) → 그림 범례. 각주 금지.
#   구조 초록 ≤250(Aim/Methods/Results/Conclusions, 약어·인용 금지), 키워드 5개 MeSH 알파벳순, 미국식 철자, Vancouver 위첨자 연속 번호,
#   참고문헌 예시 "King VM, Armstrong DM, Apps R, Trott JR. Title. J Comp Neurol 1998;390:537-551.", 표 세로줄 금지·각주 † ‡ § ¶(별표는 P값 전용),
#   그림 별도 파일, 컬러 무료, 이중 간격·A4·여백 30 mm·쪽 번호 오른쪽 위, running title < 40자, 저자 이름 성 대문자(Seongdae KIM).
#   2026-11-16 SMI 교훈: 윤리 기관명·AI·자료·연구비·기여·이해상충은 제목면에만. 단 이 저널은 Methods에 윤리 승인 문장을 요구 → 기관명 없는 문장만 둔다.
import os, re, json, subprocess
from docx.shared import Pt, Cm
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
from jkms_engine import JKMS
import content_hcc as C
from tables_hcc import table1, table2, read_draft, pandoc_cites, strip, nwords
HERE = os.path.dirname(os.path.abspath(__file__)); MS = os.path.dirname(HERE); OUT = os.path.join(MS, "out"); os.makedirs(OUT, exist_ok=True)
N = C.N; REFS = json.load(open(os.path.join(HERE, "refs_hcc.json"), encoding="utf-8"))
_zf = os.path.join(OUT, "zenodo_doi.txt"); ZENODO = open(_zf).read().strip() if os.path.exists(_zf) else "10.5281/zenodo.PENDING"
GITHUB = "https://github.com/Seongdae-Kim-Hongik/liver-cancer-care-districts-korea"
TITLE = C.TITLE; RUNNING = C.RUNNING; assert len(RUNNING) < 40
ORCID = "0000-0002-1525-0091"
AFFIL = "Department of Biohealth Convergence Open Sharing System, Hongik University, Seoul, Republic of Korea"
ADDR = "Department of Biohealth Convergence Open Sharing System, Hongik University, 94 Wausan-ro, Mapo-gu, Seoul 04066, Republic of Korea"
FUNDING = "This research did not receive any specific grant from funding agencies in the public, commercial, or not-for-profit sectors."
COI = "The author declares no conflicts of interest and no industrial links or affiliations."
ETHICS = ("The Institutional Review Board of Hongik University approved the study on 4 November 2025 (7002340-202511-HR-012) and its continuing review on 3 November 2026 "
          "(7002340-202611-HR-040). The study was performed in accordance with the Declaration of Helsinki (2013 revision).")
CONSENT = "The Institutional Review Board waived informed consent because only published aggregate statistics were used and no individual could be identified."
CONTRIB = "Seongdae Kim conceived and designed the study, curated the data, performed the analysis, wrote the code, prepared the figures and tables, and wrote and revised the manuscript."
AI = "The author used Claude (Anthropic) and ChatGPT (OpenAI) only for translation and English-language editing of the manuscript; the author takes full responsibility for the content."
def data_statement(): return ("All source data are publicly available aggregate statistics from the National Health Insurance Service, the Ministry of the Interior and Safety, the Community Health Survey, and national statistics, "
                              "as cited in the Methods and listed in the Supporting Information. The processed district-year analytic data are available from the author on reasonable request. "
                              f"The analysis code and the scripts that generate every number, table, and figure are openly available on Zenodo (https://doi.org/{ZENODO}) and GitHub ({GITHUB}).")

def ref(k):   # 저널 예시: King VM, Armstrong DM, Apps R, Trott JR. Title. J Comp Neurol 1998;390:537-551. (AMA: 저자 6명 이하 전원, 7명 이상 3명+et al)
    r = REFS[k]
    if r["type"] == "web":
        t = r['title'].rstrip('.'); y = "" if t.endswith(str(r['year'])) else f" {r['year']}."
        return f"{r['authors']}. {t}.{y} Available from: {r['url']}. Accessed {r['accessed']}."
    au = r["authors"]; a = ", ".join(au) if len(au) <= 6 else ", ".join(au[:3]) + ", et al"
    t = r["title"].rstrip(".").replace("Clonorchis sinensis", "<i>Clonorchis sinensis</i>")
    s = f"{a}. {t}{'' if t.endswith(('?', '!')) else '.'} {r['journal'].rstrip('.')} {r['year']}"
    if r.get("vol"): s += f";{r['vol']}"
    if r.get("pages"): s += f":{r['pages'].replace(chr(8211), '-')}"
    s += "."
    if not r.get("vol") and r.get("doi"): s += f" doi:{r['doi']}"
    return s

def page_number_top_right(doc):
    for s in doc.sections:
        s.top_margin = s.bottom_margin = s.left_margin = s.right_margin = Cm(3.0)
        for p in s.footer.paragraphs:
            for r in list(p.runs): r._element.getparent().remove(r._element)
        hp = s.header.paragraphs[0]; hp.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        for kind in ("begin", "instr", "end"):
            r = hp.add_run(); r.font.size = Pt(10); r.font.name = "Times New Roman"
            if kind == "instr": it = OxmlElement("w:instrText"); it.set(qn("xml:space"), "preserve"); it.text = "PAGE"; r._element.append(it)
            else: fc = OxmlElement("w:fldChar"); fc.set(qn("w:fldCharType"), kind); r._element.append(fc)

class MSDOC(JKMS):
    raw = False
    def _emit(self, p, text, sz=12, bold=False, italic=False):
        if not self.raw:
            text = re.sub(r"(\{\{[^}]+\}\})([.,;:])", r"\2\1", text)   # 위첨자는 마침표·쉼표 뒤
            text = re.sub(r"(^|[\s(])-(?=\d)", "\\1\u2212", text)
        return super()._emit(p, text, sz, bold, italic)
    def head(self, text, level=1):
        if level == 2: return super().head(f"<i>{text}</i>", 2)
        return super().head(text, level)
    def save(self, path):
        page_number_top_right(self.doc); return super().save(path)

def foot_row(J, text, sz=9, ls=15):
    t = J.doc.tables[-1]; r = t.add_row(); m = r.cells[0].merge(r.cells[-1]); m.text = ""; p = m.paragraphs[0]
    p.paragraph_format.line_spacing_rule = WD_LINE_SPACING.EXACTLY; p.paragraph_format.line_spacing = Pt(ls); p.paragraph_format.space_before = Pt(4)
    c = J.counting; J.counting = False; J._emit(p, text, sz); J.counting = c
def put_table(J, t, fs):
    title, header, rows = t[0], t[1], t[2]; foot = t[4] if len(t) == 5 else t[3]
    c = J.counting; J.counting = False; J.table_fit(title, header, rows, "", fs_max=fs, title_bold=True); foot_row(J, foot, 8); J.counting = c

FIGCAP = {
 1: "Geography and trend of liver cancer treatment in Korea. (A) Residual spatial rate ratio (RR) by district, 2011-2024, shown as the posterior mean of the exponentiated Besag-York-Mollié 2 district effect from the principal model. Solid black outlines, hot spots (posterior probability RR > 1 above 0.95); dashed blue outlines, cold spots (below 0.05); thick gray lines, province boundaries. District boundaries as of 2024. (B) National crude and directly age-standardized (2015 population) treatment rates per 100,000 population.",
 2: "Subset-stable district correlates across models. Rate ratios per 1 standard deviation (SD) with 95% credible intervals from the principal model, models with Knorr-Held type I and type IV space-time interactions, the within-district and between-district components, and the principal model fitted to the number of people treated for gastric cancer as a comparison outcome.",
}
def abstract_paras(D):
    out = []
    for p in D["Abstract"]:
        m = re.match(r"^(Aim|Methods|Results|Conclusions):\s*(.*)$", p, re.S); assert m, p[:40]; out.append((m.group(1), m.group(2)))
    assert [h for h, _ in out] == ["Aim", "Methods", "Results", "Conclusions"]; return out

def build():
    D = read_draft(); J = MSDOC(cite="sup")
    J.para(f"<b>{TITLE}</b>")
    J.head("Abstract", 1)
    for h, t in abstract_paras(D): J.para(f"<b>{h}:</b> {t}")
    J.para(f"<b>Keywords:</b> {C.KEYWORDS}", before=6)
    J.page_break(); J.counting = True
    J.head("Introduction", 1)
    for p in D["Introduction"]: J.para(pandoc_cites(p), indent=True)
    J.head("Methods", 1)
    for h, p in C.METHODS: J.head(h, 2); J.para(pandoc_cites(p), indent=True)
    J.head("Results", 1)
    for h, p in C.RESULTS: J.head(h, 2); J.para(pandoc_cites(p), indent=True)
    J.head("Discussion", 1)
    for p in D["Discussion"]:
        if p.startswith("### "): J.head(p[4:].strip(), 2); continue
        J.para(pandoc_cites(p), indent=True)
    J.head("Conclusions", 1)
    for p in D["Conclusion"]: J.para(pandoc_cites(p), indent=True)
    J.counting = False; bw = J.body_words
    J.page_break(); J.head("References", 1); J.raw = True; rl = []
    for n, k in enumerate(J.cites, 1): s = f"{n}. {ref(k)}"; rl.append(s); J.para(s)
    J.raw = False
    J.page_break(); put_table(J, table1(), 9)
    J.page_break(); put_table(J, table2(), 8)
    J.page_break(); J.head("Figure legends", 1)
    for k in sorted(FIGCAP): J.para(f"<b>Figure {k}</b> {FIGCAP[k]}")
    return J, bw, rl, D

def build_titlepage(bw, aw, nref):
    J = MSDOC(cite="sup")
    for s_ in J.doc.sections:
        ln = s_._sectPr.find(qn("w:lnNumType"))
        if ln is not None: s_._sectPr.remove(ln)
    J.para(f"<b>{TITLE}</b>")
    J.para("Seongdae KIM", before=6); J.para(AFFIL)
    J.para(f"<b>Running title:</b> {RUNNING}", before=6)
    J.para(f"<b>Correspondence:</b> Seongdae KIM, {ADDR}. Email: kimsd@hongik.ac.kr. Tel: +82-2-320-1114. ORCID: {ORCID}", before=6)
    J.para(f"<b>Word count:</b> main text {bw:,} words; abstract {aw} words; {nref} references; 2 tables; 2 figures", before=6)
    for h, t in (("Acknowledgments", "None."), ("Funding", FUNDING), ("Conflict of interest", COI), ("Ethics approval", ETHICS), ("Patient consent", CONSENT),
                 ("Clinical trial registration", "Not applicable."), ("Data availability statement", data_statement()), ("Author contributions", CONTRIB), ("Use of artificial intelligence", AI)):
        J.para(f"<b>{h}.</b> {t}", before=4)
    return J

def fix_orphans(path, heads, max_iter=8):
    from docx import Document
    for _ in range(max_iter):
        pdf = path.replace(".docx", ".pdf")
        subprocess.run(["/opt/homebrew/bin/soffice", "--headless", "-env:UserInstallation=file:///tmp/lo_hcc_ms", "--convert-to", "pdf", "--outdir", os.path.dirname(path), path], check=True, capture_output=True)
        pg = subprocess.run(["pdftotext", "-layout", pdf, "-"], capture_output=True, text=True).stdout.split("\f")
        orphan = None
        for x in pg:
            ls = [re.sub(r"^\s*\d+\s+", "", l).strip() for l in x.split("\n") if l.strip()]
            ls = [l for l in ls if not re.fullmatch(r"\d+", l)]
            if ls and ls[-1] in heads: orphan = ls[-1]; break
        if orphan is None: return
        d = Document(path)
        ps = d.paragraphs
        for i, p in enumerate(ps):
            if p.text.strip() == orphan and i > 0:   # 쪽 나눔은 앞 문단 끝에(제목 문단 안에 넣으면 LibreOffice가 제목을 앞쪽에 남김), 연속 제목이면 첫 제목 앞
                while i > 1 and ps[i - 1].text.strip() in heads: i -= 1
                r = OxmlElement("w:r"); br = OxmlElement("w:br"); br.set(qn("w:type"), "page"); r.append(br); ps[i - 1]._p.append(r); break
        d.save(path); print("orphan fixed:", orphan)

if __name__ == "__main__":
    from docx import Document
    p = os.path.join(OUT, "Manuscript_HCC.docx")
    J, bw, rl, D = build(); J.doc_title = "Manuscript"; J.save(p)
    ps = [x.text for x in Document(p).paragraphs]; i0 = ps.index("Introduction"); i1 = ps.index("References")
    bw = sum(len(x.split()) for x in ps[i0:i1]); aw = sum(len(strip(t).split()) for _, t in abstract_paras(D)); n = len(rl)
    heads = {"Abstract", "Introduction", "Methods", "Results", "Discussion", "Conclusions", "References", "Figure legends"} | {h for h, _ in C.METHODS + C.RESULTS} | {x[4:].strip() for x in D["Discussion"] if x.startswith("### ")}
    fix_orphans(p, heads)
    TP = build_titlepage(bw, aw, n); tp = os.path.join(OUT, "Title_Page_HCC.docx"); TP.doc_title = "Title page"; TP.save(tp)
    subprocess.run(["/opt/homebrew/bin/soffice", "--headless", "-env:UserInstallation=file:///tmp/lo_hcc_ms", "--convert-to", "pdf", "--outdir", OUT, tp], check=True, capture_output=True)
    rw = sum(len(x.split()) for x in rl)
    open(os.path.join(OUT, "wordcount_ms.txt"), "w").write(f"body_words={bw}\nref_words={rw}\nabstract_words={aw}\nrefs={n}\ntables=2\nfigures=2\n")
    print(f"body {bw} | abstract {aw} (≤250) | refs {n}")
    assert aw <= 250
