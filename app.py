import streamlit as st
import pandas as pd
import plotly.express as px
import io
import warnings
import os
import numpy as np
import re

warnings.filterwarnings('ignore')

# ==========================================
# 1. PAGE CONFIGURATION & DATA LOADING
# ==========================================
st.set_page_config(page_title="ACAD Master Dashboard", layout="wide", initial_sidebar_state="expanded")

# Hardcoded DPS Codes
DPS_CODES = ["2449", "19028", "212432", "234775", "265162", "353776", "3254316", "5014895", "5016187", "5017383", "5018233", "5018234"]

@st.cache_data
def load_data():
    # 1. Operational, Product & Feedback Data
    try:
        acad_cal = pd.read_csv('acad calende.csv')
        det_acad_cal = pd.read_csv('detiled acad calender.csv')
        kdm = pd.read_csv('kdmexport.csv')
        det_kdm = pd.read_csv('detiled kdm.csv')
        onboarding = pd.read_csv('onboarding.csv')
        det_onboard = pd.read_csv('detiled onboarding.csv')
        crm = pd.read_csv('crm.csv')
        feedback = pd.read_csv('feedback.csv')
        cares_schools = pd.read_csv('caresschools.csv')
        asset = pd.read_csv('Asset school list.csv')
        ms_math = pd.read_csv('Mindspark math.csv')
        ms_eng = pd.read_csv('mindspark english.csv')
        
        # Detailed Feedback and Org Hierarchy
        det_feedback = pd.read_csv('detailed feedback.csv') if os.path.exists('detailed feedback.csv') else pd.DataFrame()
        org_data = pd.read_csv('Supporting data(2)-13th March 2026 (8).xlsx - Org.csv') if os.path.exists('Supporting data(2)-13th March 2026 (8).xlsx - Org.csv') else pd.DataFrame()
        
        # Detailed CRM / MOM Data
        det_crm = pd.read_csv('Untitled spreadsheet - Sheet1.csv') if os.path.exists('Untitled spreadsheet - Sheet1.csv') else pd.DataFrame()
        
    except Exception as e:
        st.error(f"Error loading Operational CSVs. Details: {e}")
        st.stop()
    
    # 2. Financial & Risk Data
    def load_smart_csv(*filenames):
        for name in filenames:
            if os.path.exists(name):
                return pd.read_csv(name)
        return pd.DataFrame()

    fin_2025 = load_smart_csv('For Vijeta.xlsx - 2026.csv', 'Supporting data(2)-13th March 2026 (8)_2025.csv', 'Supporting data(2)-13th March 2026 (8).xlsx - 2025.csv')
    fin_2027 = load_smart_csv('Supporting data(2)-13th March 2026 (8)_2027.csv', 'Supporting data(2)-13th March 2026 (8).xlsx - 2027.csv')
    drop_risk = load_smart_csv('Supporting data(2)-13th March 2026 (8)_Drop & Risk Analysis.csv', 'Supporting data(2)-13th March 2026 (8).xlsx - Drop & Risk Analysis.csv')
        
    for df in [fin_2025, fin_2027, drop_risk, det_feedback, det_crm]:
        if 'ACAD Name' in df.columns: df.rename(columns={'ACAD Name': 'ACAD'}, inplace=True)
        if 'CRM Acad Consultant' in df.columns and 'ACAD' not in df.columns: df.rename(columns={'CRM Acad Consultant': 'ACAD'}, inplace=True)
        if 'Facilitator' in df.columns and 'ACAD' not in df.columns: df.rename(columns={'Facilitator': 'ACAD'}, inplace=True)
        if 'Host Name' in df.columns and 'ACAD' not in df.columns: df.rename(columns={'Host Name': 'ACAD'}, inplace=True)
            
    if 'School No' in fin_2025.columns: fin_2025['School No'] = fin_2025['School No'].astype(str).str.strip().str.replace('.0', '', regex=False)
    if 'School No' in fin_2027.columns: fin_2027['School No'] = fin_2027['School No'].astype(str).str.strip().str.replace('.0', '', regex=False)

    # DATA CLEANING: Remove Pakistan & Fix "North,West" to "North"
    if not fin_2025.empty:
        for col in ['Zone', 'Division', 'Country', 'State', 'Shipping State']:
            if col in fin_2025.columns:
                fin_2025 = fin_2025[~fin_2025[col].astype(str).str.contains('Pakistan', case=False, na=False)]
        
        if 'Division' in fin_2025.columns:
            fin_2025['Division'] = fin_2025['Division'].astype(str).str.replace(r'(?i)north[\s,]*west', 'North', regex=True).replace({'nan': np.nan, 'None': np.nan})
        if 'Zone' in fin_2025.columns:
            fin_2025['Zone'] = fin_2025['Zone'].astype(str).str.replace(r'(?i)north[\s,]*west', 'North', regex=True).replace({'nan': np.nan, 'None': np.nan})

    if 'Host Name' in crm.columns: crm.rename(columns={'Host Name': 'ACAD'}, inplace=True)
    if 'Acad Name' in feedback.columns: feedback.rename(columns={'Acad Name': 'ACAD'}, inplace=True)

    # ==========================================
    # 3. GLOBAL ACAD NAME NORMALIZATION
    # ==========================================
    acad_nickname_mapping = {
        "Anushka": "Anushka Gupta",
        "Aruna": "Aruna Unnikrishnan",
        "Bhavishya": "Bhavishya Bansal",
        "Chaitanya": "Chaitanya Kolluri",
        "Gargi": "Gargi Ghosh",
        "Lopa": "Lopamudra Das",
        "Manavi": "Manavi Khandelwal",
        "Pooja": "Pooja Kapoor",
        "Phanindra Reddy": "Phanindra Reddy Alla",
        "Rohit": "Rohit Kumar",
        "Shruti": "Shruti Chauhan",
        "Tanya": "Tanya Marina Brooks",
        "Vaishali": "Vaishali Yadav"
    }

    all_raw_dfs = [acad_cal, det_acad_cal, kdm, det_kdm, onboarding, det_onboard, crm, feedback, 
                   cares_schools, asset, ms_math, ms_eng, fin_2025, fin_2027, drop_risk, 
                   det_feedback, org_data, det_crm]

    for df in all_raw_dfs:
        if 'ACAD' in df.columns:
            # 1. Strip Invalid Excel Characters globally (\, /, *, ?, :, [, ])
            df['ACAD'] = df['ACAD'].astype(str).str.replace(r'[\\/*?:\[\]]', '', regex=True)
            # 2. Clean trailing spaces
            df['ACAD'] = df['ACAD'].str.strip()
            # 3. Apply Nickname to Full Name Mapping
            df['ACAD'] = df['ACAD'].replace(acad_nickname_mapping)
            # 4. Restore Null values
            df['ACAD'] = df['ACAD'].replace({'nan': np.nan, 'None': np.nan, '': np.nan})
            
    # Bulletproof Numerical Parsing
    def to_num(df, col):
        if col in df.columns:
            if df[col].dtype == object:
                df[col] = df[col].astype(str).str.replace('%', '', regex=False).str.replace(',', '', regex=False).str.strip()
                df[col] = df[col].replace({'Unknown': '0', 'nan': '0', 'None': '0'})
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

    to_num(kdm, '% Coverage')
    to_num(onboarding, '% Coverage')
    to_num(acad_cal, 'Percentage Compliant')
    to_num(cares_schools, 'Utilization (%)')
    to_num(ms_math, 'Login %')
    to_num(ms_eng, 'Login %')
    to_num(asset, 'Overall Score (%)')
    
    # Calculate Mindspark Zero Usage %
    if 'Zero Usage %' not in ms_math.columns and 'Login %' in ms_math.columns: ms_math['Zero Usage %'] = 100 - ms_math['Login %']
    if 'Zero Usage %' not in ms_eng.columns and 'Login %' in ms_eng.columns: ms_eng['Zero Usage %'] = 100 - ms_eng['Login %']

    # CARES Test Utilization GAP logic
    if 'Start Date' in cares_schools.columns:
        cares_schools['Start Date'] = pd.to_datetime(cares_schools['Start Date'], errors='coerce')
        cares_schools['Expected Utilization'] = np.minimum(((pd.Timestamp.now() - cares_schools['Start Date']).dt.days / 90) * 25, 100).fillna(100)
    else:
        cares_schools['Expected Utilization'] = 100
    if 'Utilization (%)' in cares_schools.columns:
        cares_schools['Gap'] = cares_schools['Utilization (%)'] - cares_schools['Expected Utilization']
        cares_schools['KRA Grade'] = cares_schools['Gap'].apply(lambda gap: "NI (2)" if pd.isna(gap) or gap < -1 else ("ME (3)" if gap <= 1 else ("EE (4)" if gap <= 10 else "DE (5)")))

    # CRM Update SLA Calculation (<48h)
    if not det_acad_cal.empty and 'Session Date' in det_acad_cal.columns and 'Date Updated' in det_acad_cal.columns:
        det_acad_cal['Session Date'] = pd.to_datetime(det_acad_cal['Session Date'], errors='coerce')
        det_acad_cal['Date Updated'] = pd.to_datetime(det_acad_cal['Date Updated'], errors='coerce')
        det_acad_cal['Log_Delay_Hours'] = (det_acad_cal['Date Updated'] - det_acad_cal['Session Date']).dt.total_seconds() / 3600
    else:
        det_acad_cal['Log_Delay_Hours'] = 0
        
    # Calculate MOM Word Count
    if not det_crm.empty and 'Description' in det_crm.columns:
        det_crm['MOM_Word_Count'] = det_crm['Description'].astype(str).apply(lambda x: len(x.split()) if str(x).lower() != 'nan' else 0)
    
    return acad_cal, det_acad_cal, kdm, det_kdm, onboarding, det_onboard, crm, feedback, cares_schools, asset, ms_math, ms_eng, fin_2025, fin_2027, drop_risk, det_feedback, org_data, det_crm

acad_cal, det_acad_cal, kdm, det_kdm, onboarding, det_onboard, crm, feedback, cares_schools, asset, ms_math, ms_eng, fin_2025, fin_2027, drop_risk, det_feedback, org_data, det_crm = load_data()

# Ensure ALL ACADs are tracked (Restores full 645 school count)
base_acads = pd.concat([acad_cal['ACAD'], crm['ACAD'], feedback['ACAD'], fin_2025['ACAD']]).dropna().unique()
base_acads = sorted([str(x) for x in base_acads if str(x) not in ["Unknown", "nan"]])

# Strict Retention Logic WITH Winter Round Exemption
if not fin_2025.empty and not fin_2027.empty and 'School No' in fin_2025.columns:
    schools_2027_list = fin_2027['School No'].dropna().unique().tolist()
    fin_2025['Is_Retained'] = fin_2025.apply(
        lambda row: True if row['School No'] in schools_2027_list or 'Winter' in str(row.get('ASSETRound', '')) else False, axis=1
    )
else:
    if not fin_2025.empty: fin_2025['Is_Retained'] = False

# Highlighting Logic
def style_ni(row, condition): return ['background-color: #ffe6e6' if condition else ''] * len(row)
def highlight_cares(row): 
    cond = row['KRA Category'] == 'NI' if 'KRA Category' in row.index else False
    if 'KRA Grade' in row.index and "NI" in str(row['KRA Grade']): cond = True
    return style_ni(row, cond)
def highlight_ms(row): 
    val = row['Login %'] if 'Login %' in row.index else 100
    return style_ni(row, val < 70) 
def highlight_asset(row): 
    val = row['Overall Score (%)'] if 'Overall Score (%)' in row.index else 100
    return style_ni(row, val < 80)
def highlight_kdm(row): 
    val = row['% Coverage'] if '% Coverage' in row.index else 100
    return style_ni(row, val < 20)
def highlight_sla(row): 
    val = row['Log_Delay_Hours'] if 'Log_Delay_Hours' in row.index else 0
    return style_ni(row, val > 48)

# ==========================================
# 2. SIDEBAR & DIVISION/ZONE FILTERING
# ==========================================
st.sidebar.title("Navigation & Filters")

# Division & Zone Chained Filters
available_divisions = ["All Divisions"] + sorted([str(x) for x in fin_2025['Division'].dropna().unique() if x]) if not fin_2025.empty and 'Division' in fin_2025.columns else ["All Divisions"]
selected_division = st.sidebar.selectbox("🏢 Filter by Division:", available_divisions)

if selected_division != "All Divisions" and not fin_2025.empty:
    div_filtered_fin = fin_2025[fin_2025['Division'] == selected_division]
    available_zones = ["All Zones"] + sorted([str(x) for x in div_filtered_fin['Zone'].dropna().unique() if x])
else:
    available_zones = ["All Zones"] + sorted([str(x) for x in fin_2025['Zone'].dropna().unique() if x]) if not fin_2025.empty and 'Zone' in fin_2025.columns else ["All Zones"]

selected_zone = st.sidebar.selectbox("🌍 Filter by Zone:", available_zones)

# CROSS-DIVISIONAL ACAD ISOLATION (Filter all operational data strictly by the selected schools)
if not fin_2025.empty:
    filtered_df = fin_2025.copy()
    if selected_division != "All Divisions":
        filtered_df = filtered_df[filtered_df['Division'] == selected_division]
    if selected_zone != "All Zones":
        filtered_df = filtered_df[filtered_df['Zone'] == selected_zone]
    
    valid_acads = filtered_df['ACAD'].dropna().unique().tolist()
    all_acads = sorted([a for a in base_acads if a in valid_acads])

    if selected_division != "All Divisions" or selected_zone != "All Zones":
        valid_s_names = filtered_df['School Name'].dropna().astype(str).str.strip().str.lower().unique()
        
        def filter_by_school(df, col):
            if df.empty or col not in df.columns: return df
            return df[df[col].astype(str).str.strip().str.lower().isin(valid_s_names)]

        # Apply strict school filter so ACADs crossing divisions only show data for current selection
        feedback = filter_by_school(feedback, 'School Name')
        det_feedback = filter_by_school(det_feedback, 'School Name')
        crm = filter_by_school(crm, 'Customer Account Name')
        det_crm = filter_by_school(det_crm, 'Customer Account Name')
        kdm = filter_by_school(kdm, 'School Name')
        det_kdm = filter_by_school(det_kdm, 'School Name')
        acad_cal = filter_by_school(acad_cal, 'School Name')
        det_acad_cal = filter_by_school(det_acad_cal, 'School Name')
        onboarding = filter_by_school(onboarding, 'School Name')
        det_onboard = filter_by_school(det_onboard, 'School Name')
        cares_schools = filter_by_school(cares_schools, 'School Name')
        asset = filter_by_school(asset, 'School Name')
        ms_math = filter_by_school(ms_math, 'schoolName')
        ms_eng = filter_by_school(ms_eng, 'schoolName')
else:
    all_acads = base_acads
    filtered_df = pd.DataFrame()

page = st.sidebar.radio("Select Dashboard View:", [
    "🏢 Dept 13-Point Scorecard", 
    "💰 Goal 1: Retention & Revenue", 
    "📊 Product Utilisation & Goal Logic",
    "👤 Individual Dashboard & Goal Export",
    "🛠️ ACAD Name Diagnostics"
])
st.sidebar.divider()

def get_excel_col(df, col_name):
    """Helper function to find Excel column letter dynamically to make robust formulas"""
    try:
        idx = df.columns.get_loc(col_name) + 1
        letter = ""
        while idx > 0:
            idx, remainder = divmod(idx - 1, 26)
            letter = chr(65 + remainder) + letter
        return letter
    except:
        return "A"

def generate_individual_goal_sheet(acad_name, metrics, raw_dfs):
    """Generates EXCEL FORMULAS instead of static text so the sheet updates live on edit."""
    
    fb_col = get_excel_col(raw_dfs.get('Feedback', pd.DataFrame()), 'Overall Rating')
    mom_col = get_excel_col(raw_dfs.get('Detailed_CRM_MOM', pd.DataFrame()), 'MOM_Word_Count')
    kdm_col = get_excel_col(raw_dfs.get('KDM', pd.DataFrame()), '% Coverage')
    onb_col = get_excel_col(raw_dfs.get('Onboarding', pd.DataFrame()), '% Coverage')
    cal_col = get_excel_col(raw_dfs.get('Acad_Cal', pd.DataFrame()), 'Percentage Compliant')
    cares_col = get_excel_col(raw_dfs.get('CARES', pd.DataFrame()), 'Utilization (%)')
    ms_col = get_excel_col(raw_dfs.get('MS_Math', pd.DataFrame()), 'Login %')
    asset_col = get_excel_col(raw_dfs.get('ASSET', pd.DataFrame()), 'Overall Score (%)')
    crm_col = get_excel_col(raw_dfs.get('CRM', pd.DataFrame()), 'Meetings')
    fin_ret_col = get_excel_col(raw_dfs.get('2025_Fin', pd.DataFrame()), 'Is_Retained')

    ret_pct = f"(COUNTIF('2025_Fin'!{fin_ret_col}:{fin_ret_col}, TRUE)/MAX(1, COUNTA('2025_Fin'!A:A)-1))*100"
    ret_grade = f'IF({ret_pct}>=98, "DE", IF({ret_pct}>=95, "EE", IF({ret_pct}>=90, "ME", "NI")))'
    form_1 = f'=IFERROR(TEXT({ret_pct}, "0.0") & "% Retained [" & {ret_grade} & "]", "No Data")'

    fb_val = f"AVERAGE(Feedback!{fb_col}:{fb_col})"
    fb_grade = f'IF({fb_val}>=9, "DE", IF({fb_val}>=8.5, "EE", IF({fb_val}>=8, "ME", "NI")))'
    mom_val = f"AVERAGE(Detailed_CRM_MOM!{mom_col}:{mom_col})"
    form_2 = f'=IFERROR("Avg Rating: " & TEXT({fb_val}, "0.0") & "/10 [" & {fb_grade} & "] | Avg MOM: " & TEXT({mom_val}, "0.0") & " words", "No Data")'

    kdm_val = f"AVERAGE(KDM!{kdm_col}:{kdm_col})"
    kdm_grade = f'IF({kdm_val}>=60, "DE", IF({kdm_val}>=40, "EE", IF({kdm_val}>=20, "ME", "NI")))'
    form_3 = f'=IFERROR(TEXT({kdm_val}, "0.0") & "% Coverage [" & {kdm_grade} & "]", "No Data")'

    form_4 = f'=IFERROR(TEXT(AVERAGE(Onboarding!{onb_col}:{onb_col}), "0.0") & "% Coverage", "No Data")'

    cal_val = f"AVERAGE(Acad_Cal!{cal_col}:{cal_col})"
    cal_grade = f'IF({cal_val}>=70, "DE", IF({cal_val}>=60, "EE", IF({cal_val}>=50, "ME", "NI")))'
    form_5 = f'=IFERROR(TEXT({cal_val}, "0.0") & "% Compliant [" & {cal_grade} & "]", "No Data")'

    cares_val = f"AVERAGE(CARES!{cares_col}:{cares_col})"
    ms_val = f"AVERAGE(MS_Math!{ms_col}:{ms_col})"
    ms_grade = f'IF({ms_val}>=90, "DE", IF({ms_val}>=80, "EE", IF({ms_val}>=70, "ME", "NI")))'
    asset_val = f"AVERAGE(ASSET!{asset_col}:{asset_col})"
    cares_grade_str = f"[{metrics.get('cares_grade', 'NI')}]"
    form_util = f'=IFERROR("CARES: " & TEXT({cares_val}, "0.0") & "% {cares_grade_str} | MS Logins: " & TEXT({ms_val}, "0.0") & "% [" & {ms_grade} & "] | ASSET: " & TEXT({asset_val}, "0.0") & "%", "No Data")'

    meet_pct = f"(SUM(CRM!{crm_col}:{crm_col}) / MAX(1, (COUNTA('2025_Fin'!A:A)-1)*4))*100"
    idp_grade = f'IF({meet_pct}>=100, "DE", IF({meet_pct}>=90, "EE", IF({meet_pct}>=80, "ME", "NI")))'
    form_idp = f'=IFERROR("Meeting Target Achieved: " & TEXT({meet_pct}, "0.0") & "% [" & {idp_grade} & "]", "No Data")'

    goal_df = pd.DataFrame({
        "Category": [
            "Goal 1: Retention and Revenue", "", "", 
            "Goal 2: Effective Delivery Practices", "", "", "", 
            "Goal 3: Product Utilisation", "", 
            "Goal 4: Learning", ""
        ],
        "Initiatives": [
            "Make retention customers successful (>90% renew, 115% order value)",
            "School retention to be completed by 30th May",
            "On time Collection (Retention Schools)",
            "90% Session completion/visits, MoM, feedback, CRM update",
            "KDM meeting with all the schools",
            "Onboarding New Schools (Orientation in 30 days)",
            "Recording all the schools event on the Calendar (15 days prior)",
            "Webinar + Learning Summit",
            "Product Utilisation (ASSET, MS, CARES)",
            "Measure aspirations as mentioned in IDP (Calculated via Meetings)",
            "Supporting teachers in Action Research"
        ],
        "ME (Meets Expectations) Target": [
            "90% renew and 115% order value", "80% retention completed", "90% within 45 days",
            "100% completion in 48h, rating 8", "1 per quarter, 1 testimonial", "Within 30 days", "70% recorded before 15 days",
            "20% participation", "MS>=70%, ASSET 80%, CARES 100%",
            "Achieve success set as ME in IDP", "Readiness for Action Research"
        ],
        "Weightage": ["20%", "10%", "5%", "10%", "10%", "5%", "5%", "5%", "10%", "15%", "5%"],
        "Total Group Weight": ["35%", "", "", "30%", "", "", "", "15%", "", "20%", ""],
        "ACTUAL ACHIEVED (Live Excel Formulas)": [
            form_1, "N/A", "N/A", form_2, form_3, form_4, form_5, "N/A", form_util, form_idp, "Pending HR Eval"
        ]
    })
    return goal_df

def generate_dept_goal_sheet(division, zone, metrics, raw_dfs):
    """Generates the Dept Level KPA-2026 format with actuals mapped dynamically."""
    
    fb_col = get_excel_col(raw_dfs.get('Feedback', pd.DataFrame()), 'Overall Rating')
    mom_col = get_excel_col(raw_dfs.get('Detailed_CRM_MOM', pd.DataFrame()), 'MOM_Word_Count')
    kdm_col = get_excel_col(raw_dfs.get('KDM', pd.DataFrame()), '% Coverage')
    onb_col = get_excel_col(raw_dfs.get('Onboarding', pd.DataFrame()), '% Coverage')
    cal_col = get_excel_col(raw_dfs.get('Acad_Cal', pd.DataFrame()), 'Percentage Compliant')
    cares_col = get_excel_col(raw_dfs.get('CARES', pd.DataFrame()), 'Utilization (%)')
    ms_col = get_excel_col(raw_dfs.get('MS_Math', pd.DataFrame()), 'Login %')
    asset_col = get_excel_col(raw_dfs.get('ASSET', pd.DataFrame()), 'Overall Score (%)')
    crm_col = get_excel_col(raw_dfs.get('CRM', pd.DataFrame()), 'Meetings')
    fin_ret_col = get_excel_col(raw_dfs.get('2025_Fin', pd.DataFrame()), 'Is_Retained')

    ret_pct = f"(COUNTIF('2025_Fin'!{fin_ret_col}:{fin_ret_col}, TRUE)/MAX(1, COUNTA('2025_Fin'!A:A)-1))*100"
    ret_grade = f'IF({ret_pct}>=98, "DE", IF({ret_pct}>=95, "EE", IF({ret_pct}>=90, "ME", "NI")))'
    form_1 = f'=IFERROR(TEXT({ret_pct}, "0.0") & "% Retained [" & {ret_grade} & "]", "No Data")'

    fb_val = f"AVERAGE(Feedback!{fb_col}:{fb_col})"
    fb_grade = f'IF({fb_val}>=9, "DE", IF({fb_val}>=8.5, "EE", IF({fb_val}>=8, "ME", "NI")))'
    mom_val = f"AVERAGE(Detailed_CRM_MOM!{mom_col}:{mom_col})"
    form_2 = f'=IFERROR("Avg Rating: " & TEXT({fb_val}, "0.0") & "/10 [" & {fb_grade} & "] | Avg MOM: " & TEXT({mom_val}, "0.0") & " words", "No Data")'

    kdm_val = f"AVERAGE(KDM!{kdm_col}:{kdm_col})"
    kdm_grade = f'IF({kdm_val}>=60, "DE", IF({kdm_val}>=40, "EE", IF({kdm_val}>=20, "ME", "NI")))'
    form_3 = f'=IFERROR(TEXT({kdm_val}, "0.0") & "% Coverage [" & {kdm_grade} & "]", "No Data")'

    form_4 = f'=IFERROR(TEXT(AVERAGE(Onboarding!{onb_col}:{onb_col}), "0.0") & "% Coverage", "No Data")'

    cal_val = f"AVERAGE(Acad_Cal!{cal_col}:{cal_col})"
    cal_grade = f'IF({cal_val}>=70, "DE", IF({cal_val}>=60, "EE", IF({cal_val}>=50, "ME", "NI")))'
    form_5 = f'=IFERROR(TEXT({cal_val}, "0.0") & "% Compliant [" & {cal_grade} & "]", "No Data")'

    cares_val = f"AVERAGE(CARES!{cares_col}:{cares_col})"
    ms_val = f"AVERAGE(MS_Math!{ms_col}:{ms_col})"
    ms_grade = f'IF({ms_val}>=90, "DE", IF({ms_val}>=80, "EE", IF({ms_val}>=70, "ME", "NI")))'
    asset_val = f"AVERAGE(ASSET!{asset_col}:{asset_col})"
    cares_grade_str = f"[{metrics.get('cares_grade', 'NI')}]"
    form_util = f'=IFERROR("CARES: " & TEXT({cares_val}, "0.0") & "% {cares_grade_str} | MS Logins: " & TEXT({ms_val}, "0.0") & "% [" & {ms_grade} & "] | ASSET: " & TEXT({asset_val}, "0.0") & "%", "No Data")'

    meet_pct = f"(SUM(CRM!{crm_col}:{crm_col}) / MAX(1, (COUNTA('2025_Fin'!A:A)-1)*4))*100"
    idp_grade = f'IF({meet_pct}>=100, "DE", IF({meet_pct}>=90, "EE", IF({meet_pct}>=80, "ME", "NI")))'
    form_idp = f'=IFERROR("Meeting Target Achieved: " & TEXT({meet_pct}, "0.0") & "% [" & {idp_grade} & "]", "No Data")'

    goal_df = pd.DataFrame({
        "Category": [
            f"Filters Applied -> Division: {division} | Zone: {zone}",
            "Goal 1: Retention and Revenue", "", "", 
            "Goal 2: Effective Delivery Practices", "", "", "", 
            "Goal 3: Product Utilisation", "", 
            "Goal 4: Learning", ""
        ],
        "Initiatives": [
            "",
            "Make retention customers successful (>90% renew, 115% order value)",
            "School retention to be completed by 30th May",
            "On time Collection (Retention Schools)",
            "90% Session completion/visits, MoM, feedback, CRM update",
            "KDM meeting with all the schools",
            "Onboarding New Schools (Orientation in 30 days)",
            "Recording all the schools event on the Calendar (15 days prior)",
            "Webinar + Learning Summit",
            "Product Utilisation (ASSET, MS, CARES)",
            "Measure aspirations as mentioned in IDP (Calculated via Meetings)",
            "Supporting teachers in Action Research"
        ],
        "ME (Meets Expectations) Target": [
            "",
            "90% renew and 115% order value", "80% retention completed", "90% within 45 days",
            "100% completion in 48h, rating 8", "1 per quarter, 1 testimonial", "Within 30 days", "70% recorded before 15 days",
            "20% participation", "MS>=70%, ASSET 80%, CARES 100%",
            "Achieve success set as ME in IDP", "Readiness for Action Research"
        ],
        "Weightage": ["", "20%", "10%", "5%", "10%", "10%", "5%", "5%", "5%", "10%", "15%", "5%"],
        "Total Group Weight": ["", "35%", "", "", "30%", "", "", "", "15%", "", "20%", ""],
        "ACTUAL ACHIEVED (Live Excel Formulas)": [
            "",
            form_1, "N/A", "N/A", form_2, form_3, form_4, form_5, "N/A", form_util, form_idp, "Pending HR Eval"
        ]
    })
    return goal_df

@st.cache_data
def convert_acad_to_excel(acad_name, metrics, raw_dfs):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        goal_sheet = generate_individual_goal_sheet(acad_name, metrics, raw_dfs)
        
        # Clean ACAD Name to prevent openpyxl crashes
        safe_name = re.sub(r'[\\/*?:\[\]]', '', str(acad_name))
        
        goal_sheet.to_excel(writer, sheet_name=f'KPA_2026_{safe_name[:15]}', index=False)
        for name, df in raw_dfs.items():
            if not df.empty:
                safe_sheet = re.sub(r'[\\/*?:\[\]]', '', str(name))[:31]
                df.to_excel(writer, sheet_name=safe_sheet, index=False)
    return output.getvalue()

@st.cache_data
def convert_dept_to_excel(division, zone, metrics, master_summary, raw_dfs):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        goal_sheet = generate_dept_goal_sheet(division, zone, metrics, raw_dfs)
        goal_sheet.to_excel(writer, sheet_name='Dept_KPA_Scorecard', index=False)
        master_summary.to_excel(writer, sheet_name='Dept_Master_Summary', index=False)
        for name, df in raw_dfs.items():
            if not df.empty: 
                safe_sheet = re.sub(r'[\\/*?:\[\]]', '', str(name))[:31]
                df.to_excel(writer, sheet_name=safe_sheet, index=False)
    return output.getvalue()


# ==========================================
# 3. PAGE: DEPT 13-POINT SCORECARD
# ==========================================
if page == "🏢 Dept 13-Point Scorecard":
    st.title(f"🏢 Department 13-Point Scorecard")
    st.markdown(f"**Viewing:** Division: `{selected_division}` | Zone: `{selected_zone}`")
    
    total_acads = len(all_acads)
    
    dept_fin = filtered_df if not filtered_df.empty else pd.DataFrame()
    total_2025_schools_dept = len(dept_fin) if not dept_fin.empty else 0
    
    # Calculate Dept Metrics for Export & Scorecard
    dept_fb = feedback[feedback['ACAD'].isin(all_acads)] if not feedback.empty else pd.DataFrame()
    fb_val = dept_fb['Overall Rating'].mean() if not dept_fb.empty else 0
    
    dept_crm = crm[crm['ACAD'].isin(all_acads)] if not crm.empty else pd.DataFrame()
    tot_meetings = dept_crm['Meetings'].sum() if not dept_crm.empty else 0
    avg_meetings = tot_meetings / total_acads if total_acads > 0 else 0
    target_meetings_dept = total_2025_schools_dept * 4
    dept_meet_pct = min((tot_meetings / target_meetings_dept) * 100, 100) if target_meetings_dept > 0 else 0
    
    dept_kdm = kdm[kdm['ACAD'].isin(all_acads)] if not kdm.empty else pd.DataFrame()
    dept_kdm_cov = dept_kdm['% Coverage'].mean() if not dept_kdm.empty else 0
    
    dept_onb = onboarding[onboarding['ACAD'].isin(all_acads)] if not onboarding.empty else pd.DataFrame()
    dept_onb_cov = dept_onb['% Coverage'].mean() if not dept_onb.empty else 0
    
    dept_acad_cal = acad_cal[acad_cal['ACAD'].isin(all_acads)] if not acad_cal.empty else pd.DataFrame()
    dept_acad_cal_cov = dept_acad_cal['Percentage Compliant'].mean() if not dept_acad_cal.empty else 0
    
    dept_cares = cares_schools[cares_schools['ACAD'].isin(all_acads)] if not cares_schools.empty else pd.DataFrame()
    dept_cares_util = dept_cares['Utilization (%)'].mean() if not dept_cares.empty else 0
    dept_cares_gap = dept_cares['Gap'].mean() if not dept_cares.empty and 'Gap' in dept_cares.columns else 0
    dept_cares_grade_eval = "DE" if dept_cares_gap > 10 else "EE" if dept_cares_gap >= 1 else "ME" if dept_cares_gap >= -1 else "NI"
    
    dept_det_crm = det_crm[det_crm['ACAD'].isin(all_acads)] if not det_crm.empty and 'MOM_Word_Count' in det_crm.columns else pd.DataFrame()
    dept_avg_mom = dept_det_crm['MOM_Word_Count'].mean() if not dept_det_crm.empty else 0
    
    # Render Scorecard Metrics
    s1, s2, s3, s4 = st.columns(4)
    s1.metric("1. Avg Feedback", f"{fb_val:.2f} / 10", f"Metric: Avg of all survey responses", delta_color="off")
    s2.metric("9. Avg Session (NPS)", f"{dept_crm['Average Rating'].mean() if not dept_crm.empty else 0:.2f} / 5", "Metric: Avg CRM rating", delta_color="off")
    s3.metric("7. Total Schools", total_2025_schools_dept, "Metric: Base 2025 Allocation", delta_color="off")
    s4.metric(f"6. Total Meetings", tot_meetings, f"Avg {avg_meetings:.1f}/person | Target: {target_meetings_dept} ({dept_meet_pct:.1f}%)", delta_color="off")

    st.divider()
    s5, s6, s7, s8 = st.columns(4)
    s5.metric("3. Avg KDM Coverage", f"{dept_kdm_cov:.1f}%", f"Metric: (KDM Done / Alloted) * 100", delta_color="off")
    s6.metric("4. Avg Onboarding", f"{dept_onb_cov:.1f}%", f"Metric: (Orientations / Signups) * 100", delta_color="off")
    s7.metric("5. Acad Calendar", f"{dept_acad_cal_cov:.1f}%", f"Metric: Logged >15 days prior", delta_color="off")
    s8.metric("2. Avg CARES Util", f"{dept_cares_util:.1f}%", f"Metric: Tests conducted / Packs", delta_color="off")

    st.divider()
    s9, s10 = st.columns(2)
    dept_kdm_grade = "DE" if dept_kdm_cov >= 60 else "EE" if dept_kdm_cov >= 40 else "ME" if dept_kdm_cov >= 20 else "NI"
    s9.metric("12. Avg KDM Grade", dept_kdm_grade, f"DE ≥60% | EE 40-60% | ME 20-40% | NI <20%", delta_color="off")
    s10.metric("13. Avg CRM MOM Word Count", f"{dept_avg_mom:.1f} words", "Averaged across all Detailed CRM Logs", delta_color="off")

    st.divider()
    
    st.subheader("📝 MOM (Minutes of Meeting) Word Count Analysis")
    if not dept_det_crm.empty:
        mom_stats = dept_det_crm.groupby('ACAD').agg(
            Total_Logs=('MOM_Word_Count', 'count'),
            Avg_Word_Count=('MOM_Word_Count', 'mean')
        ).reset_index()
        mom_stats.rename(columns={'Total_Logs': 'Total MOM Logs', 'Avg_Word_Count': 'Avg MOM Word Count'}, inplace=True)
        
        mom_gt_25_counts = dept_det_crm[dept_det_crm['MOM_Word_Count'] > 25].groupby('ACAD').size().reset_index(name='MOMs > 25 Words')
        mom_gt_100_counts = dept_det_crm[dept_det_crm['MOM_Word_Count'] > 100].groupby('ACAD').size().reset_index(name='MOMs > 100 Words')
        mom_multiple = mom_gt_25_counts[mom_gt_25_counts['MOMs > 25 Words'] > 1]
        
        col_mom1, col_mom2, col_mom3 = st.columns(3)
        with col_mom1:
            st.markdown("**Average MOM & Total Logs per ACAD**")
            st.dataframe(mom_stats.style.format({'Avg MOM Word Count': '{:.1f}'}), use_container_width=True, hide_index=True)
        with col_mom2:
            st.markdown("**ACADs with Multiple (>1) MOMs > 25 Words**")
            if not mom_multiple.empty:
                st.dataframe(mom_multiple, use_container_width=True, hide_index=True)
            else:
                st.info("No ACADs have multiple MOMs exceeding 25 words.")
        with col_mom3:
            st.markdown("**ACADs with MOMs Exceeding 100 Words**")
            if not mom_gt_100_counts.empty:
                st.dataframe(mom_gt_100_counts, use_container_width=True, hide_index=True)
            else:
                st.info("No ACADs have MOMs exceeding 100 words.")

    st.divider()

    st.subheader("🚨 Metrics 10 & 11: Department-Wide Zero Utilization (Remedy Required)")
    dept_ms_math = ms_math[ms_math['ACAD'].isin(all_acads)] if not ms_math.empty else pd.DataFrame()
    dept_ms_eng = ms_eng[ms_eng['ACAD'].isin(all_acads)] if not ms_eng.empty else pd.DataFrame()
    dept_asset = asset[asset['ACAD'].isin(all_acads)] if not asset.empty else pd.DataFrame()
    
    zero_cares_dept = dept_cares[dept_cares['Utilization (%)'] == 0] if not dept_cares.empty else pd.DataFrame()
    zero_ms_dept = dept_ms_math[dept_ms_math['Login %'] == 0] if not dept_ms_math.empty else pd.DataFrame()
    zero_asset_dept = dept_asset[dept_asset['Overall Score (%)'] == 0] if not dept_asset.empty else pd.DataFrame()
    
    r1, r2, r3 = st.columns(3)
    with r1:
        st.error(f"**10. CARES (0% Util)**: {len(zero_cares_dept)} Schools")
        if not zero_cares_dept.empty: st.dataframe(zero_cares_dept[['ACAD', 'School Name', 'Utilization (%)']], hide_index=True)
    with r2:
        st.error(f"**10. MS Math (0% Logins)**: {len(zero_ms_dept)} Schools")
        if not zero_ms_dept.empty: st.dataframe(zero_ms_dept[['ACAD', 'schoolName', 'Login %']], hide_index=True)
    with r3:
        st.error(f"**11. ASSET (0% Score)**: {len(zero_asset_dept)} Schools")
        if not zero_asset_dept.empty: st.dataframe(zero_asset_dept[['ACAD', 'School Name', 'Overall Score (%)']], hide_index=True)

    st.divider()

    st.subheader("📊 Consolidated ACAD Master Performance Table")
    master_summary = pd.DataFrame({'ACAD': all_acads})
    
    if not feedback.empty: master_summary = master_summary.merge(feedback.groupby('ACAD')['Overall Rating'].mean().reset_index().rename(columns={'Overall Rating': 'Avg Feedback'}), on='ACAD', how='left')
    if not crm.empty: 
        crm_agg = crm.groupby('ACAD').agg({'Meetings': 'sum', 'Average Rating': 'mean'}).reset_index().rename(columns={'Meetings': 'Total Meetings', 'Average Rating': 'Avg NPS'})
        master_summary = master_summary.merge(crm_agg, on='ACAD', how='left')
    if not kdm.empty: master_summary = master_summary.merge(kdm.groupby('ACAD')['% Coverage'].mean().reset_index().rename(columns={'% Coverage': 'Avg KDM %'}), on='ACAD', how='left')
    if not onboarding.empty: master_summary = master_summary.merge(onboarding.groupby('ACAD')['% Coverage'].mean().reset_index().rename(columns={'% Coverage': 'Onboarding %'}), on='ACAD', how='left')
    if not acad_cal.empty: master_summary = master_summary.merge(acad_cal.groupby('ACAD')['Percentage Compliant'].mean().reset_index().rename(columns={'Percentage Compliant': 'Acad Cal %'}), on='ACAD', how='left')
    if not cares_schools.empty: master_summary = master_summary.merge(cares_schools.groupby('ACAD')['Utilization (%)'].mean().reset_index().rename(columns={'Utilization (%)': 'CARES %'}), on='ACAD', how='left')
    
    if not ms_math.empty: master_summary = master_summary.merge(ms_math.groupby('ACAD')['Login %'].mean().reset_index().rename(columns={'Login %': 'MS Math %'}), on='ACAD', how='left')
    if not ms_eng.empty: master_summary = master_summary.merge(ms_eng.groupby('ACAD')['Login %'].mean().reset_index().rename(columns={'Login %': 'MS Eng %'}), on='ACAD', how='left')
    
    if not asset.empty: master_summary = master_summary.merge(asset.groupby('ACAD')['Overall Score (%)'].mean().reset_index().rename(columns={'Overall Score (%)': 'ASSET %'}), on='ACAD', how='left')
    
    if not filtered_df.empty:
        base_agg = filtered_df.groupby('ACAD').size().reset_index(name='Total 2025 Schools')
        master_summary = master_summary.merge(base_agg, on='ACAD', how='left')

    master_summary.fillna(0, inplace=True)
    format_dict = {'Avg Feedback': '{:.2f}', 'Avg NPS': '{:.2f}', 'Avg KDM %': '{:.1f}%', 'Onboarding %': '{:.1f}%', 'Acad Cal %': '{:.1f}%', 'CARES %': '{:.1f}%', 'MS Math %': '{:.1f}%', 'MS Eng %': '{:.1f}%', 'ASSET %': '{:.1f}%'}
    st.dataframe(master_summary.style.format(format_dict), use_container_width=True, hide_index=True)

    # NEW FEATURE: DOWNLOAD DEPT SCORECARD
    mapping_cols = [c for c in ['School No', 'School Name', 'ACAD', 'Division', 'Zone', 'State', 'City', 'Total Order Value (Exclusive GST)', 'ASSET Revenue', 'CARES Revenue', 'Mindspark Revenue'] if c in filtered_df.columns]
    mapping_df = filtered_df[mapping_cols].drop_duplicates() if not filtered_df.empty else pd.DataFrame()

    dept_raw_export = {
        'School_Mapping_Rev': mapping_df,
        'Feedback': dept_fb,
        'CRM': dept_crm,
        'KDM': dept_kdm,
        'CARES': dept_cares,
        'ASSET': dept_asset,
        'MS_Math': dept_ms_math,
        'MS_Eng': dept_ms_eng,
        'Onboarding': dept_onb,
        'Acad_Cal': dept_acad_cal,
        '2025_Fin': filtered_df,
        'Detailed_CRM_MOM': dept_det_crm
    }
    
    dept_metrics_dict = {'cares_grade': dept_cares_grade_eval}
    
    st.download_button(
        label="📥 Download Department 13-Point Scorecard Data (Excel)",
        data=convert_dept_to_excel(selected_division, selected_zone, dept_metrics_dict, master_summary, dept_raw_export),
        file_name=f"Dept_Scorecard_{selected_division}_{selected_zone}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        type="primary"
    )

    st.divider()
    
    st.header("🗂️ Hierarchy & Allocation Breakdown (Division -> Zone -> ACAD -> School)")
    if not dept_fin.empty:
        for c in ['Total Order Value (Exclusive GST)', 'ASSET Revenue', 'CARES Revenue', 'Mindspark Revenue']:
            if c in dept_fin.columns:
                dept_fin[c] = pd.to_numeric(dept_fin[c], errors='coerce').fillna(0)

        cols_to_show = [c for c in ['Division', 'Zone', 'ACAD', 'School No', 'School Name', 'Total Order Value (Exclusive GST)', 'ASSET Revenue', 'CARES Revenue', 'Mindspark Revenue'] if c in dept_fin.columns]
        hierarchy_df = dept_fin[cols_to_show].sort_values(by=[c for c in ['Division', 'Zone', 'ACAD'] if c in cols_to_show])
        
        h1, h2 = st.columns([1, 2])
        with h1:
            st.markdown("**Summary by Zone**")
            zone_summary = dept_fin.groupby(['Division', 'Zone']).agg(
                Total_ACADs=('ACAD', 'nunique'),
                Total_Schools=('School No', 'nunique')
            ).reset_index()
            if 'Total Order Value (Exclusive GST)' in dept_fin.columns:
                rev_sum = dept_fin.groupby(['Division', 'Zone'])['Total Order Value (Exclusive GST)'].sum().reset_index(name='Total_Revenue')
                zone_summary = zone_summary.merge(rev_sum, on=['Division', 'Zone'], how='left')
                st.dataframe(zone_summary.style.format({'Total_Revenue': '{:,.2f}'}), use_container_width=True, hide_index=True)
            else:
                st.dataframe(zone_summary, use_container_width=True, hide_index=True)
                
        with h2:
            st.markdown("**Full School Allocation & Revenue List**")
            format_dict_hier = {c: '{:,.2f}' for c in cols_to_show if 'Revenue' in c or 'Value' in c}
            st.dataframe(hierarchy_df.style.format(format_dict_hier), use_container_width=True, hide_index=True)
    else:
        st.info("No hierarchy data available for the current selection.")

    st.divider()
    st.header("🏫 Specific DPS Schools Tracking & Detailed Logs")
    st.markdown(f"Fetching logs, feedback, and visits specifically for these School Codes: `{', '.join(DPS_CODES)}`")
    
    dps_names = filtered_df[filtered_df['School No'].isin(DPS_CODES)]['School Name'].unique().tolist() if not filtered_df.empty else []
    
    tab1, tab2 = st.tabs(["DPS Qualitative Feedback", "DPS Calendar Visit Logs"])
    with tab1:
        dps_fb = det_feedback[det_feedback['School Name'].isin(dps_names)] if not det_feedback.empty else pd.DataFrame()
        if not dps_fb.empty: st.dataframe(dps_fb[['ACAD', 'School Name', 'Products', 'NPS Rating (1-10)', 'Takeaways', 'Suggestions']], use_container_width=True, hide_index=True)
        else: st.info("No qualitative feedback logged yet for these specific DPS schools.")
    with tab2:
        dps_cal = det_acad_cal[det_acad_cal['School Name'].isin(dps_names)] if not det_acad_cal.empty else pd.DataFrame()
        if not dps_cal.empty: st.dataframe(dps_cal[['ACAD', 'School Name', 'Session Date', 'Compliance Status']], use_container_width=True, hide_index=True)
        else: st.info("No visit logs found for these specific DPS schools.")


# ==========================================
# 4. PAGE: RETENTION & REVENUE (GOAL 1)
# ==========================================
elif page == "💰 Goal 1: Retention & Revenue":
    st.title(f"💰 Goal 1: Retention & Revenue")
    st.markdown(f"**Viewing:** Division: `{selected_division}` | Zone: `{selected_zone}`")
    
    dept_fin = filtered_df if not filtered_df.empty else pd.DataFrame()
    
    if not dept_fin.empty and 'ACAD' in dept_fin.columns:
        summary_data = []
        dept_fin['Total Order Value (Exclusive GST)'] = pd.to_numeric(dept_fin.get('Total Order Value (Exclusive GST)', 0), errors='coerce').fillna(0)
        if not fin_2027.empty: fin_2027['Total Order Value (Exclusive GST)'] = pd.to_numeric(fin_2027.get('Total Order Value (Exclusive GST)', 0), errors='coerce').fillna(0)
        
        for acad in dept_fin['ACAD'].dropna().unique():
            acad_2025 = dept_fin[dept_fin['ACAD'] == acad]
            allocated = len(acad_2025)
            retained = acad_2025['Is_Retained'].sum()
            retained_schools = acad_2025[acad_2025['Is_Retained']]['School No'].unique()
            
            base_rev = acad_2025['Total Order Value (Exclusive GST)'].sum()
            lost_rev = acad_2025[~acad_2025['Is_Retained']]['Total Order Value (Exclusive GST)'].sum()
            retained_rev = fin_2027[fin_2027['School No'].isin(retained_schools)]['Total Order Value (Exclusive GST)'].sum() if not fin_2027.empty else 0
            
            summary_data.append({
                "ACAD": acad, "Allocated (2025)": allocated, "Retained (2027)": retained,
                "Retention %": round((retained/allocated*100) if allocated>0 else 0, 1),
                "Base Rev 2025 (₹)": base_rev, "Retained Rev 2027 (₹)": retained_rev, "Lost Rev (₹)": lost_rev
            })
            
        st.dataframe(pd.DataFrame(summary_data).style.format({"Base Rev 2025 (₹)": "{:,.2f}", "Retained Rev 2027 (₹)": "{:,.2f}", "Lost Rev (₹)": "{:,.2f}"}), use_container_width=True, hide_index=True)


# ==========================================
# 5. PAGE: PRODUCT UTILISATION & GOAL LOGIC
# ==========================================
elif page == "📊 Product Utilisation & Goal Logic":
    st.title("📊 Product Utilisation & Goal Logic Matrix")
    st.markdown(f"Detailed view of product usage across `{selected_division}` - `{selected_zone}` and a walkthrough of the KPA-2026 methodology.")

    tab1, tab2 = st.tabs(["📈 Product Utilisation (CARES, MS, ASSET)", "📖 Goal Calculation & KRA Walkthrough"])

    with tab1:
        st.header("Product Utilisation Raw Datasets")
        
        zone_cares = cares_schools[cares_schools['ACAD'].isin(all_acads)] if not cares_schools.empty else pd.DataFrame()
        zone_ms = ms_math[ms_math['ACAD'].isin(all_acads)] if not ms_math.empty else pd.DataFrame()
        zone_ms_eng = ms_eng[ms_eng['ACAD'].isin(all_acads)] if not ms_eng.empty else pd.DataFrame()
        zone_asset = asset[asset['ACAD'].isin(all_acads)] if not asset.empty else pd.DataFrame()

        c1, c2, c3 = st.columns(3)
        c1.metric("CARES Avg Gap", f"{zone_cares['Gap'].mean():.1f}%" if not zone_cares.empty and 'Gap' in zone_cares.columns else "0%")
        c2.metric("MS Math Avg Zero Usage", f"{zone_ms['Zero Usage %'].mean():.1f}%" if not zone_ms.empty and 'Zero Usage %' in zone_ms.columns else "0%")
        c3.metric("ASSET Avg Compliance", f"{zone_asset['Overall Score (%)'].mean():.1f}%" if not zone_asset.empty else "0%")

        st.divider()

        if not zone_cares.empty:
            st.subheader("1. CARES Test Utilization & Gap Analysis")
            st.dataframe(zone_cares.style.apply(highlight_cares, axis=1), use_container_width=True, hide_index=True)

        if not zone_ms.empty:
            st.subheader("2. Mindspark Math Utilization (Zero Usage Tracked)")
            st.dataframe(zone_ms.style.apply(highlight_ms, axis=1), use_container_width=True, hide_index=True)

        if not zone_ms_eng.empty:
            st.subheader("3. Mindspark English Utilization (Zero Usage Tracked)")
            st.dataframe(zone_ms_eng.style.apply(highlight_ms, axis=1), use_container_width=True, hide_index=True)

        if not zone_asset.empty:
            st.subheader("4. ASSET Compliance Scores")
            st.dataframe(zone_asset.style.apply(highlight_asset, axis=1), use_container_width=True, hide_index=True)

    with tab2:
        st.header("📖 KPA-2026 Goal Calculation Walkthrough")
        st.markdown("Below is the exact framework and logical formulas used to calculate grades in this dashboard.")

        st.subheader("Goal 1: Retention & Revenue (Weight: 35%)")
        st.markdown("""
        * **Calculation:** Tracked via cross-referencing `School No` in the 2025 base allocation file against the 2027 renewal file. 
        * **Exemption:** Schools containing 'Winter' in their ASSET Round data are exempted from the 30th May timeline.
        * **Grading:** * **DE:** ≥ 98%
            * **EE:** 95% - 98%
            * **ME:** 90% - 95%
            * **NI:** < 90%
        """)

        st.subheader("Goal 2: Effective Delivery Practices (Weight: 30%)")
        st.markdown("""
        * **Meeting Targets:** Dynamically set at `Allocated Schools * 4`. 
        * **CRM Update SLA:** Difference = `Modified Time - From Time (Hours)`.
        * **KDM Coverage:** * **DE:** ≥ 60%
            * **EE:** 40% - 60%
            * **ME:** 20% - 40%
            * **NI:** < 20%
        * **Academic Calendar:** * **DE:** ≥ 70%
            * **EE:** 60% - 70%
            * **ME:** 50% - 60%
            * **NI:** < 50%
        """)

        st.subheader("Goal 3: Product Utilisation (Weight: 15%)")
        st.markdown("""
        * **Mindspark Utilization:** Uses Login Average across Math and English.
            * **DE:** ≥ 90%
            * **EE:** 80% - 90%
            * **ME:** 70% - 80%
            * **NI:** < 70%
        * **ASSET Utilization:** Based on Academic Calendar and CRM Event Stage.
            * **DE:** ≥ 90%
            * **EE:** 85% - 90%
            * **ME:** 80% - 85%
            * **NI:** < 80%
        """)

        st.subheader("Goal 4: Learning (Weight: 20%)")
        st.markdown("""
        * **IDP Grade Logic:** Mapped to the ACAD's success in hitting the Meeting Target (Schools * 4).
            * **DE:** ≥ 100% Target Met
            * **EE:** 90% - 100% Target Met
            * **ME:** 80% - 90% Target Met
            * **NI:** < 80% Target Met
        """)


# ==========================================
# 6. PAGE: INDIVIDUAL DASHBOARD & EXPORT
# ==========================================
elif page == "👤 Individual Dashboard & Goal Export":
    selected_acad = st.sidebar.selectbox("Select Academic Consultant", all_acads)
    st.title(f"👤 Dashboard: {selected_acad}")
    
    # Filter all dataframes
    fb_ind = feedback[feedback['ACAD'] == selected_acad]
    crm_ind = crm[crm['ACAD'] == selected_acad]
    kdm_ind = kdm[kdm['ACAD'] == selected_acad]
    acad_cal_ind = acad_cal[acad_cal['ACAD'] == selected_acad]
    onboard_ind = onboarding[onboarding['ACAD'] == selected_acad]
    cares_ind = cares_schools[cares_schools['ACAD'] == selected_acad]
    asset_ind = asset[asset['ACAD'] == selected_acad]
    ms_math_ind = ms_math[ms_math['ACAD'] == selected_acad]
    ms_eng_ind = ms_eng[ms_eng['ACAD'] == selected_acad]
    fin_2025_ind = filtered_df[filtered_df['ACAD'] == selected_acad] if not filtered_df.empty else pd.DataFrame()
    det_acad_ind = det_acad_cal[det_acad_cal['ACAD'] == selected_acad]
    det_kdm_ind = det_kdm[det_kdm['School Name'].isin(kdm_ind['School Name'])] if 'School Name' in kdm_ind.columns else pd.DataFrame()
    det_onb_ind = det_onboard[det_onboard['ACAD'] == selected_acad]
    
    det_fb_ind = det_feedback[det_feedback['ACAD'] == selected_acad] if not det_feedback.empty else pd.DataFrame()
    
    ind_det_crm = pd.DataFrame()
    if not det_crm.empty and 'MOM_Word_Count' in det_crm.columns:
        ind_det_crm = det_crm[det_crm['ACAD'] == selected_acad]
    
    allocated_25 = len(fin_2025_ind) if not fin_2025_ind.empty else 0
    retained_27 = fin_2025_ind['Is_Retained'].sum() if not fin_2025_ind.empty else 0
    retained_rev_amt = 0
    if not fin_2025_ind.empty and not fin_2027.empty:
        ret_schools = fin_2025_ind[fin_2025_ind['Is_Retained']]['School No'].unique()
        retained_rev_amt = fin_2027[fin_2027['School No'].isin(ret_schools)]['Total Order Value (Exclusive GST)'].sum()
        
    pct_logged_48h = (len(det_acad_ind[det_acad_ind['Log_Delay_Hours'] <= 48]) / len(det_acad_ind) * 100) if not det_acad_ind.empty and len(det_acad_ind) > 0 else 0
    
    target_meetings = allocated_25 * 4
    crm_tot = crm_ind['Meetings'].sum() if not crm_ind.empty else 0
    meet_pct = (crm_tot / target_meetings * 100) if target_meetings > 0 else 0
    
    idp_grade = "DE" if meet_pct >= 100 else "EE" if meet_pct >= 90 else "ME" if meet_pct >= 80 else "NI"
    asset_comp = (len(asset_ind[asset_ind['Overall Score (%)'] == 100]) / len(asset_ind) * 100) if not asset_ind.empty and len(asset_ind) > 0 else 0
    ind_avg_mom = ind_det_crm['MOM_Word_Count'].mean() if not ind_det_crm.empty else 0

    ms_math_mean = ms_math_ind['Login %'].mean() if not ms_math_ind.empty else np.nan
    ms_eng_mean = ms_eng_ind['Login %'].mean() if not ms_eng_ind.empty else np.nan
    ms_avg = np.nanmean([ms_math_mean, ms_eng_mean])
    ms_avg = 0 if np.isnan(ms_avg) else ms_avg
    
    cares_grade_eval = "DE" if cares_ind['Gap'].mean() > 10 else "EE" if cares_ind['Gap'].mean() >= 1 else "ME" if cares_ind['Gap'].mean() >= -1 else "NI" if not cares_ind.empty and 'Gap' in cares_ind.columns else "NI"

    calc_metrics = {
        'fb': fb_ind['Overall Rating'].values[0] if not fb_ind.empty else 0,
        'crm_total': crm_tot,
        'kdm': kdm_ind['% Coverage'].mean() if not kdm_ind.empty else 0,
        'onboarding': onboard_ind['% Coverage'].mean() if not onboard_ind.empty else 0,
        'acad_cal': acad_cal_ind['Percentage Compliant'].mean() if not acad_cal_ind.empty else 0,
        'cares': cares_ind['Utilization (%)'].mean() if not cares_ind.empty else 0,
        'cares_gap': cares_ind['Gap'].mean() if not cares_ind.empty and 'Gap' in cares_ind.columns else 0,
        'ms': ms_avg,
        'asset': asset_ind['Overall Score (%)'].mean() if not asset_ind.empty else 0,
        'asset_comp': asset_comp,
        'retention_rate': (retained_27 / allocated_25 * 100) if allocated_25 > 0 else 0,
        'retained_rev': retained_rev_amt,
        'sla_48': pct_logged_48h,
        'target_meetings': target_meetings,
        'meet_pct': meet_pct,
        'idp_grade': idp_grade,
        'avg_mom': ind_avg_mom
    }

    raw_export_dfs = {'Feedback': fb_ind, 'Qual_Feedback': det_fb_ind, 'CRM': crm_ind, 'KDM': kdm_ind, 'CARES': cares_ind, 'ASSET': asset_ind, 'MS_Math': ms_math_ind, 'MS_Eng': ms_eng_ind, 'Onboarding': onboard_ind, 'Acad_Cal': acad_cal_ind, '2025_Fin': fin_2025_ind}
    if not ind_det_crm.empty: raw_export_dfs['Detailed_CRM_MOM'] = ind_det_crm
    
    st.download_button(f"📥 Download {selected_acad} LIVE Dynamic Goal Sheet", convert_acad_to_excel(selected_acad, calc_metrics, raw_export_dfs), f"KPA_2026_{selected_acad}.xlsx", type="primary")

    st.divider()

    st.header("📋 13-Point Executive Scorecard")
    s1, s2, s3, s4 = st.columns(4)
    s1.metric("1. Avg Feedback", f"{calc_metrics['fb']:.2f} / 10", f"Total Responses: {fb_ind['Responses'].values[0] if not fb_ind.empty else 0}", delta_color="off")
    s2.metric("9. Avg Session (NPS)", f"{crm_ind['Average Rating'].mean() if not crm_ind.empty else 0:.2f} / 5", "From CRM System", delta_color="off")
    s3.metric("7. Total Schools", allocated_25, "From 2025 Financials", delta_color="off")
    s4.metric("6. Meetings", f"{calc_metrics['crm_total']}", f"Target: {target_meetings} ({meet_pct:.1f}%)", delta_color="off")

    st.divider()
    s5, s6, s7, s8 = st.columns(4)
    s5.metric("3. KDM Coverage %", f"{calc_metrics['kdm']:.1f}%", delta_color="off")
    s6.metric("4. Onboarding %", f"{calc_metrics['onboarding']:.1f}%", delta_color="off")
    
    ind_acad_grade = "DE" if calc_metrics['acad_cal'] >= 70 else "EE" if calc_metrics['acad_cal'] >= 60 else "ME" if calc_metrics['acad_cal'] >= 50 else "NI"
    s7.metric("5. Acad Calendar %", f"{calc_metrics['acad_cal']:.1f}%", f"Grade: [{ind_acad_grade}]", delta_color="off")
    s8.metric("2. CARES Util %", f"{calc_metrics['cares']:.1f}%", delta_color="off")

    st.divider()
    s9, s10 = st.columns(2)
    ind_kdm_grade = "DE" if calc_metrics['kdm'] >= 60 else "EE" if calc_metrics['kdm'] >= 40 else "ME" if calc_metrics['kdm'] >= 20 else "NI"
    s9.metric("12. KDM Grade", ind_kdm_grade, f"DE ≥60% | EE 40-60% | ME 20-40% | NI <20%", delta_color="off")
    s10.metric("13. Avg CRM MOM Word Count", f"{ind_avg_mom:.1f} words", "Averaged across Detailed CRM Logs", delta_color="off")

    st.divider()
    
    st.subheader("📝 MOM (Minutes of Meeting) Analysis")
    if not ind_det_crm.empty:
        total_logs = len(ind_det_crm)
        gt_25_count = len(ind_det_crm[ind_det_crm['MOM_Word_Count'] > 25])
        gt_100_count = len(ind_det_crm[ind_det_crm['MOM_Word_Count'] > 100])
        
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Total MOM Logs Available", f"{total_logs}")
        m2.metric("Average MOM Word Count", f"{ind_avg_mom:.1f} words")
        m3.metric("MOMs > 25 Words", f"{gt_25_count} entries")
        m4.metric("MOMs > 100 Words", f"{gt_100_count} entries")
        
        with st.expander("View Detailed CRM MOM Logs"):
            st.dataframe(ind_det_crm[['ACAD', 'Customer Account Name', 'Description', 'MOM_Word_Count']], use_container_width=True, hide_index=True)

    st.divider()
    
    st.subheader("🚨 Metrics 10 & 11: Zero Utilization (Immediate Remedy)")
    zero_cares_ind = cares_ind[cares_ind['Utilization (%)'] == 0]
    zero_ms_math_ind = ms_math_ind[ms_math_ind['Login %'] == 0]
    zero_ms_eng_ind = ms_eng_ind[ms_eng_ind['Login %'] == 0]
    zero_asset_ind = asset_ind[asset_ind['Overall Score (%)'] == 0]
    
    r1, r2, r3, r4 = st.columns(4)
    with r1:
        st.error(f"**CARES (0% Util)**: {len(zero_cares_ind)} Schools")
        st.dataframe(zero_cares_ind[['School Name', 'Utilization (%)']], hide_index=True)
    with r2:
        st.error(f"**MS Math (0% Logins)**: {len(zero_ms_math_ind)} Schools")
        st.dataframe(zero_ms_math_ind[['schoolName', 'Login %']], hide_index=True)
    with r3:
        st.error(f"**MS Eng (0% Logins)**: {len(zero_ms_eng_ind)} Schools")
        st.dataframe(zero_ms_eng_ind[['schoolName', 'Login %']], hide_index=True)
    with r4:
        st.error(f"**ASSET (0% Scheduled)**: {len(zero_asset_ind)} Schools")
        st.dataframe(zero_asset_ind[['School Name', 'Overall Score (%)']], hide_index=True)

    st.divider()
    
    st.header("📝 Qualitative Session Feedback & Goal Analytics")
    st.markdown("**Goal 2: CRM Update SLA (<48 hours)**")
    st.metric("% Logged within 48h", f"{pct_logged_48h:.1f}%")
    if not det_acad_ind.empty: st.dataframe(det_acad_ind[['School Name', 'Session Date', 'Date Updated', 'Log_Delay_Hours']].style.apply(highlight_sla, axis=1), hide_index=True)
    
    if not det_fb_ind.empty:
        st.markdown("**Raw Qualitative Teacher Takeaways**")
        st.dataframe(det_fb_ind[['School Name', 'Products', 'NPS Rating (1-10)', 'Takeaways', 'Suggestions']], use_container_width=True, hide_index=True)

    st.divider()
    st.header("🏫 Specific DPS Schools Tracking & Detailed Logs")
    st.markdown(f"Fetching logs and feedback specifically for these School Codes: `{', '.join(DPS_CODES)}`")
    dps_names_ind = fin_2025_ind[fin_2025_ind['School No'].isin(DPS_CODES)]['School Name'].unique().tolist() if not fin_2025_ind.empty else []
    
    tab_fb, tab_cal = st.tabs(["DPS Qualitative Feedback", "DPS Calendar Visit Logs"])
    with tab_fb:
        dps_fb_ind = det_fb_ind[det_fb_ind['School Name'].isin(dps_names_ind)] if not det_fb_ind.empty else pd.DataFrame()
        if not dps_fb_ind.empty: st.dataframe(dps_fb_ind[['School Name', 'Products', 'NPS Rating (1-10)', 'Takeaways', 'Suggestions']], use_container_width=True, hide_index=True)
        else: st.info("No qualitative feedback logged yet for these specific DPS schools.")
    with tab_cal:
        dps_cal_ind = det_acad_ind[det_acad_ind['School Name'].isin(dps_names_ind)] if not det_acad_ind.empty else pd.DataFrame()
        if not dps_cal_ind.empty: st.dataframe(dps_cal_ind[['School Name', 'Session Date', 'Compliance Status']], use_container_width=True, hide_index=True)
        else: st.info("No visit logs found for these specific DPS schools.")

    st.divider()
    st.header("🔍 Granular Raw Data Tables (Red = Needs Improvement)")
    
    if not cares_ind.empty:
        st.markdown("**CARES Utilization Raw Data**")
        st.dataframe(cares_ind.style.apply(highlight_cares, axis=1), use_container_width=True, hide_index=True)
    if not asset_ind.empty:
        st.markdown("**ASSET Utilization Raw Data**")
        st.dataframe(asset_ind.style.apply(highlight_asset, axis=1), use_container_width=True, hide_index=True)
    if not ms_math_ind.empty:
        st.markdown("**Mindspark Math Raw Data**")
        st.dataframe(ms_math_ind.style.apply(highlight_ms, axis=1), use_container_width=True, hide_index=True)
    if not ms_eng_ind.empty:
        st.markdown("**Mindspark English Raw Data**")
        st.dataframe(ms_eng_ind.style.apply(highlight_ms, axis=1), use_container_width=True, hide_index=True)
    if not kdm_ind.empty:
        st.markdown("**KDM Coverage Raw Data**")
        st.dataframe(kdm_ind.style.apply(highlight_kdm, axis=1), use_container_width=True, hide_index=True)
    if not crm_ind.empty:
        st.markdown("**CRM Log Raw Data**")
        st.dataframe(crm_ind, use_container_width=True, hide_index=True)
    if not det_acad_ind.empty:
        st.markdown("**Detailed Academic Calendar Visits**")
        st.dataframe(det_acad_ind, use_container_width=True, hide_index=True)
    if not det_onb_ind.empty:
        st.markdown("**Detailed Orientations/Onboarding**")
        st.dataframe(det_onb_ind, use_container_width=True, hide_index=True)

# ==========================================
# 7. PAGE: ACAD NAME DIAGNOSTICS
# ==========================================
elif page == "🛠️ ACAD Name Diagnostics":
    st.title("🛠️ ACAD Name Diagnostics")
    st.markdown("Excel occasionally crashes if an ACAD name in the raw data contains an invalid character (e.g., `\\`, `/`, `*`, `?`, `:`, `[`, `]`). Below is a master list of all unique ACAD names found across all loaded CSV files to help you identify and clean messy data.")
    
    data_sources = {
        "Academic Calendar": acad_cal,
        "Detailed Acad Cal": det_acad_cal,
        "KDM": kdm,
        "Detailed KDM": det_kdm,
        "Onboarding": onboarding,
        "Detailed Onboarding": det_onboard,
        "CRM": crm,
        "Feedback": feedback,
        "CARES Schools": cares_schools,
        "ASSET": asset,
        "MS Math": ms_math,
        "MS English": ms_eng,
        "Fin 2025": fin_2025,
        "Fin 2027": fin_2027,
        "Detailed Feedback": det_feedback,
        "Detailed CRM MOM": det_crm
    }
    
    mapping_data = []
    
    for src_name, df in data_sources.items():
        if not df.empty and 'ACAD' in df.columns:
            unique_acads = df['ACAD'].dropna().unique()
            for a in unique_acads:
                mapping_data.append({"ACAD Name": str(a), "Found In File": src_name})
                
    if mapping_data:
        diag_df = pd.DataFrame(mapping_data)
        
        # Identify bad characters
        bad_chars = r'[\\/*?:\[\]]'
        diag_df['Has Invalid Excel Char'] = diag_df['ACAD Name'].str.contains(bad_chars, regex=True)
        
        # Display the ones causing problems first
        bad_names_df = diag_df[diag_df['Has Invalid Excel Char'] == True]
        if not bad_names_df.empty:
            st.error(f"⚠️ Found {len(bad_names_df)} ACAD name(s) containing characters that crash Excel sheet creation.")
            st.dataframe(bad_names_df, use_container_width=True, hide_index=True)
        else:
            st.success("✅ No invalid Excel characters found in ACAD names.")
            
        st.divider()
        st.subheader("All Parsed ACAD Names by File")
        
        grouped_diag = diag_df.groupby('ACAD Name')['Found In File'].apply(lambda x: ', '.join(x.unique())).reset_index()
        st.dataframe(grouped_diag, use_container_width=True, hide_index=True)
    else:
        st.info("No ACAD names found in the loaded data.")