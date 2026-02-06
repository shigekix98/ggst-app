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

    N = st.slider("直近何戦？",10,100,30)
    recent = df.tail(N)
    recent_rate = recent["win_flag"].mean()*100

    st.metric(f"直近{N}戦勝率",f"{recent_rate:.1f}%")

    if recent_rate > overall:
        st.success("調子が上向き 👍")
    else:
        st.warning("調子やや下降")

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
    # 対策通知
    # -------------------------
    st.subheader("🚨 対策すべきキャラ")

    danger = mu[(mu["count"]>=5)&(mu["winrate"]<40)]

    if len(danger)>0:
        for _,r in danger.iterrows():
            st.error(
                f"{r['my_char']} vs {r['opponent']} "
                f"勝率{r['winrate']:.1f}%（{int(r['count'])}戦）"
            )
    else:
        st.success("特に対策必須キャラなし 👍")

    # -------------------------
    # 勝率推移（キャラ別）
    # -------------------------
    st.subheader("📈 勝率推移（キャラ別）")

    sel = st.selectbox("キャラ選択", df["my_char"].unique())
    cdf = df[df["my_char"]==sel].copy()

    cdf["cum_rate"] = cdf["win_flag"].expanding().mean()*100
    st.line_chart(cdf["cum_rate"])

    # -------------------------
    # レーダーチャート
    # -------------------------
    st.subheader("🕸️ キャラ相性レーダー")
    
    radar_char = st.selectbox(
        "レーダーを見る自キャラ",
        df["my_char"].unique(),
        key="radar"
    )
    
    radar_df = df[df["my_char"] == radar_char]
    
    mu = (
        radar_df.groupby("opponent")["win_flag"]
        .agg(["count","mean"])
        .reset_index()
    )
    
    mu = mu[mu["count"] >= 3]
    mu["winrate"] = mu["mean"] * 100
    
    if len(mu) > 2:
    
        # 勝率で色分け
        def color(rate):
            if rate < 40:
                return "red"
            elif rate < 60:
                return "yellow"
            else:
                return "lime"
    
        mu["color"] = mu["winrate"].apply(color)
    
        fig = px.line_polar(
            mu,
            r="winrate",
            theta="opponent",
            line_close=True,
            range_r=[0,100],
            template="plotly_dark"
        )
    
        # 線設定
        fig.update_traces(
            fill="toself",
            line=dict(width=3, color="cyan")
        )
    
        # 各点を色分け表示
        fig.add_scatterpolar(
            r=mu["winrate"],
            theta=mu["opponent"],
            mode="markers+text",
            marker=dict(
                size=10,
                color=mu["color"]
            ),
            text=[f"{w:.0f}%" for w in mu["winrate"]],
            textposition="top center"
        )
    
        fig.update_layout(
            paper_bgcolor="black",
            plot_bgcolor="black",
            font=dict(color="white", size=14)
        )
    
        st.plotly_chart(fig, use_container_width=True)
    
    else:
        st.write("レーダー表示するには各キャラ3戦以上必要です")

    # -------------------------
    # 戦績リスト表示
    # -------------------------
    st.subheader("📋 戦績リスト")
    
    if len(df) > 0:
    
        view_df = df.copy()
    
        # 勝敗を見やすく
        view_df["result"] = view_df["win_flag"].map(
            {1:"勝ち", 0:"負け"}
        )
    
        # 表示用整形
        view_df = view_df[[
            "date","my_char","opponent","result"
        ]].sort_index(ascending=False)
    
        st.dataframe(
            view_df,
            use_container_width=True,
            height=300
        )
    
    else:
        st.write("まだ戦績がありません")

# -------------------------
# 削除
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
