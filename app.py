import streamlit as st
import pandas as pd
import os
from datetime import datetime

# -------------------------
# 基本設定（スマホUI）
# -------------------------
st.set_page_config(
    page_title="GGST戦績管理",
    layout="centered"
)

st.title("🎮 GGST戦績管理アプリ")

DATA_FILE = "ggst_log.csv"

# -------------------------
# キャラ設定
# -------------------------

favorite_chars = ["エルフェルト"]  # ⭐自キャラをここに

all_chars = [
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

char_list = favorite_chars + [c for c in all_chars if c not in favorite_chars]

# -------------------------
# データ読み込み
# -------------------------
if os.path.exists(DATA_FILE):
    df = pd.read_csv(DATA_FILE)
else:
    df = pd.DataFrame(columns=["date","opponent","result","memo"])

# -------------------------
# 入力UI
# -------------------------
st.header("📌 戦績入力")

col1, col2 = st.columns(2)

with col1:
    opponent = st.selectbox("相手キャラ", char_list)

with col2:
    result = st.radio("結果", ["Win","Lose"], horizontal=True)

memo = st.text_input("メモ（任意）")

if st.button("✅ 記録する", use_container_width=True):
    new_row = {
        "date": datetime.now(),
        "opponent": opponent,
        "result": result,
        "memo": memo
    }
    df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
    df.to_csv(DATA_FILE, index=False)
    st.success("保存しました！")

# -------------------------
# 統計処理
# -------------------------
if len(df) > 0:

    st.header("📊 戦績分析")

    df["win_flag"] = df["result"].apply(lambda x: 1 if x=="Win" else 0)

    total = len(df)
    wins = df["win_flag"].sum()
    winrate = wins / total * 100

    st.metric("総合勝率", f"{winrate:.1f}%")

    # キャラ別
    char_stats = (
        df.groupby("opponent")["win_flag"]
        .agg(["count","mean"])
        .reset_index()
    )
    char_stats["winrate"] = char_stats["mean"]*100

    st.subheader("キャラ別勝率")
    st.dataframe(
        char_stats[["opponent","count","winrate"]]
        .sort_values("winrate")
    )

    # -------------------------
    # 苦手キャラ分析
    # -------------------------
    st.subheader("⚠️ 苦手キャラ")

    weak = char_stats[char_stats["count"]>=5]
    if len(weak)>0:
        worst = weak.sort_values("winrate").head(3)
        for _, r in worst.iterrows():
            st.write(
                f"🔥 {r['opponent']} "
                f"勝率 {r['winrate']:.1f}% "
                f"({int(r['count'])}戦)"
            )

    # -------------------------
    # グラフ
    # -------------------------
    st.subheader("📈 勝率推移")

    df["cum_winrate"] = df["win_flag"].expanding().mean()*100
    st.line_chart(df["cum_winrate"])

    st.subheader("📊 キャラ別勝率グラフ")
    chart_data = char_stats.set_index("opponent")["winrate"]
    st.bar_chart(chart_data)

# -------------------------
# 生データ表示
# -------------------------
st.header("📄 記録一覧")
st.dataframe(df.tail(50))
