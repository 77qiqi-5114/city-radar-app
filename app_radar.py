import streamlit as st
import pandas as pd
import plotly.express as px
from sqlalchemy import create_engine

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
# 1. 数据库
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
# 2. 界面渲染
# ==========================================
with st.sidebar:
    st.title("📡 City-Radar v5.5")
    st.success("✨ 欢迎使用城市产业与人才空间雷达系统") 
    city_choice = st.radio("📍 选择分析城市：", ["北京", "苏州", "深圳"])

st.title("🏙️ 城市产业与人才空间雷达系统")
tab1, tab2, tab3 = st.tabs(["📍 空间聚类格局", "💰 人才技能溢价", "🚨 企业生存预警"])

with tab1:
    city_cfg = {"北京": {"code": 110000}, "苏州": {"code": 320500}, "深圳": {"code": 440300}}
    sel = city_cfg[city_choice]
    m_col, i_col = st.columns([2.5, 1])
    
    with m_col:
        st.subheader(f"🗺️ {city_choice}·产业集聚分布图")
        df_map = load_data(f"SELECT * FROM spatial_cluster_results WHERE 城市代码 = {sel['code']} LIMIT 5000")
        if not df_map.empty:
            df_map['行业名称'] = df_map['行业门类'].astype(str).map(industry_dict).fillna("其他")
            df_map['显示名称'] = df_map['企业名称'].astype(str).apply(lambda x: x[:10]+'...' if len(x)>10 else x)
            
            # 使用 open-street-map 底图，找回“原来的感觉”
            fig = px.scatter_mapbox(
                df_map, lat="lat", lon="lng",
                hover_name="显示名称", hover_data={"lat":False, "lng":False, "行业名称":True},
                color_discrete_sequence=["#FF3366"], zoom=9.5, height=600
            )
            fig.update_layout(
                mapbox_style="open-street-map", # 这里改成了标准彩色地图样式
                margin={"r":0,"t":0,"l":0,"b":0}
            )
            st.plotly_chart(fig, use_container_width=True)
        else: st.info("数据加载中...")

    with i_col:
        st.subheader("📋 ANN 显著性检验")
        st.table(pd.DataFrame(FIXED_ANN_DATA[city_choice]))
        st.write("---")
        st.subheader("📊 空间统计诊断")
        df_moran = load_data(f"SELECT * FROM spatial_moran_results WHERE 城市 = '{city_choice}'")
        if not df_moran.empty:
            res = df_moran.iloc[0]
            st.metric("Moran's I", f"{res.get('moran_i', 0):.3f}", delta="显著正相关")

with tab2:
    st.header("核心技能与职级薪资溢价分析")
    df_sal = load_data("SELECT * FROM salary_pricing_results")
    if not df_sal.empty:
        df_sal = df_sal[df_sal['特征'].str.startswith('skill_')].sort_values('premium_rate', ascending=False)
        c1, c2 = st.columns([1, 2])
        with c1:
            if not df_sal.empty:
                st.metric("最高溢价技能", str(df_sal.iloc[0]['特征']).replace('skill_', ''), f"+{df_sal.iloc[0]['premium_rate']:.1f}%")
        with c2:
            st.plotly_chart(px.bar(df_sal, x="premium_rate", y="特征", orientation='h', color="premium_rate"), use_container_width=True)
    with st.expander("🛠️ 模型公式"):
        st.markdown(r"$$\ln(Salary) = \beta_0 + \sum \beta_i Skill_i + \epsilon$$")

with tab3:
    st.header("产业生存风险深度监测")
    df_risk = load_data("SELECT * FROM survival_industry_risk")
    if not df_risk.empty:
        st.plotly_chart(px.scatter(df_risk, x="count", y="risk", size="count", color="行业板块", text="行业板块"), use_container_width=True)
