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
        col_sb1, col_sb2 = create_responsive_columns(2)
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
    
    # These will be populated after data is loaded
    placeholder = st.empty()
    
    # Threshold Settings dengan responsive design
    with st.expander("⚙️ Forecast Thresholds", expanded=False):
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
# 🔄 DATA LOADING FUNCTIONS (DARI APLIKASI UTAMA)
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
# 📊 FUNGSI ANALYTICS (DARI APLIKASI UTAMA - LENGKAP)
# ============================================================================

# --- ====================================================== ---
# ---                FINANCIAL FUNCTIONS                    ---
# --- ====================================================== ---

@st.cache_data(ttl=300)
def calculate_financial_metrics_all(df_sales, df_product):
    """Calculate all financial metrics from sales data"""
    
    if df_sales.empty or df_product.empty:
        return pd.DataFrame()
    
    try:
        # Check if price columns exist
        required_price_cols = ['Floor_Price', 'Net_Order_Price']
        price_cols_exist = all(col in df_product.columns for col in required_price_cols)
        
        if not price_cols_exist:
            st.warning("⚠️ Price columns missing in Product Master")
            return pd.DataFrame()
        
        # Ensure sales data has product info with prices
        if 'Floor_Price' not in df_sales.columns or 'Net_Order_Price' not in df_sales.columns:
            df_sales = add_product_info_to_data(df_sales, df_product)
        
        # Fill missing prices
        df_sales['Floor_Price'] = df_sales['Floor_Price'].fillna(0)
        df_sales['Net_Order_Price'] = df_sales['Net_Order_Price'].fillna(0)
        
        # Calculate financial metrics
        df_sales['Revenue'] = df_sales['Sales_Qty'] * df_sales['Floor_Price']
        df_sales['Cost'] = df_sales['Sales_Qty'] * df_sales['Net_Order_Price']
        df_sales['Gross_Margin'] = df_sales['Revenue'] - df_sales['Cost']
        df_sales['Margin_Percentage'] = np.where(
            df_sales['Revenue'] > 0,
            (df_sales['Gross_Margin'] / df_sales['Revenue'] * 100),
            0
        )
        
        # Add additional metrics
        df_sales['Avg_Selling_Price'] = np.where(
            df_sales['Sales_Qty'] > 0,
            df_sales['Revenue'] / df_sales['Sales_Qty'],
            0
        )
        
        return df_sales
        
    except Exception as e:
        st.error(f"Financial metrics calculation error: {str(e)}")
        return pd.DataFrame()

@st.cache_data(ttl=300)
def calculate_inventory_financial(df_stock, df_product):
    """Calculate inventory financial value"""
    
    if df_stock.empty or df_product.empty:
        return pd.DataFrame()
    
    try:
        # Check price columns
        if 'Floor_Price' not in df_product.columns or 'Net_Order_Price' not in df_product.columns:
            return pd.DataFrame()
        
        # Ensure stock data has prices
        if 'Floor_Price' not in df_stock.columns or 'Net_Order_Price' not in df_stock.columns:
            df_stock = add_product_info_to_data(df_stock, df_product)
        
        # Fill missing prices
        df_stock['Floor_Price'] = df_stock['Floor_Price'].fillna(0)
        df_stock['Net_Order_Price'] = df_stock['Net_Order_Price'].fillna(0)
        
        # Calculate inventory values
        df_stock['Value_at_Cost'] = df_stock['Stock_Qty'] * df_stock['Net_Order_Price']
        df_stock['Value_at_Retail'] = df_stock['Stock_Qty'] * df_stock['Floor_Price']
        df_stock['Potential_Margin'] = df_stock['Value_at_Retail'] - df_stock['Value_at_Cost']
        df_stock['Margin_Percentage'] = np.where(
            df_stock['Value_at_Retail'] > 0,
            (df_stock['Potential_Margin'] / df_stock['Value_at_Retail'] * 100),
            0
        )
        
        return df_stock
        
    except Exception as e:
        st.error(f"Inventory financial calculation error: {str(e)}")
        return pd.DataFrame()

@st.cache_data(ttl=300)
def calculate_seasonality(df_financial):
    """Calculate seasonal patterns from financial data"""
    
    if df_financial.empty:
        return pd.DataFrame()
    
    try:
        # Add month and year columns
        df_financial['Year'] = df_financial['Month'].dt.year
        df_financial['Month_Num'] = df_financial['Month'].dt.month
        df_financial['Month_Name'] = df_financial['Month'].dt.strftime('%b')
        
        # Group by month across years
        seasonal_pattern = df_financial.groupby(['Month_Num', 'Month_Name']).agg({
            'Revenue': 'mean',
            'Gross_Margin': 'mean',
            'Sales_Qty': 'mean'
        }).reset_index()
        
        # Calculate seasonal indices
        overall_avg_revenue = seasonal_pattern['Revenue'].mean()
        seasonal_pattern['Seasonal_Index_Revenue'] = seasonal_pattern['Revenue'] / overall_avg_revenue
        
        overall_avg_margin = seasonal_pattern['Gross_Margin'].mean()
        seasonal_pattern['Seasonal_Index_Margin'] = seasonal_pattern['Gross_Margin'] / overall_avg_margin
        
        # Classify seasons
        conditions = [
            seasonal_pattern['Seasonal_Index_Revenue'] >= 1.2,
            (seasonal_pattern['Seasonal_Index_Revenue'] >= 0.9) & (seasonal_pattern['Seasonal_Index_Revenue'] < 1.2),
            seasonal_pattern['Seasonal_Index_Revenue'] < 0.9
        ]
        choices = ['Peak Season', 'Normal Season', 'Low Season']
        
        seasonal_pattern['Season_Type'] = np.select(conditions, choices, default='Normal Season')
        
        return seasonal_pattern.sort_values('Month_Num')
        
    except Exception as e:
        st.error(f"Seasonality calculation error: {str(e)}")
        return pd.DataFrame()

def calculate_eoq(demand, order_cost, holding_cost_per_unit):
    """Calculate Economic Order Quantity"""
    if demand <= 0 or order_cost <= 0 or holding_cost_per_unit <= 0:
        return 0
    
    eoq = math.sqrt((2 * demand * order_cost) / holding_cost_per_unit)
    return round(eoq)

def calculate_forecast_bias(df_forecast, df_po):
    """Calculate forecast bias (systematic over/under forecasting)"""
    
    if df_forecast.empty or df_po.empty:
        return {}
    
    try:
        # Get common months
        forecast_months = sorted(df_forecast['Month'].unique())
        po_months = sorted(df_po['Month'].unique())
        common_months = sorted(set(forecast_months) & set(po_months))
        
        if not common_months:
            return {}
        
        bias_results = []
        
        for month in common_months:
            df_f_month = df_forecast[df_forecast['Month'] == month]
            df_p_month = df_po[df_po['Month'] == month]
            
            # Merge forecast and PO
            df_merged = pd.merge(
                df_f_month[['SKU_ID', 'Forecast_Qty']],
                df_p_month[['SKU_ID', 'PO_Qty']],
                on='SKU_ID',
                how='inner'
            )
            
            # Calculate bias
            df_merged['Bias'] = df_merged['PO_Qty'] - df_merged['Forecast_Qty']
            df_merged['Bias_Percentage'] = np.where(
                df_merged['Forecast_Qty'] > 0,
                (df_merged['Bias'] / df_merged['Forecast_Qty'] * 100),
                0
            )
            
            avg_bias = df_merged['Bias'].mean()
            avg_bias_pct = df_merged['Bias_Percentage'].mean()
            
            bias_results.append({
                'Month': month,
                'Avg_Bias': avg_bias,
                'Avg_Bias_Percentage': avg_bias_pct,
                'Over_Forecast_SKUs': len(df_merged[df_merged['Bias'] > 0]),
                'Under_Forecast_SKUs': len(df_merged[df_merged['Bias'] < 0])
            })
        
        return pd.DataFrame(bias_results)
        
    except Exception as e:
        st.error(f"Forecast bias calculation error: {str(e)}")
        return pd.DataFrame()

# --- ====================================================== ---
# ---                ANALYTICS FUNCTIONS                    ---
# --- ====================================================== ---

def calculate_monthly_performance(df_forecast, df_po, df_product):
    """Calculate performance for each month separately - HANYA SKU dengan Forecast_Qty > 0"""
    
    monthly_performance = {}
    
    if df_forecast.empty or df_po.empty:
        return monthly_performance
    
    try:
        # ADD PRODUCT INFO jika belum ada
        df_forecast = add_product_info_to_data(df_forecast, df_product)
        df_po = add_product_info_to_data(df_po, df_product)
        
        # Get unique months from both datasets
        forecast_months = sorted(df_forecast['Month'].unique())
        po_months = sorted(df_po['Month'].unique())
        all_months = sorted(set(list(forecast_months) + list(po_months)))
        
        for month in all_months:
            # Get data for this month - FILTER HANYA Forecast_Qty > 0
            df_forecast_month = df_forecast[
                (df_forecast['Month'] == month) & 
                (df_forecast['Forecast_Qty'] > 0)
            ].copy()
            
            df_po_month = df_po[df_po['Month'] == month].copy()
            
            if df_forecast_month.empty or df_po_month.empty:
                continue
            
            # Merge forecast and PO for this month
            df_merged = pd.merge(
                df_forecast_month,
                df_po_month,
                on=['SKU_ID'],
                how='inner',
                suffixes=('_forecast', '_po')
            )
            
            if not df_merged.empty:
                # Add product info (jika belum ada dari merge)
                if 'Product_Name' not in df_merged.columns or 'Brand' not in df_merged.columns:
                    df_merged = add_product_info_to_data(df_merged, df_product)
                
                # Calculate ratio - Pastikan Forecast_Qty > 0
                df_merged['PO_Rofo_Ratio'] = np.where(
                    df_merged['Forecast_Qty'] > 0,
                    (df_merged['PO_Qty'] / df_merged['Forecast_Qty']) * 100,
                    0
                )
                
                # Categorize
                conditions = [
                    df_merged['PO_Rofo_Ratio'] < 80,
                    (df_merged['PO_Rofo_Ratio'] >= 80) & (df_merged['PO_Rofo_Ratio'] <= 120),
                    df_merged['PO_Rofo_Ratio'] > 120
                ]
                choices = ['Under', 'Accurate', 'Over']
                df_merged['Accuracy_Status'] = np.select(conditions, choices, default='Unknown')
                
                # Calculate metrics
                df_merged['Absolute_Percentage_Error'] = abs(df_merged['PO_Rofo_Ratio'] - 100)
                
                # Hanya hitung MAPE untuk SKU dengan Forecast_Qty > 0
                valid_skus = df_merged[df_merged['Forecast_Qty'] > 0]
                if not valid_skus.empty:
                    mape = valid_skus['Absolute_Percentage_Error'].mean()
                else:
                    mape = 0
                    
                monthly_accuracy = 100 - mape
                
                # Status counts
                status_counts = df_merged['Accuracy_Status'].value_counts().to_dict()
                total_records = len(df_merged)
                status_percentages = {k: (v/total_records*100) for k, v in status_counts.items()}
                
                # Store results
                monthly_performance[month] = {
                    'accuracy': monthly_accuracy,
                    'mape': mape,
                    'status_counts': status_counts,
                    'status_percentages': status_percentages,
                    'total_records': total_records,
                    'data': df_merged,
                    'under_skus': df_merged[df_merged['Accuracy_Status'] == 'Under'].copy(),
                    'over_skus': df_merged[df_merged['Accuracy_Status'] == 'Over'].copy(),
                    'accurate_skus': df_merged[df_merged['Accuracy_Status'] == 'Accurate'].copy()
                }
        
        return monthly_performance
        
    except Exception as e:
        st.error(f"Monthly performance calculation error: {str(e)}")
        return monthly_performance

def get_last_3_months_performance(monthly_performance):
    """Get performance for last 3 months"""
    
    if not monthly_performance:
        return {}
    
    # Get last 3 months
    sorted_months = sorted(monthly_performance.keys())
    if len(sorted_months) >= 3:
        last_3_months = sorted_months[-3:]
    else:
        last_3_months = sorted_months
    
    last_3_data = {}
    for month in last_3_months:
        last_3_data[month] = monthly_performance[month]
    
    return last_3_data

@st.cache_data(ttl=300)
def calculate_inventory_metrics_with_3month_avg(df_stock, df_sales, df_product):
    """Calculate inventory metrics using 3-month average sales (FIXED: AGGREGATE STOCK FIRST)"""
    
    metrics = {}
    
    if df_stock.empty:
        return metrics
    
    try:
        # --- FIX UTAMA: Agregasi Stok dari Level Batch ke Level SKU ---
        # Kita jumlahkan dulu Stock_Qty berdasarkan SKU_ID agar 1 SKU = 1 Baris
        df_stock_agg = df_stock.groupby('SKU_ID').agg({
            'Stock_Qty': 'sum'
        }).reset_index()
        
        # ADD PRODUCT INFO ke data yang sudah di-agregasi
        df_stock_agg = add_product_info_to_data(df_stock_agg, df_product)
        
        # Siapkan Sales Data
        df_sales = add_product_info_to_data(df_sales, df_product)
        
        # Get last 3 months sales data
        if not df_sales.empty:
            sales_months = sorted(df_sales['Month'].unique())
            if len(sales_months) >= 3:
                last_3_sales_months = sales_months[-3:]
                df_sales_last_3 = df_sales[df_sales['Month'].isin(last_3_sales_months)].copy()
            else:
                df_sales_last_3 = df_sales.copy()
        
        # Calculate average monthly sales per SKU
        if not df_sales.empty and not df_sales_last_3.empty:
            avg_monthly_sales = df_sales_last_3.groupby('SKU_ID')['Sales_Qty'].mean().reset_index()
            avg_monthly_sales.columns = ['SKU_ID', 'Avg_Monthly_Sales_3M']
        else:
            avg_monthly_sales = pd.DataFrame(columns=['SKU_ID', 'Avg_Monthly_Sales_3M'])
        
        # Merge Stock Aggregated dengan Product Info (redundant check but safe)
        df_inventory = pd.merge(
            df_stock_agg,
            df_product[['SKU_ID', 'Product_Name', 'SKU_Tier', 'Brand', 'Status']],
            on='SKU_ID',
            how='left',
            suffixes=('', '_master')
        )
        
        # Bersihkan kolom duplikat jika ada setelah merge
        df_inventory = df_inventory.loc[:,~df_inventory.columns.duplicated()]
        
        # Merge dengan Average Sales
        df_inventory = pd.merge(df_inventory, avg_monthly_sales, on='SKU_ID', how='left')
        df_inventory['Avg_Monthly_Sales_3M'] = df_inventory['Avg_Monthly_Sales_3M'].fillna(0)
        
        # Calculate cover months
        df_inventory['Cover_Months'] = np.where(
            df_inventory['Avg_Monthly_Sales_3M'] > 0,
            df_inventory['Stock_Qty'] / df_inventory['Avg_Monthly_Sales_3M'],
            999  # For SKUs with no sales
        )
        
        # Categorize inventory status
        conditions = [
            df_inventory['Cover_Months'] < 0.8,
            (df_inventory['Cover_Months'] >= 0.8) & (df_inventory['Cover_Months'] <= 1.5),
            df_inventory['Cover_Months'] > 1.5
        ]
        choices = ['Need Replenishment', 'Ideal/Healthy', 'High Stock']
        df_inventory['Inventory_Status'] = np.select(conditions, choices, default='Unknown')
        
        # Get high/low stock items
        high_stock_df = df_inventory[df_inventory['Inventory_Status'] == 'High Stock'].copy().sort_values('Cover_Months', ascending=False)
        low_stock_df = df_inventory[df_inventory['Inventory_Status'] == 'Need Replenishment'].copy().sort_values('Cover_Months', ascending=True)
        
        # Tier analysis
        if 'SKU_Tier' in df_inventory.columns:
            tier_analysis = df_inventory.groupby('SKU_Tier').agg({
                'SKU_ID': 'count',
                'Stock_Qty': 'sum',
                'Avg_Monthly_Sales_3M': 'sum',
                'Cover_Months': 'mean'
            }).reset_index()
            tier_analysis.columns = ['Tier', 'SKU_Count', 'Total_Stock', 'Total_Sales_3M_Avg', 'Avg_Cover_Months']
            tier_analysis['Turnover'] = tier_analysis['Total_Sales_3M_Avg'] / tier_analysis['Total_Stock']
            metrics['tier_analysis'] = tier_analysis
        
        metrics['inventory_df'] = df_inventory
        metrics['high_stock'] = high_stock_df
        metrics['low_stock'] = low_stock_df
        metrics['total_stock'] = df_inventory['Stock_Qty'].sum()
        metrics['total_skus'] = len(df_inventory)
        metrics['avg_cover'] = df_inventory[df_inventory['Cover_Months'] < 999]['Cover_Months'].mean()
        
        metrics['inventory_value_score'] = (len(df_inventory[df_inventory['Inventory_Status'] == 'Ideal/Healthy']) / 
                                            len(df_inventory) * 100) if len(df_inventory) > 0 else 0
        
        return metrics
        
    except Exception as e:
        st.error(f"Inventory metrics error: {str(e)}")
        return metrics

def calculate_sales_vs_forecast_po(df_sales, df_forecast, df_po, df_product):
    """Calculate sales vs forecast and PO comparison - HANYA ACTIVE SKUS"""
    
    results = {}
    
    if df_sales.empty or df_forecast.empty:
        return results
    
    try:
        # ADD PRODUCT INFO jika belum ada
        df_sales = add_product_info_to_data(df_sales, df_product)
        df_forecast = add_product_info_to_data(df_forecast, df_product)
        df_po = add_product_info_to_data(df_po, df_product)
        
        # FILTER HANYA ACTIVE SKUS
        if 'Status' in df_product.columns:
            active_skus = df_product[df_product['Status'].str.upper() == 'ACTIVE']['SKU_ID'].tolist()
            
            # Filter semua dataset untuk hanya active SKUs
            df_sales = df_sales[df_sales['SKU_ID'].isin(active_skus)]
            df_forecast = df_forecast[df_forecast['SKU_ID'].isin(active_skus)]
            if not df_po.empty:
                df_po = df_po[df_po['SKU_ID'].isin(active_skus)]
        
        # Get last 3 months for comparison
        sales_months = sorted(df_sales['Month'].unique())
        forecast_months = sorted(df_forecast['Month'].unique())
        po_months = sorted(df_po['Month'].unique())
        
        # Find common months
        common_months = sorted(set(sales_months) & set(forecast_months) & set(po_months))
        
        if not common_months:
            return results
        
        # Use last common month
        last_month = common_months[-1]
        
        # Get data for last month
        df_sales_month = df_sales[df_sales['Month'] == last_month].copy()
        df_forecast_month = df_forecast[df_forecast['Month'] == last_month].copy()
        df_po_month = df_po[df_po['Month'] == last_month].copy()
        
        # Filter hanya SKU dengan Forecast_Qty > 0
        df_forecast_month = df_forecast_month[df_forecast_month['Forecast_Qty'] > 0]
        
        # Merge all data
        df_merged = pd.merge(
            df_sales_month[['SKU_ID', 'Sales_Qty']],
            df_forecast_month[['SKU_ID', 'Forecast_Qty']],
            on='SKU_ID',
            how='inner'
        )
        
        df_merged = pd.merge(
            df_merged,
            df_po_month[['SKU_ID', 'PO_Qty']],
            on='SKU_ID',
            how='left'
        )
        
        # Add product info
        df_merged = add_product_info_to_data(df_merged, df_product)
        
        # Filter out SKU dengan PO_Qty = 0 (tidak ada PO) jika mau
        # df_merged = df_merged[df_merged['PO_Qty'] > 0]
        
        # Calculate ratios
        df_merged['Sales_vs_Forecast_Ratio'] = np.where(
            df_merged['Forecast_Qty'] > 0,
            (df_merged['Sales_Qty'] / df_merged['Forecast_Qty']) * 100,
            0
        )
        
        df_merged['Sales_vs_PO_Ratio'] = np.where(
            df_merged['PO_Qty'] > 0,
            (df_merged['Sales_Qty'] / df_merged['PO_Qty']) * 100,
            0
        )
        
        # Calculate deviations
        df_merged['Forecast_Deviation'] = abs(df_merged['Sales_vs_Forecast_Ratio'] - 100)
        df_merged['PO_Deviation'] = abs(df_merged['Sales_vs_PO_Ratio'] - 100)
        
        # Identify SKUs with high deviation (> 30%) - HANYA ACTIVE SKUS
        high_deviation_skus = df_merged[
            (df_merged['Forecast_Deviation'] > 30) | 
            (df_merged['PO_Deviation'] > 30)
        ].copy()
        
        high_deviation_skus = high_deviation_skus.sort_values('Forecast_Deviation', ascending=False)
        
        # Calculate overall metrics
        avg_forecast_deviation = df_merged['Forecast_Deviation'].mean()
        avg_po_deviation = df_merged['PO_Deviation'].mean()
        
        results = {
            'last_month': last_month,
            'comparison_data': df_merged,
            'high_deviation_skus': high_deviation_skus,
            'avg_forecast_deviation': avg_forecast_deviation,
            'avg_po_deviation': avg_po_deviation,
            'total_skus_compared': len(df_merged),
            'active_skus_only': True
        }
        
        return results
        
    except Exception as e:
        st.error(f"Sales vs forecast calculation error: {str(e)}")
        return results

def calculate_brand_performance(df_forecast, df_po, df_product):
    """Calculate forecast accuracy performance by brand"""
    
    if df_forecast.empty or df_po.empty or df_product.empty:
        return pd.DataFrame()
    
    try:
        # ADD PRODUCT INFO jika belum ada
        df_forecast = add_product_info_to_data(df_forecast, df_product)
        df_po = add_product_info_to_data(df_po, df_product)
        
        # Get last month data
        forecast_months = sorted(df_forecast['Month'].unique())
        po_months = sorted(df_po['Month'].unique())
        common_months = sorted(set(forecast_months) & set(po_months))
        
        if not common_months:
            return pd.DataFrame()
        
        last_month = common_months[-1]
        
        # Get data for last month
        df_forecast_month = df_forecast[df_forecast['Month'] == last_month].copy()
        df_po_month = df_po[df_po['Month'] == last_month].copy()
        
        # Merge forecast and PO
        df_merged = pd.merge(
            df_forecast_month,
            df_po_month,
            on=['SKU_ID'],
            how='inner'
        )
        
        # Add brand info jika belum ada
        if 'Brand' not in df_merged.columns:
            df_merged = add_product_info_to_data(df_merged, df_product)
        
        if 'Brand' not in df_merged.columns:
            return pd.DataFrame()
        
        # Calculate ratio and accuracy
        df_merged['PO_Rofo_Ratio'] = np.where(
            df_merged['Forecast_Qty'] > 0,
            (df_merged['PO_Qty'] / df_merged['Forecast_Qty']) * 100,
            0
        )
        
        # Categorize
        conditions = [
            df_merged['PO_Rofo_Ratio'] < 80,
            (df_merged['PO_Rofo_Ratio'] >= 80) & (df_merged['PO_Rofo_Ratio'] <= 120),
            df_merged['PO_Rofo_Ratio'] > 120
        ]
        choices = ['Under', 'Accurate', 'Over']
        df_merged['Accuracy_Status'] = np.select(conditions, choices, default='Unknown')
        
        # Calculate brand performance
        brand_performance = df_merged.groupby('Brand').agg({
            'SKU_ID': 'count',
            'Forecast_Qty': 'sum',
            'PO_Qty': 'sum',
            'PO_Rofo_Ratio': lambda x: 100 - abs(x - 100).mean()  # Accuracy
        }).reset_index()
        
        brand_performance.columns = ['Brand', 'SKU_Count', 'Total_Forecast', 'Total_PO', 'Accuracy']
        
        # Calculate additional metrics
        brand_performance['PO_vs_Forecast_Ratio'] = (brand_performance['Total_PO'] / brand_performance['Total_Forecast'] * 100)
        brand_performance['Qty_Difference'] = brand_performance['Total_PO'] - brand_performance['Total_Forecast']
        
        # Get status counts
        status_counts = df_merged.groupby(['Brand', 'Accuracy_Status']).size().unstack(fill_value=0).reset_index()
        
        # Merge with performance data
        brand_performance = pd.merge(brand_performance, status_counts, on='Brand', how='left')
        
        # Fill NaN with 0 for status columns
        for status in ['Under', 'Accurate', 'Over']:
            if status not in brand_performance.columns:
                brand_performance[status] = 0
        
        # Sort by accuracy
        brand_performance = brand_performance.sort_values('Accuracy', ascending=False)
        
        return brand_performance
        
    except Exception as e:
        st.error(f"Brand performance calculation error: {str(e)}")
        return pd.DataFrame()

def identify_profitability_segments(df_financial):
    """Segment SKUs by profitability"""
    
    if df_financial.empty:
        return pd.DataFrame()
    
    try:
        sku_profitability = df_financial.groupby(['SKU_ID', 'Product_Name', 'Brand']).agg({
            'Revenue': 'sum',
            'Gross_Margin': 'sum',
            'Sales_Qty': 'sum'
        }).reset_index()
        
        # Calculate metrics
        sku_profitability['Avg_Margin_Per_SKU'] = sku_profitability['Gross_Margin'] / sku_profitability['Sales_Qty']
        sku_profitability['Margin_Percentage'] = np.where(
            sku_profitability['Revenue'] > 0,
            (sku_profitability['Gross_Margin'] / sku_profitability['Revenue'] * 100),
            0
        )
        
        # Segment by margin percentage
        conditions = [
            (sku_profitability['Margin_Percentage'] >= 40),
            (sku_profitability['Margin_Percentage'] >= 20) & (sku_profitability['Margin_Percentage'] < 40),
            (sku_profitability['Margin_Percentage'] < 20) & (sku_profitability['Margin_Percentage'] > 0),
            (sku_profitability['Margin_Percentage'] <= 0)
        ]
        choices = ['High Margin (>40%)', 'Medium Margin (20-40%)', 'Low Margin (<20%)', 'Negative Margin']
        
        sku_profitability['Margin_Segment'] = np.select(conditions, choices, default='Unknown')
        
        return sku_profitability.sort_values('Gross_Margin', ascending=False)
        
    except Exception as e:
        st.error(f"Profitability segmentation error: {str(e)}")
        return pd.DataFrame()

def validate_data_quality(df, df_name):
    """Comprehensive data quality validation"""
    
    checks = {}
    
    if df.empty:
        checks['Empty Dataset'] = '❌ Dataset kosong'
        return checks
    
    # Basic checks
    checks['Total Rows'] = f"📊 {len(df):,} rows"
    checks['Total Columns'] = f"📋 {len(df.columns)} columns"
    
    # Missing values
    missing_values = df.isnull().sum().sum()
    missing_pct = (missing_values / (len(df) * len(df.columns)) * 100)
    checks['Missing Values'] = f"⚠️ {missing_values:,} ({missing_pct:.1f}%)" if missing_values > 0 else f"✅ {missing_values:,}"
    
    # Duplicates
    duplicates = df.duplicated().sum()
    checks['Duplicate Rows'] = f"⚠️ {duplicates:,}" if duplicates > 0 else f"✅ {duplicates:,}"
    
    # Zero values (for numeric columns)
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    if len(numeric_cols) > 0:
        zero_values = (df[numeric_cols] == 0).sum().sum()
        zero_pct = (zero_values / (len(df) * len(numeric_cols)) * 100)
        checks['Zero Values'] = f"📉 {zero_values:,} ({zero_pct:.1f}%)"
    
    # Negative values
    if len(numeric_cols) > 0:
        negative_values = (df[numeric_cols] < 0).sum().sum()
        if negative_values > 0:
            checks['Negative Values'] = f"❌ {negative_values:,}"
    
    # Date range (if Month column exists)
    if 'Month' in df.columns:
        try:
            min_date = df['Month'].min()
            max_date = df['Month'].max()
            checks['Date Range'] = f"📅 {min_date.strftime('%b %Y')} - {max_date.strftime('%b %Y')}"
        except:
            pass
    
    return checks

# ============================================================================
# 📱 MAIN CONTENT DENGAN RESPONSIVE DESIGN
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
    ecomm_forecast_month_cols = all_data.get('ecomm_forecast_month_cols', [])
    df_reseller_forecast = all_data.get('reseller_forecast', pd.DataFrame())
    reseller_all_month_cols = all_data.get('reseller_all_month_cols', [])
    reseller_historical_cols = all_data.get('reseller_historical_cols', [])
    reseller_forecast_cols = all_data.get('reseller_forecast_cols', [])
    df_fulfillment = all_data.get('fulfillment', pd.DataFrame())
    
    # Load complete reseller data
    with st.spinner('🔄 Loading Reseller Data...'):
        reseller_complete_data = load_reseller_complete_data(client)
        
        df_sales_reseller = reseller_complete_data.get('sales', pd.DataFrame())
        df_past_rofo_reseller = reseller_complete_data.get('past_rofo', pd.DataFrame())
        df_past_po_reseller = reseller_complete_data.get('past_po', pd.DataFrame())

# Calculate metrics
monthly_performance = calculate_monthly_performance(df_forecast, df_po, df_product)
last_3_months_performance = get_last_3_months_performance(monthly_performance)
inventory_metrics = calculate_inventory_metrics_with_3month_avg(df_stock, df_sales, df_product)
sales_vs_forecast = calculate_sales_vs_forecast_po(df_sales, df_forecast, df_po, df_product)

# Calculate financial metrics
df_financial = calculate_financial_metrics_all(df_sales, df_product)
df_inventory_financial = calculate_inventory_financial(df_stock, df_product)
seasonal_pattern = calculate_seasonality(df_financial) if not df_financial.empty else pd.DataFrame()
forecast_bias = calculate_forecast_bias(df_forecast, df_po)
profitability_segments = identify_profitability_segments(df_financial) if not df_financial.empty else pd.DataFrame()

# ============================================================================
# 📊 UPDATE SIDEBAR METRICS DENGAN DATA YANG SUDAH DIMUAT
# ============================================================================

with st.sidebar:
    # Update data overview dengan data yang sudah dimuat
    if not df_product_active.empty:
        responsive_metric("Active SKUs", len(df_product_active))
    
    if not df_stock.empty:
        total_stock = df_stock['Stock_Qty'].sum()
        responsive_metric("Total Stock", f"{total_stock:,.0f}")
    
    if monthly_performance:
        last_month = sorted(monthly_performance.keys())[-1]
        accuracy = monthly_performance[last_month]['accuracy']
        responsive_metric("Latest Accuracy", f"{accuracy:.1f}%")
    
    # Financial metrics in sidebar
    if not df_financial.empty:
        st.markdown("---")
        st.markdown("### 💰 Financial Overview")
        
        total_revenue = df_financial['Revenue'].sum()
        total_margin = df_financial['Gross_Margin'].sum()
        avg_margin_pct = (total_margin / total_revenue * 100) if total_revenue > 0 else 0
        
        responsive_metric("Total Revenue", f"Rp {total_revenue:,.0f}")
        responsive_metric("Total Margin", f"Rp {total_margin:,.0f}")
        responsive_metric("Avg Margin %", f"{avg_margin_pct:.1f}%")

# ============================================================================
# 📱 RESPONSIVE TABS IMPLEMENTATION - MOBILE VS DESKTOP
# ============================================================================

# Display device info untuk debugging (opsional)
if st.session_state.get('debug_mode', False):
    st.info(f"Device: {device_type.upper()} | Mobile: {is_mobile}")

if is_mobile:
    # ============================================================================
    # 📱 MOBILE VIEW - SIMPLIFIED
    # ============================================================================
    
    # Mobile: simplified tabs
    mobile_tab = st.selectbox(
        "Navigate:",
        ["📊 Overview", "📦 Inventory", "💰 Finance", "🔍 SKU", "📈 Sales", "⚙️ More"],
        label_visibility="collapsed"
    )
    
    # Render content based on selected tab
    if mobile_tab == "📊 Overview":
        st.subheader("📊 Dashboard Overview")
        
        # Quick metrics untuk mobile
        col1, col2 = create_responsive_columns(2)
        with col1:
            if monthly_performance:
                last_month = sorted(monthly_performance.keys())[-1]
                accuracy = monthly_performance[last_month]['accuracy']
                responsive_metric("Forecast Accuracy", f"{accuracy:.1f}%")
        
        with col2:
            if not df_stock.empty:
                total_stock = df_stock['Stock_Qty'].sum()
                responsive_metric("Total Stock", f"{total_stock:,.0f}")
        
        # Simple chart untuk mobile
        if monthly_performance:
            st.subheader("📈 Forecast Accuracy Trend")
            summary_data = []
            for month, data in sorted(monthly_performance.items()):
                summary_data.append({
                    'Month': month.strftime('%b %Y'),
                    'Accuracy': data['accuracy']
                })
            
            if summary_data:
                summary_df = pd.DataFrame(summary_data)
                fig = px.line(summary_df, x='Month', y='Accuracy', 
                             title="Monthly Accuracy Trend", markers=True)
                fig.update_layout(height=300)
                st.plotly_chart(fig, use_container_width=True)
    
    elif mobile_tab == "📦 Inventory":
        st.subheader("📦 Inventory Analysis")
        
        if 'inventory_df' in inventory_metrics:
            df_inventory = inventory_metrics['inventory_df']
            
            # Summary metrics
            col1, col2 = create_responsive_columns(2)
            with col1:
                high_stock = len(inventory_metrics.get('high_stock', pd.DataFrame()))
                responsive_metric("High Stock SKUs", high_stock)
            
            with col2:
                low_stock = len(inventory_metrics.get('low_stock', pd.DataFrame()))
                responsive_metric("Low Stock SKUs", low_stock)
            
            # Inventory status pie chart
            if 'Inventory_Status' in df_inventory.columns:
                status_counts = df_inventory['Inventory_Status'].value_counts()
                fig = px.pie(values=status_counts.values, names=status_counts.index, 
                            title="Inventory Status Distribution")
                fig.update_layout(height=300)
                st.plotly_chart(fig, use_container_width=True)
    
    elif mobile_tab == "💰 Finance":
        st.subheader("💰 Financial Analysis")
        
        if not df_financial.empty:
            # Financial metrics
            total_revenue = df_financial['Revenue'].sum()
            total_margin = df_financial['Gross_Margin'].sum()
            avg_margin_pct = (total_margin / total_revenue * 100) if total_revenue > 0 else 0
            
            col1, col2 = create_responsive_columns(2)
            with col1:
                responsive_metric("Total Revenue", f"Rp {total_revenue:,.0f}")
            
            with col2:
                responsive_metric("Gross Margin", f"Rp {total_margin:,.0f}")
            
            responsive_metric("Margin %", f"{avg_margin_pct:.1f}%")
    
    elif mobile_tab == "🔍 SKU":
        st.subheader("🔍 SKU Analysis")
        
        if monthly_performance:
            last_month = sorted(monthly_performance.keys())[-1]
            last_month_data = monthly_performance[last_month]
            
            under_count = last_month_data['status_counts'].get('Under', 0)
            accurate_count = last_month_data['status_counts'].get('Accurate', 0)
            over_count = last_month_data['status_counts'].get('Over', 0)
            
            col1, col2, col3 = create_responsive_columns(3)
            with col1:
                responsive_metric("Under", under_count)
            with col2:
                responsive_metric("Accurate", accurate_count)
            with col3:
                responsive_metric("Over", over_count)
    
    elif mobile_tab == "📈 Sales":
        st.subheader("📈 Sales Analysis")
        
        if not df_sales.empty:
            # Last 6 months sales trend
            recent_sales = df_sales.sort_values('Month').tail(6)
            monthly_sales = recent_sales.groupby('Month')['Sales_Qty'].sum().reset_index()
            monthly_sales['Month'] = monthly_sales['Month'].dt.strftime('%b %Y')
            
            fig = px.bar(monthly_sales, x='Month', y='Sales_Qty', 
                        title="Recent Monthly Sales")
            fig.update_layout(height=300)
            st.plotly_chart(fig, use_container_width=True)
    
    else:  # ⚙️ More
        st.subheader("⚙️ Settings & More")
        
        # Data Explorer untuk mobile
        with st.expander("📋 Data Explorer", expanded=False):
            dataset_options = {
                "Product Master": df_product,
                "Sales Data": df_sales,
                "Forecast Data": df_forecast,
                "Stock Data": df_stock
            }
            
            selected_dataset = st.selectbox("Select Dataset", list(dataset_options.keys()))
            df_selected = dataset_options[selected_dataset]
            
            if not df_selected.empty:
                st.dataframe(df_selected.head(10), use_container_width=True)
        
        # Settings
        with st.expander("⚙️ Advanced Settings", expanded=False):
            st.checkbox("Debug Mode", value=False, key="debug_mode")
            if st.button("Clear Cache", use_container_width=True):
                st.cache_data.clear()
                st.rerun()

else:
    # ============================================================================
    # 🖥️ DESKTOP VIEW - FULL FEATURES
    # ============================================================================
    
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
    
    # ============================================================================
    # TAB 1: MONTHLY PERFORMANCE DETAILS
    # ============================================================================
    with tabs[0]:
        st.subheader("📈 Forecast Accuracy Performance Trends")

        if monthly_performance:
            # 1. Prepare Data
            summary_data = []
            for month, data in sorted(monthly_performance.items()):
                summary_data.append({
                    'Month': month,
                    'Month_Display': month.strftime('%b %Y'),
                    'Accuracy': data['accuracy'],
                    'Total_SKUs': data['total_records'],
                    'Under': data['status_counts'].get('Under', 0),
                    'Over': data['status_counts'].get('Over', 0),
                    'Accurate': data['status_counts'].get('Accurate', 0),
                    'MAPE': data['mape']
                })
            
            summary_df = pd.DataFrame(summary_data).sort_values('Month')

            if not summary_df.empty:
                # --- A. METRIC CARDS ---
                avg_acc = summary_df['Accuracy'].mean()
                last_acc = summary_df['Accuracy'].iloc[-1]
                prev_acc = summary_df['Accuracy'].iloc[-2] if len(summary_df) > 1 else last_acc
                delta_acc = last_acc - prev_acc
                
                best_month = summary_df.loc[summary_df['Accuracy'].idxmax()]
                stability = max(0, 100 - summary_df['Accuracy'].std())

                kpi1, kpi2, kpi3, kpi4 = create_responsive_columns(4)

                with kpi1:
                    st.metric("Current Accuracy", f"{last_acc:.1f}%", 
                             delta=f"{delta_acc:+.1f}%" if delta_acc != 0 else None)
                
                with kpi2:
                    st.metric("Average (YTD)", f"{avg_acc:.1f}%")
                
                with kpi3:
                    st.metric("Best Performance", f"{best_month['Accuracy']:.1f}%", 
                             delta=best_month['Month_Display'])
                
                with kpi4:
                    st.metric("Stability Score", f"{stability:.0f}/100")

                # --- B. TREND CHART ---
                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=summary_df['Month_Display'],
                    y=summary_df['Accuracy'],
                    mode='lines+markers',
                    name='Accuracy',
                    line=dict(color='#667eea', width=3)
                ))
                
                fig.update_layout(
                    height=400,
                    title='Forecast Accuracy Trend',
                    xaxis_title='Month',
                    yaxis_title='Accuracy %',
                    hovermode='x unified'
                )
                st.plotly_chart(fig, use_container_width=True)

                # --- C. LAST 3 MONTHS PERFORMANCE ---
                st.subheader("🎯 Last 3 Months Performance")
                
                if last_3_months_performance:
                    month_cols = create_responsive_columns(3)
                    
                    for i, (month, data) in enumerate(sorted(last_3_months_performance.items())):
                        with month_cols[i]:
                            month_name = month.strftime('%b %Y')
                            accuracy = data['accuracy']
                            
                            under = data['status_counts'].get('Under', 0)
                            accurate = data['status_counts'].get('Accurate', 0)
                            over = data['status_counts'].get('Over', 0)
                            
                            st.markdown(f"**{month_name}**")
                            st.metric("Accuracy", f"{accuracy:.1f}%")
                            st.write(f"Under: {under} | Accurate: {accurate} | Over: {over}")

    # ============================================================================
    # TAB 2: BRAND ANALYSIS
    # ============================================================================
    with tabs[1]:
        st.subheader("🏷️ Brand & Tier Strategic Analysis")
        
        brand_perf = calculate_brand_performance(df_forecast, df_po, df_product)
        
        if not brand_perf.empty:
            # Top brands by accuracy
            st.subheader("🏆 Top Performing Brands")
            top_brands = brand_perf.head(10)
            
            fig = px.bar(top_brands, x='Brand', y='Accuracy',
                        title='Top 10 Brands by Forecast Accuracy',
                        color='Accuracy', color_continuous_scale='RdYlGn')
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
            
            # Brand performance table
            st.subheader("📊 Brand Performance Details")
            st.dataframe(brand_perf, use_container_width=True)

    # ============================================================================
    # TAB 3: INVENTORY ANALYSIS
    # ============================================================================
    with tabs[2]:
        st.subheader("📦 Inventory Health & Optimization")
        
        if 'inventory_df' in inventory_metrics:
            df_inventory = inventory_metrics['inventory_df']
            
            # Inventory summary
            col1, col2, col3, col4 = create_responsive_columns(4)
            
            with col1:
                st.metric("Total SKUs", inventory_metrics.get('total_skus', 0))
            
            with col2:
                st.metric("Total Stock", f"{inventory_metrics.get('total_stock', 0):,.0f}")
            
            with col3:
                st.metric("Avg Cover", f"{inventory_metrics.get('avg_cover', 0):.1f} months")
            
            with col4:
                score = inventory_metrics.get('inventory_value_score', 0)
                st.metric("Health Score", f"{score:.0f}/100")
            
            # High and low stock
            col_high, col_low = st.columns(2)
            
            with col_high:
                st.subheader("🚨 High Stock Items")
                high_stock = inventory_metrics.get('high_stock', pd.DataFrame())
                if not high_stock.empty:
                    st.dataframe(high_stock[['SKU_ID', 'Product_Name', 'Stock_Qty', 'Cover_Months']].head(10), 
                                use_container_width=True)
            
            with col_low:
                st.subheader("📉 Low Stock Items")
                low_stock = inventory_metrics.get('low_stock', pd.DataFrame())
                if not low_stock.empty:
                    st.dataframe(low_stock[['SKU_ID', 'Product_Name', 'Stock_Qty', 'Cover_Months']].head(10), 
                                use_container_width=True)
            
            # Inventory status distribution
            if 'Inventory_Status' in df_inventory.columns:
                st.subheader("📊 Inventory Status Distribution")
                status_counts = df_inventory['Inventory_Status'].value_counts()
                
                fig = px.pie(values=status_counts.values, names=status_counts.index,
                            title="Inventory Status", hole=0.4)
                fig.update_layout(height=400)
                st.plotly_chart(fig, use_container_width=True)

    # ============================================================================
    # TAB 4: SKU EVALUATION
    # ============================================================================
    with tabs[3]:
        st.subheader("🔍 SKU 360° Deep Dive Analysis")
        
        if monthly_performance and not df_sales.empty:
            # Get last month for evaluation
            last_month = sorted(monthly_performance.keys())[-1]
            last_month_data = monthly_performance[last_month]['data'].copy()
            
            # Prepare list for dropdown
            available_skus = []
            if not last_month_data.empty:
                sorted_skus = last_month_data.sort_values('Forecast_Qty', ascending=False)
                
                for _, row in sorted_skus.head(100).iterrows():
                    sku_label = f"{row['SKU_ID']} - {row.get('Product_Name', 'N/A')}"
                    available_skus.append(sku_label)
            
            # SKU Selector
            selected_sku_display = st.selectbox(
                "📋 Select SKU to Analyze", 
                options=available_skus,
                key="sku_selector"
            )
            
            if selected_sku_display:
                selected_sku = selected_sku_display.split(" - ")[0]
                
                # Get SKU Details
                sku_details = last_month_data[last_month_data['SKU_ID'] == selected_sku].iloc[0]
                
                # Display SKU Info
                col_info1, col_info2 = st.columns(2)
                
                with col_info1:
                    st.markdown(f"**SKU ID:** {selected_sku}")
                    st.markdown(f"**Product:** {sku_details.get('Product_Name', 'N/A')}")
                    st.markdown(f"**Brand:** {sku_details.get('Brand', 'N/A')}")
                
                with col_info2:
                    st.markdown(f"**Forecast:** {sku_details.get('Forecast_Qty', 0):,.0f}")
                    st.markdown(f"**PO:** {sku_details.get('PO_Qty', 0):,.0f}")
                    ratio = (sku_details.get('PO_Qty', 0) / sku_details.get('Forecast_Qty', 1) * 100) if sku_details.get('Forecast_Qty', 0) > 0 else 0
                    st.markdown(f"**PO/Rofo Ratio:** {ratio:.1f}%")
                
                # Historical sales trend
                st.subheader("📈 Historical Sales Trend")
                sku_sales = df_sales[df_sales['SKU_ID'] == selected_sku].sort_values('Month')
                
                if not sku_sales.empty:
                    fig = px.line(sku_sales, x='Month', y='Sales_Qty',
                                title=f"Sales Trend for {selected_sku}",
                                markers=True)
                    fig.update_layout(height=300)
                    st.plotly_chart(fig, use_container_width=True)

    # ============================================================================
    # TAB 5: SALES ANALYSIS
    # ============================================================================
    with tabs[4]:
        st.subheader("📈 Sales & Forecast Analysis")
        
        if not df_sales.empty and monthly_performance:
            # Sales trend
            monthly_sales = df_sales.groupby('Month')['Sales_Qty'].sum().reset_index()
            monthly_sales = monthly_sales.sort_values('Month')
            
            fig = px.line(monthly_sales, x='Month', y='Sales_Qty',
                         title="Monthly Sales Trend",
                         markers=True)
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
            
            # Sales vs Forecast comparison
            if sales_vs_forecast:
                st.subheader("🎯 Sales vs Forecast Comparison")
                
                last_month = sales_vs_forecast['last_month']
                avg_forecast_deviation = sales_vs_forecast['avg_forecast_deviation']
                
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Last Month", last_month.strftime('%B %Y'))
                with col2:
                    st.metric("Avg Forecast Deviation", f"{avg_forecast_deviation:.1f}%")
                
                # High deviation SKUs
                high_deviation = sales_vs_forecast.get('high_deviation_skus', pd.DataFrame())
                if not high_deviation.empty:
                    st.subheader("🚨 High Deviation SKUs")
                    st.dataframe(high_deviation[['SKU_ID', 'Product_Name', 'Forecast_Deviation', 'PO_Deviation']], 
                                use_container_width=True)

    # ============================================================================
    # TAB 6: DATA EXPLORER
    # ============================================================================
    with tabs[5]:
        st.subheader("📋 Data Explorer")
        
        dataset_options = {
            "Product Master": df_product,
            "Active Products": df_product_active,
            "Sales Data": df_sales,
            "Forecast Data": df_forecast,
            "PO Data": df_po,
            "Stock Data": df_stock,
            "Financial Data": df_financial,
            "Ecommerce Forecast": df_ecomm_forecast,
            "Reseller Forecast": df_reseller_forecast
        }
        
        selected_dataset = st.selectbox("Select Dataset", list(dataset_options.keys()))
        df_selected = dataset_options[selected_dataset]
        
        if not df_selected.empty:
            st.write(f"**Rows:** {df_selected.shape[0]:,} | **Columns:** {df_selected.shape[1]}")
            
            # Data preview
            st.dataframe(df_selected, use_container_width=True, height=500)
            
            # Download option
            csv = df_selected.to_csv(index=False)
            st.download_button(
                label="📥 Download CSV",
                data=csv,
                file_name=f"{selected_dataset.replace(' ', '_')}.csv",
                mime="text/csv",
                use_container_width=True
            )

    # ============================================================================
    # TAB 7: ECOMMERCE FORECAST
    # ============================================================================
    with tabs[6]:
        st.subheader("🛒 Ecommerce Forecast Intelligence")
        
        if not df_ecomm_forecast.empty:
            # Summary metrics
            total_fcst = df_ecomm_forecast[ecomm_forecast_month_cols].sum().sum()
            sku_count = len(df_ecomm_forecast)
            
            col1, col2, col3 = create_responsive_columns(3)
            
            with col1:
                st.metric("Total Forecast Qty", f"{total_fcst:,.0f}")
            
            with col2:
                st.metric("SKU Count", sku_count)
            
            with col3:
                avg_monthly = total_fcst / len(ecomm_forecast_month_cols) if ecomm_forecast_month_cols else 0
                st.metric("Avg Monthly", f"{avg_monthly:,.0f}")
            
            # Monthly forecast trend
            monthly_totals = df_ecomm_forecast[ecomm_forecast_month_cols].sum()
            monthly_df = pd.DataFrame({
                'Month': monthly_totals.index,
                'Quantity': monthly_totals.values
            })
            
            fig = px.bar(monthly_df, x='Month', y='Quantity',
                        title="Monthly Forecast Distribution")
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
            
            # Top forecast items
            st.subheader("🏆 Top Forecast Items")
            df_ecomm_forecast['Total_Forecast'] = df_ecomm_forecast[ecomm_forecast_month_cols].sum(axis=1)
            top_items = df_ecomm_forecast.sort_values('Total_Forecast', ascending=False).head(10)
            
            st.dataframe(top_items[['SKU_ID', 'Product_Name', 'Total_Forecast']], use_container_width=True)

    # ============================================================================
    # TAB 8: PROFITABILITY
    # ============================================================================
    with tabs[7]:
        st.subheader("💰 Profitability Analysis")
        
        if not df_financial.empty:
            # Financial summary
            total_revenue = df_financial['Revenue'].sum()
            total_margin = df_financial['Gross_Margin'].sum()
            margin_pct = (total_margin / total_revenue * 100) if total_revenue > 0 else 0
            
            col1, col2, col3 = create_responsive_columns(3)
            
            with col1:
                st.metric("Total Revenue", f"Rp {total_revenue:,.0f}")
            
            with col2:
                st.metric("Gross Margin", f"Rp {total_margin:,.0f}")
            
            with col3:
                st.metric("Margin %", f"{margin_pct:.1f}%")
            
            # Profitability segments
            if not profitability_segments.empty:
                st.subheader("📊 Profitability Segments")
                segment_counts = profitability_segments['Margin_Segment'].value_counts()
                
                fig = px.pie(values=segment_counts.values, names=segment_counts.index,
                            title="SKU Profitability Distribution")
                fig.update_layout(height=400)
                st.plotly_chart(fig, use_container_width=True)
                
                # Top profitable SKUs
                st.subheader("🏆 Top Profitable SKUs")
                top_profitable = profitability_segments.head(10)
                st.dataframe(top_profitable[['SKU_ID', 'Product_Name', 'Gross_Margin', 'Margin_Percentage']], 
                            use_container_width=True)

    # ============================================================================
    # TAB 9: RESELLER
    # ============================================================================
    with tabs[8]:
        st.subheader("🤝 Reseller Performance")
        
        if not df_reseller_forecast.empty:
            # Reseller summary
            total_fcst = df_reseller_forecast[reseller_forecast_cols].sum().sum() if reseller_forecast_cols else 0
            sku_count = len(df_reseller_forecast)
            
            col1, col2 = create_responsive_columns(2)
            
            with col1:
                st.metric("Total Forecast 2026", f"{total_fcst:,.0f}")
            
            with col2:
                st.metric("SKU Count", sku_count)
            
            # Monthly forecast trend
            if reseller_forecast_cols:
                monthly_totals = df_reseller_forecast[reseller_forecast_cols].sum()
                monthly_df = pd.DataFrame({
                    'Month': monthly_totals.index,
                    'Quantity': monthly_totals.values
                })
                
                fig = px.line(monthly_df, x='Month', y='Quantity',
                             title="Reseller Forecast 2026 Trend",
                             markers=True)
                fig.update_layout(height=400)
                st.plotly_chart(fig, use_container_width=True)

    # ============================================================================
    # TAB 10: FULFILLMENT
    # ============================================================================
    with tabs[9]:
        st.subheader("🚚 Fulfillment Cost Analysis")
        
        if not df_fulfillment.empty:
            # Clean and prepare data
            df_bs = df_fulfillment.copy()
            numeric_cols = ['Total Order(BS)', 'GMV (Fullfil By BS)', 'GMV Total (MP)', 'Total Cost', 'BSA', '%Cost']
            
            for col in numeric_cols:
                if col in df_bs.columns:
                    df_bs[col] = pd.to_numeric(df_bs[col], errors='coerce').fillna(0)
            
            # Calculate CPO
            if 'Total Order(BS)' in df_bs.columns and 'Total Cost' in df_bs.columns:
                df_bs['CPO'] = df_bs.apply(
                    lambda x: x['Total Cost'] / x['Total Order(BS)'] if x['Total Order(BS)'] > 0 else 0, 
                    axis=1
                )
            
            # Summary metrics
            if not df_bs.empty:
                last_row = df_bs.iloc[-1]
                
                col1, col2, col3 = create_responsive_columns(3)
                
                with col1:
                    orders = last_row.get('Total Order(BS)', 0)
                    st.metric("Total Orders", f"{orders:,.0f}")
                
                with col2:
                    cost = last_row.get('Total Cost', 0)
                    st.metric("Total Cost", f"Rp {cost:,.0f}")
                
                with col3:
                    cpo = last_row.get('CPO', 0)
                    st.metric("Cost Per Order", f"Rp {cpo:,.0f}")
                
                # Cost trend
                if 'Month' in df_bs.columns and 'Total Cost' in df_bs.columns:
                    fig = px.line(df_bs, x='Month', y='Total Cost',
                                 title="Fulfillment Cost Trend",
                                 markers=True)
                    fig.update_layout(height=400)
                    st.plotly_chart(fig, use_container_width=True)

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
