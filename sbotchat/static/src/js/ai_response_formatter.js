/**
 * AI Response Formatter - Enhanced with DeepSeek Intelligence
 * Combines simple table formatting with intelligent scenario generation
 */
class AIResponseFormatter {
    constructor() {
        this.initializeFormatter();
        this.deepSeekConfig = null;
        this.initializeDeepSeekConfig();
    }

    initializeFormatter() {
        // Initialize markdown patterns
        this.markdownPatterns = {
            // Headers
            h1: /^# (.+)$/gm,
            h2: /^## (.+)$/gm,
            h3: /^### (.+)$/gm,
            h4: /^#### (.+)$/gm,
            
            // Text formatting
            bold: /\*\*(.*?)\*\*/g,
            italic: /\*(.*?)\*/g,
            code: /`([^`]+)`/g,
            
            // Lists
            unorderedList: /^[*-] (.+)$/gm,
            orderedList: /^(\d+)\. (.+)$/gm,
            
            // Links and special
            link: /\[([^\]]+)\]\(([^)]+)\)/g,
            emoji: /([\u{1F600}-\u{1F64F}]|[\u{1F300}-\u{1F5FF}]|[\u{1F680}-\u{1F6FF}]|[\u{1F1E0}-\u{1F1FF}]|[\u{2600}-\u{26FF}]|[\u{2700}-\u{27BF}])/gu,
            
            // Code blocks
            codeBlock: /```(\w+)?\n([\s\S]*?)```/g,
            
            // Tables
            table: /(\|.*\|.*\n)+/g,
            
            // HR specific patterns  
            hrAction: /🤖.*?(API|action|thực hiện).*?/gi,
            hrData: /(\d+)\s*(nhân viên|employees|người|phòng ban|departments)/gi,
            hrStatus: /(hoàn thành|thành công|lỗi|đang xử lý)/gi,
            
            // Scenario keywords for enhanced detection
            scenarioKeywords: /(trường hợp|kịch bản|tình huống|scenario|case|situation|onboarding|performance|policy|workflow|process)/gi
        };

        // CSS classes for enhanced styling
        this.cssClasses = {
            container: 'ai-response-formatted',
            header: 'ai-response-header',
            content: 'ai-response-content',
            codeBlock: 'ai-code-block',
            table: 'ai-table-container',
            list: 'ai-list-formatted',
            hrAction: 'ai-hr-action',
            scenario: 'ai-intelligent-scenario-section',
            loader: 'ai-formatting-loader'
        };
    }

    /**
     * Initialize DeepSeek configuration from Odoo
     */
    async initializeDeepSeekConfig() {
        try {
            // Try to get config from current page context or make API call
            if (window.sbotchatConfig) {
                this.deepSeekConfig = window.sbotchatConfig;
            } else {
                // Fallback to API call
                const response = await fetch('/sbotchat/config', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-Requested-With': 'XMLHttpRequest'
                    },
                    body: JSON.stringify({})
                });
                const data = await response.json();
                this.deepSeekConfig = data.result;
            }
            console.log('DeepSeek config loaded successfully');
        } catch (error) {
            console.warn('Could not load DeepSeek config, using fallback:', error);
            this.deepSeekConfig = null;
        }
    }

    /**
     * Main formatting function - enhanced with AI intelligence
     */
    async formatResponse(content, messageType = 'assistant', data = null) {
        if (!content || typeof content !== 'string') {
            return this.createErrorMessage('Nội dung không hợp lệ');
        }

        try {
            // Detect response type
            const responseType = this.detectResponseType(content, data);
            
            // Use DeepSeek AI to intelligently enhance content with scenario tables
            let enhancedContent = await this.intelligentScenarioGeneration(content);
            
            // Apply specific formatting based on type
            let formattedContent = this.applyTypeSpecificFormatting(enhancedContent, responseType, data);
            
            // Apply general markdown formatting
            formattedContent = this.formatMarkdown(formattedContent);
            
            // Create final container with enhanced styling
            return this.createFormattedContainer(formattedContent, responseType, messageType);
            
        } catch (error) {
            console.error('AI Response Formatter Error:', error);
            return this.createErrorMessage('Lỗi khi format response: ' + error.message);
        }
    }

    /**
     * Detect content type for formatting
     */
    detectResponseType(content, data) {
        if (data && data.hr_action) {
            return 'hr_action';
        }
        
        // Simple table detection
        if (content.includes('|') && content.split('\n').filter(line => line.includes('|')).length >= 2) {
            return 'table';
        }
        
        if (content.includes('```')) {
            return 'code';
        }
        
        if (content.includes('✅') || content.includes('❌') || content.includes('⚠️')) {
            return 'status';
        }
        
        return 'markdown';
    }

    /**
     * Apply specific formatting based on type
     */
    applyTypeSpecificFormatting(content, type, data) {
        switch (type) {
            case 'hr_action':
                return this.formatHRAction(content, data);
            case 'table':
                return this.formatSimpleTable(content);
            case 'code':
                return this.formatCode(content);
            case 'status':
                return this.formatStatus(content);
            default:
                return content;
        }
    }

    /**
     * Format HR Actions - simplified
     */
    formatHRAction(content, data) {
        let formatted = `
<div class="ai-hr-action-response">
    <div class="hr-action-header">
        <div class="hr-action-title">
            <h4>🤖 HR Assistant</h4>
        </div>
    </div>
`;

        // Add API info if available
        if (data?.api_called) {
            formatted += `
    <div class="hr-action-details">
        <div class="action-detail-item">
            <strong>API:</strong> <code>${data.api_called}</code>
        </div>
    </div>
`;
        }

        formatted += `
    <div class="hr-action-content">
        ${this.formatMarkdown(content)}
    </div>
</div>
`;

        return formatted;
    }

    /**
     * Simple table formatting - no complex scenario generation
     */
    formatSimpleTable(content) {
        const lines = content.split('\n');
        let tableLines = [];
        let nonTableContent = [];
        let inTable = false;
        
        lines.forEach(line => {
            if (line.includes('|') && line.trim().length > 0) {
                tableLines.push(line);
                inTable = true;
            } else if (inTable && line.trim() === '') {
                // End of table
                if (tableLines.length > 0) {
                    nonTableContent.push(this.createSimpleHTMLTable(tableLines));
                    tableLines = [];
                }
                inTable = false;
                nonTableContent.push(line);
            } else {
                if (inTable && tableLines.length > 0) {
                    nonTableContent.push(this.createSimpleHTMLTable(tableLines));
                    tableLines = [];
                    inTable = false;
                }
                nonTableContent.push(line);
            }
        });
        
        // Handle remaining table
        if (tableLines.length > 0) {
            nonTableContent.push(this.createSimpleHTMLTable(tableLines));
        }
        
        return nonTableContent.join('\n');
    }

    /**
     * Create simple HTML table from markdown table lines
     */
    createSimpleHTMLTable(lines) {
        if (lines.length < 2) return lines.join('\n');
        
        // Filter out empty lines and separator lines
        const validLines = lines.filter(line => {
            const trimmed = line.trim();
            return trimmed.length > 0 && 
                   trimmed.includes('|') && 
                   !trimmed.match(/^[\|\s\-:]+$/); // Skip separator lines like |---|---|
        });
        
        if (validLines.length < 1) return lines.join('\n');
        
        const headerLine = validLines[0];
        const dataLines = validLines.slice(1);
        
        // Parse header - more careful parsing
        const headerCells = this.parseTableRow(headerLine);
        if (headerCells.length === 0) return lines.join('\n');
        
        let html = `
<div class="ai-table-container">
    <table class="ai-table">
        <thead>
            <tr>`;
        
        headerCells.forEach(header => {
            html += `<th>${this.escapeHtml(header)}</th>`;
        });
        
        html += `
            </tr>
        </thead>
        <tbody>`;
        
        // Parse data rows - ensure same number of columns
        dataLines.forEach(line => {
            const cells = this.parseTableRow(line);
            if (cells.length > 0) {
                html += '<tr>';
                
                // Ensure we have the same number of cells as headers
                for (let i = 0; i < headerCells.length; i++) {
                    const cellContent = cells[i] || ''; // Use empty string if cell doesn't exist
                    html += `<td>${this.escapeHtml(cellContent)}</td>`;
                }
                
                html += '</tr>';
            }
        });
        
        html += `
        </tbody>
    </table>
</div>`;
        
        return html;
    }

    /**
     * Parse a table row and return array of cell contents
     */
    parseTableRow(line) {
        if (!line || !line.includes('|')) return [];
        
        // Split by | and clean up
        let cells = line.split('|');
        
        // Remove first and last empty cells if they exist (from leading/trailing |)
        if (cells.length > 0 && cells[0].trim() === '') {
            cells = cells.slice(1);
        }
        if (cells.length > 0 && cells[cells.length - 1].trim() === '') {
            cells = cells.slice(0, -1);
        }
        
        // Trim all cells but keep empty ones to maintain column structure
        return cells.map(cell => cell.trim());
    }

    /**
     * Format Code - simplified without copy buttons
     */
    formatCode(content) {
        // Code blocks
        content = content.replace(this.markdownPatterns.codeBlock, (match, lang, code) => {
            const language = lang || 'text';
            return `
<div class="ai-code-block">
    <div class="code-header">
        <span class="code-language">${language}</span>
    </div>
    <pre class="code-content"><code class="language-${language}">${this.escapeHtml(code.trim())}</code></pre>
</div>
`;
        });

        // Inline code
        content = content.replace(this.markdownPatterns.code, '<code class="ai-inline-code">$1</code>');

        return content;
    }

    /**
     * Format Status Messages - simplified
     */
    formatStatus(content) {
        let statusType = 'info';
        let icon = 'ℹ️';

        if (/✅|thành công|hoàn thành/i.test(content)) {
            statusType = 'success';
            icon = '✅';
        } else if (/❌|lỗi|error|failed/i.test(content)) {
            statusType = 'error';
            icon = '❌';
        } else if (/⚠️|cảnh báo|warning/i.test(content)) {
            statusType = 'warning';
            icon = '⚠️';
        }

        return `
<div class="ai-status-message ai-status-${statusType}">
    <div class="status-icon">${icon}</div>
    <div class="status-content">
        ${content}
    </div>
</div>
`;
    }

    /**
     * Apply general markdown formatting - enhanced for scenario tables
     */
    formatMarkdown(content) {
        // Headers
        content = content.replace(this.markdownPatterns.h1, '<h1 class="ai-h1">$1</h1>');
        content = content.replace(this.markdownPatterns.h2, '<h2 class="ai-h2">$1</h2>');
        content = content.replace(this.markdownPatterns.h3, '<h3 class="ai-h3">$1</h3>');
        content = content.replace(this.markdownPatterns.h4, '<h4 class="ai-h4">$1</h4>');

        // Text formatting
        content = content.replace(this.markdownPatterns.bold, '<strong class="ai-bold">$1</strong>');
        content = content.replace(this.markdownPatterns.italic, '<em class="ai-italic">$1</em>');

        // Links
        content = content.replace(this.markdownPatterns.link, 
            '<a href="$2" class="ai-link" target="_blank" rel="noopener noreferrer">$1</a>');

        // Smart line break handling - preserve scenario table structure
        if (content.includes('ai-intelligent-scenario-section')) {
            // For content with scenario tables, use conservative line break handling
            content = content.replace(/\n(?![<\s])/g, '<br>');
        } else {
            // For regular content, convert double line breaks to paragraphs
            content = content.replace(/\n\n/g, '</p><p class="ai-paragraph">');
            content = content.replace(/\n/g, '<br>');
            
            // Wrap in paragraphs if not already structured
            if (!content.includes('<p>') && !content.includes('<div>') && !content.includes('<h')) {
                content = `<p class="ai-paragraph">${content}</p>`;
            }
        }

        return content;
    }

    /**
     * Create formatted container
     */
    createFormattedContainer(content, type, messageType) {
        const containerClass = `${this.cssClasses.container} ai-response-type-${type}`;
        
        return `
<div class="${containerClass}">
    <div class="ai-response-body">
        ${content}
    </div>
</div>
`;
    }

    /**
     * Create error message
     */
    createErrorMessage(message) {
        return `
<div class="ai-response-error">
    <div class="error-icon">⚠️</div>
    <div class="error-message">
        ${message}
    </div>
</div>
`;
    }

    /**
     * Escape HTML to prevent XSS
     */
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    /**
     * Use DeepSeek AI to intelligently decide when to create enhanced scenario tables
     */
    async intelligentScenarioGeneration(content) {
        try {
            // Skip if no DeepSeek config or content too short
            if (!this.deepSeekConfig || !this.deepSeekConfig.api_key || content.length < 50) {
                return content;
            }

            // Enhanced keyword detection
            const hasScenarioKeywords = this.markdownPatterns.scenarioKeywords.test(content);
            const hasHRContext = /nhân viên|employee|phòng ban|department|tuyển dụng|recruitment|lương|salary|nghỉ phép|leave/.test(content);
            
            // Only analyze if content seems relevant for scenario generation
            if (!hasScenarioKeywords && !hasHRContext) {
                return content;
            }

            // Call DeepSeek API to analyze content
            const scenarioAnalysis = await this.analyzeContentWithDeepSeek(content);
            
            if (scenarioAnalysis && scenarioAnalysis.should_create_table) {
                return this.createEnhancedScenarioTable(content, scenarioAnalysis);
            }

            return content;
        } catch (error) {
            console.warn('DeepSeek scenario analysis failed, using original content:', error);
            return content;
        }
    }

    /**
     * Analyze content with DeepSeek to determine if scenario table is needed
     */
    async analyzeContentWithDeepSeek(content) {
        const prompt = `Analyze the following HR-related content and determine if it would benefit from a scenario table with priority levels. 

Content: "${content}"

Please respond with JSON only:
{
    "should_create_table": boolean,
    "table_title": "string (if table needed)",
    "scenarios": [
        {
            "situation": "description of HR situation",
            "action": "recommended action to take",
            "priority": "high|medium|low"
        }
    ]
}

Create scenarios only if the content discusses HR situations that would benefit from structured decision-making (hiring, leave management, performance issues, onboarding, compliance, etc.). Keep scenarios practical and actionable with clear priority levels.`;

        try {
            const response = await fetch('https://api.deepseek.com/chat/completions', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${this.deepSeekConfig.api_key}`
                },
                body: JSON.stringify({
                    model: this.deepSeekConfig.model_type || 'deepseek-chat',
                    messages: [
                        {
                            role: 'system',
                            content: 'You are an expert HR management AI assistant. Respond only with valid JSON.'
                        },
                        {
                            role: 'user',
                            content: prompt
                        }
                    ],
                    temperature: 0.3,
                    max_tokens: 1000
                })
            });

            if (!response.ok) {
                throw new Error(`DeepSeek API error: ${response.status}`);
            }

            const data = await response.json();
            const responseContent = data.choices[0].message.content.trim();
            
            // Parse JSON response
            const jsonMatch = responseContent.match(/\{[\s\S]*\}/);
            if (jsonMatch) {
                return JSON.parse(jsonMatch[0]);
            }
            
            return { should_create_table: false };
        } catch (error) {
            console.warn('DeepSeek API call failed:', error);
            return { should_create_table: false };
        }
    }

    /**
     * Create enhanced scenario table with priority badges and animations
     */
    createEnhancedScenarioTable(originalContent, analysis) {
        if (!analysis.scenarios || analysis.scenarios.length === 0) {
            return originalContent;
        }

        const tableTitle = analysis.table_title || 'Các tình huống cần xem xét';
        
        let tableHTML = `
<div class="ai-intelligent-scenario-section">
    <h3 class="scenario-title">${this.escapeHtml(tableTitle)}</h3>
    <div class="scenario-table-container">
        <table class="ai-scenario-table">
            <thead>
                <tr>
                    <th class="scenario-number">#</th>
                    <th class="scenario-situation">Tình huống</th>
                    <th class="scenario-action">Hành động khuyến nghị</th>
                    <th class="scenario-priority">Mức độ ưu tiên</th>
                </tr>
            </thead>
            <tbody>
`;

        analysis.scenarios.forEach((scenario, index) => {
            const priorityClass = `priority-${scenario.priority || 'medium'}`;
            const priorityText = this.getPriorityText(scenario.priority);
            
            tableHTML += `
                <tr class="scenario-row" data-priority="${scenario.priority || 'medium'}">
                    <td class="scenario-number">${index + 1}</td>
                    <td class="scenario-situation">${this.escapeHtml(scenario.situation)}</td>
                    <td class="scenario-action">${this.escapeHtml(scenario.action)}</td>
                    <td class="scenario-priority">
                        <span class="priority-badge ${priorityClass}">${priorityText}</span>
                    </td>
                </tr>
`;
        });

        tableHTML += `
            </tbody>
        </table>
    </div>
    <div class="scenario-note">
        <i class="note-icon">💡</i>
        <span>Bảng tình huống được tạo tự động bởi AI DeepSeek để hỗ trợ ra quyết định</span>
    </div>
</div>
`;

        return originalContent + '\n\n' + tableHTML;
    }

    /**
     * Get priority text in Vietnamese
     */
    getPriorityText(priority) {
        switch (priority) {
            case 'high': return 'Cao';
            case 'medium': return 'Trung bình';
            case 'low': return 'Thấp';
            default: return 'Trung bình';
        }
    }

    /**
     * Create loading indicator for AI processing
     */
    createLoadingIndicator() {
        return `
        <div class="${this.cssClasses.loader}">
            <div class="formatting-spinner"></div>
            <span>AI đang phân tích và tạo bảng thông minh...</span>
        </div>`;
    }
}

// CSS Styles for Simple Gray-White Theme + Beautiful Scenario Tables
const aiResponseFormatterCSS = `
/* AI Response Formatter - Simple Gray-White Theme + Intelligent Tables */
.ai-response-formatted {
    background: #ffffff;
    border-radius: 8px;
    padding: 0 !important; /* Đảm bảo không có padding */
    margin: 8px 0;
    border: 1px solid #e5e5e5;
    overflow: hidden;
    color: #374151;
    display: inline-block; /* Giãn theo nội dung */
    width: auto; /* Không chiếm toàn bộ chiều rộng */
}

.ai-response-body {
    padding: 0; /* Loại bỏ padding để nội dung tự giãn */
    line-height: 1.6;
}

/* Headers */
.ai-h1 { 
    font-size: 1.5rem; 
    font-weight: 600; 
    margin: 16px 0 12px 0; 
    color: #111827;
    border-bottom: 2px solid #d1d5db;
    padding-bottom: 8px;
}

.ai-h2 { 
    font-size: 1.3rem; 
    font-weight: 600; 
    margin: 14px 0 10px 0; 
    color: #111827;
    border-left: 4px solid #6b7280;
    padding-left: 12px;
}

.ai-h3 { 
    font-size: 1.1rem; 
    font-weight: 600; 
    margin: 12px 0 8px 0; 
    color: #111827;
}

.ai-h4 { 
    font-size: 1rem; 
    font-weight: 600; 
    margin: 10px 0 6px 0; 
    color: #374151;
}

/* Text formatting */
.ai-paragraph {
    margin: 12px 0;
    color: #374151;
}

.ai-bold {
    font-weight: 600;
    color: #111827;
}

.ai-italic {
    font-style: italic;
    color: #6b7280;
}

.ai-inline-code {
    background: #f3f4f6;
    border: 1px solid #d1d5db;
    border-radius: 4px;
    padding: 2px 6px;
    font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
    font-size: 0.9rem;
    color: #dc2626;
}

.ai-link {
    color: #2563eb;
    text-decoration: none;
    border-bottom: 1px solid transparent;
    transition: all 0.2s;
}

.ai-link:hover {
    border-bottom-color: #2563eb;
}

/* Lists */
.ai-list {
    margin: 12px 0;
    padding-left: 24px;
}

.ai-list li {
    margin: 6px 0;
    color: #374151;
}

.ai-list li::marker {
    color: #6b7280;
}

/* Regular Tables */
.ai-table-container {
    margin: 16px 0;
    overflow-x: auto;
    border-radius: 8px;
    border: 1px solid #d1d5db;
}

.ai-table {
    width: 100%;
    border-collapse: collapse;
    background: #ffffff;
}

.ai-table th {
    background: #f9fafb;
    color: #111827;
    font-weight: 600;
    padding: 12px;
    text-align: left;
    border-bottom: 2px solid #d1d5db;
}

.ai-table td {
    padding: 10px 12px;
    border-bottom: 1px solid #e5e7eb;
    color: #374151;
}

.ai-table tr:hover {
    background: #f9fafb;
}

/* Intelligent Scenario Tables - Beautiful Design */
.ai-intelligent-scenario-section {
    margin: 20px 0;
    background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
    border-radius: 12px;
    padding: 24px;
    border: 1px solid #e2e8f0;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
}

.scenario-title {
    color: #1e293b;
    font-size: 1.2rem;
    font-weight: 600;
    margin: 0 0 16px 0;
    padding-bottom: 8px;
    border-bottom: 2px solid #e2e8f0;
    display: flex;
    align-items: center;
}

.scenario-title::before {
    content: "📋";
    margin-right: 8px;
    font-size: 1.1rem;
}

.scenario-table-container {
    background: #ffffff;
    border-radius: 8px;
    overflow: hidden;
    border: 1px solid #e2e8f0;
    margin-bottom: 16px;
}

.ai-scenario-table {
    width: 100%;
    border-collapse: collapse;
}

.ai-scenario-table th {
    background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
    color: #ffffff;
    font-weight: 600;
    padding: 14px 16px;
    text-align: left;
    font-size: 0.9rem;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}

.ai-scenario-table th.scenario-number {
    width: 60px;
    text-align: center;
}

.ai-scenario-table th.scenario-priority {
    width: 120px;
    text-align: center;
}

.scenario-row {
    transition: all 0.2s ease;
}

.scenario-row:nth-child(even) {
    background: #f8fafc;
}

.scenario-row:hover {
    background: #e0f2fe;
    transform: translateY(-1px);
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.ai-scenario-table td {
    padding: 16px;
    border-bottom: 1px solid #e5e7eb;
    vertical-align: top;
}

.scenario-number {
    text-align: center;
    font-weight: 600;
    color: #6366f1;
    font-size: 1.1rem;
}

.scenario-situation {
    color: #1e293b;
    font-weight: 500;
    line-height: 1.5;
}

.scenario-action {
    color: #475569;
    line-height: 1.5;
}

.priority-badge {
    display: inline-block;
    padding: 4px 12px;
    border-radius: 20px;
    font-size: 0.8rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}

.priority-high {
    background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
    color: #ffffff;
}

.priority-medium {
    background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
    color: #ffffff;
}

.priority-low {
    background: linear-gradient(135deg, #10b981 0%, #059669 100%);
    color: #ffffff;
}

.scenario-note {
    display: flex;
    align-items: center;
    gap: 8px;
    background: #f0f9ff;
    border: 1px solid #bae6fd;
    border-radius: 8px;
    padding: 12px 16px;
    color: #0369a1;
    font-size: 0.9rem;
    font-style: italic;
}

.note-icon {
    font-size: 1.1rem;
}

/* Code blocks */
.ai-code-block {
    margin: 16px 0;
    border-radius: 8px;
    overflow: hidden;
    border: 1px solid #d1d5db;
}

.code-header {
    background: #f3f4f6;
    padding: 8px 12px;
    border-bottom: 1px solid #d1d5db;
}

.code-language {
    font-size: 0.8rem;
    color: #6b7280;
    font-weight: 600;
}

.code-content {
    background: #f8fafc;
    padding: 16px;
    margin: 0;
    overflow-x: auto;
    font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
    font-size: 0.9rem;
    line-height: 1.4;
}

.code-content code {
    color: #111827;
}

/* HR Action Responses */
.ai-hr-action-response {
    background: #f8fafc;
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    overflow: hidden;
}

.hr-action-header {
    background: #f1f5f9;
    padding: 12px 16px;
    border-bottom: 1px solid #e2e8f0;
}

.hr-action-title h4 {
    margin: 0;
    color: #334155;
    font-size: 1rem;
}

.hr-action-details {
    background: #f8fafc;
    padding: 12px 16px;
    border-bottom: 1px solid #e2e8f0;
}

.action-detail-item {
    margin: 6px 0;
    font-size: 0.9rem;
    color: #475569;
}

.hr-action-content {
    padding: 16px;
}

/* Status Messages */
.ai-status-message {
    display: flex;
    align-items: flex-start;
    gap: 12px;
    padding: 12px 16px;
    border-radius: 8px;
    margin: 12px 0;
}

.ai-status-success {
    background: #f0fdf4;
    border: 1px solid #bbf7d0;
}

.ai-status-error {
    background: #fef2f2;
    border: 1px solid #fecaca;
}

.ai-status-warning {
    background: #fffbeb;
    border: 1px solid #fed7aa;
}

.ai-status-info {
    background: #eff6ff;
    border: 1px solid #bfdbfe;
}

.status-icon {
    flex-shrink: 0;
    font-size: 1.2rem;
}

.status-content {
    flex: 1;
    color: #374151;
}

/* Error Messages */
.ai-response-error {
    display: flex;
    align-items: center;
    gap: 12px;
    background: #fef2f2;
    border: 1px solid #fecaca;
    border-radius: 8px;
    padding: 12px 16px;
    color: #dc2626;
}

.error-icon {
    font-size: 1.2rem;
}

.error-message {
    flex: 1;
}

/* Enhanced message formatting */
.ai-formatted-content {
    border-radius: 8px;
    overflow: hidden;
}

.ai-formatted-content .ai-response-formatted {
    margin: 0;
    border: none;
    background: transparent;
}

/* Responsive */
@media (max-width: 768px) {
    .ai-table-container {
        font-size: 0.85rem;
    }
    
    .ai-table th,
    .ai-table td {
        padding: 8px;
    }
    
    .code-content {
        font-size: 0.8rem;
    }
    
    .ai-intelligent-scenario-section {
        padding: 16px;
        margin: 16px 0;
    }
    
    .ai-scenario-table th,
    .ai-scenario-table td {
        padding: 12px 8px;
    }
    
    .ai-scenario-table th.scenario-number,
    .ai-scenario-table th.scenario-priority {
        width: auto;
    }
    
    .priority-badge {
        font-size: 0.7rem;
        padding: 3px 8px;
    }
}
`;

// Inject CSS styles
function injectAIResponseFormatterCSS() {
    if (!document.getElementById('ai-response-formatter-styles')) {
        const style = document.createElement('style');
        style.id = 'ai-response-formatter-styles';
        style.textContent = aiResponseFormatterCSS;
        document.head.appendChild(style);
    }
}

// Auto-inject CSS when script loads
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', injectAIResponseFormatterCSS);
} else {
    injectAIResponseFormatterCSS();
}

// Make AIResponseFormatter globally available
window.AIResponseFormatter = AIResponseFormatter;

export default AIResponseFormatter;