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
import OrganizationSelector from './OrganizationSelector';
import UserMenu from './UserMenu';
import { useAuth } from '../contexts/AuthContext';

interface AppHeaderProps {
  onMenuToggle?: () => void;
}

const AppHeader: React.FC<AppHeaderProps> = ({ onMenuToggle }) => {
  const { user } = useAuth();
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
      <Toolbar>
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
        
        <Typography variant="h6" noWrap component="div" sx={{ flexGrow: 0, mr: 4, fontWeight: 600 }}>
          AI Company
        </Typography>
        
        <Box sx={{ flexGrow: 1, display: 'flex', alignItems: 'center' }}>
          <OrganizationSelector />
        </Box>
        
        <UserMenu />
      </Toolbar>
    </AppBar>
  );
};

export default AppHeader;