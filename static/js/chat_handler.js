/**
 * Chat入力・送信処理
 */

class ChatHandler {
    constructor() {
        this.structureId = window.utils.getStructureIdFromUrl();
        this.csrfToken = window.utils.getCSRFToken();
        console.log('💬 ChatHandler初期化');
        console.log('🔍 初期化時のstructureId:', this.structureId);
        console.log('🔍 初期化時のcsrfToken:', this.csrfToken ? '取得済み' : '未取得');
        console.log('🔍 現在のURL:', window.location.pathname);
        
        // デバッグモードチェック
        this.checkDebugMode();
    }
    
    // デバッグモードチェック
    checkDebugMode() {
        console.log('🔍 ChatHandler デバッグモードチェック開始');
        
        const isDebugMode = window.isDebugMode || false;
        const isTestMode = window.isTestMode || false;
        const hasStructureData = !!(window.structureData && window.structureData.content);
        
        console.log('🔍 デバッグモード状態:', {
            isDebugMode: isDebugMode,
            isTestMode: isTestMode,
            hasStructureData: hasStructureData,
            structureDataId: window.structureData?.id || 'undefined'
        });
        
        if (isDebugMode || isTestMode) {
            console.log('🧪 デバッグ/テストモードで動作中 - ChatHandler');
            
            // デバッグモード用の初期メッセージを設定
            this.debugModeMessage = "デバッグモードで動作中です。構造データが正しく設定されていない可能性があります。";
            
            // デバッグモード用の送信処理を有効化
            this.enableDebugModeChat();
        }
        
        console.log('✅ ChatHandler デバッグモードチェック完了');
    }
    
    // デバッグモード用のチャット機能有効化
    enableDebugModeChat() {
        console.log('🧪 デバッグモード用チャット機能を有効化');
        
        // 送信ボタンと入力フィールドの存在確認
        const sendButton = document.getElementById('send-button');
        const chatInput = document.getElementById('chat-input');
        
        console.log('🔍 チャット要素確認:', {
            hasSendButton: !!sendButton,
            hasChatInput: !!chatInput
        });
        
        if (!sendButton || !chatInput) {
            console.warn('⚠️ チャット要素が見つかりません - デバッグモード用に作成');
            this.createDebugModeChatElements();
        }
        
        // デバッグモード用のイベントバインド
        this.bindDebugModeEvents();
    }
    
    // デバッグモード用のチャット要素作成
    createDebugModeChatElements() {
        console.log('🧪 デバッグモード用チャット要素を作成');
        
        const chatPanel = document.querySelector('.chat-panel');
        if (!chatPanel) {
            console.error('❌ .chat-panelが見つかりません');
            return;
        }
        
        // チャット入力エリアを作成
        const chatInputArea = document.createElement('div');
        chatInputArea.className = 'chat-input-area';
        chatInputArea.innerHTML = `
            <div class="chat-input-container">
                <input type="text" id="chat-input" placeholder="デバッグモード: メッセージを入力してください..." />
                <button id="send-button" type="button">送信</button>
            </div>
        `;
        
        // チャットメッセージエリアを作成
        const chatMessages = document.createElement('div');
        chatMessages.className = 'chat-messages';
        
        // 既存の要素を確認して追加
        const existingInputArea = chatPanel.querySelector('.chat-input-area');
        const existingMessages = chatPanel.querySelector('.chat-messages');
        
        if (!existingInputArea) {
            chatPanel.appendChild(chatInputArea);
            console.log('✅ デバッグモード用チャット入力エリアを作成');
        }
        
        if (!existingMessages) {
            chatPanel.appendChild(chatMessages);
            console.log('✅ デバッグモード用チャットメッセージエリアを作成');
        }
    }
    
    // デバッグモード用のイベントバインド
    bindDebugModeEvents() {
        console.log('🧪 デバッグモード用イベントをバインド');
        
        const sendButton = document.getElementById('send-button');
        const chatInput = document.getElementById('chat-input');
        
        if (sendButton) {
            sendButton.addEventListener('click', (e) => {
                e.preventDefault();
                console.log('🧪 デバッグモード: 送信ボタンクリック');
                this.sendDebugModeMessage();
            });
            console.log('✅ デバッグモード用送信ボタンイベントをバインド');
        }
        
        if (chatInput) {
            chatInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') {
                    e.preventDefault();
                    console.log('🧪 デバッグモード: Enterキー押下');
                    this.sendDebugModeMessage();
                }
            });
            console.log('✅ デバッグモード用Enterキーイベントをバインド');
        }
    }
    
    // デバッグモード用のメッセージ送信
    sendDebugModeMessage() {
        console.log('🧪 デバッグモード用メッセージ送信開始');
        
        const chatInput = document.getElementById('chat-input');
        const content = chatInput ? chatInput.value.trim() : '';
        
        if (!content) {
            console.warn('⚠️ デバッグモード: メッセージ内容が空です');
            return;
        }
        
        console.log('🧪 デバッグモード: メッセージ送信:', content);
        
        // ユーザーメッセージを追加
        this.addChatMessage("user", content);
        
        // 入力フィールドをクリア
        if (chatInput) {
            chatInput.value = "";
        }
        
        // デバッグモード用の応答を生成
        setTimeout(() => {
            const debugResponse = this.generateDebugModeResponse(content);
            this.addChatMessage("assistant", debugResponse);
        }, 1000);
    }
    
    // デバッグモード用の応答生成
    generateDebugModeResponse(userMessage) {
        console.log('🧪 デバッグモード用応答を生成:', userMessage);
        
        const responses = [
            "デバッグモードで動作中です。構造データが正しく設定されていない可能性があります。",
            "現在テストモードで動作しています。実際のAPI呼び出しは行われません。",
            "デバッグモード: このメッセージはテスト用の応答です。",
            "構造データが空または不正なため、デバッグモードで動作しています。"
        ];
        
        const randomResponse = responses[Math.floor(Math.random() * responses.length)];
        return randomResponse;
    }

    // Chat欄の更新（通知メッセージのみ表示）
    updateChat(messages) {
        const chatMessages = document.querySelector('.chat-messages');
        if (!chatMessages) {
            console.warn('⚠️ chat-messagesエリアが見つかりません');
            return;
        }

        // 既存のメッセージをクリア
        chatMessages.innerHTML = '';

        if (messages && messages.length > 0) {
            messages.forEach(message => {
                const messageElement = this.createChatMessageElement(message);
                chatMessages.appendChild(messageElement);
            });
        } else {
            // 初期メッセージを表示
            const initialMessage = document.createElement('div');
            initialMessage.className = 'chat-message assistant';
            initialMessage.innerHTML = `
                <div class="message-content">
                    <p>こんにちは！アプリの構成について相談してください。</p>
                </div>
            `;
            chatMessages.appendChild(initialMessage);
        }
    }

    // Chatメッセージ要素を作成
    createChatMessageElement(message) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `chat-message ${message.role || 'assistant'}`;
        
        if (message.type) {
            messageDiv.dataset.type = message.type;
        }

        const content = message.content || '';
        messageDiv.innerHTML = `
            <div class="message-content">
                <p>${window.utils.sanitizeHtml(content)}</p>
            </div>
        `;

        return messageDiv;
    }

    // Chat初期化
    initChat() {
        console.log('💬 Chat初期化開始');
        
        // 既存のメッセージを読み込み
        const chatMessages = document.querySelector('.chat-messages');
        if (chatMessages) {
            const messages = Array.from(chatMessages.children).map(msg => ({
                role: msg.classList.contains('user') ? 'user' : 'assistant',
                content: msg.querySelector('.message-content')?.textContent || '',
                type: msg.dataset.type || 'message'
            }));
            this.updateChat(messages);
        }
    }

    // メッセージ送信処理
    sendMessage(messageContent = null) {
        const inputField = document.getElementById("chat-input");
        
        if (!inputField) {
            console.warn("❌ #chat-input が見つかりませんでした。");
            return;
        }
        
        const content = messageContent || inputField.value.trim();
        
        if (!content) {
            console.warn("⚠️ メッセージ内容が空です");
            return;
        }

        console.log("📤 メッセージ送信:", content);

        // ユーザーメッセージを追加
        this.addChatMessage("user", content);

        // 入力フィールドをクリア
        inputField.value = "";

        // デバッグモードの場合はサンプル応答を生成
        if (window.isDebugMode || window.isTestMode) {
            console.log("🧪 デバッグモード: サンプル応答を生成");
            const loadingDiv = this.showChatLoadingIndicator("デバッグモードで処理中...");
            
            setTimeout(() => {
                this.hideChatLoadingIndicator(loadingDiv);
                const debugResponse = this.generateDebugModeResponse(content);
                this.addChatMessage("assistant", debugResponse);
                this.addNotification("デバッグモード: サンプル応答を生成しました");
            }, 1000);
            return;
        }

        // ローディングインジケーターを表示
        const loadingDiv = this.showChatLoadingIndicator("送信中...");

        // メッセージ送信処理（実API連携）
        fetch("/api/chat", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": document.querySelector('meta[name="csrf-token"]').getAttribute('content')
            },
            body: JSON.stringify({
                message: content,
                structure_id: window.structureData?.id || null
            })
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            console.log("✅ メッセージ送信成功:", data);
            
            // ローディングインジケーターを非表示
            this.hideChatLoadingIndicator(loadingDiv);

            // アシスタントの応答を追加
            if (data.response) {
                this.addChatMessage("assistant", data.response);
            }

            // 構造データが更新された場合
            if (data.structure_data) {
                this.updateStructureData(data.structure_data);
                
                // すべてのペインを自動展開
                console.log('🔄 構造データ更新後、すべてのペインを自動展開');
                this.ensureAllPanesExpanded();
            }

            // 通知メッセージがある場合
            if (data.notification) {
                this.addNotification(data.notification);
            }

            // 成功通知
            this.addNotification("メッセージが正常に送信されました");
        })
        .catch(error => {
            console.error("❌ メッセージ送信エラー:", error);
            
            // ローディングインジケーターを非表示
            this.hideChatLoadingIndicator(loadingDiv);

            // エラーメッセージを表示
            this.addChatMessage("assistant", `エラーが発生しました: ${error.message}`, "error");
        });
    }

    // Chatメッセージを追加
    addChatMessage(role, content, type = null) {
        const chatMessages = document.querySelector('.chat-messages');
        if (!chatMessages) {
            console.warn('⚠️ chat-messagesエリアが見つかりません');
            return;
        }

        // Claude評価の出力はChat欄に表示しない（中央ペインのみ）
        if (type === 'claude_evaluation' || 
            (role === 'assistant' && content && content.includes('Claude評価')) ||
            (role === 'assistant' && content && content.includes('評価結果'))) {
            console.log('🔒 Claude評価出力をChat欄に表示しない（中央ペイン専用）:', {
                type: type,
                role: role,
                contentPreview: content ? content.substring(0, 100) : 'null'
            });
            return;
        }

        // Gemini補完の出力もChat欄に表示しない（右ペイン専用）
        if (type === 'gemini_completion' || 
            (role === 'assistant' && content && content.includes('Gemini補完')) ||
            (role === 'assistant' && content && content.includes('構成生成'))) {
            console.log('🔒 Gemini補完出力をChat欄に表示しない（右ペイン専用）:', {
                type: type,
                role: role,
                contentPreview: content ? content.substring(0, 100) : 'null'
            });
            return;
        }

        const messageElement = this.createChatMessageElement({
            role: role,
            content: content,
            type: type
        });

        chatMessages.appendChild(messageElement);
        
        // スクロールを最下部に移動
        chatMessages.scrollTop = chatMessages.scrollHeight;

        // メッセージタイプに応じた処理
        if (type === "structure") {
            console.log('🔍 structureタイプのメッセージを検出:', {
                content: content,
                contentType: typeof content,
                hasStructureCards: !!window.structureCards,
                structureCardsMethod: typeof window.structureCards?.updateFromStructureData
            });
            
            if (window.structureCards && typeof window.structureCards.updateFromStructureData === 'function') {
                console.log('✅ structureCards.updateFromStructureDataを呼び出し');
                window.structureCards.updateFromStructureData(content);
            } else {
                console.error('❌ structureCardsまたはupdateFromStructureDataメソッドが見つかりません');
            }
        }
    }

    // Chatローディングインジケーターを表示
    showChatLoadingIndicator(message = '送信中...') {
        const chatMessages = document.querySelector('.chat-messages');
        if (!chatMessages) return null;

        const loadingDiv = document.createElement('div');
        loadingDiv.className = 'chat-message assistant loading';
        loadingDiv.innerHTML = `
            <div class="message-content">
                <p>${message}</p>
                <div class="loading-spinner"></div>
            </div>
        `;

        chatMessages.appendChild(loadingDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;

        return loadingDiv;
    }

    // Chatローディングインジケーターを非表示
    hideChatLoadingIndicator(loadingDiv) {
        if (loadingDiv && loadingDiv.parentNode) {
            loadingDiv.remove();
        }
    }

    // Chat要素の初期化
    initializeChatElements() {
        console.log("✏️ Chat要素初期化開始");
        console.log("📅 Chat初期化開始時刻:", new Date().toISOString());
        
        // DOMContentLoadedイベントを使用してDOM描画後にイベントを登録
        if (document.readyState === 'loading') {
            console.log("⏳ DOMContentLoadedを待機中...");
            document.addEventListener('DOMContentLoaded', () => {
                console.log("✅ DOMContentLoaded完了 - Chat要素バインド開始");
                this.bindChatElements();
            });
        } else {
            console.log("✅ DOMContentLoaded既に完了 - 即座にChat要素バインド");
            // DOMが既に読み込まれている場合は即座に実行
            this.bindChatElements();
        }
        
        // UI初期化完了イベントをリッスン
        document.addEventListener('aideXInitComplete', (event) => {
            console.log('🎯 UI初期化完了イベントを受信 - チャット機能を有効化:', event.detail);
            this.enableChatFunctionality();
        });
        
        // フォールバック: 3秒後に強制チャット機能有効化
        setTimeout(() => {
            console.log('🔄 3秒経過 - 強制チャット機能有効化');
            this.enableChatFunctionality();
        }, 3000);
    }

    // Chat要素のバインド処理
    bindChatElements() {
        console.log("🔍 Chat要素バインド処理開始");
        
        const sendButton = document.getElementById("send-button");
        const inputField = document.getElementById("chat-input");

        console.log("🔍 要素確認:", {
            sendButton: sendButton ? "✅ found" : "❌ not found",
            inputField: inputField ? "✅ found" : "❌ not found"
        });

        // nullチェック強化
        if (!sendButton) {
            console.warn("❌ #send-button が見つかりませんでした。");
            return;
        }
        
        if (!inputField) {
            console.warn("❌ #chat-input が見つかりませんでした。");
            return;
        }

        console.log("✅ 要素が見つかりました。イベントバインドを実行します。");
        
        // 送信ボタンのクリックイベント
        sendButton.addEventListener("click", () => {
            const content = inputField.value.trim();
            if (content) {
                this.sendMessage(content);
                inputField.value = "";
            }
        });

        // Enterキーで送信
        inputField.addEventListener("keydown", (e) => {
            if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                const content = inputField.value.trim();
                if (content) {
                    this.sendMessage(content);
                    inputField.value = "";
                }
            }
        });

        console.log("✅ Chat送信ボタンと入力欄にイベントをバインドしました");
    }

    // 構造データを更新
    updateStructureData(structureData) {
        console.log('🔄 構造データ更新開始:', {
            hasStructure: !!structureData,
            structureKeys: structureData ? Object.keys(structureData) : 'null',
            hasModules: structureData && 'modules' in structureData,
            hasEvaluations: structureData && 'evaluations' in structureData,
            hasGeminiOutput: structureData && 'gemini_output' in structureData,
            hasCompletions: structureData && 'completions' in structureData
        });
        
        // グローバル変数に保存（Claude評価状況確認用）
        window.currentStructureData = structureData;
        
        // 構成カードの更新
        if (window.structureCards) {
            console.log('✅ structureCards更新を実行');
            window.structureCards.updateFromStructureData(structureData);
        } else {
            console.warn('⚠️ structureCardsインスタンスが見つかりません');
        }
        
        // Claude評価の更新（安全チェック付き）
        if (window.claudeRenderer && typeof window.claudeRenderer.updateFromStructureData === 'function') {
            console.log('✅ claudeRenderer更新を実行');
            window.claudeRenderer.updateFromStructureData(structureData);
        } else {
            console.warn('⚠️ claudeRendererインスタンスまたはupdateFromStructureData関数が見つかりません:', {
                hasClaudeRenderer: !!window.claudeRenderer,
                updateFromStructureDataType: window.claudeRenderer ? typeof window.claudeRenderer.updateFromStructureData : 'undefined'
            });
        }
        
        // Gemini補完の更新（強化版）
        if (window.geminiParser && typeof window.geminiParser.updateFromStructureData === 'function') {
            console.log('✅ GeminiParser更新を実行');
            try {
                window.geminiParser.updateFromStructureData(structureData);
                console.log('✅ GeminiParser更新完了');
                
                // 右ペインの表示を確実にする
                const geminiOutput = document.getElementById('gemini-output');
                if (geminiOutput) {
                    geminiOutput.style.display = 'block';
                    geminiOutput.style.visibility = 'visible';
                    geminiOutput.style.opacity = '1';
                    console.log('✅ 右ペイン表示を確実にしました');
                } else {
                    console.warn('⚠️ #gemini-output要素が見つかりません');
                }
            } catch (e) {
                console.error('❌ GeminiParser更新エラー:', e);
            }
        } else {
            console.warn('⚠️ geminiParserインスタンスが見つかりません:', {
                hasGeminiParser: !!window.geminiParser,
                updateFromStructureDataType: window.geminiParser ? typeof window.geminiParser.updateFromStructureData : 'undefined'
            });
        }
        
        console.log('✅ 構造データ更新完了');
    }

    // 構造差分を描画
    renderStructureDiff(geminiOutput) {
        console.log('🔍 チャットハンドラー: 構造差分描画開始');
        
        // Claude評価データを取得
        const claudeData = window.structureData?.claude_evaluation || window.structureData?.evaluation;
        
        if (!claudeData) {
            console.warn('⚠️ Claude評価データが見つかりません');
            return;
        }
        
        if (!geminiOutput) {
            console.warn('⚠️ Gemini出力データが見つかりません');
            return;
        }
        
        // DiffRendererが利用可能かチェック
        if (window.diffRenderer && typeof window.diffRenderer.renderStructureDiff === 'function') {
            console.log('✅ DiffRendererを使用して差分を描画');
            window.diffRenderer.renderStructureDiff(claudeData, geminiOutput);
        } else if (window.renderStructureDiff) {
            console.log('✅ グローバル関数を使用して差分を描画');
            const diffContainer = document.getElementById('diff-content');
            window.renderStructureDiff(claudeData, geminiOutput, diffContainer);
        } else {
            console.warn('⚠️ 差分描画機能が見つかりません');
        }
    }

    // Yes/No応答処理
    handleYesNoResponse(answer) {
        console.log(`🤔 Yes/No応答処理開始: ${answer}`);
        
        if (!this.structureId) {
            console.error('❌ structureIdが設定されていません');
            return;
        }
        
        // ローディングインジケーターを表示
        const loadingDiv = this.showChatLoadingIndicator('処理中...');
        
        fetch(`/unified/${this.structureId}/yes_no_response`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": this.csrfToken,
            },
            body: JSON.stringify({ answer: answer })
        })
        .then((res) => res.json())
        .then((data) => {
            console.log('✅ Yes/No応答処理完了:', data);
            
            // ローディングインジケーターを非表示
            this.hideChatLoadingIndicator(loadingDiv);
            
            // 通知メッセージを表示
            if (data.message) {
                this.addNotification(data.message);
            }
            
            // 構成ビューを更新
            if (window.refreshStructureView && typeof window.refreshStructureView === 'function') {
                window.refreshStructureView();
            } else {
                console.warn('⚠️ refreshStructureView関数が見つかりません');
            }
        })
        .catch((error) => {
            console.error('❌ Yes/No応答処理エラー:', error);
            this.hideChatLoadingIndicator(loadingDiv);
            this.addNotification('応答処理中にエラーが発生しました。');
        });
    }

    // 通知メッセージを追加
    addNotification(message) {
        console.log('📢 通知メッセージを追加:', message);
        
        // Chat欄に通知メッセージを追加
        this.addChatMessage('assistant', message, 'notification');
        
        // 通知用の特別なスタイルを適用
        const chatMessages = document.querySelector('.chat-messages');
        if (chatMessages) {
            const lastMessage = chatMessages.lastElementChild;
            if (lastMessage) {
                lastMessage.classList.add('notification-message');
            }
        }
    }
    
    // デバッグ用：右ペインの状態を確認
    debugRightPane() {
        console.log('🔍 右ペインデバッグ情報:');
        
        const geminiOutput = document.getElementById('gemini-output');
        if (geminiOutput) {
            console.log('✅ #gemini-output要素存在確認:', {
                display: geminiOutput.style.display,
                visibility: geminiOutput.style.visibility,
                opacity: geminiOutput.style.opacity,
                width: geminiOutput.style.width,
                height: geminiOutput.style.height,
                position: geminiOutput.style.position,
                zIndex: geminiOutput.style.zIndex,
                childrenCount: geminiOutput.children.length,
                innerHTML: geminiOutput.innerHTML.substring(0, 200) + '...'
            });
        } else {
            console.error('❌ #gemini-output要素が見つかりません');
        }
        
        const rightPane = document.querySelector('.right-pane');
        if (rightPane) {
            console.log('✅ .right-pane要素存在確認:', {
                display: rightPane.style.display,
                width: rightPane.style.width,
                visibility: rightPane.style.visibility,
                childrenCount: rightPane.children.length
            });
        } else {
            console.error('❌ .right-pane要素が見つかりません');
        }
        
        console.log('🔧 GeminiParser状態:', {
            hasGeminiParser: !!window.geminiParser,
            updateFromStructureDataType: window.geminiParser ? typeof window.geminiParser.updateFromStructureData : 'undefined'
        });
        
        console.log('📦 構造データ状態:', {
            hasStructureData: !!window.structureData,
            hasGeminiOutput: window.structureData ? !!window.structureData.gemini_output : false,
            hasCompletions: window.structureData ? !!window.structureData.completions : false
        });
    }

    // 中央ペインを自動展開
    ensureCenterPaneExpanded() {
        console.log('🔄 中央ペインを自動展開');
        
        const centerPane = document.querySelector('.center-pane');
        if (centerPane) {
            centerPane.classList.remove('collapsed');
            console.log('✅ 中央ペインを展開しました');
        } else {
            console.error('❌ .center-pane要素が見つかりません');
        }
    }

    // すべてのペインを自動展開
    ensureAllPanesExpanded() {
        console.log('🔄 すべてのペインを自動展開');
        
        const chatPane = document.querySelector('.chat-pane');
        const centerPane = document.querySelector('.center-pane');
        const rightPane = document.querySelector('.right-pane');
        
        if (chatPane) {
            chatPane.classList.remove('collapsed');
            console.log('✅ チャットペインを展開しました');
        }
        
        if (centerPane) {
            centerPane.classList.remove('collapsed');
            console.log('✅ 中央ペインを展開しました');
        }
        
        if (rightPane) {
            rightPane.classList.remove('collapsed');
            console.log('✅ 右ペインを展開しました');
        }
        
        // レイアウトを調整
        adjustLayout();
    }

    // チャット機能の有効化（新規追加）
    enableChatFunctionality() {
        console.log('🔓 チャット機能有効化開始');
        console.log('📅 チャット機能有効化開始時刻:', new Date().toISOString());
        
        // チャット入力欄の有効化
        const chatInput = document.getElementById('chat-input');
        if (chatInput) {
            chatInput.disabled = false;
            chatInput.style.opacity = '1';
            chatInput.style.pointerEvents = 'auto';
            chatInput.style.visibility = 'visible';
            chatInput.removeAttribute('readonly');
            chatInput.placeholder = 'メッセージを入力してください...';
            console.log('✅ チャット入力欄を有効化:', {
                disabled: chatInput.disabled,
                opacity: chatInput.style.opacity,
                pointerEvents: chatInput.style.pointerEvents,
                visibility: chatInput.style.visibility,
                readonly: chatInput.readOnly
            });
        } else {
            console.warn('⚠️ チャット入力欄が見つかりません');
        }
        
        // 送信ボタンの有効化
        const sendButton = document.getElementById('send-button');
        if (sendButton) {
            sendButton.disabled = false;
            sendButton.style.opacity = '1';
            sendButton.style.pointerEvents = 'auto';
            sendButton.style.visibility = 'visible';
            console.log('✅ 送信ボタンを有効化:', {
                disabled: sendButton.disabled,
                opacity: sendButton.style.opacity,
                pointerEvents: sendButton.style.pointerEvents,
                visibility: sendButton.style.visibility
            });
        } else {
            console.warn('⚠️ 送信ボタンが見つかりません');
        }
        
        // チャットメッセージエリアの有効化
        const chatMessages = document.getElementById('chat-messages');
        if (chatMessages) {
            chatMessages.style.pointerEvents = 'auto';
            chatMessages.style.opacity = '1';
            chatMessages.style.visibility = 'visible';
            console.log('✅ チャットメッセージエリアを有効化');
        }
        
        // チャットペイン全体の有効化
        const chatPane = document.querySelector('.chat-pane');
        if (chatPane) {
            chatPane.style.pointerEvents = 'auto';
            chatPane.style.opacity = '1';
            chatPane.style.visibility = 'visible';
            console.log('✅ チャットペインを有効化');
        }
        
        // ローディング状態の解除
        this.removeChatLoadingStates();
        
        // イベントバインドの再実行（確実性のため）
        this.bindChatElements();
        
        console.log('✅ チャット機能有効化完了');
        console.log('📅 チャット機能有効化完了時刻:', new Date().toISOString());
    }

    // チャットローディング状態の解除（新規追加）
    removeChatLoadingStates() {
        console.log('🔄 チャットローディング状態解除開始');
        
        // チャットローディングインジケーターの非表示
        const chatLoadingElements = document.querySelectorAll('.chat-message.assistant.loading');
        chatLoadingElements.forEach(element => {
            if (element.parentNode) {
                element.remove();
                console.log('✅ チャットローディング要素を削除:', element);
            }
        });
        
        // チャット関連のローディング要素の非表示
        const aideLoadingElements = document.querySelectorAll('.aide-loading-message, .aide-loading-spinner');
        aideLoadingElements.forEach(element => {
            element.style.display = 'none';
            console.log('✅ チャット関連ローディング要素を非表示:', element);
        });
        
        console.log('✅ チャットローディング状態解除完了');
    }
}

// クラスをグローバルに公開
window.ChatHandler = ChatHandler; 