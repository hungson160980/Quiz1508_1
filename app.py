import streamlit as st
import pandas as pd
import io
import time
from datetime import datetime

st.set_page_config(page_title="Quiz Streamlit", layout="wide")

# Helper to normalize column names
def normalize_cols(df):
    df = df.copy()
    cols = {c: c.strip().upper() for c in df.columns}
    df.rename(columns=cols, inplace=True)
    return df

EXPECTED_COLS = ["STT","CÂU HỎI","ĐÁP ÁN 1","ĐÁP ÁN 2","ĐÁP ÁN 3","ĐÁP ÁN 4","ĐÁP ÁN ĐÚNG"]

if "exams" not in st.session_state:
    st.session_state.exams = {}  # name -> dataframe
if "current_exam" not in st.session_state:
    st.session_state.current_exam = None
if "started" not in st.session_state:
    st.session_state.started = False
if "start_time" not in st.session_state:
    st.session_state.start_time = None
if "answers" not in st.session_state:
    st.session_state.answers = {}  # exam_name -> {index: selected_int}
if "corrects" not in st.session_state:
    st.session_state.corrects = {}  # exam_name -> {index: True/False}
if "index" not in st.session_state:
    st.session_state.index = 0

st.title("Ứng dụng thi trắc nghiệm (Streamlit)")
st.sidebar.header("1) Import dữ liệu (1 lần)")
uploaded = st.sidebar.file_uploader("Chọn file Excel (.xlsx) (có thể chọn nhiều) - mỗi file là 1 môn", type=["xlsx"], accept_multiple_files=True)
if st.sidebar.button("Import các file đã chọn"):
    if not uploaded:
        st.sidebar.warning("Chưa chọn file nào")
    else:
        imported = 0
        for f in uploaded:
            try:
                df = pd.read_excel(f, sheet_name=0)
                df = normalize_cols(df)
                # check columns
                missing = [c for c in EXPECTED_COLS if c not in df.columns]
                name = getattr(f, "name", f"file_{imported+1}")
                if missing:
                    st.sidebar.error(f"File {name} thiếu cột: {missing}. Bỏ qua file này.")
                    continue
                # keep only expected cols in expected order
                df = df[EXPECTED_COLS]
                st.session_state.exams[name] = df.reset_index(drop=True)
                imported += 1
            except Exception as e:
                st.sidebar.error(f"Lỗi khi đọc {getattr(f,'name',str(f))}: {e}")
        st.sidebar.success(f"Đã import {imported} file.")

st.sidebar.markdown("---")
st.sidebar.header("2) Chọn mục thi")
exam_names = list(st.session_state.exams.keys())
selected = st.sidebar.selectbox("Mục thi:", ["-- Chưa có dữ liệu --"] + exam_names) if exam_names else st.sidebar.selectbox("Mục thi:", ["-- Chưa có dữ liệu --"])
if selected and selected != "-- Chưa có dữ liệu --":
    st.session_state.current_exam = selected
else:
    st.session_state.current_exam = None

# Main area
if st.session_state.current_exam is None:
    st.info("Vui lòng import file Excel và chọn một mục thi ở sidebar.")
    st.stop()

df = st.session_state.exams[st.session_state.current_exam]
n_questions = len(df)

col1, col2 = st.columns([2,1])

with col1:
    st.header(f"Mục thi: {st.session_state.current_exam}  —  Số câu: {n_questions}")
with col2:
    st.write(" ")

# Start / control buttons
controls = st.container()
with controls:
    c1, c2, c3, c4 = st.columns(4)
    if c1.button("Bắt đầu thi"):
        # reset
        st.session_state.started = True
        st.session_state.start_time = time.time()
        st.session_state.index = 0
        st.session_state.answers[st.session_state.current_exam] = {}
        st.session_state.corrects[st.session_state.current_exam] = {}
    if c2.button("Quay lại"):
        if st.session_state.index > 0:
            st.session_state.index -= 1
    if c3.button("Kế tiếp"):
        if st.session_state.index < n_questions - 1:
            st.session_state.index += 1
    if c4.button("Kết thúc"):
        st.session_state.started = False
        # compute results
        answers = st.session_state.answers.get(st.session_state.current_exam, {})
        corrects = st.session_state.corrects.get(st.session_state.current_exam, {})
        total = n_questions
        correct_count = sum(1 for v in corrects.values() if v)
        percent = correct_count * 100.0 / total if total > 0 else 0.0
        elapsed = 0.0
        if st.session_state.start_time:
            elapsed = time.time() - st.session_state.start_time
        st.success(f"Bạn đã hoàn thành: {correct_count}/{total} đúng — {percent:.2f}% — Thời gian: {int(elapsed)//60} phút {int(elapsed)%60} giây")

# If not started, show instructions and allow review of previously answered
if not st.session_state.started:
    st.info("Nhấn 'Bắt đầu thi' để bắt đầu. Sau khi bắt đầu, hệ thống sẽ lưu câu trả lời vào bộ nhớ phiên (session). Bạn có thể chuyển câu bằng 'Quay lại' và 'Kế tiếp'.")
    # show last results if any
    if st.session_state.current_exam in st.session_state.corrects and st.session_state.corrects[st.session_state.current_exam]:
        corrects = st.session_state.corrects[st.session_state.current_exam]
        answers = st.session_state.answers.get(st.session_state.current_exam, {})
        total = n_questions
        correct_count = sum(1 for v in corrects.values() if v)
        percent = correct_count * 100.0 / total if total > 0 else 0.0
        st.write(f"---\nKết quả trước: {correct_count}/{total} đúng — {percent:.2f}%")
        if st.button("Hiện danh sách câu trả lời sai"):
            wrongs = [i for i,v in corrects.items() if not v]
            if not wrongs:
                st.write("Không có câu sai. Tốt quá!")
            else:
                for i in wrongs:
                    row = df.iloc[i]
                    selected = st.session_state.answers[st.session_state.current_exam].get(i, None)
                    st.markdown(f"**Câu {row['STT']}**: {row['CÂU HỎI']}")
                    st.write(f"Đáp án bạn chọn: {selected} — Đáp án đúng: {int(row['ĐÁP ÁN ĐÚNG'])}")
    st.stop()

# If started, show current question
idx = st.session_state.index
row = df.iloc[idx]
st.write(f"**Câu {row['STT']} / {n_questions}**")
st.write(row["CÂU HỎI"])

# Display options and handle selection
opt_cols = ["ĐÁP ÁN 1","ĐÁP ÁN 2","ĐÁP ÁN 3","ĐÁP ÁN 4"]
options = [str(row[c]) for c in opt_cols]
selected_label = st.radio("Chọn đáp án:", options, index=st.session_state.answers.get(st.session_state.current_exam, {}).get(idx, 0) if st.session_state.answers.get(st.session_state.current_exam, {}) else 0, key=f"radio_{st.session_state.current_exam}_{idx}")

# Convert selected_label to number 1-4
selected_index = options.index(selected_label) + 1

# Save answer and mark correctness
correct_ans = int(row["ĐÁP ÁN ĐÚNG"])
st.session_state.answers.setdefault(st.session_state.current_exam, {})[idx] = selected_index
is_correct = (selected_index == correct_ans)
st.session_state.corrects.setdefault(st.session_state.current_exam, {})[idx] = is_correct

# Show immediate feedback colored
if is_correct:
    st.markdown(f"<div style='padding:10px;border-radius:6px;background:#e6fff0'>✅ Đúng — đáp án: {selected_index}</div>", unsafe_allow_html=True)
else:
    st.markdown(f"<div style='padding:10px;border-radius:6px;background:#ffecec'>❌ Sai — đáp án bạn chọn: {selected_index} • Đáp án đúng: {correct_ans}</div>", unsafe_allow_html=True)

# Progress & quick controls
st.write("---")
progress = f"Câu hiện tại: {idx+1}/{n_questions}"
st.write(progress)

# Quick navigation
q1, q2 = st.columns(2)
if q1.button("Quay lại (nhanh)") and st.session_state.index > 0:
    st.session_state.index -= 1
if q2.button("Kế tiếp (nhanh)") and st.session_state.index < n_questions - 1:
    st.session_state.index += 1

# Show finish summary in a collapsible panel
if st.button("Kết thúc và hiển thị kết quả"):
    st.session_state.started = False
    answers = st.session_state.answers.get(st.session_state.current_exam, {})
    corrects = st.session_state.corrects.get(st.session_state.current_exam, {})
    total = n_questions
    correct_count = sum(1 for v in corrects.values() if v)
    percent = correct_count * 100.0 / total if total > 0 else 0.0
    elapsed = 0.0
    if st.session_state.start_time:
        elapsed = time.time() - st.session_state.start_time
    st.success(f"Bạn đã hoàn thành: {correct_count}/{total} đúng — {percent:.2f}% — Thời gian: {int(elapsed)//60} phút {int(elapsed)%60} giây")
    if st.button("Hiện danh sách câu trả lời sai (xem lại)"):
        wrongs = [i for i,v in corrects.items() if not v]
        if not wrongs:
            st.write("Không có câu sai.")
        else:
            for i in wrongs:
                row = df.iloc[i]
                selected = st.session_state.answers[st.session_state.current_exam].get(i, None)
                st.markdown(f"**Câu {row['STT']}**: {row['CÂU HỎI']}")
                st.write(f"Đáp án bạn chọn: {selected} — Đáp án đúng: {int(row['ĐÁP ÁN ĐÚNG'])}")