/**
 * 履歴表示ハンドラー
 * Claude/Gemini評価履歴の表示・モーダル操作・API連携
 */

class HistoryHandler {
    constructor() {
        console.log('📋 HistoryHandler初期化');
        this.structureId = null;
        this.historyList = [];
        this.currentHistory = null;
        this.isInitialized = false;
        
        this.init();
    }

    // 初期化
    init() {
        console.log('📋 HistoryHandler初期化開始');
        
        // 構造IDを取得
        const container = document.querySelector('.container');
        if (container && container.dataset.structure) {
            const structureDataStr = container.dataset.structure.trim();
            if (structureDataStr && structureDataStr.startsWith('{') && structureDataStr.length > 2) {
                try {
                    const structureData = JSON.parse(structureDataStr);
                    this.structureId = structureData.id;
                    console.log('✅ 構造IDを取得:', this.structureId);
                } catch (e) {
                    console.warn('⚠️ 構造IDの取得に失敗:', e);
                    console.warn('⚠️ 問題のデータ:', structureDataStr);
                    this.structureId = null;
                }
            } else {
                console.warn('⚠️ 構造データが空または不正な形式です:', structureDataStr);
                this.structureId = null;
            }
        } else {
            console.warn('⚠️ 構造データが見つかりません');
            this.structureId = null;
        }
        
        // モーダルテンプレートを追加
        this.addModalTemplates();
        
        this.isInitialized = true;
        console.log('✅ HistoryHandler初期化完了');
    }

    // モーダルテンプレートをDOMに追加
    addModalTemplates() {
        // 既に存在するかチェック
        if (document.getElementById('historyModal')) {
            return;
        }

        const modalHTML = `
            <!-- 履歴詳細モーダル -->
            <div class="history-modal" id="historyModal">
                <div class="history-modal-overlay" onclick="historyHandler.closeHistoryModal()"></div>
                <div class="history-modal-content">
                    <div class="history-modal-header">
                        <h3 id="historyModalTitle">📋 履歴詳細</h3>
                        <button class="history-modal-close" onclick="historyHandler.closeHistoryModal()">
                            <span>&times;</span>
                        </button>
                    </div>
                    <div class="history-modal-body" id="historyModalBody">
                        <!-- 動的に内容が挿入される -->
                    </div>
                    <div class="history-modal-footer">
                        <button class="btn btn-secondary" onclick="historyHandler.closeHistoryModal()">閉じる</button>
                        <button class="btn btn-primary" id="historyModalCompareBtn" onclick="historyHandler.compareWithCurrent()" style="display: none;">
                            🔄 現在と比較
                        </button>
                    </div>
                </div>
            </div>

            <!-- 履歴比較モーダル -->
            <div class="history-compare-modal" id="historyCompareModal">
                <div class="history-compare-modal-overlay" onclick="historyHandler.closeHistoryCompareModal()"></div>
                <div class="history-compare-modal-content">
                    <div class="history-compare-modal-header">
                        <h3>🔄 履歴比較</h3>
                        <button class="history-compare-modal-close" onclick="historyHandler.closeHistoryCompareModal()">
                            <span>&times;</span>
                        </button>
                    </div>
                    <div class="history-compare-modal-body" id="historyCompareModalBody">
                        <!-- 比較結果が動的に挿入される -->
                    </div>
                    <div class="history-compare-modal-footer">
                        <button class="btn btn-secondary" onclick="historyHandler.closeHistoryCompareModal()">閉じる</button>
                    </div>
                </div>
            </div>
        `;

        document.body.insertAdjacentHTML('beforeend', modalHTML);
    }

    // 履歴一覧を取得・表示
    async refreshHistoryList() {
        if (!this.structureId) {
            console.warn('⚠️ 構造IDが設定されていません');
            return;
        }

        console.log('🔄 履歴一覧を取得中:', this.structureId);
        
        try {
            const response = await fetch(`/${this.structureId}/structure-history`);
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const data = await response.json();
            if (data.status === 'success') {
                this.historyList = data.history || [];
                this.renderHistoryList();
                console.log('✅ 履歴一覧を取得:', this.historyList.length, '件');
            } else {
                throw new Error(data.message || '履歴の取得に失敗しました');
            }
        } catch (error) {
            console.error('❌ 履歴取得エラー:', error);
            this.showHistoryError('履歴の取得に失敗しました: ' + error.message);
        }
    }

    // 履歴一覧を描画
    renderHistoryList() {
        const container = document.getElementById('history-content');
        if (!container) {
            console.warn('⚠️ 履歴コンテナが見つかりません');
            return;
        }

        console.log('📋 履歴一覧描画開始');

        if (this.historyList.length === 0) {
            container.innerHTML = `
                <div class="history-placeholder">
                    <div class="history-placeholder-icon">📋</div>
                    <div class="history-placeholder-text">
                        <h4>履歴がありません</h4>
                        <p>まだ評価履歴が保存されていません。</p>
                        <p class="text-muted">Claude評価やGemini補完を実行すると履歴が表示されます。</p>
                    </div>
                </div>
            `;
        } else {
            const historyCards = this.historyList.map((history, index) => this.createHistoryCard(history, index)).join('');
            container.innerHTML = historyCards;
        }

        // 履歴描画後のレイアウト調整
        this.adjustLayoutAfterHistoryRender();
    }

    // 履歴描画後のレイアウト調整
    adjustLayoutAfterHistoryRender() {
        console.log('🎨 履歴描画後のレイアウト調整開始');
        
        // LayoutManagerが存在する場合はレイアウトを再調整
        if (window.layoutManager && typeof window.layoutManager.refreshLayout === 'function') {
            console.log('🔄 LayoutManager.refreshLayout()を実行');
            window.layoutManager.refreshLayout();
        } else if (window.layoutManager && typeof window.layoutManager.resizeAllPanes === 'function') {
            console.log('🔄 LayoutManager.resizeAllPanes()を実行');
            window.layoutManager.resizeAllPanes();
        } else {
            console.log('🔄 フォールバック: 手動レイアウト調整を実行');
            this.manualLayoutAdjustment();
        }

        // 履歴パネルが右ペイン内に正しく配置されているか確認
        this.ensureHistoryPaneInRightPane();
        
        console.log('✅ 履歴描画後のレイアウト調整完了');
    }

    // 手動レイアウト調整（フォールバック）
    manualLayoutAdjustment() {
        console.log('🔧 手動レイアウト調整実行');
        
        // 右ペインの確認と調整
        const rightPane = document.querySelector('.right-pane');
        if (rightPane) {
            // 右ペインが表示されていることを確認
            rightPane.style.display = 'flex';
            rightPane.style.visibility = 'visible';
            rightPane.style.opacity = '1';
            rightPane.style.pointerEvents = 'auto';
            
            // flex設定を確認
            const computedStyle = window.getComputedStyle(rightPane);
            if (!computedStyle.flex || computedStyle.flex === 'none') {
                rightPane.style.flex = '1';
                console.log('✅ 右ペインのflex設定を修正');
            }
        }

        // 履歴パネルが右ペイン内にあることを確認
        const historyPane = document.getElementById('history-pane');
        if (historyPane) {
            // 履歴パネルが独立したペインとして認識されないよう調整
            historyPane.style.position = 'relative';
            historyPane.style.width = '100%';
            historyPane.style.flex = 'none';
            
            // 履歴パネルが右ペインの子要素であることを確認
            const parentPane = historyPane.closest('.right-pane');
            if (!parentPane) {
                console.warn('⚠️ 履歴パネルが右ペインの子要素ではありません');
                // 履歴パネルを右ペイン内に移動
                const rightPaneContent = document.querySelector('.right-pane .pane-content');
                if (rightPaneContent && historyPane.parentElement !== rightPaneContent) {
                    rightPaneContent.appendChild(historyPane);
                    console.log('✅ 履歴パネルを右ペイン内に移動');
                }
            }
        }

        // メインコンテナのレイアウトを確認
        const mainContainer = document.querySelector('.main-container');
        if (mainContainer) {
            mainContainer.style.display = 'flex';
            mainContainer.style.flexDirection = 'row';
            mainContainer.style.width = '100%';
            mainContainer.style.height = '100%';
        }

        console.log('✅ 手動レイアウト調整完了');
    }

    // 履歴パネルが右ペイン内に正しく配置されているか確認
    ensureHistoryPaneInRightPane() {
        console.log('🔍 履歴パネル配置確認');
        
        const historyPane = document.getElementById('history-pane');
        const rightPane = document.querySelector('.right-pane');
        
        if (!historyPane || !rightPane) {
            console.warn('⚠️ 履歴パネルまたは右ペインが見つかりません');
            return;
        }

        // 履歴パネルが右ペインの子要素であることを確認
        const isInRightPane = rightPane.contains(historyPane);
        console.log('📋 履歴パネル配置状況:', {
            isInRightPane: isInRightPane,
            historyPaneParent: historyPane.parentElement?.className,
            rightPaneChildren: Array.from(rightPane.children).map(child => child.className)
        });

        if (!isInRightPane) {
            console.warn('⚠️ 履歴パネルが右ペイン外に配置されています');
            
            // 履歴パネルを右ペイン内に移動
            const rightPaneContent = rightPane.querySelector('.pane-content');
            if (rightPaneContent) {
                rightPaneContent.appendChild(historyPane);
                console.log('✅ 履歴パネルを右ペイン内に移動しました');
            } else {
                console.error('❌ 右ペインのコンテンツエリアが見つかりません');
            }
        } else {
            console.log('✅ 履歴パネルは正しく右ペイン内に配置されています');
        }

        // 履歴パネルが独立したペインとして認識されないよう調整
        historyPane.style.position = 'relative';
        historyPane.style.width = '100%';
        historyPane.style.flex = 'none';
        historyPane.style.display = 'block';
        
        // 履歴パネルが4つ目のペインとして認識されないよう確認
        const allPanes = document.querySelectorAll('.main-container > .pane, .main-container > [class*="pane"]');
        const paneCount = allPanes.length;
        console.log(`🔍 メインコンテナ内のペイン数: ${paneCount}個`);
        
        if (paneCount > 3) {
            console.warn(`⚠️ ペイン数が3個を超えています: ${paneCount}個`);
            console.log('🔍 検出されたペイン:', Array.from(allPanes).map(pane => ({
                className: pane.className,
                id: pane.id,
                tagName: pane.tagName
            })));
        } else {
            console.log('✅ ペイン数は正常です（3個以下）');
        }
    }

    // 履歴カードを作成
    createHistoryCard(history, index) {
        const timestamp = new Date(history.timestamp).toLocaleString('ja-JP');
        const provider = history.provider;
        const providerIcon = provider === 'claude' ? '🤖' : '✨';
        const providerClass = provider === 'claude' ? 'claude' : 'gemini';
        const score = history.score ? `スコア: ${history.score}` : '';
        const comment = history.comment || '';
        
        return `
            <div class="history-card" onclick="historyHandler.showHistoryDetail(${index})">
                <div class="history-card-header">
                    <div class="history-card-provider ${providerClass}">
                        ${providerIcon} ${provider === 'claude' ? 'Claude' : 'Gemini'}
                    </div>
                    <div class="history-card-timestamp">${timestamp}</div>
                </div>
                <div class="history-card-content">
                    <div class="history-card-info">
                        <div class="history-card-title">
                            ${provider === 'claude' ? '評価結果' : '補完結果'}
                            ${score ? `<span class="history-card-score">${score}</span>` : ''}
                        </div>
                        <div class="history-card-details">
                            ${comment ? comment.substring(0, 50) + (comment.length > 50 ? '...' : '') : '詳細なし'}
                        </div>
                    </div>
                    <div class="history-card-actions">
                        <button class="history-card-btn details" onclick="event.stopPropagation(); historyHandler.showHistoryDetail(${index})">
                            詳細
                        </button>
                        ${provider === 'claude' ? `
                            <button class="history-card-btn compare" onclick="event.stopPropagation(); historyHandler.compareWithCurrent(${index})">
                                比較
                            </button>
                        ` : ''}
                    </div>
                </div>
            </div>
        `;
    }

    // 履歴詳細を表示
    showHistoryDetail(index) {
        if (index < 0 || index >= this.historyList.length) {
            console.warn('⚠️ 無効な履歴インデックス:', index);
            return;
        }

        const history = this.historyList[index];
        this.currentHistory = history;
        
        console.log('📋 履歴詳細を表示:', history);
        
        const modal = document.getElementById('historyModal');
        const title = document.getElementById('historyModalTitle');
        const body = document.getElementById('historyModalBody');
        const compareBtn = document.getElementById('historyModalCompareBtn');
        
        // タイトル設定
        const providerName = history.provider === 'claude' ? 'Claude' : 'Gemini';
        title.textContent = `📋 ${providerName}履歴詳細`;
        
        // 比較ボタンの表示/非表示
        compareBtn.style.display = history.provider === 'claude' ? 'inline-block' : 'none';
        
        // 詳細内容を生成
        body.innerHTML = this.createHistoryDetailContent(history);
        
        // モーダル表示
        modal.classList.add('show');
        
        // bodyにスクロール抑制クラスを追加
        document.body.classList.add('modal-open');
    }

    // 履歴詳細内容を作成
    createHistoryDetailContent(history) {
        const timestamp = new Date(history.timestamp).toLocaleString('ja-JP');
        const provider = history.provider;
        
        let content = `
            <div class="history-detail-section">
                <h4>📊 基本情報</h4>
                <div class="history-detail-item">
                    <span class="history-detail-label">プロバイダー</span>
                    <span class="history-detail-value">${provider === 'claude' ? 'Claude' : 'Gemini'}</span>
                </div>
                <div class="history-detail-item">
                    <span class="history-detail-label">タイムスタンプ</span>
                    <span class="history-detail-value">${timestamp}</span>
                </div>
        `;
        
        if (history.score !== undefined && history.score !== null) {
            content += `
                <div class="history-detail-item">
                    <span class="history-detail-label">評価スコア</span>
                    <span class="history-detail-value">${history.score}</span>
                </div>
            `;
        }
        
        if (history.comment) {
            content += `
                <div class="history-detail-item">
                    <span class="history-detail-label">コメント</span>
                    <span class="history-detail-value"></span>
                </div>
                <div class="history-detail-comment">${history.comment}</div>
            `;
        }
        
        content += `</div>`;
        
        // 構造データの表示
        if (history.structure) {
            content += `
                <div class="history-detail-section">
                    <h4>🏗️ 構成データ</h4>
                    <div class="history-detail-structure">
                        <pre>${JSON.stringify(history.structure, null, 2)}</pre>
                    </div>
                </div>
            `;
        }
        
        return content;
    }

    // 現在の構成と比較
    async compareWithCurrent(historyIndex = null) {
        if (!this.structureId) {
            console.warn('⚠️ 構造IDが設定されていません');
            return;
        }

        const history = historyIndex !== null ? this.historyList[historyIndex] : this.currentHistory;
        if (!history) {
            console.warn('⚠️ 比較対象の履歴がありません');
            return;
        }

        console.log('🔄 履歴比較を実行:', history);
        
        try {
            // 現在の構造データを取得
            const container = document.querySelector('.container');
            if (!container || !container.dataset.structure) {
                throw new Error('現在の構造データが見つかりません');
            }
            
            const currentStructure = JSON.parse(container.dataset.structure);
            
            // 比較APIを呼び出し
            const response = await fetch(`/${this.structureId}/structure-history/compare`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    current: currentStructure,
                    history: history.structure
                })
            });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const data = await response.json();
            if (data.status === 'success') {
                this.showCompareResult(data.comparison);
            } else {
                throw new Error(data.message || '比較に失敗しました');
            }
        } catch (error) {
            console.error('❌ 履歴比較エラー:', error);
            alert('履歴比較に失敗しました: ' + error.message);
        }
    }

    // 比較結果を表示
    showCompareResult(comparison) {
        const modal = document.getElementById('historyCompareModal');
        const body = document.getElementById('historyCompareModalBody');
        
        // 比較結果を生成
        body.innerHTML = this.createCompareResultContent(comparison);
        
        // モーダル表示
        modal.classList.add('show');
        
        // bodyにスクロール抑制クラスを追加
        document.body.classList.add('modal-open');
    }

    // 比較結果内容を作成
    createCompareResultContent(comparison) {
        return `
            <div class="history-detail-section">
                <h4>🔄 比較結果</h4>
                <div class="history-detail-structure">
                    <pre>${JSON.stringify(comparison, null, 2)}</pre>
                </div>
            </div>
        `;
    }

    // 履歴モーダルを閉じる
    closeHistoryModal() {
        const modal = document.getElementById('historyModal');
        modal.classList.remove('show');
        this.currentHistory = null;
        
        // bodyからスクロール抑制クラスを削除
        document.body.classList.remove('modal-open');
    }

    // 履歴比較モーダルを閉じる
    closeHistoryCompareModal() {
        const modal = document.getElementById('historyCompareModal');
        modal.classList.remove('show');
        
        // bodyからスクロール抑制クラスを削除
        document.body.classList.remove('modal-open');
    }

    // 履歴エラーを表示
    showHistoryError(message) {
        const container = document.getElementById('history-content');
        if (container) {
            container.innerHTML = `
                <div class="history-placeholder">
                    <div class="history-placeholder-icon">⚠️</div>
                    <div class="history-placeholder-text">
                        <h4>エラーが発生しました</h4>
                        <p>${message}</p>
                        <p class="text-muted">「更新」ボタンを押して再試行してください。</p>
                    </div>
                </div>
            `;
        }
    }

    // 履歴パネルの表示/非表示を切り替え
    toggleHistoryPane() {
        const pane = document.getElementById('history-pane');
        const content = document.getElementById('history-content');
        const icon = document.getElementById('history-toggle-icon');
        
        if (content.style.display === 'none') {
            content.style.display = 'block';
            icon.textContent = '▼';
        } else {
            content.style.display = 'none';
            icon.textContent = '▶';
        }
    }
}

// クラスをグローバルに公開
window.HistoryHandler = HistoryHandler;

// グローバル関数を公開（後方互換性のため）
window.refreshHistoryList = function() {
    if (window.historyHandler) {
        window.historyHandler.refreshHistoryList();
    }
};

window.toggleHistoryPane = function() {
    if (window.historyHandler) {
        window.historyHandler.toggleHistoryPane();
    }
};

window.showHistoryDetail = function(index) {
    if (window.historyHandler) {
        window.historyHandler.showHistoryDetail(index);
    }
};

window.compareWithCurrent = function(index) {
    if (window.historyHandler) {
        window.historyHandler.compareWithCurrent(index);
    }
};

window.closeHistoryModal = function() {
    if (window.historyHandler) {
        window.historyHandler.closeHistoryModal();
    }
};

window.closeHistoryCompareModal = function() {
    if (window.historyHandler) {
        window.historyHandler.closeHistoryCompareModal();
    }
}; 