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
# 戦績入力
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

if st.button("記録する"):
    now = pd.Timestamp.now(tz="Asia/Tokyo")
    new = pd.DataFrame([{
        "date": now.isoformat(),   # ← 日付を文字列で保存
        "my_char": my_char,
        "opponent": opponent,
        "win_flag": 1 if result=="勝ち" else 0,
        "memo": memo
    }])
    df = pd.concat([df, new], ignore_index=True)
    df.to_csv(FILE, index=False)
    st.success("保存しました。反映は次回リロード時に行われます。")

# -------------------------
# 総合勝率
# -------------------------
if len(df) > 0:
    st.header("📊 分析")
    overall = df["win_flag"].mean()*100
    st.metric("総合勝率", f"{overall:.1f}%")

# -------------------------
# キャラ別勝率
# -------------------------
if len(df) > 0:
    st.subheader("📊 キャラ別勝率")
    char_stats = df.groupby("my_char")["win_flag"].agg(試合数="count", 勝ち数="sum")
    char_stats["負け数"] = char_stats["試合数"] - char_stats["勝ち数"]
    char_stats["勝率%"] = (char_stats["勝ち数"]/char_stats["試合数"]*100).round(1)
    st.dataframe(char_stats, use_container_width=True)

# -------------------------
# 苦手キャラ分析（テーブル＋レーダー）
# -------------------------
if len(df) > 0:
    st.subheader("⚠️ 苦手キャラ分析（テーブル＋レーダー）")
    filter_char = st.selectbox("自キャラを選択", df["my_char"].unique(), key="weak_char")
    filtered = df[df["my_char"]==filter_char]
    mu = filtered.groupby("opponent")["win_flag"].agg(["count","mean"])
    mu = mu[mu["count"]>=5]
    mu["勝率%"] = (mu["mean"]*100).round(1)
    mu = mu.sort_values("勝率%")

    alert = mu[mu["勝率%"]<40]
    if len(alert) > 0:
        st.write("▼ 勝率40％以下の相手キャラ")
        st.dataframe(alert[["count","勝率%"]])
    else:
        st.info("苦手キャラは今のところありません")

    if len(mu) > 2:
        mu["color"] = mu["勝率%"].apply(lambda x: "red" if x<40 else ("yellow" if x<60 else "lime"))
        fig = px.line_polar(mu, r="勝率%", theta=mu.index, line_close=True, template="plotly_dark")
        fig.update_traces(fill="toself")
        fig.add_scatterpolar(
            r=mu["勝率%"],
            theta=mu.index,
            mode="markers+text",
            marker=dict(size=10,color=mu["color"]),
            text=[f"{x:.0f}%" for x in mu["勝率%"]]
        )
        st.plotly_chart(fig, use_container_width=True)

# -------------------------
# メモ分析
# -------------------------
if len(df) > 0:
    st.subheader("📝 メモ分析")
    memo_my = st.selectbox("自キャラを選択", df["my_char"].unique(), key="memo_my_char")
    opponents = ["全て"] + list(df["opponent"].unique())
    memo_opponent = st.selectbox("相手キャラで絞り込み", opponents, key="memo_opponent_char")
    memos = df[(df["my_char"]==memo_my) & (df["memo"]!="")]
    if memo_opponent != "全て":
        memos = memos[memos["opponent"]==memo_opponent]
    memos = memos.sort_values("date", ascending=False)
    if len(memos) > 0:
        for _, row in memos.head(5).iterrows():
            st.write(f"vs {row['opponent']} ({row['date'].strftime('%Y-%m-%d')}): {row['memo']}")
    else:
        st.info("まだメモはありません")

# -------------------------
# 戦績リスト管理・削除
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
    edited = st.data_editor(show,use_container_width=True,height=300)
    del_rows = edited[edited["削除"]==True]
    if len(del_rows)>0 and st.button("チェック削除"):
        for _, r in del_rows.iterrows():
            df = df[~(
                (df["date"]==r["date"]) &
                (df["my_char"]==r["my_char"]) &
                (df["opponent"]==r["opponent"])
            )]
        df.to_csv(FILE,index=False)
        st.success("削除しました。再読み込みしてください")

# -------------------------
# CSVバックアップ
# -------------------------
st.subheader("💾 データバックアップ")
if len(df) > 0:
    csv = df.to_csv(index=False).encode("utf-8-sig")
    st.download_button(label="📥 戦績CSVをダウンロード", data=csv, file_name="ggst_backup.csv", mime="text/csv")
else:
    st.info("まだデータがありません")
