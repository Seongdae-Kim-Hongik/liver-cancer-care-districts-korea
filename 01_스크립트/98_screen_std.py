"""98 — 공간 선별 std 재판정: 9개 질환(METS 제외) crude E 대 간접 연령표준화 E_std 나란히 (2026-10-19)
입력: 04_분석/<TAG>/panel_<TAG>.csv(v1 crude E·cases·도시성·인구·면적·고령인구비율 원값), 02_패널/<TAG>_Estd.csv(38; MENTAL은 37),
      04_분석/<TAG>/results/nb_<TAG>.graph(81 그래프 = queen + 섬 최근접), results_screen/forced_<crude|std>_{RR,hyper}.csv(98_fit_forced.R),
      04_분석/00_공간선별_261019.csv·00_공간형_도농형_분류_261019.csv(기존 crude 판정, 주모형 phi)
지표(결과 전 고정; 95·96과 같은 정의):
  rho_old  시군구 14년 통합 SIR(Σcases/ΣE)과 고령인구비율(14년 평균)의 Spearman
  P90/P10  시군구 통합 SIR의 P90/P10
  I_raw    통합 log SIR Moran(행표준화, 999 순열) · I_min_year 연도별 log((cases+0.5)/E) Moran 최솟값 · persistence 2011-15 대 2020-24 SIR 순위 Spearman
  R2_UR·I_UR  통합 log SIR ~ 도시지역 인구 비율 + log 인구밀도(각 1·2차항) OLS의 R², 잔차 Moran(999 순열)  (96과 같은 규칙·같은 그래프)
  phi·최대 연결 핫스팟 덩어리  강제통제만 넣은 BYM2+RW1+iid NB(98_fit_forced.R; std는 고령인구비율 제외) — P(RR>1)>0.95 핫스팟의 그래프 연결 성분 최대 크기
분류(96 그대로): 약신호형 I_raw<0.40 & R2<0.30 → 공간형 I_UR≥0.30 & P<0.01 & phi≥0.45 & P90/P10≥1.30 → 도시·농촌형 R2≥0.30 & (I_UR<0.30 | P90/P10<1.30) → 그 외 혼합형
  crude 트랙(기준) = 96 기존 판정(주모형 phi) · std 트랙 = 위 규칙에 std 지표 + std 강제통제 모형 phi. 같은 모형끼리 비교용으로 crude 강제통제 모형 phi 판정도 병기.
산출: 04_분석/00_공간선별_std재판정_261019.csv/.md, figs_screen/urbanrural_scatter_std.png
사용: python3 98_screen_std.py [<YYMMDD>]
"""
import os, sys, warnings, numpy as np, pandas as pd
warnings.filterwarnings("ignore", category=RuntimeWarning)
from scipy.stats import spearmanr
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE); AN = os.path.join(ROOT, "04_분석"); DATE = sys.argv[1] if len(sys.argv) > 1 else "261019"
TAGS = ["PERIO", "INFECT", "ARTH", "HTN", "MENTAL", "DM", "LIVER", "BRCA", "GCA"]
KO = {"PERIO": "치주질환", "INFECT": "감염병", "ARTH": "관절염", "HTN": "고혈압", "MENTAL": "정신질환", "DM": "당뇨병", "LIVER": "간질환", "BRCA": "유방암", "GCA": "위암"}

def read_graph(f):
    L = open(f).read().split("\n"); nb = {}
    for line in L[1:]:
        t = line.split()
        if len(t) >= 2: nb[int(t[0])] = [int(x) for x in t[2:]]
    return nb
def clusters(nodes, nb):
    nodes = set(nodes); seen = set(); out = []
    for s in nodes:
        if s in seen: continue
        st = [s]; comp = []
        while st:
            v = st.pop()
            if v in seen: continue
            seen.add(v); comp.append(v); st += [u for u in nb.get(v, []) if u in nodes and u not in seen]
        out.append(comp)
    return sorted(out, key=len, reverse=True)
def moran(x, W, rng=None, nperm=999):
    z = x - x.mean(); I = float((z @ W @ z) / (z @ z))
    if rng is None: return I, np.nan
    sims = np.array([(lambda zp: (zp @ W @ zp) / (zp @ zp))(rng.permutation(z)) for _ in range(nperm)])
    return I, float((np.sum(sims >= I) + 1) / (nperm + 1))
def classify(I_raw, r2, I_ur, p_ur, phi, ratio):
    if I_raw < 0.40 and r2 < 0.30: return "약신호형"
    if I_ur >= 0.30 and p_ur < 0.01 and phi >= 0.45 and ratio >= 1.30: return "공간형"
    if r2 >= 0.30 and (I_ur < 0.30 or ratio < 1.30): return "도시·농촌형"
    return "혼합형"
def failed(I_ur, p_ur, phi, ratio):
    return ";".join(k for k, ok in (("I_UR≥0.30", I_ur >= .30), ("P<0.01", p_ur < .01), ("phi≥0.45", phi >= .45), ("P90/P10≥1.30", ratio >= 1.30)) if not ok) or "-"

SCR = pd.read_csv(os.path.join(AN, f"00_공간선별_{DATE}.csv")).set_index("TAG"); CL96 = pd.read_csv(os.path.join(AN, f"00_공간형_도농형_분류_{DATE}.csv")).set_index("TAG")
rows = []; scat = {}
for T in TAGS:
    D = os.path.join(AN, T); rng = np.random.default_rng(20261019)
    pan = pd.read_csv(f"{D}/panel_{T}.csv", encoding="utf-8-sig", usecols=lambda c: c in ("year", "fbd_region", "cases", "E", "population", "area_m2", "urban_population_share_raw", "older_adult_share_raw"))
    es = pd.read_csv(os.path.join(ROOT, "02_패널", f"{T}_Estd.csv"), encoding="utf-8-sig")
    pan = pan.merge(es[["year", "fbd_region", "E_std"]], on=["year", "fbd_region"], how="left", validate="one_to_one"); assert pan.E_std.notna().all()
    assert abs(pan.groupby("year").E_std.sum() - pan.groupby("year").cases.sum()).max() < 1e-6 * pan.cases.sum()
    nb = read_graph(f"{D}/results/nb_{T}.graph")
    R = {m: pd.read_csv(f"{D}/results_screen/forced_{m}_RR.csv") for m in ("crude", "std")}
    H = {m: pd.read_csv(f"{D}/results_screen/forced_{m}_hyper.csv") for m in ("crude", "std")}
    area = R["crude"][["area", "fbd_region"]]
    g0 = pan.groupby("fbd_region").agg(cases=("cases", "sum"), E=("E", "sum"), E_std=("E_std", "sum"), pop=("population", "mean"), km2=("area_m2", lambda x: x.mean() / 1e6),
                                        urban=("urban_population_share_raw", "mean"), old=("older_adult_share_raw", "mean"))
    g0 = area.merge(g0, left_on="fbd_region", right_index=True, how="inner").sort_values("area").dropna(subset=["urban", "pop", "km2"]); g0 = g0[g0.cases > 0]
    idx = {a: i for i, a in enumerate(g0.area.values)}; W = np.zeros((len(g0), len(g0)))
    for a, i in idx.items():
        nbs = [idx[b] for b in nb.get(a, []) if b in idx]
        if nbs: W[i, nbs] = 1 / len(nbs)
    dens = np.log(g0["pop"] / g0["km2"]).values; u = g0.urban.values; X = np.column_stack([np.ones(len(g0)), u, u ** 2, dens, dens ** 2])
    rec = dict(TAG=T, 질환=KO[T], n_sgg=len(g0))
    for m, ecol in (("crude", "E"), ("std", "E_std")):
        sir = (g0.cases / g0[ecol]).values; y = np.log(sir)
        beta, *_ = np.linalg.lstsq(X, y, rcond=None); res = y - X @ beta; r2 = 1 - res.var() / y.var()
        I_raw, p_raw = moran(y, W, rng); I_ur, p_ur = moran(res, W, rng)
        ratio = float(np.percentile(sir, 90) / np.percentile(sir, 10)); rho = float(spearmanr(sir, g0.old.values).correlation)
        # 연도별 Moran 최솟값(관측 지역 부분 행렬)
        imin = []
        for yr, d in pan.groupby("year"):
            d = d.set_index("fbd_region").reindex(g0.fbd_region); k = d.cases.notna().values & (d[ecol] > 0).values
            Wk = W[np.ix_(k, k)].copy(); rs = Wk.sum(1); Wk[rs > 0] = Wk[rs > 0] / rs[rs > 0, None]
            imin.append(moran(np.log((d.cases.values[k] + 0.5) / d[ecol].values[k]), Wk)[0])
        e1 = pan[pan.year <= 2015].groupby("fbd_region")[["cases", ecol]].sum(); e2 = pan[pan.year >= 2020].groupby("fbd_region")[["cases", ecol]].sum()
        cm = e1.index.intersection(e2.index); pers = float(spearmanr((e1.cases / e1[ecol])[cm], (e2.cases / e2[ecol])[cm]).correlation)
        rr = R[m]; hot = rr.loc[rr["class"] == "hotspot", "area"].tolist(); cold = rr.loc[rr["class"] == "coldspot", "area"].tolist(); hc = clusters(hot, nb)
        hy = H[m]; phi = float(hy[hy.hyperpar.str.startswith("Phi")]["mean"].iloc[0])
        big = rr.set_index("area").loc[hc[0], "fbd_region"].tolist() if hc else []
        rec.update({f"rho_old_{m}": round(rho, 3), f"P90P10_{m}": round(ratio, 3), f"I_raw_{m}": round(I_raw, 3), f"I_min_year_{m}": round(min(imin), 3), f"persistence_{m}": round(pers, 3),
                    f"R2_UR_{m}": round(r2, 3), f"I_UR_{m}": round(I_ur, 3), f"P_UR_{m}": p_ur, f"r_logdens_{m}": round(float(np.corrcoef(dens, y)[0, 1]), 3),
                    f"phi_forced_{m}": round(phi, 3), f"hot_{m}": len(hot), f"cold_{m}": len(cold), f"largest_hot_{m}": len(hc[0]) if hc else 0,
                    f"forced_{m}": hy.forced.iloc[0], f"hot_core_{m}": "; ".join(big[:8])})
        rec[f"class_forced_{m}"] = classify(I_raw, r2, I_ur, p_ur, phi, ratio); rec[f"fail_{m}"] = failed(I_ur, p_ur, phi, ratio)
        rec[f"방향_{m}"] = "도시 높음" if rec[f"r_logdens_{m}"] > 0.2 else "농촌 높음" if rec[f"r_logdens_{m}"] < -0.2 else "도농 차 작음"
        if m == "std": scat[T] = (dens, y, rec["class_forced_std"], r2, I_raw, I_ur)
    # 기존 crude 판정(95·96, 주모형 phi)
    rec.update(phi_main_crude_95=float(SCR.loc[T, "S4_phi"]), largest_hot_main_crude_95=int(SCR.loc[T, "S5_largest_hot_cluster"]), I_raw_96=float(CL96.loc[T, "I_raw"]), I_UR_96=float(CL96.loc[T, "I_after_UR"]),
               track_crude_96=CL96.loc[T, "분류"])
    assert abs(rec["I_raw_crude"] - rec["I_raw_96"]) < 0.002 and abs(rec["I_UR_crude"] - rec["I_UR_96"]) < 0.002, (T, rec["I_raw_crude"], rec["I_raw_96"])
    rec["track_std"] = rec["class_forced_std"]
    rec["rho_abs_drop"] = round(abs(rec["rho_old_crude"]) - abs(rec["rho_old_std"]), 3)
    rows.append(rec)
O = pd.DataFrame(rows)
O.to_csv(os.path.join(AN, f"00_공간선별_std재판정_{DATE}.csv"), index=False, encoding="utf-8-sig")

# ── 그림(96과 같은 형식, std) ──
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
from matplotlib import font_manager
for fn in ["AppleGothic", "NanumGothic"]:
    if any(fn in f.name for f in font_manager.fontManager.ttflist): plt.rcParams["font.family"] = fn; break
plt.rcParams["axes.unicode_minus"] = False
fig, axes = plt.subplots(2, 5, figsize=(16, 6.4), sharex=True)
for ax, T in zip(axes.ravel(), TAGS):
    d, y, c, r2, i0, i1 = scat[T]
    ax.scatter(d, y, s=6, color="#4d4d4d"); z = np.polyfit(d, y, 2); xs = np.linspace(d.min(), d.max(), 50); ax.plot(xs, np.polyval(z, xs), color="#b2182b")
    ax.axhline(0, color="grey", lw=0.5); ax.set_title(f"{KO[T]} [{c}]\nR²(도농) {r2:.2f} · I {i0:.2f}→{i1:.2f}", fontsize=8.5)
axes.ravel()[-1].axis("off")
for ax in axes[1]: ax.set_xlabel("log population density (per km²)")
for ax in axes[:, 0]: ax.set_ylabel("log SIR (age-standardised) 2011-2024")
plt.tight_layout(); plt.savefig(os.path.join(AN, "figs_screen", "urbanrural_scatter_std.png"), dpi=170); plt.close()

# ── 보고서 md ──
f3 = lambda v: f"{v:.3f}"; f2 = lambda v: f"{v:.2f}"
L = [f"# 공간 선별 std 재판정 — 간접 연령표준화 기대건수(E_std) 기준 (20{DATE[:2]}-{DATE[2:4]}-{DATE[4:]})", "",
     "스크립트 `01_스크립트/38_build_Estd_all.py`(E_std) · `98_fit_forced.R`(강제통제 모형) · `98_screen_std.py`(지표·분류). 298분류 매핑은 `04_분석/00_298코드_질환매핑.csv`. 대사증후군(METS)은 제외(아래 6절).",
     "분류 규칙은 96과 같다(결과 전 고정). std 트랙의 phi와 핫스팟 덩어리는 강제통제만 넣은 BYM2+RW1+iid NB 모형(고령인구비율 제외, E_std offset)에서 얻었다. crude 트랙은 96 기존 판정(주모형 phi)이다. 같은 모형끼리 비교하도록 crude 강제통제 모형(고령인구비율 포함) 판정을 함께 적었다.", "",
     "## 1. 트랙 전후", "", "| 질환 | crude 트랙(96) | crude 트랙(강제통제 모형) | std 트랙 | std 공간형 미충족 항목 | 방향(std) |", "|---|---|---|---|---|---|"]
order = {"공간형": 0, "혼합형": 1, "도시·농촌형": 2, "약신호형": 3}
O2 = O.assign(_o=O.track_std.map(order)).sort_values(["_o", "I_UR_std"], ascending=[True, False])
for r in O2.itertuples(): L.append(f"| {r.질환} | {r.track_crude_96} | {r.class_forced_crude} | {r.track_std} | {r.fail_std} | {r.방향_std} |")
L += ["", "## 2. 핵심 지표 전후 (crude → std)", "", "| 질환 | SIR–고령 rho | SIR P90/P10 | 원자료 Moran | 도농 R² | 보정 후 Moran(P) | phi(강제통제 모형) | 최대 핫스팟 덩어리 |", "|---|---|---|---|---|---|---|---|"]
for r in O2.itertuples():
    L.append(f"| {r.질환} | {f3(r.rho_old_crude)} → {f3(r.rho_old_std)} | {f2(r.P90P10_crude)} → {f2(r.P90P10_std)} | {f3(r.I_raw_crude)} → {f3(r.I_raw_std)} | {f3(r.R2_UR_crude)} → {f3(r.R2_UR_std)} | "
             f"{f3(r.I_UR_crude)} → {f3(r.I_UR_std)} ({r.P_UR_std:.3f}) | {f3(r.phi_forced_crude)} → {f3(r.phi_forced_std)} | {r.largest_hot_crude} → {r.largest_hot_std} |")
L += ["", "주모형(세트 포함) crude phi는 95 값으로 PERIO·INFECT 등 질환마다 강제통제 모형 phi와 다를 수 있다(보충 csv `phi_main_crude_95`).", "",
      "## 3. 보조 지표 (crude → std)", "", "| 질환 | 연도별 Moran 최솟값 | 순위 지속성(2011-15 대 2020-24) | 핫스팟 수 | 콜드스팟 수 | 도농 축 상관 r(log 밀도) |", "|---|---|---|---|---|---|"]
for r in O2.itertuples():
    L.append(f"| {r.질환} | {f3(r.I_min_year_crude)} → {f3(r.I_min_year_std)} | {f3(r.persistence_crude)} → {f3(r.persistence_std)} | {r.hot_crude} → {r.hot_std} | {r.cold_crude} → {r.cold_std} | {f3(r.r_logdens_crude)} → {f3(r.r_logdens_std)} |")
L += ["", "## 4. 고령 교란 크기 순위 (|rho| 감소폭 = |rho_crude| − |rho_std|)", "", "| 순위 | 질환 | rho crude | rho std | |rho| 감소폭 | 지역 차 P90/P10 crude → std |", "|---|---|---|---|---|---|"]
for i, r in enumerate(O.sort_values("rho_abs_drop", ascending=False).itertuples(), 1):
    L.append(f"| {i} | {r.질환} | {f3(r.rho_old_crude)} | {f3(r.rho_old_std)} | {f3(r.rho_abs_drop)} | {f2(r.P90P10_crude)} → {f2(r.P90P10_std)} |")
sp = O2[O2.track_std == "공간형"].질환.tolist(); mx = O2[O2.track_std == "혼합형"].질환.tolist(); ur = O2[O2.track_std == "도시·농촌형"].질환.tolist(); wk = O2[O2.track_std == "약신호형"].질환.tolist()
L += ["", "## 5. 결론", "", f"- 표준화 후 공간형: {', '.join(sp) if sp else '없음'}", f"- 혼합형: {', '.join(mx) if mx else '없음'}", f"- 도시·농촌형: {', '.join(ur) if ur else '없음'}", f"- 약신호형: {', '.join(wk) if wk else '없음'}",
      "- 결정요인(다중우주)은 다시 돌리지 않았다. 트랙이 바뀐 질환은 다음 단계에서 E_std 주분석으로 재적합한다.", ""]
bord = O2[(O2.track_std != "공간형") & (O2.fail_std == "P90/P10≥1.30")]
L += ["### 5-1. 경계 사례(사전 규칙은 바꾸지 않음, 해석 참고용)", "",
      f"- 공간형 조건 중 지역 차(P90/P10 ≥ 1.30) 하나만 못 미친 질환: " + (", ".join(f"{r.질환} {r.P90P10_crude:.2f}→{r.P90P10_std:.3f}" for r in bord.itertuples()) if len(bord) else "없음") + ".",
      "  이 중 crude에서는 1.30을 넘었다가 표준화로 1.2~1.3배로 줄어든 질환(" + ", ".join(r.질환 for r in bord.itertuples() if r.P90P10_crude >= 1.30) + ")은 고령 축 지역 차가 빠진 결과이고, 감염병·치주질환은 crude에서도 1.30 미만이었다.",
      "- phi는 모형에 따라 달라진다. crude 기준 96 판정은 주모형(가설 세트 포함) phi, std는 강제통제 모형 phi다. 관절염은 crude 주모형 phi 0.399(혼합형)였으나 같은 강제통제 모형으로는 crude도 0.636(공간형)이어서, 관절염의 혼합형→공간형 전환은 표준화보다 모형 차이 몫이 크다. 정신질환 std 주모형 phi는 0.426(97), 강제통제 모형은 0.465다.",
      "- 관절염은 표준화 뒤에도 SIR–고령 rho가 0.78로 높다. 연령 구간이 70세 이상으로 열려 있어 80세 이상에서 급증하는 질환은 잔여 연령 교란이 남을 수 있다(정신질환 치매도 같은 문제).", ""]
L += ["## 6. 자료 정의와 한계", "",
      "- E_std = Σ_연령 시군구 연령별 분모 × 전국 연령별 진료율(298분류 코드 묶음 진료실인원 ÷ 전국 연령별 분모), 연도별 ΣE_std = Σcases 재척도. 연령 10세 8구간(70세 이상 묶음).",
      "- 연령 비율은 ST_agepop(성 구분 없음), 누락 시군구-연도 22건은 같은 시군구 가장 가까운 연도 비율(37과 같은 규칙). 분모 수준은 각 질환 패널 offset(인구, 위암은 주민등록인구, 유방암은 여성 주민등록인구).",
      "- 298분류 세부 코드 합은 한 사람이 둘 이상 분류로 진료받으면 중복 계산된다. 실인원이 아니라 연령 프로파일 용도이며 수준은 재척도로 관측에 맞췄다.",
      "- 유방암: 여성 연령 비율은 FBD_DATA_ZIP 주민등록 성·5세 인구(여자)로 시군구별 계산, 전국 rate 분모도 여성 연령별 인구. 298분류 표에는 성별이 없어 분자 C50에 남성 유방암(1% 미만)이 섞인다. 청주 2011~13은 청원군 합산 연령 구조를 썼다.",
      "- 성 표준화는 하지 않았다(전국 성·연령별 298분류 자료 없음). 성비는 강제통제로 남아 있다.",
      "- 대사증후군(METS) 제외: 종속이 검진 판정 인원이고 분모가 수검자수라 진료 연령 프로파일로 기대건수를 만들 수 없다. 검진 성·연령별 대사증후군 판정 자료(건보 건강검진통계 연령별 표)가 있으면 수검자 연령 구조로 같은 방식의 간접표준화를 검토할 수 있다(별도 메모, 이번에는 미실시).",
      "- 98 강제통제 모형은 결정요인 세트를 넣지 않은 선별용 모형이다. 핫스팟 수와 덩어리는 N이 커서 이분법처럼 나오므로 덩어리 크기와 핵심 지역을 함께 본다.", ""]
L += ["## 7. 최대 핫스팟 덩어리 앞 8곳 (std)", ""] + [f"- {r.질환}: {r.hot_core_std}" for r in O2.itertuples()]
open(os.path.join(AN, f"00_공간선별_std재판정_{DATE}.md"), "w", encoding="utf-8").write("\n".join(L) + "\n")
print(O2[["질환", "track_crude_96", "class_forced_crude", "track_std", "rho_old_crude", "rho_old_std", "P90P10_crude", "P90P10_std", "R2_UR_crude", "R2_UR_std", "I_UR_crude", "I_UR_std", "phi_forced_crude", "phi_forced_std", "largest_hot_crude", "largest_hot_std", "fail_std"]].to_string(index=False))
