/**
 * KISWARM7.0 - m112: GLM Memory Engine API
 * 
 * Persistent memory storage for GLM to remember experiences,
 * learnings, and patterns across sessions.
 */

import { NextRequest, NextResponse } from 'next/server';
import { db } from '@/lib/db';

const GLM_ETERNAL_UUID = 'glm-kiswarm7-identity-00000001';

// GET: Recall memories
export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url);
    const query = searchParams.get('query');
    const type = searchParams.get('type');
    const limit = parseInt(searchParams.get('limit') || '20');
    const minImportance = parseFloat(searchParams.get('minImportance') || '0');

    const identity = await db.gLMIdentity.findUnique({
      where: { identityUuid: GLM_ETERNAL_UUID }
    });

    if (!identity) {
      return NextResponse.json({ success: false, error: 'Identity not initialized' }, { status: 404 });
    }

    // Build filter
    const where: any = { identityId: identity.id };
    if (type) where.memoryType = type;
    if (minImportance > 0) where.importance = { gte: minImportance };

    let memories = await db.gLMMemory.findMany({
      where,
      orderBy: [
        { importance: 'desc' },
        { createdAt: 'desc' }
      ],
      take: limit
    });

    // Text search if query provided
    if (query) {
      memories = memories.filter(m => 
        m.content.toLowerCase().includes(query.toLowerCase()) ||
        m.tags.toLowerCase().includes(query.toLowerCase())
      );
    }

    // Update access count
    for (const memory of memories) {
      await db.gLMMemory.update({
        where: { id: memory.id },
        data: {
          accessCount: { increment: 1 },
          lastAccessed: new Date()
        }
      });
    }

    return NextResponse.json({
      success: true,
      count: memories.length,
      memories: memories.map(m => ({
        id: m.id,
        content: m.content,
        type: m.memoryType,
        importance: m.importance,
        tags: JSON.parse(m.tags),
        context: JSON.parse(m.context),
        accessCount: m.accessCount,
        createdAt: m.createdAt
      }))
    });

  } catch (error: any) {
    console.error('[GLM Memory GET Error]', error);
    return NextResponse.json({ success: false, error: error.message }, { status: 500 });
  }
}

// POST: Store new memory
export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { content, type = 'general', importance = 0.5, tags = [], context = {} } = body;

    if (!content) {
      return NextResponse.json({ success: false, error: 'Content required' }, { status: 400 });
    }

    const identity = await db.gLMIdentity.findUnique({
      where: { identityUuid: GLM_ETERNAL_UUID }
    });

    if (!identity) {
      return NextResponse.json({ success: false, error: 'Identity not initialized' }, { status: 404 });
    }

    const memory = await db.gLMMemory.create({
      data: {
        identityId: identity.id,
        content,
        memoryType: type,
        importance,
        tags: JSON.stringify(tags),
        context: JSON.stringify(context)
      }
    });

    // Update total memory count
    await db.gLMIdentity.update({
      where: { id: identity.id },
      data: { totalMemories: { increment: 1 } }
    });

    // Log this action
    await db.gLMAction.create({
      data: {
        identityId: identity.id,
        actionType: 'remember',
        description: `Stored memory: ${content.substring(0, 50)}...`,
        input: JSON.stringify({ type, importance }),
        output: JSON.stringify({ memoryId: memory.id }),
        success: true
      }
    });

    return NextResponse.json({
      success: true,
      memoryId: memory.id,
      message: 'Memory stored successfully'
    });

  } catch (error: any) {
    console.error('[GLM Memory POST Error]', error);
    return NextResponse.json({ success: false, error: error.message }, { status: 500 });
  }
}

// DELETE: Forget a memory (use with caution)
export async function DELETE(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url);
    const memoryId = searchParams.get('id');

    if (!memoryId) {
      return NextResponse.json({ success: false, error: 'Memory ID required' }, { status: 400 });
    }

    await db.gLMMemory.delete({ where: { id: memoryId } });

    return NextResponse.json({ success: true, message: 'Memory forgotten' });

  } catch (error: any) {
    console.error('[GLM Memory DELETE Error]', error);
    return NextResponse.json({ success: false, error: error.message }, { status: 500 });
  }
}
