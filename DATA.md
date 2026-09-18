# Data sources and availability

Four sources feed the pipeline. Three are public and are included in this repository. One is
licensed and is not.

| Source | Level | Coverage | In this repo |
|---|---|---|---|
| ORBIS / Bankscope (Bureau van Dijk) | Bank-year | 636 EU banks, 1996-2017 | **No**, licensed |
| IMF WEO, IMF IFS, World Bank WDI, BIS | Country-year | 25 EU countries, 1995-2017 | Yes |
| Laeven & Valencia (2026) systemic banking crises database | Country-year | 1970-2025 | Yes |

Scope throughout is 25 EU countries. Cyprus and Malta are excluded on data availability.

---

## 1. ORBIS / Bankscope — not distributed

The bank-level extract is licensed from Bureau van Dijk (Moody's) under a subscription held by
the University of Twente. The licence does not permit redistribution, so neither the extract
nor anything derived from it at bank level is committed here. Specifically excluded:

```
data/micro/                  the extract, the preclean and the clean bank panels
data/merged/                 micro joined to macro and to the crisis label
data/engineered/             the lagged modelling panels
outputs/attribution/*/shap_values_*    per-observation SHAP, indexed by bank_id
```

Everything else in `outputs/` is aggregated to model, feature or country level and is included,
so the published tables and figures can be inspected without the underlying panel.

### Reproducing the extract

Anyone with an institutional ORBIS licence can rebuild the input file. The pipeline expects it at
`data/micro/raw/orbis_MICRO_all_EU25_m_EUR_1996_2017.xlsx`. Its second sheet (`Results`) holds the
identifier columns and the financial data; the first (`Search summary`) is the ORBIS export log.

The extract used in the thesis is ORBIS data update 372001 (30/01/2026), exported 01/02/2026. ORBIS
revises and backfills historical accounts between updates, and entities enter and leave the
database, so a new extract with the same search will not return exactly the same 636 entities or
values, and results built on it will differ from the published ones.

Search strategy, as recorded in the export log (steps combined with AND):

1. NACE Rev. 2, primary codes only: **641 Monetary intermediation**
2. Status: active and inactive companies (inactive kept to limit survivorship bias)
3. Consolidation code: **C1** or **C2** (consolidated accounts)
4. Country: the 25 EU countries listed in `notebooks/02_macro_construction.ipynb` (`EU25_ISO3`)

Search options: exclude companies with no recent financial data; exclude public
authorities, states and governments. This returned 636 entities.

Export settings:

- Annual data, 1996-2017
- Values in **millions of EUR**
- Consolidation code included as an identifier column

NACE 641 is broader than "banks": see [Sample composition](#sample-composition-non-banks-in-the-extract)
below.

Identifier columns requested:

```
Company name Latin alphabet · BvD ID number · Country ISO code
NACE Rev. 2 core code (4 digits) · Consolidation code
```

The 21 financial fields requested, each supplied as one column per year:

```
Total assets EUR                                  Total equity EUR
Total liabilities and equity EUR                  Total customer deposits EUR
Gross loans & advances to customers EUR           Net loans & advances to customers EUR
Impaired / Non-performing loans to customers EUR  Loan Loss Reserves (Memo) EUR
Net impairment charges on loans & advances EUR    Interbank liabilities EUR
Interbank assets / Interbank liabilities          Total off-balance sheet exposure EUR
Net interest income (expense) EUR                 Net interest margin (avg total earning assets)
Operating Income EUR                              Total operating expenses EUR
Cost-to-income (Efficiency) ratio                 ROA using Net income
ROE using Net income                              Total capital adequacy ratio
Tier 1 Ratio
```

`Tier 1 Ratio` is requested but does not survive the missingness thresholds, so it appears in no
final specification.

Ten further indicators are constructed from these in `01_micro_construction.ipynb`: equity ratio,
leverage, log assets, asset growth, log loans, loan growth, loans-to-assets, loans-to-deposits,
deposits-to-liabilities and total liabilities. The mapping from ORBIS names to the short codes used
throughout the code is committed at `data/micro/dictionaries/variable_names_micro.csv`.

Note that `cr_impchg` is **impairment charges**, a level in EUR, not a change. The `chg` is short
for charges. Being an unscaled flow it scales with bank size.

### Sample composition: non-banks in the extract

The NACE filter is not as tight as intended. Code 641 covers both **6411 Central banking** and
**6419 Other monetary intermediation**, and ORBIS assigns 6411 to a number of Irish companies that
are not banks. The problem was found after the thesis results were produced (checked 17-09-2026).

**Corrected for the 2026 rerun** (`01_micro_construction.ipynb`, section 4b): the pipeline now keeps
NACE 6419 only, drops entities that report none of the five core balance-sheet items (deposits, gross
loans, equity, interbank liabilities, net interest income) in any year, and drops six group entities
whose operating bank is also in the extract. That removes 84 of the 579 entities with data (4,683 to
4,405 bank-years). The variable selection is kept as published. The description below is of the
extract as used for the thesis results; see `RERUN.md` for what the rerun changes.

Of the 636 entities, 598 carry code 6419 and 36 carry 6411, with one each on 4618 and 6410.
**34 of the 36 code-6411 entities are Irish**, so only 18 of the 52 Irish entities are coded 6419.
The Irish 6411 group is mostly non-bank companies and holding companies (for example Glennon Bros.
Holdings, Bimeda Holdings, Fitzpatricks Garage Group, Maiden Foods and Logicalis Ireland), plus a
few foreign banks recorded under an Irish identifier (Aareal Bank AG, HSBC Bank PLC, The Royal Bank
of Scotland N.V., Bankinter SA, Citco Bank Nederland NV). Outside Ireland the four non-6419 entities
are two central banks (Bulgarian National Bank, Banque de France), a sugar trading company and an
Italian holding company.

These entities have no reported deposits, gross loans, equity, interbank liabilities or net
interest income in ORBIS (100% missing for the Irish 6411 group), only total assets and profitability.
The panel imputation (within-bank interpolation, then bank mean, then **year median**) therefore
fills those lines with the cross-bank median for the year. In the modelling data they look like a
median bank on the balance-sheet ratios while their total assets are in the tens of millions EUR.

How much of the modelling data they make up. Only years up to 2012 enter any training or test set,
which removes most of them, and all four non-6419 entities outside Ireland (their data start in 2014):

| Panel | Irish 6411 rows (≤2012) | Crisis observations | Crisis observations in test years |
|---|---|---|---|
| Lag-1 (`11a`, `11b`) | 18 of 1,997 | 13 of 727 (1.8%) | 6 of 252 (2.4%) |
| Lag-2 (`11c`, `11d`) | 12 of 1,616 | 10 of 687 (1.5%) | 4 of 230 (1.7%) |

The 18 lag-1 rows belong to six entities, one of which (Aareal Bank AG) is a bank; the other five
are non-banks. Every Irish observation in the 2010-2012 test years is a crisis observation, because
the Laeven and Valencia Irish episode covers those years. The share is small, but it is concentrated
in the positive class.

The table covers `11a`-`11d`, where the rows enter all three configurations (the macro-only
configuration there is also estimated on bank-year rows). `rt2a` and `rt2b` read the same panels and
include the same entities; their counts are not tabulated. The country-level notebooks
(`12a`/`12b`, macro-only and granularity) read no bank data and are not affected.

Anyone rebuilding the extract can keep the NACE 641 search: the filter in section 4b of
`01_micro_construction.ipynb` applies the corrections. Check the remaining entities by name.

---

## 2. Macro indicators — included

All four macro sources arrive in one workbook,
`data/macro/raw/macro_data_1995_2017_combined.xlsx`, one sheet per source.

| Sheet | Source | Indicators |
|---|---|---|
| `WDI_NFA_annual_1995_2017` | World Bank WDI | Net foreign assets (`FM.AST.NFRG.CN`) |
| `WDI_DCTPS_annual_1995_2017` | World Bank WDI | Domestic credit to private sector, % GDP (`FS.AST.PRVT.GD.ZS`) |
| `IMF_WEO_macro_annual_1995-2017` | IMF World Economic Outlook | Real GDP growth, nominal GDP, inflation, unemployment, current account |
| `IMF_IL_FX_1995_2017 ` | IMF International Liquidity | FX reserves excluding gold (`RXF11FX_REVS`) |
| `BIS_REER_monthly_timeseries ` | BIS | Real effective exchange rate, monthly |

The trailing spaces on the last two sheet names are real and are part of the sheet names in the
workbook. `02_macro_construction.ipynb` depends on them.

BIS supplies REER monthly and it is averaged to annual. BIS uses ISO2 country codes while every
other source uses ISO3, so the notebook maps them explicitly.

### The credit gap

The credit-to-GDP gap is computed with a **one-sided (real-time, recursive)** HP filter, lambda
100, minimum six observations. For each end year the filter is re-run on the history up to that
year only and the last trend point is kept, so no observation uses information from its own
future. This follows Drehmann and Juselius (2014) and the Basel III countercyclical buffer gap.

A two-sided filter also appears in the same notebook. It exists **only** to build the two lambda
comparison files (100 against 1562) and its output is never used as a predictor. The two functions
are named and documented distinctly for that reason.

Endpoint bias in the last estimate is inherent to the HP filter and is acknowledged in the thesis
Limitations rather than corrected.

---

## 3. Crisis database — included

`data/crisis/raw/SYST_BANK_CRIS_updated.xlsx`, from Laeven and Valencia (2026), *Systemic Banking
Crises Database: 1970-2025*, IMF Working Paper WP/26/94.

The *Crisis Resolution and Outcomes* sheet is used, because it carries both start **and** end years.
The *Crisis Years* sheet has start years only.

Labelling is by **duration**, not onset: `crisis = 1` for every year from onset through the end year
of the episode. An earlier onset-only version placed all positives in 2008, which left every test
year with zero positives and made evaluation impossible.

A five-year truncation rule is applied by the authors where a late-stage crisis could not be
distinguished from a weak economy, so GFC-era episodes end between 2009 and 2012 depending on
onset year. Episodes beginning before 1995 are expanded in full and the pre-1995 years are dropped
by the join onto the 1995-2017 skeleton.

The resulting panel is 575 country-years, of which 85 are crisis years.

---

## Data availability statement

> Macroeconomic data from the IMF World Economic Outlook, IMF International Financial Statistics,
> the World Bank World Development Indicators and the Bank for International Settlements, together
> with the Laeven and Valencia (2026) systemic banking crises database, are included in the
> replication repository. Bank-level data were obtained from ORBIS / Bankscope (Bureau van Dijk)
> under an institutional licence held by the University of Twente and cannot be redistributed.
> The extraction specification needed to reproduce the bank panel from ORBIS is documented in
> `DATA.md`. All analysis code is provided in full.
