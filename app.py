import streamlit as st
import pandas as pd
import plotly.express as px
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
    if len(df) > 0:
        df["date"] = pd.to_datetime(df["date"], errors='coerce')
else:
    df = pd.DataFrame(columns=["date","my_char","opponent","win_flag","memo"])

# -------------------------
# 入力
# -------------------------
st.title("🎮 GGST戦績管理ツール")
st.subheader("➕ 戦績入力")

if "fixed_char" not in st.session_state:
    st.session_state.fixed_char = None

fix = st.checkbox("自キャラ固定モード")
if fix:
    st.session_state.fixed_char = st.selectbox("固定キャラ", characters)
    my_char = st.session_state.fixed_char
    st.write(f"使用キャラ：**{my_char}**")
else:
    my_char = st.selectbox("自キャラ", characters)

opponent = st.selectbox("相手キャラ", characters)
result = st.radio("結果", ["勝ち","負け"])
memo = st.text_input("メモ")

from datetime import datetime

if st.button("記録する"):
    new = pd.DataFrame([{
        # ここで文字列に変換
        "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "my_char": my_char,
        "opponent": opponent,
        "win_flag": 1 if result=="勝ち" else 0,
        "memo": memo
    }])
    df = pd.concat([df, new], ignore_index=True)
    df.to_csv(FILE, index=False)
    st.success("保存しました")


# -------------------------
# 総合勝率
# -------------------------
if len(df) > 0:
    overall = df["win_flag"].mean() * 100
    st.metric("総合勝率", f"{overall:.1f}%")

# -------------------------
# 勝率推移（日別／月別 + キャラ別切替）
# -------------------------
if len(df) > 0:
    st.subheader("📈 勝率推移")
    chars = ["全体"] + list(df["my_char"].unique())
    sel_char = st.selectbox("キャラ選択", chars, key="rate_char")
    period = st.radio("表示単位", ["日別","月別"], horizontal=True)

    plot_df = df.copy()
    if sel_char != "全体":
        plot_df = plot_df[plot_df["my_char"] == sel_char]

    plot_df["date"] = pd.to_datetime(plot_df["date"], errors='coerce')
    plot_df = plot_df.dropna(subset=["date"])

    if period == "日別":
        plot_df["period"] = plot_df["date"].dt.date
    else:
        plot_df["period"] = plot_df["date"].dt.to_period("M").astype(str)

    rate_df = plot_df.groupby("period")["win_flag"].agg(["count","mean"]).rename(columns={"mean":"win_rate"})
    rate_df["win_rate"] = (rate_df["win_rate"]*100).round(1)
    
    if len(rate_df) > 0:
        st.line_chart(rate_df["win_rate"])
    else:
        st.info("表示可能なデータがありません")

# -------------------------
# 苦手キャラアラート
# -------------------------
if len(df) > 0:
    st.subheader("⚠️ 苦手キャラアラート")
    alert_df = df.groupby("opponent")["win_flag"].agg(["count","mean"])
    alert_df = alert_df[alert_df["count"] >= 5]
    alert_df["win_rate"] = (alert_df["mean"]*100).round(1)
    alert_df = alert_df.sort_values("win_rate")
    st.dataframe(alert_df)

# -------------------------
# メモ分析
# -------------------------
if len(df) > 0:
    st.subheader("📝 メモ振り返り")
    mc = st.selectbox("キャラ", df["my_char"].unique(), key="memo_char")
    of = st.selectbox("相手キャラ", ["全て"]+list(df["opponent"].unique()), key="memo_opponent")
    md = df[(df["my_char"]==mc)&(df["memo"]!="")]
    if of != "全て":
        md = md[md["opponent"]==of]
    md = md.tail(10)
    for _, r in md.iterrows():
        st.write(f"{r['date']} vs {r['opponent']}：{r['memo']}")

# -------------------------
# 戦績リスト管理
# -------------------------
st.header("📋 戦績管理")
if len(df) > 0:
    df["result"] = df["win_flag"].map({1:"勝ち",0:"負け"})

    c1,c2 = st.columns(2)
    with c1:
        mf = st.selectbox("自キャラ絞り込み", ["全て"] + list(df["my_char"].unique()))
    with c2:
        of = st.selectbox("相手キャラ絞り込み", ["全て"] + list(df["opponent"].unique()))

    view = df.copy()
    if mf != "全て": view = view[view["my_char"]==mf]
    if of != "全て": view = view[view["opponent"]==of]

    show = view[["date","my_char","opponent","result","memo"]].copy()
    show["削除"] = False

    edited = st.data_editor(show, use_container_width=True, height=300)
    del_rows = edited[edited["削除"]==True]

    if len(del_rows) > 0 and st.button("チェック削除"):
        for _, r in del_rows.iterrows():
            df = df[~((df["date"]==r["date"]) & (df["my_char"]==r["my_char"]) & (df["opponent"]==r["opponent"]))]
        df.to_csv(FILE, index=False)
        st.success("削除しました。再読み込みしてください")

# -------------------------
# バックアップダウンロード
# -------------------------
st.subheader("💾 データバックアップ")
if len(df) > 0:
    csv = df.to_csv(index=False).encode("utf-8-sig")
    st.download_button("📥 戦績CSVをダウンロード", data=csv, file_name="ggst_backup.csv", mime="text/csv")
else:
    st.info("まだデータがありません")
