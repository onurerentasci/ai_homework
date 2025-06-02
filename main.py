# streamlit run main.py
import streamlit as st
import pandas as pd
import numpy as np
import joblib
import plotly.express as px
import plotly.graph_objects as go
from currency_converter import CurrencyConverter
from datetime import datetime
from config import (
    brand_dic,
    body_dic,
    engine_type_dic,
    registration_dic,
    model_dic,
    brand_list,
    body_list,
    engine_type_list,
    registration_list,
)

# Uygulama yapılandırması
st.set_page_config(
    page_title="🚗 AIrabam.com - Araç Değer Tahmin Sistemi",
    page_icon="🚗",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Global CSS stilleri
def load_css():
    st.markdown("""
    <style>
    .main {
        padding-top: 2rem;
    }
    
    .stTabs [data-baseweb="tab-list"] {
        gap: 2rem;
    }
    
    .stTabs [data-baseweb="tab"] {
        height: 3rem;
        padding-left: 1.5rem;
        padding-right: 1.5rem;
        border-radius: 0.5rem;
        background-color: #f0f2f6;
        color: #262730;
        font-weight: 600;
    }
    
    .stTabs [aria-selected="true"] {
        background-color: #ff4b4b;
        color: white;
    }
    
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 1rem;
        color: white;
        text-align: center;
        margin: 1rem 0;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    
    .prediction-result {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        padding: 0.5rem;
        border-radius: 1rem;
        color: white;
        text-align: center;
        margin: 2rem 0;
        box-shadow: 0 8px 16px rgba(0, 0, 0, 0.1);
    }
    
    .info-card {
        background: #f8f9fa;
        padding: 1.5rem;
        border-radius: 1rem;
        border-left: 4px solid #ff4b4b;
        margin: 1rem 0;
    }
    
    .header-title {
        text-align: center;
        padding: 2rem 0;
        color: #1f2937;
        font-size: 3rem;
        font-weight: 700;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }
    
    .sidebar-info {
        background: #f0f8ff;
        padding: 0.2rem;
        border-radius: 0.5rem;
        border: 1px solid #e0e7ff;
    }
    </style>
    """, unsafe_allow_html=True)

# Currency converter ve veri yükleme
@st.cache_data
def load_data():
    try:
        c = CurrencyConverter()
        currency = c.convert(1, "USD", "TRY")
        car = pd.read_csv("processedData/Car_cleaned_with_Model.csv")
        return c, currency, car
    except Exception as e:
        st.error(f"Veri yükleme hatası: {e}")
        return None, None, None

c, currency, car = load_data()

# Utility functions
@st.cache_data
def find_model(brand):
    """Markaya göre modelleri filtreleme fonksiyonu"""
    if car is not None:
        model_list = car[car["Brand"] == brand]["Model"].unique().tolist()
        return sorted(model_list)
    return []

@st.cache_data
def model_loader(path):
    """Modelleri önbellekleme ile yükleme fonksiyonu"""
    try:
        model = joblib.load(path)
        return model
    except Exception as e:
        st.error(f"Model yükleme hatası: {e}")
        return None

def calculate_taxes(pred, engineV):
    """Tahmin edilen fiyat üzerinden vergileri hesaplama fonksiyonu"""
    # Motor hacmine ve taban fiyatına göre ÖTV oranlarını tanımla
    otv_rates = {
        (1600, 184000): 0.45,
        (1600, 220000): 0.50,
        (1600, 250000): 0.60,
        (1600, 280000): 0.70,
        (1600, float("inf")): 0.80,
        (2000, 170000): 1.30,
        (2000, float("inf")): 1.50,
        (float("inf"), float("inf")): 2.20,
    }

    # Uygulanabilir ÖTV oranını belirle
    otv_rate = 2.20  # Default rate
    for (vol_limit, price_limit), rate in otv_rates.items():
        if engineV <= vol_limit and pred <= price_limit:
            otv_rate = rate
            break

    # Vergileri hesapla
    otv = pred * otv_rate
    kdv = (pred + otv) * 0.20
    final_price = pred + otv + kdv

    return otv, kdv, round(final_price, 2)

def create_prediction_chart(pred, otv, kdv, final_price):
    """Tahmin sonuçları için görsel grafik oluştur"""
    labels = ['Temel Fiyat', 'ÖTV', 'KDV', 'Toplam Fiyat']
    values = [pred, otv, kdv, final_price]
    colors = ['#3498db', '#e74c3c', '#f39c12', '#2ecc71']
    
    fig = go.Figure(data=[
        go.Bar(x=labels, y=values, marker_color=colors, text=values, 
               texttemplate='%{text:,.0f} ₺', textposition='outside')
    ])
    
    fig.update_layout(
        title="Fiyat Analizi",
        xaxis_title="Bileşenler",
        yaxis_title="Fiyat (₺)",
        template="plotly_white",
        height=400
    )
    
    return fig

def show_statistics():
    """Veri seti istatistikleri göster"""
    if car is not None:
        st.subheader("📊 Veri Seti İstatistikleri")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Toplam Araç", len(car))
        
        with col2:
            st.metric("Marka Sayısı", car['Brand'].nunique())
        
        with col3:
            st.metric("Model Sayısı", car['Model'].nunique())
        
        # Brand distribution chart
        brand_counts = car['Brand'].value_counts()
        fig_brands = px.pie(
            values=brand_counts.values, 
            names=brand_counts.index,
            title="Markalara Göre Dağılım"
        )
        st.plotly_chart(fig_brands, use_container_width=True)

# CSS yükleme
load_css()

# Model yükleme
with st.spinner("🚗 Model yükleniyor..."):
    model_forest = model_loader("random_forest.pkl")

# Ana başlık
st.markdown('<h1 class="header-title">🚗 AIrabam.com</h1>', unsafe_allow_html=True)
st.markdown('<p style="text-align: center; font-size: 1.2rem; color: #6b7280; margin-bottom: 2rem;">Yapay Zeka Destekli Araç Değer Tahmin Sistemi</p>', unsafe_allow_html=True)

# Sidebar için bilgi
with st.sidebar:
    st.markdown('<div class="sidebar-info">', unsafe_allow_html=True)
    st.markdown("### 📋 Nasıl Kullanılır?")
    st.markdown("""
    1. **Araç Bilgilerinizi Girin**: Kilometre, yıl, marka, model vb.
    2. **Tahmin Alın**: Yapay zeka modelimiz aracınızın değerini hesaplar
    3. **Vergi Analizi**: ÖTV ve KDV dahil toplam maliyeti görün
    """)
    st.markdown('</div>', unsafe_allow_html=True)
    
    if currency:
        st.markdown(f"💱 **Güncel USD/TRY:** {currency:.2f} ₺")
    
    st.markdown("---")
    st.markdown("### 🎯 Model Bilgileri")
    st.info("Extra Trees algoritması kullanılarak eğitilmiş model")

# Ana içerik - Tab yapısı
tab1, tab2, tab3 = st.tabs(["🏠 Fiyat Tahmini", "📊 İstatistikler", "ℹ️ Hakkında"])

with tab1:
    if model_forest is None or car is None:
        st.error("❌ Uygulama başlatılamadı. Lütfen dosyaların mevcut olduğundan emin olun.")
        st.stop()
    
    # Form alanları
    with st.form("prediction_form"):
        st.markdown("### 🚙 Araç Bilgilerinizi Girin")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### 📝 Temel Bilgiler")
            mileage = st.number_input(
                "🛣️ Kilometre", 
                min_value=0, 
                max_value=1000000, 
                value=50000,
                step=1000,
                help="Aracınızın toplam kilometresi"
            )
            
            year = st.slider(
                "📅 Üretim Yılı", 
                min_value=1980, 
                max_value=2024, 
                value=2010,
                help="Aracınızın üretildiği yıl"
            )
            
            brand_inp = st.selectbox(
                "🏭 Marka", 
                options=brand_list,
                help="Aracınızın markası"
            )
            
            engine_type_inp = st.selectbox(
                "⛽ Yakıt Türü", 
                options=engine_type_list,
                help="Aracınızın yakıt türü"
            )
        
        with col2:
            st.markdown("#### 🔧 Teknik Özellikler")
            engineV = st.number_input(
                "🔧 Motor Hacmi (L)", 
                min_value=0.8, 
                max_value=6.4, 
                value=1.6,
                step=0.1,
                help="Motor hacmi litre cinsinden"
            )
            
            body_type_inp = st.selectbox(
                "🚗 Kasa Tipi", 
                options=body_list,
                help="Aracınızın kasa türü"
            )
            
            # Dinamik model seçimi
            available_models = find_model(brand_inp)
            if available_models:
                model_inp = st.selectbox(
                    f"🎯 {brand_inp} Modeli", 
                    options=available_models,
                    help=f"{brand_inp} markasına ait modeller"
                )
            else:
                st.warning(f"⚠️ {brand_inp} markası için model bulunamadı")
                model_inp = None
            
            regis_inp = st.selectbox(
                "📋 Trafik Kaydı", 
                options=registration_list,
                help="Araç trafiğe kayıtlı mı?"
            )
        
        # Tahmin butonu
        predict_button = st.form_submit_button(
            "🎯 Fiyat Tahmini Yap", 
            type="primary",
            use_container_width=True
        )
    
    # Tahmin işlemi
    if predict_button and model_inp:
        try:
            # Değerleri dönüştür
            brand = brand_dic[brand_inp]
            engine_type = engine_type_dic[engine_type_inp]
            body_type = body_dic[body_type_inp]
            model = model_dic[model_inp]
            regis = registration_dic[regis_inp]
            
            # Tahmin dizisi oluştur
            inp_array = np.array([[mileage, engineV, year, brand, body_type, engine_type, regis, model]])
            
            # Tahmin yap
            with st.spinner("🔮 Tahmin hesaplanıyor..."):
                pred = model_forest.predict(inp_array)[0]
            
            if pred < 0:
                st.error("❌ Geçersiz tahmin sonucu. Lütfen girilen değerleri kontrol edin.")
            else:
                pred_usd = round(float(pred), 2)
                pred_try = c.convert(pred_usd, "USD", "TRY") if c else pred_usd * currency
                
                # Vergi hesaplamaları
                otv_amount, kdv_amount, final_price = calculate_taxes(pred_try, engineV * 1000)
                
                # Sonuçları göster
                st.markdown('<div class="prediction-result">', unsafe_allow_html=True)
                st.markdown("## 🎯 Tahmin Sonuçları")
                
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("💰 Temel Fiyat", f"{pred_try:,.0f} ₺")
                
                with col2:
                    st.metric("📊 ÖTV", f"{otv_amount:,.0f} ₺")
                
                with col3:
                    st.metric("💸 KDV", f"{kdv_amount:,.0f} ₺")
                
                with col4:
                    st.metric("🏆 Toplam Fiyat", f"{final_price:,.0f} ₺")
                
                st.markdown('</div>', unsafe_allow_html=True)
                
                # Grafik göster
                fig = create_prediction_chart(pred_try, otv_amount, kdv_amount, final_price)
                st.plotly_chart(fig, use_container_width=True)
                
                # Detaylı bilgi
                with st.expander("📋 Detaylı Analiz"):
                    st.markdown(f"""
                    **Araç Özellikleri:**
                    - 🚗 **Marka/Model:** {brand_inp} {model_inp}
                    - 📅 **Yıl:** {year}
                    - 🛣️ **Kilometre:** {mileage:,} km
                    - ⛽ **Yakıt:** {engine_type_inp}
                    - 🔧 **Motor:** {engineV}L
                    - 🚙 **Kasa:** {body_type_inp}
                    - 📋 **Tescil:** {"Evet" if regis_inp == "yes" else "Hayır"}
                    
                    **Fiyat Analizi:**
                    - 💵 **USD Fiyat:** ${pred_usd:,.2f}
                    - 🔄 **Döviz Kuru:** {currency:.2f} ₺/USD
                    - 📈 **ÖTV Oranı:** %{(otv_amount/pred_try)*100:.1f}
                    - 📈 **KDV Oranı:** %20
                    """)
        
        except Exception as e:
            st.error(f"❌ Tahmin sırasında hata oluştu: {str(e)}")

with tab2:
    show_statistics()

with tab3:
    st.markdown("### 🎯 AIrabam.com Hakkında")
    
    st.markdown("""
    **AIrabam.com**, yapay zeka destekli bir araç değer tahmin sistemidir. 
    Modern machine learning teknikleri kullanarak aracınızın piyasa değerini hesaplar.
    
    #### 🔧 Teknik Özellikler:
    - **Algorithm:** Extra Trees Regression
    - **Framework:** Streamlit
    - **Visualization:** Plotly
    - **Data Processing:** Pandas, NumPy
    - **Currency:** Real-time USD/TRY conversion
    
    #### 📊 Model Performansı:
    - Binlerce araç verisi ile eğitilmiş
    - Sürekli güncellenen döviz kurları
    - Detaylı vergi hesaplamaları
    - Gerçek zamanlı tahminler
    
    #### 🎨 Özellikler:
    - ✅ Modern ve kullanıcı dostu arayüz
    - ✅ Responsive tasarım
    - ✅ Detaylı vergi analizi
    - ✅ İnteraktif grafikler
    - ✅ Kapsamlı istatistikler
    """)
    
    st.info("💡 Bu uygulama eğitim amaçlı geliştirilmiştir. Gerçek alım-satım kararlarında profesyonel ekspertiz alınması önerilir.")

# Footer
st.markdown("---")
st.markdown(
    '<p style="text-align: center; color: #6b7280; font-size: 0.9rem;">© 2025 AIrabam.com - Yapay Zeka Destekli Araç Değerlendirme Sistemi</p>', 
    unsafe_allow_html=True
)
