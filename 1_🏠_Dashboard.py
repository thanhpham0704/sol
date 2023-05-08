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


page_title = "Quản lý quá trình học tập của học viên"
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
    now = datetime.now()
    DEFAULT_START_DATE = datetime(now.year, now.month, 1)
    DEFAULT_END_DATE = datetime(now.year, now.month, 1) + timedelta(days=32)
    DEFAULT_END_DATE = DEFAULT_END_DATE.replace(day=1) - timedelta(days=1)

    # Create a form to get the date range filters
    with st.sidebar.form(key='date_filter_form'):
        ketoan_start_time = st.date_input(
            "Select start date", value=DEFAULT_START_DATE)
        ketoan_end_time = st.date_input(
            "Select end date", value=DEFAULT_END_DATE)
        submit_button = st.form_submit_button(
            label='Filter',  use_container_width=True)

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

    # Collect data
    hocvien = collect_data('https://vietop.tech/api/get_data/hocvien')
    molop = collect_data('https://vietop.tech/api/get_data/molop')
    diemthi = collect_data('https://vietop.tech/api/get_data/diemthi')
    diemthi['created_at'] = diemthi['created_at'].astype('datetime64[ns]')
    diemthi['created_at'] = diemthi['created_at'].dt.date
    # diemthi = diemthi.query(
    #     "created_at >= @ketoan_start_time and created_at < @ketoan_end_time")

    df = diemthi[['id', 'hv_id', 'lop_id', 'date', 'created_at', 'diemcandat',
                  'overall', 'listening', 'reading', 'writing', 'speaking', 'dahoc', 'type', 'location',]]\
        .merge(molop.query('molop_active == 1')[['hv_id']], on='hv_id')
    # Mapping
    Subjects = {1: "TĐK - Foundation 1", 2: "Thi thật", 3: "Test lại sau bảo lưu", 4: "TĐK - Foundation 2",
                5: "TĐK - 3.5", 6: "TĐK - 4.0", 7:  "TĐK - 4.5", 8: "TĐLK - 5.0", 9: "TĐK - 5.5", 10: "TĐk - 6.0",
                11: "TĐK - 6.0+", 12: "TĐK - 6.5", 13: "Thi cuối khoá"}
    # Add new columns
    df.loc[:, ("type")] = df.loc[:, ("type")].map(Subjects)
    df.location = df.location.map({1: "Vietop", 2: 'IDP', 3: "BC"})
    df_sort = df.sort_values("created_at", ascending=False)
    df1 = df_sort.drop_duplicates(subset='hv_id', keep='first')[['id', 'hv_id', 'lop_id', 'date', 'created_at',
                                                                 'overall', 'type', 'location',]]
    print(df1.shape)
    df2 = df_sort[~df_sort.id.isin(df1.id)]
    df2 = df2.drop_duplicates(subset='hv_id', keep='first')[['id', 'hv_id', 'lop_id', 'date', 'created_at',
                                                             'overall', 'type', 'location',]]
    print(df2.shape)

    df3 = df1.merge(df2, on='hv_id', how='left')
    df4 = df3.merge(hocvien[['hv_fullname', 'hv_coso', 'hv_id',
                    'dauvao_overall', 'hv_ngayhoc', 'created_at']], on='hv_id')
    df4['date_y'] = df4['date_y'].fillna(df4['hv_ngayhoc'])
    df4['created_at_y'] = df4['created_at_y'].fillna(df4['created_at'])
    df4['overall_y'] = df4['overall_y'].fillna(df4['dauvao_overall'])
    df4['type_y'] = df4['type_y'].fillna('Test đầu vào')
    df4['location_y'] = df4['location_y'].fillna('Vietop')
    df5 = df4.drop(['id_y', 'id_x', 'dauvao_overall',
                   'hv_ngayhoc', 'created_at'], axis=1)
    empty = []
    for index, row in df5.iterrows():
        if row['overall_x'] - row['overall_y'] > 0:
            empty.append('tiến bộ')
        elif row['overall_x'] - row['overall_y'] == 0:
            empty.append('không tiến bộ')
        else:
            empty.append('giảm sút')
    df5['check'] = empty
    # Filter for created_at_x of diemthi
    df5 = df5.query(
        "created_at_x >= @ketoan_start_time and created_at_x < @ketoan_end_time")

    df6 = df5.check.value_counts().reset_index()
    fig1 = bar(df6, yvalue='check',
               xvalue='index', text=df6["check"], title='', x_title='', y_title='Số học viên',)
    fig1.update_traces(
        hovertemplate="Số lần: %{y:,.0f}<extra></extra>", hoverlabel=dict(font=dict(size=20)))

    fig1.update_layout(font=dict(size=25))
    fig1.update_xaxes(tickfont=dict(size=17))
    st.subheader(
        f"Số học viên theo tiêu chí đánh giá (tổng :blue[{df5.shape[0]}] học viên)")
    st.plotly_chart(fig1, use_container_width=True)
    st.markdown("-------------------------------------------------------------------------------------------------------------------------------------------------------")
    st.subheader(f"Danh sách chi tiết (tổng :blue[{df5.shape[0]}] học viên)")
    # Create a form to filter check
    with st.form(key='check_filter_form'):
        check_filter = st.multiselect(label="Select check_status:",
                                      options=list(df5['check'].unique()), default=['tiến bộ', 'không tiến bộ', 'giảm sút'])
        submit_button = st.form_submit_button(
            label='Filter',  use_container_width=True)
    df5 = df5[df5['check'].isin(check_filter)]

    df5.drop(['date_x', 'date_y', 'location_x',
             'location_y', 'lop_id_x', 'lop_id_y'], axis=1, inplace=True)
    df5.set_index('hv_id', inplace=True)
    df5 = rename_lop(df5, 'hv_coso')
    df5['created_at_y'] = df5['created_at_y'].astype("datetime64[ns]")
    df5['created_at_y'] = df5['created_at_y'].dt.date
    df6 = df5.reindex(columns=['hv_fullname', 'overall_x', 'type_x', 'created_at_x',
                               'overall_y', 'type_y', 'created_at_y', 'check', 'hv_coso'])
    df6.columns = ['Họ và tên', 'overall gần nhất', 'loại test gần nhất', 'ngày tạo gần nhất',
                   'overall trước đó', 'loại test trước đó', 'ngày tạo trước đó', 'check', 'chi nhánh']
    ""
    ""
    st.dataframe(df6)
    import io
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
        # Write each dataframe to a different worksheet.
        df6.to_excel(writer, sheet_name='Sheet1')
        # Close the Pandas Excel writer and output the Excel file to the buffer
        writer.save()
        st.download_button(
            label="Download chi tiết",
            data=buffer,
            file_name="compare_details.xlsx",
            mime="application/vnd.ms-excel"
        )
