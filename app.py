import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from checkers import SocialMediaChecker
import io
import time
import threading

# Page configuration
st.set_page_config(
    page_title="Social Media Account Checker",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for professional styling
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 15px;
        margin-bottom: 2rem;
        text-align: center;
        color: white;
        box-shadow: 0 10px 30px rgba(0,0,0,0.2);
    }
    
    .metric-card {
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
        padding: 1.5rem;
        border-radius: 12px;
        text-align: center;
        margin: 0.5rem;
        box-shadow: 0 5px 15px rgba(0,0,0,0.1);
        border-left: 4px solid #667eea;
    }
    
    .status-live {
        background: linear-gradient(135deg, #a8edea 0%, #fed6e3 100%);
        color: #2d5016;
        font-weight: bold;
        padding: 0.5rem;
        border-radius: 8px;
        text-align: center;
    }
    
    .status-suspended {
        background: linear-gradient(135deg, #ffecd2 0%, #fcb69f 100%);
        color: #8b2635;
        font-weight: bold;
        padding: 0.5rem;
        border-radius: 8px;
        text-align: center;
    }
    
    .control-panel {
        background: linear-gradient(135deg, #e3ffe7 0%, #d9e7ff 100%);
        padding: 1.5rem;
        border-radius: 12px;
        margin: 1rem 0;
        border: 2px solid #667eea;
    }
    
    .stButton > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.5rem 1rem;
        font-weight: bold;
        transition: all 0.3s ease;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 5px 15px rgba(0,0,0,0.2);
    }
    
    .sidebar .stSelectbox > div > div {
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
        border-radius: 8px;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'checking_active' not in st.session_state:
    st.session_state.checking_active = False
if 'pause_checking' not in st.session_state:
    st.session_state.pause_checking = False
if 'live_count' not in st.session_state:
    st.session_state.live_count = 0
if 'suspended_count' not in st.session_state:
    st.session_state.suspended_count = 0
if 'error_count' not in st.session_state:
    st.session_state.error_count = 0
if 'total_checked' not in st.session_state:
    st.session_state.total_checked = 0
if 'results_data' not in st.session_state:
    st.session_state.results_data = []

# Main header
st.markdown("""
<div class="main-header">
    <h1>🔍 Social Media Account Checker</h1>
    <p>Professional tool for checking account status across social media platforms</p>
</div>
""", unsafe_allow_html=True)

# Sidebar
st.sidebar.header("⚙️ Configuration")

# Platform selection
platform = st.sidebar.selectbox(
    "Select Platform:",
    ["Instagram", "Twitter", "TikTok"],
    index=0
)

# File upload
uploaded_file = st.sidebar.file_uploader(
    "Upload Account File (.txt)",
    type=['txt'],
    help="Text file containing usernames, one per line"
)

# Platform information
platform_info = {
    "Instagram": {
        "icon": "📷",
        "url": "instagram.com",
        "description": "Check Instagram account status and availability",
        "color": "#E4405F"
    },
    "Twitter": {
        "icon": "🐦", 
        "url": "twitter.com",
        "description": "Check Twitter account status and suspension",
        "color": "#1DA1F2"
    },
    "TikTok": {
        "icon": "🎵",
        "url": "tiktok.com", 
        "description": "Check TikTok account status and availability",
        "color": "#FF0050"
    }
}

# Platform info display
st.sidebar.markdown("---")
st.sidebar.markdown(f"### {platform_info[platform]['icon']} {platform}")
st.sidebar.markdown(f"**Website:** {platform_info[platform]['url']}")
st.sidebar.markdown(f"**Description:** {platform_info[platform]['description']}")

# Real-time counters at the top
if st.session_state.checking_active or st.session_state.total_checked > 0:
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <h3 style="color: #667eea; margin: 0;">Total Checked</h3>
            <h2 style="margin: 0.5rem 0;">{st.session_state.total_checked}</h2>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <h3 style="color: #28a745; margin: 0;">Live Accounts</h3>
            <h2 style="margin: 0.5rem 0; color: #28a745;">{st.session_state.live_count}</h2>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="metric-card">
            <h3 style="color: #dc3545; margin: 0;">Suspended</h3>
            <h2 style="margin: 0.5rem 0; color: #dc3545;">{st.session_state.suspended_count}</h2>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown(f"""
        <div class="metric-card">
            <h3 style="color: #ffc107; margin: 0;">Errors</h3>
            <h2 style="margin: 0.5rem 0; color: #ffc107;">{st.session_state.error_count}</h2>
        </div>
        """, unsafe_allow_html=True)

# Main content
if uploaded_file is not None:
    # Read file
    content = uploaded_file.read().decode('utf-8')
    accounts = [line.strip() for line in content.split('\n') if line.strip()]
    
    st.success(f"✅ File uploaded successfully! Total accounts: {len(accounts)}")
    
    # Show account preview
    with st.expander("👀 Preview Accounts"):
        sample_accounts = accounts[:10]
        for i, account in enumerate(sample_accounts, 1):
            st.text(f"{i}. {account}")
        if len(accounts) > 10:
            st.info(f"... and {len(accounts) - 10} more accounts")
    
    # Control panel
    st.markdown("""
    <div class="control-panel">
        <h3 style="color: #667eea; margin-bottom: 1rem;">🎛️ Control Panel</h3>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if not st.session_state.checking_active:
            if st.button(f"🚀 Start Checking {platform}", type="primary", use_container_width=True):
                st.session_state.checking_active = True
                st.session_state.pause_checking = False
                st.session_state.live_count = 0
                st.session_state.suspended_count = 0
                st.session_state.error_count = 0
                st.session_state.total_checked = 0
                st.session_state.results_data = []
                st.rerun()
    
    with col2:
        if st.session_state.checking_active:
            if not st.session_state.pause_checking:
                if st.button("⏸️ Pause", use_container_width=True):
                    st.session_state.pause_checking = True
                    st.rerun()
            else:
                if st.button("▶️ Resume", use_container_width=True):
                    st.session_state.pause_checking = False
                    st.rerun()
    
    with col3:
        if st.session_state.checking_active:
            if st.button("🛑 Stop", use_container_width=True):
                st.session_state.checking_active = False
                st.session_state.pause_checking = False
                st.rerun()
    
    # Checking process
    if st.session_state.checking_active and not st.session_state.pause_checking:
        checker = SocialMediaChecker()
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        def update_progress(current, total, username, status):
            if not st.session_state.checking_active:
                return False
            
            while st.session_state.pause_checking and st.session_state.checking_active:
                time.sleep(0.1)
            
            if not st.session_state.checking_active:
                return False
            
            if status == "live":
                st.session_state.live_count += 1
            elif status == "suspended":
                st.session_state.suspended_count += 1
            else:
                st.session_state.error_count += 1
            
            st.session_state.total_checked = current
            
            progress = current / total
            progress_bar.progress(progress)
            status_text.text(f"Checking: {username} ({current}/{total}) - Status: {status}")
            
            return True
        
        start_time = time.time()
        results = checker.check_accounts(accounts, platform, update_progress)
        end_time = time.time()
        
        st.session_state.results_data = results
        st.session_state.checking_active = False
        
        progress_bar.empty()
        status_text.empty()
        
        st.success(f"✅ Checking completed in {end_time - start_time:.2f} seconds")
        st.rerun()
    
    # Display results if available
    if st.session_state.results_data:
        df = pd.DataFrame(st.session_state.results_data)
        
        st.markdown("## 📊 Final Statistics")
        
        # Statistics visualization
        status_counts = df['status'].value_counts()
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Pie chart
            fig_pie = px.pie(
                values=status_counts.values, 
                names=status_counts.index,
                title=f"Account Status Distribution - {platform}",
                color_discrete_map={
                    'live': '#28a745',
                    'suspended': '#dc3545', 
                    'unknown': '#ffc107',
                    'error': '#6c757d'
                }
            )
            fig_pie.update_layout(
                font=dict(size=14),
                title_font_size=16,
                showlegend=True
            )
            st.plotly_chart(fig_pie, use_container_width=True)
        
        with col2:
            # Bar chart
            fig_bar = px.bar(
                x=status_counts.index,
                y=status_counts.values,
                title=f"Account Count by Status - {platform}",
                color=status_counts.index,
                color_discrete_map={
                    'live': '#28a745',
                    'suspended': '#dc3545',
                    'unknown': '#ffc107', 
                    'error': '#6c757d'
                }
            )
            fig_bar.update_layout(
                showlegend=False,
                font=dict(size=14),
                title_font_size=16
            )
            st.plotly_chart(fig_bar, use_container_width=True)
        
        # Download section
        st.markdown("## 📥 Download Results")
        
        col1, col2, col3, col4 = st.columns(4)
        
        # Live accounts download
        with col1:
            live_accounts = df[df['status'] == 'live']
            if not live_accounts.empty:
                live_text = '\n'.join(live_accounts['original_line'].tolist())
                
                # TXT download
                st.download_button(
                    label="📄 Live Accounts (TXT)",
                    data=live_text,
                    file_name=f"live_accounts_{platform.lower()}.txt",
                    mime="text/plain",
                    use_container_width=True
                )
                
                # CSV download
                live_csv = live_accounts.to_csv(index=False)
                st.download_button(
                    label="📊 Live Accounts (CSV)",
                    data=live_csv,
                    file_name=f"live_accounts_{platform.lower()}.csv",
                    mime="text/csv",
                    use_container_width=True
                )
        
        # Suspended accounts download
        with col2:
            suspended_accounts = df[df['status'] == 'suspended']
            if not suspended_accounts.empty:
                suspended_text = '\n'.join(suspended_accounts['original_line'].tolist())
                
                # TXT download
                st.download_button(
                    label="🚫 Suspended (TXT)",
                    data=suspended_text,
                    file_name=f"suspended_accounts_{platform.lower()}.txt",
                    mime="text/plain",
                    use_container_width=True
                )
                
                # CSV download
                suspended_csv = suspended_accounts.to_csv(index=False)
                st.download_button(
                    label="📊 Suspended (CSV)",
                    data=suspended_csv,
                    file_name=f"suspended_accounts_{platform.lower()}.csv",
                    mime="text/csv",
                    use_container_width=True
                )
        
        # Error accounts download
        with col3:
            error_accounts = df[~df['status'].isin(['live', 'suspended'])]
            if not error_accounts.empty:
                error_text = '\n'.join(error_accounts['original_line'].tolist())
                
                # TXT download
                st.download_button(
                    label="⚠️ Errors (TXT)",
                    data=error_text,
                    file_name=f"error_accounts_{platform.lower()}.txt",
                    mime="text/plain",
                    use_container_width=True
                )
                
                # CSV download
                error_csv = error_accounts.to_csv(index=False)
                st.download_button(
                    label="📊 Errors (CSV)",
                    data=error_csv,
                    file_name=f"error_accounts_{platform.lower()}.csv",
                    mime="text/csv",
                    use_container_width=True
                )
        
        # All results download
        with col4:
            all_text = '\n'.join(df['original_line'].tolist())
            
            # TXT download
            st.download_button(
                label="📋 All Results (TXT)",
                data=all_text,
                file_name=f"all_results_{platform.lower()}.txt",
                mime="text/plain",
                use_container_width=True
            )
            
            # CSV download
            all_csv = df.to_csv(index=False)
            st.download_button(
                label="📊 All Results (CSV)",
                data=all_csv,
                file_name=f"all_results_{platform.lower()}.csv",
                mime="text/csv",
                use_container_width=True
            )
        
        # Detailed results tables
        st.markdown("## 📋 Detailed Results")
        
        tab1, tab2, tab3, tab4 = st.tabs(["🟢 Live Accounts", "🔴 Suspended Accounts", "⚠️ Error Accounts", "📊 All Results"])
        
        with tab1:
            if not live_accounts.empty:
                st.markdown(f"**Found {len(live_accounts)} live accounts:**")
                st.dataframe(live_accounts[['username', 'original_line']], use_container_width=True)
            else:
                st.info("No live accounts found")
        
        with tab2:
            if not suspended_accounts.empty:
                st.markdown(f"**Found {len(suspended_accounts)} suspended accounts:**")
                st.dataframe(suspended_accounts[['username', 'original_line']], use_container_width=True)
            else:
                st.info("No suspended accounts found")
        
        with tab3:
            if not error_accounts.empty:
                st.markdown(f"**Found {len(error_accounts)} accounts with errors:**")
                st.dataframe(error_accounts[['username', 'status', 'original_line']], use_container_width=True)
            else:
                st.info("No error accounts found")
        
        with tab4:
            st.markdown(f"**All {len(df)} checked accounts:**")
            st.dataframe(df[['username', 'status', 'original_line']], use_container_width=True)

else:
    # Welcome page
    st.markdown("""
    ## 🚀 Welcome to Social Media Account Checker
    
    ### 📋 How to Use:
    1. **Select Platform** from the sidebar (Instagram, Twitter, or TikTok)
    2. **Upload Account File** - A text file (.txt) containing usernames
    3. **Click "Start Checking"** and monitor the real-time progress
    4. **Download Results** in your preferred format (TXT or CSV)
    
    ### 📁 Account File Format:
    ```
    username1
    username2:password
    username3
    ```
    
    ### ✨ Features:
    - ✅ Fast and reliable checking
    - ✅ Professional user interface
    - ✅ Real-time progress monitoring
    - ✅ Pause and resume functionality
    - ✅ Multiple download formats
    - ✅ Support for all major platforms
    
    ### 🔧 Supported Platforms:
    """)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%); 
                    padding: 1.5rem; border-radius: 12px; text-align: center; 
                    border-left: 4px solid {platform_info['Instagram']['color']};">
            <h4>📷 Instagram</h4>
            <p>Check account status<br>Detect deleted accounts<br>Analyze active accounts</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%); 
                    padding: 1.5rem; border-radius: 12px; text-align: center; 
                    border-left: 4px solid {platform_info['Twitter']['color']};">
            <h4>🐦 Twitter</h4>
            <p>Check account status<br>Detect suspended accounts<br>Analyze active accounts</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%); 
                    padding: 1.5rem; border-radius: 12px; text-align: center; 
                    border-left: 4px solid {platform_info['TikTok']['color']};">
            <h4>🎵 TikTok</h4>
            <p>Check account status<br>Detect deleted accounts<br>Analyze active accounts</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    st.info("💡 **Tip:** Start with a small file (10-20 accounts) to test the tool before checking large files")