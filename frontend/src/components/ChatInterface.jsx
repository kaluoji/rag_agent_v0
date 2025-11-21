// ChatInterface - PERFECT VERSION
// - Exact color #00548F from images
// - Subtle right shadow on agent messages  
// - Tables with proper responsive overflow handling
// - Inter font family
// - Header height matches sidebar (72px)

import React, { useState, useRef, useEffect } from 'react';
import { 
  Box, 
  Typography, 
  Avatar,
  CircularProgress,
  Paper,
  IconButton,
  Fade,
  Tooltip,
  useTheme,
  alpha
} from '@mui/material';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import rehypeRaw from 'rehype-raw';
import SendIcon from '@mui/icons-material/Send';
import AttachFileIcon from '@mui/icons-material/AttachFile';
import MicIcon from '@mui/icons-material/Mic';
import MoreVertIcon from '@mui/icons-material/MoreVert';
import SmartToyIcon from '@mui/icons-material/SmartToy';
import PersonIcon from '@mui/icons-material/Person';

const ModernChatMessage = ({ message, isUser }) => {
  const theme = useTheme();
  
  return (
    <Fade in timeout={400}>
      <Box 
        sx={{ 
          display: 'flex', 
          mb: 3,
          flexDirection: isUser ? 'row-reverse' : 'row',
          gap: 2,
          alignItems: 'flex-start'
        }}
      >
        <Avatar 
          sx={{ 
            width: 40,
            height: 40,
            background: isUser 
              ? 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)'
              : '#00548F',
            boxShadow: '0 2px 6px rgba(0,0,0,0.08)',
          }}
        >
          {isUser ? <PersonIcon /> : <SmartToyIcon />}
        </Avatar>

        <Box sx={{ 
          maxWidth: '80%',
          display: 'flex',
          flexDirection: 'column',
          gap: 0.5
        }}>
          <Typography 
            variant="caption" 
            sx={{ 
              px: 1,
              color: '#666',
              fontWeight: 500,
              fontSize: '0.8125rem',
              fontFamily: '"Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif'
            }}
          >
            {isUser ? 'Tú' : 'AgentIA'}
          </Typography>

          <Paper 
            elevation={0}
            sx={{ 
              p: 3,
              backgroundColor: isUser 
                ? alpha('#00548F', 0.06)
                : '#FFFFFF',
              border: `1px solid ${isUser ? 'transparent' : alpha('#E0E0E0', 0.5)}`,
              borderRadius: isUser ? '18px 18px 4px 18px' : '18px 18px 18px 4px',
              transition: 'all 0.2s ease',
              // FIXED: Subtle shadow to the right for agent messages only
              boxShadow: isUser 
                ? 'none' 
                : '3px 0 10px rgba(0, 0, 0, 0.03), 1px 0 3px rgba(0, 0, 0, 0.02)',
              '&:hover': {
                boxShadow: isUser 
                  ? '0 2px 8px rgba(0,0,0,0.04)'
                  : '5px 0 15px rgba(0, 0, 0, 0.04), 2px 0 6px rgba(0, 0, 0, 0.02)',
                transform: 'translateY(-1px)'
              }
            }}
          >
            {isUser ? (
              <Typography 
                variant="body1" 
                sx={{ 
                  whiteSpace: 'pre-line',
                  lineHeight: 1.6,
                  color: '#1a1a1a',
                  fontSize: '0.9375rem',
                  fontFamily: '"Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif'
                }}
              >
                {message}
              </Typography>
            ) : (
              <Box 
                className="markdown-content-enhanced" 
                sx={{ 
                  fontFamily: '"Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif',
                  '& p': { 
                    mt: 0, 
                    mb: 1.5, 
                    lineHeight: 1.7,
                    fontSize: '0.9375rem',
                    color: '#333',
                    fontFamily: 'inherit'
                  },
                  '& h1, & h2': {
                    fontWeight: 700,
                    color: '#00548F',
                    lineHeight: 1.3,
                    fontFamily: 'inherit',
                    marginTop: '1.5rem',
                    marginBottom: '1rem'
                  },
                  '& h1': {
                    fontSize: '1.5rem',
                    borderBottom: '3px solid #00548F',
                    paddingBottom: '0.5rem'
                  },
                  '& h2': {
                    fontSize: '1.25rem',
                    borderBottom: '2px solid rgba(0, 84, 143, 0.25)',
                    paddingBottom: '0.4rem'
                  },
                  '& h3, & h4': {
                    fontWeight: 700,
                    color: '#00548F',
                    lineHeight: 1.3,
                    fontFamily: 'inherit',
                    marginTop: '1.25rem',
                    marginBottom: '0.75rem'
                  },
                  '& h3': {
                    fontSize: '1.125rem'
                  },
                  '& h4': {
                    fontSize: '1rem',
                    fontWeight: 600
                  },
                  '& strong': {
                    fontWeight: 700,
                    color: '#00548F',
                    fontFamily: 'inherit'
                  },
                  '& ul, & ol': { 
                    mt: 1.5, 
                    mb: 2, 
                    pl: 2.5,
                    '& li': {
                      mb: 0.75,
                      lineHeight: 1.7,
                      fontFamily: 'inherit',
                      fontSize: '0.9375rem',
                      '& strong': {
                        color: '#00548F',
                        fontWeight: 700
                      }
                    }
                  },
                  '& li::marker': {
                    color: '#00548F',
                    fontWeight: 700
                  },
                  '& code': { 
                    px: 0.75,
                    py: 0.375,
                    borderRadius: 0.75,
                    bgcolor: alpha('#00548F', 0.06),
                    fontFamily: '"SF Mono", "Monaco", "Consolas", monospace',
                    fontSize: '0.875em',
                    border: `1px solid ${alpha('#00548F', 0.12)}`,
                    fontWeight: 500,
                    color: '#00548F'
                  },
                  '& pre': { 
                    p: 2,
                    my: 2,
                    borderRadius: 2,
                    bgcolor: alpha('#00548F', 0.03),
                    overflowX: 'auto',
                    border: `1px solid ${alpha('#00548F', 0.12)}`,
                    boxShadow: 'none',
                    '& code': { 
                      p: 0, 
                      bgcolor: 'transparent',
                      border: 'none'
                    }
                  },
                  '& blockquote': {
                    my: 2,
                    pl: 2,
                    py: 1,
                    borderLeft: `4px solid #00548F`,
                    bgcolor: alpha('#00548F', 0.03),
                    fontStyle: 'italic',
                    color: '#666',
                    borderRadius: '0 8px 8px 0'
                  },
                  // TABLES - FIXED: Properly responsive with scroll
                  '& > div': {
                    overflowX: 'auto',
                    width: '100%',
                    WebkitOverflowScrolling: 'touch',
                    '&::-webkit-scrollbar': {
                      height: '6px'
                    },
                    '&::-webkit-scrollbar-thumb': {
                      backgroundColor: alpha('#00548F', 0.2),
                      borderRadius: '3px'
                    }
                  },
                  '& table': {
                    width: '100%',
                    minWidth: '600px', // Ensures horizontal scroll when needed
                    borderCollapse: 'separate',
                    borderSpacing: 0,
                    my: 2,
                    boxShadow: '0 2px 8px rgba(0, 84, 143, 0.08)',
                    borderRadius: '8px',
                    overflow: 'hidden',
                    border: `1px solid ${alpha('#00548F', 0.12)}`,
                    display: 'table' // Important: keep as table
                  },
                  '& thead': {
                    background: 'linear-gradient(135deg, #00548F 0%, #0073B7 100%)',
                    position: 'sticky',
                    top: 0,
                    zIndex: 1
                  },
                  '& th': {
                    p: 1.5,
                    textAlign: 'left',
                    fontWeight: 700,
                    fontSize: '0.8125rem',
                    color: 'white',
                    textTransform: 'uppercase',
                    letterSpacing: '0.3px',
                    borderBottom: 'none',
                    whiteSpace: 'nowrap',
                    fontFamily: 'inherit'
                  },
                  '& td': {
                    p: 1.5,
                    borderBottom: `1px solid ${alpha('#00548F', 0.08)}`,
                    fontSize: '0.875rem',
                    verticalAlign: 'top',
                    lineHeight: 1.6,
                    color: '#333',
                    fontFamily: 'inherit'
                  },
                  '& tbody tr': {
                    background: 'white',
                    transition: 'all 0.15s ease',
                    '&:nth-of-type(even)': {
                      background: alpha('#00548F', 0.02)
                    },
                    '&:hover': {
                      background: alpha('#00548F', 0.04),
                      transform: 'scale(1.001)'
                    },
                    '&:last-child td': {
                      borderBottom: 'none'
                    }
                  },
                  '& hr': {
                    my: 2.5,
                    border: 'none',
                    height: '1px',
                    background: `linear-gradient(90deg, transparent, ${alpha('#00548F', 0.2)}, transparent)`
                  },
                  '& a': {
                    color: '#00548F',
                    textDecoration: 'none',
                    fontWeight: 500,
                    borderBottom: '1px solid transparent',
                    transition: 'all 0.2s ease',
                    '&:hover': {
                      borderBottomColor: '#00548F'
                    }
                  }
                }}
              >
                <Box sx={{ overflowX: 'auto', width: '100%' }}>
                  <ReactMarkdown
                    remarkPlugins={[remarkGfm]}
                    rehypePlugins={[rehypeRaw]}
                  >
                    {message}
                  </ReactMarkdown>
                </Box>
              </Box>
            )}
          </Paper>
        </Box>
      </Box>
    </Fade>
  );
};

const QuickSuggestions = ({ onSelect }) => {
  const suggestions = [
    "¿Cuáles son las mejores prácticas de seguridad de datos?",
    "Explícame los requisitos del RGPD",
    "¿Cómo implementar controles de acceso?"
  ];

  return (
    <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 2, justifyContent: 'center' }}>
      {suggestions.map((suggestion, index) => (
        <Paper
          key={index}
          elevation={0}
          onClick={() => onSelect(suggestion)}
          sx={{
            p: 2.5,
            cursor: 'pointer',
            border: '1px solid',
            borderColor: alpha('#00548F', 0.15),
            borderRadius: 2.5,
            transition: 'all 0.2s ease',
            maxWidth: 280,
            '&:hover': {
              borderColor: '#00548F',
              bgcolor: alpha('#00548F', 0.03),
              transform: 'translateY(-2px)',
              boxShadow: `0 4px 12px ${alpha('#00548F', 0.12)}`
            }
          }}
        >
          <Typography 
            variant="body2" 
            sx={{ 
              fontFamily: '"Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif',
              fontSize: '0.875rem',
              lineHeight: 1.5,
              color: '#333'
            }}
          >
            {suggestion}
          </Typography>
        </Paper>
      ))}
    </Box>
  );
};

const ModernChatInterface = ({ onSubmitQuery, isLoading }) => {
  const [message, setMessage] = useState('');
  const [chatHistory, setChatHistory] = useState([]);
  const [showSuggestions, setShowSuggestions] = useState(true);
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);
  const theme = useTheme();

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [chatHistory, isLoading]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!message.trim() || isLoading) return;

    const userMessage = message.trim();
    setMessage('');
    setShowSuggestions(false);

    setChatHistory(prev => [...prev, { 
      text: userMessage, 
      isUser: true,
      timestamp: new Date()
    }]);

    if (onSubmitQuery) {
      await onSubmitQuery(userMessage, (response) => {
        setChatHistory(prev => [...prev, {
          text: response,
          isUser: false,
          timestamp: new Date()
        }]);
      });
    }
  };

  const handleSuggestionSelect = (suggestion) => {
    setMessage(suggestion);
    inputRef.current?.focus();
  };

  return (
    <Box sx={{ 
      display: 'flex', 
      flexDirection: 'column',
      height: '100vh',
      maxHeight: '100vh',
      bgcolor: '#FFFFFF'
    }}>
      {/* Header - PERFECTLY ALIGNED with sidebar */}
      <Box sx={{ 
        px: 3,
        py: 2,
        minHeight: '72px',
        maxHeight: '72px',
        display: 'flex',
        alignItems: 'center',
        borderBottom: `1px solid ${alpha(theme.palette.divider, 0.08)}`,
        background: '#FFFFFF'
      }}>
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', width: '100%' }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
            <Avatar 
              sx={{ 
                width: 48,
                height: 48,
                bgcolor: '#00548F',
                boxShadow: '0 2px 6px rgba(0, 84, 143, 0.15)'
              }}
            >
              <SmartToyIcon />
            </Avatar>
            <Box>
              <Typography 
                variant="h6" 
                sx={{ 
                  fontWeight: 700,
                  fontSize: '1.125rem',
                  lineHeight: 1.3,
                  fontFamily: '"Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif'
                }}
              >
                AgentIA
              </Typography>
              <Typography 
                variant="caption" 
                sx={{ 
                  fontSize: '0.8125rem',
                  color: '#666',
                  display: 'block',
                  lineHeight: 1.2,
                  fontFamily: '"Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif'
                }}
              >
                Asistente de Compliance
              </Typography>
            </Box>
          </Box>
          <IconButton>
            <MoreVertIcon />
          </IconButton>
        </Box>
      </Box>

      {/* Messages */}
      <Box 
        sx={{ 
          flexGrow: 1,
          overflowY: 'auto',
          p: 3,
          bgcolor: '#F5F7FA',
          '&::-webkit-scrollbar': { width: '6px' },
          '&::-webkit-scrollbar-track': { background: 'transparent' },
          '&::-webkit-scrollbar-thumb': {
            background: alpha('#00548F', 0.15),
            borderRadius: '10px',
          },
        }}
      >
        {chatHistory.length === 0 && showSuggestions ? (
          <Box sx={{ 
            display: 'flex', 
            flexDirection: 'column', 
            alignItems: 'center',
            justifyContent: 'center',
            minHeight: '100%',
            textAlign: 'center'
          }}>
            <Fade in timeout={800}>
              <Box>
                <Typography 
                  variant="h3" 
                  fontWeight={700}
                  sx={{ 
                    mb: 2,
                    background: 'linear-gradient(135deg, #00548F 0%, #0073B7 100%)',
                    WebkitBackgroundClip: 'text',
                    WebkitTextFillColor: 'transparent',
                    fontFamily: '"Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif',
                    fontSize: '2rem'
                  }}
                >
                  ¿Listo para hablar de compliance?
                </Typography>
                <Typography 
                  variant="body1" 
                  sx={{ 
                    mb: 6, 
                    maxWidth: 600,
                    color: '#666',
                    fontFamily: '"Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif'
                  }}
                >
                  Consulta cualquier duda normativa o regulatoria.
                </Typography>
                <QuickSuggestions onSelect={handleSuggestionSelect} />
              </Box>
            </Fade>
          </Box>
        ) : (
          chatHistory.map((msg, index) => (
            <ModernChatMessage 
              key={index}
              message={msg.text}
              isUser={msg.isUser}
            />
          ))
        )}

        {isLoading && (
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 3 }}>
            <Avatar 
              sx={{ 
                width: 40,
                height: 40,
                bgcolor: '#00548F'
              }}
            >
              <SmartToyIcon />
            </Avatar>
            <Paper
              elevation={0}
              sx={{
                p: 2,
                display: 'flex',
                alignItems: 'center',
                gap: 2,
                border: `1px solid ${alpha('#E0E0E0', 0.5)}`,
                borderRadius: '18px 18px 18px 4px',
                bgcolor: '#FFFFFF'
              }}
            >
              <CircularProgress size={20} sx={{ color: '#00548F' }} />
              <Typography 
                variant="body2" 
                sx={{ 
                  color: '#666',
                  fontFamily: '"Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif'
                }}
              >
                Pensando...
              </Typography>
            </Paper>
          </Box>
        )}

        <div ref={messagesEndRef} />
      </Box>

      {/* Input */}
      <Box sx={{ 
        p: 3,
        borderTop: `1px solid ${alpha(theme.palette.divider, 0.08)}`,
        background: '#FFFFFF'
      }}>
        <form onSubmit={handleSubmit}>
          <Paper
            elevation={0}
            sx={{
              display: 'flex',
              alignItems: 'center',
              gap: 1,
              p: 1.5,
              border: `1.5px solid ${alpha('#E0E0E0', 0.5)}`,
              borderRadius: 3,
              transition: 'all 0.2s ease',
              '&:focus-within': {
                borderColor: '#00548F',
                boxShadow: `0 0 0 3px ${alpha('#00548F', 0.08)}`
              }
            }}
          >
            <Tooltip title="Adjuntar archivo">
              <IconButton size="small" sx={{ color: '#666' }}>
                <AttachFileIcon />
              </IconButton>
            </Tooltip>

            <input
              ref={inputRef}
              type="text"
              placeholder="Escribe tu consulta aquí..."
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              disabled={isLoading}
              style={{
                flex: 1,
                border: 'none',
                outline: 'none',
                fontSize: '0.9375rem',
                padding: '8px',
                background: 'transparent',
                fontFamily: '"Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif',
                color: '#1a1a1a'
              }}
            />

            <Tooltip title="Mensaje de voz">
              <IconButton size="small" sx={{ color: '#666' }}>
                <MicIcon />
              </IconButton>
            </Tooltip>

            <Tooltip title="Enviar">
              <span>
                <IconButton 
                  type="submit"
                  disabled={!message.trim() || isLoading}
                  sx={{
                    background: !message.trim() || isLoading 
                      ? alpha('#E0E0E0', 0.3)
                      : 'linear-gradient(135deg, #00548F 0%, #0073B7 100%)',
                    color: 'white',
                    '&:hover': {
                      background: 'linear-gradient(135deg, #0073B7 0%, #00548F 100%)',
                      transform: 'scale(1.05)'
                    },
                    '&.Mui-disabled': {
                      color: alpha('#666', 0.5),
                      background: alpha('#E0E0E0', 0.3)
                    },
                    transition: 'all 0.2s ease'
                  }}
                >
                  <SendIcon />
                </IconButton>
              </span>
            </Tooltip>
          </Paper>

          <Typography 
            variant="caption" 
            sx={{ 
              display: 'block',
              textAlign: 'center',
              mt: 1.5,
              color: '#999',
              fontSize: '0.75rem',
              fontFamily: '"Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif'
            }}
          >
            AgentIA puede cometer errores. Verifica la información importante.
          </Typography>
        </form>
      </Box>
    </Box>
  );
};

export default ModernChatInterface;