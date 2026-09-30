/* ask.html: anonymous question box + published Q&A list.
 *
 * ---------------------------------------------------------------------------
 * 1) FORM_ENDPOINT: paste your Formspree form URL here, e.g.
 *        "https://formspree.io/f/abcdwxyz"
 *    While it is empty, the Send button stays disabled and the page shows
 *    "Question box opening soon". Setup: scripts/ASK_SETUP.md.
 *
 * 2) QA: to publish an answer, add one object to the QA array:
 *        {
 *            question: "The question text",
 *            answer: "Your answer.\n\nA blank line starts a new paragraph.",
 *            date: "2026-10-01"   // YYYY-MM-DD; list is sorted newest first
 *        },
 *    Text is shown as plain text (HTML is escaped); single line breaks are
 *    kept. The entry marked `template: true` is an example that only shows at
 *    ask.html?preview. Delete it or leave it; it never shows without ?preview.
 * ---------------------------------------------------------------------------
 */
var FORM_ENDPOINT = "https://formspree.io/f/mzezwagj";

var QA = [
    {
        template: true, // EXAMPLE ONLY: rendered only with ?preview
        question: "Example question: what got you into geophysics? (template entry)",
        answer: "Example answer, first paragraph. Replace this with a real one.\n\nSecond paragraph: a blank line in the answer starts a new paragraph,\nand a single line break is kept as a line break.",
        date: "2026-09-30"
    }
];

(function () {
    "use strict";

    var MAX_LENGTH = 1000;
    var preview = /[?&]preview(=|&|$)/.test(window.location.search);

    function escapeHtml(value) {
        return String(value == null ? "" : value)
            .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;").replace(/'/g, "&#39;");
    }

    function textToParagraphs(text) {
        return String(text == null ? "" : text)
            .replace(/\r\n?/g, "\n")
            .trim()
            .split(/\n\s*\n/)
            .map(function (para) {
                return "<p>" + escapeHtml(para.trim()).replace(/\n/g, "<br>") + "</p>";
            })
            .join("");
    }

    /* ---------- Published Q&A ---------- */
    function renderQA() {
        var list = document.getElementById("ask-list");
        var empty = document.getElementById("ask-empty");
        if (!list || !empty) return;

        var items = QA.filter(function (item) {
            return item && item.question && (preview || !item.template);
        }).sort(function (a, b) {
            return String(b.date || "").localeCompare(String(a.date || ""));
        });

        if (!items.length) return; // "No answered questions yet." stays visible

        list.innerHTML = items.map(function (item) {
            var date = /^\d{4}-\d{2}-\d{2}$/.test(item.date || "") ? item.date : "";
            return '<li class="ask-item">' +
                (item.template ? '<span class="ask-template-badge">Example entry – replace with a real Q&amp;A</span>' : "") +
                '<p class="ask-question">' + escapeHtml(item.question).replace(/\n/g, "<br>") + "</p>" +
                '<div class="ask-answer">' + textToParagraphs(item.answer) + "</div>" +
                (date ? '<time class="ask-date" datetime="' + date + '">Answered ' + date + "</time>" : "") +
                "</li>";
        }).join("");
        list.hidden = false;
        empty.hidden = true;
    }

    /* ---------- Question form ---------- */
    function setupForm() {
        var form = document.getElementById("ask-form");
        if (!form) return;
        var textarea = document.getElementById("ask-question");
        var button = document.getElementById("ask-submit");
        var count = document.getElementById("ask-count");
        var soon = document.getElementById("ask-soon");
        var status = document.getElementById("ask-status");
        var endpoint = String(FORM_ENDPOINT || "").trim();
        var sending = false;
        var honeypot = form.elements.namedItem("_gotcha");

        function showStatus(kind, message) {
            status.className = "ask-status is-" + kind;
            status.textContent = message;
            status.hidden = false;
        }

        function update() {
            var length = textarea.value.length;
            count.textContent = length + " / " + MAX_LENGTH;
            count.classList.toggle("is-near-limit", length >= MAX_LENGTH * 0.9);
            button.disabled = !endpoint || sending || !textarea.value.trim() || length > MAX_LENGTH;
        }

        if (!endpoint) {
            soon.hidden = false;
            button.title = "Question box opening soon";
        }

        textarea.addEventListener("input", function () {
            status.hidden = true;
            update();
        });

        form.addEventListener("submit", function (event) {
            event.preventDefault();
            var question = textarea.value.trim();
            if (!endpoint || sending || !question) return;
            if (honeypot && honeypot.value) return;
            if (question.length > MAX_LENGTH) {
                showStatus("error", "That's a bit long: please keep it under " + MAX_LENGTH + " characters.");
                return;
            }

            sending = true;
            textarea.readOnly = true;
            update();
            button.setAttribute("aria-busy", "true");
            var label = button.innerHTML;
            button.textContent = "Sending…";
            status.hidden = true;

            var data = new FormData(form);
            data.set("question", question);
            var controller = new AbortController();
            var timeout = window.setTimeout(function () { controller.abort(); }, 20000);

            fetch(endpoint, {
                method: "POST",
                body: data,
                headers: { Accept: "application/json" },
                credentials: "omit",
                signal: controller.signal
            }).then(function (response) {
                if (response.ok) return null;
                return response.json().catch(function () { return {}; }).then(function (body) {
                    var detail = body && body.errors && body.errors.length
                        ? body.errors.map(function (e) { return e.message; }).join(" ")
                        : "";
                    throw new Error(detail || ("HTTP " + response.status));
                });
            }).then(function () {
                textarea.value = "";
                showStatus("success", "Thanks! Your question was sent anonymously.");
            }).catch(function (error) {
                showStatus("error", error && error.name === "AbortError"
                    ? "The request timed out, so we couldn't confirm delivery. Your question is still here; please try again later."
                    : "Your question couldn't be sent. Your text has been kept; please try again in a moment.");
            }).then(function () {
                window.clearTimeout(timeout);
                sending = false;
                textarea.readOnly = false;
                button.removeAttribute("aria-busy");
                button.innerHTML = label;
                update();
            });
        });

        update();
    }

    function init() {
        renderQA();
        setupForm();
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", init);
    } else {
        init();
    }
})();
