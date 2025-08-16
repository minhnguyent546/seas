import { useEffect } from 'react';
import { useLanguage } from './useLanguage';

/**
 * Hook for managing page titles with automatic translation
 * @param titleKey Translation key for the page title
 * @param fallbackTitle Fallback title if translation key is not found
 */
export function usePageTitle(titleKey?: string, fallbackTitle?: string) {
  const { t } = useLanguage();

  useEffect(() => {
    if (titleKey) {
      const translatedTitle = t(titleKey);
      document.title = `${translatedTitle} | SEAS`;
    } else if (fallbackTitle) {
      document.title = `${fallbackTitle} | SEAS`;
    } else {
      document.title = 'SEAS';
    }

    return () => {
      // Reset to default title when component unmounts
      document.title = 'SEAS';
    };
  }, [titleKey, fallbackTitle, t]);
}

/**
 * Hook for setting custom page titles without translation
 * @param title Custom title string
 */
export function useCustomPageTitle(title: string) {
  useEffect(() => {
    document.title = `${title} | SEAS`;

    return () => {
      document.title = 'SEAS';
    };
  }, [title]);
}

/**
 * Hook for managing page meta tags with translation support
 * @param metaConfig Configuration for meta tags
 */
export function usePageMeta(metaConfig: {
  titleKey?: string;
  descriptionKey?: string;
  fallbackTitle?: string;
  fallbackDescription?: string;
}) {
  const { t } = useLanguage();

  useEffect(() => {
    const { titleKey, descriptionKey, fallbackTitle, fallbackDescription } =
      metaConfig;

    // Update page title
    if (titleKey) {
      const translatedTitle = t(titleKey);
      document.title = `${translatedTitle} | SEAS`;
    } else if (fallbackTitle) {
      document.title = `${fallbackTitle} | SEAS`;
    }

    // Update meta description
    let metaDescription = document.querySelector(
      'meta[name="description"]',
    ) as HTMLMetaElement;
    if (!metaDescription) {
      metaDescription = document.createElement('meta');
      metaDescription.name = 'description';
      document.head.appendChild(metaDescription);
    }

    if (descriptionKey) {
      const translatedDescription = t(descriptionKey);
      metaDescription.content = translatedDescription;
    } else if (fallbackDescription) {
      metaDescription.content = fallbackDescription;
    }

    // Update Open Graph title
    let ogTitle = document.querySelector(
      'meta[property="og:title"]',
    ) as HTMLMetaElement;
    if (!ogTitle) {
      ogTitle = document.createElement('meta');
      ogTitle.setAttribute('property', 'og:title');
      document.head.appendChild(ogTitle);
    }

    if (titleKey) {
      ogTitle.content = t(titleKey);
    } else if (fallbackTitle) {
      ogTitle.content = fallbackTitle;
    }

    // Update Open Graph description
    let ogDescription = document.querySelector(
      'meta[property="og:description"]',
    ) as HTMLMetaElement;
    if (!ogDescription) {
      ogDescription = document.createElement('meta');
      ogDescription.setAttribute('property', 'og:description');
      document.head.appendChild(ogDescription);
    }

    if (descriptionKey) {
      ogDescription.content = t(descriptionKey);
    } else if (fallbackDescription) {
      ogDescription.content = fallbackDescription;
    }

    return () => {
      // Reset to defaults
      document.title = 'SEAS';
      if (metaDescription) {
        metaDescription.content = 'SEAS - Smart Enrollment Advisory System';
      }
      if (ogTitle) {
        ogTitle.content = 'SEAS';
      }
      if (ogDescription) {
        ogDescription.content = 'SEAS - Smart Enrollment Advisory System';
      }
    };
  }, [t, metaConfig]);
}
