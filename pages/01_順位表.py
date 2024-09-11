import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

import utils

service_acount_num = utils.get_service_acount_num()

# login_p = False if "login_p" not in st.session_state else True
# if not login_p:
#     password = st.text_input("パスワードを入力してください:", type="password")
#     if password != st.secrets["all"]["password"]:
#         st.error("誰かにパスワードを確認してください")
#         exit()
st.session_state["login_p"] = True

exe_j = False if "exe_j" not in st.session_state else st.session_state["exe_j"]

if exe_j:
    st.warning(
        "事務局権限が付与されています。不要な場合は事務局ページで解除してください。"
    )

utils.clear_ss_score_update()

# カラースケールを拡張
colors = (
    px.colors.qualitative.Light24
    + px.colors.qualitative.Alphabet
    + px.colors.qualitative.Dark24
)

(
    df,
    df_team,
    current_frame,
    df_conf,
    now,
    open_result,
    stop_update,
    teams_1game_only,
    df_notice,
) = utils.update_data(service_acount_num)


# 結果発表前は19フレーム目までしか順位表に表現しない
if not open_result:
    if current_frame == 20:
        st.info("最終フレームの結果は反映していません。結果発表をお待ちください！")
        current_frame = 19
else:
    _, _, contest_mode = map(int, df_conf["値"])
    if contest_mode:
        utils.balloons_or_snows()


# 拠点に関するフィルター
# session_stateの問題で拠点、チーム、名前は関数化せずそれぞれ処理
def update_area_r():
    st.session_state["area_r"] = st.session_state["new_area_r"]


st.sidebar.title("拠点選択")
labels = ["ALL"] + sorted(df_team["拠点"].unique())
idx = labels.index(st.session_state["area_r"]) if "area_r" in st.session_state else 0
selected_area_r = st.sidebar.selectbox(
    "拠点を選択してください",
    labels,
    idx,
    key="new_area_r",
    on_change=update_area_r,
)
if selected_area_r != "ALL":
    df = df[df["拠点"] == selected_area_r]
    df_team = df_team[df_team["拠点"] == selected_area_r]


# チームに関するフィルター
def update_team_r():
    selected_team_r = st.session_state["new_team_r"]
    if "ALL" in selected_team_r and len(selected_team_r) >= 2:
        if selected_team_r[-1] == "ALL":
            selected_team_r = set({"ALL"})
        else:
            selected_team_r = set(selected_team_r)
            selected_team_r.discard("ALL")
    st.session_state["team_r"] = selected_team_r


st.sidebar.title("チーム選択")
labels = ["ALL"] + sorted(df_team["チーム"].unique())

selected_team = set(
    st.sidebar.multiselect(
        "チームを選択してください",
        labels,
        st.session_state["team_r"] if "team_r" in st.session_state else labels[0],
        key="new_team_r",
        on_change=update_team_r,
    )
)

if "ALL" not in selected_team:
    df = df[df["チーム"].isin(selected_team)]
    df_team = df_team[df_team["チーム"].isin(selected_team)]


# 名前に関するフィルター
def update_name_r():
    selected_name_r = st.session_state["new_name_r"]
    if "ALL" in selected_name_r and len(selected_name_r) >= 2:
        if selected_name_r[-1] == "ALL":
            selected_name_r = set({"ALL"})
        else:
            selected_name_r = set(selected_name_r)
            selected_name_r.discard("ALL")
    st.session_state["name_r"] = selected_name_r


st.sidebar.title("名前選択")
labels = ["ALL"] + sorted(df["名前"].unique())

selected_name = set(
    st.sidebar.multiselect(
        "名前を選択してください",
        labels,
        st.session_state["name_r"] if "name_r" in st.session_state else labels[0],
        key="new_name_r",
        on_change=update_name_r,
    )
)

if "ALL" not in selected_name:
    df = df[df["名前"].isin(selected_name)]

# 表示するフレームは進行状況に応じて自動変更
# session_stateは使用しない
if current_frame > 1:
    current_frame = st.sidebar.slider(
        label="フレームを選択してください",
        min_value=0 if current_frame <= 1 else 1,
        max_value=current_frame,
        value=current_frame,
    )


# データを表示
if st.button("順位更新"):
    (
        df,
        df_team,
        current_frame,
        df_conf,
        now,
        open_result,
        stop_update,
        teams_1game_only,
        df_notice,
    ) = utils.update_data(service_acount_num)
# st.write(f'{now.strftime("%Y/%m/%d %H:%M:%S")}時点')
# st.write("間隔が短いと更新されません。時間をあけて再度確認してください。")

if selected_name == {"ALL"}:
    st.title("チーム順位表")

    st.dataframe(
        df_team[["順位", str(current_frame), "メンバー", "拠点"]].rename(
            columns={str(current_frame): "得点"}
        ),
        use_container_width=True,
        hide_index=True,
    )
    st.write("※人数の少ないチームの得点は、多いチームと合うように補正しています。")

    if "width_team" not in st.session_state:
        st.session_state["width_team"] = 700
    fig_team = go.Figure()

    for index, row in df_team.iterrows():
        color_index = index % len(colors)
        fig_team.add_trace(
            go.Scatter(
                x=list(range(1, current_frame + 1)),
                y=row[3 : 3 + current_frame],
                mode="lines+markers",
                name=row["メンバー"],
                marker=dict(color=colors[color_index]),
            )
        )

    fig_team.update_layout(
        xaxis_title="フレーム",
        yaxis_title="スコア",
        legend_title="メンバー",
        xaxis=dict(tickmode="linear"),
        yaxis=dict(rangemode="tozero"),
        hovermode="x unified",
        legend=dict(
            orientation="h",
            x=0.5,
            y=1,
            xanchor="center",
            yanchor="bottom",
        ),
        dragmode="pan",
    )

    st.subheader("")
    st.plotly_chart(fig_team, use_container_width=True)


else:
    st.write("個人が選択されているため、チーム順位表は表示していません")

st.title("個人順位表")

st.dataframe(
    df[["順位", str(current_frame), "名前", "拠点", "チーム"]].rename(
        columns={str(current_frame): "得点"}
    ),
    use_container_width=True,
    hide_index=True,
)

fig = go.Figure()

for index, row in df.iterrows():
    color_index = index % len(colors)
    fig.add_trace(
        go.Scatter(
            x=list(range(1, current_frame + 1)),
            y=row[45 : 45 + current_frame],
            mode="lines+markers",
            name=row["名前"],
            marker=dict(color=colors[color_index]),
        )
    )

fig.update_layout(
    xaxis_title="フレーム",
    yaxis_title="スコア",
    legend_title="名前",
    xaxis=dict(tickmode="linear"),
    yaxis=dict(rangemode="tozero"),
    hovermode="x unified",
    legend=dict(
        orientation="h",
        x=0.5,
        y=1,
        xanchor="center",
        yanchor="bottom",
    ),
    dragmode="pan",
)
st.subheader("")
st.plotly_chart(fig, use_container_width=True)
