import streamlit as st

import utils

service_acount_num = 5  # 事務局ページは5
login_j = False if "login_j" not in st.session_state else True

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
utils.clear_ss_score_update()

st.title("事務局用")
data_staff = st.secrets["staff"]
if not login_j:
    password = st.text_input("パスワードを入力してください:", type="password")
    if password != data_staff["password"]:
        st.error("事務局用のページです。")
        exit()

st.session_state["login_j"] = True
st.subheader("モード選択")
with st.expander("一覧", expanded=False):
    st.markdown(
        """
    - 練習中:100
    - 大会中:001
    - 結果確認中:011
    - 結果発表以降:111
    """
    )
df_conf = st.data_editor(df_conf, hide_index=True, use_container_width=True)
if st.button("モード更新"):
    client = utils.connect_spread_sheet5()
    # スプレッドシートを開く
    try:
        ws = client.open("スコア表").worksheet("data")
    except AttributeError:
        utils.connect_spread_sheet5.clear()
        client = utils.connect_spread_sheet5()
        ws = client.open("スコア表").worksheet("data")
    cells = ws.range("AU2:AU4")
    for cell, value in zip(cells, df_conf["値"]):
        cell.value = value
    ws.update_cells(cells)
    # 再読み込み
    utils.read_origin_score5.clear()
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
    ) = utils.update_data()
    st.success("更新しました")

st.subheader("連絡更新")
st.markdown(
    """
- ここに記載した内容がそのまま、最初に開くページに行ごとに記載されます
- 絵文字入れるとバグる可能性があるので入れないで下さい（未確認です）
- 空白行または行追加して、登校したい内容を記載してください
- 削除したい内容はすべての文字を削除するか、行削除したのちお知らせ更新ボタンを押してください
"""
)


df_notice_new = st.data_editor(
    df_notice, hide_index=True, num_rows="dynamic", use_container_width=True
)
notices_pre = set([v for v in df_notice["連絡"] if v])
notices_l = [v for v in df_notice_new["連絡"] if v]
notices = set(notices_l)

notices_remove = notices_pre - notices
if st.button("連絡更新"):
    client = utils.connect_spread_sheet5()
    # スプレッドシートを開く
    try:
        ws = client.open("スコア表").worksheet("data")
    except AttributeError:
        utils.connect_spread_sheet5.clear()
        client = utils.connect_spread_sheet5()
        ws = client.open("スコア表").worksheet("data")
    # 実装を簡略化するため50セル更新（それ以上の投稿はまずないはず…
    cells = ws.range("AX2:AX51")
    notices_cur = set(
        [cell.value for cell in cells if cell.value]
    )  # 読み取ったばかりのデータ
    # 読み取ったばかりのデータにしか存在しないデータ
    values_cur = notices_cur - notices - notices_remove

    # 更新済みテーブルの後に読み取ったばかりのデータにしか存在しないデータを追加した内容で更新
    notices = sorted(notices, key=lambda x: notices_l.index(x)) + list(values_cur)
    if len(notices) > 50:
        st.error("お知らせの数が多過ぎます。数を見直してから再度更新してください。")
        exit()
    values = notices + [""] * (50 - len(notices))
    for cell, value in zip(cells, values):
        cell.value = value
    ws.update_cells(cells)
    # 再読み込み
    utils.read_origin_score5.clear()
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
    ) = utils.update_data()
    st.success("更新しました")

st.subheader("2ゲーム目を実施しないチームの設定")

selected_team = st.multiselect(
    "2ゲーム目を実施しないチームがあれば選択してください",
    df_team["チーム"],
    teams_1game_only,
)
if st.button("チームを反映"):
    client = utils.connect_spread_sheet5()
    # スプレッドシートを開く
    try:
        ws = client.open("スコア表").worksheet("data")
    except AttributeError:
        utils.connect_spread_sheet5.clear()
        client = utils.connect_spread_sheet5()
        ws = client.open("スコア表").worksheet("data")
    # 実装を簡略化するため50セル更新（チーム数が最大50未満である必要あり
    cells = ws.range("AW2:AW51")
    values = selected_team + [""] * (50 - len(selected_team))
    for cell, value in zip(cells, values):
        cell.value = value
    ws.update_cells(cells)
    # 再読み込み
    utils.read_origin_score5.clear()
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
    ) = utils.update_data()
    st.success("更新しました")
st.write(
    "今回選択したチームにすべて書き換わります。（今回選択したチームを既に選択されているチームに追加ではありません）"
)

st.subheader("事務局権限付与")

with st.expander("説明", expanded=False):
    st.markdown(
        """
    - エラーでデータの読み取りや更新ができなくなった際に事務局で対応するためのものです
    - こちらの権限を付与して実行すれば解決する可能性があります
    - 時間当たりのDBとの接続回数が一定数を超えた場合に発生するエラーであれば解決可能になります
    - 時間がたてば解決するものではあるので無理に対応する必要はなかったりします
    - 闇雲に使用すると事務局側の回数が圧迫されるため使わなくなったら戻って権限を解除してください

    """
    )

if st.button("事務局権限付与"):
    st.session_state["exe_j"] = True
    st.session_state["service_acount_num"] = 5
    st.success("権限を付与しました")

if st.button("事務局権限解除"):
    del st.session_state["exe_j"]
    del st.session_state["service_acount_num"]
    utils.get_service_acount_num()
    st.success("権限を解除しました")

st.subheader("最終確認用データ")
with st.expander("説明等", expanded=False):
    st.markdown(
        """
    結果発表前の確認時に使用(順位表に最終投球後の順位が載るのが結果発表後のため)
    - 1G、2G
        - それぞれ1ゲーム目と2ゲーム目の点数
    - 1_1などの_付きの列
        - 1_1は1フレーム目の1投目等、フレームと投球数を表します
        - 2ゲーム目はフレーム数に10を足しており、11~20となっています
    - 1~20列
        - 該当フレームまでの累積得点
        - 2ゲーム目の扱いは上と同じ
        - 累積なので最終チェック時に必要に応じて暗算が必要ですすみません…

    以下の手順で確認するとたぶん早い（たぶん）
    - 以下のデータのヘッダーのチームをクリック
        - するとデータがチームごとに昇順に並ぶはずです
    - 1G(1ゲーム目の点数)、2G(2ゲーム目の点数)があっているか確認
        - あっていれば飛ばします
            - 2ゲーム目を実施しないチームについては1ゲーム目と同じになっている点注意
        - 間違っている場合は途中経過を直します
            - 事務局権限を付与すればスコア更新のページから修正できます
            - スプレッドシートから直すこともできます
            - 1~20の数値だけの列が各フレーム時点の累積点数です（11以降は2ゲーム目です）
                - どこまであっているかを見ながらあたりをつけていきます
            - _がついている列は何フレーム目の何投目かを表しています
            - スペアやガーター等について、マークではなく倒したピンの数が表示されている点に注意してください
    - 個人が正しければチームも正しいので(ミスってなければ)チームは確認不要です
    """
    )
df["2G"] = df["20"] - df["10"]
df["1G"] = df["10"]
df = df[
    [
        "名前",
        "チーム",
        "拠点",
        "1G",
        "2G",
        "1_1",
        "1_2",
        "2_1",
        "2_2",
        "3_1",
        "3_2",
        "4_1",
        "4_2",
        "5_1",
        "5_2",
        "6_1",
        "6_2",
        "7_1",
        "7_2",
        "8_1",
        "8_2",
        "9_1",
        "9_2",
        "10_1",
        "10_2",
        "10_3",
        "11_1",
        "11_2",
        "12_1",
        "12_2",
        "13_1",
        "13_2",
        "14_1",
        "14_2",
        "15_1",
        "15_2",
        "16_1",
        "16_2",
        "17_1",
        "17_2",
        "18_1",
        "18_2",
        "19_1",
        "19_2",
        "20_1",
        "20_2",
        "20_3",
        "1",
        "2",
        "3",
        "4",
        "5",
        "6",
        "7",
        "8",
        "9",
        "10",
        "11",
        "12",
        "13",
        "14",
        "15",
        "16",
        "17",
        "18",
        "19",
        "20",
    ]
]
df = df.set_index("名前")
st.dataframe(utils.make_rank(df, "20"), use_container_width=True)
st.dataframe(utils.make_rank(df_team, "20"), hide_index=True, use_container_width=True)
