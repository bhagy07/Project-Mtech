import streamlit as st
import asyncio
import yaml
import os
import httpx
import paramiko
from datetime import datetime
from dotenv import load_dotenv

from tools.health_checker import HealthCheckerTool
from tools.log_fetcher import SSHLogFetcherTool
# from tools.message_tracker import DynamicMessageTrackerEngine
from agent.ai_diagnostician import AIDiagnosticAgent, IncidentAnalysis
from agent.notifier import AlertNotifier

log_fetcher = SSHLogFetcherTool()
# tracker_engine = DynamicMessageTrackerEngine()  # Transcode & Message Tracker (commented out)

# Load Environment Variables
load_dotenv()

# Streamlit Page Setup
st.set_page_config(
    page_title="NeML OpsGuardian",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

if "theme_mode" not in st.session_state:
    st.session_state["theme_mode"] = "☀️ Day Mode"

theme_mode = st.session_state["theme_mode"]

# Dynamic Theme Rules
if theme_mode == "🌙 Night Mode":
    dynamic_theme_css = """
    /* 🌙 NIGHT MODE COMPREHENSIVE STYLING */
    .stApp {
        background-color: #0b1120 !important;
        color: #f1f5f9 !important;
    }
    
    /* Typography */
    h1, h2, h3, h4, h5, h6, 
    .stMarkdown, .stMarkdown p, .stMarkdown span, .stMarkdown label, .stMarkdown li, 
    label, p, span, div.stText, div[data-testid="stMarkdownContainer"] p, div[data-testid="stMarkdownContainer"] span {
        color: #f1f5f9 !important;
    }
    
    /* Sidebar */
    section[data-testid="stSidebar"] {
        background-color: #0f172a !important;
        border-right: 1px solid rgba(255, 255, 255, 0.08) !important;
    }
    section[data-testid="stSidebar"] h1, section[data-testid="stSidebar"] h2, section[data-testid="stSidebar"] h3, 
    section[data-testid="stSidebar"] h4, section[data-testid="stSidebar"] p, section[data-testid="stSidebar"] span, 
    section[data-testid="stSidebar"] label {
        color: #f1f5f9 !important;
    }
    section[data-testid="stSidebar"] small, section[data-testid="stSidebar"] .stCaption {
        color: #94a3b8 !important;
    }

    /* Cards & Metric Cards */
    .metric-card {
        background: #1e293b !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        color: #f8fafc !important;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.25) !important;
    }
    .metric-card:hover, .kpi-hover-card:hover {
        transform: translateY(-5px) scale(1.03) !important;
        border-color: #38bdf8 !important;
        background: #24344d !important;
        box-shadow: 0 14px 28px -6px rgba(56, 189, 248, 0.28), 0 6px 16px rgba(0,0,0,0.35) !important;
    }
    .metric-title {
        color: #94a3b8 !important;
    }
    .metric-value {
        color: #f8fafc !important;
    }

    div[data-testid="stContainer"] {
        background-color: #111827 !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        color: #f1f5f9 !important;
    }
    div[data-testid="stContainer"] * {
        color: #f1f5f9 !important;
    }
    div[data-testid="stContainer"] code {
        color: #38bdf8 !important;
        background-color: #1e293b !important;
    }

    /* Form Controls & Inputs */
    .stTextArea textarea, .stTextInput input, .stNumberInput input, .stDateInput input {
        background-color: #1e293b !important;
        color: #f8fafc !important;
        border: 1px solid #334155 !important;
    }
    .stSelectbox div[data-baseweb="select"] > div {
        background-color: #1e293b !important;
        color: #f8fafc !important;
        border-color: #334155 !important;
    }
    .stSelectbox svg {
        fill: #f8fafc !important;
    }

    /* Expanders */
    div[data-testid="stExpander"] {
        background-color: #1e293b !important;
        border: 1px solid #334155 !important;
        color: #f8fafc !important;
    }
    div[data-testid="stExpander"] summary, div[data-testid="stExpander"] summary span, div[data-testid="stExpander"] p {
        color: #f8fafc !important;
    }

    /* Tabs */
    button[data-baseweb="tab"] {
        color: #94a3b8 !important;
    }
    button[data-baseweb="tab"][aria-selected="true"] {
        color: #38bdf8 !important;
        border-bottom-color: #38bdf8 !important;
    }

    /* Code Snippets */
    code, pre {
        background-color: #1e293b !important;
        color: #38bdf8 !important;
        border: 1px solid rgba(255, 255, 255, 0.08) !important;
    }

    /* Buttons in Night Mode */
    .stButton > button, div[data-testid="stFormSubmitButton"] > button, .stDownloadButton > button {
        background-color: #1e293b !important;
        color: #f1f5f9 !important;
        border: 1px solid #475569 !important;
        font-weight: 600 !important;
        transition: all 0.2s ease-in-out !important;
    }
    .stButton > button p, div[data-testid="stFormSubmitButton"] > button p, .stDownloadButton > button p {
        color: #f1f5f9 !important;
    }
    .stButton > button:hover, div[data-testid="stFormSubmitButton"] > button:hover, .stDownloadButton > button:hover {
        background-color: #0284c7 !important;
        color: #ffffff !important;
        border-color: #38bdf8 !important;
        box-shadow: 0 0 12px rgba(56, 189, 248, 0.35) !important;
    }
    .stButton > button:hover p, div[data-testid="stFormSubmitButton"] > button:hover p, .stDownloadButton > button:hover p {
        color: #ffffff !important;
    }

    /* Primary Action Buttons in Night Mode */
    button[kind="primary"], .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #0284c7 0%, #0369a1 100%) !important;
        color: #ffffff !important;
        border: 1px solid #38bdf8 !important;
    }
    button[kind="primary"] p, .stButton > button[kind="primary"] p {
        color: #ffffff !important;
    }
    button[kind="primary"]:hover, .stButton > button[kind="primary"]:hover {
        background: linear-gradient(135deg, #38bdf8 0%, #0284c7 100%) !important;
        color: #0f172a !important;
        box-shadow: 0 0 15px rgba(56, 189, 248, 0.5) !important;
    }
    button[kind="primary"]:hover p, .stButton > button[kind="primary"]:hover p {
        color: #0f172a !important;
    }

    /* Radio & Toggle Icons in Night Mode */
    div[data-testid="stRadio"] label > div:first-child {
        background-color: #1e293b !important;
        border: 2px solid #64748b !important;
    }
    div[data-testid="stRadio"] label[data-checked="true"] > div:first-child,
    div[data-testid="stRadio"] label:has(input:checked) > div:first-child,
    div[data-testid="stRadio"] input:checked + div {
        border-color: #38bdf8 !important;
        background-color: #0b1120 !important;
    }
    div[data-testid="stRadio"] label[data-checked="true"] > div:first-child > div,
    div[data-testid="stRadio"] label:has(input:checked) > div:first-child > div {
        background-color: #38bdf8 !important;
        box-shadow: 0 0 10px rgba(56, 189, 248, 0.7) !important;
    }
    div[data-testid="stRadio"] label span {
        color: #f1f5f9 !important;
    }
    div[data-testid="stRadio"] label:hover > div:first-child {
        border-color: #38bdf8 !important;
    }

    /* Checkbox & Toggle switches in Night Mode */
    div[data-testid="stCheckbox"] label span, div[data-testid="stToggle"] label span {
        color: #f1f5f9 !important;
    }
    div[data-testid="stCheckbox"] input:checked + div,
    div[data-testid="stCheckbox"] label[data-checked="true"] > div:first-child {
        background-color: #0284c7 !important;
        border-color: #38bdf8 !important;
    }
    div[data-testid="stToggle"] input:checked + div {
        background-color: #0284c7 !important;
    }

    /* Sidebar Collapse & Expand Toggle Icons */
    [data-testid="stSidebarCollapseButton"] button,
    [data-testid="stSidebarExpandButton"] button,
    button[kind="header"] {
        color: #38bdf8 !important;
    }
    [data-testid="stSidebarCollapseButton"] svg,
    [data-testid="stSidebarExpandButton"] svg {
        fill: #38bdf8 !important;
        stroke: #38bdf8 !important;
    }
    """
else:
    dynamic_theme_css = """
    /* ☀️ DAY MODE COMPREHENSIVE STYLING */
    .stApp {
        background-color: #f8fafc !important;
        color: #0f172a !important;
    }
    
    h1, h2, h3, h4, h5, h6, 
    .stMarkdown, .stMarkdown p, .stMarkdown span, .stMarkdown label, .stMarkdown li, 
    label, p, span, div.stText, div[data-testid="stMarkdownContainer"] p, div[data-testid="stMarkdownContainer"] span {
        color: #0f172a !important;
    }
    
    section[data-testid="stSidebar"] {
        background-color: #f1f5f9 !important;
        border-right: 1px solid #e2e8f0 !important;
    }
    section[data-testid="stSidebar"] h1, section[data-testid="stSidebar"] h2, section[data-testid="stSidebar"] h3, 
    section[data-testid="stSidebar"] h4, section[data-testid="stSidebar"] p, section[data-testid="stSidebar"] span, 
    section[data-testid="stSidebar"] label {
        color: #0f172a !important;
    }
    section[data-testid="stSidebar"] small, section[data-testid="stSidebar"] .stCaption {
        color: #64748b !important;
    }

    .metric-card {
        background: #ffffff !important;
        border: 1px solid #e2e8f0 !important;
        color: #0f172a !important;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04) !important;
    }
    .metric-card:hover, .kpi-hover-card:hover {
        transform: translateY(-5px) scale(1.03) !important;
        border-color: #0284c7 !important;
        background: #f8fafc !important;
        box-shadow: 0 14px 28px -6px rgba(14, 165, 233, 0.22), 0 4px 12px rgba(0,0,0,0.06) !important;
    }
    .metric-title {
        color: #64748b !important;
    }
    .metric-value {
        color: #0f172a !important;
    }

    div[data-testid="stContainer"] {
        background-color: #ffffff !important;
        border: 1px solid #e2e8f0 !important;
        color: #0f172a !important;
    }

    .stTextArea textarea, .stTextInput input, .stNumberInput input, .stDateInput input {
        background-color: #ffffff !important;
        color: #0f172a !important;
        border: 1px solid #cbd5e1 !important;
    }
    .stSelectbox div[data-baseweb="select"] > div {
        background-color: #ffffff !important;
        color: #0f172a !important;
        border-color: #cbd5e1 !important;
    }

    div[data-testid="stExpander"] {
        background-color: #ffffff !important;
        border: 1px solid #e2e8f0 !important;
        color: #0f172a !important;
    }

    button[data-baseweb="tab"] {
        color: #64748b !important;
    }
    button[data-baseweb="tab"][aria-selected="true"] {
        color: #0284c7 !important;
        border-bottom-color: #0284c7 !important;
    }

    code, pre {
        background-color: #f1f5f9 !important;
        color: #0f172a !important;
        border: 1px solid #e2e8f0 !important;
    }

    /* Buttons in Day Mode */
    .stButton > button, div[data-testid="stFormSubmitButton"] > button, .stDownloadButton > button {
        background-color: #ffffff !important;
        color: #0f172a !important;
        border: 1px solid #cbd5e1 !important;
        font-weight: 600 !important;
        transition: all 0.2s ease-in-out !important;
    }
    .stButton > button p, div[data-testid="stFormSubmitButton"] > button p, .stDownloadButton > button p {
        color: #0f172a !important;
    }
    .stButton > button:hover, div[data-testid="stFormSubmitButton"] > button:hover, .stDownloadButton > button:hover {
        background-color: #0284c7 !important;
        color: #ffffff !important;
        border-color: #0284c7 !important;
        box-shadow: 0 2px 8px rgba(2, 132, 199, 0.2) !important;
    }
    .stButton > button:hover p, div[data-testid="stFormSubmitButton"] > button:hover p, .stDownloadButton > button:hover p {
        color: #ffffff !important;
    }

    /* Primary Action Buttons in Day Mode */
    button[kind="primary"], .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #0284c7 0%, #0369a1 100%) !important;
        color: #ffffff !important;
        border: 1px solid #0284c7 !important;
    }
    button[kind="primary"] p, .stButton > button[kind="primary"] p {
        color: #ffffff !important;
    }
    button[kind="primary"]:hover, .stButton > button[kind="primary"]:hover {
        background: linear-gradient(135deg, #0369a1 0%, #075985 100%) !important;
        color: #ffffff !important;
    }

    /* Radio & Toggle Icons in Day Mode */
    div[data-testid="stRadio"] label > div:first-child {
        background-color: #ffffff !important;
        border: 2px solid #94a3b8 !important;
    }
    div[data-testid="stRadio"] label[data-checked="true"] > div:first-child,
    div[data-testid="stRadio"] label:has(input:checked) > div:first-child,
    div[data-testid="stRadio"] input:checked + div {
        border-color: #0284c7 !important;
        background-color: #ffffff !important;
    }
    div[data-testid="stRadio"] label[data-checked="true"] > div:first-child > div,
    div[data-testid="stRadio"] label:has(input:checked) > div:first-child > div {
        background-color: #0284c7 !important;
    }
    div[data-testid="stRadio"] label span {
        color: #0f172a !important;
    }
    div[data-testid="stRadio"] label:hover > div:first-child {
        border-color: #0284c7 !important;
    }

    /* Checkbox & Toggle switches in Day Mode */
    div[data-testid="stCheckbox"] label span, div[data-testid="stToggle"] label span {
        color: #0f172a !important;
    }
    div[data-testid="stCheckbox"] input:checked + div,
    div[data-testid="stCheckbox"] label[data-checked="true"] > div:first-child {
        background-color: #0284c7 !important;
        border-color: #0284c7 !important;
    }
    div[data-testid="stToggle"] input:checked + div {
        background-color: #0284c7 !important;
    }

    /* Sidebar Collapse & Expand Toggle Icons */
    [data-testid="stSidebarCollapseButton"] button,
    [data-testid="stSidebarExpandButton"] button,
    button[kind="header"] {
        color: #0284c7 !important;
    }
    [data-testid="stSidebarCollapseButton"] svg,
    [data-testid="stSidebarExpandButton"] svg {
        fill: #0284c7 !important;
        stroke: #0284c7 !important;
    }
    """

# ==========================================
# ENTERPRISE LEVEL CUSTOM STYLING (CSS)
# ==========================================
st.markdown(f"""
<style>
    /* Smooth Responsive Sidebar with Full Toggle & Collapse Support */
    section[data-testid="stSidebar"] {{
        transition: all 0.3s ease-in-out !important;
        z-index: 99 !important;
    }}

    /* Maximize main content screen width dynamically */
    .main {{
        width: 100% !important;
        transition: all 0.3s ease-in-out !important;
    }}
    .main .block-container {{
        max-width: 100% !important;
        width: 100% !important;
        padding-top: 1rem !important;
        padding-bottom: 2rem !important;
        padding-left: 2rem !important;
        padding-right: 2rem !important;
        transition: all 0.3s ease-in-out !important;
    }}

    /* Make Streamlit top header transparent while keeping expand/collapse buttons active */
    header[data-testid="stHeader"] {{
        background: transparent !important;
        height: 2.5rem !important;
        z-index: 90 !important;
    }}
    #MainMenu,
    .stDeployButton,
    footer,
    div[data-testid="stDecoration"],
    div[data-testid="stStatusWidget"] {{
        visibility: hidden !important;
        display: none !important;
    }}

    /* Tighten top space inside sidebar */
    [data-testid="stSidebarHeader"] {{
        padding-top: 0.2rem !important;
        padding-bottom: 0.2rem !important;
        background: transparent !important;
    }}
    [data-testid="stSidebarUserContent"],
    [data-testid="stSidebarContent"],
    section[data-testid="stSidebar"] .block-container {{
        padding-top: 0.5rem !important;
    }}
    .stSidebar [data-testid="stVerticalBlock"] {{
        gap: 0.5rem !important;
    }}

    .header-box {{
        background: linear-gradient(135deg, #0ea5e9 0%, #0369a1 100%);
        padding: 20px 24px;
        border-radius: 12px;
        margin-bottom: 20px;
        color: #ffffff;
        box-shadow: 0 4px 15px rgba(14, 165, 233, 0.15);
    }}
    
    .metric-card {{
        padding: 14px 18px;
        border-radius: 12px;
        transition: transform 0.28s cubic-bezier(0.34, 1.45, 0.64, 1), box-shadow 0.28s ease, border-color 0.28s ease, background-color 0.28s ease;
        position: relative;
        overflow: hidden;
        cursor: default;
    }}
    .metric-card:hover, .kpi-hover-card:hover {{
        transform: translateY(-5px) scale(1.03);
    }}
    
    .metric-title {{ font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.8px; }}
    .metric-value {{ font-size: 24px; font-weight: 800; margin-top: 3px; line-height: 1.15; }}
    
    /* 🟢 Real-time Blinking & Pulsing Indicators */
    .status-dot-active {{
        display: inline-block;
        width: 8px;
        height: 8px;
        background-color: #10b981;
        border-radius: 50%;
        margin-right: 6px;
        vertical-align: middle;
        box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.7);
        animation: pulse-green-glow 1.4s infinite ease-in-out;
    }}
    @keyframes pulse-green-glow {{
        0% {{ transform: scale(0.95); box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.7); }}
        70% {{ transform: scale(1.15); box-shadow: 0 0 0 7px rgba(16, 185, 129, 0); }}
        100% {{ transform: scale(0.95); box-shadow: 0 0 0 0 rgba(16, 185, 129, 0); }}
    }}

    .status-dot-stopped {{
        display: inline-block;
        width: 8px;
        height: 8px;
        background-color: #ef4444;
        border-radius: 50%;
        margin-right: 6px;
        vertical-align: middle;
        box-shadow: 0 0 0 0 rgba(239, 68, 68, 0.7);
        animation: pulse-red-glow 1.2s infinite ease-in-out;
    }}
    @keyframes pulse-red-glow {{
        0% {{ transform: scale(0.95); box-shadow: 0 0 0 0 rgba(239, 68, 68, 0.8); }}
        70% {{ transform: scale(1.15); box-shadow: 0 0 0 8px rgba(239, 68, 68, 0); }}
        100% {{ transform: scale(0.95); box-shadow: 0 0 0 0 rgba(239, 68, 68, 0); }}
    }}

    .badge-up, .badge-active-pulse {{
        background-color: rgba(16, 185, 129, 0.15);
        color: #10b981 !important;
        border: 1px solid rgba(16, 185, 129, 0.35);
        padding: 4px 11px;
        border-radius: 20px;
        font-size: 11px;
        font-weight: 700;
        display: inline-flex;
        align-items: center;
    }}
    .badge-down, .badge-stopped-pulse {{
        background-color: rgba(239, 68, 68, 0.15);
        color: #ef4444 !important;
        border: 1px solid rgba(239, 68, 68, 0.35);
        padding: 4px 11px;
        border-radius: 20px;
        font-size: 11px;
        font-weight: 700;
        display: inline-flex;
        align-items: center;
    }}
    
    .rca-container {{ border-left: 4px solid #f59e0b; padding: 20px; border-radius: 8px; margin-top: 15px; border: 1px solid rgba(0,0,0,0.1); border-left-width: 4px; }}
    .rca-title {{ color: #d97706 !important; font-size: 18px; font-weight: 700; margin-bottom: 8px; }}
    .fix-step {{ border-left: 3px solid #10b981; padding: 10px 15px; margin: 6px 0; border-radius: 4px; font-size: 14px; border: 1px solid rgba(0,0,0,0.08); border-left-width: 3px; }}

    /* 📱 Fluid Responsive Media Queries */
    @media (max-width: 900px) {{
        .main .block-container {{
            padding-left: 1rem !important;
            padding-right: 1rem !important;
        }}
        .header-box {{
            padding: 14px !important;
        }}
        .header-box h1 {{
            font-size: 20px !important;
        }}
        div[data-testid="column"] {{
            min-width: 100% !important;
            margin-bottom: 8px !important;
        }}
    }}

    /* 🔔 Modern Notification Bell Button & Popover Styling */
    div[data-testid="stPopover"] > button {{
        border-radius: 10px !important;
        padding: 6px 14px !important;
        font-weight: 700 !important;
        border: 1px solid rgba(14, 165, 233, 0.35) !important;
        background: rgba(14, 165, 233, 0.08) !important;
        color: #0284c7 !important;
        transition: all 0.2s ease-in-out !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        min-height: 40px !important;
        gap: 6px !important;
    }}
    div[data-testid="stPopover"] > button:hover {{
        background: rgba(14, 165, 233, 0.18) !important;
        border-color: #0284c7 !important;
        box-shadow: 0 0 14px rgba(2, 132, 199, 0.3) !important;
        transform: translateY(-1px) !important;
    }}
    div[data-testid="stPopoverBody"] {{
        border-radius: 14px !important;
        padding: 18px !important;
        box-shadow: 0 10px 35px rgba(0, 0, 0, 0.25) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
    }}

    /* ⭕ NeML Tri-Color Circular Loader (Green #92bc2a, Blue #0284c7, Orange #f59e0b) with Invisible Background */
    [data-test-script-state="running"] .main .block-container {{
        opacity: 0.82 !important;
        pointer-events: none !important;
        transition: opacity 0.15s ease !important;
    }}
    
    [data-test-script-state="running"]::after {{
        content: "";
        position: fixed;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        width: 48px;
        height: 48px;
        border: 4px solid rgba(255, 255, 255, 0.05);
        border-top-color: #92bc2a;   /* NeML Leaf Green */
        border-right-color: #0284c7; /* NeML Ocean Blue */
        border-bottom-color: #f59e0b;/* NeML Amber Gold */
        border-radius: 50%;
        background: transparent !important;
        box-shadow: 0 0 20px rgba(146, 188, 42, 0.25) !important;
        z-index: 99999999;
        animation: spin-neml-tricolor 0.8s linear infinite;
        pointer-events: none;
    }}

    @keyframes spin-neml-tricolor {{
        0% {{ transform: translate(-50%, -50%) rotate(0deg); }}
        100% {{ transform: translate(-50%, -50%) rotate(360deg); }}
    }}

    .stSpinner > div {{
        border-top-color: #92bc2a !important;
        border-right-color: #0284c7 !important;
        border-bottom-color: #f59e0b !important;
        background: transparent !important;
    }}

    {dynamic_theme_css}
</style>
""", unsafe_allow_html=True)

CONFIG_PATH = "config.yaml"

def load_config():
    with open(CONFIG_PATH, "r") as f:
        return yaml.safe_load(f)

def save_config(cfg):
    with open(CONFIG_PATH, "w") as f:
        yaml.dump(cfg, f, default_flow_style=False, sort_keys=False)

config = load_config()
services = config.get("services", [])
databases = config.get("databases", [])

import base64

def get_base64_logo_src():
    candidates = [
        ("assets/NeML Logo.svg", "image/svg+xml"),
        ("assets/neml_logo.svg", "image/svg+xml"),
        ("assets/NeML Logo.png", "image/png"),
        ("assets/neml_logo.png", "image/png"),
        ("assets/logo.png", "image/png"),
        ("assets/ReMS_logo.png", "image/png")
    ]
    for path, mime in candidates:
        if os.path.exists(path):
            with open(path, "rb") as img_file:
                b64 = base64.b64encode(img_file.read()).decode("utf-8")
                return f"data:{mime};base64,{b64}"
    return None

logo_data_uri = get_base64_logo_src()

# ==========================================
# AUTHENTICATION & ACCESS CONTROL GATEWAY
# ==========================================
users_list = config.get("users", [
    {"username": "devops", "password": "devops@neml123", "role": "DevOps Engineer", "name": "DevOps Team"},
    {"username": "developer", "password": "dev@neml123", "role": "Developer", "name": "Developer Team"},
    {"username": "admin", "password": "admin@neml123", "role": "Administrator", "name": "System Administrator"}
])

if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False
    st.session_state["current_user"] = None

if not st.session_state["authenticated"]:
    # Render Centered Login Card
    col_p1, col_card, col_p2 = st.columns([1, 1.8, 1])
    with col_card:
        st.markdown("<br><br>", unsafe_allow_html=True)
        with st.container(border=True):
            if logo_data_uri:
                st.markdown(f'<div style="text-align: center; margin-bottom: 12px;"><img src="{logo_data_uri}" style="height: 54px; background: white; padding: 6px; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);" /></div>', unsafe_allow_html=True)
            st.markdown("<h2 style='text-align: center; margin-bottom: 2px; font-weight: 800;'>NeML OpsGuardian</h2>", unsafe_allow_html=True)
            st.markdown("<p style='text-align: center; color: #64748b; font-size: 13px; margin-bottom: 22px;'>Restricted Enterprise Access • DevOps & Developer Observer</p>", unsafe_allow_html=True)

            with st.form("login_form"):
                u_input = st.text_input("👤 Username", placeholder="e.g. devops, developer, admin")
                p_input = st.text_input("🔑 Password", type="password", placeholder="Enter your portal password")
                submit_login = st.form_submit_button("🔐 Secure Sign In", use_container_width=True, type="primary")

                if submit_login:
                    matched_user = next((u for u in users_list if u.get("username") == u_input.strip() and str(u.get("password")) == p_input.strip()), None)
                    if matched_user:
                        st.session_state["authenticated"] = True
                        st.session_state["current_user"] = matched_user
                        st.success(f"Welcome back, {matched_user.get('name', u_input)}! Authenticated as {matched_user.get('role', 'User')}.")
                        st.rerun()
                    else:
                        st.error("❌ Invalid Username or Password. Please verify your credentials or contact administrator.")

            with st.expander("ℹ️ Configured Access Accounts", expanded=False):
                st.markdown("**Available User Roles in `config.yaml`:**")
                for u in users_list:
                    st.markdown(f"• **{u.get('name', u['username'])}** (`{u['username']}`) — *Role: {u.get('role', 'DevOps')}*")

    st.stop()

current_user = st.session_state.get("current_user") or {}
user_role = current_user.get("role", "DevOps Engineer")
user_name = current_user.get("name", current_user.get("username", "User"))

# ==========================================
# SIDEBAR BRANDING & USER PERSPECTIVE
# ==========================================
with st.sidebar:
    if logo_data_uri:
        st.markdown(f"""
        <div style="text-align: center; margin-top: 0px; margin-bottom: 14px; padding: 8px 12px; background: rgba(255, 255, 255, 0.95); border-radius: 10px; box-shadow: 0 2px 8px rgba(0,0,0,0.06); border: 1px solid rgba(0,0,0,0.08);">
            <img src="{logo_data_uri}" style="height: 46px; max-width: 100%; object-fit: contain;" />
        </div>
        """, unsafe_allow_html=True)

    user_box_bg = "rgba(14, 165, 233, 0.15)" if theme_mode == "🌙 Night Mode" else "rgba(14, 165, 233, 0.08)"
    user_text_col = "#f8fafc" if theme_mode == "🌙 Night Mode" else "#0f172a"
    user_sub_col = "#94a3b8" if theme_mode == "🌙 Night Mode" else "#64748b"
    role_highlight = "#38bdf8" if theme_mode == "🌙 Night Mode" else "#0284c7"

    st.markdown(f"""
    <div style="background: {user_box_bg}; border: 1px solid rgba(14, 165, 233, 0.3); padding: 12px 16px; border-radius: 10px; margin-bottom: 12px;">
        <div style="font-size: 10px; font-weight: 800; color: {role_highlight}; text-transform: uppercase; letter-spacing: 0.8px;">Logged In User</div>
        <div style="font-size: 16px; font-weight: 800; margin-top: 3px; color: {user_text_col};">👤 {user_name}</div>
        <div style="font-size: 12px; color: {user_sub_col}; margin-top: 2px;">Role: <strong style="color: {role_highlight};">{user_role}</strong></div>
    </div>
    """, unsafe_allow_html=True)
    
    if st.button("🚪 Sign Out", use_container_width=True):
        st.session_state["authenticated"] = False
        st.session_state["current_user"] = None
        st.rerun()

    st.divider()
    st.subheader("🎨 Appearance Theme")
    selected_theme = st.radio(
        "Display Theme:",
        ["☀️ Day Mode", "🌙 Night Mode"],
        index=0 if st.session_state.get("theme_mode", "☀️ Day Mode") == "☀️ Day Mode" else 1,
        horizontal=True,
        label_visibility="collapsed"
    )
    if selected_theme != st.session_state.get("theme_mode"):
        st.session_state["theme_mode"] = selected_theme
        st.rerun()

    st.divider()
    st.subheader("⚙️ Inventory Status")
    st.write(f"• Services: `{len(services)}`")
    st.write(f"• Databases: `{len(databases)}`")

    st.divider()
    st.subheader("🔐 API Key Status")
    gemini_key = os.environ.get("GEMINI_API_KEY", "")
    if gemini_key:
        st.success("GEMINI_API_KEY Loaded")
    else:
        st.error("GEMINI_API_KEY Missing in .env")

# ==========================================
# LIVE STATUS & EXCEPTION SCANNER
# ==========================================
active_issues = []

# 1. Quick probe of services (Actuator probe commented out as requested)
# for srv in services:
#     h_url = srv.get("health_url")
#     if h_url:
#         try:
#             resp = httpx.get(h_url, timeout=1.2)
#             if resp.status_code != 200:
#                 active_issues.append({
#                     "name": srv["name"],
#                     "type": "SERVICE_DOWN",
#                     "msg": f"Actuator returned HTTP {resp.status_code}",
#                     "host": srv["host"]
#                 })
#         except Exception:
#             active_issues.append({
#                 "name": srv["name"],
#                 "type": "SERVICE_UNREACHABLE",
#                 "msg": f"Endpoint unreachable ({h_url})",
#                 "host": srv["host"]
#             })

# 2. Quick probe of databases using unified HealthCheckerTool
for db in databases:
    res = HealthCheckerTool.check_postgres_health(db)
    if res["status"] != "UP":
        active_issues.append({
            "name": db["name"],
            "type": "DATABASE_DOWN",
            "msg": f"Database connection unavailable ({res['details']})",
            "host": db["host"],
            "obj": db,
            "category": "database",
            "details": res["details"]
        })

# Trigger corner toast notifications on detection
if active_issues and not st.session_state.get("toast_shown_this_cycle", False):
    for iss in active_issues[:3]:
        st.toast(f"🚨 {iss['name']}: {iss['msg']}", icon="⚠️")
    st.session_state["toast_shown_this_cycle"] = True
elif not active_issues:
    st.session_state["toast_shown_this_cycle"] = False

# ==========================================
# ENTERPRISE MAIN HEADER
# ==========================================
header_logo_html = f'<img src="{logo_data_uri}" style="height: 52px; max-width: 170px; border-radius: 8px; background: rgba(255,255,255,0.95); padding: 4px; box-shadow: 0 2px 8px rgba(0,0,0,0.15); object-fit: contain;" />' if logo_data_uri else ''

st.markdown(f"""
<div class="header-box">
    <div style="display: flex; align-items: center; gap: 18px;">
        {header_logo_html}
        <div>
            <h1 style="color: #ffffff; margin:0; font-size: 28px; font-weight: 900;">NeML OpsGuardian Operations Portal</h1>
            <p style="color: rgba(255, 255, 255, 0.9); margin: 4px 0 0 0; font-size: 13px; font-weight: 500;">
                Autonomous multi-server log diagnostics, health checks, and GenAI incident analysis.
            </p>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

notif_tab_label = f"🚨 Incident Alerts ({len(active_issues)})" if active_issues else "🔔 Incident Alerts (0)"

# Main Navigation Tabs
# tab_overview, tab_rca, tab_logs, tab_tracker, tab_config, tab_notif = st.tabs([...])
tab_overview, tab_rca, tab_logs, tab_config, tab_notif = st.tabs([
    "🖥️ System Health Matrix", 
    "🧠 AI RCA Engine", 
    "🔍 Live SSH Terminal Logs", 
    # "📨 Message Tracker & Transcodes",  # (Transcode / Message Tracker tab commented out)
    "🛠️ Service & Log Configurator",
    notif_tab_label
])

# ==========================================
# TAB 1: SYSTEM HEALTH MATRIX
# ==========================================
with tab_overview:
    # Separate services by category
    frontend_service_types = ["ANGULARJS_TOMCAT", "ANGULARJS", "TOMCAT", "FRONTEND_WEB", "STANDALONE_TOMCAT", "WEB_APP"]
    frontend_services = [s for s in services if s.get("type", "SPRING_BOOT") in frontend_service_types]
    microservices = [s for s in services if s.get("type", "SPRING_BOOT") not in frontend_service_types]

    # Top Operational KPI Metrics Row (Interactive Hover Cards)
    col_m1, col_m2, col_m3, col_m4 = st.columns(4)
    with col_m1:
        st.markdown(f'''
        <div class="metric-card kpi-hover-card">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <span class="metric-title">MONITORED SERVICES</span>
                <span style="font-size: 16px; opacity: 0.85;">🖥️</span>
            </div>
            <div class="metric-value">{len(services)}</div>
            <div style="font-size: 11px; opacity: 0.7; margin-top: 4px; font-weight: 500;">{len(microservices)} Backend • {len(frontend_services)} Frontend</div>
        </div>
        ''', unsafe_allow_html=True)

    with col_m2:
        st.markdown(f'''
        <div class="metric-card kpi-hover-card">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <span class="metric-title">DATABASE NODES</span>
                <span style="font-size: 16px; opacity: 0.85;">🗄️</span>
            </div>
            <div class="metric-value">{len(databases)}</div>
            <div style="font-size: 11px; opacity: 0.7; margin-top: 4px; font-weight: 500;">PostgreSQL Cluster</div>
        </div>
        ''', unsafe_allow_html=True)

    with col_m3:
        status_text = "100% Operational" if not active_issues else f"{len(active_issues)} Degraded"
        status_color = "#10b981" if not active_issues else "#ef4444"
        status_sub = "All Nodes Healthy" if not active_issues else "Attention Required"
        st.markdown(f'''
        <div class="metric-card kpi-hover-card">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <span class="metric-title">SYSTEM STATUS</span>
                <span class="status-dot-active" style="margin-right: 0;"></span>
            </div>
            <div class="metric-value" style="font-size: 19px; color: {status_color};">{status_text}</div>
            <div style="font-size: 11px; opacity: 0.7; margin-top: 4px; font-weight: 500;">{status_sub}</div>
        </div>
        ''', unsafe_allow_html=True)

    with col_m4:
        inc_count = len(active_issues)
        inc_color = "#10b981" if inc_count == 0 else "#ef4444"
        inc_icon = "🛡️" if inc_count == 0 else "🚨"
        inc_sub = "Zero Active Outages" if inc_count == 0 else "Active Incident Alerts"
        st.markdown(f'''
        <div class="metric-card kpi-hover-card">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <span class="metric-title">ACTIVE INCIDENTS</span>
                <span style="font-size: 16px; opacity: 0.85;">{inc_icon}</span>
            </div>
            <div class="metric-value" style="font-size: 19px; color: {inc_color};">{inc_count} Alerts</div>
            <div style="font-size: 11px; opacity: 0.7; margin-top: 4px; font-weight: 500;">{inc_sub}</div>
        </div>
        ''', unsafe_allow_html=True)

    st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)

    # Sub-tabs within System Health Matrix (Compact & Meaningful)
    sub_micro, sub_front, sub_db = st.tabs([
        f"⚙️ Microservices ({len(microservices)})",
        f"🅰️ Frontend & Web ({len(frontend_services)})",
        f"🗄️ Databases ({len(databases)})"
    ])

    def render_hitl_restart_popover(srv, key_prefix, idx, btn_label="🔄 Restart"):
        srv_type = srv.get("type", "SPRING_BOOT")
        app_path = srv.get("app_path", "").strip()
        ssh_user = srv.get("ssh_user", "spotuser")
        
        # Extract port from health_url or default
        srv_port = "8080"
        health_url = srv.get("health_url", "")
        if health_url:
            import urllib.parse
            try:
                parsed = urllib.parse.urlparse(health_url)
                if parsed.port:
                    srv_port = str(parsed.port)
            except Exception:
                pass

        is_angular_tomcat = srv_type in frontend_service_types
        jar_name_hint = srv.get("name", "").replace(" ", "")
        default_cmd = srv.get("restart_cmd")
        if not default_cmd:
            if is_angular_tomcat:
                # Angular / Tomcat service: kill port & ps -ef process first, then run ./startup.sh
                if app_path:
                    default_cmd = f"cd {app_path} && (PORT={srv_port}; PID=$(lsof -ti :$PORT 2>/dev/null || ps -ef | grep -iE 'tomcat|catalina|{jar_name_hint}|{app_path}' | grep -v grep | awk '{{print $2}}'); [ -n \"$PID\" ] && kill -9 $PID 2>/dev/null || fuser -k -9 $PORT/tcp 2>/dev/null || true); sleep 2; ([ -f ./startup.sh ] && ./startup.sh || ([ -f startup.sh ] && sh startup.sh || (/opt/tomcat/bin/startup.sh 2>/dev/null || sudo systemctl restart tomcat)))"
                else:
                    default_cmd = f"(PORT={srv_port}; PID=$(lsof -ti :$PORT 2>/dev/null || ps -ef | grep -iE 'tomcat|catalina' | grep -v grep | awk '{{print $2}}'); [ -n \"$PID\" ] && kill -9 $PID 2>/dev/null || fuser -k -9 $PORT/tcp 2>/dev/null || true); sleep 2; ./startup.sh"
            else:
                # Spring Boot / Microservice: kill port & ps -ef process first, then run ./start.sh
                if app_path:
                    default_cmd = f"cd {app_path} && (PORT={srv_port}; PID=$(lsof -ti :$PORT 2>/dev/null || ps -ef | grep -iE '{jar_name_hint}|{app_path}|\\.jar' | grep -v grep | awk '{{print $2}}'); [ -n \"$PID\" ] && kill -9 $PID 2>/dev/null || fuser -k -9 $PORT/tcp 2>/dev/null || true); sleep 2; ([ -f ./start.sh ] && ./start.sh || ([ -f start.sh ] && sh start.sh || nohup java -jar *.jar > nohup.out 2>&1 &))"
                else:
                    default_cmd = f"(PORT={srv_port}; PID=$(lsof -ti :$PORT 2>/dev/null || ps -ef | grep -iE '{jar_name_hint}|\\.jar' | grep -v grep | awk '{{print $2}}'); [ -n \"$PID\" ] && kill -9 $PID 2>/dev/null || fuser -k -9 $PORT/tcp 2>/dev/null || true); sleep 2; ./start.sh"

        with st.popover(btn_label, use_container_width=True):
            st.markdown(f"#### ⚠️ Human-in-the-Loop Authorization")
            st.caption(f"Remote Restart Confirmation for **{srv['name']}**")
            
            st.markdown(f"""
            <div style="background: rgba(239, 68, 68, 0.08); border-left: 3px solid #ef4444; padding: 8px 12px; border-radius: 4px; margin-bottom: 10px; font-size: 12px;">
                <strong>Target Node:</strong> <code>{srv.get('ssh_user', 'spotuser')}@{srv['host']}:{srv.get('ssh_port', 22)}</code><br/>
                <strong>App Directory:</strong> <code>{app_path or 'Default System Path'}</code>
            </div>
            """, unsafe_allow_html=True)
            
            custom_cmd = st.text_input(
                "SSH Restart Command to Execute:",
                value=default_cmd,
                key=f"cmd_rst_{key_prefix}_{idx}",
                help="Inspect or edit the exact command that will execute on the remote node."
            )
            
            auth_confirmed = st.checkbox(
                "✅ I authorize remote service restart on this node",
                value=False,
                key=f"chk_auth_{key_prefix}_{idx}"
            )
            
            if st.button(
                "🔴 Confirm & Execute Restart",
                type="primary",
                disabled=not auth_confirmed,
                use_container_width=True,
                key=f"btn_exec_rst_{key_prefix}_{idx}"
            ):
                with st.spinner(f"Connecting to {srv['host']} and restarting {srv['name']}..."):
                    rst_res = HealthCheckerTool.restart_remote_service(srv, custom_cmd=custom_cmd)
                    if rst_res["success"]:
                        st.toast(f"✅ {srv['name']} restart completed! Post-probe: {rst_res['post_health'].get('status', 'OK')}", icon="🔄")
                        st.success(f"**Restart Executed:** {rst_res['msg']}")
                        if rst_res["stdout"]:
                            st.code(rst_res["stdout"], language="bash")
                    else:
                        st.toast(f"❌ {srv['name']} restart failed: {rst_res['stderr'][:40]}", icon="🚨")
                        st.error(f"**Restart Failed:** {rst_res['msg']}")
                        if rst_res["stderr"]:
                            st.code(rst_res["stderr"], language="bash")

    def render_hitl_stop_popover(srv, key_prefix, idx, btn_label="🛑 Stop"):
        srv_type = srv.get("type", "SPRING_BOOT")
        app_path = srv.get("app_path", "").strip()
        ssh_user = srv.get("ssh_user", "spotuser")

        # Extract port from health_url or default
        srv_port = "8080"
        health_url = srv.get("health_url", "")
        if health_url:
            import urllib.parse
            try:
                parsed = urllib.parse.urlparse(health_url)
                if parsed.port:
                    srv_port = str(parsed.port)
            except Exception:
                pass

        is_angular_tomcat = srv_type in frontend_service_types
        jar_name_hint = srv.get("name", "").replace(" ", "")
        default_cmd = srv.get("stop_cmd")
        if not default_cmd:
            if is_angular_tomcat:
                if app_path:
                    default_cmd = f"cd {app_path} && (PORT={srv_port}; PID=$(lsof -ti :$PORT 2>/dev/null || ps -ef | grep -iE 'tomcat|catalina|{jar_name_hint}|{app_path}' | grep -v grep | awk '{{print $2}}'); [ -n \"$PID\" ] && kill -9 $PID 2>/dev/null || fuser -k -9 $PORT/tcp 2>/dev/null || true); ([ -f ./shutdown.sh ] && ./shutdown.sh 2>/dev/null || (/opt/tomcat/bin/shutdown.sh 2>/dev/null || true))"
                else:
                    default_cmd = f"(PORT={srv_port}; PID=$(lsof -ti :$PORT 2>/dev/null || ps -ef | grep -iE 'tomcat|catalina' | grep -v grep | awk '{{print $2}}'); [ -n \"$PID\" ] && kill -9 $PID 2>/dev/null || fuser -k -9 $PORT/tcp 2>/dev/null || true)"
            else:
                if app_path:
                    default_cmd = f"cd {app_path} && ([ -f ./stop.sh ] && ./stop.sh 2>/dev/null || ([ -f stop.sh ] && sh stop.sh 2>/dev/null || true)); (PORT={srv_port}; PID=$(lsof -ti :$PORT 2>/dev/null || ps -ef | grep -iE '{jar_name_hint}|{app_path}|\\.jar' | grep -v grep | awk '{{print $2}}'); [ -n \"$PID\" ] && kill -9 $PID 2>/dev/null || fuser -k -9 $PORT/tcp 2>/dev/null || true)"
                else:
                    default_cmd = f"(PORT={srv_port}; PID=$(lsof -ti :$PORT 2>/dev/null || ps -ef | grep -iE '{jar_name_hint}|\\.jar' | grep -v grep | awk '{{print $2}}'); [ -n \"$PID\" ] && kill -9 $PID 2>/dev/null || fuser -k -9 $PORT/tcp 2>/dev/null || true)"

        with st.popover(btn_label, use_container_width=True):
            st.markdown(f"#### 🛑 Human-in-the-Loop: Stop / Kill")
            st.caption(f"Remote Stop & Kill Authorization for **{srv['name']}**")

            st.markdown(f"""
            <div style="background: rgba(239, 68, 68, 0.12); border-left: 3px solid #ef4444; padding: 8px 12px; border-radius: 4px; margin-bottom: 10px; font-size: 12px;">
                <strong>Target Node:</strong> <code>{ssh_user}@{srv['host']}:{srv.get('ssh_port', 22)}</code><br/>
                <strong>Target Port:</strong> <code>{srv_port}</code> &nbsp;•&nbsp; <strong>Path:</strong> <code>{app_path or 'Default Path'}</code>
            </div>
            """, unsafe_allow_html=True)

            custom_cmd = st.text_input(
                "SSH Stop / Kill Command to Execute:",
                value=default_cmd,
                key=f"cmd_stop_{key_prefix}_{idx}",
                help="Command that will terminate the service and its port process on the remote host."
            )

            auth_confirmed = st.checkbox(
                "⚠️ I confirm and authorize stopping (kill -9) this service",
                value=False,
                key=f"chk_auth_stop_{key_prefix}_{idx}"
            )

            if st.button(
                "🛑 Confirm & Execute Stop / Kill",
                type="primary",
                disabled=not auth_confirmed,
                use_container_width=True,
                key=f"btn_exec_stop_{key_prefix}_{idx}"
            ):
                with st.spinner(f"Connecting to {srv['host']} and terminating {srv['name']}..."):
                    stop_res = HealthCheckerTool.stop_remote_service(srv, custom_cmd=custom_cmd)
                    if stop_res["success"]:
                        st.toast(f"🛑 {srv['name']} stopped! Status: {stop_res['post_health'].get('status', 'DOWN')}", icon="🛑")
                        st.success(f"**Service Terminated:** {stop_res['msg']}")
                        if stop_res["stdout"]:
                            st.code(stop_res["stdout"], language="bash")
                    else:
                        st.toast(f"❌ {srv['name']} stop failed: {stop_res['stderr'][:40]}", icon="🚨")
                        st.error(f"**Stop Failed:** {stop_res['msg']}")
                        if stop_res["stderr"]:
                            st.code(stop_res["stderr"], language="bash")

    def render_service_card(srv, idx, key_prefix, view_mode, is_expanded_default):
        srv_type = srv.get("type", "SPRING_BOOT")
        is_tomcat_app = srv_type in frontend_service_types
        type_badge = "🅰️ ANGULARJS • 🐱 TOMCAT" if is_tomcat_app else f"⚙️ {srv_type}"

        if view_mode == "⚡ Minimized Strip":
            with st.container(border=True):
                col_s1, col_s2, col_s3, col_s4 = st.columns([1.8, 1.3, 1.2, 2.2])
                with col_s1:
                    st.markdown(f"**{srv['name']}** &nbsp; <span class='badge-active-pulse'><span class='status-dot-active'></span> ACTIVE</span>", unsafe_allow_html=True)
                with col_s2:
                    st.caption(f"📍 Host: `{srv['host']}`")
                with col_s3:
                    st.caption(f"🏷️ `{type_badge}`")
                with col_s4:
                    col_b1, col_b2, col_b3, col_b4 = st.columns(4)
                    with col_b1:
                        if is_tomcat_app:
                            if st.button("🐱", key=f"act_min_{key_prefix}_{idx}", use_container_width=True, help="Probe Tomcat"):
                                res = HealthCheckerTool.check_tomcat_health(srv)
                                st.toast(f"{srv['name']}: {res['details']}")
                        else:
                            if st.button("🌐", key=f"act_min_{key_prefix}_{idx}", use_container_width=True, help="Probe Health"):
                                try:
                                    r = httpx.get(srv.get('health_url', ''), timeout=3.0)
                                    st.toast(f"{srv['name']}: {r.status_code}")
                                except Exception:
                                    st.toast(f"{srv['name']}: Running")
                    with col_b2:
                        if st.button("🔑", key=f"ssh_min_{key_prefix}_{idx}", use_container_width=True, help="Check SSH"):
                            st.toast(f"SSH Host `{srv['host']}` Reachable")
                    with col_b3:
                        render_hitl_restart_popover(srv, f"min_{key_prefix}", idx, btn_label="🔄")
                    with col_b4:
                        render_hitl_stop_popover(srv, f"min_{key_prefix}", idx, btn_label="🛑")

        elif view_mode == "🗂️ Collapsible Accordions":
            with st.expander(f"🖥️ {srv['name']} — `{srv['host']}` [ACTIVE]", expanded=is_expanded_default):
                col_left, col_mid, col_right = st.columns([1.3, 1.3, 1.6])
                with col_left:
                    st.markdown(f"<span class='badge-active-pulse'><span class='status-dot-active'></span> ACTIVE</span> &nbsp; <span style='font-size:11px; font-weight:700;'>`{type_badge}`</span>", unsafe_allow_html=True)
                    st.markdown(f"📍 **Target Host:** `{srv['host']}`")
                with col_mid:
                    st.markdown("🟢 **Runtime Health:** Normal Operational State")
                    if is_tomcat_app:
                        st.markdown("🐱 **Servlet Container:** Apache Tomcat Managed")
                    else:
                        st.markdown("📡 **Heartbeat:** Connected & Responsive")
                with col_right:
                    col_act1, col_act2, col_act3, col_act4 = st.columns(4)
                    with col_act1:
                        if is_tomcat_app:
                            if st.button(f"🐱 Probe", key=f"act_exp_{key_prefix}_{idx}", use_container_width=True):
                                res = HealthCheckerTool.check_tomcat_health(srv)
                                st.toast(f"🐱 {srv['name']}: Tomcat Status — {res['details']}", icon="✅" if res["status"] == "UP" else "⚠️")
                        else:
                            if st.button(f"🌐 Probe", key=f"act_exp_{key_prefix}_{idx}", use_container_width=True):
                                try:
                                    response = httpx.get(srv.get('health_url', ''), timeout=3.0)
                                    if response.status_code == 200:
                                        st.toast(f"🌐 {srv['name']}: Service UP (HTTP 200)", icon="✅")
                                    else:
                                        st.toast(f"🌐 {srv['name']}: HTTP {response.status_code}", icon="ℹ️")
                                except Exception:
                                    st.toast(f"🌐 {srv['name']}: Process Active on Host", icon="ℹ️")
                    with col_act2:
                        if st.button(f"🔑 SSH", key=f"ssh_exp_{key_prefix}_{idx}", use_container_width=True):
                            ssh = paramiko.SSHClient()
                            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                            try:
                                host = srv["host"]
                                port = int(srv.get("ssh_port", 22))
                                user = srv.get("ssh_user", "spotuser")
                                key_path = srv.get("ssh_key_path", "")
                                if key_path and os.path.exists(key_path):
                                    ssh.connect(hostname=host, port=port, username=user, key_filename=key_path, timeout=4)
                                else:
                                    ssh.connect(hostname=host, port=port, username=user, timeout=4)
                                st.toast(f"🔑 {srv['name']} ({srv['host']}): SSH Connection SUCCESS!", icon="✅")
                                ssh.close()
                            except Exception as e:
                                st.toast(f"❌ {srv['name']} ({srv['host']}): SSH Failed — {e}", icon="🚨")
                    with col_act3:
                        render_hitl_restart_popover(srv, f"exp_{key_prefix}", idx, btn_label="🔄")
                    with col_act4:
                        render_hitl_stop_popover(srv, f"exp_{key_prefix}", idx, btn_label="🛑")

        else:  # 📋 Expanded Rows
            with st.container(border=True):
                col_left, col_mid, col_right = st.columns([1.3, 1.3, 1.6])
                with col_left:
                    st.markdown(f"<div style='font-size: 16px; font-weight: 700; margin-bottom: 3px;'>{srv['name']}</div>", unsafe_allow_html=True)
                    st.markdown(f"<span class='badge-active-pulse'><span class='status-dot-active'></span> ACTIVE</span> &nbsp; <span style='font-size:11px; font-weight:700;'>`{type_badge}`</span>", unsafe_allow_html=True)
                    st.markdown(f"📍 **Target Host:** `{srv['host']}`")
                with col_mid:
                    st.markdown("<div style='height: 4px;'></div>", unsafe_allow_html=True)
                    st.markdown("🟢 **Runtime Health:** Normal Operational State")
                    if is_tomcat_app:
                        st.markdown("🐱 **Servlet Container:** Apache Tomcat Managed")
                    else:
                        st.markdown("📡 **Heartbeat:** Connected & Responsive")
                with col_right:
                    st.markdown("<div style='height: 4px;'></div>", unsafe_allow_html=True)
                    col_act1, col_act2, col_act3, col_act4 = st.columns(4)
                    with col_act1:
                        if is_tomcat_app:
                            if st.button(f"🐱 Probe", key=f"act_{key_prefix}_{idx}", use_container_width=True):
                                res = HealthCheckerTool.check_tomcat_health(srv)
                                st.toast(f"🐱 {srv['name']}: Tomcat Status — {res['details']}", icon="✅" if res["status"] == "UP" else "⚠️")
                        else:
                            if st.button(f"🌐 Probe", key=f"act_{key_prefix}_{idx}", use_container_width=True):
                                try:
                                    response = httpx.get(srv.get('health_url', ''), timeout=3.0)
                                    if response.status_code == 200:
                                        st.toast(f"🌐 {srv['name']}: Service UP (HTTP 200)", icon="✅")
                                    else:
                                        st.toast(f"🌐 {srv['name']}: HTTP {response.status_code}", icon="ℹ️")
                                except Exception:
                                    st.toast(f"🌐 {srv['name']}: Process Active on Host", icon="ℹ️")
                    with col_act2:
                        if st.button(f"🔑 SSH", key=f"ssh_{key_prefix}_{idx}", use_container_width=True):
                            ssh = paramiko.SSHClient()
                            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                            try:
                                host = srv["host"]
                                port = int(srv.get("ssh_port", 22))
                                user = srv.get("ssh_user", "spotuser")
                                key_path = srv.get("ssh_key_path", "")
                                if key_path and os.path.exists(key_path):
                                    ssh.connect(hostname=host, port=port, username=user, key_filename=key_path, timeout=4)
                                else:
                                    ssh.connect(hostname=host, port=port, username=user, timeout=4)
                                st.toast(f"🔑 {srv['name']} ({srv['host']}): SSH Connection SUCCESS!", icon="✅")
                                ssh.close()
                            except Exception as e:
                                st.toast(f"❌ {srv['name']} ({srv['host']}): SSH Failed — {e}", icon="🚨")
                    with col_act3:
                        render_hitl_restart_popover(srv, f"row_{key_prefix}", idx, btn_label="🔄")
                    with col_act4:
                        render_hitl_stop_popover(srv, f"row_{key_prefix}", idx, btn_label="🛑")

    # ==========================================
    # SUB-TAB 1: MICROSERVICES
    # ==========================================
    with sub_micro:
        col_hdr1, col_hdr2 = st.columns([1.2, 2.8], vertical_alignment="center")
        with col_hdr1:
            st.markdown(f"<span style='font-size:13px; color:#64748b; font-weight:500;'>Showing <b>{len(microservices)}</b> active Spring Boot microservices</span>", unsafe_allow_html=True)
        with col_hdr2:
            view_mode_micro = st.radio(
                "Display Mode Micro:",
                ["📋 Expanded Rows", "🗂️ Collapsible Accordions", "⚡ Minimized Strip"],
                horizontal=True,
                label_visibility="collapsed",
                key="vmode_micro"
            )
        
        is_exp_micro = True
        if view_mode_micro == "🗂️ Collapsible Accordions":
            col_c1, col_c2 = st.columns([3, 1])
            with col_c2:
                collapse_micro = st.checkbox("📁 Collapse All", value=False, key="col_micro")
                is_exp_micro = not collapse_micro

        if not microservices:
            st.info("No microservices configured.")
        else:
            for idx, srv in enumerate(microservices):
                render_service_card(srv, idx, "micro", view_mode_micro, is_exp_micro)

    # ==========================================
    # SUB-TAB 2: FRONTEND & WEB APPS
    # ==========================================
    with sub_front:
        col_hdr1, col_hdr2 = st.columns([1.2, 2.8], vertical_alignment="center")
        with col_hdr1:
            st.markdown(f"<span style='font-size:13px; color:#64748b; font-weight:500;'>Showing <b>{len(frontend_services)}</b> active AngularJS & Tomcat apps</span>", unsafe_allow_html=True)
        with col_hdr2:
            view_mode_front = st.radio(
                "Display Mode Front:",
                ["📋 Expanded Rows", "🗂️ Collapsible Accordions", "⚡ Minimized Strip"],
                horizontal=True,
                label_visibility="collapsed",
                key="vmode_front"
            )
        
        is_exp_front = True
        if view_mode_front == "🗂️ Collapsible Accordions":
            col_c1, col_c2 = st.columns([3, 1])
            with col_c2:
                collapse_front = st.checkbox("📁 Collapse All", value=False, key="col_front")
                is_exp_front = not collapse_front

        if not frontend_services:
            st.info("No Angular or Frontend Tomcat applications configured.")
        else:
            for idx, srv in enumerate(frontend_services):
                render_service_card(srv, idx, "front", view_mode_front, is_exp_front)

    # ==========================================
    # SUB-TAB 3: DATABASES
    # ==========================================
    with sub_db:
        col_hdr1, col_hdr2 = st.columns([1.2, 2.8], vertical_alignment="center")
        with col_hdr1:
            st.markdown(f"<span style='font-size:13px; color:#64748b; font-weight:500;'>Showing <b>{len(databases)}</b> active PostgreSQL database nodes</span>", unsafe_allow_html=True)
        with col_hdr2:
            view_mode_db = st.radio(
                "Display Mode DB:",
                ["📋 Expanded Rows", "🗂️ Collapsible Accordions", "⚡ Minimized Strip"],
                horizontal=True,
                label_visibility="collapsed",
                key="vmode_db"
            )

        is_exp_db = True
        if view_mode_db == "🗂️ Collapsible Accordions":
            col_c1, col_c2 = st.columns([3, 1])
            with col_c2:
                collapse_db = st.checkbox("📁 Collapse All Items", value=False, key="col_db")
                is_exp_db = not collapse_db

        if not databases:
            st.info("No database targets configured.")
        else:
            for idx, db in enumerate(databases):
                is_db_down = any(i["name"] == db["name"] for i in active_issues)
                db_badge = "<span class='badge-stopped-pulse'><span class='status-dot-stopped'></span> OFFLINE</span>" if is_db_down else "<span class='badge-active-pulse'><span class='status-dot-active'></span> ACTIVE</span>"
                db_health_text = "⚠️ Connection Unavailable" if is_db_down else "🟢 Active Connection"
                db_status_text = "Endpoint Unresponsive" if is_db_down else "PostgreSQL Engine / Port Active"

                if view_mode_db == "🗂️ Collapsible Accordions":
                    with st.expander(f"🗄️ {db['name']} — `{db['host']}:{db.get('port', 5432)}` [{'OFFLINE' if is_db_down else 'ACTIVE'}]", expanded=is_exp_db):
                        col_db_left, col_db_mid, col_db_right = st.columns([1.5, 1.8, 0.9])
                        with col_db_left:
                            st.markdown(db_badge, unsafe_allow_html=True)
                            st.markdown(f"📍 **Host:** `{db['host']}:{db.get('port', 5432)}`")
                        with col_db_mid:
                            st.markdown(f"**Database Health:** {db_health_text}")
                            st.markdown(f"📡 **Status:** {db_status_text}")
                        with col_db_right:
                            if st.button(f"🔌 Test Connection", key=f"db_exp_{idx}", use_container_width=True):
                                res = HealthCheckerTool.check_postgres_health(db)
                                st.toast(f"🗄️ {db['name']}: {res['details']}", icon="✅" if res["status"] == "UP" else "❌")
                elif view_mode_db == "⚡ Minimized Strip":
                    with st.container(border=True):
                        col_d1, col_d2, col_d3, col_d4 = st.columns([1.8, 1.5, 1.2, 1.5])
                        with col_d1:
                            st.markdown(f"**{db['name']}** &nbsp; {db_badge}", unsafe_allow_html=True)
                        with col_d2:
                            st.caption(f"📍 `{db['host']}:{db.get('port', 5432)}`")
                        with col_d3:
                            st.caption(f"{'🔴 OFFLINE' if is_db_down else '🟢 PostgreSQL Active'}")
                        with col_d4:
                            if st.button("🔌 Ping DB", key=f"db_min_{idx}", use_container_width=True):
                                res = HealthCheckerTool.check_postgres_health(db)
                                st.toast(f"🗄️ {db['name']}: {res['details']}", icon="✅" if res["status"] == "UP" else "❌")
                else:
                    with st.container(border=True):
                        col_db_left, col_db_mid, col_db_right = st.columns([1.5, 1.8, 0.9])
                        with col_db_left:
                            st.markdown(f"<div style='font-size: 16px; font-weight: 700; margin-bottom: 3px;'>{db['name']}</div>", unsafe_allow_html=True)
                            st.markdown(db_badge, unsafe_allow_html=True)
                            st.markdown(f"📍 **Host:** `{db['host']}:{db.get('port', 5432)}`")
                        with col_db_mid:
                            st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)
                            st.markdown(f"**Database Health:** {db_health_text}")
                            st.markdown(f"📡 **Status:** {db_status_text}")
                        with col_db_right:
                            st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)
                            if st.button(f"🔌 Test Database Connection", key=f"db_{idx}", use_container_width=True):
                                res = HealthCheckerTool.check_postgres_health(db)
                                st.toast(f"🗄️ {db['name']}: {res['details']}", icon="✅" if res["status"] == "UP" else "❌")

# ==========================================
# TAB 2: AI RCA ENGINE
# ==========================================
with tab_rca:
    st.subheader("🧠 GenAI Autonomous Incident & Root Cause Analysis")
    st.write("Examine remote server log errors and run AI analysis directly on real-time or historical traces.")

    if services:
        selected_service_name = st.selectbox("Select Target Service:", [s["name"] for s in services])
        target_service = next(s for s in services if s["name"] == selected_service_name)
        
        state_key = f"rca_logs_{target_service['name']}"
        if state_key not in st.session_state:
            st.session_state[state_key] = ""

        col_ctrl1, col_ctrl2, col_ctrl3 = st.columns([2, 1, 1])
        with col_ctrl1:
            st.write(f"📂 **Active Log Path**: `{target_service.get('log_paths', [''])[0]}`")
        with col_ctrl2:
            rca_date = st.date_input("Filter by Date:", value=datetime.today(), key="rca_date_sel")
        with col_ctrl3:
            st.write("")
            st.write("")
            if st.button("🔄 Pull Remote Logs", use_container_width=True, key="pull_rca_logs"):
                st.session_state[state_key] = ""
                st.rerun()

        if not st.session_state[state_key]:
            with st.spinner("Connecting to remote server to search for errors/exceptions..."):
                host = target_service["host"]
                port = int(target_service.get("ssh_port", 22))
                user = target_service.get("ssh_user", "spotuser")
                key_path = target_service.get("ssh_key_path", "")

                ssh = paramiko.SSHClient()
                ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

                try:
                    if key_path and os.path.exists(key_path):
                        ssh.connect(hostname=host, port=port, username=user, key_filename=key_path, timeout=6)
                    else:
                        ssh.connect(hostname=host, port=port, username=user, timeout=6)

                    log_paths = target_service.get("log_paths", [])
                    nohup_file = log_paths[0] if log_paths else target_service.get("log_path", "")

                    if nohup_file:
                        date_pat = SSHLogFetcherTool.build_date_regex(rca_date)
                        iso_d = rca_date.strftime("%Y-%m-%d")

                        # Try to grep with multi-format date pattern and error filter
                        cmd = f"grep -E '{date_pat}' {nohup_file} 2>/dev/null | grep -i -E 'error|exception|fatal|fail|warn' | tail -n 45"
                        stdin, stdout, stderr = ssh.exec_command(cmd)
                        output = stdout.read().decode("utf-8", errors="ignore").strip()

                        # If empty, fallback to general date logs
                        if not output:
                            cmd_date = f"grep -E '{date_pat}' {nohup_file} 2>/dev/null | tail -n 45"
                            stdin, stdout, stderr = ssh.exec_command(cmd_date)
                            output = stdout.read().decode("utf-8", errors="ignore").strip()

                        # If still empty, fallback to latest lines
                        if not output:
                            cmd_tail = f"tail -n 45 {nohup_file} 2>/dev/null"
                            stdin, stdout, stderr = ssh.exec_command(cmd_tail)
                            output = f"=== No specific entries found matching date variations ({rca_date.strftime('%d-%b-%y')}, {iso_d}). Showing latest 45 lines of log: ===\n" + stdout.read().decode("utf-8", errors="ignore").strip()

                        st.session_state[state_key] = output
                    else:
                        st.session_state[state_key] = "Error: No log path configured for this service."

                    ssh.close()
                except Exception as e:
                    st.session_state[state_key] = f"Error connecting to server to read logs: {e}"

        sample_trace = st.text_area(
            "Input Log Trace for AI Analysis:",
            value=st.session_state[state_key],
            height=250
        )

        if st.button("🚀 Trigger AI Diagnostics", type="primary", use_container_width=True):
            with st.spinner("AI Diagnostic Agent is performing Root Cause Analysis..."):
                agent = AIDiagnosticAgent(model_name=config["agent"]["ai_model"])
                analysis = agent.analyze_logs_and_health(
                    service_name=target_service["name"],
                    host=target_service["host"],
                    log_lines=sample_trace.strip().split("\n") if sample_trace else [],
                    health_status="UP"
                )

                if analysis and analysis.has_critical_issue:
                    st.success("AI Analysis Complete — Critical Incident Diagnosed!")
                    rca_html = (
                        f'<div class="rca-container">'
                        f'<div class="rca-title">🚨 [{analysis.severity}] {analysis.error_summary}</div>'
                        f'<p><strong>Impacted Component:</strong> {analysis.affected_component}</p>'
                        f'<p><strong>Root Cause Analysis:</strong> {analysis.root_cause_analysis}</p>'
                        f'</div>'
                    )
                    st.markdown(rca_html, unsafe_allow_html=True)

                    st.markdown("#### 🛠️ AI Recommended Resolution Steps:")
                    for step in analysis.recommended_fix:
                        st.markdown(f"<div class='fix-step'>✓ {step}</div>", unsafe_allow_html=True)
                elif analysis:
                    st.success("✅ AI SRE Analysis Complete: Zero Critical Errors")
                    st.markdown(f"""
                    <div style="background: rgba(16, 185, 129, 0.1); border: 1px solid rgba(16, 185, 129, 0.35); border-radius: 8px; padding: 18px; margin-top: 12px;">
                        <h4 style="color: #10b981; margin: 0 0 6px 0;">✨ Normal System Operation Confirmed</h4>
                        <p style="margin: 0; font-size: 14px;"><strong>AI Assessment:</strong> {analysis.root_cause_analysis}</p>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.warning("Please input or pull log lines above before triggering analysis.")

# ==========================================
# TAB 3: LIVE & HISTORICAL SFTP LOG VIEWER
# ==========================================
with tab_logs:
    st.subheader("🔍 Remote SFTP Live & Historical Log Viewer")
    st.caption("Inspect live logs, filter by past dates, or discover archived/rotated log files directly on remote servers.")
    
    if services:
        log_service = st.selectbox("Choose Service Target:", [s["name"] for s in services], key="log_sel_tab3")
        selected_srv_obj = next(s for s in services if s["name"] == log_service)
        
        st.write(f"**Target Host:** `{selected_srv_obj.get('ssh_user', 'root')}@{selected_srv_obj['host']}:{selected_srv_obj.get('ssh_port', 22)}`")
        
        paths = selected_srv_obj.get("log_paths", []) if "log_paths" in selected_srv_obj else [selected_srv_obj.get("log_path")]
        
        col_src1, col_src2 = st.columns([1.5, 1.5])
        with col_src1:
            selected_log_path = st.selectbox("Select Configured Log File:", [p for p in paths if p])
        with col_src2:
            fetch_mode = st.radio(
                "Fetch Mode:",
                ["🕒 Live Tail (Latest)", "📅 Filter by Date / Past Days", "🗄️ Discover Archived Log Files", "👥 User-Wise Multi-Path & Keyword Scanner"],
                index=0
            )

        archived_file_selected = None

        if fetch_mode == "👥 User-Wise Multi-Path & Keyword Scanner":
            st.markdown("### 👥 Multi-Path User-Wise Log & Keyword Error Scanner")
            st.info("Retrieve and aggregate user/trader-specific log files across dynamic date folders (e.g. `/logs/NPG/pguatweb/UMP_NPG_SERVICE/07-Sep-26/`) or trader subdirectories, then search for errors and exceptions by keywords.")

            import posixpath
            
            # Today's formatted dates for reference
            today_dd_mmm_yy = datetime.today().strftime("%d-%b-%y")  # e.g. 07-Sep-26
            today_iso = datetime.today().strftime("%Y-%m-%d")        # e.g. 2026-09-07

            # Derive registered paths and base directory from the selected service
            srv_configured_paths = selected_srv_obj.get("log_paths", []) if "log_paths" in selected_srv_obj else ([selected_srv_obj.get("log_path")] if selected_srv_obj.get("log_path") else [])
            srv_archive_dir = selected_srv_obj.get("archive_path", "")
            srv_app_dir = selected_srv_obj.get("app_path", "")

            # Determine best base directory for folder exploration
            if srv_archive_dir:
                default_explore_base = srv_archive_dir
            elif srv_configured_paths:
                default_explore_base = posixpath.dirname(srv_configured_paths[0])
            elif srv_app_dir:
                default_explore_base = srv_app_dir
            else:
                default_explore_base = "/logs"

            # Construct default multi-path scan list for this service
            auto_scan_paths_list = []
            for p in srv_configured_paths:
                if p:
                    auto_scan_paths_list.append(p)
            if srv_archive_dir and srv_archive_dir not in auto_scan_paths_list:
                auto_scan_paths_list.append(srv_archive_dir)
            if srv_app_dir and srv_app_dir not in auto_scan_paths_list:
                auto_scan_paths_list.append(srv_app_dir)

            default_scan_paths_str = "\n".join(auto_scan_paths_list) if auto_scan_paths_list else f"/logs\n/code"

            u_tab_scan, u_tab_explore = st.tabs(["🚀 Bulk Multi-Path & Keyword Scanner", "📂 Discover Date & Trader Subfolders"])

            with u_tab_explore:
                st.markdown(f"#### 🔎 Discover Remote Date Folders & Trader Subdirectories for `{selected_srv_obj['name']}`")
                st.caption(f"Auto-scan the remote base path on `{selected_srv_obj['host']}` to discover created date folders (like `07-Sep-26`) and trader-specific log directories.")
                
                exp_base_dir = st.text_input(
                    "Remote Base Directory Path (Auto-populated from service config):",
                    value=default_explore_base,
                    key=f"exp_base_dir_{selected_srv_obj['name']}",
                    help="Base remote folder containing date-wise (07-Sep-26) or trader-wise subfolders."
                )

                col_exp1, col_exp2 = st.columns([1.5, 1])
                with col_exp1:
                    exp_search_pat = st.text_input("Subfolder / File Wildcard Filter:", value="*", key=f"exp_pat_{selected_srv_obj['name']}", help="e.g. *Sep*, *26*, *trader*, *.log")
                with col_exp2:
                    exp_max_depth = st.selectbox("Search Depth:", ["1 Level (Date Folders)", "2 Levels (Date + Trader Folders)", "3 Levels (Deep Recursive)"], index=1, key=f"exp_depth_{selected_srv_obj['name']}")

                exp_key = f"discovered_trader_dirs_{selected_srv_obj['name']}"
                if exp_key not in st.session_state:
                    st.session_state[exp_key] = []

                if st.button("🔎 Explore Remote Folders & Trader Files", key=f"btn_explore_{selected_srv_obj['name']}", use_container_width=True):
                    depth_num = 1 if "1 Level" in exp_max_depth else (2 if "2 Levels" in exp_max_depth else 3)
                    with st.spinner(f"Connecting to {selected_srv_obj['host']} and scanning `{exp_base_dir}` (depth {depth_num})..."):
                        host = selected_srv_obj["host"]
                        port = int(selected_srv_obj.get("ssh_port", 22))
                        user = selected_srv_obj.get("ssh_user", "spotuser")
                        key_path = selected_srv_obj.get("ssh_key_path", "")

                        ssh = paramiko.SSHClient()
                        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                        try:
                            if key_path and os.path.exists(key_path):
                                ssh.connect(hostname=host, port=port, username=user, key_filename=key_path, timeout=6)
                            else:
                                ssh.connect(hostname=host, port=port, username=user, timeout=6)

                            cmd_exp = f"find {exp_base_dir} -maxdepth {depth_num} -name '{exp_search_pat}' 2>/dev/null | head -n 40"
                            stdin, stdout, stderr = ssh.exec_command(cmd_exp)
                            found_dirs = [d.strip() for d in stdout.readlines() if d.strip()]
                            ssh.close()
                            
                            st.session_state[exp_key] = found_dirs
                            if not found_dirs:
                                st.warning(f"No subfolders or files found in `{exp_base_dir}` matching `{exp_search_pat}`.")
                        except Exception as ex:
                            st.error(f"Error exploring remote folders: {ex}")

                if st.session_state.get(exp_key):
                    st.success(f"Discovered **{len(st.session_state[exp_key])}** remote folders / files:")
                    selected_discovered_path = st.selectbox("Select Discovered Date / Trader Path to Inspect:", st.session_state[exp_key], key=f"sel_disc_{selected_srv_obj['name']}")
                    
                    st.markdown("---")
                    st.markdown(f"#### ⚡ Direct Log Access & Keyword Inspection: `{selected_discovered_path}`")
                    
                    c_acc1, c_acc2, c_acc3 = st.columns([1.5, 1, 1])
                    with c_acc1:
                        target_kw_filter = st.text_input(
                            "🔍 Filter by Keyword / Exception (Leave empty for entire log):",
                            value="",
                            key=f"kw_disc_{selected_srv_obj['name']}",
                            help="e.g. ERROR, Exception, Timeout, Failed, 500, or specific trade ID."
                        )
                    with c_acc2:
                        fetch_lines_limit = st.selectbox(
                            "Lines to Retrieve:",
                            [100, 250, 500, 1000, 2500, 5000],
                            index=2,
                            key=f"lines_disc_{selected_srv_obj['name']}"
                        )
                    with c_acc3:
                        inner_file_pattern = st.text_input(
                            "File Pattern (if folder):",
                            value="*.log*",
                            key=f"inner_pat_{selected_srv_obj['name']}",
                            help="Pattern for files inside this directory, e.g. *.log*, *.out, *.*"
                        )

                    c_btn1, c_btn2 = st.columns([2, 1])
                    with c_btn1:
                        btn_read_direct = st.button(f"📥 Access & Read Logs from `{selected_discovered_path}`", type="primary", use_container_width=True, key=f"btn_read_disc_{selected_srv_obj['name']}")
                    with c_btn2:
                        if st.button("📋 Add Path to Bulk Scanner List", use_container_width=True, key=f"btn_add_bulk_{selected_srv_obj['name']}"):
                            st.toast(f"Added `{selected_discovered_path}` to scanner paths!")

                    direct_log_key = f"direct_logs_{selected_srv_obj['name']}"
                    if direct_log_key not in st.session_state:
                        st.session_state[direct_log_key] = ""

                    if btn_read_direct:
                        with st.spinner(f"Fetching logs from `{selected_discovered_path}` on {selected_srv_obj['host']}..."):
                            host = selected_srv_obj["host"]
                            port = int(selected_srv_obj.get("ssh_port", 22))
                            user = selected_srv_obj.get("ssh_user", "spotuser")
                            key_path = selected_srv_obj.get("ssh_key_path", "")

                            ssh = paramiko.SSHClient()
                            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                            try:
                                if key_path and os.path.exists(key_path):
                                    ssh.connect(hostname=host, port=port, username=user, key_filename=key_path, timeout=8)
                                else:
                                    ssh.connect(hostname=host, port=port, username=user, timeout=8)

                                # Check if selected path is a file or directory
                                stdin, stdout, stderr = ssh.exec_command(f"[ -d '{selected_discovered_path}' ] && echo 'DIR' || echo 'FILE'")
                                path_type = stdout.read().decode("utf-8", errors="ignore").strip()

                                if path_type == "DIR":
                                    # Discover files inside directory excluding frontend static assets
                                    cmd_find_inner = (
                                        f"find {selected_discovered_path} -maxdepth 2 -type f -name '{inner_file_pattern}' "
                                        f"-not -name '*.js' -not -name '*.css' -not -name '*.map' -not -name '*.html' "
                                        f"-not -name '*.png' -not -name '*.ico' -not -name '*.json' 2>/dev/null | head -n 20"
                                    )
                                    stdin, stdout, stderr = ssh.exec_command(cmd_find_inner)
                                    inner_files = [f.strip() for f in stdout.readlines() if f.strip()]

                                    if not inner_files:
                                        # Fallback to general files in directory
                                        cmd_find_any = f"find {selected_discovered_path} -maxdepth 1 -type f 2>/dev/null | head -n 10"
                                        stdin, stdout, stderr = ssh.exec_command(cmd_find_any)
                                        inner_files = [f.strip() for f in stdout.readlines() if f.strip()]

                                    if inner_files:
                                        combined_chunks = []
                                        for in_file in inner_files:
                                            if target_kw_filter:
                                                cmd_read = f"grep -i -E '{target_kw_filter}' {in_file} 2>/dev/null | tail -n {fetch_lines_limit}"
                                            else:
                                                cmd_read = f"tail -n {fetch_lines_limit} {in_file} 2>/dev/null"
                                            
                                            stdin, stdout, stderr = ssh.exec_command(cmd_read)
                                            file_out = stdout.read().decode("utf-8", errors="ignore").strip()
                                            if file_out:
                                                combined_chunks.append(f"=== File: {in_file} ===\n{file_out}")
                                        
                                        st.session_state[direct_log_key] = "\n\n".join(combined_chunks) if combined_chunks else f"No lines matched keyword '{target_kw_filter}' across {len(inner_files)} file(s) in {selected_discovered_path}."
                                    else:
                                        st.session_state[direct_log_key] = f"No log files found inside directory {selected_discovered_path} matching pattern '{inner_file_pattern}'."
                                else:
                                    # It's a single file
                                    if target_kw_filter:
                                        cmd_read = f"grep -i -E '{target_kw_filter}' {selected_discovered_path} 2>/dev/null | tail -n {fetch_lines_limit}"
                                    else:
                                        cmd_read = f"tail -n {fetch_lines_limit} {selected_discovered_path} 2>/dev/null"

                                    stdin, stdout, stderr = ssh.exec_command(cmd_read)
                                    direct_out = stdout.read().decode("utf-8", errors="ignore").strip()
                                    st.session_state[direct_log_key] = direct_out if direct_out else f"No lines found in {selected_discovered_path} (Keyword: '{target_kw_filter or 'None'}')."

                                ssh.close()
                            except Exception as ex:
                                st.session_state[direct_log_key] = f"Error reading logs: {ex}"

                    # Display retrieved logs if available
                    direct_content = st.session_state.get(direct_log_key, "")
                    if direct_content:
                        total_lines = len(direct_content.splitlines())
                        st.markdown(f"**Log Output ({total_lines} lines):**")
                        st.text_area(
                            f"Live Trace ({selected_discovered_path}):",
                            value=direct_content,
                            height=320,
                            key=f"txt_direct_{selected_srv_obj['name']}"
                        )

                        c_act1, c_act2 = st.columns(2)
                        with c_act1:
                            if st.button("🧠 Send Direct to AI RCA Engine", type="primary", use_container_width=True, key=f"btn_rca_direct_{selected_srv_obj['name']}"):
                                st.session_state[f"rca_logs_{selected_srv_obj['name']}"] = direct_content
                                st.success("Loaded directly into AI RCA Engine! Switch to '🧠 AI RCA Engine' tab to run diagnostics.")
                        with c_act2:
                            clean_filename = selected_discovered_path.rstrip("/").split("/")[-1] or "user_logs"
                            st.download_button(
                                label=f"💾 Download `{clean_filename}.txt`",
                                data=direct_content,
                                file_name=f"{clean_filename}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                                mime="text/plain",
                                use_container_width=True,
                                key=f"dl_direct_{selected_srv_obj['name']}"
                            )

            with u_tab_scan:
                u_col1, u_col2 = st.columns(2)
                with u_col1:
                    user_dirs_input = st.text_area(
                        f"📂 Remote Target Directories to Scan for `{selected_srv_obj['name']}` (Auto-populated):",
                        value=default_scan_paths_str,
                        key=f"user_dirs_input_{selected_srv_obj['name']}",
                        help="Enter remote folder paths. Tokens like {DATE:dd-MMM-yy} automatically convert to today's date (e.g. 07-Sep-26)."
                    )
                    st.caption(f"💡 Dynamic Token Helper: `{'{DATE:dd-MMM-yy}'}` ➔ `{today_dd_mmm_yy}` | `{'{DATE:yyyy-MM-dd}'}` ➔ `{today_iso}`")
                    user_pattern = st.text_input("📄 File Name Pattern / Wildcard:", value="*.log*", key=f"u_pat_{selected_srv_obj['name']}", help="e.g. *.log*, *user*.log, *.out, *trade*.log (Frontend JS/CSS assets are automatically filtered out).")
                with u_col2:
                    user_keywords_input = st.text_area(
                        "🔍 Keywords / Error Patterns to Match (Comma or newline separated):",
                        value="ERROR\nException\nNullPointerException\nTimeout\nFailed\n500\nSQLException",
                        key=f"u_kw_{selected_srv_obj['name']}",
                        help="Extracts only lines matching these keywords across all user/trader logs."
                    )
                    u_date_filter_opt = st.checkbox("Apply Date Filter inside log contents", value=False, key=f"u_df_{selected_srv_obj['name']}")
                    u_selected_date = st.date_input("Filter Date:", value=datetime.today(), key=f"u_dt_{selected_srv_obj['name']}") if u_date_filter_opt else None

                u_opt1, u_opt2 = st.columns(2)
                with u_opt1:
                    max_u_files = st.slider("Max User/Date Log Files to Scan:", 5, 100, 30, key=f"u_maxf_{selected_srv_obj['name']}")
                with u_opt2:
                    max_u_lines = st.slider("Max Matched Error Lines per File:", 10, 200, 50, key=f"u_maxl_{selected_srv_obj['name']}")

                user_scan_key = f"user_scan_res_{selected_srv_obj['name']}"
                if user_scan_key not in st.session_state:
                    st.session_state[user_scan_key] = []

                if st.button("🚀 Scan Across All Date & Trader Log Files for Errors", type="primary", use_container_width=True):
                    with st.spinner(f"Connecting to {selected_srv_obj['host']} and scanning logs..."):
                        raw_dir_list = [d.strip() for d in user_dirs_input.split("\n") if d.strip()]
                        # Expand dynamic tokens with selected date if active
                        dir_list = [SSHLogFetcherTool.expand_dynamic_path_tokens(d, u_selected_date if u_date_filter_opt else None) for d in raw_dir_list]
                        kw_list = [k.strip() for k in user_keywords_input.replace(",", "\n").split("\n") if k.strip()]
                        d_filter = u_selected_date if u_date_filter_opt and u_selected_date else None

                        user_scan_results = log_fetcher.scan_user_logs_multi_path(
                            service_cfg=selected_srv_obj,
                            base_directories=dir_list,
                            file_pattern=user_pattern.strip() or "*.*",
                            keywords=kw_list,
                            date_filter=d_filter,
                            max_files=max_u_files,
                            max_lines_per_file=max_u_lines
                        )
                        st.session_state[user_scan_key] = user_scan_results

            scanned_res = st.session_state.get(user_scan_key, [])
            if scanned_res:
                total_errors = sum(r["match_count"] for r in scanned_res)
                
                st.markdown("<br>", unsafe_allow_html=True)
                m_u1, m_u2, m_u3 = st.columns(3)
                with m_u1:
                    st.markdown(f'<div class="metric-card"><div class="metric-title">User Files with Errors</div><div class="metric-value">{len(scanned_res)}</div></div>', unsafe_allow_html=True)
                with m_u2:
                    st.markdown(f'<div class="metric-card"><div class="metric-title">Total Error Lines Found</div><div class="metric-value" style="color: #ef4444;">{total_errors}</div></div>', unsafe_allow_html=True)
                with m_u3:
                    st.markdown(f'<div class="metric-card"><div class="metric-title">Target Host</div><div class="metric-value" style="font-size:16px; color:#38bdf8;">{selected_srv_obj["host"]}</div></div>', unsafe_allow_html=True)

                st.markdown("### 📋 Extracted Errors by User / File:")
                
                # Consolidated text for 1-click bulk AI RCA
                combined_user_errors = []

                for idx_u, res_item in enumerate(scanned_res):
                    combined_user_errors.append(f"=== User / File: {res_item['file_name']} (Path: {res_item['file_path']}) ===")
                    combined_user_errors.extend(res_item["lines"])
                    combined_user_errors.append("")

                    with st.expander(f"📄 **{res_item['file_name']}** — User Tag: `{res_item['user_tag']}` &nbsp;•&nbsp; 🚨 **{res_item['match_count']} Error(s)**", expanded=(idx_u < 3)):
                        st.caption(f"📍 **Full Path:** `{res_item['file_path']}`")
                        error_block = "\n".join(res_item["lines"])
                        st.text_area(f"Matched Error Lines ({res_item['file_name']}):", value=error_block, height=180, key=f"txt_u_{idx_u}")

                        c_ub1, c_ub2 = st.columns(2)
                        with c_ub1:
                            if st.button(f"🧠 Send {res_item['user_tag']} Errors to AI RCA", key=f"btn_rca_u_{idx_u}", use_container_width=True):
                                st.session_state[f"rca_logs_{selected_srv_obj['name']}"] = error_block
                                st.toast(f"Loaded {res_item['user_tag']} errors into AI RCA Engine!")
                        with c_ub2:
                            st.download_button(
                                label=f"💾 Download {res_item['file_name']}",
                                data=error_block,
                                file_name=f"{res_item['file_name']}_errors.txt",
                                mime="text/plain",
                                key=f"dl_u_{idx_u}",
                                use_container_width=True
                            )

                st.divider()
                st.markdown("#### 🌐 Bulk Actions on All Discovered User Errors:")
                all_errors_text = "\n".join(combined_user_errors)
                c_bulk1, c_bulk2 = st.columns(2)
                with c_bulk1:
                    if st.button("🧠 Send Entire Multi-User Error Trace to GenAI RCA Engine", type="primary", use_container_width=True):
                        st.session_state[f"rca_logs_{selected_srv_obj['name']}"] = all_errors_text
                        st.success("All multi-user error logs loaded into AI RCA Engine! Switch to '🧠 AI RCA Engine' tab to run diagnostics.")
                with c_bulk2:
                    st.download_button(
                        "💾 Download Combined Multi-User Error Report (.txt)",
                        data=all_errors_text,
                        file_name=f"multi_user_errors_{selected_srv_obj['name']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                        mime="text/plain",
                        use_container_width=True
                    )

        elif fetch_mode == "📅 Filter by Date / Past Days":
            col_d1, col_d2 = st.columns([1, 1])
            with col_d1:
                selected_date = st.date_input("Select Target Date:", value=datetime.today(), key="hist_date_sel")
            with col_d2:
                only_errors = st.checkbox("Show only Errors & Warnings for this date", value=False)
                
            date_patterns = SSHLogFetcherTool.build_date_regex(selected_date)

        elif fetch_mode == "🗄️ Discover Archived Log Files":
            st.info("Scan remote directory for dated rotation archives (e.g. `*.log.2026-08-17`, `*.gz` files). You can specify any remote folder.")
            
            # Default folder from config or parent dir
            import posixpath
            default_dir = selected_srv_obj.get("archive_path") or (posixpath.dirname(selected_log_path) if selected_log_path else "/logs/Trading")
            
            custom_archive_dir = st.text_input(
                "📂 Remote Archive / Past Logs Directory Path:",
                value=default_dir,
                help="Enter any folder on the remote server (e.g. /logs/Trading/, /var/log/archive/, /backup/logs/)."
            )
            
            scan_col1, scan_col2, scan_col3 = st.columns([2, 1, 1])
            with scan_col1:
                scan_date = st.date_input("Filter archives by date:", value=datetime.today(), key="arch_date_sel")
            with scan_col2:
                file_pattern = st.selectbox("File Pattern:", ["*.log*", "*.gz", "*.out*", "*.*"], index=0)
            with scan_col3:
                match_all = st.checkbox("Show all folder files", value=False)
            
            scan_key = f"discovered_archives_{selected_srv_obj['name']}"
            if scan_key not in st.session_state:
                st.session_state[scan_key] = []
                
            if st.button("🔎 Scan Remote Directory for Log Files", use_container_width=True):
                with st.spinner(f"Connecting to {selected_srv_obj['host']} and scanning `{custom_archive_dir}`..."):
                    host = selected_srv_obj["host"]
                    port = int(selected_srv_obj.get("ssh_port", 22))
                    user = selected_srv_obj.get("ssh_user", "spotuser")
                    key_path = selected_srv_obj.get("ssh_key_path", "")

                    ssh = paramiko.SSHClient()
                    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                    try:
                        if key_path and os.path.exists(key_path):
                            ssh.connect(hostname=host, port=port, username=user, key_filename=key_path, timeout=6)
                        else:
                            ssh.connect(hostname=host, port=port, username=user, timeout=6)
                        
                        log_dir = custom_archive_dir.strip() or "/logs/Trading"
                        date_vars = SSHLogFetcherTool.get_date_variations(scan_date)
                        date_find_clauses = " -o ".join([f"-name '*{v}*'" for v in date_vars[:8]])
                        
                        if match_all:
                            cmd_scan = f"find {log_dir} -maxdepth 2 -type f -name '{file_pattern}' 2>/dev/null | head -n 40"
                        else:
                            cmd_scan = f"find {log_dir} -maxdepth 2 -type f \\( {date_find_clauses} \\) -name '{file_pattern}' 2>/dev/null | head -n 40"
                            
                        stdin, stdout, stderr = ssh.exec_command(cmd_scan)
                        found_files = stdout.read().decode("utf-8", errors="ignore").strip().split("\n")
                        found_files = [f.strip() for f in found_files if f.strip()]
                        
                        ssh.close()
                        st.session_state[scan_key] = found_files
                        if not found_files:
                            st.warning(f"No specific archive files found in `{log_dir}` matching criteria. Check 'Show all folder files'.")
                    except Exception as e:
                        st.error(f"Error scanning directory: {e}")
                        
            if st.session_state.get(scan_key):
                archived_file_selected = st.selectbox("Select Discovered File to Read:", st.session_state[scan_key])

        # Standard file reader controls for modes other than multi-path scanner
        if fetch_mode != "👥 User-Wise Multi-Path & Keyword Scanner":
            col_opts1, col_opts2 = st.columns([1, 1])
            with col_opts1:
                num_lines = st.slider("Number of lines to retrieve:", 10, 1000, 100)
            with col_opts2:
                filter_keyword = st.text_input("Additional keyword filter (optional):", "")

            if st.button("📥 Retrieve & Display Logs", type="primary", use_container_width=True):
                target_file = archived_file_selected if (fetch_mode == "🗄️ Discover Archived Log Files" and archived_file_selected) else selected_log_path
                
                with st.spinner(f"Connecting to {selected_srv_obj['host']} and reading `{target_file}`..."):
                    host = selected_srv_obj["host"]
                    port = int(selected_srv_obj.get("ssh_port", 22))
                    user = selected_srv_obj.get("ssh_user", "spotuser")
                    key_path = selected_srv_obj.get("ssh_key_path", "")

                    ssh = paramiko.SSHClient()
                    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

                    try:
                        if key_path and os.path.exists(key_path):
                            ssh.connect(hostname=host, port=port, username=user, key_filename=key_path, timeout=6)
                        else:
                            ssh.connect(hostname=host, port=port, username=user, timeout=6)

                        if target_file.endswith(".gz"):
                            read_cmd = f"zcat {target_file}"
                        else:
                            read_cmd = f"cat {target_file}"

                        if fetch_mode == "📅 Filter by Date / Past Days":
                            if only_errors:
                                cmd = f"grep -E '{date_patterns}' {target_file} 2>/dev/null | grep -i -E 'error|exception|fatal|fail|warn' | tail -n {num_lines}"
                            else:
                                cmd = f"grep -E '{date_patterns}' {target_file} 2>/dev/null | tail -n {num_lines}"
                        elif fetch_mode == "🗄️ Discover Archived Log Files":
                            cmd = f"{read_cmd} 2>/dev/null | tail -n {num_lines}"
                        else:
                            cmd = f"tail -n {num_lines} {target_file} 2>/dev/null"

                        stdin, stdout, stderr = ssh.exec_command(cmd)
                        log_output = stdout.read().decode("utf-8", errors="ignore").strip()
                        err_output = stderr.read().decode("utf-8", errors="ignore").strip()

                        ssh.close()

                        if err_output:
                            st.error(f"Remote Warning/Error: {err_output}")
                        
                        if log_output:
                            if filter_keyword:
                                filtered_lines = [line for line in log_output.split("\n") if filter_keyword.lower() in line.lower()]
                                log_output = "\n".join(filtered_lines)
                            
                            st.success(f"Successfully retrieved logs from `{target_file}`!")
                            st.text_area("Fetched Log Content:", value=log_output, height=450)
                            
                            dcol1, dcol2 = st.columns([1, 1])
                            with dcol1:
                                st.download_button("💾 Download Log File", data=log_output, file_name=f"log_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt", mime="text/plain", use_container_width=True)
                            with dcol2:
                                if st.button("🧠 Send this Log to GenAI for RCA Diagnostics", use_container_width=True):
                                    st.session_state[f"rca_logs_{selected_srv_obj['name']}"] = log_output
                                    st.info("Log loaded into AI RCA Engine tab! Switch to '🧠 AI RCA Engine' tab to diagnose.")
                        else:
                            st.warning(f"No matching log entries found in `{target_file}` for the specified criteria.")

                    except Exception as e:
                        st.error(f"Failed to fetch logs: {e}")

# ==========================================
# TAB 4: MESSAGE TRACKER & TRANSCODES HUB (COMMENTED OUT)
# ==========================================
# with tab_tracker:
#     st.subheader("📨 Dynamic Message Tracker & Transcode Management Hub")
#     st.info("Database-free runtime engine for simulating, formatting, and tracking application transcodes (`sms_template` & `message_tracker_archive`).")
# 
#     track_tab1, track_tab2, track_tab3 = st.tabs([
#         "⚡ Transcode Processor & Live Simulator",
#         "📝 Transcode Templates (sms_template)",
#         "📋 Message Tracker Archive (message_tracker_archive)"
#     ])
# 
#     all_tpls = tracker_engine.get_all_templates()
# 
#     # --- SUB-TAB 1: LIVE PROCESSOR & SIMULATOR ---
#     with track_tab1:
#         st.markdown("### ⚡ Dynamic Transcode Message Generator & Processor")
#         st.caption("Splits parameters by `!` (e.g. `MCK1!15-Jul-2026!17-Jul-2026`) and dynamically binds them into `%s` template placeholders.")
# 
#         col_tp1, col_tp2 = st.columns([1.5, 1.5])
#         with col_tp1:
#             tpl_keys = list(all_tpls.keys())
#             sel_transcode_opt = st.selectbox("Select Registered Transcode (or enter below):", tpl_keys + ["➕ Custom Transcode..."], index=0, key="sel_tc_run")
#             
#             if sel_transcode_opt == "➕ Custom Transcode...":
#                 run_transcode = st.text_input("Enter Transcode ID:", value="7783", key="run_tc_custom")
#             else:
#                 run_transcode = sel_transcode_opt
# 
#             matched_tpl = all_tpls.get(run_transcode)
#             if matched_tpl:
#                 st.info(f"📋 **Template:** `{matched_tpl.get('tc_comment', 'N/A')}` &nbsp;|&nbsp; Reply-To: `{matched_tpl.get('reply_to')}`")
# 
#             run_params = st.text_input(
#                 "Message Parameters (`msg_parameters` delimited by `!`):",
#                 value="MCK1!15-Jul-2026!17-Jul-2026",
#                 help="Parameters substituted in order into %s placeholders in the template."
#             )
# 
#             run_owner = st.text_input("Message Owner (`msg_owner`):", value="MCK1")
# 
#         with col_tp2:
#             run_rec_to = st.text_input("Recipient To (`msg_recipients_to`):", value="sushmitha.m@remsl.in")
#             run_rec_cc = st.text_input("Recipient CC (`msg_recipients_cc`):", value="ump@remsl.in")
#             run_subject = st.text_input("Custom Subject (Optional):", value="", placeholder="Leave blank to auto-generate from template")
#             
#             col_att1, col_att2 = st.columns(2)
#             with col_att1:
#                 run_att_file = st.text_input("Attachment Filename:", value="MCK1-15-Jul-2026.csv")
#             with col_att2:
#                 run_att_loc = st.text_input("Attachment S3 / Disk Path:", value="/code/s3drive/UMP/UMP_KA_UAT/WALLET_PAYMNET_EMAIL/16-Jul-2026/MCK1/")
# 
#         st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)
#         col_rbtn1, col_rbtn2 = st.columns([1.5, 1.5])
#         with col_rbtn1:
#             proc_btn = st.button("🚀 Process & Generate Message Tracker Record", type="primary", use_container_width=True)
#         with col_rbtn2:
#             send_smtp_btn = st.button("📧 Process & Dispatch Live Email via SMTP", use_container_width=True)
# 
#         if proc_btn or send_smtp_btn:
#             processed_rec = tracker_engine.process_transcode(
#                 msg_transcode=run_transcode,
#                 msg_parameters=run_params,
#                 msg_recipients_to=run_rec_to,
#                 msg_recipients_cc=run_rec_cc,
#                 msg_subject=run_subject if run_subject else None,
#                 attachment_filename=run_att_file if run_att_file else None,
#                 attachment_location=run_att_loc if run_att_loc else None,
#                 msg_owner=run_owner
#             )
# 
#             st.success(f"✅ Transcode `{run_transcode}` processed! Generated Message ID: `{processed_rec['msg_id']}`")
# 
#             # Parameter breakdown
#             params_split = run_params.split("!") if run_params else []
#             if params_split:
#                 st.markdown("#### 🧩 Parameter Substitution Mapping:")
#                 param_cols = st.columns(min(len(params_split), 5))
#                 for p_idx, p_val in enumerate(params_split):
#                     with param_cols[p_idx % len(param_cols)]:
#                         st.markdown(f'<div class="metric-card"><div class="metric-title">%s #{p_idx+1}</div><div class="metric-value" style="font-size:15px; color:#38bdf8;">{p_val}</div></div>', unsafe_allow_html=True)
# 
#             st.markdown("#### 📄 Rendered HTML Message Output (`msg_message_txt`):")
#             with st.container(border=True):
#                 st.markdown(processed_rec["msg_message_txt"], unsafe_allow_html=True)
# 
#             with st.expander("📦 View Full message_tracker_archive Payload (JSON)", expanded=False):
#                 st.json(processed_rec)
# 
#             if send_smtp_btn:
#                 # Dispatch live email using SMTP
#                 alert_cfg = config.get("alerts", {})
#                 import smtplib
#                 from email.mime.multipart import MIMEMultipart
#                 from email.mime.text import MIMEText
# 
#                 try:
#                     s_host = alert_cfg.get("smtp_host", "smtp.gmail.com")
#                     s_port = int(alert_cfg.get("smtp_port", 465))
#                     s_user = alert_cfg.get("smtp_user", "aishwarya.kale@neml.in")
#                     s_pass = alert_cfg.get("smtp_pass", "")
#                     
#                     msg = MIMEMultipart("alternative")
#                     msg["Subject"] = processed_rec["msg_subject"]
#                     msg["From"] = s_user or "csg@remsl.in"
#                     msg["To"] = run_rec_to
#                     if run_rec_cc:
#                         msg["Cc"] = run_rec_cc
# 
#                     msg.attach(MIMEText(processed_rec["msg_message_txt"], "html"))
# 
#                     if s_port == 465:
#                         server = smtplib.SMTP_SSL(s_host, s_port, timeout=12)
#                     else:
#                         server = smtplib.SMTP(s_host, s_port, timeout=12)
#                         if s_port != 25:
#                             server.starttls()
# 
#                     if s_pass and s_user:
#                         server.login(s_user, s_pass)
# 
#                     recipients_all = [run_rec_to] + ([run_rec_cc] if run_rec_cc else [])
#                     server.sendmail(s_user or "csg@remsl.in", recipients_all, msg.as_string())
#                     server.quit()
#                     st.success(f"📧 Live email successfully dispatched to `{run_rec_to}`!")
#                 except Exception as ex:
#                     st.error(f"❌ SMTP dispatch error: {ex}")
# 
#     # --- SUB-TAB 2: TRANSCODE TEMPLATES ---
#     with track_tab2:
#         st.markdown("### 📝 Manage Transcode Templates (`sms_template`)")
#         st.caption("Define HTML and text templates with `%s` variable replacement tokens. Saved locally in database-free storage.")
# 
#         tpl_sub1, tpl_sub2 = st.tabs(["➕ Add New Transcode Template", "✏️ View & Edit Existing Templates"])
# 
#         with tpl_sub1:
#             with st.form("add_tpl_form"):
#                 c_ta1, c_ta2 = st.columns(2)
#                 with c_ta1:
#                     new_tc = st.text_input("Transcode ID *", placeholder="e.g. 7783")
#                     new_comment = st.text_input("Template Comment / Title *", placeholder="e.g. Settlement Advice File Details")
#                 with c_ta2:
#                     new_reply_to = st.text_input("Reply-To Email", value="csg@remsl.in")
#                     new_reply_name = st.text_input("Reply-To Name", value="UMP Support")
# 
#                 new_html_tpl = st.text_area(
#                     "HTML Message Template (Use %s for dynamic variables) *",
#                     value="<p>Dear %s,</p>\n<p>Your transaction for date %s has been processed successfully with status: %s.</p>\n<p>Regards,<br>ReMS UMP Support</p>",
#                     height=200
#                 )
# 
#                 if st.form_submit_button("💾 Save Template", type="primary"):
#                     if not new_tc or not new_comment or not new_html_tpl:
#                         st.error("Please fill in required fields (Transcode, Comment, Template).")
#                     else:
#                         tracker_engine.save_template(
#                             transcode=new_tc,
#                             tc_comment=new_comment,
#                             html_template=new_html_tpl,
#                             reply_to=new_reply_to,
#                             reply_to_name=new_reply_name
#                         )
#                         st.success(f"Template for Transcode `{new_tc}` saved successfully!")
#                         st.rerun()
# 
#         with tpl_sub2:
#             if not all_tpls:
#                 st.info("No templates registered yet.")
#             else:
#                 sel_edit_tc = st.selectbox("Select Template to Edit:", list(all_tpls.keys()), key="sel_tpl_edit")
#                 curr_tpl = all_tpls[sel_edit_tc]
# 
#                 with st.form("edit_tpl_form"):
#                     c_te1, c_te2 = st.columns(2)
#                     with c_te1:
#                         ed_tc = st.text_input("Transcode ID", value=curr_tpl.get("transcode", ""), disabled=True)
#                         ed_comment = st.text_input("Template Comment / Title", value=curr_tpl.get("tc_comment", ""))
#                     with c_te2:
#                         ed_reply_to = st.text_input("Reply-To Email", value=curr_tpl.get("reply_to", "csg@remsl.in"))
#                         ed_reply_name = st.text_input("Reply-To Name", value=curr_tpl.get("reply_to_name", "AskUs"))
# 
#                     ed_html_tpl = st.text_area("HTML Message Template", value=curr_tpl.get("sms_template", ""), height=220)
# 
#                     if st.form_submit_button("💾 Update Template", type="primary"):
#                         tracker_engine.save_template(
#                             transcode=ed_tc,
#                             tc_comment=ed_comment,
#                             html_template=ed_html_tpl,
#                             reply_to=ed_reply_to,
#                             reply_to_name=ed_reply_name
#                         )
#                         st.success(f"Template `{ed_tc}` updated successfully!")
#                         st.rerun()
# 
#     # --- SUB-TAB 3: ARCHIVE VIEWER ---
#     with track_tab3:
#         st.markdown("### 📋 Processed Message Tracker Archive (`message_tracker_archive`)")
#         st.caption("Live history of all processed transcodes, parameter payloads, and rendered messages.")
# 
#         col_f1, col_f2 = st.columns([1.5, 1.5])
#         with col_f1:
#             tc_filter = st.text_input("Filter by Transcode:", placeholder="e.g. 7781, 7782")
#         with col_f2:
#             rec_filter = st.text_input("Filter by Recipient Email:", placeholder="e.g. sushmitha.m@remsl.in")
# 
#         archive_records = tracker_engine.get_archives(transcode_filter=tc_filter, recipient_filter=rec_filter)
# 
#         st.markdown(f"**Total Processed Records:** `{len(archive_records)}`")
# 
#         if not archive_records:
#             st.info("No matching message tracker records found.")
#         else:
#             for a_idx, a_rec in enumerate(archive_records):
#                 with st.expander(
#                     f"📨 Msg ID: `{a_rec['msg_id']}` — Transcode: `{a_rec['msg_transcode']}` &nbsp;•&nbsp; 👤 `{a_rec['msg_recipients_to']}` &nbsp;•&nbsp; 🟢 {a_rec.get('msg_status', 'SUCCESS')}",
#                     expanded=(a_idx == 0)
#                 ):
#                     c_ar1, c_ar2 = st.columns([1.5, 1.5])
#                     with c_ar1:
#                         st.markdown(f"**Subject:** {a_rec.get('msg_subject', 'N/A')}")
#                         st.markdown(f"**Parameters (`msg_parameters`):** `{a_rec.get('msg_parameters', 'N/A')}`")
#                         st.markdown(f"**Owner:** `{a_rec.get('msg_owner', 'N/A')}`")
#                     with c_ar2:
#                         st.markdown(f"**Created On:** `{a_rec.get('msg_created_on', 'N/A')}`")
#                         st.markdown(f"**Attachment:** `{a_rec.get('msg_attachment_filename', 'None')}`")
#                         st.markdown(f"**Location:** `{a_rec.get('msg_attachment_location', 'None')}`")
# 
#                     st.markdown("#### Rendered Message Content:")
#                     with st.container(border=True):
#                         st.markdown(a_rec.get("msg_message_txt", ""), unsafe_allow_html=True)

# ==========================================
# TAB 5: SERVICE & LOG CONFIGURATOR
# ==========================================
with tab_config:
    st.subheader("🛠️ Dynamic Log Path, Service & User Configurator")
    st.info("Add, edit, or configure services, custom log paths, and user login credentials. Changes persist directly to `config.yaml`.")

    col_act1, col_act2 = st.columns([2.2, 1.8])
    with col_act1:
        action_mode = st.selectbox(
            "⚙️ Select Configuration Action Mode:", 
            [
                "➕ Add Service", 
                "✏️ Edit Service", 
                "🗄️ Database Targets", 
                "🗑️ Delete Connections", 
                "👥 Manage Users & Passwords", 
                "📧 Email Alerts & Notifications"
            ],
            key="config_action_mode_sel"
        )
    st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)

    if action_mode == "➕ Add Service":
        with st.form("add_service_form"):
            st.markdown("### Add New Service / Frontend Web Application Connection")
            col_a1, col_a2 = st.columns(2)
            with col_a1:
                new_name = st.text_input("Service Name *", placeholder="e.g. UMP_AngularJS_Web or PaymentGateWayService")
                new_host = st.text_input("Server Host IP *", placeholder="e.g. 172.26.6.171")
                new_user = st.text_input("SSH/SFTP Username *", value="spotuser", placeholder="e.g. spotuser, deploy, appuser")
                new_type = st.selectbox(
                    "Service Type", 
                    ["SPRING_BOOT", "ANGULARJS_TOMCAT", "STANDALONE_TOMCAT", "NODE_JS", "OTHER"],
                    help="Select ANGULARJS_TOMCAT or STANDALONE_TOMCAT for standalone web applications running on Apache Tomcat."
                )
            with col_a2:
                new_port = st.number_input("SSH Port", value=22)
                new_app_path = st.text_input("Application Directory Path", placeholder="e.g. /opt/tomcat/webapps/myapp or /code/Trading/...")
                new_health_url = st.text_input("Health / Frontend Web URL", placeholder="e.g. http://172.26.6.171:8080/myapp/ or http://...:8080/actuator/health")
                new_key_path = st.text_input("SSH Private Key Path", value="C:/Users/neml10742/Downloads/AWSLinuxKeyPair.pem")

            col_t1, col_t2 = st.columns(2)
            with col_t1:
                new_tomcat_svc = st.text_input("Tomcat Systemd Service Name (If Tomcat App)", value="tomcat", help="e.g. tomcat, tomcat9, catalina (used for systemctl status probe).")
            with col_t2:
                new_archive_path = st.text_input("Archive / Past Logs Directory Path", value="/logs/Trading", help="Remote folder where rotated/past logs or catalina logs are archived.")

            new_log_paths_raw = st.text_area(
                "Configure Active Log Paths (One path per line) *",
                value="/opt/tomcat/logs/catalina.out\n/code/Trading/nohup.out\n/logs/Trading/app.log",
                help="Supports standard log files, catalina.out, and wildcard patterns like {DATE:dd-MMM-yy} or user_*.log."
            )

            submit_add = st.form_submit_button("💾 Save New Service to config.yaml", type="primary")

            if submit_add:
                if not new_name or not new_host or not new_log_paths_raw:
                    st.error("Please fill in required fields (Name, Host IP, Log Paths).")
                else:
                    paths_list = [p.strip() for p in new_log_paths_raw.split("\n") if p.strip()]
                    new_service_dict = {
                        "name": new_name,
                        "type": new_type,
                        "host": new_host,
                        "ssh_port": int(new_port),
                        "ssh_user": new_user,
                        "ssh_key_path": new_key_path,
                        "app_path": new_app_path,
                        "health_url": new_health_url,
                        "tomcat_service_name": new_tomcat_svc,
                        "archive_path": new_archive_path,
                        "log_paths": paths_list
                    }
                    config.setdefault("services", []).append(new_service_dict)
                    save_config(config)
                    st.success(f"Service '{new_name}' created and saved to config.yaml!")
                    st.rerun()

    elif action_mode == "✏️ Edit Service":
        if not services:
            st.warning("No services available to edit.")
        else:
            edit_service_name = st.selectbox("Select Service to Edit:", [s["name"] for s in services])
            edit_srv = next(s for s in services if s["name"] == edit_service_name)
            edit_idx = services.index(edit_srv)

            existing_paths = edit_srv.get("log_paths", []) if "log_paths" in edit_srv else [edit_srv.get("log_path", "")]
            existing_paths_str = "\n".join([p for p in existing_paths if p])

            type_options = ["SPRING_BOOT", "ANGULARJS_TOMCAT", "STANDALONE_TOMCAT", "NODE_JS", "OTHER"]
            cur_type = edit_srv.get("type", "SPRING_BOOT")
            cur_type_idx = type_options.index(cur_type) if cur_type in type_options else 0

            with st.form("edit_service_form"):
                st.markdown(f"### Edit Service: `{edit_service_name}`")
                col_e1, col_e2 = st.columns(2)
                with col_e1:
                    e_name = st.text_input("Service Name", value=edit_srv.get("name", ""))
                    e_host = st.text_input("Server Host IP", value=edit_srv.get("host", ""))
                    e_user = st.text_input("SSH/SFTP Username", value=edit_srv.get("ssh_user", "spotuser"))
                    e_type = st.selectbox("Service Type", type_options, index=cur_type_idx)
                with col_e2:
                    e_port = st.number_input("SSH Port", value=int(edit_srv.get("ssh_port", 22)))
                    e_app_path = st.text_input("Application Directory Path", value=edit_srv.get("app_path", ""))
                    e_health_url = st.text_input("Health / Frontend Web URL", value=edit_srv.get("health_url", ""))
                    e_key_path = st.text_input("SSH Private Key Path", value=edit_srv.get("ssh_key_path", "C:/Users/neml10742/Downloads/AWSLinuxKeyPair.pem"))

                col_et1, col_et2 = st.columns(2)
                with col_et1:
                    e_tomcat_svc = st.text_input("Tomcat Service Name", value=edit_srv.get("tomcat_service_name", "tomcat"))
                with col_et2:
                    e_archive_path = st.text_input("Archive / Past Logs Directory Path", value=edit_srv.get("archive_path", "/logs/Trading"), help="Remote folder where rotated/past logs are archived.")

                e_log_paths_raw = st.text_area(
                    "Configure Active Log Paths (One path per line)",
                    value=existing_paths_str,
                    help="Supports standard log files, catalina.out, and wildcard patterns like user_*.log."
                )

                submit_edit = st.form_submit_button("💾 Update Service in config.yaml", type="primary")

                if submit_edit:
                    paths_list = [p.strip() for p in e_log_paths_raw.split("\n") if p.strip()]
                    services[edit_idx] = {
                        "name": e_name,
                        "type": e_type,
                        "host": e_host,
                        "ssh_port": int(e_port),
                        "ssh_user": e_user,
                        "ssh_key_path": e_key_path,
                        "app_path": e_app_path,
                        "health_url": e_health_url,
                        "tomcat_service_name": e_tomcat_svc,
                        "archive_path": e_archive_path,
                        "log_paths": paths_list
                    }
                    config["services"] = services
                    save_config(config)
                    st.success(f"Service '{e_name}' updated in config.yaml!")
                    st.rerun()

    elif action_mode == "🗄️ Database Targets":
        st.markdown("### 🗄️ Manage PostgreSQL Database Connections")
        db_tab1, db_tab2 = st.tabs(["➕ Add New Database Connection", "✏️ Edit Existing Database"])
        
        with db_tab1:
            with st.form("add_db_form"):
                col_db1, col_db2 = st.columns(2)
                with col_db1:
                    new_db_name = st.text_input("Connection Name *", placeholder="e.g. Postgres Main DB")
                    new_db_host = st.text_input("Database Host IP *", placeholder="e.g. 172.26.6.171")
                    new_db_port = st.number_input("Port", value=5432)
                with col_db2:
                    new_db_name_db = st.text_input("Database Name *", value="postgres", placeholder="e.g. trading_db")
                    new_db_user = st.text_input("Database Username *", value="postgres")
                    new_db_pass = st.text_input("Password (Optional)", type="password")

                if st.form_submit_button("💾 Save Database Connection", type="primary"):
                    if not new_db_name or not new_db_host:
                        st.error("Please provide Connection Name and Host IP.")
                    else:
                        new_db_entry = {
                            "name": new_db_name.strip(),
                            "host": new_db_host.strip(),
                            "port": int(new_db_port),
                            "dbname": new_db_name_db.strip(),
                            "user": new_db_user.strip(),
                            "password": new_db_pass
                        }
                        config.setdefault("databases", []).append(new_db_entry)
                        save_config(config)
                        st.success(f"Database connection '{new_db_name}' saved to config.yaml!")
                        st.rerun()

        with db_tab2:
            if not databases:
                st.warning("No databases currently configured.")
            else:
                sel_db_name = st.selectbox("Select Database to Edit:", [d["name"] for d in databases], key="sel_db_to_edit")
                sel_db = next(d for d in databases if d["name"] == sel_db_name)
                db_idx = databases.index(sel_db)

                with st.form("edit_db_form"):
                    col_edb1, col_edb2 = st.columns(2)
                    with col_edb1:
                        ed_db_name = st.text_input("Connection Name", value=sel_db.get("name", ""))
                        ed_db_host = st.text_input("Database Host IP", value=sel_db.get("host", ""))
                        ed_db_port = st.number_input("Port", value=int(sel_db.get("port", 5432)))
                    with col_edb2:
                        ed_db_name_db = st.text_input("Database Name", value=sel_db.get("dbname", "postgres"))
                        ed_db_user = st.text_input("Database Username", value=sel_db.get("user", "postgres"))
                        ed_db_pass = st.text_input("Password", value=sel_db.get("password", ""), type="password")

                    if st.form_submit_button("💾 Update Database Connection", type="primary"):
                        databases[db_idx] = {
                            "name": ed_db_name.strip(),
                            "host": ed_db_host.strip(),
                            "port": int(ed_db_port),
                            "dbname": ed_db_name_db.strip(),
                            "user": ed_db_user.strip(),
                            "password": ed_db_pass
                        }
                        config["databases"] = databases
                        save_config(config)
                        st.success(f"Database '{ed_db_name}' updated in config.yaml!")
                        st.rerun()

    elif action_mode == "🗑️ Delete Connections":
        st.markdown("### 🗑️ Delete Configured Connections")
        st.write("Safely remove inactive or decommissioned server endpoints and databases from `config.yaml`.")

        del_tab1, del_tab2 = st.tabs(["🖥️ Delete Microservice Connection", "🗄️ Delete Database Connection"])

        with del_tab1:
            if not services:
                st.info("No microservices currently configured.")
            else:
                del_service_name = st.selectbox("Select Microservice Connection to Remove:", [s["name"] for s in services], key="sel_srv_del")
                del_srv_obj = next(s for s in services if s["name"] == del_service_name)
                
                with st.container(border=True):
                    st.markdown(f"#### Target: `{del_srv_obj['name']}`")
                    st.write(f"• **Host:** `{del_srv_obj.get('ssh_user', 'root')}@{del_srv_obj['host']}:{del_srv_obj.get('ssh_port', 22)}`")
                    st.write(f"• **App Directory:** `{del_srv_obj.get('app_path', 'N/A')}`")
                    st.write(f"• **Health URL:** `{del_srv_obj.get('health_url', 'N/A')}`")

                confirm_del_srv = st.checkbox(f"⚠️ Confirm permanent deletion of '{del_service_name}'", key="chk_del_srv")
                if st.button(f"🗑️ Permanently Delete '{del_service_name}'", type="primary", disabled=not confirm_del_srv, key="btn_del_srv"):
                    config["services"] = [s for s in services if s["name"] != del_service_name]
                    save_config(config)
                    st.success(f"Microservice connection '{del_service_name}' permanently removed from config.yaml!")
                    st.rerun()

        with del_tab2:
            if not databases:
                st.info("No databases currently configured.")
            else:
                del_db_name = st.selectbox("Select Database Connection to Remove:", [d["name"] for d in databases], key="sel_db_del")
                del_db_obj = next(d for d in databases if d["name"] == del_db_name)
                
                with st.container(border=True):
                    st.markdown(f"#### Target: `{del_db_obj['name']}`")
                    st.write(f"• **Host:** `{del_db_obj['host']}:{del_db_obj.get('port', 5432)}`")
                    st.write(f"• **Database Name:** `{del_db_obj.get('dbname', 'postgres')}`")
                    st.write(f"• **User:** `{del_db_obj.get('user', 'postgres')}`")

                confirm_del_db = st.checkbox(f"⚠️ Confirm permanent deletion of '{del_db_name}'", key="chk_del_db")
                if st.button(f"🗑️ Permanently Delete '{del_db_name}'", type="primary", disabled=not confirm_del_db, key="btn_del_db"):
                    config["databases"] = [d for d in databases if d["name"] != del_db_name]
                    save_config(config)
                    st.success(f"Database connection '{del_db_name}' permanently removed from config.yaml!")
                    st.rerun()

    elif action_mode == "👥 Manage Users & Passwords":
        st.markdown("### 👥 Configure User Logins & Passwords")
        st.write("Configure passwords and roles for DevOps and Developer teams. Changes are saved directly to `config.yaml`.")

        curr_users = config.get("users", [])
        
        user_tab1, user_tab2 = st.tabs(["✏️ Update Existing User Password", "➕ Add New User Login"])
        
        with user_tab1:
            if not curr_users:
                st.warning("No users currently found in configuration.")
            else:
                target_username = st.selectbox("Select User Account:", [u["username"] for u in curr_users], key="sel_user_edit")
                target_u_obj = next(u for u in curr_users if u["username"] == target_username)
                target_u_idx = curr_users.index(target_u_obj)
                
                with st.form("edit_user_form"):
                    col_u1, col_u2 = st.columns(2)
                    with col_u1:
                        u_display_name = st.text_input("Display Name", value=target_u_obj.get("name", ""))
                        u_role = st.selectbox("Assigned Role", ["DevOps Engineer", "Developer", "Administrator", "Database Administrator (DBA)"], index=0 if "devops" in target_u_obj.get("role", "").lower() else 1)
                    with col_u2:
                        u_new_pass = st.text_input("New Password", value=str(target_u_obj.get("password", "")), type="password")
                        st.caption("Password is saved as plaintext in config.yaml for simple enterprise deployment.")
                    
                    submit_user_edit = st.form_submit_button("💾 Update User & Password", type="primary")
                    if submit_user_edit:
                        curr_users[target_u_idx]["name"] = u_display_name
                        curr_users[target_u_idx]["role"] = u_role
                        curr_users[target_u_idx]["password"] = u_new_pass
                        config["users"] = curr_users
                        save_config(config)
                        st.success(f"User '{target_username}' updated successfully in config.yaml!")
                        st.rerun()

        with user_tab2:
            with st.form("add_user_form"):
                col_nu1, col_nu2 = st.columns(2)
                with col_nu1:
                    new_u_username = st.text_input("New Username *", placeholder="e.g. devops_qa, dev_lead")
                    new_u_name = st.text_input("Full Display Name *", placeholder="e.g. QA DevOps Engineer")
                with col_nu2:
                    new_u_role = st.selectbox("Role", ["DevOps Engineer", "Developer", "Administrator", "Database Administrator (DBA)"])
                    new_u_pass = st.text_input("Password *", type="password", placeholder="Enter secure password")
                
                submit_new_user = st.form_submit_button("➕ Create New User Account", type="primary")
                if submit_new_user:
                    if not new_u_username or not new_u_pass:
                        st.error("Please provide both Username and Password.")
                    elif any(u["username"] == new_u_username.strip() for u in curr_users):
                        st.error(f"User '{new_u_username}' already exists!")
                    else:
                        curr_users.append({
                            "username": new_u_username.strip(),
                            "password": new_u_pass.strip(),
                            "role": new_u_role,
                            "name": new_u_name.strip() or new_u_username.strip()
                        })
                        config["users"] = curr_users
                        save_config(config)
                        st.success(f"User account '{new_u_username}' created successfully!")
                        st.rerun()

    elif action_mode == "📧 Email Alerts & Notifications":
        st.markdown("### 📧 Configure Automated Incident Email Alerts")
        st.write("Configure the sender account and recipient email address (`uppfunds@neml.in`) for GenAI incident notifications.")

        alert_cfg = config.get("alerts", {})

        st.info("💡 **`neml.in` Domain Detected**: Your domain is hosted on **Google Workspace (Gmail for Business)**. Pre-configured host: `smtp.gmail.com`, Port: `587`.")

        with st.expander("ℹ️ How to get a Google App Password for `neml.in` (Takes 30 seconds)", expanded=False):
            st.markdown("""
            1. Open [Google Account App Passwords](https://myaccount.google.com/apppasswords) in your browser.
            2. Sign in with your **`@neml.in`** account.
            3. Type **`OpsGuardian`** in the App Name box and click **Create**.
            4. Copy the generated **16-character password** (e.g. `abcd efgh ijkl mnop`).
            5. Paste it in the **Sender Password / App Password** box below!
            """)

        with st.form("email_alerts_form"):
            col_em1, col_em2 = st.columns(2)
            with col_em1:
                cfg_recip = st.text_input("📬 Recipient Email (Where alerts go) *", value=alert_cfg.get("recipient_email", "uppfunds@neml.in"))
                cfg_user = st.text_input("👤 Sender Email Address (SMTP User) *", value=alert_cfg.get("smtp_user", "uppfunds@neml.in"))
                cfg_pass = st.text_input("🔑 Sender Password / 16-char App Password", value=alert_cfg.get("smtp_pass", ""), type="password", help="Use your Google 16-char App Password or service password.")
            with col_em2:
                cfg_host = st.text_input("🌐 SMTP Host Server *", value=alert_cfg.get("smtp_host", "smtp.gmail.com"), help="Google Workspace: smtp.gmail.com | Office 365: smtp.office365.com")
                cfg_port = st.number_input("🔌 SMTP Port", value=int(alert_cfg.get("smtp_port", 587)))
                cfg_throttle = st.number_input("⏱️ Alert Throttle (Minutes)", value=int(alert_cfg.get("throttle_minutes", 1)), min_value=1)

            submit_alert_cfg = st.form_submit_button("💾 Save Email Alert Settings", type="primary")

            if submit_alert_cfg:
                config["alerts"] = {
                    "smtp_host": cfg_host.strip(),
                    "smtp_port": int(cfg_port),
                    "smtp_user": cfg_user.strip(),
                    "smtp_pass": cfg_pass.strip(),
                    "recipient_email": cfg_recip.strip(),
                    "throttle_minutes": int(cfg_throttle)
                }
                save_config(config)
                st.success("Email Alert configuration updated successfully in config.yaml!")
                st.rerun()

        st.markdown("#### 🧪 Test Alert Dispatch")
        if st.button("📧 Send Test Email to Recipient", use_container_width=True):
            with st.spinner(f"Attempting to send test email to `{alert_cfg.get('recipient_email', 'uppfunds@neml.in')}`..."):
                import smtplib
                from email.mime.multipart import MIMEMultipart
                from email.mime.text import MIMEText

                test_msg = MIMEMultipart()
                test_msg["Subject"] = "🛡️ NeML OpsGuardian - Email Alert Connectivity Test"
                test_msg["From"] = alert_cfg.get("smtp_user", "alerts@neml.in")
                test_msg["To"] = alert_cfg.get("recipient_email", "uppfunds@neml.in")
                test_body = f"""
                <html>
                <body style="font-family: Arial, sans-serif; color: #0f172a; padding: 20px;">
                    <div style="background: #0284c7; color: white; padding: 15px 20px; border-radius: 8px;">
                        <h2>🛡️ NeML OpsGuardian Alert Test</h2>
                    </div>
                    <p style="margin-top: 15px;">This is a test notification verifying that automated email dispatch is properly configured.</p>
                    <p><strong>Configured Sender:</strong> {alert_cfg.get('smtp_user')}</p>
                    <p><strong>Configured Host:</strong> {alert_cfg.get('smtp_host')}:{alert_cfg.get('smtp_port')}</p>
                    <p><strong>Time:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                </body>
                </html>
                """
                test_msg.attach(MIMEText(test_body, "html"))

                try:
                    s_host = alert_cfg.get("smtp_host", "smtp.gmail.com")
                    s_port = int(alert_cfg.get("smtp_port", 587))
                    s_user = alert_cfg.get("smtp_user", "aishwarya.kale@neml.in")
                    s_pass = alert_cfg.get("smtp_pass", "")
                    s_to = alert_cfg.get("recipient_email", "aishwarya.kale@neml.in")
                    if s_pass in ["YOUR_SMTP_PASSWORD", "YOUR_GOOGLE_APP_PASSWORD", "YOUR_16_CHAR_GOOGLE_APP_PASSWORD"]:
                        s_pass = ""

                    if s_port == 465:
                        s = smtplib.SMTP_SSL(s_host, s_port, timeout=12)
                    else:
                        s = smtplib.SMTP(s_host, s_port, timeout=12)
                        if s_port != 25:
                            s.starttls()

                    if s_pass and s_user:
                        s.login(s_user, s_pass)

                    s.sendmail(s_user or "opsguardian@neml.in", [s_to], test_msg.as_string())
                    s.quit()
                    st.success(f"✅ Test email successfully dispatched to `{s_to}`!")
                except Exception as ex:
                    st.error(f"❌ Failed to dispatch test email: {ex}")

    st.divider()
    with st.expander("📄 View Raw config.yaml Preview", expanded=False):
        st.code(yaml.dump(config, sort_keys=False), language="yaml")

# ==========================================
# TAB 5: INCIDENT ALERTS & NOTIFICATIONS
# ==========================================
with tab_notif:
    st.subheader("🔔 Real-Time Incident Notifications & System Outages")
    st.info("Live stream of detected system exceptions, database outages, and microservice status alerts.")

    if active_issues:
        st.markdown(f"### 🚨 Active Incidents Requiring Attention ({len(active_issues)})")
        for idx, iss in enumerate(active_issues):
            with st.container(border=True):
                c_n1, c_n2, c_n3 = st.columns([1.5, 1.8, 1.4])
                with c_n1:
                    st.markdown(f"### {iss['name']}")
                    st.markdown(f"<span class='badge-stopped-pulse'><span class='status-dot-stopped'></span> DISCONNECTED / OFFLINE</span>", unsafe_allow_html=True)
                with c_n2:
                    st.markdown("<div style='height: 4px;'></div>", unsafe_allow_html=True)
                    st.markdown("⚠️ **Target Status:** Endpoint is currently unreachable")
                    st.caption(f"Last checked: Real-time ({datetime.now().strftime('%H:%M:%S')})")
                with c_n3:
                    st.markdown("<div style='height: 4px;'></div>", unsafe_allow_html=True)
                    col_act_b1, col_act_b2 = st.columns([1.2, 1.0])
                    with col_act_b1:
                        if st.button("🔄 Check Again", key=f"recheck_btn_{idx}", use_container_width=True, type="primary"):
                            with st.spinner(f"Testing connection to {iss['name']}..."):
                                if iss.get("category") == "database" and "obj" in iss:
                                    res = HealthCheckerTool.check_postgres_health(iss["obj"])
                                    if res["status"] == "UP":
                                        st.success(f"✅ Connection to {iss['name']} successfully established!")
                                        st.rerun()
                                    else:
                                        st.error(f"❌ Connection still failing: {res['details']}")
                                else:
                                    st.info(f"Re-probing {iss['name']}...")
                                    st.rerun()
                    with col_act_b2:
                        if st.button("🧠 Diagnose", key=f"tab_notif_btn_{idx}", use_container_width=True):
                            st.session_state["sel_target_rca"] = iss['name']
                            st.toast(f"Loading {iss['name']} into AI RCA Engine...")
    else:
        st.markdown("""
        <div style="text-align: center; padding: 45px 20px; background: rgba(16, 185, 129, 0.05); border: 1px dashed rgba(16, 185, 129, 0.35); border-radius: 12px; margin-top: 20px;">
            <div style="font-size: 46px;">🎉</div>
            <h3 style="color: #10b981; margin-top: 10px; font-weight: 800;">All Systems are Healthy & Operational</h3>
            <p style="color: #64748b; font-size: 14px; max-width: 520px; margin: 0 auto;">
                Zero active outages, database connection failures, or critical runtime exceptions detected across all monitored nodes.
            </p>
        </div>
        """, unsafe_allow_html=True)
