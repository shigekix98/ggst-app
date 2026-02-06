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
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.dropna(subset=["date"])
else:
    df = pd.DataFrame(columns=["date","my_char","opponent","win_flag","memo"])

# -------------------------
# 戦績入力
# -------------------------
st.title("🎮 GGST戦績管理＋分析")

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
# 総合勝率
# -------------------------
if len(df) > 0:
    st.subheader("📊 総合勝率")
    overall = df["win_flag"].mean() * 100
    st.metric("総合勝率", f"{overall:.1f}%")

# -------------------------
# 今日の勝率
# -------------------------
if len(df) > 0:
    today_date = pd.Timestamp.now(tz="Asia/Tokyo").date()
    today = df[df["date"].apply(lambda x: x.date()==today_date)]
    if len(today) > 0:
        st.metric("今日の勝率", f"{today['win_flag'].mean()*100:.1f}%")
        st.write(f"今日の試合数：{len(today)}")
    else:
        st.info("今日の試合はまだありません")

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
# 勝率推移（キャラ別）
# -------------------------
if len(df) > 0:
    st.subheader("📈 勝率推移（キャラ別）")

    # キャラ選択
    sel = st.selectbox("キャラ選択", df["my_char"].unique(), key="rate_char")

    # 集計方法選択（日別／月別）
    period = st.selectbox("集計単位", ["日別", "月別"])

    cdf = df[df["my_char"]==sel].copy()
    cdf["date"] = pd.to_datetime(cdf["date"], errors="coerce")
    cdf = cdf.dropna(subset=["date"])

    if period == "日別":
        cdf_group = cdf.groupby(cdf["date"].dt.date)["win_flag"].mean()
    else:  # 月別
        cdf_group = cdf.groupby(cdf["date"].dt.to_period("M"))["win_flag"].mean()

    st.line_chart(cdf_group * 100, use_container_width=True)

# -------------------------
# 苦手キャラアラート
# -------------------------
if len(df) > 0:
    st.subheader("⚠️ 苦手キャラアラート")

    filter_char = st.selectbox("自キャラを選択", df["my_char"].unique(), key="alert_char")
    filtered = df[df["my_char"]==filter_char]

    alert = (
        filtered.groupby("opponent")["win_flag"]
        .agg(["count","mean"])
        .query("count>=5")  # 試行回数5以上
    )
    alert["勝率%"] = (alert["mean"]*100).round(1)
    alert = alert.sort_values("勝率%")
    alert_low = alert[alert["勝率%"]<40]

    if len(alert_low) > 0:
        st.dataframe(alert_low[["count","勝率%"]])
    else:
        st.info("苦手キャラは今のところありません")

# -------------------------
# 苦手キャラレーダー
# -------------------------
if len(df) > 0:
    st.subheader("⚠️ 苦手キャラレーダー")

    # 自キャラ選択
    rc = st.selectbox("自キャラを選択", df["my_char"].unique(), key="weak_radar_char")

    # 自キャラで絞り込み
    rdf = df[df["my_char"]==rc]

    # 集計
    mu = rdf.groupby("opponent")["win_flag"].agg(["count","mean"])
    mu = mu[mu["count"] >= 5]  # 試行回数5以上
    mu["勝率%"] = (mu["mean"]*100).round(1)
    mu = mu.reset_index()

    if len(mu) >= 3:  # レーダーチャートは3点以上必要
        mu["color"] = mu["勝率%"].apply(lambda x: "red" if x<40 else "yellow" if x<60 else "lime")

        import plotly.express as px
        fig = px.line_polar(
            mu,
            r="勝率%",
            theta="opponent",
            line_close=True,
            template="plotly_dark"
        )
        fig.update_traces(fill="toself")
        fig.add_scatterpolar(
            r=mu["勝率%"],
            theta=mu["opponent"],
            mode="markers+text",
            marker=dict(size=10, color=mu["color"]),
            text=[f"{v:.0f}%" for v in mu["勝率%"]]
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("苦手キャラレーダーを表示するには、試行回数5以上の相手キャラが3人以上必要です。")

# -------------------------
# 戦績リスト
# -------------------------
if len(df) > 0:
    st.subheader("📋 戦績リスト管理")

    # 表示用にコピー
    view = df.copy()
    view["result"] = view["win_flag"].map({1: "勝ち", 0: "負け"})
    view["削除"] = False  # 削除チェック列

    # データエディタで表示
    edited = st.data_editor(
        view[["date","my_char","opponent","result","memo","削除"]],
        use_container_width=True,
        height=300
    )

    # 削除処理
    del_rows = edited[edited["削除"]==True]
    if len(del_rows) > 0 and st.button("チェック削除"):
        for _, r in del_rows.iterrows():
            df = df[~(
                (df["date"]==r["date"]) &
                (df["my_char"]==r["my_char"]) &
                (df["opponent"]==r["opponent"])
            )]
        df.to_csv(FILE, index=False, date_format="%Y-%m-%d %H:%M:%S")
        st.success("削除しました。画面を更新すると反映されます。")

# -------------------------
# メモ振り返り
# -------------------------
if len(df) > 0:
    st.subheader("📝 メモ分析")

    # 自キャラ選択
    memo_my = st.selectbox("自キャラを選択", df["my_char"].unique(), key="memo_my_char")

    # 相手キャラ選択（全て含めるオプション付き）
    opponents = ["全て"] + list(df["opponent"].unique())
    memo_opponent = st.selectbox("相手キャラで絞り込み", opponents, key="memo_opponent_char")

    # フィルタリング
    memos = df[(df["my_char"]==memo_my) & (df["memo"]!="")]
    if memo_opponent != "全て":
        memos = memos[memos["opponent"]==memo_opponent]

    memos = memos.sort_values("date", ascending=False)

    # 表示
    if len(memos) > 0:
        for _, row in memos.head(5).iterrows():
            st.write(f"vs {row['opponent']} ({row['date'].strftime('%Y-%m-%d')}): {row['memo']}")
    else:
        st.info("まだメモはありません")

# -------------------------
# CSVバックアップ
# -------------------------
if len(df) > 0:
    st.subheader("💾 CSVバックアップ")
    csv = df.to_csv(index=False).encode("utf-8-sig")
    st.download_button(
        label="📥 戦績CSVをダウンロード",
        data=csv,
        file_name="ggst_backup.csv",
        mime="text/csv"
    )
