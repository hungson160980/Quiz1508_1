# Streamlit Quiz App

Ứng dụng thi trắc nghiệm bằng Streamlit. Mỗi file Excel (.xlsx) là một "môn" / mục thi. Mỗi file phải có sheet 1 với các cột (chính xác, có dấu):
- STT
- CÂU HỎI
- ĐÁP ÁN 1
- ĐÁP ÁN 2
- ĐÁP ÁN 3
- ĐÁP ÁN 4
- ĐÁP ÁN ĐÚNG  (là 1/2/3/4)

Hướng dẫn chạy cục bộ:
1. Cài đặt: `pip install -r requirements.txt`
2. Chạy: `streamlit run app.py`
3. Trên sidebar, chọn và upload các file .xlsx (có thể chọn nhiều)
4. Chọn mục thi, nhấn "Bắt đầu thi" và làm bài.

Kết quả lưu trong session (không ghi ra file).

Cấu trúc repo:
- app.py
- requirements.txt
- README.md