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
names = ["Phạm Tấn Thành", "Phạm Minh Tâm", "Vận hành", "Kinh doanh", "SOL"]
usernames = ["thanhpham", "tampham",
             "vietopvanhanh", 'vietopkinhdoanh', 'vietop_sol']

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

    @st.cache_data(ttl=timedelta(hours=3))
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
        totals[column] = "Tổng giờ"
        # append the new row to the dataframe
        dataframe = dataframe.append(totals, ignore_index=True)
        return dataframe
    # Define a function

    @st.cache_data(ttl=timedelta(hours=3))
    def read_excel_cache(name):
        df = pd.read_excel(name)
        return df

    @st.cache_data(ttl=timedelta(hours=3))
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

    @st.cache_data(ttl=timedelta(hours=3))
    def chuyencan_converter(df):
        # Mapping diemdanh_details.chuyencan
        conditions = df.chuyencan == 1, df.chuyencan == 4, df.chuyencan == 7, df.chuyencan == 0
        choices = ["Đi học", "Không học", "Nghỉ học", "Thiếu data"]
        df.chuyencan = np.select(conditions, choices)
        return df

    # Read Excel
    # df = read_excel_cache('sol_score_update.xlsx')
    df = read_excel_cache('hv_doanhnghiep.xlsx')
    df = rename_lop(df, 'hv_coso_x')
    # Create a form to filter fullname
    with st.sidebar.form(key='coso_filter_form'):
        name_filter = st.selectbox(label="Select fullname:",
                                   options=list(df['hv_fullname_x'].unique()))
        submit_button = st.form_submit_button(
            label='Filter',  use_container_width=True)
    df1 = df[df['hv_fullname_x'].isin([name_filter])]
    # First row
    col1, col2, col3 = st.columns([1, 1, 2])
    col1.subheader(f"{df1.iloc[0, 8]}")
    col2.subheader(f"")
    col3.subheader(f"")

    # SEcond row
    col1, col2, col3, col4 = st.columns([1, 1, 1, 1])
    col1.markdown(f"Hv id: {df1.iloc[0,6]}")
    col2.markdown(f"Email: {df1.iloc[0, 9]}")
    col3.markdown(f"Ngày bắt đầu học {df1.iloc[0, 19]}")
    col4.markdown(f"Học tại: {df1.iloc[0, 11]}")
    # Third rowr
    col1, col2, col3, col4 = st.columns(4)
    col1.markdown(f"Lớp đang học: {df1.iloc[0, 21]}")
    # col2.markdown(f"Lớp TKB: {df1.iloc[0, 20]}")
    col3.markdown(f"Lớp ca học: {df1.iloc[0, 23]}")
    col4.markdown(f"Lớp giáo viên: {df1.iloc[0, 24]}")

    df2 = pd.melt(df1[['hv_fullname_x', 'listening', 'reading', 'writing', 'speaking', 'dauvao_overall']],
                  id_vars='hv_fullname_x', var_name='Skills', value_name='Score')
    fig1 = bar(df2, yvalue='Score',
               xvalue='Skills', text=df2["Score"], title='', x_title='Kỹ năng', y_title='Điểm',)
    fig1.update_traces(
        hovertemplate="Score: %{y:,.0f}<extra></extra>", hoverlabel=dict(font=dict(size=20)))
    fig1.update_layout(font=dict(size=25))
    fig1.update_xaxes(tickfont=dict(size=17))

    df3 = pd.melt(df1[['hv_fullname_x', 'thực buổi đăng ký của pđk đang học', 'Đi học', 'Nghỉ học']],
                  id_vars='hv_fullname_x', var_name='chuyên cần', value_name='số lần')
    fig2 = bar(df3, yvalue='số lần',
               xvalue='chuyên cần', text=df3["số lần"], title='', x_title='', y_title='Số buổi',)
    fig2.update_traces(
        hovertemplate="Số buổi: %{y:,.0f}<extra></extra>", hoverlabel=dict(font=dict(size=20)))

    fig2.update_layout(font=dict(size=25))
    fig2.update_xaxes(tickfont=dict(size=17))

    st.markdown("-------------------------------------------------------------------------------------------------------------------------------------------------------")
    df4 = pd.melt(df1[['hv_fullname_x', 'thực buổi đăng ký của pđk đang học', 'Không làm bài tập', 'Làm thiếu bài tập']],
                  id_vars='hv_fullname_x', var_name='chuyên cần', value_name='số lần')
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

    # st.markdown("-------------------------------------------------------------------------------------------------------------------------------------------------------")
    # diemthi = collect_data('https://vietop.tech/api/get_data/diemthi')

    # st.subheader('Chi tiết test định kỳ')
    # df_diemthi = diemthi[['hv_id', 'lop_id', 'created_at', 'diemcandat', 'overall', 'reading',
    #                       'listening', 'writing', 'speaking', 'result', 'dahoc', 'type', 'location', 'note_gv']].query("diemcandat.notnull()")
    # # Mapping
    # Subjects = {1: "TĐK - Foundation 1", 2: "Thi thật", 3: "Test lại sau bảo lưu", 4: "TĐK - Foundation 2",
    #             5: "TĐK - 3.5", 6: "TĐK - 4.0", 7:  "TĐK - 4.5", 8: "TĐLK - 5.0", 9: "TĐK - 5.5", 10: "TĐk - 6.0",
    #             11: "TĐK - 6.0+", 12: "TĐK - 6.5", 13: "Thi cuối khoá"}
    # # Add new columns
    # df_diemthi.loc[:, ("type")] = df_diemthi.loc[:, ("type")].map(Subjects)
    # df_diemthi.location = df_diemthi.location.map(
    #     {1: "Vietop", 2: 'IDP', 3: "BC"})
    # # Merge
    # df_diemthi = df_diemthi.merge(df[['hv_id', 'hv_fullname_x']], on='hv_id').query(
    #     "`hv_fullname_x` == @name_filter")

    # st.dataframe(df_diemthi)
    import io
    buffer = io.BytesIO()
    # with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
    #     # Write each dataframe to a different worksheet.
    #     df_diemthi.to_excel(writer, sheet_name='Sheet1')
    #     # Close the Pandas Excel writer and output the Excel file to the buffer
    #     writer.save()
    #     st.download_button(
    #         label="Download chi tiết test định kỳ học viên",
    #         data=buffer,
    #         file_name="tdk_details.xlsx",
    #         mime="application/vnd.ms-excel"
    #     )
    # st.markdown("-------------------------------------------------------------------------------------------------------------------------------------------------------")
    lophoc = collect_data(
        'https://vietop.tech/api/get_data/lophoc').query("company != 'vietop'")
    lophoc_schedules = collect_data(
        'https://vietop.tech/api/get_data/lophoc_schedules')
    users = collect_data('https://vietop.tech/api/get_data/users')
    molop = collect_data('https://vietop.tech/api/get_data/molop')
    diemdanh_details = collect_data(
        'https://vietop.tech/api/get_data/diemdanh_details')
    # Lophoc
    df_lophoc = lophoc[['lop_id', 'lop_cn', 'lop_ten', 'lop_cahoc', 'lop_thoigianhoc']]\
        .merge(lophoc_schedules[['lop_id', 'teacher_id']], on='lop_id', how='left')\
        .merge(users[['fullname', 'id']], left_on='teacher_id', right_on='id', how='left')\
        .drop_duplicates(subset=['teacher_id', 'lop_id'])
    df_lophoc1 = df_lophoc.merge(
        molop[['lop_id', 'hv_id', 'molop_active']], on='lop_id')
    df = df_lophoc1.merge(df1[['hv_id', 'hv_fullname_x', 'hv_coso_x']], on='hv_id')\
        .drop(['teacher_id', 'id', 'hv_coso_x'], axis=1)
    df = df.reindex(columns=['hv_id', 'hv_fullname_x', 'lop_id', 'lop_ten', 'lop_cahoc',
                    'lop_thoigianhoc', 'fullname', 'molop_active'])
    df['molop_active'] = ['Lớp đang học' if i ==
                          1 else 'Lớp kết thúc' for i in df['molop_active']]

    # merge lophoc and diemdanh
    df3 = df.merge(
        diemdanh_details[['lop_id', 'giohoc', 'chuyencan', 'date_created']], on='lop_id')
    df3 = df3.drop_duplicates().sort_values(
        "date_created", ascending=False)
    df4 = df3[['fullname', 'lop_id', 'date_created', 'giohoc', 'chuyencan', 'lop_ten', 'lop_cahoc',
               'lop_thoigianhoc', 'molop_active']]

    df4 = chuyencan_converter(df4)
    st.subheader("Các lớp đã và đang học")
    # Create a form to filter check
    with st.form(key='check_filter_form'):
        lop_filter = st.multiselect(label="Select lớp id:",
                                    options=list(df4['lop_id'].unique()), default=df4['lop_id'].unique())
        submit_button = st.form_submit_button(
            label='Filter',  use_container_width=True)
    df4 = df4[df4['lop_id'].isin(lop_filter)]
    # st.markdown("-------------------------------------------------------------------------------------------------------------------------------------------------------")
    ""
    diemdanh = collect_data(
        'https://vietop.tech/api/get_data/diemdanh').query('lop_id == @lop_filter')
    df_drop = df4.drop_duplicates(subset='lop_id')[['lop_id']]\
        .merge(diemdanh[['lop_id', 'kynang', 'noidung_note', 'date_created',
                         'cahoc', 'giaovien',]], on='lop_id')

    # df_drop = df_drop[df_drop['kynang'].isin([1, 2, 3, 4])]
    df_drop['kynang_1'] = df_drop['kynang'].map(
        {1: 'Writing', 2: 'Speaking', 3: 'Reading', 4: 'Listening', })
    df_drop['kynang_2'] = df_drop['kynang'].map(
        {1: 'Buổi học', 2: 'Buổi học', 3: 'Buổi học', 4: 'Buổi học', 5: 'Buổi học', 7: 'Buổi học', 6: 'Không học'})
    df_drop['kynang_3'] = df_drop['kynang'].map(
        {1: 'Buổi học', 2: 'Buổi học', 3: 'Buổi học', 4: 'Buổi học', 5: 'Lần test', 7: 'Lần test', 6: 'Buổi học'})

    def pie_chart(col):
        df_group = df_drop.groupby(col, as_index=False)[
            col].value_counts()
        # Create a pie chart
        fig = px.pie(df_group, names=df_group[col], values=df_group['count'])
        fig.update_traces(
            hovertemplate='%{label}: %{value} (%{percent})', hoverlabel=dict(font=dict(size=15)))
        fig.update_layout(font=dict(size=20))
        fig.update_xaxes(tickfont=dict(size=15))

        return fig

    fig5 = pie_chart('kynang_1')
    fig5.update_layout(
        title=f"Tỉ trọng kỹ năng của lớp {df4['lop_id'].unique()}")

    fig6 = pie_chart('kynang_2')
    fig6.update_layout(
        title=f"Tỉ trọng không học của lớp {df4['lop_id'].unique()}")

    fig7 = pie_chart('kynang_3')
    fig7.update_layout(
        title=f"Tỉ trọng tỷ lệ test của lớp {df4['lop_id'].unique()}")
    ""
    col1, col2, col3 = st.columns(3)

    col1.plotly_chart(fig5,  use_container_width=True)

    col2.plotly_chart(fig6, use_container_width=True)

    col3.plotly_chart(fig7, use_container_width=True)
    st.subheader("Qúa trình giảng dạy")
    df = diemdanh[diemdanh['lop_id'].isin(lop_filter)][[
        'created_at', 'giaovien', 'cahoc', 'buoihoc', 'kynang', 'module', 'noidung_note']]\
        .merge(users[['id', 'fullname']], left_on='giaovien', right_on='id')
    df['kynang'] = df['kynang'].map(
        {1: 'Writing', 2: 'Speaking', 3: 'Reading', 4: 'Listening', 5: 'Test', 6: 'Không học', 7: 'Test ngày 2'})
    df.drop(['id', 'giaovien'], axis=1, inplace=True)
    df['created_at'] = df['created_at'].astype('datetime64[ns]')
    df['created_at'] = df['created_at'].dt.date
    df.columns = ['Ngày học',  'Ca dạy',
                  'Buổi học', 'Kỹ năng', 'Module', 'Giáo viên note', 'Giáo viên',]
    st.dataframe(df)

    # st.markdown("-------------------------------------------------------------------------------------------------------------------------------------------------------")
    df4 = df4.drop_duplicates(subset='date_created', keep='last')
    df5 = df4.copy()
    df4.columns = ['tên giáo viên', 'lớp id', 'ngày học', 'giờ học', 'chuyên cần', 'lớp tên', 'lớp ca học',
                   'lớp thời gian học',  'tình trạng lớp']

    ""
    st.subheader(f"Tổng giờ học theo tháng của :blue[{name_filter}]")
    df5['date_created'] = df5['date_created'].astype('datetime64[ns]')
    df5['date_created_month'] = df5['date_created'].dt.strftime('%m-%Y')
    # Groupby date_created_month
    df6 = df5.groupby("date_created_month", as_index=False)['giohoc'].sum()
    fig3 = bar(df6, yvalue='giohoc',
               xvalue='date_created_month', text=df6["giohoc"], title='', x_title='tháng trong năm', y_title='Tổng giờ học',)
    fig3.update_traces(
        hovertemplate="Tổng giờ học: %{y:,.0f}<extra></extra>", hoverlabel=dict(font=dict(size=20)))

    fig3.update_layout(font=dict(size=20))
    fig3.update_xaxes(tickfont=dict(size=15))
    st.plotly_chart(fig3, use_container_width=True)
    # st.markdown("-------------------------------------------------------------------------------------------------------------------------------------------------------")

    ""
    st.subheader("Chi tiết điểm danh")
    st.subheader(
        f"Tổng giờ học lớp :blue[{df4['lớp id'].unique()[0]}] là :blue[{df4['giờ học'].sum()}] giờ")
    ""
    st.dataframe(df4.style.background_gradient(
        cmap='YlOrRd', subset='giờ học').format({'giờ học': '{:,.0f}'}))

    with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
        # Write each dataframe to a different worksheet.
        df4.to_excel(writer, sheet_name='Sheet1')
        # Close the Pandas Excel writer and output the Excel file to the buffer
        writer.save()
        st.download_button(
            label="Download chi tiết điểm danh học viên",
            data=buffer,
            file_name="diemdanh_details.xlsx",
            mime="application/vnd.ms-excel"
        )
    # st.markdown("-------------------------------------------------------------------------------------------------------------------------------------------------------")
    # ignore SettingWithCopyWarning
    pd.options.mode.chained_assignment = None  # default='warn'
    hocvien = collect_data('https://vietop.tech/api/get_data/hocvien')
    hocvien = hocvien.query('hv_fullname == @name_filter')
    orders = collect_data('https://vietop.tech/api/get_data/orders')
    order_details = collect_data(
        'https://vietop.tech/api/get_data/order_details')
    khoahoc = collect_data('https://vietop.tech/api/get_data/khoahoc')
    discounts = collect_data('https://vietop.tech/api/get_data/discounts')

    df = orders[['ketoan_id', 'hv_id', 'kh_id', 'ketoan_coso',
                 'ketoan_price', 'ketoan_sogio', 'ketoan_tientrengio', 'remaining_time',
                 'hv_discount', 'ketoan_active', 'created_at']]\
        .merge(khoahoc[['kh_id', 'kh_ten']], on='kh_id')\
        .merge(hocvien[['hv_id', 'hv_fullname', 'user_id']])\
        .merge(users[['id', 'fullname']], left_on='user_id', right_on='id')\
        .drop(['kh_id', 'user_id', 'id'], axis=1)
    df1 = df[df['hv_discount'].str.len() < 8]
    df1.loc[:, 'hv_discount'] = df1.loc[:,
                                        'hv_discount'].str.replace('[^\w\s]', '')
    df1.loc[:, 'hv_discount'] = df1.loc[:, 'hv_discount'].astype('int32')
    df2 = df1.merge(discounts[['dis_id', 'dis_name']],
                    left_on='hv_discount', right_on='dis_id')
    df3 = df2.drop(['dis_id', 'hv_discount'], axis=1)
    ""
    st.markdown("-------------------------------------------------------------------------------------------------------------------------------------------------------")
    # Diemdanh dahoc
    df_diemdanh_details = diemdanh_details.groupby(
        "ketoan_id", as_index=False)['giohoc'].sum()
    df4 = df3.merge(df_diemdanh_details, on='ketoan_id')
    df4['conlai'] = df4['remaining_time'] - df4['giohoc']
    # Mapping ketoan_active
    conditions = [(df4['ketoan_active'] == 0), df4['ketoan_active']
                  == 1, df4['ketoan_active'] == 4, df4['ketoan_active'] == 5]
    choices = ["Chưa học", "Đang học", "Bảo lưu", "Kết thúc"]
    df4['ketoan_active'] = np.select(conditions, choices)
    df4 = rename_lop(df4, 'ketoan_coso')
    df4 = df4.reindex(columns=['ketoan_id', 'hv_id', 'ketoan_coso', 'ketoan_price', 'ketoan_sogio', 'remaining_time',
                      'giohoc', 'conlai', 'ketoan_tientrengio', 'dis_name', 'kh_ten', 'ketoan_active', 'fullname'])
    df4.columns = ['Mã PĐK', 'hv_id', 'cơ sở', 'Học phí khoá học', 'Tổng giờ khoá học', 'Thực giờ đăng ký',
                   'Đã học', 'Còn lại', 'Tiền trên giờ', 'Khuyến mãi', 'Khoá học', 'Trạng thái', 'Nhân viên tư vấn']
    st.subheader("Phiếu đăng ký")
    ""

    st.dataframe(df4)
    st.subheader("Phiếu thu")
    df_order_details = order_details[['detail_id',
                                      'ketoan_id', 'hv_id', 'detail_price', 'detail_reason']]\
        .merge(hocvien.query("hv_fullname == @name_filter")[['hv_id']], on='hv_id')
    df_order_details.columns = ['Mã phiếu thu',
                                'Mã PĐK', 'hv_id', 'Đã thu', 'note']
    st.dataframe(df_order_details, use_container_width=True)

    # .query('ketoan_id == 6848')
