# Dataset documentation
## Sources and rows (hand-transcribed from the team's screenshot PDF; counts verified in code)
| Source | Rows | Tables | Variables |
|---|---|---|---|
| P1 Optical (pH & temperature, O-delignified hardwood kraft) | 62 | Tab. 1-2 (40 C, 20 C) | pH, T, ozone consumed, time, L*, a*, b* |
| P2 DP (cellulose chain scission) | 62 | matching tables | pH, T, ozone consumed, time, DP |
| P3 Eucalyptus kraft kinetics (BioResources) | 15 | numeric tables | ozone, kappa, brightness, viscosity |
| P4 Low-consistency kinetics (BioResources) | 0 | tables are images | only text values -> flagged, not entered as rows |
| P5 Ozone organosolv, radiata pine | 29 | Tables 1-4 | ozone consumed, medium, kappa, viscosity, brightness |
| P6 Cellulose protectors | 10 | Table 1 | additive, kappa, viscosity, brightness |
| PAT1 US20030006017A1 (US6579412B2 shows the same tables - not double counted) | 11 | Tables 1-4 | consistency, pressure, ozone, kappa, brightness, viscosity |
| PAT3 WO2005059241A1 | 0 | none in screenshots | - |
Total 189 observation rows. P1+P2 are joined on the shared experiment number (ozone and time verified equal) giving 62 kinetics rows (1 baseline) -> **61 rows train the model**.

## Rules applied
Never invented; never estimated from graphs; units preserved next to converted values (kg/t -> %: x0.1; s -> min: /60); ISO and Elrepho brightness kept in separate columns (not interchangeable); L* is CIELAB lightness, not brightness; rows from different papers are **not** assumed comparable; 70 calculated values (`derived_calculated_not_observations.csv`) are never used as measurements. Bibliographic details (authors, year, DOI) that were not visible in the screenshots are marked UNVERIFIED in `source_index.csv` - fill them in before publication.

## Targets are kept separate
Kinetics model: L*, a*, b*, DP (one model each). Kappa/brightness/viscosity data from other papers sit in separate task groups and are **not** merged into those targets.

## Measured vs calculated
Measured (as reported): 180 rows. 9 rows carry both measured values and one calculated column (theoretical reactivity), labelled in `Value_Type`.

## Limitations
2 temperatures, 5 pH levels, one pulp family for the model; different reactors/pulps across papers; the previously "existing dataset" is the as-printed transcription in sheet `Existing_Dataset` (kept untouched); the ACS file is not ozone data and shows signs of algorithmic generation.

## ACS (A, external)
1,033 daily rows, no missing values. Chronological 70/15/15 split; model selected on validation only. Integrity probe: linear R2 = 1.000000 -> benchmark only.

## Meaning of the key numbers (checked against the files)
- **189** raw transcribed literature rows -> **127** harmonised rows (`combined_clean_dataset.csv`; 189 - 62 = 127 because the optical paper and the DP paper report the same 62 experiments in two tables, which are merged) -> **61** kinetic rows train the model (62 merged kinetic rows minus 1 untreated baseline row).
- **1,033** = rows of ACS Table S1 `Input_Data`: one record per day, 2020-01-01 to 2022-10-29 (1,033 consecutive days). Historical data of a European paper-mill wastewater plant. Not ours. Not ozone.
- **0** = our own logged experiments (a count, not a result).
- **12** = software threshold, see `config/settings.json`; NOT a count of experiments and NOT from a paper.
