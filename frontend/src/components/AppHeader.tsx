import React from 'react';
import {
  AppBar,
  Toolbar,
  Typography,
  Box,
  IconButton,
  useTheme,
  useMediaQuery
} from '@mui/material';
import { Menu as MenuIcon } from '@mui/icons-material';
import UserMenu from './UserMenu';
import ThemeToggle from './ThemeToggle';
import { useSupabaseAuth } from '../contexts/SupabaseAuthContext';

interface AppHeaderProps {
  onMenuToggle?: () => void;
}

const AppHeader: React.FC<AppHeaderProps> = ({ onMenuToggle }) => {
  const { user } = useSupabaseAuth();
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));

  if (!user) return null;

  return (
    <AppBar 
      position="fixed" 
      sx={{ 
        zIndex: (theme) => theme.zIndex.drawer + 1,
        backgroundColor: 'background.paper',
        color: 'text.primary',
        boxShadow: 1
      }}
    >
      <Toolbar sx={{ minHeight: '48px !important', height: '48px' }}>
        {isMobile && onMenuToggle && (
          <IconButton
            color="inherit"
            aria-label="open drawer"
            onClick={onMenuToggle}
            edge="start"
            sx={{ mr: 2 }}
          >
            <MenuIcon />
          </IconButton>
        )}
        
        <Box sx={{ display: 'flex', alignItems: 'center', mr: 3 }}>
          <img src="/logo.svg" alt="AICOS Logo" style={{ width: 24, height: 24, marginRight: 6 }} />
          <Typography variant="body1" noWrap component="div" sx={{ fontWeight: 600, fontSize: '15px' }}>
            AICOS
          </Typography>
        </Box>
        
        <Box sx={{ flexGrow: 1 }} />
        
        <ThemeToggle />
        <UserMenu />
      </Toolbar>
    </AppBar>
  );
};

export default AppHeader;