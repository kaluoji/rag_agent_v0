import type { RequestHandler } from './$types';

/**
 * POST /api/file - Upload file for analysis
 * GET /api/file - Download file
 * Proxy endpoints for file operations
 */

const API_BASE_URL = process.env.VITE_API_URL || 'http://localhost:8000';
const MAX_FILE_SIZE = 50 * 1024 * 1024; // 50MB
const ALLOWED_TYPES = ['application/pdf', 'application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'text/plain'];
const UPLOAD_TIMEOUT = 60000; // 60 seconds

/**
 * Handle POST request for file upload
 */
export const POST: RequestHandler = async ({ request }) => {
  try {
    const contentType = request.headers.get('content-type');

    if (!contentType || !contentType.includes('multipart/form-data')) {
      return new Response(
        JSON.stringify({
          error: 'Invalid content type',
          message: 'Content-Type must be multipart/form-data',
        }),
        {
          status: 400,
          headers: { 'Content-Type': 'application/json' },
        }
      );
    }

    // Parse form data
    let formData: FormData;
    try {
      formData = await request.formData();
    } catch (error) {
      return new Response(
        JSON.stringify({
          error: 'Invalid form data',
          message: 'Failed to parse form data',
          details: error instanceof Error ? error.message : 'Unknown error',
        }),
        {
          status: 400,
          headers: { 'Content-Type': 'application/json' },
        }
      );
    }

    // Get file from form data
    const file = formData.get('file');

    if (!file || !(file instanceof File)) {
      return new Response(
        JSON.stringify({
          error: 'Validation error',
          message: 'File field is required and must be a file',
        }),
        {
          status: 400,
          headers: { 'Content-Type': 'application/json' },
        }
      );
    }

    // Validate file size
    if (file.size > MAX_FILE_SIZE) {
      return new Response(
        JSON.stringify({
          error: 'File too large',
          message: `File size must not exceed ${MAX_FILE_SIZE / 1024 / 1024}MB`,
        }),
        {
          status: 413,
          headers: { 'Content-Type': 'application/json' },
        }
      );
    }

    // Validate file type
    if (!ALLOWED_TYPES.includes(file.type)) {
      return new Response(
        JSON.stringify({
          error: 'Invalid file type',
          message: `Allowed types: ${ALLOWED_TYPES.join(', ')}`,
        }),
        {
          status: 400,
          headers: { 'Content-Type': 'application/json' },
        }
      );
    }

    // Get optional sector
    const sector = formData.get('sector') as string | null;

    // Forward to backend
    const backendFormData = new FormData();
    backendFormData.append('file', file);
    if (sector) {
      backendFormData.append('sector', sector);
    }

    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), UPLOAD_TIMEOUT);

    try {
      const backendUrl = new URL('/api/upload', API_BASE_URL);
      const backendResponse = await fetch(backendUrl.toString(), {
        method: 'POST',
        body: backendFormData,
        signal: controller.signal,
      });

      clearTimeout(timeoutId);

      if (!backendResponse.ok) {
        const errorData = await backendResponse.json().catch(() => ({}));
        return new Response(
          JSON.stringify({
            error: 'Backend error',
            statusCode: backendResponse.status,
            message:
              errorData.message || `Backend returned status ${backendResponse.status}`,
            details: errorData.details || errorData.error,
          }),
          {
            status: backendResponse.status,
            headers: { 'Content-Type': 'application/json' },
          }
        );
      }

      const data = await backendResponse.json();
      return new Response(JSON.stringify(data), {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      });
    } catch (error) {
      clearTimeout(timeoutId);

      if (error instanceof Error) {
        if (error.name === 'AbortError') {
          return new Response(
            JSON.stringify({
              error: 'Upload timeout',
              message: 'File upload took too long. Please try again.',
              statusCode: 408,
            }),
            {
              status: 408,
              headers: { 'Content-Type': 'application/json' },
            }
          );
        }

        return new Response(
          JSON.stringify({
            error: 'Backend connection error',
            message: 'Failed to connect to upload service',
            details: error.message,
            statusCode: 503,
          }),
          {
            status: 503,
            headers: { 'Content-Type': 'application/json' },
          }
        );
      }

      throw error;
    }
  } catch (error) {
    console.error('Error in file upload API route:', error);
    return new Response(
      JSON.stringify({
        error: 'Internal server error',
        message: error instanceof Error ? error.message : 'Unknown error occurred',
        statusCode: 500,
      }),
      {
        status: 500,
        headers: { 'Content-Type': 'application/json' },
      }
    );
  }
};

/**
 * Handle GET request for file download
 */
export const GET: RequestHandler = async ({ url }) => {
  try {
    const fileId = url.searchParams.get('fileId');

    if (!fileId) {
      return new Response(
        JSON.stringify({
          error: 'Validation error',
          message: 'fileId query parameter is required',
        }),
        {
          status: 400,
          headers: { 'Content-Type': 'application/json' },
        }
      );
    }

    const backendUrl = new URL(`/api/files/${fileId}/download`, API_BASE_URL);
    const response = await fetch(backendUrl.toString(), {
      method: 'GET',
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      return new Response(
        JSON.stringify({
          error: 'Backend error',
          statusCode: response.status,
          message: errorData.message || `Backend returned status ${response.status}`,
        }),
        {
          status: response.status,
          headers: { 'Content-Type': 'application/json' },
        }
      );
    }

    // Stream file as blob
    const blob = await response.blob();
    const filename =
      response.headers
        .get('content-disposition')
        ?.split('filename=')[1]
        ?.replace(/"/g, '') || 'download';

    return new Response(blob, {
      status: 200,
      headers: {
        'Content-Type': blob.type,
        'Content-Disposition': `attachment; filename="${filename}"`,
        'Content-Length': blob.size.toString(),
      },
    });
  } catch (error) {
    console.error('Error in file download API route:', error);
    return new Response(
      JSON.stringify({
        error: 'Internal server error',
        message: error instanceof Error ? error.message : 'Unknown error occurred',
        statusCode: 500,
      }),
      {
        status: 500,
        headers: { 'Content-Type': 'application/json' },
      }
    );
  }
};

/**
 * Handle OPTIONS request for CORS preflight
 */
export const OPTIONS: RequestHandler = async () => {
  return new Response(null, {
    status: 204,
    headers: {
      'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type',
    },
  });
};
