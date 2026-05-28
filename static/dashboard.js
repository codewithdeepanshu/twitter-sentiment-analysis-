/* ==========================================================================
   STATISTICAL DASHBOARD CONTROLLER (dashboard.js)
   ========================================================================== */

document.addEventListener("DOMContentLoaded", () => {
    // DOM Elements
    const dashboardLoader = document.getElementById("dashboard-loader");
    const loaderMsg = document.getElementById("loader-msg");
    const dashboardContent = document.getElementById("dashboard-content");
    const headline = document.getElementById("dashboard-headline");
    const subHeadline = document.getElementById("dashboard-sub-headline");
    const dataSourceBadge = document.getElementById("data-source-badge");

    // KPI Elements
    const kpiTotal = document.getElementById("kpi-total");
    const kpiAvgScore = document.getElementById("kpi-avg-score");
    const kpiAvgLbl = document.getElementById("kpi-avg-lbl");
    const kpiPositivity = document.getElementById("kpi-positivity");

    // Sentiment Card Elements
    const dominantEmoji = document.getElementById("dominant-emoji");
    const dominantLabel = document.getElementById("dominant-label");
    const dominantConfidence = document.getElementById("dominant-confidence");
    const dominantCard = document.getElementById("dominant-sentiment-card");

    // Tweet Feed Elements
    const tweetListTarget = document.getElementById("tweet-list-target");
    const analyzedFeedContainer = document.getElementById("analyzed-feed-container");

    // Chart Handles
    let doughnutChartInstance = null;
    let lineChartInstance = null;

    // ----------------------------------------------------
    // Initialization & Query Parsing
    // ----------------------------------------------------

    const params = new URLSearchParams(window.location.search);
    const type = params.get("type");

    if (!type) {
        // Redirection fallback if loaded directly without parameters
        window.location.href = "/";
        return;
    }

    if (type === "text") {
        loadManualTextData();
    } else if (type === "user") {
        const username = params.get("username");
        const count = params.get("count") || 5;
        const mock = params.get("mock") !== "false"; // Default true
        loadXUserData(username, count, mock);
    } else {
        window.location.href = "/";
    }

    // ----------------------------------------------------
    // Load Manual Single Text Data
    // ----------------------------------------------------
    function loadManualTextData() {
        showLoader(true);
        
        try {
            const cachedData = sessionStorage.getItem("manual_result");
            if (!cachedData) {
                throw new Error("No analysis result found. Please go back and analyze a post first.");
            }

            const data = JSON.parse(cachedData);
            
            // Populate UI Elements
            headline.textContent = "Custom Text Analysis";
            subHeadline.textContent = `Analyzed: "${truncateText(data.text, 50)}"`;
            dataSourceBadge.textContent = "Direct Text Input";

            // Populate KPIs
            kpiTotal.textContent = "1";
            
            // Map sentiment to a numerical score
            let score = 0.00;
            let scoreLabel = "Neutral";
            if (data.sentiment === "Positive") {
                score = 1.00;
                scoreLabel = "Highly Positive";
            } else if (data.sentiment === "Negative") {
                score = -1.00;
                scoreLabel = "Highly Negative";
            }
            
            kpiAvgScore.textContent = score > 0 ? `+${score.toFixed(2)}` : score.toFixed(2);
            kpiAvgScore.className = `kpi-val ${getSentimentColorClass(data.sentiment)}`;
            kpiAvgLbl.textContent = `Net Sentiment (${scoreLabel})`;
            
            const posRate = data.sentiment === "Positive" ? 100 : 0;
            kpiPositivity.textContent = `${posRate}%`;
            kpiPositivity.className = `kpi-val ${posRate > 0 ? 'color-pos' : 'color-neg'}`;

            // Populate Dominant Card
            dominantEmoji.textContent = data.emoji;
            dominantLabel.textContent = data.sentiment;
            dominantConfidence.textContent = `Confidence: ${data.confidence}%`;
            resetSentimentCardTheme(data.sentiment);

            // Setup single tweet list card representation
            tweetListTarget.innerHTML = `
                <div class="tweet-card card-${data.sentiment.toLowerCase()}">
                    <div class="tweet-card-header">
                        <span class="tweet-badge">${data.emoji} ${data.sentiment}</span>
                        <span class="tweet-date">Now</span>
                    </div>
                    <div class="tweet-text">${escapeHTML(data.text)}</div>
                </div>
            `;
            analyzedFeedContainer.classList.remove("hidden");

            // Render distribution doughnut (100% of analyzed sentiment)
            const distribution = {
                positive: data.sentiment === "Positive" ? 100 : 0,
                neutral: data.sentiment === "Neutral" ? 100 : 0,
                negative: data.sentiment === "Negative" ? 100 : 0
            };
            
            renderDoughnutChart(distribution);

            // Hide progression line chart card as timeline is not applicable for a single text input
            document.getElementById("timeline-chart-card").style.display = "none";
            // Expand the distribution card to take full width
            document.querySelector(".charts-grid").style.gridTemplateColumns = "1fr";

            showLoader(false);
            showContent(true);
        } catch (error) {
            alert(error.message);
            window.location.href = "/";
        }
    }

    // ----------------------------------------------------
    // Load X User Feed Data (Fetch from API)
    // ----------------------------------------------------
    async function loadXUserData(username, count, useMock) {
        loaderMsg.textContent = `Querying @${username}'s posts from X and evaluating sentiments...`;
        showLoader(true);

        try {
            const response = await fetch("/api/analyze-user", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    username: username,
                    count: parseInt(count),
                    mock: useMock
                })
            });

            if (!response.ok) {
                const errData = await response.json().catch(() => ({ error: "Server analysis failed" }));
                throw new Error(errData.error || "Failed to download feed");
            }

            const data = await response.json();
            
            // Populate UI Layout titles
            headline.textContent = `@${data.username} Feed Insights`;
            subHeadline.textContent = `Analyzing ${data.count} recent posts from Twitter/X profile`;
            dataSourceBadge.textContent = data.is_mock ? "Mock Demo Mode" : "Live Twitter API";

            // Compute metrics
            const total = data.summary.total;
            const positivity = data.summary.positive_percentage;
            
            // Calculate Net Sentiment Index: (Pos - Neg) / Total
            const netScore = total > 0 ? (data.summary.positive - data.summary.negative) / total : 0.00;
            let scoreCategory = "Neutral";
            let scoreColor = "color-neu";
            if (netScore > 0.15) {
                scoreCategory = netScore > 0.5 ? "Very Positive" : "Leaning Positive";
                scoreColor = "color-pos";
            } else if (netScore < -0.15) {
                scoreCategory = netScore < -0.5 ? "Very Negative" : "Leaning Negative";
                scoreColor = "color-neg";
            }

            // Fill KPIs
            kpiTotal.textContent = total;
            kpiAvgScore.textContent = netScore > 0 ? `+${netScore.toFixed(2)}` : netScore.toFixed(2);
            kpiAvgScore.className = `kpi-val ${scoreColor}`;
            kpiAvgLbl.textContent = `Net Sentiment Index (${scoreCategory})`;

            kpiPositivity.textContent = `${positivity}%`;
            kpiPositivity.className = `kpi-val ${positivity > 50 ? 'color-pos' : positivity < 30 ? 'color-neg' : 'color-neu'}`;

            // Calculate overall dominant sentiment
            let dominant = "Neutral";
            let maxCount = data.summary.neutral;
            let emoji = "😐";

            if (data.summary.positive > maxCount) {
                dominant = "Positive";
                maxCount = data.summary.positive;
                emoji = "😊";
            }
            if (data.summary.negative > maxCount) {
                dominant = "Negative";
                maxCount = data.summary.negative;
                emoji = "😡";
            }
            // Check for equal counts (tie)
            if (data.summary.positive === data.summary.negative && data.summary.positive > 0 && dominant !== "Neutral") {
                dominant = "Mixed";
                emoji = "🤔";
            }

            dominantEmoji.textContent = emoji;
            dominantLabel.textContent = dominant.toUpperCase();
            dominantConfidence.textContent = `${maxCount} of ${total} posts classified`;
            resetSentimentCardTheme(dominant);

            // Render Charts
            renderDoughnutChart(data.summary);
            renderLineProgressionChart(data.tweets);

            // Render Tweet Feed
            tweetListTarget.innerHTML = "";
            data.tweets.forEach(tweet => {
                const card = document.createElement("div");
                card.className = `tweet-card card-${tweet.sentiment.toLowerCase()}`;
                
                const dateStr = formatTweetDate(tweet.created_at);
                
                card.innerHTML = `
                    <div class="tweet-card-header">
                        <span class="tweet-badge">${tweet.emoji} ${tweet.sentiment}</span>
                        <span class="tweet-date">${dateStr}</span>
                    </div>
                    <div class="tweet-text">${escapeHTML(tweet.text)}</div>
                `;
                tweetListTarget.appendChild(card);
            });
            analyzedFeedContainer.classList.remove("hidden");

            showLoader(false);
            showContent(true);
        } catch (error) {
            alert(`Error: ${error.message}`);
            window.location.href = "/";
        }
    }

    // ----------------------------------------------------
    // Chart.js Rendering Logic
    // ----------------------------------------------------

    // Chart.js Doughnut Chart
    function renderDoughnutChart(summary) {
        const ctx = document.getElementById("doughnutChart").getContext("2d");
        
        const dataValues = [summary.positive, summary.neutral, summary.negative];
        
        if (doughnutChartInstance) {
            doughnutChartInstance.destroy();
        }

        doughnutChartInstance = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: ['Positive', 'Neutral', 'Negative'],
                datasets: [{
                    data: dataValues,
                    backgroundColor: [
                        'rgba(16, 185, 129, 0.75)', // Emerald
                        'rgba(245, 158, 11, 0.75)',  // Amber
                        'rgba(239, 68, 68, 0.75)'   // Rose
                    ],
                    borderColor: [
                        '#10b981',
                        '#f59e0b',
                        '#ef4444'
                    ],
                    borderWidth: 1.5,
                    hoverOffset: 6
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false // We use our own indicators/overall display
                    },
                    tooltip: {
                        backgroundColor: '#1f2937',
                        titleFont: { family: 'Poppins', weight: 'bold' },
                        bodyFont: { family: 'Poppins' },
                        borderColor: 'rgba(255,255,255,0.08)',
                        borderWidth: 1,
                        callbacks: {
                            label: function(context) {
                                const total = context.dataset.data.reduce((a, b) => a + b, 0);
                                const val = context.raw;
                                const pct = total > 0 ? ((val / total) * 100).toFixed(1) : 0;
                                return ` ${context.label}: ${val} (${pct}%)`;
                            }
                        }
                    }
                },
                cutout: '72%'
            }
        });
    }

    // Chart.js Line Chart representing Timeline Progression
    function renderLineProgressionChart(tweets) {
        const ctx = document.getElementById("lineChart").getContext("2d");
        
        // Reverse array for line progression so it is shown chronologically oldest -> newest (left -> right)
        const sortedTweets = [...tweets].reverse();

        // X-axis labels: Post indices or times
        const labels = sortedTweets.map((_, i) => `Post ${i + 1}`);

        // Y-axis values: Map Positive to +1, Neutral to 0, Negative to -1
        const dataValues = sortedTweets.map(tweet => {
            if (tweet.sentiment === "Positive") return 1;
            if (tweet.sentiment === "Negative") return -1;
            return 0;
        });

        // Dynamic styling for points: color points according to sentiment
        const pointBackgroundColors = sortedTweets.map(tweet => {
            if (tweet.sentiment === "Positive") return '#10b981';
            if (tweet.sentiment === "Negative") return '#ef4444';
            return '#f59e0b';
        });

        if (lineChartInstance) {
            lineChartInstance.destroy();
        }

        lineChartInstance = new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Sentiment Trajectory',
                    data: dataValues,
                    borderColor: 'rgba(99, 102, 241, 0.6)', // Indigo line
                    borderWidth: 3,
                    fill: false,
                    tension: 0.35,
                    pointBackgroundColor: pointBackgroundColors,
                    pointBorderColor: 'rgba(3, 7, 18, 0.8)',
                    pointBorderWidth: 2,
                    pointRadius: 6,
                    pointHoverRadius: 8
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        backgroundColor: '#1f2937',
                        titleFont: { family: 'Poppins', weight: 'bold' },
                        bodyFont: { family: 'Poppins' },
                        borderColor: 'rgba(255,255,255,0.08)',
                        borderWidth: 1,
                        callbacks: {
                            label: function(context) {
                                const idx = context.dataIndex;
                                const originalTweet = sortedTweets[idx];
                                return ` Sentiment: ${originalTweet.sentiment} | "${truncateText(originalTweet.text, 35)}"`;
                            }
                        }
                    }
                },
                scales: {
                    y: {
                        min: -1.2,
                        max: 1.2,
                        ticks: {
                            stepSize: 1,
                            callback: function(value) {
                                if (value === 1) return 'Positive 😊';
                                if (value === 0) return 'Neutral 😐';
                                if (value === -1) return 'Negative 😡';
                                return '';
                            },
                            color: '#4b5563',
                            font: { family: 'Poppins', size: 10 }
                        },
                        grid: {
                            color: 'rgba(0, 0, 0, 0.06)',
                            drawBorder: false
                        }
                    },
                    x: {
                        ticks: {
                            color: '#4b5563',
                            font: { family: 'Poppins', size: 10 }
                        },
                        grid: {
                            display: false
                        }
                    }
                }
            }
        });
    }

    // ----------------------------------------------------
    // Small Helper Utilities
    // ----------------------------------------------------

    function showLoader(visible) {
        if (visible) {
            dashboardLoader.classList.remove("hidden");
        } else {
            dashboardLoader.classList.add("hidden");
        }
    }

    function showContent(visible) {
        if (visible) {
            dashboardContent.classList.remove("hidden");
        } else {
            dashboardContent.classList.add("hidden");
        }
    }

    function truncateText(str, n) {
        return str.length > n ? str.substr(0, n - 1) + "..." : str;
    }

    function getSentimentColorClass(sentiment) {
        if (sentiment === "Positive") return "color-pos";
        if (sentiment === "Negative") return "color-neg";
        return "color-neu";
    }

    function resetSentimentCardTheme(sentiment) {
        dominantCard.classList.remove("card-pos", "card-neu", "card-neg");
        dominantCard.style.border = "none";
        dominantCard.style.borderLeft = "";
        
        if (sentiment === "Positive") {
            dominantCard.style.borderLeft = "5px solid var(--pos-color)";
        } else if (sentiment === "Negative") {
            dominantCard.style.borderLeft = "5px solid var(--neg-color)";
        } else if (sentiment === "Neutral") {
            dominantCard.style.borderLeft = "5px solid var(--neu-color)";
        } else {
            dominantCard.style.borderLeft = "5px solid var(--secondary)";
        }
    }

    function formatTweetDate(isoString) {
        try {
            const date = new Date(isoString);
            return date.toLocaleDateString("en-US", {
                month: "short",
                day: "numeric",
                hour: "2-digit",
                minute: "2-digit"
            });
        } catch (e) {
            return "Just now";
        }
    }

    function escapeHTML(str) {
        return str
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    }
});
