import DOMPurify from 'dompurify';
import hljs from 'highlight.js';
import 'highlight.js/styles/github-dark.min.css';
import MarkdownIt from 'markdown-it';
import { useMemo } from 'react';

const md: MarkdownIt = new MarkdownIt({
  html: true, // Enable HTML tags in source
  xhtmlOut: false, // Use HTML5 output
  breaks: true, // Convert '\n' in paragraphs into <br>
  linkify: true, // Auto-convert URL-like text to links
  typographer: true, // Enable quotes beautification and other typography
  highlight: function (str: string, lang: string): string {
    if (lang && hljs.getLanguage(lang)) {
      try {
        return hljs.highlight(str, {
          language: lang,
          ignoreIllegals: true,
        }).value;
      } catch (__) {}
    }
    return md.utils.escapeHtml(str);
  },
});

export const useMarkdownRenderer = (content: string) => {
  return useMemo(() => {
    const rendered = md.render(content);
    const sanitized = DOMPurify.sanitize(rendered);
    return sanitized;
  }, [content]);
};
