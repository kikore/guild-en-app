import streamlit as st
import pandas as pd
import hashlib
import altair as alt # 円グラフ作成用に追加

# --- 設定 ---
SPREADSHEET_ID = st.secrets["spreadsheet_id"]
COMMON_PASSWORD_HASH = st.secrets["common_password_hash"]

st.set_page_config(page_title="ギルド戦分析", layout="wide")

# --- パスワードを暗号化する関数 ---
def make_hash(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

# --- 関数：スプシ読み込み ---
def load_data(sheet_name):
    # あなたの環境で成功したURL形式
    url = f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/gviz/tq?tqx=out:csv&sheet={sheet_name}"
    return pd.read_csv(url)

# ログイン状態の管理
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'page' not in st.session_state:
    st.session_state.page = "home" # 初期ページ

# --- ログイン画面 ---
if not st.session_state.logged_in:
    st.title("🛡️ ギルドメンバー認証")
    user_id = st.text_input("ユーザーIDを入力")
    password = st.text_input("共通パスワードを入力", type="password")
    
    if st.button("ログイン"):
        try:
            acc_df = load_data("accounts")
            hashed_input = make_hash(password)
            
            # IDが一致し、かつ入力されたパスワードのハッシュが共通ハッシュと一致するか確認
            user_match = acc_df[acc_df['user_id'].astype(str) == str(user_id)]
            
            if not user_match.empty and hashed_input == COMMON_PASSWORD_HASH:
                st.session_state.logged_in = True
                st.session_state.user_name = user_match.iloc[0]['name']
                st.rerun()
            else:
                st.error("IDまたはパスワードが正しくありません")
                # --- ハッシュ値確認用コード（必要時にコメントアウトを外す） ---
                #st.info(f"入力されたパスワードのハッシュ値: {hashed_input}")
            
        except Exception as e:
            st.error("データの読み込みに失敗しました。")
            st.write(e)

# --- ログイン後のメイン画面 ---
else:
    # サイドバー
    # 1. サイドバーの設定
    st.sidebar.markdown("# 📊 ギルド戦データ分析") # メニュー先頭
    st.sidebar.divider() # 区切り線
    
    # ボタンをリンクのように見せるデザイン
    if st.sidebar.button("🏠 << 宴 >> 基本情報", use_container_width=True, type="secondary"):
        st.session_state.page = "home"
        st.rerun()
        
    if st.sidebar.button("⚔️ 戦績データ", use_container_width=True, type="secondary"):
        st.session_state.page = "score"
        st.rerun()
    
    st.sidebar.divider()

    st.sidebar.write(f"👤 {st.session_state.user_name} さん")
    if st.sidebar.button("ログアウト"):
        st.session_state.logged_in = False
        st.rerun()

    # 2. メインコンテンツ
    if st.session_state.page == "home":
        st.title("<< 宴 >> 基本情報") # メインタトルを更新

        # データの読み込み
        try:
            raw_df = load_data("players")
            
            # ギルドIDが 1 のメンバーだけに絞り込み
            df = raw_df[raw_df['現ギルドID'] == 1][['名前', '流派', '備考']].copy()

            # 1. 流派分布（円グラフ）
            st.subheader("🔮 流派分布")
            # 集計処理（ここも「流派」という名前をそのまま使えます）
            job_counts = df['流派'].value_counts().reset_index()
            job_counts.columns = ['流派', '人数']

            empty_left, col_main, empty_right = st.columns([1, 2, 1])

            with col_main:
                domain = ['神相', '鉄衣', '素問', '血河', '九霊', '砕夢', '龍吟']
                range_ = ['#1E90FF', "#FFC400", '#FF69B4', '#8B0000', '#9400D3', "#66DBDB", "#18BE3C"]
                # 円グラフの作成
                chart = alt.Chart(job_counts).mark_arc(innerRadius=50).encode(
                    theta=alt.Theta(field="人数", type="quantitative"),
                    # scaleを使って色を固定
                    color=alt.Color(
                        field="流派", 
                        type="nominal",
                        scale=alt.Scale(domain=domain, range=range_),
                        legend=alt.Legend(title="流派", orient="right")
                    ),
                    tooltip=['流派', '人数']
                ).properties(height=350)
                st.altair_chart(chart, use_container_width=True)

            # 2. メンバー名簿（テーブル）を下に配置
            st.subheader("📝 メンバー名簿")
            st.dataframe(df, hide_index=True, use_container_width=True)

        except Exception as e:
            st.error("データの表示に失敗しました。")

    elif st.session_state.page == "score":
        st.title("⚔️ ギルド戦 戦績データ")
        try:
            score_df = load_data("戦績")
            if '名前' in score_df.columns and 'ダメージ' in score_df.columns:
                st.subheader("🔥 ダメージランキング")
                ranking_df = score_df.sort_values(by='ダメージ', ascending=False)
                st.bar_chart(ranking_df.set_index('名前')['ダメージ'])
            
            st.subheader("📋 戦績詳細一覧")
            st.dataframe(score_df, hide_index=True, use_container_width=True)
        except Exception as e:
            st.error("データの表示に失敗しました。")