import streamlit as st
import random
import requests
import pandas as pd
import threading
import time  

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
@st.cache_data(ttl=60)
def load_ranking():
    try:
        response = requests.get(GAS_URL)
        return response.json()
    except:
        return []

# --- ここ（54行目付近）に追加 ---
def handle_answer(user_selection, current_rank):
    case = st.session_state.current_case
    if user_selection == case["answer"]:
        st.session_state.feedback = f"✅ 見事！正解です（{user_selection}）。"
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
    ("農民", "🌾"), ("迷子の足軽", "🏃‍♂️"), ("いけてる足軽", "✨"), ("槍の又左のパシリ", "👣"), ("運のいい足軽頭", "🍀"),("当直明けのゾンビ", "🧟"),
    ("影武者の影武者", "👥"), ("疾風の忍び", "🥷"), ("闇夜の暗殺者", "🗡️"), ("独眼竜の右目", "👁️"), ("傾奇者", "👘"),
    ("六文銭の旗持ち", "🚩"), ("信濃の荒武者", "🐻"), ("川中島からの生還者", "🌊"), ("赤備えの先鋒", "🔴"), ("血ガス侍", "🦊"),
    ("上田城の門番", "🏯"), ("pH7.40の番人", "⚖️"),("真田十勇士", "🏹"),("戸石城の攻略者", "⛰️"), ("長野県の守護神", "🛡️"),("J-OSLERの覇者", "📝"), ("鬼神の如き猛将", "👹"), ("越後の龍の鱗", "🐉"),
    ("剣聖", "⚔️"), ("東国無双", "🥇"), ("天下布武まであと一歩", "✋"), ("真田幸村級", "🏮"), ("諸葛孔明級", "🧠"),
    ("病院内の関白", "👔"), ("征夷大将軍", "🏇"), ("東照大権現", "🌅"), ("不可逆的アシデミア", "🔥"),("漆黒の堕天使", "🖤"), ("輪廻転生せし修羅", "🌀"),
    ("時空を統べる太閤", "⏳"), ("森羅万象の理", "🌍"), ("宇宙の理を解き明かす者", "💫"),("血gasグランドマスター", "⚡"), ("酸塩基を司る者", "👻"), ("創造主", "👁‍🗨")
]
# --- 後半ほど上がりづらいレベル計算ロジック（前回のまま） ---
def calculate_level(score):
    if score <= 40: level = score // 2
    elif score <= 70: level = 20 + (score - 40) // 3
    elif score <= 90: level = 30 + (score - 70) // 4
    else: level = 35 + (score - 90) // 5
    return min(level, 100)

current_lv = calculate_level(st.session_state.score)

# 階級名と絵文字の決定
if current_lv < len(rank_data):
    current_rank, character = rank_data[current_lv]
elif current_lv < 100:
    current_rank, character = f"☆創造主☆", "👑"
else:
    current_rank, character = "創造主", "🌌"

# --- UI表示部分 ---
col1, col2, col3 = st.columns(3)
col1.metric("現在の試練", f"第 {st.session_state.question_count} 問")
col2.metric("現在のスコア", st.session_state.score)
# 階級の横にキャラクターを表示！
col3.metric("現在の階級", f"{character} Lv.{current_lv}")

st.subheader(f"称号：{current_rank}")

# --- 派手なゲームオーバー画面（振り返り機能付き） ---
if st.session_state.is_game_over:
    failed_case = st.session_state.current_case # 討死した時のデータを保持
    
    st.error("💀 **無念、討死...！！**")
    
    # 【追加】問題の振り返りエリア
    st.markdown(f"""
        <div style="background-color: #4d0000; padding: 15px; border-radius: 10px; border: 1px solid #ff4b4b; margin-bottom: 20px; color: white;">
            <p style="margin: 0; color: #ffbcbc; font-size: 0.8rem;">【討死した問題のデータ】</p>
            <p style="font-size: 1.1rem; font-weight: bold; margin: 5px 0;">
                pH: {failed_case['pH']} | PaCO2: {failed_case['PaCO2']} mmHg | HCO3-: {failed_case['HCO3']} mEq/L
            </p>
            <div style="margin-top: 10px; padding-top: 10px; border-top: 1px solid #662222;">
                <span style="font-size: 0.9rem;">正答：</span>
                <span style="font-size: 1.2rem; font-weight: bold; color: #00ff00;">{failed_case['answer']}</span>
            </div>
        </div>
    """, unsafe_allow_html=True)
    
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
    
    if st.session_state.last_score >= 10:
        st.balloons()
    
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("🔄 新たな戦（ゲーム）を始める", use_container_width=True, type="primary"):
        st.session_state.is_game_over = False
        st.session_state.current_case = generate_case()
        st.rerun()
    
    st.stop()


# --- ステータス表示（1行に集約） ---
st.markdown(f"""
    <div style="display: flex; justify-content: space-between; align-items: center; padding: 10px; background: #262730; border-radius: 10px; margin-bottom: 20px; color: white;">
        <div style="text-align: center; flex: 1;">
            <div style="font-size: 0.7rem; color: #888;">試練</div>
            <div style="font-size: 1.1rem; font-weight: bold;">第 {st.session_state.question_count} 問</div>
        </div>
        <div style="text-align: center; flex: 1; border-left: 1px solid #444; border-right: 1px solid #444;">
            <div style="font-size: 0.7rem; color: #888;">レベル</div>
            <div style="font-size: 1.1rem; font-weight: bold; color: #ff4b4b;">Lv.{current_lv}</div>
        </div>
        <div style="text-align: center; flex: 2;">
            <div style="font-size: 1.8rem;">{character}</div>
            <div style="font-size: 0.9rem; font-weight: bold;">{current_rank}</div>
        </div>
    </div>
""", unsafe_allow_html=True)


# --- 進行状況バー（レベルアップ条件に完全同期） ---
# 1. 前回のレベルを記憶しておくための準備
if 'last_rendered_lv' not in st.session_state:
    st.session_state.last_rendered_lv = current_lv

# 2. レベルアップしたかどうかの判定（今のレベルが前回より高ければON）
just_leveled_up = current_lv > st.session_state.last_rendered_lv
st.session_state.last_rendered_lv = current_lv  # 次回のために記憶を更新
score = st.session_state.score
if score < 40:
    # Lv20までは2問でレベルアップ (50%ずつ)
    progress_val = (score % 2) / 2.0
elif score < 70:
    # Lv21〜50は3問でレベルアップ (33%ずつ)
    progress_val = ((score - 70) % 3) / 3.0
elif score < 90:
    # Lv51〜90は4問でレベルアップ (25%ずつ)
    progress_val = ((score - 90) % 4) / 4.0
elif score < 115:
    # Lv91〜100は5問でレベルアップ (20%ずつ)
    progress_val = ((score - 115) % 5) / 5.0
else:
    # 創造主（Lv100）到達時は常にMAX
    progress_val = 1.0

# 4. バーを描画するための「専用の枠」を作る
bar_placeholder = st.empty()

# 5. 【ここが魔法！】レベルアップした瞬間だけ、一瞬100%を表示して時間を止める
if just_leveled_up:
    bar_placeholder.progress(1.0, text="✨ 見事！階級昇格！！ ✨")
    time.sleep(0.8)  # 0.8秒間だけプレイヤーに100%のドヤ顔バーを見せつける

# 6. その後、通常のバー（0%や現在の状態）で上書きしてゲームを再開
if progress_val == 1.0:
    bar_text = "🌌 創造主到達！あなたは神です 🌌"
else:
    bar_text = f"次の階級まで... {'新たなる試練へ' if progress_val == 0.0 else '出陣中！'}"

bar_placeholder.progress(progress_val, text=bar_text)
# ==========================================


# --- 問題（患者データ）表示 ---
case = st.session_state.current_case

# 1. 単位を追加
st.info(f"**pH**: {case['pH']} | **PaCO2**: {case['PaCO2']} mmHg | **HCO3-**: {case['HCO3']} mEq/L")

# 2. 問題文を追加
st.write("最も疑われる一次性の酸塩基平衡異常はどれですか？")


# --- 視覚的な回答ボタン ---
col_a, col_b = st.columns(2)

with col_a:
    st.write("🟦 **アシドーシス系**")
    if st.button("💦 代謝性アシドーシス", use_container_width=True):
        handle_answer("代謝性アシドーシス", current_rank)
    if st.button("🌬️ 呼吸性アシドーシス", use_container_width=True):
        handle_answer("呼吸性アシドーシス", current_rank)

with col_b:
    st.write("🟥 **アルカローシス系**")
    if st.button("🔥 代謝性アルカローシス", use_container_width=True):
        handle_answer("代謝性アルカローシス", current_rank)
    if st.button("☁️ 呼吸性アルカローシス", use_container_width=True):
        handle_answer("呼吸性アルカローシス", current_rank)
