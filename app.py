import streamlit as st
import pandas as pd
from datetime import datetime
import os

DATA_FILE = "ggst_matches.csv"

st.set_page_config(layout="wide")
st.title("GGST 戦績管理")

# データ読み込み
if os.path.exists(DATA_FILE):
    df = pd.read_csv(DATA_FILE)
else:
    df = pd.DataFrame(columns=[
        "date","my_char","opponent","result","memo"
    ])

char_list = [
    "ソル","カイ","メイ","ミリア","チップ",
    "ポチョムキン","ファウスト","アクセル",
    "ラムレザル","レオ","名残雪",
    "ジオヴァーナ","ハッピーケイオス",
    "ブリジット","シン","ベッドマン？",
    "飛鳥=R#","ジョニー","エルフェルト",
    "ザトー","闇慈","イノ","ゴールドルイス",
    "ジャック・オー","梅喧","テスタメント","A.B.A"
    "スレイヤー","ディズィー","ヴェノム","ユニカ","ルーシー"
]

st.header("🎮 戦績入力")

c1,c2 = st.columns(2)
with c1:
    my_char = st.selectbox("自キャラ", char_list)
with c2:
    opponent = st.selectbox("相手キャラ", char_list)

result = st.radio("勝敗", ["Win","Lose"], horizontal=True)
memo = st.text_input("対戦メモ")

if st.button("保存"):
    new_data = pd.DataFrame([{
        "date": datetime.now(),
        "my_char": my_char,
        "opponent": opponent,
        "result": result,
        "memo": memo
    }])
    df = pd.concat([df,new_data])
    df.to_csv(DATA_FILE,index=False)
    st.success("保存完了！")

# 基本統計
st.header("📊 基本統計")
if len(df)>0:
    wins=(df["result"]=="Win").sum()
    total=len(df)
    st.metric("総試合数",total)
    st.metric("勝率",f"{wins/total*100:.1f}%")

# 直近20試合
st.header("⚡ 直近20試合")
recent=df.tail(20)
if len(recent)>0:
    st.metric("直近勝率",
        f"{(recent['result']=='Win').mean()*100:.1f}%")

# 苦手キャラ
st.header("🔥 苦手キャラTOP3")

stats=[]
for char in df["opponent"].unique():
    cdf=df[df["opponent"]==char]
    if len(cdf)<5: continue
    rate=(cdf["result"]=="Win").mean()*100
    stats.append([char,len(cdf),rate])

if stats:
    sdf=pd.DataFrame(
        stats,columns=["キャラ","試合数","勝率"]
    ).sort_values("勝率").head(3)

    for _,r in sdf.iterrows():
        st.error(f"{r['キャラ']} 勝率{r['勝率']:.1f}%")

# メモ検索
st.header("🔍 メモ検索")
key=st.text_input("検索")
if key:
    st.dataframe(df[
        df["memo"].str.contains(key,na=False) |
        df["opponent"].str.contains(key,na=False)
    ])

st.header("履歴")
st.dataframe(df.sort_values("date",ascending=False))
