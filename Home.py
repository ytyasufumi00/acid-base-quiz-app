import streamlit as st

# 表紙のページ設定
st.set_page_config(page_title="信州上田 医療ツールポータル", page_icon="🏥")

st.title("🏥 信州上田 医療アプリ総合ポータル")

st.markdown("""
ここは臨床現場で役立つシミュレーターや、学習用のゲームをまとめたポータルサイトです。

### 👇 以下のメニューからアプリを選んで出陣してください！
""")

# 💡 st.page_link を使って、画面中央にクリックできるリンクを作ります
st.page_link("pages/1_酸塩基合戦.py", label="⚔️ 酸塩基合戦（RPG風学習ツール）", icon="▶️")

st.markdown("---")
st.markdown("### 🚧 今後追加予定のツール")
st.markdown("* **💧 シミュレーター**：（※次回作の予定！）")
st.markdown("* **🩺 予測システム**：（※絶賛開発中！）")

st.info("💡 サイドバーのメニューからでも各ページへ移動できます。")