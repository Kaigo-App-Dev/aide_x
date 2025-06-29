/**
 * 構成UIの簡易プレビューレンダラー
 * 将来的に右ペインでフォームやテーブルなどのUIプレビューを表示するための枠組み
 */

class UIRenderer {
    constructor() {
        console.log('🎨 UIRenderer初期化');
        this.container = null;
        this.isInitialized = false;
        this.currentData = null;
        
        this.init();
    }

    // 初期化
    init() {
        console.log('🎨 UIRenderer初期化開始');
        
        // コンテナ要素の取得（将来的に右ペインに追加予定）
        this.container = document.getElementById('ui-preview-container');
        if (!this.container) {
            console.log('ℹ️ UIプレビューコンテナが見つかりません（将来的に追加予定）');
            return;
        }
        
        this.isInitialized = true;
        console.log('✅ UIRenderer初期化完了');
    }

    // モジュールデータからUIをレンダリング
    renderModuleUI(moduleData) {
        console.log('🎨 モジュールUIレンダリング開始:', {
            type: moduleData.type,
            title: moduleData.title,
            hasContent: !!moduleData.content
        });

        if (!moduleData || !moduleData.type) {
            return this.renderRawJson(moduleData);
        }

        switch (moduleData.type.toLowerCase()) {
            case 'form':
                return this.renderForm(moduleData);
            case 'table':
                return this.renderTable(moduleData);
            case 'chart':
                return this.renderChart(moduleData);
            case 'api':
                return this.renderAPI(moduleData);
            case 'auth':
                return this.renderAuth(moduleData);
            case 'database':
                return this.renderDatabase(moduleData);
            case 'config':
                return this.renderConfig(moduleData);
            case 'page':
                return this.renderPage(moduleData);
            case 'component':
                return this.renderComponent(moduleData);
            default:
                return this.renderRawJson(moduleData);
        }
    }

    // フォームUIをレンダリング
    renderForm(moduleData) {
        const fields = moduleData.fields || moduleData.content || {};
        const title = moduleData.title || 'フォーム';
        const description = moduleData.description || '';

        let formHTML = `
            <div class="ui-preview form-preview">
                <div class="preview-header">
                    <h3>📝 ${title}</h3>
                    ${description ? `<p class="preview-description">${description}</p>` : ''}
                </div>
                <div class="preview-content">
                    <form class="preview-form">
        `;

        Object.entries(fields).forEach(([fieldName, fieldConfig]) => {
            const fieldType = this.getFieldType(fieldConfig);
            const fieldLabel = fieldConfig.label || fieldConfig.title || fieldName;
            const fieldPlaceholder = fieldConfig.placeholder || fieldConfig.hint || '';
            const fieldRequired = fieldConfig.required || false;

            formHTML += `
                <div class="form-field">
                    <label class="field-label">
                        ${fieldLabel}
                        ${fieldRequired ? '<span class="required">*</span>' : ''}
                    </label>
                    ${this.renderFormField(fieldName, fieldType, fieldConfig, fieldPlaceholder)}
                </div>
            `;
        });

        formHTML += `
                    <div class="form-actions">
                        <button type="submit" class="btn btn-primary">送信</button>
                        <button type="reset" class="btn btn-secondary">リセット</button>
                    </div>
                </form>
            </div>
        </div>
        `;

        return formHTML;
    }

    // フォームフィールドをレンダリング
    renderFormField(fieldName, fieldType, fieldConfig, placeholder) {
        const fieldId = `preview-${fieldName}`;
        
        switch (fieldType) {
            case 'textarea':
                return `<textarea id="${fieldId}" name="${fieldName}" placeholder="${placeholder}" class="form-control"></textarea>`;
            
            case 'select':
                const options = fieldConfig.options || [];
                let selectHTML = `<select id="${fieldId}" name="${fieldName}" class="form-control">`;
                options.forEach(option => {
                    selectHTML += `<option value="${option.value || option}">${option.label || option}</option>`;
                });
                selectHTML += '</select>';
                return selectHTML;
            
            case 'checkbox':
                return `<input type="checkbox" id="${fieldId}" name="${fieldName}" class="form-check-input">`;
            
            case 'radio':
                const radioOptions = fieldConfig.options || [];
                let radioHTML = '';
                radioOptions.forEach((option, index) => {
                    const radioId = `${fieldId}-${index}`;
                    radioHTML += `
                        <div class="form-check">
                            <input type="radio" id="${radioId}" name="${fieldName}" value="${option.value || option}" class="form-check-input">
                            <label class="form-check-label" for="${radioId}">${option.label || option}</label>
                        </div>
                    `;
                });
                return radioHTML;
            
            case 'number':
                return `<input type="number" id="${fieldId}" name="${fieldName}" placeholder="${placeholder}" class="form-control">`;
            
            case 'email':
                return `<input type="email" id="${fieldId}" name="${fieldName}" placeholder="${placeholder}" class="form-control">`;
            
            case 'password':
                return `<input type="password" id="${fieldId}" name="${fieldName}" placeholder="${placeholder}" class="form-control">`;
            
            default:
                return `<input type="text" id="${fieldId}" name="${fieldName}" placeholder="${placeholder}" class="form-control">`;
        }
    }

    // フィールドタイプを判定
    getFieldType(fieldConfig) {
        if (fieldConfig.type) return fieldConfig.type;
        if (fieldConfig.textarea || fieldConfig.multiline) return 'textarea';
        if (fieldConfig.options) return fieldConfig.select ? 'select' : 'radio';
        if (fieldConfig.checkbox) return 'checkbox';
        if (fieldConfig.number || fieldConfig.numeric) return 'number';
        if (fieldConfig.email) return 'email';
        if (fieldConfig.password) return 'password';
        return 'text';
    }

    // テーブルUIをレンダリング
    renderTable(moduleData) {
        const columns = moduleData.columns || moduleData.fields || {};
        const data = moduleData.data || moduleData.sample_data || [];
        const title = moduleData.title || 'テーブル';
        const description = moduleData.description || '';

        let tableHTML = `
            <div class="ui-preview table-preview">
                <div class="preview-header">
                    <h3>📊 ${title}</h3>
                    ${description ? `<p class="preview-description">${description}</p>` : ''}
                </div>
                <div class="preview-content">
                    <div class="table-container">
                        <table class="preview-table">
                            <thead>
                                <tr>
        `;

        // ヘッダー行
        Object.keys(columns).forEach(columnKey => {
            const column = columns[columnKey];
            const columnTitle = column.title || column.label || columnKey;
            tableHTML += `<th>${columnTitle}</th>`;
        });

        tableHTML += `
                                </tr>
                            </thead>
                            <tbody>
        `;

        // データ行
        if (data.length > 0) {
            data.forEach(row => {
                tableHTML += '<tr>';
                Object.keys(columns).forEach(columnKey => {
                    const value = row[columnKey] || '';
                    tableHTML += `<td>${value}</td>`;
                });
                tableHTML += '</tr>';
            });
        } else {
            // サンプルデータがない場合
            tableHTML += `
                <tr>
                    <td colspan="${Object.keys(columns).length}" class="no-data">
                        データがありません
                    </td>
                </tr>
            `;
        }

        tableHTML += `
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
        `;

        return tableHTML;
    }

    // チャートUIをレンダリング
    renderChart(moduleData) {
        const title = moduleData.title || 'チャート';
        const description = moduleData.description || '';
        const chartType = moduleData.chart_type || 'bar';

        return `
            <div class="ui-preview chart-preview">
                <div class="preview-header">
                    <h3>📈 ${title}</h3>
                    ${description ? `<p class="preview-description">${description}</p>` : ''}
                </div>
                <div class="preview-content">
                    <div class="chart-placeholder">
                        <div class="chart-icon">📊</div>
                        <p>${chartType.toUpperCase()} チャート</p>
                        <small>実際のチャートライブラリで描画されます</small>
                    </div>
                </div>
            </div>
        `;
    }

    // API UIをレンダリング
    renderAPI(moduleData) {
        const title = moduleData.title || 'API';
        const description = moduleData.description || '';
        const endpoints = moduleData.endpoints || moduleData.routes || {};

        let apiHTML = `
            <div class="ui-preview api-preview">
                <div class="preview-header">
                    <h3>🔌 ${title}</h3>
                    ${description ? `<p class="preview-description">${description}</p>` : ''}
                </div>
                <div class="preview-content">
                    <div class="api-endpoints">
        `;

        Object.entries(endpoints).forEach(([endpoint, config]) => {
            const method = config.method || 'GET';
            const path = config.path || endpoint;
            const description = config.description || '';
            
            apiHTML += `
                <div class="api-endpoint">
                    <div class="endpoint-method ${method.toLowerCase()}">${method}</div>
                    <div class="endpoint-path">${path}</div>
                    ${description ? `<div class="endpoint-description">${description}</div>` : ''}
                </div>
            `;
        });

        apiHTML += `
                    </div>
                </div>
            </div>
        `;

        return apiHTML;
    }

    // 認証UIをレンダリング
    renderAuth(moduleData) {
        const title = moduleData.title || '認証';
        const description = moduleData.description || '';

        return `
            <div class="ui-preview auth-preview">
                <div class="preview-header">
                    <h3>🔐 ${title}</h3>
                    ${description ? `<p class="preview-description">${description}</p>` : ''}
                </div>
                <div class="preview-content">
                    <div class="auth-form">
                        <div class="form-field">
                            <label class="field-label">ユーザー名</label>
                            <input type="text" class="form-control" placeholder="ユーザー名を入力">
                        </div>
                        <div class="form-field">
                            <label class="field-label">パスワード</label>
                            <input type="password" class="form-control" placeholder="パスワードを入力">
                        </div>
                        <div class="form-actions">
                            <button type="submit" class="btn btn-primary">ログイン</button>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    // データベースUIをレンダリング
    renderDatabase(moduleData) {
        const title = moduleData.title || 'データベース';
        const description = moduleData.description || '';
        const tables = moduleData.tables || moduleData.schema || {};

        let dbHTML = `
            <div class="ui-preview database-preview">
                <div class="preview-header">
                    <h3>🗄️ ${title}</h3>
                    ${description ? `<p class="preview-description">${description}</p>` : ''}
                </div>
                <div class="preview-content">
                    <div class="database-schema">
        `;

        Object.entries(tables).forEach(([tableName, tableConfig]) => {
            const columns = tableConfig.columns || {};
            
            dbHTML += `
                <div class="database-table">
                    <h4>📋 ${tableName}</h4>
                    <div class="table-columns">
            `;

            Object.entries(columns).forEach(([columnName, columnConfig]) => {
                const columnType = columnConfig.type || 'text';
                const isPrimary = columnConfig.primary || false;
                const isRequired = columnConfig.required || false;
                
                dbHTML += `
                    <div class="column-item">
                        <span class="column-name">${columnName}</span>
                        <span class="column-type">${columnType}</span>
                        ${isPrimary ? '<span class="column-primary">🔑</span>' : ''}
                        ${isRequired ? '<span class="column-required">*</span>' : ''}
                    </div>
                `;
            });

            dbHTML += `
                    </div>
                </div>
            `;
        });

        dbHTML += `
                    </div>
                </div>
            </div>
        `;

        return dbHTML;
    }

    // 設定UIをレンダリング
    renderConfig(moduleData) {
        const title = moduleData.title || '設定';
        const description = moduleData.description || '';
        const settings = moduleData.settings || moduleData.config || {};

        let configHTML = `
            <div class="ui-preview config-preview">
                <div class="preview-header">
                    <h3>⚙️ ${title}</h3>
                    ${description ? `<p class="preview-description">${description}</p>` : ''}
                </div>
                <div class="preview-content">
                    <div class="config-settings">
        `;

        Object.entries(settings).forEach(([settingKey, settingConfig]) => {
            const settingTitle = settingConfig.title || settingConfig.label || settingKey;
            const settingDescription = settingConfig.description || '';
            const settingType = settingConfig.type || 'text';
            
            configHTML += `
                <div class="config-item">
                    <div class="config-label">
                        <span class="config-title">${settingTitle}</span>
                        ${settingDescription ? `<span class="config-description">${settingDescription}</span>` : ''}
                    </div>
                    <div class="config-control">
                        ${this.renderConfigControl(settingKey, settingType, settingConfig)}
                    </div>
                </div>
            `;
        });

        configHTML += `
                    </div>
                </div>
            </div>
        `;

        return configHTML;
    }

    // 設定コントロールをレンダリング
    renderConfigControl(settingKey, settingType, settingConfig) {
        const controlId = `config-${settingKey}`;
        
        switch (settingType) {
            case 'boolean':
                return `<input type="checkbox" id="${controlId}" class="form-check-input">`;
            
            case 'select':
                const options = settingConfig.options || [];
                let selectHTML = `<select id="${controlId}" class="form-control">`;
                options.forEach(option => {
                    selectHTML += `<option value="${option.value || option}">${option.label || option}</option>`;
                });
                selectHTML += '</select>';
                return selectHTML;
            
            case 'number':
                return `<input type="number" id="${controlId}" class="form-control">`;
            
            default:
                return `<input type="text" id="${controlId}" class="form-control">`;
        }
    }

    // ページUIをレンダリング
    renderPage(moduleData) {
        const title = moduleData.title || 'ページ';
        const description = moduleData.description || '';
        const layout = moduleData.layout || 'default';

        return `
            <div class="ui-preview page-preview">
                <div class="preview-header">
                    <h3>📄 ${title}</h3>
                    ${description ? `<p class="preview-description">${description}</p>` : ''}
                </div>
                <div class="preview-content">
                    <div class="page-layout ${layout}">
                        <div class="page-header">ヘッダー</div>
                        <div class="page-body">メインコンテンツ</div>
                        <div class="page-sidebar">サイドバー</div>
                        <div class="page-footer">フッター</div>
                    </div>
                </div>
            </div>
        `;
    }

    // コンポーネントUIをレンダリング
    renderComponent(moduleData) {
        const title = moduleData.title || 'コンポーネント';
        const description = moduleData.description || '';
        const componentType = moduleData.component_type || 'widget';

        return `
            <div class="ui-preview component-preview">
                <div class="preview-header">
                    <h3>🧩 ${title}</h3>
                    ${description ? `<p class="preview-description">${description}</p>` : ''}
                </div>
                <div class="preview-content">
                    <div class="component-widget ${componentType}">
                        <div class="widget-content">
                            <div class="widget-icon">🧩</div>
                            <p>${componentType} コンポーネント</p>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    // 生JSONをレンダリング（フォールバック）
    renderRawJson(moduleData) {
        return `
            <div class="ui-preview raw-preview">
                <div class="preview-header">
                    <h3>📋 生データ</h3>
                </div>
                <div class="preview-content">
                    <pre class="raw-json">${JSON.stringify(moduleData, null, 2)}</pre>
                </div>
            </div>
        `;
    }

    // 初期化状態のチェック
    isReady() {
        return this.isInitialized;
    }
}

// グローバル関数
function renderModuleUI(moduleData) {
    if (window.uiRenderer) {
        return window.uiRenderer.renderModuleUI(moduleData);
    } else {
        console.warn('⚠️ UIRendererが初期化されていません');
        return '<div class="ui-preview-error">UIRendererが初期化されていません</div>';
    }
}

// 初期化
document.addEventListener('DOMContentLoaded', function() {
    console.log('🎨 UIRenderer初期化開始');
    
    if (window.UIRenderer) {
        window.uiRenderer = new window.UIRenderer();
        console.log('✅ UIRenderer初期化完了');
    } else {
        console.warn('⚠️ UIRendererクラスが見つかりません');
    }
});

// クラスをグローバルに公開
window.UIRenderer = UIRenderer; 