def evaluate_with_claude(structure: dict) -> dict:
    return {
        "intent_match": 0.9,
        "quality_score": 0.85,
        "comment": "Claudeによる仮評価"
    }

def evaluate_with_chatgpt(structure: dict) -> dict:
    return {
        "intent_match": 0.88,
        "quality_score": 0.80,
        "comment": "ChatGPTによる仮評価"
    }

def call_claude_and_gpt(structure: dict) -> dict:
    return {
        "claude": evaluate_with_claude(structure),
        "chatgpt": evaluate_with_chatgpt(structure)
    } 