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

# NEW FEATURE: Hardcoded DPS Codes
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
        
        # Detailed Feedback, Early Delivery, and Org Hierarchy
        det_feedback = pd.read_csv('detailed feedback.csv') if os.path.exists('detailed feedback.csv') else pd.DataFrame()
        cares_early = pd.read_csv('cares earlydelivery.csv') if os.path.exists('cares earlydelivery.csv') else pd.DataFrame()
        org_data = pd.read_csv('Supporting data(2)-13th March 2026 (8).xlsx - Org.csv') if os.path.exists('Supporting data(2)-13th March 2026 (8).xlsx - Org.csv') else pd.DataFrame()
        
        # Detailed CRM / MOM Data
        det_crm = pd.read_csv('Untitled spreadsheet - Sheet1.csv') if os.path.exists('Untitled spreadsheet - Sheet1.csv') else pd.DataFrame()
        
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
        
    for df in [fin_2025, fin_2027, drop_risk, det_feedback, det_crm]:
        if 'ACAD Name' in df.columns: df.rename(columns={'ACAD Name': 'ACAD'}, inplace=True)
        if 'CRM Acad Consultant' in df.columns and 'ACAD' not in df.columns: df.rename(columns={'CRM Acad Consultant': 'ACAD'}, inplace=True)
        if 'Facilitator' in df.columns and 'ACAD' not in df.columns: df.rename(columns={'Facilitator': 'ACAD'}, inplace=True)
        if 'Host Name' in df.columns and 'ACAD' not in df.columns: df.rename(columns={'Host Name': 'ACAD'}, inplace=True)
            
    if 'School No' in fin_2025.columns: fin_2025['School No'] = fin_2025['School No'].astype(str).str.strip().str.replace('.0', '', regex=False)
    if 'School No' in fin_2027.columns: fin_2027['School No'] = fin_2027['School No'].astype(str).str.strip().str.replace('.0', '', regex=False)

    if 'Host Name' in crm.columns: crm.rename(columns={'Host Name': 'ACAD'}, inplace=True)
    if 'Acad Name' in feedback.columns: feedback.rename(columns={'Acad Name': 'ACAD'}, inplace=True)
    
    kdm['% Coverage'] = pd.to_numeric(kdm['% Coverage'].replace({'Unknown': '0'}), errors='coerce').fillna(0)
    onboarding['% Coverage'] = pd.to_numeric(onboarding['% Coverage'].replace({'Unknown': '0'}), errors='coerce').fillna(0)
    ms_math['Login %'] = pd.to_numeric(ms_math['Login %'], errors='coerce').fillna(0)
    
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
    
    return acad_cal, det_acad_cal, kdm, det_kdm, onboarding, det_onboard, crm, feedback, cares_schools, asset, ms_math, fin_2025, fin_2027, drop_risk, det_feedback, cares_early, org_data, det_crm

acad_cal, det_acad_cal, kdm, det_kdm, onboarding, det_onboard, crm, feedback, cares_schools, asset, ms_math, fin_2025, fin_2027, drop_risk, det_feedback, cares_early, org_data, det_crm = load_data()

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
def highlight_cares(row): return style_ni(row, row.get('KRA Category', '') == 'NI')
def highlight_ms(row): return style_ni(row, row.get('Login %', 100) < 80)
def highlight_asset(row): return style_ni(row, row.get('Overall Score (%)', 100) < 100 and row.get('Included in Calculation', 'No') == 'Yes')
def highlight_kdm(row): return style_ni(row, row.get('% Coverage', 100) < 25)
def highlight_sla(row): return style_ni(row, row.get('Log_Delay_Hours', 0) > 48)

# ==========================================
# 2. SIDEBAR & MASTER EXPORT GENERATOR
# ==========================================
st.sidebar.title("Navigation & Filters")

# Global Zone Filter
available_zones = ["All Zones"] + sorted(fin_2025['Zone'].dropna().unique().tolist()) if not fin_2025.empty and 'Zone' in fin_2025.columns else ["All Zones"]
selected_zone = st.sidebar.selectbox("🌍 Filter by Zone:", available_zones)

if selected_zone != "All Zones" and not fin_2025.empty:
    valid_acads = fin_2025[fin_2025['Zone'] == selected_zone]['ACAD'].dropna().unique().tolist()
    all_acads = sorted([a for a in base_acads if a in valid_acads])
else:
    all_acads = base_acads

page = st.sidebar.radio("Select Dashboard View:", [
    "🏢 Dept 11-Point Scorecard", 
    "💰 Goal 1: Retention & Revenue", 
    "👤 Individual Dashboard & Goal Export"
])
st.sidebar.divider()

def generate_individual_goal_sheet(acad_name, metrics):
    """Generates the KPA-2026 format with actuals mapped dynamically AND NEW NI/ME/EE/DE Grades."""
    
    # Grading Logic Additions
    ret_grade = "DE" if metrics['retention_rate'] >= 98 else "EE" if metrics['retention_rate'] >= 95 else "ME" if metrics['retention_rate'] >= 90 else "NI"
    fb_grade = "DE" if metrics['fb'] >= 9 else "EE" if metrics['fb'] >= 8.5 else "ME" if metrics['fb'] >= 8 else "NI"
    cares_grade = "DE" if (metrics['cares'] >= 100 and metrics['early_reqs'] < 4) else "EE" if (metrics['cares'] >= 100 and metrics['early_reqs'] <= 4) else "ME" if (metrics['cares'] >= 100 and metrics['early_reqs'] <= 6) else "NI"
    ms_grade = "DE" if metrics['ms'] >= 90 else "EE" if metrics['ms'] >= 85 else "ME" if metrics['ms'] >= 80 else "NI"

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
            "20% participation", "MS>=80%, ASSET 80%, CARES 100%",
            "Achieve success set as ME in IDP", "Readiness for Action Research"
        ],
        "Weightage": ["20%", "10%", "5%", "10%", "10%", "5%", "5%", "5%", "10%", "15%", "5%"],
        "Total Group Weight": ["35%", "", "", "30%", "", "", "", "15%", "", "20%", ""],
        "ACTUAL ACHIEVED (Data)": [
            f"{metrics['retention_rate']:.1f}% Retained | ₹{metrics['retained_rev']:,.0f} [{ret_grade}]",
            "N/A", "N/A",
            f"Avg Rating: {metrics['fb']:.2f}/10 | {metrics['sla_48']:.1f}% logged <48h [{fb_grade}]",
            f"{metrics['kdm']:.1f}% Coverage",
            f"{metrics['onboarding']:.1f}% Coverage",
            f"{metrics['acad_cal']:.1f}% Compliant",
            "N/A",
            f"CARES: {metrics['cares']:.1f}% [{cares_grade}] | MS: {metrics['ms']:.1f}% [{ms_grade}] | ASSET: {metrics['asset']:.1f}%",
            f"Meeting Target Achieved: {metrics['meet_pct']:.1f}% [{metrics['idp_grade']}]", "Pending HR Eval"
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
    st.title(f"🏢 Department 11-Point Scorecard ({selected_zone})")
    st.markdown("**Metric Definitions:** Explicitly listing totals, averages, and the exact metric logic used.")
    
    total_acads = len(all_acads)
    
    # Use len(fin_2025) to properly count ALL allocated school rows
    dept_fin = fin_2025[fin_2025['ACAD'].isin(all_acads)] if not fin_2025.empty else pd.DataFrame()
    total_2025_schools_dept = len(dept_fin) if not dept_fin.empty else 0
    
    s1, s2, s3, s4 = st.columns(4)
    fb_val = feedback['Overall Rating'].mean() if not feedback.empty else 0
    s1.metric("1. Avg Feedback", f"{fb_val:.2f} / 10", f"Metric: Avg of all survey responses", delta_color="off")
    s2.metric("9. Avg Session (NPS)", f"{crm['Average Rating'].mean() if not crm.empty else 0:.2f} / 5", "Metric: Avg CRM rating", delta_color="off")
    s3.metric("7. Total Schools", total_2025_schools_dept, "Metric: Base 2025 Allocation", delta_color="off")
    
    # DYNAMIC MEETING TARGET (Schools x 4)
    tot_meetings = crm['Meetings'].sum() if not crm.empty else 0
    avg_meetings = tot_meetings / total_acads if total_acads > 0 else 0
    target_meetings_dept = total_2025_schools_dept * 4
    dept_meet_pct = min((tot_meetings / target_meetings_dept) * 100, 100) if target_meetings_dept > 0 else 0
    s4.metric(f"6. Total Meetings", tot_meetings, f"Avg {avg_meetings:.1f}/person | Target: {target_meetings_dept} ({dept_meet_pct:.1f}%)", delta_color="off")

    st.divider()
    s5, s6, s7, s8 = st.columns(4)
    
    s5.metric("3. Avg KDM Coverage", f"{kdm['% Coverage'].mean() if not kdm.empty else 0:.1f}%", f"Metric: (KDM Done / Alloted) * 100", delta_color="off")
    s6.metric("4. Avg Onboarding", f"{onboarding['% Coverage'].mean() if not onboarding.empty else 0:.1f}%", f"Metric: (Orientations / Signups) * 100", delta_color="off")
    s7.metric("5. Acad Calendar", f"{acad_cal['Percentage Compliant'].mean() if not acad_cal.empty else 0:.1f}%", f"Metric: Logged >15 days prior", delta_color="off")
    s8.metric("2. Avg CARES Util", f"{cares_schools['Utilization (%)'].mean() if not cares_schools.empty else 0:.1f}%", f"Metric: Tests conducted / Packs", delta_color="off")

    st.divider()
    
    # MOM Word Count Analysis (Department View)
    st.subheader("📝 MOM (Minutes of Meeting) Word Count Analysis")
    if not det_crm.empty and 'MOM_Word_Count' in det_crm.columns:
        dept_det_crm = det_crm[det_crm['ACAD'].isin(all_acads)]
        
        # Calculate stats: Total Logs and Average Word Count
        mom_stats = dept_det_crm.groupby('ACAD').agg(
            Total_Logs=('MOM_Word_Count', 'count'),
            Avg_Word_Count=('MOM_Word_Count', 'mean')
        ).reset_index()
        mom_stats.rename(columns={'Total_Logs': 'Total MOM Logs', 'Avg_Word_Count': 'Avg MOM Word Count'}, inplace=True)
        
        # Counts for >25 and >100 words
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

    # Dept-Wide Zero Utilization with COUNTS
    st.subheader("🚨 Metrics 10 & 11: Department-Wide Zero Utilization (Remedy Required)")
    zero_cares_dept = cares_schools[cares_schools['Utilization (%)'] == 0]
    zero_ms_dept = ms_math[ms_math['Login %'] == 0]
    zero_asset_dept = asset[asset['Overall Score (%)'] == 0]
    
    r1, r2, r3 = st.columns(3)
    with r1:
        st.error(f"**10. CARES (0% Util)**: {len(zero_cares_dept)} Schools")
        st.dataframe(zero_cares_dept[['ACAD', 'School Name', 'Utilization (%)']], hide_index=True)
    with r2:
        st.error(f"**10. MS Math (0% Logins)**: {len(zero_ms_dept)} Schools")
        st.dataframe(zero_ms_dept[['ACAD', 'schoolName', 'Login %']], hide_index=True)
    with r3:
        st.error(f"**11. ASSET (0% Score)**: {len(zero_asset_dept)} Schools")
        st.dataframe(zero_asset_dept[['ACAD', 'School Name', 'Overall Score (%)']], hide_index=True)

    st.divider()

    # Master Summary Table
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
        base_agg = fin_2025.groupby('ACAD').size().reset_index(name='Total 2025 Schools')
        master_summary = master_summary.merge(base_agg, on='ACAD', how='left')

    master_summary.fillna(0, inplace=True)
    format_dict = {'Avg Feedback': '{:.2f}', 'Avg NPS': '{:.2f}', 'Avg KDM %': '{:.1f}%', 'Onboarding %': '{:.1f}%', 'Acad Cal %': '{:.1f}%', 'CARES %': '{:.1f}%', 'MS Math %': '{:.1f}%', 'ASSET %': '{:.1f}%'}
    st.dataframe(master_summary.style.format(format_dict), use_container_width=True, hide_index=True)

    # DPS Detailed Logs (Dept View)
    st.divider()
    st.header("🏫 Specific DPS Schools Tracking & Detailed Logs")
    st.markdown(f"Fetching logs, feedback, and visits specifically for these School Codes: `{', '.join(DPS_CODES)}`")
    
    dps_names = fin_2025[fin_2025['School No'].isin(DPS_CODES)]['School Name'].unique().tolist() if not fin_2025.empty else []
    
    tab1, tab2 = st.tabs(["DPS Qualitative Feedback", "DPS Calendar Visit Logs"])
    with tab1:
        dps_fb = det_feedback[det_feedback['School Name'].isin(dps_names)] if not det_feedback.empty else pd.DataFrame()
        if not dps_fb.empty: st.dataframe(dps_fb[['ACAD', 'School Name', 'Products', 'NPS Rating (1-10)', 'Takeaways', 'Suggestions']], use_container_width=True, hide_index=True)
        else: st.info("No qualitative feedback logged yet for these specific DPS schools.")
    with tab2:
        dps_cal = det_acad_cal[det_acad_cal['School Name'].isin(dps_names)] if not det_acad_cal.empty else pd.DataFrame()
        if not dps_cal.empty: st.dataframe(dps_cal[['ACAD', 'School Name', 'Session Date', 'Compliance Status']], use_container_width=True, hide_index=True)
        else: st.info("No visit logs found for these specific DPS schools.")

    # Raw Data Expander for Dept
    st.divider()
    with st.expander("📁 View All Raw Operational CSV Data"):
        st.markdown("**CRM Data**"); st.dataframe(crm, use_container_width=True)
        st.markdown("**Feedback Data**"); st.dataframe(feedback, use_container_width=True)
        st.markdown("**ASSET Data**"); st.dataframe(asset, use_container_width=True)
        st.markdown("**Detailed Academic Calendar**"); st.dataframe(det_acad_cal, use_container_width=True)
        if not org_data.empty: st.markdown("**Organizational Hierarchy**"); st.dataframe(org_data, use_container_width=True)


# ==========================================
# 4. PAGE: RETENTION & REVENUE (GOAL 1)
# ==========================================
elif page == "💰 Goal 1: Retention & Revenue":
    st.title(f"💰 Goal 1: Retention & Revenue ({selected_zone})")
    
    dept_fin = fin_2025[fin_2025['ACAD'].isin(all_acads)] if not fin_2025.empty else pd.DataFrame()
    
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
    
    det_fb_ind = det_feedback[det_feedback['ACAD'] == selected_acad] if not det_feedback.empty else pd.DataFrame()
    cares_early_ind = cares_early[cares_early['ACAD'] == selected_acad] if not cares_early.empty else pd.DataFrame()
    
    # Calculate Core Metrics for Goal Sheet
    allocated_25 = len(fin_2025_ind) if not fin_2025_ind.empty else 0
    retained_27 = fin_2025_ind['Is_Retained'].sum() if not fin_2025_ind.empty else 0
    retained_rev_amt = 0
    if not fin_2025_ind.empty and not fin_2027.empty:
        ret_schools = fin_2025_ind[fin_2025_ind['Is_Retained']]['School No'].unique()
        retained_rev_amt = fin_2027[fin_2027['School No'].isin(ret_schools)]['Total Order Value (Exclusive GST)'].sum()
        
    early_requests = cares_early_ind['Total Requests'].sum() if not cares_early_ind.empty else 0
    pct_logged_48h = (len(det_acad_ind[det_acad_ind['Log_Delay_Hours'] <= 48]) / len(det_acad_ind) * 100) if not det_acad_ind.empty and len(det_acad_ind) > 0 else 0
    
    # DYNAMIC TARGET CALCULATION (Schools x 4)
    target_meetings = allocated_25 * 4
    crm_tot = crm_ind['Meetings'].sum() if not crm_ind.empty else 0
    meet_pct = (crm_tot / target_meetings * 100) if target_meetings > 0 else 0
    
    # IDP GRADING LOGIC (Goal 4) based on Meeting targets
    idp_grade = "DE" if meet_pct >= 100 else "EE" if meet_pct >= 90 else "ME" if meet_pct >= 80 else "NI"

    calc_metrics = {
        'fb': fb_ind['Overall Rating'].values[0] if not fb_ind.empty else 0,
        'crm_total': crm_tot,
        'kdm': kdm_ind['% Coverage'].mean() if not kdm_ind.empty else 0,
        'onboarding': onboard_ind['% Coverage'].mean() if not onboard_ind.empty else 0,
        'acad_cal': acad_cal_ind['Percentage Compliant'].mean() if not acad_cal_ind.empty else 0,
        'cares': cares_ind['Utilization (%)'].mean() if not cares_ind.empty else 0,
        'ms': ms_math_ind['Login %'].mean() if not ms_math_ind.empty else 0,
        'asset': asset_ind['Overall Score (%)'].mean() if not asset_ind.empty else 0,
        'retention_rate': (retained_27 / allocated_25 * 100) if allocated_25 > 0 else 0,
        'retained_rev': retained_rev_amt,
        'early_reqs': early_requests,
        'sla_48': pct_logged_48h,
        'target_meetings': target_meetings,
        'meet_pct': meet_pct,
        'idp_grade': idp_grade
    }

    # Include ALL raw data for the individual export
    raw_export_dfs = {'Feedback': fb_ind, 'Qual_Feedback': det_fb_ind, 'CRM': crm_ind, 'KDM': kdm_ind, 'CARES': cares_ind, 'ASSET': asset_ind, 'MS_Math': ms_math_ind, 'Onboarding': onboard_ind, 'Acad_Cal': acad_cal_ind, '2025_Fin': fin_2025_ind}
    if not det_crm.empty: raw_export_dfs['Detailed_CRM_MOM'] = det_crm[det_crm['ACAD'] == selected_acad]
    
    st.download_button(f"📥 Download {selected_acad} KPA Goal Sheet & Data", convert_acad_to_excel(selected_acad, calc_metrics, raw_export_dfs), f"KPA_2026_{selected_acad}.xlsx", type="primary")

    st.divider()

    st.header("📋 11-Point Executive Scorecard")
    s1, s2, s3, s4 = st.columns(4)
    s1.metric("1. Avg Feedback", f"{calc_metrics['fb']:.2f} / 10", f"Total Responses: {fb_ind['Responses'].values[0] if not fb_ind.empty else 0}", delta_color="off")
    s2.metric("9. Avg Session (NPS)", f"{crm_ind['Average Rating'].mean() if not crm_ind.empty else 0:.2f} / 5", "From CRM System", delta_color="off")
    s3.metric("7. Total Schools", allocated_25, "From 2025 Financials", delta_color="off")
    s4.metric("6. Meetings", f"{calc_metrics['crm_total']}", f"Target: {target_meetings} ({meet_pct:.1f}%)", delta_color="off")

    st.divider()
    s5, s6, s7, s8 = st.columns(4)
    s5.metric("3. KDM Coverage %", f"{calc_metrics['kdm']:.1f}%", delta_color="off")
    s6.metric("4. Onboarding %", f"{calc_metrics['onboarding']:.1f}%", delta_color="off")
    s7.metric("5. Acad Calendar %", f"{calc_metrics['acad_cal']:.1f}%", delta_color="off")
    s8.metric("2. CARES Util %", f"{calc_metrics['cares']:.1f}%", delta_color="off")

    st.divider()
    
    # MOM Word Count Analysis (Individual View)
    st.subheader("📝 MOM (Minutes of Meeting) Analysis")
    if not det_crm.empty and 'MOM_Word_Count' in det_crm.columns:
        ind_det_crm = det_crm[det_crm['ACAD'] == selected_acad]
        total_logs = len(ind_det_crm)
        avg_word_count = ind_det_crm['MOM_Word_Count'].mean() if not ind_det_crm.empty else 0
        gt_25_count = len(ind_det_crm[ind_det_crm['MOM_Word_Count'] > 25])
        gt_100_count = len(ind_det_crm[ind_det_crm['MOM_Word_Count'] > 100])
        
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Total MOM Logs Available", f"{total_logs}")
        m2.metric("Average MOM Word Count", f"{avg_word_count:.1f} words")
        m3.metric("MOMs > 25 Words", f"{gt_25_count} entries")
        m4.metric("MOMs > 100 Words", f"{gt_100_count} entries")
        
        with st.expander("View Detailed CRM MOM Logs"):
            st.dataframe(ind_det_crm[['ACAD', 'Customer Account Name', 'Description', 'MOM_Word_Count']], use_container_width=True, hide_index=True)

    st.divider()
    
    # Individual Zero Utilization Section with COUNTS
    st.subheader("🚨 Metrics 10 & 11: Zero Utilization (Immediate Remedy)")
    zero_cares_ind = cares_ind[cares_ind['Utilization (%)'] == 0]
    zero_ms_ind = ms_math_ind[ms_math_ind['Login %'] == 0]
    zero_asset_ind = asset_ind[asset_ind['Overall Score (%)'] == 0]
    
    r1, r2, r3 = st.columns(3)
    with r1:
        st.error(f"**10. CARES (0% Util)**: {len(zero_cares_ind)} Schools")
        st.dataframe(zero_cares_ind[['School Name', 'Utilization (%)']], hide_index=True)
    with r2:
        st.error(f"**10. MS Math (0% Logins)**: {len(zero_ms_ind)} Schools")
        st.dataframe(zero_ms_ind[['schoolName', 'Login %']], hide_index=True)
    with r3:
        st.error(f"**11. ASSET (0% Scheduled)**: {len(zero_asset_ind)} Schools")
        st.dataframe(zero_asset_ind[['School Name', 'Overall Score (%)']], hide_index=True)

    st.divider()
    
    # Qualitative Feedback and Goal 2/3 SLAs
    st.header("📝 Qualitative Session Feedback & Goal Analytics")
    c_col1, c_col2 = st.columns(2)
    with c_col1:
        st.markdown("**Goal 2: CRM Update SLA (<48 hours)**")
        st.metric("% Logged within 48h", f"{pct_logged_48h:.1f}%")
        if not det_acad_ind.empty: st.dataframe(det_acad_ind[['School Name', 'Session Date', 'Date Updated', 'Log_Delay_Hours']].style.apply(highlight_sla, axis=1), hide_index=True)
        
    with c_col2:
        st.markdown("**Goal 3: CARES Early Delivery Penalty**")
        st.metric("Total Early Delivery Requests", early_requests, "Penalty triggered if > 4")
        if early_requests > 4: st.error("Penalty Triggered: Early delivery requests exceed baseline target.")
    
    if not det_fb_ind.empty:
        st.markdown("**Raw Qualitative Teacher Takeaways**")
        st.dataframe(det_fb_ind[['School Name', 'Products', 'NPS Rating (1-10)', 'Takeaways', 'Suggestions']], use_container_width=True, hide_index=True)

    # DPS Detailed Logs (Individual View)
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