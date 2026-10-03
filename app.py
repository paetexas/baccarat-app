import streamlit as st
import numpy as np
import pandas as pd

st.set_page_config(page_title="BAR Rich BAR Pro Elite", layout="centered", initial_sidebar_state="collapsed")

st.markdown("""
<style>
    .stApp { background-color: #0E1117; color: #E0E0E0; }
    div[data-testid="column"] button {
        height: 3.2em !important; font-size: 13px !important;
        font-weight: 800 !important; border-radius: 10px !important;
        box-shadow: 0px 4px 10px rgba(0, 0, 0, 0.4);
    }
    .stMetric { background: linear-gradient(145deg, #161B22, #1E2430); padding: 10px; border-radius: 12px; border: 1px solid #2D3748; }
    .app-title { text-align: center; font-size: 26px; font-weight: 900; background: linear-gradient(90deg, #FFD700, #FF3D00); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
    .creator-title { text-align: center; font-size: 13px; font-weight: 700; color: #00E676; margin-bottom: 2px; }
    .step-badge { background: linear-gradient(135deg, #1A1F2C, #252D3D); border: 2px solid #FF3D00; border-radius: 14px; padding: 12px; text-align: center; font-size: 18px; font-weight: 800; color: #FF3D00; margin-bottom: 15px; }
    .kelly-card { background: #1E222D; border-left: 5px solid #FFD700; padding: 10px 15px; border-radius: 8px; margin-bottom: 15px; }
    .pinned-guide {
        background: linear-gradient(145deg, #161B22, #1A1F2C);
        border: 2px solid #FFD700;
        border-radius: 14px;
        padding: 18px;
        margin-top: 30px;
        margin-bottom: 15px;
        box-shadow: 0px 4px 15px rgba(255, 215, 0, 0.15);
    }
    .pinned-guide h4 { color: #FFD700; margin-top: 0; margin-bottom: 10px; font-weight: 900; }
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
        return "ปิงปองยาว", 0.15, 0.85
    if last5 == ['B', 'P', 'B', 'P', 'B']:
        return "ปิงปองยาว", 0.85, 0.15
    if last4 == ['B', 'B', 'B', 'B']:
        return "มังกรแดงเดือด", 0.88, 0.12
    if last4 == ['P', 'P', 'P', 'P']:
        return "มังกรน้ำเงินเดือด", 0.12, 0.88
    if last4 == ['B', 'B', 'P', 'P']:
        return "สองตัดคมๆ", 0.80, 0.20
    if last4 == ['P', 'P', 'B', 'B']:
        return "สองตัดคมๆ", 0.20, 0.80
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

def analyze_engine(history_slice, base_threshold, min_rounds):
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
                "ตาที่": i + 1, "ทาย": pred, "ผล": actual_result,
                "ไม้": f"ไม้ {curr_step}", "สถานะ": "ชนะ" if is_win else "ผิด"
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

st.markdown('<div class="app-title">BAR Rich BAR Pro Elite [SNIPER V2]</div>', unsafe_allow_html=True)
st.markdown('<div class="creator-title">KAiTUN888 By.Epic</div>', unsafe_allow_html=True)

st.markdown("### ปรับแต่งเกณฑ์ความคม (Sniper Settings)")
strategy = st.selectbox(
    "เลือกโหมดการยิง:",
    ["โหมดมาตรฐาน (สมดุล คมๆ เกณฑ์ 57%+)", "โหมดซูปเปอร์บู๊ (ออกไม้ถี่ รัวๆ เกณฑ์ 52%+)", "โหมดสไนเปอร์ (เน้นชัวร์ๆ เกณฑ์ 62%+)"],
    index=0
)
if "ซูปเปอร์บู๊" in strategy:
    base_threshold, min_rounds = 52.0, 6
elif "สไนเปอร์" in strategy:
    base_threshold, min_rounds = 62.0, 8
else:
    base_threshold, min_rounds = 57.0, 8

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
sc1, sc2, sc3 = st.columns(3)
with sc1:
    if st.button("PLAYER ชนะ", use_container_width=True):
        st.session_state.history.append('P')
        st.session_state.spreads.append(2)
        st.rerun()
with sc2:
    if st.button("BANKER ชนะ", use_container_width=True):
        st.session_state.history.append('B')
        st.session_state.spreads.append(2)
        st.rerun()
with sc3:
    if st.button("TIE เสมอ", use_container_width=True):
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
            curr_step, w1_val, w2_val, w3_val, w4_val, losses_val, _ = evaluate_martingale_4steps(st.session_state.history, base_threshold, min_rounds)
            st.session_state.shoe_logs.append({
                "ขอนที่": f"ขอน #{st.session_state.shoe_count}",
                "จำนวนตา": len(st.session_state.history),
                "ไม้ 1": w1_val, "ไม้ 2": w2_val, "ไม้ 3": w3_val, "ไม้ 4": w4_val, "แตก": losses_val
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

curr_step, w1, w2, w3, w4, losses, detailed_logs = evaluate_martingale_4steps(st.session_state.history, base_threshold, min_rounds)
st.markdown(f'<div class="step-badge">สถานะเดินเงิน: [ ไม้ที่ {curr_step} ]</div>', unsafe_allow_html=True)

res = analyze_engine(st.session_state.history, base_threshold, min_rounds)
if res:
    if res["pat_name"]:
        st.success(f"ตรวจพบเค้าไพ่พิเศษ: **{res['pat_name']}**")
    if res["is_fusion_match"]:
        st.markdown('<div class="kelly-card">**MATRIX FUSION ALERT:** ตารางหลักและตารางลูกพุ่งตรงกัน!</div>', unsafe_allow_html=True)

    if res["action"] == "BANKER":
        st.error(f"### ฟันธงแทง BANKER ({res['conf_b']:.1f}%)")
    elif res["action"] == "PLAYER":
        st.info(f"### ฟันธงแทง PLAYER ({res['conf_p']:.1f}%)")
    else:
        st.warning(f"### หลบเลี่ยง (SKIP) - รอจังหวะคมๆ")

    m1, m2 = st.columns(2)
    with m1:
        st.metric("Player Prob", f"{res['conf_p']:.1f}%", f"EV: {res['ev_p']:.2f}")
    with m2:
        st.metric("Banker Prob", f"{res['conf_b']:.1f}%", f"EV: {res['ev_b']:.2f}")
else:
    clean_count = len([x for x in st.session_state.history if x in ['B','P']])
    st.info(f"กำลังสะสมข้อมูล: {clean_count}/{min_rounds} ตา")

st.divider()

st.write("**สถิติการเข้าไม้ขอนปัจจุบัน:**")
s1, s2, s3, s4, s5 = st.columns(5)
with s1: st.metric("ไม้ 1", f"{w1}")
with s2: st.metric("ไม้ 2", f"{w2}")
with s3: st.metric("ไม้ 3", f"{w3}")
with s4: st.metric("ไม้ 4", f"{w4}")
with s5: st.metric("แตก", f"{losses}")

st.markdown("### ประวัติย้อนหลังหลายขอน")
if st.session_state.shoe_logs:
    st.dataframe(pd.DataFrame(st.session_state.shoe_logs), use_container_width=True)

st.markdown("### ประวัติการเข้าไม้ตาต่อตา")
if detailed_logs:
    st.dataframe(pd.DataFrame(detailed_logs), use_container_width=True)

# ---------------- PINNED GUIDE AT THE BOTTOM ----------------
st.markdown("""
<div class="pinned-guide">
    <h4>คู่มือการใช้งานระบบ [BAR Rich BAR Pro Elite]</h4>
    <ol style="margin: 0; padding-left: 20px; line-height: 1.6; font-size: 14px;">
        <li><b>บันทึกผลจริง:</b> กดปุ่ม <b>PLAYER ชนะ</b> หรือ <b>BANKER ชนะ</b> ทันทีเมื่อทราบผล ระบบจะบันทึกและประมวลผลให้อัตโนมัติ</li>
        <li><b>นับไพ่เสริมความแม่นยำ:</b> สามารถจิ้มเลือกหน้าไพ่ที่เปิดบนโต๊ะด้านบนเพื่อช่วยคำนวณความน่าจะเป็นเพิ่มเติมได้</li>
        <li><b>ลุยตามสัญญาณ AI:</b> รอสัญญาณฟันธงและทำตามสถานะการเดินเงินที่ระบบแนะนำเพื่อทำกำไร</li>
    </ol>
</div>
""", unsafe_allow_html=True)

st.markdown('<div class="warning-banner">โปรแกรมเพื่อการวิจัย ไม่สนับสนุนการพนัน</div>', unsafe_allow_html=True)
st.markdown('<div class="footer-text">BAR Rich BAR Pro Elite Sniper V2 • Created by KAiTUN888 By.Epic</div>', unsafe_allow_html=True)
        
