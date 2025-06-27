/**
 * 履歴差分表示用JavaScript
 * 前後ボタンで履歴を切り替え、Ajaxで差分データを取得・表示
 */

class HistoryDiffManager {
    constructor(structureId) {
        this.structureId = structureId;
        this.currentIndex = 0;
        this.totalCount = 0;
        this.isLoading = false;
        
        this.init();
    }
    
    init() {
        // 初期データを読み込み
        this.loadDiffData(0);
        
        // ボタンイベントを設定
        this.setupEventListeners();
    }
    
    setupEventListeners() {
        // 前へボタン
        const prevBtn = document.querySelector('[data-history-index="prev"]');
        if (prevBtn) {
            prevBtn.addEventListener('click', () => {
                if (!this.isLoading && this.currentIndex < this.totalCount - 1) {
                    this.loadDiffData(this.currentIndex + 1);
                }
            });
        }
        
        // 次へボタン
        const nextBtn = document.querySelector('[data-history-index="next"]');
        if (nextBtn) {
            nextBtn.addEventListener('click', () => {
                if (!this.isLoading && this.currentIndex > 0) {
                    this.loadDiffData(this.currentIndex - 1);
                }
            });
        }
    }
    
    async loadDiffData(index) {
        if (this.isLoading) return;
        
        this.isLoading = true;
        this.showLoading(true);
        
        try {
            const response = await fetch(`/logs/api/structure/${this.structureId}?index=${index}`);
            const result = await response.json();
            
            if (result.success) {
                this.updateDiffDisplay(result.data);
                this.currentIndex = result.data.index;
                this.totalCount = result.data.total_count;
                this.updateButtonStates();
            } else {
                console.error('履歴データの取得に失敗:', result.error);
                this.showError(result.error);
            }
        } catch (error) {
            console.error('API呼び出しエラー:', error);
            this.showError('ネットワークエラーが発生しました');
        } finally {
            this.isLoading = false;
            this.showLoading(false);
        }
    }
    
    updateDiffDisplay(diffData) {
        const previousContent = document.getElementById('previousContent');
        const currentContent = document.getElementById('currentContent');
        
        if (!previousContent || !currentContent) return;
        
        // 前の履歴データを表示
        if (diffData.previous_content) {
            previousContent.innerHTML = this.formatHistoryContent(diffData.previous_content, 'previous');
        } else {
            previousContent.innerHTML = '<div class="no-diff">前の履歴がありません</div>';
        }
        
        // 現在の履歴データを表示
        if (diffData.current_content) {
            currentContent.innerHTML = this.formatHistoryContent(diffData.current_content, 'current');
        } else {
            currentContent.innerHTML = '<div class="no-diff">現在の履歴がありません</div>';
        }
        
        // タイムスタンプとソース情報を更新
        this.updateDiffInfo(diffData);
    }
    
    formatHistoryContent(historyData, type) {
        let html = '';
        
        // タイムスタンプ
        const timestamp = historyData.timestamp ? 
            new Date(historyData.timestamp).toLocaleString('ja-JP') : '不明';
        html += `<div class="history-timestamp">${timestamp}</div>`;
        
        // 評価履歴
        if (historyData.evaluations && historyData.evaluations.length > 0) {
            html += '<div class="history-section"><h4>評価履歴</h4>';
            historyData.evaluations.forEach(evaluationItem => {
                const score = evaluationItem.score ? `${(evaluationItem.score * 100).toFixed(1)}%` : 'N/A';
                html += `<div class="eval-item">
                    <div class="eval-score">スコア: ${score}</div>
                    <div class="eval-feedback">${evaluationItem.feedback || 'フィードバックなし'}</div>
                </div>`;
            });
            html += '</div>';
        }
        
        // 補完履歴
        if (historyData.completions && historyData.completions.length > 0) {
            html += '<div class="history-section"><h4>補完履歴</h4>';
            historyData.completions.forEach(comp => {
                html += `<div class="comp-item">
                    <pre class="comp-content">${comp.content || '補完内容なし'}</pre>
                </div>`;
            });
            html += '</div>';
        }
        
        return html || '<div class="no-content">履歴内容がありません</div>';
    }
    
    updateDiffInfo(diffData) {
        // 差分情報表示エリアを更新（存在する場合）
        const infoElement = document.querySelector('.diff-info');
        if (infoElement) {
            const timestamp = diffData.timestamp ? 
                new Date(diffData.timestamp).toLocaleString('ja-JP') : '不明';
            infoElement.innerHTML = `
                <div>履歴 ${diffData.index + 1} / ${diffData.total_count}</div>
                <div>タイムスタンプ: ${timestamp}</div>
                <div>ソース: ${diffData.source}</div>
            `;
        }
    }
    
    updateButtonStates() {
        const prevBtn = document.querySelector('[data-history-index="prev"]');
        const nextBtn = document.querySelector('[data-history-index="next"]');
        
        if (prevBtn) {
            prevBtn.disabled = this.currentIndex >= this.totalCount - 1;
        }
        
        if (nextBtn) {
            nextBtn.disabled = this.currentIndex <= 0;
        }
    }
    
    showLoading(show) {
        const loadingElement = document.querySelector('.diff-loading');
        if (loadingElement) {
            loadingElement.style.display = show ? 'block' : 'none';
        }
        
        // ボタンを無効化
        const buttons = document.querySelectorAll('[data-history-index]');
        buttons.forEach(btn => {
            btn.disabled = show;
        });
    }
    
    showError(message) {
        const previousContent = document.getElementById('previousContent');
        const currentContent = document.getElementById('currentContent');
        
        if (previousContent) {
            previousContent.innerHTML = `<div class="error">エラー: ${message}</div>`;
        }
        if (currentContent) {
            currentContent.innerHTML = `<div class="error">エラー: ${message}</div>`;
        }
    }
}

// ページ読み込み時に初期化
document.addEventListener('DOMContentLoaded', function() {
    // structure_idを取得（URLパスから）
    const pathParts = window.location.pathname.split('/');
    const structureId = pathParts[pathParts.length - 1];
    
    if (structureId && structureId !== 'structure') {
        new HistoryDiffManager(structureId);
    }
}); 