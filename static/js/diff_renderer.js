/**
 * 構造差分レンダラー
 * Claude評価結果とGemini補完構成の差分を可視化
 */

class DiffRenderer {
    constructor() {
        console.log('🔍 DiffRenderer初期化');
        this.container = null;
        this.isInitialized = false;
        this.animationDuration = 300;
        
        this.init();
    }

    // 初期化
    init() {
        console.log('🔍 DiffRenderer初期化開始');
        
        // コンテナ要素の取得
        this.container = document.getElementById('diff-pane');
        if (!this.container) {
            console.warn('⚠️ 差分表示コンテナが見つかりません');
            return;
        }
        
        this.isInitialized = true;
        console.log('✅ DiffRenderer初期化完了');
    }

    // 構造差分を描画
    renderStructureDiff(claudeData, geminiData, containerElement = null) {
        console.log('🔄 構造差分描画開始:', {
            hasClaudeData: !!claudeData,
            hasGeminiData: !!geminiData,
            claudeKeys: claudeData ? Object.keys(claudeData) : 'null',
            geminiKeys: geminiData ? Object.keys(geminiData) : 'null'
        });

        const container = containerElement || this.container;
        if (!container) {
            console.error('❌ 差分表示コンテナが見つかりません');
            return;
        }

        // データの正規化
        const normalizedClaude = this.normalizeStructureData(claudeData);
        const normalizedGemini = this.normalizeStructureData(geminiData);

        // 差分の計算
        const diffResult = this.calculateStructureDiff(normalizedClaude, normalizedGemini);

        // 差分の描画
        this.renderDiffResult(diffResult, container);

        // アニメーション効果
        this.addFadeInAnimation(container);
    }

    // 構造データの正規化
    normalizeStructureData(data) {
        if (!data) return null;

        // 優先順位: structure > modules > 直接データ
        let normalized = null;
        
        if (data.structure) {
            normalized = data.structure;
        } else if (data.modules) {
            normalized = {
                title: data.title || '構成',
                modules: data.modules
            };
        } else if (data.title || data.modules) {
            normalized = {
                title: data.title || '構成',
                modules: data.modules || []
            };
        } else {
            normalized = data;
        }

        console.log('📋 データ正規化結果:', {
            originalKeys: Object.keys(data),
            normalizedKeys: Object.keys(normalized),
            hasTitle: !!normalized.title,
            modulesCount: normalized.modules ? normalized.modules.length : 0
        });

        return normalized;
    }

    // 構造差分の計算
    calculateStructureDiff(claudeData, geminiData) {
        console.log('🔍 差分計算開始');

        const result = {
            title: this.compareField('title', claudeData?.title, geminiData?.title),
            modules: this.compareModules(claudeData?.modules || [], geminiData?.modules || []),
            summary: {
                added: 0,
                removed: 0,
                modified: 0,
                unchanged: 0
            }
        };

        // サマリーの計算
        result.modules.forEach(module => {
            if (module.status === 'added') result.summary.added++;
            else if (module.status === 'removed') result.summary.removed++;
            else if (module.status === 'modified') result.summary.modified++;
            else if (module.status === 'unchanged') result.summary.unchanged++;
        });

        console.log('✅ 差分計算完了:', result.summary);
        return result;
    }

    // フィールド比較
    compareField(fieldName, claudeValue, geminiValue) {
        const isEqual = JSON.stringify(claudeValue) === JSON.stringify(geminiValue);
        return {
            field: fieldName,
            claude: claudeValue,
            gemini: geminiValue,
            status: isEqual ? 'unchanged' : 'modified'
        };
    }

    // モジュール比較
    compareModules(claudeModules, geminiModules) {
        console.log('🔍 モジュール比較開始:', {
            claudeCount: claudeModules.length,
            geminiCount: geminiModules.length
        });

        const result = [];
        const claudeMap = new Map();
        const geminiMap = new Map();

        // Claudeモジュールをマップ化
        claudeModules.forEach((module, index) => {
            const key = this.getModuleKey(module);
            claudeMap.set(key, { module, index });
        });

        // Geminiモジュールをマップ化
        geminiModules.forEach((module, index) => {
            const key = this.getModuleKey(module);
            geminiMap.set(key, { module, index });
        });

        // 全キーを収集
        const allKeys = new Set([...claudeMap.keys(), ...geminiMap.keys()]);

        // 各キーについて差分を計算
        allKeys.forEach(key => {
            const claudeEntry = claudeMap.get(key);
            const geminiEntry = geminiMap.get(key);

            if (!claudeEntry && geminiEntry) {
                // 追加されたモジュール
                result.push({
                    key: key,
                    status: 'added',
                    claude: null,
                    gemini: geminiEntry.module,
                    changes: this.getModuleChanges(null, geminiEntry.module)
                });
            } else if (claudeEntry && !geminiEntry) {
                // 削除されたモジュール
                result.push({
                    key: key,
                    status: 'removed',
                    claude: claudeEntry.module,
                    gemini: null,
                    changes: this.getModuleChanges(claudeEntry.module, null)
                });
            } else if (claudeEntry && geminiEntry) {
                // 両方に存在するモジュール
                const changes = this.getModuleChanges(claudeEntry.module, geminiEntry.module);
                const status = changes.length > 0 ? 'modified' : 'unchanged';
                
                result.push({
                    key: key,
                    status: status,
                    claude: claudeEntry.module,
                    gemini: geminiEntry.module,
                    changes: changes
                });
            }
        });

        console.log('✅ モジュール比較完了:', {
            totalModules: result.length,
            added: result.filter(r => r.status === 'added').length,
            removed: result.filter(r => r.status === 'removed').length,
            modified: result.filter(r => r.status === 'modified').length,
            unchanged: result.filter(r => r.status === 'unchanged').length
        });

        return result;
    }

    // モジュールキーの取得
    getModuleKey(module) {
        // 優先順位: id > title > インデックス
        if (module.id) return module.id;
        if (module.title) return module.title;
        return JSON.stringify(module); // フォールバック
    }

    // モジュール変更点の取得
    getModuleChanges(claudeModule, geminiModule) {
        const changes = [];
        
        if (!claudeModule && !geminiModule) return changes;
        
        const fields = ['title', 'type', 'description', 'content'];
        
        fields.forEach(field => {
            const claudeValue = claudeModule?.[field];
            const geminiValue = geminiModule?.[field];
            
            if (JSON.stringify(claudeValue) !== JSON.stringify(geminiValue)) {
                changes.push({
                    field: field,
                    claude: claudeValue,
                    gemini: geminiValue,
                    status: !claudeValue ? 'added' : !geminiValue ? 'removed' : 'modified'
                });
            }
        });

        return changes;
    }

    // 差分結果の描画
    renderDiffResult(diffResult, container) {
        console.log('🎨 差分結果描画開始');

        const hasChanges = diffResult.title.status !== 'unchanged' || 
                          diffResult.modules.some(m => m.status !== 'unchanged');

        if (!hasChanges) {
            container.innerHTML = `
                <div class="diff-no-changes">
                    <div class="diff-no-changes-icon">✅</div>
                    <div class="diff-no-changes-text">
                        <h4>差分なし</h4>
                        <p>Claude評価とGemini補完の構成は一致しています。</p>
                    </div>
                </div>
            `;
            return;
        }

        let html = `
            <div class="diff-container">
                <div class="diff-header">
                    <h3>🔍 構成差分</h3>
                    <div class="diff-summary">
                        <span class="diff-summary-item added">+${diffResult.summary.added}</span>
                        <span class="diff-summary-item removed">-${diffResult.summary.removed}</span>
                        <span class="diff-summary-item modified">~${diffResult.summary.modified}</span>
                        <span class="diff-summary-item unchanged">${diffResult.summary.unchanged}</span>
                    </div>
                </div>
        `;

        // タイトルの差分
        if (diffResult.title.status !== 'unchanged') {
            html += this.renderTitleDiff(diffResult.title);
        }

        // モジュールの差分
        const changedModules = diffResult.modules.filter(m => m.status !== 'unchanged');
        if (changedModules.length > 0) {
            html += '<div class="diff-modules">';
            changedModules.forEach(module => {
                html += this.renderModuleDiff(module);
            });
            html += '</div>';
        }

        html += '</div>';
        container.innerHTML = html;
    }

    // タイトル差分の描画
    renderTitleDiff(titleDiff) {
        return `
            <div class="diff-title ${titleDiff.status}">
                <div class="diff-title-header">
                    <span class="diff-icon">📝</span>
                    <span class="diff-label">タイトル</span>
                    <span class="diff-status">${this.getStatusLabel(titleDiff.status)}</span>
                </div>
                <div class="diff-content">
                    <div class="diff-old">
                        <span class="diff-label">Claude:</span>
                        <span class="diff-value">${titleDiff.claude || '-'}</span>
                    </div>
                    <div class="diff-new">
                        <span class="diff-label">Gemini:</span>
                        <span class="diff-value">${titleDiff.gemini || '-'}</span>
                    </div>
                </div>
            </div>
        `;
    }

    // モジュール差分の描画
    renderModuleDiff(moduleDiff) {
        const moduleTitle = moduleDiff.gemini?.title || moduleDiff.claude?.title || 'モジュール';
        const moduleType = moduleDiff.gemini?.type || moduleDiff.claude?.type || 'unknown';
        
        let html = `
            <div class="diff-module ${moduleDiff.status}">
                <div class="diff-module-header">
                    <span class="diff-icon">${this.getModuleIcon(moduleType)}</span>
                    <span class="diff-label">${moduleTitle}</span>
                    <span class="diff-status">${this.getStatusLabel(moduleDiff.status)}</span>
                </div>
        `;

        if (moduleDiff.changes.length > 0) {
            html += '<div class="diff-module-changes">';
            moduleDiff.changes.forEach(change => {
                html += this.renderFieldChange(change);
            });
            html += '</div>';
        }

        html += '</div>';
        return html;
    }

    // フィールド変更の描画
    renderFieldChange(change) {
        return `
            <div class="diff-field ${change.status}">
                <div class="diff-field-header">
                    <span class="diff-field-name">${this.getFieldLabel(change.field)}</span>
                    <span class="diff-field-status">${this.getStatusLabel(change.status)}</span>
                </div>
                <div class="diff-field-content">
                    <div class="diff-old">
                        <span class="diff-label">Claude:</span>
                        <span class="diff-value">${change.claude || '-'}</span>
                    </div>
                    <div class="diff-new">
                        <span class="diff-label">Gemini:</span>
                        <span class="diff-value">${change.gemini || '-'}</span>
                    </div>
                </div>
            </div>
        `;
    }

    // ステータスラベルの取得
    getStatusLabel(status) {
        const labels = {
            'added': '追加',
            'removed': '削除',
            'modified': '変更',
            'unchanged': '変更なし'
        };
        return labels[status] || status;
    }

    // モジュールアイコンの取得
    getModuleIcon(type) {
        const icons = {
            'ui': '🎨',
            'api': '🔌',
            'database': '🗄️',
            'auth': '🔐',
            'file': '📁',
            'email': '📧',
            'notification': '🔔',
            'payment': '💳',
            'search': '🔍',
            'report': '📊',
            'admin': '⚙️',
            'user': '👤'
        };
        return icons[type] || '📦';
    }

    // フィールドラベルの取得
    getFieldLabel(field) {
        const labels = {
            'title': 'タイトル',
            'type': 'タイプ',
            'description': '説明',
            'content': '内容'
        };
        return labels[field] || field;
    }

    // フェードインアニメーション
    addFadeInAnimation(element) {
        element.style.opacity = '0';
        element.style.transform = 'translateY(10px)';
        
        setTimeout(() => {
            element.style.transition = `opacity ${this.animationDuration}ms ease, transform ${this.animationDuration}ms ease`;
            element.style.opacity = '1';
            element.style.transform = 'translateY(0)';
            
            setTimeout(() => {
                element.style.transition = '';
                element.style.transform = '';
            }, this.animationDuration);
        }, 10);
    }

    // 差分表示の表示/非表示切り替え
    toggleDiffPane() {
        if (!this.container) return;
        
        const isVisible = this.container.style.display !== 'none';
        this.container.style.display = isVisible ? 'none' : 'block';
        
        if (!isVisible) {
            this.addFadeInAnimation(this.container);
        }
        
        // 差分表示後のレイアウト調整
        this.adjustLayoutAfterDiffRender();
    }

    // 差分表示後のレイアウト調整
    adjustLayoutAfterDiffRender() {
        console.log('🎨 差分表示後のレイアウト調整開始');
        
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

        // 差分パネルが右ペイン内に正しく配置されているか確認
        this.ensureDiffPanelInRightPane();
        
        console.log('✅ 差分表示後のレイアウト調整完了');
    }

    // 手動レイアウト調整（フォールバック）
    manualLayoutAdjustment() {
        console.log('🔧 差分表示 - 手動レイアウト調整実行');
        
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
                console.log('✅ 右ペインのflex設定を修正（差分表示）');
            }
        }

        // 差分パネルが右ペイン内にあることを確認
        const diffPanel = document.getElementById('diff-panel');
        if (diffPanel) {
            // 差分パネルが独立したペインとして認識されないよう調整
            diffPanel.style.position = 'relative';
            diffPanel.style.width = '100%';
            diffPanel.style.flex = 'none';
            
            // 差分パネルが右ペインの子要素であることを確認
            const parentPane = diffPanel.closest('.right-pane');
            if (!parentPane) {
                console.warn('⚠️ 差分パネルが右ペインの子要素ではありません');
                // 差分パネルを右ペイン内に移動
                const rightPaneContent = document.querySelector('.right-pane .pane-content');
                if (rightPaneContent && diffPanel.parentElement !== rightPaneContent) {
                    rightPaneContent.appendChild(diffPanel);
                    console.log('✅ 差分パネルを右ペイン内に移動');
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

        console.log('✅ 差分表示 - 手動レイアウト調整完了');
    }

    // 差分パネルが右ペイン内に正しく配置されているか確認
    ensureDiffPanelInRightPane() {
        console.log('🔍 差分パネル配置確認');
        
        const diffPanel = document.getElementById('diff-panel');
        const rightPane = document.querySelector('.right-pane');
        
        if (!diffPanel || !rightPane) {
            console.warn('⚠️ 差分パネルまたは右ペインが見つかりません');
            return;
        }

        // 差分パネルが右ペインの子要素であることを確認
        const isInRightPane = rightPane.contains(diffPanel);
        console.log('🔍 差分パネル配置状況:', {
            isInRightPane: isInRightPane,
            diffPanelParent: diffPanel.parentElement?.className,
            rightPaneChildren: Array.from(rightPane.children).map(child => child.className)
        });

        if (!isInRightPane) {
            console.warn('⚠️ 差分パネルが右ペイン外に配置されています');
            
            // 差分パネルを右ペイン内に移動
            const rightPaneContent = rightPane.querySelector('.pane-content');
            if (rightPaneContent) {
                rightPaneContent.appendChild(diffPanel);
                console.log('✅ 差分パネルを右ペイン内に移動しました');
            } else {
                console.error('❌ 右ペインのコンテンツエリアが見つかりません');
            }
        } else {
            console.log('✅ 差分パネルは正しく右ペイン内に配置されています');
        }

        // 差分パネルが独立したペインとして認識されないよう調整
        diffPanel.style.position = 'relative';
        diffPanel.style.width = '100%';
        diffPanel.style.flex = 'none';
        diffPanel.style.display = 'block';
        
        // 差分パネルが4つ目のペインとして認識されないよう確認
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

    // 差分表示のクリア
    clearDiff() {
        if (!this.container) return;
        
        this.container.innerHTML = `
            <div class="diff-placeholder">
                <div class="diff-placeholder-icon">🔍</div>
                <div class="diff-placeholder-text">
                    <h4>構成差分</h4>
                    <p>Claude評価とGemini補完の差分がここに表示されます。</p>
                </div>
            </div>
        `;
    }

    // 初期化状態の確認
    isReady() {
        return this.isInitialized && this.container !== null;
    }

    // 差分パネルの表示切替
    toggleDiffPanel() {
        console.log('🔍 差分パネル表示切替');
        
        const panel = document.getElementById('diff-panel');
        const button = document.getElementById('toggle-diff-btn');
        
        if (panel && button) {
            const isHidden = panel.classList.contains('hidden');
            
            if (isHidden) {
                // パネルを表示
                panel.classList.remove('hidden');
                button.textContent = '差分を隠す 🔍';
                button.classList.remove('btn-outline-primary');
                button.classList.add('btn-outline-secondary');
                
                // 差分が未生成の場合は自動更新を試行
                if (panel.querySelector('.diff-placeholder')) {
                    this.refreshDiffContent();
                }
            } else {
                // パネルを非表示
                panel.classList.add('hidden');
                button.textContent = '差分を表示 🔍';
                button.classList.remove('btn-outline-secondary');
                button.classList.add('btn-outline-primary');
            }
        } else {
            console.warn('⚠️ 差分パネルまたはボタンが見つかりません');
        }
    }

    // 差分コンテンツの更新
    refreshDiffContent() {
        console.log('🔄 差分コンテンツ更新中');
        
        // 構造データから差分を再生成
        if (window.structureData && window.structureData.diff_html) {
            const panel = document.getElementById('diff-panel');
            if (panel) {
                panel.innerHTML = `
                    <div class="diff-content">
                        ${window.structureData.diff_html}
                    </div>
                `;
                console.log('✅ 差分コンテンツを更新しました');
            }
        }
    }
}

// クラスをグローバルに公開
window.DiffRenderer = DiffRenderer;

// グローバル関数としても公開
window.renderStructureDiff = function(claudeData, geminiData, containerElement) {
    if (!window.diffRenderer) {
        window.diffRenderer = new DiffRenderer();
    }
    window.diffRenderer.renderStructureDiff(claudeData, geminiData, containerElement);
};

// テスト用のサンプルデータ
window.testDiffRenderer = function() {
    console.log('🧪 差分レンダラーのテスト開始');
    
    const sampleClaudeData = {
        title: "ECサイト",
        modules: [
            {
                id: "user_management",
                title: "ユーザー管理",
                type: "auth",
                description: "ユーザーの登録・認証機能"
            },
            {
                id: "product_catalog",
                title: "商品カタログ",
                type: "database",
                description: "商品情報の管理"
            },
            {
                id: "order_management",
                title: "注文管理",
                type: "api",
                description: "注文処理機能"
            }
        ]
    };
    
    const sampleGeminiData = {
        title: "ECサイトシステム",
        modules: [
            {
                id: "user_management",
                title: "ユーザー管理システム",
                type: "auth",
                description: "ユーザーの登録・認証・プロフィール管理機能"
            },
            {
                id: "product_catalog",
                title: "商品カタログ",
                type: "database",
                description: "商品情報の管理"
            },
            {
                id: "payment_system",
                title: "決済システム",
                type: "payment",
                description: "クレジットカード決済機能"
            }
        ]
    };
    
    if (window.diffRenderer) {
        window.diffRenderer.renderStructureDiff(sampleClaudeData, sampleGeminiData);
        console.log('✅ テスト差分描画完了');
    } else {
        console.error('❌ diffRendererが見つかりません');
    }
};

// グローバル関数として差分パネルの表示切替を提供
function toggleDiffPanel() {
    if (window.diffRenderer && typeof window.diffRenderer.toggleDiffPanel === 'function') {
        window.diffRenderer.toggleDiffPanel();
    } else {
        console.warn('⚠️ DiffRendererが初期化されていません');
        
        // フォールバック処理
        const panel = document.getElementById('diff-panel');
        const button = document.getElementById('toggle-diff-btn');
        
        if (panel && button) {
            const isHidden = panel.classList.contains('hidden');
            
            if (isHidden) {
                panel.classList.remove('hidden');
                button.textContent = '差分を隠す 🔍';
            } else {
                panel.classList.add('hidden');
                button.textContent = '差分を表示 🔍';
            }
        }
    }
} 