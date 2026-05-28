/* ==========================================================================
   FORM CONTROLLER & REDIRECTION LOGIC (script.js)
   ========================================================================== */

document.addEventListener("DOMContentLoaded", () => {
    // DOM Elements
    const userForm = document.getElementById("user-form");
    const textForm = document.getElementById("text-form");
    const usernameInput = document.getElementById("username");
    const manualTextarea = document.getElementById("manual-text");
    const charCounter = document.getElementById("char-counter");
    const tweetCountSlider = document.getElementById("tweet-count");
    const sliderValBadge = document.getElementById("slider-val");
    const mockToggle = document.getElementById("mock-toggle");

    // Slider change handler
    tweetCountSlider.addEventListener("input", (e) => {
        sliderValBadge.textContent = e.target.value;
    });

    // Character counter for textarea
    manualTextarea.addEventListener("input", () => {
        const length = manualTextarea.value.length;
        charCounter.textContent = `${length} / 280`;
        
        if (length > 280) {
            charCounter.style.color = "var(--neg-color)";
            charCounter.style.fontWeight = "bold";
        } else {
            charCounter.style.color = "var(--text-muted)";
            charCounter.style.fontWeight = "normal";
        }
    });

    // ----------------------------------------------------
    // Form Submission Handlers (Page Redirection)
    // ----------------------------------------------------

    // Manual Text Submission
    textForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        const textValue = manualTextarea.value.trim();
        
        if (!textValue) return;

        const btn = document.getElementById("btn-analyze-text");
        const originalHTML = btn.innerHTML;
        btn.disabled = true;
        btn.innerHTML = '<i class="fa-solid fa-circle-notch fa-spin"></i> Analyzing...';

        try {
            // Call API directly from home page, cache result, and redirect
            const response = await fetch('/api/analyze-text', {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({ text: textValue })
            });

            if (!response.ok) {
                const errData = await response.ok ? {} : await response.json().catch(() => ({}));
                throw new Error(errData.error || "Server response failed");
            }

            const data = await response.json();
            
            // Cache in session storage for the dashboard page to consume
            sessionStorage.setItem("manual_result", JSON.stringify(data));
            
            // Redirect to dashboard page with parameter type=text
            window.location.href = "/dashboard?type=text";
        } catch (error) {
            console.error("Text analysis redirect error:", error);
            alert(`Error running analysis: ${error.message}`);
            btn.disabled = false;
            btn.innerHTML = originalHTML;
        }
    });

    // User Feed Submission
    userForm.addEventListener("submit", (e) => {
        e.preventDefault();
        const username = usernameInput.value.trim().replace("@", "");
        const count = tweetCountSlider.value;
        const useMock = mockToggle.checked;

        if (!username) return;

        // Redirect to dashboard.html with parameters
        window.location.href = `/dashboard?type=user&username=${encodeURIComponent(username)}&count=${count}&mock=${useMock}`;
    });
});
