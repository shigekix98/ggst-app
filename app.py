import streamlit as st
import pandas as pd
import os
from datetime import datetime

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
    df = pd.DataFrame(
        columns=["date","my_char","opponent","result","memo"]
    )

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

    df["win_flag"] = (df["result"]=="Win").astype(int)
    df["date"] = pd.to_datetime(df["date"])

    st.header("📊 戦績分析")

    # 総合勝率
    overall = df["win_flag"].mean()*100
    st.metric("総合勝率", f"{overall:.1f}%")

    # -------------------------
    # 直近成績
    # -------------------------
    st.subheader("📈 直近パフォーマンス")

    N = st.slider("直近何戦を見る？",10,100,30)
    recent = df.tail(N)
    recent_rate = recent["win_flag"].mean()*100

    st.metric(f"直近{N}戦勝率",f"{recent_rate:.1f}%")

    if recent_rate > overall:
        st.success("調子が上向きです 👍")
    else:
        st.warning("少し調子が落ちています")

    # -------------------------
    # マッチアップ分析
    # -------------------------
    st.subheader("🎯 マッチアップ別勝率")

    mu = (
        df.groupby(["my_char","opponent"])["win_flag"]
        .agg(["count","mean"])
        .reset_index()
    )

    mu["winrate"] = mu["mean"]*100

    st.dataframe(mu.sort_values("winrate"))

    # -------------------------
    # 🔥 対策すべきキャラ通知
    # -------------------------
    st.subheader("🚨 対策すべきキャラ")

    danger = mu[
        (mu["count"] >= 5) &
        (mu["winrate"] < 40)
    ].sort_values("winrate")

    if len(danger) > 0:
        for _,r in danger.iterrows():
            st.error(
                f"⚠️ {r['my_char']} vs {r['opponent']} "
                f"勝率{r['winrate']:.1f}% "
                f"（{int(r['count'])}戦）\n"
                f"👉 このキャラは要対策！"
            )
    else:
        st.success("特に対策が必要なキャラはいません 👍")

    # -------------------------
    # 勝率推移
    # -------------------------
    st.subheader("📈 勝率推移")

    df["cum_rate"]=df["win_flag"].expanding().mean()*100
    st.line_chart(df["cum_rate"])

# -------------------------
# 削除機能
# -------------------------
st.header("🗑️ 記録削除")

if len(df)>0:

    idx = st.selectbox(
        "削除する試合",
        df.index,
        format_func=lambda x:
        f"{df.loc[x,'date']} | "
        f"{df.loc[x,'my_char']} vs {df.loc[x,'opponent']} | "
        f"{df.loc[x,'result']}"
    )

    if st.button("削除"):
        df = df.drop(idx)
        df.to_csv(DATA_FILE,index=False)
        st.warning("削除しました")
        st.rerun()

