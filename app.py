import streamlit as st
import pandas as pd
import os

st.set_page_config(layout="wide")
FILE = "ggst_log.csv"

# キャラリスト
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
if "df" not in st.session_state:
    if os.path.exists(FILE):
        df = pd.read_csv(FILE)
        df["date"] = pd.to_datetime(df["date"], errors="coerce")
        df = df.dropna(subset=["date"])
    else:
        df = pd.DataFrame(columns=["date","my_char","opponent","win_flag","memo"])
    st.session_state.df = df

df = st.session_state.df

# -------------------------
# 戦績入力
# -------------------------
st.title("🎮 GGST戦績管理（シンプル版）")

my_char = st.selectbox("自キャラ", characters)
opponent = st.selectbox("相手キャラ", characters)
result = st.radio("結果", ["勝ち", "負け"])
memo = st.text_input("メモ")

if st.button("記録する"):
    now = pd.Timestamp.now(tz="Asia/Tokyo")
    new = pd.DataFrame([{
        "date": now,
        "my_char": my_char,
        "opponent": opponent,
        "win_flag": 1 if result=="勝ち" else 0,
        "memo": memo
    }])
    df = pd.concat([df, new], ignore_index=True)
    st.session_state.df = df
    df.to_csv(FILE, index=False, date_format="%Y-%m-%d %H:%M:%S")
    st.success(f"{my_char} vs {opponent} を保存しました ({now.strftime('%Y-%m-%d %H:%M:%S')})")

# -------------------------
# 今日の勝率
# -------------------------
if len(df) > 0:
    today_date = pd.Timestamp.now(tz="Asia/Tokyo").date()
    today = df[df["date"].dt.date == today_date]
    if len(today) > 0:
        st.metric("今日の勝率", f"{today['win_flag'].mean()*100:.1f}%")
        st.write(f"今日の試合数：{len(today)}")

# -------------------------
# キャラ別勝率
# -------------------------
if len(df) > 0:
    st.subheader("キャラ別勝率")
    char_stats = df.groupby("my_char")["win_flag"].agg(試合数="count", 勝ち数="sum")
    char_stats["負け数"] = char_stats["試合数"] - char_stats["勝ち数"]
    char_stats["勝率%"] = (char_stats["勝ち数"]/char_stats["試合数"]*100).round(1)
    st.dataframe(char_stats, use_container_width=True)

# -------------------------
# 戦績リスト
# -------------------------
if len(df) > 0:
    st.subheader("戦績リスト")
    view = df.copy()
    st.dataframe(view[["date","my_char","opponent","win_flag","memo"]], use_container_width=True)
