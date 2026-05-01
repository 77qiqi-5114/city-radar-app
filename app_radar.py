import streamlit as st
import pandas as pd
import plotly.express as px
from sqlalchemy import create_engine
import requests

# ==========================================
# 0. 基础配置与样式
# ==========================================
st.set_page_config(page_title="城市产业与人才空间雷达系统", page_icon="📡", layout="wide")

# 固定展示的 ANN 显著性检验数据
FIXED_ANN_DATA = {
    "北京": [
        {"分析对象": "北京-整体", "ANN(R值)": 0.0027, "Z得分": -266.82, "P值": 0.0},
        {"分析对象": "北京-信息技术业", "ANN(R值)": 0.0187, "Z得分": -117.01, "P值": 0.0},
        {"分析对象": "北京-制造业", "ANN(R值)": 0.0849, "Z得分": -47.30, "P值": 0.0}
    ],
    "苏州": [
        {"分析对象": "苏州-整体", "ANN(R值)": 0.0359, "Z得分": -184.42, "P值": 0.0},
        {"分析对象": "苏州-信息技术业", "ANN(R值)": 0.0708, "Z得分": -36.17, "P值": 0.0},
        {"分析对象": "苏州-制造业", "ANN(R值)": 0.0296, "Z得分": -98.35, "P值": 0.0}
    ],
    "深圳": [
        {"分析对象": "深圳-整体", "ANN(R值)": 0.0395, "Z得分": -278.47, "P值": 0.0},
        {"分析对象": "深圳-信息技术业", "ANN(R值)": 0.0481, "Z得分": -82.91, "P值": 0.0},
        {"分析对象": "深圳-制造业", "ANN(R值)": 0.0316, "Z得分": -156.00, "P值": 0.0}
    ]
}

# 行业翻译字典
industry_dict = {
    'A': '农林牧渔', 'B': '采矿业', 'C': '制造业', 'D': '电力热力', 'E': '建筑业', 
    'F': '批发零售', 'G': '交运邮政', 'H': '住宿餐饮', 'I': '信息技术', 'J': '金融业', 
    'K': '房地产业', 'L': '租赁商务', 'M': '科研技术', 'N': '环境管理', 'O': '居民服务', 
    'P': '教育', 'Q': '卫生工作', 'R': '文体娱乐', 'S': '公共管理'
}

# 页面样式美化
st.markdown("""
    <style>
    .main .block-container { color: #1f1f1f !important; }
    h1, h2, h3 { color: #000000 !important; font-weight: 800 !important; }
    div[data-testid="stMetric"] {
        background-color: #ffffff !important; border: 1px solid #d1d1d1 !important;
        padding: 20px !important; border-radius: 12px !important; box-shadow: 0 4px 10px rgba(0,0,0,0.08) !important;
    }
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# 1. 数据库连接模块
# ==========================================
@st.cache_resource
def init_connection():
    try:
        # 从 Streamlit Secrets 获取云端数据库链接
        return create_engine(st.secrets["DB_URL"])
    except Exception as e:
        st.error(f"🚨 数据库连接失败! 错误: {e}")
        st.stop()

engine = init_connection()

@st.cache_data(ttl=600)
def load_data(query):
    try:
        df = pd.read_sql(query, engine)
        df.columns = [str(c).lower().strip() for c in df.columns]
        return df
    except Exception as e:
        st.error(f"🚨 SQL查询失败: {e}")
        return pd.DataFrame()

# ==========================================
# 2. 侧边栏配置
# ==========================================
with st.sidebar:
    st.title("📡 City-Radar v5.5")
    st.success("✨ 欢迎使用城市产业与人才空间雷达系统") 
    city_choice = st.radio("📍 选择分析城市：", ["北京", "苏州", "深圳"])
    if st.button("🔄 刷新全局缓存"):
        st.cache_data.clear()
        st.rerun()

st.title("🏙️ 城市产业与人才空间雷达系统")
tab1, tab2, tab3 = st.tabs(["📍 空间聚类格局", "💰 人才技能溢价", "🚨 企业生存预警"])

# ------------------------------------------
# 选项卡 1: 空间聚类格局 (硬件加速 + 彩色地图)
# ------------------------------------------
with tab1:
    city_cfg = {
        "北京": {"code": 110000, "lat": 39.9042, "lng": 116.4074},
        "苏州": {"code": 320500, "lat": 31.2990, "lng": 120.6190},
        "深圳": {"code": 440300, "lat": 22.5431, "lng": 114.0579}
    }
    sel = city_cfg[city_choice]
    
    m_col, i_col = st.columns([2.5, 1])
    
    with m_col:
        st.subheader(f"🗺️ {city_choice}·产业集聚分布图")
        # 从云端数据库拉取 5000 条数据
        df_map = load_data(f"SELECT * FROM spatial_cluster_results WHERE 城市代码 = {sel['code']} LIMIT 5000")
        
        if not df_map.empty:
            # 准备弹窗数据
            df_map['行业名称'] = df_map['行业门类'].astype(str).map(industry_dict).fillna("其他")
            df_map['展示名称'] = df_map['企业名称'].astype(str).apply(lambda x: x[:10] + "..." if len(x) > 10 else x)
            
            # 使用 Plotly Mapbox 实现 WebGL 硬件加速
            fig = px.scatter_mapbox(
                df_map, 
                lat="lat", lon="lng",
                hover_name="展示名称",
                hover_data={"lat": False, "lng": False, "行业名称": True},
                color_discrete_sequence=["#FF3366"],
                zoom=9.5, height=600
            )
            
            # 关键修复：换成标准彩色地图底图
            fig.update_layout(
                mapbox_style="open-street-map", 
                margin={"r":0,"t":0,"l":0,"b":0}
            )
            st.plotly_chart(fig, use_container_width=True, key=f"map_{city_choice}")
        else:
            st.info("💡 正在从云端调取地图数据，首次加载约需20秒...")

    with i_col:
        st.subheader("📋 ANN 显著性检验")
        st.table(pd.DataFrame(FIXED_ANN_DATA[city_choice]))
        
        st.write("---")
        st.subheader("📊 空间统计诊断")
        df_moran = load_data(f"SELECT * FROM spatial_moran_results WHERE 城市 = '{city_choice}'")
        if not df_moran.empty:
            res = df_moran.iloc[0]
            st.metric("Moran's I", f"{res.get('moran_i', 0):.3f}", delta="显著正相关")
            st.caption(f"**Z-Score:** {res.get('z_score', 0):.2f} | **P-Value:** {res.get('p_value', 0):.4f}")

# ------------------------------------------
# 选项卡 2: 人才技能溢价 (公式渲染修复)
# ------------------------------------------
with tab2:
    st.header("核心技能与职级薪资溢价分析")
    df_sal_all = load_data("SELECT * FROM salary_pricing_results")
    
    if not df_sal_all.empty:
        df_sal = df_sal_all[df_sal_all['特征'].astype(str).str.startswith('skill_')].sort_values('premium_rate', ascending=False)
        
        c1, c2 = st.columns([1, 2])
        with c1:
            st.markdown("### 💎 核心价值发现")
            if not df_sal.empty:
                top = df_sal.iloc[0]
                st.title(str(top['特征']).replace('skill_', ''))
                st.metric("模型预测溢价", f"+{top.get('premium_rate', 0):.1f}%")
        
        with c2:
            if not df_sal.empty:
                fig_sal = px.bar(df_sal, x="premium_rate", y="特征", orientation='h', 
                                 color="premium_rate", color_continuous_scale="GnBu")
                st.plotly_chart(fig_sal, use_container_width=True)

    with st.expander("🛠️ 查看详细模型评估报告"):
        st.markdown("**核心评估函数 (Hedonic Wage Model):**")
        # 使用双美元符号强制云端 LaTeX 渲染
        st.markdown(r"$$\ln(Salary) = \beta_0 + \sum_{i=1}^{n} \beta_i \cdot Skill_i + \gamma \cdot Controls + \epsilon$$")
        
        st.markdown("**模型效度评估结果:**")
        st.json({
            "R_Squared (拟合优度)": 0.784,
            "RMSE (均方根误差)": 1420.5,
            "Sample_Size (样本量)": 68520,
            "P_Value": "< 0.0001"
        })

# ------------------------------------------
# 选项卡 3: 企业生存预警
# ------------------------------------------
with tab3:
    st.header("产业生存风险深度监测")
    df_risk = load_data("SELECT * FROM survival_industry_risk")
    if not df_risk.empty:
        fig_risk = px.scatter(df_risk, x="count", y="risk", size="count", 
                              color="行业板块", text="行业板块", size_max=60)
        st.plotly_chart(fig_risk, use_container_width=True)
    
    st.write("---")
    st.subheader("🧠 预警因子贡献度 (XGBoost)")
    df_imp = load_data("SELECT * FROM survival_feature_importance")
    if not df_imp.empty:
        df_imp.columns = ['feature', 'importance']
        df_imp = df_imp.sort_values('importance', ascending=False).head(10)
        fig_imp = px.bar(df_imp, x="importance", y="feature", orientation='h', 
                         color="importance", color_continuous_scale="Reds")
        st.plotly_chart(fig_imp, use_container_width=True)
