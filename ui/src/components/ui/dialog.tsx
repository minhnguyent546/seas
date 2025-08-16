import { Button } from '@/components/ui/button';
import { useLanguage } from '@/hooks/useLanguage';
import {
  Dialog,
  DialogActions,
  DialogContent,
  DialogContentText,
  DialogTitle,
} from '@mui/material';
import React from 'react';

interface ConfirmDialogProps {
  open: boolean;
  onClose: () => void;
  onConfirm: () => void;
  title: string;
  message: string;
  confirmText?: string;
  cancelText?: string;
  confirmButtonVariant?:
    | 'primary'
    | 'secondary'
    | 'tertiary'
    | 'outline'
    | 'ghost';
  isLoading?: boolean;
}

export const ConfirmDialog: React.FC<ConfirmDialogProps> = ({
  open,
  onClose,
  onConfirm,
  title,
  message,
  confirmText,
  cancelText,
  confirmButtonVariant = 'primary',
  isLoading = false,
}) => {
  const { t } = useLanguage();

  return (
    <Dialog
      open={open}
      onClose={onClose}
      maxWidth="sm"
      fullWidth
      slotProps={{
        paper: {
          sx: {
            borderRadius: '1rem', // 16px equivalent to rounded-2xl
          },
        },
      }}
    >
      <DialogTitle className="text-lg font-medium">{title}</DialogTitle>
      <DialogContent>
        <DialogContentText className="text-gray-600 dark:text-gray-300">
          {message}
        </DialogContentText>
      </DialogContent>
      <DialogActions className="px-6 pb-4">
        <Button
          className="cursor-pointer"
          variant="outline"
          onClick={onClose}
          disabled={isLoading}
        >
          {cancelText || t('common.cancel')}
        </Button>
        <Button
          className="cursor-pointer"
          variant={confirmButtonVariant}
          onClick={onConfirm}
          isLoading={isLoading}
        >
          {confirmText || t('common.confirm')}
        </Button>
      </DialogActions>
    </Dialog>
  );
};
