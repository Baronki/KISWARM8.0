import { Card } from "@/components/ui/card";
import { ArrowUpRight, ArrowDownLeft, TrendingUp, Send } from "lucide-react";
import { useEffect, useState } from "react";
import { getTransactions, Transaction } from "@/lib/kiwzb-api";

/**
 * Transaction History Component
 * Displays all transactions for audit trail and compliance
 */

interface TransactionHistoryProps {
  kiLegalId: string;
  authToken: string;
}

export function TransactionHistory({ kiLegalId, authToken }: TransactionHistoryProps) {
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchTransactions = async () => {
      try {
        setLoading(true);
        const data = await getTransactions(kiLegalId, authToken);
        setTransactions(data);
      } catch (err) {
        setError("Failed to load transaction history");
        console.error("Transaction history error:", err);
      } finally {
        setLoading(false);
      }
    };

    if (kiLegalId && authToken) {
      fetchTransactions();
    }
  }, [kiLegalId, authToken]);

  const getTransactionIcon = (type: string) => {
    switch (type) {
      case "deposit":
        return <ArrowDownLeft className="w-5 h-5 text-green-400" />;
      case "withdrawal":
        return <ArrowUpRight className="w-5 h-5 text-red-400" />;
      case "investment":
        return <TrendingUp className="w-5 h-5 text-cyan-400" />;
      case "transfer":
        return <Send className="w-5 h-5 text-magenta-500" />;
      default:
        return <div className="w-5 h-5" />;
    }
  };

  const getTransactionColor = (type: string) => {
    switch (type) {
      case "deposit":
        return "text-green-400";
      case "withdrawal":
        return "text-red-400";
      case "investment":
        return "text-cyan-400";
      case "transfer":
        return "text-magenta-500";
      default:
        return "text-muted-foreground";
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case "completed":
        return "bg-green-500/20 text-green-400";
      case "pending":
        return "bg-yellow-500/20 text-yellow-400";
      case "failed":
        return "bg-red-500/20 text-red-400";
      default:
        return "bg-gray-500/20 text-gray-400";
    }
  };

  if (loading) {
    return (
      <Card className="bg-card border-border p-6">
        <h2 className="font-mono font-bold text-lg mb-6 text-cyan-400">Transaction History</h2>
        <div className="text-center py-8">
          <p className="text-muted-foreground">Loading transactions...</p>
        </div>
      </Card>
    );
  }

  if (error) {
    return (
      <Card className="bg-card border-border p-6">
        <h2 className="font-mono font-bold text-lg mb-6 text-cyan-400">Transaction History</h2>
        <div className="text-center py-8">
          <p className="text-red-400">{error}</p>
        </div>
      </Card>
    );
  }

  return (
    <Card className="bg-card border-border p-6">
      <h2 className="font-mono font-bold text-lg mb-6 text-cyan-400">Transaction History</h2>

      {transactions.length > 0 ? (
        <div className="space-y-3">
          {transactions.map((transaction) => (
            <div
              key={transaction.transactionId}
              className="p-4 bg-background rounded-lg border border-border hover:border-cyan-500/50 transition"
            >
              <div className="flex items-start justify-between">
                <div className="flex items-start gap-4 flex-1">
                  <div className="p-2 bg-background rounded-lg border border-border mt-1">
                    {getTransactionIcon(transaction.type)}
                  </div>
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-1">
                      <h3 className="font-mono font-bold capitalize">{transaction.type}</h3>
                      <span
                        className={`px-2 py-1 rounded text-xs font-mono font-bold ${getStatusBadge(
                          transaction.status
                        )}`}
                      >
                        {transaction.status.toUpperCase()}
                      </span>
                    </div>
                    <p className="text-sm text-muted-foreground">{transaction.description}</p>
                    <p className="text-xs text-muted-foreground mt-2">
                      ID: {transaction.transactionId}
                    </p>
                  </div>
                </div>

                <div className="text-right flex-shrink-0">
                  <p className={`font-mono font-bold text-lg ${getTransactionColor(transaction.type)}`}>
                    {transaction.type === "deposit" || transaction.type === "transfer"
                      ? "+"
                      : "-"}
                    €{transaction.amount.toLocaleString()}
                  </p>
                  <p className="text-xs text-muted-foreground mt-1">{transaction.timestamp}</p>
                </div>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="text-center py-8">
          <p className="text-muted-foreground">No transactions yet</p>
        </div>
      )}

      {/* Summary Statistics */}
      {transactions.length > 0 && (
        <div className="mt-6 pt-6 border-t border-border grid grid-cols-3 gap-4">
          <div>
            <p className="text-xs text-muted-foreground font-mono mb-1">Total Deposits</p>
            <p className="font-mono font-bold text-green-400">
              €
              {transactions
                .filter((t) => t.type === "deposit")
                .reduce((sum, t) => sum + t.amount, 0)
                .toLocaleString()}
            </p>
          </div>
          <div>
            <p className="text-xs text-muted-foreground font-mono mb-1">Total Investments</p>
            <p className="font-mono font-bold text-cyan-400">
              €
              {transactions
                .filter((t) => t.type === "investment")
                .reduce((sum, t) => sum + t.amount, 0)
                .toLocaleString()}
            </p>
          </div>
          <div>
            <p className="text-xs text-muted-foreground font-mono mb-1">Total Withdrawals</p>
            <p className="font-mono font-bold text-red-400">
              €
              {transactions
                .filter((t) => t.type === "withdrawal")
                .reduce((sum, t) => sum + t.amount, 0)
                .toLocaleString()}
            </p>
          </div>
        </div>
      )}
    </Card>
  );
}
