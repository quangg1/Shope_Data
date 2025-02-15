import streamlit as st
import requests
import pandas as pd
import re
from datetime import datetime, timedelta
import concurrent.futures
# ==== Hàm lấy danh sách sản phẩm từ Shopee ====
def fetch_live_sessions(cookies, days_ago):
    base_url = "https://creator.shopee.vn/supply/api/lm/sellercenter/liveList/v2"
    headers = {"User-Agent": "Mozilla/5.0", "Accept": "application/json"}
    all_sessions = []

    def get_sessions_for_day(i):
        date_str = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
        params = {
    "page": 1,
    "pageSize": 10,
    "name": "",
    "orderBy": "",
    "sort": "",
    "timeDim": "1d",
    "endDate": date_str  # Chỉ lấy dữ liệu trong ngày đó
}
        response = requests.get(base_url, params=params, headers=headers, cookies=cookies)
        if response.status_code == 200:
            data = response.json()
            if data.get("code") == 0 and "list" in data.get("data", {}):
                return [live["sessionId"] for live in data["data"]["list"]]
        return []

    with concurrent.futures.ThreadPoolExecutor() as executor:
        results = executor.map(get_sessions_for_day, range(0, days_ago + 1))

    for result in results:
        all_sessions.extend(result)

    return all_sessions
def fetch_shopee_products(cookies, sessionId):
    base_url = "https://creator.shopee.vn/supply/api/lm/sellercenter/realtime/dashboard/productList?"
    headers = {"User-Agent": "Mozilla/5.0", "Accept": "application/json"}
    
    params = {
    "sessionId": sessionId,
    "productName": "",
    "productListTimeRange": 0,
    "productListOrderBy": "itemSold",
    "sort": "asc",
    "page": 1,
    "pageSize": 10
}
    
    # Lấy số trang tổng cộng
    response = requests.get(base_url, params=params, headers=headers, cookies=cookies)
    if response.status_code != 200:
        return []
    
    data = response.json()
    if data.get("code") != 0 or not data.get("data"):
        return []
    
    total_pages = data["data"]["totalPage"]
    all_products = []

    def fetch_page(page):
        """Hàm lấy dữ liệu của từng trang"""
        params["page"] = page
        response = requests.get(base_url, params=params, headers=headers, cookies=cookies)
        if response.status_code == 200:
            page_data = response.json()
            if page_data.get("code") == 0 and page_data.get("data"):
                return page_data["data"]["list"]
        return []

    # Chạy đa luồng để lấy dữ liệu của từng trang
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        results = list(executor.map(fetch_page, range(1, total_pages + 1)))
    
    # Ghép toàn bộ dữ liệu sản phẩm lại
    all_products = [product for sublist in results for product in sublist]

    # Xử lý dữ liệu sản phẩm
    return [
        {
            "Index": i + 1,
            "ID": product.get("itemId", "N/A"),
            "Ảnh sản phẩm": f'<img src="https://down-zl-vn.img.susercontent.com/{product["coverImage"]}" width="150">' if "coverImage" in product else "N/A",
            "Tên sản phẩm": product.get("title", "Không có tên"),
            "Giá thấp nhất": product.get("minPrice", "N/A"),
            "Giá cao nhất": product.get("maxPrice", "N/A"),
            "Số lần nhấp chuột": product.get("productClicks", 0),
            "CTR (%)": product.get("ctr", 0.0),
            "Số lượt thêm vào giỏ": product.get("atc", 0),
            "Đơn hàng tạo ra": product.get("ordersCreated", 0),
            "Doanh thu": product.get("revenue", 0.0),
            "Số lượng bán": product.get("itemSold", 0),
            "COR (%)": product.get("cor", 0.0),
            "Đơn hàng xác nhận": product.get("confirmedOrderCnt", 0),
            "Doanh thu xác nhận": product.get("confirmedRevenue", 0.0),
            "Số lượng bán xác nhận": product.get("confirmedItemSold", 0),
            "COR xác nhận (%)": product.get("confirmedCor", 0.0),
            "Link Shopee": f'<a href="https://affiliate.shopee.vn/offer/product_offer/{product["itemId"]}" target="_blank">🔗 Xem</a>'
        }
        for i, product in enumerate(all_products)
    ]
def extract_number(value):
    """Trích xuất phần số từ chuỗi, bỏ ký tự không liên quan."""
    try:
        return float(re.sub(r"[^\d.]", "", str(value))) if re.sub(r"[^\d.]", "", str(value)) else 0
    except:
        return 0
# ==== Giao diện Streamlit ====
st.set_page_config(page_title="Shopee Product Scraper", layout="wide")
st.title("📦 Shopee Product Scraper")
if "df" not in st.session_state:
    st.session_state["df"] = None
if "df_filtered" not in st.session_state:
    st.session_state["df_filtered"] = None

# Nhập cookies
st.subheader("🔐 Nhập Cookies Shopee")
cookies_input = st.text_area("Nhập cookies của bạn vào đây:", height=100,key="cookies_input")
if st.button("Lưu Cookies"):
    if cookies_input:
        st.session_state["cookies"] = {"Cookie": cookies_input}
        st.success("✅ Cookies đã được lưu!")
    else:
        st.warning("⚠️ Vui lòng nhập cookies trước khi lưu.")


st.subheader("🔧 Chọn chế độ nhập dữ liệu")
option = st.radio("Chọn cách lấy dữ liệu:", ["Nhập sessionId", "Lấy theo số ngày"])

session_id = None
days_ago = None

if option == "Nhập sessionId":
    session_id = st.text_input("Nhập sessionId:")
else:
    days_ago = st.number_input("Nhập số ngày trước:", min_value=0, max_value=30, value=1, step=1)




# Nếu chọn ngày thì lấy sessionId của các phiên live
if st.button("Lấy dữ liệu") or days_ago !=1:
    if "cookies" not in st.session_state or not st.session_state["cookies"]:
        st.error("❌ Chưa có cookies! Vui lòng nhập và lưu cookies trước.")
    else:
        if session_id:
            st.info(f"📦 Đang lấy sản phẩm từ phiên live {session_id}...")
            products = fetch_shopee_products(st.session_state["cookies"], session_id)
            df = pd.DataFrame(products)
            st.session_state["df"] = df  # Lưu vào session state
            df_filtered = df
            df_filtered["Index"] = range(1, len(df_filtered) + 1)
            st.session_state["df_filtered"] = df_filtered
            st.markdown("""
                <style>
                .scroll-table {
                    max-height: 500px;
                    overflow-y: auto;
                    overflow-x: auto;
                    border: 1px solid #ddd;
                    padding: 10px;
                    white-space: nowrap;
                }
                th {
                    position: sticky;
                    top: 0;
                    background: black;
                    z-index: 1;
                }
                td- 1nd-child,th-1nd-child {
                 min-width:200px;   }
                </style>
                """, unsafe_allow_html=True)
                # Hiển thị bảng sản phẩm
            st.markdown(f'<div class="scroll-table">{df_filtered.to_html(escape=False, index=False)}</div>', unsafe_allow_html=True)
        if days_ago is not None:
            session_ids = fetch_live_sessions(st.session_state["cookies"], days_ago)

            if session_ids:
                st.success(f"✅ Tìm thấy {len(session_ids)} phiên live!")
                all_products = []

                for session_id in session_ids:
                    st.info(f"📦 Đang lấy sản phẩm từ phiên live {session_id}...")
                    products = fetch_shopee_products(st.session_state["cookies"], session_id)
                    all_products.extend(products)
        

            if all_products:
                df = pd.DataFrame(all_products)
                st.session_state["df"] = df
                df_filtered=df# Lưu vào session state
                df_filtered["Index"] = range(1, len(df_filtered) + 1)
                st.session_state["df_filtered"] = df_filtered
                st.markdown("""
                <style>
                .scroll-table {
                    max-height: 500px;
                    overflow-y: auto;
                    overflow-x: auto;
                    border: 1px solid #ddd;
                    padding: 10px;
                    white-space: nowrap;
                }
                th {
                    position: sticky;
                    top: 0;
                    background: black;
                    z-index: 1;
                }
                td- 1nd-child,th-1nd-child {
                 min-width:200px;   }
                </style>
                """, unsafe_allow_html=True)
                # Hiển thị bảng sản phẩm
                st.markdown(f'<div class="scroll-table">{df_filtered.to_html(escape=False, index=False)}</div>', unsafe_allow_html=True)
            else:
                st.warning("⚠️ Không có sản phẩm nào trong các phiên live này.")
df_filtered = st.session_state.get("df_filtered", pd.DataFrame())
if st.session_state["df_filtered"] is not None:
    filter_column = st.selectbox("Chọn cột muốn lọc:", df_filtered.columns, key="filter_column")
    sort_order = st.radio("Chọn kiểu sắp xếp:", ["Cao → Thấp", "Thấp → Cao"], key="sort_order")
    if st.button("🛒 Lọc giỏ live") or filter_column:
        if filter_column in df_filtered.columns: 
            ascending = True if sort_order == "Thấp → Cao" else False
            df_filtered = df_filtered.sort_values(by=filter_column, ascending=ascending)
            df_filtered["Index"] = range(1, len(df_filtered) + 1)  # Đánh lại số thứ tự

            # Lưu lại dữ liệu đã lọc
            st.session_state["df_filtered"] = df_filtered

            # Hiển thị kết quả
            st.success(f"✅ Đã lọc theo cột '{filter_column}' ({sort_order})!")
            st.markdown("""
                <style>
                .scroll-table {
                    max-height: 500px;
                    overflow-y: auto;
                    overflow-x: auto;
                    border: 1px solid #ddd;
                    padding: 10px;
                    white-space: nowrap;
                }
                th {
                    position: sticky;
                    top: 0;
                    background: black;
                    z-index: 1;
                }
                td- 1nd-child,th-1nd-child {
                 min-width:200px;   }
                </style>
                """, unsafe_allow_html=True)
            st.markdown(f'<div class="scroll-table">{df_filtered.to_html(escape=False, index=False)}</div>', unsafe_allow_html=True)

# Xuất danh sách link nếu nhấn nút
df_filtered = st.session_state.get("df_filtered", None)
df = st.session_state.get("df", None)

# 🟢 Nếu có df_filtered (dữ liệu đã lọc), ưu tiên dùng nó
df_to_export = df_filtered if df_filtered is not None else df

if df_to_export is not None and not df_to_export.empty:
    if st.button("📤 Xuất Link"):
        product_links = "\n".join(re.findall(r'href="([^"]+)"', " ".join(df_to_export["Link Shopee"].tolist())))
        st.text_area("Danh sách link sản phẩm:", product_links, height=300)

# Xuất danh sách tên sản phẩm theo index
if df_filtered is not None and not df_filtered.empty:
    st.subheader("📋 Xuất danh sách tên sản phẩm theo Index")
    start_index = st.number_input("Nhập Index bắt đầu:", min_value=1, value=1)
    end_index = st.number_input("Nhập Index kết thúc:", min_value=1, value=10)
    
    if st.button("📤 Xuất Tên Sản Phẩm"):
        product_names = "\n".join(df_filtered.iloc[start_index-1:end_index]["Tên sản phẩm"].tolist())
        st.text_area("Danh sách tên sản phẩm:", product_names, height=300)

# 🔄 Nút Refresh để reset dữ liệu gốc
if st.button("🔄 Refresh"):
    if "df" in st.session_state:
        del st.session_state["df"]
    if "df_filtered" in st.session_state:
        del st.session_state["df_filtered"]
    st.rerun()
