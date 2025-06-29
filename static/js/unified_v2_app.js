/**
 * AIDE-X Unified v2 メインアプリケーション
 * 統合インターフェースの全体制御
 */

class UnifiedV2App {
    constructor() {
        console.log('🚀 UnifiedV2App初期化');
        
        this.layoutManager = null;
        this.geminiParser = null;
        this.isInitialized = false;
        this.currentState = 'initializing';
        
        // 状態管理
        this.states = {
            initializing: '初期化中',
            ready: '準備完了',
            generating: '構成生成中',
            evaluating: '評価中',
            completing: '補完中',
            completed: '完了',
            error: 'エラー'
        };
    }

    init() {
        console.log('🚀 UnifiedV2App初期化開始');
        
        try {
            // 初期状態の設定
            this.updateStatus('初期化中...');
            
            // 各コンポーネントの初期化
            this.initializeComponents();
            
            // イベントハンドラーの設定
            this.setupEventHandlers();
            
            // 初期状態の確認
            this.checkInitialState();
            
            // 初期化完了
            this.isInitialized = true;
            this.setState('ready');
            this.updateStatus('準備完了');
            
            console.log('✅ UnifiedV2App初期化完了');
            
        } catch (error) {
            console.error('❌ UnifiedV2App初期化エラー:', error);
            this.setState('error');
            this.updateStatus('初期化エラー: ' + error.message);
        }
    }

    // コンポーネントの初期化
    initializeComponents() {
        console.log('🔧 コンポーネント初期化開始');
        
        // LayoutManagerV2の初期化
        if (typeof LayoutManagerV2 !== 'undefined') {
            this.layoutManager = new LayoutManagerV2();
            console.log('✅ LayoutManagerV2初期化完了');
        } else {
            console.error('❌ LayoutManagerV2クラスが見つかりません');
            throw new Error('LayoutManagerV2クラスが見つかりません');
        }
        
        // GeminiParserV2の初期化
        if (typeof GeminiParserV2 !== 'undefined') {
            this.geminiParser = new GeminiParserV2();
            console.log('✅ GeminiParserV2初期化完了');
        } else {
            console.error('❌ GeminiParserV2クラスが見つかりません');
            throw new Error('GeminiParserV2クラスが見つかりません');
        }
        
        // 既存コンポーネントの初期化（必要に応じて）
        this.initializeLegacyComponents();
    }

    // 既存コンポーネントの初期化
    initializeLegacyComponents() {
        console.log('🔄 既存コンポーネント初期化');
        
        const components = [
            { name: 'Utils', class: 'Utils' },
            { name: 'ChatHandler', class: 'ChatHandler' },
            { name: 'ClaudeRenderer', class: 'ClaudeRenderer' },
            { name: 'StructureCards', class: 'StructureCards' },
            { name: 'DiffRenderer', class: 'DiffRenderer' },
            { name: 'HistoryHandler', class: 'HistoryHandler' }
        ];
        
        components.forEach(component => {
            if (typeof window[component.class] !== 'undefined') {
                try {
                    window[component.name.toLowerCase()] = new window[component.class]();
                    console.log(`✅ ${component.name}初期化完了`);
                } catch (error) {
                    console.warn(`⚠️ ${component.name}初期化エラー:`, error);
                }
            }
        });
    }

    // イベントハンドラーの設定
    setupEventHandlers() {
        console.log('🎛️ イベントハンドラー設定');
        
        // ページ離脱時のレイアウト保存
        window.addEventListener('beforeunload', () => {
            if (this.layoutManager) {
                this.layoutManager.saveLayout();
            }
        });
        
        // エラーハンドリング
        window.addEventListener('error', (event) => {
            console.error('❌ グローバルエラー:', event.error);
            this.handleError(event.error);
        });
        
        // 未処理のPromise拒否
        window.addEventListener('unhandledrejection', (event) => {
            console.error('❌ 未処理のPromise拒否:', event.reason);
            this.handleError(event.reason);
        });
    }

    // 初期状態の確認
    checkInitialState() {
        console.log('🔍 初期状態確認');
        
        // 構造データの確認
        if (window.structureData) {
            console.log('✅ 構造データ確認完了:', {
                id: window.structureData.id,
                hasContent: !!(window.structureData.content),
                hasGeminiOutput: !!(window.structureData.gemini_output)
            });
            
            // GeminiParserにデータを渡す
            if (this.geminiParser) {
                this.geminiParser.updateFromStructureData(window.structureData);
            }
        } else {
            console.log('ℹ️ 構造データなし');
        }
        
        // デバッグモードの確認
        if (window.isDebugMode || window.isTestMode) {
            console.log('🧪 デバッグモード有効');
        }
    }

    // 状態の設定
    setState(newState) {
        if (this.states[newState]) {
            this.currentState = newState;
            console.log(`🔄 状態変更: ${this.states[newState]}`);
            
            // 状態に応じたUI更新
            this.updateUIForState(newState);
        }
    }

    // 状態に応じたUI更新
    updateUIForState(state) {
        const statusElement = document.getElementById('current-status');
        if (statusElement) {
            statusElement.textContent = this.states[state] || state;
        }
        
        // 状態に応じたペインの表示制御
        switch (state) {
            case 'generating':
                this.showStructurePane();
                break;
            case 'evaluating':
                this.showStructurePane();
                break;
            case 'completing':
                this.showGeminiPane();
                break;
            case 'completed':
                this.showAllPanes();
                break;
        }
    }

    // 構成ペインの表示
    showStructurePane() {
        if (this.layoutManager) {
            this.layoutManager.expandPane('structure');
        }
    }

    // Geminiペインの表示
    showGeminiPane() {
        if (this.layoutManager) {
            this.layoutManager.expandPane('gemini');
        }
    }

    // 全ペインの表示
    showAllPanes() {
        if (this.layoutManager) {
            this.layoutManager.expandAllPanes();
        }
    }

    // ステータス更新
    updateStatus(message) {
        const statusElement = document.getElementById('current-status');
        if (statusElement) {
            statusElement.textContent = message;
        }
    }

    // エラーハンドリング
    handleError(error) {
        console.error('❌ エラーハンドリング:', error);
        
        this.setState('error');
        this.updateStatus('エラーが発生しました: ' + (error.message || error));
        
        // エラー状態をUIに反映
        const geminiPane = document.getElementById('gemini-pane');
        if (geminiPane) {
            geminiPane.classList.add('error');
        }
    }

    // 構成生成の開始
    startStructureGeneration() {
        console.log('🚀 構成生成開始');
        
        this.setState('generating');
        this.updateStatus('構成を生成中...');
        
        // 構成ペインを表示
        this.showStructurePane();
    }

    // 構成評価の開始
    startStructureEvaluation() {
        console.log('🔍 構成評価開始');
        
        this.setState('evaluating');
        this.updateStatus('構成を評価中...');
        
        // 構成ペインを表示
        this.showStructurePane();
    }

    // Gemini補完の開始
    startGeminiCompletion() {
        console.log('🤖 Gemini補完開始');
        
        this.setState('completing');
        this.updateStatus('Gemini補完を生成中...');
        
        // Geminiペインを表示
        this.showGeminiPane();
        
        // ローディング状態を設定
        if (this.geminiParser) {
            this.geminiParser.setLoading(true);
        }
    }

    // Gemini補完の完了
    completeGeminiCompletion(geminiOutput) {
        console.log('✅ Gemini補完完了');
        
        this.setState('completed');
        this.updateStatus('Gemini補完完了');
        
        // ローディング状態を解除
        if (this.geminiParser) {
            this.geminiParser.setLoading(false);
            this.geminiParser.updateGeminiOutput(geminiOutput);
        }
        
        // 全ペインを表示
        this.showAllPanes();
    }

    // ワークフローの実行
    async executeWorkflow(userInput) {
        console.log('🔄 ワークフロー実行開始');
        
        try {
            // 1. 構成生成
            this.startStructureGeneration();
            // TODO: 実際の構成生成処理
            
            // 2. 構成評価
            this.startStructureEvaluation();
            // TODO: 実際の構成評価処理
            
            // 3. Gemini補完
            this.startGeminiCompletion();
            // TODO: 実際のGemini補完処理
            
            // 4. 完了
            this.completeGeminiCompletion({});
            
        } catch (error) {
            this.handleError(error);
        }
    }

    // デバッグ情報の出力
    debug() {
        console.log('🔍 UnifiedV2App デバッグ情報:', {
            isInitialized: this.isInitialized,
            currentState: this.currentState,
            layoutManager: !!this.layoutManager,
            geminiParser: !!this.geminiParser,
            structureData: window.structureData,
            isDebugMode: window.isDebugMode,
            isTestMode: window.isTestMode
        });
        
        // 各コンポーネントのデバッグ情報も出力
        if (this.layoutManager) {
            this.layoutManager.debug();
        }
        
        if (this.geminiParser) {
            this.geminiParser.debug();
        }
    }

    // アプリケーションのリセット
    reset() {
        console.log('🔄 アプリケーションリセット');
        
        this.setState('initializing');
        this.updateStatus('リセット中...');
        
        // 各コンポーネントのリセット
        if (this.layoutManager) {
            this.layoutManager.resetLayout();
        }
        
        if (this.geminiParser) {
            this.geminiParser.clearOutput();
        }
        
        // 初期状態に戻す
        setTimeout(() => {
            this.setState('ready');
            this.updateStatus('準備完了');
        }, 1000);
    }
}

console.log('✅ UnifiedV2Appクラス定義完了'); 