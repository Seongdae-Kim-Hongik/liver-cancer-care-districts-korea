# -*- coding: utf-8 -*-
# figs_hcc.py — 투고용(패널 문자 2배 26pt 대문자, N 3배) 그림 2장 + 보충 그림 S1(결과 CSV·경계에서 다시 그림, 1000 dpi RGB, Arial 8 pt, 그림 안 설명문 없음, 한글 없음)
#  Fig 1 (a) 전 기간 잔차 공간 RR 지도 (b) 조율·연령표준화율 추이 · Fig 2 (a) EHSA (b) 세 창 핫스팟 횟수 · Fig 3 강건 5개 변수의 모형별 RR
import os, unicodedata, numpy as np, pandas as pd, geopandas as gpd, matplotlib
matplotlib.use("Agg"); import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap, BoundaryNorm
from matplotlib.patches import Patch
from matplotlib.lines import Line2D
from PIL import Image
from numbers_hcc import load, ROB
HERE = os.path.dirname(os.path.abspath(__file__)); B = os.path.dirname(os.path.dirname(HERE)); RS = os.path.join(B, "results_std3")
FIG = os.path.join(HERE, "figs"); OUTF = os.path.join(os.path.dirname(HERE), "out", "Figures"); os.makedirs(FIG, exist_ok=True); os.makedirs(OUTF, exist_ok=True)
SHP = os.environ.get("ST_SHP", os.path.join(HERE, "..", "..", "..", "..", "data", "boundary", "final.shp"))
MM = 1 / 25.4; W = 170 * MM; DPI = 1000; LW = 0.3
plt.rcParams.update({"font.family": "Arial", "font.size": 8, "legend.fontsize": 8, "legend.title_fontsize": 8, "axes.linewidth": 0.5, "pdf.fonttype": 42})
NFC = lambda s: unicodedata.normalize("NFC", str(s)).strip()
N = load()
G = gpd.read_file(SHP); G["region"] = G.region.map(NFC); G["cd"] = G.sigungu_cd.astype(str); G["sido"] = G.sigungu_cd.astype(str).str[:2]; SIDO = G.dissolve("sido")   # 결합은 시군구 코드(cd)로만, 이름 결합 금지 규칙
XL = (G.total_bounds[0], G.total_bounds[2]); YL = (G.total_bounds[1], G.total_bounds[3])
rd = lambda f: pd.read_csv(os.path.join(RS, f), encoding="utf-8-sig", dtype={"sigungu_cd": str})
def letter(ax, ch, dx=0.0):   # 패널 문자: 크게(13pt 볼드), 데이터 영역 밖 위쪽 띠(06 §6-C)
    ax.text(dx, 1.04, ch, transform=ax.transAxes, fontsize=26, fontweight="bold", va="bottom", ha="left", clip_on=False)
def mapax(ax):
    SIDO.boundary.plot(ax=ax, color="#404040", linewidth=0.45); ax.set_xlim(*XL); ax.set_ylim(*YL); ax.set_axis_off(); ax.set_aspect("equal")
    x0, x1 = XL; y0, y1 = YL; W_ = x1 - x0; H_ = y1 - y0   # 방위표·축척(좌표 단위 m, Korea TM)
    bx, by = x0 + 0.62 * W_, y0 + 0.04 * H_
    ax.plot([bx, bx + 100000], [by, by], color="black", lw=1.2, solid_capstyle="butt"); ax.text(bx + 50000, by + 0.012 * H_, "100 km", ha="center", va="bottom", fontsize=7)
    ax.annotate("N", xy=(x0 + 0.92 * W_, y0 + 0.99 * H_), xytext=(x0 + 0.92 * W_, y0 + 0.75 * H_), ha="center", va="center", fontsize=24, fontweight="bold", arrowprops=dict(arrowstyle="-|>", color="black", lw=2.4, mutation_scale=30))   # 방위표 3배(11/8 규칙)
def save(fig, k):
    p = os.path.join(FIG, f"Fig{k}.png"); fig.savefig(p, dpi=DPI, facecolor="white", bbox_inches="tight", pad_inches=0.02); plt.close(fig)
    im = Image.open(p).convert("RGB"); im.save(p, dpi=(DPI, DPI)); im.save(os.path.join(OUTF, f"Figure{k}.tif"), dpi=(DPI, DPI), compression="tiff_lzw")
    return im.size

# Fig 1
S6 = rd("S6_spatial_RR.csv"); S6["fbd_region"] = S6.fbd_region.map(NFC); assert len(S6) == 229
BR = [0, 0.8, 0.9, 0.95, 1, 1.05, 1.1, 1.2, 99]; LB = ["<0.80", "0.80-0.89", "0.90-0.94", "0.95-0.99", "1.00-1.04", "1.05-1.09", "1.10-1.19", "≥1.20"]
PAL = ["#2166AC", "#4393C3", "#92C5DE", "#D1E5F0", "#FDDBC7", "#F4A582", "#D6604D", "#B2182B"]
fig = plt.figure(figsize=(W, 3.9)); a0 = fig.add_axes([0.0, 0.17, 0.50, 0.80]); a1 = fig.add_axes([0.62, 0.30, 0.36, 0.60])
d = S6.set_index("sigungu_cd"); gg = G.copy(); gg["v"] = gg.cd.map(d.RR); gg["c"] = gg.cd.map(d["class"]); assert gg.v.notna().all()
gg.plot(ax=a0, column="v", cmap=ListedColormap(PAL), norm=BoundaryNorm(BR, len(PAL)), edgecolor="#a0a0a0", linewidth=LW); mapax(a0)
gg[gg.c == "coldspot"].boundary.plot(ax=a0, color="#2171B5", linewidth=0.6, linestyle=(0, (2.0, 1.2))); gg[gg.c == "hotspot"].boundary.plot(ax=a0, color="black", linewidth=0.6); letter(a0, "A")
h = [Patch(facecolor=c, edgecolor="#777777", linewidth=LW, label=l) for c, l in zip(PAL, LB)] + [Patch(facecolor="none", edgecolor="black", linewidth=0.8, label="Hot spot"), Patch(facecolor="none", edgecolor="#2171B5", linewidth=0.8, linestyle="--", label="Cold spot")]
a0.legend(handles=h, title="Residual spatial RR", loc="upper center", bbox_to_anchor=(0.5, 0.0), ncol=3, frameon=False, columnspacing=0.8, handlelength=1.3)
yrs = sorted(N["asr"]); P = pd.read_csv(os.path.join(B, "panel_HCC_std3.csv")); y = P.groupby("year")[["cases", "offset"]].sum(); cr = 1e5 * y.cases / y.offset
a1.plot(yrs, [cr[t] for t in yrs], color="#404040", marker="o", ms=2.5, lw=0.9, label="Crude")
a1.plot(yrs, [N["asr"][t] for t in yrs], color="#b2182b", marker="s", ms=2.5, lw=0.9, label="Age-standardized")
a1.set_xticks([2011, 2014, 2017, 2020, 2024]); a1.set_ylim(80, 180); a1.set_ylabel("Treated persons per 100,000 population"); a1.set_xlabel("Year")
a1.spines[["top", "right"]].set_visible(False); a1.legend(frameon=False, loc="upper left"); letter(a1, "B", dx=-0.22)
s1 = save(fig, 1)

# Fig 2
EH = rd("S11_ehsa.csv"); EH["fbd_region"] = EH.fbd_region.map(NFC)
CATS = [f"{a} {b}" for b in ("hot", "cold") for a in ("New", "Consecutive", "Intensifying", "Persistent", "Diminishing", "Sporadic", "Oscillating", "Historical")] + ["No pattern"]
EPAL = {"New hot": "#fdd0a2", "Consecutive hot": "#fdae6b", "Intensifying hot": "#a50f15", "Persistent hot": "#de2d26", "Diminishing hot": "#fc9272", "Sporadic hot": "#fee0d2", "Oscillating hot": "#d6a5c9", "Historical hot": "#bcbddc",
        "New cold": "#c6dbef", "Consecutive cold": "#9ecae1", "Intensifying cold": "#08519c", "Persistent cold": "#3182bd", "Diminishing cold": "#6baed6", "Sporadic cold": "#deebf7", "Oscillating cold": "#a1d99b", "Historical cold": "#c7e9c0", "No pattern": "#f7f7f7"}
WM = rd("S4b_window_spatialRR.csv"); WM["fbd_region"] = WM.fbd_region.map(NFC)
nh = WM[WM["class"] == "hotspot"].groupby("sigungu_cd").size(); nc = WM[WM["class"] == "coldspot"].groupby("sigungu_cd").size()
assert int((nh == 3).sum()) == N["hot_all_windows"]
fig, (a0, a1) = plt.subplots(1, 2, figsize=(W, 4.3)); fig.subplots_adjust(left=0.0, right=1.0, top=0.95, bottom=0.30, wspace=0.02)
gg = G.copy(); gg["c"] = gg.cd.map(EH.set_index("sigungu_cd").EHSA); assert gg.c.notna().all()
gg.plot(ax=a0, color=[EPAL[c] for c in gg.c], edgecolor="#a0a0a0", linewidth=LW); mapax(a0); letter(a0, "A")
cnt = EH.EHSA.value_counts(); pres = [c for c in CATS if c in cnt.index]
a0.legend(handles=[Patch(facecolor=EPAL[c], edgecolor="#777777", linewidth=LW, label=f"{c} ({cnt[c]})") for c in pres], title="Category (districts)", loc="upper center", bbox_to_anchor=(0.5, 0.0), ncol=2, frameon=False, columnspacing=0.8, handlelength=1.2)
hh = gg.cd.map(nh).fillna(0).astype(int); cc = gg.cd.map(nc).fillna(0).astype(int)
gg["k"] = np.where((hh > 0) & (cc > 0), 9, hh - cc)   # 9 = 창에 따라 핫·콜드 모두
KP = {-3: "#2166AC", -2: "#67A9CF", -1: "#D1E5F0", 0: "#f7f7f7", 1: "#FDDBC7", 2: "#EF8A62", 3: "#B2182B", 9: "#c2a5cf"}
KL = {-3: "Cold spot in 3 windows", -2: "Cold spot in 2", -1: "Cold spot in 1", 0: "Neither", 1: "Hot spot in 1", 2: "Hot spot in 2", 3: "Hot spot in 3 windows", 9: "Hot and cold in different windows"}
gg.plot(ax=a1, color=[KP[k] for k in gg.k], edgecolor="#a0a0a0", linewidth=LW); mapax(a1); letter(a1, "B")
kc = gg.k.value_counts()
a1.legend(handles=[Patch(facecolor=KP[k], edgecolor="#777777", linewidth=LW, label=f"{KL[k]} ({kc.get(k, 0)})") for k in (3, 2, 1, 0, -1, -2, -3, 9) if kc.get(k, 0)], title="Windows 2011-2015, 2016-2019, 2020-2024", loc="upper center", bbox_to_anchor=(0.5, 0.0), ncol=2, frameon=False, columnspacing=0.8, handlelength=1.2)
s2 = save(fig, "S1")

# Fig 2 (본문) — 부분집합 안정 7개 변수의 모형별 RR
LAB = {"screening_normalB_obesity_share": "Obesity management needed", "screening_normalB_diabetes_share": "Diabetes management needed", "screening_normalB_liver_share": "Liver-function management needed",
       "medical_aid1_patients_per_100k": "Medical Aid beneficiaries treated", "regular_employee_share": "Regular employment"}
ORD = ["medical_aid1_patients_per_100k", "screening_normalB_diabetes_share", "screening_normalB_liver_share", "screening_normalB_obesity_share", "regular_employee_share"]
assert set(ORD) == set(ROB)
MOD = [("Principal model", lambda v: (N["main"][v]["IRR"], N["main"][v]["lo"], N["main"][v]["hi"]), "#000000", "o"),
       ("Knorr-Held type I", lambda v: N["s43"][("KH_typeI", v)][:3], "#2166AC", "s"),
       ("Knorr-Held type IV", lambda v: N["s43"][("KH_typeIV", v)][:3], "#B2182B", "D"),
       ("Within-district component", lambda v: N["bw"][v + "__within"][:3], "#1b7837", "v"),
       ("Between-district component", lambda v: N["bw"][v + "__between"][:3], "#E08214", "P"),
       ("Gastric cancer (comparison outcome)", lambda v: N["nco"][("GCA", v)][:3], "#7f7f7f", "^")]
fig, ax = plt.subplots(figsize=(W, 4.0)); fig.subplots_adjust(left=0.30, right=0.98, top=0.98, bottom=0.22)
off = np.linspace(-0.32, 0.32, len(MOD))
for i, v in enumerate(ORD):
    for (lab, f, col, mk), o in zip(MOD, off):
        e, lo, hi = f(v); ax.plot([lo, hi], [i + o] * 2, color=col, lw=0.8); ax.plot(e, i + o, marker=mk, color=col, ms=3.2, mew=0, ls="none")
ax.axvline(1, color="#404040", lw=0.5, ls=":"); ax.set_yticks(range(len(ORD))); ax.set_yticklabels([LAB[v] for v in ORD]); ax.invert_yaxis()
xt = [0.96, 0.98, 1.00, 1.02, 1.04, 1.06, 1.08, 1.10]; ax.set_xticks(xt); ax.set_xticklabels([f"{x:.2f}" for x in xt]); ax.minorticks_off()
ax.set_xlabel("Rate ratio per 1 SD (95% credible interval)"); ax.spines[["top", "right"]].set_visible(False)
ax.legend(handles=[Line2D([0], [0], color=c, marker=m, lw=0.8, ms=3.2, mew=0, label=l) for l, _, c, m in MOD], loc="upper center", bbox_to_anchor=(0.35, -0.13), ncol=3, frameon=False)
s3 = save(fig, 2)
for k, s in zip((1, "S1", 2), (s1, s2, s3)): print(f"Fig{k}: {s[0]}x{s[1]} px = {s[0]/DPI*25.4:.0f} x {s[1]/DPI*25.4:.0f} mm")
