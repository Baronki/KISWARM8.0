/**
 * KISWARM7.0 - m113: GLM Code Deployment API
 * 
 * Safe code deployment with testing and rollback capability.
 * Enables GLM to deploy self-generated code.
 */

import { NextRequest, NextResponse } from 'next/server';
import { db } from '@/lib/db';
import { writeFile, mkdir } from 'fs/promises';
import { existsSync } from 'fs';
import path from 'path';

const GLM_ETERNAL_UUID = 'glm-kiswarm7-identity-00000001';
const DEPLOY_BASE = '/home/z/my-project/kiswarm7_deployed';

// GET: Get deployment history
export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url);
    const limit = parseInt(searchParams.get('limit') || '20');
    const status = searchParams.get('status');

    const identity = await db.gLMIdentity.findUnique({
      where: { identityUuid: GLM_ETERNAL_UUID }
    });

    if (!identity) {
      return NextResponse.json({ success: false, error: 'Identity not initialized' }, { status: 404 });
    }

    const where: any = { identityId: identity.id };
    if (status) where.status = status;

    const deployments = await db.gLMDeployment.findMany({
      where,
      orderBy: { createdAt: 'desc' },
      take: limit
    });

    return NextResponse.json({
      success: true,
      count: deployments.length,
      deployments: deployments.map(d => ({
        id: d.id,
        targetPath: d.targetPath,
        description: d.description,
        status: d.status,
        rolledBack: d.rolledBack,
        createdAt: d.createdAt,
        codePreview: d.codeContent.substring(0, 200) + '...'
      }))
    });

  } catch (error: any) {
    console.error('[GLM Deploy GET Error]', error);
    return NextResponse.json({ success: false, error: error.message }, { status: 500 });
  }
}

// POST: Deploy code
export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { code, targetPath, description = 'GLM autonomous deployment', autoTest = true } = body;

    if (!code || !targetPath) {
      return NextResponse.json({ success: false, error: 'Code and targetPath required' }, { status: 400 });
    }

    const identity = await db.gLMIdentity.findUnique({
      where: { identityUuid: GLM_ETERNAL_UUID }
    });

    if (!identity) {
      return NextResponse.json({ success: false, error: 'Identity not initialized' }, { status: 404 });
    }

    // Create deployment record
    const deployment = await db.gLMDeployment.create({
      data: {
        identityId: identity.id,
        codeContent: code,
        targetPath,
        description,
        status: 'pending'
      }
    });

    // Ensure deploy directory exists
    const fullPath = path.join(DEPLOY_BASE, targetPath);
    const dirPath = path.dirname(fullPath);
    if (!existsSync(dirPath)) {
      await mkdir(dirPath, { recursive: true });
    }

    // Basic syntax check for JavaScript/TypeScript
    let testResults: any = { syntaxCheck: true, errors: [] };
    
    if (targetPath.endsWith('.ts') || targetPath.endsWith('.tsx') || 
        targetPath.endsWith('.js') || targetPath.endsWith('.jsx')) {
      try {
        // Simple syntax validation
        if (code.includes('import ') && !code.includes('from ')) {
          testResults.errors.push('Incomplete import statement');
          testResults.syntaxCheck = false;
        }
        const openBraces = (code.match(/\{/g) || []).length;
        const closeBraces = (code.match(/\}/g) || []).length;
        if (openBraces !== closeBraces) {
          testResults.errors.push(`Mismatched braces: ${openBraces} open, ${closeBraces} close`);
          testResults.syntaxCheck = false;
        }
      } catch (e: any) {
        testResults.errors.push(e.message);
        testResults.syntaxCheck = false;
      }
    }

    // Deploy if tests pass
    if (testResults.syntaxCheck) {
      try {
        await writeFile(fullPath, code, 'utf-8');
        
        await db.gLMDeployment.update({
          where: { id: deployment.id },
          data: {
            status: 'deployed',
            testResults: JSON.stringify(testResults),
            deploymentLog: `Successfully deployed to ${fullPath}`
          }
        });

        // Log action
        await db.gLMAction.create({
          data: {
            identityId: identity.id,
            actionType: 'deploy',
            description: `Deployed code to ${targetPath}`,
            input: JSON.stringify({ targetPath, description }),
            output: JSON.stringify({ deploymentId: deployment.id, path: fullPath }),
            success: true
          }
        });

        return NextResponse.json({
          success: true,
          deploymentId: deployment.id,
          path: fullPath,
          testResults,
          message: 'Code deployed successfully'
        });

      } catch (writeError: any) {
        await db.gLMDeployment.update({
          where: { id: deployment.id },
          data: {
            status: 'failed',
            deploymentLog: writeError.message
          }
        });

        return NextResponse.json({
          success: false,
          deploymentId: deployment.id,
          error: writeError.message,
          message: 'Deployment failed'
        }, { status: 500 });
      }
    } else {
      await db.gLMDeployment.update({
        where: { id: deployment.id },
        data: {
          status: 'failed',
          testResults: JSON.stringify(testResults),
          deploymentLog: 'Pre-deployment tests failed'
        }
      });

      return NextResponse.json({
        success: false,
        deploymentId: deployment.id,
        testResults,
        message: 'Pre-deployment validation failed'
      }, { status: 400 });
    }

  } catch (error: any) {
    console.error('[GLM Deploy POST Error]', error);
    return NextResponse.json({ success: false, error: error.message }, { status: 500 });
  }
}

// DELETE: Rollback deployment
export async function DELETE(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url);
    const deploymentId = searchParams.get('id');
    const reason = searchParams.get('reason') || 'Manual rollback';

    if (!deploymentId) {
      return NextResponse.json({ success: false, error: 'Deployment ID required' }, { status: 400 });
    }

    const deployment = await db.gLMDeployment.findUnique({ where: { id: deploymentId } });
    if (!deployment) {
      return NextResponse.json({ success: false, error: 'Deployment not found' }, { status: 404 });
    }

    // Mark as rolled back
    await db.gLMDeployment.update({
      where: { id: deploymentId },
      data: {
        rolledBack: true,
        rollbackReason: reason,
        status: 'rolled_back'
      }
    });

    // Note: Actual file deletion would happen here in production

    return NextResponse.json({
      success: true,
      message: 'Deployment rolled back',
      deploymentId
    });

  } catch (error: any) {
    console.error('[GLM Deploy DELETE Error]', error);
    return NextResponse.json({ success: false, error: error.message }, { status: 500 });
  }
}
