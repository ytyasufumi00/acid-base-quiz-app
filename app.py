import streamlit as st
import random
import requests
import pandas as pd
import threading
import time
import math  

# 発行したGASのURL
GAS_URL = "https://script.google.com/macros/s/AKfycbyItu-Z6pmfnN-UUFME3I_YFv7rfujWFhI2oEsqFAW5CTu6AU7iZZuLEM7bBDRay5jU/exec"

# --- 症例生成ロジック（雑魚敵用） ---
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

    return {"pH": round(ph, 2), "PaCO2": paco2, "HCO3": hco3, "answer": primary, "is_boss": False}

# --- 症例生成ロジック（ボス戦・混合性異常用） ---
def generate_boss_case():
    boss_patterns = [
        "MetAc_RespAc", "MetAc_RespAlk", 
        "RespAc_MetAc", "RespAc_MetAlk",
        "MetAlk_RespAlk", "MetAlk_RespAc",
        "RespAlk_MetAlk", "RespAlk_MetAc"
    ]
    
    while True: 
        pattern = random.choice(boss_patterns)

        if pattern == "MetAc_RespAc":
            primary = "代謝性アシドーシス"
            answer = "呼吸性アシドーシス"
            hco3 = random.randint(10, 18)
            expected_paco2 = 1.5 * hco3 + 8
            paco2 = int(expected_paco2 + random.randint(6, 12))
        elif pattern == "MetAc_RespAlk":
            primary = "代謝性アシドーシス"
            answer = "呼吸性アルカローシス"
            hco3 = random.randint(10, 18)
            expected_paco2 = 1.5 * hco3 + 8
            paco2 = int(expected_paco2 - random.randint(4, 8))
        elif pattern == "RespAc_MetAc":
            primary = "呼吸性アシドーシス"
            answer = "代謝性アシドーシス"
            paco2 = random.randint(50, 70)
            expected_hco3 = 24 + 0.1 * (paco2 - 40)
            hco3 = int(expected_hco3 - random.randint(4, 8))
        elif pattern == "RespAc_MetAlk":
            primary = "呼吸性アシドーシス"
            answer = "代謝性アルカローシス"
            paco2 = random.randint(50, 70)
            expected_hco3 = 24 + 0.1 * (paco2 - 40)
            hco3 = int(expected_hco3 + random.randint(6, 12))
        elif pattern == "MetAlk_RespAlk":
            primary = "代謝性アルカローシス"
            answer = "呼吸性アルカローシス"
            hco3 = random.randint(30, 40)
            expected_paco2 = 40 + 0.7 * (hco3 - 24)
            paco2 = int(expected_paco2 - random.randint(6, 12))
        elif pattern == "MetAlk_RespAc":
            primary = "代謝性アルカローシス"
            answer = "呼吸性アシドーシス"
            hco3 = random.randint(30, 40)
            expected_paco2 = 40 + 0.7 * (hco3 - 24)
            paco2 = int(expected_paco2 + random.randint(4, 8))
        elif pattern == "RespAlk_MetAlk":
            primary = "呼吸性アルカローシス"
            answer = "代謝性アルカローシス"
            paco2 = random.randint(20, 30)
            expected_hco3 = 24 - 0.2 * (40 - paco2)
            hco3 = int(expected_hco3 + random.randint(4, 8))
        elif pattern == "RespAlk_MetAc":
            primary = "呼吸性アルカローシス"
            answer = "代謝性アシドーシス"
            paco2 = random.randint(20, 30)
            expected_hco3 = 24 - 0.2 * (40 - paco2)
            hco3 = int(expected_hco3 - random.randint(4, 8))

        ph = 6.1 + math.log10(hco3 / (0.03 * paco2))
        ph = round(ph, 2)
        
        if "アシドーシス" in primary and ph < 7.40: break
        if "アルカローシス" in primary and ph > 7.40: break

    return {"pH": ph, "PaCO2": paco2, "HCO3": hco3, "answer": answer, "primary": primary, "is_boss": True}

# --- 通信用の関数 ---
def save_score(name, score, rank):
    def _send_data():
        try:
            data = {"name": name, "score": score, "rank": rank}
            requests.post(GAS_URL, json=data)
            load_ranking.clear() 
        except:
            pass
    thread = threading.Thread(target=_send_data)
    thread.start()

@st.cache_data(ttl=60)
def load_ranking():
    try:
        response = requests.get(GAS_URL)
        return response.json()
    except:
        return []

# --- 回答判定ロジック ---
def handle_answer(user_selection, current_rank):
    case = st.session_state.current_case
    if user_selection == case["answer"]:
        st.session_state.feedback = f"✅ 見事！正解です（{user_selection}）。"
        st.session_state.score += 1
        st.session_state.question_count += 1
        st.session_state.just_correct = True # 討伐エフェクトの目印
        
        if st.session_state.question_count % 10 == 0:
            st.session_state.current_case = generate_boss_case()
        else:
            st.session_state.current_case = generate_case()
    else:
        st.session_state.feedback = "" 
        st.session_state.last_score = st.session_state.score
        st.session_state.last_rank = current_rank
        
        if st.session_state.score > 0:
            save_score(st.session_state.player_name, st.session_state.score, current_rank)
        
        st.session_state.score = 0
        st.session_state.question_count = 1
        st.session_state.is_game_over = True
    
    st.rerun()

# --- Streamlit UI設定 ---
st.set_page_config(page_title="酸塩基平衡アタック", page_icon="⚔️")

# 👇 ★追加：【超強力版】翻訳ポップアップ完全撃退スクリプト
import streamlit.components.v1 as components
components.html(
    """
    <script>
        // Streamlitの親枠（一番外側のHTML）を直接操作する
        const parentDoc = window.parent.document;
        
        // 1. 言語を強制的に日本語に書き換え
        parentDoc.documentElement.lang = 'ja';
        
        // 2. ページ全体に「翻訳ツール絶対禁止（notranslate）」の呪文を付与
        parentDoc.documentElement.classList.add('notranslate');
        parentDoc.body.classList.add('notranslate');
        
        // 3. metaタグもhead領域の最上部に強制的にねじ込む
        if (!parentDoc.querySelector('meta[name="google"]')) {
            let meta = parentDoc.createElement('meta');
            meta.name = "google";
            meta.content = "notranslate";
            parentDoc.head.appendChild(meta);
        }
    </script>
    """,
    height=0, width=0
)

# 💡 UIデザイン（CSSのみにスッキリ整理しました）
st.markdown(
    """
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Shippori+Mincho:wght@500;800&display=swap');

        .stApp {
            background-color: #f0f7e6; 
            background-image:
                linear-gradient(45deg, #e2eed2 25%, transparent 25%, transparent 75%, #e2eed2 75%, #e2eed2),
                linear-gradient(45deg, #e2eed2 25%, transparent 25%, transparent 75%, #e2eed2 75%, #e2eed2);
            background-size: 60px 60px; 
            background-position: 0 0, 30px 30px;
        }

        .block-container {
            background-color: rgba(255, 255, 255, 0.95); 
            padding: 3rem !important; 
            border-radius: 15px; 
            box-shadow: 0 4px 15px rgba(0,0,0,0.1); 
            margin-top: 20px;
        }

        h1 {
            font-family: 'Shippori Mincho', serif !important;
            color: #4a5d23 !important; 
            text-align: center;
        }
        h2, h3 {
            font-family: 'Shippori Mincho', serif !important;
        }

        p, label {
            color: #2c3e50 !important; 
        }
        header {
            background-color: transparent !important;
        }
    </style>
    """,
    unsafe_allow_html=True
)

if 'score' not in st.session_state: st.session_state.score = 0
if 'question_count' not in st.session_state: st.session_state.question_count = 1
if 'current_case' not in st.session_state: st.session_state.current_case = generate_case()
if 'feedback' not in st.session_state: st.session_state.feedback = ""
if 'is_game_over' not in st.session_state: st.session_state.is_game_over = False
if 'last_score' not in st.session_state: st.session_state.last_score = 0
if 'last_rank' not in st.session_state: st.session_state.last_rank = ""
if 'player_name' not in st.session_state: st.session_state.player_name = "名無し"

st.title("信州上田　酸塩基合戦　⚔️")

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

rank_data = [
    ("農民", "🌾"), ("迷子の足軽", "🏃‍♂️"), ("いけてる足軽", "✨"), ("槍の又左のパシリ", "👣"), ("運のいい足軽頭", "🍀"),("当直明けのゾンビ", "🧟"),
    ("影武者の影武者", "👥"), ("疾風の忍び", "🥷"), ("闇夜の暗殺者", "🗡️"), ("独眼竜の右目", "👁️"), ("傾奇者", "👘"),
    ("六文銭の旗持ち", "🚩"), ("信濃の荒武者", "🐻"), ("川中島からの生還者", "🌊"), ("赤備えの先鋒", "🔴"), ("血ガス侍", "🤺"),
    ("上田城の門番", "🏯"), ("pH7.40の番人", "⚖️"),("真田十勇士", "🏹"),("戸石城の攻略者", "⛰️"), ("長野県の守護神", "🛡️"),("J-OSLERの覇者", "👨‍⚕️"), ("鬼神の如き猛将", "👹"), ("越後の龍の鱗", "🐉"),
    ("剣聖", "⚔️"), ("東国無双", "🥇"), ("天下布武まであと一歩", "✋"), ("真田幸村級", "🏮"), ("諸葛孔明級", "🧠"),
    ("病院内の関白", "👔"), ("征夷大将軍", "🏇"), ("東照大権現", "🌅"), ("ヒト型対アシデミア兵器", "🤖"),("漆黒の堕天使", "🖤"), ("輪廻転生せし修羅", "🌀"),
    ("時空を統べる太閤", "⏳"), ("地球", "🌍"), ("宇宙の理を解き明かす者", "💫"),("血gasグランドマスター", "⚡"), ("酸塩基を司る者", "👻"), ("創造主", "👁‍🗨")
]

def calculate_level(score):
    if score <= 40: return score // 2
    elif score <= 70: return 20 + (score - 40) // 3
    elif score <= 90: return 30 + (score - 70) // 4
    else: return min(35 + (score - 90) // 5, 100)

# --- ゲームオーバー画面 ---
if st.session_state.is_game_over:
    failed_case = st.session_state.current_case
    st.error("💀 **無念、討死...！！**")
    
    # 💡 <p>タグをすべて<div>タグに変更して、スマホ用CSSの呪縛を完全に回避！
    st.markdown(f"""
        <div style="background-color: #4d0000; padding: 15px; border-radius: 10px; border: 1px solid #ff4b4b; margin-bottom: 20px; color: white;">
            <div style="margin: 0; color: #ffdddd; font-size: 0.9rem; font-weight: bold;">【討死した問題のデータ】</div>
            <div style="font-size: 1.2rem; font-weight: bold; margin: 5px 0; color: #ffffff;">
                pH: {failed_case['pH']} | PaCO2: {failed_case['PaCO2']} mmHg | HCO3-: {failed_case['HCO3']} mEq/L
            </div>
            <div style="margin-top: 10px; padding-top: 10px; border-top: 1px solid #662222;">
                <span style="font-size: 1rem; color: #ffffff;">正答：</span>
                <span style="font-size: 1.3rem; font-weight: bold; color: #00ff00;">{failed_case['answer']}</span>
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    # 💡 こちらの戦績報告も<p>タグを<div>タグに変更！
    st.markdown(f"""
    <div style='text-align: center; border: 3px solid #ff4b4b; padding: 20px; border-radius: 10px; background-color: #330000; color: white;'>
        <h2 style='color: #ff4b4b; font-family: "Shippori Mincho", serif;'>⚔️ 戦績報告 ⚔️</h2>
        <div style='font-size: 20px; color: #ffffff; margin-bottom: 15px;'><b>{st.session_state.player_name}</b> 殿</div>
        <h1 style='color: #ffea00; font-family: "Shippori Mincho", serif;'>最終スコア： {st.session_state.last_score}</h1>
        <h2 style='color: gold; font-family: "Shippori Mincho", serif;'>最終階級：【 {st.session_state.last_rank} 】</h2>
        <div style='font-size: 16px; color: #ffbcbc; font-weight: bold; margin-top: 15px;'>ランキングに記録されました！次の出陣をお待ちしております。</div>
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

# ==========================================
# ⚔️ ゲーム継続中画面
# ==========================================
current_lv = calculate_level(st.session_state.score)

if current_lv < len(rank_data):
    current_rank, character = rank_data[current_lv]
elif current_lv < 100:
    current_rank, character = f"☆創造主☆", "👑"
else:
    current_rank, character = "創造主", "🌌"

is_boss = (st.session_state.question_count % 10 == 0)

if is_boss:
    boss_list = [
        ("🐉", "混合性異常ドラゴン"), ("👹", "代償逸脱の鬼将軍"), ("👺", "多重病態の大天狗"),
        ("💀", "敗血症ショックの怨霊"), ("🐍", "致死性アシデミア大蛇"),
        ("🌋", "重症DKAの業火"), ("👁️", "酸塩基を統べる魔王")
    ]
    random.seed(st.session_state.question_count) 
    enemy_char, enemy_name = random.choice(boss_list)
    random.seed() 
    enemy_name = f"{enemy_name} (BOSS)" 
    bg_color = "#4d0000" 
else:
    zako_list = [
        ("🧟", "アシデミア歩兵"), ("🥷", "アルカレミア忍者"), ("👻", "過換気ゴースト"), 
        ("💩", "下痢スライム"), ("💃", "嘔吐くノ一"), ("👲", "乳酸戦士"), 
        ("👹", "ケトン武者"), ("👺", "アルドステロン大名"), ("💊", "利尿薬商人"), 
        ("💨", "COPDだるま"), ("💤", "鎮静剤の眠り猫"), ("📿", "尿毒症坊主"), 
        ("🏃", "尿細管足軽"), ("🌪️", "パニック天狗")
    ]
    random.seed(st.session_state.question_count)
    enemy_char, enemy_name = random.choice(zako_list)
    random.seed() 
    bg_color = "#262730" 

# --- 💥 敵を討ち取った時のエフェクト生成 ---
battle_effect = ""
if st.session_state.get("just_correct", False):
    # 💡 アニメーション名（floatUp_〇〇）に問題番号を混ぜて、毎回「新しいアニメーション」だとブラウザに錯覚させる！
    c = st.session_state.question_count
    battle_effect = f"<div style='position: absolute; top: -30px; left: 50%; transform: translateX(-50%); color: #ffea00; font-size: 1.5rem; font-weight: bold; white-space: nowrap; text-shadow: 2px 2px 0 #000, -2px -2px 0 #000, 2px -2px 0 #000, -2px 2px 0 #000; z-index: 10; animation: floatUp_{c} 1.5s ease-out forwards;'>💥 討ち取ったり！</div><style>@keyframes floatUp_{c} {{ 0% {{ opacity: 0; transform: translate(-50%, 20px) scale(0.5); }} 15% {{ opacity: 1; transform: translate(-50%, -10px) scale(1.2); }} 80% {{ opacity: 1; transform: translate(-50%, -20px) scale(1); }} 100% {{ opacity: 0; transform: translate(-50%, -50px) scale(1); }} }}</style>"
    st.session_state.just_correct = False
# 💡 コードブロック化のバグを防ぐため、HTMLの字下げ（インデント）を左端に詰めています
html_ui = f"""
<div style="font-family: 'Shippori Mincho', serif; display: flex; justify-content: space-between; align-items: center; padding: 15px; background: {bg_color}; border-radius: 10px; margin-bottom: 20px; color: white; border: {'2px solid #ff4b4b' if is_boss else '1px solid #444'}; box-shadow: 0 4px 8px rgba(0,0,0,0.5);">
<div style="text-align: center; flex: 2; border-right: 2px solid #444; padding-right: 10px;">
<div style="font-size: 0.8rem; color: #aaa;">Lv.{current_lv} {current_rank}</div>
<div style="font-size: 2.5rem;">{character}</div>
<div style="font-size: 1.2rem; font-weight: bold; color: #fff;">{st.session_state.player_name} <span style="font-size:0.8rem; color:#aaa;">殿</span></div>
</div>
<div style="text-align: center; flex: 1; padding: 0 10px;">
<div style="font-size: 1.8rem; font-weight: bold; color: #ff4b4b; text-shadow: 0 0 8px #ff0000;">VS</div>
<div style="font-size: 0.8rem; color: #aaa;">第 {st.session_state.question_count} 問</div>
</div>
<div style="position: relative; text-align: center; flex: 2; border-left: 2px solid #444; padding-left: 10px;">
{battle_effect}
<div style="font-size: 0.8rem; color: {'#ffbcbc' if is_boss else '#aaa'};">{'⚠️ 10問目の試練' if is_boss else '雑魚敵'}</div>
<div style="font-size: 2.5rem;">{enemy_char}</div>
<div style="font-size: 1.2rem; font-weight: bold; color: {'#ff4b4b' if is_boss else '#e6b422'};">{enemy_name}</div>
</div>
</div>
"""
st.markdown(html_ui, unsafe_allow_html=True)

if 'last_rendered_lv' not in st.session_state:
    st.session_state.last_rendered_lv = current_lv
just_leveled_up = current_lv > st.session_state.last_rendered_lv
st.session_state.last_rendered_lv = current_lv 

score = st.session_state.score
if score < 40: progress_val = (score % 2) / 2.0
elif score < 70: progress_val = ((score - 40) % 3) / 3.0
elif score < 90: progress_val = ((score - 70) % 4) / 4.0
elif score < 115: progress_val = ((score - 90) % 5) / 5.0
else: progress_val = 1.0

bar_placeholder = st.empty()
if just_leveled_up:
    bar_placeholder.progress(1.0, text="✨ 見事！階級昇格！！ ✨")
    time.sleep(0.8) 

if progress_val == 1.0: bar_text = "🌌 創造主到達！あなたは神です 🌌"
else: bar_text = f"次の階級まで... {'新たなる試練へ' if progress_val == 0.0 else '出陣中！'}"
bar_placeholder.progress(progress_val, text=bar_text)

# --- 問題表示 ---
case = st.session_state.current_case
st.info(f"**pH**: {case['pH']} | **PaCO2**: {case['PaCO2']} mmHg | **HCO3-**: {case['HCO3']} mEq/L")

if case.get("is_boss"):
    st.error(f"🔥 **【警告：代償範囲からの逸脱】**\n\nこの患者の一次性異常は **「{case['primary']}」** です。\n\nしかし数値が代償範囲から逸脱しています。合併している **二次性異常（混合性異常）** はどれですか？")
else:
    st.write("最も疑われる一次性の酸塩基平衡異常はどれですか？")

col_a, col_b = st.columns(2)
with col_a:
    st.write("🟦 **アシドーシス系**")
    if st.button("💦 代謝性アシドーシス", use_container_width=True): handle_answer("代謝性アシドーシス", current_rank)
    if st.button("🌬️ 呼吸性アシドーシス", use_container_width=True): handle_answer("呼吸性アシドーシス", current_rank)
with col_b:
    st.write("🟥 **アルカローシス系**")
    if st.button("🔥 代謝性アルカローシス", use_container_width=True): handle_answer("代謝性アルカローシス", current_rank)
    if st.button("☁️ 呼吸性アルカローシス", use_container_width=True): handle_answer("呼吸性アルカローシス", current_rank)
