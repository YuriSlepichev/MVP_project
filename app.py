import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st

# Шапка страницы
st.set_page_config(page_title="Анализ зарплат и ВВП в России", layout="wide")
st.title("📊 Анализ зарплат и ВВП в России")

# Загрузка файлов
st.header("⬇️ Шаг 1. Загрузите данные")
st.markdown("**Пример таблицы с номинальными зарплатами (отрасли — строки, (годы по возрастанию) — столбцы):**")
st.image("зарплаты_пример.png", use_container_width=True)
wages_file = st.file_uploader("Загрузите файл с номинальными зарплатами", type=["xlsx"])
st.markdown("**Пример таблицы с номинальным ВВП:**")
st.image("ввп_пример.png", use_container_width=True)
gdp_file = st.file_uploader("Загрузите файл с номинальным ВВП", type=["xlsx"])
st.markdown("**Пример таблицы с инфляцией (годы — по возрастанию):**")
st.image("инфляция_пример.png", use_container_width=True)
inflation_file = st.file_uploader("Загрузите файл с инфляцией по годам", type=["xlsx"])

if wages_file and gdp_file and inflation_file:
    # Загрузка и обработка зарплат
    wages_df = pd.read_excel(wages_file, header=None)

    # Первая строка — годы
    wages_years = wages_df.iloc[0, 1:]
    numeric_years = pd.to_numeric(wages_years, errors='coerce')
    wages_df.columns = ['Отрасль'] + numeric_years.tolist()

    wages_df = wages_df.drop(index=0)

    # Устанавливаем индекс — отрасли
    wages_df.set_index('Отрасль', inplace=True)

    # Удаляем столбцы с нечисловыми годами
    wages_df = wages_df.loc[:, ~wages_df.columns.isna()]

    # Преобразуем значения в числа
    wages_df = wages_df.apply(pd.to_numeric, errors='coerce')

    # Отрасли
    industries = wages_df.index.tolist()
    default_options = [name for name in ['Добыча полезных ископаемых', 'Финансовая деятельность'] if name in industries]
    selected = st.multiselect("Выберите отрасли для анализа:", industries, default=default_options)

    if selected:
        selected_wages = wages_df.loc[selected].transpose()
        selected_wages.index = selected_wages.index.astype(int)

        # Загрузка и обработка ВВП
        gdp_df = pd.read_excel(gdp_file, index_col=0).transpose()
        gdp_df.columns = ['ВВП']
        gdp_df.index = gdp_df.index.astype(int)
        gdp_series = gdp_df['ВВП']

        # Загрузка и обработка инфляции
        inflation_df = pd.read_excel(inflation_file, index_col=0).transpose()
        inflation_df.columns = ['Инфляция']
        inflation_df.index = inflation_df.index.astype(int)
        inflation_series = inflation_df['Инфляция']

        # Общие годы
        common_years = selected_wages.index.intersection(gdp_series.index).intersection(inflation_series.index)
        selected_wages = selected_wages.loc[common_years]
        gdp_series = gdp_series.loc[common_years]
        inflation_series = inflation_series.loc[common_years]

        # Реальные значения
        inflation_cum = (1 + inflation_series / 100).cumprod()
        real_wages = selected_wages.div(inflation_cum, axis=0)
        real_gdp = gdp_series.div(inflation_cum)

        # Темпы роста
        wage_growth_nominal = selected_wages.pct_change() * 100
        wage_growth_real = real_wages.pct_change() * 100
        gdp_growth = gdp_series.pct_change() * 100

        # Графики
        st.header("📈 График 1. Номинальные значения")
        fig1, ax1 = plt.subplots()
        for column in selected_wages.columns:
            ax1.plot(selected_wages.index, selected_wages[column], label=f"{column} — номинальная")
        ax1.plot(gdp_series.index, gdp_series, 'k--', label="ВВП — номинальный")
        ax1.set_title("Номинальные зарплаты и номинальный ВВП")
        ax1.set_xlabel("Год")
        ax1.set_ylabel("Значения (руб.)")
        ax1.legend()
        st.pyplot(fig1)

        st.header("📉 График 2. Реальные значения с учётом инфляции")
        fig2, ax2 = plt.subplots()
        for column in real_wages.columns:
            ax2.plot(real_wages.index, real_wages[column], label=f"{column} — реальная")
        ax2.plot(real_gdp.index, real_gdp, 'k--', label="ВВП — реальный")
        ax2.set_title("Реальные зарплаты и реальный ВВП")
        ax2.set_xlabel("Год")
        ax2.set_ylabel("Значения (реальные рубли)")
        ax2.legend()
        st.pyplot(fig2)

        st.header("📊 График 3. Темпы роста")
        fig3, ax3 = plt.subplots()
        for column in wage_growth_nominal.columns:
            ax3.plot(wage_growth_nominal.index, wage_growth_nominal[column], linestyle='--', label=f"{column} — номинальная")
        for column in wage_growth_real.columns:
            ax3.plot(wage_growth_real.index, wage_growth_real[column], label=f"{column} — реальная")
        ax3.plot(gdp_growth.index, gdp_growth, 'k-.', label="ВВП — темп роста")
        ax3.set_title("Темпы роста зарплат и ВВП по годам")
        ax3.set_xlabel("Год")
        ax3.set_ylabel("Темп роста (%)")
        ax3.legend()
        st.pyplot(fig3)

        # Аналитика
        st.header("Экономическая аналитика")

        st.subheader("CAGR по отраслям")
        for col in selected_wages.columns:
            start_val = selected_wages[col].iloc[0]
            end_val = selected_wages[col].iloc[-1]
            n_years = len(selected_wages) - 1
            if start_val > 0:
                cagr = ((end_val / start_val) ** (1 / n_years) - 1) * 100
                st.markdown(f"**{col}**: CAGR ≈ **{cagr:.2f}%** в течение {n_years} лет")
            else:
                st.markdown(f"**{col}**: невозможно рассчитать CAGR (начальное значение ≤ 0)")

        st.subheader("Годы с экстремальными значениями роста")
        for col in selected_wages.columns:
            growth_nom = selected_wages[col].pct_change().dropna() * 100
            growth_real = real_wages[col].pct_change().dropna() * 100

            if not growth_nom.empty:
                min_year_nom = growth_nom.idxmin()
                max_year_nom = growth_nom.idxmax()
                st.markdown(f"**{col}** — номинальный рост:")
                st.markdown(f"- Минимальный: **{growth_nom[min_year_nom]:.2f}%** в **{min_year_nom}**")
                st.markdown(f"- Максимальный: **{growth_nom[max_year_nom]:.2f}%** в **{max_year_nom}**")
            if not growth_real.empty:
                min_year_real = growth_real.idxmin()
                max_year_real = growth_real.idxmax()
                st.markdown(f"**{col}** — реальный рост:")
                st.markdown(f"- Минимальный: **{growth_real[min_year_real]:.2f}%** в **{min_year_real}**")
                st.markdown(f"- Максимальный: **{growth_real[max_year_real]:.2f}%** в **{max_year_real}**")

        st.subheader("Корреляция роста зарплат и ВВП")

        for col in selected_wages.columns:
            wage_growth = selected_wages[col].pct_change().dropna()
            gdp_growth_trimmed = gdp_series.pct_change().dropna()
            common_index = wage_growth.index.intersection(gdp_growth_trimmed.index)
            corr = wage_growth[common_index].corr(gdp_growth_trimmed[common_index])

            if pd.isna(corr):
                st.markdown(f"**{col}**: недостаточно данных для оценки корреляции.")
                continue

            if corr > 0.7:
                strength = "высокая положительная"
                interpretation = "зарплаты в отрасли тесно связаны с ростом ВВП"
            elif corr > 0.4:
                strength = "умеренная положительная"
                interpretation = "зарплаты в отрасли чувствительны к изменению ВВП"
            elif corr > 0.1:
                strength = "слабая положительная"
                interpretation = "зарплаты слабо зависят от ВВП"
            elif corr < -0.4:
                strength = "отрицательная"
                interpretation = "зарплаты движутся в противоположном направлении от ВВП"
            else:
                strength = "низкая"
                interpretation = "связь между зарплатами и ВВП не прослеживается"

            st.markdown(f"**{col}**: коэффициент корреляции = **{corr:.2f}** — {strength} связь: {interpretation}.")
            st.subheader("Годы, когда рост реальных зарплат обгонял инфляцию")

            for col in wage_growth_real.columns:
                try:
                    years_outpace = wage_growth_real[col][wage_growth_real[col] > inflation_series].index
                    years_outpace = list(map(int, years_outpace))
                    if years_outpace:
                        st.markdown(
                            f"**{col}**: рост зарплат обгонял инфляцию в годы: {', '.join(map(str, years_outpace))}")
                    else:
                        st.markdown(f"**{col}**: зарплаты не обгоняли инфляцию ни в один год.")
                except Exception as e:
                    st.markdown(f"**{col}**: не удалось вычислить — {e}")


    else:
        st.warning("Выберите хотя бы одну отрасль для анализа.")
else:
    st.info("Пожалуйста, загрузите все три файла для продолжения.")
