#!/usr/bin/env python3
"""
ChatGPTプロンプトと応答の詳細ログ確認テストスクリプト
"""

import sys
import os
import json
import logging
from datetime import datetime

# プロジェクトルートをパスに追加
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.llm.prompts import PromptManager
from src.llm.controller import AIController
from src.utils.files import extract_json_part

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(f'logs/chatgpt_test_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log', encoding='utf-8')
    ]
)

logger = logging.getLogger(__name__)

def test_chatgpt_structure_generation():
    """ChatGPTの構成生成をテスト"""
    
    print("=" * 80)
    print("🔍 ChatGPT構成生成テスト開始")
    print("=" * 80)
    
    # テスト用のユーザー入力
    test_inputs = [
        "ブログサイトの構成を作成してください",
        "ECサイトの構成を考えてください",
        "ポートフォリオサイトの構成を提案してください"
    ]
    
    try:
        # PromptManagerとAIControllerを初期化
        prompt_manager = PromptManager()
        from src.llm.prompts.templates import register_all_templates
        register_all_templates(prompt_manager)
        controller = AIController(prompt_manager)
        
        # ChatGPTプロバイダーを登録
        from src.llm.providers.chatgpt import ChatGPTProvider
        chatgpt_provider = ChatGPTProvider(prompt_manager=prompt_manager)
        controller.register_provider("chatgpt", chatgpt_provider)
        
        print("✅ PromptManagerとAIControllerの初期化完了")
        
        for i, user_input in enumerate(test_inputs, 1):
            print(f"\n{'='*60}")
            print(f"🧪 テストケース {i}: {user_input}")
            print(f"{'='*60}")
            
            # プロンプトテンプレートを取得
            prompt_template_str = prompt_manager.get("structure_from_input")
            if not isinstance(prompt_template_str, str):
                print(f"❌ structure_from_inputプロンプトが見つかりません")
                continue
            
            # プロンプトをフォーマット
            formatted_input = prompt_template_str.format(user_input=user_input)
            
            print("\n📝 ChatGPTプロンプト全文:")
            print("-" * 40)
            print(formatted_input)
            print("-" * 40)
            
            # ChatGPTに送信
            print(f"\n🤖 ChatGPTにリクエスト送信中...")
            ai_response_dict = controller._call("chatgpt", [{"role": "user", "content": formatted_input}])
            raw_response = ai_response_dict if isinstance(ai_response_dict, str) else str(ai_response_dict)
            
            print(f"\n📤 ChatGPT応答全文:")
            print("-" * 40)
            print(raw_response)
            print("-" * 40)
            print(f"📊 応答統計: 文字数={len(raw_response)}, 改行数={raw_response.count(chr(10))}")
            
            # 応答の特徴を分析
            print(f"\n🔍 応答分析:")
            if "```json" in raw_response:
                print("✅ JSONコードブロックが含まれています")
            elif "{" in raw_response and "}" in raw_response:
                print("✅ JSONオブジェクトが含まれています")
            else:
                print("⚠️ JSONが含まれていません")
            
            if "構成" in raw_response:
                print("✅ 「構成」キーワードが含まれています")
            if "JSON" in raw_response:
                print("✅ 「JSON」キーワードが含まれています")
            
            # extract_json_partでJSON抽出をテスト
            print(f"\n🔧 extract_json_partテスト:")
            try:
                extracted_json = extract_json_part(raw_response)
                print(f"結果型: {type(extracted_json)}")
                
                if isinstance(extracted_json, dict):
                    if 'error' in extracted_json:
                        print(f"❌ エラー: {extracted_json['error']}")
                        if 'reason' in extracted_json:
                            print(f"理由: {extracted_json['reason']}")
                        if 'original_text' in extracted_json:
                            print(f"元テキスト: {extracted_json['original_text'][:200]}...")
                        if 'extracted_json_string' in extracted_json:
                            print(f"抽出されたJSON文字列: {extracted_json['extracted_json_string']}")
                    else:
                        print(f"✅ 抽出成功")
                        print(f"抽出されたキー: {list(extracted_json.keys())}")
                        print(f"抽出された内容: {json.dumps(extracted_json, ensure_ascii=False, indent=2)[:500]}...")
                else:
                    print(f"⚠️ 予期しない結果型: {extracted_json}")
                    
            except Exception as e:
                print(f"❌ extract_json_partでエラー: {e}")
                import traceback
                traceback.print_exc()
            
            print(f"\n{'='*60}")
            print(f"テストケース {i} 完了")
            print(f"{'='*60}")
    
    except Exception as e:
        print(f"❌ テスト実行中にエラーが発生: {e}")
        import traceback
        traceback.print_exc()

def test_specific_structure(structure_id):
    """特定のstructure IDのデータをテスト"""
    
    print(f"\n{'='*80}")
    print(f"🔍 特定structureテスト: {structure_id}")
    print(f"{'='*80}")
    
    try:
        # データファイルを読み込み
        data_file = f"data/{structure_id}.json"
        if not os.path.exists(data_file):
            print(f"❌ データファイルが見つかりません: {data_file}")
            return
        
        with open(data_file, 'r', encoding='utf-8') as f:
            structure_data = json.load(f)
        
        print(f"✅ データファイル読み込み完了")
        print(f"📋 structureキー: {list(structure_data.keys())}")
        
        # messagesからChatGPTの応答を探す
        messages = structure_data.get('messages', [])
        chatgpt_messages = [msg for msg in messages if msg.get('source') == 'chatgpt']
        
        if not chatgpt_messages:
            print("⚠️ ChatGPTのメッセージが見つかりません")
            return
        
        print(f"✅ ChatGPTメッセージ数: {len(chatgpt_messages)}")
        
        for i, msg in enumerate(chatgpt_messages, 1):
            print(f"\n📝 ChatGPTメッセージ {i}:")
            print(f"タイプ: {msg.get('type', 'N/A')}")
            print(f"内容: {msg.get('content', 'N/A')[:200]}...")
            
            # extract_json_partでテスト
            content = msg.get('content', '')
            if content:
                print(f"\n🔧 extract_json_partテスト:")
                try:
                    extracted_json = extract_json_part(content)
                    print(f"結果型: {type(extracted_json)}")
                    
                    if isinstance(extracted_json, dict):
                        if 'error' in extracted_json:
                            print(f"❌ エラー: {extracted_json['error']}")
                            if 'reason' in extracted_json:
                                print(f"理由: {extracted_json['reason']}")
                        else:
                            print(f"✅ 抽出成功")
                            print(f"抽出されたキー: {list(extracted_json.keys())}")
                except Exception as e:
                    print(f"❌ extract_json_partでエラー: {e}")
    
    except Exception as e:
        print(f"❌ 特定structureテストでエラー: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("🚀 ChatGPTログテスト開始")
    
    # ログディレクトリを作成
    os.makedirs('logs', exist_ok=True)
    
    # 基本テスト
    test_chatgpt_structure_generation()
    
    # 特定のstructure IDをテスト（コメントアウトを外して使用）
    # test_specific_structure("eeab3b98-e029-4650-b207-576ba1e47007")
    
    print("\n✅ テスト完了") 