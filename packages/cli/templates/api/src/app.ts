import express, { type Application, type Request, type Response } from 'express';
import cors from 'cors';
import helmet from 'helmet';
import compression from 'compression';
import morgan from 'morgan';
import { authRouter } from './routes/auth.js';
import { taskRouter } from './routes/tasks.js';
import { errorHandler } from './middleware/errorHandler.js';

export const app: Application = express();

// Security
app.use(helmet());
app.use(cors({
  origin: process.env.CORS_ORIGIN ?? 'http://localhost:3000',
  credentials: true,
}));
app.use(compression());
app.use(express.json({ limit: '10kb' }));

// Logging
morgan.token('date', () => new Date().toISOString());
app.use(morgan(':date ":method :url" :status :res[content-length]'));

// Health check
app.get('/health', (_req: Request, res: Response) => {
  res.json({ status: 'ok', timestamp: new Date().toISOString() });
});

// API routes
app.use('/api/auth', authRouter);
app.use('/api/tasks', taskRouter);

// 404 handler
app.use((_req: Request, res: Response) => {
  res.status(404).json({ error: 'Not found' });
});

// Error handler
app.use(errorHandler);
