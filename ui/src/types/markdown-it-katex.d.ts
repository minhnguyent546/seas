declare module '@traptitech/markdown-it-katex' {
  interface KatexOptions {
    throwOnError?: boolean;
    errorColor?: string;
    macros?: Record<string, string>;
    fleqn?: boolean;
    leqno?: boolean;
    displayMode?: boolean;
    strict?: boolean | 'warn' | 'ignore';
    trust?: boolean;
    maxSize?: number;
    maxExpand?: number;
    globalGroup?: boolean;
  }

  const markdownItKatex: MarkdownIt.PluginWithOptions<KatexOptions>;
  export = markdownItKatex;
}
