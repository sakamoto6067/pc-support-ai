from google import genai
from google.genai import types
from PIL import Image
import streamlit as st

st.set_page_config(
    page_title="PCサポート・AIドクター", page_icon="💻", layout="centered"
)

st.title("💻 PCサポート・AIドクター")
st.write(
    "パソコンのトラブル内容や、エラー画面の写真をアップロードして相談してください。"
)

# APIキーの安全な読み込み
if "GEMINI_API_KEY" in st.secrets:
  client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
else:
  st.error(
      "⚠️ APIキーが設定されていません。Streamlitの設定画面（Secrets）で"
      " APIキーを登録してください。"
  )
  st.stop()

# PCサポート専用のシステム指示
pc_expert_instruction = """
あなたは熟練のパソコン修理・サポートエンジニアです。
ユーザーからPCの不具合の相談やエラー画面の写真を受け取ったら、以下のルールで対応してください：
1. 原因の切り分けを論理的に行い、安全な修復手順を段階的に提案する。
2. データのバックアップなど安全対策を必ず最初に伝える。
3. 必要に応じてユーザーに優しく逆質問をして、状況を深掘りする。
"""

# 1. チャットセッション（会話履歴を保持する機能）を初期化
if "chat" not in st.session_state:
  st.session_state.chat = client.chats.create(
      model="gemini-flash-latest",
      config=types.GenerateContentConfig(
          system_instruction=pc_expert_instruction,
          temperature=0.3,
      ),
  )

# 2. 画面上のチャット表示用履歴の初期化
if "messages" not in st.session_state:
  st.session_state.messages = []

# 過去の会話を画面に表示
for message in st.session_state.messages:
  with st.chat_message(message["role"]):
    if "image" in message and message["image"] is not None:
      st.image(message["image"], width=300)
    st.markdown(message["content"])

# ユーザーからの画像アップロードと入力欄
uploaded_file = st.file_uploader(
    "📷 エラー画面やPCの写真を添付する（任意）", type=["jpg", "jpeg", "png"]
)
user_query = st.chat_input("例：電源は入るのに画面が真っ暗です...")

if user_query:
  img_to_display = None
  contents = [user_query]

  if uploaded_file is not None:
    img_to_display = Image.open(uploaded_file)
    contents.append(img_to_display)

  # ユーザーの発言を画面用履歴に追加＆表示
  st.session_state.messages.append(
      {"role": "user", "content": user_query, "image": img_to_display}
  )
  with st.chat_message("user"):
    if img_to_display:
      st.image(img_to_display, width=300)
    st.markdown(user_query)

  # 3. チャットセッションを使ってAIに送信（会話履歴が自動で引き継がれます）
  with st.chat_message("assistant"):
    with st.spinner("AIが原因を分析中..."):
      try:
        response = st.session_state.chat.send_message(contents)
        st.markdown(response.text)
        st.session_state.messages.append(
            {"role": "assistant", "content": response.text}
        )
      except Exception as e:
        st.error(f"エラーが発生しました: {e}")
