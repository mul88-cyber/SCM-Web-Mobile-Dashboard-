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
warnings.filterwarnings('ignore')

# ============================================================================
# 📱 IMPORT MOBILE CONFIGURATION
# ============================================================================

try:
    from mobile_config import is_mobile_device, apply_mobile_css, get_device_type, get_responsive_columns
except ImportError:
    # Fallback functions jika mobile_config.py tidak ditemukan
    def is_mobile_device(): 
        # Simple detection based on query params
        query_params = st.query_params
        if 'mobile' in query_params:
            return query_params['mobile'].lower() == 'true'
        return False
    
    def apply_mobile_css(): 
        return "<style></style>"
    
    def get_device_type(): 
        if is_mobile_device():
            if 'tablet' in st.query_params and st.query_params['tablet'].lower() == 'true':
                return 'tablet'
            return 'mobile'
        return 'desktop'
    
    def get_responsive_columns(device_type, default_cols=4): 
        return 1 if device_type == 'mobile' else (2 if device_type == 'tablet' else default_cols)

# ============================================================================
# 🎯 KONFIGURASI HALAMAN DENGAN RESPONSIVE DESIGN
# ============================================================================

# Set page config dengan layout wide (akan disesuaikan dengan CSS mobile)
st.set_page_config(
    page_title="Inventory Intelligence Pro",
    page_icon="📊",
    layout="wide",  # Tetap wide untuk desktop, akan diatur ulang dengan CSS
    initial_sidebar_state="expanded"
)

# ============================================================================
# 📱 DETEKSI DEVICE & APLIKASI CSS RESPONSIVE
# ============================================================================

# Deteksi device type
device_type = get_device_type()
is_mobile = is_mobile_device()

# Apply mobile CSS
mobile_css = apply_mobile_css()
st.markdown(mobile_css, unsafe_allow_html=True)

# ============================================================================
# 📱 RESPONSIVE HELPER FUNCTIONS
# ============================================================================

def create_responsive_columns(num_cols_desktop=4):
    """Create columns based on device type"""
    if is_mobile:
        return [st.container()]  # Single column on mobile
    elif device_type == 'tablet':
        return st.columns(2)  # Two columns on tablet
    else:
        return st.columns(num_cols_desktop)  # Desktop

def responsive_metric(label, value, delta=None):
    """Display metric with responsive sizing"""
    if is_mobile:
        # Compact metric for mobile
        col1, col2 = st.columns([1, 2])
        with col1:
            st.markdown(f"**{label}:**")
        with col2:
            if delta:
                st.markdown(f"**{value}** ({delta})")
            else:
                st.markdown(f"**{value}**")
        st.markdown("---")
    else:
        # Regular metric for desktop
        st.metric(label, value, delta)

def responsive_tabs(tab_names):
    """Create responsive tabs based on device"""
    if is_mobile:
        # Mobile: Use selectbox
        selected_tab = st.selectbox(
            "Navigate:",
            tab_names,
            label_visibility="collapsed"
        )
        return selected_tab
    else:
        # Desktop: Use full tabs
        return st.tabs(tab_names)

# ============================================================================
# 🎨 CSS PREMIUM + MOBILE OPTIMIZATION
# ============================================================================

# --- CSS KHUSUS PRINT PDF (FIX BLANK PAGE) ---
st.markdown("""
<style>
    @media print {
        /* FIX UTAMA: Reset SEMUA element ke block/visible */
        * {
            overflow: visible !important;
            position: static !important;
            display: block !important;
            float: none !important;
            height: auto !important;
            max-height: none !important;
            width: auto !important;
            max-width: none !important;
            -webkit-print-color-adjust: exact !important;
            print-color-adjust: exact !important;
            break-inside: avoid !important;
        }

        /* Hide unnecessary elements */
        [data-testid="stSidebar"],
        [data-testid="stHeader"],
        .stButton,
        .stDeployButton,
        footer,
        .stDownloadButton,
        .stActionButton,
        button,
        [data-testid="baseButton-secondary"],
        [data-testid="baseButton-primary"],
        .stAlert,
        .stMarkdown:has(button) {
            display: none !important;
            height: 0 !important;
            width: 0 !important;
            opacity: 0 !important;
            visibility: hidden !important;
        }

        /* Force main container to be visible */
        [data-testid="stAppViewContainer"],
        [data-testid="stMain"] {
            position: static !important;
            width: 100vw !important;
            height: auto !important;
            margin: 0 !important;
            padding: 0 !important;
            overflow: visible !important;
            display: block !important;
        }

        /* Force all content to be visible */
        section[data-testid="stMain"] > div,
        [data-testid="block-container"] {
            overflow: visible !important;
            height: auto !important;
            max-height: none !important;
            display: block !important;
            position: static !important;
            break-inside: avoid;
        }

        /* Charts and tables - force visibility */
        .element-container,
        .stDataFrame,
        .stPlotlyChart,
        .stAltairChart,
        [data-testid="stHorizontalBlock"] {
            break-inside: avoid-page !important;
            page-break-inside: avoid !important;
            overflow: visible !important;
        }

        /* Ensure text is black for printing */
        body, h1, h2, h3, h4, h5, h6, p, div, span {
            color: #000000 !important;
            background-color: white !important;
        }

        /* Remove shadows and gradients for print */
        .status-indicator,
        .inventory-card,
        .metric-highlight {
            box-shadow: none !important;
            background: white !important;
            border: 1px solid #ccc !important;
        }

        /* Fix for Plotly charts */
        .js-plotly-plot,
        .plotly,
        .plot-container {
            width: 100% !important;
            height: auto !important;
        }

        /* Add page breaks between major sections */
        .stTabs {
            break-after: page !important;
        }

        /* Ensure all content fits page width */
        .row {
            display: block !important;
        }

        .column {
            width: 100% !important;
            float: none !important;
        }
    }
</style>
""", unsafe_allow_html=True)

# --- Custom CSS Premium dengan Mobile Support ---
st.markdown(f"""
<style>
    /* Responsive header */
    .main-header {{
        font-size: 2.5rem;
        font-weight: 900;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        padding: 1rem;
        margin-bottom: 1.5rem;
    }}
    
    /* Mobile-specific adjustments */
    @media only screen and (max-width: 768px) {{
        .main-header {{
            font-size: 1.8rem !important;
            padding: 0.5rem !important;
        }}
        
        /* Stack columns on mobile */
        [data-testid="column"] {{
            width: 100% !important;
            margin-bottom: 0.5rem !important;
        }}
        
        /* Smaller tabs on mobile */
        .stTabs [data-baseweb="tab"] {{
            padding: 6px 10px !important;
            font-size: 0.8rem !important;
        }}
        
        /* Compact metrics for mobile */
        .compact-metric {{
            padding: 0.5rem !important;
            margin: 0.2rem 0 !important;
            font-size: 0.9rem !important;
        }}
        
        /* Hide some elements on mobile */
        .mobile-hide {{
            display: none !important;
        }}
        
        /* Adjust chart sizes */
        .js-plotly-plot, .plotly, .plot-container {{
            height: 280px !important;
        }}
    }}
    
    /* Tablet-specific adjustments */
    @media only screen and (min-width: 769px) and (max-width: 1024px) {{
        [data-testid="column"] {{
            flex: 0 0 50% !important;
            width: 50% !important;
        }}
        
        .stTabs [data-baseweb="tab"] {{
            flex: 1 0 calc(33.33% - 8px) !important;
            min-width: calc(33.33% - 8px) !important;
        }}
        
        .main-header {{
            font-size: 2.2rem !important;
        }}
        
        .js-plotly-plot, .plotly, .plot-container {{
            height: 350px !important;
        }}
    }}
    
    /* Existing premium styles */
    .status-indicator {{
        border-radius: 10px;
        padding: 1rem;
        margin: 0.5rem 0;
        font-weight: 700;
        text-align: center;
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        transition: transform 0.3s ease;
    }}
    .status-indicator:hover {{
        transform: translateY(-5px);
    }}
    .status-under {{ 
        background: linear-gradient(135deg, #FF5252 0%, #FF1744 100%);
        color: white;
        border-left: 5px solid #D32F2F;
    }}
    .status-accurate {{ 
        background: linear-gradient(135deg, #4CAF50 0%, #2E7D32 100%);
        color: white;
        border-left: 5px solid #1B5E20;
    }}
    .status-over {{ 
        background: linear-gradient(135deg, #FF9800 0%, #F57C00 100%);
        color: white;
        border-left: 5px solid #E65100;
    }}
    
    .inventory-card {{
        border-radius: 12px;
        padding: 1rem;
        text-align: center;
        font-weight: 700;
        box-shadow: 0 4px 15px rgba(0,0,0,0.08);
        margin: 0.5rem 0;
        transition: all 0.3s ease;
    }}
    .inventory-card:hover {{
        box-shadow: 0 6px 20px rgba(0,0,0,0.12);
    }}
    .card-replenish {{ 
        background: linear-gradient(135deg, #FFF3E0 0%, #FFE0B2 100%);
        color: #EF6C00;
        border: 2px solid #FF9800;
    }}
    .card-ideal {{ 
        background: linear-gradient(135deg, #E8F5E9 0%, #C8E6C9 100%);
        color: #2E7D32;
        border: 2px solid #4CAF50;
    }}
    .card-high {{ 
        background: linear-gradient(135deg, #FFEBEE 0%, #FFCDD2 100%);
        color: #C62828;
        border: 2px solid #F44336;
    }}
    
    .metric-highlight {{
        background: white;
        border-radius: 15px;
        padding: 1.5rem;
        box-shadow: 0 6px 20px rgba(102, 126, 234, 0.15);
        border-top: 5px solid #667eea;
        margin: 0.5rem 0;
        text-align: center;
    }}
    
    /* Tab styling */
    .stTabs [data-baseweb="tab-list"] {{
        gap: 10px;
        padding: 10px 0;
    }}
    .stTabs [data-baseweb="tab"] {{
        height: 50px;
        white-space: pre-wrap;
        background: linear-gradient(135deg, #F8F9FA 0%, #E9ECEF 100%);
        border-radius: 10px 10px 0 0;
        padding: 12px 24px;
        font-weight: 700;
        font-size: 1rem;
        border: 2px solid transparent;
        transition: all 0.3s ease;
    }}
    .stTabs [aria-selected="true"] {{
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
        color: white !important;
        border: 2px solid #5a67d8 !important;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
    }}
    
    .stDataFrame {{
        border-radius: 10px;
        overflow: hidden;
        box-shadow: 0 4px 15px rgba(0,0,0,0.08);
    }}
    
    .sankey-container {{
        background: white;
        border-radius: 15px;
        padding: 1.5rem;
        box-shadow: 0 6px 20px rgba(0,0,0,0.1);
        margin: 1rem 0;
    }}
    
    /* New CSS */
    .monthly-performance-card {{
        background: white;
        border-radius: 12px;
        padding: 1.5rem;
        margin: 0.5rem;
        box-shadow: 0 4px 12px rgba(0,0,0,0.08);
        border-left: 5px solid;
    }}
    
    .performance-under {{ border-left-color: #F44336; }}
    .performance-accurate {{ border-left-color: #4CAF50; }}
    .performance-over {{ border-left-color: #FF9800; }}
    
    .highlight-row {{
        background-color: #FFF9C4 !important;
        font-weight: bold !important;
    }}
    
    .warning-badge {{
        background: #FF5252;
        color: white;
        padding: 2px 8px;
        border-radius: 12px;
        font-size: 0.8rem;
        font-weight: bold;
    }}
    
    .success-badge {{
        background: #4CAF50;
        color: white;
        padding: 2px 8px;
        border-radius: 12px;
        font-size: 0.8rem;
        font-weight: bold;
    }}
    
    /* Compact metrics */
    .compact-metric {{
        background: white;
        border-radius: 10px;
        padding: 1rem;
        box-shadow: 0 4px 12px rgba(0,0,0,0.08);
        margin: 0.5rem 0;
    }}
    
    /* Brand performance */
    .brand-card {{
        background: white;
        border-radius: 12px;
        padding: 1rem;
        box-shadow: 0 4px 15px rgba(0,0,0,0.08);
        border-top: 4px solid #667eea;
    }}
    
    /* Financial cards */
    .financial-card {{
        background: white;
        border-radius: 12px;
        padding: 1.5rem;
        margin: 0.5rem 0;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        border-top: 4px solid;
        transition: all 0.3s ease;
    }}
    .financial-card:hover {{
        transform: translateY(-3px);
        box-shadow: 0 8px 25px rgba(0,0,0,0.15);
    }}
    .card-revenue {{ border-top-color: #667eea; }}
    .card-margin {{ border-top-color: #4CAF50; }}
    .card-cost {{ border-top-color: #FF9800; }}
    .card-inventory {{ border-top-color: #9C27B0; }}
    
    /* Dark mode support */
    @media (prefers-color-scheme: dark) {{
        .stApp {{
            background-color: #0E1117;
            color: #FFFFFF;
        }}
        .financial-card, .brand-card, .compact-metric {{
            background-color: #1E1E1E;
            color: #FFFFFF;
        }}
    }}
    
    /* Progress bar animation */
    @keyframes pulse {{
        0% {{ opacity: 1; }}
        50% {{ opacity: 0.7; }}
        100% {{ opacity: 1; }}
    }}
    
    .pulse-animation {{
        animation: pulse 2s infinite;
    }}
</style>
""", unsafe_allow_html=True)

# ============================================================================
# 📊 MAIN APP HEADER DENGAN RESPONSIVE
# ============================================================================

st.markdown('<h1 class="main-header">💰 FORECAST & INVENTORY CONTROL PRO DASHBOARD</h1>', unsafe_allow_html=True)

if is_mobile:
    st.caption(f"📱 Mobile View | Updated: {datetime.now().strftime('%d %b %Y')}")
else:
    st.caption(f"🚀 Inventory Control & Forecast Analytics - D2C Demand Planner Mulyanto | Real-time Insights | Updated: {datetime.now().strftime('%d %B %Y %H:%M')}")

# ============================================================================
# 📱 MOBILE-OPTIMIZED SIDEBAR
# ============================================================================

with st.sidebar:
    # Device info (for debugging)
    if st.session_state.get('debug_mode', False):
        st.info(f"Device: {device_type.upper()} | Mobile: {is_mobile}")
    
    if is_mobile:
        with st.expander("⚙️ Menu", expanded=False):
            refresh_btn = st.button("🔄 Refresh", use_container_width=True, type="primary")
            if st.button("📊 Data Stats", use_container_width=True):
                st.session_state.show_stats = True
    else:
        st.markdown("### ⚙️ Dashboard Controls")
        col_sb1, col_sb2 = st.columns(2)
        with col_sb1:
            refresh_btn = st.button("🔄 Refresh Data", use_container_width=True, type="primary")
        with col_sb2:
            if st.button("📊 Show Data Stats", use_container_width=True):
                st.session_state.show_stats = True
    
    st.markdown("---")
    
    # Data Overview dengan responsive
    st.markdown("### 📈 Data Overview")
    
    # Placeholder untuk metrics (akan diisi setelah data dimuat)
    data_loaded = False  # Akan diupdate setelah load data
    
    if st.session_state.get('data_loaded', False):
        # Contoh metrics
        responsive_metric("Active SKUs", "1,250")
        responsive_metric("Total Stock", "45,890")
        responsive_metric("Latest Accuracy", "85.2%", "+2.1%")
    else:
        st.info("📊 Data will appear after loading")
    
    # Threshold Settings dengan responsive design
    with st.expander("⚙️ Threshold Settings", expanded=False):
        under_threshold = st.slider("Under Forecast Threshold (%)", 0, 100, 80)
        over_threshold = st.slider("Over Forecast Threshold (%)", 100, 200, 120)
    
    # Inventory Thresholds
    st.markdown("---")
    st.markdown("### 📦 Inventory Thresholds")
    low_stock_threshold = st.slider("Low Stock (months)", 0.0, 2.0, 0.8, 0.1)
    high_stock_threshold = st.slider("High Stock (months)", 1.0, 6.0, 1.5, 0.1)
    
    # Financial Thresholds
    st.markdown("---")
    st.markdown("### 💰 Financial Thresholds")
    high_margin_threshold = st.slider("High Margin Threshold (%)", 0, 100, 40)
    low_margin_threshold = st.slider("Low Margin Threshold (%)", 0, 100, 20)
    
    # Dark mode toggle
    st.markdown("---")
    dark_mode = st.checkbox("🌙 Dark Mode", value=False)
    if dark_mode:
        st.markdown("""
        <style>
            .stApp { background-color: #0E1117; color: white; }
            .stDataFrame { background-color: #1E1E1E; }
        </style>
        """, unsafe_allow_html=True)
    
    # TOMBOL CETAK PDF
    st.markdown("---")
    import streamlit.components.v1 as components
    
    if st.button("🖨️ Save as PDF", use_container_width=True):
        # Script JavaScript untuk memicu dialog print browser
        components.html(
            """
            <script>
            window.print();
            </script>
            """,
            height=0,
            width=0
        )
    st.caption("Tip: Pilih Destination **'Save as PDF'** & centang **'Background graphics'** di settings print.")

# ============================================================================
# 🚀 BAGIAN UTAMA APLIKASI DENGAN RESPONSIVE DESIGN
# ============================================================================

# Display device info untuk debugging (opsional)
if st.session_state.get('debug_mode', False):
    st.info(f"Device: {device_type.upper()} | Mobile: {is_mobile}")

# ============================================================================
# 🔄 DATA LOADING FUNCTIONS (SAMA DENGAN APLIKASI UTAMA)
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

def validate_month_format(month_str):
    """Validate and standardize month formats"""
    if pd.isna(month_str):
        return datetime.now()
    
    month_str = str(month_str).strip().upper()
    
    # Mapping bulan
    month_map = {
        'JAN': 1, 'FEB': 2, 'MAR': 3, 'APR': 4, 'MAY': 5, 'JUN': 6,
        'JUL': 7, 'AUG': 8, 'SEP': 9, 'OCT': 10, 'NOV': 11, 'DEC': 12
    }
    
    formats_to_try = ['%b-%Y', '%b-%y', '%B %Y', '%m/%Y', '%Y-%m']
    
    for fmt in formats_to_try:
        try:
            return datetime.strptime(month_str, fmt)
        except:
            continue
    
    # Fallback: cari bulan dalam string
    for month_name, month_num in month_map.items():
        if month_name in month_str:
            # Cari tahun
            year_part = month_str.replace(month_name, '').replace('-', '').replace(' ', '').strip()
            if year_part and year_part.isdigit():
                year = int('20' + year_part) if len(year_part) == 2 else int(year_part)
            else:
                year = datetime.now().year
            
            return datetime(year, month_num, 1)
    
    return datetime.now()

def add_product_info_to_data(df, df_product):
    """Add Product_Name, Brand, SKU_Tier, Prices from Product_Master to any dataframe"""
    if df.empty or df_product.empty or 'SKU_ID' not in df.columns:
        return df
    
    # Get product info from Product_Master (including prices)
    price_cols = ['Floor_Price', 'Net_Order_Price'] if 'Floor_Price' in df_product.columns and 'Net_Order_Price' in df_product.columns else []
    
    product_info_cols = ['SKU_ID', 'Product_Name', 'Brand', 'SKU_Tier', 'Status'] + price_cols
    product_info_cols = [col for col in product_info_cols if col in df_product.columns]
    
    product_info = df_product[product_info_cols].copy()
    product_info = product_info.drop_duplicates(subset=['SKU_ID'])
    
    # Remove existing columns if they exist (except SKU_ID)
    cols_to_remove = []
    for col in ['Product_Name', 'Brand', 'SKU_Tier', 'Status', 'Floor_Price', 'Net_Order_Price']:
        if col in df.columns and col != 'SKU_ID':
            cols_to_remove.append(col)
    
    if cols_to_remove:
        df_temp = df.drop(columns=cols_to_remove)
    else:
        df_temp = df.copy()
    
    # Merge with product info
    df_result = pd.merge(df_temp, product_info, on='SKU_ID', how='left')
    return df_result

@st.cache_data(ttl=300, max_entries=3, show_spinner=False)
def load_and_process_data(_client):
    """
    Load semua data termasuk sheet baru: BS_Fullfilment_Cost
    """
    
    sheet_id = "1jcs8L0CysdzxemPz1EYVVfVhsSR-ik46khIw5jhhBgw"
    data = {}

    # --- HELPER: Baca Sheet Manual ---
    def safe_read_stock_sheet(sheet_name):
        try:
            ws = _client.open_by_key(sheet_id).worksheet(sheet_name)
            raw_data = ws.get_all_values()
            if len(raw_data) < 2: return pd.DataFrame()
            headers = [str(h).strip() for h in raw_data[0]]
            df = pd.DataFrame(raw_data[1:], columns=headers)
            df = df.loc[:, df.columns != '']
            return df
        except: return pd.DataFrame()

    try:
        # 1. PRODUCT MASTER
        ws_prod = _client.open_by_key(sheet_id).worksheet("Product_Master")
        df_product = pd.DataFrame(ws_prod.get_all_records())
        df_product.columns = [col.strip().replace(' ', '_') for col in df_product.columns]
        
        for col in ['Floor_Price', 'Net_Order_Price']:
            if col in df_product.columns:
                df_product[col] = pd.to_numeric(df_product[col], errors='coerce').fillna(0)
        
        if 'Status' not in df_product.columns: df_product['Status'] = 'Active'
        df_product_active = df_product[df_product['Status'].str.upper() == 'ACTIVE'].copy()
        active_skus = df_product_active['SKU_ID'].tolist()
        
        data['product'] = df_product
        data['product_active'] = df_product_active

        # 2. SALES DATA
        ws_sales = _client.open_by_key(sheet_id).worksheet("Sales")
        df_sales_raw = pd.DataFrame(ws_sales.get_all_records())
        df_sales_raw.columns = [col.strip() for col in df_sales_raw.columns]
        month_cols = [c for c in df_sales_raw.columns if any(m in c.upper() for m in ['JAN','FEB','MAR','APR','MAY','JUN','JUL','AUG','SEP','OCT','NOV','DEC'])]
        if month_cols and 'SKU_ID' in df_sales_raw.columns:
            id_cols = ['SKU_ID']
            for col in ['SKU_Name', 'Product_Name', 'Brand', 'SKU_Tier']:
                if col in df_sales_raw.columns: id_cols.append(col)
            df_sales_long = df_sales_raw.melt(id_vars=id_cols, value_vars=month_cols, var_name='Month_Label', value_name='Sales_Qty')
            df_sales_long['Sales_Qty'] = pd.to_numeric(df_sales_long['Sales_Qty'], errors='coerce').fillna(0)
            df_sales_long['Month'] = df_sales_long['Month_Label'].apply(validate_month_format)
            df_sales_long = df_sales_long[df_sales_long['SKU_ID'].isin(active_skus)]
            df_sales_long = add_product_info_to_data(df_sales_long, df_product)
            data['sales'] = df_sales_long.sort_values('Month')

        # 3. ROFO DATA
        ws_rofo = _client.open_by_key(sheet_id).worksheet("Rofo")
        df_rofo_raw = pd.DataFrame(ws_rofo.get_all_records())
        df_rofo_raw.columns = [col.strip() for col in df_rofo_raw.columns]
        month_cols_rofo = [c for c in df_rofo_raw.columns if any(m in c.upper() for m in ['JAN','FEB','MAR','APR','MAY','JUN','JUL','AUG','SEP','OCT','NOV','DEC'])]
        if month_cols_rofo:
            id_cols_rofo = ['SKU_ID']
            for col in ['Product_Name', 'Brand']:
                if col in df_rofo_raw.columns: id_cols_rofo.append(col)
            df_rofo_long = df_rofo_raw.melt(id_vars=id_cols_rofo, value_vars=month_cols_rofo, var_name='Month_Label', value_name='Forecast_Qty')
            df_rofo_long['Forecast_Qty'] = pd.to_numeric(df_rofo_long['Forecast_Qty'], errors='coerce').fillna(0)
            df_rofo_long['Month'] = df_rofo_long['Month_Label'].apply(validate_month_format)
            df_rofo_long = df_rofo_long[df_rofo_long['SKU_ID'].isin(active_skus)]
            df_rofo_long = add_product_info_to_data(df_rofo_long, df_product)
            data['forecast'] = df_rofo_long

        # 4. PO DATA
        ws_po = _client.open_by_key(sheet_id).worksheet("PO")
        df_po_raw = pd.DataFrame(ws_po.get_all_records())
        df_po_raw.columns = [col.strip() for col in df_po_raw.columns]
        month_cols_po = [c for c in df_po_raw.columns if any(m in c.upper() for m in ['JAN','FEB','MAR','APR','MAY','JUN','JUL','AUG','SEP','OCT','NOV','DEC'])]
        if month_cols_po and 'SKU_ID' in df_po_raw.columns:
            df_po_long = df_po_raw.melt(id_vars=['SKU_ID'], value_vars=month_cols_po, var_name='Month_Label', value_name='PO_Qty')
            df_po_long['PO_Qty'] = pd.to_numeric(df_po_long['PO_Qty'], errors='coerce').fillna(0)
            df_po_long['Month'] = df_po_long['Month_Label'].apply(validate_month_format)
            df_po_long = df_po_long[df_po_long['SKU_ID'].isin(active_skus)]
            df_po_long = add_product_info_to_data(df_po_long, df_product)
            data['po'] = df_po_long

        # 5. STOCK DATA
        df_stock_raw = safe_read_stock_sheet("Stock_Onhand")
        if not df_stock_raw.empty:
            col_mapping = {
                'SKU_ID': 'SKU_ID', 'Qty_Available': 'Stock_Qty', 'Product_Code': 'Anchanto_Code',
                'Stock_Category': 'Stock_Category', 'Expiry_Date': 'Expiry_Date', 'Product_Name': 'Product_Name'
            }
            if 'SKU_ID' in df_stock_raw.columns and 'Qty_Available' in df_stock_raw.columns:
                cols_to_use = [c for c in col_mapping.keys() if c in df_stock_raw.columns]
                df_stock = df_stock_raw[cols_to_use].copy()
                df_stock = df_stock.rename(columns=col_mapping)
                df_stock['Stock_Qty'] = pd.to_numeric(df_stock['Stock_Qty'], errors='coerce').fillna(0)
                df_stock['SKU_ID'] = df_stock['SKU_ID'].astype(str).str.strip()
                if 'Floor_Price' in df_product.columns:
                    df_stock = pd.merge(df_stock, df_product[['SKU_ID', 'Floor_Price', 'Net_Order_Price']], on='SKU_ID', how='left')
                data['stock'] = df_stock
            else:
                data['stock'] = pd.DataFrame(columns=['SKU_ID', 'Stock_Qty'])
        else:
            data['stock'] = pd.DataFrame(columns=['SKU_ID', 'Stock_Qty'])

        # 6. FORECAST 2026 ECOMM
        try:
            ws_ecomm = _client.open_by_key(sheet_id).worksheet("Forecast_2026_Ecomm")
            df_ecomm_raw = pd.DataFrame(ws_ecomm.get_all_records())
            df_ecomm_raw.columns = [col.strip().replace(' ', '_') for col in df_ecomm_raw.columns]
            month_cols_ecomm = [c for c in df_ecomm_raw.columns if any(m in c.upper() for m in ['JAN','FEB','MAR','APR','MAY','JUN','JUL','AUG','SEP','OCT','NOV','DEC'])]
            for col in month_cols_ecomm:
                df_ecomm_raw[col] = pd.to_numeric(df_ecomm_raw[col], errors='coerce').fillna(0)
            data['ecomm_forecast'] = df_ecomm_raw
            data['ecomm_forecast_month_cols'] = month_cols_ecomm
        except:
            data['ecomm_forecast'] = pd.DataFrame()
            data['ecomm_forecast_month_cols'] = []
        
        # 7. FORECAST 2026 RESELLER
        try:
            ws_reseller = _client.open_by_key(sheet_id).worksheet("Forecast_2026_Reseller")
            df_reseller_raw = pd.DataFrame(ws_reseller.get_all_records())
            df_reseller_raw.columns = [col.strip().replace(' ', '_') for col in df_reseller_raw.columns]
            all_month_cols_res = [c for c in df_reseller_raw.columns if any(m in c.upper() for m in ['JAN','FEB','MAR','APR','MAY','JUN','JUL','AUG','SEP','OCT','NOV','DEC'])]
            for col in all_month_cols_res:
                df_reseller_raw[col] = pd.to_numeric(df_reseller_raw[col], errors='coerce').fillna(0)
            
            forecast_start_date = datetime(2026, 1, 1)
            def is_forecast_month(month_str):
                try:
                    month_str = str(month_str).upper().replace('_', ' ').replace('-', ' ')
                    if ' ' in month_str:
                        month_part, year_part = month_str.split(' ')
                        month_num = datetime.strptime(month_part[:3], '%b').month
                        year_clean = ''.join(filter(str.isdigit, year_part))
                        year = 2000 + int(year_clean) if len(year_clean) == 2 else int(year_clean)
                        return datetime(year, month_num, 1) >= forecast_start_date
                except: return False
                return False
            
            hist_cols = [c for c in all_month_cols_res if not is_forecast_month(c)]
            fcst_cols = [c for c in all_month_cols_res if is_forecast_month(c)]
            data['reseller_forecast'] = df_reseller_raw
            data['reseller_all_month_cols'] = all_month_cols_res
            data['reseller_historical_cols'] = hist_cols
            data['reseller_forecast_cols'] = fcst_cols
        except:
            data['reseller_forecast'] = pd.DataFrame()
            data['reseller_all_month_cols'] = []
            data['reseller_historical_cols'] = []
            data['reseller_forecast_cols'] = []

        # ==============================================================================
        # 8. BS FULLFILMENT COST (NEW SHEET)
        # ==============================================================================
        try:
            ws_bs = _client.open_by_key(sheet_id).worksheet("BS_Fullfilment_Cost")
            df_bs = pd.DataFrame(ws_bs.get_all_records())
            
            # Cleaning Headers & Data
            # Hapus spasi di nama kolom
            df_bs.columns = [c.strip() for c in df_bs.columns]
            
            # Helper untuk bersihkan angka (hapus koma dan persen)
            def clean_currency(x):
                if isinstance(x, str):
                    return pd.to_numeric(x.replace(',', '').replace('%', ''), errors='coerce')
                return x

            # List kolom angka yang perlu dibersihkan
            numeric_cols = ['Total Order(BS)', 'GMV (Fullfil By BS)', 'GMV Total (MP)', 'Total Cost', 'BSA', '%Cost']
            
            for col in numeric_cols:
                if col in df_bs.columns:
                    df_bs[col] = df_bs[col].apply(clean_currency).fillna(0)
            
            # Convert Percentages (karena 3.14% jadi 3.14, mungkin perlu dibagi 100 utk kalkulasi, tapi utk display biar saja)
            # Kita tandai kolom ini
            
            # Parse Date (Apr-25)
            df_bs['Month_Date'] = pd.to_datetime(df_bs['Month'], format='%b-%y', errors='coerce')
            df_bs = df_bs.sort_values('Month_Date')
            
            data['fulfillment'] = df_bs
            
        except Exception as e:
            st.warning(f"Gagal load BS_Fullfilment_Cost: {e}")
            data['fulfillment'] = pd.DataFrame()

        return data
        
    except Exception as e:
        st.error(f"Error loading data: {str(e)}")
        return {}

# --- FUNGSI BARU: LOAD DATA RESELLER LENGKAP ---
@st.cache_data(ttl=300, show_spinner=False)
def load_reseller_complete_data(_client):
    """
    Load SEMUA data reseller: forecast, sales, past rofo, past PO
    """
    # Gunakan sheet_id yang sudah ada
    sheet_id = "1jcs8L0CysdzxemPz1EYVVfVhsSR-ik46khIw5jhhBgw"
    reseller_data = {}
    
    try:
        # 1. FORECAST 2026 RESELLER
        ws_fcst = _client.open_by_key(sheet_id).worksheet("Forecast_2026_Reseller")
        df_fcst_raw = pd.DataFrame(ws_fcst.get_all_records())
        df_fcst_raw.columns = [col.strip() for col in df_fcst_raw.columns]
        
        # Identifikasi kolom bulan
        all_month_cols = [c for c in df_fcst_raw.columns if any(m in c.upper() for m in 
                      ['JAN','FEB','MAR','APR','MAY','JUN','JUL','AUG','SEP','OCT','NOV','DEC'])]
        
        # Pisahkan 2025 (history) vs 2026+ (forecast)
        hist_cols = []
        fcst_cols = []
        
        for col in all_month_cols:
            col_str = str(col).upper()
            if '25' in col_str or '2025' in col_str:
                hist_cols.append(col)
            else:
                fcst_cols.append(col)  # 2026, 2027, dll
        
        # Convert numeric
        for col in all_month_cols:
            df_fcst_raw[col] = pd.to_numeric(df_fcst_raw[col], errors='coerce').fillna(0)
        
        reseller_data['forecast'] = df_fcst_raw
        reseller_data['forecast_month_cols'] = fcst_cols
        reseller_data['historical_month_cols'] = hist_cols
        
        # 2. SALES RESELLER
        try:
            ws_sales = _client.open_by_key(sheet_id).worksheet("Sales_Reseller")
            df_sales_raw = pd.DataFrame(ws_sales.get_all_records())
            df_sales_raw.columns = [col.strip() for col in df_sales_raw.columns]
            
            # Transform ke long format
            month_cols_sales = [c for c in df_sales_raw.columns if any(m in c.upper() for m in 
                          ['JAN','FEB','MAR','APR','MAY','JUN','JUL','AUG','SEP','OCT','NOV','DEC'])]
            
            if month_cols_sales and 'SKU_ID' in df_sales_raw.columns:
                id_cols_sales = ['SKU_ID', 'Brand', 'Product_Name', 'SKU_Tier', 'Floor_Price']
                id_cols_sales = [c for c in id_cols_sales if c in df_sales_raw.columns]
                
                df_sales_long = df_sales_raw.melt(
                    id_vars=id_cols_sales,
                    value_vars=month_cols_sales,
                    var_name='Month_Label',
                    value_name='Sales_Qty'
                )
                df_sales_long['Sales_Qty'] = pd.to_numeric(df_sales_long['Sales_Qty'], errors='coerce').fillna(0)
                df_sales_long['Month'] = df_sales_long['Month_Label'].apply(validate_month_format)
                reseller_data['sales'] = df_sales_long
        except Exception as e:
            st.warning(f"⚠️ Sales_Reseller sheet not accessible: {str(e)}")
        
        # 3. PAST ROFO RESELLER
        try:
            ws_rofo = _client.open_by_key(sheet_id).worksheet("Past_Rofo_Reseller")
            df_rofo_raw = pd.DataFrame(ws_rofo.get_all_records())
            df_rofo_raw.columns = [col.strip() for col in df_rofo_raw.columns]
            
            month_cols_rofo = [c for c in df_rofo_raw.columns if any(m in c.upper() for m in 
                          ['JAN','FEB','MAR','APR','MAY','JUN','JUL','AUG','SEP','OCT','NOV','DEC'])]
            
            if month_cols_rofo and 'SKU_ID' in df_rofo_raw.columns:
                id_cols_rofo = ['SKU_ID', 'Brand', 'Product_Name', 'SKU_Tier', 'Floor_Price']
                id_cols_rofo = [c for c in id_cols_rofo if c in df_rofo_raw.columns]
                
                df_rofo_long = df_rofo_raw.melt(
                    id_vars=id_cols_rofo,
                    value_vars=month_cols_rofo,
                    var_name='Month_Label',
                    value_name='Forecast_Qty'
                )
                df_rofo_long['Forecast_Qty'] = pd.to_numeric(df_rofo_long['Forecast_Qty'], errors='coerce').fillna(0)
                df_rofo_long['Month'] = df_rofo_long['Month_Label'].apply(validate_month_format)
                reseller_data['past_rofo'] = df_rofo_long
        except Exception as e:
            st.warning(f"⚠️ Past_Rofo_Reseller sheet not accessible: {str(e)}")
        
        # 4. PAST PO RESELLER
        try:
            ws_po = _client.open_by_key(sheet_id).worksheet("Past_PO_Reseller")
            df_po_raw = pd.DataFrame(ws_po.get_all_records())
            df_po_raw.columns = [col.strip() for col in df_po_raw.columns]
            
            month_cols_po = [c for c in df_po_raw.columns if any(m in c.upper() for m in 
                          ['JAN','FEB','MAR','APR','MAY','JUN','JUL','AUG','SEP','OCT','NOV','DEC'])]
            
            if month_cols_po and 'SKU_ID' in df_po_raw.columns:
                id_cols_po = ['SKU_ID', 'Brand', 'Product_Name', 'SKU_Tier', 'Floor_Price']
                id_cols_po = [c for c in id_cols_po if c in df_po_raw.columns]
                
                df_po_long = df_po_raw.melt(
                    id_vars=id_cols_po,
                    value_vars=month_cols_po,
                    var_name='Month_Label',
                    value_name='PO_Qty'
                )
                df_po_long['PO_Qty'] = pd.to_numeric(df_po_long['PO_Qty'], errors='coerce').fillna(0)
                df_po_long['Month'] = df_po_long['Month_Label'].apply(validate_month_format)
                reseller_data['past_po'] = df_po_long
        except Exception as e:
            st.warning(f"⚠️ Past_PO_Reseller sheet not accessible: {str(e)}")
        
        return reseller_data
        
    except Exception as e:
        st.error(f"❌ Error loading reseller data: {str(e)}")
        return {}

# ============================================================================
# 📊 FUNGSI ANALYTICS (SAMA DENGAN APLIKASI UTAMA)
# ============================================================================

# --- Fungsi-fungsi analytics dari aplikasi utama ---
def calculate_monthly_performance(df_forecast, df_po, df_product):
    """Calculate performance for each month separately - HANYA SKU dengan Forecast_Qty > 0"""
    # Implementasi fungsi ini dari aplikasi utama
    pass

def calculate_inventory_metrics_with_3month_avg(df_stock, df_sales, df_product):
    """Calculate inventory metrics using 3-month average sales"""
    # Implementasi fungsi ini dari aplikasi utama
    pass

def calculate_sales_vs_forecast_po(df_sales, df_forecast, df_po, df_product):
    """Calculate sales vs forecast and PO comparison"""
    # Implementasi fungsi ini dari aplikasi utama
    pass

def calculate_brand_performance(df_forecast, df_po, df_product):
    """Calculate forecast accuracy performance by brand"""
    # Implementasi fungsi ini dari aplikasi utama
    pass

def calculate_financial_metrics_all(df_sales, df_product):
    """Calculate all financial metrics from sales data"""
    # Implementasi fungsi ini dari aplikasi utama
    pass

def calculate_inventory_financial(df_stock, df_product):
    """Calculate inventory financial value"""
    # Implementasi fungsi ini dari aplikasi utama
    pass

def calculate_seasonality(df_financial):
    """Calculate seasonal patterns from financial data"""
    # Implementasi fungsi ini dari aplikasi utama
    pass

# ============================================================================
# 📱 IMPLEMENTASI RESPONSIVE MAIN CONTENT
# ============================================================================

# Initialize connection
client = init_gsheet_connection()

if client is None:
    st.error("❌ Tidak dapat terhubung ke Google Sheets")
    st.stop()

# Load and process data
with st.spinner('🔄 Loading and processing data from Google Sheets...'):
    all_data = load_and_process_data(client)
    
    df_product = all_data.get('product', pd.DataFrame())
    df_product_active = all_data.get('product_active', pd.DataFrame())
    df_sales = all_data.get('sales', pd.DataFrame())
    df_forecast = all_data.get('forecast', pd.DataFrame())
    df_po = all_data.get('po', pd.DataFrame())
    df_stock = all_data.get('stock', pd.DataFrame())
    df_ecomm_forecast = all_data.get('ecomm_forecast', pd.DataFrame())
    df_reseller_forecast = all_data.get('reseller_forecast', pd.DataFrame())
    df_fulfillment = all_data.get('fulfillment', pd.DataFrame())
    
    # Update session state
    st.session_state.data_loaded = True

# Calculate metrics (skeleton)
if not df_forecast.empty and not df_po.empty:
    monthly_performance = calculate_monthly_performance(df_forecast, df_po, df_product)
    # Hitung metrics lainnya...
else:
    st.warning("⚠️ Data forecast atau PO tidak tersedia")

# ============================================================================
# 📱 RESPONSIVE TABS IMPLEMENTATION
# ============================================================================

# Tentukan tab names berdasarkan device
if is_mobile:
    # Mobile: simplified tabs
    mobile_tab = st.selectbox(
        "Navigate:",
        ["📊 Overview", "📦 Inventory", "💰 Finance", "⚙️ More"],
        label_visibility="collapsed"
    )
    
    # Render content based on selected tab
    if mobile_tab == "📊 Overview":
        st.subheader("📊 Overview")
        # Tampilkan overview metrics dengan responsive design
        if monthly_performance:
            # Contoh: tampilkan metrics sederhana untuk mobile
            col1, col2 = create_responsive_columns(2)
            with col1:
                responsive_metric("Total SKUs", "1,250")
            with col2:
                responsive_metric("Avg Accuracy", "85.2%")
            
            # Tampilkan chart sederhana
            st.plotly_chart(go.Figure(
                data=[go.Bar(x=['Jan', 'Feb', 'Mar'], y=[100, 200, 150])],
                layout=go.Layout(height=300)
            ), use_container_width=True)
    
    elif mobile_tab == "📦 Inventory":
        st.subheader("📦 Inventory")
        # Tampilkan inventory summary untuk mobile
    
    elif mobile_tab == "💰 Finance":
        st.subheader("💰 Finance")
        # Tampilkan financial metrics untuk mobile
    
    else:
        st.subheader("⚙️ Settings & More")
        # Tampilkan settings dan info lainnya

else:
    # Desktop: Full tabs (10 tabs seperti aplikasi utama)
    tab_names = [
        "📈 Monthly Performance",
        "🏷️ Brand Analysis", 
        "📦 Inventory",
        "🔍 SKU Evaluation",
        "📈 Sales Analysis",
        "📋 Data Explorer",
        "🛒 Ecommerce",
        "💰 Profitability",
        "🤝 Reseller",
        "🚚 Fulfillment"
    ]
    
    # Buat tabs
    tabs = st.tabs(tab_names)
    
    # Isi masing-masing tab (akan diisi dengan logika dari aplikasi utama)
    # Contoh: Tab 1 - Monthly Performance
    with tabs[0]:
        st.subheader("📈 Monthly Performance Details")
        # Implementasi logika dari aplikasi utama Tab 1
    
    # Tab 2 - Brand Analysis
    with tabs[1]:
        st.subheader("🏷️ Forecast Performance by Brand & Tier Analysis")
        # Implementasi logika dari aplikasi utama Tab 2
    
    # ... dan seterusnya untuk tab lainnya

# ============================================================================
# 📱 FOOTER RESPONSIVE
# ============================================================================

st.divider()

if is_mobile:
    footer = f"""
    <div style="text-align: center; color: #666; font-size: 0.8rem; padding: 0.5rem;">
        <p>📱 Inventory Mobile v6.1 | {datetime.now().strftime('%d %b %Y')}</p>
    </div>
    """
else:
    footer = f"""
    <div style="text-align: center; color: #666; font-size: 0.9rem; padding: 1rem;">
        <p>🚀 Inventory Intelligence Dashboard v6.1 | Updated: {datetime.now().strftime('%d %B %Y %H:%M')}</p>
        <p>✅ Mobile Optimized | ✅ Responsive Design | ✅ Real-time Updates</p>
    </div>
    """

st.markdown(footer, unsafe_allow_html=True)

# ============================================================================
# 📱 JAVASCRIPT FOR DEVICE DETECTION
# ============================================================================

st.markdown("""
<script>
// Simple device detection
function updateDeviceInfo() {
    const width = window.innerWidth;
    const isMobile = width <= 768;
    const isTablet = width > 768 && width <= 1024;
    
    // Update URL for Streamlit to detect
    const url = new URL(window.location.href);
    
    if (isMobile) {
        url.searchParams.set('mobile', 'true');
        url.searchParams.delete('tablet');
    } else if (isTablet) {
        url.searchParams.set('tablet', 'true');
        url.searchParams.delete('mobile');
    } else {
        url.searchParams.delete('mobile');
        url.searchParams.delete('tablet');
    }
    
    // Only update if changed
    if (url.href !== window.location.href) {
        window.history.replaceState({}, '', url);
        
        // For Streamlit Cloud, we need to trigger a rerun
        setTimeout(() => {
            if (window.frameElement && window.frameElement.id === 'streamlitFrame') {
                window.parent.location.reload();
            }
        }, 100);
    }
}

// Run on load and resize
window.addEventListener('load', updateDeviceInfo);
window.addEventListener('resize', updateDeviceInfo);

// Initial call
updateDeviceInfo();
</script>
""", unsafe_allow_html=True)
