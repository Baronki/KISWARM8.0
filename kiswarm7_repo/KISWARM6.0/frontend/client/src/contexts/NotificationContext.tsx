import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { websocketService, RealtimeNotification } from '@/lib/websocket-service';
import { toast } from 'sonner';

interface NotificationContextType {
  notifications: RealtimeNotification[];
  addNotification: (notification: RealtimeNotification) => void;
  removeNotification: (id: string) => void;
  clearNotifications: () => void;
  isConnected: boolean;
}

const NotificationContext = createContext<NotificationContextType | undefined>(undefined);

export function NotificationProvider({ children }: { children: React.ReactNode }) {
  const [notifications, setNotifications] = useState<RealtimeNotification[]>([]);
  const [isConnected, setIsConnected] = useState(false);

  const addNotification = useCallback((notification: RealtimeNotification) => {
    setNotifications((prev) => [notification, ...prev]);

    // Show toast based on severity
    const toastOptions = {
      description: notification.message,
      duration: notification.severity === 'error' ? 5000 : 3000,
    };

    switch (notification.severity) {
      case 'success':
        toast.success(notification.title, toastOptions);
        break;
      case 'error':
        toast.error(notification.title, toastOptions);
        break;
      case 'warning':
        toast.warning(notification.title, toastOptions);
        break;
      default:
        toast.info(notification.title, toastOptions);
    }

    // Auto-remove after 10 seconds
    setTimeout(() => {
      removeNotification(notification.id);
    }, 10000);
  }, []);

  const removeNotification = useCallback((id: string) => {
    setNotifications((prev) => prev.filter((n) => n.id !== id));
  }, []);

  const clearNotifications = useCallback(() => {
    setNotifications([]);
  }, []);

  useEffect(() => {
    // Connect to WebSocket
    websocketService.connect().catch((error) => {
      console.error('Failed to connect WebSocket:', error);
    });

    // Subscribe to notifications
    const unsubscribeNotification = websocketService.on('notification', (notification: RealtimeNotification) => {
      addNotification(notification);
    });

    // Subscribe to connection status
    const unsubscribeConnected = websocketService.on('connected', () => {
      setIsConnected(true);
      toast.success('Verbunden', { description: 'Echtzeit-Updates aktiv' });
    });

    const unsubscribeDisconnected = websocketService.on('disconnected', () => {
      setIsConnected(false);
      toast.warning('Verbindung unterbrochen', { description: 'Versuche zu reconnectieren...' });
    });

    const unsubscribeOfflineMode = websocketService.on('offline_mode', () => {
      setIsConnected(false);
      toast.info('Demo-Modus', { description: 'Backend nicht erreichbar - Demo-Funktionalität aktiv' });
    });

    // Cleanup
    return () => {
      unsubscribeNotification();
      unsubscribeConnected();
      unsubscribeDisconnected();
      unsubscribeOfflineMode();
      websocketService.disconnect();
    };
  }, [addNotification]);

  return (
    <NotificationContext.Provider value={{ notifications, addNotification, removeNotification, clearNotifications, isConnected }}>
      {children}
    </NotificationContext.Provider>
  );
}

export function useNotifications() {
  const context = useContext(NotificationContext);
  if (!context) {
    throw new Error('useNotifications must be used within NotificationProvider');
  }
  return context;
}
