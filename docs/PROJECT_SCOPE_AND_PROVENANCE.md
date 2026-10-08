# Project scope and provenance (A / B / C)
## A. What WE did
- Built this decision-support software and the traceable data pipeline; transcribed the literature tables from our screenshots.
- Built the physical prototype (PVC contact column, pump, ESP-class board, ozonizer ~15 W + air pump 3-5 W per the poster).
- A 2-sample "Proof of Concept" shown on the poster (spectrophotometer scan, pH, TDS). The samples are unlabeled and TDS did not decrease (765 -> 784): unverified context, not training data, not evidence of removal.
- Own logged experiments: **0** so far (a count, not a result).
## B. Found in literature / external sources (NOT performed by us)
- 61 pulp-bleaching kinetic experiments (inside 127 harmonised rows; 189 rows transcribed from 6 papers + 1 patent).
- ACS Engineering Au 2026 Table S1: 1,033 daily records, 2020-01-01 to 2022-10-29, European paper-mill wastewater plant. Benchmark only; shows signs of being algorithmically generated.
- OSHA ozone exposure limit (config/settings.json, to be verified for Egypt).
## C. Considered earlier, NOT used in the final system
- Detecting dripping water by whether a paper strip bleaches. Tried on one type of water (**NEEDS INPUT: which**). Replaced, after discussion with the instructor, by an indicator showing whether the paper changed (**NEEDS INPUT: which indicator**).
- Pulp bleaching as the project's own use-case: set aside. The final use-case is laboratory wastewater; the pulp module stays only as a labelled literature-background module.
## Team-stated reference conditions (handwritten notes)
Oxygen flow 90-120 L/hour (controlled) - ozone <= 400 mg/hour (controlled; unit NEEDS VERIFICATION) - 25 C (natural) - pH 6.3 (natural; NEEDS CLARIFICATION which sample).
## Safety logic
The AI works inside fixed, human-set safety rules. A violated rule takes priority: the recipe is BLOCKED and the run must not start. The AI cannot change or bypass the rules. During a run the operator stops the ozone generator and cuts power with the emergency stop; the dashboard is not connected to the hardware and cannot do it.
## Still NEEDS SOURCE VERIFICATION
1. Unit of the ozone specification (<= 400 mg/h?). 2. Which sample pH 6.3 belongs to. 3. The default of 12 own runs (developer-chosen, no source). 4. The indicator and the water type of the abandoned paper-drip idea. 5. The legal source of the poster's discharge criteria. 6. Bibliographic details (authors/year/DOI) of the literature sources marked UNVERIFIED in source_index.csv.
