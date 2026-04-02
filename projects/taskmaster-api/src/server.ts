import { PrismaClient } from '@prisma/client';
import { app } from './app.js';
import { logger } from './utils/logger.js';

const prisma = new PrismaClient();
const PORT = Number(process.env.PORT) || 3000;

async function bootstrap(): Promise<void> {
  try {
    // Test database connection
    await prisma.$connect();
    logger.info('Database connection established');

    // Graceful shutdown
    const shutdown = async (signal: string): Promise<void> => {
      logger.info(`${signal} received, shutting down gracefully`);
      await prisma.$disconnect();
      process.exit(0);
    };

    process.on('SIGTERM', () => shutdown('SIGTERM'));
    process.on('SIGINT', () => shutdown('SIGINT'));

    // Start server
    app.listen(PORT, () => {
      logger.info(`Server running on port ${PORT}`);
      logger.info(`Environment: ${process.env.NODE_ENV ?? 'development'}`);
    });
  } catch (error) {
    logger.error('Failed to start server', { error });
    process.exit(1);
  }
}

bootstrap();
