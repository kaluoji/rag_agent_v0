// AppLayout - PERFECTLY ALIGNED VERSION
// Matches exact design from provided images

import React, { useState } from 'react';
import { Link as RouterLink, useLocation, useNavigate } from 'react-router-dom';
import {
  Box,
  Toolbar,
  Typography,
  IconButton,
  Drawer,
  List,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Avatar,
  useMediaQuery,
  useTheme,
  Collapse,
  Divider,
  alpha,
  Badge,
  Menu,
  MenuItem,
  Tooltip,
  Stack
} from '@mui/material';
import MenuIcon from '@mui/icons-material/Menu';
import ChatBubbleOutlineIcon from '@mui/icons-material/ChatBubbleOutline';
import HistoryIcon from '@mui/icons-material/History';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import ExpandLessIcon from '@mui/icons-material/ExpandLess';
import SettingsIcon from '@mui/icons-material/Settings';
import LogoutIcon from '@mui/icons-material/Logout';
import SmartToyIcon from '@mui/icons-material/SmartToy';
import AddIcon from '@mui/icons-material/Add';
import LightModeIcon from '@mui/icons-material/LightMode';
import DarkModeIcon from '@mui/icons-material/DarkMode';
import { useQueryStore } from '../contexts/store';

const ModernAppLayout = ({ children }) => {
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [historyOpen, setHistoryOpen] = useState(false);
  const [userMenuAnchor, setUserMenuAnchor] = useState(null);
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));
  const location = useLocation();
  const navigate = useNavigate();
  
  const { recentQueries } = useQueryStore();
  
  const toggleDrawer = (open) => (event) => {
    if (event.type === 'keydown' && (event.key === 'Tab' || event.key === 'Shift')) {
      return;
    }
    setDrawerOpen(open);
  };
  
  const toggleHistory = () => {
    setHistoryOpen(!historyOpen);
  };

  const isActive = (path) => location.pathname === path;

  const handleNewChat = () => {
    navigate('/');
  };

  const handleUserMenuOpen = (event) => {
    setUserMenuAnchor(event.currentTarget);
  };

  const handleUserMenuClose = () => {
    setUserMenuAnchor(null);
  };

  // Sidebar content
  const sidebarContent = (
    <Box sx={{ 
      width: 250,
      height: '100%',
      display: 'flex',
      flexDirection: 'column',
      bgcolor: '#FAFBFC', // Light gray background like in image
    }}>
      {/* Logo / Brand - PERFECTLY ALIGNED */}
      <Box sx={{ 
        px: 2.5,
        py: 2,
        display: 'flex',
        alignItems: 'center',
        gap: 1.5,
        minHeight: '72px', // Exact height to match chat header
        maxHeight: '72px',
        borderBottom: `1px solid ${alpha(theme.palette.divider, 0.08)}`
      }}>
        <Avatar 
          sx={{ 
            width: 48,
            height: 48,
            bgcolor: '#00548F', // Exact color from image
            boxShadow: 'none'
          }}
        >
          <SmartToyIcon sx={{ fontSize: 26, color: 'white' }} />
        </Avatar>
        <Box sx={{ flex: 1, minWidth: 0 }}>
          <Typography 
            variant="h6" 
            sx={{ 
              fontSize: '1.125rem',
              fontWeight: 700,
              letterSpacing: '-0.01em',
              lineHeight: 1.3,
              color: '#1a1a1a',
              fontFamily: '"Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif'
            }}
          >
            AgentIA
          </Typography>
          <Typography 
            variant="caption" 
            sx={{ 
              fontSize: '0.8125rem',
              lineHeight: 1.2,
              color: '#666',
              display: 'block',
              fontFamily: '"Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif'
            }}
          >
            Compliance Assistant
          </Typography>
        </Box>
      </Box>

      {/* New Chat Button - Prominent */}
      <Box sx={{ p: 2 }}>
        <ListItemButton
          onClick={handleNewChat}
          sx={{
            borderRadius: 2,
            py: 1.25,
            bgcolor: alpha('#00548F', 0.08),
            border: `1.5px solid ${alpha('#00548F', 0.2)}`,
            '&:hover': {
              bgcolor: alpha('#00548F', 0.12),
              border: `1.5px solid ${alpha('#00548F', 0.3)}`,
            },
            transition: 'all 0.2s ease'
          }}
        >
          <ListItemIcon sx={{ 
            color: '#00548F',
            minWidth: 36
          }}>
            <AddIcon sx={{ fontSize: 20 }} />
          </ListItemIcon>
          <ListItemText 
            primary="Nueva conversación"
            primaryTypographyProps={{
              fontWeight: 600,
              fontSize: '0.875rem',
              color: '#00548F',
              fontFamily: '"Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif'
            }}
          />
        </ListItemButton>
      </Box>

      <Divider sx={{ mx: 2, opacity: 0.6 }} />

      {/* Main Navigation */}
      <Box sx={{ flexGrow: 1, overflowY: 'auto', p: 2, pt: 1 }}>
        <List sx={{ px: 0 }}>
          {/* Conversaciones */}
          <ListItemButton
            onClick={() => navigate('/')}
            sx={{
              borderRadius: 2,
              mb: 0.5,
              py: 1,
              bgcolor: isActive('/') 
                ? alpha('#00548F', 0.08)
                : 'transparent',
              '&:hover': {
                bgcolor: alpha('#00548F', 0.06),
              }
            }}
          >
            <ListItemIcon sx={{ 
              color: isActive('/') ? '#00548F' : '#666',
              minWidth: 36
            }}>
              <ChatBubbleOutlineIcon sx={{ fontSize: 20 }} />
            </ListItemIcon>
            <ListItemText 
              primary="Conversaciones"
              primaryTypographyProps={{
                fontWeight: isActive('/') ? 600 : 400,
                fontSize: '0.875rem',
                fontFamily: '"Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif'
              }}
            />
          </ListItemButton>

          {/* Historial expandible */}
          <ListItemButton
            onClick={toggleHistory}
            sx={{
              borderRadius: 2,
              mb: 0.5,
              py: 1,
              '&:hover': {
                bgcolor: alpha('#00548F', 0.06),
              }
            }}
          >
            <ListItemIcon sx={{ 
              color: '#666',
              minWidth: 36
            }}>
              <Badge 
                badgeContent={recentQueries?.length || 0} 
                color="primary"
                invisible={!recentQueries?.length}
                sx={{
                  '& .MuiBadge-badge': {
                    fontSize: '0.625rem',
                    height: 16,
                    minWidth: 16,
                    padding: '0 4px',
                    bgcolor: '#00548F'
                  }
                }}
              >
                <HistoryIcon sx={{ fontSize: 20 }} />
              </Badge>
            </ListItemIcon>
            <ListItemText 
              primary="Historial"
              primaryTypographyProps={{
                fontWeight: 400,
                fontSize: '0.875rem',
                fontFamily: '"Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif'
              }}
            />
            {historyOpen ? 
              <ExpandLessIcon sx={{ fontSize: 18, color: '#666' }} /> : 
              <ExpandMoreIcon sx={{ fontSize: 18, color: '#666' }} />
            }
          </ListItemButton>

          {/* Historial items */}
          <Collapse in={historyOpen} timeout="auto" unmountOnExit>
            <Box sx={{ pl: 1, mt: 0.5 }}>
              <List component="div" disablePadding>
                {/* Ver todo */}
                <ListItemButton
                  onClick={() => navigate('/historial')}
                  sx={{
                    pl: 4,
                    py: 0.75,
                    borderRadius: 2,
                    mb: 0.5,
                    '&:hover': {
                      bgcolor: alpha('#00548F', 0.04),
                    }
                  }}
                >
                  <ListItemText 
                    primary="Ver todo"
                    primaryTypographyProps={{
                      fontSize: '0.8125rem',
                      fontWeight: 500,
                      color: '#00548F',
                      fontFamily: '"Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif'
                    }}
                  />
                </ListItemButton>

                {recentQueries?.length > 0 && (
                  <Divider sx={{ my: 0.5, opacity: 0.4 }} />
                )}

                {/* Consultas recientes */}
                {recentQueries?.slice(0, 5).map((query) => (
                  <ListItemButton
                    key={query.id}
                    onClick={() => navigate(`/consulta/${query.id}`)}
                    sx={{
                      pl: 4,
                      py: 0.75,
                      borderRadius: 2,
                      mb: 0.25,
                      bgcolor: location.pathname === `/consulta/${query.id}`
                        ? alpha('#00548F', 0.06)
                        : 'transparent',
                      '&:hover': {
                        bgcolor: alpha('#00548F', 0.04),
                      }
                    }}
                  >
                    <ListItemText 
                      primary={query.text?.length > 30 
                        ? `${query.text.substring(0, 30)}...` 
                        : query.text
                      }
                      secondary={new Date(query.timestamp).toLocaleDateString('es-ES', { 
                        day: 'numeric', 
                        month: 'short' 
                      })}
                      primaryTypographyProps={{
                        fontSize: '0.75rem',
                        noWrap: true,
                        color: '#333',
                        fontFamily: '"Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif'
                      }}
                      secondaryTypographyProps={{
                        fontSize: '0.6875rem',
                        color: '#999',
                        fontFamily: '"Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif'
                      }}
                    />
                  </ListItemButton>
                ))}

                {(!recentQueries || recentQueries.length === 0) && (
                  <Box sx={{ pl: 4, py: 2 }}>
                    <Typography 
                      variant="caption" 
                      color="text.disabled"
                      sx={{ 
                        fontSize: '0.75rem', 
                        fontStyle: 'italic',
                        fontFamily: '"Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif'
                      }}
                    >
                      Sin consultas recientes
                    </Typography>
                  </Box>
                )}
              </List>
            </Box>
          </Collapse>
        </List>
      </Box>

      <Divider sx={{ opacity: 0.6 }} />

      {/* User Profile - Clean */}
      <Box sx={{ p: 2 }}>
        <ListItemButton
          onClick={handleUserMenuOpen}
          sx={{
            borderRadius: 2,
            p: 1.25,
            '&:hover': {
              bgcolor: alpha('#00548F', 0.04)
            }
          }}
        >
          <Avatar 
            sx={{ 
              width: 32,
              height: 32,
              mr: 1.5,
              bgcolor: '#00548F',
              fontSize: '0.875rem',
              fontWeight: 600,
              fontFamily: '"Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif'
            }}
          >
            U
          </Avatar>
          <ListItemText 
            primary="Usuario"
            secondary="usuario@company.com"
            primaryTypographyProps={{
              fontSize: '0.875rem',
              fontWeight: 500,
              noWrap: true,
              fontFamily: '"Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif'
            }}
            secondaryTypographyProps={{
              fontSize: '0.75rem',
              noWrap: true,
              fontFamily: '"Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif'
            }}
          />
          <SettingsIcon sx={{ fontSize: 18, color: '#666', ml: 'auto' }} />
        </ListItemButton>
      </Box>
    </Box>
  );

  return (
    <Box sx={{ display: 'flex', minHeight: '100vh', bgcolor: '#F5F7FA' }}>
      {/* Mobile Drawer */}
      {isMobile && (
        <>
          {/* Mobile Header */}
          <Box
            sx={{
              position: 'fixed',
              top: 0,
              left: 0,
              right: 0,
              height: 64,
              bgcolor: 'background.paper',
              borderBottom: `1px solid ${alpha(theme.palette.divider, 0.08)}`,
              display: 'flex',
              alignItems: 'center',
              px: 2,
              zIndex: 1100,
              boxShadow: '0 1px 2px rgba(0,0,0,0.05)'
            }}
          >
            <IconButton
              edge="start"
              onClick={toggleDrawer(true)}
              sx={{ mr: 2 }}
            >
              <MenuIcon />
            </IconButton>
            <Avatar 
              sx={{ 
                width: 32,
                height: 32,
                mr: 1.5,
                bgcolor: '#00548F'
              }}
            >
              <SmartToyIcon sx={{ fontSize: 18 }} />
            </Avatar>
            <Typography 
              variant="h6" 
              fontWeight={700} 
              sx={{ 
                fontSize: '1rem',
                fontFamily: '"Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif'
              }}
            >
              AgentIA
            </Typography>
          </Box>

          <Drawer
            anchor="left"
            open={drawerOpen}
            onClose={toggleDrawer(false)}
            sx={{
              '& .MuiDrawer-paper': { 
                width: 250,
                border: 'none',
                boxShadow: 3
              },
            }}
          >
            {sidebarContent}
          </Drawer>
        </>
      )}

      {/* Desktop Permanent Drawer */}
      {!isMobile && (
        <Drawer
          variant="permanent"
          sx={{
            width: 250,
            flexShrink: 0,
            '& .MuiDrawer-paper': { 
              width: 250,
              border: 'none',
              borderRight: `1px solid ${alpha(theme.palette.divider, 0.08)}`,
              bgcolor: '#FAFBFC',
              boxShadow: 'none'
            },
          }}
        >
          {sidebarContent}
        </Drawer>
      )}

      {/* Main Content */}
      <Box
        component="main"
        sx={{
          flexGrow: 1,
          bgcolor: '#F5F7FA',
          minHeight: '100vh',
          mt: isMobile ? '64px' : 0,
          display: 'flex',
          flexDirection: 'column'
        }}
      >
        {children}
      </Box>

      {/* User Menu */}
      <Menu
        anchorEl={userMenuAnchor}
        open={Boolean(userMenuAnchor)}
        onClose={handleUserMenuClose}
        PaperProps={{
          sx: {
            mt: 1,
            minWidth: 200,
            boxShadow: '0 4px 20px rgba(0,0,0,0.08)',
            borderRadius: 2,
            border: `1px solid ${alpha(theme.palette.divider, 0.08)}`
          }
        }}
        transformOrigin={{ horizontal: 'left', vertical: 'bottom' }}
        anchorOrigin={{ horizontal: 'left', vertical: 'top' }}
      >
        <MenuItem 
          onClick={handleUserMenuClose}
          sx={{ 
            py: 1.25,
            fontFamily: '"Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif',
            '&:hover': { bgcolor: alpha('#00548F', 0.04) }
          }}
        >
          <ListItemIcon>
            <SettingsIcon fontSize="small" />
          </ListItemIcon>
          <ListItemText 
            primary="Configuración"
            primaryTypographyProps={{ 
              fontSize: '0.875rem',
              fontFamily: '"Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif'
            }}
          />
        </MenuItem>
        <Divider sx={{ my: 0.5 }} />
        <MenuItem 
          onClick={handleUserMenuClose}
          sx={{ 
            py: 1.25,
            color: 'error.main',
            fontFamily: '"Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif',
            '&:hover': { bgcolor: alpha(theme.palette.error.main, 0.04) }
          }}
        >
          <ListItemIcon>
            <LogoutIcon fontSize="small" color="error" />
          </ListItemIcon>
          <ListItemText 
            primary="Cerrar sesión"
            primaryTypographyProps={{ 
              fontSize: '0.875rem',
              fontFamily: '"Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif'
            }}
          />
        </MenuItem>
      </Menu>
    </Box>
  );
};

export default ModernAppLayout;