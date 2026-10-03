import streamlit as st
import numpy as np

# ตั้งค่าชื่อหน้าเว็บเบราว์เซอร์
st.set_page_config(page_title="BAR Rich BAR", layout="centered")

# Custom CSS สำหรับตกแต่ง UI บนมือถือ
st.markdown("""
<style>
    div[data-testid="column"] button {
        height: 3.5em !important;
        font-size: 16px !important;
        font-weight: bold !important;
        border-radius: 10px !important;
    }
    .stMetric {
        background-color: #1E222D;
        padding: 8px;
        border-radius: 8px;
    }
    .app-title {
        text-align: center;
        font-size: 28px;
        font-weight: 800;
        color: #FFD700;
        margin-bottom: 0px;
    }
    .creator-title {
        text-align: center;
        font-size: 16px;
        font-weight: 600;
        color: #00E676;
        margin-bottom: 4px;
    }
    .sub-title {
        text-align: center;
        font-size: 13px;
        color: #AAAAAA;
        margin-bottom: 15px;
    }
    .footer-text {
        text-align: center;
        font-size: 12px;
        color: #666666;
        margin-top: 25px;
    }
</style>
""", unsafe_allow_html=True)

if "history" not in st.session_state:
    st.session_state.history = []

# --- OPTIMIZED ALGORITHM ---
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

def derived_roads_bias(history):
    clean = [x for x in history if x in ['B', 'P']][-30:]
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
    
    if avg_streak > 2.2:
        return (0.65, 0.35) if clean[-1] == 'B' else (0.35, 0.65)
    elif avg_streak < 1.4:
        return (0.35, 0.65) if clean[-1] == 'B' else (0.65, 0.35)
        
    return 0.5, 0.5

def analyze_engine(history_slice):
    clean = [x for x in history_slice if x in ['B', 'P']]
    if len(clean) < 15:
        return None
    
    p_b_base, p_p_base = 0.5068, 0.4932
    p_b_mk, p_p_mk = markov_chain_prob(clean)
    p_b_rd, p_p_rd = derived_roads_bias(clean)
    
    composite_b = (p_b_base * 0.15) + (p_b_mk * 0.55) + (p_b_rd * 0.30)
    composite_p = (p_p_base * 0.15) + (p_p_mk * 0.55) + (p_p_rd * 0.30)
    
    win_rate_b = composite_b * 100
    win_rate_p = composite_p * 100
    
    ev_b = (composite_b * 0.95) - (composite_p * 1.0)
    ev_p = (composite_p * 1.00) - (composite_b * 1.0)
    
    # เงื่อนไข Win Rate >= 70% เท่านั้นถึงจะส่งสัญญาณ
    if win_rate_b >= 70.0 and ev_b > 0.02:
        action = "BANKER"
    elif win_rate_p >= 70.0 and ev_p > 0.02:
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

# --- CALCULATE WIN / LOSS TRACKER ---
def evaluate_performance(history):
    wins, losses = 0, 0
    # คำนวณสัญญาณย้อนหลังตั้งแต่ตาที่ 16 เป็นต้นไป
    for i in range(15, len(history)):
        actual_result = history[i]
        if actual_result not in ['B', 'P']:
            continue  # ถ้าผลออก Tie จะข้าม ไม่นับแพ้/ชนะ
        
        # ดึงสัญญาณที่แอปเคยคำนวณไว้ก่อนหน้านั้น
        past_signal = analyze_engine(history[:i])
        if past_signal and past_signal["action"] in ["BANKER", "PLAYER"]:
            pred = past_signal["action"]
            if (pred == "BANKER" and actual_result == 'B') or (pred == "PLAYER" and actual_result == 'P'):
                wins += 1
            else:
                losses += 1
                
    return wins, losses

# ---------------- HEADER & DISPLAY ----------------

st.markdown('<div class="app-title">🎰 BAR Rich BAR</div>', unsafe_allow_html=True)
st.markdown('<div class="creator-title">KAiTUN888 By.Epic</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">(Signal Threshold: Win Rate 70%+ | Min Rounds: 15)</div>', unsafe_allow_html=True)

# 1. กล่องแสดงผลวิเคราะห์สัญญาณปัจจุบัน
res = analyze_engine(st.session_state.history)

if res:
    action = res["action"]
    if action == "BANKER":
        st.error(f"### 🔴 แทง BANKER ({res['conf_b']:.1f}%) 🔥")
    elif action == "PLAYER":
        st.info(f"### 🔵 แทง PLAYER ({res['conf_p']:.1f}%) 🔥")
    else:
        st.warning("### ⚪ ข้ามรอบนี้ (SKIP) - อัตราชนะไม่ถึง 70%")
        
    m1, m2 = st.columns(2)
    with m1:
        st.metric("🔴 Banker Prob", f"{res['conf_b']:.1f}%", f"EV: {res['ev_b']:.2f}")
    with m2:
        st.metric("🔵 Player Prob", f"{res['conf_p']:.1f}%", f"EV: {res['ev_p']:.2f}")
else:
    clean_count = len([x for x in st.session_state.history if x in ['B','P']])
    st.info(f"⏳ กรุณาใส่ข้อมูลให้ครบอย่างน้อย 15 ตาก่อนเริ่มวิเคราะห์ (สะสมแล้ว: {clean_count}/15)")

# 2. แผงแสดงสถิติ ถูก / ผิด
wins, losses = evaluate_performance(st.session_state.history)
total_bets = wins + losses
accuracy = (wins / total_bets * 100) if total_bets > 0 else 0.0

st.markdown("---")
st.write("📊 **สถิติผลการทำนาย (Win / Loss):**")
s1, s2, s3 = st.columns(3)
with s1:
    st.metric("✅ ถูก (Win)", f"{wins} ตา")
with s2:
    st.metric("❌ ผิด (Loss)", f"{losses} ตา")
with s3:
    st.metric("🎯 ความแม่นยำ", f"{accuracy:.1f}%")

st.divider()

# 3. ปุ่มกดบันทึก 3 ปุ่มขนานกัน
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

# 4. ปุ่มควบคุมสถิติ
st.write("---")
if st.session_state.history:
    recent = " ".join(st.session_state.history[-12:])
    st.write(f"**สถิติรวม ({len(st.session_state.history)} ตา):** {recent}")

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

# เครดิตด้านล่าง
st.markdown('<div class="footer-text">BAR Rich BAR AI Engine • Created by KAiTUN888 By.Epic</div>', unsafe_allow_html=True)
