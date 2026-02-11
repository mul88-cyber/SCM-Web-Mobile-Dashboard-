"""
Mobile-specific configuration and utilities
"""
import streamlit as st
from streamlit_user_agent import streamlit_user_agent

def is_mobile_device():
    """Detect if user is on mobile device"""
    try:
        user_agent = streamlit_user_agent()
        if user_agent:
            mobile_keywords = ['Mobile', 'iPhone', 'Android', 'iPad', 'iPod']
            return any(keyword in user_agent for keyword in mobile_keywords)
    except:
        pass
    return False

def get_device_type():
    """Get device type for responsive design"""
    try:
        user_agent = streamlit_user_agent()
        if user_agent:
            if 'Mobile' in user_agent and 'iPad' not in user_agent:
                return 'mobile'
            elif 'Tablet' in user_agent or 'iPad' in user_agent:
                return 'tablet'
        return 'desktop'
    except:
        return 'desktop'

def apply_mobile_css():
    """Apply mobile-specific CSS"""
    mobile_css = """
    <style>
        /* ============================================
           MOBILE OPTIMIZATION (max-width: 768px)
           ============================================ */
        @media only screen and (max-width: 768px) {
            /* Main container */
            .main .block-container {
                padding-top: 1rem !important;
                padding-bottom: 1rem !important;
                padding-left: 0.5rem !important;
                padding-right: 0.5rem !important;
            }
            
            /* Header optimization */
            .main-header {
                font-size: 1.6rem !important;
                padding: 0.5rem !important;
                margin-bottom: 0.5rem !important;
            }
            
            /* Metric cards - stacked on mobile */
            [data-testid="column"] {
                width: 100% !important;
                flex: 0 0 100% !important;
                margin-bottom: 0.5rem !important;
            }
            
            /* Tabs optimization */
            .stTabs [data-baseweb="tab-list"] {
                flex-wrap: wrap !important;
                gap: 4px !important;
                padding: 4px 0 !important;
            }
            
            .stTabs [data-baseweb="tab"] {
                flex: 1 0 calc(50% - 8px) !important;
                min-width: calc(50% - 8px) !important;
                max-width: calc(50% - 8px) !important;
                height: 36px !important;
                padding: 6px 8px !important;
                font-size: 0.75rem !important;
                margin: 2px !important;
            }
            
            /* Data tables */
            .stDataFrame {
                font-size: 0.8rem !important;
            }
            
            /* Charts */
            .js-plotly-plot, .plotly, .plot-container {
                height: 280px !important;
            }
            
            /* Sidebar */
            [data-testid="stSidebar"] {
                min-width: 180px !important;
                max-width: 200px !important;
            }
            
            /* Hide some elements on mobile */
            .mobile-hide {
                display: none !important;
            }
            
            /* Compact metrics */
            .compact-metric {
                padding: 0.5rem !important;
                margin: 0.2rem 0 !important;
            }
            
            /* Financial cards smaller */
            .financial-card {
                padding: 0.8rem !important;
                margin: 0.3rem 0 !important;
            }
            
            /* Adjust button sizes */
            .stButton button {
                width: 100% !important;
                font-size: 0.9rem !important;
                padding: 8px 12px !important;
            }
            
            /* Reduce font sizes */
            h1 { font-size: 1.8rem !important; }
            h2 { font-size: 1.4rem !important; }
            h3 { font-size: 1.2rem !important; }
            h4 { font-size: 1.1rem !important; }
            p, div, span { font-size: 0.9rem !important; }
            
            /* Stack process flow */
            .process-container {
                grid-template-columns: 1fr !important;
                gap: 10px !important;
            }
        }
        
        /* ============================================
           TABLET OPTIMIZATION (769px - 1024px)
           ============================================ */
        @media only screen and (min-width: 769px) and (max-width: 1024px) {
            [data-testid="column"] {
                flex: 0 0 50% !important;
                width: 50% !important;
            }
            
            .stTabs [data-baseweb="tab"] {
                flex: 1 0 calc(33.33% - 8px) !important;
                min-width: calc(33.33% - 8px) !important;
            }
            
            .main-header {
                font-size: 2.2rem !important;
            }
            
            .js-plotly-plot, .plotly, .plot-container {
                height: 350px !important;
            }
        }
        
        /* ============================================
           MOBILE-SPECIFIC COMPONENTS
           ============================================ */
        .mobile-only {
            display: none !important;
        }
        
        @media only screen and (max-width: 768px) {
            .mobile-only {
                display: block !important;
            }
            
            .desktop-only {
                display: none !important;
            }
        }
        
        /* Mobile bottom navigation */
        .mobile-nav {
            position: fixed;
            bottom: 0;
            left: 0;
            right: 0;
            background: white;
            border-top: 1px solid #e0e0e0;
            display: flex;
            justify-content: space-around;
            padding: 10px 0;
            z-index: 1000;
            display: none;
        }
        
        @media only screen and (max-width: 768px) {
            .mobile-nav {
                display: flex;
            }
            
            /* Add padding to main content for bottom nav */
            .main .block-container {
                padding-bottom: 70px !important;
            }
        }
        
        .mobile-nav-item {
            text-align: center;
            color: #666;
            flex: 1;
            padding: 5px;
        }
        
        .mobile-nav-item.active {
            color: #667eea;
            font-weight: bold;
        }
        
        .mobile-nav-icon {
            font-size: 1.2rem;
            display: block;
            margin-bottom: 2px;
        }
        
        /* Mobile-friendly tooltips */
        @media only screen and (max-width: 768px) {
            .stTooltip {
                font-size: 0.8rem !important;
                max-width: 200px !important;
            }
        }
        
        /* Touch-friendly buttons */
        @media (hover: none) and (pointer: coarse) {
            button, [role="button"], .stButton button {
                min-height: 44px !important;
                min-width: 44px !important;
            }
            
            /* Larger touch targets */
            [data-testid="stMetricValue"] {
                font-size: 1.4rem !important;
            }
        }
        
        /* PWA (Progressive Web App) styles */
        @media (display-mode: standalone) {
            header {
                display: none;
            }
            
            .main .block-container {
                padding-top: 0.5rem !important;
            }
        }
        
        /* Dark mode support for mobile */
        @media (prefers-color-scheme: dark) {
            .mobile-nav {
                background: #1e1e1e;
                border-top-color: #333;
            }
            
            .mobile-nav-item {
                color: #aaa;
            }
            
            .mobile-nav-item.active {
                color: #667eea;
            }
        }
    </style>
    """
    return mobile_css

def get_responsive_columns(device_type, default_cols=4):
    """Get responsive column layout based on device"""
    if device_type == 'mobile':
        return 1  # Stack everything on mobile
    elif device_type == 'tablet':
        return 2  # Two columns on tablet
    else:
        return default_cols  # Default on desktop
