import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from checkers import SocialMediaChecker
import io
import time
import threading

# Page Configuration
st.set_page_config(
    page_title="Social Media Account Checker",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for professional styling
st.markdown("""
<style>
    .stApp {
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
    }
    
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin: 0.5rem 0;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    
    .success-card {
        background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        margin: 0.5rem 0;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    
    .error-card {
        background: linear-gradient(135deg, #fa709a 0%, #fee140 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        margin: 0.5rem 0;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    
    .stButton > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 25px;
        padding: 0.5rem 2rem;
        font-weight: bold;
        transition: all 0.3s ease;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
    }
    
    .live-counter {
        background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
        padding: 2rem;
        border-radius: 15px;
        text-align: center;
        margin: 1rem 0;
        box-shadow: 0 8px 16px rgba(0, 0, 0, 0.1);
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
if 'current_status' not in st.session_state:
    st.session_state.current_status = ""

# Header with live counter
st.markdown("""
<div class="live-counter">
    <h1>🔍 Social Media Account Checker</h1>
    <p style="font-size: 1.2rem; margin: 0;">Professional Account Verification Tool</p>
</div>
""", unsafe_allow_html=True)

# Live Statistics Counter - Always visible with real values
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown(f"""
    <div class="metric-card">
        <h3>{st.session_state.total_checked}</h3>
        <p>Total Checked</p>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown(f"""
    <div class="success-card">
        <h3>{st.session_state.live_count}</h3>
        <p>Live Accounts</p>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown(f"""
    <div class="error-card">
        <h3>{st.session_state.suspended_count}</h3>
        <p>Suspended</p>
    </div>
    """, unsafe_allow_html=True)

with col4:
    st.markdown(f"""
    <div class="metric-card">
        <h3>{st.session_state.error_count}</h3>
        <p>Errors</p>
    </div>
    """, unsafe_allow_html=True)

# Current status display
if st.session_state.current_status:
    st.info(f"🔄 {st.session_state.current_status}")

# Sidebar Configuration
st.sidebar.markdown("## ⚙️ Settings")

# Platform Selection
platform = st.sidebar.selectbox(
    "Select Platform:",
    ["Instagram", "Twitter", "TikTok"],
    index=0
)

# Input Method Selection
st.sidebar.markdown("## 📝 Input Method")
input_method = st.sidebar.radio(
    "Choose input method:",
    ["Upload File", "Paste Text"]
)

accounts = []

if input_method == "Upload File":
    # File Upload
    uploaded_file = st.sidebar.file_uploader(
        "Upload Accounts File (.txt)",
        type=['txt'],
        help="Text file containing usernames, one per line"
    )
    
    if uploaded_file is not None:
        content = uploaded_file.read().decode('utf-8')
        accounts = [line.strip() for line in content.split('\n') if line.strip()]
        st.sidebar.success(f"✅ File loaded: {len(accounts)} accounts")

else:
    # Text Area Input
    st.sidebar.markdown("### 📝 Paste Accounts")
    text_input = st.sidebar.text_area(
        "Enter accounts (one per line):",
        height=200,
        placeholder="username1\nusername2:password\nusername3\n..."
    )
    
    if text_input.strip():
        accounts = [line.strip() for line in text_input.split('\n') if line.strip()]
        st.sidebar.success(f"✅ Text loaded: {len(accounts)} accounts")

# Download Format Selection
st.sidebar.markdown("## 📥 Download Format")
download_format = st.sidebar.radio(
    "Choose format:",
    ["TXT", "CSV"]
)

# Platform Information
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
        "description": "Verify Twitter account status and suspension",
        "color": "#1DA1F2"
    },
    "TikTok": {
        "icon": "🎵",
        "url": "tiktok.com", 
        "description": "Check TikTok account status and availability",
        "color": "#000000"
    }
}

# Display Platform Info
st.sidebar.markdown("---")
st.sidebar.markdown(f"### {platform_info[platform]['icon']} {platform}")
st.sidebar.markdown(f"**Website:** {platform_info[platform]['url']}")
st.sidebar.markdown(f"**Description:** {platform_info[platform]['description']}")

# Main Content
if len(accounts) > 0:
    
    # Show account preview
    with st.expander("👀 Preview Accounts"):
        sample_accounts = accounts[:10]
        for i, account in enumerate(sample_accounts, 1):
            st.text(f"{i}. {account}")
        if len(accounts) > 10:
            st.info(f"... and {len(accounts) - 10} more accounts")
    
    # Control Buttons
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        if not st.session_state.checking_active:
            if st.button(f"🚀 Start Checking {platform} Accounts", type="primary"):
                st.session_state.checking_active = True
                st.session_state.pause_checking = False
                st.session_state.live_count = 0
                st.session_state.suspended_count = 0
                st.session_state.error_count = 0
                st.session_state.total_checked = 0
                st.session_state.results_data = []
                st.session_state.current_status = "Starting check process..."
                st.rerun()
    
    with col2:
        if st.session_state.checking_active:
            pause_text = "▶️ Resume" if st.session_state.pause_checking else "⏸️ Pause"
            if st.button(pause_text, key="pause_btn"):
                st.session_state.pause_checking = not st.session_state.pause_checking
                if st.session_state.pause_checking:
                    st.session_state.current_status = "Process paused by user"
                else:
                    st.session_state.current_status = "Process resumed"
                st.rerun()
    
    with col3:
        if st.session_state.checking_active:
            if st.button("🛑 Stop", key="stop_btn"):
                st.session_state.checking_active = False
                st.session_state.pause_checking = False
                st.session_state.current_status = "Process stopped by user"
                st.rerun()
    
    # Checking Process
    if st.session_state.checking_active and not st.session_state.pause_checking:
        checker = SocialMediaChecker()
        
        # Progress indicators
        progress_bar = st.progress(0)
        status_placeholder = st.empty()
        
        # Create placeholders for live updates
        live_placeholder = st.empty()
        
        # Progress update function
        def update_progress(current, total, username, status):
            if not st.session_state.checking_active:
                return False
                
            # Handle pause
            while st.session_state.pause_checking and st.session_state.checking_active:
                time.sleep(0.1)
            
            if not st.session_state.checking_active:
                return False
            
            # Update counters based on status
            if status == "live":
                st.session_state.live_count += 1
            elif status == "suspended":
                st.session_state.suspended_count += 1
            else:
                st.session_state.error_count += 1
            
            st.session_state.total_checked = current
            
            # Update progress bar
            progress = current / total
            progress_bar.progress(progress)
            
            # Update status
            pause_status = " (PAUSED)" if st.session_state.pause_checking else ""
            st.session_state.current_status = f"Checking: {username} ({current}/{total}) - Status: {status}{pause_status}"
            
            # Force UI update by rerunning every few accounts
            if current % 3 == 0:  # Update UI every 3 accounts
                st.rerun()
            
            return st.session_state.checking_active
        
        # Start checking
        start_time = time.time()
        results = checker.check_accounts(accounts, platform, update_progress)
        end_time = time.time()
        
        # Store results
        st.session_state.results_data = results
        
        # Clear progress indicators
        progress_bar.empty()
        status_placeholder.empty()
        
        # Show completion message
        if st.session_state.checking_active:
            st.session_state.current_status = f"✅ Checking completed in {end_time - start_time:.2f} seconds"
            st.success(st.session_state.current_status)
        else:
            st.session_state.current_status = "⚠️ Checking was stopped by user"
            st.warning(st.session_state.current_status)
        
        st.session_state.checking_active = False
        st.rerun()

# Results Display and Download - Show if results exist
if st.session_state.results_data and len(st.session_state.results_data) > 0:
    df = pd.DataFrame(st.session_state.results_data)
    
    st.markdown("---")
    st.markdown("## 📊 Final Statistics")
    
    # Statistics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Processed", len(st.session_state.results_data))
    with col2:
        live_count = len(df[df['status'] == 'live'])
        st.metric("Live Accounts", live_count)
    with col3:
        suspended_count = len(df[df['status'] == 'suspended'])
        st.metric("Suspended Accounts", suspended_count)
    with col4:
        error_count = len(df[~df['status'].isin(['live', 'suspended'])])
        st.metric("Errors/Unknown", error_count)
    
    # Charts
    status_counts = df['status'].value_counts()
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Pie chart
        fig_pie = px.pie(
            values=status_counts.values, 
            names=status_counts.index,
            title=f"Account Status Distribution - {platform}",
            color_discrete_map={
                'live': '#4facfe',
                'suspended': '#ff6b6b', 
                'unknown': '#feca57',
                'error': '#95a5a6'
            }
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
                'live': '#4facfe',
                'suspended': '#ff6b6b',
                'unknown': '#feca57', 
                'error': '#95a5a6'
            }
        )
        fig_bar.update_layout(showlegend=False)
        st.plotly_chart(fig_bar, use_container_width=True)
    
    # Download Buttons
    st.markdown("## 📥 Download Results")
    
    col1, col2, col3, col4 = st.columns(4)
    
    # Live accounts download
    with col1:
        live_accounts = df[df['status'] == 'live']
        if not live_accounts.empty:
            if download_format == "TXT":
                live_data = '\n'.join(live_accounts['original_line'].tolist())
                file_ext = "txt"
                mime_type = "text/plain"
            else:
                live_data = live_accounts.to_csv(index=False)
                file_ext = "csv"
                mime_type = "text/csv"
            
            st.download_button(
                label=f"📥 Live Accounts ({download_format})",
                data=live_data,
                file_name=f"live_accounts_{platform.lower()}.{file_ext}",
                mime=mime_type,
                type="primary"
            )
        else:
            st.info("No live accounts found")
    
    # Suspended accounts download
    with col2:
        suspended_accounts = df[df['status'] == 'suspended']
        if not suspended_accounts.empty:
            if download_format == "TXT":
                suspended_data = '\n'.join(suspended_accounts['original_line'].tolist())
                file_ext = "txt"
                mime_type = "text/plain"
            else:
                suspended_data = suspended_accounts.to_csv(index=False)
                file_ext = "csv"
                mime_type = "text/csv"
            
            st.download_button(
                label=f"📥 Suspended ({download_format})",
                data=suspended_data,
                file_name=f"suspended_accounts_{platform.lower()}.{file_ext}",
                mime=mime_type
            )
        else:
            st.info("No suspended accounts")
    
    # Error accounts download
    with col3:
        error_accounts = df[~df['status'].isin(['live', 'suspended'])]
        if not error_accounts.empty:
            if download_format == "TXT":
                error_data = '\n'.join(error_accounts['original_line'].tolist())
                file_ext = "txt"
                mime_type = "text/plain"
            else:
                error_data = error_accounts.to_csv(index=False)
                file_ext = "csv"
                mime_type = "text/csv"
            
            st.download_button(
                label=f"📥 Errors ({download_format})",
                data=error_data,
                file_name=f"error_accounts_{platform.lower()}.{file_ext}",
                mime=mime_type
            )
        else:
            st.info("No error accounts")
    
    # All results download
    with col4:
        if download_format == "TXT":
            all_data = '\n'.join(df['original_line'].tolist())
            file_ext = "txt"
            mime_type = "text/plain"
        else:
            all_data = df.to_csv(index=False)
            file_ext = "csv"
            mime_type = "text/csv"
        
        st.download_button(
            label=f"📥 All Results ({download_format})",
            data=all_data,
            file_name=f"all_results_{platform.lower()}.{file_ext}",
            mime=mime_type
        )
    
    # Results Tables
    st.markdown("## 📋 Detailed Results")
    
    tab1, tab2, tab3 = st.tabs(["🟢 Live Accounts", "🔴 Suspended Accounts", "📊 All Results"])
    
    with tab1:
        live_accounts = df[df['status'] == 'live']
        if not live_accounts.empty:
            st.dataframe(live_accounts[['username', 'status', 'original_line']], use_container_width=True)
        else:
            st.info("No live accounts found")
    
    with tab2:
        suspended_accounts = df[df['status'] == 'suspended']
        if not suspended_accounts.empty:
            st.dataframe(suspended_accounts[['username', 'status', 'original_line']], use_container_width=True)
        else:
            st.info("No suspended accounts found")
    
    with tab3:
        st.dataframe(df[['username', 'status', 'original_line']], use_container_width=True)

else:
    # Welcome Page
    st.markdown("""
    ## 🚀 Welcome to Social Media Account Checker
    
    ### 📋 How to Use:
    1. **Select Platform** from sidebar (Instagram, Twitter, or TikTok)
    2. **Choose Input Method** - Upload file or paste text directly
    3. **Add Accounts** - Either upload .txt file or paste accounts in text area
    4. **Choose Download Format** - TXT or CSV
    5. **Click "Start Checking"** and monitor real-time progress
    
    ### 📝 Input Methods:
    
    #### 📁 Upload File:
    - Upload a .txt file with usernames (one per line)
    
    #### ✍️ Paste Text:
    - Paste accounts directly in the text area
    - One account per line
    
    ### 📁 Account Format:
    ```
    username1
    username2:password
    username3
    ```
    
    ### ✨ Features:
    - ✅ Fast and reliable checking
    - ✅ Professional user interface with real-time updates
    - ✅ Live progress tracking with counters
    - ✅ Pause/Resume/Stop controls
    - ✅ Multiple input methods (file upload or text paste)
    - ✅ Multiple download formats (TXT/CSV)
    - ✅ Interactive statistics and charts
    
    ### 🔧 Supported Platforms:
    """)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        #### 📷 Instagram
        - Check account status
        - Detect deleted accounts
        - Analyze active profiles
        """)
    
    with col2:
        st.markdown("""
        #### 🐦 Twitter  
        - Verify account status
        - Detect suspended accounts
        - Check profile availability
        """)
    
    with col3:
        st.markdown("""
        #### 🎵 TikTok
        - Check account status
        - Detect banned accounts
        - Verify profile existence
        """)
    
    st.markdown("---")
    st.info("💡 **Tip:** Start with a small number of accounts (10-20) to test the tool before processing large files")
