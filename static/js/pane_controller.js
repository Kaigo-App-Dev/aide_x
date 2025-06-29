/**
 * 段階的ペイン制御機能
 * 3ペイン構成の自動制御とユーザー手動制御を統合
 */

class PaneController {
    constructor() {
        console.log('🎯 PaneController初期化開始');
        
        // ペイン制御の状態管理
        this.paneControlState = {
            isInitialAccess: true,        // 初期アクセスフラグ
            isStructureGenerated: false,  // 構成生成フラグ
            isStructureSaved: false,      // 構成保存フラグ
            isCardClicked: false          // カードクリックフラグ
        };
        
        // 初期化
        this.init();
        
        console.log('✅ PaneController初期化完了');
    }

    // 初期化
    init() {
        console.log('🎯 PaneController.init() 開始');
        
        // 初期状態の判定
        this.determineInitialState();
        
        // 初期レイアウトの設定
        this.setInitialLayout();
        
        // イベントリスナーの設定
        this.setupEventListeners();
        
        console.log('✅ PaneController.init() 完了');
    }

    // 初期状態の判定
    determineInitialState() {
        console.log('🎯 初期状態判定開始');
        
        const hasGeminiOutput = this.checkGeminiOutputExists();
        const hasStructureData = !!window.structureData;
        const savedState = localStorage.getItem('aide_x_pane_state');
        
        if (savedState) {
            try {
                const parsedState = JSON.parse(savedState);
                this.paneControlState = { ...this.paneControlState, ...parsedState };
                console.log('📦 保存された状態を復元:', parsedState);
            } catch (error) {
                console.warn('⚠️ 保存された状態の復元に失敗:', error);
            }
        }
        
        // 状態の自動判定
        if (hasGeminiOutput && !this.paneControlState.isStructureSaved) {
            this.paneControlState.isStructureGenerated = true;
            this.paneControlState.isInitialAccess = false;
        }
        
        console.log('📊 初期状態:', this.paneControlState);
        this.savePaneState();
    }

    // 初期レイアウトの設定
    setInitialLayout() {
        console.log('🎯 初期レイアウト設定開始');
        
        // 構成データの存在確認
        const hasStructureData = !!window.structureData;
        console.log('📊 構成データ存在確認:', hasStructureData);
        
        // 構成があれば必ず3ペイン表示
        if (hasStructureData) {
            console.log('🔄 構成データあり - 3ペイン強制表示開始');
            this.forceAllPanesVisibility();
        } else if (this.paneControlState.isInitialAccess) {
            this.setInitialAccessLayout();
        } else if (this.paneControlState.isStructureGenerated) {
            this.setStructureGeneratedLayout();
        } else if (this.paneControlState.isStructureSaved) {
            this.setStructureSavedLayout();
        } else if (this.paneControlState.isCardClicked) {
            this.setCardClickedLayout();
        } else {
            this.setDefaultLayout();
        }
        
        console.log('✅ 初期レイアウト設定完了');
    }

    // 全ペインの強制表示（3分割レイアウト確立）
    forceAllPanesVisibility() {
        console.log('🔧 全ペイン強制表示開始');
        
        const chatPane = document.querySelector('.chat-pane');
        const centerPane = document.querySelector('.center-pane');
        const rightPane = document.querySelector('.right-pane');
        const mainContainer = document.querySelector('.main-container');
        
        console.log('📋 ペイン要素取得状況:', {
            chatPane: !!chatPane,
            centerPane: !!centerPane,
            rightPane: !!rightPane,
            mainContainer: !!mainContainer
        });
        
        // メインコンテナの設定
        if (mainContainer) {
            mainContainer.style.display = 'flex';
            mainContainer.style.flexDirection = 'row';
            mainContainer.style.width = '100%';
            mainContainer.style.height = '100%';
            mainContainer.style.alignItems = 'stretch';
            mainContainer.style.justifyContent = 'space-between';
            console.log('✅ メインコンテナ設定完了');
        }
        
        // チャットペインの強制表示
        if (chatPane) {
            chatPane.classList.remove('collapsed');
            chatPane.style.display = 'flex';
            chatPane.style.visibility = 'visible';
            chatPane.style.flex = '1 1 33.3%';
            chatPane.style.width = 'auto';
            chatPane.style.opacity = '1';
            chatPane.style.minWidth = '20%';
            chatPane.style.maxWidth = '50%';
            console.log('✅ チャットペイン強制表示完了');
        }
        
        // 中央ペインの強制表示
        if (centerPane) {
            centerPane.classList.remove('collapsed');
            centerPane.style.display = 'flex';
            centerPane.style.visibility = 'visible';
            centerPane.style.flex = '1 1 33.3%';
            centerPane.style.width = 'auto';
            centerPane.style.opacity = '1';
            centerPane.style.minWidth = '20%';
            centerPane.style.maxWidth = '50%';
            console.log('✅ 中央ペイン強制表示完了');
        }
        
        // 右ペインの強制表示
        if (rightPane) {
            rightPane.classList.remove('collapsed');
            rightPane.style.display = 'flex';
            rightPane.style.visibility = 'visible';
            rightPane.style.flex = '1 1 33.3%';
            rightPane.style.width = 'auto';
            rightPane.style.opacity = '1';
            rightPane.style.minWidth = '20%';
            rightPane.style.maxWidth = '50%';
            console.log('✅ 右ペイン強制表示完了');
        }
        
        // 設定後の状態確認
        setTimeout(() => {
            console.log('🔍 全ペイン強制表示後の状態確認:');
            
            [chatPane, centerPane, rightPane].forEach((pane, index) => {
                if (pane) {
                    const computedStyle = window.getComputedStyle(pane);
                    const paneName = ['チャット', '中央', '右'][index];
                    console.log(`📊 ${paneName}ペイン:`, {
                        display: computedStyle.display,
                        visibility: computedStyle.visibility,
                        flex: computedStyle.flex,
                        width: computedStyle.width,
                        offsetWidth: pane.offsetWidth,
                        isCollapsed: pane.classList.contains('collapsed')
                    });
                }
            });
            
            console.log('✅ 全ペイン強制表示完了');
        }, 50);
    }

    // イベントリスナーの設定
    setupEventListeners() {
        console.log('🎯 イベントリスナー設定開始');
        
        // 構成生成イベント
        document.addEventListener('structureGenerated', () => {
            console.log('🎯 構成生成イベント受信');
            this.onStructureGenerated();
        });
        
        // 構成保存イベント
        document.addEventListener('structureSaved', () => {
            console.log('🎯 構成保存イベント受信');
            this.onStructureSaved();
        });
        
        // カードクリックイベント
        document.addEventListener('cardClicked', () => {
            console.log('🎯 カードクリックイベント受信');
            this.onCardClicked();
        });
        
        console.log('✅ イベントリスナー設定完了');
    }

    // 段階的ペイン制御：構成生成時
    onStructureGenerated() {
        console.log('🎯 構成生成時のペイン制御開始');
        console.log('📅 構成生成時刻:', new Date().toISOString());
        
        this.paneControlState.isStructureGenerated = true;
        this.paneControlState.isInitialAccess = false;
        
        // 右ペインを自動表示
        this.autoShowRightPane();
        
        // 左ペインは維持（会話継続のため）
        this.ensureChatPaneVisible();
        
        this.savePaneState();
        console.log('✅ 構成生成時のペイン制御完了');
        this.logPaneControlState();
    }

    // 段階的ペイン制御：構成保存時
    onStructureSaved() {
        console.log('🎯 構成保存時のペイン制御開始');
        console.log('📅 構成保存時刻:', new Date().toISOString());
        
        this.paneControlState.isStructureSaved = true;
        this.paneControlState.isStructureGenerated = false;
        
        // 左ペインを自動非表示
        this.autoCollapseChatPane();
        
        // 右ペインは維持（UI確認のため）
        this.ensureRightPaneVisible();
        
        this.savePaneState();
        console.log('✅ 構成保存時のペイン制御完了');
        this.logPaneControlState();
    }

    // 段階的ペイン制御：カードクリック時
    onCardClicked() {
        console.log('🎯 カードクリック時のペイン制御開始');
        console.log('📅 カードクリック時刻:', new Date().toISOString());
        
        this.paneControlState.isCardClicked = true;
        this.paneControlState.isStructureSaved = false;
        
        // 左ペインを再表示
        this.autoExpandChatPane();
        
        // 右ペインに対応UIを表示
        this.ensureRightPaneVisible();
        
        this.savePaneState();
        console.log('✅ カードクリック時のペイン制御完了');
        this.logPaneControlState();
    }

    // 初期アクセス時のレイアウト設定
    setInitialAccessLayout() {
        console.log('🎯 初期アクセス時のレイアウト設定開始');
        
        const chatPane = document.querySelector('.chat-pane');
        const centerPane = document.querySelector('.center-pane');
        const rightPane = document.querySelector('.right-pane');
        const mainContainer = document.querySelector('.main-container');
        
        // メインコンテナの設定
        if (mainContainer) {
            mainContainer.style.display = 'flex';
            mainContainer.style.flexDirection = 'row';
            mainContainer.style.width = '100%';
            mainContainer.style.height = '100%';
        }
        
        // 左ペイン（チャット）：表示
        if (chatPane) {
            chatPane.classList.remove('collapsed');
            chatPane.style.display = 'flex';
            chatPane.style.visibility = 'visible';
            chatPane.style.opacity = '1';
            chatPane.style.flex = '1 1 40%';
            chatPane.style.minWidth = '300px';
            chatPane.style.maxWidth = '50%';
        }
        
        // 中央ペイン：表示
        if (centerPane) {
            centerPane.classList.remove('collapsed');
            centerPane.style.display = 'flex';
            centerPane.style.visibility = 'visible';
            centerPane.style.opacity = '1';
            centerPane.style.flex = '1 1 60%';
            centerPane.style.minWidth = '300px';
        }
        
        // 右ペイン：初期は非表示（構成生成後に表示）
        if (rightPane) {
            rightPane.classList.add('collapsed');
            rightPane.style.display = 'none';
            rightPane.style.visibility = 'hidden';
            rightPane.style.opacity = '0';
            rightPane.style.flex = '0 0 0%';
            rightPane.style.minWidth = '0';
        }
        
        console.log('✅ 初期アクセス時のレイアウト設定完了');
    }

    // 構成生成後のレイアウト設定
    setStructureGeneratedLayout() {
        console.log('🎯 構成生成後のレイアウト設定開始');
        
        const chatPane = document.querySelector('.chat-pane');
        const centerPane = document.querySelector('.center-pane');
        const rightPane = document.querySelector('.right-pane');
        
        // 左ペイン：維持
        if (chatPane) {
            chatPane.classList.remove('collapsed');
            chatPane.style.display = 'flex';
            chatPane.style.visibility = 'visible';
            chatPane.style.opacity = '1';
            chatPane.style.flex = '1 1 30%';
            chatPane.style.minWidth = '250px';
        }
        
        // 中央ペイン：調整
        if (centerPane) {
            centerPane.classList.remove('collapsed');
            centerPane.style.display = 'flex';
            centerPane.style.visibility = 'visible';
            centerPane.style.opacity = '1';
            centerPane.style.flex = '1 1 35%';
            centerPane.style.minWidth = '350px';
        }
        
        // 右ペイン：表示
        if (rightPane) {
            rightPane.classList.remove('collapsed');
            rightPane.style.display = 'flex';
            rightPane.style.visibility = 'visible';
            rightPane.style.opacity = '1';
            rightPane.style.flex = '1 1 35%';
            rightPane.style.minWidth = '300px';
            
            // アニメーション効果
            this.addFadeInAnimation(rightPane);
        }
        
        console.log('✅ 構成生成後のレイアウト設定完了');
    }

    // 構成保存後のレイアウト設定
    setStructureSavedLayout() {
        console.log('🎯 構成保存後のレイアウト設定開始');
        
        const chatPane = document.querySelector('.chat-pane');
        const centerPane = document.querySelector('.center-pane');
        const rightPane = document.querySelector('.right-pane');
        
        // 左ペイン：非表示
        if (chatPane) {
            chatPane.classList.add('collapsed');
            chatPane.style.flex = '0 0 36px';
            chatPane.style.minWidth = '36px';
            chatPane.style.maxWidth = '36px';
        }
        
        // 中央ペイン：拡大
        if (centerPane) {
            centerPane.classList.remove('collapsed');
            centerPane.style.display = 'flex';
            centerPane.style.visibility = 'visible';
            centerPane.style.opacity = '1';
            centerPane.style.flex = '1 1 50%';
            centerPane.style.minWidth = '400px';
        }
        
        // 右ペイン：維持
        if (rightPane) {
            rightPane.classList.remove('collapsed');
            rightPane.style.display = 'flex';
            rightPane.style.visibility = 'visible';
            rightPane.style.opacity = '1';
            rightPane.style.flex = '1 1 50%';
            rightPane.style.minWidth = '350px';
        }
        
        console.log('✅ 構成保存後のレイアウト設定完了');
    }

    // カードクリック後のレイアウト設定
    setCardClickedLayout() {
        console.log('🎯 カードクリック後のレイアウト設定開始');
        
        const chatPane = document.querySelector('.chat-pane');
        const centerPane = document.querySelector('.center-pane');
        const rightPane = document.querySelector('.right-pane');
        
        // 左ペイン：再表示
        if (chatPane) {
            chatPane.classList.remove('collapsed');
            chatPane.style.display = 'flex';
            chatPane.style.visibility = 'visible';
            chatPane.style.opacity = '1';
            chatPane.style.flex = '1 1 30%';
            chatPane.style.minWidth = '250px';
            
            // アニメーション効果
            this.addFadeInAnimation(chatPane);
        }
        
        // 中央ペイン：調整
        if (centerPane) {
            centerPane.classList.remove('collapsed');
            centerPane.style.display = 'flex';
            centerPane.style.visibility = 'visible';
            centerPane.style.opacity = '1';
            centerPane.style.flex = '1 1 35%';
            centerPane.style.minWidth = '350px';
        }
        
        // 右ペイン：維持
        if (rightPane) {
            rightPane.classList.remove('collapsed');
            rightPane.style.display = 'flex';
            rightPane.style.visibility = 'visible';
            rightPane.style.opacity = '1';
            rightPane.style.flex = '1 1 35%';
            rightPane.style.minWidth = '300px';
        }
        
        console.log('✅ カードクリック後のレイアウト設定完了');
    }

    // デフォルトレイアウト設定
    setDefaultLayout() {
        console.log('🎯 デフォルトレイアウト設定開始');
        
        const chatPane = document.querySelector('.chat-pane');
        const centerPane = document.querySelector('.center-pane');
        const rightPane = document.querySelector('.right-pane');
        
        // 全ペイン表示
        [chatPane, centerPane, rightPane].forEach((pane, index) => {
            if (pane) {
                pane.classList.remove('collapsed');
                pane.style.display = 'flex';
                pane.style.visibility = 'visible';
                pane.style.opacity = '1';
                pane.style.flex = '1 1 33.3%';
                pane.style.minWidth = '250px';
            }
        });
        
        console.log('✅ デフォルトレイアウト設定完了');
    }

    // 右ペイン自動表示
    autoShowRightPane() {
        console.log('🎨 右ペイン自動表示開始');
        
        const rightPane = document.querySelector('.right-pane');
        if (rightPane) {
            rightPane.classList.remove('collapsed');
            rightPane.style.display = 'flex';
            rightPane.style.visibility = 'visible';
            rightPane.style.opacity = '1';
            rightPane.style.flex = '1 1 33.3%';
            rightPane.style.minWidth = '300px';
            
            // アニメーション効果
            this.addFadeInAnimation(rightPane);
            
            console.log('✅ 右ペイン自動表示完了');
        } else {
            console.warn('⚠️ 右ペインが見つかりません');
        }
    }

    // チャットペイン自動非表示
    autoCollapseChatPane() {
        console.log('🎨 チャットペイン自動非表示開始');
        
        const chatPane = document.querySelector('.chat-pane');
        if (chatPane) {
            chatPane.classList.add('collapsed');
            chatPane.style.flex = '0 0 36px';
            chatPane.style.minWidth = '36px';
            chatPane.style.maxWidth = '36px';
            
            console.log('✅ チャットペイン自動非表示完了');
        } else {
            console.warn('⚠️ チャットペインが見つかりません');
        }
    }

    // チャットペイン自動再表示
    autoExpandChatPane() {
        console.log('🎨 チャットペイン自動再表示開始');
        
        const chatPane = document.querySelector('.chat-pane');
        if (chatPane) {
            chatPane.classList.remove('collapsed');
            chatPane.style.flex = '1 1 33.3%';
            chatPane.style.minWidth = '250px';
            chatPane.style.maxWidth = '50%';
            
            // アニメーション効果
            this.addFadeInAnimation(chatPane);
            
            console.log('✅ チャットペイン自動再表示完了');
        } else {
            console.warn('⚠️ チャットペインが見つかりません');
        }
    }

    // チャットペイン表示確保
    ensureChatPaneVisible() {
        console.log('🎨 チャットペイン表示確保開始');
        
        const chatPane = document.querySelector('.chat-pane');
        if (chatPane && chatPane.classList.contains('collapsed')) {
            this.autoExpandChatPane();
        }
    }

    // 右ペイン表示確保
    ensureRightPaneVisible() {
        console.log('🎨 右ペイン表示確保開始');
        
        const rightPane = document.querySelector('.right-pane');
        if (rightPane && rightPane.classList.contains('collapsed')) {
            this.autoShowRightPane();
        }
    }

    // Gemini出力の存在確認
    checkGeminiOutputExists() {
        if (window.structureData && window.structureData.gemini_output) {
            return true;
        }
        
        const geminiOutputElement = document.querySelector('#gemini-output');
        if (geminiOutputElement && geminiOutputElement.innerHTML.trim()) {
            return true;
        }
        
        return false;
    }

    // ペイン制御状態のログ出力
    logPaneControlState() {
        console.log('📊 ペイン制御状態:', {
            isInitialAccess: this.paneControlState.isInitialAccess,
            isStructureGenerated: this.paneControlState.isStructureGenerated,
            isStructureSaved: this.paneControlState.isStructureSaved,
            isCardClicked: this.paneControlState.isCardClicked,
            timestamp: new Date().toISOString()
        });
    }

    // フェードインアニメーション追加
    addFadeInAnimation(element) {
        element.style.opacity = '0';
        element.style.transform = 'translateX(20px)';
        
        setTimeout(() => {
            element.style.transition = 'opacity 0.3s ease, transform 0.3s ease';
            element.style.opacity = '1';
            element.style.transform = 'translateX(0)';
        }, 50);
    }

    // ペイン状態の保存
    savePaneState() {
        try {
            localStorage.setItem('aide_x_pane_state', JSON.stringify(this.paneControlState));
            console.log('💾 ペイン状態を保存:', this.paneControlState);
        } catch (error) {
            console.warn('⚠️ ペイン状態の保存に失敗:', error);
        }
    }

    // 手動制御メソッド
    togglePane(paneType) {
        console.log(`🎨 ${paneType}ペイン手動切り替え開始`);
        
        const targetElement = document.querySelector(`.${paneType}-pane`);
        if (!targetElement) {
            console.warn(`⚠️ ${paneType}ペインが見つかりません`);
            return;
        }
        
        if (targetElement.classList.contains('collapsed')) {
            targetElement.classList.remove('collapsed');
            this.addFadeInAnimation(targetElement);
        } else {
            targetElement.classList.add('collapsed');
        }
        
        console.log(`✅ ${paneType}ペイン手動切り替え完了`);
    }

    // 全ペイン展開
    expandAllPanes() {
        console.log('🎨 全ペイン手動展開開始');
        
        ['chat', 'center', 'right'].forEach(paneType => {
            this.togglePane(paneType);
        });
        
        console.log('✅ 全ペイン手動展開完了');
    }
}

// グローバルインスタンスの作成
window.paneController = new PaneController();

// イベント発火用のヘルパー関数
window.triggerStructureGenerated = () => {
    document.dispatchEvent(new CustomEvent('structureGenerated'));
};

window.triggerStructureSaved = () => {
    document.dispatchEvent(new CustomEvent('structureSaved'));
};

window.triggerCardClicked = () => {
    document.dispatchEvent(new CustomEvent('cardClicked'));
};

console.log('🎯 PaneController読み込み完了'); 