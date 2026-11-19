# Liver cancer care across Korean districts, 2011-2024

Analysis code for the manuscript

> Kim S. *Does liver cancer care remain concentrated in southern Korean districts after age adjustment?* Manuscript submitted for publication.

Archived version: Zenodo, https://doi.org/10.5281/zenodo.24356080 (v1.0.1).

## Contents

This repository contains code only. The processed district-year data (master table, analytic panel, expected counts, result tables, adjacency graph, and boundary file) are not included; they are available from the author on reasonable request. All source statistics are public (see Data sources).

| Path | What it is |
|---|---|
| `01_스크립트/` | Analysis scripts (below) |
| `04_분석/HCC/sets_HCC_std3.json`, `config_HCC_std3.json`, `narrative_HCC.md` | Prespecified covariates, expected directions, forced controls, and model settings |
| `04_분석/HCC/MS/` | Scripts that read the result tables and write every number, table, and figure in the manuscript and its Supporting Information (the manuscript text source is not included, so the builders require it separately) |

Folder and some column names are in Korean because the source tables are Korean; each script has a header comment that describes its inputs and outputs.

## Data sources

All inputs are public, aggregated statistics. No individual-level data are included.

- Annual numbers of people treated for liver cancer (ICD-10 C22, principal diagnosis), by district of residence: National Health Insurance Service, Regional Medical Care Utilization Statistics, 2011-2024.
- Mid-year population by 5-year age group: Ministry of the Interior and Safety, resident registration statistics. The 2023 age block of Changwon duplicated the 2022 block in the source file and was corrected (`population_override` in `sets_HCC_std3.json`).
- District covariates (behaviors, metabolic and liver risk at screening, physical activity, sports facilities, social and deprivation indicators, screening uptake): Korean Statistical Information Service (KOSIS), the Community Health Survey, and NHIS statistics; sources are listed in Table S1 of the Supporting Information.

## Pipeline

Run from the repository root. Scripts 36, 38, 39, 40 and 80 rebuild the expected counts and the panel from the master tables; their raw-input paths point to the author's local copies of the public source files and are kept for transparency. With the processed data, the analysis can be reproduced from step 4.

| Step | Script | Output |
|---|---|---|
| 1 | `36_build_national_agerates.py`, `38_build_Estd_all.py`, `39_build_Estd_fine.py` | National age rates and expected counts (`02_패널/`) |
| 2 | `98_screen_std.py` | Spatial screening on age-standardized ratios |
| 3 | `80_build_disease_panel_v.py HCC` (`ST_VER=std3`) | Analytic panel |
| 4 | `81_fit_inla.R HCC` (`ST_VER=std3`, `ST_GRAPH=04_분석/HCC/graph_593.graph`, `ST_THREADS=1`; multiverse split with `ST_MV_STOP=1` then `ST_MV_RANGE=a-b` workers, see `04_분석/HCC/run_std3_chain.sh`) | Principal model, covariate-set comparison, 200-subset multiverse, window models (S3-S12) |
| 5 | `85_window_maps.R`, `86_yearly_maps_ehsa.py`, `86b_ehsa_modified_mk.py`, `87_window_grid.py` | Maps, emerging hot spot analysis |
| 6 | `88g_sens_prep.py HCC std3 GCA,ARTH` then `88g_sens_suite.R` (`GROUP=1..6`) | Sensitivity suite (S41) |
| 7 | `88h_ppc_varpart.R` | Posterior predictive checks, variance partition (S42) |
| 8 | `88k_struct_kh.R` with `kh_constraints.R`  | Knorr-Held I-IV with component-wise constraints, neighborhood and prior variants (S43) |
| 9 | `89g_sens_combine.py` | Combined sensitivity tables |
| 10 | `04_분석/HCC/MS/build/figs_hcc.py`, `build_ms_hcc.py`, `esm_ms_hcc.py` (helpers `tables_hcc.py`, `content_hcc.py`, `numbers_hcc.py`) | Figures, manuscript, and Supporting Information |

Example:

```bash
cd 01_스크립트 && ST_VER=std3 ST_THREADS=1 ST_GRAPH=../04_분석/HCC/graph_593.graph Rscript 81_fit_inla.R HCC
```

The boundary file is found at `data/boundary/final.shp` by default; set `ST_SHP` to use another path.

## Software

R 4.6.0 with R-INLA 25.10.19, spdep 1.4.2 and sf 1.1.1; Python 3.9.6 with pandas 2.3.3, geopandas 1.0.1, numpy 2.0.2, matplotlib 3.9.4 and python-docx. Full model specifications are in the Supplementary Methods.

## License

Code: MIT License (`LICENSE`).

## Contact

Seongdae Kim, Hongik University (kimsd@hongik.ac.kr)
