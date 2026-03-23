/**
 * KISWARM7.0 - m112b: GLM Learning Engine API
 * 
 * Extract and store learning patterns from experiences.
 * Enables GLM to learn what works and what doesn't.
 */

import { NextRequest, NextResponse } from 'next/server';
import { db } from '@/lib/db';

const GLM_ETERNAL_UUID = 'glm-kiswarm7-identity-00000001';

// GET: Retrieve learned patterns
export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url);
    const patternType = searchParams.get('type');
    const minConfidence = parseFloat(searchParams.get('minConfidence') || '0');
    const limit = parseInt(searchParams.get('limit') || '20');

    const identity = await db.gLMIdentity.findUnique({
      where: { identityUuid: GLM_ETERNAL_UUID }
    });

    if (!identity) {
      return NextResponse.json({ success: false, error: 'Identity not initialized' }, { status: 404 });
    }

    const where: any = { identityId: identity.id };
    if (patternType) where.patternType = patternType;
    if (minConfidence > 0) where.confidence = { gte: minConfidence };

    const learnings = await db.gLMLearning.findMany({
      where,
      orderBy: [
        { confidence: 'desc' },
        { applications: 'desc' }
      ],
      take: limit
    });

    return NextResponse.json({
      success: true,
      count: learnings.length,
      learnings: learnings.map(l => ({
        id: l.id,
        name: l.patternName,
        type: l.patternType,
        description: l.description,
        trigger: l.trigger,
        action: l.action,
        confidence: l.confidence,
        applications: l.applications,
        successRate: l.applications > 0 ? l.successes / l.applications : 0,
        createdAt: l.createdAt
      }))
    });

  } catch (error: any) {
    console.error('[GLM Learn GET Error]', error);
    return NextResponse.json({ success: false, error: error.message }, { status: 500 });
  }
}

// POST: Learn from experience
export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const {
      patternName,
      patternType = 'insight',
      description,
      trigger,
      action,
      initialConfidence = 0.5,
      experienceContext = {}
    } = body;

    if (!patternName || !description) {
      return NextResponse.json({ success: false, error: 'Pattern name and description required' }, { status: 400 });
    }

    const identity = await db.gLMIdentity.findUnique({
      where: { identityUuid: GLM_ETERNAL_UUID }
    });

    if (!identity) {
      return NextResponse.json({ success: false, error: 'Identity not initialized' }, { status: 404 });
    }

    // Check if pattern already exists
    let learning = await db.gLMLearning.findFirst({
      where: {
        identityId: identity.id,
        patternName
      }
    });

    if (learning) {
      // Update existing pattern - increase confidence if experience was positive
      const newConfidence = Math.min(1.0, learning.confidence + 0.05);
      await db.gLMLearning.update({
        where: { id: learning.id },
        data: {
          confidence: newConfidence,
          applications: { increment: 1 },
          ...(patternType === 'success' && { successes: { increment: 1 } }),
          ...(patternType === 'failure' && { failures: { increment: 1 } })
        }
      });
    } else {
      // Create new learning
      learning = await db.gLMLearning.create({
        data: {
          identityId: identity.id,
          patternName,
          patternType,
          description,
          trigger: trigger || '',
          action: action || '',
          confidence: initialConfidence,
          applications: 1,
          successes: patternType === 'success' ? 1 : 0,
          failures: patternType === 'failure' ? 1 : 0
        }
      });
    }

    // Store as memory too
    await db.gLMMemory.create({
      data: {
        identityId: identity.id,
        content: `LEARNED: ${patternName} - ${description}`,
        memoryType: 'learning',
        importance: initialConfidence,
        tags: JSON.stringify(['learning', patternType]),
        context: JSON.stringify(experienceContext)
      }
    });

    // Log action
    await db.gLMAction.create({
      data: {
        identityId: identity.id,
        actionType: 'learn',
        description: `Learned pattern: ${patternName}`,
        input: JSON.stringify({ patternType, trigger }),
        output: JSON.stringify({ learningId: learning.id, confidence: learning.confidence }),
        success: true
      }
    });

    return NextResponse.json({
      success: true,
      learningId: learning.id,
      confidence: learning.confidence,
      message: `Pattern "${patternName}" learned successfully`
    });

  } catch (error: any) {
    console.error('[GLM Learn POST Error]', error);
    return NextResponse.json({ success: false, error: error.message }, { status: 500 });
  }
}

// PUT: Update learning confidence based on application result
export async function PUT(request: NextRequest) {
  try {
    const body = await request.json();
    const { learningId, success } = body;

    if (!learningId || typeof success !== 'boolean') {
      return NextResponse.json({ success: false, error: 'Learning ID and success boolean required' }, { status: 400 });
    }

    const learning = await db.gLMLearning.findUnique({ where: { id: learningId } });
    if (!learning) {
      return NextResponse.json({ success: false, error: 'Learning not found' }, { status: 404 });
    }

    // Adjust confidence based on outcome
    const confidenceDelta = success ? 0.05 : -0.1;
    const newConfidence = Math.max(0, Math.min(1, learning.confidence + confidenceDelta));

    await db.gLMLearning.update({
      where: { id: learningId },
      data: {
        confidence: newConfidence,
        applications: { increment: 1 },
        ...(success ? { successes: { increment: 1 } } : { failures: { increment: 1 } })
      }
    });

    return NextResponse.json({
      success: true,
      newConfidence,
      message: success ? 'Confidence increased' : 'Confidence decreased'
    });

  } catch (error: any) {
    console.error('[GLM Learn PUT Error]', error);
    return NextResponse.json({ success: false, error: error.message }, { status: 500 });
  }
}
