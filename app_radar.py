import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from folium.plugins import MarkerCluster, HeatMap
from sqlalchemy import create_engine
import plotly.express as px

# ==========================================
# 0. 页面配置与行业映射 (内存映射，无需修改数据库)
# ==========================================
st.set_page_config(page_title="城市产业与人才空间雷达系统", page_icon="📡", layout="wide")

# 你的行业代码映射表
INDUSTRY_MAP = {
    'A': '农林牧渔', 'B': '采矿业', 'C': '制造业', 'D': '电力热力',
    'E': '建筑业', 'F': '批发零售', 'G': '交运邮政', 'H': '住宿餐饮',
    'I': '信息技术', 'J': '金融业', 'K': '房地产业', 'L': '租赁商务',
    'M': '科研技术', 'N': '环境管理', 'O': '居民服务', 'P': '教育',
    'Q': '卫生工作', 'R': '文体娱乐', 'S': '公共管理'
}

# ==========================================
# 1. 数据库连接
# ==========================================
engine = create_engine('postgresql://postgres:postgres@localhost:5432/CityRadar')


@st.cache_data(ttl=600)
def load_data(query):
    try:
        df = pd.read_sql(query, engine)
        if '行业代码' in df.columns:
            df['行业名称'] = df['行业代码'].map(INDUSTRY_MAP).fillna('未知行业')
        return df
    except Exception as e:
        st.error(f"查询错误: {e}")
        return pd.DataFrame()


# ==========================================
# 2. 侧边栏
# ==========================================
with st.sidebar:
    st.title("📡 City-Radar v3.0")
    st.success("✨ 欢迎使用城市产业与人才空间雷达系统")
    city_choice = st.radio("📍 选择分析区域：", ["全国", "北京", "苏州", "深圳"])

    if st.button("🔄 刷新系统数据"):
        st.cache_data.clear()
        st.rerun()

# ==========================================
# 3. 布局区 (严格按照你的要求)
# ==========================================
st.title("🏙️ 城市产业与人才空间雷达系统")
st.markdown("##### 📍 空间聚类格局")
st.write("---")

# 地图定义
amap_url = "http://wprd04.is.autonavi.com/appmaptile?x={x}&y={y}&z={z}&lang=zh_cn&size=1&scl=1&style=7"
city_cfg = {
    "全国": {"lat": 35.86, "lng": 104.19, "code": "ALL", "zoom": 4},
    "北京": {"lat": 39.90, "lng": 116.40, "code": 110000, "zoom": 10},
    "苏州": {"lat": 31.29, "lng": 120.61, "code": 320500, "zoom": 10},
    "深圳": {"lat": 22.54, "lng": 114.05, "code": 440300, "zoom": 10}
}
sel = city_cfg[city_choice]

m_col, i_col = st.columns([2.5, 1])

# --- 左侧：地图区域 ---
with m_col:
    if sel['code'] == "ALL":
        query = "SELECT lat, lng FROM spatial_cluster_results LIMIT 30000"
    else:
        query = f"SELECT lat, lng, 企业名称, 行业代码 FROM spatial_cluster_results WHERE 城市代码 = {sel['code']}"

    df_map = load_data(query)

    if not df_map.empty:
        m = folium.Map(location=[sel['lat'], sel['lng']], zoom_start=sel['zoom'], tiles=amap_url, attr='高德地图')

        if city_choice == "全国":
            HeatMap(df_map[['lat', 'lng']].values.tolist(), radius=10, blur=15).add_to(m)
        else:
            mc = MarkerCluster().add_to(m)
            for _, r in df_map.iterrows():
                industry = r.get('行业名称', '未知')
                tooltip_text = f"企业: {r['企业名称']}<br>行业: {industry}"
                folium.CircleMarker(
                    [r['lat'], r['lng']], radius=5, color='#1abc9c', fill=True,
                    tooltip=tooltip_text
                ).add_to(mc)

        st_folium(m, width=900, height=600)

# --- 右侧：数据分析区 ---
with i_col:
    st.subheader("📊 产业数据洞察")
    where_clause = "" if sel['code'] == "ALL" else f"WHERE 城市代码 = {sel['code']}"

    # 行业统计
    df_ind = load_data(f"SELECT 行业代码 FROM spatial_cluster_results {where_clause}")
    if not df_ind.empty:
        df_stats = df_ind['行业名称'].value_counts().reset_index()
        df_stats.columns = ['行业名称', 'count']
        fig = px.bar(df_stats.head(8), x='count', y='行业名称', orientation='h', color='count',
                     color_continuous_scale='Viridis')
        fig.update_layout(showlegend=False, margin=dict(l=0, r=0, t=20, b=20), height=300)
        st.plotly_chart(fig, use_container_width=True)

    # 招聘详情
    df_hire = load_data(
        f"SELECT 企业名称, 行业代码, 招聘人数_clean FROM spatial_cluster_results {where_clause} ORDER BY 招聘人数_clean DESC LIMIT 10")
    if not df_hire.empty:
        st.dataframe(df_hire[['企业名称', '行业名称', '招聘人数_clean']], use_container_width=True, hide_index=True)
