import os
import json
import logging
from datetime import datetime
from typing import Union, Dict, Any, List, Set

# Initialize logger
logger = logging.getLogger(__name__)

# 構造テンプレート保存ディレクトリ
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'data')

def get_history_path(structure_id: str) -> str:
    """Get the path for a structure history file"""
    return os.path.join(DATA_DIR, f"{structure_id}_history.json")

def save_structure(structure, is_final=False):
    """
    構造データを保存する関数
    
    Args:
        structure (Union[str, dict]): 保存する構造データ
        is_final (bool): 最終版かどうかのフラグ
    
    Raises:
        ValueError: 無効な入力や空のコンテンツの場合
    """
    os.makedirs(DATA_DIR, exist_ok=True)

    logger.debug(f"save_structure 入力の型: {type(structure)}")

    # 文字列の場合はdictに変換
    if isinstance(structure, str):
        if not structure.strip():
            raise ValueError("⚠ 保存失敗：空のJSON文字列です。")
        try:
            structure = json.loads(structure)
        except json.JSONDecodeError:
            raise ValueError("⚠ 保存失敗：構造テンプレートが不正なJSONです。")

    # 型チェック
    if not isinstance(structure, dict):
        raise ValueError("⚠ 保存失敗：structure が dict ではありません。")

    # contentの存在チェック
    if not structure.get("content"):
        raise ValueError("⚠ 保存失敗：content が空です。")

    # contentがdictの場合はJSON文字列に変換
    if isinstance(structure.get("content"), dict):
        logger.debug("💡 structure['content'] は dict → JSON 文字列に変換")
        structure["content"] = json.dumps(structure["content"], ensure_ascii=False, indent=2)

    # is_finalフラグを確実に追加
    structure['is_final'] = is_final

    # IDの生成
    if 'id' not in structure or not structure['id']:
        structure['id'] = f"auto_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    # プロジェクトディレクトリの準備
    project = structure.get("project", "default")
    project_dir = os.path.join(DATA_DIR, project)
    os.makedirs(project_dir, exist_ok=True)

    filename = os.path.join(project_dir, f"{structure['id']}.json")

    # 履歴の管理
    if os.path.exists(filename):
        with open(filename, 'r', encoding='utf-8') as f:
            current_data = json.load(f)
        
        history_path = get_history_path(structure['id'])
        history = []
        
        # 既存の履歴を読み込み
        if os.path.exists(history_path):
            with open(history_path, 'r', encoding='utf-8') as f:
                history = json.load(f)
        
        # 現在のデータを履歴に追加
        history.append(current_data)
        
        # 最新10件のみを保持
        history = history[-10:]
        
        # 履歴を保存
        with open(history_path, 'w', encoding='utf-8') as f:
            json.dump(history, f, ensure_ascii=False, indent=2)

    # 新しいデータを保存
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(structure, f, ensure_ascii=False, indent=2)

def normalize_structure_for_pages(content):
    """
    自由形式の構成データを正規化されたページ構造に変換する関数
    
    Args:
        content (Union[dict, str]): 変換対象の構成データ
        
    Returns:
        dict: 正規化されたページ構造
            {
                "pages": [
                    {
                        "title": str,
                        "sections": [
                            {
                                "title": str,
                                "fields": [
                                    {
                                        "label": str,
                                        "name": str,
                                        "type": str,
                                        "value": Any
                                    }
                                ]
                            }
                        ]
                    }
                ]
            }
    """
    import re
    from typing import Any, Dict, List, Union
    from collections import defaultdict

    def is_nested_dict(d: dict) -> bool:
        """辞書がネストされた構造かどうかを判定"""
        return isinstance(d, dict) and any(isinstance(v, dict) for v in d.values())

    def normalize_text(text: str) -> str:
        """
        テキストを正規化してスネークケースに変換
        
        Args:
            text (str): 変換対象のテキスト
            
        Returns:
            str: 正規化されたスネークケースのテキスト
        """
        if not isinstance(text, str):
            text = str(text)
        
        # 全角文字を半角に変換
        text = text.translate(str.maketrans(
            'ＡＢＣＤＥＦＧＨＩＪＫＬＭＮＯＰＱＲＳＴＵＶＷＸＹＺａｂｃｄｅｆｇｈｉｊｋｌｍｎｏｐｑｒｓｔｕｖｗｘｙｚ０１２３４５６７８９',
            'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789'
        ))
        
        # 特殊文字を適切に変換
        text = text.replace('・', '_')
        text = text.replace('、', '_')
        text = text.replace('，', '_')
        text = text.replace('（', '(')
        text = text.replace('）', ')')
        
        # 括弧内の文字を保持しつつ、括弧を削除
        text = re.sub(r'[\(（]([^\)）]+)[\)）]', r'\1', text)
        
        # 英数字以外の文字をアンダースコアに変換
        text = re.sub(r'[^a-zA-Z0-9_]', '_', text)
        
        # 連続するアンダースコアを1つに
        text = re.sub(r'_+', '_', text)
        
        # 先頭と末尾のアンダースコアを削除
        text = text.strip('_')
        
        # 小文字に変換
        text = text.lower()
        
        return text

    def generate_field_name(label: str, section_title: str, existing_names: set) -> str:
        """
        フィールド名を生成
        
        Args:
            label (str): フィールドのラベル
            section_title (str): セクションのタイトル
            existing_names (set): 既存のフィールド名のセット
            
        Returns:
            str: 生成されたフィールド名
        """
        # ラベルを正規化
        base_name = normalize_text(label)
        
        # セクションタイトルを正規化して接頭辞として使用
        section_prefix = normalize_text(section_title)
        
        # フィールド名を生成（セクション名_フィールド名）
        field_name = f"{section_prefix}_{base_name}"
        
        # 既存の名前と重複する場合は連番を付与
        if field_name in existing_names:
            counter = 1
            while f"{field_name}_{counter}" in existing_names:
                counter += 1
            field_name = f"{field_name}_{counter}"
        
        return field_name

    def create_field(label: str, value: Any, section_title: str, existing_names: set) -> Dict:
        """フィールドオブジェクトを生成"""
        field_name = generate_field_name(label, section_title, existing_names)
        existing_names.add(field_name)
        
        return {
            "label": str(label),
            "name": field_name,
            "type": "text",
            "value": value
        }

    def process_section(section_data: Any, section_title: str, existing_names: set) -> Dict:
        """セクションデータを処理して正規化されたセクション構造を返す"""
        section = {
            "title": section_title,
            "fields": []
        }

        if isinstance(section_data, dict):
            for field_key, field_val in section_data.items():
                section["fields"].append(create_field(field_key, field_val, section_title, existing_names))
        else:
            section["fields"].append(create_field("説明", section_data, section_title, existing_names))
        
        return section

    def process_page(page_data: Any, page_title: str) -> Dict:
        """ページデータを処理して正規化されたページ構造を返す"""
        existing_names = set()  # フィールド名の重複を防ぐためのセット
        page = {
            "title": page_title,
            "sections": []
        }

        if isinstance(page_data, dict):
            if is_nested_dict(page_data):
                # ネストされた構造の場合
                for section_key, section_val in page_data.items():
                    page["sections"].append(process_section(section_val, section_key, existing_names))
            else:
                # フラットな構造の場合
                page["sections"].append(process_section(page_data, "概要", existing_names))
        else:
            # 単一の値の場合
            page["sections"].append(process_section(page_data, "概要", existing_names))

        return page

    try:
        # 入力値の検証
        if not content:
            return {"pages": [], "sections": []}

        if isinstance(content, str):
            try:
                content = json.loads(content)
            except json.JSONDecodeError:
                raise ValueError("無効なJSON文字列です")

        if not isinstance(content, dict):
            raise ValueError("contentは辞書型である必要があります")

        # ページ構造の生成
        pages = []
        for page_key, page_val in content.items():
            try:
                pages.append(process_page(page_val, page_key))
            except Exception as e:
                logger.warning(f"ページ '{page_key}' の処理中にエラーが発生: {str(e)}")
                continue

        return {
            "pages": pages,
            "sections": pages  # 後方互換性のため
        }

    except Exception as e:
        logger.error(f"構造の正規化中にエラーが発生: {str(e)}")
        raise ValueError(f"構造の正規化に失敗しました: {str(e)}") 