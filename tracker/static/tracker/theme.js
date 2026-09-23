(function () {
    const STORAGE_KEY = "expenseTrackerTheme";

    function applyTheme(theme) {
        document.documentElement.setAttribute("data-theme", theme);

        const button = document.querySelector(".theme-toggle");

        if (button) {
            button.textContent = theme === "dark" ? "☀️" : "🌙";
            button.setAttribute(
                "aria-label",
                theme === "dark"
                    ? "Switch to light mode"
                    : "Switch to dark mode"
            );
        }
    }

    function getSavedTheme() {
        const saved = localStorage.getItem(STORAGE_KEY);

        if (saved === "dark" || saved === "light") {
            return saved;
        }

        return window.matchMedia &&
            window.matchMedia("(prefers-color-scheme: dark)").matches
            ? "dark"
            : "light";
    }

    function createToggle() {
        if (document.querySelector(".theme-toggle")) {
            return;
        }

        const button = document.createElement("button");

        button.className = "theme-toggle";
        button.type = "button";

        button.addEventListener("click", function () {
            const current =
                document.documentElement.getAttribute("data-theme") || "light";

            const next = current === "dark" ? "light" : "dark";

            localStorage.setItem(STORAGE_KEY, next);
            applyTheme(next);
        });

        document.body.appendChild(button);

        applyTheme(
            document.documentElement.getAttribute("data-theme") ||
            getSavedTheme()
        );
    }

    const initialTheme = getSavedTheme();

    document.documentElement.setAttribute("data-theme", initialTheme);

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", createToggle);
    } else {
        createToggle();
    }
})();