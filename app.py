import streamlit as st

st.set_page_config(
    page_title="信州上田医療ゲームズ",
    page_icon="🏯",
    initial_sidebar_state="collapsed" # 👈 最初から左メニューを閉じておく設定
)

st.title("🏯 信州上田医療ゲームズ 総合陣地")
st.markdown("---")

st.write("ようこそ！ここは医療従事者向けの学習ゲームポータルです。")
st.write("下のリンクをクリックして、プレイしたい戦（ゲーム）へ出陣してください！")

st.markdown("<br>", unsafe_allow_html=True)
st.markdown("### 🎮 現在遊べるゲーム")

# 👇 中央画面から直接ゲームへ飛ぶ魔法のリンクボタン
st.page_link("pages/1_酸塩基合戦.py", label="第1弾：酸塩基合戦 に出陣する！", icon="⚔️")

st.markdown("<br><br><br>", unsafe_allow_html=True)
st.markdown("---")
st.write("（※ 今後、新しいゲームが続々と追加される予定です...！）")

# --- おまけ：左のサイドバーを完全に消し去るCSS（よりポータルサイトっぽくなります） ---
st.markdown(
    """
    <style>
        /* 左のサイドバーを非表示にする */
        [data-testid="stSidebar"] {
            display: none;
        }
        /* 左上のサイドバーを開く「＞」ボタンも非表示にする */
        [data-testid="collapsedControl"] {
            display: none;
        }
    </style>
    """,
    unsafe_allow_html=True
)