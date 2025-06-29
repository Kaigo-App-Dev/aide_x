/**
 * AIDE-X Unified v2 レイアウトマネージャー
 * 3ペイン構成（チャット、構成、Gemini補完）の制御
 */

class LayoutManagerV2 {
    constructor() {
        console.log('🎨 LayoutManagerV2初期化');
        
        this.panes = {
            chat: { id: 'chat-pane', name: 'チャット', defaultVisible: true },
            structure: { id: 'structure-pane', name: '構成', defaultVisible: true },
            gemini: { id: 'gemini-pane', name: 'Gemini補完', defaultVisible: true }
        };
        
        this.storageKey = 'aide_x_v2_layout';
        this.minPaneWidth = 250;
        this.maxPaneWidth = window.innerWidth * 0.5;
        this.isResizing = false;
        this.currentResizer = null;
        
        this.init();
    }

    init() {
        console.log('🎨 LayoutManagerV2初期化開始');
        
        try {
            // ペイン要素の存在確認
            this.validatePanes();
            
            // 保存されたレイアウトの復元
            this.restoreLayout();
            
            // ペイン切り替えの初期化
            this.initPaneToggles();
            
            // ペインリサイザーの初期化
            this.initPaneResizers();
            
            // ヘッダーコントロールの初期化
            this.initHeaderControls();
            
            // キーボードショートカットの初期化
            this.initKeyboardShortcuts();
            
            // ウィンドウリサイズ対応
            this.initWindowResizeHandler();
            
            console.log('✅ LayoutManagerV2初期化完了');
            
        } catch (error) {
            console.error('❌ LayoutManagerV2初期化エラー:', error);
        }
    }

    // ペイン要素の存在確認
    validatePanes() {
        console.log('🔍 ペイン要素確認');
        
        Object.entries(this.panes).forEach(([key, pane]) => {
            const element = document.getElementById(pane.id);
            if (!element) {
                console.error(`❌ ペイン要素が見つかりません: ${pane.id}`);
                throw new Error(`ペイン要素が見つかりません: ${pane.id}`);
            }
            console.log(`✅ ${pane.name}ペイン確認完了: ${pane.id}`);
        });
    }

    // ペイン切り替えの初期化
    initPaneToggles() {
        console.log('🔄 ペイン切り替え初期化');
        
        document.querySelectorAll('.pane-toggle').forEach(button => {
            button.addEventListener('click', (e) => {
                e.preventDefault();
                const paneType = button.getAttribute('data-pane');
                if (paneType && this.panes[paneType]) {
                    this.togglePane(paneType);
                }
            });
        });
    }

    // ペイン切り替え
    togglePane(paneType) {
        console.log(`🔄 ${this.panes[paneType].name}ペイン切り替え`);
        
        const pane = document.getElementById(this.panes[paneType].id);
        if (!pane) return;
        
        const isCollapsed = pane.classList.contains('collapsed');
        
        if (isCollapsed) {
            this.expandPane(paneType);
        } else {
            this.collapsePane(paneType);
        }
        
        this.saveLayout();
        this.updateStatus(`${this.panes[paneType].name}ペインを${isCollapsed ? '展開' : '折りたたみ'}しました`);
    }

    // ペイン展開
    expandPane(paneType) {
        const pane = document.getElementById(this.panes[paneType].id);
        if (!pane) return;
        
        pane.classList.remove('collapsed');
        pane.style.display = 'flex';
        pane.style.visibility = 'visible';
        pane.style.opacity = '1';
        pane.style.pointerEvents = 'auto';
        
        // 最小幅を確保
        if (pane.offsetWidth < this.minPaneWidth) {
            pane.style.minWidth = `${this.minPaneWidth}px`;
        }
        
        console.log(`✅ ${this.panes[paneType].name}ペイン展開完了`);
    }

    // ペイン折りたたみ
    collapsePane(paneType) {
        const pane = document.getElementById(this.panes[paneType].id);
        if (!pane) return;
        
        pane.classList.add('collapsed');
        pane.style.minWidth = '0';
        pane.style.width = '0';
        pane.style.overflow = 'hidden';
        
        console.log(`✅ ${this.panes[paneType].name}ペイン折りたたみ完了`);
    }

    // 全ペイン展開
    expandAllPanes() {
        console.log('🔄 全ペイン展開');
        
        Object.keys(this.panes).forEach(paneType => {
            this.expandPane(paneType);
        });
        
        this.saveLayout();
        this.updateStatus('全ペインを展開しました');
    }

    // ペインリサイザーの初期化
    initPaneResizers() {
        console.log('🔧 ペインリサイザー初期化');
        
        document.querySelectorAll('.pane-resizer').forEach(resizer => {
            resizer.addEventListener('mousedown', (e) => {
                this.startResize(e, resizer);
            });
        });
    }

    // リサイズ開始
    startResize(e, resizer) {
        e.preventDefault();
        this.isResizing = true;
        this.currentResizer = resizer;
        resizer.classList.add('resizing');
        
        const handleMouseMove = (e) => {
            if (!this.isResizing) return;
            this.handleResize(e, resizer);
        };
        
        const handleMouseUp = () => {
            this.isResizing = false;
            this.currentResizer = null;
            resizer.classList.remove('resizing');
            document.removeEventListener('mousemove', handleMouseMove);
            document.removeEventListener('mouseup', handleMouseUp);
            this.saveLayout();
        };
        
        document.addEventListener('mousemove', handleMouseMove);
        document.addEventListener('mouseup', handleMouseUp);
    }

    // リサイズ処理
    handleResize(e, resizer) {
        const container = document.querySelector('.unified-v2-main');
        const containerRect = container.getBoundingClientRect();
        const mouseX = e.clientX - containerRect.left;
        
        const targetPaneId = resizer.getAttribute('data-resize');
        const targetPane = document.getElementById(targetPaneId);
        
        if (targetPane && !targetPane.classList.contains('collapsed')) {
            const newWidth = Math.max(this.minPaneWidth, Math.min(this.maxPaneWidth, mouseX));
            targetPane.style.width = `${newWidth}px`;
            targetPane.style.minWidth = `${newWidth}px`;
        }
    }

    // ヘッダーコントロールの初期化
    initHeaderControls() {
        console.log('🎛️ ヘッダーコントロール初期化');
        
        // 全展開ボタン
        const expandAllBtn = document.getElementById('expand-all-panes');
        if (expandAllBtn) {
            expandAllBtn.addEventListener('click', () => {
                this.expandAllPanes();
            });
        }
        
        // リセットボタン
        const resetBtn = document.getElementById('reset-layout');
        if (resetBtn) {
            resetBtn.addEventListener('click', () => {
                this.resetLayout();
            });
        }
    }

    // レイアウトリセット
    resetLayout() {
        console.log('🔄 レイアウトリセット');
        
        Object.keys(this.panes).forEach(paneType => {
            const pane = document.getElementById(this.panes[paneType].id);
            if (pane) {
                pane.classList.remove('collapsed');
                pane.style.width = '';
                pane.style.minWidth = '';
                pane.style.display = 'flex';
                pane.style.visibility = 'visible';
                pane.style.opacity = '1';
                pane.style.pointerEvents = 'auto';
            }
        });
        
        localStorage.removeItem(this.storageKey);
        this.updateStatus('レイアウトをリセットしました');
    }

    // キーボードショートカットの初期化
    initKeyboardShortcuts() {
        console.log('⌨️ キーボードショートカット初期化');
        
        document.addEventListener('keydown', (e) => {
            // Ctrl+1: チャットペイン切り替え
            if (e.ctrlKey && e.key === '1') {
                e.preventDefault();
                this.togglePane('chat');
            }
            
            // Ctrl+2: 構成ペイン切り替え
            if (e.ctrlKey && e.key === '2') {
                e.preventDefault();
                this.togglePane('structure');
            }
            
            // Ctrl+3: Geminiペイン切り替え
            if (e.ctrlKey && e.key === '3') {
                e.preventDefault();
                this.togglePane('gemini');
            }
            
            // Ctrl+0: 全ペイン展開
            if (e.ctrlKey && e.key === '0') {
                e.preventDefault();
                this.expandAllPanes();
            }
        });
    }

    // ウィンドウリサイズ対応
    initWindowResizeHandler() {
        window.addEventListener('resize', () => {
            this.handleWindowResize();
        });
    }

    // ウィンドウリサイズ処理
    handleWindowResize() {
        this.maxPaneWidth = window.innerWidth * 0.5;
        
        // ペインの最大幅を調整
        Object.keys(this.panes).forEach(paneType => {
            const pane = document.getElementById(this.panes[paneType].id);
            if (pane && !pane.classList.contains('collapsed')) {
                const currentWidth = pane.offsetWidth;
                if (currentWidth > this.maxPaneWidth) {
                    pane.style.width = `${this.maxPaneWidth}px`;
                    pane.style.minWidth = `${this.maxPaneWidth}px`;
                }
            }
        });
    }

    // レイアウトの保存
    saveLayout() {
        const layout = {
            panes: {},
            timestamp: Date.now()
        };
        
        Object.entries(this.panes).forEach(([key, pane]) => {
            const element = document.getElementById(pane.id);
            if (element) {
                layout.panes[key] = {
                    collapsed: element.classList.contains('collapsed'),
                    width: element.offsetWidth,
                    minWidth: element.style.minWidth
                };
            }
        });
        
        localStorage.setItem(this.storageKey, JSON.stringify(layout));
        console.log('💾 レイアウト保存完了');
    }

    // レイアウトの復元
    restoreLayout() {
        const savedLayout = localStorage.getItem(this.storageKey);
        if (!savedLayout) {
            console.log('📂 保存されたレイアウトなし - デフォルト設定を使用');
            return;
        }
        
        try {
            const layout = JSON.parse(savedLayout);
            
            Object.entries(layout.panes || {}).forEach(([key, paneData]) => {
                const pane = document.getElementById(this.panes[key].id);
                if (pane) {
                    if (paneData.collapsed) {
                        this.collapsePane(key);
                    } else {
                        this.expandPane(key);
                        if (paneData.width) {
                            pane.style.width = `${paneData.width}px`;
                            pane.style.minWidth = `${paneData.width}px`;
                        }
                    }
                }
            });
            
            console.log('✅ レイアウト復元完了');
            
        } catch (error) {
            console.error('❌ レイアウト復元エラー:', error);
        }
    }

    // ステータス更新
    updateStatus(message) {
        const statusElement = document.getElementById('current-status');
        if (statusElement) {
            statusElement.textContent = message;
            
            // 3秒後にデフォルトメッセージに戻す
            setTimeout(() => {
                statusElement.textContent = '初期化完了';
            }, 3000);
        }
    }

    // ペイン状態の取得
    getPaneState(paneType) {
        const pane = document.getElementById(this.panes[paneType].id);
        if (!pane) return null;
        
        return {
            collapsed: pane.classList.contains('collapsed'),
            visible: pane.style.display !== 'none' && pane.style.visibility !== 'hidden',
            width: pane.offsetWidth,
            minWidth: pane.style.minWidth
        };
    }

    // 全ペイン状態の取得
    getAllPaneStates() {
        const states = {};
        Object.keys(this.panes).forEach(key => {
            states[key] = this.getPaneState(key);
        });
        return states;
    }

    // デバッグ情報の出力
    debug() {
        console.log('🔍 LayoutManagerV2 デバッグ情報:', {
            panes: this.getAllPaneStates(),
            storageKey: this.storageKey,
            minPaneWidth: this.minPaneWidth,
            maxPaneWidth: this.maxPaneWidth,
            isResizing: this.isResizing
        });
    }
}

console.log('✅ LayoutManagerV2クラス定義完了'); 