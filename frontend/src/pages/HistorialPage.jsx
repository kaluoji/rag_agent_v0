// Modern History Page with card-based design
import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  Box, 
  Typography, 
  Container, 
  Paper, 
  TextField,
  InputAdornment,
  IconButton,
  Chip,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Alert,
  Grid,
  Card,
  CardContent,
  CardActions,
  Menu,
  MenuItem,
  alpha,
  useTheme,
  Fade
} from '@mui/material';
import SearchIcon from '@mui/icons-material/Search';
import DeleteIcon from '@mui/icons-material/Delete';
import ShareIcon from '@mui/icons-material/Share';
import MoreVertIcon from '@mui/icons-material/MoreVert';
import ClearAllIcon from '@mui/icons-material/ClearAll';
import FilterListIcon from '@mui/icons-material/FilterList';
import CalendarTodayIcon from '@mui/icons-material/CalendarToday';
import ChatBubbleOutlineIcon from '@mui/icons-material/ChatBubbleOutline';
import AnalyticsIcon from '@mui/icons-material/Analytics';
import { useQueryStore } from '../contexts/store';

const ModernHistoryPage = () => {
  const navigate = useNavigate();
  const theme = useTheme();
  const { recentQueries, loadStoredQueries } = useQueryStore();
  
  const [searchTerm, setSearchTerm] = useState('');
  const [filteredQueries, setFilteredQueries] = useState([]);
  const [confirmDeleteOpen, setConfirmDeleteOpen] = useState(false);
  const [queryToDelete, setQueryToDelete] = useState(null);
  const [confirmClearAllOpen, setConfirmClearAllOpen] = useState(false);
  const [selectedFilter, setSelectedFilter] = useState('all');
  const [menuAnchor, setMenuAnchor] = useState(null);
  const [selectedQuery, setSelectedQuery] = useState(null);

  useEffect(() => {
    loadStoredQueries();
  }, [loadStoredQueries]);

  useEffect(() => {
    let filtered = recentQueries;

    // Filtrar por búsqueda
    if (searchTerm.trim()) {
      filtered = filtered.filter(query =>
        query.text?.toLowerCase().includes(searchTerm.toLowerCase())
      );
    }

    // Filtrar por tipo
    if (selectedFilter !== 'all') {
      filtered = filtered.filter(query => query.type === selectedFilter);
    }

    setFilteredQueries(filtered);
  }, [recentQueries, searchTerm, selectedFilter]);

  const formatDate = (timestamp) => {
    const date = new Date(timestamp);
    const now = new Date();
    const diffInHours = (now - date) / (1000 * 60 * 60);
    
    if (diffInHours < 1) return 'Hace menos de una hora';
    if (diffInHours < 24) return `Hace ${Math.floor(diffInHours)} horas`;
    if (diffInHours < 48) return 'Ayer';
    return date.toLocaleDateString('es-ES', {
      day: 'numeric',
      month: 'short',
      year: 'numeric'
    });
  };

  const truncateText = (text, maxLength = 120) => {
    if (!text) return 'Sin contenido disponible';
    const textString = typeof text === 'string' ? text : String(text);
    return textString.length <= maxLength 
      ? textString 
      : textString.substring(0, maxLength) + '...';
  };

  const handleDeleteQuery = (query) => {
    setQueryToDelete(query);
    setConfirmDeleteOpen(true);
    setMenuAnchor(null);
  };

  const confirmDeleteQuery = () => {
    if (queryToDelete) {
      const updatedQueries = recentQueries.filter(q => q.id !== queryToDelete.id);
      localStorage.setItem('recentQueries', JSON.stringify(updatedQueries));
      loadStoredQueries();
    }
    setConfirmDeleteOpen(false);
    setQueryToDelete(null);
  };

  const handleClearAll = () => {
    setConfirmClearAllOpen(true);
  };

  const confirmClearAll = () => {
    localStorage.removeItem('recentQueries');
    loadStoredQueries();
    setConfirmClearAllOpen(false);
  };

  const handleShareQuery = async (query) => {
    const shareUrl = `${window.location.origin}/consulta/${query.id}`;
    
    if (navigator.share) {
      try {
        await navigator.share({
          title: 'Consulta Normativa',
          text: truncateText(query.text, 100),
          url: shareUrl,
        });
      } catch (error) {
        navigator.clipboard.writeText(shareUrl);
        alert('Enlace copiado al portapapeles');
      }
    } else {
      navigator.clipboard.writeText(shareUrl);
      alert('Enlace copiado al portapapeles');
    }
    setMenuAnchor(null);
  };

  const getQueryTypeConfig = (query) => {
    const lowerText = query.text?.toLowerCase() || '';
    if (lowerText.includes('gap') || lowerText.includes('análisis')) {
      return { 
        label: 'Análisis GAP', 
        color: 'secondary',
        icon: <AnalyticsIcon fontSize="small" />
      };
    }
    return { 
      label: 'Consulta', 
      color: 'primary',
      icon: <ChatBubbleOutlineIcon fontSize="small" />
    };
  };

  const handleMenuOpen = (event, query) => {
    event.stopPropagation();
    setMenuAnchor(event.currentTarget);
    setSelectedQuery(query);
  };

  const handleMenuClose = () => {
    setMenuAnchor(null);
    setSelectedQuery(null);
  };

  return (
    <Box sx={{ 
      minHeight: '100vh',
      bgcolor: 'background.default',
      pb: 4
    }}>
      <Container maxWidth="xl" sx={{ pt: 4 }}>
        {/* Header */}
        <Box sx={{ mb: 4 }}>
          <Typography 
            variant="h3" 
            fontWeight={700}
            sx={{ 
              mb: 1,
              background: 'linear-gradient(135deg, #4F062A 0%, #7A1149 100%)',
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent',
            }}
          >
            Historial de Conversaciones
          </Typography>
          <Typography variant="body1" color="text.secondary">
            Revisa y gestiona tus consultas anteriores
          </Typography>
        </Box>

        {/* Search and Filters */}
        <Paper 
          elevation={0}
          sx={{ 
            p: 3, 
            mb: 4,
            border: `1px solid ${alpha(theme.palette.divider, 0.5)}`,
            borderRadius: 3
          }}
        >
          <Grid container spacing={2} alignItems="center">
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                placeholder="Buscar en el historial..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                InputProps={{
                  startAdornment: (
                    <InputAdornment position="start">
                      <SearchIcon />
                    </InputAdornment>
                  ),
                }}
                sx={{
                  '& .MuiOutlinedInput-root': {
                    borderRadius: 3
                  }
                }}
              />
            </Grid>

            <Grid item xs={12} md={3}>
              <Box sx={{ display: 'flex', gap: 1 }}>
                <Chip
                  label="Todas"
                  onClick={() => setSelectedFilter('all')}
                  color={selectedFilter === 'all' ? 'primary' : 'default'}
                  variant={selectedFilter === 'all' ? 'filled' : 'outlined'}
                />
                <Chip
                  label="Análisis"
                  onClick={() => setSelectedFilter('gap_analysis')}
                  color={selectedFilter === 'gap_analysis' ? 'secondary' : 'default'}
                  variant={selectedFilter === 'gap_analysis' ? 'filled' : 'outlined'}
                />
                <Chip
                  label="Consultas"
                  onClick={() => setSelectedFilter('consultation')}
                  color={selectedFilter === 'consultation' ? 'primary' : 'default'}
                  variant={selectedFilter === 'consultation' ? 'filled' : 'outlined'}
                />
              </Box>
            </Grid>

            <Grid item xs={12} md={3}>
              <Box sx={{ display: 'flex', justifyContent: 'flex-end', gap: 1 }}>
                <Button
                  variant="outlined"
                  color="error"
                  startIcon={<ClearAllIcon />}
                  onClick={handleClearAll}
                  disabled={recentQueries.length === 0}
                >
                  Limpiar Todo
                </Button>
              </Box>
            </Grid>
          </Grid>
          
          <Typography variant="caption" color="text.secondary" sx={{ mt: 2, display: 'block' }}>
            {filteredQueries.length} de {recentQueries.length} conversaciones
          </Typography>
        </Paper>

        {/* Query Cards Grid */}
        {filteredQueries.length === 0 ? (
          <Paper 
            elevation={0}
            sx={{ 
              p: 6, 
              textAlign: 'center',
              border: `1px solid ${alpha(theme.palette.divider, 0.5)}`,
              borderRadius: 3
            }}
          >
            {recentQueries.length === 0 ? (
              <>
                <ChatBubbleOutlineIcon 
                  sx={{ 
                    fontSize: 64, 
                    color: 'text.disabled',
                    mb: 2
                  }} 
                />
                <Typography variant="h6" gutterBottom>
                  No hay conversaciones en tu historial
                </Typography>
                <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
                  Comienza una nueva conversación para ver tu historial aquí
                </Typography>
                <Button 
                  variant="contained"
                  onClick={() => navigate('/')}
                  sx={{
                    background: 'linear-gradient(135deg, #4F062A 0%, #7A1149 100%)',
                    px: 4,
                    py: 1.5,
                    borderRadius: 3
                  }}
                >
                  Nueva Conversación
                </Button>
              </>
            ) : (
              <>
                <SearchIcon 
                  sx={{ 
                    fontSize: 64, 
                    color: 'text.disabled',
                    mb: 2
                  }} 
                />
                <Typography variant="h6" gutterBottom>
                  No se encontraron resultados
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Intenta con otros términos de búsqueda
                </Typography>
              </>
            )}
          </Paper>
        ) : (
          <Grid container spacing={3}>
            {filteredQueries.map((query, index) => {
              const typeConfig = getQueryTypeConfig(query);
              
              return (
                <Grid item xs={12} sm={6} lg={4} key={query.id}>
                  <Fade in timeout={300} style={{ transitionDelay: `${index * 50}ms` }}>
                    <Card
                      elevation={0}
                      sx={{
                        height: '100%',
                        display: 'flex',
                        flexDirection: 'column',
                        cursor: 'pointer',
                        border: `1px solid ${alpha(theme.palette.divider, 0.5)}`,
                        borderRadius: 3,
                        transition: 'all 0.3s ease',
                        '&:hover': {
                          boxShadow: `0 8px 24px ${alpha(theme.palette.primary.main, 0.15)}`,
                          transform: 'translateY(-4px)',
                          borderColor: 'primary.main'
                        }
                      }}
                      onClick={() => navigate(`/consulta/${query.id}`)}
                    >
                      <CardContent sx={{ flexGrow: 1, p: 3 }}>
                        <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 2 }}>
                          <Chip 
                            icon={typeConfig.icon}
                            label={typeConfig.label}
                            color={typeConfig.color}
                            size="small"
                            variant="outlined"
                          />
                          <IconButton 
                            size="small"
                            onClick={(e) => handleMenuOpen(e, query)}
                          >
                            <MoreVertIcon fontSize="small" />
                          </IconButton>
                        </Box>

                        <Typography 
                          variant="h6" 
                          sx={{ 
                            mb: 1.5,
                            fontWeight: 600,
                            fontSize: '1rem',
                            lineHeight: 1.4,
                            display: '-webkit-box',
                            WebkitLineClamp: 2,
                            WebkitBoxOrient: 'vertical',
                            overflow: 'hidden'
                          }}
                        >
                          {query.text}
                        </Typography>

                        <Typography 
                          variant="body2" 
                          color="text.secondary"
                          sx={{
                            display: '-webkit-box',
                            WebkitLineClamp: 3,
                            WebkitBoxOrient: 'vertical',
                            overflow: 'hidden',
                            lineHeight: 1.6
                          }}
                        >
                          {typeof query.response === 'string' 
                            ? truncateText(query.response, 150)
                            : 'Ver respuesta completa...'
                          }
                        </Typography>
                      </CardContent>

                      <CardActions sx={{ 
                        p: 2, 
                        pt: 0,
                        borderTop: `1px solid ${alpha(theme.palette.divider, 0.5)}`
                      }}>
                        <Box sx={{ 
                          display: 'flex', 
                          alignItems: 'center',
                          color: 'text.secondary'
                        }}>
                          <CalendarTodayIcon sx={{ fontSize: 14, mr: 0.5 }} />
                          <Typography variant="caption">
                            {formatDate(query.timestamp)}
                          </Typography>
                        </Box>
                      </CardActions>
                    </Card>
                  </Fade>
                </Grid>
              );
            })}
          </Grid>
        )}

        {/* Context Menu */}
        <Menu
          anchorEl={menuAnchor}
          open={Boolean(menuAnchor)}
          onClose={handleMenuClose}
          PaperProps={{
            sx: {
              minWidth: 180,
              boxShadow: 3,
              borderRadius: 2
            }
          }}
        >
          <MenuItem onClick={() => {
            navigate(`/consulta/${selectedQuery?.id}`);
            handleMenuClose();
          }}>
            <ChatBubbleOutlineIcon fontSize="small" sx={{ mr: 1.5 }} />
            Ver conversación
          </MenuItem>
          <MenuItem onClick={() => {
            handleShareQuery(selectedQuery);
          }}>
            <ShareIcon fontSize="small" sx={{ mr: 1.5 }} />
            Compartir
          </MenuItem>
          <MenuItem 
            onClick={() => handleDeleteQuery(selectedQuery)}
            sx={{ color: 'error.main' }}
          >
            <DeleteIcon fontSize="small" sx={{ mr: 1.5 }} />
            Eliminar
          </MenuItem>
        </Menu>

        {/* Delete Confirmation Dialog */}
        <Dialog 
          open={confirmDeleteOpen} 
          onClose={() => setConfirmDeleteOpen(false)}
          PaperProps={{
            sx: { borderRadius: 3 }
          }}
        >
          <DialogTitle>Confirmar Eliminación</DialogTitle>
          <DialogContent>
            <Typography>
              ¿Estás seguro de que quieres eliminar esta conversación? Esta acción no se puede deshacer.
            </Typography>
            {queryToDelete && (
              <Paper sx={{ p: 2, mt: 2, bgcolor: 'background.default', borderRadius: 2 }}>
                <Typography variant="body2" fontWeight="medium">
                  {truncateText(queryToDelete.text, 100)}
                </Typography>
              </Paper>
            )}
          </DialogContent>
          <DialogActions sx={{ p: 2 }}>
            <Button onClick={() => setConfirmDeleteOpen(false)}>
              Cancelar
            </Button>
            <Button 
              onClick={confirmDeleteQuery} 
              color="error" 
              variant="contained"
              sx={{ borderRadius: 2 }}
            >
              Eliminar
            </Button>
          </DialogActions>
        </Dialog>

        {/* Clear All Confirmation Dialog */}
        <Dialog 
          open={confirmClearAllOpen} 
          onClose={() => setConfirmClearAllOpen(false)}
          PaperProps={{
            sx: { borderRadius: 3 }
          }}
        >
          <DialogTitle>Limpiar Todo el Historial</DialogTitle>
          <DialogContent>
            <Typography>
              ¿Estás seguro de que quieres eliminar todo tu historial de conversaciones? 
              Esta acción eliminará permanentemente todas las conversaciones guardadas y no se puede deshacer.
            </Typography>
          </DialogContent>
          <DialogActions sx={{ p: 2 }}>
            <Button onClick={() => setConfirmClearAllOpen(false)}>
              Cancelar
            </Button>
            <Button 
              onClick={confirmClearAll} 
              color="error" 
              variant="contained"
              sx={{ borderRadius: 2 }}
            >
              Limpiar Todo
            </Button>
          </DialogActions>
        </Dialog>
      </Container>
    </Box>
  );
};

export default ModernHistoryPage;