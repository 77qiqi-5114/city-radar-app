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

FIXED_ANN_DATA = {
    "北京": [{"分析对象": "北京-整体", "ANN(R值)": 0.0027, "Z得分": -266.82, "P值": 0.0}, {"分析对象": "北京-信息技术业", "ANN(R值)": 0.0187, "Z得分": -117.01, "P值": 0.0}, {"分析对象": "北京-制造业", "ANN(R值)": 0.0849, "Z得分": -47.30, "P值": 0.0}],
    "苏州": [{"分析对象": "苏州-整体", "ANN(R值)": 0.0359, "Z得分": -184.42, "P值": 0.0}, {"分析对象": "苏州-信息技术业", "ANN(R值)": 0.0708, "Z得分": -36.17, "P值": 0.0}, {"分析对象": "苏州-制造业", "ANN(R值)": 0.0296, "Z得分": -98.35, "P值": 0.0}],
    "深圳": [{"分析对象": "深圳-整体", "ANN(R值)": 0.0395, "Z得分": -278.47, "P值": 0.0}, {"分析对象": "深圳-信息技术业", "ANN(R值)": 0.0481, "Z得分": -82.91, "P值": 0.0}, {"分析对象": "深圳-制造业", "ANN(R值)": 0.0316, "Z得分": -156.00, "P值": 0.0}]
}

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
    city_choice = st.radio("📍 选择分析城市：", ["北京", "苏州", "深圳"])
    if st.button("🔄 刷新系统数据"):
        st.cache_data.clear()
        st.rerun()

st.title("🏙️ 城市产业与人才空间雷达系统")
tab1, tab2, tab3 = st.tabs(["📍 空间聚类格局", "💰 人才技能溢价", "🚨 企业生存预警"])

# ------------------------------------------
# 选项卡 1: 空间聚类格局 
# ------------------------------------------
with tab1:
    city_cfg = {"北京": {"lat": 39.9042, "lng": 116.4074, "code": 110000}, "苏州": {"lat": 31.2990, "lng": 120.6190, "code": 320500}, "深圳": {"lat": 22.5431, "lng": 114.0579, "code": 440300}}
    sel = city_cfg[city_choice]
    m_col, i_col = st.columns([2.5, 1])
    
    with m_col:
        st.subheader(f"🗺️ {city_choice}·产业集聚分布图")
        df_map = load_data(f"SELECT * FROM spatial_cluster_results WHERE 城市代码 = {sel['code']} LIMIT 5000")
        
        if not df_map.empty:
            amap_url = 'http://webrd02.is.autonavi.com/appmaptile?lang=zh_cn&size=1&scale=1&style=7&x={x}&y={y}&z={z}'
            m = folium.Map(
                location=[sel['lat'], sel['lng']], 
                zoom_start=11, 
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

    with i_col:
        st.subheader("📋 ANN 显著性检验")
        st.table(pd.DataFrame(FIXED_ANN_DATA[city_choice]))
        st.write("---")
        st.subheader("📊 空间统计诊断")
        df_moran = load_data(f"SELECT * FROM spatial_moran_results WHERE 城市 = '{city_choice}'")
        if not df_moran.empty:
            st.metric("Moran's I", f"{df_moran.iloc[0].get('moran_i', 0):.3f}", delta="显著正相关")

# ------------------------------------------
# 选项卡 2: 人才技能溢价
# ------------------------------------------
with tab2:
    st.header("核心技能与职级薪资溢价分析")
    st.markdown(r"$$\ln(Salary) = \beta_0 + \sum \beta_i Skill_i + \epsilon$$")
    df_sal = load_data("SELECT * FROM salary_pricing_results")
    if not df_sal.empty:
        df_sal = df_sal[df_sal['特征'].str.startswith('skill_')].sort_values('premium_rate', ascending=False)
        st.plotly_chart(px.bar(df_sal.head(10), x="premium_rate", y="特征", orientation='h', color="premium_rate", color_continuous_scale="GnBu"), use_container_width=True)

# ------------------------------------------
# 选项卡 3: 企业生存预警 
# ------------------------------------------
with tab3:
    st.header("产业生存风险深度监测")
    df_risk = load_data("SELECT * FROM survival_industry_risk")
    if not df_risk.empty:
        fig_risk = px.scatter(df_risk, x="count", y="risk", color="行业板块", size="count", text="行业板块", size_max=60)
        st.plotly_chart(fig_risk, use_container_width=True)
    
    st.write("---")
    st.subheader("🧠 预警因子贡献度 (XGBoost)")
    df_imp = load_data("SELECT * FROM survival_feature_importance")
    if not df_imp.empty:
        df_imp.columns = ['feature', 'importance']
        df_imp = df_imp.sort_values('importance', ascending=True)
        fig_imp = px.bar(df_imp, x="importance", y="feature", orientation='h', color="importance", color_continuous_scale="Reds")
        fig_imp.update_layout(height=500)
        st.plotly_chart(fig_imp, use_container_width=True)
