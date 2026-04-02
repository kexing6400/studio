import { Router } from 'express';
import { z } from 'zod';
import { prisma } from '../lib/prisma.js';
import { authMiddleware, type AuthRequest } from '../middleware/auth.js';

export const taskRouter = Router();

taskRouter.use(authMiddleware);

const createTaskSchema = z.object({
  title: z.string().min(1).max(200),
  description: z.string().max(5000).optional(),
  priority: z.enum(['LOW', 'MEDIUM', 'HIGH', 'URGENT']).optional(),
  dueDate: z.string().datetime().optional(),
});

const updateTaskSchema = z.object({
  title: z.string().min(1).max(200).optional(),
  description: z.string().max(5000).optional().nullable(),
  status: z.enum(['TODO', 'IN_PROGRESS', 'IN_REVIEW', 'DONE']).optional(),
  priority: z.enum(['LOW', 'MEDIUM', 'HIGH', 'URGENT']).optional(),
  dueDate: z.string().datetime().optional().nullable(),
});

// GET /api/tasks
taskRouter.get('/', async (req: AuthRequest, res) => {
  try {
    const { status, priority } = req.query;

    const tasks = await prisma.task.findMany({
      where: {
        OR: [
          { authorId: req.userId },
          { assigneeId: req.userId },
        ],
        ...(status && { status: status as string }),
        ...(priority && { priority: priority as string }),
      },
      include: {
        author: { select: { id: true, name: true } },
        assignee: { select: { id: true, name: true } },
        _count: { select: { comments: true } },
      },
      orderBy: [{ priority: 'desc' }, { createdAt: 'desc' }],
    });

    res.json({ tasks });
  } catch (error) {
    console.error('Get tasks error:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
});

// POST /api/tasks
taskRouter.post('/', async (req: AuthRequest, res) => {
  try {
    const data = createTaskSchema.parse(req.body);
    const { title, description, priority, dueDate } = data;

    const task = await prisma.task.create({
      data: {
        title,
        description,
        priority: priority ?? 'MEDIUM',
        dueDate: dueDate ? new Date(dueDate) : null,
        authorId: req.userId ?? '',
      },
      include: {
        author: { select: { id: true, name: true } },
        assignee: { select: { id: true, name: true } },
      },
    });

    res.status(201).json({ task });
  } catch (error) {
    if (error instanceof z.ZodError) {
      return res.status(400).json({ error: 'Validation error', details: error.errors });
    }
    console.error('Create task error:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
});

// GET /api/tasks/:id
taskRouter.get('/:id', async (req: AuthRequest, res) => {
  try {
    const task = await prisma.task.findFirst({
      where: {
        id: req.params.id,
        OR: [{ authorId: req.userId }, { assigneeId: req.userId }],
      },
      include: {
        author: { select: { id: true, name: true } },
        assignee: { select: { id: true, name: true } },
        comments: {
          include: { author: { select: { id: true, name: true } } },
          orderBy: { createdAt: 'asc' },
        },
      },
    });

    if (!task) {
      return res.status(404).json({ error: 'Task not found' });
    }

    res.json({ task });
  } catch (error) {
    console.error('Get task error:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
});

// PATCH /api/tasks/:id
taskRouter.patch('/:id', async (req: AuthRequest, res) => {
  try {
    const data = updateTaskSchema.parse(req.body);
    const { dueDate, ...rest } = data;

    const existing = await prisma.task.findFirst({
      where: { id: req.params.id, authorId: req.userId },
    });

    if (!existing) {
      return res.status(404).json({ error: 'Task not found or access denied' });
    }

    const task = await prisma.task.update({
      where: { id: req.params.id },
      data: {
        ...rest,
        dueDate: dueDate ? new Date(dueDate) : dueDate === null ? null : undefined,
        completedAt: data.status === 'DONE' && existing.status !== 'DONE'
          ? new Date()
          : data.status !== 'DONE' && existing.status === 'DONE'
            ? null
            : undefined,
      },
      include: {
        author: { select: { id: true, name: true } },
        assignee: { select: { id: true, name: true } },
      },
    });

    res.json({ task });
  } catch (error) {
    if (error instanceof z.ZodError) {
      return res.status(400).json({ error: 'Validation error', details: error.errors });
    }
    console.error('Update task error:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
});

// DELETE /api/tasks/:id
taskRouter.delete('/:id', async (req: AuthRequest, res) => {
  try {
    const task = await prisma.task.findFirst({
      where: { id: req.params.id, authorId: req.userId },
    });

    if (!task) {
      return res.status(404).json({ error: 'Task not found or access denied' });
    }

    await prisma.task.delete({ where: { id: req.params.id } });
    res.status(204).send();
  } catch (error) {
    console.error('Delete task error:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
});
