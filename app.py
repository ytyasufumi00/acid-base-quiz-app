import streamlit as st
import random
import requests
import pandas as pd

# 発行したGASのURL（連携済み）
GAS_URL = "https://script.google.com/macros/s/AKfycbyCSJ8P3-0HoBHWL-KzdF8DnV21ArXCeNa8j93Apx5lokKu6RpHDKYl0aetvgdOVAQ-1g/exec"

# --- 症例生成ロジック ---
def generate_case():
    disorders = ["代謝性アシドーシス", "代謝性アルカローシス", "呼吸性アシドーシス", "呼吸性アルカローシス"]
    primary = random.choice(disorders)

    # 臨床的にあり得る数値をWinterの式などをベースに生成（急性代償を想定）
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

# --- 通信用の関数 ---
def save_score(name, score, rank):
    data = {"name": name, "score": score, "rank": rank}
    requests.post(GAS_URL, json=data)

def load_ranking():
    response = requests.get(GAS_URL)
    return response.json()

# --- Streamlit UI ---
st.set_page_config(page_title="酸塩基平衡アタック", page_icon="⚔️")

# セッションステート初期化
if 'score' not in st.session_state: st.session_state.score = 0
if 'current_case' not in st.session_state: st.session_state.current_case = generate_case()
if 'feedback' not in st.session_state: st.session_state.feedback = ""
if 'player_name' not in st.session_state: st.session_state.player_name = "名無し"

st.title("電解質・酸塩基平衡 タイムアタック ⚔️")

# サイドバーにランキングを表示
st.sidebar.header("🏆 歴代トップランカー")
try:
    ranking_data = load_ranking()
    if ranking_data:
        df = pd.DataFrame(ranking_data)
        df.index = df.index + 1 # 順位を1からスタート
        st.sidebar.dataframe(df[['name', 'score', 'rank']])
except:
    st.sidebar.write("ランキング読み込み中...")

# --- プレイヤー名入力 ---
st.session_state.player_name = st.text_input("あなたの名前（武将名）を入力して出陣！", st.session_state.player_name)

st.markdown("---")

# 階級判定
ranks = [(0, "足軽"), (3, "侍大将"), (7, "家老"), (10, "真田家臣"), (15, "上田城主（指導医級）")]
current_rank = "足軽"
for threshold, rank in ranks:
    if st.session_state.score >= threshold:
        current_rank = rank

col1, col2 = st.columns(2)
col1.metric("現在のスコア", st.session_state.score)
col2.metric("現在の階級", current_rank)

st.write(st.session_state.feedback)

# 問題表示
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
        else:
            st.session_state.feedback = f"❌ 無念…！正解は「{case['answer']}」でした。"
            
            # --- 📌 ここでスコアを保存！ ---
            if st.session_state.score > 0:
                save_score(st.session_state.player_name, st.session_state.score, current_rank)
                st.session_state.feedback += f"\n\n（スコア {st.session_state.score} で記録されました）"
            
            st.session_state.score = 0 # リセット
        
        st.session_state.current_case = generate_case()
        st.rerun()
