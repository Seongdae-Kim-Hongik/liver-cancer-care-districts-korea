#!/bin/bash
# HCC(간암, 7호) std3 전 체인 — 런북 15 §1-B + 7호부터 S7 병렬화(81 ST_MV_STOP/ST_MV_RANGE, 2026-11-05)
#  비교 결과: 위암(GCA)·관절염(ARTH). 감염병(INFECT)은 B형·C형 간염(B15-B19)을 포함해 간암 병인과 겹치므로 쓰지 않음.
set -x
S="${ST_ROOT:-$(cd "$(dirname "$0")/../.." && pwd)}"; cd "$S"
RC="${ST_FBDZIP_CORRECTED:?set ST_FBDZIP_CORRECTED to the corrected population folder}"
GR="$S/04_분석/HCC/graph_593.graph"; T=HCC; D=261105; NW=5; NMV=200
ST_FBDZIP="$RC" python3 01_스크립트/39_build_Estd_fine.py $T || exit 1   # 선별용 panel_HCC.csv가 이미 창원 교정 인구라 첫 단계도 교정 원자료 사용
ST_VER=std3 python3 01_스크립트/80_build_disease_panel_v.py $T || exit 1
ST_FBDZIP="$RC" ST_E2_PANEL_SUF=_std3 python3 01_스크립트/39_build_Estd_fine.py $T || exit 1
ST_VER=std3 python3 01_스크립트/80_build_disease_panel_v.py $T || exit 1
python3 ../논문_마스터자료/00_분석전_데이터게이트/data_gate.py 04_분석/$T/panel_${T}_std3.csv --region fbd_region > 04_분석/$T/data_gate_${T}_std3_$D.txt 2>&1
echo "GATE rc=$?"
( for V in s577 s2 s8; do ST_VER=$V python3 01_스크립트/80_build_disease_panel_v.py $T && (cd 01_스크립트 && ST_VER=$V ST_THREADS=1 ST_MV_N=2 ST_GRAPH=$([ $V = s577 ] || echo "$GR") Rscript 81_fit_inla.R $T); done > 04_분석/$T/run_sens3.log 2>&1 ) &
# 81: S1~S6 + S7 사양표까지(ST_MV_STOP) → 사양 구간 병렬 → 본 실행(합치기·요약·S9 이후) → 82·83
export ST_VER=std3 ST_THREADS=1 ST_GRAPH="$GR"
(cd 01_스크립트 && ST_MV_STOP=1 Rscript 81_fit_inla.R $T) > 04_분석/$T/run_std3_81a.log 2>&1 || exit 1
STEP=$(( NMV / NW ))
for k in $(seq 0 $((NW-1))); do a=$(( k*STEP+1 )); b=$(( (k+1)*STEP )); (cd 01_스크립트 && ST_MV_RANGE=$a-$b Rscript 81_fit_inla.R $T) > 04_분석/$T/run_std3_81_mv_$a.log 2>&1 & sleep 20; done
wait
(cd 01_스크립트 && Rscript 81_fit_inla.R $T) > 04_분석/$T/run_std3_81b.log 2>&1 || exit 1
python3 01_스크립트/82_core_report.py $T $D > 04_분석/$T/run_std3_82.log 2>&1
python3 01_스크립트/83_check_report.py $T $D >> 04_분석/$T/run_std3_82.log 2>&1
echo "CHAIN done"
python3 01_스크립트/87_window_grid.py $T std3; (cd 01_스크립트 && TAG=$T ST_VER=std3 Rscript 85_window_maps.R $T std3); python3 01_스크립트/86_yearly_maps_ehsa.py $T std3
python3 01_스크립트/88g_sens_prep.py $T std3 GCA,ARTH || exit 1
cd 01_스크립트; export TAG=$T NCO=GCA,ARTH
L=../04_분석/$T
for G in 1 2 3 4 5 6; do GROUP=$G Rscript 88g_sens_suite.R > $L/run_std3_88g_$G.log 2>&1 & done
Rscript 88h_ppc_varpart.R > $L/run_std3_88h.log 2>&1 &
for G in nb struct kh; do Rscript 88k_struct_kh.R $G > $L/run_std3_88k_$G.log 2>&1 & done
wait
if grep -q 'KH_typeII FAILED' $L/run_std3_88k_kh.log; then mv $L/results_std3/S43_part_KH_typeII.csv $L/results_std3/S43_part_KH_typeII_failed_init.csv.bak; KH_INIT=0 Rscript 88k_struct_kh.R kh > $L/run_std3_88k_kh_init0.log 2>&1; fi
cd ..; TAG=$T ST_VER=std3 python3 01_스크립트/89g_sens_combine.py $T std3 > 04_분석/$T/run_std3_89g.log 2>&1
echo "ALL rc=$?"; grep -l "FAILED" 04_분석/$T/run_std3_88*.log; true
