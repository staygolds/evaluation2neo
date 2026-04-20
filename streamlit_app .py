
import streamlit as st
import pandas as pd
import google.genai as genai # Changed from google.generativeai
import os
import json # jsonモジュールをインポート

# --- 設定 ---
st.set_page_config(page_title="誠実な管理者AI(Gemini版)：職員評価分析", layout="wide")

# Gemini APIキーの設定
# 直接入力するか、環境変数から取得するようにしてください
# genai.configure(api_key="YOUR_GEMINI_API_KEY")

# サイドバーでのAPIキー入力
with st.sidebar:
    api_key_for_app = st.text_input("Gemini API Keyを入力してください", type="password")
    if api_key_for_app:
        genai.configure(api_key=api_key_for_app)

# CSVファイルパスのマッピング (ファイル名を半角スペースに統一)
# Streamlit Community Cloudにデプロイする際は、これらのファイルをGitHubリポジトリのルートに配置する必要があります
csv_file_map = {
    "幹部": "cleaned_評価表 幹部 新ver. .csv",
    "医務": "cleaned_評価表 医務 新ver. .csv",
    "事務": "cleaned_評価表 事務 新ver. .csv",
    "栄養課": "cleaned_評価表 栄養課 新ver. .csv",
    "支援": "cleaned_評価表 支援 新ver. .csv",
    "初任者": "cleaned_評価表 新任職員 新ver. .csv",
}

# 職員データを保存するディレクトリ
SAVE_DIR = 'employee_data'

# --- データ保存・読み込み関数 ---
def save_employee_profile(profile_name, data):
    if not os.path.exists(SAVE_DIR):
        os.makedirs(SAVE_DIR)
    file_path = os.path.join(SAVE_DIR, f"{profile_name}.json")
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    return file_path

def load_employee_profile(profile_name):
    file_path = os.path.join(SAVE_DIR, f"{profile_name}.json")
    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return None

def get_saved_profiles():
    if not os.path.exists(SAVE_DIR):
        return []
    profiles = [f.replace('.json', '') for f in os.listdir(SAVE_DIR) if f.endswith('.json')]
    return sorted(profiles)

# --- UI構築 ---
st.title("🛡️ 誠実な管理者AI：Gemini分析システム")
st.caption("職員情報とコンピテンシー評価、面接所感を統合し、経営的視点からアドバイスを生成します。")

# --- サイドバーでの職員情報入力 ---
st.sidebar.subheader("職員情報入力")

# プロファイルの保存・読み込み機能を追加
st.sidebar.markdown("--- プロファイルの保存/読み込み ---")
saved_profiles = get_saved_profiles()

selected_profile_to_load = st.sidebar.selectbox("保存済みプロファイルの選択", [''] + saved_profiles, key="load_profile_select")
if st.sidebar.button("プロファイルを読み込む", key="load_profile_button"):
    if selected_profile_to_load:
        loaded_data = load_employee_profile(selected_profile_to_load)
        if loaded_data:
            st.session_state.staff_name_input = loaded_data.get('target_name', '')
            st.session_state.staff_position_input = loaded_data.get('役職', '')
            # 所属はselectboxなので直接値をセットできない可能性があるため、初期値で処理するか、stateを更新する
            # ここではselected_departmentを再設定するためにキーを探す
            if loaded_data.get('所属') in csv_file_map:
                st.session_state.department_selectbox = loaded_data.get('所属')
            st.session_state.staff_mission_input = loaded_data.get('重点ミッション', '')
            st.session_state.staff_duties_input = loaded_data.get('具体的職務', '')
            st.session_state.staff_interview_impression = loaded_data.get('面接所感', '')
            st.session_state.eval_items = loaded_data.get('eval_items', [])
            st.session_state.ai_analysis_result = loaded_data.get('ai_analysis_result', '') # AI分析結果を読み込む
            st.sidebar.success(f"'{selected_profile_to_load}' を読み込みました。")
        else:
            st.sidebar.error(f"'{selected_profile_to_load}' の読み込みに失敗しました。")

profile_name_to_save = st.sidebar.text_input("新しいプロファイル名で保存", key="save_profile_name_input")
if st.sidebar.button("プロファイルを保存", key="save_profile_button"):
    if profile_name_to_save:
        data_to_save = {
            "target_name": st.session_state.staff_name_input,
            "役職": st.session_state.staff_position_input,
            "所属": st.session_state.department_selectbox, # 所属も保存
            "重点ミッション": st.session_state.staff_mission_input,
            "具体的職務": st.session_state.staff_duties_input,
            "面接所感": st.session_state.staff_interview_impression,
            "eval_items": st.session_state.eval_items,
            "ai_analysis_result": st.session_state.get('ai_analysis_result', '') # AI分析結果を保存
        }
        save_employee_profile(profile_name_to_save, data_to_save);
        st.sidebar.success(f"'{profile_name_to_save}' としてプロファイルを保存しました。");
        st.rerun() # 保存後、サイドバーの選択肢を更新するために再実行
    else:
        st.sidebar.error("保存するプロファイル名を入力してください。")


# 職員情報入力欄（セッションステートで管理）
target_name_for_app = st.sidebar.text_input("職員名", "木暮　光広", key="staff_name_input")
jd_役職 = st.sidebar.text_input("役職", "主任看護師", key="staff_position_input")
selected_department = st.sidebar.selectbox(
    "所属",
    options=list(csv_file_map.keys()),
    index=list(csv_file_map.keys()).index("医務") if "医務" in csv_file_map else 0, # Default to '医務' or first item
    key="department_selectbox"
)
jd_重点ミッション = st.sidebar.text_area("重点ミッション", "徹底した健康管理により重度化・欠員を防止し施設入所稼働率を維持。口腔ケアや機能訓練の充実による高い支援品質の提供。短期入所の利用促進（稼働率25.5%からの向上）。", height=100, key="staff_mission_input")
jd_具体的職務 = st.sidebar.text_area("具体的職務", "医務日誌整備、服薬管理、口腔ケア、協力医療機関との連携、第1種衛生管理責任者、保健部会担当", height=100, key="staff_duties_input")
jd_面接所感 = st.sidebar.text_area("面接所感", "面接を通して、真面目で着実に業務に取り組む姿勢が見受けられました。一方で、リーダーシップを発揮する場面はまだ少ない印象です。", height=100, key="staff_interview_impression") # 新しい面接所感入力欄

# 職務分掌データを辞書にまとめる
jd_for_app = {
    "役職": jd_役職,
    "所属": selected_department,
    "重点ミッション": jd_重点ミッション,
    "具体的職務": jd_具体的職務,
    "面接所感": jd_面接所感 # 面接所感を辞書に追加
}

# --- サイドバーでの評価項目と評価点の入力 ---
st.sidebar.subheader("評価項目と評価点")

# セッションステートで評価項目を管理
if 'eval_items' not in st.session_state:
    st.session_state.eval_items = []

# 選択された所属に基づいて評価項目を読み込む
current_eval_items_options = []
if selected_department and selected_department in csv_file_map:
    csv_path = csv_file_map[selected_department]

    try:
        df_department_eval = pd.read_csv(csv_path, encoding='utf-8')
        # 評価項目列が存在することを確認
        if '評価項目（具体的行動）' in df_department_eval.columns:
            current_eval_items_options = df_department_eval['評価項目（具体的行動）'].dropna().tolist()
        else:
            st.sidebar.error(f"エラー: CSVファイル '{selected_department}' に '評価項目（具体的行動）' 列が見つかりません。")
    except FileNotFoundError:
        st.sidebar.error(f"所属 '{selected_department}' の評価項目ファイルが見つかりません。パスを確認してください: {csv_path}")
    except Exception as e:
        st.sidebar.error(f"所属 '{selected_department}' の評価項目を読み込めませんでした: {e}")

selected_eval_item_desc = st.sidebar.selectbox(
    "新しい評価項目（具体的行動）",
    options=current_eval_items_options,
    key="eval_item_selectbox"
)
new_item_score = st.sidebar.number_input("評価点 (1-5)", min_value=1, max_value=5, value=3, key="new_item_score_input")

if st.sidebar.button("評価項目を追加", key="add_eval_item_button"):
    if selected_eval_item_desc and new_item_score:
        # Check if the item already exists to prevent duplicates (optional)
        if not any(item['評価項目（具体的行動）'] == selected_eval_item_desc for item in st.session_state.eval_items):
            st.session_state.eval_items.append({"評価項目（具体的行動）": selected_eval_item_desc, "評価点 (1-5)": float(new_item_score)})
            st.sidebar.success("評価項目を追加しました。")
        else:
            st.sidebar.warning("その評価項目は既に追加されています。")
    else:
        st.sidebar.error("評価項目と評価点を入力してください。")

# 既存の評価項目を表示・編集
if st.session_state.eval_items:
    st.sidebar.markdown("--- 現在の評価項目 ---")
    eval_df_display_sidebar = pd.DataFrame(st.session_state.eval_items)
    st.sidebar.dataframe(eval_df_display_sidebar, width='stretch', hide_index=True, height=200) # Changed use_container_width=True to width='stretch'

    # 評価項目をクリアするボタン
    if st.sidebar.button("すべての評価項目をクリア", key="clear_eval_items_button"):
        st.session_state.eval_items = []
        st.sidebar.info("すべての評価項目をクリアしました。")


# --- メインコンテンツエリア ---
col1, col2 = st.columns([1, 1])

with col1:
    st.subheader(f"📋 職務分掌の確認: {target_name_for_app}")
    st.info(f"**期待される役割**: {jd_for_app['役職']}")
    st.info(f"**所属**: {jd_for_app['所属']}")
    st.markdown(f"""**重点目標**:
{jd_for_app['重点ミッション']}""")
    st.markdown(f"""**具体的職務**:
{jd_for_app['具体的職務']}""")
    st.markdown(f"""**面接所感**:
{jd_for_app['面接所感']}""") # 面接所感をメインコンテンツに表示

    st.subheader("📊 評価スコア一覧")
    if st.session_state.eval_items:
        eval_df_display = pd.DataFrame(st.session_state.eval_items)
        st.dataframe(eval_df_display, width='stretch', hide_index=True, height=300) # Changed use_container_width=True to width='stretch'
        # 合計点の表示をメインコンテンツに移動
        total_score = eval_df_display['評価点 (1-5)'].sum()
        st.info(f"**合計点**: {total_score}点") # Display in main content, not sidebar
    else:
        st.info("サイドバーから評価項目と評価点を追加してください。")

with col2:
    st.subheader("🧠 Gemini 誠実な管理者分析") # タイトルも変更

    if st.button("AI分析を開始"):
        if not api_key_for_app:
            st.error("APIキーを入力してください。")
        elif not st.session_state.eval_items:
            st.error("評価項目と評価点を入力してください。")
        else:
            with st.spinner("誠実な管理者が思考中..."): # スピナーメッセージも変更
                # 分析用のプロンプト構築
                eval_text_for_app = ""
                for item in st.session_state.eval_items:
                    eval_text_for_app += "- {}: {}点\n".format(item['評価項目（具体的行動）'], item['評価点 (1-5)'])

                prompt_for_app = f"""
                あなたは障害者支援施設の「誠実な施設長」です。
                部下の「職務分掌（期待される役割）」と「実際の評価結果」、「面接所感」を突き合わせ、深い洞察を行ってください。

                【対象職員】: {target_name_for_app}
                【役職】: {jd_for_app['役職']}
                【所属】: {jd_for_app['所属']}
                【この職員に課された経営目標】: {jd_for_app['重点ミッション']}
                【面接所感】: {jd_for_app['面接所感']}

                【今回のコンピテンシー評価結果】:
                {eval_text_for_app}

                上記を踏まえ、以下の4項目について、プロの経営者として日本語で回答してください。
                1. 【強みの連結】: 評価点が高い項目が、経営目標（稼働率向上やコスト抑制等）にどう貢献しているか。
                2. 【懸念される乖離】: 目標達成のために不可欠なのに、評価点が伸び悩んでいる項目（ボトルネック）の指摘。
                3. 【具体的指導案】: 現場での行動をどう変えさせるべきか、誠実な管理者として具体的な助言。
                4. 【面談のキラーフレーズ】: 本人のモチベーションを高めつつ、核心を突くための最初の一言。
                """

                # Geminiモデルの初期化
                model = genai.GenerativeModel('gemini-1.5-flash') # Confirming model name based on previous output

                try:
                    response_for_app = model.generate_content(prompt_for_app)
                    st.session_state.ai_analysis_result = response_for_app.text # AI分析結果をセッションステートに保存
                    st.success("分析完了")
                    st.markdown(st.session_state.ai_analysis_result) # セッションステートから表示
                except Exception as e:
                    st.error(f"エラーが発生しました: {e}")

    # 読み込んだAI分析結果がある場合は表示
    if 'ai_analysis_result' in st.session_state and st.session_state.ai_analysis_result:
        st.markdown("--- 読み込み済みのAI分析結果 ---")
        st.markdown(st.session_state.ai_analysis_result)
    