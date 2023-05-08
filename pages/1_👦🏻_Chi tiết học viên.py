import streamlit as st
import requests
import plotly.express as px
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path
import pickle
import streamlit_authenticator as stauth
import numpy as np
import ast


page_title = "Thông tin học viên"
page_icon = "👦🏻"
layout = "wide"
st.set_page_config(page_title=page_title, page_icon=page_icon, layout=layout)

# ----------------------------------------
names = ["Phạm Tấn Thành", "Phạm Minh Tâm", "Vận hành", "Kinh doanh"]
usernames = ["thanhpham", "tampham", "vietopvanhanh", 'vietopkinhdoanh']

# Load hashed password
file_path = Path(__file__).parent / 'hashed_pw.pkl'
with file_path.open("rb") as file:
    hashed_passwords = pickle.load(file)

authenticator = stauth.Authenticate(names, usernames, hashed_passwords,
                                    "sales_dashboard", "abcdef", cookie_expiry_days=1)

name, authentication_status, username = authenticator.login("Login", "main")

if authentication_status == False:
    st.error("Username/password is incorrect")

if authentication_status == None:
    st.warning("Please enter your username and password")

if authentication_status:
    authenticator.logout("logout", "main")

    # Add CSS styling to position the button on the top right corner of the page
    st.markdown(
        """
            <style>
            .stButton button {
                position: absolute;
                top: 0px;
                right: 0px;
            }
            </style>
            """,
        unsafe_allow_html=True
    )
    st.title(page_title + " " + page_icon)
    st.markdown("---")
    # ----------------------#
    # Filter
    # now = datetime.now()
    # DEFAULT_START_DATE = datetime(now.year, now.month, 1)
    # DEFAULT_END_DATE = datetime(now.year, now.month, 1) + timedelta(days=32)
    # DEFAULT_END_DATE = DEFAULT_END_DATE.replace(day=1) - timedelta(days=1)

    # # Create a form to get the date range filters
    # with st.sidebar.form(key='date_filter_form'):
    #     ketoan_start_time = st.date_input(
    #         "Select start date", value=DEFAULT_START_DATE)
    #     ketoan_end_time = st.date_input(
    #         "Select end date", value=DEFAULT_END_DATE)
    #     submit_button = st.form_submit_button(
    #         label='Filter',  use_container_width=True)

    @st.cache_data(ttl=timedelta(days=1))
    def collect_data(link):
        return (pd.DataFrame((requests.get(link).json())))

    @st.cache_data()
    def rename_lop(dataframe, column_name):
        dataframe[column_name] = dataframe[column_name].replace(
            {1: "Hoa Cúc", 2: "Gò Dầu", 3: "Lê Quang Định", 5: "Lê Hồng Phong"})
        return dataframe

    @st.cache_data()
    def grand_total(dataframe, column):
        # create a new row with the sum of each numerical column
        totals = dataframe.select_dtypes(include=[float, int]).sum()
        totals[column] = "Grand total"
        # append the new row to the dataframe
        dataframe = dataframe.append(totals, ignore_index=True)
        return dataframe
    # Define a function

    @st.cache_data()
    def read_excel_cache(name):
        df = pd.read_excel(name)
        return df

    @st.cache_data()
    def bar(df, yvalue, xvalue, text, title, y_title, x_title, color=None, discrete_sequence=None, map=None):
        fig = px.bar(df, y=yvalue,
                     x=xvalue, text=text, color=color, color_discrete_sequence=discrete_sequence, color_discrete_map=map)
        fig.update_layout(
            title=title,
            yaxis_title=y_title,
            xaxis_title=x_title,
        )
        fig.update_traces(textposition='auto')
        return fig
    df = read_excel_cache('sol_score_update.xlsx')
    # Create a form to filter fullname
    with st.sidebar.form(key='coso_filter_form'):
        name_filter = st.selectbox(label="Select fullname:",
                                   options=list(df['Họ tên'].unique()))
        submit_button = st.form_submit_button(
            label='Filter',  use_container_width=True)
    df1 = df[df['Họ tên'].isin([name_filter])]
    # First row
    col1, col2, col3 = st.columns([1, 1, 2])
    col1.subheader(f"{df1.iloc[0, 2]}")
    col2.subheader(f"{df1.iloc[0, 9]}")
    col3.subheader(f"{df1.iloc[0, 10]}")

    # SEcond row
    col1, col2, col3, col4 = st.columns([1, 1, 1, 1])
    col1.markdown(f"MSNV: {df1.iloc[0,1]}")
    col2.markdown(f"Email: {df1.iloc[0, 11]}")
    col3.markdown(f"Ngày bắt đầu học {df1.iloc[0, 16]}")
    col4.markdown(f"Học tại: {df1.iloc[0, 12]}")
    df1 = df1.drop(['STT'], axis=1)
    # Third row
    col1, col2, col3, col4 = st.columns(4)
    col1.markdown(f"Lớp đang học: {df1.iloc[0, 18]}")
    col2.markdown(f"Lớp TKB: {df1.iloc[0, 20]}")
    col3.markdown(f"Lớp ca học: {df1.iloc[0, 21]}")
    col4.markdown(f"Lớp giáo viên: {df1.iloc[0, 22]}")

    df2 = pd.melt(df1[['Họ tên', 'Nghe', 'Đọc', 'Viết', 'Nói', 'Overall']],
                  id_vars='Họ tên', var_name='Skills', value_name='Score')
    fig1 = bar(df2, yvalue='Score',
               xvalue='Skills', text=df2["Score"], title='', x_title='Kỹ năng', y_title='Điểm',)
    fig1.update_traces(
        hovertemplate="Score: %{y:,.0f}<extra></extra>", hoverlabel=dict(font=dict(size=20)))
    fig1.update_layout(font=dict(size=25))
    fig1.update_xaxes(tickfont=dict(size=17))

    df3 = pd.melt(df1[['Họ tên', 'thực buổi đăng ký', 'đã học', 'nghỉ']],
                  id_vars='Họ tên', var_name='chuyên cần', value_name='số lần')
    fig2 = bar(df3, yvalue='số lần',
               xvalue='chuyên cần', text=df3["số lần"], title='', x_title='', y_title='Số buổi',)
    fig2.update_traces(
        hovertemplate="Số buổi: %{y:,.0f}<extra></extra>", hoverlabel=dict(font=dict(size=20)))

    fig2.update_layout(font=dict(size=25))
    fig2.update_xaxes(tickfont=dict(size=17))

    st.markdown("-------------------------------------------------------------------------------------------------------------------------------------------------------")
    df4 = pd.melt(df1[['Họ tên', 'thực buổi đăng ký', 'không làm', 'làm thiếu']],
                  id_vars='Họ tên', var_name='chuyên cần', value_name='số lần')
    fig3 = bar(df4, yvalue='số lần',
               xvalue='chuyên cần', text=df4["số lần"], title='', x_title='', y_title='Số buổi',)
    fig3.update_traces(
        hovertemplate="Số buổi: %{y:,.0f}<extra></extra>", hoverlabel=dict(font=dict(size=20)))

    fig3.update_layout(font=dict(size=25))
    fig3.update_xaxes(tickfont=dict(size=17))
    # Create 2 columns
    col1, col2 = st.columns(2)
    col1.subheader('Chuyên cần')
    col1.plotly_chart(fig2, use_container_width=True)
    col2.subheader('Làm bài tập')
    col2.plotly_chart(fig3, use_container_width=True)

    st.markdown("-------------------------------------------------------------------------------------------------------------------------------------------------------")
    st.subheader('Điềm đầu vào')
    st.plotly_chart(fig1, use_container_width=True)

    st.markdown("-------------------------------------------------------------------------------------------------------------------------------------------------------")
    diemthi = collect_data('https://vietop.tech/api/get_data/diemthi')
    st.subheader('Chi tiết')
    df_diemthi = diemthi[['hv_id', 'lop_id', 'created_at', 'diemcandat', 'overall', 'reading',
                          'listening', 'writing', 'speaking', 'result', 'dahoc', 'type', 'location', 'note_gv']].query("diemcandat.notnull()")
    # Mapping
    Subjects = {1: "TĐK - Foundation 1", 2: "Thi thật", 3: "Test lại sau bảo lưu", 4: "TĐK - Foundation 2",
                5: "TĐK - 3.5", 6: "TĐK - 4.0", 7:  "TĐK - 4.5", 8: "TĐLK - 5.0", 9: "TĐK - 5.5", 10: "TĐk - 6.0",
                11: "TĐK - 6.0+", 12: "TĐK - 6.5", 13: "Thi cuối khoá"}
    # Add new columns
    df_diemthi.loc[:, ("type")] = df_diemthi.loc[:, ("type")].map(Subjects)
    df_diemthi.location = df_diemthi.location.map(
        {1: "Vietop", 2: 'IDP', 3: "BC"})
    # Merge
    df_diemthi = df_diemthi.merge(df[['hv_id', 'Họ tên']], on='hv_id').query(
        "`Họ tên` == @name_filter")
    st.dataframe(df_diemthi)
    import io
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
        # Write each dataframe to a different worksheet.
        df_diemthi.to_excel(writer, sheet_name='Sheet1')
        # Close the Pandas Excel writer and output the Excel file to the buffer
        writer.save()
        st.download_button(
            label="Download chi tiết test định kỳ học viên",
            data=buffer,
            file_name="tdk_details.xlsx",
            mime="application/vnd.ms-excel"
        )
