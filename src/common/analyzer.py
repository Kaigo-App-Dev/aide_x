import difflib
from typing import Optional, List, Dict, Any
from src.types import StructureDict, EvaluationResult

# 🧠 指示・誘導メッセージ（ChatGPT向け）
GUIDED_MESSAGES = {
    "repeat_detected": {
        "type": "prompt",
        "content": "ユーザーが似た発言を繰り返しています。今回は、前回と少し違う角度から聞き返してください。たとえば『使う場面を想定すると、どんな場所や人を意識していますか？』など。"
    },
    "info_missing": {
        "type": "prompt",
        "content": "発話が短く、情報が不足しています。『どういう目的のアプリですか？』など、目的や対象者について尋ねてください。"
    },
    "loop_detected": {
        "type": "text",
        "content": (
            "🔁 何度か似た話が続いているようです。\n"
            "💡 もしよければ別の視点から考えてみましょうか？\n"
            "たとえば『どんな場面で使いますか？』や『他の人と共有しますか？』など。"
        )
    }
}


def analyze_conversation(chat_history: List[Dict[str, Any]]) -> Optional[str]:
    """
    会話履歴を分析し、次のアクションを返す：
    - "prompt:〇〇" → GPTに渡す指示
    - 通常文字列 → analyzerの発話
    - None → 何もしない
    """
    if not chat_history:
        return None

    recent_msgs = [m["content"] for m in chat_history[-5:] if m["role"] == "user"]
    if len(recent_msgs) < 2:
        return None

    # ✅ 類似発言の繰り返し検出（意味ベース）
    is_similar, _ = detect_repeated_user_messages(chat_history, similarity_threshold=0.85)
    if is_similar:
        message = GUIDED_MESSAGES["repeat_detected"]
        return f"prompt:{message['content']}"

    # ✅ 情報不足検出
    if detect_missing_info(chat_history):
        message = GUIDED_MESSAGES["info_missing"]
        return f"prompt:{message['content']}"

    return None


def detect_repeated_user_messages(chat_history: List[Dict[str, Any]], similarity_threshold: float = 0.90) -> tuple[bool, Optional[str]]:
    """
    過去のユーザー発言と最新の発言を比較し、類似度が高ければ再発話と見なす。
    """
    user_messages = [m['content'] for m in chat_history if m['role'] == 'user']
    if len(user_messages) < 2:
        return False, None

    latest = user_messages[-1]
    for prev in user_messages[:-1][::-1]:
        ratio = difflib.SequenceMatcher(None, latest, prev).ratio()
        if ratio >= similarity_threshold:
            return True, prev

    return False, None


def detect_missing_info(chat_history: List[Dict[str, Any]]) -> bool:
    """
    ユーザーの発話に重要な要素が欠けていないかを検出。
    - 発話が短すぎる場合や、特定キーワードが2つ未満なら True（情報不足と判定）
    """
    keywords = ["アプリ", "機能", "目的", "使いたい人", "使い方"]
    recent_messages = [m["content"] for m in chat_history if m["role"] == "user"][-3:]
    score = sum(any(k in msg for k in keywords) for msg in recent_messages)
    last_msg = recent_messages[-1] if recent_messages else ""
    return score < 2 or len(last_msg.strip()) < 10


def analyze_structure(structure: StructureDict) -> EvaluationResult:
    """
    構成を分析して評価結果を返す
    
    Args:
        structure (StructureDict): 分析対象の構成
        
    Returns:
        EvaluationResult: 評価結果
    """
    result: EvaluationResult = {
        "score": 0.0,
        "comment": "",
        "metrics": {}
    }
    
    # タイトルの評価
    if structure.get("title"):
        result["metrics"]["title_length"] = len(structure["title"])
        if len(structure["title"]) > 10:
            result["score"] += 0.2
    
    # 説明の評価
    if structure.get("description"):
        result["metrics"]["description_length"] = len(structure["description"])
        if len(structure["description"]) > 50:
            result["score"] += 0.3
    
    # コンテンツの評価
    content = structure.get("content", {})
    if content:
        result["metrics"]["content_sections"] = len(content)
        if len(content) >= 3:
            result["score"] += 0.5
        
        # 各セクションの評価
        for key, value in content.items():
            if isinstance(value, dict):
                result["metrics"][f"{key}_items"] = len(value)
                if len(value) >= 2:
                    result["score"] += 0.1
    
    # コメントの生成
    comments = []
    if result["metrics"].get("title_length", 0) > 10:
        comments.append("タイトルが適切な長さです")
    if result["metrics"].get("description_length", 0) > 50:
        comments.append("説明が十分に詳細です")
    if result["metrics"].get("content_sections", 0) >= 3:
        comments.append("コンテンツの構成が充実しています")
    
    result["comment"] = "、".join(comments) if comments else "改善の余地があります"
    
    return result


def get_structure_metrics(structure: StructureDict) -> Dict[str, Any]:
    """
    構成のメトリクスを計算する
    
    Args:
        structure (StructureDict): 分析対象の構成
        
    Returns:
        Dict[str, Any]: メトリクス
    """
    metrics = {
        "title_length": len(structure.get("title", "")),
        "description_length": len(structure.get("description", "")),
        "content_sections": len(structure.get("content", {})),
        "total_items": 0
    }
    
    content = structure.get("content", {})
    for value in content.values():
        if isinstance(value, dict):
            metrics["total_items"] += len(value)
    
    return metrics 