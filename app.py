import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path

st.set_page_config(layout="wide")

# CSVパス
FILE = Path(__file__).parent / "ggst_log.csv"

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
# session_state に df を保持
# -------------------------
if "df" not in st.session_state:
    if FILE.exists():
        df_load = pd.read_csv(FILE)

        # ★ここで日付を安全に datetime に変換
        df_load["date"] = pd.to_datetime(df_load["date"], errors="coerce")
        df_load = df_load.dropna(subset=["date"])  # 変換できなかった行は削除

        st.session_state.df = df_load
    else:
        st.session_state.df = pd.DataFrame(columns=["date","my_char","opponent","win_flag","memo"])

df = st.session_state.df

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
result = st.radio("結果", ["勝ち", "負け"])
memo = st.text_input("メモ")

if st.button("記録する"):
    now = pd.Timestamp.now(tz="Asia/Tokyo")
    new = pd.DataFrame([{
        "date": now,  # ★datetime型で保存
        "my_char": my_char,
        "opponent": opponent,
        "win_flag": 1 if result=="勝ち" else 0,
        "memo": memo
    }])

    # session_state に追記
    st.session_state.df = pd.concat([st.session_state.df, new], ignore_index=True)
    df = st.session_state.df

    # CSV 保存
    df.to_csv(FILE, index=False, date_format="%Y-%m-%d %H:%M:%S")
    st.success(f"{my_char} vs {opponent} を保存しました ({now.strftime('%Y-%m-%d %H:%M:%S')})")

# -------------------------
# 分析
# -------------------------
if len(df) > 0:
    st.header("📊 分析")
    overall = df["win_flag"].mean()*100
    st.metric("総合勝率", f"{overall:.1f}%")

    # 今日の勝率（安全版）
    today = df[df["date"].notna() & (df["date"].dt.date == pd.Timestamp.now(tz="Asia/Tokyo").date())]
    if len(today) > 0:
        st.metric("今日の勝率", f"{today['win_flag'].mean()*100:.1f}%")
        st.write(f"今日の試合数：{len(today)}")

    # キャラ別勝率
    st.subheader("📊 キャラ別勝率（詳細）")
    char_stats = df.groupby("my_char")["win_flag"].agg(試合数="count", 勝ち数="sum")
    char_stats["負け数"] = char_stats["試合数"] - char_stats["勝ち数"]
    char_stats["勝率%"] = (char_stats["勝ち数"]/char_stats["試合数"]*100).round(1)
    st.dataframe(char_stats, use_container_width=True)

    # 勝率推移（日別／月別）
    st.subheader("📈 勝率推移（日別／月別）")
    period = st.radio("集計単位", ["日別","月別"], horizontal=True)
    sel_char = st.selectbox("キャラ選択（推移）", df["my_char"].unique())
    df_rate = df[df["my_char"]==sel_char].copy()

    if period=="日別":
        df_rate["date_only"] = df_rate["date"].dt.date
        win_rate = df_rate.groupby("date_only")["win_flag"].mean()*100
        win_rate.index = pd.to_datetime(win_rate.index)
    else:
        df_rate["month"] = df_rate["date"].dt.to_period("M")
        win_rate = df_rate.groupby("month")["win_flag"].mean()*100
        win_rate.index = win_rate.index.to_timestamp()

    st.line_chart(win_rate, use_container_width=True)

    # 直近勝率
    st.subheader("直近パフォーマンス")
    N = st.slider("直近何戦？", 10, 100, 30)
    st.metric("直近勝率", f"{df.tail(N)['win_flag'].mean()*100:.1f}%")

# -------------------------
# 戦績リスト管理
# -------------------------
st.header("📋 戦績管理")
if len(df) > 0:
    df["result"] = df["win_flag"].map({1:"勝ち",0:"負け"})
    c1,c2 = st.columns(2)
    with c1:
        mf = st.selectbox("自キャラ絞り込み", ["全て"]+list(df["my_char"].unique()))
    with c2:
        of = st.selectbox("相手キャラ絞り込み", ["全て"]+list(df["opponent"].unique()))

    view = df.copy()
    if mf != "全て": view = view[view["my_char"]==mf]
    if of != "全て": view = view[view["opponent"]==of]

    show = view[["date","my_char","opponent","result","memo"]].copy()
    show["削除"] = False

    edited = st.data_editor(show, use_container_width=True, height=300)
    del_rows = edited[edited["削除"]==True]

    if len(del_rows)>0 and st.button("チェック削除"):
        for _,r in del_rows.iterrows():
            df = df[~(
                (df["date"]==r["date"]) &
                (df["my_char"]==r["my_char"]) &
                (df["opponent"]==r["opponent"])
            )]
        st.session_state.df = df
        df.to_csv(FILE, index=False, date_format="%Y-%m-%d %H:%M:%S")
        st.success("削除しました。再読み込みしてください")

# -------------------------
# バックアップダウンロード
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

