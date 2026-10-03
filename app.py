import streamlit as st
import numpy as np

# ตั้งค่าหน้าจอ
st.set_page_config(page_title="Baccarat AI Pro", layout="centered")

# Custom CSS ตกแต่งปุ่มและ UI สำหรับมือถือโดยเฉพาะ
st.markdown("""
<style>
    /* ปรับแต่งปุ่มกดบันทึก */
    div[data-testid="column"] button {
        height: 3.5em !important;
        font-size: 16px !important;
        font-weight: bold !important;
        border-radius: 10px !important;
        padding: 0px !important;
    }
    
    /* กล่องแนะนำ AI */
    .result-box {
        padding: 15px;
        border-radius: 12px;
        text-align: center;
        margin-bottom: 10px;
    }
</style>
""", unsafe_allow_html=True)

# Initialize Session State
if "history" not in st.session_state:
    st.session_state.history = []

# --- CORE ALGORITHM ---
def markov_chain_prob(history):
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
    clean = [x for x in history if x in ['B', 'P']]
    if len(clean) < 6:
        return 0.5, 0.5
    
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
    
    if avg_streak > 2.2: # Dragon
        last = clean[-1]
        return (0.65, 0.35) if last == 'B' else (0.35, 0.65)
    elif avg_streak < 1.4: # Ping-Pong
        last = clean[-1]
        return (0.35, 0.65) if last == 'B' else (0.65, 0.35)
        
    return 0.5, 0.5

def analyze_engine(history):
    clean = [x for x in history if x in ['B', 'P']]
    if len(clean) < 5:
        return None
    
    p_b_base, p_p_base = 0.5068, 0.4932
    p_b_mk, p_p_mk = markov_chain_prob(clean)
    p_b_rd, p_p_rd = derived_roads_bias(clean)
    
    composite_b = (p_b_base * 0.2) + (p_b_mk * 0.5) + (p_b_rd * 0.3)
    composite_p = (p_p_base * 0.2) + (p_p_mk * 0.5) + (p_p_rd * 0.3)
    
    ev_b = (composite_b * 0.95) - (composite_p * 1.0)
    ev_p = (composite_p * 1.00) - (composite_b * 1.0)
    
    if ev_b > 0.02 and composite_b > composite_p:
        action = "BANKER"
    elif ev_p > 0.02 and composite_p > composite_b:
        action = "PLAYER"
    else:
        action = "SKIP"
        
    return {
        "action": action,
        "conf_b": composite_b * 100,
        "conf_p": composite_p * 100,
        "ev_b": ev_b,
        "ev_p": ev_p
    }

# ---------------- UI LAYOUT (TOP TO BOTTOM) ----------------

st.caption("🎲 Baccarat AI Real-Time Analytics")

# 1. ANALYTICS DISPLAY (ขึ้นก่อนเลย อยู่บนสุด)
res = analyze_engine(st.session_state.history)

if res:
    action = res["action"]
    if action == "BANKER":
        st.error(f"### 🔴 แทง BANKER ({res['conf_b']:.1f}%)")
    elif action == "PLAYER":
        st.info(f"### 🔵 แทง PLAYER ({res['conf_p']:.1f}%)")
    else:
        st.warning("### ⚪ ข้ามรอบนี้ (SKIP)")
        
    # Stats Compact
    m1, m2 = st.columns(2)
    with m1:
        st.metric("🔴 Banker", f"{res['conf_b']:.1f}%", f"EV: {res['ev_b']:.2f}")
    with m2:
        st.metric("🔵 Player", f"{res['conf_p']:.1f}%", f"EV: {res['ev_p']:.2f}")
else:
    st.info(f"⏳ ใส่ข้อมูลอีก {max(0, 5 - len([x for x in st.session_state.history if x in ['B','P']]))} ตา เพื่อเริ่มคำนวณ")

st.divider()

# 2. BUTTONS INPUT (ปุ่มกดแนวนอน 3 ปุ่ม เรียงข้างกัน)
st.write("**กดบันทึกผลตาถัดไป:**")
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

# 3. HISTORY & CONTROL TOOLS (ด้านล่างสุด)
st.write("---")
# แสดงประวัติเค้าไพ่ล่าสุดแบบวงกลม/สี
if st.session_state.history:
    recent = " ".join(st.session_state.history[-10:])
    st.write(f"**สถิติ ({len(st.session_state.history)} ตา):** {recent}")

t1, t2 = st.columns(2)
with t1:
    if st.button("↩️ ย้อนกลับ", use_container_width=True):
        if st.session_state.history:
            st.session_state.history.pop()
            st.rerun()
with t2:
    if st.button("🔄 ล้างขอน", use_container_width=True):
        st.session_state.history = []
        st.rerun()
