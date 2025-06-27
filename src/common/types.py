"""
共通の型定義

このモジュールは、アプリケーション全体で使用される共通の型定義を提供します。
"""

from typing import TypedDict, List, Optional, Dict, Any, Union, Literal, Protocol, Callable
from datetime import datetime
from dataclasses import dataclass, field
from typing_extensions import Required

# メッセージ関連の型定義
class MessageParam(TypedDict, total=False):
    """AIプロバイダーのメッセージパラメータ"""
    role: Required[str]
    content: Required[str]
    name: Optional[str]

MessageParamList = List[MessageParam]

# AIプロバイダ関連の型定義
class AIProviderResponse(TypedDict, total=False):
    """AIプロバイダーのレスポンス型定義"""
    content: str  # 実際の生成結果
    raw: Optional[Dict[str, Any]]  # 元のレスポンス全文（任意）
    provider: Optional[str]  # "claude", "gemini", "chatgpt" など
    error: Optional[str]  # エラーメッセージ（任意）
    model: Optional[str]  # 使用したモデル名
    usage: Optional[Dict[str, Any]]  # トークン数やコスト情報

class AIProvider(Protocol):
    """AIプロバイダーのインターフェース"""
    def call(self, prompt: str, **kwargs) -> AIProviderResponse:
        """AIを呼び出して応答を取得"""
        ...

    def format_messages(self, prompt: str) -> MessageParamList:
        """プロンプトをメッセージ形式に変換"""
        ...

# 構成テンプレート関連の型定義
class StructureDict(TypedDict, total=False):
    """構成テンプレートの型定義"""
    id: Required[str]
    title: Required[str]
    description: Required[str]
    content: Required[Dict[str, Any]]
    metadata: Optional[Dict[str, Any]]
    history: Optional[List['StructureHistory']]

# 評価結果関連の型定義
@dataclass
class EvaluationResult:
    """評価結果の型定義"""
    score: float
    feedback: str
    details: Dict[str, Any] = field(default_factory=dict)
    is_valid: bool = True  # デフォルトでTrue

    def __str__(self) -> str:
        """評価結果を文字列形式で返す"""
        return f"[評価結果]\n- 妥当性: {self.is_valid}\n- スコア: {self.score:.2f}\n- コメント: {self.feedback}"

# 評価関数の型定義
EvaluationFunction = Callable[[str, Optional[Any]], EvaluationResult]

# 例外クラス
class AIError(Exception):
    """AI関連の基本例外クラス"""
    pass

class ProviderError(AIError):
    """プロバイダー固有の例外"""
    pass

class EvaluationError(AIError):
    """評価関連の例外"""
    pass

# ユーティリティ関数
def safe_cast_list(value: Any) -> List[Any]:
    """安全にリストにキャスト"""
    if isinstance(value, list):
        return value
    return []

def safe_cast_dict(value: Any) -> Dict[str, Any]:
    """安全に辞書にキャスト"""
    if isinstance(value, dict):
        return value
    return {}

def safe_cast_datetime(value: Any) -> Optional[datetime]:
    """安全に日時型にキャスト"""
    if isinstance(value, datetime):
        return value
    return None

def safe_cast_message_param(data: Dict[str, Any]) -> MessageParam:
    """安全にMessageParamにキャスト"""
    return {
        "role": str(data.get("role", "")),
        "content": str(data.get("content", "")),
        "name": str(data.get("name")) if data.get("name") is not None else None
    }

def safe_cast_ai_response(data: Dict[str, Any]) -> AIProviderResponse:
    """安全にAIProviderResponseにキャスト"""
    return {
        "content": str(data.get("content", "")),
        "error": str(data.get("error")) if data.get("error") is not None else None,
        "model": str(data.get("model")) if data.get("model") is not None else None,
        "usage": data.get("usage")
    }

@dataclass
class ChatMessage:
    """チャットメッセージ"""
    role: str
    content: str

class StructureHistory(TypedDict):
    """構成データの履歴ログの型定義"""
    timestamp: str  # ISO8601形式のタイムスタンプ
    action: Literal["create", "update", "repair", "evaluate"]  # 実行されたアクション
    summary: str  # 変更内容の要約
    diff: Optional[str]  # 差分情報（存在する場合のみ）
    by: Literal["user", "Claude", "Gemini", "Cursor"]  # 実行主体

class ChatHistory(TypedDict):
    """チャット履歴の型定義"""
    messages: List[ChatMessage]
    metadata: Dict[str, Any]

class LLMResponse(TypedDict):
    """LLMからの応答の型定義"""
    content: Union[str, Dict[str, Any]]  # 生成された内容（テキストまたは構造化データ）
    model: str  # 使用したモデル名
    usage: Dict[str, Any]  # トークン数やコスト情報
    provider: Literal["Claude", "Gemini", "ChatGPT", "Cursor"]  # プロバイダ名

class DiffResult(TypedDict):
    """差分結果の型定義"""
    before: str  # 変更前の内容
    after: str  # 変更後の内容
    highlight: str  # 差分がハイライトされたHTMLやマークアップ
    summary: str  # 差分の簡易説明

class UIComponent(TypedDict):
    """UIコンポーネントの型定義"""
    type: str  # 'button', 'text', 'image', 'container', etc.
    label: Optional[str]  # 表示ラベル
    content: Optional[str]  # コンテンツ（テキスト、画像URL等）
    children: Optional[List['UIComponent']]  # 子コンポーネント
    style: Optional[Dict[str, Any]]  # スタイル設定
    props: Optional[Dict[str, Any]]  # その他のプロパティ
    metadata: Optional[Dict[str, Any]]  # メタデータ

__all__ = [
    'MessageParam',
    'MessageParamList',
    'AIProviderResponse',
    'AIProvider',
    'StructureDict',
    'EvaluationResult',
    'EvaluationFunction',
    'AIError',
    'ProviderError',
    'EvaluationError',
    'safe_cast_list',
    'safe_cast_dict',
    'safe_cast_datetime',
    'safe_cast_message_param',
    'safe_cast_ai_response',
    'ChatMessage',
    'StructureHistory',
    'ChatHistory',
    'LLMResponse',
    'DiffResult',
    'UIComponent'
] 