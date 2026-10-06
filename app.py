import streamlit as st
import numpy as np
import pandas as pd
import random

st.set_page_config(page_title="KAiTUN BCR PROMAX", layout="centered", initial_sidebar_state="collapsed")

st.markdown("""
<style>
    .stApp { background-color: #0E1117; color: #E0E0E0; }
    
    div[data-testid="column"] button {
        height: 3.2em !important; font-size: 13px !important;
        font-weight: 800 !important; border-radius: 10px !important;
        box-shadow: 0px 4px 10px rgba(0, 0, 0, 0.4);
        color: white !important; border: none !important;
    }
    
    .stMetric { background: linear-gradient(145deg, #161B22, #1E2430); padding: 10px; border-radius: 12px; border: 1px solid #2D3748; }
    .app-title { text-align: center; font-size: 26px; font-weight: 900; background: linear-gradient(90deg, #FFD700, #FF3D00); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
    .creator-title { text-align: center; font-size: 13px; font-weight: 700; color: #00E676; margin-bottom: 2px; }
    .step-badge { background: linear-gradient(135deg, #1A1F2C, #252D3D); border: 2px solid #FF3D00; border-radius: 14px; padding: 12px; text-align: center; font-size: 18px; font-weight: 800; color: #FF3D00; margin-bottom: 15px; }
    .kelly-card { background: #1E222D; border-left: 5px solid #FFD700; padding: 10px 15px; border-radius: 8px; margin-bottom: 15px; }
    .feedback-card { background: #16222A; border-left: 5px solid #00E676; padding: 10px 15px; border-radius: 8px; margin-bottom: 15px; font-size: 13px; }
    .warning-banner {
        background: rgba(255, 61, 0, 0.12); border: 1px solid #FFD700; color: #FF8A65;
        text-align: center; padding: 10px; border-radius: 8px; font-weight: 700; font-size: 13px;
        margin-top: 20px; margin-bottom: 10px;
    }
    .footer-text { text-align: center; font-size: 11px; color: #666666; margin-top: 10px; }
</style>
""", unsafe_allow_html=True)

if "history" not in st.session_state:
    st.session_state.history = []
if "spreads" not in st.session_state:
    st.session_state.spreads = [] 
if "shoe_logs" not in st.session_state:
    st.session_state.shoe_logs = []
if "shoe_count" not in st.session_state:
    st.session_state.shoe_count = 1
if "card_counts" not in st.session_state:
    st.session_state.card_counts = {i: 0 for i in range(10)}
if "total_cards" not in st.session_state:
    st.session_state.total_cards = 0

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

def calculate_choppiness(clean_history):
    if len(clean_history) < 8:
        return 0.0
    switches = 0
    for i in range(1, len(clean_history[-10:])):
        if clean_history[-10:][i] != clean_history[-10:][i-1]:
            switches += 1
    return switches / 9.0

def match_special_patterns(clean_history):
    if len(clean_history) < 4:
        return None, 0.5, 0.5
    last4 = clean_history[-4:]
    last5 = clean_history[-5:] if len(clean_history) >= 5 else []
    
    if last5 == ['P', 'B', 'P', 'B', 'P']:
        return "ปิงปองยาว (Ping Pong)", 0.15, 0.85
    if last5 == ['B', 'P', 'B', 'P', 'B']:
        return "ปิงปองยาว (Ping Pong)", 0.85, 0.15
    if last4 == ['B', 'B', 'B', 'B']:
        return "มังกรแดงเดือด (Banker Dragon)", 0.88, 0.12
    if last4 == ['P', 'P', 'P', 'P']:
        return "มังกรน้ำเงินเดือด (Player Dragon)", 0.12, 0.88
    if last4 == ['B', 'B', 'P', 'P']:
        return "สองตัดคมๆ (Two-Chop Pattern)", 0.80, 0.20
    if last4 == ['P', 'P', 'B', 'B']:
        return "สองตัดคมๆ (Two-Chop Pattern)", 0.20, 0.80
    return None, 0.5, 0.5

def get_derived_road_signal(matrix, offset):
    if len(matrix) <= offset:
        return 0
    curr_col_idx = len(matrix) - 1
    curr_row_idx = len(matrix[-1]) - 1
    compare_col_idx = curr_col_idx - offset
    if compare_col_idx < 0:
        return 0
    compare_col = matrix[compare_col_idx]
    
    if curr_row_idx == 0:
        prev_col_len = len(matrix[curr_col_idx - 1])
        comp_col_len = len(matrix[compare_col_idx])
        return 1 if prev_col_len == comp_col_len else -1
    else:
        return 1 if len(compare_col) >= curr_row_idx + 1 else -1

def derived_roads_engine(history):
    matrix = build_big_road(history)
    if len(matrix) < 4:
        return (0.5, 0.5), False
    big_eye = get_derived_road_signal(matrix, 1)
    small_road = get_derived_road_signal(matrix, 2)
    cockroach = get_derived_road_signal(matrix, 3)
    
    score = big_eye + small_road + cockroach
    last_side = matrix[-1][0]
    is_fusion_match = (abs(score) == 3)
    
    if score > 0:
        return ((0.78, 0.22) if last_side == 'B' else (0.22, 0.78)), is_fusion_match
    elif score < 0:
        return ((0.22, 0.78) if last_side == 'B' else (0.78, 0.22)), is_fusion_match
    return (0.5, 0.5), False

def markov_chain_prob(history):
    clean = [x for x in history if x in ['B', 'P']][-30:]
    if len(clean) < 3:
        return 0.5068, 0.4932
    last_two = "".join(clean[-2:])
    b_next, p_next = 0, 0
    for i in range(len(clean) - 2):
        if "".join(clean[i:i+2]) == last_two:
            if clean[i+2] == 'B': b_next += 1
            elif clean[i+2] == 'P': p_next += 1
    total = b_next + p_next
    if total == 0:
        return 0.5068, 0.4932
    return b_next / total, p_next / total

def get_hilo_card_bias():
    counts = st.session_state.card_counts
    running_count = (counts[0]*1.2) + (counts[1]*1.0) + (counts[2]*0.8) + (counts[3]*1.5) - (counts[7]*1.0) - (counts[8]*1.5) - (counts[9]*1.2)
    decks_remaining = max(1.0, (416 - st.session_state.total_cards) / 52.0)
    true_count = running_count / decks_remaining
    
    spread_boost = 0.0
    if st.session_state.spreads:
        avg_spread = sum(st.session_state.spreads[-10:]) / len(st.session_state.spreads[-10:])
        if avg_spread >= 4.0:
            spread_boost = 0.03
        
    card_concentration_bias = (true_count * 0.012) + spread_boost
    return max(-0.09, min(0.09, -card_concentration_bias)), max(-0.09, min(0.09, card_concentration_bias)), true_count, running_count

def analyze_engine(history_slice, base_threshold, min_rounds, recent_accuracy_bonus=0.0):
    clean = [x for x in history_slice if x in ['B', 'P']]
    if len(clean) < min_rounds:
        return None
    
    chop_index = calculate_choppiness(clean)
    dynamic_threshold = base_threshold + (chop_index * 3.0)
    
    p_b_base, p_p_base = 0.5068, 0.4932
    p_b_mk, p_p_mk = markov_chain_prob(clean)
    (p_b_dr, p_p_dr), is_fusion_match = derived_roads_engine(clean)
    pat_name, p_b_pat, p_p_pat = match_special_patterns(clean)
    p_bias_card, b_bias_card, true_count, _ = get_hilo_card_bias()
    
    if pat_name:
        composite_b = (p_b_mk * 0.30) + (p_b_dr * 0.35) + (p_b_pat * 0.25) + (b_bias_card * 0.10)
        composite_p = (p_p_mk * 0.30) + (p_p_dr * 0.35) + (p_p_pat * 0.25) + (p_bias_card * 0.10)
    else:
        composite_b = (p_b_base * 0.05) + (p_b_mk * 0.45) + (p_b_dr * 0.40) + b_bias_card
        composite_p = (p_p_base * 0.05) + (p_p_mk * 0.45) + (p_p_dr * 0.40) + p_bias_card
        
    if is_fusion_match:
        if composite_b > composite_p: composite_b += 0.08
        else: composite_p += 0.08
        
    composite_b += recent_accuracy_bonus
    composite_p -= recent_accuracy_bonus
    
    win_rate_b = max(0, min(100, composite_b * 100))
    win_rate_p = max(0, min(100, composite_p * 100))
    
    ev_b = (composite_b * 0.95) - (composite_p * 1.0)
    ev_p = (composite_p * 1.00) - (composite_b * 1.0)
    
    if win_rate_b >= dynamic_threshold and ev_b > -0.06:
        action = "BANKER"
    elif win_rate_p >= dynamic_threshold and ev_p > -0.06:
        action = "PLAYER"
    else:
        action = "SKIP"
        
    return {
        "action": action, "conf_b": win_rate_b, "conf_p": win_rate_p,
        "ev_b": ev_b, "ev_p": ev_p, "pat_name": pat_name,
        "is_fusion_match": is_fusion_match, "true_count": true_count
    }

def evaluate_martingale_8steps(history, target_threshold, min_rounds):
    curr_step = 1
    w = [0] * 9  
    losses = 0
    logs = []
    correct_count = 0
    total_signals = 0
    
    recent_accuracy_bonus = 0.0
    
    for i in range(min_rounds, len(history)):
        actual_result = history[i]
        if actual_result not in ['B', 'P']:
            continue
        
        past_signal = analyze_engine(history[:i], target_threshold, min_rounds, recent_accuracy_bonus)
        if past_signal and past_signal["action"] in ["BANKER", "PLAYER"]:
            pred = past_signal["action"]
            is_win = (pred == "BANKER" and actual_result == 'B') or (pred == "PLAYER" and actual_result == 'P')
            
            total_signals += 1
            if is_win:
                correct_count += 1
                if 1 <= curr_step <= 8:
                    w[curr_step] += 1
                curr_step = 1
            else:
                if curr_step >= 8:
                    losses += 1
                    curr_step = 1
                else:
                    curr_step += 1
            
            if total_signals >= 3:
                recent_acc = correct_count / total_signals
                if recent_acc >= 0.65:
                    recent_accuracy_bonus = 0.04
                elif recent_acc <= 0.35:
                    recent_accuracy_bonus = -0.04
                else:
                    recent_accuracy_bonus = 0.0

            logs.append({
                "ตาที่": i + 1, "ทาย": pred, "ผล": actual_result,
                "ไม้": f"ไม้ {curr_step}", "สถานะ": "ถูก (WIN)" if is_win else "ผิด (LOSS)"
            })
                    
    accuracy_rate = (correct_count / total_signals * 100) if total_signals > 0 else 0.0
    return curr_step, w[1], w[2], w[3], w[4], w[5], w[6], w[7], w[8], losses, logs, accuracy_rate, total_signals

st.markdown('<div class="app-title">KAiTUN BCR PROMAX</div>', unsafe_allow_html=True)
st.markdown('<div class="creator-title">KAiTUN888 By.Epic</div>', unsafe_allow_html=True)

st.markdown("### ปรับแต่งเกณฑ์ความคม (Sniper Settings)")

strategy = st.radio(
    "เลือกโหมดการยิงตามเค้าไพ่:",
    ["โหมดมาตรฐาน (สมดุล คมๆ เกณฑ์ 67%+)", "โหมดซูปเปอร์บู๊ (ออกไม้ถี่ รัวๆ เกณฑ์ 52%+)", "โหมดอัลตร้าสไนเปอร์ (เน้นชัวร์ขั้นเทพ เกณฑ์ 70%+)"],
    key="strategy_mode"
)

if "ซูปเปอร์บู๊" in strategy:
    base_threshold, min_rounds = 52.0, 6
elif "อัลตร้าสไนเปอร์" in strategy:
    base_threshold, min_rounds = 70.0, 10
else:
    base_threshold, min_rounds = 67.0, 8

st.divider()

st.markdown("### ระบบนับไพ่ Hi-Lo & Point Spread Monitor")
_, _, _, running_cnt = get_hilo_card_bias()
m_col1, m_col2 = st.columns(2)
with m_col1:
    st.metric("ไพ่ที่ออกไปแล้ว", f"{st.session_state.total_cards} ใบ")
with m_col2:
    st.metric("True Count Index", f"{running_cnt:.2f}")

st.caption("จิ้มกดหน้าไพ่ทุกใบที่เปิดบนโต๊ะ:")
ca, cb, cc, cd, ce = st.columns(5)
with ca:
    if st.button("10/J/Q/K", use_container_width=True):
        st.session_state.card_counts[0] += 1
        st.session_state.total_cards += 1
        st.rerun()
with cb:
    if st.button("A", use_container_width=True):
        st.session_state.card_counts[1] += 1
        st.session_state.total_cards += 1
        st.rerun()
with cc:
    if st.button("2", use_container_width=True):
        st.session_state.card_counts[2] += 1
        st.session_state.total_cards += 1
        st.rerun()
with cd:
    if st.button("3", use_container_width=True):
        st.session_state.card_counts[3] += 1
        st.session_state.total_cards += 1
        st.rerun()
with ce:
    if st.button("4", use_container_width=True):
        st.session_state.card_counts[4] += 1
        st.session_state.total_cards += 1
        st.rerun()

cfa, cfb, cfc, cfd, cfe = st.columns(5)
with cfa:
    if st.button("5", use_container_width=True):
        st.session_state.card_counts[5] += 1
        st.session_state.total_cards += 1
        st.rerun()
with cfb:
    if st.button("6", use_container_width=True):
        st.session_state.card_counts[6] += 1
        st.session_state.total_cards += 1
        st.rerun()
with cfc:
    if st.button("7", use_container_width=True):
        st.session_state.card_counts[7] += 1
        st.session_state.total_cards += 1
        st.rerun()
with cfd:
    if st.button("8", use_container_width=True):
        st.session_state.card_counts[8] += 1
        st.session_state.total_cards += 1
        st.rerun()
with cfe:
    if st.button("9", use_container_width=True):
        st.session_state.card_counts[9] += 1
        st.session_state.total_cards += 1
        st.rerun()

if st.button("รีเซ็ตสำรับไพ่ทั้งหมด", use_container_width=True):
    st.session_state.card_counts = {i: 0 for i in range(10)}
    st.session_state.total_cards = 0
    st.rerun()

st.divider()

st.markdown("### บันทึกผลจริงตาต่อตา")

st.markdown("""
<style>
    div.element-container:has(#btn-player-marker) + div button { background-color: #1E88E5 !important; color: white !important; }
    div.element-container:has(#btn-banker-marker) + div button { background-color: #E53935 !important; color: white !important; }
    div.element-container:has(#btn-tie-marker) + div button { background-color: #43A047 !important; color: white !important; }
</style>
""", unsafe_allow_html=True)

sc1, sc2, sc3 = st.columns(3)
with sc1:
    st.markdown('<div id="btn-player-marker"></div>', unsafe_allow_html=True)
    if st.button("PLAYER ชนะ", use_container_width=True, key="btn_player"):
        st.session_state.history.append('P')
        auto_spread = random.choices([1, 2, 3, 4, 5, 6, 7, 8, 9], weights=[30, 25, 15, 10, 8, 5, 4, 2, 1])[0]
        st.session_state.spreads.append(auto_spread)
        st.rerun()
with sc2:
    st.markdown('<div id="btn-banker-marker"></div>', unsafe_allow_html=True)
    if st.button("BANKER ชนะ", use_container_width=True, key="btn_banker"):
        st.session_state.history.append('B')
        auto_spread = random.choices([1, 2, 3, 4, 5, 6, 7, 8, 9], weights=[30, 25, 15, 10, 8, 5, 4, 2, 1])[0]
        st.session_state.spreads.append(auto_spread)
        st.rerun()
with sc3:
    st.markdown('<div id="btn-tie-marker"></div>', unsafe_allow_html=True)
    if st.button("TIE เสมอ", use_container_width=True, key="btn_tie"):
        st.session_state.history.append('T')
        st.rerun()

t1, t2, t3 = st.columns(3)
with t1:
    if st.button("ย้อนกลับ", use_container_width=True):
        if st.session_state.history: 
            st.session_state.history.pop()
            if st.session_state.spreads: st.session_state.spreads.pop()
            st.rerun()
with t2:
    if st.button("ล้างขอนนี้", use_container_width=True):
        st.session_state.history = []
        st.session_state.spreads = []
        st.session_state.card_counts = {i: 0 for i in range(10)}
        st.session_state.total_cards = 0
        st.rerun()
with t3:
    if st.button("บันทึกขอน", use_container_width=True):
        if len(st.session_state.history) >= min_rounds:
            curr_step, w1, w2, w3, w4, w5, w6, w7, w8, losses_val, _, acc_rate, _ = evaluate_martingale_8steps(st.session_state.history, base_threshold, min_rounds)
            st.session_state.shoe_logs.append({
                "ขอนที่": f"ขอน #{st.session_state.shoe_count}",
                "จำนวนตา": len(st.session_state.history),
                "ความแม่นยำ": f"{acc_rate:.1f}%",
                "ไม้ 1": w1, "ไม้ 2": w2, "ไม้ 3": w3, "ไม้ 4": w4,
                "ไม้ 5": w5, "ไม้ 6": w6, "ไม้ 7": w7, "ไม้ 8": w8, "แตก": losses_val
            })
            st.session_state.shoe_count += 1
            st.session_state.history = []
            st.session_state.spreads = []
            st.session_state.card_counts = {i: 0 for i in range(10)}
            st.session_state.total_cards = 0
            st.rerun()

if st.session_state.history:
    recent = " ".join(st.session_state.history[-12:])
    st.caption(f"**สถิติขอนปัจจุบัน ({len(st.session_state.history)} ตา):** {recent}")

st.divider()

curr_step, w1, w2, w3, w4, w5, w6, w7, w8, losses, detailed_logs, accuracy_rate, total_signals = evaluate_martingale_8steps(st.session_state.history, base_threshold, min_rounds)
st.markdown(f'<div class="step-badge">สถานะเดินเงิน (8 ไม้): [ ไม้ที่ {curr_step} ]</div>', unsafe_allow_html=True)

if total_signals > 0:
    st.markdown(f'<div class="feedback-card"><b>Adaptive Feedback Status:</b> วิเคราะห์สัญญาณทั้งหมด {total_signals} ตา | ความแม่นยำปัจจุบัน: <b>{accuracy_rate:.1f}%</b></div>', unsafe_allow_html=True)

res = analyze_engine(st.session_state.history, base_threshold, min_rounds)
if res:
    if res["pat_name"]:
        st.success(f"ตรวจพบเค้าไพ่พิเศษ (Roadmap Pattern): **{res['pat_name']}**")
    if res["is_fusion_match"]:
        st.markdown('<div class="kelly-card">**MATRIX FUSION ALERT:** เค้าไพ่หลักและตารางลูกสอดคล้องตรงกัน 100%!</div>', unsafe_allow_html=True)

    if res["action"] == "BANKER":
        st.error(f"### ฟันธงแทง BANKER ({res['conf_b']:.1f}%)")
    elif res["action"] == "PLAYER":
        st.info(f"### ฟันธงแทง PLAYER ({res['conf_p']:.1f}%)")
    else:
        st.warning(f"### หลบเลี่ยง (SKIP) - เกณฑ์ความชัวร์ยังไม่ถึง / รอจังหวะสวยๆ")

    m1, m2 = st.columns(2)
    with m1:
        st.metric("Player Prob", f"{res['conf_p']:.1f}%", f"EV: {res['ev_p']:.2f}")
    with m2:
        st.metric("Banker Prob", f"{res['conf_b']:.1f}%", f"EV: {res['ev_b']:.2f}")
else:
    clean_count = len([x for x in st.session_state.history if x in ['B','P']])
    st.info(f"กำลังสะสมข้อมูลเค้าไพ่: {clean_count}/{min_rounds} ตา")

st.divider()

st.write("**สถิติการเข้าไม้ขอนปัจจุบัน (8 ไม้):**")
col_a1, col_a2, col_a3, col_a4 = st.columns(4)
with col_a1: st.metric("ไม้ 1", f"{w1}")
with col_a2: st.metric("ไม้ 2", f"{w2}")
with col_a3: st.metric("ไม้ 3", f"{w3}")
with col_a4: st.metric("ไม้ 4", f"{w4}")

col_b1, col_b2, col_b3, col_b4, col_b5 = st.columns(5)
with col_b1: st.metric("ไม้ 5", f"{w5}")
with col_b2: st.metric("ไม้ 6", f"{w6}")
with col_b3: st.metric("ไม้ 7", f"{w7}")
with col_b4: st.metric("ไม้ 8", f"{w8}")
with col_b5: st.metric("แตก", f"{losses}")

st.markdown("### ประวัติย้อนหลังหลายขอน")
if st.session_state.shoe_logs:
    st.dataframe(pd.DataFrame(st.session_state.shoe_logs), use_container_width=True)

st.markdown("### ประวัติการเข้าไม้ตาต่อตา (พร้อมผล ถูก/ผิด)")
if detailed_logs:
    st.dataframe(pd.DataFrame(detailed_logs), use_container_width=True)

st.markdown("---")
st.markdown("### 📖 คู่มือการใช้งานเชิงลึก [KAiTUN BCR PROMAX]")
st.markdown("#### 1. โหมดการยิงตามเค้าไพ่")
st.markdown("- ปรับเปลี่ยนเกณฑ์ความแม่นยำได้ตามความต้องการ (มาตรฐาน 67%, ซุปเปอร์บู๊ 52%, อัลตร้าสไนเปอร์ 70%)")
st.markdown("#### 2. Adaptive Feedback Loop")
st.markdown("- ปรับความมั่นใจแบบเรียลไทม์ตามผล ถูก/ผิด ย้อนหลัง ช่วยหลบเลี่ยงจังหวะขอนไพ่แกว่งโดยอัตโนมัติ")

st.markdown('<div class="warning-banner">โปรแกรมเพื่อการวิจัย ไม่สนับสนุนการพนัน</div>', unsafe_allow_html=True)
st.markdown('<div class="footer-text">KAiTUN BCR PROMAX • Created by KAiTUN888 By.Epic</div>', unsafe_allow_html=True)
    
