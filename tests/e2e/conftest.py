"""
E2Eテスト用の設定ファイル
"""

import pytest
import logging
from playwright.sync_api import sync_playwright

logger = logging.getLogger(__name__)

@pytest.fixture(scope="session")
def browser_context_args():
    """ブラウザコンテキストの設定"""
    return {
        "viewport": {
            "width": 1920,
            "height": 1080,
        },
        "ignore_https_errors": True,
    }

@pytest.fixture(scope="session")
def base_url():
    """テスト対象のベースURL"""
    return "http://localhost:5000"

@pytest.fixture(scope="session")
def playwright():
    """Playwrightインスタンス"""
    with sync_playwright() as p:
        yield p

@pytest.fixture
def browser(playwright):
    """ブラウザインスタンス"""
    browser = playwright.chromium.launch(
        headless=False,  # デバッグ用にヘッドレスモードを無効化
        slow_mo=1000,    # 動作を遅くして確認しやすくする
    )
    yield browser
    browser.close()

@pytest.fixture
def page(browser):
    """ページインスタンス"""
    page = browser.new_page()
    yield page
    page.close() 