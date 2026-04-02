import express, { type Application, type Request, type Response } from 'express';
import cors from 'cors';
import helmet from 'helmet';
import compression from 'compression';
import morgan from 'morgan';

export const app: Application = express();

// Security
app.use(helmet());
app.use(cors());
app.use(compression());
app.use(express.json());

// Logging
morgan.token('date', () => new Date().toISOString());
app.use(morgan(':date ":method :url" :status :res[content-length]'));

// Health check
app.get('/health', (_req: Request, res: Response) => {
  res.json({ status: 'ok', timestamp: new Date().toISOString() });
});

// API routes here

// Error handler
app.use((err: Error, _req: Request, res: Response, _next: Function) => {
  console.error(err.stack);
  res.status(500).json({ error: 'Internal server error' });
});
