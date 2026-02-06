import streamlit as st
import pandas as pd
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
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.dropna(subset=["date"])
else:
    df = pd.DataFrame(columns=["date","my_char","opponent","win_flag","memo"])

# -------------------------
# 戦績入力
# -------------------------
st.title("🎮 GGST戦績管理（安全版）")

my_char = st.selectbox("自キャラ", characters)
opponent = st.selectbox("相手キャラ", characters)
result = st.radio("結果", ["勝ち", "負け"])
memo = st.text_input("メモ")

if st.button("記録する"):
    new = pd.DataFrame([{
        "date": pd.Timestamp.now(tz="Asia/Tokyo"),
        "my_char": my_char,
        "opponent": opponent,
        "win_flag": 1 if result=="勝ち" else 0,
        "memo": memo
    }])
    df = pd.concat([df, new], ignore_index=True)
    df.to_csv(FILE, index=False, date_format="%Y-%m-%d %H:%M:%S")
    st.success("保存しました。画面を更新すると反映されます。")

# -------------------------
# 今日の勝率
# -------------------------
if len(df) > 0:
    today_date = pd.Timestamp.now(tz="Asia/Tokyo").date()
    today = df[df["date"].dt.date == today_date]
    if len(today) > 0:
        st.metric("今日の勝率", f"{today['win_flag'].mean()*100:.1f}%")
        st.write(f"今日の試合数：{len(today)}")
    else:
        st.info("今日の試合はまだありません")

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
# 苦手キャラランキング
# -------------------------
if len(df) > 0:
    st.subheader("⚠️ 苦手キャラ")
    mu = df.groupby("opponent")["win_flag"].agg(["count","mean"])
    mu = mu[mu["count"] >= 5]  # 試行回数5回以上
    mu["勝率%"] = (mu["mean"]*100).round(1)
    st.dataframe(mu.sort_values("勝率%"))

# -------------------------
# 戦績リスト
# -------------------------
if len(df) > 0:
    st.subheader("戦績リスト")
    st.dataframe(df[["date","my_char","opponent","win_flag","memo"]], use_container_width=True)

# -------------------------
# メモ振り返り
# -------------------------
if len(df) > 0:
    st.subheader("📝 メモ振り返り")
    mc = st.selectbox("キャラ選択", df["my_char"].unique(), key="memo_char")
    md = df[(df["my_char"]==mc) & (df["memo"]!="")].tail(5)
    for _, r in md.iterrows():
        st.write(f"vs {r['opponent']}：{r['memo']}")

# -------------------------
# CSVバックアップ
# -------------------------
st.subheader("💾 CSVバックアップ")
if len(df) > 0:
    csv = df.to_csv(index=False).encode("utf-8-sig")
    st.download_button(
        label="📥 戦績CSVをダウンロード",
        data=csv,
        file_name="ggst_backup.csv",
        mime="text/csv"
    )

