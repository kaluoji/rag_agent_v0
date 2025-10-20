// frontend/src/components/ChatInterface.jsx (modificado)
import React, { useState, useRef, useEffect } from 'react';
import { 
  Box, 
  Typography, 
  Avatar,
  CircularProgress,
  Divider,
  Paper,
  Grid,
  Fade,
  Zoom,
  IconButton,
  Collapse,
  Chip,
  Button,
  Tooltip
} from '@mui/material';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import rehypeRaw from 'rehype-raw';
import ChatInputArea from './ChatInputArea';
import DocxPreviewPanel from './DocxPreviewPanel';
import VisibilityIcon from '@mui/icons-material/Visibility';
import DescriptionIcon from '@mui/icons-material/Description';
import DocumentUploader from './DocumentUploader';
import AttachFileIcon from '@mui/icons-material/AttachFile';
import AnalyticsIcon from '@mui/icons-material/Analytics';
import DeleteIcon from '@mui/icons-material/Delete';


// Importamos la imagen del avatar del agente
import agentAvatar from '../assets/a.png';
// Importamos el logo
import logoImage from '../assets/ablack.png';

// Componente para un mensaje individual en el chat
const ChatMessage = ({ message, isUser, onViewReport }) => {
  // Estado para almacenar la información del reporte si existe
  const [reportInfo, setReportInfo] = useState(null);
  
  // Al montar el componente, analizar el mensaje para detectar informe
  useEffect(() => {
    if (!isUser && message) {
      // Verificar si el mensaje contiene información de un reporte
      const hasTitulo = message.includes('Título:');
      const hasUbicacion = message.includes('Ubicación:');
      
      if (hasTitulo && hasUbicacion) {
        try {
          // Extraer la información del reporte usando regex
          const titleMatch = message.match(/Título:\s+([^\n]+)/);
          const locationMatch = message.match(/Ubicación:\s+([^\n]+)/);
          
          if (titleMatch && locationMatch) {
            setReportInfo({
              title: titleMatch[1].trim(),
              path: locationMatch[1].trim()
            });
          }
        } catch (error) {
          console.error('Error al analizar información del reporte:', error);
        }
      }
    }
  }, [message, isUser]);

  return (
    <Box 
      sx={{ 
        display: 'flex', 
        mb: 2,
        flexDirection: isUser ? 'row-reverse' : 'row',
      }}
      className="chat-message"
    >
      {isUser ? (
        <Avatar 
          sx={{ 
            bgcolor: '#4F062A',
            width: 38,
            height: 38,
            mr: isUser ? 0 : 1,
            ml: isUser ? 1 : 0
          }}
        >
          U
        </Avatar>
      ) : (
        <Box
          sx={{
            width: 38,
            height: 38,
            mr: 1,
            borderRadius: '50%',
            bgcolor: '#4F062A',
            display: 'flex',
            justifyContent: 'center',
            alignItems: 'center',
            overflow: 'hidden'
          }}
        >
          <Box
            component="img"
            src={agentAvatar}
            alt="Agent"
            sx={{
              width: '80%',
              height: '80%',
              objectFit: 'contain'
            }}
          />
        </Box>
      )}
      <Paper 
        elevation={1} 
        sx={{ 
          p: 2, 
          maxWidth: '80%',
          bgcolor: isUser ? '#4F062A' : 'grey.100',
          color: isUser ? 'white' : 'inherit',
          borderRadius: '16px',
        }}
      >
        {isUser ? (
          <Typography variant="body1" sx={{ whiteSpace: 'pre-line', color: 'inherit', fontSize: '1.05rem' }}>
            {message.split(/(\¿Listo para hablar compliance\?)/).map((part, index) => {
              if (part === '¿Listo para hablar compliance?') {
                return <span key={index} className="highlighted-text">{part}</span>;
              }
              return part;
            })}
          </Typography>
        ) : (
          <Box 
            className="markdown-content" 
            sx={{ 
              '& p': { mt: 0, mb: 2, fontSize: '1.05rem' },
              '& ul, & ol': { mt: 0, mb: 2, pl: 3 },
              '& code': { 
                p: 0.5, 
                borderRadius: 1, 
                bgcolor: 'rgba(0, 0, 0, 0.04)', 
                fontFamily: 'monospace' 
              },
              '& pre': { 
                p: 1.5, 
                borderRadius: 1, 
                bgcolor: 'rgba(0, 0, 0, 0.04)', 
                overflowX: 'auto',
                '& code': { p: 0, bgcolor: 'transparent' }
              },
              '& blockquote': { 
                borderLeft: '4px solid #e0e0e0', 
                pl: 2, 
                ml: 0, 
                fontStyle: 'italic' 
              },
              '& h1, & h2, & h3, & h4, & h5, & h6': { 
                mt: 2, 
                mb: 1 
              },
              '& mark': {
                backgroundColor: '#ffeb3b',
                padding: '2px 4px',
                fontSize: '1.4em',
                fontWeight: 500,
                borderRadius: '3px'
              },

              // Estilos específicos para tablas
              '& table': {
                width: '100%',
                borderCollapse: 'collapse',
                margin: '16px 0',
                boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
                overflow: 'hidden',
                borderRadius: '8px'
              },
              '& thead': {
                backgroundColor: '#4F062A',
                color: 'white'
              },
              '& th': {
                padding: '12px 16px',
                textAlign: 'left',
                fontWeight: 600,
                fontSize: '0.9rem',
                borderBottom: 'none'
              },
              '& td': {
                padding: '12px 16px',
                borderBottom: '1px solid #e0e0e0',
                fontSize: '0.9rem',
                verticalAlign: 'top'
              },
              '& tbody tr': {
                backgroundColor: '#fff',
                transition: 'background-color 0.2s ease',
                '&:hover': {
                  backgroundColor: '#f9f9f9'
                },
                '&:last-child td': {
                  borderBottom: 'none'
                }
              },
              '& tbody tr:nth-of-type(even)': {
                backgroundColor: '#f8f9fa'
              },
    
              position: 'relative', // Para el botón de previsualización
            }}
          >
            <ReactMarkdown 
              remarkPlugins={[remarkGfm]}
              rehypePlugins={[rehypeRaw]}
            >
              {message}
            </ReactMarkdown>
            
            {/* Botón para previsualizar informe si existe */}
            {reportInfo && (
              <Box sx={{ 
                mt: 2, 
                display: 'flex', 
                alignItems: 'center',
                p: 1,
                borderTop: '1px solid rgba(0,0,0,0.1)'
              }}>
                <DescriptionIcon sx={{ mr: 1, color: '#4F062A' }} />
                <Typography variant="body2" sx={{ flexGrow: 1 }}>
                  Documento generado: {reportInfo.title.split('/').pop()}
                </Typography>
                <Tooltip title="Ver documento">
                  <IconButton 
                    size="small"
                    onClick={() => onViewReport(reportInfo)}
                    sx={{ 
                      color: '#4F062A',
                      backgroundColor: 'rgba(79, 6, 42, 0.1)',
                      '&:hover': {
                        backgroundColor: 'rgba(79, 6, 42, 0.2)',
                      }
                    }}
                  >
                    <VisibilityIcon fontSize="small" />
                  </IconButton>
                </Tooltip>
              </Box>
            )}
          </Box>
        )}
      </Paper>
    </Box>
  );
};

const ChatInterface = ({ onSubmitQuery, isLoading }) => {
  const [chatHistory, setChatHistory] = useState([]);
  const messagesEndRef = useRef(null);
  const messageContainerRef = useRef(null);
  const [showDocumentUploader, setShowDocumentUploader] = useState(false);
  const [uploadedDocuments, setUploadedDocuments] = useState([]);
  const [isGapAnalysisMode, setIsGapAnalysisMode] = useState(false);
  
  // Estado para controlar las animaciones
  const [showWelcome, setShowWelcome] = useState(false);
  
  // Estado para el panel de previsualización de documentos
  const [previewOpen, setPreviewOpen] = useState(false);
  const [previewReport, setPreviewReport] = useState(null);

  // Scroll al final cuando se agregan nuevos mensajes
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [chatHistory]);
  
  // Efecto para mostrar la animación de bienvenida
  useEffect(() => {
    // Pequeño retraso para que la animación sea perceptible
    const timer = setTimeout(() => {
      setShowWelcome(true);
    }, 300);
    
    return () => clearTimeout(timer);
  }, []);

  // Agregar respuesta al historial de chat
  const addResponseToChat = (response) => {
    setChatHistory(prevHistory => [
      ...prevHistory,
      { isUser: false, text: response }
    ]);
  };
  
  // Manejar visualización de reporte
  const handleViewReport = (reportInfo) => {
    console.log("Abriendo reporte:", reportInfo);
    
    // Mejorar extracción del ID del reporte
    let reportId = null;
    
    // Intentar extraer ID de diferentes formatos de path
    const patterns = [
      /Reporte_Normativo_.*?_(\d{8}_\d{6})\.docx/,
      /Reporte_Normativo_(\d{8}_\d{6})\.docx/,
      /_(\d{8}_\d{6})\.docx/
    ];
    
    for (const pattern of patterns) {
      const match = reportInfo.path.match(pattern);
      if (match && match[1]) {
        reportId = match[1];
        break;
      }
    }
    
    console.log("ID del reporte extraído:", reportId);
    
    setPreviewReport({
      ...reportInfo,
      extractedId: reportId
    });
    setPreviewOpen(true);
  };
  
  // Cerrar panel de previsualización
  const handleClosePreview = () => {
    setPreviewOpen(false);
  };

  // Función para manejar la selección directa de archivos
  const handleDirectFileSelection = async (file) => {
    // Validar el archivo
    const maxSize = 10 * 1024 * 1024; // 10MB
    const allowedTypes = ['.pdf', '.docx', '.txt'];
    
    if (file.size > maxSize) {
      alert('El archivo es demasiado grande. Máximo 10MB.');
      return;
    }
    
    const extension = '.' + file.name.split('.').pop().toLowerCase();
    if (!allowedTypes.includes(extension)) {
      alert(`Tipo de archivo no permitido. Tipos válidos: ${allowedTypes.join(', ')}`);
      return;
    }

    // Crear objeto de archivo compatible con el sistema existente
    const fileObject = {
      id: Date.now() + Math.random(),
      file: file,
      name: file.name,
      size: file.size,
      type: file.type,
      uploadedAt: new Date()
    };
    
    // Actualizar el estado
    setUploadedDocuments([fileObject]);
    setIsGapAnalysisMode(true);
    setShowDocumentUploader(true); // Mostrar el área compacta de confirmación
  };

  const handleToggleDocumentUploader = () => {
    // Si ya hay documentos cargados, alternar la vista
    if (uploadedDocuments.length > 0) {
      setShowDocumentUploader(!showDocumentUploader);
      setIsGapAnalysisMode(!isGapAnalysisMode);
      
      // Si estamos cerrando el uploader, limpiar documentos
      if (showDocumentUploader) {
        setUploadedDocuments([]);
      }
    } else {
      // Si no hay documentos, abrir directamente el selector de archivos
      const fileInput = document.createElement('input');
      fileInput.type = 'file';
      fileInput.accept = '.pdf,.docx,.txt';
      fileInput.onchange = (e) => {
        const file = e.target.files[0];
        if (file) {
          handleDirectFileSelection(file);
        }
      };
      fileInput.click();
    }
  };

  const handleFilesChange = (files) => {
    setUploadedDocuments(files);
  };

  const handleSubmitWithDocuments = async (message) => {
    if (isGapAnalysisMode && uploadedDocuments.length === 0) {
      // Mostrar mensaje de error si no hay documentos cargados
      alert('Por favor, carga al menos un documento para realizar el análisis GAP');
      return;
    }
    
    // Procesar los archivos a base64 si hay documentos cargados
    let documentsData = null;
    
    if (uploadedDocuments.length > 0) {
      documentsData = await Promise.all(
        uploadedDocuments.map(async (fileObj) => {
          return new Promise((resolve) => {
            const reader = new FileReader();
            reader.onload = (e) => {
              resolve({
                name: fileObj.name,
                type: fileObj.type,
                content: e.target.result.split(',')[1], // Remover el prefijo data:...base64,
                size: fileObj.size
              });
            };
            reader.readAsDataURL(fileObj.file);
          });
        })
      );
    }
    
    // Construir el mensaje enriquecido para GAP analysis
    let enrichedMessage = message;
    
    if (isGapAnalysisMode && documentsData) {
      enrichedMessage = `Realiza un análisis GAP del siguiente documento: ${documentsData[0].name}

Política a evaluar:
[DOCUMENTO_CARGADO: ${documentsData[0].name}]

Consulta específica: ${message}`;
    }
    
    // Agregar consulta del usuario al historial (mensaje original, no enriquecido)
    setChatHistory(prevHistory => [
      ...prevHistory,
      { isUser: true, text: message, hasDocuments: uploadedDocuments.length > 0 }
    ]);
    
    // Enviar consulta al componente padre con los documentos
    onSubmitQuery(enrichedMessage, addResponseToChat, documentsData);
    
    // Limpiar el modo GAP analysis después del envío
    if (isGapAnalysisMode) {
      setShowDocumentUploader(false);
      setIsGapAnalysisMode(false);
      setUploadedDocuments([]);
    }
  };


  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      {/* Área de mensajes con clase especial para scrollbar sutil y fondo con degradado */}
      <Box 
        ref={messageContainerRef}
        className="chat-messages-container"
        sx={{ 
          flexGrow: 1, 
          overflowY: 'auto', 
          p: 3,
          // Degradado sutil de fondo
          background: 'linear-gradient(to bottom, rgba(249, 250, 252, 0.8) 0%, rgba(249, 250, 252, 1) 100%)',
          display: 'flex',
          flexDirection: 'column',
          '&::-webkit-scrollbar': {
            width: '6px',
          },
          '&::-webkit-scrollbar-track': {
            background: 'transparent',
            borderRadius: '10px',
          },
          '&::-webkit-scrollbar-thumb': {
            background: 'rgba(79, 6, 42, 0.2)',
            borderRadius: '10px',
            transition: 'background 0.3s'
          },
          '&::-webkit-scrollbar-thumb:hover': {
            background: 'rgba(79, 6, 42, 0.4)',
          },
          // Para Firefox
          scrollbarWidth: 'thin',
          scrollbarColor: 'rgba(79, 6, 42, 0.2) transparent',
        }}
      >
        {chatHistory.length === 0 ? (
          <Box 
            sx={{ 
              display: 'flex', 
              flexDirection: 'column', 
              alignItems: 'center', 
              justifyContent: 'center',
              height: '100%',
              p: 4,
              // Mover el conjunto ligeramente hacia arriba
              mt: { xs: 0, sm: -5, md: -8 }
            }}
          >
            {/* Contenedor tabular para logo y texto con animación */}
            <Fade in={showWelcome} timeout={1000}>
              <Box>
                <Grid 
                  container 
                  spacing={2} 
                  alignItems="center" 
                  justifyContent="center"
                  sx={{ mb: 3 }}
                >
                  <Grid item xs={12} sm="auto" sx={{ textAlign: 'center' }}>
                    <Zoom in={showWelcome} timeout={800}>
                      <Box 
                        component="img" 
                        src={logoImage} 
                        alt="AgentIA Logo"
                        sx={{ 
                          height: 60,
                          maxWidth: '100%',
                          filter: 'drop-shadow(0 2px 4px rgba(0,0,0,0.1))'  // Sombra sutil
                        }}
                      />
                    </Zoom>
                  </Grid>
                  <Grid item xs={12} sm="auto">
                    <Typography 
                      variant="h4" 
                      color="primary.dark" 
                      align="center" 
                      fontWeight="500" 
                      sx={{ 
                        ml: { sm: 2 },
                        fontSize: {
                          xs: '1.8rem',
                          sm: '2.2rem',
                          md: '2.2rem'
                        },
                        textShadow: '0 1px 2px rgba(0,0,0,0.05)'  // Sombra sutil en el texto
                      }}
                    >
                      ¿Listo para hablar de compliance?
                    </Typography>
                  </Grid>
                </Grid>
                
                {/* Línea decorativa con animación */}
                <Fade in={showWelcome} timeout={1500} style={{ transitionDelay: '500ms' }}>
                  <Box 
                    sx={{ 
                      width: '80px', 
                      height: '3px', 
                      background: 'linear-gradient(to right, transparent, rgba(79, 6, 42, 0.7), transparent)', 
                      borderRadius: '2px',
                      mx: 'auto',
                      mb: 4
                    }} 
                  />
                </Fade>
                
                {/* Pequeño texto descriptivo */}
                <Fade in={showWelcome} timeout={1500} style={{ transitionDelay: '700ms' }}>
                  <Typography 
                    variant="body1" 
                    color="text.secondary" 
                    align="center" 
                    sx={{ 
                      mt: 2, 
                      opacity: 0.8,
                      maxWidth: '600px',
                      mx: 'auto'
                    }}
                  >
                    Consulte cualquier duda normativa o regulatoria
                  </Typography>
                </Fade>
              </Box>
            </Fade>
          </Box>
        ) : (
          <Box sx={{ width: '100%' }}>
            {chatHistory.map((msg, index) => (
              <ChatMessage 
                key={index} 
                message={msg.text} 
                isUser={msg.isUser}
                onViewReport={handleViewReport}
              />
            ))}
          </Box>
        )}
        
        {isLoading && (
          <Box sx={{ display: 'flex', justifyContent: 'flex-start', mb: 2 }}>
            <Box
              sx={{
                display: 'flex',
                p: 2,
                borderRadius: '16px',
                bgcolor: 'grey.100',
                alignItems: 'center',
                maxWidth: '80%'
              }}
            >
              <Box className="typing-indicator" sx={{ mx: 2 }}>
                <span></span>
                <span></span>
                <span></span>
              </Box>
            </Box>
          </Box>
        )}
        
        <div ref={messagesEndRef} />
      </Box>
      
      {/* Área de confirmación de documento cargado - compacta */}
      <Collapse in={showDocumentUploader && uploadedDocuments.length > 0}>
        <Box sx={{ 
          p: 2, 
          borderTop: '1px solid rgba(0,0,0,0.1)',
          backgroundColor: 'rgba(79, 6, 42, 0.02)'
        }}>
          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <Box sx={{ display: 'flex', alignItems: 'center' }}>
              <AnalyticsIcon sx={{ mr: 1, fontSize: '1.2rem', color: '#4F062A' }} />
              <Box>
                <Typography variant="subtitle2" sx={{ 
                  color: '#4F062A',
                  fontWeight: 600,
                  lineHeight: 1.2
                }}>
                  Análisis GAP activado
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  {uploadedDocuments[0]?.name} cargado correctamente
                </Typography>
              </Box>
            </Box>
            <IconButton
              size="small"
              onClick={() => {
                setUploadedDocuments([]);
                setIsGapAnalysisMode(false);
                setShowDocumentUploader(false);
              }}
              sx={{ color: 'text.secondary' }}
            >
              <DeleteIcon fontSize="small" />
            </IconButton>
          </Box>
        </Box>
      </Collapse>

      {/* Área de entrada - fijada en la parte inferior */}
      <Box sx={{ flexShrink: 0 }}>
        <ChatInputArea 
          onSendMessage={handleSubmitWithDocuments}
          isLoading={isLoading}
          onToggleDocuments={handleToggleDocumentUploader}
          hasDocuments={uploadedDocuments.length > 0}
        />
      </Box>
      
      {/* Panel de previsualización de documentos */}
      <DocxPreviewPanel
        open={previewOpen}
        onClose={handleClosePreview}
        reportPath={previewReport?.path}
        reportTitle={previewReport?.title}
      />
    </Box>
  );
};

export default ChatInterface;