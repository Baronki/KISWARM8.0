import { useEffect, useState, useCallback } from 'react';
import { websocketService } from '@/lib/websocket-service';
import { useNotifications } from '@/contexts/NotificationContext';

/**
 * Hook for subscribing to real-time updates
 * Automatically handles connection and cleanup
 */

export interface OrderUpdate {
  orderId: string;
  status: 'pending' | 'confirmed' | 'processing' | 'shipped' | 'delivered' | 'cancelled';
  progress: number;
  message: string;
  timestamp: number;
}

export interface InvestmentUpdate {
  investmentId: string;
  status: 'pending' | 'active' | 'completed' | 'failed';
  currentValue: number;
  roi: number;
  message: string;
  timestamp: number;
}

export interface AccountActivity {
  activityId: string;
  type: 'deposit' | 'withdrawal' | 'investment' | 'transfer' | 'fee';
  amount: number;
  description: string;
  timestamp: number;
}

export function useOrderUpdates(orderId?: string) {
  const [orders, setOrders] = useState<OrderUpdate[]>([]);
  const { addNotification } = useNotifications();

  useEffect(() => {
    const unsubscribe = websocketService.on('order_update', (update: OrderUpdate) => {
      if (!orderId || update.orderId === orderId) {
        setOrders((prev) => {
          const existing = prev.find((o) => o.orderId === update.orderId);
          if (existing) {
            return prev.map((o) => (o.orderId === update.orderId ? update : o));
          }
          return [update, ...prev];
        });

        // Show notification
        addNotification({
          id: `order_${update.orderId}`,
          type: 'order_status',
          title: `Order ${update.orderId}`,
          message: update.message,
          timestamp: update.timestamp,
          data: { status: update.status, progress: update.progress },
          severity: update.status === 'cancelled' ? 'error' : 'info',
        });
      }
    });

    return unsubscribe;
  }, [orderId, addNotification]);

  return orders;
}

export function useInvestmentUpdates(investmentId?: string) {
  const [investments, setInvestments] = useState<InvestmentUpdate[]>([]);
  const { addNotification } = useNotifications();

  useEffect(() => {
    const unsubscribe = websocketService.on('investment_update', (update: InvestmentUpdate) => {
      if (!investmentId || update.investmentId === investmentId) {
        setInvestments((prev) => {
          const existing = prev.find((i) => i.investmentId === update.investmentId);
          if (existing) {
            return prev.map((i) => (i.investmentId === update.investmentId ? update : i));
          }
          return [update, ...prev];
        });

        // Show notification
        addNotification({
          id: `investment_${update.investmentId}`,
          type: 'investment_update',
          title: `Investment ${update.investmentId}`,
          message: update.message,
          timestamp: update.timestamp,
          data: { status: update.status, roi: update.roi, value: update.currentValue },
          severity: update.status === 'failed' ? 'error' : 'success',
        });
      }
    });

    return unsubscribe;
  }, [investmentId, addNotification]);

  return investments;
}

export function useAccountActivity() {
  const [activities, setActivities] = useState<AccountActivity[]>([]);
  const { addNotification } = useNotifications();

  useEffect(() => {
    const unsubscribe = websocketService.on('account_activity', (activity: AccountActivity) => {
      setActivities((prev) => [activity, ...prev]);

      // Show notification
      addNotification({
        id: `activity_${activity.activityId}`,
        type: 'account_activity',
        title: `Account Activity: ${activity.type}`,
        message: activity.description,
        timestamp: activity.timestamp,
        data: { amount: activity.amount, type: activity.type },
        severity: 'info',
      });
    });

    return unsubscribe;
  }, [addNotification]);

  return activities;
}

export function usePaymentConfirmation() {
  const [confirmations, setConfirmations] = useState<any[]>([]);
  const { addNotification } = useNotifications();

  useEffect(() => {
    const unsubscribe = websocketService.on('payment_confirmation', (confirmation: any) => {
      setConfirmations((prev) => [confirmation, ...prev]);

      // Show notification
      addNotification({
        id: `payment_${confirmation.transactionId}`,
        type: 'payment_confirmation',
        title: 'Zahlungsbestätigung',
        message: `Zahlung von ${confirmation.amount} EUR bestätigt`,
        timestamp: confirmation.timestamp,
        data: { transactionId: confirmation.transactionId, amount: confirmation.amount },
        severity: 'success',
      });
    });

    return unsubscribe;
  }, [addNotification]);

  return confirmations;
}

export function useSendOrderUpdate(orderId: string, status: string, progress: number, message: string) {
  const callback = useCallback(() => {
    websocketService.send('order_update', {
      orderId,
      status,
      progress,
      message,
      timestamp: Date.now(),
    });
  }, [orderId, status, progress, message]);

  return callback;
}

export function useSendInvestmentUpdate(investmentId: string, status: string, currentValue: number, roi: number, message: string) {
  const callback = useCallback(() => {
    websocketService.send('investment_update', {
      investmentId,
      status,
      currentValue,
      roi,
      message,
      timestamp: Date.now(),
    });
  }, [investmentId, status, currentValue, roi, message]);

  return callback;
}
