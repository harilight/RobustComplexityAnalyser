document.addEventListener('DOMContentLoaded', () => {
    const analyzeBtn = document.getElementById('analyze-btn');
    const resultsContent = document.getElementById('results-content');
    const codeInput = document.getElementById('code-input');

    analyzeBtn.addEventListener('click', async () => {
        // Change button state
        const originalText = analyzeBtn.innerText;
        analyzeBtn.innerText = 'Analyzing...';
        analyzeBtn.disabled = true;
        
        // Show loading state in results
        resultsContent.innerHTML = `
            <div class="empty-state">
                <p>Running static analyzer & dynamic profiler...</p>
            </div>
        `;

        let code = codeInput.value;
        
        // Font Ligature Sanitation
        // Replace visual ligatures that break AST parsing with standard ASCII operators
        code = code.replace(/≠/g, '!=').replace(/≤/g, '<=').replace(/≥/g, '>=').replace(/≡/g, '==');
        
        const language = document.getElementById('language-select').value;
        const generator = document.getElementById('generator-select').value;

        try {
            const response = await fetch('/api/analyze', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ code, language, generator })
            });
            const data = await response.json();
            
            if (!data.success) {
                resultsContent.innerHTML = `<div class="empty-state" style="color: #ef4444;"><p>Error: ${data.error}</p></div>`;
            } else {
                renderResults(data);
            }
        } catch (e) {
            resultsContent.innerHTML = `<div class="empty-state" style="color: #ef4444;"><p>Network Error: ${e.message}</p></div>`;
        } finally {
            analyzeBtn.innerText = originalText;
            analyzeBtn.disabled = false;
        }
    });

    function renderResults(data) {
        let verdictHTML = '';
        let breakdownHTML = '';
        
        if (typeof data.verdict === 'object') {
            verdictHTML = data.verdict.worst;
            breakdownHTML = `
                <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; margin-top: 20px; font-size: 0.9rem; text-align: center;">
                    <div style="background: rgba(255,255,255,0.03); padding: 10px; border-radius: 8px; border-top: 2px solid #22c55e;">
                        <div style="color: var(--text-secondary); margin-bottom: 5px; font-size: 0.8rem;">BEST CASE</div>
                        <div style="font-family: 'Fira Code', monospace; color: #22c55e;">${data.verdict.best}</div>
                    </div>
                    <div style="background: rgba(255,255,255,0.03); padding: 10px; border-radius: 8px; border-top: 2px solid #eab308;">
                        <div style="color: var(--text-secondary); margin-bottom: 5px; font-size: 0.8rem;">AVERAGE CASE</div>
                        <div style="font-family: 'Fira Code', monospace; color: #eab308;">${data.verdict.average}</div>
                    </div>
                    <div style="background: rgba(255,255,255,0.03); padding: 10px; border-radius: 8px; border-top: 2px solid #ef4444;">
                        <div style="color: var(--text-secondary); margin-bottom: 5px; font-size: 0.8rem;">WORST CASE</div>
                        <div style="font-family: 'Fira Code', monospace; color: #ef4444;">${data.verdict.worst}</div>
                    </div>
                </div>
            `;
        } else {
            verdictHTML = data.verdict;
        }

        let confidenceClass = data.confidence === 'HIGH' ? 'good' : (data.confidence === 'MEDIUM' ? 'warning' : 'bad');

        resultsContent.innerHTML = `
            <div class="metric-card animate-in" style="animation-delay: 0.1s">
                <div class="metric-header" style="display: flex; justify-content: space-between; align-items: center;">
                    Reconciled Time Complexity
                    <span class="confidence-badge ${confidenceClass}" style="font-size: 0.75rem; padding: 2px 8px; border-radius: 12px; border: 1px solid currentColor;">${data.confidence} CONFIDENCE</span>
                </div>
                <div class="metric-value ${confidenceClass}" style="font-size: 1.8rem; margin-top: 10px;">${verdictHTML}</div>
                ${breakdownHTML}
                ${data.inferred_structure ? `<div style="margin-top: 15px; font-size: 0.85rem; color: var(--text-secondary); background: rgba(255,255,255,0.05); padding: 8px 12px; border-radius: 6px; border-left: 3px solid var(--accent);"><span style="opacity: 0.7;">✨ ${data.inferred_structure}</span></div>` : ''}
            </div>

            <div class="metric-card animate-in" style="animation-delay: 0.2s">
                <div class="metric-header">Raw Signals</div>
                <div style="display: flex; gap: 20px; margin-top: 10px; font-size: 1.2rem;">
                    <div><strong>Static:</strong> <span style="color: var(--text-secondary);">${data.static}</span></div>
                    <div><strong>Dynamic:</strong> <span style="color: var(--text-secondary);">${data.dynamic}</span></div>
                </div>
            </div>

            <div class="reasoning-box animate-in" style="animation-delay: 0.3s">
                <h3 style="margin-top:0;">🔍 Explainability Trace</h3>
                <p style="margin-bottom:0; line-height:1.6;">${data.reasoning}</p>
            </div>
        `;
    }
});
