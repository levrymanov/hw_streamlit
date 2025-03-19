import streamlit as st
import pandas as pd
import altair as alt
import requests
from datetime import datetime

st.title("Панель погоды")
data_file = st.file_uploader("Загрузите CSV с историческими данными", type=["csv"])
city_list = ["Moscow", "London", "New York", "Tokyo"]
selected_city = st.selectbox("Выберите город", city_list)
api_key = st.text_input("API ключ OpenWeatherMap", type="password")

if data_file:
    df = pd.read_csv(data_file)
    if selected_city not in df["city"].unique():
        st.warning("Нет данных для выбранного города.")
    else:
        city_df = df[df["city"] == selected_city].copy()
        st.subheader("Описательная статистика")
        st.write(city_df["temperature"].describe())

        city_df["timestamp"] = pd.to_datetime(city_df["timestamp"])
        mean_temp = city_df["temperature"].mean()
        std_temp = city_df["temperature"].std()
        city_df["outlier"] = (city_df["temperature"] - mean_temp).abs() > 3 * std_temp

        base_chart = alt.Chart(city_df).mark_line(point=True).encode(
            x="timestamp:T", y="temperature:Q"
        ).properties(title="График изменения температуры")
        outliers = alt.Chart(city_df[city_df["outlier"]]).mark_point(color="red", size=100).encode(
            x="timestamp:T", y="temperature:Q"
        )
        st.altair_chart(base_chart + outliers, use_container_width=True)

        city_df["Month"] = city_df["timestamp"].dt.month
        season_mean = city_df.groupby("Month")["temperature"].mean()
        season_std = city_df.groupby("Month")["temperature"].std()
        st.subheader("Сезонные профили")
        st.write("Среднее:", season_mean)
        st.write("Стандартное отклонение:", season_std)

        if api_key:
            resp = requests.get(
                f"https://api.openweathermap.org/data/2.5/weather?q={selected_city}&appid={api_key}&units=metric"
            )
            if resp.status_code == 401:
                st.error('{"cod":401,"message":"Invalid API key. Please see https://openweathermap.org/faq#error401 for more info"}')
            else:
                current_temp = resp.json()["main"]["temp"]
                st.subheader("Текущая температура")
                st.write(f"{current_temp} °C")
                month = datetime.now().month
                avg = season_mean.get(month, mean_temp)
                std = season_std.get(month, std_temp)
                if avg - std <= current_temp <= avg + std:
                    st.write("Температура в пределах нормальных значений для сезона.")
                else:
                    st.write("Температура необычна для этого сезона.")
else:
    st.warning("Пожалуйста, загрузите CSV файл.")