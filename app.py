import streamlit as st
import numpy as np

# ตั้งค่าหน้าเว็บ
st.set_page_config(page_title="BAR Rich BAR (4-Step Engine)", layout="centered")

# Custom CSS สำหรับตกแต่ง UI
st.markdown("""
<style>
    div[data-testid="column"] button {
        height: 3.5em !important;
        font-size: 15px !important;
        font-weight: bold !important;
        border-radius: 10px !important;
    }
    .stMetric {
        background-color: #1E222D;
        padding: 6px;
        border-radius: 8px;
    }
    .app-title {
        text-align: center;
        font-size: 26px;
        font-weight: 800;
        color: #FFD700;
        margin-bottom: 0px;
    }
    .creator-title {
        text-align: center;
        font-size: 15px;
        font-weight: 600;
        color: #00E676;
        margin-bottom: 2px;
    }
    .sub-title {
        text-align: center;
        font-size: 12px;
        color: #AAAAAA;
        margin-bottom: 10px;
    }
    .step-badge {
        background-color: #1E222D;
        border: 2px solid #FFD700;
        border-radius: 10px;
        padding: 10px;
        text-align: center;
        font-size: 18px;
        font-weight: bold;
        color: #FFD700;
        margin-bottom: 15px;
    }
    .footer-text {
        text-align: center;
        font-size: 11px;
        color: #666666;
        margin-top: 20px;
    }
</style>
""", unsafe_allow_html=True)

if "history" not in st.session_state:
    st.session_state.history = []

# --- HIGH ACCURACY ALGORITHM ENGINE ---
def markov_chain_prob(history):
    clean = [x for x in history if x in ['B', 'P']][-30:]
    if len(clean) < 3:
        return 0.5068, 0.4932
    
    last_two = "".join(clean[-2:])
    b_next, p_next = 0, 0
    
    for i in range(len(clean) - 2):
        if "".join(clean[i:i+2]) == last_two:
            next_val = clean[i+2]
            if next_val == 'B': b_next += 1
            elif next_val == 'P': p_next += 1
            
    total = b_next + p_next
    if total == 0:
        return 0.5068, 0.4932
    
    return b_next / total, p_next / total

def pattern_recognition_bias(history):
    clean = [x for x in history if x in ['B', 'P']][-20:]
    if len(clean) < 4:
        return 0.5, 0.5
    
    # 1. Check Ping-Pong (P-B-P-B)
    if clean[-4:] == ['P', 'B', 'P', 'B']:
        return 0.30, 0.70  # Expect P
    if clean[-4:] == ['B', 'P', 'B', 'P']:
        return 0.70, 0.30  # Expect B
        
    # 2. Check Dragon Streak (B-B-B-B or P-P-P-P)
    if clean[-4:] == ['B', 'B', 'B', 'B']:
        return 0.75, 0.25  # Follow Dragon B
    if clean[-4:] == ['P', 'P', 'P', 'P']:
        return 0.25, 0.75  # Follow Dragon P

    # 3. Double Cut (B-B-P-P or P-P-B-B)
    if clean[-3:] == ['B', 'B', 'P']:
        return 0.30, 0.70  # Follow P
    if clean[-3:] == ['P', 'P', 'B']:
        return 0.70, 0.30  # Follow B
        
    return 0.5, 0.5

def derived_roads_bias(history):
    clean = [x for x in history if x in ['B', 'P']][-30:]
    if len(clean) < 5:
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
    
    if avg_streak > 2.0:
        return (0.65, 0.35) if clean[-1] == 'B' else (0.35, 0.65)
    elif avg_streak < 1.5:
        return (0.35, 0.65) if clean[-1] == 'B' else (0.65, 0.35)
        
    return 0.5, 0.5

def analyze_engine(history_slice):
    clean = [x for x in history_slice if x in ['B', 'P']]
    if len(clean) < 10:
        return None
    
    p_b_base, p_p_base = 0.5068, 0.4932
    p_b_mk, p_p_mk = markov_chain_prob(clean)
    p_b_pat, p_p_pat = pattern_recognition_bias(clean)
    p_b_rd, p_p_rd = derived_roads_bias(clean)
    
    # ถ่วงน้ำหนัก AI Multi-Engine
    composite_b = (p_b_base * 0.10) + (p_b_mk * 0.40) + (p_b_pat * 0.30) + (p_b_rd * 0.20)
    composite_p = (p_p_base * 0.10) + (p_p_mk * 0.40) + (p_p_pat * 0.30) + (p_p_rd * 0.20)
    
    win_rate_b = composite_b * 100
    win_rate_p = composite_p * 100
    
    ev_b = (composite_b * 0.95) - (composite_p * 1.0)
    ev_p = (composite_p * 1.00) - (composite_b * 1.0)
    
    if win_rate_b >= 62.0 and ev_b > 0.00:
        action = "BANKER"
    elif win_rate_p >= 62.0 and ev_p > 0.00:
        action = "PLAYER"
    else:
        action = "SKIP"
        
    return {
        "action": action,
        "conf_b": win_rate_b,
        "conf_p": win_rate_p,
        "ev_b": ev_b,
        "ev_p": ev_p
    }

# --- 4-STEP MARTINGALE EVALUATOR ---
def evaluate_martingale_4steps(history):
    curr_step = 1
    w1, w2, w3, w4, losses = 0, 0, 0, 0, 0
    
    for i in range(10, len(history)):
        actual_result = history[i]
        if actual_result not in ['B', 'P']:
            continue
        
        past_signal = analyze_engine(history[:i])
        if past_signal and past_signal["action"] in ["BANKER", "PLAYER"]:
            pred = past_signal["action"]
            is_win = (pred == "BANKER" and actual_result == 'B') or (pred == "PLAYER" and actual_result == 'P')
            
            if is_win:
                if curr_step == 1: w1 += 1
                elif curr_step == 2: w2 += 1
                elif curr_step == 3: w3 += 1
                elif curr_step >= 4: w4 += 1
                curr_step = 1
            else:
                if curr_step >= 4:
                    losses += 1
                    curr_step = 1
                else:
                    curr_step += 1
                    
    return curr_step, w1, w2, w3, w4, losses

# ---------------- HEADER ----------------
st.markdown('<div class="app-title">🎰 BAR Rich BAR (4-Step AI)</div>', unsafe_allow_html=True)
st.markdown('<div class="creator-title">KAiTUN888 By.Epic</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">(4-Step Martingale System | Min Rounds: 10)</div>', unsafe_allow_html=True)

# ---------------- 1. ปุ่มคีย์สถิติ (เรียง P ขึ้นก่อน B) ----------------
c1, c2, c3 = st.columns(3)
with c1:
    if st.button("🔵 PLAYER", use_container_width=True):
        st.session_state.history.append('P')
        st.rerun()

with c2:
    if st.button("🔴 BANKER", use_container_width=True):
        st.session_state.history.append('B')
        st.rerun()

with c3:
    if st.button("🟢 TIE", use_container_width=True):
        st.session_state.history.append('T')
        st.rerun()

# ปุ่มควบคุม
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

if st.session_state.history:
    recent = " ".join(st.session_state.history[-12:])
    st.caption(f"**สถิติรวม ({len(st.session_state.history)} ตา):** {recent}")

st.divider()

# คำนวณสถานะทบ 4 ไม้
curr_step, w1, w2, w3, w4, losses = evaluate_martingale_4steps(st.session_state.history)

# ---------------- 2. แสดงป้ายสถานะทบไม้ 4 สเต็ป ----------------
if curr_step == 1:
    st.markdown('<div class="step-badge">💰 สถานะปัจจุบัน: [ ไม้ที่ 1 ]</div>', unsafe_allow_html=True)
elif curr_step == 2:
    st.markdown('<div class="step-badge" style="border-color:#FFB300; color:#FFB300;">🔥 สถานะปัจจุบัน: [ ทบไม้ที่ 2 ]</div>', unsafe_allow_html=True)
elif curr_step == 3:
    st.markdown('<div class="step-badge" style="border-color:#FF9800; color:#FF9800;">⚡ สถานะปัจจุบัน: [ ทบไม้ที่ 3 ]</div>', unsafe_allow_html=True)
else:
    st.markdown('<div class="step-badge" style="border-color:#FF3D00; color:#FF3D00;">⚠️ สถานะปัจจุบัน: [ ทบไม้ที่ 4 (สุดท้าย) ]</div>', unsafe_allow_html=True)

# ---------------- 3. กล่องวิเคราะห์ผล ----------------
res = analyze_engine(st.session_state.history)

if res:
    action = res["action"]
    if action == "BANKER":
        st.error(f"### 🔴 แทง BANKER ({res['conf_b']:.1f}%)")
    elif action == "PLAYER":
        st.info(f"### 🔵 แทง PLAYER ({res['conf_p']:.1f}%)")
    else:
        st.warning("### ⚪ ข้ามรอบนี้ (SKIP) - อัตราชนะไม่ถึงเกณฑ์")
        
    m1, m2 = st.columns(2)
    with m1:
        st.metric("🔵 Player Prob", f"{res['conf_p']:.1f}%", f"EV: {res['ev_p']:.2f}")
    with m2:
        st.metric("🔴 Banker Prob", f"{res['conf_b']:.1f}%", f"EV: {res['ev_b']:.2f}")
else:
    clean_count = len([x for x in st.session_state.history if x in ['B','P']])
    st.info(f"⏳ กรุณาใส่ข้อมูลให้ครบอย่างน้อย 10 ตาก่อนเริ่มวิเคราะห์ (สะสมแล้ว: {clean_count}/10)")

st.divider()

# ---------------- 4. ตารางสถิติเข้าไม้ 4 ไม้ + แตก ----------------
st.write("📊 **สถิติการเข้าไม้ (4-Step Tracker):**")
s1, s2, s3, s4, s5 = st.columns(5)
with s1:
    st.metric("🎯 ไม้ 1", f"{w1}")
with s2:
    st.metric("🔥 ไม้ 2", f"{w2}")
with s3:
    st.metric("⚡ ไม้ 3", f"{w3}")
with s4:
    st.metric("🚀 ไม้ 4", f"{w4}")
with s5:
    st.metric("❌ แตก", f"{losses}")

# เครดิต
st.markdown('<div class="footer-text">BAR Rich BAR AI Engine • Created by KAiTUN888 By.Epic</div>', unsafe_allow_html=True)
