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

# 数据清洗与合并函数
@st.cache_data(ttl=600)
def get_data(city_code):
    query_ent = "SELECT lat, lng, 企业名称, 行业代码, 城市代码, 招聘人数_clean FROM spatial_cluster_results"
    if city_code != "ALL":
        query_ent += f" WHERE 城市代码 = {city_code}"
    
    query_ind = "SELECT 行业代码, 行业名称 FROM industry_codes"
    
    df_ent = pd.read_sql(query_ent, engine)
    df_ind = pd.read_sql(query_ind, engine)
    
    df_ent['行业代码'] = df_ent['行业代码'].astype(str).str.split('.').str[0].str.strip()
    df_ind['行业代码'] = df_ind['行业代码'].astype(str).str.split('.').str[0].str.strip()
    df_ind = df_ind.drop_duplicates(subset=['行业代码'])
    
    df = pd.merge(df_ent, df_ind, on='行业代码', how='left')
    df['行业名称'] = df['行业名称'].fillna('未知行业')
    return df

# ==========================================
# 1. 侧边栏
# ==========================================
with st.sidebar:
    st.title("📡 City-Radar v3.0")
    st.info("📅 数据覆盖周期: 2010 - 2025")
    city_choice = st.radio("📍 选择分析区域：", ["全国", "北京", "苏州", "深圳"])
    if st.button("🔄 刷新系统数据"):
        st.cache_data.clear()
        st.rerun()

# ==========================================
# 2. 主界面布局
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

# 定义不同城市的文字描述
city_descriptions = {
    "全国": (
        "**宏观产业空间格局：** 全国产业呈现显著的“多极化与走廊化”演进特征。长三角、珠三角、京津冀三大城市群依托极强的资源整合能力，形成了以知识密集型服务业与高端装备制造业为核心的产业“引力场”。"
        "目前，全国产业链的空间布局正从“简单集群”向“网络化协同”转型。内陆节点城市正通过承接沿海产业梯度转移，逐步构建起区域性的增长极，产业转移与分工进一步深化。"
    ),
    "北京": (
        "**创新驱动与总部经济：** 北京作为核心功能区，其产业结构表现出极高的“知识壁垒”。研发、科技服务与金融业的深度融合，构成了全国性的决策中心与创新策源地。"
        "北京产业的深度价值在于：通过高等院校与科研院所的原始创新，带动高精尖产业溢出。这种基于人才密度与政策导向的增长模型，使得北京在该区域内对高端人才具有无可替代的‘虹吸效应’。"
    ),
    "苏州": (
        "**产业能级与价值链整合：** 苏州是典型的“强工业、微城市”模式，其核心优势在于极其完备的工业生态体系。从传统制造向生物医药、纳米科技等高端制造升级，苏州成功实现了产业链从“组装加工”向“核心技术制造”的跃迁。"
        "苏州的产业深度体现在其与上海的协同效应上：通过深度融入长三角服务链，苏州实现了‘制造+研发’的闭环，是目前全球产业链条中极具竞争力的工业枢纽。"
    ),
    "深圳": (
        "**内生性创新与高密度创业：** 深圳展示了一个极高密度的“敏捷制造与硬科技生态”。其产业链特色在于极短的研发-转化周期，这种基于成千上万中小科技企业的自发竞争，造就了深圳独特的硬科技创新引擎。"
        "深圳的人才流向不仅受薪资驱动，更受“创新密度”吸引。通过高密度的人才流动与跨界碰撞，深圳在电子信息、人工智能等领域构建了极强的内生增长动力，体现了‘创新是第一竞争力’的真实写照。"
    )
}

df = get_data(sel['code'])
m_col, i_col = st.columns([2.5, 1])

# --- 左侧地图区域 ---
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
        
        # 新增：地图下方的动态文本内容
        st.markdown("---")
        st.info(f"💡 **{city_choice}产业空间观察**：\n\n{city_descriptions[city_choice]}")

# --- 右侧数据分析区域 ---
with i_col:
    st.subheader("📊 产业数据洞察")
    
    st.markdown("##### 行业聚集度分析")
    if not df.empty:
        df_stats = df['行业名称'].value_counts().reset_index()
        df_stats.columns = ['行业名称', '数量']
        fig = px.bar(df_stats.head(8), x='数量', y='行业名称', orientation='h', color='数量', color_continuous_scale='Viridis')
        fig.update_layout(margin=dict(l=0, r=0, t=20, b=20), height=300)
        st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("##### 企业招聘详情 (Top 10)")
    if not df.empty:
        display_df = df[['企业名称', '行业名称', '招聘人数_clean']].copy()
        display_df.columns = ['企业名称', '行业名称', '招聘人数']
        st.dataframe(
            display_df.sort_values('招聘人数', ascending=False).head(10), 
            use_container_width=True, 
            hide_index=True
        )
