import streamlit as st

st.set_page_config(page_title="Baccarat Analytics", layout="centered")
st.title("🎲 ระบบวิเคราะห์เค้าไพ่")

if "history" not in st.session_state:
    st.session_state.history = []

def calculate_signal(history):
    clean_history = [x for x in history if x in ['B', 'P']]
    if len(clean_history) < 5:
        return 0, 0, 0, 0, "SKIP"
    
    total = len(clean_history)
    b_count = clean_history.count('B')
    p_count = clean_history.count('P')
    
    conf_b = (b_count / total) * 100
    conf_p = (p_count / total) * 100
    
    ev_b = (conf_b / 100 * 0.95) - ((100 - conf_b) / 100 * 1.0)
    ev_p = (conf_p / 100 * 1.00) - ((100 - conf_p) / 100 * 1.0)
    
    if ev_b > 0.02 and conf_b > conf_p:
        action = "BET BANKER"
    elif ev_p > 0.02 and conf_p > conf_b:
        action = "BET PLAYER"
    else:
        action = "SKIP"
        
    return conf_b, conf_p, ev_b, ev_p, action

col1, col2 = st.columns(2)

with col1:
    if st.button("🔴 BANKER (B)", use_container_width=True):
        st.session_state.history.append('B')

with col2:
    if st.button("🔵 PLAYER (P)", use_container_width=True):
        st.session_state.history.append('P')

st.write("**สถิติจดสะสม:**", " - ".join(st.session_state.history))

if len(st.session_state.history) >= 5:
    conf_b, conf_p, ev_b, ev_p, action = calculate_signal(st.session_state.history)
    
    st.divider()
    st.subheader("📊 ผลการวิเคราะห์รอบถัดไป")
    st.write(f"🔴 **Banker:** {conf_b:.1f}% (EV: {ev_b:.3f})")
    st.write(f"🔵 **Player:** {conf_p:.1f}% (EV: {ev_p:.3f})")
    
    if action == "BET BANKER":
        st.success("👉 คำแนะนำ: 🔴 **แทง BANKER**")
    elif action == "BET PLAYER":
        st.info("👉 คำแนะนำ: 🔵 **แทง PLAYER**")
    else:
        st.warning("👉 คำแนะนำ: ⚪ **ข้ามรอบนี้ (SKIP)**")
else:
    st.info(f"⏳ กรุณาใส่ข้อมูลให้ครบ 5 ตาก่อน (ตอนนี้ใส่แล้ว {len(st.session_state.history)}/5)")

st.divider()
if st.button("🔄 ล้างขอน (Reset)"):
    st.session_state.history = []
    st.rerun()
  
