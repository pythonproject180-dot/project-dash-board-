// Website theme toggle for NexusAI-based public pages
(function() {
    const getStoredTheme = () => localStorage.getItem("theme");
    const setStoredTheme = (theme) => localStorage.setItem("theme", theme);
    const getPreferredTheme = () => {
        const stored = getStoredTheme();
        if (stored) return stored;
        return window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
    };
    const setTheme = (theme) => {
        if (theme === "auto" && window.matchMedia("(prefers-color-scheme: dark)").matches) {
            document.documentElement.setAttribute("data-bs-theme", "dark");
        } else {
            document.documentElement.setAttribute("data-bs-theme", theme);
        }
        // Update website-specific styles
        const body = document.body;
        const nav = document.getElementById('nbar');
        if (theme === "dark") {
            body.style.background = '#1a1a2e';
            body.style.color = '#e0e0e0';
            if (nav) nav.style.background = 'rgba(26,26,46,0.95)';
        } else if (theme === "light") {
            body.style.background = '';
            body.style.color = '';
            if (nav) nav.style.background = '';
        }
    };
    setTheme(getPreferredTheme());
    
    window.addEventListener("DOMContentLoaded", () => {
        const btn = document.getElementById("websiteThemeBtn");
        if (btn) {
            btn.addEventListener("click", () => {
                const current = getStoredTheme() || "light";
                const next = current === "light" ? "dark" : current === "dark" ? "auto" : "light";
                setStoredTheme(next);
                setTheme(next);
                updateBtn(next);
            });
            updateBtn(getPreferredTheme());
        }
    });
    
    function updateBtn(theme) {
        const btn = document.getElementById("websiteThemeBtn");
        if (!btn) return;
        if (theme === "dark") btn.innerHTML = '<i class="fa-solid fa-moon"></i>';
        else if (theme === "auto") btn.innerHTML = '<i class="fa-solid fa-circle-half-stroke"></i>';
        else btn.innerHTML = '<i class="fa-solid fa-sun"></i>';
    }
})();
