import streamlit as st
import pandas as pd
import os
from datetime import datetime
import plotly.express as px

# -------------------------
# 基本設定
# -------------------------
st.set_page_config(page_title="GGST戦績分析ツール", layout="centered")
st.title("🎮 GGST戦績分析ツール")

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
# セッション状態
# -------------------------
if "fixed_char" not in st.session_state:
    st.session_state.fixed_char = None

# -------------------------
# データ読み込み
# -------------------------
if os.path.exists(DATA_FILE):
    df = pd.read_csv(DATA_FILE)
else:
    df = pd.DataFrame(columns=["date","my_char","opponent","result","memo"])

# -------------------------
# 自キャラ固定
# -------------------------
st.header("⚙️ 自キャラ設定")

fix = st.checkbox("自キャラ固定モード")

if fix:
    st.session_state.fixed_char = st.selectbox("使用キャラ", char_list)
    st.success(f"{st.session_state.fixed_char}で固定中")

# -------------------------
# 入力UI
# -------------------------
st.header("📌 戦績入力")

if st.session_state.fixed_char:
    my_char = st.session_state.fixed_char
    st.write(f"🎯 自キャラ：{my_char}")
else:
    my_char = st.selectbox("自キャラ", char_list)

opponent = st.selectbox("相手キャラ", char_list)
result = st.radio("結果", ["Win","Lose"], horizontal=True)
memo = st.text_input("メモ")

if st.button("記録する"):
    new = {
        "date": datetime.now(),
        "my_char": my_char,
        "opponent": opponent,
        "result": result,
        "memo": memo
    }
    df = pd.concat([df,pd.DataFrame([new])])
    df.to_csv(DATA_FILE,index=False)
    st.success("保存完了")
    st.rerun()

# -------------------------
# 分析
# -------------------------
if len(df) > 0:

    df["date"] = pd.to_datetime(df["date"])
    df["win_flag"] = (df["result"]=="Win").astype(int)

    st.header("📊 戦績分析")

    # 総合勝率
    overall = df["win_flag"].mean()*100
    st.metric("総合勝率", f"{overall:.1f}%")

    # -------------------------
    # 直近成績
    # -------------------------
    st.subheader("📈 直近パフォーマンス")

    N = st.slider("
