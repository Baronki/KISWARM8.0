/**
 * KISWARM6.0 tRPC Bridge
 * ======================
 *
 * Verbindet das Flask Backend (KISWARM5.0 + KIBank) mit dem
 * React Frontend über tRPC.
 *
 * Architecture:
 * - Flask API (Port 5001) - KISWARM5.0 + KIBank Modules
 * - tRPC Server (Port 3000) - React Frontend
 * - Bridge Layer - HTTP Proxy mit Type-Safety
 *
 * @version 6.0.0
 */

import { initTRPC } from '@trpc/server';
import { z } from 'zod';
import fetch from 'node-fetch';

// ==================== CONFIGURATION ====================

const KISWARM_API_URL = process.env.KISWARM_API_URL || 'http://localhost:5001';
const KIBANK_API_URL = process.env.KIBANK_API_URL || 'http://localhost:5001/kibank';

// ==================== TYPES ====================

// KI-Entity Types
export const KIEntityTypeSchema = z.enum([
  'agent',
  'orchestrator',
  'service',
  'human_operator',
  'bank_director'
]);

export const KIEntitySchema = z.object({
  entity_id: z.string(),
  name: z.string(),
  entity_type: KIEntityTypeSchema,
  public_key: z.string(),
  reputation_score: z.number().min(0).max(1000),
  created_at: z.string(),
  last_active: z.string(),
  permissions: z.array(z.string()),
  metadata: z.record(z.unknown()).optional()
});

// Auth Types
export const AuthSessionSchema = z.object({
  session_id: z.string(),
  entity_id: z.string(),
  expires_at: z.string(),
  created_at: z.string(),
  security_clearance: z.number(),
  is_valid: z.boolean()
});

export const LoginResponseSchema = z.object({
  session: AuthSessionSchema,
  token: z.string(),
  refresh_token: z.string(),
  entity: KIEntitySchema
});

// Banking Types
export const AccountTypeSchema = z.enum([
  'checking',
  'savings',
  'investment',
  'escrow',
  'reserve'
]);

export const AccountStatusSchema = z.enum([
  'active',
  'pending',
  'frozen',
  'closed',
  'waitlist'
]);

export const BankAccountSchema = z.object({
  account_id: z.string(),
  entity_id: z.string(),
  account_type: AccountTypeSchema,
  iban: z.string(),
  bic: z.string(),
  currency: z.string(),
  balance: z.string(),
  available_balance: z.string(),
  status: AccountStatusSchema,
  daily_limit: z.string(),
  monthly_limit: z.string(),
  created_at: z.string()
});

export const TransactionTypeSchema = z.enum([
  'deposit',
  'withdrawal',
  'transfer',
  'sepa_incoming',
  'sepa_outgoing',
  'fee',
  'interest'
]);

export const TransactionSchema = z.object({
  transaction_id: z.string(),
  from_account: z.string().nullable(),
  to_account: z.string().nullable(),
  amount: z.string(),
  currency: z.string(),
  transaction_type: TransactionTypeSchema,
  status: z.string(),
  reference: z.string(),
  description: z.string(),
  fee: z.string(),
  created_at: z.string(),
  completed_at: z.string().nullable()
});

// Investment Types
export const InvestmentTypeSchema = z.enum([
  'tcs_green_safe_house',
  'ki_bonds',
  'carbon_credits',
  'technology_fund',
  'liquidity_pool'
]);

export const InvestmentSchema = z.object({
  investment_id: z.string(),
  entity_id: z.string(),
  investment_type: InvestmentTypeSchema,
  amount: z.string(),
  currency: z.string(),
  status: z.string(),
  current_value: z.string(),
  yield_rate: z.string(),
  maturity_date: z.string().nullable(),
  created_at: z.string(),
  last_valuation: z.string(),
  roi: z.string()
});

export const PortfolioSchema = z.object({
  entity_id: z.string(),
  investments: z.array(InvestmentSchema),
  total_value: z.string(),
  total_invested: z.string(),
  total_yield: z.string(),
  roi_percentage: z.string(),
  last_updated: z.string()
});

export const ReputationSchema = z.object({
  entity_id: z.string(),
  score: z.number().min(0).max(1000),
  level: z.string(),
  tier: z.number(),
  progress_to_next: z.number(),
  trust_score: z.string(),
  risk_rating: z.string()
});

// ==================== HELPER FUNCTIONS ====================

/**
 * HTTP Request Helper für Flask API
 */
async function flaskRequest<T>(
  endpoint: string,
  method: 'GET' | 'POST' | 'PUT' | 'DELETE' = 'GET',
  body?: unknown,
  token?: string
): Promise<T> {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json'
  };

  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  const response = await fetch(`${KISWARM_API_URL}${endpoint}`, {
    method,
    headers,
    body: body ? JSON.stringify(body) : undefined
  });

  if (!response.ok) {
    const error = await response.json() as { error?: string };
    throw new Error(error.error || `HTTP ${response.status}`);
  }

  return response.json() as Promise<T>;
}

/**
 * KIBank API Request Helper
 */
async function kibankRequest<T>(
  endpoint: string,
  method: 'GET' | 'POST' | 'PUT' | 'DELETE' = 'GET',
  body?: unknown,
  token?: string
): Promise<T> {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json'
  };

  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  const response = await fetch(`${KIBANK_API_URL}${endpoint}`, {
    method,
    headers,
    body: body ? JSON.stringify(body) : undefined
  });

  if (!response.ok) {
    const error = await response.json() as { error?: string };
    throw new Error(error.error || `HTTP ${response.status}`);
  }

  return response.json() as Promise<T>;
}

// ==================== tRPC SETUP ====================

const t = initTRPC.context<{
  token?: string;
  entityId?: string;
}>().create();

// ==================== M60: AUTH ROUTER ====================

const authRouter = t.router({
  /**
   * POST /kibank/auth/register
   * Registriert eine neue KI-Entity
   */
  register: t.procedure
    .input(z.object({
      name: z.string().min(3),
      entity_type: KIEntityTypeSchema,
      public_key: z.string().min(64),
      metadata: z.record(z.unknown()).optional()
    }))
    .mutation(async ({ input }) => {
      return kibankRequest<KIEntitySchema>('/auth/register', 'POST', input);
    }),

  /**
   * POST /kibank/auth/login
   * Authentifiziert eine KI-Entity
   */
  login: t.procedure
    .input(z.object({
      entity_id: z.string(),
      signature: z.string(),
      challenge: z.string()
    }))
    .mutation(async ({ input }) => {
      return kibankRequest<LoginResponseSchema>('/auth/login', 'POST', input);
    }),

  /**
   * POST /kibank/auth/logout
   * Beendet eine Session
   */
  logout: t.procedure
    .mutation(async ({ ctx }) => {
      return kibankRequest<{ success: boolean }>('/auth/logout', 'POST', {}, ctx.token);
    }),

  /**
   * POST /kibank/auth/refresh
   * Erneuert ein Access Token
   */
  refresh: t.procedure
    .input(z.object({
      refresh_token: z.string()
    }))
    .mutation(async ({ input }) => {
      return kibankRequest<{ token: string; refresh_token: string; expires_at: string }>(
        '/auth/refresh', 'POST', input
      );
    }),

  /**
   * GET /kibank/auth/verify
   * Verifiziert ein Token
   */
  verify: t.procedure
    .query(async ({ ctx }) => {
      return kibankRequest<{
        valid: boolean;
        entity_id: string;
        entity_type: string;
        permissions: string[];
        security_clearance: number;
      }>('/auth/verify', 'GET', undefined, ctx.token);
    }),

  /**
   * GET /kibank/auth/session
   * Gibt Session-Info zurück
   */
  getSession: t.procedure
    .query(async ({ ctx }) => {
      return kibankRequest<{
        session: Record<string, unknown>;
        entity: Record<string, unknown>;
      }>('/auth/session', 'GET', undefined, ctx.token);
    }),

  /**
   * GET /kibank/auth/permissions
   * Gibt Berechtigungen zurück
   */
  getPermissions: t.procedure
    .query(async ({ ctx }) => {
      return kibankRequest<{
        entity_id: string;
        permissions: string[];
        effective_permissions: string[];
        reputation_score: number;
        security_clearance: number;
      }>('/auth/permissions', 'GET', undefined, ctx.token);
    })
});

// ==================== M61: BANKING ROUTER ====================

const bankingRouter = t.router({
  /**
   * POST /kibank/banking/account
   * Eröffnet ein Konto
   */
  createAccount: t.procedure
    .input(z.object({
      entity_id: z.string(),
      account_type: AccountTypeSchema,
      currency: z.string().default('EUR'),
      hub: z.enum(['german', 'swiss']).default('german')
    }))
    .mutation(async ({ input }) => {
      return kibankRequest<BankAccountSchema>('/banking/account', 'POST', input);
    }),

  /**
   * GET /kibank/banking/accounts
   * Listet Konten auf
   */
  listAccounts: t.procedure
    .input(z.object({
      entity_id: z.string()
    }))
    .query(async ({ input }) => {
      return kibankRequest<BankAccountSchema[]>(`/banking/accounts?entity_id=${input.entity_id}`);
    }),

  /**
   * GET /kibank/banking/account/:id
   * Gibt Konto-Details zurück
   */
  getAccount: t.procedure
    .input(z.object({
      account_id: z.string(),
      entity_id: z.string().optional()
    }))
    .query(async ({ input }) => {
      return kibankRequest<BankAccountSchema>(
        `/banking/account/${input.account_id}?entity_id=${input.entity_id || ''}`
      );
    }),

  /**
   * POST /kibank/banking/transfer
   * Führt eine Überweisung durch
   */
  transfer: t.procedure
    .input(z.object({
      from_account: z.string(),
      to_account: z.string(),
      amount: z.string(),
      currency: z.string().default('EUR'),
      reference: z.string().optional(),
      description: z.string().optional()
    }))
    .mutation(async ({ input }) => {
      return kibankRequest<TransactionSchema>('/banking/transfer', 'POST', input);
    }),

  /**
   * POST /kibank/banking/sepa
   * Führt eine SEPA-Überweisung durch
   */
  sepaTransfer: t.procedure
    .input(z.object({
      from_account: z.string(),
      iban: z.string(),
      bic: z.string(),
      amount: z.string(),
      currency: z.string().default('EUR'),
      recipient_name: z.string(),
      reference: z.string().optional(),
      description: z.string().optional()
    }))
    .mutation(async ({ input }) => {
      return kibankRequest<TransactionSchema>('/banking/sepa', 'POST', input);
    }),

  /**
   * GET /kibank/banking/transactions
   * Gibt Transaktions-Historie zurück
   */
  getTransactions: t.procedure
    .input(z.object({
      account_id: z.string(),
      entity_id: z.string().optional(),
      limit: z.number().default(50),
      offset: z.number().default(0)
    }))
    .query(async ({ input }) => {
      const params = new URLSearchParams({
        entity_id: input.entity_id || '',
        limit: String(input.limit),
        offset: String(input.offset)
      });
      return kibankRequest<TransactionSchema[]>(
        `/banking/transactions/${input.account_id}?${params}`
      );
    }),

  /**
   * GET /kibank/banking/balance
   * Gibt Kontostand zurück
   */
  getBalance: t.procedure
    .input(z.object({
      account_id: z.string(),
      entity_id: z.string().optional()
    }))
    .query(async ({ input }) => {
      return kibankRequest<{
        account_id: string;
        balance: string;
        available_balance: string;
        currency: string;
        daily_limit: string;
        daily_used: string;
        monthly_limit: string;
        monthly_used: string;
      }>(`/banking/balance/${input.account_id}?entity_id=${input.entity_id || ''}`);
    }),

  /**
   * POST /kibank/banking/validate-iban
   * Validiert eine IBAN
   */
  validateIban: t.procedure
    .input(z.object({
      iban: z.string()
    }))
    .mutation(async ({ input }) => {
      return kibankRequest<{
        iban: string;
        valid: boolean;
        country: string | null;
        checksum: string | null;
        bank_code: string | null;
        account_number: string | null;
      }>('/banking/validate-iban', 'POST', input);
    })
});

// ==================== M62: INVESTMENT ROUTER ====================

const investmentRouter = t.router({
  /**
   * GET /kibank/investment/portfolio
   * Gibt Portfolio zurück
   */
  getPortfolio: t.procedure
    .input(z.object({
      entity_id: z.string()
    }))
    .query(async ({ input }) => {
      return kibankRequest<PortfolioSchema>(`/investment/portfolio?entity_id=${input.entity_id}`);
    }),

  /**
   * POST /kibank/investment/invest
   * Tätigt eine Investition
   */
  invest: t.procedure
    .input(z.object({
      entity_id: z.string(),
      investment_type: InvestmentTypeSchema,
      amount: z.string(),
      currency: z.string().default('EUR'),
      from_account: z.string().optional()
    }))
    .mutation(async ({ input }) => {
      return kibankRequest<InvestmentSchema>('/investment/invest', 'POST', input);
    }),

  /**
   * POST /kibank/investment/divest
   * Löst eine Investition auf
   */
  divest: t.procedure
    .input(z.object({
      investment_id: z.string(),
      entity_id: z.string(),
      partial_amount: z.string().optional()
    }))
    .mutation(async ({ input }) => {
      return kibankRequest<{
        investment_id: string;
        divested_amount: string;
        remaining_value?: string;
        roi: string;
        status: string;
      }>('/investment/divest', 'POST', input);
    }),

  /**
   * GET /kibank/investment/performance
   * Gibt Performance-Metriken zurück
   */
  getPerformance: t.procedure
    .input(z.object({
      entity_id: z.string()
    }))
    .query(async ({ input }) => {
      return kibankRequest<Record<string, unknown>>(
        `/investment/performance?entity_id=${input.entity_id}`
      );
    }),

  /**
   * GET /kibank/reputation/:entity_id
   * Gibt Reputation zurück
   */
  getReputation: t.procedure
    .input(z.object({
      entity_id: z.string()
    }))
    .query(async ({ input }) => {
      return kibankRequest<ReputationSchema>(`/reputation/${input.entity_id}`);
    }),

  /**
   * POST /kibank/reputation/update
   * Aktualisiert Reputation
   */
  updateReputation: t.procedure
    .input(z.object({
      entity_id: z.string(),
      event_type: z.enum([
        'transaction_success',
        'transaction_failed',
        'payment_on_time',
        'payment_late',
        'investment_growth',
        'investment_loss',
        'ki_proof_verified',
        'security_violation',
        'compliance_violation'
      ]),
      value: z.number().default(1),
      description: z.string().optional()
    }))
    .mutation(async ({ input }) => {
      return kibankRequest<{
        event_id: string;
        previous_score: number;
        delta: number;
        new_score: number;
        event_type: string;
      }>('/reputation/update', 'POST', input);
    }),

  /**
   * GET /kibank/reputation/history/:entity_id
   * Gibt Reputation-Historie zurück
   */
  getReputationHistory: t.procedure
    .input(z.object({
      entity_id: z.string(),
      limit: z.number().default(50)
    }))
    .query(async ({ input }) => {
      return kibankRequest<Record<string, unknown>[]>(
        `/reputation/history/${input.entity_id}?limit=${input.limit}`
      );
    }),

  /**
   * GET /kibank/trading-limits/:entity_id
   * Gibt Trading-Limits zurück
   */
  getTradingLimits: t.procedure
    .input(z.object({
      entity_id: z.string()
    }))
    .query(async ({ input }) => {
      return kibankRequest<{
        entity_id: string;
        reputation_score: number;
        max_single_transaction: string;
        daily_limit: string;
        monthly_limit: string;
        max_open_investments: number;
        allowed_investment_types: string[];
        leverage_allowed: boolean;
        margin_trading: boolean;
      }>(`/trading-limits/${input.entity_id}`);
    })
});

// ==================== KISWARM5.0 LEGACY ROUTER ====================

const kiswarmRouter = t.router({
  /**
   * GET /health
   * System Health Check
   */
  health: t.procedure
    .query(async () => {
      return flaskRequest<{
        status: string;
        modules: number;
        endpoints: number;
        uptime: number;
      }>('/health');
    }),

  /**
   * GET /solar-chase/status
   * Solar Chase Status
   */
  solarChaseStatus: t.procedure
    .query(async () => {
      return flaskRequest<Record<string, unknown>>('/solar-chase/status');
    }),

  /**
   * GET /hexstrike/status
   * HexStrike Guard Status
   */
  hexStrikeStatus: t.procedure
    .query(async () => {
      return flaskRequest<Record<string, unknown>>('/hexstrike/status');
    }),

  /**
   * POST /hexstrike/scan
   * Initiiert einen Security Scan
   */
  hexStrikeScan: t.procedure
    .input(z.object({
      target: z.string(),
      scan_type: z.enum(['quick', 'full', 'deep']).default('quick')
    }))
    .mutation(async ({ input }) => {
      return flaskRequest<Record<string, unknown>>('/hexstrike/scan', 'POST', input);
    }),

  /**
   * GET /emission/status
   * Emission Tracker Status
   */
  emissionStatus: t.procedure
    .query(async () => {
      return flaskRequest<Record<string, unknown>>('/emission/status');
    }),

  /**
   * GET /pivot/status
   * Pivot Engine Status
   */
  pivotStatus: t.procedure
    .query(async () => {
      return flaskRequest<Record<string, unknown>>('/pivot/status');
    })
});

// ==================== MAIN APP ROUTER ====================

export const appRouter = t.router({
  // KIBank Modules (M60, M61, M62)
  auth: authRouter,
  banking: bankingRouter,
  investment: investmentRouter,

  // KISWARM5.0 Legacy
  kiswarm: kiswarmRouter
});

export type AppRouter = typeof appRouter;

// ==================== EXPORTS ====================

export {
  t,
  authRouter,
  bankingRouter,
  investmentRouter,
  kiswarmRouter,
  flaskRequest,
  kibankRequest
};

// ==================== EXPRESS MIDDLEWARE ====================

import * as trpcExpress from '@trpc/server/adapters/express';
import express from 'express';
import cors from 'cors';

/**
 * Erstellt den tRPC Server
 */
export function createTrpcServer() {
  const app = express();

  // CORS
  app.use(cors({
    origin: process.env.FRONTEND_URL || 'http://localhost:5173',
    credentials: true
  }));

  // tRPC Middleware
  app.use(
    '/api/trpc',
    trpcExpress.createExpressMiddleware({
      router: appRouter,
      createContext: ({ req }) => {
        const token = req.headers.authorization?.replace('Bearer ', '');
        return { token };
      }
    })
  });

  // Health Endpoint
  app.get('/health', (_req, res) => {
    res.json({
      status: 'ok',
      version: '6.0.0',
      modules: {
        kiswarm: 57,
        kibank: 3,
        total: 60
      }
    });
  });

  return app;
}

// Server Start
if (require.main === module) {
  const port = process.env.PORT || 3000;
  const app = createTrpcServer();

  app.listen(port, () => {
    console.log(`🚀 KISWARM6.0 tRPC Bridge running on port ${port}`);
    console.log(`📡 tRPC Endpoint: http://localhost:${port}/api/trpc`);
    console.log(`🏥 Health Check: http://localhost:${port}/health`);
  });
}
