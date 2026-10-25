import streamlit as st
import requests
import pandas as pd
from datetime import date, datetime

# ---------------------------------------------------------
# 1. PAGE CONFIGURATION
# ---------------------------------------------------------
st.set_page_config(
    page_title="Saylani HCM Lite - Enterprise HR Portal",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded",
)

API_BASE = "http://localhost:8000/api"
REQUEST_TIMEOUT = 15

ROLE_THEMES = {
    "Admin": {"primary": "#4f46e5", "badge_bg": "#e0e7ff", "badge_text": "#3730a3"},
    "HR": {"primary": "#059669", "badge_bg": "#d1fae5", "badge_text": "#065f46"},
    "Employee": {"primary": "#0284c7", "badge_bg": "#e0f2fe", "badge_text": "#075985"},
    "Guest": {"primary": "#2563eb", "badge_bg": "#e0e7ff", "badge_text": "#3730a3"},
}

# ---------------------------------------------------------
# 2. SESSION STATE
# ---------------------------------------------------------
if "user" not in st.session_state:
    st.session_state.user = None
if "messages" not in st.session_state:
    st.session_state.messages = []

# ---------------------------------------------------------
# 3. HELPERS
# ---------------------------------------------------------
def api_request(method, endpoint, **kwargs):
    """Call the FastAPI backend and return the response."""
    url = f"{API_BASE}{endpoint}"
    kwargs.setdefault("timeout", REQUEST_TIMEOUT)
    return requests.request(method, url, **kwargs)


def show_api_error(error, context="Request"):
    st.error(
        f"{context} complete nahi ho saka. Backend check karein "
        f"({API_BASE}) aur phir dobara try karein.\n\nDetails: {error}"
    )


def get_theme(role):
    return ROLE_THEMES.get(role, ROLE_THEMES["Guest"])


def render_metric(title, value, color_code="#2563eb"):
    return f"""
    <div class="metric-card">
        <div class="metric-title">
            <span class="metric-indicator" style="background-color:{color_code};"></span>
            {title}
        </div>
        <div class="metric-value">{value}</div>
    </div>
    """


def login_form(tab_title, expected_role, key_suffix):
    """Login form for a specific portal. Backend must enforce role permissions."""
    with st.form(f"login_form_{key_suffix}", border=True):
        email = st.text_input("Corporate Email", placeholder="name@company.com", key=f"email_{key_suffix}")
        password = st.text_input("Password", type="password", placeholder="Enter your password", key=f"password_{key_suffix}")
        submitted = st.form_submit_button(
            f"Sign in to {tab_title}",
            type="primary",
            use_container_width=True,
        )

    if not submitted:
        return

    if not email.strip() or not password:
        st.warning("Email aur password dono enter karein.")
        return

    try:
        response = api_request(
            "POST",
            "/auth/login",
            json={"email": email.strip(), "password": password},
        )

        if response.status_code != 200:
            try:
                detail = response.json().get("detail", "Email ya password durust nahi.")
            except ValueError:
                detail = "Email ya password durust nahi."
            st.error(f"Login failed: {detail}")
            return

        try:
            account = response.json()
        except ValueError:
            st.error("Backend ne valid JSON response nahi diya.")
            return

        actual_role = str(account.get("role", "")).strip().lower()
        if actual_role != expected_role.lower():
            st.error(
                f"Yeh account {tab_title} ke liye nahi hai. "
                "Apne account ke mutabiq sahi login tab select karein."
            )
            return

        st.session_state.user = account
        st.session_state.messages = []
        st.rerun()

    except requests.RequestException as error:
        show_api_error(error, "Login")


def get_json(endpoint, fallback=None):
    """Fetch JSON safely. Returns fallback only when explicitly supplied."""
    response = api_request("GET", endpoint)
    response.raise_for_status()
    return response.json()


# ---------------------------------------------------------
# 4. ROLE-BASED THEME / CSS
# ---------------------------------------------------------
current_role = (
    str(st.session_state.user.get("role", "Guest"))
    if st.session_state.user
    else "Guest"
)
active_theme = get_theme(current_role)

st.markdown(
    f"""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');

        html, body, [class*="css"] {{
            font-family: 'Plus Jakarta Sans', sans-serif;
        }}
        .stApp {{ background-color: #f8fafc; }}
        header[data-testid="stHeader"] {{ visibility: hidden; }}
        footer {{ visibility: hidden; }}

        section[data-testid="stSidebar"] {{
            background-color: #0f172a;
            border-right: 1px solid #1e293b;
        }}
        section[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p,
        section[data-testid="stSidebar"] label {{
            color: #e2e8f0;
        }}
        section[data-testid="stSidebar"] .stRadio label {{
            font-weight: 600;
            font-size: 0.9rem;
            padding: 6px 8px;
            border-radius: 8px;
        }}

        .role-badge {{
            background-color: {active_theme['badge_bg']};
            color: {active_theme['badge_text']};
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.75rem;
            font-weight: 800;
            letter-spacing: 0.04em;
            text-transform: uppercase;
            display: inline-block;
        }}
        .metric-card {{
            background: #fff;
            border: 1px solid #e2e8f0;
            border-radius: 14px;
            padding: 22px;
            box-shadow: 0 4px 20px -2px rgba(0,0,0,.04);
            transition: all .2s ease;
        }}
        .metric-card:hover {{
            transform: translateY(-3px);
            border-color: {active_theme['primary']};
        }}
        .metric-title {{
            font-size: .8rem;
            color: #64748b;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: .05em;
        }}
        .metric-value {{
            font-size: 2.1rem;
            font-weight: 800;
            color: #0f172a;
            margin-top: 6px;
        }}
        .metric-indicator {{
            display: inline-block;
            width: 9px;
            height: 9px;
            border-radius: 50%;
            margin-right: 8px;
        }}
        .stButton > button {{
            border-radius: 10px;
            font-weight: 700;
            padding: .5rem 1rem;
        }}
        .stButton > button[kind="primary"] {{
            background-color: {active_theme['primary']};
            color: white;
            border: 0;
        }}
        .custom-container {{
            background: #fff;
            padding: 24px;
            border-radius: 16px;
            border: 1px solid #e2e8f0;
            margin-bottom: 20px;
        }}
        .ai-badge {{
            background: #6366f1;
            color: #fff;
            padding: 2px 8px;
            border-radius: 12px;
            font-size: .7rem;
            font-weight: 700;
        }}
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------
# 5. SIDEBAR BRANDING
# ---------------------------------------------------------
st.sidebar.markdown(
    """
    <div style="text-align:center;padding:15px 0 5px;">
        <h2 style="color:white;margin:0;font-weight:800;">SAYLANI</h2>
        <p style="color:#94a3b8;margin:4px 0 0;">HCM Lite Enterprise</p>
    </div>
    <hr style="border-color:#1e293b;margin:15px 0 20px;">
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------
# 6. AUTHENTICATION SCREEN
# ---------------------------------------------------------
if st.session_state.user is None:
    _, center, _ = st.columns([1, 2.2, 1])
    with center:
        st.markdown(
            "<h1 style='text-align:center;color:#0f172a;font-weight:800;'>🏢 Saylani HCM Portal</h1>",
            unsafe_allow_html=True,
        )
        st.markdown(
            "<p style='text-align:center;color:#64748b;'>Human Capital & Workforce Management</p>",
            unsafe_allow_html=True,
        )
        st.info("Apne account ki type ke mutabiq login tab select karein.")

        admin_tab, hr_tab, employee_tab, setup_tab = st.tabs(
            ["🔐 Admin Login", "🧑‍💼 HR Login", "👤 Employee Login", "⚙️ First-Time Setup"]
        )

        with admin_tab:
            st.subheader("Administrator Portal")
            login_form("Admin Portal", "Admin", "admin")

        with hr_tab:
            st.subheader("Human Resources Portal")
            login_form("HR Portal", "HR", "hr")

        with employee_tab:
            st.subheader("Employee Self-Service Portal")
            login_form("Employee Portal", "Employee", "employee")

        with setup_tab:
            st.subheader("First-Run Enterprise Setup")
            st.warning(
                "Setup sirf tab run karein jab database pehle initialize na hua ho. "
                "Is endpoint ko backend par secure rakhein."
            )
            with st.form("setup_form", border=True):
                company_name = st.text_input("Company Name", value="Saylani Welfare Trust")
                admin_email = st.text_input("Super Admin Email", value="admin@saylani.com")
                admin_password = st.text_input("Admin Password", type="password")
                setup_submit = st.form_submit_button(
                    "Initialize System", type="primary", use_container_width=True
                )

            if setup_submit:
                if not company_name.strip() or not admin_email.strip() or len(admin_password) < 12:
                    st.warning("Company/email enter karein aur password kam az kam 12 characters ka rakhein.")
                else:
                    try:
                        response = api_request(
                            "POST",
                            "/setup/first-run",
                            json={
                                "company_name": company_name.strip(),
                                "admin_email": admin_email.strip(),
                                "admin_password": admin_password,
                            },
                        )
                        if response.status_code in (200, 201):
                            st.success("Setup complete. Ab Admin Login tab se sign in karein.")
                        else:
                            try:
                                detail = response.json().get("detail", "Setup failed.")
                            except ValueError:
                                detail = "Setup failed."
                            st.error(detail)
                    except requests.RequestException as error:
                        show_api_error(error, "Setup")

# ---------------------------------------------------------
# 7. LOGGED-IN APPLICATION
# ---------------------------------------------------------
else:
    user = st.session_state.user
    role = str(user.get("role", "Employee")).strip()
    email = user.get("email", "Signed-in user")

    with st.sidebar:
        st.markdown(
            f"""
            <div style="background:#1e293b;padding:14px;border-radius:12px;margin-bottom:16px;border:1px solid #334155;">
                <div style="font-size:.72rem;color:#94a3b8;font-weight:800;">ACTIVE SESSION</div>
                <div style="font-weight:700;color:white;margin-top:5px;overflow-wrap:anywhere;">{email}</div>
                <div style="margin-top:8px;"><span class="role-badge">{role} Portal</span></div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        if st.button("🚪 Logout", use_container_width=True):
            st.session_state.user = None
            st.session_state.messages = []
            st.rerun()

        if role.lower() == "admin":
            menu_items = [
                "Dashboard & Analytics", "Company Setup", "Employee Directory",
                "Payroll Finalization", "AI Assistant", "Audit Logs",
            ]
        elif role.lower() == "hr":
            menu_items = [
                "HR Operations Hub", "Employee Registration", "Attendance Board",
                "Leave Approvals", "Payroll Draft", "AI Assistant",
            ]
        else:
            menu_items = [
                "My Employee Portal", "Camera Check-In", "Apply Leave",
                "My Payslips", "AI Assistant",
            ]

        menu = st.radio("MAIN NAVIGATION", menu_items)

    st.markdown(
        f"""
        <div style="background:white;padding:20px 24px;border-radius:14px;border:1px solid #e2e8f0;margin-bottom:24px;">
            <h2 style="margin:0;font-weight:800;color:#0f172a;">{menu}</h2>
            <p style="margin:5px 0 0;color:#64748b;font-size:.875rem;">
                Signed in as <b>{email}</b> · {datetime.now().strftime('%A, %d %B %Y')}
            </p>
            <div style="margin-top:10px;"><span class="role-badge">{role} View</span></div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # 7A. DASHBOARD
    if menu in ("Dashboard & Analytics", "HR Operations Hub", "My Employee Portal"):
        try:
            response = api_request("GET", "/dashboard/metrics")
            response.raise_for_status()
            metrics = response.json()
        except (requests.RequestException, ValueError) as error:
            metrics = None
            st.warning("Dashboard metrics backend se load nahi ho sakin.")
            st.caption(str(error))

        if metrics is not None:
            col1, col2, col3, col4 = st.columns(4)
            col1.markdown(render_metric("Total Headcount", metrics.get("headcount", "—"), "#4f46e5"), unsafe_allow_html=True)
            col2.markdown(render_metric("Present Today", metrics.get("present", "—"), "#059669"), unsafe_allow_html=True)
            col3.markdown(render_metric("Late Arrivals", metrics.get("late", "—"), "#d97706"), unsafe_allow_html=True)
            col4.markdown(render_metric("On Leave", metrics.get("on_leave", "—"), "#dc2626"), unsafe_allow_html=True)

        st.subheader("🏢 Workforce & Attendance Breakdown")
        st.info("Department-wise live chart/table ke liye backend se department metrics endpoint connect karna hoga.")

    # 7B. CAMERA CHECK-IN
    elif menu == "Camera Check-In":
        st.subheader("📷 Camera Check-In")
        st.warning(
            "Camera se photo capture karna facial recognition verify nahi karta. "
            "Is screen par real face matching ya geofence verification abhi implement nahi hai."
        )
        image = st.camera_input("Capture check-in photo")
        st.info("Photo capture abhi sirf UI preview hai; real verification service ke baghair attendance submit nahi ki ja rahi.")
        if image is not None:
            st.image(image, caption="Captured photo preview", use_container_width=True)

    # 7C. APPLY LEAVE
    elif menu == "Apply Leave":
        with st.form("leave_form", border=True):
            st.subheader("New Leave Application")
            leave_type = st.selectbox(
                "Leave Category",
                ["Casual Leave", "Sick Leave", "Annual Paid Leave", "Unpaid Leave"],
            )
            col1, col2 = st.columns(2)
            start_date = col1.date_input("Start Date", value=date.today())
            end_date = col2.date_input("End Date", value=date.today())
            reason = st.text_area("Reason for Leave")
            submitted = st.form_submit_button("Submit Application", type="primary")

        if submitted:
            employee_id = user.get("employee_id")
            if not employee_id:
                st.error("Login response mein employee_id nahi mila. Backend auth response ko check karein.")
            elif end_date < start_date:
                st.error("End Date, Start Date se pehle nahi ho sakti.")
            elif not reason.strip():
                st.warning("Leave ki reason enter karein.")
            else:
                try:
                    response = api_request(
                        "POST",
                        "/leave/apply",
                        json={
                            "employee_id": employee_id,
                            "leave_type": leave_type,
                            "start_date": str(start_date),
                            "end_date": str(end_date),
                            "reason": reason.strip(),
                        },
                    )
                    if response.status_code in (200, 201):
                        st.success("Leave application submit ho gayi.")
                    else:
                        try:
                            st.error(response.json().get("detail", "Leave application failed."))
                        except ValueError:
                            st.error(f"Leave application failed: HTTP {response.status_code}")
                except requests.RequestException as error:
                    show_api_error(error, "Leave application")

    # 7D. EMPLOYEE REGISTRATION
    elif menu == "Employee Registration":
        with st.form("employee_registration_form", border=True):
            st.subheader("New Employee Registration")
            col1, col2 = st.columns(2)
            employee_code = col1.text_input("Employee Code")
            full_name = col1.text_input("Full Name")
            employee_email = col1.text_input("Corporate Email")
            department = col2.text_input("Department")
            designation = col2.text_input("Designation")
            salary = col2.number_input("Basic Monthly Salary (PKR)", min_value=0.0, value=50000.0, step=5000.0)
            joining_date = st.date_input("Date of Joining", value=date.today())
            submitted = st.form_submit_button("Create Employee Profile", type="primary")

        if submitted:
            if not all([employee_code.strip(), full_name.strip(), employee_email.strip(), department.strip(), designation.strip()]):
                st.warning("Tamam required fields fill karein.")
            else:
                try:
                    response = api_request(
                        "POST",
                        "/employees",
                        json={
                            "employee_code": employee_code.strip(),
                            "full_name": full_name.strip(),
                            "email": employee_email.strip(),
                            "department": department.strip(),
                            "designation": designation.strip(),
                            "joining_date": str(joining_date),
                            "basic_salary": salary,
                            "allowances": salary * 0.2,
                        },
                    )
                    if response.status_code in (200, 201):
                        st.success("Employee profile create ho gaya.")
                    else:
                        try:
                            st.error(response.json().get("detail", "Employee registration failed."))
                        except ValueError:
                            st.error(f"Registration failed: HTTP {response.status_code}")
                except requests.RequestException as error:
                    show_api_error(error, "Employee registration")

    # 7E. LEAVE APPROVALS
    elif menu == "Leave Approvals":
        try:
            response = api_request("GET", "/leave/list")
            response.raise_for_status()
            leaves = response.json()
            if isinstance(leaves, dict):
                leaves = leaves.get("items", leaves.get("leaves", []))
            if not isinstance(leaves, list):
                leaves = []
        except (requests.RequestException, ValueError) as error:
            leaves = []
            st.error("Leave list load nahi ho saki. Backend endpoint check karein.")
            st.caption(str(error))

        if not leaves:
            st.info("Koi leave request display karne ke liye available nahi hai.")
        for leave in leaves:
            leave_id = leave.get("id")
            employee_name = leave.get("employee_name", "Employee")
            leave_type = leave.get("leave_type", "Leave")
            days = leave.get("days", leave.get("days_count", "—"))
            with st.expander(f"📋 {employee_name} — {leave_type} ({days} days)"):
                st.write(f"**Duration:** {leave.get('start_date', '—')} to {leave.get('end_date', '—')}")
                st.write(f"**Reason:** {leave.get('reason', '—')}")
                st.write(f"**Status:** {leave.get('status', 'Pending')}")
                col1, col2 = st.columns(2)
                for column, action, label in [
                    (col1, "Approved", "Approve"),
                    (col2, "Rejected", "Reject"),
                ]:
                    if column.button(label, key=f"{action}_{leave_id}", use_container_width=True):
                        try:
                            result = api_request(
                                "POST",
                                f"/leave/action?leave_id={leave_id}&action={action}",
                            )
                            if result.status_code in (200, 201):
                                st.success(f"Leave {action.lower()} ho gayi.")
                                st.rerun()
                            else:
                                st.error(f"Action failed: HTTP {result.status_code} — {result.text}")
                        except requests.RequestException as error:
                            show_api_error(error, "Leave action")

    # 7F. AI ASSISTANT
    elif menu == "AI Assistant":
        st.caption("AI Assistant endpoint aapke FastAPI backend se response leta hai.")
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.write(message["content"])

        query = st.chat_input("Apna HR sawal likhein...")
        if query:
            st.session_state.messages.append({"role": "user", "content": query})
            with st.chat_message("user"):
                st.write(query)

            try:
                response = api_request(
                    "POST",
                    "/ai/chat",
                    json={
                        "role": role,
                        "employee_id": user.get("employee_id"),
                        "message": query,
                    },
                )
                response.raise_for_status()
                result = response.json()
                answer = result.get("response", "Backend se response mila, lekin response field nahi mili.")
            except (requests.RequestException, ValueError) as error:
                result = {}
                answer = f"AI service abhi available nahi hai. Details: {error}"

            with st.chat_message("assistant"):
                st.write(answer)
                if result.get("smart_leave"):
                    st.info("AI ne leave intent identify kiya:")
                    st.json(result["smart_leave"])
                    st.caption("Smart leave ko submit karne ke liye backend confirmation endpoint implement karna hoga.")

            st.session_state.messages.append({"role": "assistant", "content": answer})

    # 7G. PLACEHOLDER PAGES
    elif menu in (
        "Company Setup", "Employee Directory", "Payroll Finalization",
        "Audit Logs", "Attendance Board", "Payroll Draft", "My Payslips",
    ):
        st.subheader(menu)
        st.info(
            "Menu navigation ready hai, lekin is page ka live data/form abhi connect nahi hua. "
            "Isay complete karne ke liye relevant FastAPI endpoint aur response schema chahiye."
        )

    else:
        st.info("Is menu ke liye page abhi implement nahi hua.")
