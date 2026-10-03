import streamlit as st
import numpy as np
import pandas as pd

# ตั้งค่าหน้าเว็บ
st.set_page_config(page_title="BAR Rich BAR Pro Elite", layout="centered", initial_sidebar_state="collapsed")

# Custom CSS ตกแต่ง UI Neon Dark Theme
st.markdown("""
<style>
    .stApp { background-color: #0E1117; color: #E0E0E0; }
    div[data-testid="column"] button {
        height: 3.8em !important; font-size: 15px !important;
        font-weight: 800 !important; border-radius: 12px !important;
        box-shadow: 0px 4px 10px rgba(0, 0, 0, 0.3);
    }
    .stMetric { background: linear-gradient(145deg, #161B22, #1E2430); padding: 10px; border-radius: 12px; border: 1px solid #2D3748; }
    .app-title { text-align: center; font-size: 26px; font-weight: 900; background: linear-gradient(90deg, #FFD700, #FFA500); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
    .creator-title { text-align: center; font-size: 13px; font-weight: 700; color: #00E676; margin-bottom: 2px; }
    .step-badge { background: linear-gradient(135deg, #1A1F2C, #252D3D); border: 2px solid #FFD700; border-radius: 14px; padding: 12px; text-align: center; font-size: 18px; font-weight: 800; color: #FFD700; margin-bottom: 15px; }
    .kelly-card { background: #1E222D; border-left: 5px solid #00E676; padding: 10px 15px; border-radius: 8px; margin-bottom: 15px; }
    .footer-text { text-align: center; font-size: 11px; color: #666666; margin-top: 25px; }
</style>
""", unsafe_allow_html=True)

# --- SESSION STATES ---
if "history" not in st.session_state: st.session_state.history = []
if "shoe_logs" not in st.session_state: st.session_state.shoe_logs = []
if "shoe_count" not in st.session_state: st.session_state.shoe_count = 1
if "count_4" not in st.session_state: st.session_state.count_4 = 0
if "count_high" not in st.session_state: st.session_state.count_high = 0

# --- 1. BUILD BIG ROAD MATRIX ---
def build_big_road(history):
    clean = [x for x in history if x in ['B', 'P']]
    if not clean: return []
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

# --- 2. CHOPPINESS INDEX ---
def calculate_choppiness(clean_history):
    if len(clean_history) < 8: return 0.0
    switches = 0
    for i in range(1, len(clean_history[-10:])):
        if clean_history[-10:][i] != clean_history[-10:][i-1]:
            switches += 1
    return switches / 9.0

# --- 3. PATTERN TEMPLATE MATCHING ---
def match_special_patterns(clean_history):
    if len(clean_history) < 4: return None, 0.5, 0.5
    last4 = clean_history[-4:]
    last5 = clean_history[-5:] if len(clean_history) >= 5 else []
    
    if last5 == ['P', 'B', 'P', 'B', 'P']: return "🏓 ปิงปองยาว", 0.20, 0.80
    if last5 == ['B', 'P', 'B', 'P', 'B']: return "🏓 ปิงปองยาว", 0.80, 0.20
    if last4 == ['B', 'B', 'B', 'B']: return "🐉 มังกรแดง", 0.82, 0.18
    if last4 == ['P', 'P', 'P', 'P']: return "🐉 มังกรน้ำเงิน", 0.18, 0.82
    if last4 == ['B', 'B', 'P', 'P']: return "✂️ สองตัด", 0.75, 0.25
    if last4 == ['P', 'P', 'B', 'B']: return "✂️ สองตัด", 0.25, 0.75
    
    return None, 0.5, 0.5

# --- 4. 3 DERIVED ROADS ENGINE ---
def get_derived_road_signal(matrix, offset):
    if len(matrix) <= offset: return 0
    curr_col_idx = len(matrix) - 1
    curr_row_idx = len(matrix[-1]) - 1
    compare_col_idx = curr_col_idx - offset
    if compare_col_idx < 0: return 0
    compare_col = matrix[compare_col_idx]
    
    if curr_row_idx == 0:
        prev_col_len = len(matrix[curr_col_idx - 1])
        comp_col_len = len(matrix[compare_col_idx])
        return 1 if prev_col_len == comp_col_len else -1
    else:
        return 1 if len(compare_col) >= curr_row_idx + 1 else -1

def derived_roads_engine(history):
    matrix = build_big_road(history)
    if len(matrix) < 4: return 0.5, 0.5
    big_eye = get_derived_road_signal(matrix, 1)   
    small_road = get_derived_road_signal(matrix, 2) 
    cockroach = get_derived_road_signal(matrix, 3)  
    
    score = big_eye + small_road + cockroach
    last_side = matrix[-1][0]
    
    if score > 0:
        return (0.72, 0.28) if last_side == 'B' else (0.28, 0.72)
    elif score < 0:
        return (0.28, 0.72) if last_side == 'B' else (0.72, 0.28)
    return 0.5, 0.5

# --- 5. MARKOV CHAIN ENGINE ---
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

# --- 6. CARD COUNTING BIAS ENGINE ---
def get_card_counting_bias():
    b_bias = (st.session_state.count_4 * 0.015) - (st.session_state.count_high * 0.005)
    p_bias = (st.session_state.count_high * 0.010) - (st.session_state.count_4 * 0.010)
    return max(-0.05, min(0.05, p_bias)), max(-0.05, min(0.05, b_bias))

# --- 7. MAIN ANALYZER ENGINE ---
def analyze_engine(history_slice, base_threshold, min_rounds):
    clean = [x for x in history_slice if x in ['B', 'P']]
    if len(clean) < min_rounds: return None
    
    chop_index = calculate_choppiness(clean)
    dynamic_threshold = base_threshold + (chop_index * 5.0)
    
    p_b_base, p_p_base = 0.5068, 0.4932
    p_b_mk, p_p_mk = markov_chain_prob(clean)
    p_b_dr, p_p_dr = derived_roads_engine(clean)
    pat_name, p_b_pat, p_p_pat = match_special_patterns(clean)
    p_bias_card, b_bias_card = get_card_counting_bias()
    
    if pat_name:
        composite_b = (p_b_base * 0.05) + (p_b_mk * 0.35) + (p_b_dr * 0.35) + (p_b_pat * 0.25) + b_bias_card
        composite_p = (p_p_base * 0.05) + (p_p_mk * 0.35) + (p_p_dr * 0.35) + (p_p_pat * 0.25) + p_bias_card
    else:
        composite_b = (p_b_base * 0.10) + (p_b_mk * 0.45) + (p_b_dr * 0.45) + b_bias_card
        composite_p = (p_p_base * 0.10) + (p_p_mk * 0.45) + (p_p_dr * 0.45) + p_bias_card
    
    win_rate_b = max(0, min(100, composite_b * 100))
    win_rate_p = max(0, min(100, composite_p * 100))
    
    ev_b = (composite_b * 0.95) - (composite_p * 1.0)
    ev_p = (composite_p * 1.00) - (composite_b * 1.0)
    
    if win_rate_b >= dynamic_threshold and ev_b > -0.05:
        action = "BANKER"
    elif win_rate_p >= dynamic_threshold and ev_p > -0.05:
        action = "PLAYER"
    else:
        action = "SKIP"
        
    return {
        "action": action,
        "conf_b": win_rate_b,
        "conf_p": win_rate_p,
        "ev_b": ev_b,
        "ev_p": ev_p,
        "pat_name": pat_name,
        "chop_index": chop_index,
        "dynamic_threshold": dynamic_threshold
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
st.markdown('<div class="app-title">🎰 BAR Rich BAR Pro Elite</div>', unsafe_allow_html=True)
st.markdown('<div class="creator-title">KAiTUN888 By.Epic</div>', unsafe_allow_html=True)

with st.expander("⚙️ ปรับแต่งเกณฑ์วิเคราะห์ (Strategy Settings)", expanded=False):
    strategy = st.radio(
        "เลือกลักษณะการแทง:",
        ["⚡ สายบู๊ (ออกไม้ถี่ เกณฑ์ 55%+)", "⚖️ สายสมดุล (เกณฑ์มาตรฐาน 60%+)", "🛡️ สายชัวร์ (แม่นยำสูง เกณฑ์ 65%+)"],
        index=2
    )
    if "สายบู๊" in strategy: base_threshold, min_rounds = 55.0, 8
    elif "สายชัวร์" in strategy: base_threshold, min_rounds = 65.0, 10
    else: base_threshold, min_rounds = 60.0, 10

# ---------------- CARD COUNTER SECTION ----------------
with st.expander("🃏 ตัวช่วยนับไพ่ในขอน (Quick Card Counter)", expanded=True):
    col1, col2 = st.columns(2)
    with col1:
        if st.button(f"🃏 เห็นไพ่เลข 4 ({st.session_state.count_4})", use_container_width=True):
            st.session_state.count_4 += 1
            st.rerun()
    with col2:
        if st.button(f"👑 เห็นหน้าใหญ่/9 ({st.session_state.count_high})", use_container_width=True):
            st.session_state.count_high += 1
            st.rerun()

# ---------------- MAIN GAME BUTTONS ----------------
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
    if st.button("↩ ย้อนกลับ", use_container_width=True):
        if st.session_state.history: st.session_state.history.pop(); st.rerun()
with t2:
    if st.button("🔄 ล้างขอนนี้", use_container_width=True):
        st.session_state.history = []
        st.session_state.count_4 = 0
        st.session_state.count_high = 0
        st.rerun()
with t3:
    if st.button("💾 บันทึกขอน", use_container_width=True):
        if len(st.session_state.history) >= min_rounds:
            curr_step, w1, w2, w3, w4, losses, _ = evaluate_martingale_4steps(st.session_state.history, base_threshold, min_rounds)
            st.session_state.shoe_logs.append({
                "ขอนที่": f"ขอน #{st.session_state.shoe_count}",
                "จำนวนตา": len(st.session_state.history),
                "ไม้ 1": w1, "ไม้ 2": w2, "ไม้ 3": w3, "ไม้ 4": w4, "แตก": losses
            })
            st.session_state.shoe_count += 1
            st.session_state.history = []
            st.session_state.count_4 = 0
            st.session_state.count_high = 0
            st.toast("✅ บันทึกประวัติขอนเรียบร้อยแล้ว!")
            st.rerun()

if st.session_state.history:
    recent = " ".join(st.session_state.history[-12:])
    st.caption(f"**สถิติขอนปัจจุบัน ({len(st.session_state.history)} ตา):** {recent}")

st.divider()

curr_step, w1, w2, w3, w4, losses, detailed_logs = evaluate_martingale_4steps(st.session_state.history, base_threshold, min_rounds)

if curr_step == 1: st.markdown('<div class="step-badge">💰 สถานะปัจจุบัน: [ ไม้ที่ 1 ]</div>', unsafe_allow_html=True)
elif curr_step == 2: st.markdown('<div class="step-badge" style="border-color:#FFB300; color:#FFB300;">🔥 สถานะปัจจุบัน: [ ทบไม้ที่ 2 ]</div>', unsafe_allow_html=True)
elif curr_step == 3: st.markdown('<div class="step-badge" style="border-color:#FF9800; color:#FF9800;">⚡ สถานะปัจจุบัน: [ ทบไม้ที่ 3 ]</div>', unsafe_allow_html=True)
else: st.markdown('<div class="step-badge" style="border-color:#FF3D00; color:#FF3D00;">⚠️ สถานะปัจจุบัน: [ ทบไม้ที่ 4 (สุดท้าย) ]</div>', unsafe_allow_html=True)

res = analyze_engine(st.session_state.history, base_threshold, min_rounds)

if res:
    action = res["action"]
    chop_val = res["chop_index"]
    
    if chop_val > 0.6:
        st.caption(f"⚠️ **ขอนนี้ไพ่สลับแกว่งสูง ({chop_val*100:.0f}%)** -> ยกระดับเกณฑ์ขึ้นเป็น {res['dynamic_threshold']:.1f}% เพื่อความปลอดภัย")
    
    if res["pat_name"]:
        st.success(f"🎯 ตรวจพบเค้าไพ่พิเศษ: **{res['pat_name']}**")

    if action == "BANKER":
        st.error(f"### 🔴 แทง BANKER ({res['conf_b']:.1f}%)")
    elif action == "PLAYER":
        st.info(f"### 🔵 แทง PLAYER ({res['conf_p']:.1f}%)")
    else:
        st.warning(f"### ⚪ ข้ามรอบนี้ (SKIP) - ความน่าจะเป็นยังไม่ถึงเกณฑ์ที่ปลอดภัย")
        
    highest_conf = max(res['conf_b'], res['conf_p'])
    if action != "SKIP":
        if highest_conf >= 72.0:
            st.markdown('<div class="kelly-card">💡 **คำแนะนำการลงเงิน:** ความมั่นใจสูงมาก **(แนะนำอัด 1.5x - 2.0x เท่าของไม้ปกติ)**</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="kelly-card">💡 **คำแนะนำการลงเงิน:** ความมั่นใจมาตรฐาน **(เดินเงิน 1.0x ตามแผนปกติ)**</div>', unsafe_allow_html=True)

    m1, m2 = st.columns(2)
    with m1: st.metric("🔵 Player Prob", f"{res['conf_p']:.1f}%", f"EV: {res['ev_p']:.2f}")
    with m2: st.metric("🔴 Banker Prob", f"{res['conf_b']:.1f}%", f"EV: {res['ev_b']:.2f}")
else:
    clean_count = len([x for x in st.session_state.history if x in ['B','P']])
    st.info(f"⏳ สะสมข้อมูล: {clean_count}/{min_rounds} ตา (เริ่มวิเคราะห์เมื่อครบ {min_rounds} ตา)")

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

# ---------------- HOW TO USE SECTION (ADDED AT BOTTOM) ----------------
with st.expander("📖 คู่มือและวิธีใช้งานระบบ (How to Use)", expanded=False):
    st.markdown("""
    **ขั้นตอนการใช้งานในแต่ละตา:**
    1. **เช็คไพ่พิเศษ:** หากในตานั้นคุณเห็นไพ่เลข **4** หรือ ไพ่หน้าใหญ่/ป๊อก (**9, 10, J, Q, K**) เปิดออกมา ให้กดปุ่มนับไพ่ด้านบน *(`🃏 เห็นไพ่เลข 4` หรือ `👑 เห็นหน้าใหญ่/9`)* ตามที่พบจริง (หากตาไหนไม่มีให้ข้ามไป)
    2. **บันทึกผลจริง:** เมื่อผลรอบนั้นออกแล้ว ให้กดบันทึกผลลัพธ์จริงที่ปุ่ม **🔵 PLAYER**, **🔴 BANKER** หรือ **🟢 TIE**
    3. **ดูคำแนะนำตาถัดไป:** ระบบจะนำผลลัพธ์และแต้มไพ่ที่สะสมไปประมวลผลทันที เพื่อแสดงผลคำแนะนำการแทงและความมั่นใจในตาถัดไปให้ทราบ
    """)

st.markdown('<div class="footer-text">BAR Rich BAR Pro Elite Engine • Created by KAiTUN888 By.Epic</div>', unsafe_allow_html=True)
    
