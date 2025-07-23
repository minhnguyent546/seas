import { SeasLogo } from '@/components/icons';
import { Box, CircularProgress, Typography } from '@mui/material';

interface LoadingProps {
  message?: string;
  size?: number;
  fullScreen?: boolean;
}

export function Loading({
  message = 'Loading...',
  size = 40,
  fullScreen = true,
}: LoadingProps) {
  return (
    <Box
      sx={{
        display: 'flex',
        height: fullScreen ? '100vh' : '100%',
        justifyContent: 'center',
        alignItems: 'center',
        flexDirection: 'column',
        gap: 2,
      }}
    >
      <SeasLogo size={60} className="text-primary mb-2" />
      <CircularProgress size={size} />
      {message && (
        <Typography variant="body1" color="text.secondary">
          {message}
        </Typography>
      )}
    </Box>
  );
}
