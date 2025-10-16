import os
import zipfile

# Tạo cấu trúc thư mục và file
files = {
    'app.py': '''import streamlit as st
import pandas as pd
from datetime import datetime
import time
from utils.quiz_manager import QuizManager
from utils.file_handler import load_excel_file

# Cấu hình trang
st.set_page_config(
    page_title="Hệ thống Thi Trắc Nghiệm",
    page_icon="📝",
    layout="wide"
)

# Khởi tạo session state
if 'quiz_manager' not in st.session_state:
    st.session_state.quiz_manager = QuizManager()
if 'current_quiz' not in st.session_state:
    st.session_state.current_quiz = None
if 'current_question' not in st.session_state:
    st.session_state.current_question = 0
if 'start_time' not in st.session_state:
    st.session_state.start_time = None
if 'answers' not in st.session_state:
    st.session_state.answers = {}
if 'quiz_finished' not in st.session_state:
    st.session_state.quiz_finished = False

def main():
    st.title("📝 Hệ Thống Thi Trắc Nghiệm")
    
    # Sidebar - Import dữ liệu
    with st.sidebar:
        st.header("📂 Quản lý dữ liệu")
        
        uploaded_file = st.file_uploader(
            "Import file Excel",
            type=['xlsx', 'xls'],
            help="Chọn file Excel chứa câu hỏi"
        )
        
        if uploaded_file:
            quiz_name = st.text_input(
                "Tên mục thi",
                value=uploaded_file.name.replace('.xlsx', '').replace('.xls', '')
            )
            
            if st.button("➕ Thêm mục thi"):
                try:
                    df = load_excel_file(uploaded_file)
                    st.session_state.quiz_manager.add_quiz(quiz_name, df)
                    st.success(f"✅ Đã thêm mục thi: {quiz_name}")
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Lỗi: {str(e)}")
        
        st.divider()
        
        # Hiển thị danh sách mục thi
        quizzes = st.session_state.quiz_manager.get_quiz_list()
        if quizzes:
            st.subheader(f"📚 Danh sách mục thi ({len(quizzes)})")
            for quiz in quizzes:
                if st.button(f"📖 {quiz}", key=f"quiz_{quiz}", use_container_width=True):
                    st.session_state.current_quiz = quiz
                    st.session_state.current_question = 0
                    st.session_state.start_time = None
                    st.session_state.answers = {}
                    st.session_state.quiz_finished = False
                    st.rerun()
    
    # Main content
    if st.session_state.current_quiz is None:
        show_welcome_screen()
    elif st.session_state.quiz_finished:
        show_results()
    else:
        show_quiz()

def show_welcome_screen():
    st.markdown("### 👋 Chào mừng đến với Hệ thống Thi Trắc Nghiệm!")
    st.info("📌 Hướng dẫn: Chọn một mục thi từ menu bên trái để bắt đầu")
    
    quizzes = st.session_state.quiz_manager.get_quiz_list()
    if quizzes:
        st.markdown("#### 📚 Các mục thi hiện có:")
        cols = st.columns(3)
        for idx, quiz in enumerate(quizzes):
            with cols[idx % 3]:
                st.info(f"**{quiz}**\\n{st.session_state.quiz_manager.get_question_count(quiz)} câu hỏi")
    else:
        st.warning("⚠️ Chưa có mục thi nào. Vui lòng import file Excel từ menu bên trái.")

def show_quiz():
    quiz_name = st.session_state.current_quiz
    current_q = st.session_state.current_question
    
    # Header
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        st.header(f"📝 {quiz_name}")
    with col2:
        total_questions = st.session_state.quiz_manager.get_question_count(quiz_name)
        st.metric("Tiến độ", f"{current_q + 1}/{total_questions}")
    with col3:
        if st.session_state.start_time:
            elapsed = int(time.time() - st.session_state.start_time)
            st.metric("Thời gian", f"{elapsed // 60}:{elapsed % 60:02d}")
    
    # Nút bắt đầu thi
    if st.session_state.start_time is None:
        if st.button("🚀 Bắt đầu thi", type="primary", use_container_width=True):
            st.session_state.start_time = time.time()
            st.rerun()
        return
    
    # Hiển thị câu hỏi
    question_data = st.session_state.quiz_manager.get_question(quiz_name, current_q)
    
    if question_data:
        st.markdown(f"### Câu {current_q + 1}: {question_data['question']}")
        st.divider()
        
        # Hiển thị các đáp án
        selected_answer = st.session_state.answers.get(current_q)
        correct_answer = question_data['correct_answer']
        
        for i, answer in enumerate(question_data['answers'], 1):
            col1, col2 = st.columns([0.1, 0.9])
            
            with col1:
                if st.button(f"{i}", key=f"ans_{current_q}_{i}", use_container_width=True):
                    st.session_state.answers[current_q] = i
                    st.rerun()
            
            with col2:
                # Xác định màu sắc
                if selected_answer == i:
                    if i == correct_answer:
                        st.success(f"✅ {answer}")
                    else:
                        st.error(f"❌ {answer}")
                else:
                    st.write(answer)
        
        st.divider()
        
        # Navigation buttons
        col1, col2, col3 = st.columns([1, 1, 1])
        
        with col1:
            if current_q > 0:
                if st.button("⬅️ Quay lại", use_container_width=True):
                    st.session_state.current_question -= 1
                    st.rerun()
        
        with col2:
            if st.button("🏁 Kết thúc", type="secondary", use_container_width=True):
                st.session_state.quiz_finished = True
                st.rerun()
        
        with col3:
            if current_q < total_questions - 1:
                if st.button("Kế tiếp ➡️", type="primary", use_container_width=True):
                    st.session_state.current_question += 1
                    st.rerun()
            else:
                if st.button("🏁 Hoàn thành", type="primary", use_container_width=True):
                    st.session_state.quiz_finished = True
                    st.rerun()

def show_results():
    quiz_name = st.session_state.current_quiz
    total_questions = st.session_state.quiz_manager.get_question_count(quiz_name)
    
    # Tính điểm
    correct_count = 0
    wrong_questions = []
    
    for q_idx in range(total_questions):
        question_data = st.session_state.quiz_manager.get_question(quiz_name, q_idx)
        user_answer = st.session_state.answers.get(q_idx)
        correct_answer = question_data['correct_answer']
        
        if user_answer == correct_answer:
            correct_count += 1
        else:
            wrong_questions.append({
                'index': q_idx + 1,
                'question': question_data['question'],
                'user_answer': user_answer,
                'correct_answer': correct_answer,
                'answers': question_data['answers']
            })
    
    score_percent = (correct_count / total_questions) * 100 if total_questions > 0 else 0
    elapsed_time = int(time.time() - st.session_state.start_time) if st.session_state.start_time else 0
    
    # Hiển thị kết quả
    st.balloons()
    st.header("🎉 Kết quả bài thi")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Tổng câu hỏi", total_questions)
    with col2:
        st.metric("Trả lời đúng", correct_count)
    with col3:
        st.metric("Điểm", f"{score_percent:.1f}%")
    with col4:
        st.metric("Thời gian", f"{elapsed_time // 60}:{elapsed_time % 60:02d}")
    
    # Đánh giá
    if score_percent >= 80:
        st.success("🌟 Xuất sắc! Bạn đã làm rất tốt!")
    elif score_percent >= 60:
        st.info("👍 Khá tốt! Hãy tiếp tục cố gắng!")
    else:
        st.warning("💪 Hãy ôn tập thêm và thử lại nhé!")
    
    st.divider()
    
    # Hiển thị câu sai
    if wrong_questions:
        with st.expander(f"📋 Xem {len(wrong_questions)} câu trả lời sai", expanded=True):
            for wrong in wrong_questions:
                st.markdown(f"**Câu {wrong['index']}: {wrong['question']}**")
                
                col1, col2 = st.columns(2)
                with col1:
                    user_ans_text = wrong['answers'][wrong['user_answer'] - 1] if wrong['user_answer'] else "Chưa trả lời"
                    st.error(f"❌ Bạn chọn: {user_ans_text}")
                with col2:
                    correct_ans_text = wrong['answers'][wrong['correct_answer'] - 1]
                    st.success(f"✅ Đáp án đúng: {correct_ans_text}")
                
                st.divider()
    else:
        st.success("🎯 Hoàn hảo! Bạn đã trả lời đúng tất cả các câu!")
    
    # Nút thi lại
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔄 Thi lại", type="primary", use_container_width=True):
            st.session_state.current_question = 0
            st.session_state.start_time = None
            st.session_state.answers = {}
            st.session_state.quiz_finished = False
            st.rerun()
    with col2:
        if st.button("🏠 Về trang chủ", use_container_width=True):
            st.session_state.current_quiz = None
            st.session_state.current_question = 0
            st.session_state.start_time = None
            st.session_state.answers = {}
            st.session_state.quiz_finished = False
            st.rerun()

if __name__ == "__main__":
    main()
''',

    'utils/quiz_manager.py': '''class QuizManager:
    def __init__(self):
        self.quizzes = {}
    
    def add_quiz(self, quiz_name, df):
        """Thêm một mục thi mới"""
        questions = []
        
        for _, row in df.iterrows():
            question = {
                'question': str(row['CÂU HỎI']),
                'answers': [
                    str(row['ĐÁP ÁN 1']),
                    str(row['ĐÁP ÁN 2']),
                    str(row['ĐÁP ÁN 3']),
                    str(row['ĐÁP ÁN 4'])
                ],
                'correct_answer': int(row['ĐÁP ÁN ĐÚNG'])
            }
            questions.append(question)
        
        self.quizzes[quiz_name] = questions
    
    def get_quiz_list(self):
        """Lấy danh sách các mục thi"""
        return list(self.quizzes.keys())
    
    def get_question(self, quiz_name, question_index):
        """Lấy một câu hỏi cụ thể"""
        if quiz_name in self.quizzes:
            if 0 <= question_index < len(self.quizzes[quiz_name]):
                return self.quizzes[quiz_name][question_index]
        return None
    
    def get_question_count(self, quiz_name):
        """Đếm số câu hỏi trong một mục thi"""
        if quiz_name in self.quizzes:
            return len(self.quizzes[quiz_name])
        return 0
''',

    'utils/file_handler.py': '''import pandas as pd

def load_excel_file(uploaded_file):
    """Đọc file Excel và trả về DataFrame"""
    try:
        # Đọc sheet đầu tiên
        df = pd.read_excel(uploaded_file, sheet_name=0)
        
        # Kiểm tra các cột bắt buộc
        required_columns = ['STT', 'CÂU HỎI', 'ĐÁP ÁN 1', 'ĐÁP ÁN 2', 
                          'ĐÁP ÁN 3', 'ĐÁP ÁN 4', 'ĐÁP ÁN ĐÚNG']
        
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            raise ValueError(f"Thiếu các cột: {', '.join(missing_columns)}")
        
        # Loại bỏ các dòng trống
        df = df.dropna(subset=['CÂU HỎI'])
        
        return df
        
    except Exception as e:
        raise Exception(f"Lỗi đọc file Excel: {str(e)}")
''',

    'requirements.txt': '''streamlit==1.31.0
pandas==2.1.4
openpyxl==3.1.2
xlrd==2.0.1
''',

    'README.md': '''# 📝 Hệ Thống Thi Trắc Nghiệm

Ứng dụng thi trắc nghiệm trực tuyến được xây dựng bằng Python và Streamlit.

## 🚀 Cài đặt

1. Clone repository:
```bash
git clone <repository-url>
cd quiz_app
```

2. Cài đặt dependencies:
```bash
pip install -r requirements.txt
```

3. Chạy ứng dụng:
```bash
streamlit run app.py
```

## 📋 Định dạng file Excel

File Excel cần có các cột sau ở Sheet 1:
- **STT**: Số thứ tự câu hỏi
- **CÂU HỎI**: Nội dung câu hỏi
- **ĐÁP ÁN 1**: Đáp án thứ nhất
- **ĐÁP ÁN 2**: Đáp án thứ hai
- **ĐÁP ÁN 3**: Đáp án thứ ba
- **ĐÁP ÁN 4**: Đáp án thứ tư
- **ĐÁP ÁN ĐÚNG**: Số thứ tự đáp án đúng (1, 2, 3, hoặc 4)

## 🎯 Tính năng

- ✅ Import nhiều file Excel (17 mục thi)
- ✅ Tính thời gian làm bài
- ✅ Điều hướng câu hỏi (Quay lại/Kế tiếp)
- ✅ Hiển thị đáp án đúng/sai ngay lập tức
- ✅ Thống kê kết quả chi tiết
- ✅ Xem lại các câu trả lời sai
- ✅ Giao diện thân thiện, dễ sử dụng

## 🌐 Deploy lên Streamlit Cloud

1. Push code lên GitHub
2. Truy cập https://share.streamlit.io
3. Đăng nhập và chọn repository
4. Deploy!

## 📧 Liên hệ

Nếu có vấn đề, vui lòng tạo issue trên GitHub.
''',

    '.gitignore': '''# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
ENV/

# Streamlit
.streamlit/

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Data files (optional)
# data/*.xlsx
# data/*.xls
''',

    'data/.gitkeep': ''
}

def create_project():
    """Tạo cấu trúc thư mục và file"""
    base_dir = 'quiz_app'
    
    # Tạo thư mục gốc
    if not os.path.exists(base_dir):
        os.makedirs(base_dir)
    
    # Tạo các file và thư mục
    for filepath, content in files.items():
        full_path = os.path.join(base_dir, filepath)
        
        # Tạo thư mục nếu chưa có
        dir_path = os.path.dirname(full_path)
        if dir_path and not os.path.exists(dir_path):
            os.makedirs(dir_path)
        
        # Ghi file
        with open(full_path, 'w', encoding='utf-8') as f:
            f.write(content)
    
    print(f"✅ Đã tạo cấu trúc project trong thư mục '{base_dir}'")

def create_zip():
    """Nén thư mục thành file zip"""
    base_dir = 'quiz_app'
    zip_filename = 'quiz_app.zip'
    
    with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files_list in os.walk(base_dir):
            for file in files_list:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, os.path.dirname(base_dir))
                zipf.write(file_path, arcname)
    
    print(f"✅ Đã tạo file zip: {zip_filename}")
    print(f"📦 Kích thước: {os.path.getsize(zip_filename) / 1024:.2f} KB")

if __name__ == '__main__':
    print("🚀 Bắt đầu tạo project...")
    create_project()
    create_zip()
    print("✨ Hoàn thành! File 'quiz_app.zip' đã sẵn sàng.")
