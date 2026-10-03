import streamlit as st
import numpy as np
import pandas as pd

# ตั้งค่าหน้าเว็บ
st.set_page_config(page_title="BAR Rich BAR Pro (Derived Roads Engine)", layout="centered", initial_sidebar_state="collapsed")

st.markdown("""
<style>
    .stApp { background-color: #0E1117; color: #E0E0E0; }
    div[data-testid="column"] button {
        height: 3.8em !important; font-size: 16px !important;
        font-weight: 800 !important; border-radius: 12px !important;
        box-shadow: 0px 4px 10px rgba(0, 0, 0, 0.3);
    }
    .stMetric { background: linear-gradient(145deg, #161B22, #1E2430); padding: 10px; border-radius: 12px; border: 1px solid #2D3748; }
    .app-title { text-align: center; font-size: 28px; font-weight: 900; background: linear-gradient(90deg, #FFD700, #FFA500); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
    .creator-title { text-align: center; font-size: 14px; font-weight: 700; color: #00E676; margin-bottom: 2px; }
    .step-badge { background: linear-gradient(135deg, #1A1F2C, #252D3D); border: 2px solid #FFD700; border-radius: 14px; padding: 12px; text-align: center; font-size: 19px; font-weight: 800; color: #FFD700; margin-bottom: 15px; }
    .footer-text { text-align: center; font-size: 11px; color: #666666; margin-top: 25px; }
</style>
""", unsafe_allow_html=True)

if "history" not in st.session_state: st.session_state.history = []
if "shoe_logs" not in st.session_state: st.session_state.shoe_logs = []
if "shoe_count" not in st.session_state: st.session_state.shoe_count = 1

# --- 1. สร้างกระดานหลัก (Big Road Matrix) ---
def build_big_road(history):
    clean = [x for x in history if x in ['B', 'P']]
    if not clean:
        return []
    
    matrix = []
    curr_col = [clean[0]]
    
    for x in clean[1:]:
        if x == curr_col[0]:
            curr_col.append(x)
        else:
            matrix.append(curr_col)
            curr_col = [x]
    matrix.append(curr_col)
    return matrix

# --- 2. ฟังก์ชั่นคำนวณ 3 เค้าไพ่อนุพันธ์จริง (True Derived Roads Logic) ---
def get_derived_road_signal(matrix, offset):
    """
    offset = 1 : ไข่ปลา (Big Eye Boy)
    offset = 2 : ทึบ (Small Road)
    offset = 3 : ไม้ขีด (Cockroach Road)
    คืนค่า 1 (สีแดง - มีรูปแบบซ้ำ) หรือ -1 (สีน้ำเงิน - เปลี่ยนรูปแบบ)
    """
    if len(matrix) <= offset:
        return 0
    
    curr_col_idx = len(matrix) - 1
    curr_row_idx = len(matrix[-1]) - 1
    compare_col_idx = curr_col_idx - offset
    
    if compare_col_idx < 0:
        return 0
        
    compare_col = matrix[compare_col_idx]
    
    if curr_row_idx == 0:
        # เปรียบเทียบความยาวของคอลัมน์ก่อนหน้า
        prev_col_len = len(matrix[curr_col_idx - 1])
        comp_col_len = len(matrix[compare_col_idx])
        return 1 if prev_col_len == comp_col_len else -1
    else:
        # เปรียบเทียบความลึกในคอลัมน์เดียวกัน
        if len(compare_col) >= curr_row_idx + 1:
            return 1  # สีแดง
        else:
            return -1 # สีน้ำเงิน

def derived_roads_engine(history):
    matrix = build_big_road(history)
    if len(matrix) < 4:
        return 0.5, 0.5
    
    # คำนวณสัญญาณจากทั้ง 3 เค้าไพ่
    big_eye = get_derived_road_signal(matrix, 1)   # ไข่ปลา
    small_road = get_derived_road_signal(matrix, 2) # ทึบ
    cockroach = get_derived_road_signal(matrix, 3)  # ไม้ขีด
    
    score = big_eye + small_road + cockroach
    last_side = matrix[-1][0] # ตัวล่าสุดในกระดานหลัก
    
    # ถ้า 3 เค้าไพ่ขึ้นสีแดง (Score > 0) -> ตามเค้าไพ่เดิม
    # ถ้า 3 เค้าไพ่ขึ้นสีน้ำเงิน (Score < 0) -> แทงสวนเค้าไพ่เดิม
    if score > 0:
        return (0.70, 0.30) if last_side == 'B' else (0.30, 0.70)
    elif score < 0:
        return (0.30, 0.70) if last_side == 'B' else (0.70, 0.30)
    
    return 0.5, 0.5

# --- 3. Markov Chain ---
def markov_chain_prob(history):
    clean = [x for x in history if x in ['B', 'P']][-30:]
    if len(clean) < 3: return 0.5068, 0.4932
    last_two = "".join(clean[-2:])
    b_next, p_next = 0, 0
    for i in range(len(clean) - 2):
        if "".join(clean[i:i+2]) == last_two:
            if clean[i+2] == 'B': b_next += 1
            elif clean[i+2] == 'P': p_next += 1
    total = b_next + p_next
    if total == 0: return 0.5068, 0.4932
    return b_next / total, p_next / total

# --- 4. Main Analyzer Engine ---
def analyze_engine(history_slice, target_threshold, min_rounds):
    clean = [x for x in history_slice if x in ['B', 'P']]
    if len(clean) < min_rounds:
        return None
    
    p_b_base, p_p_base = 0.5068, 0.4932
    p_b_mk, p_p_mk = markov_chain_prob(clean)
    p_b_dr, p_p_dr = derived_roads_engine(clean) # ดึงผลคำนวณจาก ไข่ปลา, ทึบ, ไม้ขีด จริง
    
    # ถ่วงน้ำหนักคำนวณ: 3 เค้าไพ่อนุพันธ์จริง (45%) + Markov (45%) + Base (10%)
    composite_b = (p_b_base * 0.10) + (p_b_mk * 0.45) + (p_b_dr * 0.45)
    composite_p = (p_p_base * 0.10) + (p_p_mk * 0.45) + (p_p_dr * 0.45)
    
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
        if actual_result not in ['B', 'P']: continue
        
        past_signal = analyze_engine(history[:i], target_threshold, min_rounds)
        if past_signal and past_signal["action"] in ["BANKER", "PLAYER"]:
            pred = past_signal["action"]
            is_win = (pred == "BANKER" and actual_result == 'B') or (pred == "PLAYER" and actual_result == 'P')
            
            logs.append({
                "ตาที่": i + 1, "ทาย": pred, "ผล": actual_result,
                "ไม้": f"ไม้ {curr_step}", "สถานะ": "✅ ชนะ" if is_win else "❌ ผิด"
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

with st.expander("⚙️ ปรับแต่งเกณฑ์วิเคราะห์ (Strategy Settings)", expanded=False):
    strategy = st.radio(
        "เลือกลักษณะการแทง:",
        ["⚡ สายบู๊ (ออกไม้ถี่ เกณฑ์ 55%+)", "⚖️ สายสมดุล (เกณฑ์มาตรฐาน 60%+)", "🛡️ สายชัวร์ (แม่นยำสูง เกณฑ์ 65%+)"],
        index=2
    )
    if "สายบู๊" in strategy: target_threshold, min_rounds = 55.0, 8
    elif "สายชัวร์" in strategy: target_threshold, min_rounds = 65.0, 10
    else: target_threshold, min_rounds = 60.0, 10

st.caption(f"🎯 เกณฑ์ที่ใช้: **{target_threshold}%** | ใช้สูตรคำนวณ **ไข่ปลา/ทึบ/ไม้ขีด แบบ Real Matrix**")

# ---------------- BUTTONS ----------------
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

t1, t2, t3 = st.columns(3)
with t1:
    if st.button("↩️ ย้อนกลับ", use_container_width=True):
        if st.session_state.history: st.session_state.history.pop(); st.rerun()
with t2:
    if st.button("🔄 ล้างขอนนี้", use_container_width=True):
        st.session_state.history = []; st.rerun()
with t3:
    if st.button("💾 บันทึกขอน", use_container_width=True):
        if len(st.session_state.history) >= min_rounds:
            curr_step, w1, w2, w3, w4, losses, _ = evaluate_martingale_4steps(st.session_state.history, target_threshold, min_rounds)
            st.session_state.shoe_logs.append({
                "ขอนที่": f"ขอน #{st.session_state.shoe_count}",
                "จำนวนตา": len(st.session_state.history),
                "ไม้ 1": w1, "ไม้ 2": w2, "ไม้ 3": w3, "ไม้ 4": w4, "แตก": losses
            })
            st.session_state.shoe_count += 1
            st.session_state.history = []
            st.toast("✅ บันทึกประวัติขอนเรียบร้อยแล้ว!")
            st.rerun()

if st.session_state.history:
    recent = " ".join(st.session_state.history[-12:])
    st.caption(f"**สถิติขอนปัจจุบัน ({len(st.session_state.history)} ตา):** {recent}")

st.divider()

curr_step, w1, w2, w3, w4, losses, detailed_logs = evaluate_martingale_4steps(st.session_state.history, target_threshold, min_rounds)

if curr_step == 1: st.markdown('<div class="step-badge">💰 สถานะปัจจุบัน: [ ไม้ที่ 1 ]</div>', unsafe_allow_html=True)
elif curr_step == 2: st.markdown('<div class="step-badge" style="border-color:#FFB300; color:#FFB300;">🔥 สถานะปัจจุบัน: [ ทบไม้ที่ 2 ]</div>', unsafe_allow_html=True)
elif curr_step == 3: st.markdown('<div class="step-badge" style="border-color:#FF9800; color:#FF9800;">⚡ สถานะปัจจุบัน: [ ทบไม้ที่ 3 ]</div>', unsafe_allow_html=True)
else: st.markdown('<div class="step-badge" style="border-color:#FF3D00; color:#FF3D00;">⚠️ สถานะปัจจุบัน: [ ทบไม้ที่ 4 (สุดท้าย) ]</div>', unsafe_allow_html=True)

res = analyze_engine(st.session_state.history, target_threshold, min_rounds)

if res:
    action = res["action"]
    if action == "BANKER": st.error(f"### 🔴 แทง BANKER ({res['conf_b']:.1f}%)")
    elif action == "PLAYER": st.info(f"### 🔵 แทง PLAYER ({res['conf_p']:.1f}%)")
    else: st.warning(f"### ⚪ ข้ามรอบนี้ (SKIP) - อัตราชนะไม่ถึง {target_threshold:.0f}%")
        
    m1, m2 = st.columns(2)
    with m1: st.metric("🔵 Player Prob", f"{res['conf_p']:.1f}%", f"EV: {res['ev_p']:.2f}")
    with m2: st.metric("🔴 Banker Prob", f"{res['conf_b']:.1f}%", f"EV: {res['ev_b']:.2f}")
else:
    clean_count = len([x for x in st.session_state.history if x in ['B','P']])
    st.info(f"⏳ กรุณาใส่ข้อมูลอย่างน้อย {min_rounds} ตาก่อนเริ่มวิเคราะห์ (สะสมแล้ว: {clean_count}/{min_rounds})")

st.divider()

st.write("📊 **สถิติการเข้าไม้ขอนปัจจุบัน:**")
s1, s2, s3, s4, s5 = st.columns(5)
with s1: st.metric("🎯 ไม้ 1", f"{w1}")
with s2: st.metric("🔥 ไม้ 2", f"{w2}")
with s3: st.metric("⚡ ไม้ 3", f"{w3}")
with s4: st.metric("🚀 ไม้ 4", f"{w4}")
with s5: st.metric("❌ แตก", f"{losses}")

with st.expander("📜 ประวัติย้อนหลังหลายขอน (Multi-Shoe History)"):
    if st.session_state.shoe_logs:
        df_shoes = pd.DataFrame(st.session_state.shoe_logs)
        st.dataframe(df_shoes, use_container_width=True)
        if st.button("🗑️ ล้างประวัติขอนทั้งหมด"):
            st.session_state.shoe_logs = []; st.session_state.shoe_count = 1; st.rerun()
    else: st.write("ยังไม่มีประวัติขอนที่บันทึกไว้")

with st.expander("📝 บันทึกประวัติการเข้าไม้ตาต่อตา (Current Shoe Logs)"):
    if detailed_logs:
        df_logs = pd.DataFrame(detailed_logs)
        st.dataframe(df_logs, use_container_width=True)
    else: st.write("ยังไม่มีบันทึกการเข้าไม้ในขอนนี้")

st.markdown('<div class="footer-text">BAR Rich BAR Pro Engine • Created by KAiTUN888 By.Epic</div>', unsafe_allow_html=True)ndss)

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
    
