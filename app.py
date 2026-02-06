import streamlit as st
import pandas as pd
import plotly.express as px
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

# 日付をdatetime型に変換（読み込み時）
if len(df) > 0:
    df["date"] = pd.to_datetime(df["date"], errors="coerce")

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
    # 日付を文字列化して保存
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
    # 再読み込みで反映（即反映はなし）

# -------------------------
# 分析
# -------------------------
if len(df) > 0:
    st.header("📊 分析")

    # 総合勝率
    overall = df["win_flag"].mean() * 100
    st.metric("総合勝率", f"{overall:.1f}%")

    # 今日の勝率
    today_date = datetime.now().date()
    today = df[df["date"].dt.date == today_date]
    if len(today) > 0:
        st.metric("今日の勝率", f"{today['win_flag'].mean()*100:.1f}%")
        st.write(f"今日の試合数：{len(today)}")

    # -------------------------
    # 勝率推移
    # -------------------------
    st.subheader("📈 勝率推移")
    time_filter = st.radio("集計単位", ["日別","月別"])
    char_sel = st.selectbox("キャラ選択（全体は空欄）", ["全体"] + list(df["my_char"].unique()), key="rate_char")

    plot_df = df.copy()
    if char_sel != "全体":
        plot_df = plot_df[plot_df["my_char"] == char_sel]

    plot_df["date"] = pd.to_datetime(plot_df["date"], errors="coerce")
    if time_filter == "日別":
        plot_df["period"] = plot_df["date"].dt.date
    else:
        plot_df["period"] = plot_df["date"].dt.to_period("M").astype(str)

    rate_df = plot_df.groupby("period")["win_flag"].mean().reset_index()
    rate_df["win_rate"] = rate_df["win_flag"]*100

    st.line_chart(rate_df.set_index("period")["win_rate"])

    # -------------------------
    # 苦手キャラアラート
    # -------------------------
    st.subheader("⚠️ 苦手キャラアラート")
    mu = df.groupby("opponent")["win_flag"].agg(["count","mean"])
    mu = mu[mu["count"] >= 5]
    mu["winrate"] = mu["mean"]*100
    mu["color"] = mu["winrate"].apply(lambda x: "red" if x<40 else ("yellow" if x<60 else "lime"))
    st.dataframe(mu.sort_values("winrate"))

    # -------------------------
    # メモ分析
    # -------------------------
    st.subheader("📝 メモ振り返り")
    mc = st.selectbox("キャラ（自キャラフィルタ）", df["my_char"].unique(), key="memo_char")
    of = st.selectbox("相手キャラ（任意）", ["全て"] + list(df["opponent"].unique()), key="memo_opponent")

    md = df[df["my_char"] == mc]
    if of != "全て":
        md = md[md["opponent"] == of]
    md = md[md["memo"] != ""].tail(5)

    for _, r in md.iterrows():
        st.write(f"vs {r['opponent']}：{r['memo']}")

# -------------------------
# 戦績リスト管理
# -------------------------
st.header("📋 戦績管理")
if len(df) > 0:
    df["result"] = df["win_flag"].map({1:"勝ち",0:"負け"})
    c1, c2 = st.columns(2)
    with c1:
        mf = st.selectbox("自キャラ絞り込み", ["全て"] + list(df["my_char"].unique()))
    with c2:
        of = st.selectbox("相手キャラ絞り込み", ["全て"] + list(df["opponent"].unique()))

    view = df.copy()
    if mf != "全て": view = view[view["my_char"] == mf]
    if of != "全て": view = view[view["opponent"] == of]

    show = view[["date","my_char","opponent","result","memo"]].copy()
    show["削除"] = False

    edited = st.data_editor(show, use_container_width=True, height=300)
    del_rows = edited[edited["削除"]==True]

    if len(del_rows) > 0 and st.button("チェック削除"):
        for _, r in del_rows.iterrows():
            df = df[~(
                (df["date"] == r["date"]) &
                (df["my_char"] == r["my_char"]) &
                (df["opponent"] == r["opponent"])
            )]
        df.to_csv(FILE, index=False)
        st.success("削除しました。再読み込みしてください")

# -------------------------
# バックアップ
# -------------------------
st.subheader("💾 データバックアップ")
if len(df) > 0:
    csv = df.to_csv(index=False).encode("utf-8-sig")
    st.download_button(
        label="📥 戦績CSVをダウンロード",
        data=csv,
        file_name="ggst_backup.csv",
        mime="text/csv"
    )
else:
    st.info("まだデータがありません")
