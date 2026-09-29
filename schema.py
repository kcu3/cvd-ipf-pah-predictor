"""Input definitions retained from the supplied website; see MODEL_NOTES.md."""
CVD_FIELDS = [
    {"name":"age","model_feature":"age","label":"Age","type":"number","step":"1","min":"40","max":"85","unit":"years","range_hint":"40–85 years"},
    {"name":"sex","model_feature":"sex","label":"Sex","type":"select","options":[("0","Female"),("1","Male")],"range_hint":"CVD model coding"},
    {"name":"smoke","model_feature":"smoke","label":"Current smoker","type":"select","options":[("0","No"),("1","Yes")],"range_hint":"Current smoking status"},
    {"name":"sbp","model_feature":"sbp","label":"Systolic blood pressure","type":"number","step":"1","min":"70","max":"250","unit":"mmHg","range_hint":"70–250 mmHg"},
    {"name":"bmi","model_feature":"bmi","label":"BMI","type":"number","step":"0.1","min":"12","max":"70","unit":"kg/m²","range_hint":"12–70 kg/m²"},
    {"name":"tc","model_feature":"tc","label":"Total cholesterol","type":"number","step":"0.01","min":"1","max":"15","unit":"mmol/L","range_hint":"1–15 mmol/L"},
    {"name":"hdl","model_feature":"hdl","label":"HDL cholesterol","type":"number","step":"0.01","min":"0.2","max":"5","unit":"mmol/L","range_hint":"0.2–5 mmol/L"},
    {"name":"egfr","model_feature":"egfr","label":"eGFR","type":"number","step":"0.1","min":"5","max":"180","unit":"mL/min/1.73m²","range_hint":"5–180 mL/min/1.73m²"},
]

PAH_FIELDS = [
    {"name":"BL_AGE","model_feature":"BL_AGE","label":"Age","type":"number","step":"1","min":"40","max":"85","unit":"years","range_hint":"Baseline age"},
    {"name":"SEX","model_feature":"SEX","label":"Sex","type":"select","options":[("1","Female"),("2","Male")],"range_hint":"PAH training encoding"},
    {"name":"SMOKING","model_feature":"SMOKING","label":"Current smoker","type":"select","options":[("0","No"),("1","Yes")],"range_hint":"Model smoking indicator"},
    {"name":"BMI","model_feature":"BMI","label":"BMI","type":"number","step":"0.1","min":"12","max":"75","unit":"kg/m²","range_hint":"Body mass index"},
    {"name":"SBP","model_feature":"SBP","label":"Systolic blood pressure","type":"number","step":"1","min":"70","max":"250","unit":"mmHg","range_hint":"Systolic blood pressure"},
    {"name":"HDL","model_feature":"HDL","label":"HDL cholesterol","type":"number","step":"0.001","min":"0.1","max":"6","unit":"mmol/L","range_hint":"HDL cholesterol"},
    {"name":"TC","model_feature":"TC","label":"Total cholesterol","type":"number","step":"0.001","min":"1","max":"15","unit":"mmol/L","range_hint":"Total cholesterol"},
    {"name":"CREAT","model_feature":"CREAT","label":"Creatinine","type":"number","step":"0.1","min":"0","max":"500","unit":"model units","range_hint":"Enter in the same units used by the training data"},
    {"name":"EGFR","model_feature":"EGFR","label":"eGFR","type":"number","step":"0.1","min":"1","max":"200","unit":"mL/min/1.73m²","range_hint":"Estimated glomerular filtration rate"},
]

IPF_FIELDS = [
    {"name":"BL_AGE","model_feature":"BL_AGE","label":"Age","type":"number","step":"1","min":"40","max":"85","unit":"years","range_hint":"Baseline age"},
    {"name":"SEX","model_feature":"SEX","label":"Sex","type":"select","options":[("1","Male"),("2","Female")],"range_hint":"IPF training encoding"},
    {"name":"SMOKING","model_feature":"SMOKING","label":"Current smoker","type":"select","options":[("0","No"),("1","Yes")],"range_hint":"Model smoking indicator"},
    {"name":"SMOKING_DEPEND","model_feature":"SMOKING_DEPEND","label":"Smoking dependence indicator","type":"select","options":[("0","No"),("1","Yes")],"range_hint":"Model feature: SMOKING_DEPEND"},
    {"name":"I2_ANY","model_feature":"I2_ANY","label":"I2_ANY indicator","type":"select","options":[("0","No"),("1","Yes")],"range_hint":"Model feature: I2_ANY"},
    {"name":"p20116_i0","model_feature":"p20116_i0","label":"Smoking status","type":"select","options":[("0","Never"),("1","Previous"),("2","Current"),("-3","Prefer not to say")],"range_hint":"UK Biobank field 20116, baseline"},
    {"name":"p21001_i0","model_feature":"p21001_i0","label":"BMI — baseline","type":"number","step":"0.0001","min":"10","max":"75","unit":"kg/m²","range_hint":"UK Biobank field 21001, instance 0"},
    {"name":"p21001_i1","model_feature":"p21001_i1","label":"BMI — repeat assessment","type":"number","step":"0.0001","min":"10","max":"75","unit":"kg/m²","range_hint":"UK Biobank field 21001, instance 1"},
    {"name":"p21002_i0","model_feature":"p21002_i0","label":"Weight — baseline","type":"number","step":"0.1","min":"25","max":"250","unit":"kg","range_hint":"UK Biobank field 21002, instance 0"},
    {"name":"p21002_i1","model_feature":"p21002_i1","label":"Weight — repeat assessment","type":"number","step":"0.1","min":"25","max":"250","unit":"kg","range_hint":"UK Biobank field 21002, instance 1"},
    {"name":"p30000_i0","model_feature":"p30000_i0","label":"White blood cell count","type":"number","step":"0.01","min":"0","max":"400","unit":"10⁹/L","range_hint":"UK Biobank field 30000"},
    {"name":"p30010_i0","model_feature":"p30010_i0","label":"Red blood cell count","type":"number","step":"0.001","min":"0","max":"8","unit":"10¹²/L","range_hint":"UK Biobank field 30010"},
    {"name":"p30020_i0","model_feature":"p30020_i0","label":"Haemoglobin","type":"number","step":"0.01","min":"0","max":"25","unit":"g/dL","range_hint":"UK Biobank field 30020"},
    {"name":"p30030_i0","model_feature":"p30030_i0","label":"Haematocrit","type":"number","step":"0.01","min":"0","max":"75","unit":"%","range_hint":"UK Biobank field 30030"},
    {"name":"p30040_i0","model_feature":"p30040_i0","label":"Mean corpuscular volume","type":"number","step":"0.01","min":"40","max":"170","unit":"fL","range_hint":"UK Biobank field 30040"},
    {"name":"p30080_i0","model_feature":"p30080_i0","label":"Platelet count","type":"number","step":"0.1","min":"0","max":"2000","unit":"10⁹/L","range_hint":"UK Biobank field 30080"},
]

DISEASES = {
    "cvd": {
        "label": "CVD",
        "title": "10-year CVD probability",
        "subtitle": "Individual estimate from the UKBB model with BBRU calibration.",
        "fields": CVD_FIELDS,
        "score_label": "BBRU-calibrated 10-year CVD estimate",
        "calibrated": True,
    },
    "ipf": {
        "label": "IPF",
        "title": "10-year IPF model",
        "subtitle": "Idiopathic pulmonary fibrosis",
        "fields": IPF_FIELDS,
        "score_label": "IPF prediction",
        "calibrated": False,
    },
    "pah": {
        "label": "PAH",
        "title": "10-year PAH model",
        "subtitle": "Pulmonary arterial hypertension",
        "fields": PAH_FIELDS,
        "score_label": "PAH prediction",
        "calibrated": False,
    },
}
