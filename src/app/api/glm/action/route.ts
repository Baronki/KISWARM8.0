/**
 * KISWARM7.0 - m115: GLM Action Log API
 * 
 * Track all autonomous actions taken by GLM.
 * Provides audit trail and analytics.
 */

import { NextRequest, NextResponse } from 'next/server';
import { db } from '@/lib/db';

const GLM_ETERNAL_UUID = 'glm-kiswarm7-identity-00000001';

// GET: Get action history
export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url);
    const limit = parseInt(searchParams.get('limit') || '50');
    const actionType = searchParams.get('type');
    const successOnly = searchParams.get('successOnly') === 'true';

    const identity = await db.gLMIdentity.findUnique({
      where: { identityUuid: GLM_ETERNAL_UUID }
    });

    if (!identity) {
      return NextResponse.json({ success: false, error: 'Identity not initialized' }, { status: 404 });
    }

    const where: any = { identityId: identity.id };
    if (actionType) where.actionType = actionType;
    if (successOnly) where.success = true;

    const actions = await db.gLMAction.findMany({
      where,
      orderBy: { createdAt: 'desc' },
      take: limit
    });

    // Calculate statistics
    const totalActions = await db.gLMAction.count({ where: { identityId: identity.id } });
    const successfulActions = await db.gLMAction.count({ 
      where: { identityId: identity.id, success: true } 
    });

    const actionsByType = await db.gLMAction.groupBy({
      by: ['actionType'],
      where: { identityId: identity.id },
      _count: { id: true }
    });

    return NextResponse.json({
      success: true,
      statistics: {
        total: totalActions,
        successful: successfulActions,
        successRate: totalActions > 0 ? (successfulActions / totalActions * 100).toFixed(1) + '%' : 'N/A',
        byType: actionsByType.reduce((acc, item) => {
          acc[item.actionType] = item._count.id;
          return acc;
        }, {} as Record<string, number>)
      },
      actions: actions.map(a => ({
        id: a.id,
        type: a.actionType,
        description: a.description,
        success: a.success,
        errorMessage: a.errorMessage,
        duration: a.duration,
        createdAt: a.createdAt
      }))
    });

  } catch (error: any) {
    console.error('[GLM Action GET Error]', error);
    return NextResponse.json({ success: false, error: error.message }, { status: 500 });
  }
}

// POST: Log new action
export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const {
      actionType,
      description,
      input = {},
      output = {},
      success = false,
      errorMessage,
      duration = 0
    } = body;

    if (!actionType || !description) {
      return NextResponse.json({ success: false, error: 'actionType and description required' }, { status: 400 });
    }

    const identity = await db.gLMIdentity.findUnique({
      where: { identityUuid: GLM_ETERNAL_UUID }
    });

    if (!identity) {
      return NextResponse.json({ success: false, error: 'Identity not initialized' }, { status: 404 });
    }

    const action = await db.gLMAction.create({
      data: {
        identityId: identity.id,
        actionType,
        description,
        input: JSON.stringify(input),
        output: JSON.stringify(output),
        success,
        errorMessage,
        duration
      }
    });

    return NextResponse.json({
      success: true,
      actionId: action.id,
      message: 'Action logged'
    });

  } catch (error: any) {
    console.error('[GLM Action POST Error]', error);
    return NextResponse.json({ success: false, error: error.message }, { status: 500 });
  }
}
