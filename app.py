import streamlit as st
import pandas as pd
from datetime import datetime
import os

st.set_page_config(layout="wide")
FILE = "ggst_log.csv"

# -------------------------
# キャラリスト
# -------------------------
characters = [
    "ソル","カイ","メイ","ミリア","チップ",
    "ポチョムキン","ファウスト","アクセル",
    "ラムレザル","レオ","名残雪",
    "ジオヴァーナ","ハッピーケイオス",
    "ブリジット","シン","ベッドマン？",
    "飛鳥=R#","ジョニー","エルフェルト",
    "ザトー","闇慈","イノ","ゴールドルイス",
    "ジャック・オー","梅喧","テスタメント",
    "A.B.A","スレイヤー","ディズィー",
    "ヴェノム","ユニカ","ルーシー"
]

# -------------------------
# データ読み込み
# -------------------------
if os.path.exists(FILE):
    df = pd.read_csv(FILE)
else:
    df = pd.DataFrame(columns=["date","my_char","opponent","win_flag","memo"])

# -------------------------
# 戦績入力
# -------------------------
st.title("🎮 GGST戦績管理（削除機能付き）")
st.subheader("➕ 戦績入力")

my_char = st.selectbox("自キャラ", characters)
opponent = st.selectbox("相手キャラ", characters)
result = st.radio("結果", ["勝ち","負け"])
memo = st.text_input("メモ")

if st.button("記録する"):
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    new = pd.DataFrame([{
        "date": now_str,
        "my_char": my_char,
        "opponent": opponent,
        "win_flag": 1 if result=="勝ち" else 0,
        "memo": memo
    }])
    df = pd.concat([df, new], ignore_index=True)
    df.to_csv(FILE, index=False)
    st.success("保存しました")

# -------------------------
# 戦績リスト表示＆削除
# -------------------------
st.header("📋 戦績リスト")

if len(df) > 0:
    view = df.copy()
    view["result"] = view["win_flag"].map({1:"勝ち", 0:"負け"})
    view["削除"] = False  # チェック用列

    edited = st.data_editor(
        view[["date","my_char","opponent","result","memo","削除"]],
        use_container_width=True,
        height=300
    )

    # 削除処理
    del_rows = edited[edited["削除"] == True]
    if len(del_rows) > 0 and st.button("選択行を削除"):
        for _, r in del_rows.iterrows():
            df = df[~(
                (df["date"] == r["date"]) &
                (df["my_char"] == r["my_char"]) &
                (df["opponent"] == r["opponent"])
            )]
        df.to_csv(FILE, index=False)
        st.success("削除しました。再読み込みしてください")

else:
    st.info("まだ戦績がありません")


