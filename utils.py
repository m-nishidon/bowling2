import datetime
import random

import gspread
import pandas as pd
import requests
import streamlit as st
from oauth2client.service_account import ServiceAccountCredentials


def calc_bowling_score(pins):
    from itertools import accumulate

    scores = calc_one_game(pins[:21]) + calc_one_game(pins[21:])
    return list(accumulate(scores))


def calc_one_game(pins):
    types, cnts = get_one_game_info(pins)
    first = True
    scores = []
    for i, (type_, cnt) in enumerate(zip(types[:-3], cnts[:-3])):
        if type_ == 1:
            scores.append(cnt + cnts[i + 1] + cnts[i + 2])
        elif first:
            first ^= True
            continue
        else:
            if type_ == 2:
                scores.append(cnts[i - 1] + cnt + cnts[i + 1])
            else:
                scores.append(cnts[i - 1] + cnt)
            first ^= True

    scores.append(sum(pins[-3:]))
    return scores


def get_one_game_info(pins):
    pins = list(pins)
    odd = False
    cnts = []
    types = []  # 0特になし、1ストライク、2スペア
    for pin in pins[:-3]:
        odd ^= True
        if odd:
            if pin == 10:
                cnts.append(pin)
                types.append(1)
            else:
                cnts.append(pin)
                types.append(0)
        else:
            if types[-1] == 1:
                continue
            elif cnts[-1] + pin == 10:
                cnts.append(pin)
                types.append(2)
            else:
                cnts.append(pin)
                types.append(0)

    types += [0, 0, 0]
    cnts += pins[-3:]
    return types, cnts


def get_now():
    # strealitにデプロイするとJSTではなくUTCとなる
    DIFF = 9
    return datetime.datetime.now(datetime.UTC) + datetime.timedelta(hours=DIFF)


# スプレッドシートのデータを読み込み
@st.cache_data
def read_origin_score():
    now = get_now()
    client = connect_spread_sheet()
    # スプレッドシートを開く
    try:
        spreadsheet = client.open("スコア表").worksheet("data")
    except AttributeError:
        connect_spread_sheet.clear()
        client = connect_spread_sheet()
        spreadsheet = client.open("スコア表").worksheet("data")

    sheet_data = spreadsheet.get_all_records()

    df = pd.DataFrame(sheet_data)

    df, df_conf, df_1game_only, df_notice = (
        df[df.columns[:-5]].copy(),
        df[df.columns[-5:-2]][:3].copy(),
        pd.DataFrame(df[df.columns[-2]].copy()),
        pd.DataFrame(df[df.columns[-1]].copy()),
    )

    df_notice["連絡"] = df_notice["連絡"].astype(str)
    r = 10
    for i in range(r, len(df_notice)):
        if df_notice["連絡"][i]:
            r = i
    df_notice = df_notice[:r].copy()

    open_result, stop_update, contest_mode = map(int, df_conf["値"])
    teams_1game_only = set([v for v in df_1game_only["2ゲーム目非実施"] if v])
    df = (
        df[: df.shape[0] // 2].copy() if contest_mode else df[df.shape[0] // 2 :].copy()
    )
    for col in df.columns[:2:-1]:
        if df[~df["チーム"].isin(teams_1game_only)][col].sum() > 0:
            break
    current_frame = int(col.split("_")[0])

    for i in range(df.shape[0]):
        if df.iat[i, 1] not in teams_1game_only:
            continue
        for j in range(21):
            c = j + 24
            df.iat[i, c] = df.iat[i, c - 21]

    df[[str(i) for i in range(1, 21)]] = df[df.columns[3:]].apply(
        calc_bowling_score, result_type="expand", axis=1
    )

    df_team = df[list(df.columns[:3]) + list(df.columns[-20:])].copy()
    df_team = df_team.groupby("チーム", as_index=False).agg(
        {
            "名前": lambda x: "  ".join(x),
            "拠点": "first",
            **{
                col: "sum"
                for col in df_team.columns
                if col not in ["チーム", "名前", "拠点"]
            },
        }
    )
    df_team["人数"] = list(df.groupby("チーム")["名前"].count())
    df_team = df_team.rename(columns={"名前": "メンバー"})
    max_ = df_team["人数"].max()
    df_team[[str(i) for i in range(1, 21)]] = df_team.apply(
        keisha, result_type="expand", axis=1, max_=max_
    )
    df_team = make_rank(df_team, str(current_frame))
    df = make_rank(df, str(current_frame))

    return (
        df,
        df_team,
        current_frame,
        df_conf,
        now,
        open_result,
        stop_update,
        teams_1game_only,
        df_notice,
    )


@st.cache_data
def connect_spread_sheet():
    # Google Sheets APIの認証情報を設定
    scope = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ]

    creds = ServiceAccountCredentials.from_json_keyfile_dict(
        st.secrets["gcp_service_account"], scope
    )
    return gspread.authorize(creds)


def keisha(row, max_):
    rate = max_ / row["人数"]
    for i in range(1, 21):
        row[str(i)] *= rate
    return row[3:-1]


def make_rank(df, current_frame):
    df = df.sort_values(current_frame, ascending=False)
    df["順位"] = [i + 1 for i in range(df.shape[0])]
    return df


def send_message(message, token, image):
    headers = {
        "Authorization": f"Bearer {token}",
    }
    if image:
        files = {
            "message": (None, message),
            "imageFile": ("image.jpg", image, "image/jpeg"),
        }
    else:
        files = {"message": (None, message)}
    requests.post("https://notify-api.line.me/api/notify", headers=headers, files=files)


def update_table(
    requests,
):
    client = connect_spread_sheet()
    # スプレッドシートを開く
    try:
        spreadsheet = client.open("スコア表")
    except AttributeError:
        connect_spread_sheet.clear()
        client = connect_spread_sheet()
        spreadsheet = client.open("スコア表").worksheet("data")
    spreadsheet.batch_update(
        {"value_input_option": "RAW", "data": requests}  # 数値をそのまま書き込む
    )

    st.success("データを送信しました")
    balloons_or_snows()


def balloons_or_snows():
    if random.randint(0, 1):
        st.balloons()
    else:
        st.snow()


def style_diff(col, target):
    t = target[col.name]
    return [
        "background-color: lightcoral;" if t[idx] != val else ""
        for idx, val in col.items()
    ]


def highlight_specific_cell(x, row, col):
    df_styler = pd.DataFrame("", index=x.index, columns=x.columns)
    df_styler.iat[row, col] = "background-color: yellow"
    return df_styler


def clear_ss_score_update():
    # import inspect

    # print(inspect.stack())
    for key in ["rc", "df"]:
        if key in st.session_state:
            del st.session_state[key]
