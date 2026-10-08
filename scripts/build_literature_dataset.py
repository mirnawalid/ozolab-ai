"""
Builds the OzoLab AI ozone-bleaching literature dataset.

SOURCE OF EVERY NUMBER: tables printed in the team's screenshot PDF
("ozone_bleaching_dataset_from_the_papers ... (screenshots).pdf"), transcribed by hand.
NOTHING is estimated from graphs, interpolated, or invented.

Run:  python scripts/build_literature_dataset.py
Out:  Project_Archive/OzoLab_Ozone_Bleaching_Dataset.xlsx
      data/literature/*.csv
"""
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
ARCHIVE = ROOT / "Project_Archive"
LIT = ROOT / "data" / "literature"
ARCHIVE.mkdir(exist_ok=True); LIT.mkdir(parents=True, exist_ok=True)

COLS = ["Dataset_Source", "Paper_ID", "DOI_or_Patent", "Experiment_ID", "Table_ID", "Pulp_Type", "Wood_Type",
        "Pulp_Consistency_percent", "Initial_Kappa", "Initial_Brightness", "Initial_Viscosity", "Temperature_C", "pH",
        "Ozone_Dose", "Ozone_Dose_Unit", "Ozone_Concentration", "Ozone_Concentration_Unit", "Ozone_Consumed",
        "Ozone_Consumed_Unit", "Reaction_Time", "Reaction_Time_Unit", "Gas_Flow", "Gas_Flow_Unit", "Pressure",
        "Pressure_Unit", "Pretreatment", "Additive", "Additive_Concentration", "Medium", "Final_Kappa",
        "Final_Brightness", "Brightness_Scale", "Final_Viscosity", "Final_Viscosity_Unit", "Selectivity",
        "Delignification", "DP", "L_star", "a_star", "b_star", "Other_Measured_Output", "Original_Unit",
        "Value_Type", "Is_Baseline", "Notes"]

SOURCES = {
 "P1_OPTICAL": dict(title="Effect of pH and temperature on the optical properties in ozonization oxygen delignified hardwood kraft pulp",
    authors="UNVERIFIED (not in screenshots)", year="UNVERIFIED",
    doi="No DOI verified", url="https://www.researchgate.net/publication/235227836_Effect_of_pH_and_temperature_on_the_optical_properties_in_ozonization_oxygen_delignified_hardwood_kraft_pulp",
    tables="Tab.1 (40 C), Tab.2 (20 C) [L*, a*, b*]; Tab.3 (fit parameters - calculated)"),
 "P2_DP": dict(title="Effect of pH and temperature on cellulose chain scission number in ozonization of oxygen delignified hardwood kraft pulp",
    authors="UNVERIFIED (not in screenshots)", year="UNVERIFIED", doi="No DOI verified",
    url="https://www.researchgate.net/publication/227335376_Effect_of_PH_and_temperature_on_cellulose_chain_scission_number_in_ozonization_of_oxygen_delignified_hardwood_kraft_pulp",
    tables="Tab.1 (40 C), Tab.2 (20 C) [intrinsic viscosity, DP]"),
 "P3_EKP": dict(title="Kinetics of Ozone Bleaching of Eucalyptus Kraft Pulp and Factors Affecting the Properties of the Bleached Pulp",
    authors="UNVERIFIED (not in screenshots)", year="UNVERIFIED (BioResources)", doi="No DOI verified",
    url="https://bioresources.cnr.ncsu.edu/resources/kinetics-of-ozone-bleaching-of-eucalyptus-kraft-pulp-and-factors-affecting-the-properties-of-the-bleached-pulp/",
    tables="Table 1 (consistency effect), Table 2 (additives / mass transfer)"),
 "P4_LCKIN": dict(title="Kinetics of delignification and carbohydrate degradation during the ozone bleaching of low-consistency hardwood pulps",
    authors="UNVERIFIED (not in screenshots)", year="UNVERIFIED (BioResources)", doi="No DOI verified",
    url="https://bioresources.cnr.ncsu.edu/resources/kinetics-of-delignification-and-carbohydrate-degradation-during-the-ozone-bleaching-of-low-consistency-hardwood-pulps/",
    tables="Table 1 (ln k, CALCULATED), Table 2 and 3 (regression fits, CALCULATED) - no raw observations in screenshots"),
 "P5_ORGANOSOLV": dict(title="Ozone organosolv bleaching of radiata pine kraft pulp",
    authors="UNVERIFIED (not in screenshots)", year="UNVERIFIED", doi="No DOI verified",
    url="https://www.researchgate.net/publication/226189721_Ozone_organosolv_bleaching_of_radiata_pine_kraft_pulp",
    tables="Tables 1-4"),
 "P6_PROTECTORS": dict(title="Influence of new cellulose protectors in ozone bleaching",
    authors="UNVERIFIED (not in screenshots)", year="UNVERIFIED", doi="No DOI verified",
    url="https://www.researchgate.net/publication/227338883_Influence_of_new_cellulose_protectors_in_ozone_bleaching",
    tables="Table 1 (additives)"),
 "PAT1_US20030006017A1": dict(title="Ozone bleaching of low consistency pulp (patent)", authors="See patent", year="2003 (publication)",
    doi="US20030006017A1", url="https://patents.google.com/patent/US20030006017A1/en",
    tables="Table 1, Table 2, Table 3+4, mixer-energy table and O3 solubility table (reference)"),
 "PAT2_US6579412B2": dict(title="Process for ozone bleaching of low consistency pulp (patent)", authors="See patent", year="UNVERIFIED",
    doi="US6579412B2", url="https://patents.google.com/patent/US6579412B2/en",
    tables="Screenshots show the same tables as PAT1 (patent family) -> NOT counted twice"),
 "PAT3_WO2005059241A1": dict(title="Method for the acidification of pulp prior to ozone bleaching (patent)", authors="See patent", year="UNVERIFIED",
    doi="WO2005059241A1", url="https://patents.google.com/patent/WO2005059241A1/en",
    tables="No table was included in the team's screenshot PDF -> 0 rows extracted"),
}

def ref(pid): return SOURCES[pid]["doi"] if SOURCES[pid]["doi"].startswith(("US", "WO")) else "see URL: " + SOURCES[pid]["url"]

rows = []
def add(pid, **kw):
    r = {c: None for c in COLS}
    r.update(Dataset_Source="Literature (external, real, screenshot-transcribed)", Paper_ID=pid, DOI_or_Patent=ref(pid),
             Value_Type="measured (as reported)", Is_Baseline=False)
    r.update(kw); rows.append(r)

# ------------------------------------------------------------------ P1 + P2 -----------------
# exp, pH, O3(% on o.d. pulp), t(s), L*, a*, b*      (Tab.1, 40 C)
T40 = """1 .26 .10 72 86.02 2.70 14.50|2 .26 .20 216 86.61 2.47 13.67|3 .26 .31 288 87.36 2.40 13.50|4 .26 .41 432 87.32 2.47 13.33|5 .26 .51 576 88.15 2.20 12.73|6 .26 .62 720 88.19 2.23 12.73
7 2.61 .05 72 86.06 2.57 13.87|8 2.61 .28 144 86.39 2.37 13.13|9 2.61 .37 216 86.70 2.50 13.63|10 2.61 .44 287 87.06 2.40 13.47|11 2.61 .76 431 87.79 2.27 12.83|12 2.61 .95 575 87.85 2.27 12.63|13 2.61 .90 719 88.65 2.10 12.43
14 3.86 .14 76 84.32 2.63 14.10|15 3.86 .26 152 85.32 2.57 13.77|16 3.86 .41 228 85.56 2.53 13.70|17 3.86 .51 304 86.51 2.43 13.33|18 3.86 .68 456 86.59 2.40 13.33|19 3.86 .80 607 86.80 2.30 13.03|20 3.86 .85 759 87.12 2.30 12.93
21 8.83 .15 74 84.23 2.40 14.53|22 8.83 .35 148 84.95 2.40 13.83|23 8.83 .36 222 84.69 2.43 13.97|24 8.83 .60 247 85.13 2.27 13.57|25 8.83 .88 445 85.57 2.20 13.30|26 8.83 1.14 593 86.45 2.17 13.10|27 8.83 1.45 742 85.60 2.30 13.33
28 9.6 .07 60 84.33 2.60 14.33|29 9.6 .11 30 84.52 2.47 14.17|30 9.6 .20 90 85.03 2.40 13.97|31 9.6 .21 120 84.94 2.43 13.77|32 9.6 .29 150 85.29 2.37 13.50|33 9.6 .32 180 85.70 2.23 13.27"""
T20 = """34 .26 .06 67 86.11 2.50 14.00|35 .26 .15 133 86.61 2.57 14.17|36 .26 .20 200 87.13 2.40 13.87|37 .26 .22 266 87.50 2.30 13.40|38 .26 .32 399 87.84 2.27 13.00|39 .26 .39 532 88.21 2.13 12.77|40 .26 .54 665 87.92 2.23 12.87
41 2.61 .19 37 84.51 2.60 14.30|42 2.61 .24 134 86.29 2.50 13.67|43 2.61 .32 201 86.62 2.50 13.70|44 2.61 .43 263 85.26 2.30 13.90|45 2.61 .56 394 86.77 2.43 13.53|46 2.61 .67 525 87.06 2.37 13.77|47 2.61 .82 657 86.76 2.13 13.07
48 3.86 .12 70 85.47 2.60 14.30|49 3.86 .29 140 85.82 2.60 13.97|50 3.86 .38 209 85.75 2.63 14.23|51 3.86 .47 279 86.03 2.53 13.73|52 3.86 .62 419 86.52 2.50 13.87|53 3.86 .81 559 86.65 2.47 13.77|54 3.86 .87 698 87.03 2.37 13.27
55 8.83 .04 67 83.92 2.53 14.33|56 8.83 .28 133 84.19 2.53 14.27|57 8.83 .39 200 84.43 2.47 14.13|58 8.83 .46 266 84.64 2.43 14.03|59 8.83 .59 400 84.47 2.57 14.23|60 8.83 .71 533 85.24 2.37 13.83|61 8.83 1.09 667 85.90 2.30 13.40"""
# P2: exp, O3, t, [eta] ml/g, DP  (pH labels are rounded differently in P2: 0.3/2.6/3.9/8.8/9.6)
D40 = """1 .10 72 720 1046|2 .20 216 702 1017|3 .31 288 679 980|4 .41 432 677 977|5 .51 576 672 968|6 .62 720 667 961
7 .05 72 763 1115|8 .28 144 723 1050|9 .37 216 706 1023|10 .44 287 691 999|11 .76 431 705 1021|12 .95 575 660 949|13 .90 719 630 902
14 .14 76 783 1146|15 .26 152 757 1104|16 .41 228 754 1100|17 .51 304 746 1087|18 .68 456 729 1060|19 .80 607 710 1029|20 .85 759 698 1010
21 .15 74 752 1096|22 .35 148 723 1050|23 .36 222 703 1019|24 .60 247 693 1003|25 .88 445 702 1017|26 1.14 593 668 962|27 1.45 742 615 878
28 .07 60 781 1144|29 .11 30 763 1115|30 .20 90 727 1057|31 .21 120 718 1043|32 .29 150 702 1016|33 .32 180 712 1032"""
D20 = """34 .06 67 753 1098|35 .15 133 739 1076|36 .20 200 730 1061|37 .22 266 697 1009|38 .32 399 696 1006|39 .39 532 697 1009|40 .54 665 682 984
41 .19 37 750 1093|42 .24 134 709 1028|43 .32 201 709 1027|44 .43 263 706 1023|45 .56 394 687 992|46 .67 525 648 931|47 .82 657 652 937
48 .12 70 771 1128|49 .29 140 751 1095|50 .38 209 752 1097|51 .47 279 729 1060|52 .62 419 705 1020|53 .81 559 689 996|54 .87 698 658 947
55 .04 67 708 1027|56 .28 133 728 1058|57 .39 200 703 1018|58 .46 266 691 999|59 .59 400 681 983|60 .71 533 663 954|61 1.09 667 644 924"""

def parse(block, ncols):
    out = []
    for chunk in block.replace("\n", "|").split("|"):
        p = chunk.split()
        if p: out.append([float(x) for x in p]); assert len(p) == ncols, chunk
    return out

P1 = {40: parse(T40, 7), 20: parse(T20, 7)}
P2 = {40: parse(D40, 5), 20: parse(D20, 5)}
PULP1 = "Oxygen-delignified hardwood kraft pulp"
add("P1_OPTICAL", Experiment_ID="P1_Exp0", Table_ID="Tab.1/Tab.2 (Exp 0 baseline)", Pulp_Type=PULP1, Wood_Type="hardwood",
    Ozone_Consumed=0.0, Ozone_Consumed_Unit="% O3 on o.d. pulp", Reaction_Time=0, Reaction_Time_Unit="s",
    L_star=83.04, a_star=2.67, b_star=15.13, Is_Baseline=True, Original_Unit="L*,a*,b* CIELAB",
    Notes="Untreated reference; printed once per pH block in the source, stored once here (genuine duplicate removed). Temperature/pH not applicable.")
add("P2_DP", Experiment_ID="P2_Exp0", Table_ID="Tab.1/Tab.2 (Exp 0 baseline)", Pulp_Type=PULP1, Wood_Type="hardwood",
    Ozone_Consumed=0.0, Ozone_Consumed_Unit="% O3 on o.d. pulp", Reaction_Time=0, Reaction_Time_Unit="s",
    Final_Viscosity=817, Final_Viscosity_Unit="ml/g (intrinsic viscosity)", DP=1201, Is_Baseline=True,
    Original_Unit="[eta] ml/g; DP dimensionless", Notes="Untreated reference (stored once).")
for T in (40, 20):
    for (e, pH, o3, t, L, a, b) in P1[T]:
        add("P1_OPTICAL", Experiment_ID=f"P1_Exp{int(e)}", Table_ID=f"Tab.{1 if T==40 else 2}", Pulp_Type=PULP1, Wood_Type="hardwood",
            Temperature_C=T, pH=pH, Ozone_Consumed=o3, Ozone_Consumed_Unit="% O3 on o.d. pulp", Reaction_Time=t,
            Reaction_Time_Unit="s", L_star=L, a_star=a, b_star=b, Original_Unit="O3 % o.d. pulp; t s; CIELAB",
            Notes="Brightness NOT reported per experiment - only CIELAB L*a*b*.")
    for (e, o3, t, eta, dp) in P2[T]:
        add("P2_DP", Experiment_ID=f"P2_Exp{int(e)}", Table_ID=f"Tab.{1 if T==40 else 2}", Pulp_Type=PULP1, Wood_Type="hardwood",
            Temperature_C=T, Ozone_Consumed=o3, Ozone_Consumed_Unit="% O3 on o.d. pulp", Reaction_Time=t, Reaction_Time_Unit="s",
            Final_Viscosity=eta, Final_Viscosity_Unit="ml/g (intrinsic viscosity)", DP=dp, Original_Unit="[eta] ml/g",
            Notes="pH not repeated in this table's rows in our transcription; pH taken from companion P1 row with the same Exp number (verified same O3 and t). Source prints pH as 0.3/2.6/3.9/8.8/9.6.")

# fill pH for P2 rows via verified join on Exp number
p1_by_exp = {int(r[0]): r for T in P1 for r in P1[T]}
for r in rows:
    if r["Paper_ID"] == "P2_DP" and not r["Is_Baseline"]:
        e = int(r["Experiment_ID"].split("Exp")[1]); q = p1_by_exp[e]
        assert abs(q[2] - r["Ozone_Consumed"]) < 1e-9 and q[3] == r["Reaction_Time"], f"P1/P2 mismatch exp {e}"
        r["pH"] = q[1]

# ------------------------------------------------------------------ P3 -----------------------
P3_T1 = [(3,1.2,2,30,None,65.2,580,8.8),(3,1.2,2,30,0.05,68,579,7.9),(15,1.2,2,15,None,65.1,515,9.5),
         (15,1.2,2,15,0.05,69.4,513,8.3),(35,1.2,2,3,None,66.4,510,9.1),(35,1.2,2,3,0.05,70.2,511,8.1)]
for i, (cons, dose, pH, tm, add_, br, vis, kap) in enumerate(P3_T1, 1):
    add("P3_EKP", Experiment_ID=f"P3_T1_r{i}", Table_ID="Table 1", Pulp_Type="Eucalyptus kraft pulp (EKP)", Wood_Type="eucalyptus (hardwood)",
        Pulp_Consistency_percent=cons, pH=pH, Ozone_Dose=dose, Ozone_Dose_Unit="% o.d.p", Reaction_Time=tm, Reaction_Time_Unit="min",
        Additive="NP-10" if add_ else "none", Additive_Concentration=add_, Final_Brightness=br, Brightness_Scale="%ISO",
        Final_Viscosity=vis, Final_Viscosity_Unit="as printed '(%ISO)' - unit label looks like a typo in source; UNVERIFIED",
        Final_Kappa=kap, Original_Unit="Viscosity printed as (%ISO)", Notes="Temperature not stated in table.")
P3_T2 = [("No additive",.038,18.1,.1310,45.1,45.1,6.6),("Tert-Butyl alcohol",.064,23.6,.1251,81.6,83.4,8.3),
         ("1-Butyl alcohol",.060,20.5,.1206,79.5,82.9,8.5),("Dimethylformamide",.040,18.2,.1504,50.8,5.9,7.0),
         ("Dimethyl sulphoxide",.035,17.2,.1467,65.7,58.3,7.1),("Ethyl acetate",.056,20.6,.1298,78.1,75.6,7.9),
         ("Acetic acid",.050,20.1,.1366,46.5,62.3,7.1),("Oxalic acid",.033,17.1,.1328,41.5,40.3,6.5),("NP-10",.098,16.4,.1653,88.9,80.5,9.1)]
for i, (ad, kla, cl, sg, er, tr, ef) in enumerate(P3_T2, 1):
    add("P3_EKP", Experiment_ID=f"P3_T2_r{i}", Table_ID="Table 2", Pulp_Type="(mass-transfer test, no pulp outcome)",
        Additive=ad, Value_Type="measured (KLa, C*L, sigma, exp. reactivity) + CALCULATED (theoretical reactivity)",
        Other_Measured_Output=f"KLa={kla} s-1; C*L={cl} mg/L; sigma={sg} N/m; exp_reactivity={er}; theoretical_reactivity={tr} (calculated); efficiency={ef}",
        Original_Unit="KLa s-1; C*L mg/L; sigma N/m", Notes="Gas-liquid ozone mass-transfer study; NOT a pulp-quality outcome. " + ("Theoretical reactivity printed as 5.9 - likely typo (neighbours ~50-80); kept as printed, UNVERIFIED." if ad=="Dimethylformamide" else ""))

# ------------------------------------------------------------------ P5 -----------------------
P5 = dict(Pulp_Type="Kraft-oxygen pulp, extended cook", Wood_Type="Pinus radiata (softwood)", Initial_Kappa=16.0, Initial_Viscosity=27.0, Initial_Brightness=37.2)
add("P5_ORGANOSOLV", Experiment_ID="P5_T1_reference", Table_ID="Table 1 / 2 (Reference)", Final_Kappa=16.0, Final_Viscosity=27.0,
    Final_Viscosity_Unit="mPa.s", Final_Brightness=37.2, Brightness_Scale="Elrepho", Is_Baseline=True,
    Notes="Untreated reference pulp.", **{k: v for k, v in P5.items() if k in ("Pulp_Type", "Wood_Type")})
T1 = [("Acetic acid 96%",6.9,18.9,1.90,58.6),("Acetic acid 90%",5.4,18.1,2.00,60.5),("Acetic acid 80%",4.9,18.3,2.15,63.8),
      ("Acetic acid 70%",4.9,18.0,2.08,64.0),("Acetic acid 48%",5.7,18.0,1.93,59.4),("Formic acid 98%",4.1,18.1,2.25,64.7),
      ("Formic acid-water 1:1 (V/V)",5.9,18.5,2.00,59.3),("Formic acid-acetone 7:3 (V/V)",5.6,18.8,2.14,61.3),
      ("Formic acid-acetone 1:1 (V/V)",5.1,17.9,2.02,62.3),("Formic acid-acetone 3:7 (V/V)",5.7,18.8,2.12,61.5),
      ("Acetic acid-acetone 7:3 (V/V)",6.8,19.1,1.96,59.7),("Acetic acid-acetone 1:1 (V/V)",7.8,20.5,2.13,57.2),
      ("Acetic acid-acetone 3:7 (V/V)",7.2,15.3,1.27,57.5),("Acetone",11.7,16.6,0.70,47.4),("Water, pH 2.5",6.7,16.7,1.52,57.9)]
for i, (pre, k, v, s, b) in enumerate(T1, 1):
    add("P5_ORGANOSOLV", Experiment_ID=f"P5_T1_r{i}", Table_ID="Table 1", Pretreatment=pre, Medium=pre,
        Ozone_Consumed=1.1, Ozone_Consumed_Unit="% b.d. pulp", pH=2.5 if pre.startswith("Water") else None,
        Final_Kappa=k, Final_Viscosity=v, Final_Viscosity_Unit="mPa.s", Selectivity=s, Final_Brightness=b, Brightness_Scale="Elrepho",
        Original_Unit="ozone consumed %/b.d. pulp; viscosity mPa.s", **P5,
        Notes="Formic acid 98% row (kappa 4.1, visc 18.1, bright 64.7) differs slightly from Table 2 row at 1.1% (4.2, 17.6, 62.6): both kept as printed." if pre=="Formic acid 98%" else "")
T2 = [(0.9,6.6,18.1,1.78,50.8,10.5),(1.1,4.2,17.6,2.12,62.6,10.7),(1.4,3.5,16.0,1.92,67.5,8.9),(1.7,3.1,15.7,1.93,70.3,7.6)]
for i, (oc, k, v, s, b, ef) in enumerate(T2, 1):
    add("P5_ORGANOSOLV", Experiment_ID=f"P5_T2_r{i}", Table_ID="Table 2", Pretreatment="Formic acid 98%", Medium="Formic acid 98%",
        Ozone_Consumed=oc, Ozone_Consumed_Unit="% (basis as printed, b.d. pulp)", Final_Kappa=k, Final_Viscosity=v, Final_Viscosity_Unit="mPa.s",
        Selectivity=s, Final_Brightness=b, Brightness_Scale="Elrepho", Other_Measured_Output=f"Efficiency={ef}", Original_Unit="mPa.s; Elrepho", **P5)
T3 = [(1.1,1.7,15.1,76.3),(1.4,1.1,14.7,80.7),(1.7,0.9,13.9,83.1)]
for i, (oc, k, v, b) in enumerate(T3, 1):
    add("P5_ORGANOSOLV", Experiment_ID=f"P5_T3_P{i}", Table_ID="Table 3 (P stage)", Pretreatment="Formic acid 98%", Medium="Z then P (1% H2O2)",
        Ozone_Consumed=oc, Ozone_Consumed_Unit="% (Z-stage, as printed)", Final_Kappa=k, Final_Viscosity=v, Final_Viscosity_Unit="mPa.s",
        Final_Brightness=b, Brightness_Scale="Elrepho", Other_Measured_Output="After P stage (1% hydrogen peroxide)", **P5,
        Notes="Z-stage rows of Table 3 are identical to Table 2 rows 1.1/1.4/1.7 -> genuine duplicates removed.")
T4 = [("Formic medium","Z",6.6,18.1,1.78,57.6),("Formic medium","P",2.2,16.1,None,72.0),
      ("pH 2.5 water-medium, formic-wet pulp","Z",7.5,13.0,1.02,57.5),("pH 2.5 water-medium, formic-wet pulp","P",2.8,11.8,None,72.2),
      ("pH 2.5 water-medium","Z",9.9,14.1,0.80,50.8),("pH 2.5 water-medium","P",4.2,12.5,None,67.6)]
for i, (med, st, k, v, s, b) in enumerate(T4, 1):
    add("P5_ORGANOSOLV", Experiment_ID=f"P5_T4_r{i}", Table_ID="Table 4", Pretreatment=med, Medium=med, Ozone_Consumed=0.9,
        Ozone_Consumed_Unit="% ozone (Z), as printed", pH=2.5 if "pH 2.5" in med else None, Final_Kappa=k, Final_Viscosity=v,
        Final_Viscosity_Unit="mPa.s", Selectivity=s, Final_Brightness=b, Brightness_Scale="Elrepho",
        Other_Measured_Output=f"Stage={st}", **P5,
        Notes="Formic-medium Z brightness printed 57.6 here vs 50.8 in Table 2 at 0.9% - inconsistency in source, kept as printed." if (med=="Formic medium" and st=="Z") else "")

# ------------------------------------------------------------------ P6 -----------------------
P6 = [("Without additive",.1852,6.39,763,47.92),("Methylhydroxyethyl cellulose",.2393,7.34,647,54.36),("Zirconium(IV) propoxide",.1535,8.41,723,49.43),
      ("2-tert-butyl-5-aminopyrimidine",.1964,10.17,808,50.25),("Ammonium molybdate",.1311,6.99,745,54.21),("Urea",.1330,6.36,745,53.58),
      ("Salicylic acid",.1664,6.45,728,56.14),("Cationic potato starch",.1397,6.93,740,51.13),("D-mannitol",.1444,6.03,814,50.17),("Magnesium ethoxide",.1432,5.90,693,54.25)]
for i, (ad, oc, k, v, b) in enumerate(P6, 1):
    add("P6_PROTECTORS", Experiment_ID=f"P6_T1_r{i}", Table_ID="Table 1", Pulp_Type="UNKNOWN (not visible in screenshot)",
        Ozone_Dose=0.3, Ozone_Dose_Unit="% ozone on o.d. pulp (ozone charge)", Ozone_Consumed=oc, Ozone_Consumed_Unit="% o.d. pulp",
        Additive=ad if i > 1 else "none", Additive_Concentration=1.0 if i > 1 else None, Final_Kappa=k, Final_Viscosity=v, Final_Viscosity_Unit="ml/g",
        Final_Brightness=b, Brightness_Scale="%ISO", Original_Unit="additive 1% o.d. pulp")

# ------------------------------------------------------------------ PATENT ------------------
PT = "PAT1_US20030006017A1"
for i, (ch, co, rx, ps) in enumerate([(2.4,2.2,93.0,46),(4.0,3.9,95.0,55),(6.1,5.8,95.1,52),(7.3,7.0,95.9,65)], 1):
    add(PT, Experiment_ID=f"PAT1_T1_r{i}", Table_ID="Table 1", Pulp_Type="Low-consistency pulp (details not in table image)",
        Ozone_Dose=ch, Ozone_Dose_Unit="kg O3 / t pulp (charge)", Ozone_Consumed=co, Ozone_Consumed_Unit="kg/t", Reaction_Time=5,
        Reaction_Time_Unit="min (retention)", Pressure=ps, Pressure_Unit="psig", Other_Measured_Output=f"O3 reacted={rx}%", Original_Unit="kg/t; psig; min",
        Notes="No kappa/brightness outcomes in this table.")
for i, (pi, pb, cm, ct) in enumerate([(30,20,87,99),(90,80,94,99),(110,100,99,99)], 1):
    add(PT, Experiment_ID=f"PAT1_T2_r{i}", Table_ID="Table 2", Ozone_Dose=6.3, Ozone_Dose_Unit="kg O3 / t pulp (charge; printed '6-3' in 2 rows = typo for 6.3)",
        Pressure=pi, Pressure_Unit="psig (inlet mixer)", Other_Measured_Output=f"Bottom tower pressure={pb} psig; O3 consumed in mixer={cm}%; consumed at top of tower={ct}%",
        Original_Unit="kg/t; psig; %")
for run, (chg, conc, pr) in {1: (0.551, 12.85, 30), 2: (0.566, 13.21, 90)}.items():
    res = {1: {"Bottom": (0.072, 0.479, None, None, None), "Top": (0.001, 0.550, None, None, None)},
           2: {"Bottom": (0.037, 0.530, 27.0, 31.4, 25.3), "Top": (0.001, 0.565, 24.1, 32.2, 23.3)}}[run]
    for pos, (resid, cons, kap, bri, vis) in res.items():
        add(PT, Experiment_ID=f"PAT1_T34_run{run}_{pos}", Table_ID="Table 3+4", Pulp_Type="Pulp (type not stated in table image)",
            Pulp_Consistency_percent=3.8, Initial_Kappa=30.8, Initial_Brightness=27.9, Initial_Viscosity=39.5, Temperature_C=40, pH=2.4,
            Ozone_Dose=chg, Ozone_Dose_Unit="% o.d. pulp (charge)", Ozone_Concentration=conc, Ozone_Concentration_Unit="% (gas)",
            Ozone_Consumed=cons, Ozone_Consumed_Unit="% o.d. pulp", Reaction_Time=6.4, Reaction_Time_Unit="min (residence)", Pressure=pr,
            Pressure_Unit="not stated in table (psig likely)", Final_Kappa=kap, Final_Brightness=bri, Brightness_Scale="%ISO", Final_Viscosity=vis,
            Final_Viscosity_Unit="cP", Other_Measured_Output=f"Sample position={pos} of tower; ozone residual={resid}% o.d. pulp",
            Original_Unit="% o.d. pulp; cP",
            Notes="Kappa/brightness/viscosity were printed only under the second run in the source." if run == 1 else "")

lit = pd.DataFrame(rows, columns=COLS)
assert lit.duplicated(subset=[c for c in COLS if c != "Notes"]).sum() == 0

# ------------------------------------------------------------------ DERIVED (calculated) ----
der = []
lnk = {25: [-10.027,-10.192,-10.167,-10.098,-10.010,-9.982,-10.111,-10.159], 30: [-10.220,-10.357,-10.459,-10.304,-10.31,-10.277,-10.416,-10.508],
       35: [-10.4,-10.583,-10.632,-10.646,-10.706,-10.723,-10.791,-10.864]}
for T, vals in lnk.items():
    for tm, v in zip(range(5, 45, 5), vals):
        der.append(dict(Paper_ID="P4_LCKIN", Table_ID="Table 1", Description="ln k (rate constant, CALCULATED)", Temperature_C=T, Time_min=tm, Value_Name="ln_k", Value=v))
for T, (a1, b1, r1, a2, b2, r2) in {25: (.031,5.076,.9833,.047,4.770,.9729), 30: (.046,5.078,.9926,.058,4.847,.9929), 35: (.072,5.08,.9955,.083,4.78,.9899)}.items():
    der.append(dict(Paper_ID="P4_LCKIN", Table_ID="Table 2", Description="Linear regression 0<t<=20 min (CALCULATED)", Temperature_C=T, Value_Name="slope|intercept|R2", Value=f"{a1}|{b1}|{r1}"))
    der.append(dict(Paper_ID="P4_LCKIN", Table_ID="Table 2", Description="Linear regression 20<t<=40 min (CALCULATED)", Temperature_C=T, Value_Name="slope|intercept|R2", Value=f"{a2}|{b2}|{r2}"))
for dose, pH, e1, e2 in [(0.4,2.0,(.026,5.094,.9958),(.049,4.654,.9879)),(0.8,2.0,(.048,5.137,.9927),(.072,4.633,.9983)),(1.0,2.0,(.066,5.134,.9972),(.087,4.66,.9959)),
                         (1.2,2.0,(.084,5.184,.9740),(.112,4.53,.9954)),(1.0,"2.0 (second block)",(.067,5.096,.9973),(.081,4.855,.9969)),
                         (1.0,2.5,(.081,5.111,.9980),(.096,4.798,.9954)),(1.0,3.0,(.105,5.100,.9979),(.123,4.771,.9976))]:
    for lab, e in (("0<=t<=20", e1), ("20<t<=40", e2)):
        der.append(dict(Paper_ID="P4_LCKIN", Table_ID="Table 3", Description=f"Regression {lab} min (CALCULATED)", Ozone_Dose_pct=dose, pH=pH, Value_Name="slope|intercept|R2", Value="|".join(map(str, e))))
FIT = {"Brightness (B, %ISO)": {20: {.26:(.9490,58.56,.79,-9.91,1.06,.12,.03), 2.61:(.9035,58.76,1.13,-8.84,1.40,.28,.10), 3.86:(.9212,55.32,.58,-6.90,.91,.19,.07), 8.83:(.8236,57.38,10.12,-8.33,9.87,1.43,2.40)},
                               40: {.26:(.9693,59.00,.89,-10.60,1.03,.19,.05), 2.61:(.8439,59.27,1.70,-9.22,1.95,.30,.18), 3.86:(.9865,57.63,.68,-9.55,.85,.37,.07), 9.6:(.9678,54.44,.85,-6.15,.82,.15,.05)}},
       "Total color difference (dE)": {20: {.26:(.9483,5.71,0,-5.39,.42,.16,.02), 2.61:(.8319,4.28,0,-4.31,.66,.23,.06), 3.86:(.8986,4.41,0,-3.99,.42,.31,.06), 8.83:(.8366,3.36,0,-2.94,.31,.62,.14)},
                               40: {.26:(.9716,5.69,0,-5.52,.35,.17,.02), 2.61:(.8342,6.25,0,-5.07,.65,.39,.10), 3.86:(.9781,4.64,0,-4.65,.23,.32,.03), 8.83:(.9277,4.0,0,-3.81,.31,.52,.08), 9.6:(.9670,3.28,0,-3.21,.20,.14,.02)}},
       "Yellowness (Ys, %)": {20: {.26:(.8995,26.21,0,5.74,.61,.18,.03), 2.61:(.8730,27.04,0,5.13,.58,.34,.06), 3.86:(.8600,27.87,0,4.04,.48,.34,.07), 8.83:(.7417,28.42,0,3.06,.43,.58,.17)},
                              40: {.26:(.9652,26.25,0,6.07,.40,.23,.03), 2.61:(.8473,25.35,0,5.77,.70,.41,.10), 3.86:(.9778,26.78,0,5.36,.26,.33,.03), 8.83:(.9719,27.44,0,4.77,.27,.38,.04), 9.6:(.9637,27.77,0,4.41,.29,.14,.02)}}}
for var, byT in FIT.items():
    for T, byP in byT.items():
        for pH, (r2, y0, y0e, a1, a1e, t1, t1e) in byP.items():
            der.append(dict(Paper_ID="P1_OPTICAL", Table_ID="Tab.3", Description=f"Exp. decay fit Y=Y0+A1*exp(-O3/T1) for {var} (CALCULATED FIT)", Temperature_C=T, pH=pH,
                            Value_Name="R2|Y0|Y0_err|A1|A1_err|T1|T1_err", Value=f"{r2}|{y0}|{y0e}|{a1}|{a1e}|{t1}|{t1e}"))
derived = pd.DataFrame(der); derived["Value_Type"] = "CALCULATED (model fit / derived by the paper's authors) - NOT an observation"

# ------------------------------------------------------------------ REFERENCE (physical) ----
ref_tbl = pd.DataFrame(
    [dict(Paper_ID=PT, Table_ID="mixer table", Item=m, Consistency_wt_pct=c, Power_Dissipation_W_per_m3=p, Energy_MJ_per_ton=e) for m, c, p, e in
     [("Hand mixing","3","2e4",120),("CSTR","2-3","600","5-9"),("Quantum (high shear) mixer","5","4.5e5",63),("High shear","10","1.8e6",180)]] +
    [dict(Paper_ID=PT, Table_ID="ozone solubility table", Item="O3 solubility vs pressure", Total_Pressure_psia=a, O3_Partial_Pressure_psia=b, O3_Solubility_g_per_m3=c) for a, b, c in
     [(14.7,1.22,13.2),(24.7,2.05,22.2),(164.7,13.67,147.9)]])

# ------------------------------------------------------------------ COMBINED CLEAN ---------
def std_row(r, group):
    o3d = r["Ozone_Dose"]; o3c = r["Ozone_Consumed"]
    if r["Ozone_Dose_Unit"] and str(r["Ozone_Dose_Unit"]).startswith("kg"): o3d = o3d * 0.1  # 1 kg/t = 0.1 % o.d. pulp
    if r["Ozone_Consumed_Unit"] and str(r["Ozone_Consumed_Unit"]).startswith("kg"): o3c = o3c * 0.1
    tmin = None
    if r["Reaction_Time"] is not None:
        tmin = r["Reaction_Time"] / 60 if r["Reaction_Time_Unit"] == "s" else r["Reaction_Time"]
    vu = str(r["Final_Viscosity_Unit"] or "")
    return dict(Task_Group=group, Paper_ID=r["Paper_ID"], Experiment_ID=r["Experiment_ID"], Origin="EXTERNAL_LITERATURE", Wood_Type=r["Wood_Type"],
                Temp_C=r["Temperature_C"], pH=r["pH"], Consistency_pct=r["Pulp_Consistency_percent"], O3_Dose_pct_odp=o3d, O3_Consumed_pct_odp=o3c,
                Time_min=tmin, Additive=r["Additive"], Medium=r["Medium"], Initial_Kappa=r["Initial_Kappa"],
                Kappa=r["Final_Kappa"], Brightness_ISO=r["Final_Brightness"] if r["Brightness_Scale"] == "%ISO" else None,
                Brightness_Elrepho=r["Final_Brightness"] if r["Brightness_Scale"] == "Elrepho" else None,
                Viscosity_mPas=r["Final_Viscosity"] if vu == "mPa.s" else None, Viscosity_cP=r["Final_Viscosity"] if vu == "cP" else None,
                Viscosity_mlg=r["Final_Viscosity"] if vu.startswith("ml/g") else None, Selectivity=r["Selectivity"], DP=r["DP"],
                L_star=r["L_star"], a_star=r["a_star"], b_star=r["b_star"], Is_Baseline=r["Is_Baseline"],
                Unit_Conversions="kg/t -> %: x0.1; s -> min: /60 (originals kept in Literature sheet)", Source_Row=r["Experiment_ID"])
clean = []
p1 = {r["Experiment_ID"].split("Exp")[1]: r for r in rows if r["Paper_ID"] == "P1_OPTICAL"}
p2 = {r["Experiment_ID"].split("Exp")[1]: r for r in rows if r["Paper_ID"] == "P2_DP"}
for k, r in p1.items():
    d = std_row(r, "KINETICS_OPTICAL_DP")
    q = p2[k]; d["Viscosity_mlg"] = q["Final_Viscosity"]; d["DP"] = q["DP"]
    d["Source_Row"] = f"{r['Experiment_ID']} + {q['Experiment_ID']} (joined on shared Exp number; O3 and t verified equal)"
    clean.append(d)
grp = {"P3_EKP": "PULP_QUALITY_KAPPA_BRIGHTNESS", "P5_ORGANOSOLV": "PULP_QUALITY_KAPPA_BRIGHTNESS", "P6_PROTECTORS": "PULP_QUALITY_KAPPA_BRIGHTNESS", PT: "PULP_QUALITY_KAPPA_BRIGHTNESS"}
for r in rows:
    if r["Paper_ID"] in grp:
        if r["Paper_ID"] == "P3_EKP" and r["Table_ID"] == "Table 2": clean.append(std_row(r, "OZONE_MASS_TRANSFER_ADDITIVES")); continue
        if r["Paper_ID"] == PT and r["Table_ID"] in ("Table 1", "Table 2"): clean.append(std_row(r, "OZONE_UTILISATION_REACTOR")); continue
        clean.append(std_row(r, grp[r["Paper_ID"]]))
combined = pd.DataFrame(clean); combined.insert(0, "Row_ID", [f"C{i:04d}" for i in range(1, len(combined) + 1)])
combined["Brightness_Scale_Note"] = "ISO and Elrepho kept in separate columns - NOT interchangeable; L* is CIELAB lightness, not brightness."

# ------------------------------------------------------------------ SOURCE INDEX ------------
idx = []
for pid, s in SOURCES.items():
    n = int((lit.Paper_ID == pid).sum())
    sub = lit[lit.Paper_ID == pid]
    vars_ = ", ".join(c for c in COLS if n and sub[c].notna().any() and c not in ("Dataset_Source", "Paper_ID", "DOI_or_Patent", "Value_Type", "Is_Baseline")) or "-"
    idx.append(dict(Source_ID=pid, Full_title=s["title"], Authors=s["authors"], Year=s["year"], DOI_or_patent=s["doi"], URL=s["url"],
                    Data_tables_extracted=s["tables"], Number_of_experimental_rows=n,
                    Derived_rows_in_Derived_sheet=int((derived.Paper_ID == pid).sum()) if pid in derived.Paper_ID.values else 0, Variables_available=vars_))
src_idx = pd.DataFrame(idx)

# ------------------------------------------------------------------ EXISTING (verbatim) -----
# The team's own screenshot-PDF, preserved as printed (numbers as printed, one block per printed table).
def block(title, df): return title, df
blocks = [
 ("P1 Tab.1 - 40 C (as printed)  cols: Exp | pH | O3con (% on o.d. pulp) | t (s) | L | a* | b*", pd.DataFrame([[int(r[0]), r[1], r[2], int(r[3]), r[4], r[5], r[6]] for r in P1[40]], columns=["Exp","pH","O3con","t_s","L","a*","b*"])),
 ("P1 Tab.2 - 20 C (as printed)", pd.DataFrame([[int(r[0]), r[1], r[2], int(r[3]), r[4], r[5], r[6]] for r in P1[20]], columns=["Exp","pH","O3con","t_s","L","a*","b*"])),
 ("P2 Tab.1 - 40 C (as printed)  cols: Exp | O3con | t (s) | [eta] ml/g | DP", pd.DataFrame([[int(r[0]), r[1], int(r[2]), int(r[3]), int(r[4])] for r in P2[40]], columns=["Exp","O3con","t_s","eta_ml_g","DP"])),
 ("P2 Tab.2 - 20 C (as printed)", pd.DataFrame([[int(r[0]), r[1], int(r[2]), int(r[3]), int(r[4])] for r in P2[20]], columns=["Exp","O3con","t_s","eta_ml_g","DP"])),
 ("P3 Table 1 (as printed)", pd.DataFrame(P3_T1, columns=["Consistency_pct","Ozone_dosage_pct_odp","pH","Time_min","NP10_pct_odp","Brightness_pctISO","Viscosity_printed_pctISO","Kappa"])),
 ("P3 Table 2 (as printed)", pd.DataFrame(P3_T2, columns=["Additive","KLa_s-1","C*L_mg_L","sigma_N_m","Exp_reactivity","Theor_reactivity","Efficiency"])),
 ("P5 Table 1 (as printed; ozone consumed 1.1% b.d. pulp)", pd.DataFrame(T1, columns=["Pretreatment","Kappa","Viscosity_mPas","Selectivity","Brightness_Elrepho"])),
 ("P5 Table 2 (as printed)", pd.DataFrame(T2, columns=["Ozone_consumed_pct","Kappa","Viscosity_mPas","Selectivity","Brightness_Elrepho","Efficiency"])),
 ("P5 Table 3 (as printed; P stage rows)", pd.DataFrame(T3, columns=["Z_ozone_consumed_pct","Kappa_after_P","Viscosity_after_P","Brightness_after_P"])),
 ("P5 Table 4 (as printed)", pd.DataFrame(T4, columns=["Medium","Stage","Kappa","Viscosity_mPas","Selectivity","Brightness_Elrepho"])),
 ("P6 Table 1 (as printed; ozone charge 0.3% o.d. pulp; additives 1% o.d. pulp)", pd.DataFrame(P6, columns=["Additive","Ozone_consumption_pct_odp","Kappa","Viscosity_ml_g","Brightness_pctISO"])),
 ("PAT1 Table 1 (as printed)", pd.DataFrame([(2.4,2.2,93.0,5,46),(4.0,3.9,95.0,5,55),(6.1,5.8,95.1,5,52),(7.3,7.0,95.9,5,65)], columns=["O3_charge_kg_t","O3_consumed_kg_t","O3_reacted_pct","Retention_min","Pressure_psig"])),
 ("PAT1 Table 2 (as printed; '6-3' typo kept as 6.3)", pd.DataFrame([(6.3,30,20,87,99),(6.3,90,80,94,99),(6.3,110,100,99,99)], columns=["Ozone_charge_kg_t","Inlet_mixer_psig","Bottom_tower_psig","Consumed_in_mixer_pct","Consumed_top_tower_pct"])),
]
with pd.ExcelWriter(ARCHIVE / "OzoLab_Ozone_Bleaching_Dataset.xlsx", engine="openpyxl") as xw:
    r0 = 0; title_rows = []
    for title, df in blocks:
        pd.DataFrame({title: []}).to_excel(xw, sheet_name="Existing_Dataset", startrow=r0, index=False)
        df.to_excel(xw, sheet_name="Existing_Dataset", startrow=r0 + 1, index=False); r0 += len(df) + 4
    pd.DataFrame({"README": ["Existing_Dataset = the team's screenshot PDF, transcribed exactly as printed (numbers unchanged). "
                             "Not harmonised, no unit conversion. PAT2/PAT3 blocks omitted: PAT2 repeats PAT1 tables, PAT3 had no table in the PDF. "
                             "P4 and P1-Tab.3 fit tables are in the Derived_Calculated sheet."]}).to_excel(xw, sheet_name="Existing_Dataset", startrow=r0, index=False)
    lit.to_excel(xw, sheet_name="Literature_Ozone_Bleaching", index=False)
    combined.to_excel(xw, sheet_name="Combined_Clean_Dataset", index=False)
    src_idx.to_excel(xw, sheet_name="Source_Index", index=False)
    derived.to_excel(xw, sheet_name="Derived_Calculated", index=False)
    ref_tbl.to_excel(xw, sheet_name="Reference_Physical", index=False)
    for ws in xw.book.worksheets:
        for col in ws.columns:
            ws.column_dimensions[col[0].column_letter].width = min(38, max(10, max(len(str(c.value)) if c.value is not None else 0 for c in col[:60]) + 2))
        ws.freeze_panes = "A2" if ws.title != "Existing_Dataset" else None

lit.to_csv(LIT / "literature_ozone_bleaching.csv", index=False)
combined.to_csv(LIT / "combined_clean_dataset.csv", index=False)
derived.to_csv(LIT / "derived_calculated_not_observations.csv", index=False)
src_idx.to_csv(LIT / "source_index.csv", index=False)
print("Literature rows:", len(lit), "| Combined clean rows:", len(combined), "| Derived rows:", len(derived))
print(lit.groupby("Paper_ID").size().to_string()); print(combined.groupby("Task_Group").size().to_string())
