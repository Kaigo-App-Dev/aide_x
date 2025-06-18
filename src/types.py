"""
共通の型定義

このモジュールは、AIDE-X全体で使用される共通の型定義を提供します。
型の定義は以下のセクションに分かれています：

1. メッセージ関連の型定義
2. AIプロバイダ関連の型定義
3. 構成テンプレート関連の型定義
4. 評価結果関連の型定義
5. チャット関連の型定義
6. UI関連の型定義
7. ユーティリティ関数
"""

from typing import TypedDict, List, Optional, Dict, Any, Union, Literal, Protocol, Callable, TypeAlias, TYPE_CHECKING
from datetime import datetime
from dataclasses import dataclass

# ===== メッセージ関連の型定義 =====

class MessageParam(TypedDict):
    """AIプロバイダーのメッセージパラメータ"""
    role: str
    content: str
    name: Optional[str]

MessageParamList = List[MessageParam]

# ===== AIプロバイダ関連の型定義 =====

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

# ===== 構成テンプレート関連の型定義 =====

class StructureDict(TypedDict):
    """構成テンプレートの型定義"""
    id: str  # 一意のID
    title: str  # タイトル
    description: str  # 説明
    content: Dict[str, Any]  # コンテンツ
    metadata: Optional[Dict[str, Any]]  # メタデータ
    history: Optional[List['StructureHistory']]  # 履歴

class StructureHistory(TypedDict):
    """構成データの履歴ログの型定義"""
    timestamp: str  # ISO8601形式のタイムスタンプ
    action: str  # 実行されたアクション
    summary: str  # 変更内容の要約
    diff: Optional[str]  # 差分情報（存在する場合のみ）
    by: Literal["user", "Claude", "Gemini", "Cursor"]  # 実行主体
    detail: Optional[str]  # 詳細情報
    snapshot: Optional[Dict[str, Any]]  # スナップショット

# ===== 評価結果関連の型定義 =====

class EvaluationResult(TypedDict, total=False):
    """評価結果の型定義"""
    score: float  # 評価スコア
    feedback: str  # フィードバック
    details: Dict[str, Any]  # 詳細情報
    is_valid: bool  # 有効性フラグ
    comment: Optional[str]  # コメント
    metrics: Optional[Dict[str, Any]]  # メトリクス
    error: Optional[str]  # エラーメッセージ
    intent_match: Optional[float]  # 意図の一致度
    intent_reason: Optional[str]  # 意図の一致理由
    quality_score: Optional[float]  # 品質スコア
    improvement_suggestions: Optional[List[str]]  # 改善提案

# 評価関数の型定義
EvaluationFunction = Callable[[str, Optional[Any]], EvaluationResult]

# ===== チャット関連の型定義 =====

class ChatHistory(TypedDict):
    """チャット履歴の型定義"""
    messages: List[Any]
    metadata: Dict[str, Any]

class LLMResponse(TypedDict):
    """LLMからの応答の型定義"""
    content: Union[str, Dict[str, Any]]  # 生成された内容（テキストまたは構造化データ）
    model: str  # 使用したモデル名
    usage: Dict[str, Any]  # トークン数やコスト情報
    provider: Literal["Claude", "Gemini", "ChatGPT", "Cursor"]  # プロバイダ名
    role: Optional[str]  # メッセージの役割
    status: Optional[str]  # ステータス
    error: Optional[str]  # エラーメッセージ

# ===== UI関連の型定義 =====

class UIComponent(TypedDict):
    """UIコンポーネントの型定義"""
    type: str  # 'button', 'text', 'image', 'container', etc.
    label: Optional[str]  # 表示ラベル
    content: Optional[str]  # コンテンツ（テキスト、画像URL等）
    children: Optional[List['UIComponent']]  # 子コンポーネント
    style: Optional[Dict[str, Any]]  # スタイル設定
    props: Optional[Dict[str, Any]]  # その他のプロパティ
    metadata: Optional[Dict[str, Any]]  # メタデータ
    title: Optional[str]  # タイトル

class DiffResult(TypedDict):
    """差分結果の型定義"""
    before: str  # 変更前の内容
    after: str  # 変更後の内容
    highlight: str  # 差分がハイライトされたHTMLやマークアップ
    summary: str  # 差分の簡易説明
    added: List[Dict[str, Any]]  # 追加された項目
    removed: List[Dict[str, Any]]  # 削除された項目
    changed: List[Dict[str, Any]]  # 変更された項目
    context: Dict[str, str]  # コンテキスト情報

# ===== ユーティリティ関数 =====

def safe_cast_list(value: Any) -> List[Any]:
    """安全にリストにキャスト"""
    if isinstance(value, list):
        return value
    return []

def safe_cast_str(value: Any) -> str:
    """安全に文字列にキャスト"""
    if isinstance(value, str):
        return value
    return str(value) if value is not None else ""

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

# ===== re-export =====

__all__ = [
    # メッセージ関連
    'MessageParam',
    'MessageParamList',
    
    # AIプロバイダ関連
    'AIProviderResponse',
    'AIProvider',
    
    # 構成テンプレート関連
    'StructureDict',
    'StructureHistory',
    
    # 評価結果関連
    'EvaluationResult',
    'EvaluationFunction',
    
    # チャット関連
    'ChatHistory',
    'LLMResponse',
    
    # UI関連
    'UIComponent',
    'DiffResult',
    
    # ユーティリティ関数
    'safe_cast_list',
    'safe_cast_str',
    'safe_cast_dict',
    'safe_cast_datetime',
    'safe_cast_message_param',
    'safe_cast_ai_response'
] 