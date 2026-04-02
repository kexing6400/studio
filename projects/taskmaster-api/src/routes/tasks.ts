import { Router } from 'express';
import { z } from 'zod';
import { prisma } from '../lib/prisma.js';
import { validate } from '../middleware/validate.js';
import { authMiddleware, type AuthRequest } from '../middleware/auth.js';
import { AppError } from '../types/index.js';

export const taskRouter = Router();

// All routes require authentication
taskRouter.use(authMiddleware);

const createTaskSchema = z.object({
  title: z.string().min(1).max(200),
  description: z.string().max(5000).optional(),
  priority: z.enum(['LOW', 'MEDIUM', 'HIGH', 'URGENT']).optional(),
  dueDate: z.string().datetime().optional(),
  assigneeId: z.string().optional(),
});

const updateTaskSchema = z.object({
  title: z.string().min(1).max(200).optional(),
  description: z.string().max(5000).optional().nullable(),
  status: z.enum(['TODO', 'IN_PROGRESS', 'IN_REVIEW', 'DONE']).optional(),
  priority: z.enum(['LOW', 'MEDIUM', 'HIGH', 'URGENT']).optional(),
  dueDate: z.string().datetime().optional().nullable(),
  assigneeId: z.string().optional().nullable(),
});

// GET /api/tasks
taskRouter.get('/', async (req: AuthRequest, res, next) => {
  try {
    const { status, priority, assignee } = req.query;

    const tasks = await prisma.task.findMany({
      where: {
        OR: [
          { authorId: req.userId },
          { assigneeId: req.userId },
        ],
        ...(status && { status: status as string }),
        ...(priority && { priority: priority as string }),
        ...(assignee === 'me' && { assigneeId: req.userId }),
      },
      include: {
        author: { select: { id: true, name: true, email: true } },
        assignee: { select: { id: true, name: true, email: true } },
        _count: { select: { comments: true } },
      },
      orderBy: [{ priority: 'desc' }, { createdAt: 'desc' }],
    });

    res.json({ tasks });
  } catch (error) {
    next(error);
  }
});

// POST /api/tasks
taskRouter.post('/', validate(createTaskSchema), async (req: AuthRequest, res, next) => {
  try {
    const { title, description, priority, dueDate, assigneeId } = req.body;

    // Validate assignee exists if provided
    if (assigneeId) {
      const assignee = await prisma.user.findUnique({ where: { id: assigneeId } });
      if (!assignee) {
        throw new AppError('Assignee not found', 404, 'USER_NOT_FOUND');
      }
    }

    const task = await prisma.task.create({
      data: {
        title,
        description,
        priority: priority ?? 'MEDIUM',
        dueDate: dueDate ? new Date(dueDate) : null,
        assigneeId: assigneeId ?? null,
        authorId: req.userId ?? '',
      },
      include: {
        author: { select: { id: true, name: true, email: true } },
        assignee: { select: { id: true, name: true, email: true } },
      },
    });

    res.status(201).json({ task });
  } catch (error) {
    next(error);
  }
});

// GET /api/tasks/:id
taskRouter.get('/:id', async (req: AuthRequest, res, next) => {
  try {
    const task = await prisma.task.findFirst({
      where: {
        id: req.params.id,
        OR: [
          { authorId: req.userId },
          { assigneeId: req.userId },
        ],
      },
      include: {
        author: { select: { id: true, name: true, email: true } },
        assignee: { select: { id: true, name: true, email: true } },
        comments: {
          include: {
            author: { select: { id: true, name: true } },
          },
          orderBy: { createdAt: 'asc' },
        },
      },
    });

    if (!task) {
      throw new AppError('Task not found', 404, 'TASK_NOT_FOUND');
    }

    res.json({ task });
  } catch (error) {
    next(error);
  }
});

// PATCH /api/tasks/:id
taskRouter.patch('/:id', validate(updateTaskSchema), async (req: AuthRequest, res, next) => {
  try {
    const { id } = req.params;
    const { dueDate, ...rest } = req.body;

    // Check ownership
    const existingTask = await prisma.task.findFirst({
      where: { id, authorId: req.userId },
    });

    if (!existingTask) {
      throw new AppError('Task not found or access denied', 404, 'TASK_NOT_FOUND');
    }

    const task = await prisma.task.update({
      where: { id },
      data: {
        ...rest,
        dueDate: dueDate ? new Date(dueDate) : dueDate === null ? null : undefined,
        completedAt: rest.status === 'DONE' && existingTask.status !== 'DONE'
          ? new Date()
          : rest.status !== 'DONE' && existingTask.status === 'DONE'
            ? null
            : undefined,
      },
      include: {
        author: { select: { id: true, name: true, email: true } },
        assignee: { select: { id: true, name: true, email: true } },
      },
    });

    res.json({ task });
  } catch (error) {
    next(error);
  }
});

// DELETE /api/tasks/:id
taskRouter.delete('/:id', async (req: AuthRequest, res, next) => {
  try {
    const { id } = req.params;

    // Check ownership
    const task = await prisma.task.findFirst({
      where: { id, authorId: req.userId },
    });

    if (!task) {
      throw new AppError('Task not found or access denied', 404, 'TASK_NOT_FOUND');
    }

    await prisma.task.delete({ where: { id } });

    res.status(204).send();
  } catch (error) {
    next(error);
  }
});

// POST /api/tasks/:id/comments
taskRouter.post('/:id/comments', async (req: AuthRequest, res, next) => {
  try {
    const { id } = req.params;
    const { content } = req.body;

    if (!content || typeof content !== 'string' || content.trim().length === 0) {
      throw new AppError('Comment content is required', 400, 'VALIDATION_ERROR');
    }

    // Check task access
    const task = await prisma.task.findFirst({
      where: {
        id,
        OR: [
          { authorId: req.userId },
          { assigneeId: req.userId },
        ],
      },
    });

    if (!task) {
      throw new AppError('Task not found or access denied', 404, 'TASK_NOT_FOUND');
    }

    const comment = await prisma.comment.create({
      data: {
        content: content.trim(),
        taskId: id,
        authorId: req.userId ?? '',
      },
      include: {
        author: { select: { id: true, name: true } },
      },
    });

    res.status(201).json({ comment });
  } catch (error) {
    next(error);
  }
});
