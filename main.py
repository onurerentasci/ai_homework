# streamlit run main.py
import streamlit as st
import pandas as pd
import numpy as np
import joblib
from currency_converter import CurrencyConverter
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

c = CurrencyConverter()
currency = c.convert(1, "USD", "TRY")

# Özel sayfa yapılandırmasını ayarla
st.set_page_config(page_title="AIrabam.com", page_icon="🅰️")

# Veri setini yükle
car = pd.read_csv("Car_cleaned_with_Model.csv")


# Markaya göre modelleri filtreleme fonksiyonu
def find_model(brand):
    model = car[car["Brand"] == brand]["Model"]
    return list(model)


# Modelleri önbellekleme ile yükleme fonksiyonu
@st.cache_data
def model_loader(path):
    model = joblib.load(path)
    return model


# Tahmin edilen fiyat üzerinden vergileri hesaplama fonksiyonu
def calculate_taxes(pred, engineV):
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
    for (vol_limit, price_limit), rate in otv_rates.items():
        if engineV <= vol_limit and pred <= price_limit:
            otv_rate = rate
            break

    # ÖTV'yi hesapla
    otv = pred * otv_rate

    # KDV'yi hesapla
    kdv = (pred + otv) * 0.20

    # Nihai fiyatı hesapla
    final_price = pred + otv + kdv

    return otv, kdv, round(final_price, 2)


# Arka plan rengini ayarlama fonksiyonu
def set_background_color():
    st.markdown(
        """
        <style>
        .custom-markdown {
            background-color: rgba(252, 252, 3, 0.3);
            padding-left: 20px;
            padding-right: 20px;
            padding-top: 10px;
            padding-bottom: 10px;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


# Random Forest modelini yükle
with st.spinner("⚠️"):
    model_forest = model_loader("rf1_base_rf.pkl")

# Uygulama başlığı
st.markdown(
    "<h1 style='text-align: center; margin-bottom: 20px;'>"
    "<span style='background-color: #a503fc; border-radius: 10px; color: black; padding-left:8px; padding-right:8px'>AI</span>rabam<span style='color:#a503fc;'>.</span>com</h1>",
    unsafe_allow_html=True,
)

# Giriş alanları için iki sütun oluştur
col1, col2 = st.columns(2)

# Kilometre girişi
mileage = col1.number_input(label="Aracınızın km'sini yazınız. [ör: 20000 km]")

# Üretim yılı kaydırıcısı
year = col1.slider("Aracınızın üretildiği yılı seçin [ör: 2005]", 1980, 2020, 2005)

# Marka seçimi
brand_inp = col1.selectbox(label="Aracınızın markasını girin", options=brand_list)
brand = brand_dic[brand_inp]

# Motor tipi seçimi
engine_type = col1.selectbox(label="Yakıt Türünüzü Seçin", options=engine_type_list)
engine_type = engine_type_dic[engine_type]

# Motor hacmi girişi
engineV = col2.number_input(
    label="Araba motorunun hacmini girin. [ör: 1.3]", max_value=6.4
)
engineV = float(engineV)

# Kasa tipi seçimi
body_type = col2.selectbox(label="Aracınızın kasa tipini giriniz", options=body_list)
body_type = body_dic[body_type]

# Markaya göre model seçimi
model_inp = col2.selectbox(
    f"{brand_inp}, olarak seçmiş olduğunuz aracın modelini seçiniz",
    options=find_model(brand_inp),
)
model = model_dic[model_inp]

# Tescil durumu seçimi
regis = col2.selectbox(label="Araç Trafiğe kayıtlı mı?", options=registration_list)
regis = registration_dic[regis]

# Tahmin için giriş dizisi oluştur
inp_array = np.array(
    [[mileage, engineV, year, brand, body_type, engine_type, regis, model]]
)

# Tahmin butonu
predict = col2.button("Tahmini Fiyat")

# Tahmin sonucunu göster
if predict:
    pred = model_forest.predict(inp_array)
    if pred < 0:
        st.error(
            "Giriş değerleri birbiriyle alakasız görünüyor, ilgili bilgileri vererek tekrar deneyin."
        )
    else:
        pred = round(float(pred), 3)
        pred = c.convert(pred, "USD", "TRY")
        st.success(f"Aracınızın tahmini vergisiz satış fiyatı: {pred:.2f} ₺")
        otv_amount, kdv_amount, final_price = calculate_taxes(pred, engineV)
        set_background_color()
        st.markdown(
            f"<div class='custom-markdown'>Güncel Dolar Kuru: {currency:.2f}₺ <br> ÖTV Miktarı: {otv_amount:.2f}₺ <br> KDV Miktarı: {kdv_amount:.2f}₺ <br> Aracınızın tahmini vergili satış fiyatı: {final_price}₺</div>",
            unsafe_allow_html=True,
        )
