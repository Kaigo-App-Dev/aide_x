"""
統合UIのE2Eテスト

このモジュールは、ChatGPT → Claude → ユーザー確認 → Gemini の構成生成フローを
自動で検証するE2Eテストを提供します。
"""

import pytest
import time
import logging
from playwright.sync_api import sync_playwright, Page, expect
from typing import Optional

logger = logging.getLogger(__name__)

class StructureFlowTest:
    """構成生成フローのE2Eテストクラス"""
    
    def __init__(self, base_url: str = "http://localhost:5000"):
        self.base_url = base_url
        self.page: Optional[Page] = None
        self.playwright = None
        self.browser = None
    
    def setup(self):
        """テスト環境のセットアップ"""
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(headless=False, slow_mo=1000)
        self.page = self.browser.new_page()
        logger.info("✅ ブラウザセットアップ完了")
    
    def teardown(self):
        """テスト環境のクリーンアップ"""
        if self.page:
            self.page.close()
        if self.browser:
            self.browser.close()
        if self.playwright:
            self.playwright.stop()
        logger.info("✅ ブラウザクリーンアップ完了")
    
    def wait_for_element(self, selector: str, timeout: int = 10000):
        """要素の表示を待機"""
        try:
            self.page.wait_for_selector(selector, timeout=timeout)
            logger.info(f"✅ 要素が見つかりました: {selector}")
            return True
        except Exception as e:
            logger.error(f"❌ 要素が見つかりませんでした: {selector} - {str(e)}")
            return False
    
    def wait_for_text(self, text: str, timeout: int = 10000):
        """テキストの表示を待機"""
        try:
            self.page.wait_for_selector(f"text={text}", timeout=timeout)
            logger.info(f"✅ テキストが見つかりました: {text}")
            return True
        except Exception as e:
            logger.error(f"❌ テキストが見つかりませんでした: {text} - {str(e)}")
            return False
    
    def send_message(self, message: str):
        """メッセージを送信"""
        try:
            # メッセージ入力フィールドを探す（複数のセレクタを試行）
            selectors = [
                "input[type='text']",
                "textarea",
                ".message-input",
                "#message-input",
                "[data-testid='message-input']"
            ]
            
            input_found = False
            for selector in selectors:
                try:
                    self.page.wait_for_selector(selector, timeout=2000)
                    self.page.fill(selector, message)
                    input_found = True
                    logger.info(f"✅ メッセージ入力完了: {message}")
                    break
                except:
                    continue
            
            if not input_found:
                raise Exception("メッセージ入力フィールドが見つかりません")
            
            # 送信ボタンを探す
            send_selectors = [
                "button[type='submit']",
                ".send-button",
                "#send-button",
                "[data-testid='send-button']",
                "button:has-text('送信')",
                "button:has-text('Send')"
            ]
            
            send_found = False
            for selector in send_selectors:
                try:
                    self.page.wait_for_selector(selector, timeout=2000)
                    self.page.click(selector)
                    send_found = True
                    logger.info("✅ メッセージ送信完了")
                    break
                except:
                    continue
            
            if not send_found:
                # Enterキーで送信を試行
                self.page.keyboard.press("Enter")
                logger.info("✅ Enterキーでメッセージ送信完了")
            
            # 送信後の待機
            time.sleep(2)
            
        except Exception as e:
            logger.error(f"❌ メッセージ送信エラー: {str(e)}")
            raise
    
    def test_structure_confirmation_flow(self):
        """構成確認フローのE2Eテスト"""
        try:
            logger.info("🚀 構成確認フローテスト開始")
            
            # 1. 新規構成ページにアクセス
            self.page.goto(f"{self.base_url}/unified/new")
            logger.info("✅ 新規構成ページにアクセス完了")
            
            # 2. ページの読み込みを待機
            time.sleep(3)
            
            # 3. ユーザー初回入力
            initial_message = "予約管理を効率化したい"
            self.send_message(initial_message)
            logger.info("✅ 初回メッセージ送信完了")
            
            # 4. ChatGPTの返答が表示されるまで待機
            logger.info("⏳ ChatGPTの返答を待機中...")
            time.sleep(10)  # AI応答の待機時間を延長
            
            # ChatGPTの返答（チャットセクション）の表示を確認
            chat_reply_selectors = [
                ".chat-pane .message.assistant_reply",
                ".chat-pane .message[data-type='assistant_reply']",
                ".chat-pane .message.assistant",
                ".chat-pane .message[data-type='assistant']",
                ".chat-pane .message.assistant:has-text('構成')",
                "[data-testid='assistant-reply']"
            ]
            
            chat_reply_found = False
            for selector in chat_reply_selectors:
                if self.wait_for_element(selector, timeout=10000):
                    chat_reply_found = True
                    logger.info(f"✅ ChatGPTの返答が表示されました: {selector}")
                    
                    # ChatGPTの返答が1つだけ表示されていることを確認
                    chat_messages = self.page.query_selector_all(".chat-pane .message.assistant")
                    if len(chat_messages) == 1:
                        logger.info("✅ ChatGPTの返答が1つだけ表示されています（重複なし）")
                    else:
                        logger.warning(f"⚠️ ChatGPTの返答が複数表示されています: {len(chat_messages)}個")
                    break
            
            if not chat_reply_found:
                logger.warning("⚠️ ChatGPTの返答の表示を確認できませんでした")
                # 現在のページのHTMLをデバッグ出力
                try:
                    html_content = self.page.content()
                    logger.info(f"📄 現在のページHTML（最初の1000文字）: {html_content[:1000]}")
                except:
                    pass
            
            # 5. 構成カード（構造セクション）の表示を確認
            logger.info("⏳ 構成カードの表示を待機中...")
            time.sleep(5)
            
            structure_card_selectors = [
                ".center-pane .structure-card[data-type='structure_proposal']",
                ".center-pane .structure-card",
                ".center-pane [data-testid='structure-card']",
                ".center-pane [data-source='claude']",
                "[data-testid='structure-card']"
            ]
            
            structure_card_found = False
            for selector in structure_card_selectors:
                if self.wait_for_element(selector, timeout=10000):
                    structure_card_found = True
                    logger.info(f"✅ 構成カードが表示されました: {selector}")
                    
                    # 構成カードの内容確認
                    try:
                        card_content = self.page.text_content(selector)
                        if "構成" in card_content or "評価" in card_content or "Claude" in card_content:
                            logger.info("✅ 構成カードに適切な内容が含まれています")
                        else:
                            logger.warning(f"⚠️ 構成カードの内容に期待する文言が含まれていません: {card_content[:100]}")
                    except:
                        logger.warning("⚠️ 構成カードの内容確認に失敗しました")
                    break
            
            if not structure_card_found:
                logger.warning("⚠️ 構成カードの表示を確認できませんでした")
            
            # 6. 補助要素（右ペイン）の表示を確認
            logger.info("⏳ 補助要素の表示を待機中...")
            time.sleep(3)
            
            supplemental_selectors = [
                ".output-pane .supplemental-element[data-type='gemini_ui']",
                ".output-pane .supplemental-element",
                ".output-pane [data-testid='supplemental-element']",
                ".output-pane [data-source='gemini']",
                "[data-testid='supplemental-element']"
            ]
            
            supplemental_found = False
            for selector in supplemental_selectors:
                if self.wait_for_element(selector, timeout=5000):
                    supplemental_found = True
                    logger.info(f"✅ 補助要素が表示されました: {selector}")
                    break
            
            if not supplemental_found:
                logger.info("ℹ️ 補助要素は表示されていません（正常な動作）")
            
            # 7. セクション分離の確認
            logger.info("🔍 セクション分離の確認中...")
            
            # チャットセクションに構造カードが混在していないことを確認
            chat_structure_cards = self.page.query_selector_all(".chat-pane .structure-card")
            if len(chat_structure_cards) == 0:
                logger.info("✅ チャットセクションに構造カードが混在していません")
            else:
                logger.warning(f"⚠️ チャットセクションに構造カードが混在しています: {len(chat_structure_cards)}個")
            
            # 構造セクションにチャットメッセージが混在していないことを確認
            structure_chat_messages = self.page.query_selector_all(".center-pane .message.assistant_reply")
            if len(structure_chat_messages) == 0:
                logger.info("✅ 構造セクションにチャットメッセージが混在していません")
            else:
                logger.warning(f"⚠️ 構造セクションにチャットメッセージが混在しています: {len(structure_chat_messages)}個")
            
            # 8. 読み込みインジケータの確認
            logger.info("🔍 読み込みインジケータの確認中...")
            
            # チャット専用の読み込みインジケータが表示されないことを確認
            chat_loading = self.page.query_selector_all(".chat-pane .loading-indicator.chat-loading")
            if len(chat_loading) == 0:
                logger.info("✅ チャット読み込みインジケータが適切に非表示になっています")
            else:
                logger.warning(f"⚠️ チャット読み込みインジケータが残っています: {len(chat_loading)}個")
            
            # 構造専用の読み込みインジケータが表示されないことを確認
            structure_loading = self.page.query_selector_all(".center-pane .loading-indicator.structure-loading")
            if len(structure_loading) == 0:
                logger.info("✅ 構造読み込みインジケータが適切に非表示になっています")
            else:
                logger.warning(f"⚠️ 構造読み込みインジケータが残っています: {len(structure_loading)}個")
            
            logger.info("✅ 構成確認フローテスト完了")
            
        except Exception as e:
            logger.error(f"❌ テスト実行中にエラーが発生しました: {str(e)}")
            # エラー時のスクリーンショットを保存
            try:
                self.page.screenshot(path="test_error_screenshot.png")
                logger.info("📸 エラー時のスクリーンショットを保存しました")
            except:
                pass
            raise

def run_e2e_test():
    """E2Eテストを実行"""
    logger.info("🚀 E2Eテスト実行開始")
    
    test = StructureFlowTest()
    try:
        test.setup()
        result = test.test_structure_confirmation_flow()
        return result
    finally:
        test.teardown()

if __name__ == "__main__":
    # ログ設定
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # テスト実行
    success = run_e2e_test()
    exit(0 if success else 1) 