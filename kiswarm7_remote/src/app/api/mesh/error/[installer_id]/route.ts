/**
 * Legacy Mesh API - Error Report Endpoint
 * 
 * Handles error reports from installers and provides automatic fixes
 * Route: /api/mesh/error/[installer_id]
 */

import { NextRequest, NextResponse } from 'next/server';

// Global registry
declare global {
  var meshInstallers: Map<string, any>;
}

// Knowledge base of common fixes
const FIXES_DB: Record<string, {
  title: string;
  fix_type: string;
  commands: string[];
  explanation: string;
}> = {
  "ImportError": {
    title: "Install Missing Python Module",
    fix_type: "pip_install",
    commands: ["pip install flask flask-cors structlog requests pyngrok"],
    explanation: "Install the missing Python module using pip",
  },
  "ModuleNotFoundError": {
    title: "Install Missing Module",
    fix_type: "pip_install",
    commands: ["pip install -r requirements.txt"],
    explanation: "Install all required dependencies from requirements.txt",
  },
  "IndentationError": {
    title: "Fix Python Indentation",
    fix_type: "code_fix",
    commands: ["# Check the file for mixed tabs and spaces", "python -m py_compile <file>"],
    explanation: "Python indentation error - check for mixed tabs and spaces",
  },
  "ConnectionRefusedError": {
    title: "Service Not Running",
    fix_type: "service_start",
    commands: ["# Check if the service is running", "lsof -i :5002 || echo 'Port 5002 is free'"],
    explanation: "The target service is not running. Start it first.",
  },
  "TimeoutError": {
    title: "Connection Timeout",
    fix_type: "wait_retry",
    commands: ["# Wait and retry", "sleep 30 && retry_command"],
    explanation: "The connection timed out. The service might be starting up.",
  },
  "PermissionError": {
    title: "Permission Denied",
    fix_type: "permission_fix",
    commands: ["chmod +x <file>", "# or run with sudo if appropriate"],
    explanation: "File permission error. Make the file executable or adjust permissions.",
  },
  "FileNotFoundError": {
    title: "Missing File",
    fix_type: "file_check",
    commands: ["ls -la <path>", "# Check if the file exists and path is correct"],
    explanation: "The requested file was not found. Check the path.",
  },
  "OSError": {
    title: "System Error",
    fix_type: "system_check",
    commands: ["# Check system resources", "df -h", "free -m"],
    explanation: "Operating system error. Check disk space and memory.",
  },
};

export async function POST(
  request: NextRequest,
  { params }: { params: Promise<{ installer_id: string }> }
) {
  try {
    const { installer_id } = await params;
    const body = await request.json();
    
    const errorType = body.error_type || 'UnknownError';
    const errorMessage = body.error_message || 'No message provided';
    const moduleName = body.module || 'unknown';
    
    // Get or create installer record
    if (!globalThis.meshInstallers) {
      globalThis.meshInstallers = new Map();
    }
    
    let installer = globalThis.meshInstallers.get(installer_id);
    if (!installer) {
      installer = {
        installer_id,
        installer_name: installer_id,
        environment: 'unknown',
        registered_at: new Date().toISOString(),
        last_seen: new Date().toISOString(),
        status: 'error',
        progress: [],
        errors: [],
      };
      globalThis.meshInstallers.set(installer_id, installer);
    }
    
    // Record the error
    const errorRecord = {
      error_type: errorType,
      error_message: errorMessage,
      module: moduleName,
      timestamp: new Date().toISOString(),
    };
    installer.errors.push(errorRecord);
    installer.status = 'error';
    
    console.log(`[MESH] ❌ Error from ${installer_id}:`);
    console.log(`[MESH]    Type: ${errorType}`);
    console.log(`[MESH]    Message: ${errorMessage}`);
    console.log(`[MESH]    Module: ${moduleName}`);
    
    // Look up fix
    const fix = FIXES_DB[errorType] || {
      title: "General Fix",
      fix_type: "manual",
      commands: ["# No automatic fix available - requires manual intervention"],
      explanation: `Unknown error type: ${errorType}`,
    };
    
    // Generate specific fix based on error message
    let specificFix = { ...fix };
    
    if (errorMessage.includes('flask_cors')) {
      specificFix = {
        title: "Install flask-cors",
        fix_type: "pip_install",
        commands: ["pip install flask-cors"],
        explanation: "The flask-cors package is required for cross-origin support",
      };
    } else if (errorMessage.includes('structlog')) {
      specificFix = {
        title: "Install structlog",
        fix_type: "pip_install",
        commands: ["pip install structlog"],
        explanation: "The structlog package is required for structured logging",
      };
    } else if (errorMessage.includes('pyngrok')) {
      specificFix = {
        title: "Install pyngrok",
        fix_type: "pip_install",
        commands: ["pip install pyngrok"],
        explanation: "The pyngrok package is required for tunnel creation",
      };
    } else if (errorMessage.includes('ollama')) {
      specificFix = {
        title: "Install Ollama",
        fix_type: "ollama_install",
        commands: [
          "curl -fsSL https://ollama.com/install.sh | sh",
          "ollama serve &",
        ],
        explanation: "Ollama is required for local AI model deployment",
      };
    }
    
    return NextResponse.json({
      status: "error_recorded",
      installer_id,
      error_id: `err_${Date.now().toString(36)}`,
      fix: specificFix,
      message: "Error recorded. Fix suggestion provided.",
      support_available: true,
    });
    
  } catch (error) {
    return NextResponse.json({
      status: "error",
      message: error instanceof Error ? error.message : "Unknown error",
    }, { status: 500 });
  }
}

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ installer_id: string }> }
) {
  const { installer_id } = await params;
  
  if (!globalThis.meshInstallers) {
    globalThis.meshInstallers = new Map();
  }
  
  const installer = globalThis.meshInstallers.get(installer_id);
  
  if (!installer) {
    return NextResponse.json({
      status: "not_found",
      errors: [],
    });
  }
  
  return NextResponse.json({
    installer_id,
    total_errors: installer.errors.length,
    errors: installer.errors,
  });
}
