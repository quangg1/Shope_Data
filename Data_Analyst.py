import streamlit as st
import pandas as pd
import numpy as np
from bs4 import BeautifulSoup
import requests
import json
import re
st.set_page_config(page_title="CSV Analyzer", layout="wide")

st.title("📊 CSV Data Analyzer")

# Upload CSV file
uploaded_file = st.file_uploader("Chọn file CSV để phân tích (Chỉ dùng cho lấy sản phẩm ở Afffiliate)", type=["csv"])
def preprocess_sold_column(df):
    if 'Sold' in df.columns:
        df['Sold'] = df['Sold'].astype(str).str.replace('lượt bán', '', regex=True).str.strip()
        df['Sold'] = df['Sold'].str.replace(',', '.')  # Thay dấu phẩy thành dấu chấm
        df['Sold'] = df['Sold'].apply(lambda x: float(x.replace('k', '')) * 1000 if 'k' in x else float(x) if x.replace('.', '', 1).isdigit() else np.nan)
    return df


if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)
    
    # Display full dataframe with scroll
    st.subheader("📌 Dữ liệu tải lên:")
    st.dataframe(df, height=500)
    
    # Processing options
    st.subheader("⚙️ Xử lý dữ liệu")
    
    if st.button("📈 Hiển thị thống kê mô tả"):
        st.write(df.describe())
    

    if st.button("Lọc dữ liệu"):
        df = preprocess_sold_column(df)
        st.write("### Dữ liệu sau khi lọc")
        st.dataframe(df, height=400)
    # Chọn cột để copy dữ liệu
    column_to_copy = st.selectbox("Chọn cột để sao chép dữ liệu:", df.columns)
    row_range = st.text_input("Nhập phạm vi dòng (ví dụ: 2,100):")
    
    if st.button("Sao chép dữ liệu cột"):
        try:
            start, end = map(int, row_range.split(","))
            copied_text = ';'.join(df[column_to_copy].astype(str).iloc[start-1:end].tolist())
            st.text_area("Dữ liệu đã sao chép:", copied_text, height=200)
        except:
            st.error("Vui lòng nhập phạm vi hợp lệ (ví dụ: 2,100)")
##############################################      


# Nhập dữ liệu
search_values = st.text_area("Nhập các giá trị cần tìm (ngăn cách bằng dấu ;):")
    
if st.button("Tìm vị trí"):
    if search_values:
        values_list = [val.strip() for val in search_values.split(";")]
        matched_indexes = []
            
        for val in values_list:
            matched_rows = df[df[column_to_copy].astype(str) == val].index.tolist()
            matched_indexes.extend(matched_rows)
            
        matched_indexes = sorted(set(matched_indexes))  # Loại bỏ trùng lặp và sắp xếp
            
        if matched_indexes:
            st.write("### Kết quả:")
            st.write(f"Các dòng chứa giá trị tìm kiếm: {matched_indexes}")
        else:
            st.warning("Không tìm thấy giá trị nào trong cột đã chọn.")
    else:
        st.error("Vui lòng nhập các giá trị cần tìm kiếm!")
