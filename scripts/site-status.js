/* Homepage "Site Status" panel.
 * Runtime is computed from SITE_START; counts and last-updated time come from
 * the public GitHub REST API (2 requests, cached in sessionStorage). If the API
 * is unavailable, the hardcoded FALLBACK values below are shown instead. */
(function () {
    "use strict";

    var REPO = "jasonxu-cell/jasonxu-cell.github.io";
    var BRANCH = "main";
    var API = "https://api.github.com/repos/" + REPO;
    // First commit / GitHub repo creation: 2026-08-13 21:27 (UTC+8).
    var SITE_START = new Date("2026-08-13T21:27:39+08:00");
    var CACHE_KEY = "siteStatus:v1";
    var CACHE_TTL = 30 * 60 * 1000; // 30 minutes
    var FALLBACK = {
        articles: 3,
        notes: 28,
        commits: 48,
        lastUpdated: "2026-09-30T12:00:00+08:00"
    };

    var panel = document.querySelector("[data-site-status]");
    if (!panel) return;

    function field(name) {
        return panel.querySelector('[data-status="' + name + '"]');
    }

    function setText(name, text) {
        var el = field(name);
        if (el) el.textContent = text;
    }

    function plural(n, word) {
        return n + " " + word + (n === 1 ? "" : "s");
    }

    function runtimeText(now) {
        var months = (now.getFullYear() - SITE_START.getFullYear()) * 12 +
            (now.getMonth() - SITE_START.getMonth());
        if (now.getDate() < SITE_START.getDate()) months -= 1;
        if (months < 1) {
            var days = Math.max(0, Math.floor((now - SITE_START) / 86400000));
            return plural(days, "day");
        }
        var years = Math.floor(months / 12);
        var rest = months % 12;
        var parts = [];
        if (years > 0) parts.push(plural(years, "year"));
        if (rest > 0) parts.push(plural(rest, "month"));
        return parts.join(" ");
    }

    function pad(n) {
        return (n < 10 ? "0" : "") + n;
    }

    function relativeText(date, now) {
        var diff = Math.max(0, now - date);
        var mins = Math.floor(diff / 60000);
        if (mins < 1) return "just now";
        if (mins < 60) return plural(mins, "min") + " ago";
        var hours = Math.floor(mins / 60);
        // Count days by local calendar date, so "yesterday" means yesterday.
        var dayStart = function (d) { return new Date(d.getFullYear(), d.getMonth(), d.getDate()); };
        var days = Math.round((dayStart(now) - dayStart(date)) / 86400000);
        if (days < 1) return plural(hours, "hour") + " ago";
        if (days < 30) return days === 1 ? "yesterday" : days + " days ago";
        var months = Math.floor(days / 30);
        if (months < 12) return plural(months, "month") + " ago";
        return plural(Math.floor(days / 365), "year") + " ago";
    }

    function render(data) {
        var now = new Date();
        setText("runtime", runtimeText(now));
        setText("articles", String(data.articles));
        setText("notes", String(data.notes));
        setText("commits", String(data.commits));

        var updated = new Date(data.lastUpdated);
        var el = field("updated");
        if (el && !isNaN(updated)) {
            el.setAttribute("datetime", updated.toISOString());
            el.setAttribute("title", updated.toLocaleString());
            el.textContent = updated.getFullYear() + "-" + pad(updated.getMonth() + 1) + "-" + pad(updated.getDate());
            setText("updated-relative", relativeText(updated, now));
        }
    }

    function readCache() {
        try {
            var raw = window.sessionStorage.getItem(CACHE_KEY);
            return raw ? JSON.parse(raw) : null;
        } catch (e) {
            return null;
        }
    }

    function writeCache(data) {
        try {
            data.savedAt = Date.now();
            window.sessionStorage.setItem(CACHE_KEY, JSON.stringify(data));
        } catch (e) { /* storage unavailable: ignore */ }
    }

    function getJSON(url) {
        return fetch(url, { headers: { Accept: "application/vnd.github+json" } }).then(function (res) {
            if (!res.ok) throw new Error("HTTP " + res.status);
            return res.json().then(function (body) {
                return { body: body, headers: res.headers };
            });
        });
    }

    function fetchCommits() {
        return getJSON(API + "/commits?per_page=1&sha=" + BRANCH).then(function (r) {
            var latest = r.body && r.body[0];
            if (!latest) throw new Error("no commits");
            var count = r.body.length;
            var link = r.headers.get("Link") || "";
            var m = link.match(/[?&]page=(\d+)[^>]*>;\s*rel="last"/);
            if (m) count = parseInt(m[1], 10);
            return { commits: count, lastUpdated: latest.commit.committer.date };
        });
    }

    function fetchCounts() {
        return getJSON(API + "/git/trees/" + BRANCH + "?recursive=1").then(function (r) {
            var tree = (r.body && r.body.tree) || [];
            var notes = 0;
            var articles = 0;
            tree.forEach(function (item) {
                if (item.type !== "blob") return;
                // Note pages live at notes/<subject>/<note>.html;
                // subject index pages (notes/<subject>.html) are not counted.
                if (/^notes\/[^\/]+\/[^\/]+\.html$/.test(item.path)) notes += 1;
                else if (/^articles\/[^\/]+\.html$/.test(item.path)) articles += 1;
            });
            if (r.body.truncated || !notes || !articles) throw new Error("incomplete tree");
            return { notes: notes, articles: articles };
        });
    }

    var cached = readCache();
    var current = cached || FALLBACK;
    render(current);
    // Keep the runtime / "x hours ago" text fresh on long-open tabs.
    window.setInterval(function () { render(current); }, 60 * 1000);

    if (cached && Date.now() - cached.savedAt < CACHE_TTL) return;
    if (!window.fetch || !window.Promise) return;

    Promise.all([
        fetchCommits().catch(function () { return null; }),
        fetchCounts().catch(function () { return null; })
    ]).then(function (results) {
        if (!results[0] && !results[1]) return;
        var data = {
            articles: current.articles,
            notes: current.notes,
            commits: current.commits,
            lastUpdated: current.lastUpdated
        };
        if (results[0]) {
            data.commits = results[0].commits;
            data.lastUpdated = results[0].lastUpdated;
        }
        if (results[1]) {
            data.notes = results[1].notes;
            data.articles = results[1].articles;
        }
        current = data;
        render(data);
        if (results[0] && results[1]) writeCache(data);
    });
})();
