"""
Mobile-specific configuration and utilities
"""
import streamlit as st
from streamlit.runtime.scriptrunner import get_script_run_ctx

def is_mobile_device():
    """
    Deteksi mobile device menggunakan user agent dari request headers
    Fallback ke query parameter untuk testing
    """
    try:
        # Method 1: Check query parameter (untuk testing)
        query_params = st.query_params
        if 'mobile' in query_params:
            return query_params['mobile'].lower() == 'true'
        
        # Method 2: Check session state (set by JavaScript)
        if 'device_type' in st.session_state:
            return st.session_state.device_type == 'mobile'
        
        # Method 3: Try to get from request (advanced)
        try:
            ctx = get_script_run_ctx()
            if ctx and hasattr(ctx, 'request'):
                user_agent = ctx.request.headers.get('user-agent', '').lower()
                mobile_keywords = ['mobile', 'iphone', 'android', 'ipad', 'ipod']
                return any(keyword in user_agent for keyword in mobile_keywords)
        except:
            pass
            
        # Default: assume desktop
        return False
        
    except Exception:
        return False

def get_device_type():
    """Get device type for responsive design"""
    try:
        if is_mobile_device():
            # Check query param untuk tablet
            query_params = st.query_params
            if 'tablet' in query_params and query_params['tablet'].lower() == 'true':
                return 'tablet'
            return 'mobile'
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
           DEVICE DETECTION SCRIPT
           ============================================ */
        <script>
        function detectDevice() {
            const isMobile = window.innerWidth <= 768;
            const isTablet = window.innerWidth > 768 && window.innerWidth <= 1024;
            
            // Store in session storage for persistence
            sessionStorage.setItem('isMobile', isMobile);
            sessionStorage.setItem('isTablet', isTablet);
            
            // Send to Streamlit via query parameters
            if (window.parent) {
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
                
                // Update URL without reload
                window.history.replaceState({}, '', url);
                
                // Trigger Streamlit to re-run with new params
                if (window.parent.streamlitDebug) {
                    window.parent.location.reload();
                }
            }
        }
        
        // Run on load and resize
        window.addEventListener('load', detectDevice);
        window.addEventListener('resize', detectDevice);
        
        // Initial detection
        detectDevice();
        </script>
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
