import markdownItKatex from '@traptitech/markdown-it-katex';
import DOMPurify from 'dompurify';
import hljs from 'highlight.js';
import 'highlight.js/styles/github-dark.min.css';
import 'katex/dist/katex.min.css';
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

// Add KaTeX plugin for LaTeX formula rendering
md.use(markdownItKatex, {
  throwOnError: false, // Don't throw on invalid LaTeX
  errorColor: '#cc0000', // Color for invalid LaTeX
});

export const useMarkdownRenderer = (content: string) => {
  return useMemo(() => {
    const rendered = md.render(content);

    // Configure DOMPurify to allow KaTeX elements and attributes
    const sanitized = DOMPurify.sanitize(rendered, {
      ADD_TAGS: [
        'span',
        'math',
        'semantics',
        'mrow',
        'mi',
        'mo',
        'mn',
        'msubsup',
        'msub',
        'msup',
        'mfrac',
        'mroot',
        'msqrt',
        'mtext',
        'mspace',
        'mtable',
        'mtr',
        'mtd',
        'mlabeledtr',
        'munder',
        'mover',
        'munderover',
        'annotation',
        'annotation-xml',
      ],
      ADD_ATTR: [
        'class',
        'data-*',
        'xmlns',
        'style',
        'aria-hidden',
        'mathvariant',
        'mathsize',
        'mathcolor',
        'mathbackground',
        'displaystyle',
        'scriptlevel',
        'dir',
        'lspace',
        'rspace',
        'stretchy',
        'symmetric',
        'maxsize',
        'minsize',
        'fence',
        'separator',
        'accent',
        'accentunder',
        'linebreak',
        'linebreakmultchar',
        'indentalign',
        'indentshift',
        'indenttarget',
        'form',
        'position',
        'frame',
        'rowspacing',
        'columnspacing',
        'rowlines',
        'columnlines',
        'framespacing',
        'equalrows',
        'equalcolumns',
        'rowalign',
        'columnalign',
        'groupalign',
        'alignmentscope',
        'columnwidth',
        'rowspan',
        'columnspan',
        'side',
      ],
    });

    return sanitized;
  }, [content]);
};
