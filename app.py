# =========================================================
# ROOFLEAD AI SAAS - COMPLETE PROFESSIONAL VERSION
# FULLY WORKING - ALL ISSUES FIXED
# =========================================================

import streamlit as st
import pandas as pd
import datetime
import time
import re
import hashlib
import hmac
import secrets
import uuid
import json
import plotly.express as px
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
from enum import Enum

# =========================================================
# PAGE CONFIGURATION
# =========================================================
st.set_page_config(
    page_title="RoofLead AI SaaS - Professional Lead Management",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =========================================================
# SECURITY & CONFIGURATION
# =========================================================
try:
    WHATSAPP_BUSINESS_NUMBER = st.secrets["WHATSAPP_NUMBER"]
    ADMIN_PASSWORD = st.secrets["ADMIN_PASSWORD"]
except:
    WHATSAPP_BUSINESS_NUMBER = "923217676965"
    ADMIN_PASSWORD = "Admin123!"

COMPANY_NAME = "RoofLead AI"
COMPANY_LOGO = "🏠"
COMPANY_EMAIL = "support@rooflead.com"
COMPANY_PHONE = "+92 321 7676965"

WHATSAPP_TEMPLATES = {
    "welcome": {
        "name": "👋 Welcome Message",
        "message": "Hi {name}, thank you for choosing {company}! We're excited to help with your roofing needs. How can we assist you today?"
    },
    "free_inspection": {
        "name": "🔍 Free Inspection Offer",
        "message": "Hi {name}, we're offering FREE roof inspections this week! No obligation, just peace of mind. Would you like to schedule yours?"
    },
    "estimate_followup": {
        "name": "💰 Estimate Follow-up",
        "message": "Hi {name}, following up on your roof estimate. We have special financing options available. Are you free for a quick 5-min call today?"
    },
    "booking_confirmation": {
        "name": "📅 Booking Confirmation",
        "message": "Hi {name}, your roof inspection is confirmed for {date} at {time}. Our inspector will call 30 mins before arrival."
    },
    "booking_reminder": {
        "name": "⏰ Booking Reminder",
        "message": "Hi {name}, this is a reminder about your roof inspection tomorrow at {time}. Please reply CONFIRM to confirm."
    },
    "satisfaction": {
        "name": "⭐ Customer Satisfaction",
        "message": "Hi {name}, how was your experience with {company}? We'd love your feedback! Reply with a rating 1-5."
    },
    "hot_lead": {
        "name": "🔥 Hot Lead Alert",
        "message": "🔥 HOT LEAD ALERT! {name} from {state} needs a {project} roof. Score: {score}/100. Contact: {phone}"
    },
    "referral": {
        "name": "🤝 Referral Request",
        "message": "Hi {name}, we hope you're happy with your new roof! Know anyone who needs roofing services? We offer $100 referral bonus!"
    }
}

# =========================================================
# ENUMS
# =========================================================
class UserRole(Enum):
    ADMIN = "admin"
    SALES = "sales"
    VIEWER = "viewer"

class LeadStatus(Enum):
    HOT = "🔥 HOT"
    WARM = "🌤️ WARM"
    COLD = "❄️ COLD"
    CONVERTED = "✅ CONVERTED"
    LOST = "❌ LOST"

class BookingStatus(Enum):
    PENDING = "⏳ Pending"
    CONFIRMED = "✅ Confirmed"
    COMPLETED = "🎉 Completed"
    CANCELLED = "❌ Cancelled"
    RESCHEDULED = "🔄 Rescheduled"

# =========================================================
# DATA CLASSES
# =========================================================
@dataclass
class User:
    username: str
    email: str
    password_hash: str
    role: UserRole
    full_name: str
    phone: str
    created_at: str
    last_login: Optional[str] = None
    is_active: bool = True
    avatar: str = "👤"

@dataclass
class AuditLog:
    id: str
    user: str
    action: str
    entity_type: str
    entity_id: str
    details: str
    ip_address: str
    timestamp: str

# =========================================================
# UTILITY FUNCTIONS
# =========================================================
def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(password: str, hashed: str) -> bool:
    return hmac.compare_digest(hash_password(password), hashed)

def validate_phone(phone: str) -> tuple:
    if not phone:
        return False, "Phone number is required"
    cleaned = re.sub(r'[\s\-\(\)\+\.]', '', phone)
    if not cleaned.isdigit():
        return False, "Phone number contains invalid characters"
    if len(cleaned) < 10 or len(cleaned) > 12:
        return False, "Phone number must be 10-12 digits"
    fake_patterns = ['1234567890', '1111111111', '0000000000', '9999999999', '0123456789']
    if cleaned in fake_patterns:
        return False, "Invalid phone number"
    return True, cleaned

def validate_email(email: str) -> tuple:
    if not email:
        return True, "", False
    email = email.lower().strip()
    pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
    if not re.match(pattern, email):
        return False, email, False
    disposable_domains = ['tempmail.com', '10minutemail.com', 'guerrillamail.com', 'mailinator.com']
    domain = email.split('@')[1]
    is_disposable = domain in disposable_domains
    return True, email, is_disposable

def get_whatsapp_link(phone: str, message: str = "") -> str:
    if not phone or phone == "Not provided":
        return None
    cleaned = re.sub(r'[\s\-\(\)\+\.]', '', str(phone))
    if not cleaned.startswith('92') and len(cleaned) == 10:
        cleaned = '92' + cleaned
    encoded_msg = message.replace(' ', '%20').replace('\n', '%0A').replace('#', '%23')
    if encoded_msg:
        return f"https://wa.me/{cleaned}?text={encoded_msg}"
    return f"https://wa.me/{cleaned}"

def calculate_lead_score(lead_data: Dict) -> int:
    score = 50
    if lead_data.get('phone'):
        score += 20
    if lead_data.get('email'):
        score += 15
    if lead_data.get('roof_size', 0) > 2000:
        score += 10
    if lead_data.get('project_type') == "Commercial":
        score += 10
    if lead_data.get('state') in ["Texas", "Oklahoma", "Kansas", "California", "Florida"]:
        score += 5
    if lead_data.get('lead_source') in ["Referral", "Website"]:
        score += 5
    return min(score, 100)

def get_lead_status(score: int) -> str:
    if score >= 70:
        return LeadStatus.HOT.value
    elif score >= 40:
        return LeadStatus.WARM.value
    else:
        return LeadStatus.COLD.value

def get_dashboard_metrics():
    total_leads = len(st.session_state.leads)
    hot_leads = len([l for l in st.session_state.leads if LeadStatus.HOT.value in l.get("Status", "")])
    warm_leads = len([l for l in st.session_state.leads if LeadStatus.WARM.value in l.get("Status", "")])
    cold_leads = len([l for l in st.session_state.leads if LeadStatus.COLD.value in l.get("Status", "")])
    converted_leads = len([l for l in st.session_state.leads if LeadStatus.CONVERTED.value in l.get("Status", "")])
    total_bookings = len(st.session_state.bookings)
    pending_bookings = len([b for b in st.session_state.bookings if BookingStatus.PENDING.value in b.get("Status", "")])
    confirmed_bookings = len([b for b in st.session_state.bookings if BookingStatus.CONFIRMED.value in b.get("Status", "")])
    completed_bookings = len([b for b in st.session_state.bookings if BookingStatus.COMPLETED.value in b.get("Status", "")])
    avg_lead_score = sum([l.get("Score", 0) for l in st.session_state.leads]) / total_leads if total_leads > 0 else 0
    return {
        "total_leads": total_leads,
        "hot_leads": hot_leads,
        "warm_leads": warm_leads,
        "cold_leads": cold_leads,
        "converted_leads": converted_leads,
        "total_bookings": total_bookings,
        "pending_bookings": pending_bookings,
        "confirmed_bookings": confirmed_bookings,
        "completed_bookings": completed_bookings,
        "avg_lead_score": avg_lead_score
    }

def log_audit(action: str, entity_type: str, entity_id: str, details: str):
    if "audit_logs" not in st.session_state:
        st.session_state.audit_logs = []
    log = AuditLog(
        id=str(uuid.uuid4()),
        user=st.session_state.get('current_user', 'SYSTEM'),
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        details=details,
        ip_address=st.session_state.get('ip_address', '127.0.0.1'),
        timestamp=datetime.datetime.now().isoformat()
    )
    st.session_state.audit_logs.append(log)

# =========================================================
# SESSION STATE INITIALIZATION - FIXED
# =========================================================
def init_session_state():
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    if "current_user" not in st.session_state:
        st.session_state.current_user = None
    if "user_role" not in st.session_state:
        st.session_state.user_role = None
    if "user_role_value" not in st.session_state:
        st.session_state.user_role_value = None
    if "user_full_name" not in st.session_state:
        st.session_state.user_full_name = None
    if "leads" not in st.session_state:
        st.session_state.leads = []
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    if "bookings" not in st.session_state:
        st.session_state.bookings = []
    if "audit_logs" not in st.session_state:
        st.session_state.audit_logs = []
    if "whatsapp_messages" not in st.session_state:
        st.session_state.whatsapp_messages = []
    if "notifications" not in st.session_state:
        st.session_state.notifications = []
    if "page" not in st.session_state:
        st.session_state.page = "dashboard"
    if "users" not in st.session_state:
        st.session_state.users = {
            "admin": User(
                username="admin",
                email="admin@rooflead.com",
                password_hash=hash_password(ADMIN_PASSWORD),
                role=UserRole.ADMIN,
                full_name="System Administrator",
                phone="1234567890",
                created_at=datetime.datetime.now().isoformat(),
                is_active=True
            )
        }
    if "ip_address" not in st.session_state:
        st.session_state.ip_address = f"session_{secrets.token_hex(4)}"
    
    # Sample data
    if len(st.session_state.leads) == 0:
        st.session_state.leads = [
            {
                "id": str(uuid.uuid4()),
                "Name": "John Smith",
                "Phone": "923001234567",
                "Email": "john.smith@example.com",
                "State": "Texas",
                "Project": "Residential",
                "Roof Size": 2500,
                "Lead Source": "Website",
                "Score": 85,
                "Status": LeadStatus.HOT.value,
                "Created By": "admin",
                "Created": datetime.datetime.now().strftime("%Y-%m-%d"),
                "Notes": "Interested in asphalt shingles"
            },
            {
                "id": str(uuid.uuid4()),
                "Name": "Sarah Johnson",
                "Phone": "923001234568",
                "Email": "sarah.j@example.com",
                "State": "California",
                "Project": "Commercial",
                "Roof Size": 5000,
                "Lead Source": "Referral",
                "Score": 75,
                "Status": LeadStatus.HOT.value,
                "Created By": "admin",
                "Created": datetime.datetime.now().strftime("%Y-%m-%d"),
                "Notes": "Metal roof for warehouse"
            }
        ]
    
    if len(st.session_state.bookings) == 0:
        st.session_state.bookings = [
            {
                "id": str(uuid.uuid4()),
                "Name": "John Smith",
                "Phone": "923001234567",
                "Email": "john.smith@example.com",
                "Address": "123 Main St, Dallas, TX",
                "Preferred Date": (datetime.date.today() + datetime.timedelta(days=2)).strftime("%Y-%m-%d"),
                "Preferred Time": "Morning (9am-12pm)",
                "Notes": "Check for storm damage",
                "Status": BookingStatus.CONFIRMED.value,
                "Created By": "admin",
                "Created At": datetime.datetime.now().strftime("%Y-%m-%d")
            }
        ]

init_session_state()

# =========================================================
# AUTHENTICATION FUNCTIONS - FIXED
# =========================================================
def login_user(username: str, password: str) -> tuple:
    if username not in st.session_state.users:
        return False, "Invalid username or password"
    
    user = st.session_state.users[username]
    
    if not user.is_active:
        return False, "Account is deactivated. Contact administrator."
    
    if verify_password(password, user.password_hash):
        st.session_state.authenticated = True
        st.session_state.current_user = username
        # FIX: Store both the enum and the string value
        st.session_state.user_role = user.role
        st.session_state.user_role_value = user.role.value
        st.session_state.user_full_name = user.full_name
        
        user.last_login = datetime.datetime.now().isoformat()
        log_audit("LOGIN_SUCCESS", "user", username, "User logged in successfully")
        return True, "Login successful!"
    else:
        log_audit("LOGIN_FAILED", "user", username, "Failed login attempt")
        return False, "Invalid username or password"

def logout_user():
    if st.session_state.current_user:
        log_audit("LOGOUT", "user", st.session_state.current_user, "User logged out")
    st.session_state.authenticated = False
    st.session_state.current_user = None
    st.session_state.user_role = None
    st.session_state.user_role_value = None
    st.session_state.user_full_name = None
    st.session_state.page = "dashboard"

# =========================================================
# LEAD MANAGEMENT FUNCTIONS
# =========================================================
def add_lead(name: str, phone: str, email: str, state: str, project: str, roof_size: int, source: str, notes: str = ""):
    score = calculate_lead_score({
        'phone': phone, 'email': email, 'roof_size': roof_size,
        'project_type': project, 'state': state, 'lead_source': source
    })
    status = get_lead_status(score)
    
    lead = {
        "id": str(uuid.uuid4()),
        "Name": name,
        "Phone": phone,
        "Email": email or "Not provided",
        "State": state,
        "Project": project,
        "Roof Size": roof_size,
        "Lead Source": source,
        "Score": score,
        "Status": status,
        "Notes": notes,
        "Created By": st.session_state.current_user,
        "Created": datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    }
    st.session_state.leads.append(lead)
    log_audit("CREATE_LEAD", "lead", name, f"Lead created with score {score}")
    st.session_state.notifications.append(f"New lead created: {name} (Score: {score})")
    return lead

def update_lead_status(lead_id: str, new_status: str):
    for lead in st.session_state.leads:
        if lead.get("id") == lead_id:
            old_status = lead.get("Status")
            lead["Status"] = new_status
            log_audit("UPDATE_LEAD", "lead", lead["Name"], f"Status changed from {old_status} to {new_status}")
            return True
    return False

def delete_lead(lead_id: str):
    for i, lead in enumerate(st.session_state.leads):
        if lead.get("id") == lead_id:
            lead_name = lead.get("Name")
            del st.session_state.leads[i]
            log_audit("DELETE_LEAD", "lead", lead_name, "Lead deleted")
            return True
    return False

def add_booking(name: str, phone: str, email: str, address: str, date: str, time: str, notes: str):
    booking = {
        "id": str(uuid.uuid4()),
        "Name": name,
        "Phone": phone,
        "Email": email or "Not provided",
        "Address": address or "Not provided",
        "Preferred Date": date,
        "Preferred Time": time,
        "Notes": notes,
        "Status": BookingStatus.PENDING.value,
        "Created By": st.session_state.current_user,
        "Created At": datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    }
    st.session_state.bookings.append(booking)
    log_audit("CREATE_BOOKING", "booking", name, "Booking created")
    st.session_state.notifications.append(f"New booking request from {name}")
    return booking

def update_booking_status(booking_id: str, new_status: str):
    for booking in st.session_state.bookings:
        if booking.get("id") == booking_id:
            old_status = booking.get("Status")
            booking["Status"] = new_status
            log_audit("UPDATE_BOOKING", "booking", booking["Name"], f"Status changed from {old_status} to {new_status}")
            return True
    return False

def delete_booking(booking_id: str):
    for i, booking in enumerate(st.session_state.bookings):
        if booking.get("id") == booking_id:
            del st.session_state.bookings[i]
            log_audit("DELETE_BOOKING", "booking", booking.get("Name", "Unknown"), "Booking deleted")
            return True
    return False

# =========================================================
# AI CHATBOT RESPONSE
# =========================================================
def ai_chatbot_response(user_message: str) -> str:
    msg = user_message.lower().strip()
    
    if any(word in msg for word in ["price", "cost", "how much", "estimate", "quote"]):
        return "💰 **Average Roofing Costs:**\n• Residential (2,000 sq ft): $8,000-16,000\n• Commercial (5,000 sq ft): $20,000-50,000\n• Leak Repair: $200-1,500\n\nGet a free estimate by booking an inspection!"
    elif any(word in msg for word in ["leak", "leaking", "water damage"]):
        return "💧 **Roof Leak Information:**\n\nRepair Costs: $200-1,500\n\nWe offer FREE inspections to diagnose the exact issue."
    elif any(word in msg for word in ["inspect", "inspection", "check"]):
        return "🔍 **FREE Roof Inspections:**\n\n• 24-48 hour response time\n• Professional certified inspectors\n• No obligation, completely free\n\n**Schedule now in the Bookings page!**"
    elif any(word in msg for word in ["hello", "hi", "hey"]):
        return f"👋 Hello! I'm RoofLead AI, your roofing assistant.\n\nI can help you with:\n• Roofing costs and estimates\n• Leak repairs\n• Free inspections\n• Booking appointments\n\nWhat would you like to know?"
    else:
        return "🤖 **RoofLead AI Assistant**\n\nI can help you with:\n• 💰 Pricing & Estimates\n• 💧 Leak Repairs\n• 🔍 Free Inspections\n• 📅 Booking Appointments\n\nWhat specific information do you need?"

# =========================================================
# PAGE: DASHBOARD
# =========================================================
def page_dashboard():
    st.title("📊 Dashboard")
    st.markdown(f"Welcome back, **{st.session_state.user_full_name}!** Here's your business overview.")
    st.markdown("---")
    
    metrics = get_dashboard_metrics()
    
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.metric("Total Leads", metrics["total_leads"])
    with col2:
        st.metric("🔥 Hot Leads", metrics["hot_leads"])
    with col3:
        st.metric("✅ Converted", metrics["converted_leads"])
    with col4:
        st.metric("📅 Total Bookings", metrics["total_bookings"])
    with col5:
        st.metric("⭐ Avg Lead Score", f"{metrics['avg_lead_score']:.0f}/100")
    
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Leads by Status")
        if st.session_state.leads:
            df_leads = pd.DataFrame(st.session_state.leads)
            status_data = df_leads["Status"].value_counts().reset_index()
            status_data.columns = ["Status", "Count"]
            fig = px.pie(status_data, values="Count", names="Status", title="Lead Status Distribution")
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("Leads by State")
        if st.session_state.leads:
            df_leads = pd.DataFrame(st.session_state.leads)
            state_data = df_leads["State"].value_counts().head(10).reset_index()
            state_data.columns = ["State", "Count"]
            fig = px.bar(state_data, x="State", y="Count", title="Top States by Leads")
            st.plotly_chart(fig, use_container_width=True)
    
    st.subheader("📋 Recent Leads")
    if st.session_state.leads:
        recent_leads = pd.DataFrame(st.session_state.leads[-5:])
        st.dataframe(recent_leads[["Name", "Status", "Score", "Phone", "Created"]], use_container_width=True)
    
    st.markdown("---")
    st.subheader("⚡ Quick Actions")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        if st.button("➕ Create Lead", use_container_width=True):
            st.session_state.page = "create_lead"
            st.rerun()
    with col2:
        if st.button("📅 New Booking", use_container_width=True):
            st.session_state.page = "bookings"
            st.rerun()
    with col3:
        if st.button("📲 WhatsApp Center", use_container_width=True):
            st.session_state.page = "whatsapp"
            st.rerun()
    with col4:
        if st.button("🤖 AI Assistant", use_container_width=True):
            st.session_state.page = "chatbot"
            st.rerun()

# =========================================================
# PAGE: CREATE LEAD
# =========================================================
def page_create_lead():
    st.title("➕ Create New Lead")
    st.markdown("Enter lead information below. All fields marked with * are required.")
    st.markdown("---")
    
    with st.form("create_lead_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            first_name = st.text_input("First Name *")
            last_name = st.text_input("Last Name *")
            phone = st.text_input("Phone Number *", placeholder="03XXXXXXXXX or 923XXXXXXXXX")
            email = st.text_input("Email Address")
        
        with col2:
            project_type = st.selectbox("Project Type *", ["Residential", "Commercial"])
            state = st.selectbox("State *", ["Texas", "California", "Florida", "New York", "Oklahoma", "Kansas", "Other"])
            roof_size = st.number_input("Roof Size (sq ft)", min_value=100, max_value=100000, value=1500, step=100)
            lead_source = st.selectbox("Lead Source", ["Website", "Referral", "Social Media", "Cold Call", "Other"])
        
        notes = st.text_area("Notes", height=100)
        
        submitted = st.form_submit_button("🚀 Create Lead", use_container_width=True, type="primary")
        
        if submitted:
            if not first_name or not last_name or not phone:
                st.error("Please fill all required fields")
                return
            
            is_valid, cleaned_phone = validate_phone(phone)
            if not is_valid:
                st.error(cleaned_phone)
                return
            
            if email:
                is_valid, cleaned_email, _ = validate_email(email)
                if not is_valid:
                    st.error("Invalid email format")
                    return
                email = cleaned_email
            
            full_name = f"{first_name} {last_name}"
            lead = add_lead(full_name, cleaned_phone, email, state, project_type, roof_size, lead_source, notes)
            
            if lead:
                st.success(f"✅ Lead created successfully! Score: {lead['Score']}/100 - {lead['Status']}")
                st.balloons()
                
                # WhatsApp option
                wa_message = f"Hi {first_name}, thank you for your interest in {COMPANY_NAME}. We'll contact you shortly."
                wa_link = get_whatsapp_link(cleaned_phone, wa_message)
                if wa_link:
                    st.markdown(f"[📲 Send WhatsApp message]({wa_link})")
                
                if st.button("➕ Create Another Lead"):
                    st.rerun()

# =========================================================
# PAGE: CRM
# =========================================================
def page_crm():
    st.title("📋 Customer Relationship Management")
    st.markdown("Manage and track all your leads.")
    st.markdown("---")
    
    if not st.session_state.leads:
        st.info("No leads yet. Create your first lead!")
        if st.button("➕ Create Lead"):
            st.session_state.page = "create_lead"
            st.rerun()
        return
    
    # Filters
    col1, col2 = st.columns(2)
    with col1:
        status_filter = st.multiselect("Filter by Status", [s.value for s in LeadStatus], default=[s.value for s in LeadStatus])
    with col2:
        search_term = st.text_input("🔍 Search", placeholder="Name or phone...")
    
    filtered_leads = [l for l in st.session_state.leads if l.get("Status") in status_filter]
    if search_term:
        search_lower = search_term.lower()
        filtered_leads = [l for l in filtered_leads if search_lower in l.get("Name", "").lower() or search_lower in l.get("Phone", "").lower()]
    
    st.markdown(f"### 📋 {len(filtered_leads)} Leads Found")
    
    for idx, lead in enumerate(filtered_leads):
        with st.expander(f"{lead['Status']} | {lead['Name']} - Score: {lead['Score']}/100"):
            col1, col2, col3 = st.columns([2, 1, 1])
            
            with col1:
                st.write(f"**Phone:** {lead['Phone']}")
                st.write(f"**Email:** {lead['Email']}")
                st.write(f"**State:** {lead['State']} | **Project:** {lead['Project']}")
                st.write(f"**Roof Size:** {lead['Roof Size']:,} sq ft")
                if lead.get("Notes"):
                    st.write(f"**Notes:** {lead['Notes']}")
            
            with col2:
                new_status = st.selectbox("Update Status", [s.value for s in LeadStatus], 
                                         index=[s.value for s in LeadStatus].index(lead['Status']),
                                         key=f"status_{lead['id']}_{idx}")
                if new_status != lead['Status']:
                    update_lead_status(lead['id'], new_status)
                    st.rerun()
                
                wa_link = get_whatsapp_link(lead['Phone'])
                if wa_link:
                    st.markdown(f"[📲 WhatsApp Lead]({wa_link})")
            
            with col3:
                # Use user_role_value for comparison (string)
                if st.session_state.user_role_value == "admin":
                    if st.button(f"🗑️ Delete", key=f"del_{lead['id']}_{idx}"):
                        delete_lead(lead['id'])
                        st.rerun()

# =========================================================
# PAGE: BOOKINGS
# =========================================================
def page_bookings():
    st.title("📅 Inspection Bookings")
    st.markdown("---")
    
    with st.expander("➕ Create New Booking", expanded=False):
        with st.form("new_booking_form"):
            col1, col2 = st.columns(2)
            with col1:
                name = st.text_input("Full Name *")
                phone = st.text_input("Phone Number *")
                email = st.text_input("Email Address")
            with col2:
                address = st.text_input("Property Address")
                preferred_date = st.date_input("Preferred Date", min_value=datetime.date.today())
                preferred_time = st.selectbox("Preferred Time", ["Morning (9am-12pm)", "Afternoon (1pm-5pm)", "Evening (5pm-7pm)"])
            notes = st.text_area("Additional Notes")
            
            if st.form_submit_button("Create Booking"):
                if not name or not phone:
                    st.error("Name and phone are required")
                else:
                    is_valid, cleaned_phone = validate_phone(phone)
                    if is_valid:
                        add_booking(name, cleaned_phone, email, address, str(preferred_date), preferred_time, notes)
                        st.success("Booking created!")
                        st.rerun()
                    else:
                        st.error(cleaned_phone)
    
    if st.session_state.bookings:
        for booking in st.session_state.bookings:
            with st.container():
                col1, col2, col3 = st.columns([2, 1, 1])
                with col1:
                    st.markdown(f"**{booking['Name']}**")
                    st.caption(f"📞 {booking['Phone']} | 📅 {booking['Preferred Date']} at {booking['Preferred Time']}")
                with col2:
                    new_status = st.selectbox("Status", [s.value for s in BookingStatus],
                                             index=[s.value for s in BookingStatus].index(booking['Status']),
                                             key=f"booking_status_{booking['id']}")
                    if new_status != booking['Status']:
                        update_booking_status(booking['id'], new_status)
                        st.rerun()
                with col3:
                    if st.session_state.user_role_value == "admin":
                        if st.button(f"Delete", key=f"del_booking_{booking['id']}"):
                            delete_booking(booking['id'])
                            st.rerun()
                st.divider()

# =========================================================
# PAGE: WHATSAPP CENTER - FIXED ACCESS
# =========================================================
def page_whatsapp_center():
    st.title("📲 WhatsApp Integration Center")
    st.markdown("Send WhatsApp messages to leads.")
    st.markdown("---")
    
    # FIX: Use user_role_value (string) instead of enum comparison
    if st.session_state.user_role_value not in ["admin", "sales"]:
        st.error("❌ Access Denied: Only Admin and Sales can access WhatsApp Center.")
        st.info(f"Your current role: {st.session_state.user_role_value}")
        return
    
    st.success(f"✅ Access granted! Your role: {st.session_state.user_role_value}")
    
    # Templates
    with st.expander("📝 Message Templates", expanded=True):
        for key, template in WHATSAPP_TEMPLATES.items():
            st.markdown(f"**{template['name']}**")
            st.code(template['message'], language="text")
            st.markdown("---")
    
    # Send to individual lead
    st.markdown("### 🎯 Send to Individual Lead")
    
    if st.session_state.leads:
        lead_options = {f"{l['Name']} ({l['Status']})": l for l in st.session_state.leads if l.get("Phone") and l["Phone"] != "Not provided"}
        
        if lead_options:
            col1, col2 = st.columns([2, 1])
            with col1:
                selected_lead_name = st.selectbox("Select Lead", list(lead_options.keys()))
                selected_lead = lead_options[selected_lead_name]
            with col2:
                template_key = st.selectbox("Template", list(WHATSAPP_TEMPLATES.keys()),
                                           format_func=lambda x: WHATSAPP_TEMPLATES[x]['name'])
            
            name = selected_lead['Name'].split()[0] if selected_lead['Name'] else "there"
            preview = WHATSAPP_TEMPLATES[template_key]['message']
            preview = preview.replace("{name}", name).replace("{company}", COMPANY_NAME)
            preview = preview.replace("{state}", selected_lead.get('State', '')).replace("{project}", selected_lead.get('Project', ''))
            
            st.info(f"Preview: {preview}")
            
            if st.button("📲 Send WhatsApp", type="primary"):
                wa_link = get_whatsapp_link(selected_lead['Phone'], preview)
                if wa_link:
                    st.markdown(f"[Click to send on WhatsApp]({wa_link})", unsafe_allow_html=True)
                    st.success("WhatsApp link generated!")

# =========================================================
# PAGE: AI CHATBOT
# =========================================================
def page_ai_chatbot():
    st.title("🤖 AI Roofing Assistant")
    st.markdown("Ask me anything about roofing!")
    st.markdown("---")
    
    for role, message in st.session_state.chat_history:
        with st.chat_message(role):
            st.write(message)
    
    if prompt := st.chat_input("Ask a question..."):
        st.session_state.chat_history.append(("user", prompt))
        with st.chat_message("user"):
            st.write(prompt)
        
        response = ai_chatbot_response(prompt)
        st.session_state.chat_history.append(("assistant", response))
        with st.chat_message("assistant"):
            st.write(response)
        st.rerun()
    
    if st.button("Clear Chat"):
        st.session_state.chat_history = []
        st.rerun()

# =========================================================
# PAGE: USER MANAGEMENT (ADMIN ONLY)
# =========================================================
def page_user_management():
    st.title("👥 User Management")
    
    if st.session_state.user_role_value != "admin":
        st.error("❌ Access Denied: Only administrators can access this page.")
        return
    
    st.markdown("---")
    
    for username, user in st.session_state.users.items():
        with st.expander(f"{user.full_name} (@{username}) - Role: {user.role.value}"):
            col1, col2 = st.columns(2)
            with col1:
                st.write(f"**Email:** {user.email}")
                st.write(f"**Phone:** {user.phone}")
                st.write(f"**Created:** {user.created_at[:10]}")
            with col2:
                if username != "admin":
                    new_role = st.selectbox("Change Role", ["admin", "sales", "viewer"],
                                           index=["admin", "sales", "viewer"].index(user.role.value),
                                           key=f"role_{username}")
                    if new_role != user.role.value:
                        user.role = UserRole(new_role)
                        st.success(f"Role updated to {new_role}")
                        st.rerun()
                    
                    if st.button(f"Delete User", key=f"del_{username}"):
                        del st.session_state.users[username]
                        st.rerun()

# =========================================================
# PAGE: AUDIT LOGS (ADMIN ONLY)
# =========================================================
def page_audit_logs():
    st.title("🔒 Audit Logs")
    
    if st.session_state.user_role_value != "admin":
        st.error("❌ Access Denied: Only administrators can view audit logs.")
        return
    
    if st.session_state.audit_logs:
        df = pd.DataFrame([{
            "Time": log.timestamp[:19],
            "User": log.user,
            "Action": log.action,
            "Details": log.details[:100]
        } for log in reversed(st.session_state.audit_logs[-100:])])
        st.dataframe(df, use_container_width=True)

# =========================================================
# PAGE: SETTINGS (ADMIN ONLY)
# =========================================================
def page_settings():
    st.title("⚙️ Settings")
    
    if st.session_state.user_role_value != "admin":
        st.error("❌ Access Denied: Only administrators can access settings.")
        return
    
    metrics = get_dashboard_metrics()
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Users", len(st.session_state.users))
    with col2:
        st.metric("Total Leads", metrics["total_leads"])
    with col3:
        st.metric("Total Bookings", metrics["total_bookings"])
    
    st.markdown("---")
    st.info(f"**WhatsApp Number:** {WHATSAPP_BUSINESS_NUMBER}")
    st.info(f"**Company Name:** {COMPANY_NAME}")

# =========================================================
# LOGIN SCREEN
# =========================================================
def login_screen():
    st.title(f"{COMPANY_LOGO} {COMPANY_NAME}")
    st.markdown("### Professional Lead Management Platform")
    st.markdown("---")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        
        if st.button("Login", use_container_width=True, type="primary"):
            success, message = login_user(username, password)
            if success:
                st.success(message)
                st.rerun()
            else:
                st.error(message)
        
        st.markdown("---")
        st.caption("👑 Demo Admin: **admin** / **Admin123!**")

# =========================================================
# MAIN APPLICATION - FIXED
# =========================================================
def render_sidebar():
    with st.sidebar:
        st.title(f"{COMPANY_LOGO} {COMPANY_NAME}")
        
        if st.session_state.user_full_name:
            st.markdown(f"**{st.session_state.user_full_name}**")
            st.caption(f"Role: {st.session_state.user_role_value}")
        st.divider()
        
        # Navigation based on role_value (string)
        role = st.session_state.user_role_value
        
        if role == "admin":
            pages = {
                "📊 Dashboard": "dashboard",
                "➕ Create Lead": "create_lead",
                "📋 CRM": "crm",
                "📅 Bookings": "bookings",
                "📲 WhatsApp Center": "whatsapp",
                "🤖 AI Chatbot": "chatbot",
                "👥 User Management": "users",
                "🔒 Audit Logs": "audit",
                "⚙️ Settings": "settings"
            }
        elif role == "sales":
            pages = {
                "📊 Dashboard": "dashboard",
                "➕ Create Lead": "create_lead",
                "📋 CRM": "crm",
                "📅 Bookings": "bookings",
                "📲 WhatsApp Center": "whatsapp",
                "🤖 AI Chatbot": "chatbot"
            }
        else:  # viewer
            pages = {
                "📊 Dashboard": "dashboard",
                "📋 CRM": "crm",
                "📅 Bookings": "bookings",
                "🤖 AI Chatbot": "chatbot"
            }
        
        selected_page = st.radio("Navigation", list(pages.keys()))
        st.session_state.page = pages[selected_page]
        
        st.divider()
        metrics = get_dashboard_metrics()
        st.metric("Total Leads", metrics["total_leads"])
        st.metric("Hot Leads", metrics["hot_leads"])
        
        st.divider()
        if st.button("🚪 Logout", use_container_width=True):
            logout_user()
            st.rerun()
    
    return st.session_state.page

def main():
    if not st.session_state.authenticated:
        login_screen()
        return
    
    current_page = render_sidebar()
    
    # Page routing
    if current_page == "dashboard":
        page_dashboard()
    elif current_page == "create_lead":
        if st.session_state.user_role_value in ["admin", "sales"]:
            page_create_lead()
        else:
            st.error("❌ Access Denied: Only Admin and Sales can create leads")
    elif current_page == "crm":
        page_crm()
    elif current_page == "bookings":
        page_bookings()
    elif current_page == "whatsapp":
        page_whatsapp_center()
    elif current_page == "chatbot":
        page_ai_chatbot()
    elif current_page == "users":
        page_user_management()
    elif current_page == "audit":
        page_audit_logs()
    elif current_page == "settings":
        page_settings()
    
    # Footer
    st.divider()
    st.markdown(
        f"""
        <div style='text-align: center; color: gray; font-size: 12px;'>
        {COMPANY_LOGO} {COMPANY_NAME} | WhatsApp: {WHATSAPP_BUSINESS_NUMBER} | © {datetime.datetime.now().year}
        </div>
        """,
        unsafe_allow_html=True
    )

if __name__ == "__main__":
    main()
