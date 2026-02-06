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
else:
    df = pd.DataFrame(
        columns=["date","my_char","opponent","win_flag","memo"]
    )

# -------------------------
# 入力
# -------------------------
st.title("🎮 GGST戦績管理")

st.subheader("➕ 戦績入力")

my_char = st.selectbox("自キャラ", characters)
opponent = st.selectbox("相手キャラ", characters)
result = st.radio("結果", ["勝ち","負け"])
memo = st.text_input("メモ")

if st.button("記録する"):
    new = pd.DataFrame([{
        "date": pd.Timestamp.now(),
        "my_char": my_char,
        "opponent": opponent,
        "win_flag": 1 if result=="勝ち" else 0,
        "memo": memo
    }])
    df = pd.concat([df,new],ignore_index=True)
    df.to_csv(FILE,index=False)
    st.success("保存しました")

# -------------------------
# 分析開始
# -------------------------
if len(df)>0:

    st.header("📊 分析")

    overall = df["win_flag"].mean()*100
    st.metric("総合勝率",f"{overall:.1f}%")

    # ---------------------
    # キャラ別勝率
    # ---------------------
    st.subheader("キャラ別勝率")

    mu = (
        df.groupby("my_char")["win_flag"]
        .agg(["count","mean"])
        .reset_index()
    )
    mu["winrate"]=mu["mean"]*100
    st.dataframe(mu)

    # ---------------------
    # 勝率推移
    # ---------------------
    st.subheader("📈 勝率推移")

    sel = st.selectbox(
        "キャラ選択",
        df["my_char"].unique()
    )

    cdf = df[df["my_char"]==sel].copy()
    cdf["cum_rate"]=cdf["win_flag"].expanding().mean()*100
    st.line_chart(cdf["cum_rate"])

    # ---------------------
    # 直近成績
    # ---------------------
    st.subheader("直近パフォーマンス")

    N = st.slider("直近何戦？",10,100,30)

    recent=df.tail(N)
    rrate=recent["win_flag"].mean()*100

    st.metric(f"直近{N}戦勝率",f"{rrate:.1f}%")

    # ---------------------
    # レーダー
    # ---------------------
    st.subheader("🕸️ キャラ相性レーダー")

    radar_char=st.selectbox(
        "レーダー自キャラ",
        df["my_char"].unique(),
        key="radar"
    )

    rdf=df[df["my_char"]==radar_char]

    mu=(
        rdf.groupby("opponent")["win_flag"]
        .agg(["count","mean"])
        .reset_index()
    )

    mu=mu[mu["count"]>=3]
    mu["winrate"]=mu["mean"]*100

    if len(mu)>2:

        def color(r):
            if r<40:return "red"
            elif r<60:return "yellow"
            else:return "lime"

        mu["color"]=mu["winrate"].apply(color)

        fig=px.line_polar(
            mu,
            r="winrate",
            theta="opponent",
            line_close=True,
            range_r=[0,100],
            template="plotly_dark"
        )

        fig.update_traces(fill="toself")

        fig.add_scatterpolar(
            r=mu["winrate"],
            theta=mu["opponent"],
            mode="markers+text",
            marker=dict(size=10,color=mu["color"]),
            text=[f"{w:.0f}%" for w in mu["winrate"]],
            textposition="top center"
        )

        st.plotly_chart(fig,use_container_width=True)

    # ---------------------
    # 苦手ランキング
    # ---------------------
    st.subheader("⚠️ 苦手キャラランキング")

    mu=(
        df.groupby("opponent")["win_flag"]
        .agg(["count","mean"])
        .reset_index()
    )

    mu=mu[mu["count"]>=5]
    mu["winrate"]=mu["mean"]*100

    weak=mu.sort_values("winrate")

    st.dataframe(
        weak[["opponent","count","winrate"]]
        .rename(columns={
            "opponent":"キャラ",
            "count":"試合数",
            "winrate":"勝率%"
        })
    )

    # -------------------------
    # 戦績リスト管理（タップ削除）
    # -------------------------
    st.subheader("📋 戦績リスト管理")
    
    df["result"] = df["win_flag"].map({1:"勝ち",0:"負け"})
    
    # 絞り込み
    fchar = st.selectbox(
        "自キャラで絞り込み",
        ["全て"] + list(df["my_char"].unique())
    )
    
    view = df.copy()
    
    if fchar != "全て":
        view = view[view["my_char"] == fchar]
    
    view = view.reset_index(drop=True)
    
    # 表示用
    show = view[[
        "date","my_char","opponent","result","memo"
    ]].copy()
    
    # 削除チェック列追加
    show["削除"] = False
    
    edited = st.data_editor(
        show,
        use_container_width=True,
        height=300,
        column_config={
            "削除": st.column_config.CheckboxColumn(
                "削除",
                help="削除したい行にチェック"
            )
        }
    )
    
    # -----------------
    # 削除処理
    # -----------------
    delete_rows = edited[edited["削除"] == True]
    
    if len(delete_rows) > 0:
        if st.button("チェックした記録を削除"):
            
            # 元データと照合して削除
            for _, row in delete_rows.iterrows():
                df = df[
                    ~(
                        (df["date"] == row["date"]) &
                        (df["my_char"] == row["my_char"]) &
                        (df["opponent"] == row["opponent"])
                    )
                ]
    
            df.to_csv(FILE, index=False)
            st.success("削除しました！再読み込みしてください")
