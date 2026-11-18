#!/usr/bin/env python3
# 99 — 2차 묶음 암 4종(대장암·폐암·간암·자궁경부암) 공간 선별 준비(2026-11-05, 7호 후보 선정). 38·98과 같은 정의·같은 규칙.
#  ① 298분류 → 암 정의 매핑(참조표 ICD가 정의 안에 완전히 들어가는 코드만):
#     CRC C18-C21(건보 대장암; 298분류가 C19-C21을 한 코드로 묶어 항문 C21이 섞임 → 연령 프로파일 용도로만 쓰므로 포함, 한계 기록)
#     LCA C33-C34 · HCC C22 · CERV C53(분모 = 여성 주민등록인구, 38 BRCA와 같은 규칙)
#  ② 전국 연령별 진료실인원(38의 kosis_codes·excel_codes 재사용) → rate[y,a] = 진료실인원 / 전국 연령별 분모
#  ③ E_std = Σ_a pop[d,y,a] × rate[y,a], 연도별 ΣE_std = Σcases 재척도. crude E = offset × 전국 조율.
#  ④ 98·98_fit_forced.R 입력 형식으로 저장: 04_분석/<TAG>/panel_<TAG>.csv(PERIO v1 패널의 공변량 열 + 새 cases·E·offset), config_<TAG>.json(PERIO v1 forced),
#     results/nb_<TAG>.graph(PERIO와 같은 그래프), 02_패널/<TAG>_Estd.csv
#  사용: python3 99_screen_cancers_prep.py
import os, sys, json, shutil, importlib.util
import numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE); AN = os.path.join(ROOT, "04_분석")
spec = importlib.util.spec_from_file_location("m38", os.path.join(HERE, "38_build_Estd_all.py")); m38 = importlib.util.module_from_spec(spec); spec.loader.exec_module(m38)
NFC = m38.NFC
NEW = {"CRC": ("대장암", [("C18", "C21")], "C18-C21"), "LCA": ("폐암", [("C33", "C34")], "C33-C34"), "HCC": ("간암", [("C22", "C22")], "C22"), "CERV": ("자궁경부암", [("C53", "C53")], "C53")}
CHANGWON = dict(year=2023, fbd_region="경상남도창원시", population=1009038)   # 창원 2023 인구 교정(메모리 changwon-2023-population-stale)

def mapping():
    ref = m38.ref_table(os.path.join(m38.SRC, "2020_298 질병분류참조표.hwp")); rows = []
    for T, (ko, D, txt) in NEW.items():
        for c, (nm, icd) in ref.items():
            st = [m38.overlap(r, D) for r in m38.icd_ranges(icd)]
            if all(s == "none" for s in st): continue
            rows.append(dict(TAG=T, 질환=ko, 정의=txt, code298=c, 명칭=nm, ICD=icd, 포함=all(s == "full" for s in st)))
    return pd.DataFrame(rows)

if __name__ == "__main__":
    M = mapping(); print(M.to_string()); M.to_csv(os.path.join(AN, "00_298코드_암4종매핑_261105.csv"), index=False, encoding="utf-8-sig")
    CODES = {T: M[(M.TAG == T) & M["포함"]].code298.astype(int).tolist() for T in NEW}; assert all(CODES.values()), CODES
    allc = sorted({c for v in CODES.values() for c in v}); ko_, kdiff = m38.kosis_codes(allc)
    L = pd.DataFrame(ko_ + m38.excel_codes(allc), columns=["year", "code", "age10", "patients"]).groupby(["year", "code", "age10"], as_index=False).patients.sum()
    A = L[L.age10 != "TOTAL"]; assert sorted(A.year.unique()) == list(range(2011, 2025))
    base = pd.read_csv(os.path.join(AN, "PERIO", "panel_PERIO.csv"), encoding="utf-8-sig"); base["fbd_region"] = base.fbd_region.map(NFC)
    MA = pd.read_parquet(os.path.join(ROOT, "02_패널", "MASTER_시군구_연도_wide.parquet"), columns=["year", "fbd_region", "population"] + [f"nhis__{v[0]}__진료실인원수" for v in NEW.values()])
    MA["fbd_region"] = MA.fbd_region.map(NFC); MA = MA[(MA.year >= 2011) & (MA.year <= 2024)]
    m = (MA.year == CHANGWON["year"]) & (MA.fbd_region == NFC(CHANGWON["fbd_region"])); assert m.sum() == 1; MA.loc[m, "population"] = CHANGWON["population"]
    WT = m38.shares_total(); WF = FT = None; SUM = []
    for T, (ko, D, txt) in NEW.items():
        P = base.drop(columns=["cases", "E", "SIR", "offset"]).merge(MA[["year", "fbd_region", "population", f"nhis__{ko}__진료실인원수"]].rename(columns={f"nhis__{ko}__진료실인원수": "cases", "population": "pop_master"}),
                                                                 on=["year", "fbd_region"], how="left", validate="one_to_one")
        assert P.cases.notna().all() and len(P) == 3206, (T, P.cases.isna().sum())
        P["population"] = P.pop_master; P = P.drop(columns=["pop_master"])
        if T == "CERV":
            WF, FT, _ = m38.shares_female(P.fbd_region.unique()); FT.index.names = ["fbd_region", "year"]
            P = P.merge(FT.rename("offset").reset_index() if isinstance(FT, pd.Series) else FT.reset_index().rename(columns={FT.columns[0]: "offset"}), on=["fbd_region", "year"], how="left")
            assert P.offset.notna().all(); W = WF
        else: P["offset"] = P.population; W = WT
        nat = P.groupby("year").apply(lambda d: d.cases.sum() / d.offset.sum(), include_groups=False); P["E"] = P.offset * P.year.map(nat); P["SIR"] = P.cases / P.E
        AP, fb = m38.agepop(P[["year", "fbd_region", "offset"]], W)
        num = A[A.code.isin(CODES[T])].groupby(["year", "age10"]).patients.sum(); den = AP.groupby(["year", "age10"])["pop"].sum()
        rate = (num / den).rename("rate").reset_index()
        X = AP.merge(rate, on=["year", "age10"], how="left"); assert X.rate.notna().all(); X["e"] = X["pop"] * X.rate
        E = X.groupby(["year", "fbd_region"], as_index=False).e.sum(); P = P.merge(E, on=["year", "fbd_region"], how="left", validate="one_to_one")
        P["E_std"] = P.e * P.groupby("year").cases.transform("sum") / P.groupby("year").e.transform("sum")
        out = P[["year", "fbd_region", "E_std"]].assign(SIR_crude=P.cases / P.E, SIR_std=P.cases / P.E_std)
        out.to_csv(os.path.join(ROOT, "02_패널", f"{T}_Estd.csv"), index=False, encoding="utf-8-sig")
        d = os.path.join(AN, T); os.makedirs(os.path.join(d, "results"), exist_ok=True)
        P.drop(columns=["e", "E_std"]).to_csv(os.path.join(d, f"panel_{T}.csv"), index=False, encoding="utf-8-sig")
        shutil.copy2(os.path.join(AN, "PERIO", "config_PERIO.json"), os.path.join(d, f"config_{T}.json"))
        shutil.copy2(os.path.join(AN, "PERIO", "results", "nb_PERIO.graph"), os.path.join(d, "results", f"nb_{T}.graph"))
        r24 = rate[rate.year == 2024].set_index("age10").rate
        SUM.append((T, ko, CODES[T], int(P.cases.sum()), round(float((P.E_std / P.E).min()), 3), round(float((P.E_std / P.E).max()), 3), len(fb)))
        print(f"[99] {T} {ko}: 코드 {CODES[T]} · 14년 진료 {int(P.cases.sum()):,} · E_std/E {SUM[-1][4]}~{SUM[-1][5]} · 2024 연령별 율(천 명당) {dict((k, round(v*1e3, 2)) for k, v in r24.items())}")
    print("[99] 저장: 02_패널/<TAG>_Estd.csv, 04_분석/<TAG>/panel·config·graph (CRC LCA HCC CERV)")
