/**
 * レイアウト管理・UI制御（再構築版）
 * 3ペイン構成（左：チャット、中央：構成、右：Gemini補完）の制御
 */

class LayoutManager {
    constructor() {
        console.log('🎨 LayoutManager初期化');
        this.isResizing = false;
        this.currentResizer = null;
        this.minPaneWidth = 200;
        this.collapseThreshold = 150;
        this.storageKey = 'aide_x_pane_layout';
        
        // ペイン制御の状態管理
        this.paneControlState = {
            isInitialAccess: true,
            isStructureGenerated: false,
            isStructureSaved: false,
            isCardClicked: false
        };
        
        // localStorage用のキー
        this.paneStateKeys = {
            chat: 'left-pane-collapsed',
            center: 'center-pane-collapsed', 
            gemini: 'gemini-pane-collapsed'
        };
        
        this.init();
    }

    // 初期化
    init() {
        console.log('🎨 LayoutManager初期化開始');
        
        try {
            // DOM要素の存在確認
            this.debugPaneElements();
            
            // localStorageからペイン状態を復元
            this.restorePaneStates();
            
            // ペイン切り替えの初期化
            this.initPaneToggles();
            
            // ペインリサイザーの初期化
            this.initPaneResizers();
            
            // 保存されたレイアウトの復元
            this.restoreLayout();
            
            // 初期レイアウトの設定
            this.initializePaneLayout();
            
            // ウィンドウリサイズ対応
            this.initWindowResizeHandler();
            
            // ショートカットキーの初期化
            this.initKeyboardShortcuts();
            
            console.log('✅ LayoutManager初期化完了');
            
        } catch (error) {
            console.error('❌ LayoutManager初期化エラー:', error);
        }
    }

    // ショートカットキーの初期化
    initKeyboardShortcuts() {
        console.log('⌨️ ショートカットキー初期化開始');
        
        document.addEventListener('keydown', (e) => {
            // Ctrl+1: 左ペイン（チャット）切り替え
            if (e.ctrlKey && e.key === '1') {
                e.preventDefault();
                console.log('⌨️ Ctrl+1: 左ペイン切り替え');
                this.togglePane('chat');
            }
            
            // Ctrl+2: 中央ペイン切り替え
            if (e.ctrlKey && e.key === '2') {
                e.preventDefault();
                console.log('⌨️ Ctrl+2: 中央ペイン切り替え');
                this.togglePane('center');
            }
            
            // Ctrl+3: Geminiペイン切り替え
            if (e.ctrlKey && e.key === '3') {
                e.preventDefault();
                console.log('⌨️ Ctrl+3: Geminiペイン切り替え');
                this.togglePane('gemini');
            }
            
            // Ctrl+0: 全ペイン展開
            if (e.ctrlKey && e.key === '0') {
                e.preventDefault();
                console.log('⌨️ Ctrl+0: 全ペイン展開');
                this.expandAllPanes();
            }
        });
        
        console.log('✅ ショートカットキー初期化完了');
    }

    // ペイン切り替え（トグル）
    togglePane(paneType) {
        console.log(`🎨 ${paneType}ペイン切り替え開始`);
        
        const targetElement = document.querySelector(`#${paneType}-pane`);
        if (!targetElement) {
            console.warn(`⚠️ ${paneType}ペインが見つかりません`);
            return;
        }
        
        const isCollapsed = targetElement.classList.contains('collapsed');
        console.log(`🔍 ${paneType}ペイン状態:`, {
            isCollapsed: isCollapsed,
            display: window.getComputedStyle(targetElement).display,
            offsetWidth: targetElement.offsetWidth
        });
        
        if (isCollapsed) {
            this.expandPane(paneType);
        } else {
            this.collapsePane(paneType);
        }
        
        // localStorageに状態を保存
        this.savePaneStates();
    }

    // 全ペイン展開
    expandAllPanes() {
        console.log('🎨 全ペイン展開開始');
        
        ['chat', 'center', 'gemini'].forEach(paneType => {
            this.expandPane(paneType);
        });
        
        console.log('✅ 全ペイン展開完了');
    }

    // ペイン展開
    expandPane(paneType) {
        const pane = document.querySelector(`#${paneType}-pane`);
        if (!pane) return;
        
        pane.classList.remove('collapsed');
        pane.style.display = 'flex';
        pane.style.visibility = 'visible';
        pane.style.opacity = '1';
        
        // 最小幅を確保
        if (pane.offsetWidth < this.minPaneWidth) {
            pane.style.width = `${this.minPaneWidth}px`;
        }
        
        console.log(`✅ ${paneType}ペイン展開完了`);
    }

    // ペイン折りたたみ
    collapsePane(paneType) {
        const pane = document.querySelector(`#${paneType}-pane`);
        if (!pane) return;
        
        pane.classList.add('collapsed');
        pane.style.width = '0';
        pane.style.overflow = 'hidden';
        
        console.log(`✅ ${paneType}ペイン折りたたみ完了`);
    }

    // ペインリサイザーの初期化
    initPaneResizers() {
        console.log('🔧 ペインリサイザー初期化開始');
        
        const resizers = document.querySelectorAll('.pane-resizer');
        resizers.forEach(resizer => {
            resizer.addEventListener('mousedown', (e) => {
                this.startResize(e, resizer);
            });
        });
        
        console.log('✅ ペインリサイザー初期化完了');
    }

    // リサイズ開始
    startResize(e, resizer) {
        e.preventDefault();
        this.isResizing = true;
        this.currentResizer = resizer;
        
        const handleMouseMove = (e) => {
            if (!this.isResizing) return;
            
            const container = document.querySelector('.main-container');
            const containerRect = container.getBoundingClientRect();
            const mouseX = e.clientX - containerRect.left;
            
            // リサイズ処理
            this.handleResize(mouseX, resizer);
        };
        
        const handleMouseUp = () => {
            this.isResizing = false;
            this.currentResizer = null;
            document.removeEventListener('mousemove', handleMouseMove);
            document.removeEventListener('mouseup', handleMouseUp);
        };
        
        document.addEventListener('mousemove', handleMouseMove);
        document.addEventListener('mouseup', handleMouseUp);
    }

    // リサイズ処理
    handleResize(mouseX, resizer) {
        const resizeTarget = resizer.getAttribute('data-resize');
        const targetPane = document.getElementById(resizeTarget);
        
        if (!targetPane) return;
        
        const containerWidth = document.querySelector('.main-container').offsetWidth;
        const newWidth = Math.max(this.minPaneWidth, Math.min(mouseX, containerWidth * 0.5));
        
        targetPane.style.width = `${newWidth}px`;
    }

    // ペイン切り替えボタンの初期化
    initPaneToggles() {
        console.log('🎨 ペイン切り替えボタン初期化開始');
        
        const toggleButtons = document.querySelectorAll('.pane-toggle');
        toggleButtons.forEach(button => {
            button.addEventListener('click', (e) => {
                e.preventDefault();
                const paneType = this.getPaneTypeFromButton(button);
                if (paneType) {
                    this.togglePane(paneType);
                }
            });
        });
        
        console.log('✅ ペイン切り替えボタン初期化完了');
    }

    // ボタンからペインタイプを取得
    getPaneTypeFromButton(button) {
        const controls = button.getAttribute('aria-controls');
        if (controls === 'chat-pane') return 'chat';
        if (controls === 'center-pane') return 'center';
        if (controls === 'gemini-pane') return 'gemini';
        return null;
    }

    // ウィンドウリサイズ対応
    initWindowResizeHandler() {
        window.addEventListener('resize', () => {
            this.handleWindowResize();
        });
    }

    // ウィンドウリサイズ処理
    handleWindowResize() {
        const containerWidth = document.querySelector('.main-container').offsetWidth;
        
        // コンテナが狭い場合は自動的にペインを折りたたみ
        if (containerWidth < 800) {
            this.autoCollapsePanes(containerWidth);
        }
    }

    // 自動ペイン折りたたみ
    autoCollapsePanes(containerWidth) {
        if (containerWidth < 600) {
            // チャットペインを折りたたみ
            this.collapsePane('chat');
        }
    }

    // 初期レイアウト設定
    initializePaneLayout() {
        console.log('🎨 初期レイアウト設定開始');
        
        const mainContainer = document.querySelector('.main-container');
        if (!mainContainer) {
            console.warn('⚠️ メインコンテナが見つかりません');
            return;
        }
        
        // メインコンテナのレイアウト設定
        mainContainer.style.display = 'flex';
        mainContainer.style.flexDirection = 'row';
        mainContainer.style.width = '100%';
        mainContainer.style.height = '100%';
        
        // 各ペインの初期設定
        const panes = ['chat', 'center', 'gemini'];
        panes.forEach(paneType => {
            const pane = document.getElementById(`${paneType}-pane`);
            if (pane) {
                pane.style.flex = '1 1 33.3%';
                pane.style.minWidth = '20%';
                pane.style.maxWidth = '50%';
                pane.style.display = 'flex';
                pane.style.flexDirection = 'column';
            }
        });
        
        console.log('✅ 初期レイアウト設定完了');
    }

    // ペイン状態の復元
    restorePaneStates() {
        console.log('🔄 ペイン状態復元開始');
        
        Object.entries(this.paneStateKeys).forEach(([paneType, key]) => {
            const isCollapsed = localStorage.getItem(key) === 'true';
            if (isCollapsed) {
                this.collapsePane(paneType);
            }
        });
        
        console.log('✅ ペイン状態復元完了');
    }

    // ペイン状態の保存
    savePaneStates() {
        Object.entries(this.paneStateKeys).forEach(([paneType, key]) => {
            const pane = document.getElementById(`${paneType}-pane`);
            if (pane) {
                const isCollapsed = pane.classList.contains('collapsed');
                localStorage.setItem(key, isCollapsed.toString());
            }
        });
    }

    // レイアウトの保存
    saveLayout() {
        const layout = {
            panes: {}
        };
        
        ['chat', 'center', 'gemini'].forEach(paneType => {
            const pane = document.getElementById(`${paneType}-pane`);
            if (pane) {
                layout.panes[paneType] = {
                    width: pane.offsetWidth,
                    collapsed: pane.classList.contains('collapsed')
                };
            }
        });
        
        localStorage.setItem(this.storageKey, JSON.stringify(layout));
    }

    // レイアウトの復元
    restoreLayout() {
        const savedLayout = localStorage.getItem(this.storageKey);
        if (!savedLayout) return;
        
        try {
            const layout = JSON.parse(savedLayout);
            
            Object.entries(layout.panes || {}).forEach(([paneType, paneData]) => {
                const pane = document.getElementById(`${paneType}-pane`);
                if (pane && paneData.width) {
                    pane.style.width = `${paneData.width}px`;
                }
            });
            
            console.log('✅ レイアウト復元完了');
        } catch (error) {
            console.error('❌ レイアウト復元エラー:', error);
        }
    }

    // デバッグ用：ペイン要素の確認
    debugPaneElements() {
        console.log('🔍 ペイン要素確認:', {
            mainContainer: !!document.querySelector('.main-container'),
            chatPane: !!document.getElementById('chat-pane'),
            centerPane: !!document.getElementById('center-pane'),
            geminiPane: !!document.getElementById('gemini-pane'),
            resizers: document.querySelectorAll('.pane-resizer').length
        });
    }

    // UI有効化
    enableUI() {
        console.log('🔓 UI有効化開始');
        
        // ローディングオーバーレイを完全に非表示
        this.hideLoadingOverlay();
        
        // メインコンテナの表示確認
        const mainContainer = document.querySelector('.main-container');
        if (mainContainer) {
            mainContainer.style.display = 'flex';
            mainContainer.style.visibility = 'visible';
            mainContainer.style.opacity = '1';
            mainContainer.style.pointerEvents = 'auto';
            console.log('✅ メインコンテナ有効化完了');
        }
        
        // 全ペインを有効化
        ['chat', 'center', 'gemini'].forEach(paneType => {
            const pane = document.getElementById(`${paneType}-pane`);
            if (pane) {
                // 強制的に表示状態に設定
                pane.style.display = 'flex';
                pane.style.visibility = 'visible';
                pane.style.opacity = '1';
                pane.style.pointerEvents = 'auto';
                pane.style.position = 'relative';
                pane.style.zIndex = '1';
                
                // hiddenクラスを削除
                pane.classList.remove('hidden');
                pane.classList.remove('collapsed');
                
                console.log(`✅ ${paneType}ペイン有効化完了:`, {
                    display: pane.style.display,
                    visibility: pane.style.visibility,
                    opacity: pane.style.opacity,
                    pointerEvents: pane.style.pointerEvents,
                    hasHiddenClass: pane.classList.contains('hidden'),
                    hasCollapsedClass: pane.classList.contains('collapsed')
                });
            } else {
                console.warn(`⚠️ ${paneType}ペインが見つかりません`);
            }
        });
        
        // その他のUI要素も有効化
        const allPanes = document.querySelectorAll('.pane, .chat-pane, .center-pane, .gemini-pane');
        allPanes.forEach(pane => {
            if (pane.id !== 'chat-pane' && pane.id !== 'center-pane' && pane.id !== 'gemini-pane') {
                pane.style.pointerEvents = 'auto';
                pane.style.opacity = '1';
                pane.style.visibility = 'visible';
            }
        });
        
        console.log('✅ UI有効化完了');
    }

    // ローディングオーバーレイ非表示
    hideLoadingOverlay() {
        console.log('🚫 ローディングオーバーレイ非表示処理開始');
        
        // 複数の方法でローディングオーバーレイを非表示
        const loadingOverlays = [
            document.getElementById('loading-overlay'),
            document.querySelector('.loading-overlay'),
            document.querySelector('.aide-loading'),
            document.querySelector('.screen-mask'),
            document.querySelector('.overlay')
        ];
        
        loadingOverlays.forEach(overlay => {
            if (overlay) {
                // 強制的に非表示に設定
                overlay.style.display = 'none';
                overlay.style.visibility = 'hidden';
                overlay.style.opacity = '0';
                overlay.style.zIndex = '-9999';
                overlay.style.pointerEvents = 'none';
                overlay.style.position = 'absolute';
                overlay.style.top = '-9999px';
                overlay.style.left = '-9999px';
                overlay.style.width = '0';
                overlay.style.height = '0';
                overlay.style.overflow = 'hidden';
                
                // hiddenクラスを追加
                overlay.classList.add('hidden');
                
                console.log('✅ ローディングオーバーレイ非表示完了:', {
                    id: overlay.id,
                    className: overlay.className,
                    display: overlay.style.display,
                    visibility: overlay.style.visibility,
                    zIndex: overlay.style.zIndex
                });
            }
        });
        
        // bodyとhtmlのスタイルも確認
        document.body.style.pointerEvents = 'auto';
        document.body.style.overflow = 'auto';
        document.documentElement.style.pointerEvents = 'auto';
        document.documentElement.style.overflow = 'auto';
        
        console.log('✅ ローディングオーバーレイ非表示処理完了');
    }
}

/**
 * アプリケーション初期化クラス
 * 各コンポーネントの初期化順序を管理
 */
class AppInitializer {
    constructor() {
        console.log('🚀 AppInitializer初期化');
        this.initializedComponents = new Set();
        this.enableUICalled = false;
    }

    // 初期化実行
    init() {
        console.log('🚀 AppInitializer.init() 開始');
        
        try {
            // 各コンポーネントの初期化
            this.initializeLayoutManager();
            this.initializeGeminiParser();
            this.initializeOtherComponents();
            
            // UI有効化
            this.enableUI();
            
            console.log('✅ AppInitializer初期化完了');
            
        } catch (error) {
            console.error('❌ AppInitializer初期化エラー:', error);
        }
    }

    // LayoutManager初期化
    initializeLayoutManager() {
        console.log('🎨 LayoutManager初期化開始');
        
        if (typeof LayoutManager !== 'undefined') {
            window.layoutManager = new LayoutManager();
            this.initializedComponents.add('LayoutManager');
            console.log('✅ LayoutManager初期化完了');
        } else {
            console.error('❌ LayoutManagerクラスが見つかりません');
        }
    }

    // GeminiParser初期化
    initializeGeminiParser() {
        console.log('🤖 GeminiParser初期化開始');
        
        if (typeof GeminiParser !== 'undefined') {
            window.geminiParser = new GeminiParser();
            this.initializedComponents.add('GeminiParser');
            console.log('✅ GeminiParser初期化完了');
        } else {
            console.error('❌ GeminiParserクラスが見つかりません');
        }
    }

    // その他のコンポーネント初期化
    initializeOtherComponents() {
        console.log('🔧 その他のコンポーネント初期化開始');
        
        // 利用可能なコンポーネントを初期化
        const components = [
            { name: 'Utils', class: 'Utils' },
            { name: 'ChatHandler', class: 'ChatHandler' },
            { name: 'ClaudeRenderer', class: 'ClaudeRenderer' },
            { name: 'StructureCards', class: 'StructureCards' },
            { name: 'DiffRenderer', class: 'DiffRenderer' },
            { name: 'HistoryHandler', class: 'HistoryHandler' },
            { name: 'ModuleDiff', class: 'ModuleDiff' },
            { name: 'Renderer', class: 'Renderer' }
        ];
        
        components.forEach(component => {
            if (typeof window[component.class] !== 'undefined') {
                try {
                    window[component.name.toLowerCase()] = new window[component.class]();
                    this.initializedComponents.add(component.name);
                    console.log(`✅ ${component.name}初期化完了`);
                } catch (error) {
                    console.warn(`⚠️ ${component.name}初期化エラー:`, error);
                }
            }
        });
        
        console.log('✅ その他のコンポーネント初期化完了');
    }

    // UI有効化
    enableUI() {
        if (this.enableUICalled) {
            console.log('ℹ️ UI有効化は既に実行済みです');
            return;
        }
        
        console.log('🔓 AppInitializer UI有効化開始');
        
        // LayoutManagerのUI有効化を呼び出し
        if (window.layoutManager && typeof window.layoutManager.enableUI === 'function') {
            window.layoutManager.enableUI();
        }
        
        // 構造データがある場合はGeminiParserに渡す
        if (window.structureData && window.geminiParser) {
            window.geminiParser.updateFromStructureData(window.structureData);
        }
        
        // 追加のUI有効化処理
        this.forceEnableUI();
        
        this.enableUICalled = true;
        console.log('✅ AppInitializer UI有効化完了');
    }
    
    // 強制UI有効化
    forceEnableUI() {
        console.log('🔧 強制UI有効化開始');
        
        // 遅延実行で確実にUIを有効化
        setTimeout(() => {
            // ローディングオーバーレイの最終確認
            const loadingOverlays = document.querySelectorAll('#loading-overlay, .loading-overlay, .aide-loading, .screen-mask, .overlay');
            loadingOverlays.forEach(overlay => {
                overlay.style.display = 'none';
                overlay.style.visibility = 'hidden';
                overlay.style.opacity = '0';
                overlay.style.zIndex = '-9999';
                overlay.style.pointerEvents = 'none';
            });
            
            // ペインの最終確認
            const panes = document.querySelectorAll('#chat-pane, #center-pane, #gemini-pane');
            panes.forEach(pane => {
                pane.style.display = 'flex';
                pane.style.visibility = 'visible';
                pane.style.opacity = '1';
                pane.style.pointerEvents = 'auto';
                pane.style.position = 'relative';
                pane.style.zIndex = '1';
                pane.classList.remove('hidden', 'collapsed');
            });
            
            // メインコンテナの最終確認
            const mainContainer = document.querySelector('.main-container');
            if (mainContainer) {
                mainContainer.style.display = 'flex';
                mainContainer.style.visibility = 'visible';
                mainContainer.style.opacity = '1';
                mainContainer.style.pointerEvents = 'auto';
            }
            
            console.log('✅ 強制UI有効化完了');
        }, 100);
    }
}

console.log('✅ LayoutManager・AppInitializerクラス定義完了');

// アプリケーション初期化の開始 