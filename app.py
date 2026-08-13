import streamlit as st
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="CliniQ AI - Smart Intake & Queue", layout="wide")

# Initialize central session database
if "queue_db" not in st.session_state:
    st.session_state.queue_db = []

if "counter" not in st.session_state:
    st.session_state.counter = 100

# App Navigation
st.sidebar.title("🏥 CliniQ AI System")
mode = st.sidebar.radio("Select Interface Module:", [
    "1. Patient Check-In Kiosk", 
    "2. Doctor/Consultant Dashboard", 
    "3. Waiting Room TV Display"
])

# ==========================================
# MODULE 1: PATIENT CHECK-IN & EMERGENCY SCAN
# ==========================================
if mode == "1. Patient Check-In Kiosk":
    st.title("📲 Welcome to CliniQ Check-In")
    st.subheader("Please check in to get your ticket number")

    with st.form("patient_kiosk_form"):
        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input("Full Name", placeholder="e.g., Jane Doe")
            phone = st.text_input("Phone Number", placeholder="078XXXXXXX")
            age = st.number_input("Age", min_value=1, max_value=110, value=25)
        
        with col2:
            gender = st.selectbox("Gender", ["Female", "Male", "Other"])
            visit_reason = st.selectbox("Reason for Visit", [
                "General Consultation", 
                "Follow-up / Lab Results", 
                "Pharmacy / Prescription Renewal", 
                "Urgent / Emergency Care"
            ])
        
        st.markdown("---")
        st.write("### 🚨 Rapid Emergency Screening")
        emergency_check = st.multiselect(
            "Are you or the patient currently experiencing any of these critical symptoms?",
            ["Chest Pain / Heart Distress", "Severe Difficulty Breathing", "Unconsciousness", "Heavy Uncontrolled Bleeding"]
        )
        
        symptoms_detail = st.text_area("Briefly describe your symptoms or reason for visit:")

        submitted = st.form_submit_button("🎟️ Submit & Print Ticket")

    if submitted:
        if not name:
            st.error("Please enter your name to proceed.")
        else:
            st.session_state.counter += 1
            is_emergency = len(emergency_check) > 0
            
            # Determine Ticket Code & Priority
            if is_emergency:
                ticket_id = f"EMG-{st.session_state.counter}"
                priority = 1  # Top Priority
                status_color = "red"
            else:
                ticket_id = f"A-{st.session_state.counter}"
                priority = 2
                status_color = "green"

            # Create Record
            entry = {
                "ticket_id": ticket_id,
                "name": name,
                "phone": phone,
                "age": age,
                "gender": gender,
                "reason": visit_reason,
                "symptoms": symptoms_detail,
                "is_emergency": is_emergency,
                "priority": priority,
                "status": "WAITING",
                "time": datetime.now().strftime("%H:%M:%S")
            }
            
            st.session_state.queue_db.append(entry)
            
            # Printed Ticket Simulation Box
            st.success("✅ Check-in complete! Please take your ticket below:")
            
            st.markdown(f"""
            <div style="border: 2px dashed #333; padding: 20px; border-radius: 10px; width: 320px; background-color: #fdfdfd; color: #000;">
                <h3 style="text-align: center; margin:0;">CLINIQ TICKET</h3>
                <hr>
                <h1 style="text-align: center; color: {status_color}; margin: 5px 0;">{ticket_id}</h1>
                <p><b>Name:</b> {name}</p>
                <p><b>Time:</b> {entry['time']}</p>
                <p><b>Category:</b> {'🚨 EMERGENCY PRIORITY' if is_emergency else 'Standard Queue'}</p>
                <hr>
                <p style="font-size: 11px; text-align: center;">Please watch the display screen for your number.</p>
            </div>
            """, unsafe_allow_html=True)

# ==========================================
# MODULE 2: DOCTOR / CONSULTANT DASHBOARD
# ==========================================
elif mode == "2. Doctor/Consultant Dashboard":
    st.title("🩺 Doctor & Consultant Dashboard")

    if not st.session_state.queue_db:
        st.info("No patients in the queue right now.")
    else:
        # Convert to DataFrame and sort by Priority (Emergency first) then Time
        df = pd.DataFrame(st.session_state.queue_db)
        df_waiting = df[df["status"] == "WAITING"].sort_values(by=["priority", "time"])

        # Check for Emergency Alert Banner
        emergencies = df_waiting[df_waiting["is_emergency"] == True]
        if not emergencies.empty:
            st.error(f"🚨 ALERT: There are {len(emergencies)} EMERGENCY cases in the queue needing immediate attention!")

        col_left, col_right = st.columns([1, 1])

        with col_left:
            st.subheader("📋 Active Patient Queue")
            st.dataframe(
                df_waiting[["ticket_id", "name", "reason", "time", "is_emergency"]],
                use_container_width=True
            )

            # Action to Call Next Patient
            if not df_waiting.empty:
                next_patient = df_waiting.iloc[0]
                if st.button(f"🔔 Call Next Patient ({next_patient['ticket_id']} - {next_patient['name']})"):
                    # Update status in session state
                    for record in st.session_state.queue_db:
                        if record["ticket_id"] == next_patient["ticket_id"]:
                            record["status"] = "IN CONSULTATION"
                    st.rerun()

        with col_right:
            # Active Patient View / AI Pre-Consultation Summary
            active_patients = [p for p in st.session_state.queue_db if p["status"] == "IN CONSULTATION"]
            
            if active_patients:
                p = active_patients[-1]  # Most recently called
                st.subheader(f"Current Patient: {p['name']} ({p['ticket_id']})")
                
                st.markdown("### 🤖 Auto-Generated Pre-Consultation SOAP Note")
                st.info("The system pre-filled this from the patient's kiosk answers to save consultation time:")

                st.markdown(f"""
                * **SUBJECTIVE:** {p['age']} yo {p['gender']}. Reason for visit: *{p['reason']}*. Reported symptoms: "{p['symptoms']}"
                * **OBJECTIVE:** Pending physical assessment & vitals intake.
                * **ASSESSMENT:** Preliminary intake review for *{p['reason']}*.
                * **PLAN:** Check vitals, proceed with consultation.
                """)

                if st.button("✅ Complete Consultation"):
                    p["status"] = "COMPLETED"
                    st.rerun()
            else:
                st.write("Click **Call Next Patient** to start a consultation.")

# ==========================================
# MODULE 3: WAITING ROOM TV DISPLAY
# ==========================================
elif mode == "3. Waiting Room TV Display":
    st.title("📢 Waiting Room Display")
    st.markdown("---")

    if st.session_state.queue_db:
        in_consultation = [p for p in st.session_state.queue_db if p["status"] == "IN CONSULTATION"]
        waiting = [p for p in st.session_state.queue_db if p["status"] == "WAITING"]
        
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("🔊 NOW SERVING / PROCEED TO ROOM")
            if in_consultation:
                current = in_consultation[-1]
                st.markdown(f"""
                <div style="background-color: #2e7d32; padding: 30px; border-radius: 15px; text-align: center; color: white;">
                    <h1 style="font-size: 80px; margin: 0;">{current['ticket_id']}</h1>
                    <h2>{current['name']}</h2>
                    <p style="font-size: 20px;">Please enter Consultation Room 1</p>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.info("Waiting for next patient call...")

        with col2:
            st.subheader("⏳ NEXT IN LINE")
            if waiting:
                # Sort by priority
                sorted_waiting = sorted(waiting, key=lambda x: (x["priority"], x["time"]))
                for item in sorted_waiting[:4]:
                    box_color = "#c62828" if item["is_emergency"] else "#1565c0"
                    st.markdown(f"""
                    <div style="background-color: {box_color}; padding: 10px; border-radius: 8px; margin-bottom: 10px; color: white;">
                        <span style="font-size: 24px; font-weight: bold;">{item['ticket_id']}</span> - {item['name']} ({'EMERGENCY' if item['is_emergency'] else 'Standard'})
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.write("No patients currently waiting.")
    else:
        st.write("Queue is currently empty.")