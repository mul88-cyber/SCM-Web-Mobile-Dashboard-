"""
📱 INVENTORY INTELLIGENCE DASHBOARD - MOBILE OPTIMIZED
Streamlit app optimized for both desktop and mobile devices
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials
from tenacity import retry, stop_after_attempt, wait_exponential
import warnings
warnings.filterwarnings('ignore')

# Import mobile config
try:
    from mobile_config import is_mobile_device, apply_mobile_css, get_device_type, get_responsive_columns
except ImportError:
    # Fallback functions
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
# 🎯 CONFIGURATION
# ============================================================================

# Set page config
st.set_page_config(
    page_title="Inventory Intelligence Pro",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Apply mobile CSS
mobile_css = apply_mobile_css()
st.markdown(mobile_css, unsafe_allow_html=True)

# Detect device
device_type = get_device_type()
is_mobile = is_mobile_device()

# ============================================================================
# 📱 RESPONSIVE CSS (SIMPLIFIED)
# ============================================================================

st.markdown("""
<style>
    /* Responsive header */
    .main-header {
        font-size: 2.5rem;
        font-weight: 900;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        padding: 1rem;
    }
    
    @media (max-width: 768px) {
        .main-header {
            font-size: 1.8rem !important;
            padding: 0.5rem !important;
        }
        
        /* Stack columns on mobile */
        [data-testid="column"] {
            width: 100% !important;
            margin-bottom: 0.5rem !important;
        }
        
        /* Smaller tabs on mobile */
        .stTabs [data-baseweb="tab"] {
            padding: 6px 10px !important;
            font-size: 0.8rem !important;
        }
    }
    
    /* Dark mode support */
    @media (prefers-color-scheme: dark) {
        .stApp {
            background-color: #0E1117;
            color: #FFFFFF;
        }
    }
</style>
""", unsafe_allow_html=True)

# ============================================================================
# 📊 MAIN APP HEADER
# ============================================================================

st.markdown('<h1 class="main-header">💰 FORECAST & INVENTORY CONTROL PRO DASHBOARD</h1>', unsafe_allow_html=True)

if is_mobile:
    st.caption(f"📱 Mobile View | Updated: {datetime.now().strftime('%d %b %Y')}")
else:
    st.caption(f"🚀 Inventory Intelligence Dashboard | Updated: {datetime.now().strftime('%d %B %Y %H:%M')}")

# ============================================================================
# 📱 MOBILE-OPTIMIZED SIDEBAR
# ============================================================================

with st.sidebar:
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
    
    # Data Overview
    st.markdown("### 📈 Data Overview")
    # ... your existing data overview code ...
    
    # Threshold Settings dengan responsive design
    with st.expander("⚙️ Threshold Settings", expanded=False):
        under_threshold = st.slider("Under Forecast Threshold (%)", 0, 100, 80)
        over_threshold = st.slider("Over Forecast Threshold (%)", 100, 200, 120)

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
# 📊 MAIN CONTENT AREA
# ============================================================================

# Display device info for debugging (remove in production)
if st.session_state.get('debug_mode', False):
    st.info(f"Device: {device_type.upper()} | Mobile: {is_mobile}")

# Create tabs with responsive design
if is_mobile:
    # Simplified tabs for mobile
    mobile_tab = st.selectbox(
        "Navigate:",
        ["📊 Overview", "📦 Inventory", "💰 Finance", "⚙️ More"],
        label_visibility="collapsed"
    )
    
    # Render content based on selected tab
    if mobile_tab == "📊 Overview":
        st.subheader("📊 Overview")
        # ... overview content ...
    elif mobile_tab == "📦 Inventory":
        st.subheader("📦 Inventory")
        # ... inventory content ...
    elif mobile_tab == "💰 Finance":
        st.subheader("💰 Finance")
        # ... finance content ...
    else:
        st.subheader("⚙️ Settings & More")
        # ... more content ...
        
else:
    # Desktop: Full tabs
    tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9, tab10 = st.tabs([
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
    ])
    
    # ... your existing tab content goes here ...
    # But use responsive helpers inside each tab

# ============================================================================
# 🔄 DATA LOADING FUNCTIONS (YOUR EXISTING CODE)
# ============================================================================

@st.cache_resource(show_spinner=False)
@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
def init_gsheet_connection():
    """Initialize Google Sheets connection"""
    try:
        skey = st.secrets["gcp_service_account"]
        scopes = ["https://www.googleapis.com/auth/spreadsheets"]
        credentials = Credentials.from_service_account_info(skey, scopes=scopes)
        client = gspread.authorize(credentials)
        return client
    except Exception as e:
        st.error(f"❌ Connection Failed: {str(e)}")
        return None

# ... (ALL YOUR EXISTING DATA FUNCTIONS GO HERE - NO CHANGES NEEDED) ...

# ============================================================================
# 📱 FOOTER
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
</script>
""", unsafe_allow_html=True)
