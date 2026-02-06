import streamlit as st
import plotly.express as px
import pandas as pd
from datetime import datetime
import os

st.set_page_config(layout="wide")
FILE = "ggst_log.csv"

# -------------------------
# キャラリスト（エルフェルトを先頭に）
# -------------------------
characters = [
    "エルフェルト", "ソル","カイ","メイ","ミリア","チップ",
    "ポチョムキン","ファウスト","アクセル",
    "ラムレザル","レオ","名残雪",
    "ジオヴァーナ","ハッピーケイオス",
    "ブリジット","シン","ベッドマン？",
    "飛鳥=R#","ジョニー",
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
st.title("🎮 GGST戦績管理（勝率・試合数表示付き）")
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
# 戦績リスト表示＆削除（絞り込み付き）
# -------------------------
st.header("📋 戦績リスト")

if len(df) > 0:
    # 絞り込みセレクト
    col1, col2 = st.columns(2)
    with col1:
        filter_my = st.selectbox("自キャラ絞り込み", ["全て"] + list(df["my_char"].unique()))
    with col2:
        filter_op = st.selectbox("相手キャラ絞り込み", ["全て"] + list(df["opponent"].unique()))

    # フィルタ適用
    view = df.copy()
    if filter_my != "全て":
        view = view[view["my_char"] == filter_my]
    if filter_op != "全て":
        view = view[view["opponent"] == filter_op]

    # 試合数・勝利数・勝率計算
    if len(view) > 0:
        summary = pd.DataFrame({
            "試合数": [len(view)],
            "勝利数": [view["win_flag"].sum()],
            "勝率(%)": [round(view["win_flag"].mean()*100, 1)]
        })
        st.table(summary)
    else:
        st.info("絞り込み結果に該当する戦績がありません")

    # 表示用
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

# -------------------------
# 絞り込み後のサマリー表（自キャラ・相手キャラ別）
# -------------------------
st.subheader("📊 絞り込み後の戦績サマリー（キャラ別）")

if len(view) > 0:
    # 自キャラ別サマリー
    self_summary = (
        view.groupby("my_char")["win_flag"]
        .agg(試合数="count", 勝利数="sum")
    )
    self_summary["勝率(%)"] = (self_summary["勝利数"] / self_summary["試合数"] * 100).round(1)
    st.markdown("**自キャラ別**")
    st.table(self_summary)

    # 相手キャラ別サマリー
    opp_summary = (
        view.groupby("opponent")["win_flag"]
        .agg(試合数="count", 勝利数="sum")
    )
    opp_summary["勝率(%)"] = (opp_summary["勝利数"] / opp_summary["試合数"] * 100).round(1)
    st.markdown("**相手キャラ別**")
    st.table(opp_summary)

else:
    st.info("絞り込み結果に該当する戦績がありません")

# -------------------------
# 勝率＆試合数推移（戦績リストフィルタ連動）
# -------------------------
st.subheader("📈 勝率＆試合数推移（日／月）")

if len(view) > 0:
    # view はすでに戦績リストのフィルタが適用されたデータ
    rate_df = view.copy()

    # 日付列を datetime に変換
    rate_df["date_dt"] = pd.to_datetime(rate_df["date"], errors="coerce")

    # 日ごと／月ごと切り替え
    freq = st.radio("集計単位", ["日ごと", "月ごと"], key="freq_view")
    if freq == "日ごと":
        grouped = rate_df.groupby(rate_df["date_dt"].dt.date)["win_flag"].agg(試合数="count", 勝利数="sum")
    else:
        grouped = rate_df.groupby(rate_df["date_dt"].dt.to_period("M"))["win_flag"].agg(試合数="count", 勝利数="sum")
        grouped.index = grouped.index.to_timestamp()  # plot用に timestamp に変換

    # 勝率計算
    grouped["勝率(%)"] = (grouped["勝利数"] / grouped["試合数"] * 100).round(1)

    # Plotlyで2軸グラフ作成
    fig = px.line(grouped, x=grouped.index, y="勝率(%)", title="勝率＆試合数推移", labels={"y":"勝率(%)", "x":"日付"})
    fig.add_bar(x=grouped.index, y=grouped["試合数"], name="試合数", opacity=0.3, yaxis="y2")

    # 2軸設定
    fig.update_layout(
        yaxis2=dict(
            title="試合数",
            overlaying="y",
            side="right"
        ),
        legend=dict(y=0.99, x=0.01),
        template="plotly_white"
    )

    st.plotly_chart(fig, use_container_width=True)

else:
    st.info("絞り込み結果に該当する戦績がありません")


# -------------------------
# 苦手キャラアラート
# -------------------------
st.header("⚠️ 苦手キャラアラート")

if len(df) > 0:
    # 自キャラ選択フィルタ
    filter_self = st.selectbox("自キャラを選択", ["全て"] + list(df["my_char"].unique()), key="alert_self")
    alert_df = df.copy()
    if filter_self != "全て":
        alert_df = alert_df[alert_df["my_char"] == filter_self]

    # 集計
    stats = (
        alert_df.groupby("opponent")["win_flag"]
        .agg(["count","mean"])
        .reset_index()
    )
    stats = stats[stats["count"] >= 5]  # 試合数5戦以上
    stats["winrate"] = stats["mean"] * 100
    stats = stats.sort_values("winrate")

    # 苦手キャラの抽出
    weak_chars = stats[stats["winrate"] < 40]

    if len(weak_chars) > 0:
        for _, r in weak_chars.iterrows():
            st.warning(f"自キャラ: {filter_self if filter_self!='全て' else '全て'} → 相手キャラ: {r['opponent']} 勝率 {r['winrate']:.1f}% （{int(r['count'])}戦）")
    else:
        st.success("苦手キャラは見つかりません")
else:
    st.info("まだ戦績がありません")

