document.addEventListener('DOMContentLoaded', () => {
    // --- Navigation Logic for Single Page Layout ---
    const navLinks = document.querySelectorAll('.nav-link');
    const sections = document.querySelectorAll('main > section');

    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                navLinks.forEach(link => {
                    link.classList.remove('active');
                    if (`#${entry.target.id}` === link.getAttribute('href')) {
                        link.classList.add('active');
                    }
                });
            }
        });
    }, { rootMargin: "-40% 0px -60% 0px" });

    sections.forEach(section => observer.observe(section));

    // --- Tab Functionality for Connection Examples ---
    const tabContainer = document.getElementById('connection-tabs');
    if (tabContainer) {
        const tabs = tabContainer.querySelectorAll('.tab-button');
        const tabContents = tabContainer.querySelectorAll('.tab-content');
        tabs.forEach(tab => {
            tab.addEventListener('click', () => {
                tabs.forEach(t => t.classList.remove('active'));
                tab.classList.add('active');
                tabContents.forEach(content => {
                    content.classList.remove('active');
                    if(content.id === tab.dataset.target) {
                        content.classList.add('active');
                    }
                });
            });
        });
    }

    // --- Copy Button Functionality ---
    document.querySelectorAll('.copy-btn').forEach(button => {
        button.addEventListener('click', (e) => {
            const codeBlock = e.currentTarget.closest('.code-block');
            const codeToCopy = codeBlock.querySelector('pre');
            
            navigator.clipboard.writeText(codeToCopy.innerText).then(() => {
                e.currentTarget.innerText = 'Copied!';
                setTimeout(() => { e.currentTarget.innerText = 'Copy'; }, 2000);
            });
        });
    });
});
