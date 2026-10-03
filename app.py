import streamlit as st
import numpy as np

# ตั้งค่าหน้าจอสำหรับมือถือ
st.set_page_config(page_title="Baccarat Pro Analytics", layout="centered")

# Custom CSS ตกแต่งปุ่มและ UI
st.markdown("""
<style>
    .stButton>button {
        height: 3em;
        font-size: 18px !important;
        font-weight: bold;
        border-radius: 12px;
    }
    .metric-card {
        background-color: #1E222D;
        padding: 15px;
        border-radius: 10px;
        text-align: center;
        border: 1px solid #2B2E3A;
    }
</style>
""", unsafe_allow_html=True)

st.title("🎲 Baccarat Pro AI Analytics")

# Initialize Session State
if "history" not in st.session_state:
    st.session_state.history = []

# --- CORE ALGORITHM ---
def markov_chain_prob(history):
    """2nd Order Markov Chain Engine"""
    clean = [x for x in history if x in ['B', 'P']]
    if len(clean) < 3:
        return 0.5068, 0.4932
    
    last_two = "".join(clean[-2:])
    b_next, p_next = 0, 0
    
    for i in range(len(clean) - 2):
        pair = "".join(clean[i:i+2])
        if pair == last_two:
            next_val = clean[i+2]
            if next_val == 'B': b_next += 1
            elif next_val == 'P': p_next += 1
            
    total = b_next + p_next
    if total == 0:
        return 0.5068, 0.4932
    
    return b_next / total, p_next / total

def derived_roads_bias(history):
    """Simulated Derived Roads Logic"""
    clean = [x for x in history if x in ['B', 'P']]
    if len(clean) < 6:
        return 0.5, 0.5
    
    # Check for ping-pong or dragon trends
    streaks = []
    curr, count = clean[0], 1
    for x in clean[1:]:
        if x == curr:
            count += 1
        else:
            streaks.append(count)
            curr, count = x, 1
    streaks.append(count)
    
    avg_streak = np.mean(streaks[-3:]) if len(streaks) >= 3 else 1
    
    # Trend Analysis
    if avg_streak > 2.2: # Dragon Bias
        last = clean[-1]
        return (0.65, 0.35) if last == 'B' else (0.35, 0.65)
    elif avg_streak < 1.4: # Ping-Pong Bias
        last = clean[-1]
        return (0.35, 0.65) if last == 'B' else (0.65, 0.35)
        
    return 0.5, 0.5

def analyze_engine(history):
    clean = [x for x in history if x in ['B', 'P']]
    if len(clean) < 5:
        return None
    
    # 1. Base Probabilities (Baccarat standard House Edge)
    p_b_base, p_p_base = 0.5068, 0.4932
    
    # 2. Markov Chain
    p_b_mk, p_p_mk = markov_chain_prob(clean)
    
    # 3. Derived Roads Simulation
    p_b_rd, p_p_rd = derived_roads_bias(clean)
    
    # Weighted Composite Probabilities
    composite_b = (p_b_base * 0.2) + (p_b_mk * 0.5) + (p_b_rd * 0.3)
    composite_p = (p_p_base * 0.2) + (p_p_mk * 0.5) + (p_p_rd * 0.3)
    
    # Expected Value (EV) Filter
    ev_b = (composite_b * 0.95) - (composite_p * 1.0)
    ev_p = (composite_p * 1.00) - (composite_b * 1.0)
    
    # Signal Decision
    if ev_b > 0.02 and composite_b > composite_p:
        action = "BANKER"
        confidence = composite_b * 100
    elif ev_p > 0.02 and composite_p > composite_b:
        action = "PLAYER"
        confidence = composite_p * 100
    else:
        action = "SKIP"
        confidence = max(composite_b, composite_p) * 100
        
    return {
        "action": action,
        "conf_b": composite_b * 100,
        "conf_p": composite_p * 100,
        "ev_b": ev_b,
        "ev_p": ev_p,
        "confidence": confidence
    }

# --- CONTROLS SECTION ---
st.subheader("บันทึกผลเค้าไพ่")
c1, c2, c3 = st.columns(3)

with c1:
    if st.button("🔴 BANKER", use_container_width=True):
        st.session_state.history.append('B')
        st.rerun()

with c2:
    if st.button("🔵 PLAYER", use_container_width=True):
        st.session_state.history.append('P')
        st.rerun()

with c3:
    if st.button("🟢 TIE", use_container_width=True):
        st.session_state.history.append('T')
        st.rerun()

# Tools Row
t1, t2 = st.columns(2)
with t1:
    if st.button("↩️ ย้อนกลับ (Undo)", use_container_width=True):
        if st.session_state.history:
            st.session_state.history.pop()
            st.rerun()
with t2:
    if st.button("🔄 ล้างขอน (Reset)", use_container_width=True):
        st.session_state.history = []
        st.rerun()

# --- DISPLAY HISTORY ---
st.divider()
st.write(f"**จำนวนตาที่บันทึก:** {len(st.session_state.history)} ตา")
if st.session_state.history:
    st.write("**สถิติจด:**", " - ".join(st.session_state.history[-15:]))

# --- ANALYTICS DISPLAY ---
res = analyze_engine(st.session_state.history)

if res:
    st.divider()
    st.subheader("🎯 ผลการวิเคราะห์ AI (รอบถัดไป)")
    
    # Display Recommendation Box
    action = res["action"]
    if action == "BANKER":
        st.error(f"### 🔴 แทง BANKER (มั่นใจ {res['conf_b']:.1f}%)")
    elif action == "PLAYER":
        st.info(f"### 🔵 แทง PLAYER (มั่นใจ {res['conf_p']:.1f}%)")
    else:
        st.warning("### ⚪ ข้ามรอบนี้ (SKIP) - ความเสี่ยงสูง")
        
    # Metrics
    m1, m2 = st.columns(2)
    with m1:
        st.metric("🔴 Banker Prob / EV", f"{res['conf_b']:.1f}%", f"EV: {res['ev_b']:.3f}")
    with m2:
        st.metric("🔵 Player Prob / EV", f"{res['conf_p']:.1f}%", f"EV: {res['ev_p']:.3f}")

else:
    st.info(f"⏳ กรุณาบันทึกข้อมูลอย่างน้อย 5 ตาก่อนเริ่มวิเคราะห์ (ปัจจุบัน: {len(st.session_state.history)}/5)")
