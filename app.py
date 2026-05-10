import streamlit as st
import random
import requests
import pandas as pd
import threading

# 発行したGASのURL
GAS_URL = "https://script.google.com/macros/s/AKfycbyItu-Z6pmfnN-UUFME3I_YFv7rfujWFhI2oEsqFAW5CTu6AU7iZZuLEM7bBDRay5jU/exec"

# --- 症例生成ロジック ---
def generate_case():
    disorders = ["代謝性アシドーシス", "代謝性アルカローシス", "呼吸性アシドーシス", "呼吸性アルカローシス"]
    primary = random.choice(disorders)

    if primary == "代謝性アシドーシス":
        hco3 = random.randint(10, 20)
        paco2 = int(1.5 * hco3 + 8 + random.randint(-2, 2))
        ph = 7.40 - (24 - hco3) * 0.015 - random.uniform(0, 0.05)
    elif primary == "代謝性アルカローシス":
        hco3 = random.randint(28, 40)
        paco2 = 40 + int(0.7 * (hco3 - 24) + random.randint(-2, 2))
        ph = 7.40 + (hco3 - 24) * 0.015 + random.uniform(0, 0.05)
    elif primary == "呼吸性アシドーシス":
        paco2 = random.randint(50, 70)
        hco3 = 24 + int(0.1 * (paco2 - 40) + random.randint(-1, 1))
        ph = 7.40 - (paco2 - 40) * 0.008 - random.uniform(0, 0.02)
    elif primary == "呼吸性アルカローシス":
        paco2 = random.randint(20, 35)
        hco3 = 24 - int(0.2 * (40 - paco2) + random.randint(-1, 1))
        ph = 7.40 + (40 - paco2) * 0.008 + random.uniform(0, 0.02)

    return {"pH": round(ph, 2), "PaCO2": paco2, "HCO3": hco3, "answer": primary}

# --- 通信用の関数（爆速化） ---
def save_score(name, score, rank):
    def _send_data():
        try:
            data = {"name": name, "score": score, "rank": rank}
            requests.post(GAS_URL, json=data)
            # 送信完了後、即座にキャッシュをクリアして最新を読み込めるようにする
            load_ranking.clear() 
        except:
            pass
    thread = threading.Thread(target=_send_data)
    thread.start()

@st.cache_data(ttl=60) # 60秒間はデータを使い回して爆速表示
def load_ranking():
    try:
        response = requests.get(GAS_URL)
        return response.json()
    except:
        return []

# --- Streamlit UI ---
st.set_page_config(page_title="酸塩基平衡アタック", page_icon="⚔️")

# ブラウザの自動翻訳を無効化する設定
st.markdown(
    """
    <style>
        /* ページ全体を翻訳対象外に設定 */
    </style>
    <script>
        // HTMLのlang属性を固定し、翻訳のトリガーを抑制
        document.documentElement.lang = 'ja';
    </script>
    <meta name="google" content="notranslate">
    """,
    unsafe_allow_html=True
)

# セッションステート初期化
if 'score' not in st.session_state: st.session_state.score = 0
if 'question_count' not in st.session_state: st.session_state.question_count = 1
if 'current_case' not in st.session_state: st.session_state.current_case = generate_case()
if 'feedback' not in st.session_state: st.session_state.feedback = ""
if 'is_game_over' not in st.session_state: st.session_state.is_game_over = False
if 'last_score' not in st.session_state: st.session_state.last_score = 0
if 'last_rank' not in st.session_state: st.session_state.last_rank = ""
if 'player_name' not in st.session_state: st.session_state.player_name = "名無し"

st.title("信州上田　酸塩基合戦　⚔️")

# --- サイドバー（ランキング） ---
st.sidebar.header("🏆 歴代トップランカー")
try:
    ranking_data = load_ranking()
    if ranking_data:
        df = pd.DataFrame(ranking_data)
        df.index = df.index + 1 
        st.sidebar.dataframe(df[['name', 'score', 'rank']])
except:
    st.sidebar.write("ランキング読み込み中...")

st.session_state.player_name = st.text_input("あなたの名前（武将名）を入力して出陣！", st.session_state.player_name)
st.markdown("---")

# --- キャラクター絵文字付き階級リスト（全40段階の代表例） ---
rank_data = [
    ("農民", "🌾"), ("迷子の足軽", "🏃‍♂️"), ("いけてる足軽", "✨"), ("槍の又左のパシリ", "👣"), ("運のいい足軽頭", "🍀"),
    ("影武者の影武者", "👥"), ("疾風の忍び", "🥷"), ("闇夜の暗殺者", "🗡️"), ("独眼竜の右目", "👁️"), ("傾奇者", "👘"),
    ("六文銭の旗持ち", "🚩"), ("信濃の荒武者", "🐻"), ("川中島からの生還者", "🌊"), ("赤備えの先鋒", "🔴"), ("表裏比興の弟子", "🦊"),
    ("上田城の門番", "🏯"), ("真田十勇士", "🏹"), ("真田信之級", "🛡️"), ("鬼神の如き猛将", "👹"), ("越後の龍の鱗", "🐉"),
    ("剣聖", "⚔️"), ("東国無双", "🥇"), ("天下布武の右腕", "✋"), ("日ノ本一の兵", "🏮"), ("覇王の軍師", "🧠"),
    ("関白", "👔"), ("征夷大将軍", "🏇"), ("東照大権現", "🌅"), ("漆黒の堕天使", "🖤"), ("輪廻転生せし修羅", "🌀"),
    ("時空を統べる太閤", "⏳"), ("森羅万象の理", "🌍"), ("神の領域", "⚡"), ("概念", "👻"), ("創造主", "👁‍🗨")
]

# --- 後半ほど上がりづらいレベル計算ロジック（前回のまま） ---
def calculate_level(score):
    if score <= 40: level = score // 2
    elif score <= 130: level = 20 + (score - 40) // 3
    elif score <= 290: level = 50 + (score - 130) // 4
    else: level = 90 + (score - 290) // 5
    return min(level, 100)

current_lv = calculate_level(st.session_state.score)

# 階級名と絵文字の決定
if current_lv < len(rank_data):
    current_rank, character = rank_data[current_lv]
elif current_lv < 100:
    current_rank, character = f"伝説の英雄", "👑"
else:
    current_rank, character = "創造主", "🌌"

# --- UI表示部分 ---
col1, col2, col3 = st.columns(3)
col1.metric("現在の試練", f"第 {st.session_state.question_count} 問")
col2.metric("現在のスコア", st.session_state.score)
# 階級の横にキャラクターを表示！
col3.metric("現在の階級", f"{character} Lv.{current_lv}")

st.subheader(f"称号：{current_rank}")


# --- 派手なゲームオーバー画面 ---
if st.session_state.is_game_over:
    st.error("💀 **無念、討死...！！** 正解は「" + st.session_state.current_case['answer'] + "」でした。")
    
    # HTMLを使ってド派手な戦績カードを作成
    st.markdown(f"""
    <div style='text-align: center; border: 3px solid #ff4b4b; padding: 20px; border-radius: 10px; background-color: #330000; color: white;'>
        <h2 style='color: #ff4b4b;'>⚔️ 戦績報告 ⚔️</h2>
        <p style='font-size: 20px;'><b>{st.session_state.player_name}</b> 殿</p>
        <h1>最終スコア： {st.session_state.last_score}</h1>
        <h2 style='color: gold;'>最終階級：【 {st.session_state.last_rank} 】</h2>
        <p>ランキングに記録されました！次の出陣をお待ちしております。</p>
    </div>
    """, unsafe_allow_html=True)
    
    # 10点以上（六文銭の旗持ち以上）なら風船でお祝い
    if st.session_state.last_score >= 10:
        st.balloons()
    
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("🔄 新たな戦（ゲーム）を始める", use_container_width=True, type="primary"):
        st.session_state.is_game_over = False
        st.session_state.current_case = generate_case()
        st.rerun()
    
    st.stop() # ここで止めて下の問題を表示させない

# --- ステータス表示 ---
col1, col2, col3 = st.columns(3)
col1.metric("現在の試練", f"第 {st.session_state.question_count} 問")
col2.metric("現在のスコア", st.session_state.score)
col3.metric("現在の階級", current_rank)

# 階級アップのプログレスバー
st.progress((st.session_state.score % 2) / 2, text=f"次の階級まで... {'あと1問！' if (st.session_state.score % 2) != 0 else '出陣中'}")

if st.session_state.feedback:
    st.success(st.session_state.feedback)

# --- 問題表示 ---
case = st.session_state.current_case
st.info(f"**【患者データ】**\n\n**pH**: {case['pH']}　|　**PaCO2**: {case['PaCO2']} mmHg　|　**HCO3-**: {case['HCO3']} mEq/L")
st.write("最も疑われる一次性の酸塩基平衡異常はどれですか？")

options = ["代謝性アシドーシス", "代謝性アルカローシス", "呼吸性アシドーシス", "呼吸性アルカローシス"]
cols = st.columns(2)

for i, option in enumerate(options):
    if cols[i % 2].button(option, use_container_width=True):
        if option == case["answer"]:
            st.session_state.feedback = f"✅ 見事！正解です（{option}）。"
            st.session_state.score += 1
            st.session_state.question_count += 1
            st.session_state.current_case = generate_case()
        else:
            # 討死処理
            st.session_state.feedback = "" 
            st.session_state.last_score = st.session_state.score
            st.session_state.last_rank = current_rank
            
            if st.session_state.score > 0:
                save_score(st.session_state.player_name, st.session_state.score, current_rank)
            
            # リセット
            st.session_state.score = 0
            st.session_state.question_count = 1
            st.session_state.is_game_over = True
            
        st.rerun()
