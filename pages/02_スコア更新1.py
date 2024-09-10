import streamlit as st

import utils

service_acount_num = utils.get_service_acount_num()
login_p = False if "login_p" not in st.session_state else True
if not login_p:
    password = st.text_input("パスワードを入力してください:", type="password")
    if password != st.secrets["all"]["password"]:
        st.error("誰かにパスワードを確認してください")
        exit()
st.session_state["login_p"] = True
exe_j = False if "exe_j" not in st.session_state else st.session_state["exe_j"]

if exe_j:
    st.warning(
        "事務局権限が付与されています。不要な場合は事務局ページで解除してください。"
    )
st.title("スコア更新用")

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

if stop_update and not exe_j:
    st.info("事務局確認中のため更新できません。結果発表をお待ちください。")
    exit()

if stop_update:
    st.warning("参加者画面では更新停止中")


df = df[df.columns[:-21]]


# チームに関するフィルター
def update_team():
    selected_team = st.session_state["new_team"]
    if "ALL" in selected_team and len(selected_team) >= 2:
        if selected_team[-1] == "ALL":
            selected_team = set({"ALL"})
        else:
            selected_team = set(selected_team)
            selected_team.discard("ALL")
    st.session_state["team"] = selected_team
    utils.clear_ss_score_update()


st.subheader("チーム選択")
labels = ["ALL"] + sorted(df["チーム"].unique())
selected_team = set(
    st.multiselect(
        "チームを選択してください",
        labels,
        st.session_state["team"] if "team" in st.session_state else labels[0],
        key="new_team",
        on_change=update_team,
    )
)
if selected_team != {"ALL"}:
    df = df[df["チーム"].isin(selected_team)]


# 1ゲーム目2ゲーム目の選択

st.subheader("ゲーム選択")
idx = st.session_state["game"] if "game" in st.session_state else 0
selected_game = st.selectbox(
    "何ゲーム目かを選択してください",
    (1, 2),
    idx,
    on_change=utils.clear_ss_score_update,
)
st.session_state["game"] = selected_game - 1
if selected_game == 1:
    df = df[df.columns[:-21]]
else:
    df = df[list(df.columns[:3]) + list(df.columns[24:])]


# フレームの選択
def update_frame():
    st.session_state["frame"] = st.session_state["new_frame"]
    utils.clear_ss_score_update()


start, end = st.slider(
    "何フレーム目を更新するか選んでください",
    min_value=1,
    max_value=10,
    key="new_frame",
    value=st.session_state["frame"] if "frame" in st.session_state else (1, 10),
    on_change=update_frame,
)
if end == 10:
    df = df[list(df.columns[:3]) + list(df.columns[3 + (start - 1) * 2 :])]
else:
    df = df[
        list(df.columns[:3])
        + list(df.columns[3 + (start - 1) * 2 : -(3 + (9 - end) * 2)])
    ]

# インデックスを名前列にする
df = df.sort_index()
df["index"] = df.index
idx_min, idx_ma = df["index"].min(), df["index"].max()
df = df.set_index("名前")
df = df[df.columns[2:]]


st.write("以下の表を直接更新してください")
edited_df = st.data_editor(df[df.columns[:-1]], use_container_width=True)

with st.expander(
    "データ更新説明",
    expanded=False,
    column_config={
        "名前": st.column_config.Column(editable=False)  # インデックス列は編集不可に
    },
):
    st.markdown(
        """
    【概要】  
    - （事前にチーム単位でフィルターをかけ、チーム全員分まとめて入力いただけると助かります）
    - 例えば1_1列は1フレーム目の1投目という風に、列はフレーム数と投球数を意味しています
        - 2ゲーム目の1フレーム目は21という風に2ゲーム目は10加算されます。
    - 投球ごとに倒したピンの数を記録していってください。
    - 例えば、ストライクの場合は(10 ,0)、一投目が7で2投目でスペアの場合は(7,3)を入力します。
    - ストライクで2投目を投げなかった場合も、ガーターとなった場合も、倒した数が0の場合は0と入力してください。
    - 間違えても後から上書き可能なので問題ありません！（最後に運営もチェックします）
    
    【入力方法】  
    - 更新したいデータを選び2回タップするとキーボードが表示されるので倒したピンの数を入力します
        - iphoneでひらがな入力できる状態だと同じ数字が2度入力されます
        - キーボードを別のものに変えてから入力をお願いします
    - 更新したいデータがすべて更新できたら、確認 → 更新とクリックします

    """
    )


def check_error(df):
    for row in df.values:
        for v in row:
            if v < 0 or 10 < v:
                st.error("0~10の数値以外のデータがあるため更新できません")
                return False
    if end == 10:
        df, df_10 = df[df.columns[:-3]], df[df.columns[-3:]]
        for i, s1, s2, s3 in df_10.itertuples():
            t = s1 + s2
            if t > 10 and t != 20:
                st.error("1投目と2投目の合計が10を超えるため更新できません")
                return False
            if s3 and t < 9:
                st.error("3投目が存在しないケースで入力されているため更新できません")
                return False

    if df.shape[
        1
    ]:  # 10列目しか存在しない場合はスライスでインデックス列のみになっている
        for _, *row in df.itertuples():
            for i in range(0, len(row), 2):
                if row[i] + row[i + 1] > 10:
                    st.error("1投目と2投目の合計が10を超えるため更新できません")
                    return False
    return True


res = st.button("確認")
st.session_state["res"] = True
if res:
    st.dataframe(
        edited_df.style.apply(utils.style_diff, target=df, axis=0),
        use_container_width=True,
    )

    if not check_error(edited_df):
        st.error(
            "赤色箇所のいづれかまたはすべてを更新しようとしてエラーとなりました。周辺を含めて内容を確認してください。"
        )
        exit()
    st.markdown(
        """
    **赤色部分のデータを更新します。更新する場合は更新ボタンを押してください。**
    - 修正する場合は、修正して再度確認ボタンを押してください。
    - ページを切り替えることで入力前の状態に戻すこともできます。
    """
    )

connects = [
    utils.connect_spread_sheet1,
    utils.connect_spread_sheet2,
    utils.connect_spread_sheet3,
    utils.connect_spread_sheet4,
    utils.connect_spread_sheet5,
]
reads = [
    utils.read_origin_score1,
    utils.read_origin_score2,
    utils.read_origin_score3,
    utils.read_origin_score4,
    utils.read_origin_score5,
]
if "res" in st.session_state and st.session_state["res"]:
    if st.button("更新"):
        client = connects[service_acount_num - 1]()
        # スプレッドシートを開く
        try:
            ws = client.open("スコア表").worksheet("data")
        except AttributeError:
            connects[service_acount_num - 1].clear()
            client = connects[service_acount_num - 1]()
            ws = client.open("スコア表").worksheet("data")
        if selected_game == 1:
            cells = ws.range(f"D{idx_min+2}:X{idx_ma+2}")
        else:
            cells = ws.range(f"Y{idx_min+2}:AS{idx_ma+2}")
        cells_update = []
        for idx, row_before, row_after in zip(
            df["index"], df.itertuples(), edited_df.itertuples()
        ):
            idx %= idx_min
            for idx2, (v_before, v_after) in enumerate(
                zip(row_before[1:-1], row_after[1:])
            ):
                if v_before == v_after:
                    continue
                else:
                    cell = cells[idx * 21 + (start - 1) * 2 + idx2]
                    cell.value = v_after
                    cells_update.append(cell)
        if not cells_update:
            st.warning("更新対象データがありませんでした")
            st.session_state["res"] = False
        else:
            ws.update_cells(cells_update)
            # 再読み込み
            reads[service_acount_num - 1].clear()
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
            st.success("更新しました")
            utils.balloons_or_snows()
            st.session_state["res"] = True
