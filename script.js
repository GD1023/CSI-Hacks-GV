function initTermsModal() {
    const modal = document.getElementById('terms-modal');
    if (!modal) return;

    const scrollBox = document.getElementById('terms-scroll');
    const checkbox = document.getElementById('terms-checkbox');
    const acceptBtn = document.getElementById('terms-accept');

    function checkScrolled() {
        const reachedBottom = scrollBox.scrollTop + scrollBox.clientHeight >= scrollBox.scrollHeight - 10;
        if (reachedBottom) {
            checkbox.disabled = false;
        }
    }

    scrollBox.addEventListener('scroll', checkScrolled);
    checkbox.addEventListener('change', () => {
        acceptBtn.disabled = !checkbox.checked;
    });
    acceptBtn.addEventListener('click', () => {
        modal.classList.add('modal-hidden');
    });

    // Handles the case where the summary already fits without scrolling.
    checkScrolled();
}

initTermsModal();
