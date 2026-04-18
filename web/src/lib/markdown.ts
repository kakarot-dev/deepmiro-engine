/** Markdown renderer for report content. */

import MarkdownIt from "markdown-it";
import DOMPurify from "dompurify";

const md = new MarkdownIt({
  html: false,
  linkify: true,
  breaks: true,
  typographer: true,
});

export function renderMarkdown(source: string): string {
  if (!source) return "";
  const rendered = md.render(source);
  return DOMPurify.sanitize(rendered, {
    // Allow these tags; strip everything else (incl. <script>, <style>, inline event handlers).
    ALLOWED_TAGS: [
      "h1", "h2", "h3", "h4", "h5", "h6",
      "p", "br", "hr",
      "strong", "em", "b", "i", "u", "s", "del", "mark",
      "ul", "ol", "li",
      "blockquote",
      "code", "pre",
      "a",
      "table", "thead", "tbody", "tr", "th", "td",
      "img",
    ],
    ALLOWED_ATTR: ["href", "title", "src", "alt", "target", "rel", "class"],
  });
}
