import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from folium.plugins import MarkerCluster, HeatMap
from sqlalchemy import create_engine
import plotly.express as px

# ==========================================
# 0. 页面设置
# ==========================================
st.set_page_config(page_title="城市产业与人才空间雷达系统", page_icon="📡", layout="wide")

engine = create_engine('postgresql://postgres:postgres@localhost:5432/CityRadar')

# 统一数据加载函数
@st.cache_data(ttl=600)
def get_data(city_code):
    query_ent = "SELECT lat, lng, 企业名称, 行业代码, 城市代码, 招聘人数_clean FROM spatial_cluster_results"
    if city_code != "ALL":
        query_ent += f" WHERE 城市代码 = {city_code}"
    
    query_ind = "SELECT 行业代码, 行业名称 FROM industry_codes"
    
    df_ent = pd.read_sql(query_ent, engine)
    df_ind = pd.read_sql(query_ind, engine)
    
    # 格式统一化
    df_ent['行业代码'] = df_ent['行业代码'].astype(str).str.split('.').str[0].str.strip()
    df_ind['行业代码'] = df_ind['行业代码'].astype(str).str.split('.').str[0].str.strip()
    df_ind = df_ind.drop_duplicates(subset=['行业代码'])
    
    # 合并
    df = pd.merge(df_ent, df_ind, on='行业代码', how='left')
    df['行业名称'] = df['行业名称'].fillna('未知行业')
    return df

# ==========================================
# 2. 侧边栏 (已添加数据时间标识)
# ==========================================
with st.sidebar:
    st.title("📡 City-Radar v3.0")
    # 明确标注数据时间
    st.info("📅 数据覆盖周期: 2010 - 2025")
    st.success("✨ 欢迎使用系统")
    
    city_choice = st.radio("📍 选择分析区域：", ["全国", "北京", "苏州", "深圳"])
    if st.button("🔄 刷新系统数据"):
        st.cache_data.clear()
        st.rerun()

# ==========================================
# 3. 主界面布局
# ==========================================
st.title("🏙️ 城市产业与人才空间雷达系统")
st.markdown("##### 📍 空间聚类格局")
st.write("---")

city_cfg = {
    "全国": {"lat": 35.86, "lng": 104.19, "code": "ALL", "zoom": 4},
    "北京": {"lat": 39.90, "lng": 116.40, "code": 110000, "zoom": 10},
    "苏州": {"lat": 31.29, "lng": 120.61, "code": 320500, "zoom": 10},
    "深圳": {"lat": 22.54, "lng": 114.05, "code": 440300, "zoom": 10}
}
sel = city_cfg[city_choice]

# 获取数据
df = get_data(sel['code'])

m_col, i_col = st.columns([2.5, 1])

# --- 左侧地图 ---
with m_col:
    if not df.empty:
        m = folium.Map(location=[sel['lat'], sel['lng']], zoom_start=sel['zoom'], 
                       tiles="http://wprd04.is.autonavi.com/appmaptile?x={x}&y={y}&z={z}&lang=zh_cn&size=1&scl=1&style=7", attr='高德地图')
        if city_choice == "全国":
            HeatMap(df[['lat', 'lng']].values.tolist(), radius=10, blur=15).add_to(m)
        else:
            mc = MarkerCluster().add_to(m)
            for _, r in df.iterrows():
                folium.CircleMarker([r['lat'], r['lng']], radius=5, color='#1abc9c', fill=True,
                                   tooltip=f"企业: {r['企业名称']}<br>行业: {r['行业名称']}").add_to(mc)
        st_folium(m, width=900, height=600)

# --- 右侧分析 ---
with i_col:
    st.subheader("📊 产业数据洞察")
    
    # 行业统计图
    st.markdown("##### 行业聚集度分析")
    if not df.empty:
        df_stats = df['行业名称'].value_counts().reset_index()
        df_stats.columns = ['行业名称', '数量']
        fig = px.bar(df_stats.head(8), x='数量', y='行业名称', orientation='h', color='数量', color_continuous_scale='Viridis')
        fig.update_layout(margin=dict(l=0, r=0, t=20, b=20), height=300)
        st.plotly_chart(fig, use_container_width=True)
    
    # 招聘表格
    st.markdown("##### 企业招聘详情 (Top 10)")
    if not df.empty:
        display_df = df[['企业名称', '行业名称', '招聘人数_clean']].copy()
        display_df.columns = ['企业名称', '行业名称', '招聘人数']
        st.dataframe(
            display_df.sort_values('招聘人数', ascending=False).head(10), 
            use_container_width=True, 
            hide_index=True
        )
