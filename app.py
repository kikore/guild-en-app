import streamlit as st
import pandas as pd
import hashlib
import altair as alt # 円グラフ作成用に追加
import plotly.express as px # 冒頭に追加

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
         
    if st.sidebar.button("🔍 対戦詳細確認", use_container_width=True):
        st.session_state.page = "battle_detail"
        st.rerun()
       
    if st.sidebar.button("👤 プレイヤー検索", use_container_width=True):
        st.session_state.page = "player_search"
        st.rerun()

    st.sidebar.divider()

    st.sidebar.write(f"👤 {st.session_state.user_name} さん")
    if st.sidebar.button("ログアウト"):
        st.session_state.logged_in = False
        st.rerun()

    # 2. メインコンテンツ
    if st.session_state.page == "home":
        st.markdown("### << 宴 >> 基本情報")

        # データの読み込み
        try:
            raw_df = load_data("players")
            
            # ギルドIDが 1 のメンバーだけに絞り込み
            df = raw_df[raw_df['現ギルドID'] == 1][['名前', '流派', '備考']].copy()

            # 1. 流派分布（円グラフ）
            st.markdown("#### 🔮 流派分布")
            # 集計処理（ここも「流派」という名前をそのまま使えます）
            job_counts = df['流派'].value_counts().reset_index()
            job_counts.columns = ['流派', '人数']

            job_counts = job_counts.sort_values(by='人数', ascending=False)

            # グラフと集計表を横並びにする
            col_chart, col_table = st.columns([2, 1]) # 2:1の比率

            with col_chart:
                color_map = {
                    '神相': '#1E90FF', '鉄衣': "#FFA600", '素問': '#FF69B4', 
                    '血河': '#8B0000', '九霊': '#9400D3', '砕夢': '#66DBDB', '龍吟': '#18BE3C'
                }
                fig = px.pie(
                    job_counts, 
                    values='人数', 
                    names='流派', 
                    hole=0.5,
                    color='流派',
                    color_discrete_map=color_map, # 色を固定
                    category_orders={"流派": job_counts['流派'].tolist()} # ★ここが多い順の決め手
                )
        
                # グラフの見た目調整（中央寄せっぽく）
                fig.update_traces(textposition='inside', textinfo='percent+label')
                fig.update_layout(showlegend=False, margin=dict(t=0, b=0, l=0, r=0), height=350)
                
                st.plotly_chart(fig, use_container_width=True)
            with col_table:
                # 右側に集計表を表示
                st.write("【内訳】")
                st.dataframe(job_counts, hide_index=True, use_container_width=True)

            # 2. メンバー名簿（テーブル）を下に配置
            st.markdown("#### 📝 メンバー名簿")
            st.dataframe(df, hide_index=True, use_container_width=True)

        except Exception as e:
            st.error("データの表示に失敗しました。")

    elif st.session_state.page == "score":
        st.markdown("### ⚔️ ギルド戦 戦績データ")
        try:
            # 1. データの読み込みと結合
            score_df = load_data("guild_battle")
            guild_master_df = load_data("guilds")
            p_strat = load_data("battle_player_strategy")
            p_dmg = load_data("battle_player_damage")
            p_heal = load_data("battle_player_heal")
            p_inj = load_data("battle_player_injury")

            # 2. 集計用関数 (自軍 ID=1 と 敵軍 ID!=1 を分けて集計)
            def get_agg_scores(df, cols):
                for c in cols:
                    df[c] = pd.to_numeric(df[c], errors='coerce').fillna(0)
                # 自軍
                mine = df[df['ギルドID'] == 1].groupby('対戦ID')[cols].sum().reset_index()
                mine.columns = ['対戦ID'] + [f'自_{c}' for c in cols]
                # 敵軍
                opp = df[df['ギルドID'] != 1].groupby('対戦ID')[cols].sum().reset_index()
                opp.columns = ['対戦ID'] + [f'敵_{c}' for c in cols]
                return mine, opp

            # 各シートから集計値を取得
            s_mine, s_opp = get_agg_scores(p_strat, ['キル数', 'アシスト数'])
            d_mine, d_opp = get_agg_scores(p_dmg, ['対人与ダメージ', '建築与ダメージ'])
            h_mine, h_opp = get_agg_scores(p_heal, ['回復量'])
            i_mine, i_opp = get_agg_scores(p_inj, ['蘇生'])

            # 3. メイン表と結合
            df = score_df.merge(guild_master_df, left_on='対戦ギルドID', right_on='ギルドID', how='left')
            # すべての集計データを結合
            for add_df in [s_mine, s_opp, d_mine, d_opp, h_mine, h_opp, i_mine, i_opp]:
                df = df.merge(add_df, on='対戦ID', how='left')

            df['日付'] = pd.to_datetime(df['日付'], errors='coerce')

            # --- 絞り込みエリア ---
            with st.expander("🔍 データを絞り込む", expanded=True):
                col_f1, col_f2 = st.columns(2)
                with col_f1:
                    target_guilds = st.multiselect("対戦相手", options=df['ギルド名'].unique())
                    target_results = st.multiselect("勝敗", options=df['結果'].unique())
                with col_f2:
                    morale_filter = st.radio("士気Lvの比較", ["すべて", "自軍が高い", "自軍が低い/同等"], horizontal=True)
                    res_filter = st.radio("戦備資源の比較", ["すべて", "自軍が多い", "自軍が少ない/同等"], horizontal=True)

            filtered_df = df.copy()
            # フィルタ適用ロジック (省略せず維持)
            if target_guilds: filtered_df = filtered_df[filtered_df['ギルド名'].isin(target_guilds)]
            if target_results: filtered_df = filtered_df[filtered_df['結果'].isin(target_results)]
            if morale_filter == "自軍が高い": filtered_df = filtered_df[filtered_df['主ギルド士気Lv'] > filtered_df['対戦ギルド士気Lv']]
            elif morale_filter == "自軍が低い/同等": filtered_df = filtered_df[filtered_df['主ギルド士気Lv'] <= filtered_df['対戦ギルド士気Lv']]
            if res_filter == "自軍が多い": filtered_df = filtered_df[filtered_df['主ギルド戦備資源'] > filtered_df['対戦ギルド戦備資源']]
            elif res_filter == "自軍が少ない/同等": filtered_df = filtered_df[filtered_df['主ギルド戦備資源'] <= filtered_df['対戦ギルド戦備資源']]

            filtered_df = filtered_df.sort_values(by='対戦ID', ascending=False)

            # --- 4. 詳細一覧テーブル (すべての情報を統合) ---
            st.subheader("📋 戦績詳細一覧")
            
            display_cols = [
                '対戦ID', '日付', '結果', 'ギルド名', 
                '主ギルド塔HP', '対戦ギルド塔HP', 
                '主ギルド士気Lv', '対戦ギルド士気Lv', 
                '主ギルド戦備資源', '対戦ギルド戦備資源',
                '自_キル数', '敵_キル数', 
                '自_対人与ダメージ', '敵_対人与ダメージ', 
                '自_建築与ダメージ', '敵_建築与ダメージ',
                '自_回復量', '敵_回復量',
                '自_蘇生', '敵_蘇生'
            ]
            
            st.dataframe(
                filtered_df[display_cols],
                column_config={
                    "日付": st.column_config.DateColumn("日付", format="MM/DD"),
                    "主ギルド塔HP": "自HP", 
                    "対戦ギルド塔HP": "敵HP",
                    "主ギルド士気Lv": "自士気", 
                    "対戦ギルド士気Lv": "敵士気",
                    # 以下の NumberColumn の format に %,d を指定
                    "主ギルド戦備資源": st.column_config.NumberColumn("自戦備", format="%,d"),
                    "対戦ギルド戦備資源": st.column_config.NumberColumn("敵戦備", format="%,d"),
                    "自_キル数": st.column_config.NumberColumn("自K", format="%,d"), 
                    "敵_キル数": st.column_config.NumberColumn("敵K", format="%,d"),
                    "自_対人与ダメージ": st.column_config.NumberColumn("自対人", format="%,d"),
                    "敵_対人与ダメージ": st.column_config.NumberColumn("敵対人", format="%,d"),
                    "自_建築与ダメージ": st.column_config.NumberColumn("自建", format="%,d"),
                    "敵_建築与ダメージ": st.column_config.NumberColumn("敵建", format="%,d"),
                    "自_回復量": st.column_config.NumberColumn("自回復", format="%,d"),
                    "敵_回復量": st.column_config.NumberColumn("敵回復", format="%,d"),
                    "自_蘇生": st.column_config.NumberColumn("自蘇生", format="%,d"),
                    "敵_蘇生": st.column_config.NumberColumn("敵蘇生", format="%,d"),
                },
                hide_index=True, 
                use_container_width=True
            )

            # --- 5. 資源差分のグラフ ---
            if not filtered_df.empty:
                st.subheader("⚔️ 戦備資源の獲得差と勝敗")
                chart_data = filtered_df.copy().dropna(subset=['日付'])
                chart_data['資源差分'] = chart_data['主ギルド戦備資源'] - chart_data['対戦ギルド戦備資源']
                chart_data['表示ラベル'] = chart_data['日付'].dt.strftime('%m/%d') + " " + chart_data['ギルド名'].fillna('不明')
                chart_data = chart_data.sort_values('日付')
                fig = px.bar(chart_data, x='表示ラベル', y='資源差分', color='結果',
                             color_discrete_map={'勝利': '#1f77b4', '失敗': '#ef553b'}, height=400)
                fig.update_layout(legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5),
                                  margin=dict(l=10, r=10, t=30, b=80), xaxis=dict(tickangle=45, title=None))
                fig.add_hline(y=0, line_dash="dash", line_color="gray")
                st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

        except Exception as e:
            st.error(f"データの表示に失敗しました: {e}")
    
    elif st.session_state.page == "player_search":
        st.title("👤 プレイヤー別戦績検索")
        # 各データをマージしてプレイヤー軸の巨大な表を作る
        p_strat = load_data("battle_player_strategy")
        p_dmg = load_data("battle_player_damage")[['対戦ID', 'プレイヤーID', '対人与ダメージ', '建築与ダメージ']]
        p_heal = load_data("battle_player_heal")[['対戦ID', 'プレイヤーID', '回復量']]
        p_inj = load_data("battle_player_injury")[['対戦ID', 'プレイヤーID', '蘇生']]

        merged_p = p_strat.merge(p_dmg, on=['対戦ID', 'プレイヤーID'], how='left')\
                          .merge(p_heal, on=['対戦ID', 'プレイヤーID'], how='left')\
                          .merge(p_inj, on=['対戦ID', 'プレイヤーID'], how='left')

        player_names = merged_p['名前'].unique()
        selected_player = st.selectbox("プレイヤー名を選択", options=player_names)

        if selected_player:
            player_df = merged_p[merged_p['名前'] == selected_player].sort_values('対戦ID', ascending=False)
            
            # メトリクスで通算成績を表示
            c1, c2, c3 = st.columns(3)
            c1.metric("通算キル", int(player_df['キル数'].sum()))
            c2.metric("最大対人ダメ", f"{int(player_df['対人与ダメージ'].max()):,}")
            c3.metric("平均アシスト", round(player_df['アシスト数'].mean(), 1))

            st.dataframe(player_df.drop(columns=['プレイヤーID', 'ギルドID', '名前']), hide_index=True)
    
    elif st.session_state.page == "battle_detail":
        st.title("🔍 対戦詳細リポート")
        try:
            # 1. データの読み込み
            score_df = load_data("guild_battle")
            guild_master_df = load_data("guilds")
            p_strat = load_data("battle_player_strategy")
            p_dmg = load_data("battle_player_damage")
            p_heal = load_data("battle_player_heal")
            p_inj = load_data("battle_player_injury")

            # 2. 選択用ラベルの作成 (日付 + ギルド名) を対戦IDの降順で作成
            score_df['日付'] = pd.to_datetime(score_df['日付'], errors='coerce')
            
            # 対戦IDの降順（新しい順）で並び替え
            score_df = score_df.sort_values('対戦ID', ascending=False)
            
            display_df = score_df.merge(guild_master_df, left_on='対戦ギルドID', right_on='ギルドID', how='left')
            display_df['label'] = display_df['日付'].dt.strftime('%m/%d') + " vs " + display_df['ギルド名'].fillna("不明")
            
            # プルダウンのリスト（並び順を維持したままユニークな値を取得）
            options_labels = display_df['label'].unique().tolist()
            
            target_label = st.selectbox("対戦を選択", options=options_labels)
            # 選択された試合のデータを取得
            match_row = display_df[display_df['label'] == target_label].iloc[0]
            selected_bid = match_row['対戦ID']

            color_map = {
                '神相': '#1E90FF', '鉄衣': "#FFA600", '素問': '#FF69B4', 
                '血河': '#8B0000', '九霊': '#9400D3', '砕夢': '#66DBDB', '龍吟': '#18BE3C'
            }

            if selected_bid:
                # データ結合と数値変換
                p_all = p_strat[p_strat['対戦ID'] == selected_bid].copy()
                d_part = p_dmg[p_dmg['対戦ID'] == selected_bid][['プレイヤーID', '対人与ダメージ', '建築与ダメージ']]
                h_part = p_heal[p_heal['対戦ID'] == selected_bid][['プレイヤーID', '回復量', '被ダメージ']]
                i_part = p_inj[p_inj['対戦ID'] == selected_bid][['プレイヤーID', '重症', '蘇生']]
                
                merged_p = p_all.merge(d_part, on='プレイヤーID', how='left')\
                                .merge(h_part, on='プレイヤーID', how='left')\
                                .merge(i_part, on='プレイヤーID', how='left')
                
                num_cols = ['キル数', 'アシスト数', '対人与ダメージ', '建築与ダメージ', '回復量', '被ダメージ', '重症', '蘇生']
                for col in num_cols:
                    merged_p[col] = pd.to_numeric(merged_p[col], errors='coerce').fillna(0)

                tab1, tab2, tab3, tab4 = st.tabs(["⚔️ 勢力比較", "🔮 流派分析", "🏆 ランキング", "📋 全データ"])

                with tab1:
                    res_color = "#1f77b4" if match_row['結果'] == "勝利" else "#ef553b"
                    st.markdown(f"<h2 style='text-align: center; color: {res_color};'>【 {match_row['結果']} 】</h2>", unsafe_allow_html=True)
                    
                    c1, c2, c3 = st.columns(3)
                    c1.metric("塔HP", f"{match_row['主ギルド塔HP']}", f"相手: {match_row['対戦ギルド塔HP']}", delta_color="off")
                    c2.metric("士気Lv", f"Lv.{match_row['主ギルド士気Lv']}", f"相手: Lv.{match_row['対戦ギルド士気Lv']}", delta_color="off")
                    c3.metric("戦備資源", f"{int(match_row['主ギルド戦備資源']):,}", f"相手: {int(match_row['対戦ギルド戦備資源']):,}", delta_color="off")

                    st.subheader("📊 ギルド合計スタッツ比較")
                    guild_stats = merged_p.groupby('ギルドID')[num_cols].sum().reset_index()
                    guild_stats['勢力'] = guild_stats['ギルドID'].apply(lambda x: '自軍' if x == 1 else '相手')
                    
                    # カンマ区切り設定を追加
                    st.dataframe(
                        guild_stats[['勢力'] + num_cols], 
                        column_config={
                            col: st.column_config.NumberColumn(format="%,d") for col in num_cols
                        },
                        hide_index=True, 
                        use_container_width=True
                    )

                    st.write("項目別比較グラフ")
                    compare_col = st.selectbox("比較する項目", num_cols, key="guild_comp")
                    fig_comp = px.bar(guild_stats, x='勢力', y=compare_col, color='勢力', 
                                      color_discrete_map={'自軍': '#1f77b4', '相手': '#ef553b'}, height=300)
                    st.plotly_chart(fig_comp, use_container_width=True)

                with tab2:
                    st.subheader("🔮 流派別分析 (自軍 vs 相手)")
                    job_agg = merged_p.groupby(['ギルドID', '流派']).agg({'対人与ダメージ':['sum','mean','count']}).reset_index()
                    job_agg.columns = ['ギルドID', '流派', '総ダメ', '平均ダメ', '人数']
                    job_agg['勢力'] = job_agg['ギルドID'].apply(lambda x: '自軍' if x == 1 else '相手')

                    col_left, col_right = st.columns(2)
                    with col_left:
                        st.write("【自軍】")
                        mine_job = job_agg[job_agg['勢力'] == '自軍']
                        st.plotly_chart(px.pie(mine_job, values='人数', names='流派', hole=0.4, color='流派', color_discrete_map=color_map), use_container_width=True)
                        st.dataframe(mine_job[['流派', '人数']].sort_values('人数', ascending=False), hide_index=True, use_container_width=True)
                    with col_right:
                        st.write("【相手】")
                        opp_job = job_agg[job_agg['勢力'] == '相手']
                        st.plotly_chart(px.pie(opp_job, values='人数', names='流派', hole=0.4, color='流派', color_discrete_map=color_map), use_container_width=True)
                        st.dataframe(opp_job[['流派', '人数']].sort_values('人数', ascending=False), hide_index=True, use_container_width=True)

                    st.write("1人あたり平均ダメージの比較")
                    fig_avg = px.bar(job_agg, x='平均ダメ', y='流派', orientation='h', color='勢力', barmode='group', 
                                     color_discrete_map={'自軍': '#1f77b4', '相手': '#ef553b'})
                    st.plotly_chart(fig_avg, use_container_width=True)

                with tab3:
                    st.subheader("🏆 プレイヤーランキング (Top 20)")
                    rank_item = st.selectbox("ランキング項目", num_cols, key="rank_select")
                    
                    for side, g_id in [("自軍", 1), ("相手", 2)]:
                        st.write(f"【{side}】")
                        side_df = merged_p[merged_p['ギルドID'] == g_id] if side=="自軍" else merged_p[merged_p['ギルドID'] != 1]
                        top20 = side_df.sort_values(rank_item, ascending=False).head(20)
                        
                        fig = px.bar(top20, x=rank_item, y='名前', orientation='h', color='流派', color_discrete_map=color_map, height=700)
                        fig.update_layout(yaxis={'categoryorder': 'total ascending', 'title': None}, xaxis_title=rank_item)
                        st.plotly_chart(fig, use_container_width=True)

                with tab4:
                    st.subheader("👥 全プレイヤーデータ詳細")
                    final_df = merged_p.merge(guild_master_df, left_on='ギルドID', right_on='ギルドID', how='left')
                    final_df['ギルド名'] = final_df['ギルド名'].fillna("<< 宴 >>")
                    display_final = final_df.drop(columns=['ID', '対戦ID', 'プレイヤーID', 'ギルドID'])
                    
                    st.dataframe(
                        display_final[['ギルド名', '名前', '流派', 'レベル'] + num_cols].sort_values(['ギルド名', '対人与ダメージ'], ascending=[True, False]),
                        column_config={col: st.column_config.NumberColumn(format="%,d") for col in num_cols},
                        hide_index=True, use_container_width=True
                    )

        except Exception as e:
            st.error(f"エラーが発生しました: {e}")