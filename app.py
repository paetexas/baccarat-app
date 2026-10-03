import streamlit as st

# 1. กำหนด Session State สำหรับสะสมจำนวนไพ่ที่รู้ออกไปแล้วในขอนนี้
if "count_4" not in st.session_state:
    st.session_state.count_4 = 0  # จำนวนไพ่แต้ม 4 ที่ใช้ออกไป
if "count_high" not in st.session_state:
    st.session_state.count_high = 0  # จำนวนไพ่หน้าใหญ่/ป๊อก ที่ใช้ออกไป
if "total_cards_dealt" not in st.session_state:
    st.session_state.total_cards_dealt = 0  # จำนวนไพ่โดยประมาณที่เปิดไปแล้ว

# 2. ส่วนคำนวณ ค่าน้ำหนักความน่าจะเป็น (Bias Indicator)
def calculate_card_counting_bias():
    # อ้างอิงไพ่ 8 สำรับ (416 ใบ)
    # ไพ่แต้ม 4 ออกเยอะ -> Banker ได้เปรียบ (+0.12% ต่อใบ)
    # ไพ่หน้าใหญ่ออกเยอะ -> Player ได้เปรียบ (+0.08% ต่อใบ)
    banker_bias = (st.session_state.count_4 * 0.12) - (
        st.session_state.count_high * 0.05
    )
    player_bias = (st.session_state.count_high * 0.08) - (
        st.session_state.count_4 * 0.08
    )

    return player_bias, banker_bias


# 3. หน้าตา UI ปุ่มกดแบบง่าย
st.subheader("🃏 ตัวช่วยนับไพ่ในขอน (Card Counter)")
col1, col2, col3 = st.columns(3)

with col1:
    if st.button("🃏 เห็นไพ่เลข 4 (+1)"):
        st.session_state.count_4 += 1
        st.session_state.total_cards_dealt += 1

with col2:
    if st.button("👑 เห็นหน้าใหญ่/9 (+1)"):
        st.session_state.count_high += 1
        st.session_state.total_cards_dealt += 1

with col3:
    if st.button("🔄 รีเซ็ตขอนใหม่"):
        st.session_state.count_4 = 0
        st.session_state.count_high = 0
        st.session_state.total_cards_dealt = 0

# แสดงผล Bias ให้ผู้ใช้เห็น
p_bias, b_bias = calculate_card_counting_bias()
if b_bias > 0.3:
    st.info(f"💡 ไพ่เลข 4 ออกไปแล้ว {st.session_state.count_4} ใบ ➔ **ขอนนี้ดัน Banker ขึ้น (+{b_bias:.2f}%)**")
elif p_bias > 0.3:
    st.info(f"💡 ไพ่หน้าใหญ่ออกไปแล้ว {st.session_state.count_high} ใบ ➔ **ขอนนี้ดัน Player ขึ้น (+{p_bias:.2f}%)**")
    
