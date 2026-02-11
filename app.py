"""
📱 INVENTORY INTELLIGENCE DASHBOARD - MOBILE OPTIMIZED
Streamlit app optimized for both desktop and mobile devices
"""

import streamlit as st
import pandas as pd
import numpy as np
import altair as alt
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, date, timedelta
import gspread
from google.oauth2.service_account import Credentials
from dateutil.relativedelta import relativedelta
import warnings
from tenacity import retry, stop_after_attempt, wait_exponential
import math
import sys
import os
from pathlib import Path

# Import mobile config
try:
    from mobile_config import is_mobile_device, apply_mobile_css, get_device_type, get_responsive_columns
except ImportError:
    # Fallback functions if mobile_config not available
    def is_mobile_device(): return False
    def apply_mobile_css(): return ""
    def get_device_type(): return "desktop"
    def get_responsive_columns(device_type, default_cols=4): return default_cols

warnings.filterwarnings('ignore')

# ============================================================================
# 🎯 CONFIGURATION & INITIALIZATION
# ============================================================================

# Detect device type early
device_type = get_device_type()
is_mobile = is_mobile_device()

# Set page config with mobile optimization
st.set_page_config(
    page_title="Inventory Intelligence Pro",
    page_icon="📊",
    layout="wide" if not is_mobile else "centered",  # Centered layout on mobile
    initial_sidebar_state="expanded" if not is_mobile else "collapsed",  # Collapse sidebar on mobile
    menu_items={
        'Get Help': 'https://docs.streamlit.io',
        'Report a bug': 'https://github.com/streamlit/streamlit/issues',
        'About': '### Inventory Intelligence Dashboard v6.1\nOptimized for mobile & desktop'
    }
)

# ============================================================================
# 📱 MOBILE-SPECIFIC CSS (COMPREHENSIVE)
# ============================================================================

# Apply mobile CSS
mobile_css = apply_mobile_css()
st.markdown(mobile_css, unsafe_allow_html=True)

# Main CSS with mobile optimizations
st.markdown("""
<style>
    /* ============================================
       GLOBAL STYLES (Both Desktop & Mobile)
       ============================================ */
    .main-header {
        font-size: 2.5rem;
        font-weight: 900;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 1rem;
        text-align: center;
        padding: 1rem;
        border-bottom: 3px solid;
        border-image: linear-gradient(90deg, #667eea 0%, #764ba2 100%) 1;
    }
    
    /* Responsive header */
    @media (max-width: 768px) {
        .main-header {
            font-size: 1.8rem !important;
            padding: 0.5rem !important;
            margin-bottom: 0.5rem !important;
        }
    }
    
    .status-indicator {
        border-radius: 10px;
        padding: 1rem;
        margin: 0.5rem 0;
        font-weight: 700;
        text-align: center;
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        transition: transform 0.3s ease;
    }
    
    @media (max-width: 768px) {
        .status-indicator {
            padding: 0.8rem !important;
            margin: 0.3rem 0 !important;
            font-size: 0.9rem !important;
        }
    }
    
    .status-indicator:hover {
        transform: translateY(-5px);
    }
    
    .status-under { 
        background: linear-gradient(135deg, #FF5252 0%, #FF1744 100%);
        color: white;
        border-left: 5px solid #D32F2F;
    }
    
    .status-accurate { 
        background: linear-gradient(135deg, #4CAF50 0%, #2E7D32 100%);
        color: white;
        border-left: 5px solid #1B5E20;
    }
    
    .status-over { 
        background: linear-gradient(135deg, #FF9800 0%, #F57C00 100%);
        color: white;
        border-left: 5px solid #E65100;
    }
    
    .inventory-card {
        border-radius: 12px;
        padding: 1rem;
        text-align: center;
        font-weight: 700;
        box-shadow: 0 4px 15px rgba(0,0,0,0.08);
        margin: 0.5rem 0;
        transition: all 0.3s ease;
    }
    
    @media (max-width: 768px) {
        .inventory-card {
            padding: 0.7rem !important;
            margin: 0.3rem 0 !important;
            font-size: 0.9rem !important;
        }
    }
    
    .inventory-card:hover {
        box-shadow: 0 6px 20px rgba(0,0,0,0.12);
    }
    
    .card-replenish { 
        background: linear-gradient(135deg, #FFF3E0 0%, #FFE0B2 100%);
        color: #EF6C00;
        border: 2px solid #FF9800;
    }
    
    .card-ideal { 
        background: linear-gradient(135deg, #E8F5E9 0%, #C8E6C9 100%);
        color: #2E7D32;
        border: 2px solid #4CAF50;
    }
    
    .card-high { 
        background: linear-gradient(135deg, #FFEBEE 0%, #FFCDD2 100%);
        color: #C62828;
        border: 2px solid #F44336;
    }
    
    .metric-highlight {
        background: white;
        border-radius: 15px;
        padding: 1.5rem;
        box-shadow: 0 6px 20px rgba(102, 126, 234, 0.15);
        border-top: 5px solid #667eea;
        margin: 0.5rem 0;
        text-align: center;
    }
    
    @media (max-width: 768px) {
        .metric-highlight {
            padding: 1rem !important;
            margin: 0.3rem 0 !important;
            border-radius: 10px !important;
        }
    }
    
    /* Tab styling - Responsive */
    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
        padding: 10px 0;
    }
    
    @media (max-width: 768px) {
        .stTabs [data-baseweb="tab-list"] {
            gap: 4px !important;
            padding: 4px 0 !important;
        }
    }
    
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        background: linear-gradient(135deg, #F8F9FA 0%, #E9ECEF 100%);
        border-radius: 10px 10px 0 0;
        padding: 12px 24px;
        font-weight: 700;
        font-size: 1rem;
        border: 2px solid transparent;
        transition: all 0.3s ease;
    }
    
    @media (max-width: 768px) {
        .stTabs [data-baseweb="tab"] {
            height: 40px !important;
            padding: 8px 12px !important;
            font-size: 0.85rem !important;
            border-radius: 8px 8px 0 0 !important;
        }
    }
    
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
        color: white !important;
        border: 2px solid #5a67d8 !important;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
    }
    
    .stDataFrame {
        border-radius: 10px;
        overflow: hidden;
        box-shadow: 0 4px 15px rgba(0,0,0,0.08);
    }
    
    @media (max-width: 768px) {
        .stDataFrame {
            font-size: 0.85rem !important;
        }
    }
    
    .sankey-container {
        background: white;
        border-radius: 15px;
        padding: 1.5rem;
        box-shadow: 0 6px 20px rgba(0,0,0,0.1);
        margin: 1rem 0;
    }
    
    /* Monthly performance card - Responsive */
    .monthly-performance-card {
        background: white;
        border-radius: 12px;
        padding: 1.5rem;
        margin: 0.5rem;
        box-shadow: 0 4px 12px rgba(0,0,0,0.08);
        border-left: 5px solid;
    }
    
    @media (max-width: 768px) {
        .monthly-performance-card {
            padding: 1rem !important;
            margin: 0.3rem !important;
        }
    }
    
    .performance-under { border-left-color: #F44336; }
    .performance-accurate { border-left-color: #4CAF50; }
    .performance-over { border-left-color: #FF9800; }
    
    .highlight-row {
        background-color: #FFF9C4 !important;
        font-weight: bold !important;
    }
    
    .warning-badge {
        background: #FF5252;
        color: white;
        padding: 2px 8px;
        border-radius: 12px;
        font-size: 0.8rem;
        font-weight: bold;
    }
    
    .success-badge {
        background: #4CAF50;
        color: white;
        padding: 2px 8px;
        border-radius: 12px;
        font-size: 0.8rem;
        font-weight: bold;
    }
    
    /* Compact metrics - Mobile optimized */
    .compact-metric {
        background: white;
        border-radius: 10px;
        padding: 1rem;
        box-shadow: 0 4px 12px rgba(0,0,0,0.08);
        margin: 0.5rem 0;
    }
    
    @media (max-width: 768px) {
        .compact-metric {
            padding: 0.7rem !important;
            margin: 0.3rem 0 !important;
        }
    }
    
    /* Brand performance */
    .brand-card {
        background: white;
        border-radius: 12px;
        padding: 1rem;
        box-shadow: 0 4px 15px rgba(0,0,0,0.08);
        border-top: 4px solid #667eea;
    }
    
    /* Financial cards - Mobile optimized */
    .financial-card {
        background: white;
        border-radius: 12px;
        padding: 1.5rem;
        margin: 0.5rem 0;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        border-top: 4px solid;
        transition: all 0.3s ease;
    }
    
    @media (max-width: 768px) {
        .financial-card {
            padding: 1rem !important;
            margin: 0.3rem 0 !important;
        }
    }
    
    .financial-card:hover {
        transform: translateY(-3px);
        box-shadow: 0 8px 25px rgba(0,0,0,0.15);
    }
    
    .card-revenue { border-top-color: #667eea; }
    .card-margin { border-top-color: #4CAF50; }
    .card-cost { border-top-color: #FF9800; }
    .card-inventory { border-top-color: #9C27B0; }
    
    /* Dark mode support */
    @media (prefers-color-scheme: dark) {
        .stApp {
            background-color: #0E1117;
            color: #FFFFFF;
        }
        .financial-card, .brand-card, .compact-metric {
            background-color: #1E1E1E;
            color: #FFFFFF;
        }
    }
    
    /* Progress bar animation */
    @keyframes pulse {
        0% { opacity: 1; }
        50% { opacity: 0.7; }
        100% { opacity: 1; }
    }
    
    .pulse-animation {
        animation: pulse 2s infinite;
    }
    
    /* ============================================
       MOBILE-SPECIFIC COMPONENTS
       ============================================ */
    
    /* Mobile bottom navigation (hidden by default) */
    .mobile-bottom-nav {
        display: none;
    }
    
    @media (max-width: 768px) {
        .mobile-bottom-nav {
            display: flex;
            position: fixed;
            bottom: 0;
            left: 0;
            right: 0;
            background: white;
            border-top: 1px solid #e0e0e0;
            padding: 10px 0;
            z-index: 1000;
            justify-content: space-around;
            box-shadow: 0 -2px 10px rgba(0,0,0,0.1);
        }
        
        /* Add padding to main content to avoid overlap */
        .main .block-container {
            padding-bottom: 80px !important;
        }
        
        .mobile-nav-item {
            text-align: center;
            color: #666;
            flex: 1;
            padding: 5px;
            text-decoration: none;
            font-size: 0.8rem;
        }
        
        .mobile-nav-item.active {
            color: #667eea;
            font-weight: bold;
        }
        
        .mobile-nav-icon {
            font-size: 1.2rem;
            display: block;
            margin-bottom: 3px;
        }
    }
    
    /* Touch-friendly elements */
    @media (hover: none) and (pointer: coarse) {
        /* Larger touch targets */
        button, [role="button"], .stButton button {
            min-height: 44px !important;
            min-width: 44px !important;
        }
        
        /* Larger text for readability */
        .stMetric {
            font-size: 1.1rem !important;
        }
        
        /* Larger checkbox/radio */
        .stCheckbox, .stRadio {
            transform: scale(1.1);
            transform-origin: left;
        }
    }
    
    /* Print styles (unchanged) */
    @media print {
        /* Your existing print styles... */
    }
</style>
""", unsafe_allow_html=True)

# ============================================================================
# 📱 MOBILE BOTTOM NAVIGATION (OPTIONAL)
# ============================================================================

def render_mobile_navigation(current_tab=0):
    """Render mobile bottom navigation if on mobile device"""
    if is_mobile:
        nav_html = """
        <div class="mobile-bottom-nav">
            <a href="#" class="mobile-nav-item %s" onclick="switchTab(0)">
                <span class="mobile-nav-icon">📊</span>
                <span>Overview</span>
            </a>
            <a href="#" class="mobile-nav-item %s" onclick="switchTab(1)">
                <span class="mobile-nav-icon">📦</span>
                <span>Inventory</span>
            </a>
            <a href="#" class="mobile-nav-item %s" onclick="switchTab(2)">
                <span class="mobile-nav-icon">💰</span>
                <span>Finance</span>
            </a>
            <a href="#" class="mobile-nav-item %s" onclick="switchTab(9)">
                <span class="mobile-nav-icon">⚙️</span>
                <span>More</span>
            </a>
        </div>
        
        <script>
        function switchTab(tabIndex) {
            // This would need JavaScript to switch tabs
            // For now, it's a visual placeholder
            document.querySelectorAll('.mobile-nav-item').forEach((item, index) => {
                item.classList.remove('active');
                if(index === tabIndex) {
                    item.classList.add('active');
                }
            });
            return false;
        }
        </script>
        """ % (
            "active" if current_tab == 0 else "",
            "active" if current_tab == 1 else "",
            "active" if current_tab == 2 else "",
            "active" if current_tab == 9 else ""
        )
        st.markdown(nav_html, unsafe_allow_html=True)

# ============================================================================
# 🎯 MAIN APP FUNCTIONS (SAME AS BEFORE - OPTIMIZED FOR MOBILE)
# ============================================================================

# --- Judul Dashboard dengan Responsive Design ---
st.markdown('<h1 class="main-header">💰 FORECAST & INVENTORY CONTROL PRO DASHBOARD</h1>', unsafe_allow_html=True)

# Responsive caption based on device
if is_mobile:
    st.caption(f"📱 Mobile View | Updated: {datetime.now().strftime('%d %b %Y')}")
else:
    st.caption(f"🚀 Inventory Control & Forecast Analytics - D2C Demand Planner Mulyanto | Real-time Insights | Updated: {datetime.now().strftime('%d %B %Y %H:%M')}")

# ============================================================================
# 🔄 DATA LOADING FUNCTIONS (UNCHANGED - SAME AS BEFORE)
# ============================================================================

@st.cache_resource(show_spinner=False)
@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
def init_gsheet_connection():
    """Inisialisasi koneksi ke Google Sheets dengan retry mechanism"""
    try:
        skey = st.secrets["gcp_service_account"]
        scopes = ["https://www.googleapis.com/auth/spreadsheets"]
        credentials = Credentials.from_service_account_info(skey, scopes=scopes)
        client = gspread.authorize(credentials)
        return client
    except Exception as e:
        st.error(f"❌ Koneksi Gagal: {str(e)}")
        return None

# ... [ALL YOUR EXISTING DATA FUNCTIONS REMAIN THE SAME] ...
# I'm keeping the structure but removing duplicate code for brevity
# Your existing functions from the original app go here:
# - validate_month_format
# - add_product_info_to_data
# - load_and_process_data
# - load_reseller_complete_data
# - calculate_financial_metrics_all
# - calculate_inventory_financial
# - calculate_seasonality
# - calculate_eoq
# - calculate_forecast_bias
# - calculate_monthly_performance
# - get_last_3_months_performance
# - calculate_inventory_metrics_with_3month_avg
# - calculate_sales_vs_forecast_po
# - calculate_brand_performance
# - identify_profitability_segments
# - validate_data_quality

# ============================================================================
# 📱 RESPONSIVE LAYOUT HELPERS
# ============================================================================

def create_responsive_columns(num_items, items_per_row_desktop=4):
    """
    Create responsive columns based on device type
    Returns: list of column objects for the current row
    """
    if is_mobile:
        items_per_row = 1  # Stack on mobile
    elif device_type == 'tablet':
        items_per_row = 2  # Two columns on tablet
    else:
        items_per_row = items_per_row_desktop  # Desktop
    
    # Calculate how many full rows we need
    full_rows = num_items // items_per_row
    remainder = num_items % items_per_row
    
    columns = []
    for i in range(full_rows):
        row_cols = st.columns(items_per_row)
        columns.extend(row_cols)
    
    if remainder > 0:
        last_row_cols = st.columns(remainder)
        columns.extend(last_row_cols)
    
    return columns

def responsive_dataframe(df, height=None):
    """Display dataframe with responsive height"""
    if is_mobile:
        default_height = 300
    else:
        default_height = 500
    
    height = height or default_height
    
    return st.dataframe(
        df,
        use_container_width=True,
        height=height
    )

def responsive_plotly_chart(fig, height=None):
    """Display plotly chart with responsive height"""
    if is_mobile:
        default_height = 300
    elif device_type == 'tablet':
        default_height = 400
    else:
        default_height = 500
    
    height = height or default_height
    
    fig.update_layout(height=height)
    return st.plotly_chart(fig, use_container_width=True)

# ============================================================================
# 📊 MAIN DASHBOARD LAYOUT WITH MOBILE OPTIMIZATION
# ============================================================================

# --- SIDEBAR dengan Mobile Optimization ---
with st.sidebar:
    if is_mobile:
        st.markdown("### 📱 Mobile Menu")
        # Collapsible sidebar for mobile
        with st.expander("⚙️ Settings", expanded=False):
            # Settings content
            pass
    else:
        st.markdown("### ⚙️ Dashboard Controls")
    
    # Responsive button layout
    if is_mobile:
        col_sb1, col_sb2 = st.columns(2)
        with col_sb1:
            refresh_btn = st.button("🔄 Refresh", use_container_width=True, type="primary")
        with col_sb2:
            if st.button("📊 Stats", use_container_width=True):
                st.session_state.show_stats = True
    else:
        col_sb1, col_sb2 = st.columns(2)
        with col_sb1:
            refresh_btn = st.button("🔄 Refresh Data", use_container_width=True, type="primary")
        with col_sb2:
            if st.button("📊 Show Data Stats", use_container_width=True):
                st.session_state.show_stats = True
    
    # --- Responsive Print Button ---
    st.markdown("---")
    if is_mobile:
        print_text = "🖨️ Print PDF"
    else:
        print_text = "🖨️ Save as PDF"
    
    if st.button(print_text, use_container_width=True):
        import streamlit.components.v1 as components
        components.html(
            """
            <script>
            window.print();
            </script>
            """,
            height=0,
            width=0
        )
    
    if is_mobile:
        st.caption("Tip: Choose 'Save as PDF' in print options.")
    else:
        st.caption("Tip: Pilih Destination **'Save as PDF'** & centang **'Background graphics'** di settings print.")
    
    # --- Data Overview dengan Responsive Layout ---
    st.markdown("---")
    st.markdown("### 📈 Data Overview")
    
    # Responsive metrics in sidebar
    if not df_product_active.empty:
        if is_mobile:
            st.metric("Active SKUs", f"{len(df_product_active):,}")
        else:
            st.metric("Active SKUs", len(df_product_active))
    
    # ... rest of sidebar remains similar but could be optimized ...

# ============================================================================
# 📱 MAIN CONTENT AREA - RESPONSIVE DESIGN
# ============================================================================

# Initialize session state for mobile tabs if not exists
if 'mobile_current_tab' not in st.session_state:
    st.session_state.mobile_current_tab = 0

# --- Mobile Tab Selector (Only shown on mobile) ---
if is_mobile:
    mobile_tabs = st.radio(
        "Navigate:",
        ["📊 Overview", "📈 Accuracy", "📦 Inventory", "💰 Finance", "⚙️ More"],
        horizontal=True,
        label_visibility="collapsed"
    )
    
    # Map mobile tabs to actual tabs
    mobile_tab_map = {
        "📊 Overview": 0,  # Tab 1
        "📈 Accuracy": 0,  # Tab 1 (same)
        "📦 Inventory": 2,  # Tab 3
        "💰 Finance": 7,   # Tab 8
        "⚙️ More": 9      # Tab 10
    }
    
    current_tab_index = mobile_tab_map[mobile_tabs]
else:
    # Desktop: Use regular tabs
    current_tab_index = 0  # Default

# --- Define Tab Structure dengan Mobile Optimization ---
tab_titles = [
    "📈 Monthly Performance Details",
    "🏷️ Brand & Tier Analysis",
    "📦 Inventory Analysis",
    "🔍 SKU Evaluation",
    "📈 Sales & Forecast Analysis",
    "📋 Data Explorer",
    "🛒 Ecommerce Forecast",  
    "💰 Profitability Analysis",
    "🤝 Reseller Forecast",
    "🚚 Fulfillment Cost Analysis"
]

# Shortened titles for mobile
mobile_tab_titles = [
    "📈 Performance",
    "🏷️ Brands",
    "📦 Stock",
    "🔍 SKU",
    "📈 Sales",
    "📋 Data",
    "🛒 Ecomm",
    "💰 Profit",
    "🤝 Reseller",
    "🚚 Cost"
]

# Create tabs
if is_mobile:
    # On mobile, we use a different navigation system
    # We'll show content based on selected mobile tab
    tabs = [st.container() for _ in range(len(tab_titles))]
    active_tab_index = current_tab_index
else:
    # On desktop, use regular tabs
    tabs = st.tabs(tab_titles if not is_mobile else mobile_tab_titles)
    active_tab_index = 0  # Will be set by Streamlit

# ============================================================================
# 📱 TAB CONTENTS WITH RESPONSIVE DESIGN
# ============================================================================

# Helper function to render tab content with responsive design
def render_tab_content(tab_index, content_func):
    """Render tab content with responsive adjustments"""
    if is_mobile and current_tab_index != tab_index:
        return  # Only render the active tab on mobile
    
    with tabs[tab_index]:
        # Add mobile-specific header for each tab
        if is_mobile:
            st.markdown(f"### {tab_titles[tab_index]}")
            st.markdown("---")
        
        # Render the content
        content_func()

# ============================================================================
# 🎯 DEFINE TAB CONTENTS (YOUR EXISTING LOGIC, OPTIMIZED)
# ============================================================================

# Note: I'm showing the structure. You would put your existing tab content
# inside these functions, making sure to use the responsive helpers

def tab1_content():
    """Tab 1: Monthly Performance Details - Optimized for mobile"""
    st.subheader("📅 Monthly Performance Details")
    
    if monthly_performance:
        # Use responsive columns
        if is_mobile:
            # Stack metrics on mobile
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Current Accuracy", f"{last_month_accuracy:.1f}%")
            with col2:
                st.metric("Avg Accuracy", f"{avg_acc:.1f}%")
        else:
            # Desktop layout
            col1, col2, col3, col4 = st.columns(4)
            # ... your existing desktop metrics code
        
        # Use responsive chart
        responsive_plotly_chart(fig_trend)
        
        # Responsive dataframe
        responsive_dataframe(summary_df)
        
    else:
        st.info("No monthly performance data available")

def tab2_content():
    """Tab 2: Brand & Tier Analysis - Optimized for mobile"""
    st.subheader("🏷️ Brand & Tier Strategic Analysis")
    
    if is_mobile:
        # Simplified mobile view
        st.markdown("**Top 5 Brands by Accuracy**")
        
        # Simple bar chart for mobile
        if not brand_performance.empty:
            top_brands = brand_performance.head(5)
            fig = px.bar(top_brands, x='Brand', y='Accuracy', 
                        title="Top Brands Accuracy")
            responsive_plotly_chart(fig, height=300)
    else:
        # Desktop view - your existing code
        pass

def tab3_content():
    """Tab 3: Inventory Analysis - Optimized for mobile"""
    st.subheader("📦 Inventory Health Dashboard")
    
    # Responsive KPI cards
    if is_mobile:
        # Stacked metrics on mobile
        metrics = [
            ("Total Stock", f"{total_stock:,.0f}"),
            ("Avg Cover", f"{avg_cover_months:.1f} mo"),
            ("Value", f"Rp {total_val/1e6:.1f}M")
        ]
        
        for label, value in metrics:
            col1, col2 = st.columns([1, 2])
            with col1:
                st.markdown(f"**{label}:**")
            with col2:
                st.markdown(f"**{value}**")
            st.markdown("---")
    else:
        # Desktop grid
        col1, col2, col3, col4 = st.columns(4)
        # ... your existing desktop code

# ... Define other tab content functions similarly ...

# ============================================================================
# 📱 RENDER ALL TABS
# ============================================================================

# Map tab index to content function
tab_contents = {
    0: tab1_content,
    1: tab2_content,
    2: tab3_content,
    # ... add all your tab functions
}

# Render the active tab(s)
if is_mobile:
    # On mobile, only render the active tab
    active_func = tab_contents.get(current_tab_index, lambda: st.info("Content not available"))
    active_func()
else:
    # On desktop, render all tabs
    for i in range(len(tab_titles)):
        with tabs[i]:
            func = tab_contents.get(i, lambda: st.info("Content not available"))
            func()

# ============================================================================
# 📱 MOBILE BOTTOM NAVIGATION
# ============================================================================

# Render mobile navigation at the bottom
render_mobile_navigation(current_tab_index)

# ============================================================================
# 📊 LOAD DATA (SAME AS BEFORE)
# ============================================================================

# Initialize connection
client = init_gsheet_connection()

if client is None:
    st.error("❌ Tidak dapat terhubung ke Google Sheets")
    st.stop()

# Load data with progress indicator
with st.spinner('🔄 Loading data...' if is_mobile else '🔄 Loading and processing data from Google Sheets...'):
    # Your existing data loading code here
    # all_data = load_and_process_data(client)
    # ... etc
    
    # For now, placeholder
    st.info("Data loading would happen here...")

# ============================================================================
# 📱 PROGRESSIVE WEB APP (PWA) MANIFEST
# ============================================================================

# Add PWA support for mobile
if is_mobile:
    st.markdown("""
    <link rel="manifest" href="manifest.json">
    <meta name="theme-color" content="#667eea">
    <meta name="apple-mobile-web-app-capable" content="yes">
    <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
    <meta name="apple-mobile-web-app-title" content="Inventory Dashboard">
    <link rel="apple-touch-icon" href="icon-192.png">
    """, unsafe_allow_html=True)

# ============================================================================
# 🎯 FOOTER WITH RESPONSIVE DESIGN
# ============================================================================

st.divider()

if is_mobile:
    footer_text = """
    <div style="text-align: center; color: #666; font-size: 0.8rem; padding: 0.5rem;">
        <p>📱 <strong>Inventory Mobile v6.1</strong></p>
        <p>Optimized for mobile devices</p>
        <p>Last update: {}</p>
    </div>
    """.format(datetime.now().strftime('%d %b %Y'))
else:
    footer_text = """
    <div style="text-align: center; color: #666; font-size: 0.9rem; padding: 1rem;">
        <p>🚀 <strong>Inventory Intelligence Dashboard v6.1</strong> | Professional Inventory Control & Financial Analytics</p>
        <p>✅ Mobile Optimized | ✅ Responsive Design | ✅ Touch-Friendly</p>
        <p>💰 Profitability Dashboard | 📊 Seasonality Analysis | 🎯 Margin Segmentation</p>
        <p>📈 Data since January 2024 | 🔄 Real-time Google Sheets Integration</p>
    </div>
    """

st.markdown(footer_text, unsafe_allow_html=True)

# ============================================================================
# 📱 JAVASCRIPT FOR MOBILE INTERACTIONS
# ============================================================================

if is_mobile:
    st.markdown("""
    <script>
    // Prevent zoom on input focus (iOS)
    document.addEventListener('DOMContentLoaded', function() {
        var metas = document.getElementsByTagName('meta');
        for (var i = 0; i < metas.length; i++) {
            if (metas[i].name == "viewport") {
                metas[i].content = "width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=0";
            }
        }
    });
    
    // Touch event handling
    document.addEventListener('touchstart', function() {}, {passive: true});
    
    // Prevent bounce on iOS
    document.body.addEventListener('touchmove', function(e) {
        if(e.target.tagName != 'INPUT' && e.target.tagName != 'TEXTAREA') {
            e.preventDefault();
        }
    }, { passive: false });
    </script>
    """, unsafe_allow_html=True)
