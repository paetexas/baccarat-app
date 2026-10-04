import streamlit as st
import numpy as np
import pandas as pd

st.set_page_config(page_title="BAR Rich BAR Pro Elite", layout="centered", initial_sidebar_state="collapsed")

st.markdown("""
<style>
    .stApp { background-color: #0E1117; color: #E0E0E0; }
    div.stButton > button {
        width: 100%; height: 3.2em !important; font-size: 13px !important; font-weight: 800 !important;
        border-radius: 10px !important; background: linear-gradient(135deg, #1F2937, #111827) !important;
        color: white !important; border: 1px solid #374151 !important;
    }
    div.stButton > button:hover { border-color: #FF3D00 !important; }
    .stMetric { background: #161B22; padding: 10px; border-radius: 12px; border: 1px solid #2D3748; }
    .app-title { text-align: center; font-size: 24px; font-weight: 900; color: #FFD700; }
    .creator-title { text-align: center; font-size: 12px; font-weight: 700; color: #00E676; margin-bottom: 10px; }
    .step-badge { background: #1A1F2C; border: 2px solid #FF3D00; border-radius: 10px; padding: 10px; text-align: center; font-size: 16px; font-weight: 800; color: #FF3D00; margin-bottom: 10px; }
    .warning-banner {
        background: rgba(255, 61, 0, 0.12); border: 1px solid #FFD700; color: #FF8A65;
        text-align: center; padding: 10px; border-radius: 8px; font-weight: 700; font-size: 13px;
        margin-top: 20px; margin-bottom: 10px;
    }
    .footer-text { text-align: center; font-size: 11px; color: #666666; margin-top: 10px; }
</style>
""", unsafe_allow_html=True)

if "history" not in st.session_state: st.session_state.history = []
if "shoe_logs" not in st.session_state: st.session_state.shoe_logs = []
if "shoe_count" not in st.session_state: st.session_state.shoe_count = 1

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

def match_special_patterns(clean_history):
    if len(clean_history) < 4: return None, 0.5, 0.5
    last4 = clean_history[-4:]
    if last4 == ['B', 'B', 'B', 'B']: return "มังกรแดงเดือด (Banker Dragon)", 0.88, 0.12
    if last4 == ['P', 'P', 'P', 'P']: return "มังกรน้ำเงินเดือด (Player Dragon)", 0.12, 0.88
    if last4 == ['B', 'B', 'P', 'P']: return "สองตัดคมๆ (Two-Chop)", 0.80, 0.20
    if last4 == ['P', 'P', 'B', 'B']: return "สองตัดคมๆ (Two-Chop)", 0.20, 0.80
    return None, 0.5, 0.5

def analyze_engine(history_slice, base_threshold, min_rounds):
    clean = [x for x in history_slice if x in ['B', 'P']]
    if len(clean) < min_rounds: return None
    
    p_b_mk, p_p_mk = markov_chain_prob(clean)
    pat_name, p_b_pat, p_p_pat = match_special_patterns(clean)
    
    if pat_name:
        composite_b = (p_b_mk * 0.4) + (p_b_pat * 0.6)
        composite_p = (p_p_mk * 0.4) + (p_p_pat * 0.6)
    else:
        composite_b, composite_p = p_b_mk, p_p_mk
        
    win_rate_b, win_rate_p = composite_b * 100, composite_p * 100
    ev_b = (composite_b * 0.95) - (composite_p * 1.0)
    ev_p = (composite_p * 1.00) - (composite_b * 1.0)
    
    action = "BANKER" if win_rate_b >= base_threshold else ("PLAYER" if win_rate_p >= base_threshold else "SKIP")
    return {"action": action, "conf_b": win_rate_b, "conf_p": win_rate_p, "ev_b": ev_b, "ev_p": ev_p, "pat_name": pat_name}

def evaluate_martingale(history, target_threshold, min_rounds):
    curr_step, w, losses = 1, [0] * 9, 0
    detailed_logs = []
    
    for i in range(min_rounds, len(history)):
        actual = history[i]
        if actual not in ['B', 'P']: continue
        res = analyze_engine(history[:i], target_threshold, min_rounds)
        if res and res["action"] in ["BANKER", "PLAYER"]:
            pred = res["action"]
            is_win = (pred == "BANKER" and actual == 'B') or (pred == "PLAYER" and actual == 'P')
            if is_win:
                if 1 <= curr_step <= 8: w[curr_step] += 1
                curr_step = 1
            else:
                if curr_step >= 8: losses += 1; curr_step = 1
                else: curr_step += 1
            detailed_logs.append({"ตาที่": i + 1, "ทาย": pred, "ผล": actual, "ไม้": f"ไม้ {curr_step}", "สถานะ": "ถูก (WIN)" if is_win else "ผิด (LOSS)"})
            
    return curr_step, w[1], w[2], w[3], w[4], w[5], w[6], w[7], w[8], losses, detailed_logs

# ส่วนหัวแอปพลิเคชัน
st.markdown('<div class="app-title">BAR Rich BAR Pro Elite</div>', unsafe_allow_html=True)
st.markdown('<div class="creator-title">KAiTUN888 By.Epic</div>', unsafe_allow_html=True)

# ส่วนเลือกโหมด
strategy = st.radio("เลือกโหมดการยิง:", ["โหมดมาตรฐาน (เกณฑ์ 57%+)", "โหมดซูปเปอร์บู๊ (เกณฑ์ 52%+)"], key="strat")
base_threshold, min_rounds = (52.0, 6) if "ซูปเปอร์บู๊" in strategy else (57.0, 8)

st.divider()

# ส่วนปุ่มบันทึกผลจริง
st.markdown("### บันทึกผลจริง")
sc1, sc2, sc3 = st.columns(3)
with sc1:
    if st.button("PLAYER", use_container_width=True, key="btn_p"): 
        st.session_state.history.append('P')
        st.rerun()
with sc2:
    if st.button("BANKER", use_container_width=True, key="btn_b"): 
        st.session_state.history.append('B')
        st.rerun()
with sc3:
    if st.button("TIE", use_container_width=True, key="btn_t"): 
        st.session_state.history.append('T')
        st.rerun()

# ส่วนปุ่มควบคุมย่อย
t1, t2, t3 = st.columns(3)
with t1:
    if st.button("ย้อนกลับ", use_container_width=True, key="btn_back"): 
        if st.session_state.history: 
            st.session_state.history.pop()
            st.rerun()
with t2:
    if st.button("ล้างขอน", use_container_width=True, key="btn_clear"): 
        st.session_state.history = []
        st.rerun()
with t3:
    if st.button("บันทึกขอน", use_container_width=True, key="btn_save_shoe"): 
        if len(st.session_state.history) >= min_rounds:
            _, w1, w2, w3, w4, w5, w6, w7, w8, losses_val, _ = evaluate_martingale(st.session_state.history, base_threshold, min_rounds)
            st.session_state.shoe_logs.append({
                "ขอนที่": f"ขอน #{st.session_state.shoe_count}", 
                "จำนวนตา": len(st.session_state.history), 
                "ไม้ 1": w1, "ไม้ 2": w2, "ไม้ 3": w3, "ไม้ 4": w4, 
                "ไม้ 5": w5, "ไม้ 6": w6, "ไม้ 7": w7, "ไม้ 8": w8, "แตก": losses_val
            })
            st.session_state.shoe_count += 1
            st.session_state.history = []
            st.rerun()

if st.session_state.history:
    st.caption(f"**สถิติ ({len(st.session_state.history)} ตา):** {' '.join(st.session_state.history[-12:])}")

st.divider()

# การประมวลผลและการแสดงผลวิเคราะห์
curr_step, w1, w2, w3, w4, w5, w6, w7, w8, losses, detailed_logs = evaluate_martingale(st.session_state.history, base_threshold, min_rounds)
st.markdown(f'<div class="step-badge">สถานะเดินเงิน (8 ไม้): [ ไม้ที่ {curr_step} ]</div>', unsafe_allow_html=True)

res = analyze_engine(st.session_state.history, base_threshold, min_rounds)
if res:
    if res["pat_name"]: 
        st.success(f"ตรวจพบเค้าไพ่พิเศษ: **{res['pat_name']}**")
    
    if res["action"] == "BANKER": 
        st.error(f"### ฟันธง: BANKER ({res['conf_b']:.1f}%)")
    elif res["action"] == "PLAYER": 
        st.info(f"### ฟันธง: PLAYER ({res['conf_p']:.1f}%)")
    else: 
        st.warning("### หลบเลี่ยง (SKIP) - ตลาดผันผวน")
    
    m1, m2 = st.columns(2)
    with m1: st.metric("Player Prob", f"{res['conf_p']:.1f}%", f"EV: {res['ev_p']:.2f}")
    with m2: st.metric("Banker Prob", f"{res['conf_b']:.1f}%", f"EV: {res['ev_b']:.2f}")
else:
    clean_len = len([x for x in st.session_state.history if x in ['B', 'P']])
    st.info(f"กำลังสะสมข้อมูล: {clean_len}/{min_rounds} ตา")

st.divider()
st.write("**สถิติการเข้าไม้:**")
cols = st.columns(4)
for idx, val in enumerate([w1, w2, w3, w4], 1):
    with cols[idx-1]: st.metric(f"ไม้ {idx}", f"{val}")
cols2 = st.columns(5)
for idx, val in enumerate([w5, w6, w7, w8, losses], 5):
    lbl = f"ไม้ {idx}" if idx <= 8 else "แตก"
    with cols2[idx-5]: st.metric(lbl, f"{val}")

if st.session_state.shoe_logs:
    st.markdown("### ประวัติย้อนหลังหลายขอน")
    st.dataframe(pd.DataFrame(st.session_state.shoe_logs), use_container_width=True)

if detailed_logs:
    st.markdown("### ประวัติการเข้าไม้ตาต่อตา")
    st.dataframe(pd.DataFrame(detailed_logs), use_container_width=True)

# คู่มือและคำเตือน
st.markdown("---")
st.markdown("### 📖 คู่มือและวิธีใช้งาน")
st.markdown("- **บันทึกผล:** กดปุ่ม PLAYER, BANKER หรือ TIE ตามผลจริงบนโต๊ะเพื่อเก็บสถิติ")
st.markdown("- **ระบบประเมิน:** โปรแกรมจะคำนวณความน่าจะเป็นผ่านระบบ Markov Chain และเค้าไพ่พิเศษ พร้อมบอกสถานะว่าควรแทงฝั่งไหนหรือกดข้าม (SKIP)")
st.markdown("- **ระบบเดินเงิน:** ติดตามสถานะไม้เดินเงิน 8 ไม้เพื่อบริหารความเสี่ยง")

st.markdown('<div class="warning-banner">โปรแกรมเพื่อการวิจัยและศึกษาวิชาการทางสถิติ ไม่สนับสนุนการพนัน</div>', unsafe_allow_html=True)
st.markdown('<div class="footer-text">BAR Rich BAR Pro Elite Edition • Created by KAiTUN888 By.Epic</div>', unsafe_allow_html=True)
