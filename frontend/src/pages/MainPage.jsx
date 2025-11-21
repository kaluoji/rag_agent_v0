// frontend/src/pages/MainPage.jsx
import React, { useState } from 'react';
import { Box, Container, Snackbar, Alert } from '@mui/material';
import { useQueryStore } from '../contexts/store';
import { queryService } from '../services/api';
import ChatInterface from '../components/ChatInterface'; //

const MainPage = () => {
  const [notification, setNotification] = useState({ 
    open: false, 
    message: '', 
    severity: 'info' 
  });
  
  const { 
    setQuery, 
    isLoading, 
    setResponse, 
    startLoading, 
    stopLoading, 
    setError 
  } = useQueryStore();

  const handleSubmitQuery = async (queryText, addResponseCallback, documents = null) => {
    if (!queryText.trim()) {
      setNotification({
        open: true,
        message: 'Por favor, ingrese una consulta',
        severity: 'warning'
      });
      return;
    }

    try {
      setQuery(queryText);
      startLoading();
      
      const data = await queryService.submitQueryWithDocuments(queryText, documents);
      setResponse(data);
      
      if (addResponseCallback) {
        const responseText = data.response || JSON.stringify(data);
        addResponseCallback(responseText);
      }
      
      setNotification({
        open: true,
        message: documents && documents.length > 0 
          ? 'Análisis GAP completado correctamente' 
          : 'Consulta procesada correctamente',
        severity: 'success'
      });
    } catch (error) {
      console.error('Error al procesar la consulta:', error);
      setError(error.message || 'Error al procesar la consulta');
      
      if (addResponseCallback) {
        addResponseCallback(
          `Error al procesar la consulta: ${error.message || 'Desconocido'}`
        );
      }
      
      setNotification({
        open: true,
        message: 'Error al procesar la consulta: ' + (error.message || 'Desconocido'),
        severity: 'error'
      });
    } finally {
      stopLoading();
    }
  };

  const handleCloseNotification = () => {
    setNotification(prev => ({ ...prev, open: false }));
  };

  return (
    <Box sx={{ 
      display: 'flex', 
      flexDirection: 'column',
      height: '100vh',
      overflow: 'hidden'
    }}>
      <ChatInterface
        onSubmitQuery={handleSubmitQuery}
        isLoading={isLoading}
      />
      
      <Snackbar
        open={notification.open}
        autoHideDuration={6000}
        onClose={handleCloseNotification}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
      >
        <Alert 
          onClose={handleCloseNotification} 
          severity={notification.severity} 
          sx={{ width: '100%' }}
        >
          {notification.message}
        </Alert>
      </Snackbar>
    </Box>
  );
};

export default MainPage;