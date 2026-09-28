/*
 * Client-side note search for notes.html.
 *
 * The index is built at runtime in the browser, so it stays in sync with the
 * Obsidian sync script without any changes to it:
 *   notes.html  -> subject pages (links in .note-card)
 *   subject pages -> note pages (links in .article-card)
 *   note pages  -> title, subject and the raw Markdown in #article-markdown
 * Pages are fetched lazily on first focus/typing and cached in sessionStorage.
 */
(function () {
    "use strict";

    const INDEX_VERSION = "1";
    const CACHE_PREFIX = "noteSearch:v" + INDEX_VERSION + ":";
    const MAX_RESULTS = 30;
    const SNIPPETS_PER_RESULT = 2;
    const SNIPPET_RADIUS = 60;
    const FETCH_CONCURRENCY = 6;

    const root = document.getElementById("note-search");
    const input = document.getElementById("note-search-input");
    const status = document.getElementById("note-search-status");
    const results = document.getElementById("note-search-results");
    if (!root || !input || !status || !results) {
        return;
    }

    root.hidden = false;

    let indexPromise = null;
    let debounceTimer = 0;
    let lastQuery = "";

    /* ---------- Helpers ---------- */

    const escapeHtml = (value) => String(value == null ? "" : value)
        .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;").replace(/'/g, "&#39;");

    const escapeRegExp = (value) => value.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");

    const collapse = (value) => String(value || "").replace(/\s+/g, " ").trim();

    function hashString(value) {
        let hash = 5381;
        for (let i = 0; i < value.length; i += 1) {
            hash = ((hash << 5) + hash + value.charCodeAt(i)) | 0;
        }
        return (hash >>> 0).toString(36);
    }

    // Mirrors normalizeHeadingId/slugify in scripts/markdown-article.js so that
    // result links can jump to the rendered heading anchors.
    function unescapeMarkdown(value) {
        return value.replace(/\\([\\`*{}\[\]()#+\-.!_>])/g, "$1");
    }

    function stripMarkdown(value) {
        return value
            .replace(/!\[[^\]]*\]\([^)]+\)/g, "")
            .replace(/\[([^\]]+)\]\([^)]+\)/g, "$1")
            .replace(/[`*_>#-]/g, "")
            .trim();
    }

    function headingId(value) {
        const resolved = unescapeMarkdown(value)
            .replace(/\bC\+\+/gi, "Cplusplus")
            .replace(/\bC#/gi, "Csharp");
        return stripMarkdown(resolved)
            .toLowerCase()
            .replace(/[^a-z0-9\u4e00-\u9fa5]+/g, "-")
            .replace(/^-+|-+$/g, "") || "section";
    }

    // Turns a Markdown line into readable plain text for snippets.
    function plainText(line) {
        return line
            .replace(/\$\$[\s\S]*?\$\$/g, " ⋯ ")
            .replace(/\\\[[\s\S]*?\\\]/g, " ⋯ ")
            .replace(/!\[\[[^\]]*\]\]/g, "")
            .replace(/!\[[^\]]*\]\([^)]*\)/g, "")
            .replace(/\[\[([^\]|]+)\|([^\]]+)\]\]/g, "$2")
            .replace(/\[\[([^\]]+)\]\]/g, "$1")
            .replace(/\[([^\]]+)\]\([^)]*\)/g, "$1")
            .replace(/<[^>]+>/g, " ")
            .replace(/^\s*>\s*\[![^\]]*\][+-]?\s*/, "")
            .replace(/^\s*(?:>\s*)+/, "")
            .replace(/^\s*(?:[-*+]|\d+[.)])\s+/, "")
            .replace(/\*\*|__|`/g, "")
            .replace(/(^|\s)[*_](\S)/g, "$1$2")
            .replace(/(\S)[*_](\s|$)/g, "$1$2")
            .replace(/^\s*\|/, "").replace(/\|\s*$/, "").replace(/\s*\|\s*/g, " · ");
    }

    // Splits a note's Markdown into sections keyed by heading anchor.
    function parseSections(markdown) {
        const lines = markdown.replace(/\r\n?/g, "\n").split("\n");
        const used = new Map();
        const sections = [{ id: "", heading: "", text: [] }];
        let inCode = false;
        let mathClose = null;
        let latexEnd = null;

        lines.forEach((line) => {
            const trimmed = line.trim();
            if (/^```/.test(trimmed)) {
                inCode = !inCode;
                return;
            }
            const current = sections[sections.length - 1];
            if (inCode) {
                current.text.push(line);
                return;
            }
            if (mathClose) {
                if (trimmed === mathClose) mathClose = null;
                return;
            }
            if (latexEnd) {
                if (trimmed === latexEnd) latexEnd = null;
                return;
            }
            if (trimmed === "$$" || trimmed === "\\[") {
                mathClose = trimmed === "$$" ? "$$" : "\\]";
                current.text.push("⋯");
                return;
            }
            const latex = trimmed.match(/^\\begin\{(figure|table)\}/);
            if (latex) {
                latexEnd = "\\end{" + latex[1] + "}";
                return;
            }
            const heading = trimmed.match(/^(#{1,4})\s+(.+)$/);
            if (heading) {
                const text = unescapeMarkdown(heading[2].trim());
                const base = headingId(text);
                const count = used.get(base) || 0;
                used.set(base, count + 1);
                sections.push({
                    id: count ? base + "-" + (count + 1) : base,
                    heading: collapse(plainText(text).replace(/[#]/g, "")),
                    text: []
                });
                return;
            }
            if (/^---+$/.test(trimmed)) return;
            const plain = collapse(plainText(line));
            if (plain) current.text.push(plain);
        });

        return sections
            .map((section) => ({
                id: section.id,
                heading: section.heading,
                text: collapse(section.text.join(" ").replace(/(?:\s*⋯\s*)+/g, " ⋯ "))
            }))
            .filter((section) => section.heading || section.text);
    }

    /* ---------- Index building ---------- */

    async function fetchDocument(url) {
        const response = await fetch(url, { credentials: "same-origin" });
        if (!response.ok) {
            throw new Error("HTTP " + response.status + " for " + url);
        }
        return new DOMParser().parseFromString(await response.text(), "text/html");
    }

    async function mapLimit(items, limit, worker) {
        const output = new Array(items.length);
        let next = 0;
        async function run() {
            while (next < items.length) {
                const index = next;
                next += 1;
                try {
                    output[index] = await worker(items[index], index);
                } catch (error) {
                    output[index] = null;
                }
            }
        }
        await Promise.all(Array.from({ length: Math.min(limit, items.length) }, run));
        return output;
    }

    function uniqueUrls(anchors, base) {
        const seen = new Set();
        const urls = [];
        anchors.forEach((anchor) => {
            const href = anchor.getAttribute("href");
            if (!href) return;
            const url = new URL(href, base);
            url.hash = "";
            if (url.origin !== window.location.origin || seen.has(url.href)) return;
            seen.add(url.href);
            urls.push(url.href);
        });
        return urls;
    }

    async function buildIndex() {
        const subjectCards = [...document.querySelectorAll(".note-grid a.note-card[href]")];
        const subjects = subjectCards.map((card) => ({
            url: new URL(card.getAttribute("href"), window.location.href).href,
            label: collapse((card.querySelector("h2") || card).textContent)
        }));

        const subjectDocs = await mapLimit(subjects, FETCH_CONCURRENCY, (subject) => fetchDocument(subject.url));
        const notes = [];
        const seen = new Set();
        subjectDocs.forEach((doc, index) => {
            if (!doc) return;
            uniqueUrls([...doc.querySelectorAll("a.article-card[href]")], subjects[index].url).forEach((url) => {
                if (seen.has(url)) return;
                seen.add(url);
                notes.push({ url, subject: subjects[index].label });
            });
        });

        const cacheKey = CACHE_PREFIX + hashString(notes.map((note) => note.url).join("|"));
        try {
            const cached = sessionStorage.getItem(cacheKey);
            if (cached) return JSON.parse(cached);
        } catch (error) {
            /* sessionStorage unavailable: fall through */
        }

        const entries = await mapLimit(notes, FETCH_CONCURRENCY, async (note) => {
            const doc = await fetchDocument(note.url);
            const source = doc.getElementById("article-markdown");
            const titleNode = doc.querySelector(".article-detail-header h1") || doc.querySelector("h1");
            const title = collapse(titleNode ? titleNode.textContent : doc.title.replace(/\s*\|\s*Yang Xu\s*$/, ""));
            const markdown = source ? source.textContent : collapse((doc.querySelector("main") || doc.body).textContent);
            const path = new URL(note.url).pathname;
            return {
                url: path + new URL(note.url).search,
                title,
                subject: note.subject,
                sections: parseSections(markdown)
            };
        });

        const index = entries.filter(Boolean);
        try {
            Object.keys(sessionStorage)
                .filter((key) => key.indexOf("noteSearch:") === 0 && key !== cacheKey)
                .forEach((key) => sessionStorage.removeItem(key));
            sessionStorage.setItem(cacheKey, JSON.stringify(index));
        } catch (error) {
            /* quota exceeded or storage disabled: keep the in-memory index only */
        }
        return index;
    }

    function ensureIndex() {
        if (!indexPromise) {
            indexPromise = buildIndex().catch((error) => {
                indexPromise = null;
                throw error;
            });
        }
        return indexPromise;
    }

    /* ---------- Searching ---------- */

    function parseTerms(query) {
        return [...new Set(query.toLowerCase().split(/\s+/).filter(Boolean))];
    }

    function highlight(text, terms) {
        if (!terms.length) return escapeHtml(text);
        const pattern = new RegExp("(" + terms.map(escapeRegExp).sort((a, b) => b.length - a.length).join("|") + ")", "gi");
        return text.split(pattern).map((part, i) => (i % 2 ? "<mark>" + escapeHtml(part) + "</mark>" : escapeHtml(part))).join("");
    }

    function makeSnippet(text, position, termLength) {
        let start = Math.max(0, position - SNIPPET_RADIUS);
        let end = Math.min(text.length, position + termLength + SNIPPET_RADIUS);
        // Snap to word boundaries (no-op for CJK text without spaces).
        if (start > 0) {
            const space = text.indexOf(" ", start);
            if (space !== -1 && space < position) start = space + 1;
        }
        if (end < text.length) {
            const space = text.lastIndexOf(" ", end);
            if (space > position + termLength) end = space;
        }
        return (start > 0 ? "… " : "") + text.slice(start, end).trim() + (end < text.length ? " …" : "");
    }

    function searchIndex(index, terms) {
        const matches = [];
        index.forEach((note) => {
            const titleLower = note.title.toLowerCase();
            const subjectLower = note.subject.toLowerCase();
            const sectionData = note.sections.map((section) => ({
                section,
                headingLower: section.heading.toLowerCase(),
                textLower: section.text.toLowerCase()
            }));
            const haystack = [titleLower, subjectLower]
                .concat(sectionData.map((s) => s.headingLower + " " + s.textLower))
                .join("\n");
            if (!terms.every((term) => haystack.includes(term))) return;

            let score = 0;
            terms.forEach((term) => {
                if (titleLower.includes(term)) score += 20;
                if (subjectLower.includes(term)) score += 4;
            });

            const scored = sectionData.map((data) => {
                let hits = 0;
                let sectionScore = 0;
                terms.forEach((term) => {
                    const inHeading = data.headingLower.includes(term);
                    const inText = data.textLower.includes(term);
                    if (inHeading || inText) hits += 1;
                    if (inHeading) sectionScore += 6;
                    if (inText) sectionScore += 1;
                });
                return { data, hits, sectionScore };
            }).filter((item) => item.hits > 0)
                .sort((a, b) => (b.hits - a.hits) || (b.sectionScore - a.sectionScore));

            scored.forEach((item) => { score += item.sectionScore; });

            const snippets = [];
            scored.slice(0, SNIPPETS_PER_RESULT).forEach((item) => {
                const { section, textLower } = item.data;
                let text = "";
                const term = terms.find((t) => textLower.includes(t));
                if (term) {
                    text = makeSnippet(section.text, textLower.indexOf(term), term.length);
                } else if (section.text) {
                    text = makeSnippet(section.text, 0, 0);
                }
                snippets.push({ id: section.id, heading: section.heading, text });
            });

            const target = snippets.find((s) => s.id);
            matches.push({ note, score, snippets, anchor: target ? target.id : "" });
        });
        return matches.sort((a, b) => (b.score - a.score) || a.note.title.localeCompare(b.note.title));
    }

    function render(matches, terms) {
        if (!matches.length) {
            results.innerHTML = "";
            results.hidden = true;
            status.textContent = "No results.";
            status.classList.add("is-empty");
            return;
        }
        status.classList.remove("is-empty");
        const total = matches.length;
        status.textContent = total === 1 ? "1 note found." : total + " notes found.";
        results.innerHTML = matches.slice(0, MAX_RESULTS).map((match) => {
            const href = match.note.url + (match.anchor ? "#" + encodeURIComponent(match.anchor) : "");
            const snippets = match.snippets.map((snippet) => {
                const heading = snippet.heading
                    ? '<span class="note-search-section">' + highlight(snippet.heading, terms) + "</span>"
                    : "";
                const body = snippet.text ? '<span class="note-search-text">' + highlight(snippet.text, terms) + "</span>" : "";
                return heading || body ? '<p class="note-search-snippet">' + heading + body + "</p>" : "";
            }).join("");
            return '<li><a class="note-search-result" href="' + escapeHtml(href) + '">'
                + '<span class="note-search-meta">' + escapeHtml(match.note.subject) + "</span>"
                + '<span class="note-search-title">' + highlight(match.note.title, terms) + "</span>"
                + snippets
                + "</a></li>";
        }).join("");
        results.hidden = false;
    }

    function clearResults() {
        results.innerHTML = "";
        results.hidden = true;
        status.textContent = "";
        status.classList.remove("is-empty");
        root.classList.remove("has-query");
    }

    async function runSearch() {
        const query = input.value.trim();
        lastQuery = query;
        if (!query) {
            clearResults();
            return;
        }
        root.classList.add("has-query");
        let index;
        try {
            if (!indexPromise) status.textContent = "Loading notes…";
            index = await ensureIndex();
        } catch (error) {
            status.textContent = "Search is unavailable right now.";
            return;
        }
        if (query !== lastQuery) return; // a newer query is in flight
        render(searchIndex(index, parseTerms(query)), parseTerms(query));
    }

    /* ---------- Events ---------- */

    input.addEventListener("focus", () => { ensureIndex().catch(() => {}); }, { once: true });

    input.addEventListener("input", () => {
        window.clearTimeout(debounceTimer);
        debounceTimer = window.setTimeout(runSearch, 180);
    });

    input.addEventListener("keydown", (event) => {
        if (event.key === "Escape") {
            if (input.value) {
                event.preventDefault();
                input.value = "";
                clearResults();
            } else {
                input.blur();
            }
        } else if (event.key === "Enter") {
            const first = results.querySelector("a");
            if (first && !results.hidden) {
                event.preventDefault();
                window.location.href = first.href;
            }
        }
    });

    root.addEventListener("submit", (event) => event.preventDefault());

    document.addEventListener("keydown", (event) => {
        if (event.key !== "/" || event.ctrlKey || event.metaKey || event.altKey) return;
        const target = event.target;
        const tag = target && target.tagName;
        if (tag === "INPUT" || tag === "TEXTAREA" || tag === "SELECT" || (target && target.isContentEditable)) return;
        event.preventDefault();
        input.focus();
        input.select();
    });
})();
