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
  api_key = st.secrets["GEMINI_API_KEY"]
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

# クライアントの初期化
client = genai.Client(api_key=api_key)

# 画面上のチャット履歴の初期化
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

  if uploaded_file is not None:
    img_to_display = Image.open(uploaded_file)

  # ユーザーの発言を画面用履歴に追加＆表示
  st.session_state.messages.append(
      {"role": "user", "content": user_query, "image": img_to_display}
  )
  with st.chat_message("user"):
    if img_to_display:
      st.image(img_to_display, width=300)
    st.markdown(user_query)

  # Geminiに渡すための「これまでの全会話履歴」を構築する
  # これにより、AIが過去のやり取りを完璧に思い出しながら返答できるようになります
  chat_history_for_gemini = []
  for msg in st.session_state.messages[:-1]:  # 今回の最新発言を除く過去の履歴
    role = "user" if msg["role"] == "user" else "model"
    # テキストと画像が含まれている場合はリストとしてまとめる
    content_parts = [msg["content"]]
    if "image" in msg and msg["image"] is not None:
      content_parts.append(msg["image"])
    chat_history_for_gemini.append(
        types.Content(
            role=role,
            parts=[
                p
                if isinstance(p, Image.Image)
                else types.Part.from_text(text=p)
                for p in content_parts
            ],
        )
    )

  # 最新のユーザー入力を準備
  latest_parts = [user_query]
  if img_to_display is not None:
    latest_parts.append(img_to_display)

  # AIに送信して返答をもらう
  with st.chat_message("assistant"):
    with st.spinner("AIが原因を分析中..."):
      try:
        # チャットセッションを開始し、過去の全履歴（chat_history_for_gemini）をコンテキストとして渡す
        chat = client.chats.create(
            model="gemini-flash-latest",
            history=chat_history_for_gemini,
            config=types.GenerateContentConfig(
                system_instruction=pc_expert_instruction,
                temperature=0.3,
            ),
        )
        response = chat.send_message(latest_parts)
        st.markdown(response.text)
        st.session_state.messages.append(
            {"role": "assistant", "content": response.text}
        )
      except Exception as e:
        st.error(f"エラーが発生しました: {e}")
