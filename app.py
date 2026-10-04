import streamlit as st
import numpy as np
import pandas as pd
import random

st.set_page_config(page_title="KAiTUN BCR PROMAX", layout="centered", initial_sidebar_state="collapsed")

st.markdown("""
<style>
    .stApp { 
        background: radial-gradient(circle at 50% 0%, #111827 0%, #0B0F19 100%); 
        color: #F3F4F6; 
        font-family: 'Inter', sans-serif;
    }
    .glass-card {
        background: rgba(22, 27, 34, 0.75);
        backdrop-filter: blur(12px);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 16px;
        padding: 18px;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
        margin-bottom: 15px;
    }
    div[data-testid="column"] button {
        height: 3.4em !important; 
        font-size: 13px !important;
        font-weight: 800 !important; 
        border-radius: 12px !important;
        box-shadow: 0px 4px 15px rgba(0, 0, 0, 0.3);
        color: white !important; 
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
    }
    .app-title { 
        text-align: center; font-size: 30px; font-weight: 900; 
        background: linear-gradient(135deg, #FFD700 0%, #FF3D00 100%); 
        -webkit-background-clip: text; -webkit-text-fill-color: transparent; 
        margin-bottom: 0px;
    }
    .creator-title { 
        text-align: center; font-size: 13px; font-weight: 700; 
        color: #00E676; margin-bottom: 20px; text-transform: uppercase;
    }
    .step-badge { 
        background: rgba(26, 31, 44, 0.9); border: 2px solid #FF3D00; 
        border-radius: 16px; padding: 14px; text-align: center; 
        font-size: 18px; font-weight: 800; color: #FF3D00; margin-bottom: 15px;
    }
    .kelly-card { 
        background: rgba(30, 34, 45, 0.85); border-left: 5px solid #FFD700; 
        padding: 12px 18px; border-radius: 10px; margin-bottom: 15px; font-size: 14px;
    }
    .feedback-card { 
        background: rgba(22, 34, 42, 0.85); border-left: 5px solid #00E676; 
        padding: 12px 18px; border-radius: 10px; margin-bottom: 15px; font-size: 13px; 
    }
    .warning-banner {
        background: rgba(255, 61, 0, 0.1); border: 1px solid rgba(255, 215, 0, 0.4); 
        color: #FF8A65; text-align: center; padding: 12px; border-radius: 12px; 
        font-weight: 700; font-size: 13px; margin-top: 25px; margin-bottom: 10px;
    }
</style>
""", unsafe_allow_html=True)

if "history" not in st.session_state: st.session_state.history = []
if "spreads" not in st.session_state: st.session_state.spreads = [] 
if "shoe_logs" not in st.session_state: st.session_state.shoe_logs = []
if "shoe_count" not in st.session_state: st.session_state.shoe_count = 1
if "card_counts" not in st.session_state: st.session_state.card_counts = {i: 0 for i in range(10)}
if "total_cards" not in st.session_state: st.session_state.total_cards = 0

def build_big_road(history):
    clean = [x for x in history if x in ['B', 'P']]
    if not clean: return []
    matrix, curr_col = [], [clean[0]]
    for x in clean[1:]:
        if x == curr_col[0]: curr_col.append(x)
        else:
            matrix.append(curr_col)
            curr_col = [x]
    matrix.append(curr_col)
    return matrix

def calculate_choppiness(clean_history):
    if len(clean_history) < 8: return 0.0
    switches = sum(1 for i in range(1, len(clean_history[-10:])) if clean_history[-10:][i] != clean_history[-10:][i-1])
    return switches / 9.0

def match_special_patterns(clean_history):
    if len(clean_history) < 4: return None, 0.5, 0.5
    last4, last5 = clean_history[-4:], clean_history[-5:] if len(clean_history) >= 5 else []
    if last5 in [['P', 'B', 'P', 'B', 'P'], ['B', 'P', 'B', 'P', 'B']]:
        return "ปิงปองยาว", 0.15, 0.85
    if last4 == ['B', 'B', 'B', 'B']: return "มังกรแดง", 0.88, 0.12
    if last4 == ['P', 'P', 'P', 'P']: return "มังกรน้ำเงิน", 0.12, 0.88
    if last4 == ['B', 'B', 'P', 'P']: return "สองตัด", 0.80, 0.20
    if last4 == ['P', 'P', 'B', 'B']: return "สองตัด", 0.20, 0.80
    return None, 0.5, 0.5

def get_derived_road_signal(matrix, offset):
    if len(matrix) <= offset: return 0
    curr_col_idx, curr_row_idx = len(matrix) - 1, len(matrix[-1]) - 1
    compare_col_idx = curr_col_idx - offset
    if compare_col_idx < 0: return 0
    compare_col = matrix[compare_col_idx]
    if curr_row_idx == 0:
        return 1 if len(matrix[curr_col_idx - 1]) == len(compare_col) else -1
    else:
        return 1 if len(compare_col) >= curr_row_idx + 1 else -1

def derived_roads_engine(history):
    matrix = build_big_road(history)
    if len(matrix) < 4: return (0.5, 0.5), False
    score = get_derived_road_signal(matrix, 1) + get_derived_road_signal(matrix, 2) + get_derived_road_signal(matrix, 3)
    last_side = matrix[-1][0]
    is_fusion = (abs(score) == 3)
    if score > 0: return ((0.78, 0.22) if last_side == 'B' else (0.22, 0.78)), is_fusion
    elif score < 0: return ((0.22, 0.78) if last_side == 'B' else (0.78, 0.22)), is_fusion
    return (0.5, 0.5), False

def markov_chain_prob(history):
    clean = [x for x in history if x in ['B', 'P']][-30:]
    if len(clean) < 3: return 0.5068, 0.4932
    last_two, b_next, p_next = "".join(clean[-2:]), 0, 0
    for i in range(len(clean) - 2):
        if "".join(clean[i:i+2]) == last_two:
            if clean[i+2] == 'B': b_next += 1
            elif clean[i+2] == 'P': p_next += 1
    total = b_next + p_next
    if total == 0: return 0.5068, 0.4932
    return b_next / total, p_next / total

def get_hilo_card_bias():
    counts = st.session_state.card_counts
    running_count = (counts[0]*1.2) + (counts[1]*1.0) + (counts[2]*0.8) + (counts[3]*1.5) - (counts[7]*1.0) - (counts[8]*1.5) - (counts[9]*1.2)
    decks_remaining = max(1.0, (416 - st.session_state.total_cards) / 52.0)
    true_count = running_count / decks_remaining
    spread_boost = 0.03 if st.session_state.spreads and sum(st.session_state.spreads[-10:]) / len(st.session_state.spreads[-10:]) >= 4.0 else 0.0
    bias = (true_count * 0.012) + spread_boost
    return max(-0.09, min(0.09, -bias)), max(-0.09, min(0.09, bias)), true_count, running_count

def analyze_engine(history_slice, base_threshold, min_rounds, recent_bonus=0.0):
    clean = [x for x in history_slice if x in ['B', 'P']]
    if len(clean) < min_rounds: return None
    dynamic_threshold = base_threshold + (calculate_choppiness(clean) * 3.0)
    
    p_b_mk, p_p_mk = markov_chain_prob(clean)
    (p_b_dr, p_p_dr), is_fusion = derived_roads_engine(clean)
    pat_name, p_b_pat, p_p_pat = match_special_patterns(clean)
    p_bias, b_bias, _, _ = get_hilo_card_bias()
    
    if pat_name:
        comp_b = (p_b_mk * 0.30) + (p_b_dr * 0.35) + (p_b_pat * 0.25) + (b_bias * 0.10)
        comp_p = (p_p_mk * 0.30) + (p_p_dr * 0.35) + (p_p_pat * 0.25) + (p_bias * 0.10)
    else:
        comp_b = (0.5068 * 0.05) + (p_b_mk * 0.45) + (p_b_dr * 0.40) + b_bias
        comp_p = (0.4932 * 0.05) + (p_p_mk * 0.45) + (p_p_dr * 0.40) + p_bias
        
    if is_fusion:
        if comp_b > comp_p: comp_b += 0.08
        else: comp_p += 0.08
        
    comp_b += recent_bonus
    comp_p -= recent_bonus
    
    win_b, win_p = max(0, min(100, comp_b * 100)), max(0, min(100, comp_p * 100))
    ev_b, ev_p = (comp_b * 0.95) - (comp_p * 1.0), (comp_p * 1.00) - (comp_b * 1.0)
    
    if win_b >= dynamic_threshold and ev_b > -0.06: action = "BANKER"
    elif win_p >= dynamic_threshold and ev_p > -0.06: action = "PLAYER"
    else: action = "SKIP"
        
    return {"action": action, "conf_b": win_b, "conf_p": win_p, "ev_b": ev_b, "ev_p": ev_p, "pat_name": pat_name, "is_fusion": is_fusion}

def evaluate_martingale_8steps(history, target_threshold, min_rounds):
    curr_step, w, losses, logs, correct_count, total_signals, recent_bonus = 1, [0] * 9, 0, [], 0, 0, 0.0
    for i in range(min_rounds, len(history)):
        actual = history[i]
        if actual not in ['B', 'P']: continue
        past_signal = analyze_engine(history[:i], target_threshold, min_rounds, recent_bonus)
        if past_signal and past_signal["action"] in ["BANKER", "PLAYER"]:
            pred = past_signal["action"]
            is_win = (pred == "BANKER" and actual == 'B') or (pred == "PLAYER" and actual == 'P')
            total_signals += 1
            if is_win:
                correct_count += 1
                if 1 <= curr_step <= 8: w[curr_step] += 1
                curr_step = 1
            else:
                if curr_step >= 8: losses += 1; curr_step = 1
                else: curr_step += 1
            if total_signals >= 3:
                recent_acc = correct_count / total_signals
                recent_bonus = 0.04 if recent_acc >= 0.65 else (-0.04 if recent_acc <= 0.35 else 0.0)
            logs.append({"ตาที่": i + 1, "ทาย": pred, "ผล": actual, "ไม้": f"ไม้ {curr_step}", "สถานะ": "ถูก" if is_win else "ผิด"})
    acc_rate = (correct_count / total_signals * 100) if total_signals > 0 else 0.0
    return curr_step, w[1], w[2], w[3], w[4], w[5], w[6], w[7], w[8], losses, logs, acc_rate, total_signals

st.markdown('<div class="app-title">KAiTUN BCR PROMAX</div>', unsafe_allow_html=True)
st.markdown('<div class="creator-title">Created by KAiTUN888 By.Epic</div>', unsafe_allow_html=True)

strategy = st.radio("เลือกโหมดการยิงตามเค้าไพ่:", ["โหมดมาตรฐาน (เกณฑ์ 57%+)", "โหมดซูปเปอร์บู๊ (เกณฑ์ 52%+)", "โหมดอัลตร้าสไนเปอร์ (เกณฑ์ 70%+)"])
if "ซูปเปอร์บู๊" in strategy: base_threshold, min_rounds = 52.0, 6
elif "อัลตร้าสไนเปอร์" in strategy: base_threshold, min_rounds = 70.0, 10
else: base_threshold, min_rounds = 57.0, 8

st.divider()

with st.container():
    st.markdown("### 📊 ระบบนับไพ่ Hi-Lo")
    _, _, _, running_cnt = get_hilo_card_bias()
    m1, m2 = st.columns(2)
    with m1: st.metric("ไพ่ที่ออก", f"{st.session_state.total_cards}")
    with m2: st.metric("True Count", f"{running_cnt:.2f}")

    cards = ["10/J/Q/K", "A", "2", "3", "4", "5", "6", "7", "8", "9"]
    cols = st.columns(5)
    for idx, c in enumerate(cards[:5]):
        with cols[idx]:
            if st.button(c, use_container_width=True):
                st.session_state.card_counts[idx if idx > 0 else 0] += 1
                st.session_state.total_cards += 1
                st.rerun()
    cols2 = st.columns(5)
    for idx, c in enumerate(cards[5:]):
        with cols2[idx]:
            if st.button(c, use_container_width=True):
                st.session_state.card_counts[idx + 5] += 1
                st.session_state.total_cards += 1
                st.rerun()
    if st.button("🔄 รีเซ็ตสำรับไพ่", use_container_width=True):
        st.session_state.card_counts = {i: 0 for i in range(10)}
        st.session_state.total_cards = 0
        st.rerun()

st.divider()

st.markdown("### 🕹️ บันทึกผลจริงตาต่อตา")
sc1, sc2, sc3 = st.columns(3)
with sc1:
    if st.button("PLAYER ชนะ", use_container_width=True):
        st.session_state.history.append('P')
        st.session_state.spreads.append(random.choice([1, 2, 3, 4, 5]))
        st.rerun()
with sc2:
    if st.button("BANKER ชนะ", use_container_width=True):
        st.session_state.history.append('B')
        st.session_state.spreads.append(random.choice([1, 2, 3, 4, 5]))
        st.rerun()
with sc3:
    if st.button("TIE เสมอ", use_container_width=True):
        st.session_state.history.append('T')
        st.rerun()

t1, t2, t3 = st.columns(3)
with t1:
    if st.button("↩ ย้อนกลับ", use_container_width=True) and st.session_state.history:
        st.session_state.history.pop()
        if st.session_state.spreads: st.session_state.spreads.pop()
        st.rerun()
with t2:
    if st.button("🗑️ ล้างขอน", use_container_width=True):
        st.session_state.history, st.session_state.spreads = [], []
        st.session_state.card_counts = {i: 0 for i in range(10)}
        st.session_state.total_cards = 0
        st.rerun()
with t3:
    if st.button("💾 บันทึกขอน", use_container_width=True) and len(st.session_state.history) >= min_rounds:
        curr_step, w1, w2, w3, w4, w5, w6, w7, w8, losses_val, _, acc_rate, _ = evaluate_martingale_8steps(st.session_state.history, base_threshold, min_rounds)
        st.session_state.shoe_logs.append({"ขอน": f"#{st.session_state.shoe_count}", "ตา": len(st.session_state.history), "แม่นยำ": f"{acc_rate:.1f}%", "แตก": losses_val})
        st.session_state.shoe_count += 1
        st.session_state.history, st.session_state.spreads = [], []
        st.session_state.card_counts = {i: 0 for i in range(10)}
        st.session_state.total_cards = 0
        st.rerun()

if st.session_state.history:
    st.caption(f"**สถิติขอนปัจจุบัน ({len(st.session_state.history)} ตา):** " + " ".join(st.session_state.history[-12:]))

st.divider()

curr_step, w1, w2, w3, w4, w5, w6, w7, w8, losses, detailed_logs, accuracy_rate, total_signals = evaluate_martingale_8steps(st.session_state.history, base_threshold, min_rounds)
st.markdown(f'<div class="step-badge">สถานะเดินเงิน: ไม้ที่ {curr_step}</div>', unsafe_allow_html=True)

if total_signals > 0:
    st.markdown(f'<div class="feedback-card">วิเคราะห์ {total_signals} ตา | ความแม่นยำ: <b>{accuracy_rate:.1f}%</b></div>', unsafe_allow_html=True)

res = analyze_engine(st.session_state.history, base_threshold, min_rounds)
if res:
    if res["pat_name"]: st.success(f"🎯 เค้าไพ่พิเศษ: {res['pat_name']}")
    if res["is_fusion"]: st.markdown('<div class="kelly-card">🔥 Matrix Fusion ตรงกัน 100%</div>', unsafe_allow_html=True)
    if res["action"] == "BANKER": st.error(f"### 🛑 ฟันธง: BANKER ({res['conf_b']:.1f}%)")
    elif res["action"] == "PLAYER": st.info(f"### 🔵 ฟันธง: PLAYER ({res['conf_p']:.1f}%)")
    else: st.warning("### ⏳ หลบเลี่ยง (SKIP) - รอจังหวะสวยๆ")

    m1, m2 = st.columns(2)
    with m1: st.metric("Player Prob", f"{res['conf_p']:.1f}%")
    with m2: st.metric("Banker Prob", f"{res['conf_b']:.1f}%")
else:
    st.info(f"⏳ กำลังสะสมข้อมูล: {len([x for x in st.session_state.history if x in ['B','P']])}/{min_rounds} ตา")

st.divider()
st.write("**📈 สถิติการเข้าไม้:**")
cols_stat = st.columns(4)
cols_stat[0].metric("ไม้ 1", f"{w1}")
cols_stat[1].metric("ไม้ 2", f"{w2}")
cols_stat[2].metric("ไม้ 3", f"{w3}")
cols_stat[3].metric("ไม้ 4", f"{w4}")

cols_stat2 = st.columns(5)
cols_stat2[0].metric("ไม้ 5", f"{w5}")
cols_stat2[1].metric("ไม้ 6", f"{w6}")
cols_stat2[2].metric("ไม้ 7", f"{w7}")
cols_stat2[3].metric("ไม้ 8", f"{w8}")
cols_stat2[4].metric("แตก", f"{losses}")

if st.session_state.shoe_logs:
    st.markdown("### 📚 ประวัติย้อนหลัง")
    st.dataframe(pd.DataFrame(st.session_state.shoe_logs), use_container_width=True)

if detailed_logs:
    st.markdown("### 📋 ประวัติรายตา")
    st.dataframe(pd.DataFrame(detailed_logs), use_container_width=True)

st.markdown('<div class="warning-banner">โปรแกรมเพื่อการวิจัยทางสถิติเท่านั้น</div>', unsafe_allow_html=True)
        
