/**
 * モジュール差分表示ハンドラー
 * Claude構成とGemini補完のモジュール差分を可視化
 */

class ModuleDiffHandler {
    constructor() {
        console.log('🔍 ModuleDiffHandler初期化');
        this.container = null;
        this.isInitialized = false;
        this.diffData = null;
        this.structureId = null;
        
        this.init();
    }

    // 初期化
    init() {
        console.log('🔍 ModuleDiffHandler初期化開始');
        
        // 構造IDを取得
        this.structureId = this.getStructureId();
        if (!this.structureId) {
            console.warn('⚠️ 構造IDが取得できません');
            return;
        }
        
        // コンテナ要素の取得
        this.container = document.getElementById('module-diff-container');
        if (!this.container) {
            console.warn('⚠️ モジュール差分表示コンテナが見つかりません');
            return;
        }
        
        this.isInitialized = true;
        console.log('✅ ModuleDiffHandler初期化完了');
    }

    // 構造IDを取得
    getStructureId() {
        // URLから構造IDを取得
        const path = window.location.pathname;
        const match = path.match(/\/unified\/([^\/]+)/);
        return match ? match[1] : null;
    }

    // APIからモジュール差分データを取得
    async fetchModuleDiff() {
        if (!this.structureId) {
            console.error('❌ 構造IDが設定されていません');
            return null;
        }

        try {
            console.log('📡 モジュール差分データを取得中...');
            
            const response = await fetch(`/unified/${this.structureId}/module-diff`);
            const data = await response.json();
            
            if (data.status === 'success') {
                console.log('✅ モジュール差分データ取得成功:', {
                    added: data.module_diff.added?.length || 0,
                    removed: data.module_diff.removed?.length || 0,
                    changed: data.module_diff.changed?.length || 0
                });
                return data.module_diff;
            } else {
                console.warn('⚠️ モジュール差分データ取得失敗:', data.message);
                return null;
            }
        } catch (error) {
            console.error('❌ モジュール差分データ取得エラー:', error);
            return null;
        }
    }

    // モジュール差分データを自動取得して表示
    async loadAndDisplayModuleDiff() {
        console.log('🔄 モジュール差分データを自動取得中...');
        
        const diffData = await this.fetchModuleDiff();
        if (diffData) {
            this.setDiffData(diffData);
        } else {
            // データがない場合はクリア状態を表示
            this.clearDiff();
        }
    }

    // モジュール差分データを設定
    setDiffData(diffData) {
        console.log('📋 モジュール差分データを設定:', {
            added: diffData.added?.length || 0,
            removed: diffData.removed?.length || 0,
            changed: diffData.changed?.length || 0
        });
        
        this.diffData = diffData;
        this.renderDiff();
    }

    // 差分を描画
    renderDiff() {
        if (!this.container || !this.diffData) {
            console.warn('⚠️ コンテナまたは差分データがありません');
            return;
        }

        console.log('🎨 モジュール差分を描画中');
        
        // 差分サマリーを更新
        this.updateDiffSummary();
        
        // 各セクションを描画
        this.renderAddedModules();
        this.renderRemovedModules();
        this.renderChangedModules();
        
        // アニメーション効果を追加
        this.addFadeInAnimation();
        
        console.log('✅ モジュール差分描画完了');
    }

    // 差分サマリーを更新
    updateDiffSummary() {
        const summaryContainer = this.container.querySelector('.module-diff-summary');
        if (!summaryContainer) return;

        const addedCount = this.diffData.added?.length || 0;
        const removedCount = this.diffData.removed?.length || 0;
        const changedCount = this.diffData.changed?.length || 0;

        summaryContainer.innerHTML = `
            <span class="diff-summary-item added">
                🟢 追加: ${addedCount}
            </span>
            <span class="diff-summary-item removed">
                🔴 削除: ${removedCount}
            </span>
            <span class="diff-summary-item changed">
                🟡 変更: ${changedCount}
            </span>
        `;
    }

    // 追加されたモジュールを描画
    renderAddedModules() {
        const section = this.container.querySelector('.added-section');
        if (!section) return;

        if (!this.diffData.added || this.diffData.added.length === 0) {
            section.style.display = 'none';
            return;
        }

        section.style.display = 'block';
        const list = section.querySelector('.added-list');
        if (!list) return;

        list.innerHTML = this.diffData.added.map(module => `
            <li class="diff-module-item added">
                <div class="module-name">
                    <span class="diff-icon">＋</span>
                    ${module.name || module.title || '無名モジュール'}
                </div>
                ${module.description ? `
                    <div class="module-description">
                        ${module.description}
                    </div>
                ` : ''}
            </li>
        `).join('');
    }

    // 削除されたモジュールを描画
    renderRemovedModules() {
        const section = this.container.querySelector('.removed-section');
        if (!section) return;

        if (!this.diffData.removed || this.diffData.removed.length === 0) {
            section.style.display = 'none';
            return;
        }

        section.style.display = 'block';
        const list = section.querySelector('.removed-list');
        if (!list) return;

        list.innerHTML = this.diffData.removed.map(module => `
            <li class="diff-module-item removed">
                <div class="module-name">
                    <span class="diff-icon">−</span>
                    ${module.name || module.title || '無名モジュール'}
                </div>
                ${module.description ? `
                    <div class="module-description">
                        ${module.description}
                    </div>
                ` : ''}
            </li>
        `).join('');
    }

    // 変更されたモジュールを描画
    renderChangedModules() {
        const section = this.container.querySelector('.changed-section');
        if (!section) return;

        if (!this.diffData.changed || this.diffData.changed.length === 0) {
            section.style.display = 'none';
            return;
        }

        section.style.display = 'block';
        const list = section.querySelector('.changed-list');
        if (!list) return;

        list.innerHTML = this.diffData.changed.map(module => `
            <li class="diff-module-item changed">
                <div class="module-name">
                    <span class="diff-icon">±</span>
                    ${module.name}
                </div>
                ${module.changes && module.changes.length > 0 ? `
                    <div class="module-changes">
                        <details class="changes-details">
                            <summary class="changes-summary">
                                変更内容を表示 (${module.changes.length}件)
                            </summary>
                            <ul class="changes-list">
                                ${module.changes.map(change => `
                                    <li class="change-item">
                                        <span class="change-field">${change.field}:</span>
                                        <div class="change-values">
                                            <div class="change-before">
                                                <span class="change-label">変更前:</span>
                                                <span class="change-value">${JSON.stringify(change.before)}</span>
                                            </div>
                                            <div class="change-after">
                                                <span class="change-label">変更後:</span>
                                                <span class="change-value">${JSON.stringify(change.after)}</span>
                                            </div>
                                        </div>
                                    </li>
                                `).join('')}
                            </ul>
                        </details>
                    </div>
                ` : ''}
            </li>
        `).join('');
    }

    // フェードインアニメーションを追加
    addFadeInAnimation() {
        const items = this.container.querySelectorAll('.diff-module-item');
        items.forEach((item, index) => {
            item.style.opacity = '0';
            item.style.transform = 'translateY(10px)';
            
            setTimeout(() => {
                item.style.transition = 'all 0.3s ease';
                item.style.opacity = '1';
                item.style.transform = 'translateY(0)';
            }, index * 100);
        });
    }

    // 差分をクリア
    clearDiff() {
        if (this.container) {
            this.container.innerHTML = `
                <div class="module-diff-header">
                    <h3 class="module-diff-title">🔍 モジュール差分</h3>
                    <div class="module-diff-summary">
                        <span class="diff-summary-item">データなし</span>
                    </div>
                </div>
                <div class="module-diff-content">
                    <div class="diff-section no-changes-section">
                        <div class="no-changes-message">
                            <span class="no-changes-icon">📋</span>
                            <h4 class="no-changes-title">差分データがありません</h4>
                            <p class="no-changes-description">
                                Claude構成とGemini補完のモジュール差分を比較してください。
                            </p>
                        </div>
                    </div>
                </div>
            `;
        }
        this.diffData = null;
    }

    // 差分パネルの表示切替
    toggleModuleDiffPanel() {
        console.log('🔍 モジュール差分パネル表示切替');
        
        const panel = document.getElementById('module-diff-panel');
        const button = document.getElementById('toggle-module-diff-btn');
        
        if (panel && button) {
            const isHidden = panel.classList.contains('hidden');
            
            if (isHidden) {
                // パネルを表示
                panel.classList.remove('hidden');
                button.textContent = 'モジュール差分を隠す 🔍';
                button.classList.remove('btn-outline-primary');
                button.classList.add('btn-outline-secondary');
                
                // パネル表示時にデータを自動取得
                this.loadAndDisplayModuleDiff();
            } else {
                // パネルを非表示
                panel.classList.add('hidden');
                button.textContent = 'モジュール差分を表示 🔍';
                button.classList.remove('btn-outline-secondary');
                button.classList.add('btn-outline-primary');
            }
        } else {
            console.warn('⚠️ モジュール差分パネルまたはボタンが見つかりません');
        }
    }

    // 準備完了チェック
    isReady() {
        return this.isInitialized && this.container !== null;
    }
}

// グローバル関数としてモジュール差分パネルの表示切替を提供
function toggleModuleDiffPanel() {
    if (window.moduleDiffHandler && typeof window.moduleDiffHandler.toggleModuleDiffPanel === 'function') {
        window.moduleDiffHandler.toggleModuleDiffPanel();
    } else {
        console.warn('⚠️ ModuleDiffHandlerが初期化されていません');
        
        // フォールバック処理
        const panel = document.getElementById('module-diff-panel');
        const button = document.getElementById('toggle-module-diff-btn');
        
        if (panel && button) {
            const isHidden = panel.classList.contains('hidden');
            
            if (isHidden) {
                panel.classList.remove('hidden');
                button.textContent = 'モジュール差分を隠す 🔍';
            } else {
                panel.classList.add('hidden');
                button.textContent = 'モジュール差分を表示 🔍';
            }
        }
    }
}

// クラスをグローバルに公開
window.ModuleDiff = ModuleDiffHandler; 