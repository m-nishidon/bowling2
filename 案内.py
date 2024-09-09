import io

import streamlit as st
from PIL import Image

import utils

st.title(":bowling:ボウリング大会:bowling:")
utils.clear_ss_score_update()
login_p = False if "login_p" not in st.session_state else True
if not login_p:
    password = st.text_input("パスワードを入力してください:", type="password")
    if password != st.secrets["all"]["password"]:
        st.error("誰かにパスワードを確認してください")
        exit()
st.session_state["login_p"] = True

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
) = utils.read_origin_score()


for notice in df_notice["連絡"]:
    if notice:
        st.info((notice.replace("\n", "  \n")))  # 改行のため

if open_result:
    _, _, contest_mode = map(int, df_conf["値"])
    if "first_visit" not in st.session_state:

        if not contest_mode:
            st.balloons()
        elif open_result:
            st.snow()
st.session_state["first_visit"] = True
utils.clear_ss_score_update()

st.subheader("アプリの説明")
st.markdown(
    """
- リアルタイムで各拠点のスコアを確認することでボウリング大会を盛り上げるためのアプリです
    - 好きなようにボタンを押してもらってOKです！
- リアルタイムで各拠点のスコアを確認するためには、スコアの入力が必要です
    - 余裕のある方はぜひ、スコア更新のページから入力してください！
    - 余裕のそこまでない方も、本ページ下部からスコア表の写真を適宜お送りいただけると助かります！
"""
)

with st.expander("各ページの概要", expanded=False):
    st.markdown(
        """
    1. 「案内」ページ(本ページ)
        - 事務局からの連絡及び参加者からの連絡用
            - 参加者からの連絡は事務局のグループラインに届きますので、確認後適宜対応します
    2. 「順位表」ページ
        - チームと個人の順位表とグラフが表示されます
        - 順位はその時点で登録されているデータをもとに、リアルタイムで更新されていきます
        - 拠点ごと、チームごと、個人ごとにフィルターがかけられます。楽しく確認しましょう！
    3. 「スコア更新」ページ
        - 1と2がありますがどちらで更新しても結果は同じです。使いやすい方で更新ください。
        - スコア更新1はテーブルを直接更新するイメージです
            - 直観的には分かりやすいですが、操作感がいまいちかもしれません
            - 特にiphoneだとひらがな入力できないキーボードに設定変更しながら入力する必要があるのでより難しいです
        - スコア更新2は数字やマークをタップしながら入力していくイメージです
            - 直観的にはわかりにくいかもですが、**慣れればこちらの方が早いと思います**
        - チーム単位程度を目安に、複数人をまとめて登録いただけると大変助かります！
    4. 「事務局用」ページ
        - 事務局のみ使用するページです


    """
    )


st.subheader("QRコード")
with st.expander("QRコードを共有する場合はこちらから表示", expanded=False):
    st.image(Image.open("_images/qrcode.PNG"), caption="QRcode", use_column_width=True)
    st.write(f'パスワードは{st.secrets["all"]["password"]}です。')
# 画像アップロード
st.subheader("画像アップロード")
with st.expander("展開", expanded=False):
    uploaded_file = st.file_uploader(
        "写真や画像を送る場合はアップロードしてください", type=["jpg", "png", "jpeg"]
    )

    if uploaded_file:
        # 画像を表示
        image = Image.open(uploaded_file)
        st.image(image, caption="Uploaded Image", use_column_width=True)
        image_format = image.format
        image_byte_array = io.BytesIO()
        image.save(image_byte_array, format=image_format)
        image_bytes = image_byte_array.getvalue()
        st.session_state["picture"] = image_bytes

st.subheader("事務局グループに連絡")
st.write(
    "事務局のLINEグループにメッセージが送信されます。問い合わせやスコア表のアップロードに使用してください。"
)
st.write("スコア表の写真その他画像等は上の画像アップロードから行ってください")

name = st.text_input("名前を入力してください。(匿名可)")
message = st.text_area("メッセージを入力してください。")

if st.button("送信"):
    if not message:
        st.error("メッセージが入力されていません。")
    else:
        message = "\n".join(["名前", str(name), message])
        token = st.secrets["LINE"]["token"]
        image_bytes = (
            None if "picture" not in st.session_state else st.session_state["picture"]
        )
        st.write(str(image_bytes))
        if not name:
            utils.send_message(message, token, image_bytes)
            st.warning("匿名でメッセージを送信しました。")
            st.session_state["picture"] = None
        else:
            utils.send_message(message, token, image_bytes)
            st.success("メッセージを送信しました。")
            st.session_state["picture"] = None
