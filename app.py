import streamlit as st
import pandas as pd
import plotly.express as px
import io
import warnings
import os

warnings.filterwarnings('ignore')

# ==========================================
# 1. PAGE CONFIGURATION & DATA LOADING
# ==========================================
st.set_page_config(page_title="ACAD Master Dashboard", layout="wide", initial_sidebar_state="expanded")

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
    except Exception as e:
        st.error(f"Error loading Operational CSVs. Details: {e}")
        st.stop()
    
    # 2. Financial & Risk Data
    def load_smart_csv(primary_name, fallback_name):
        if os.path.exists(primary_name): return pd.read_csv(primary_name)
        elif os.path.exists(fallback_name): return pd.read_csv(fallback_name)
        return pd.DataFrame()

    fin_2025 = load_smart_csv('Supporting data(2)-13th March 2026 (8)_2025.csv', 'Supporting data(2)-13th March 2026 (8).xlsx - 2025.csv')
    fin_2027 = load_smart_csv('Supporting data(2)-13th March 2026 (8)_2027.csv', 'Supporting data(2)-13th March 2026 (8).xlsx - 2027.csv')
    drop_risk = load_smart_csv('Supporting data(2)-13th March 2026 (8)_Drop & Risk Analysis.csv', 'Supporting data(2)-13th March 2026 (8).xlsx - Drop & Risk Analysis.csv')
        
    for df in [fin_2025, fin_2027, drop_risk]:
        if 'ACAD Name' in df.columns: df.rename(columns={'ACAD Name': 'ACAD'}, inplace=True)
        if 'CRM Acad Consultant' in df.columns and 'ACAD' not in df.columns: df.rename(columns={'CRM Acad Consultant': 'ACAD'}, inplace=True)
            
    if 'School No' in fin_2025.columns: fin_2025['School No'] = fin_2025['School No'].astype(str).str.strip().str.replace('.0', '', regex=False)
    if 'School No' in fin_2027.columns: fin_2027['School No'] = fin_2027['School No'].astype(str).str.strip().str.replace('.0', '', regex=False)

    if 'Host Name' in crm.columns: crm.rename(columns={'Host Name': 'ACAD'}, inplace=True)
    if 'Acad Name' in feedback.columns: feedback.rename(columns={'Acad Name': 'ACAD'}, inplace=True)
    
    kdm['% Coverage'] = pd.to_numeric(kdm['% Coverage'].replace({'Unknown': '0'}), errors='coerce').fillna(0)
    onboarding['% Coverage'] = pd.to_numeric(onboarding['% Coverage'].replace({'Unknown': '0'}), errors='coerce').fillna(0)
    ms_math['Login %'] = pd.to_numeric(ms_math['Login %'], errors='coerce').fillna(0)
    
    return acad_cal, det_acad_cal, kdm, det_kdm, onboarding, det_onboard, crm, feedback, cares_schools, asset, ms_math, fin_2025, fin_2027, drop_risk

acad_cal, det_acad_cal, kdm, det_kdm, onboarding, det_onboard, crm, feedback, cares_schools, asset, ms_math, fin_2025, fin_2027, drop_risk = load_data()

all_acads = pd.concat([acad_cal['ACAD'], crm['ACAD'], feedback['ACAD']]).dropna().unique()
all_acads = sorted([str(x) for x in all_acads if str(x) not in ["Unknown", "nan"]])

# Strict Retention Logic (2025 -> 2027)
if not fin_2025.empty and not fin_2027.empty and 'School No' in fin_2025.columns:
    schools_2027_list = fin_2027['School No'].dropna().unique().tolist()
    fin_2025['Is_Retained'] = fin_2025['School No'].isin(schools_2027_list)
else:
    if not fin_2025.empty: fin_2025['Is_Retained'] = False

# Highlighting Logic
def style_ni(row, condition): return ['background-color: #ffe6e6' if condition else ''] * len(row)
def highlight_cares(row): return style_ni(row, row.get('KRA Category', '') == 'NI')
def highlight_ms(row): return style_ni(row, row.get('Login %', 100) < 80)
def highlight_asset(row): return style_ni(row, row.get('Overall Score (%)', 100) < 100 and row.get('Included in Calculation', 'No') == 'Yes')
def highlight_kdm(row): return style_ni(row, row.get('% Coverage', 100) < 25)

# ==========================================
# 2. SIDEBAR & MASTER EXPORT GENERATOR
# ==========================================
st.sidebar.title("Navigation")
page = st.sidebar.radio("Select Dashboard View:", [
    "🏢 Dept 11-Point Scorecard", 
    "💰 Goal 1: Retention & Revenue", 
    "👤 Individual Dashboard & Goal Export"
])
st.sidebar.divider()

def generate_individual_goal_sheet(acad_name, metrics):
    """Generates the KPA-2026 format with actuals mapped dynamically."""
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
            "Measure aspirations as mentioned in IDP",
            "Supporting teachers in Action Research"
        ],
        "ME (Meets Expectations) Target": [
            "90% renew and 115% order value", "80% retention completed", "90% within 45 days",
            "100% completion in 48h, rating 8", "1 per quarter, 1 testimonial", "Within 30 days", "70% recorded before 15 days",
            "20% participation", "MS>=80%, ASSET 80%, CARES 100%",
            "Achieve success set as ME in IDP", "Readiness for Action Research"
        ],
        "Weightage": ["20%", "10%", "5%", "10%", "10%", "5%", "5%", "5%", "10%", "15%", "5%"],
        "Total Group Weight": ["35%", "", "", "30%", "", "", "", "15%", "", "20%", ""],
        "ACTUAL ACHIEVED (Data)": [
            f"{metrics['retention_rate']:.1f}% Retained | ₹{metrics['retained_rev']:,.0f}",
            "N/A", "N/A",
            f"Avg Rating: {metrics['fb']:.2f}/10 | Total CRM: {metrics['crm_total']}",
            f"{metrics['kdm']:.1f}% Coverage",
            f"{metrics['onboarding']:.1f}% Coverage",
            f"{metrics['acad_cal']:.1f}% Compliant",
            "N/A",
            f"CARES: {metrics['cares']:.1f}% | MS: {metrics['ms']:.1f}% | ASSET: {metrics['asset']:.1f}%",
            "Pending HR Eval", "Pending HR Eval"
        ]
    })
    return goal_df

@st.cache_data
def convert_acad_to_excel(acad_name, metrics, raw_dfs):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        goal_sheet = generate_individual_goal_sheet(acad_name, metrics)
        goal_sheet.to_excel(writer, sheet_name=f'KPA_2026_{acad_name[:15]}', index=False)
        for name, df in raw_dfs.items():
            if not df.empty: df.to_excel(writer, sheet_name=name, index=False)
    return output.getvalue()


# ==========================================
# 3. PAGE: DEPT 11-POINT SCORECARD
# ==========================================
if page == "🏢 Dept 11-Point Scorecard":
    st.title("🏢 Department 11-Point Scorecard & Master Table")
    st.markdown("**Metric Definitions:** Explicitly listing totals, averages, and the exact metric logic used.")
    
    total_acads = len(all_acads)
    total_2025_schools_dept = fin_2025['School No'].nunique() if not fin_2025.empty else 0
    
    s1, s2, s3, s4 = st.columns(4)
    fb_val = feedback['Overall Rating'].mean() if not feedback.empty else 0
    s1.metric("1. Avg Feedback", f"{fb_val:.2f} / 10", f"Metric: Avg of all survey responses", delta_color="off")
    s2.metric("9. Avg Session (NPS)", f"{crm['Average Rating'].mean() if not crm.empty else 0:.2f} / 5", "Metric: Avg CRM rating", delta_color="off")
    s3.metric("7. Total Schools", total_2025_schools_dept, "Metric: Base 2025 Allocation", delta_color="off")
    
    tot_meetings = crm['Meetings'].sum() if not crm.empty else 0
    avg_meetings = tot_meetings / total_acads if total_acads > 0 else 0
    s4.metric(f"6. Total Meetings", tot_meetings, f"Avg {avg_meetings:.1f}/person | Target: 120", delta_color="off")

    st.divider()
    s5, s6, s7, s8 = st.columns(4)
    
    s5.metric("3. Avg KDM Coverage", f"{kdm['% Coverage'].mean() if not kdm.empty else 0:.1f}%", f"Metric: (KDM Done / Alloted) * 100", delta_color="off")
    s6.metric("4. Avg Onboarding", f"{onboarding['% Coverage'].mean() if not onboarding.empty else 0:.1f}%", f"Metric: (Orientations / Signups) * 100", delta_color="off")
    s7.metric("5. Acad Calendar", f"{acad_cal['Percentage Compliant'].mean() if not acad_cal.empty else 0:.1f}%", f"Metric: Logged >15 days prior", delta_color="off")
    s8.metric("2. Avg CARES Util", f"{cares_schools['Utilization (%)'].mean() if not cares_schools.empty else 0:.1f}%", f"Metric: Tests conducted / Packs", delta_color="off")

    st.divider()
    
    # Fully Restored Master Summary Table
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
    if not asset.empty: master_summary = master_summary.merge(asset.groupby('ACAD')['Overall Score (%)'].mean().reset_index().rename(columns={'Overall Score (%)': 'ASSET %'}), on='ACAD', how='left')
    
    if not fin_2025.empty:
        base_agg = fin_2025.groupby('ACAD')['School No'].nunique().reset_index().rename(columns={'School No': 'Total 2025 Schools'})
        master_summary = master_summary.merge(base_agg, on='ACAD', how='left')

    master_summary.fillna(0, inplace=True)
    format_dict = {'Avg Feedback': '{:.2f}', 'Avg NPS': '{:.2f}', 'Avg KDM %': '{:.1f}%', 'Onboarding %': '{:.1f}%', 'Acad Cal %': '{:.1f}%', 'CARES %': '{:.1f}%', 'MS Math %': '{:.1f}%', 'ASSET %': '{:.1f}%'}
    st.dataframe(master_summary.style.format(format_dict), use_container_width=True, hide_index=True)

    # Fully Restored Raw Data Expander for Dept
    st.divider()
    with st.expander("📁 View All Raw Operational CSV Data"):
        st.markdown("**CRM Data**"); st.dataframe(crm, use_container_width=True)
        st.markdown("**Feedback Data**"); st.dataframe(feedback, use_container_width=True)
        st.markdown("**ASSET Data**"); st.dataframe(asset, use_container_width=True)
        st.markdown("**Detailed Academic Calendar**"); st.dataframe(det_acad_cal, use_container_width=True)


# ==========================================
# 4. PAGE: RETENTION & REVENUE (GOAL 1)
# ==========================================
elif page == "💰 Goal 1: Retention & Revenue":
    st.title("💰 Goal 1: Retention & Revenue")
    
    if not fin_2025.empty and 'ACAD' in fin_2025.columns:
        summary_data = []
        fin_2025['Total Order Value (Exclusive GST)'] = pd.to_numeric(fin_2025.get('Total Order Value (Exclusive GST)', 0), errors='coerce').fillna(0)
        if not fin_2027.empty: fin_2027['Total Order Value (Exclusive GST)'] = pd.to_numeric(fin_2027.get('Total Order Value (Exclusive GST)', 0), errors='coerce').fillna(0)
        
        for acad in fin_2025['ACAD'].dropna().unique():
            acad_2025 = fin_2025[fin_2025['ACAD'] == acad]
            allocated = acad_2025['School No'].nunique()
            retained_schools = acad_2025[acad_2025['Is_Retained']]['School No'].unique()
            retained = len(retained_schools)
            
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
# 5. PAGE: INDIVIDUAL DASHBOARD & EXPORT
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
    fin_2025_ind = fin_2025[fin_2025['ACAD'] == selected_acad] if 'ACAD' in fin_2025.columns else pd.DataFrame()
    det_acad_ind = det_acad_cal[det_acad_cal['ACAD'] == selected_acad]
    det_kdm_ind = det_kdm[det_kdm['School Name'].isin(kdm_ind['School Name'])] if 'School Name' in kdm_ind.columns else pd.DataFrame()
    det_onb_ind = det_onboard[det_onboard['ACAD'] == selected_acad]
    
    # Calculate Core Metrics for Goal Sheet
    allocated_25 = fin_2025_ind['School No'].nunique() if not fin_2025_ind.empty else 0
    retained_27 = fin_2025_ind['Is_Retained'].sum() if not fin_2025_ind.empty else 0
    retained_rev_amt = 0
    if not fin_2025_ind.empty and not fin_2027.empty:
        ret_schools = fin_2025_ind[fin_2025_ind['Is_Retained']]['School No'].unique()
        retained_rev_amt = fin_2027[fin_2027['School No'].isin(ret_schools)]['Total Order Value (Exclusive GST)'].sum()
        
    calc_metrics = {
        'fb': fb_ind['Overall Rating'].values[0] if not fb_ind.empty else 0,
        'crm_total': crm_ind['Meetings'].sum() if not crm_ind.empty else 0,
        'kdm': kdm_ind['% Coverage'].mean() if not kdm_ind.empty else 0,
        'onboarding': onboard_ind['% Coverage'].mean() if not onboard_ind.empty else 0,
        'acad_cal': acad_cal_ind['Percentage Compliant'].mean() if not acad_cal_ind.empty else 0,
        'cares': cares_ind['Utilization (%)'].mean() if not cares_ind.empty else 0,
        'ms': ms_math_ind['Login %'].mean() if not ms_math_ind.empty else 0,
        'asset': asset_ind['Overall Score (%)'].mean() if not asset_ind.empty else 0,
        'retention_rate': (retained_27 / allocated_25 * 100) if allocated_25 > 0 else 0,
        'retained_rev': retained_rev_amt
    }

    # Include ALL raw data for the individual export
    raw_export_dfs = {'Feedback': fb_ind, 'CRM': crm_ind, 'KDM': kdm_ind, 'CARES': cares_ind, 'ASSET': asset_ind, 'MS_Math': ms_math_ind, 'Onboarding': onboard_ind, 'Acad_Cal': acad_cal_ind, '2025_Fin': fin_2025_ind}
    st.download_button(f"📥 Download {selected_acad} KPA Goal Sheet & Data", convert_acad_to_excel(selected_acad, calc_metrics, raw_export_dfs), f"KPA_2026_{selected_acad}.xlsx", type="primary")

    st.divider()

    st.header("📋 11-Point Executive Scorecard")
    s1, s2, s3, s4 = st.columns(4)
    s1.metric("1. Avg Feedback", f"{calc_metrics['fb']:.2f} / 10", f"Total Responses: {fb_ind['Responses'].values[0] if not fb_ind.empty else 0}", delta_color="off")
    s2.metric("9. Avg Session (NPS)", f"{crm_ind['Average Rating'].mean() if not crm_ind.empty else 0:.2f} / 5", "From CRM System", delta_color="off")
    s3.metric("7. Total Schools", allocated_25, "From 2025 Financials", delta_color="off")
    s4.metric("6. Meetings", f"{calc_metrics['crm_total']}", f"Target: 120", delta_color="off")

    st.divider()
    s5, s6, s7, s8 = st.columns(4)
    s5.metric("3. KDM Coverage %", f"{calc_metrics['kdm']:.1f}%", delta_color="off")
    s6.metric("4. Onboarding %", f"{calc_metrics['onboarding']:.1f}%", delta_color="off")
    s7.metric("5. Acad Calendar %", f"{calc_metrics['acad_cal']:.1f}%", delta_color="off")
    s8.metric("2. CARES Util %", f"{calc_metrics['cares']:.1f}%", delta_color="off")

    st.divider()
    st.header("🔍 Granular Raw Data Tables (Red = Needs Improvement)")
    
    # Restored ALL Granular Tables
    if not cares_ind.empty:
        st.markdown("**CARES Utilization Raw Data**")
        st.dataframe(cares_ind.style.apply(highlight_cares, axis=1), use_container_width=True, hide_index=True)
    if not asset_ind.empty:
        st.markdown("**ASSET Utilization Raw Data**")
        st.dataframe(asset_ind.style.apply(highlight_asset, axis=1), use_container_width=True, hide_index=True)
    if not ms_math_ind.empty:
        st.markdown("**Mindspark Math Raw Data**")
        st.dataframe(ms_math_ind.style.apply(highlight_ms, axis=1), use_container_width=True, hide_index=True)
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