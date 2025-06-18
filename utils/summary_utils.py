# utils/summary_utils.py

def summarize_user_requirements(chat_history):
    """
    ユーザーのチャット履歴から要件を要約する（簡易版）
    """
    # ユーザーの発話だけを抜き出してまとめる
    user_inputs = [msg["content"] for msg in chat_history if msg["role"] == "user"]
    summary = "・" + "\n・".join(user_inputs[-5:])  # 最新5件だけ例として表示
    return summary
