import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from folium.plugins import MarkerCluster
from sqlalchemy import create_engine
import plotly.express as px

# ==========================================
# 0. 基础配置
# ==========================================
st.set_page_config(page_title="城市产业与人才空间雷达系统", page_icon="📡", layout="wide")

industry_dict = {'A': '农林牧渔', 'B': '采矿业', 'C': '制造业', 'D': '电力热力', 'E': '建筑业', 'F': '批发零售', 'G': '交运邮政', 'H': '住宿餐饮', 'I': '信息技术', 'J': '金融业', 'K': '房地产业', 'L': '租赁商务', 'M': '科研技术', 'N': '环境管理', 'O': '居民服务', 'P': '教育', 'Q': '卫生工作', 'R': '文体娱乐', 'S': '公共管理'}

# ==========================================
# 1. 数据库模块
# ==========================================
@st.cache_resource
def init_connection():
    return create_engine(st.secrets["DB_URL"])

engine = init_connection()

@st.cache_data(ttl=600)
def load_data(query):
    try:
        df = pd.read_sql(query, engine)
        df.columns = [str(c).lower().strip() for c in df.columns]
        return df
    except: return pd.DataFrame()

# ==========================================
# 2. 侧边栏
# ==========================================
with st.sidebar:
    st.title("📡 City-Radar v3.0")
    st.success("✨ 欢迎使用城市产业与人才空间雷达系统")
    city_choice = st.radio("📍 选择分析城市：", ["全国", "北京", "苏州", "深圳"])
    if st.button("🔄 刷新系统数据"):
        st.cache_data.clear()
        st.rerun()

st.title("🏙️ 城市产业与人才空间雷达系统")

# 替代原来的 Tabs，直接作为页面副标题
st.markdown("##### 📍 空间聚类格局")
st.write("---")

# ✅ 修改点 2：加入全国配置，并为每个选项加上 zoom 字段
city_cfg = {
    "全国": {"lat": 35.8617, "lng": 104.1954, "code": "ALL", "zoom": 5}, # 全国中心点，zoom 设为 5
    "北京": {"lat": 39.9042, "lng": 116.4074, "code": 110000, "zoom": 11},
    "苏州": {"lat": 31.2990, "lng": 120.6190, "code": 320500, "zoom": 11},
    "深圳": {"lat": 22.5431, "lng": 114.0579, "code": 440300, "zoom": 11}
}
sel = city_cfg[city_choice]

# 保持左右两列的布局
m_col, i_col = st.columns([2.5, 1])

# ------------------------------------------
# 左侧：地图区域
# ------------------------------------------
with m_col:
    st.subheader(f"🗺️ {city_choice}·产业集聚分布图")
    
    # ✅ 修改点 3：根据是否是“全国”动态生成 SQL 语句
    if sel['code'] == "ALL":
        # 查询全国数据（没有 WHERE 限制）。建议把 LIMIT 调大一些，比如 10000 或 20000，视你的电脑性能而定
        query = "SELECT * FROM spatial_cluster_results LIMIT 30000" 
    else:
        # 查询特定城市数据
        query = f"SELECT * FROM spatial_cluster_results WHERE 城市代码 = {sel['code']} LIMIT 3000"
        
    df_map = load_data(query)
    
    if not df_map.empty:
        amap_url = 'http://webrd02.is.autonavi.com/appmaptile?lang=zh_cn&size=1&scale=1&style=7&x={x}&y={y}&z={z}'
        m = folium.Map(
            location=[sel['lat'], sel['lng']], 
            zoom_start=sel['zoom'], # ✅ 修改点 4：使用字典里配置的动态缩放级别
            tiles=amap_url, 
            attr='高德地图'
        )
        
        marker_cluster = MarkerCluster().add_to(m)
        
        for _, r in df_map.iterrows():
            ind = industry_dict.get(str(r.get('行业门类', '')).upper(), "其他")
            popup_html = f"企业:{str(r.get('企业名称',''))[:8]}...<br>行业:{ind}"
            folium.CircleMarker(
                [r['lat'], r['lng']], 
                radius=5, 
                color='#1abc9c', 
                fill=True, 
                popup=folium.Popup(popup_html, max_width=200)
            ).add_to(marker_cluster)
        
        st_folium(m, width=900, height=550, returned_objects=[])
    else:
        st.warning("正在连接高德底图服务器...")

# ------------------------------------------
# 右侧：文本、图片、表格展示区域
# ------------------------------------------
with i_col:
    st.subheader("📝 核心分析结论")
    
    # 1. 插入普通文本与 Markdown
    st.write("根据最新云端数据更新，当前城市的产业集群分布呈现出新的特征。您可以结合左侧地图查看具体的空间集聚情况。")
    st.markdown("""
    **主要发现：**
    * 核心商圈的活跃度提升了 **15%**
    * 新兴产业向周边区域扩散趋势明显
    """)
    
    st.write("---")
    
    # 2. 插入一个补充表格
    st.subheader("📊 基础统计概览")
    # 这里可以替换成你从数据库 fetch 出来的真实 DataFrame，目前用静态数据做演示
    sample_data = pd.DataFrame({
        "指标": ["活跃企业总数", "高新技术企业占比", "平均通勤距离"],
        "数值": ["12,450", "34.5%", "8.2 km"]
    })
    st.dataframe(sample_data, hide_index=True) # hide_index=True 隐藏行号，更美观
    
    st.write("---")
    
    # 3. 插入图片
    st.subheader("📈 趋势分析图")
    # 🚨 注意：请将下面的链接替换为你本地真实的图片路径（如 "assets/my_chart.png"）
    # 或者如果你把图片存在了图床，可以直接放图片的 URL 链接
    st.image("https://images.unsplash.com/photo-1551288049-bebda4e38f71?q=80&w=500&auto=format&fit=crop", caption="产业发展趋势示例", use_container_width=True)
