document.addEventListener('DOMContentLoaded', function () {

    // --- Modality selection ---
    function updateModalityCount() {
        const count = document.querySelectorAll('.modality-checkbox:checked').length;
        document.getElementById('modalityCount').textContent = `${count} selected`;
    }

    document.querySelectorAll('.modality-checkbox').forEach(cb => {
        cb.addEventListener('change', updateModalityCount);
    });

    document.getElementById('selectAllModalities')?.addEventListener('click', () => {
        document.querySelectorAll('.modality-checkbox').forEach(cb => cb.checked = true);
        updateModalityCount();
    });

    document.getElementById('clearAllModalities')?.addEventListener('click', () => {
        document.querySelectorAll('.modality-checkbox').forEach(cb => cb.checked = false);
        updateModalityCount();
    });

    // Initial count
    updateModalityCount();

    // --- Field selection buttons ---
    document.querySelectorAll('[data-select]').forEach(btn => {
        btn.addEventListener('click', () => {
            const fieldType = btn.dataset.select;
            const action = btn.dataset.action;
            const shouldCheck = action === 'all';
            const selector = fieldType === 'agnostic' ? '.agnostic-field' : '.specific-field';

            document.querySelectorAll(selector).forEach(cb => {
                cb.checked = shouldCheck;
            });
        });
    });

    // --- JSON Copy Button ---
    const copyBtn = document.getElementById('copyJsonButton');
    if (copyBtn) {
        copyBtn.addEventListener('click', () => {
            const jsonText = document.getElementById('jsonDataPreview').textContent;
            navigator.clipboard.writeText(jsonText).then(() => {
                copyBtn.innerHTML = '<i class="fas fa-check"></i> Copied!';
                setTimeout(() => {
                    copyBtn.innerHTML = '<i class="fas fa-copy me-1"></i>Copy JSON';
                }, 2000);
            });
        });
    }
});
