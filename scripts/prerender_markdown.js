#!/usr/bin/env node
/*
 * Pre-render the Markdown stored in <script id="article-markdown"> into the
 * page's <article id="markdown-body"> at build time.
 *
 * Search engines and visitors without JavaScript then get the full article
 * HTML. The browser script (markdown-article.js) detects
 * data-prerendered="true" and only adds the interactive parts (table of
 * contents, copy/collapse buttons, MathJax, highlight.js).
 *
 * The Markdown source block is kept as the single source of truth, so this
 * step is idempotent: running it again simply re-renders from the source.
 *
 * Usage:
 *   node scripts/prerender_markdown.js page1.html page2.html   # rewrite files in place
 *   node scripts/prerender_markdown.js --stdin-json < pages.json > out.json
 *     pages.json = ["<html>...", "<html>..."]  ->  out.json = ["<html>...", ...]
 */
"use strict";

const fs = require("fs");
const path = require("path");
const { createRenderer } = require("./markdown-article.js");

const SOURCE_PATTERN = /<script type="text\/plain" id="article-markdown">([\s\S]*?)<\/script>/;
const BODY_PATTERN = /<article\b[^>]*\bid="markdown-body"[^>]*>[\s\S]*?<\/article>/;
const HEADINGS_PATTERN = /\s*<script type="application\/json" id="article-headings">[\s\S]*?<\/script>/g;

function prerender(page) {
    const source = page.match(SOURCE_PATTERN);
    const body = page.match(BODY_PATTERN);

    if (!source || !body) {
        return page;
    }

    // A fresh renderer per page so heading ids are numbered per document,
    // exactly like the browser does.
    const renderer = createRenderer();
    const result = renderer.renderMarkdown(renderer.normalizeMarkdown(source[1]));
    const headingsJson = JSON.stringify(result.headings).replace(/</g, "\\u003c");

    const article = [
        '<article class="markdown-body" id="markdown-body" data-prerendered="true">',
        // Not re-indented: <pre> blocks and display math are whitespace-sensitive.
        result.html,
        "            </article>",
        `            <script type="application/json" id="article-headings">${headingsJson}</script>`
    ].join("\n");

    let output = page.replace(HEADINGS_PATTERN, "");
    output = output.replace(BODY_PATTERN, () => article);
    return output;
}

function main(argv) {
    if (argv[0] === "--stdin-json") {
        const pages = JSON.parse(fs.readFileSync(0, "utf8"));
        process.stdout.write(JSON.stringify(pages.map(prerender)));
        return 0;
    }

    let changed = 0;
    argv.forEach((file) => {
        const resolved = path.resolve(file);
        const original = fs.readFileSync(resolved, "utf8");
        const updated = prerender(original);
        if (updated !== original) {
            fs.writeFileSync(resolved, updated, "utf8");
            changed += 1;
        }
    });
    process.stdout.write(`Pre-rendered ${changed} of ${argv.length} pages\n`);
    return 0;
}

if (require.main === module) {
    process.exitCode = main(process.argv.slice(2));
}

module.exports = { prerender };
