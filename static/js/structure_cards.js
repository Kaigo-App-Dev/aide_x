/**
 * 構成カードの描画処理
 */

class StructureCards {
    constructor() {
        console.log('📋 StructureCards初期化');
    }

    // 初期化メソッド
    init() {
        console.log("✅ StructureCards.init() を呼び出しました");
        
        // 右ペインの初期化
        const rightPane = document.getElementById("right-pane");
        if (rightPane) {
            console.log('🔧 右ペインを初期化します');
            rightPane.style.display = "flex";
            rightPane.style.width = "30%";
            rightPane.style.visibility = "visible";
            rightPane.style.opacity = "1";
            console.log('✅ 右ペイン初期化完了:', {
                display: rightPane.style.display,
                width: rightPane.style.width,
                visibility: rightPane.style.visibility,
                opacity: rightPane.style.opacity
            });
        } else {
            console.warn('⚠️ 右ペイン要素が見つかりません');
        }
        
        // Gemini出力コンテナの確認
        const geminiOutput = document.getElementById("gemini-output");
        if (geminiOutput) {
            console.log('✅ Gemini出力コンテナを確認:', {
                id: geminiOutput.id,
                className: geminiOutput.className,
                display: geminiOutput.style.display,
                visibility: geminiOutput.style.visibility
            });
        } else {
            console.warn('⚠️ Gemini出力コンテナが見つかりません');
        }
        
        // 構造データが存在する場合は初期更新を実行
        if (window.structureData) {
            console.log('🔄 初期構造データを検出、StructureCardsを更新');
            this.updateFromStructureData(window.structureData);
        }
    }

    // 折り畳み機能の実装
    toggleCard(button) {
        const card = button.closest('.structure-card');
        const content = card.querySelector('.card-content');
        const isExpanded = card.classList.contains('expanded');
        
        if (isExpanded) {
            card.classList.remove('expanded');
            button.textContent = '▼';
            content.style.display = 'none';
        } else {
            card.classList.add('expanded');
            button.textContent = '▲';
            content.style.display = 'block';
        }
        
        console.log('🔄 カード折り畳み切り替え:', {
            cardId: card.getAttribute('data-source'),
            isExpanded: !isExpanded,
            buttonText: button.textContent
        });
    }

    // プレースホルダーを非表示にする
    hideStructurePlaceholder() {
        const placeholder = document.getElementById('structure-placeholder');
        if (placeholder) {
            placeholder.style.display = 'none';
            console.log('✅ 構成プレースホルダーを非表示にしました');
        }
    }

    // 構成カードの更新
    updateStructureCards(content) {
        const structureContainer = document.querySelector('.structure-cards');
        if (!structureContainer) {
            console.warn('⚠️ structure-cardsコンテナが見つかりません');
            return;
        }
        
        console.log('🔄 updateStructureCards開始:', {
            contentType: typeof content,
            isArray: Array.isArray(content),
            contentKeys: content ? Object.keys(content) : 'null',
            contentLength: content ? (Array.isArray(content) ? content.length : Object.keys(content).length) : 0,
            containerExists: !!structureContainer,
            containerVisible: structureContainer.style.display !== 'none',
            containerHeight: structureContainer.offsetHeight,
            containerWidth: structureContainer.offsetWidth
        });
        
        // 既存のカードをクリア（Claude評価カードは除く）
        const existingCards = structureContainer.querySelectorAll('.structure-card:not(.claude-evaluation-card)');
        existingCards.forEach(card => card.remove());
        
        // 「構成なし」メッセージも削除
        const noContentMessages = structureContainer.querySelectorAll('.no-content');
        noContentMessages.forEach(msg => msg.remove());
        
        // contentがnull、undefined、空文字列、空配列の場合は「構成なし」メッセージを表示
        if (!content || 
            (typeof content === 'string' && content.trim() === '') ||
            (Array.isArray(content) && content.length === 0) ||
            (typeof content === 'object' && Object.keys(content).length === 0)) {
            console.warn('⚠️ contentが空です - 構成なしメッセージを表示');
            
            // Claude評価の状況をチェック
            const structureData = window.currentStructureData;
            let messageText = '構成がまだ生成されていません';
            
            if (structureData && structureData.evaluations && structureData.evaluations.claude) {
                const claudeEval = structureData.evaluations.claude;
                if (claudeEval.status === 'skipped') {
                    messageText = 'Claude評価がスキップされました';
                } else if (claudeEval.status === 'failed') {
                    messageText = 'Claude評価が失敗しました';
                } else if (claudeEval.status === 'success') {
                    messageText = 'Claude評価は完了していますが、構成が未生成です';
                }
            } else {
                messageText = 'Claude評価が未実行です';
            }
            
            const emptyDiv = document.createElement('div');
            emptyDiv.className = 'no-content';
            emptyDiv.innerHTML = `<p>${messageText}</p>`;
            structureContainer.appendChild(emptyDiv);
            return;
        }
        
        // プレースホルダーを非表示にする（構成データが存在する場合）
        this.hideStructurePlaceholder();
        
        // 不完全なJSONの検出とスキップ処理
        if (typeof content === 'string') {
            const contentStr = content.trim();
            if (contentStr === '{' || contentStr === '}') {
                console.error('❌ 不完全なJSONを検出、スキップします:', contentStr);
                const errorDiv = document.createElement('div');
                errorDiv.className = 'no-content error';
                errorDiv.innerHTML = `
                    <p>⚠️ 不完全な構成データが検出されました</p>
                    <details>
                        <summary>エラー詳細</summary>
                        <p>検出されたデータ: <code>${contentStr}</code></p>
                        <p>このデータは不完全なため、表示をスキップしました。</p>
                    </details>
                `;
                structureContainer.appendChild(errorDiv);
                return;
            }
            
            if (contentStr.startsWith('{') && !contentStr.endsWith('}')) {
                console.error('❌ 不完全なJSONを検出、スキップします: 開き括弧のみ');
                const errorDiv = document.createElement('div');
                errorDiv.className = 'no-content error';
                errorDiv.innerHTML = `
                    <p>⚠️ 不完全な構成データが検出されました</p>
                    <details>
                        <summary>エラー詳細</summary>
                        <p>検出されたデータ: <code>${contentStr.substring(0, 100)}...</code></p>
                        <p>開き括弧のみの不完全なJSONのため、表示をスキップしました。</p>
                    </details>
                `;
                structureContainer.appendChild(errorDiv);
                return;
            }
            
            if (!contentStr.startsWith('{') && contentStr.endsWith('}')) {
                console.error('❌ 不完全なJSONを検出、スキップします: 閉じ括弧のみ');
                const errorDiv = document.createElement('div');
                errorDiv.className = 'no-content error';
                errorDiv.innerHTML = `
                    <p>⚠️ 不完全な構成データが検出されました</p>
                    <details>
                        <summary>エラー詳細</summary>
                        <p>検出されたデータ: <code>...${contentStr.substring(-100)}</code></p>
                        <p>閉じ括弧のみの不完全なJSONのため、表示をスキップしました。</p>
                    </details>
                `;
                structureContainer.appendChild(errorDiv);
                return;
            }
            
            // 括弧の均衡チェック
            const openBraces = (contentStr.match(/\{/g) || []).length;
            const closeBraces = (contentStr.match(/\}/g) || []).length;
            if (openBraces !== closeBraces) {
                console.error('❌ 括弧の不均衡を検出、スキップします:', { openBraces, closeBraces });
                const errorDiv = document.createElement('div');
                errorDiv.className = 'no-content error';
                errorDiv.innerHTML = `
                    <p>⚠️ 不正な構成データが検出されました</p>
                    <details>
                        <summary>エラー詳細</summary>
                        <p>括弧の不均衡: 開き括弧${openBraces}個、閉じ括弧${closeBraces}個</p>
                        <p>検出されたデータ: <code>${contentStr.substring(0, 200)}...</code></p>
                        <p>不正なJSONのため、表示をスキップしました。</p>
                    </details>
                `;
                structureContainer.appendChild(errorDiv);
                return;
            }
        }
        
        if (content && (typeof content === 'object' || Array.isArray(content))) {
            // 配列形式のmodulesかどうかを判定
            const isArrayModules = Array.isArray(content) && content.length > 0 && 
                content.every(item => item && typeof item === 'object' && (item.name || item.detail));
            
            // オブジェクト形式のmodulesかどうかを判定
            const isObjectModules = !Array.isArray(content) && typeof content === 'object' && 
                Object.values(content).some(item => 
                    item && typeof item === 'object' && 
                    (item.title || item.description || item.sections || item.name || item.detail)
                );
            
            console.log('📋 構造判定:', {
                isArrayModules: isArrayModules,
                isObjectModules: isObjectModules
            });
            
            if (isArrayModules) {
                // 配列形式のmodules構造の場合（Gemini補完結果）
                console.log('📋 配列modules構造として処理:', content.length, '件');
                content.forEach((module, index) => {
                    console.log(`📋 モジュール作成 [${index}]:`, module);
                    const card = this.createArrayModuleCard(index, module);
                    structureContainer.appendChild(card);
                });
            } else if (isObjectModules) {
                // オブジェクト形式のmodules構造の場合
                console.log('📋 オブジェクトmodules構造として処理:', Object.keys(content));
                Object.entries(content).forEach(([key, module]) => {
                    console.log(`📋 モジュール作成: ${key}`, module);
                    const card = this.createModuleCard(key, module);
                    structureContainer.appendChild(card);
                });
            } else {
                // 通常の構造の場合
                console.log('📋 通常構造として処理:', Object.keys(content));
                Object.entries(content).forEach(([key, value]) => {
                    console.log(`📋 カード作成: ${key}`, value);
                    const card = this.createStructureCard(key, value);
                    structureContainer.appendChild(card);
                });
            }
            
            console.log('✅ updateStructureCards完了 - 作成されたカード数:', structureContainer.children.length);
            
            // 作成されたカードの表示状況を確認
            const createdCards = structureContainer.querySelectorAll('.structure-card');
            console.log('📋 作成されたカードの詳細:', {
                totalCards: createdCards.length,
                cards: Array.from(createdCards).map((card, index) => ({
                    index: index,
                    visible: card.style.display !== 'none',
                    height: card.offsetHeight,
                    width: card.offsetWidth,
                    className: card.className,
                    textContent: card.textContent.substring(0, 50) + '...'
                }))
            });
        } else {
            // 予期しないデータ型の場合は「構成なし」メッセージを表示
            console.warn('⚠️ 予期しないデータ型です:', typeof content);
            const emptyDiv = document.createElement('div');
            emptyDiv.className = 'no-content';
            emptyDiv.innerHTML = `
                <p>構成データの形式が正しくありません</p>
                <details>
                    <summary>データ詳細</summary>
                    <p>データ型: <code>${typeof content}</code></p>
                    <p>データ内容: <code>${JSON.stringify(content).substring(0, 200)}...</code></p>
                </details>
            `;
            structureContainer.appendChild(emptyDiv);
        }
    }

    // 構造データから適切なコンテンツを取得（フォールバック機能付き）
    getStructureContent(structure) {
        console.log('🔍 構造データからコンテンツ取得開始:', {
            hasStructure: !!structure,
            structureKeys: structure ? Object.keys(structure) : 'null'
        });
        
        // 安全なデータアクセス
        const content = structure?.content || {};
        
        // 優先順位: sections > modules > functions > その他
        if ('sections' in content && content.sections && Array.isArray(content.sections)) {
            console.log('✅ content.sectionsを使用');
            return this.parseSectionsContent(content.sections);
        }
        
        if ('modules' in content && content.modules) {
            console.log('✅ content.modulesを使用');
            return this.parseModulesContent(content.modules);
        }
        
        if ('functions' in content && content.functions) {
            console.log('✅ content.functionsを使用');
            return this.parseModulesContent(content.functions);
        }
        
        // structure.sections の直接アクセス（後方互換性）
        if (structure && structure.sections && Array.isArray(structure.sections)) {
            console.log('✅ structure.sectionsを使用（後方互換性）');
            return this.parseSectionsContent(structure.sections);
        }
        
        // structure.modules の直接アクセス（後方互換性）
        if (structure && structure.modules) {
            console.log('✅ structure.modulesを使用（後方互換性）');
            return this.parseModulesContent(structure.modules);
        }
        
        // structure.functions の直接アクセス（後方互換性）
        if (structure && structure.functions) {
            console.log('✅ structure.functionsを使用（後方互換性）');
            return this.parseModulesContent(structure.functions);
        }
        
        console.log('❌ 利用可能な構造データが見つかりません');
        return null;
    }
    
    // セクションコンテンツの解析
    parseSectionsContent(sectionsContent) {
        console.log('📋 セクションコンテンツ解析開始:', {
            sectionsCount: sectionsContent.length,
            sections: sectionsContent.map(section => ({
                title: section.title,
                description: section.description,
                componentsCount: section.components ? section.components.length : 0
            }))
        });
        
        // セクションをモジュール形式に変換
        const modules = {};
        
        sectionsContent.forEach((section, index) => {
            const sectionKey = section.title || `セクション${index + 1}`;
            
            modules[sectionKey] = {
                title: section.title || `セクション${index + 1}`,
                description: section.description || '',
                type: 'section',
                components: section.components || [],
                sections: {
                    [sectionKey]: {
                        title: section.title || `セクション${index + 1}`,
                        content: section.description || '',
                        implementation: this.formatComponents(section.components || [])
                    }
                }
            };
        });
        
        console.log('✅ セクションコンテンツ解析完了:', {
            convertedModulesCount: Object.keys(modules).length,
            modules: Object.keys(modules)
        });
        
        return modules;
    }
    
    // コンポーネントをフォーマット
    formatComponents(components) {
        if (!components || components.length === 0) {
            return 'コンポーネントが定義されていません';
        }
        
        return components.map(component => {
            const type = component.type || 'unknown';
            const content = component.content || '';
            
            switch (type) {
                case 'text':
                    return `テキスト: ${content}`;
                case 'input':
                    return `入力フィールド: ${content}`;
                case 'button':
                    return `ボタン: ${content}`;
                case 'select':
                    return `選択肢: ${content}`;
                case 'textarea':
                    return `テキストエリア: ${content}`;
                default:
                    return `${type}: ${content}`;
            }
        }).join('\n');
    }

    // モジュールコンテンツの解析
    parseModulesContent(modulesContent) {
        // 文字列の場合はJSON.parseを試行
        if (typeof modulesContent === 'string') {
            try {
                // 不完全なJSONの検出
                const modulesStr = modulesContent.trim();
                if (modulesStr === '{' || modulesStr === '}') {
                    console.warn('⚠️ 不完全なJSONを検出:', modulesStr);
                    return null;
                }
                
                if (modulesStr.startsWith('{') && !modulesStr.endsWith('}')) {
                    console.warn('⚠️ 不完全なJSONを検出: 開き括弧のみ');
                    return null;
                }
                
                if (!modulesStr.startsWith('{') && modulesStr.endsWith('}')) {
                    console.warn('⚠️ 不完全なJSONを検出: 閉じ括弧のみ');
                    return null;
                }
                
                // 括弧の均衡チェック
                const openBraces = (modulesStr.match(/\{/g) || []).length;
                const closeBraces = (modulesStr.match(/\}/g) || []).length;
                if (openBraces !== closeBraces) {
                    console.warn('⚠️ 括弧の不均衡を検出:', { openBraces, closeBraces });
                    return null;
                }
                
                const parsedModules = JSON.parse(modulesContent);
                console.log('✅ JSON.parse成功');
                return parsedModules;
            } catch (parseError) {
                console.warn('⚠️ JSON.parse失敗:', parseError.message);
                return null;
            }
        } else {
            // 既にオブジェクトの場合はそのまま返す
            return modulesContent;
        }
    }

    // 構造データを自動更新
    updateFromStructureData(structure) {
        console.log('🔄 構造データからの自動更新開始');
        
        try {
            const content = this.getStructureContent(structure);
            if (content) {
                console.log('✅ 構造データからコンテンツを取得、カードを更新');
                console.log('📋 取得したコンテンツ:', {
                    type: typeof content,
                    isArray: Array.isArray(content),
                    keys: typeof content === 'object' ? Object.keys(content) : 'N/A',
                    length: Array.isArray(content) ? content.length : 'N/A'
                });
                this.updateStructureCards(content);
                // プレースホルダーを非表示にする
                this.hideStructurePlaceholder();
            } else {
                console.log('⚠️ 構造データからコンテンツを取得できませんでした');
                this.updateStructureCards(null);
            }
        } catch (error) {
            console.error('❌ 構造データの更新中にエラーが発生:', error);
            console.error('❌ エラー詳細:', {
                message: error.message,
                stack: error.stack
            });
            // エラーが発生した場合は空の状態を表示
            this.updateStructureCards(null);
        }
    }

    // カードクリック時の構成読み込み処理
    loadStructureOnCardClick(structureId) {
        console.log('🔄 カードクリック時の構成読み込み開始:', structureId);
        
        if (!structureId) {
            console.warn('⚠️ 構成IDが指定されていません');
            return;
        }
        
        // ローディング状態を表示
        this.showCardLoadingState(structureId);
        
        // 構成データを取得
        fetch(`/unified/${structureId}/data`)
            .then(response => {
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                return response.json();
            })
            .then(data => {
                console.log('✅ 構成データ取得成功:', data);
                
                // グローバル変数に保存
                window.currentStructureData = data.structure || data;
                
                // 構造カードを更新
                if (window.structureCards) {
                    window.structureCards.updateFromStructureData(data.structure || data);
                }
                
                // Gemini補完結果があれば右ペインを表示
                if (window.geminiParser) {
                    window.geminiParser.updateFromStructureData(data.structure || data);
                }
                
                // 右ペインの表示を確保
                if (window.layoutManager) {
                    window.layoutManager.ensureRightPaneVisibility();
                }
                
                // ローディング状態を解除
                this.hideCardLoadingState(structureId);
                
                console.log('✅ カードクリック時の構成読み込み完了');
            })
            .catch(error => {
                console.error('❌ 構成データ取得エラー:', error);
                this.hideCardLoadingState(structureId);
                this.showCardErrorState(structureId, error.message);
            });
    }
    
    // カードのローディング状態を表示
    showCardLoadingState(structureId) {
        const card = document.querySelector(`[data-structure-id="${structureId}"]`);
        if (card) {
            card.classList.add('loading');
            const loadingDiv = document.createElement('div');
            loadingDiv.className = 'card-loading';
            loadingDiv.innerHTML = '<div class="spinner"></div><span>読み込み中...</span>';
            card.appendChild(loadingDiv);
        }
    }
    
    // カードのローディング状態を解除
    hideCardLoadingState(structureId) {
        const card = document.querySelector(`[data-structure-id="${structureId}"]`);
        if (card) {
            card.classList.remove('loading');
            const loadingDiv = card.querySelector('.card-loading');
            if (loadingDiv) {
                loadingDiv.remove();
            }
        }
    }
    
    // カードのエラー状態を表示
    showCardErrorState(structureId, errorMessage) {
        const card = document.querySelector(`[data-structure-id="${structureId}"]`);
        if (card) {
            const errorDiv = document.createElement('div');
            errorDiv.className = 'card-error';
            errorDiv.innerHTML = `<span>❌ エラー: ${errorMessage}</span>`;
            card.appendChild(errorDiv);
        }
    }

    // 配列形式のモジュールカードの作成（Gemini補完結果用）
    createArrayModuleCard(index, module) {
        const card = document.createElement('div');
        card.className = 'structure-card module-card array-module-card';
        
        // モジュール名を取得（デフォルト値も設定）
        const moduleName = module.name || `モジュール ${index + 1}`;
        
        const header = document.createElement('div');
        header.className = 'card-header';
        header.innerHTML = `
            <h3 class="module-title">${moduleName}</h3>
            <button class="structure-card-toggle" onclick="window.StructureCards.prototype.toggleCard(this)">▼</button>
        `;
        
        const content = document.createElement('div');
        content.className = 'card-content';
        content.style.display = 'none'; // 初期状態は折り畳み
        
        let contentHtml = '';
        
        // モジュールの詳細（口語調でわかりやすく表示）
        if (module.detail) {
            contentHtml += `<div class="module-detail">
                <div class="detail-description">
                    <strong>📝 この機能について:</strong><br>
                    ${window.utils.sanitizeHtml(module.detail)}
                </div>
            </div>`;
        }
        
        // 機能の特徴を表示（アイコン付き）
        contentHtml += `<div class="module-features">
            <strong>✨ この機能でできること:</strong>
            <div class="features-list">`;
        
        // モジュールの特徴を推測して表示
        const features = this.extractModuleFeatures(module);
        features.forEach(feature => {
            contentHtml += `<div class="feature-item">
                <span class="feature-icon">${feature.icon}</span>
                <span class="feature-text">${feature.text}</span>
            </div>`;
        });
        
        contentHtml += `</div></div>`;
        
        // その他のプロパティがあれば表示
        const otherProps = Object.entries(module).filter(([key]) => !['name', 'detail'].includes(key));
        if (otherProps.length > 0) {
            contentHtml += '<div class="module-other-props">' +
                '<strong>📋 その他の情報:</strong>' +
                '<ul>';
            otherProps.forEach(([key, value]) => {
                contentHtml += '<li><strong>' + key + ':</strong> ' + window.utils.sanitizeHtml(value) + '</li>';
            });
            contentHtml += '</ul></div>';
        }
        
        content.innerHTML = contentHtml || `<pre>${JSON.stringify(module, null, 2)}</pre>`;
        
        card.appendChild(header);
        card.appendChild(content);
        
        return card;
    }
    
    // モジュールの特徴を抽出するヘルパーメソッド
    extractModuleFeatures(module) {
        const features = [];
        const moduleName = (module.name || '').toLowerCase();
        const moduleDetail = (module.detail || '').toLowerCase();
        
        // モジュール名や詳細から特徴を推測
        if (moduleName.includes('認証') || moduleDetail.includes('認証') || moduleDetail.includes('ログイン')) {
            features.push({ icon: '🔐', text: 'ユーザー認証・ログイン機能' });
        }
        if (moduleName.includes('データ') || moduleDetail.includes('データ') || moduleDetail.includes('保存')) {
            features.push({ icon: '💾', text: 'データの保存・管理' });
        }
        if (moduleName.includes('api') || moduleDetail.includes('api') || moduleDetail.includes('外部')) {
            features.push({ icon: '🔌', text: '外部サービスとの連携' });
        }
        if (moduleName.includes('ui') || moduleName.includes('画面') || moduleDetail.includes('画面') || moduleDetail.includes('表示')) {
            features.push({ icon: '🖥️', text: 'ユーザーインターフェース' });
        }
        if (moduleName.includes('請求') || moduleDetail.includes('請求') || moduleDetail.includes('支払')) {
            features.push({ icon: '💰', text: '請求書・支払い処理' });
        }
        if (moduleName.includes('通知') || moduleDetail.includes('通知') || moduleDetail.includes('メール')) {
            features.push({ icon: '📧', text: '通知・メール送信' });
        }
        if (moduleName.includes('検索') || moduleDetail.includes('検索') || moduleDetail.includes('フィルタ')) {
            features.push({ icon: '🔍', text: '検索・フィルタ機能' });
        }
        if (moduleName.includes('レポート') || moduleDetail.includes('レポート') || moduleDetail.includes('集計')) {
            features.push({ icon: '📊', text: 'レポート・集計機能' });
        }
        if (moduleName.includes('設定') || moduleDetail.includes('設定') || moduleDetail.includes('管理')) {
            features.push({ icon: '⚙️', text: '設定・管理機能' });
        }
        
        // デフォルトの特徴（上記に該当しない場合）
        if (features.length === 0) {
            features.push({ icon: '🛠️', text: 'アプリケーション機能' });
            if (moduleDetail.includes('自動')) {
                features.push({ icon: '🤖', text: '自動処理機能' });
            }
            if (moduleDetail.includes('作成') || moduleDetail.includes('生成')) {
                features.push({ icon: '✨', text: 'コンテンツ作成機能' });
            }
        }
        
        return features;
    }

    // モジュールカードの作成
    createModuleCard(key, module) {
        const card = document.createElement('div');
        card.className = 'structure-card module-card';
        
        const header = document.createElement('div');
        header.className = 'card-header';
        header.innerHTML = `
            <h3>${module.title || key}</h3>
            <button class="structure-card-toggle" onclick="window.StructureCards.prototype.toggleCard(this)">▼</button>
        `;
        
        const content = document.createElement('div');
        content.className = 'card-content';
        content.style.display = 'none'; // 初期状態は折り畳み
        
        let contentHtml = '';
        
        // モジュールの説明
        if (module.description) {
            contentHtml += `<div class="module-description"><strong>説明:</strong> ${window.utils.sanitizeHtml(module.description)}</div>`;
        }
        
        // セクションの表示
        if (module.sections && typeof module.sections === 'object') {
            contentHtml += '<div class="module-sections"><strong>セクション:</strong><ul>';
            Object.entries(module.sections).forEach(([sectionKey, section]) => {
                contentHtml += `
                    <li>
                        <strong>${window.utils.sanitizeHtml(section.title || sectionKey)}</strong>
                        ${section.content ? `<br><span class="section-content">${window.utils.sanitizeHtml(section.content)}</span>` : ''}
                        ${section.implementation ? `<br><span class="section-implementation"><em>実装:</em> ${window.utils.sanitizeHtml(section.implementation)}</span>` : ''}
                    </li>
                `;
            });
            contentHtml += '</ul></div>';
        }
        
        content.innerHTML = contentHtml || `<pre>${JSON.stringify(module, null, 2)}</pre>`;
        
        card.appendChild(header);
        card.appendChild(content);
        
        return card;
    }

    // 構成カードの作成
    createStructureCard(key, value) {
        console.log('🔍 createStructureCard開始:', { key, value });
        
        // データの安全性チェック
        if (!value) {
            console.error('❌ valueがnullまたはundefinedです');
            return this.createErrorCard('構成データが存在しません', 'valueがnullまたはundefinedです');
        }
        
        // 構造データの取得（複数のソースから安全に取得）
        let structureData = null;
        let dataSource = 'unknown';
        
        // 1. structure["structure"]を優先的にチェック
        if (value.structure !== undefined && value.structure !== null) {
            if (typeof value.structure === 'string') {
                try {
                    structureData = JSON.parse(value.structure);
                    dataSource = 'structure.structure (string)';
                    console.log('✅ structure.structure (string)からデータを取得');
                } catch (e) {
                    console.warn('⚠️ structure.structureのJSON解析に失敗:', e);
                    structureData = value.structure;
                    dataSource = 'structure.structure (raw)';
                }
            } else {
                structureData = value.structure;
                dataSource = 'structure.structure (object)';
                console.log('✅ structure.structure (object)からデータを取得');
            }
        }
        // 2. value自体が構造データの場合
        else if (value.title || value.name || value.modules) {
            structureData = value;
            dataSource = 'value (direct)';
            console.log('✅ value (direct)からデータを取得');
        }
        // 3. value.contentが構造データの場合
        else if (value.content && (typeof value.content === 'object')) {
            structureData = value.content;
            dataSource = 'value.content';
            console.log('✅ value.contentからデータを取得');
        }
        // 4. value.contentが文字列の場合（JSONとして解析を試行）
        else if (value.content && (typeof value.content === 'string')) {
            try {
                structureData = JSON.parse(value.content);
                dataSource = 'value.content (parsed)';
                console.log('✅ value.content (parsed)からデータを取得');
            } catch (e) {
                console.warn('⚠️ value.contentのJSON解析に失敗:', e);
                structureData = { content: value.content };
                dataSource = 'value.content (raw)';
            }
        }
        // 5. その他の場合
        else {
            structureData = value;
            dataSource = 'value (fallback)';
            console.log('✅ value (fallback)からデータを取得');
        }
        
        // 構造データの安全性チェック
        if (!structureData) {
            console.error('❌ 構造データが取得できませんでした');
            return this.createErrorCard('構造データの取得に失敗', '構造データがnullまたはundefinedです');
        }
        
        // カード要素の作成
        const card = document.createElement('div');
        card.className = 'structure-card';
        card.setAttribute('data-source', dataSource);
        
        // 構成IDを設定（クリックイベント用）
        const structureId = value.id || key;
        if (structureId) {
            card.setAttribute('data-structure-id', structureId);
            // クリックイベントを追加
            card.addEventListener('click', (e) => {
                // 折りたたみボタンのクリックは除外
                if (e.target.classList.contains('structure-card-toggle')) {
                    return;
                }
                this.loadStructureOnCardClick(structureId);
            });
            card.style.cursor = 'pointer';
        }
        
        // タイトルの取得
        const title = structureData.title || structureData.name || key || '無題の構成';
        
        // カードのHTML構築
        card.innerHTML = `
            <div class="card-header">
                <h3 class="card-title">${this.escapeHtml(title)}</h3>
                <button class="structure-card-toggle" onclick="window.StructureCards.prototype.toggleCard(this)">▼</button>
                <div class="card-meta">
                    <span class="data-source">データソース: ${dataSource}</span>
                    <span class="structure-id">ID: ${value.id || 'N/A'}</span>
                </div>
            </div>
            <div class="card-content" style="display: none;">
                ${this.generateStructureContent(structureData)}
            </div>
        `;
        
        return card;
    }

    createErrorCard(title, message, details = null) {
        console.error('🚨 エラーカードを作成:', title, message, details);
        
        const card = document.createElement('div');
        card.className = 'structure-card error-card';
        
        let detailsHtml = '';
        if (details) {
            detailsHtml = `
                <div class="error-details">
                    <details>
                        <summary>詳細情報</summary>
                        <pre>${this.escapeHtml(details)}</pre>
                    </details>
                </div>
            `;
        }
        
        card.innerHTML = `
            <div class="card-header error-header">
                <h3 class="card-title error-title">🚨 ${this.escapeHtml(title)}</h3>
            </div>
            <div class="card-content error-content">
                <p class="error-message">${this.escapeHtml(message)}</p>
                ${detailsHtml}
            </div>
        `;
        
        return card;
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    generateStructureContent(structureData) {
        // 既存のgenerateStructureContent関数の実装
        // ここに既存のロジックを配置
        return '<p>構成内容が表示されます</p>';
    }
}

// クラスをグローバルに公開
window.StructureCards = StructureCards; 