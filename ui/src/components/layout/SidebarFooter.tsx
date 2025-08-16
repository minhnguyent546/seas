import { useLanguage } from '@/hooks/useLanguage';
import { IconBug, IconHome2, IconSchool } from '@tabler/icons-react';
import React from 'react';

interface SidebarFooterProps {
  isCollapsed: boolean;
  reportIssueUrl?: string;
}

export const SidebarFooter: React.FC<SidebarFooterProps> = ({
  isCollapsed,
  reportIssueUrl,
}) => {
  const { t } = useLanguage();

  return (
    <div className="border-t border-gray-200 p-2 space-y-1">
      {/* CTU Homepage Link */}
      {!isCollapsed ? (
        <a
          href="https://www.ctu.edu.vn/"
          target="_blank"
          rel="noopener noreferrer"
          className="flex items-center gap-2 rounded-lg px-2 py-1 cursor-pointer"
          title={t('sidebar.ctuHomepage')}
        >
          <IconHome2 size={16} className="text-primary" />
          <span className="text-xs text-primary">
            {t('sidebar.ctuHomepage')}
          </span>
        </a>
      ) : (
        <a
          href="https://www.ctu.edu.vn/"
          target="_blank"
          rel="noopener noreferrer"
          className="flex items-center justify-center p-2 cursor-pointer"
          title={t('sidebar.ctuHomepage')}
        >
          <IconHome2 size={16} className="text-primary" />
        </a>
      )}

      {/* CTU Admissions Link */}
      {!isCollapsed ? (
        <a
          href="https://tuyensinh.ctu.edu.vn/"
          target="_blank"
          rel="noopener noreferrer"
          className="flex items-center gap-2 rounded-lg px-2 py-1 cursor-pointer"
          title={t('sidebar.ctuAdmissions')}
        >
          <IconSchool size={16} className="text-primary" />
          <span className="text-xs text-primary">
            {t('sidebar.ctuAdmissions')}
          </span>
        </a>
      ) : (
        <a
          href="https://tuyensinh.ctu.edu.vn/"
          target="_blank"
          rel="noopener noreferrer"
          className="flex items-center justify-center p-2 cursor-pointer"
          title={t('sidebar.ctuAdmissions')}
        >
          <IconSchool size={16} className="text-primary" />
        </a>
      )}

      {/* Report Issue Link (optional) */}
      {reportIssueUrl && (
        <>
          {!isCollapsed ? (
            <a
              href={reportIssueUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-2 rounded-lg px-2 py-1 cursor-pointer"
              title={t('sidebar.reportIssue')}
            >
              <IconBug size={16} className="text-primary" />
              <span className="text-xs text-primary">
                {t('sidebar.reportIssue')}
              </span>
            </a>
          ) : (
            <a
              href={reportIssueUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center justify-center p-2 cursor-pointer"
              title={t('sidebar.reportIssue')}
            >
              <IconBug size={16} className="text-primary" />
            </a>
          )}
        </>
      )}
    </div>
  );
};
