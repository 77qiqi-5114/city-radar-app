import streamlit as st
import pandas as pd
import plotly.express as px
from sqlalchemy import create_engine
import folium
from streamlit_folium import st_folium
from folium.plugins import MarkerCluster
import requests

# ==========================================
# 0. 页面配置与固定统计数据
# ==========================================
st.set_page_config(page_title="城市产业与人才空间雷达系统", page_icon="📡", layout="wide")

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

st.markdown("""
    <style>
    .main .block-container { color: #1f1f1f !important; }
    h1, h2, h3 { color: #000000 !important; font-weight: 800 !important; }
    div[data-testid="stMetric"] {
        background-color: #ffffff !important; border: 1px solid #d1d1d1 !important;
        padding: 20px !important; border-radius: 12px !important; box-shadow: 0 4px 10px rgba(0,0,0,0.08) !important;
    }
    div[data-testid="stMetricLabel"] { color: #555555 !important; font-weight: bold !important; }
    div[data-testid="stMetricValue"] { color: #000000 !important; font-size: 2rem !important; }
    .css-1d391kg { background-color: #f8f9fa !important; }
    </style>
    """, unsafe_allow_html=True)

industry_dict = {
    'A': '农林牧渔', 'B': '采矿业', 'C': '制造业', 'D': '电力热力', 'E': '建筑业', 
    'F': '批发零售', 'G': '交运邮政', 'H': '住宿餐饮', 'I': '信息技术', 'J': '金融业', 
    'K': '房地产业', 'L': '租赁商务', 'M': '科研技术', 'N': '环境管理', 'O': '居民服务', 
    'P': '教育', 'Q': '卫生工作', 'R': '文体娱乐', 'S': '公共管理'
}

# ==========================================
# 1. 数据库连接与智能加载
# ==========================================
@st.cache_resource
def init_connection():
    try:
        return create_engine(st.secrets["DB_URL"])
    except Exception as e:
        st.error(f"❌ 数据库配置缺失: {e}")
        st.stop()

engine = init_connection()

# 🚨 修复：恢复成直接执行具体 SQL，避免一次性拉取 7 万条数据导致内存崩溃
@st.cache_data(ttl=300)
def load_data(query):
    try:
        df = pd.read_sql(query, engine)
        df.columns = [str(c).lower().strip() for c in df.columns]
        return df
    except Exception:
        return pd.DataFrame()

@st.cache_data
def get_city_boundary(adcode):
    try: return requests.get(f"https://geo.datav.aliyun.com/areas_v3/bound/{adcode}_full.json").json()
    except: return None

# ==========================================
# 2. 侧边栏
# ==========================================
with st.sidebar:
    st.title("📡 City-Radar v5.2")
    # ✅ 这里改成了你需要的文字
    st.success("✨ 系统运行环境正常 | 云端已连接") 
    city_choice = st.radio("📍 选择分析城市：", ["北京", "苏州", "深圳"])
    if st.button("🔄 刷新系统缓存"):
        st.cache_data.clear()
        st.rerun()

st.title("🏙️ 城市产业与人才空间雷达系统")
tab1, tab2, tab3 = st.tabs(["📍 空间聚类格局", "💰 人才技能溢价", "🚨 企业生存预警"])

# ------------------------------------------
# 选项卡 1: 空间聚类格局
# ------------------------------------------
with tab1:
    city_map = {"北京": {"code": 110000, "adcode": 110000}, "苏州": {"code": 320500, "adcode": 320500}, "深圳": {"code": 440300, "adcode": 440300}}
    sel = city_map[city_choice]
    
    m_col, i_col = st.columns([2.5, 1])
    with m_col:
        st.subheader(f"🗺️ {city_choice}·产业集聚分布图")
        # 🚨 修复：让数据库自己去挑 5000 条，瞬间加载完成
        df_map = load_data(f"SELECT * FROM spatial_cluster_results WHERE 城市代码 = {sel['code']} LIMIT 5000")
        
        if not df_map.empty:
            m = folium.Map(location=[df_map['lat'].mean(), df_map['lng'].mean()], zoom_start=11, tiles='http://webrd02.is.autonavi.com/appmaptile?lang=zh_cn&size=1&scale=1&style=7&x={x}&y={y}&z={z}', attr='高德地图')
            geo = get_city_boundary(sel['adcode'])
            if geo: folium.GeoJson(geo, style_function=lambda x: {'color': '#3498db', 'weight': 2, 'fillOpacity': 0.05}).add_to(m)
            
            mc = MarkerCluster().add_to(m)
            for _, r in df_map.iterrows():
                is_cls = r.get('cluster_label', -1) >= 0
                ind_name = industry_dict.get(str(r.get('行业门类', '未知')), "其他")
                comp_name = str(r.get('企业名称', '未知'))
                short_comp = comp_name[:8] + "..." if len(comp_name) > 8 else comp_name 
                
                popup_html = f"<b>企业ID:</b> {short_comp}<br><b>行业:</b> {ind_name}"
                folium.CircleMarker([r['lat'], r['lng']], radius=5 if is_cls else 3, color='#FF3366' if is_cls else '#1abc9c', fill=True, fill_opacity=0.7, popup=folium.Popup(popup_html, max_width=250)).add_to(mc)
            
            st_folium(m, width=900, height=550, returned_objects=[], key=f"map_{city_choice}")
        else:
            st.warning("⚠️ 暂无该城市的地理坐标数据。")

    with i_col:
        st.subheader("📋 ANN 显著性检验")
        ann_table = pd.DataFrame(FIXED_ANN_DATA[city_choice])
        st.table(ann_table)
        
        st.write("---")
        st.subheader("📊 空间统计诊断")
        df_moran = load_data(f"SELECT * FROM spatial_moran_results WHERE 城市 = '{city_choice}'")
        if not df_moran.empty:
            res = df_moran.iloc[0]
            st.metric("Moran's I", f"{res.get('moran_i', 0):.3f}", delta="显著正相关")
            st.caption(f"**Z-Score:** {res.get('z_score', 0):.2f}")
            st.caption(f"**P-Value:** {res.get('p_value', 0):.4f}")

# ------------------------------------------
# 选项卡 2: 人才技能溢价
# ------------------------------------------
with tab2:
    st.header("核心技能与职级薪资溢价分析")
    df_sal_all = load_data("SELECT * FROM salary_pricing_results")
    
    if not df_sal_all.empty and '特征' in df_sal_all.columns:
        df_sal = df_sal_all[df_sal_all['特征'].astype(str).str.startswith('skill_')].sort_values('premium_rate', ascending=False)
        
        if not df_sal.empty:
            c1, c2 = st.columns([1, 2])
            with c1:
                st.markdown("### 💎 核心价值发现")
                top = df_sal.iloc[0]
                st.title(str(top['特征']).replace('skill_', ''))
                st.metric("模型预测溢价", f"+{top.get('premium_rate', 0):.1f}%")
            
            with c2:
                fig = px.bar(df_sal, x="premium_rate", y="特征", orientation='h', color="premium_rate", color_continuous_scale="GnBu")
                st.plotly_chart(fig, use_container_width=True)
                
            # ✅ 这里完美保留了你要求的数学公式和JSON参数
            with st.expander("🛠️ 查看详细模型评估"):
                st.markdown("**核心评估函数 (Hedonic Wage Model):**")
                st.latex(r"\ln(Salary) = \beta_0 + \sum_{i=1}^{n} \beta_i \cdot Skill_i + \gamma \cdot Controls + \epsilon")
                
                st.markdown("**模型效度评估结果:**")
                FIXED_EVAL_DATA = {
                    "Model_Architecture": "Gradient Boosting + OLS",
                    "R_Squared (拟合优度)": 0.784,
                    "Adjusted_R2": 0.781,
                    "RMSE (均方根误差)": 1420.5,
                    "F_Statistic": 452.3,
                    "P_Value": "< 0.0001",
                    "Sample_Size (样本量)": 68520
                }
                st.json(FIXED_EVAL_DATA)
        else:
            st.info("数据表中没有找到相关技能特征。")
    else:
        st.warning("💡 当前数据库暂无薪资溢价分析结果。")

# ------------------------------------------
# 选项卡 3: 企业生存预警
# ------------------------------------------
with tab3:
    st.header("产业生存风险深度监测")
    df_risk = load_data("SELECT * FROM survival_industry_risk")
    if not df_risk.empty:
        fig_risk = px.scatter(df_risk, x="count", y="risk", size="count", color="行业板块", text="行业板块")
        st.plotly_chart(fig_risk, use_container_width=True)
    
    st.write("---")
    st.subheader("🧠 预警因子贡献度 (XGBoost)")
    df_imp = load_data("SELECT * FROM survival_feature_importance")
    
    if not df_imp.empty and len(df_imp.columns) >= 2:
        df_imp = df_imp.iloc[:, :2]  # 保险起见，只取前两列
        df_imp.columns = ['feature', 'importance']
        df_imp = df_imp.sort_values('importance', ascending=False)
        fig_imp = px.bar(df_imp, x="importance", y="feature", orientation='h', color="importance", color_continuous_scale="Reds")
        st.plotly_chart(fig_imp, use_container_width=True)
    else:
        st.warning("💡 当前数据库暂无生存预警因子权重数据。")