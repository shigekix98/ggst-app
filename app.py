import streamlit as st
import pandas as pd
import os
from datetime import datetime

# -------------------------
# 基本設定
# -------------------------
st.set_page_config(
    page_title="GGST戦績管理",
    layout="centered"
)

st.title("🎮 GGST戦績管理アプリ")

DATA_FILE = "ggst_log.csv"

# -------------------------
# キャラリスト
# -------------------------
char_list = [
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
# セッション状態（自キャラ固定）
# -------------------------
if "fixed_char" not in st.session_state:
    st.session_state.fixed_char = None

# -------------------------
# データ読み込み
# -------------------------
if os.path.exists(DATA_FILE):
    df = pd.read_csv(DATA_FILE)
else:
    df = pd.DataFrame(
        columns=["date","my_char","opponent","result","memo"]
    )

# -------------------------
# 自キャラ固定設定
# -------------------------
st.header("⚙️ 自キャラ設定")

colA, colB = st.columns(2)

with colA:
    fixed_toggle = st.checkbox("自キャラを固定する")

with colB:
    selected_char = st.selectbox("使用キャラ", char_list)

if fixed_toggle:
    st.session_state.fixed_char = selected_char
    st.success(f"✅ {selected_char}で固定中")

# -------------------------
# 入力UI
# -------------------------
st.header("📌 戦績入力")

# 自キャラ自動設定
if st.session_state.fixed_char:
    my_char = st.session_state.fixed_char
    st.write(f"🎯 自キャラ：**{my_char}（固定中）**")
else:
    my_char = st.selectbox("自分のキャラ", char_list)

opponent = st.selectbox("相手キャラ", char_list)

result = st.radio("結果", ["Win","Lose"], horizontal=True)

memo = st.text_input("メモ（任意）")

if st.button("✅ 記録する", use_container_width=True):
    new_row = {
        "date": datetime.now(),
        "my_char": my_char,
        "opponent": opponent,
        "result": result,
        "memo": memo
    }
    df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
    df.to_csv(DATA_FILE, index=False)
    st.success("保存しました！")

# -------------------------
# 分析
# -------------------------
if len(df) > 0:

    st.header("📊 戦績分析")

    df["win_flag"] = df["result"].apply(lambda x: 1 if x=="Win" else 0)

    # 総合勝率
    winrate = df["win_flag"].mean()*100
    st.metric("総合勝率", f"{winrate:.1f}%")

    # 相手別勝率
    char_stats = (
        df.groupby("opponent")["win_flag"]
        .agg(["count","mean"])
        .reset_index()
    )
    char_stats["winrate"] = char_stats["mean"]*100

    st.subheader("📊 相手キャラ別勝率")
    st.dataframe(
        char_stats[["opponent","count","winrate"]]
        .sort_values("winrate")
    )

    # 苦手キャラ
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

    # 勝率推移
    st.subheader("📈 勝率推移")
    df["cum_winrate"] = df["win_flag"].expanding().mean()*100
    st.line_chart(df["cum_winrate"])

    # キャラ別グラフ
    st.subheader("📊 キャラ別勝率グラフ")
    chart_data = char_stats.set_index("opponent")["winrate"]
    st.bar_chart(chart_data)

# -------------------------
# マッチアップ分析（自キャラ×相手）
# -------------------------
st.subheader("🎯 マッチアップ別勝率")

matchup_stats = (
    df.groupby(["my_char","opponent"])["win_flag"]
    .agg(["count","mean"])
    .reset_index()
)

matchup_stats["winrate"] = matchup_stats["mean"] * 100

st.dataframe(
    matchup_stats[["my_char","opponent","count","winrate"]]
    .sort_values("winrate")
)

# -------------------------
# データ表示＆削除
# -------------------------
st.header("📄 記録一覧")

if len(df) > 0:

    # 表示用インデックス振り直し
    df_display = df.reset_index()

    selected_index = st.selectbox(
        "削除する記録を選択",
        df_display.index,
        format_func=lambda x:
            f"{df_display.loc[x,'date']} | "
            f"{df_display.loc[x,'my_char']} vs "
            f"{df_display.loc[x,'opponent']} | "
            f"{df_display.loc[x,'result']}"
    )

    if st.button("🗑️ 選択した記録を削除", use_container_width=True):
        df = df.drop(selected_index)
        df.to_csv(DATA_FILE, index=False)
        st.warning("削除しました！")
        st.rerun()

    st.dataframe(df.tail(50))

else:
    st.write("まだ記録がありません")
