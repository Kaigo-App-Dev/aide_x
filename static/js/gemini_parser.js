/**
 * Gemini補完パーサー・レンダラー（再構築版）
 * 要件: デバッグモード対応、右ペイン強制表示、仮データ注入
 */

class GeminiParser {
    constructor() {
        console.log('🟦 GeminiParser constructor called');
        this.container = null;
        this.isInitialized = false;
        this.currentData = null;
        this.animationDuration = 400;
        
        // デバッグモードチェック
        this.checkDebugMode();
        
        this.init();
    }

    // デバッグモードチェック
    checkDebugMode() {
        console.log('🔍 GeminiParser デバッグモードチェック開始');
        
        const isDebugMode = window.isDebugMode || false;
        const isTestMode = window.isTestMode || false;
        
        console.log('🔍 GeminiParser デバッグモード状態:', {
            isDebugMode: isDebugMode,
            isTestMode: isTestMode,
            hasStructureData: !!(window.structureData && window.structureData.content)
        });
        
        if (isDebugMode || isTestMode) {
            console.log('🧪 デバッグ/テストモードで動作中 - GeminiParser');
            
            // デバッグモード用のサンプルデータを設定
            this.debugModeData = {
                status: 'success',
                content: `
                    <div style="padding: 20px; font-family: Arial, sans-serif;">
                        <h2 style="color: #4285f4; margin-bottom: 16px;">🧪 デバッグモード - Gemini補完結果</h2>
                        <div style="background: #f8f9fa; padding: 16px; border-radius: 8px; margin-bottom: 16px;">
                            <h3 style="color: #34a853; margin-top: 0;">📋 サンプルUI構成</h3>
                            <p>これはデバッグモード用の仮のGemini補完結果です。</p>
                            <ul>
                                <li>✅ ヘッダーセクション</li>
                                <li>✅ メインコンテンツエリア</li>
                                <li>✅ サイドバーナビゲーション</li>
                                <li>✅ フッター情報</li>
                            </ul>
                        </div>
                        <div style="background: #e8f5e8; padding: 12px; border-radius: 6px; border-left: 4px solid #34a853;">
                            <strong>🎯 期待される動作:</strong> このサンプルデータが右ペインに表示されることで、Gemini出力の表示機能が正常に動作していることを確認できます。
                        </div>
                    </div>
                `,
                timestamp: new Date().toISOString(),
                provider: 'gemini',
                debug_mode: true
            };
            
            // 構造データに仮のgemini_outputを追加
            if (window.structureData) {
                window.structureData.gemini_output = this.debugModeData;
                console.log('🔄 構造データに仮のgemini_outputを追加:', this.debugModeData);
            } else {
                console.warn('⚠️ window.structureDataが存在しません - 新規作成');
                window.structureData = {
                    id: 'debug-structure',
                    content: { sections: [] },
                    gemini_output: this.debugModeData
                };
            }
            
            // グローバル変数にも設定
            window.debugGeminiOutput = this.debugModeData;
            console.log('✅ デバッグGeminiデータをグローバル変数に設定');
        }
        
        console.log('✅ GeminiParser デバッグモードチェック完了');
    }

    // 初期化
    init() {
        console.log('🟦 GeminiParser.init() called');
        console.log('🤖 GeminiParser初期化開始');
        
        // コンテナ要素の取得
        this.container = document.getElementById('gemini-output');
        if (!this.container) {
            console.warn('⚠️ Gemini出力コンテナが見つかりません');
            return;
        }
        
        // 初期状態の設定
        this.setInitialState();
        
        // 右ペインの表示状態を確保
        this.ensureRightPaneVisibility();
        
        // デバッグモードの場合はサンプルデータを表示
        if (window.isDebugMode || window.isTestMode) {
            console.log('🧪 デバッグモード: サンプルGeminiデータを表示');
            console.log('🔍 デバッグデータ確認:', {
                hasDebugModeData: !!this.debugModeData,
                debugModeDataContent: this.debugModeData?.content?.substring(0, 100) + '...',
                hasStructureData: !!window.structureData,
                hasGeminiOutput: !!(window.structureData && window.structureData.gemini_output)
            });
            
            // 確実にデバッグデータを表示
            if (this.debugModeData) {
                this.updateGeminiOutput(this.debugModeData);
                console.log('✅ デバッグGeminiデータを表示完了');
            } else {
                console.warn('⚠️ デバッグデータが設定されていません');
            }
        }
        
        this.isInitialized = true;
        console.log('✅ GeminiParser初期化完了');
    }

    // 初期状態の設定
    setInitialState() {
        if (!this.container) return;
        
        this.container.innerHTML = `
            <div class="gemini-output-placeholder">
                <div class="placeholder-icon">🤖</div>
                <div class="placeholder-text">Gemini補完結果がここに表示されます</div>
            </div>
        `;
        
        // プレースホルダーにアニメーションを追加
        this.addFadeInAnimation(this.container);
    }

    // 右ペインの表示状態を確保
    ensureRightPaneVisibility() {
        const rightPane = document.querySelector('#gemini-pane');
        if (!rightPane) {
            console.warn('⚠️ Geminiペイン要素が見つかりません');
            return;
        }
        
        console.log('🔍 Geminiペイン表示状態チェック:', {
            offsetWidth: rightPane.offsetWidth,
            clientWidth: rightPane.clientWidth,
            display: rightPane.style.display,
            visibility: rightPane.style.visibility,
            opacity: rightPane.style.opacity,
            className: rightPane.className,
            isCollapsed: rightPane.classList.contains('collapsed')
        });
        
        // Geminiペインが非表示または幅が0の場合は強制表示
        if (rightPane.offsetWidth === 0 || 
            rightPane.style.display === 'none' || 
            rightPane.style.visibility === 'hidden' ||
            rightPane.style.opacity === '0') {
            
            console.log('⚠️ Geminiペインが非表示状態を検出、強制表示を実行');
            rightPane.style.display = 'flex';
            rightPane.style.visibility = 'visible';
            rightPane.style.opacity = '1';
            
            // 最小幅を確保
            if (rightPane.offsetWidth < 200) {
                rightPane.style.width = '200px';
            }
            
            console.log('✅ Geminiペイン強制表示完了:', {
                offsetWidth: rightPane.offsetWidth,
                display: rightPane.style.display,
                visibility: rightPane.style.visibility,
                opacity: rightPane.style.opacity
            });
        } else {
            console.log('✅ Geminiペインは正常に表示されています');
        }
    }

    // フェードインアニメーション追加
    addFadeInAnimation(element) {
        element.style.opacity = '0';
        element.style.transform = 'translateY(10px)';
        
        setTimeout(() => {
            element.style.transition = `opacity ${this.animationDuration}ms ease, transform ${this.animationDuration}ms ease`;
            element.style.opacity = '1';
            element.style.transform = 'translateY(0)';
            
            setTimeout(() => {
                element.style.transition = '';
            }, this.animationDuration);
        }, 100);
    }

    // Gemini出力の更新
    updateGeminiOutput(geminiOutput) {
        if (!this.container) {
            console.warn('⚠️ Gemini出力コンテナが見つかりません');
            return;
        }

        console.log('🔄 Gemini出力更新開始:', {
            hasGeminiOutput: !!geminiOutput,
            status: geminiOutput?.status,
            provider: geminiOutput?.provider,
            debugMode: geminiOutput?.debug_mode
        });

        try {
            if (!geminiOutput || !geminiOutput.content) {
                this.showNoDataMessage();
                return;
            }

            // コンテンツを設定
            this.container.innerHTML = geminiOutput.content;
            
            // アニメーションを追加
            this.addFadeInAnimation(this.container);
            
            // 現在のデータを保存
            this.currentData = geminiOutput;
            
            console.log('✅ Gemini出力更新完了');
            
        } catch (error) {
            console.error('❌ Gemini出力更新エラー:', error);
            this.showError('Gemini出力の表示中にエラーが発生しました');
        }
    }

    // 構造データからの更新
    updateFromStructureData(structureData) {
        console.log('🔄 構造データからのGemini出力更新開始');
        
        if (!structureData || !structureData.gemini_output) {
            console.log('ℹ️ 構造データにGemini出力が含まれていません');
            return;
        }

        const geminiOutput = structureData.gemini_output;
        console.log('🔍 構造データから取得したGemini出力:', {
            hasGeminiOutput: !!geminiOutput,
            type: typeof geminiOutput,
            keys: Object.keys(geminiOutput || {})
        });

        // 構造データのgemini_outputを直接使用
        this.updateGeminiOutput(geminiOutput);
    }

    // データなしメッセージの表示
    showNoDataMessage() {
        if (!this.container) return;
        
        this.container.innerHTML = `
            <div class="gemini-output-placeholder">
                <div class="placeholder-icon">🤖</div>
                <div class="placeholder-text">Gemini補完結果がありません</div>
                <div class="placeholder-subtext">新しい補完を生成してください</div>
            </div>
        `;
        
        this.addFadeInAnimation(this.container);
    }

    // エラーメッセージの表示
    showError(message) {
        if (!this.container) return;
        
        this.container.innerHTML = `
            <div class="gemini-output-error">
                <div class="error-icon">❌</div>
                <div class="error-text">エラーが発生しました</div>
                <div class="error-message">${this.escapeHtml(message)}</div>
            </div>
        `;
        
        this.addFadeInAnimation(this.container);
    }

    // HTMLエスケープ
    escapeHtml(str) {
        const div = document.createElement('div');
        div.textContent = str;
        return div.innerHTML;
    }

    // 準備完了チェック
    isReady() {
        return this.isInitialized && this.container !== null;
    }

    // 現在のデータ取得
    getCurrentData() {
        return this.currentData;
    }

    // 表示状態チェック
    isVisible() {
        return this.container && this.container.offsetWidth > 0;
    }
}

// グローバル関数（後方互換性）
function updateGeminiOutput(geminiOutput) {
    if (window.geminiParser) {
        window.geminiParser.updateGeminiOutput(geminiOutput);
    } else {
        console.warn('⚠️ GeminiParserインスタンスが見つかりません');
    }
}

function updateFromStructureData(structureData) {
    if (window.geminiParser) {
        window.geminiParser.updateFromStructureData(structureData);
    } else {
        console.warn('⚠️ GeminiParserインスタンスが見つかりません');
    }
}

console.log('✅ GeminiParserクラス定義完了'); 