/**
 * AIDE-X Unified v2 GeminiParser
 * Gemini補完出力の解析と表示制御
 */

class GeminiParserV2 {
    constructor() {
        console.log('🤖 GeminiParserV2初期化');
        
        this.outputContainer = null;
        this.isDebugMode = window.isDebugMode || false;
        this.isTestMode = window.isTestMode || false;
        this.currentData = null;
        
        this.init();
    }

    init() {
        console.log('🤖 GeminiParserV2初期化開始');
        
        try {
            // 出力コンテナの取得
            this.outputContainer = document.getElementById('gemini-output');
            if (!this.outputContainer) {
                console.warn('⚠️ gemini-outputコンテナが見つかりません');
            } else {
                console.log('✅ gemini-outputコンテナ確認完了');
            }
            
            // 構造データがある場合は処理
            if (window.structureData) {
                this.updateFromStructureData(window.structureData);
            }
            
            console.log('✅ GeminiParserV2初期化完了');
            
        } catch (error) {
            console.error('❌ GeminiParserV2初期化エラー:', error);
        }
    }

    // 構造データからの更新
    updateFromStructureData(structureData) {
        console.log('🔄 構造データからの更新開始');
        
        this.currentData = structureData;
        
        if (structureData.gemini_output) {
            this.updateGeminiOutput(structureData.gemini_output);
        } else if (this.isDebugMode || this.isTestMode) {
            this.injectDebugData();
        } else {
            this.showNoDataMessage();
        }
    }

    // Gemini出力の更新
    updateGeminiOutput(geminiOutput) {
        console.log('🔄 Gemini出力更新開始:', geminiOutput);
        
        if (!this.outputContainer) {
            console.error('❌ 出力コンテナが見つかりません');
            return;
        }
        
        try {
            // 出力コンテナをクリア
            this.outputContainer.innerHTML = '';
            
            if (!geminiOutput || Object.keys(geminiOutput).length === 0) {
                this.showNoDataMessage();
                return;
            }
            
            // 各セクションの出力を処理
            Object.entries(geminiOutput).forEach(([sectionName, sectionData]) => {
                const sectionElement = this.createSectionElement(sectionName, sectionData);
                this.outputContainer.appendChild(sectionElement);
            });
            
            // 成功状態を設定
            this.setPaneState('success');
            console.log('✅ Gemini出力更新完了');
            
        } catch (error) {
            console.error('❌ Gemini出力更新エラー:', error);
            this.showErrorMessage('Gemini出力の更新中にエラーが発生しました: ' + error.message);
        }
    }

    // セクション要素の作成
    createSectionElement(sectionName, sectionData) {
        const sectionDiv = document.createElement('div');
        sectionDiv.className = 'gemini-section';
        
        // セクションヘッダー
        const headerDiv = document.createElement('div');
        headerDiv.className = 'gemini-section-header';
        
        const titleSpan = document.createElement('span');
        titleSpan.className = 'gemini-section-title';
        titleSpan.textContent = sectionData.title || sectionName;
        
        const statusSpan = document.createElement('span');
        statusSpan.className = 'gemini-section-status';
        statusSpan.textContent = '✅ 完了';
        
        headerDiv.appendChild(titleSpan);
        headerDiv.appendChild(statusSpan);
        
        // セクションコンテンツ
        const contentDiv = document.createElement('div');
        contentDiv.className = 'gemini-section-content';
        
        if (sectionData.output) {
            // 出力内容をHTMLとして処理
            const outputDiv = document.createElement('div');
            outputDiv.className = 'gemini-output-text';
            outputDiv.innerHTML = this.formatOutput(sectionData.output);
            contentDiv.appendChild(outputDiv);
        }
        
        // メタデータ
        if (sectionData.metadata) {
            const metadataDiv = document.createElement('div');
            metadataDiv.className = 'gemini-section-metadata';
            metadataDiv.innerHTML = this.createMetadataHTML(sectionData.metadata);
            contentDiv.appendChild(metadataDiv);
        }
        
        sectionDiv.appendChild(headerDiv);
        sectionDiv.appendChild(contentDiv);
        
        return sectionDiv;
    }

    // 出力のフォーマット
    formatOutput(output) {
        if (typeof output !== 'string') {
            return JSON.stringify(output, null, 2);
        }
        
        // コードブロックの処理
        let formatted = output
            .replace(/```(\w+)?\n([\s\S]*?)```/g, (match, lang, code) => {
                return `<pre class="code-block ${lang || ''}"><code>${this.escapeHtml(code)}</code></pre>`;
            })
            .replace(/`([^`]+)`/g, '<code>$1</code>')
            .replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>')
            .replace(/\*([^*]+)\*/g, '<em>$1</em>')
            .replace(/\n/g, '<br>');
        
        return formatted;
    }

    // HTMLエスケープ
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    // メタデータHTMLの作成
    createMetadataHTML(metadata) {
        if (!metadata || typeof metadata !== 'object') {
            return '';
        }
        
        const items = Object.entries(metadata).map(([key, value]) => {
            return `<div class="metadata-item"><span class="metadata-key">${key}:</span> <span class="metadata-value">${value}</span></div>`;
        });
        
        return `<div class="metadata-container">${items.join('')}</div>`;
    }

    // デバッグデータの注入
    injectDebugData() {
        console.log('🧪 デバッグデータ注入');
        
        const debugOutput = {
            "テストセクション": {
                title: "テストセクション",
                output: "これはGeminiのv2デバッグ出力です。\n\n```javascript\n// サンプルコード\nfunction test() {\n    console.log('Hello, World!');\n}\n```\n\n**太字テキスト**と*斜体テキスト*も表示されます。",
                metadata: {
                    "生成時刻": new Date().toLocaleString(),
                    "モード": "デバッグ",
                    "バージョン": "v2.0.0"
                }
            }
        };
        
        this.updateGeminiOutput(debugOutput);
    }

    // データなしメッセージの表示
    showNoDataMessage() {
        if (!this.outputContainer) return;
        
        this.outputContainer.innerHTML = `
            <div class="gemini-no-data">
                <div class="no-data-icon">📋</div>
                <div class="no-data-title">Gemini補完データがありません</div>
                <div class="no-data-description">
                    構成の評価が完了すると、ここにGeminiによる補完結果が表示されます。
                </div>
            </div>
        `;
        
        this.setPaneState('warning');
    }

    // エラーメッセージの表示
    showErrorMessage(message) {
        if (!this.outputContainer) return;
        
        this.outputContainer.innerHTML = `
            <div class="gemini-error">
                <div class="error-icon">❌</div>
                <div class="error-title">エラーが発生しました</div>
                <div class="error-message">${this.escapeHtml(message)}</div>
            </div>
        `;
        
        this.setPaneState('error');
    }

    // ペイン状態の設定
    setPaneState(state) {
        const geminiPane = document.getElementById('gemini-pane');
        if (!geminiPane) return;
        
        // 既存の状態クラスを削除
        geminiPane.classList.remove('success', 'error', 'warning', 'loading');
        
        // 新しい状態クラスを追加
        if (state) {
            geminiPane.classList.add(state);
        }
    }

    // ローディング状態の設定
    setLoading(loading = true) {
        const geminiPane = document.getElementById('gemini-pane');
        if (!geminiPane) return;
        
        if (loading) {
            geminiPane.classList.add('loading');
            if (this.outputContainer) {
                this.outputContainer.innerHTML = `
                    <div class="gemini-loading">
                        <div class="loading-spinner"></div>
                        <div class="loading-text">Gemini補完を生成中...</div>
                    </div>
                `;
            }
        } else {
            geminiPane.classList.remove('loading');
        }
    }

    // データの取得
    getCurrentData() {
        return this.currentData;
    }

    // 出力のクリア
    clearOutput() {
        if (this.outputContainer) {
            this.outputContainer.innerHTML = '';
        }
        this.setPaneState(null);
    }

    // デバッグ情報の出力
    debug() {
        console.log('🔍 GeminiParserV2 デバッグ情報:', {
            outputContainer: !!this.outputContainer,
            isDebugMode: this.isDebugMode,
            isTestMode: this.isTestMode,
            currentData: this.currentData,
            geminiOutput: this.currentData?.gemini_output
        });
    }
}

console.log('✅ GeminiParserV2クラス定義完了'); 