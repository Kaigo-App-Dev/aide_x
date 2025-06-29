/**
 * Claude評価出力の描画処理
 */

class ClaudeRenderer {
    constructor() {
        console.log('🤖 ClaudeRenderer初期化');
        
        // デバッグモードチェック
        this.checkDebugMode();
    }

    // デバッグモードチェック
    checkDebugMode() {
        console.log('🔍 ClaudeRenderer デバッグモードチェック開始');
        
        const isDebugMode = window.isDebugMode || false;
        const isTestMode = window.isTestMode || false;
        const hasStructureData = !!(window.structureData && window.structureData.content);
        
        console.log('🔍 ClaudeRenderer デバッグモード状態:', {
            isDebugMode: isDebugMode,
            isTestMode: isTestMode,
            hasStructureData: hasStructureData,
            structureDataId: window.structureData?.id || 'undefined'
        });
        
        if (isDebugMode || isTestMode) {
            console.log('🧪 デバッグ/テストモードで動作中 - ClaudeRenderer');
            
            // デバッグモード用のサンプル評価データを設定
            this.debugModeEvaluation = {
                status: 'success',
                feedback: 'デバッグモード用のClaude評価結果です。構造データが正しく設定されていない可能性があります。',
                score: 0.85,
                details: {
                    '構成の一貫性': '良好',
                    '実装可能性': '高い',
                    '保守性': '良好'
                },
                timestamp: new Date().toISOString(),
                provider: 'claude',
                debug_mode: true
            };
        }
        
        console.log('✅ ClaudeRenderer デバッグモードチェック完了');
    }

    // 構造データからClaude評価を更新
    updateFromStructureData(structureData) {
        console.log('🔄 ClaudeRenderer: 構造データからの更新開始:', {
            hasStructure: !!structureData,
            structureKeys: structureData ? Object.keys(structureData) : 'null',
            hasEvaluations: structureData && 'evaluations' in structureData,
            hasClaudeEval: structureData && structureData.evaluations && 'claude' in structureData.evaluations,
            hasClaudeEvaluation: structureData && 'claude_evaluation' in structureData,
            isDebugMode: window.isDebugMode || false,
            isTestMode: window.isTestMode || false
        });

        // デバッグモードの場合はサンプルデータを表示
        if (window.isDebugMode || window.isTestMode) {
            console.log('🧪 デバッグモード: サンプルClaude評価データを表示');
            this.updateClaudeEvaluation(this.debugModeEvaluation);
            return;
        }

        if (!structureData) {
            console.warn('⚠️ 構造データが空です');
            this.updateClaudeEvaluation(null);
            return;
        }

        // 優先順位: evaluations["claude"] > claude_evaluation
        let claudeEvaluation = null;
        
        // 1. evaluations["claude"]から取得（新しい形式）
        if (structureData.evaluations && structureData.evaluations.claude) {
            claudeEvaluation = structureData.evaluations.claude;
            console.log('✅ evaluations["claude"]から取得:', {
                status: claudeEvaluation.status,
                hasFeedback: !!claudeEvaluation.feedback,
                hasScore: !!claudeEvaluation.score,
                hasDetails: !!claudeEvaluation.details
            });
        }
        // 2. claude_evaluationから取得（旧形式）
        else if (structureData.claude_evaluation) {
            const claudeEval = structureData.claude_evaluation;
            
            // claude_evaluationが文字列の場合は適切に処理
            if (typeof claudeEval === 'string') {
                console.log('✅ claude_evaluation（文字列）から取得:', {
                    contentLength: claudeEval.length,
                    contentPreview: claudeEval.substring(0, 100) + '...'
                });
                
                // 文字列を評価オブジェクトとして扱う
                claudeEvaluation = {
                    status: 'success',
                    feedback: claudeEval,
                    content: claudeEval,
                    provider: 'claude',
                    timestamp: new Date().toISOString()
                };
            } else if (typeof claudeEval === 'object') {
                console.log('✅ claude_evaluation（オブジェクト）から取得:', {
                    status: claudeEval.status,
                    hasContent: !!claudeEval.content,
                    hasFeedback: !!claudeEval.feedback
                });
                claudeEvaluation = claudeEval;
            }
        }
        
        if (claudeEvaluation) {
            console.log('✅ Claude評価データを検出、表示を更新');
            this.updateClaudeEvaluation(claudeEvaluation);
        } else {
            console.log('⚠️ Claude評価データが見つかりません');
            this.updateClaudeEvaluation(null);
        }
    }

    // Claude評価結果を中央ペインに表示
    updateClaudeEvaluation(claudeEvaluation) {
        console.log('[DEBUG] updateClaudeEvaluation 開始:', {
            claudeEvaluation: claudeEvaluation,
            type: typeof claudeEvaluation,
            isNull: claudeEvaluation === null,
            isUndefined: claudeEvaluation === undefined
        });

        const evaluationContent = document.getElementById('claude-evaluation-content');
        if (!evaluationContent) {
            console.warn('⚠️ claude-evaluation-contentエリアが見つかりません');
            return;
        }

        // 評価データがない場合はプレースホルダーを表示
        if (!claudeEvaluation || 
            (typeof claudeEvaluation === 'object' && Object.keys(claudeEvaluation).length === 0) ||
            (claudeEvaluation.status && claudeEvaluation.status !== 'success')) {
            console.log('[DEBUG] Claude評価が空または失敗のため、プレースホルダーを表示');
            evaluationContent.innerHTML = `
                <div class="evaluation-placeholder">
                    <div class="empty-message">
                        <h4>🧠 Claude評価</h4>
                        <p>評価がまだ実行されていません</p>
                        <p class="text-muted">「再評価」ボタンを押すと、Claudeによる評価が実行されます。</p>
                    </div>
                </div>
            `;
            return;
        }

        console.log('[DEBUG] Claude評価が存在するため、評価カードを描画:', claudeEvaluation);

        try {
            const evaluationHtml = `
                <div class="evaluation-success">
                    <div class="evaluation-header">
                        <h4>✨ Claude評価完了</h4>
                        <div class="evaluation-meta">
                            ${claudeEvaluation.timestamp ? `<span class="evaluation-timestamp">${this.formatTimestamp(claudeEvaluation.timestamp)}</span>` : ''}
                            ${claudeEvaluation.score ? `<span class="evaluation-score">スコア: ${(claudeEvaluation.score * 100).toFixed(1)}%</span>` : ''}
                        </div>
                    </div>
                    <div class="evaluation-content">
                        ${this.renderClaudeEvaluation(claudeEvaluation)}
                    </div>
                </div>
            `;

            console.log('[DEBUG] 生成された評価HTML:', evaluationHtml);
            evaluationContent.innerHTML = evaluationHtml;

            console.log('✅ Claude評価結果を中央ペインに表示しました');

        } catch (error) {
            console.error('❌ Claude評価結果の表示エラー:', error);
            evaluationContent.innerHTML = `
                <div class="evaluation-error">
                    <h4>⚠️ 表示エラー</h4>
                    <p>Claude評価結果の表示中にエラーが発生しました: ${error.message}</p>
                    <details>
                        <summary>エラー詳細</summary>
                        <pre>${error.stack}</pre>
                    </details>
                </div>
            `;
        }
    }

    // Claude評価をHTMLとして描画
    renderClaudeEvaluation(evaluation) {
        console.log('🎨 renderClaudeEvaluation開始:', {
            evaluation: evaluation,
            type: typeof evaluation,
            keys: Object.keys(evaluation)
        });

        let html = '<div class="claude-evaluation-cards">';

        if (typeof evaluation === 'object') {
            // 評価結果の各項目を処理
            Object.entries(evaluation).forEach(([key, value]) => {
                html += this.createEvaluationCard(key, value);
            });
        } else if (typeof evaluation === 'string') {
            // 文字列の場合はそのまま表示
            html += `
                <div class="evaluation-text">
                    <p>${window.utils.sanitizeHtml(evaluation)}</p>
                </div>
            `;
        } else {
            html += '<div class="no-evaluation">評価データが見つかりません</div>';
        }

        html += '</div>';
        console.log('✅ renderClaudeEvaluation完了');
        return html;
    }

    // 評価カードを作成
    createEvaluationCard(key, value) {
        const cardTitle = this.formatCardTitle(key);
        
        let cardContent = '';
        
        if (typeof value === 'object' && value !== null) {
            // オブジェクトの場合は詳細表示
            if (Array.isArray(value)) {
                cardContent = '<ul>';
                value.forEach(item => {
                    cardContent += `<li>${window.utils.sanitizeHtml(item)}</li>`;
                });
                cardContent += '</ul>';
            } else {
                cardContent = '<ul>';
                Object.entries(value).forEach(([subKey, subValue]) => {
                    cardContent += `<li><strong>${window.utils.sanitizeHtml(subKey)}:</strong> ${window.utils.sanitizeHtml(subValue)}</li>`;
                });
                cardContent += '</ul>';
            }
        } else {
            // 文字列やその他の値
            cardContent = `<p>${window.utils.sanitizeHtml(value)}</p>`;
        }

        return `
            <div class="evaluation-card claude-evaluation-card">
                <div class="card-header">
                    <h5 class="card-title">${cardTitle}</h5>
                    <button class="structure-card-toggle" onclick="window.StructureCards.prototype.toggleCard(this)">▼</button>
                </div>
                <div class="card-content" style="display: none;">
                    ${cardContent}
                </div>
            </div>
        `;
    }

    // カードタイトルをフォーマット
    formatCardTitle(key) {
        const titleMap = {
            'overall_assessment': '全体評価',
            'structure_analysis': '構造分析',
            'completeness': '完全性',
            'consistency': '一貫性',
            'feasibility': '実現可能性',
            'recommendations': '推奨事項',
            'issues': '問題点',
            'improvements': '改善点',
            'score': 'スコア',
            'summary': 'サマリー',
            'details': '詳細',
            'assessment': '評価',
            'analysis': '分析',
            'review': 'レビュー',
            'status': 'ステータス',
            'feedback': 'フィードバック',
            'provider': 'プロバイダー',
            'timestamp': 'タイムスタンプ',
            'reason': '理由',
            'error_details': 'エラー詳細'
        };

        return titleMap[key] || key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
    }

    // タイムスタンプをフォーマット
    formatTimestamp(timestamp) {
        if (!timestamp) return '';
        
        try {
            const date = new Date(timestamp);
            return date.toLocaleString('ja-JP', {
                year: 'numeric',
                month: '2-digit',
                day: '2-digit',
                hour: '2-digit',
                minute: '2-digit'
            });
        } catch (error) {
            console.warn('タイムスタンプのフォーマットに失敗:', error);
            return timestamp;
        }
    }

    // Claude評価の実行
    triggerClaudeEvaluation() {
        console.log('🧠 Claude評価実行開始');
        
        // デバッグモードの場合はサンプル評価を生成
        if (window.isDebugMode || window.isTestMode) {
            console.log('🧪 デバッグモード: サンプルClaude評価を生成');
            
            // ローディング表示
            const evaluationContent = document.getElementById('claude-evaluation-content');
            if (evaluationContent) {
                evaluationContent.innerHTML = `
                    <div class="evaluation-loading">
                        <div class="loading-spinner"></div>
                        <p>デバッグモードで評価中...</p>
                    </div>
                `;
            }
            
            // 1秒後にサンプル評価結果を表示
            setTimeout(() => {
                this.updateClaudeEvaluation(this.debugModeEvaluation);
                console.log('✅ デバッグモード: サンプルClaude評価完了');
            }, 1000);
            return;
        }
        
        // 実API連携での評価実行
        const evaluationContent = document.getElementById('claude-evaluation-content');
        if (evaluationContent) {
            evaluationContent.innerHTML = `
                <div class="evaluation-loading">
                    <div class="loading-spinner"></div>
                    <p>Claudeによる評価を実行中...</p>
                </div>
            `;
        }

        // 評価APIを呼び出し
        fetch("/api/evaluate/claude", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": document.querySelector('meta[name="csrf-token"]').getAttribute('content')
            },
            body: JSON.stringify({
                structure_id: window.structureData?.id || null,
                structure_data: window.structureData
            })
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            console.log("✅ Claude評価成功:", data);
            
            if (data.evaluation) {
                this.updateClaudeEvaluation(data.evaluation);
            } else {
                this.showEvaluationError("評価結果が取得できませんでした");
            }
        })
        .catch(error => {
            console.error("❌ Claude評価エラー:", error);
            this.showEvaluationError(`評価中にエラーが発生しました: ${error.message}`);
        });
    }
    
    // 評価エラーを表示
    showEvaluationError(message) {
        const evaluationContent = document.getElementById('claude-evaluation-content');
        if (evaluationContent) {
            evaluationContent.innerHTML = `
                <div class="evaluation-error">
                    <h4>❌ 評価エラー</h4>
                    <p>${message}</p>
                    <button class="btn btn-sm btn-outline-primary" onclick="window.claudeRenderer.triggerClaudeEvaluation()">
                        🔄 再試行
                    </button>
                </div>
            `;
        }
    }
}

// クラスをグローバルに公開
window.ClaudeRenderer = ClaudeRenderer;

// グローバル関数
function triggerClaudeEvaluation() {
    if (window.claudeRenderer) {
        window.claudeRenderer.triggerClaudeEvaluation();
    } else {
        console.error('❌ claudeRendererが初期化されていません');
    }
}

// 初期化
document.addEventListener('DOMContentLoaded', function() {
    console.log('�� ClaudeRenderer初期化開始');
    
    if (window.ClaudeRenderer) {
        window.claudeRenderer = new window.ClaudeRenderer();
        console.log('✅ ClaudeRenderer初期化完了');
        
        // 構造データが存在する場合、初期更新を実行
        if (window.structureData) {
            console.log('🔄 初期構造データを検出、Claude評価を更新');
            window.claudeRenderer.updateFromStructureData(window.structureData);
        }
    } else {
        console.warn('⚠️ ClaudeRendererクラスが見つかりません');
    }
}); 