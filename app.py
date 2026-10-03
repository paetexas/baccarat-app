import streamlit as st
import numpy as np
import pandas as pd

# ตั้งค่าหน้าเว็บ
st.set_page_config(page_title="BAR Rich BAR Pro", layout="centered", initial_sidebar_state="collapsed")

# Custom CSS ตกแต่ง UI Neon Dark Theme สบายตา
st.markdown("""
<style>
    /* Global Theme */
    .stApp {
        background-color: #0E1117;
        color: #E0E0E0;
    }
    div[data-testid="column"] button {
        height: 3.8em !important;
        font-size: 16px !important;
        font-weight: 800 !important;
        border-radius: 12px !important;
        box-shadow: 0px 4px 10px rgba(0, 0, 0, 0.3);
        transition: all 0.2s ease-in-out;
    }
    div[data-testid="column"] button:active {
        transform: scale(0.96);
    }
    .stMetric {
        background: linear-gradient(145deg, #161B22, #1E2430);
        padding: 10px;
        border-radius: 12px;
        border: 1px solid #2D3748;
    }
    .app-title {
        text-align: center;
        font-size: 28px;
        font-weight: 900;
        background: linear-gradient(90deg, #FFD700, #FFA500);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0px;
    }
    .creator-title {
        text-align: center;
        font-size: 14px;
        font-weight: 700;
        color: #00E676;
        margin-bottom: 2px;
    }
    .step-badge {
        background: linear-gradient(135deg, #1A1F2C, #252D3D);
        border: 2px solid #FFD700;
        border-radius: 14px;
        padding: 12px;
        text-align: center;
        font-size: 19px;
        font-weight: 800;
        color: #FFD700;
        box-shadow: 0 0 15px rgba(255, 215, 0, 0.2);
        margin-bottom: 15px;
    }
    .footer-text {
        text-align: center;
        font-size: 11px;
        color: #666666;
        margin-top: 25px;
    }
</style>
""", unsafe_allow_html=True)

# Initialize Session States
if "history" not in st.session_state:
    st.session_state.history = []
if "shoe_logs" not in st.session_state:
    st.session_state.shoe_logs = []
if "shoe_count" not in st.session_state:
    st.session_state.shoe_count = 1

# --- ALGORITHM ENGINE ---
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
    
    if clean[-4:] == ['P', 'B', 'P', 'B']: return 0.30, 0.70
    if clean[-4:] == ['B', 'P', 'B', 'P']: return 0.70, 0.30
    if clean[-4:] == ['B', 'B', 'B', 'B']: return 0.75, 0.25
    if clean[-4:] == ['P', 'P', 'P', 'P']: return 0.25, 0.75
    if clean[-3:] == ['B', 'B', 'P']: return 0.30, 0.70
    if clean[-3:] == ['P', 'P', 'B']: return 0.70, 0.30
        
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

def analyze_engine(history_slice, target_threshold, min_rounds):
    clean = [x for x in history_slice if x in ['B', 'P']]
    if len(clean) < min_rounds:
        return None
    
    p_b_base, p_p_base = 0.5068, 0.4932
    p_b_mk, p_p_mk = markov_chain_prob(clean)
    p_b_pat, p_p_pat = pattern_recognition_bias(clean)
    p_b_rd, p_p_rd = derived_roads_bias(clean)
    
    composite_b = (p_b_base * 0.10) + (p_b_mk * 0.40) + (p_b_pat * 0.30) + (p_b_rd * 0.20)
    composite_p = (p_p_base * 0.10) + (p_p_mk * 0.40) + (p_p_pat * 0.30) + (p_p_rd * 0.20)
    
    win_rate_b = composite_b * 100
    win_rate_p = composite_p * 100
    
    ev_b = (composite_b * 0.95) - (composite_p * 1.0)
    ev_p = (composite_p * 1.00) - (composite_b * 1.0)
    
    if win_rate_b >= target_threshold and ev_b > -0.05:
        action = "BANKER"
    elif win_rate_p >= target_threshold and ev_p > -0.05:
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

def evaluate_martingale_4steps(history, target_threshold, min_rounds):
    curr_step = 1
    w1, w2, w3, w4, losses = 0, 0, 0, 0, 0
    logs = []
    
    for i in range(min_rounds, len(history)):
        actual_result = history[i]
        if actual_result not in ['B', 'P']:
            continue
        
        past_signal = analyze_engine(history[:i], target_threshold, min_rounds)
        if past_signal and past_signal["action"] in ["BANKER", "PLAYER"]:
            pred = past_signal["action"]
            is_win = (pred == "BANKER" and actual_result == 'B') or (pred == "PLAYER" and actual_result == 'P')
            
            logs.append({
                "ตาที่": i + 1,
                "ทาย": pred,
                "ผล": actual_result,
                "ไม้": f"ไม้ {curr_step}",
                "สถานะ": "✅ ชนะ" if is_win else "❌ ผิด"
            })
            
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
                    
    return curr_step, w1, w2, w3, w4, losses, logs

# ---------------- HEADER ----------------
st.markdown('<div class="app-title">🎰 BAR Rich BAR Pro</div>', unsafe_allow_html=True)
st.markdown('<div class="creator-title">KAiTUN888 By.Epic</div>', unsafe_allow_html=True)

# ---------------- SETTINGS (เลือกความแม่นยำ) ----------------
with st.expander("⚙️ ปรับแต่งเกณฑ์วิเคราะห์ (Strategy Settings)", expanded=False):
    strategy = st.radio(
        "เลือกลักษณะการแทง:",
        ["⚡ สายบู๊ (ออกไม้ถี่ เกณฑ์ 55%+)", "⚖️ สายสมดุล (เกณฑ์มาตรฐาน 60%+)", "🛡️ สายชัวร์ (แม่นยำสูง เกณฑ์ 65%+)"],
        index=2  # ตั้งค่าเริ่มต้นเป็นสายชัวร์ 65%
    )
    
    if "สายบู๊" in strategy:
        target_threshold = 55.0
        min_rounds = 8
    elif "สายชัวร์" in strategy:
        target_threshold = 65.0
        min_rounds = 10
    else:
        target_threshold = 60.0
        min_rounds = 10

st.caption(f"🎯 เกณฑ์ที่ใช้: **{target_threshold}%** | สะสมขั้นต่ำ: **{min_rounds} ตา**")

# ---------------- 1. ปุ่มคีย์สถิติ (เรียง P ซ้าย / B กลาง / T ขวา) ----------------
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
t1, t2, t3 = st.columns(3)
with t1:
    if st.button("↩️ ย้อนกลับ", use_container_width=True):
        if st.session_state.history:
            st.session_state.history.pop()
            st.rerun()
with t2:
    if st.button("🔄 ล้างขอนนี้", use_container_width=True):
        st.session_state.history = []
        st.rerun()
with t3:
    if st.button("💾 บันทึกขอน", use_container_width=True):
        if len(st.session_state.history) >= min_rounds:
            curr_step, w1, w2, w3, w4, losses, _ = evaluate_martingale_4steps(st.session_state.history, target_threshold, min_rounds)
            st.session_state.shoe_logs.append({
                "ขอนที่": f"ขอน #{st.session_state.shoe_count}",
                "จำนวนตา": len(st.session_state.history),
                "ไม้ 1": w1, "ไม้ 2": w2, "ไม้ 3": w3, "ไม้ 4": w4,
                "แตก": losses
            })
            st.session_state.shoe_count += 1
            st.session_state.history = []
            st.toast("✅ บันทึกประวัติขอนเรียบร้อยแล้ว!")
            st.rerun()

if st.session_state.history:
    recent = " ".join(st.session_state.history[-12:])
    st.caption(f"**สถิติขอนปัจจุบัน ({len(st.session_state.history)} ตา):** {recent}")

st.divider()

# คำนวณสถานะทบ 4 ไม้
curr_step, w1, w2, w3, w4, losses, detailed_logs = evaluate_martingale_4steps(st.session_state.history, target_threshold, min_rounds)

# ---------------- 2. แสดงป้ายสถานะทบไม้ ----------------
if curr_step == 1:
    st.markdown('<div class="step-badge">💰 สถานะปัจจุบัน: [ ไม้ที่ 1 ]</div>', unsafe_allow_html=True)
elif curr_step == 2:
    st.markdown('<div class="step-badge" style="border-color:#FFB300; color:#FFB300;">🔥 สถานะปัจจุบัน: [ ทบไม้ที่ 2 ]</div>', unsafe_allow_html=True)
elif curr_step == 3:
    st.markdown('<div class="step-badge" style="border-color:#FF9800; color:#FF9800;">⚡ สถานะปัจจุบัน: [ ทบไม้ที่ 3 ]</div>', unsafe_allow_html=True)
else:
    st.markdown('<div class="step-badge" style="border-color:#FF3D00; color:#FF3D00;">⚠️ สถานะปัจจุบัน: [ ทบไม้ที่ 4 (สุดท้าย) ]</div>', unsafe_allow_html=True)

# ---------------- 3. กล่องวิเคราะห์ผล ----------------
res = analyze_engine(st.session_state.history, target_threshold, min_rounds)

if res:
    action = res["action"]
    if action == "BANKER":
        st.error(f"### 🔴 แทง BANKER ({res['conf_b']:.1f}%)")
    elif action == "PLAYER":
        st.info(f"### 🔵 แทง PLAYER ({res['conf_p']:.1f}%)")
    else:
        st.warning(f"### ⚪ ข้ามรอบนี้ (SKIP) - อัตราชนะไม่ถึง {target_threshold:.0f}%")
        
    m1, m2 = st.columns(2)
    with m1:
        st.metric("🔵 Player Prob", f"{res['conf_p']:.1f}%", f"EV: {res['ev_p']:.2f}")
    with m2:
        st.metric("🔴 Banker Prob", f"{res['conf_b']:.1f}%", f"EV: {res['ev_b']:.2f}")
else:
    clean_count = len([x for x in st.session_state.history if x in ['B','P']])
    st.info(f"⏳ กรุณาใส่ข้อมูลอย่างน้อย {min_rounds} ตาก่อนเริ่มวิเคราะห์ (สะสมแล้ว: {clean_count}/{min_rounds})")

st.divider()

# ---------------- 4. ตารางสถิติเข้าไม้ขอนปัจจุบัน ----------------
st.write("📊 **สถิติการเข้าไม้ขอนปัจจุบัน:**")
s1, s2, s3, s4, s5 = st.columns(5)
with s1: st.metric("🎯 ไม้ 1", f"{w1}")
with s2: st.metric("🔥 ไม้ 2", f"{w2}")
with s3: st.metric("⚡ ไม้ 3", f"{w3}")
with s4: st.metric("🚀 ไม้ 4", f"{w4}")
with s5: st.metric("❌ แตก", f"{losses}")

# ---------------- 5. ย้อนดูประวัติสถิติรวมหลายๆ ขอน ----------------
with st.expander("📜 ประวัติย้อนหลังหลายขอน (Multi-Shoe History)"):
    if st.session_state.shoe_logs:
        df_shoes = pd.DataFrame(st.session_state.shoe_logs)
        st.dataframe(df_shoes, use_container_width=True)
        if st.button("🗑️ ล้างประวัติขอนทั้งหมด"):
            st.session_state.shoe_logs = []
            st.session_state.shoe_count = 1
            st.rerun()
    else:
        st.write("ยังไม่มีประวัติขอนที่บันทึกไว้ (กด '💾 บันทึกขอน' เมื่อเล่นจบขอน)")

with st.expander("📝 บันทึกประวัติการเข้าไม้ตาต่อตา (Current Shoe Logs)"):
    if detailed_logs:
        df_logs = pd.DataFrame(detailed_logs)
        st.dataframe(df_logs, use_container_width=True)
    else:
        st.write("ยังไม่มีบันทึกการเข้าไม้ในขอนนี้")

# เครดิต
st.markdown('<div class="footer-text">BAR Rich BAR Pro Engine • Created by KAiTUN888 By.Epic</div>', unsafe_allow_html=True)
    
