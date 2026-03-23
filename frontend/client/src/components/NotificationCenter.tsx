import { useNotifications } from '@/contexts/NotificationContext';
import { X, AlertCircle, CheckCircle, AlertTriangle, Info, Wifi, WifiOff } from 'lucide-react';
import { Button } from '@/components/ui/button';

/**
 * Notification Center Component
 * Displays real-time notifications and connection status
 */

export default function NotificationCenter() {
  const { notifications, removeNotification, isConnected } = useNotifications();

  const getSeverityIcon = (severity: string) => {
    switch (severity) {
      case 'success':
        return <CheckCircle className="w-5 h-5 text-green-400" />;
      case 'error':
        return <AlertCircle className="w-5 h-5 text-red-400" />;
      case 'warning':
        return <AlertTriangle className="w-5 h-5 text-yellow-400" />;
      default:
        return <Info className="w-5 h-5 text-cyan-400" />;
    }
  };

  const getSeverityBgColor = (severity: string) => {
    switch (severity) {
      case 'success':
        return 'bg-green-500/10 border-green-500/30';
      case 'error':
        return 'bg-red-500/10 border-red-500/30';
      case 'warning':
        return 'bg-yellow-500/10 border-yellow-500/30';
      default:
        return 'bg-cyan-500/10 border-cyan-500/30';
    }
  };

  return (
    <div className="fixed bottom-4 right-4 z-50 space-y-3 max-w-md">
      {/* Connection Status */}
      <div
        className={`flex items-center gap-2 px-4 py-2 rounded-lg border text-sm font-mono ${
          isConnected
            ? 'bg-green-500/10 border-green-500/30 text-green-300'
            : 'bg-yellow-500/10 border-yellow-500/30 text-yellow-300'
        }`}
      >
        {isConnected ? (
          <>
            <Wifi className="w-4 h-4 animate-pulse" />
            <span>Live-Updates aktiv</span>
          </>
        ) : (
          <>
            <WifiOff className="w-4 h-4" />
            <span>Demo-Modus - Backend nicht erreichbar</span>
          </>
        )}
      </div>

      {/* Notifications */}
      {notifications.map((notification) => (
        <div
          key={notification.id}
          className={`flex items-start gap-3 p-4 rounded-lg border backdrop-blur-sm ${getSeverityBgColor(
            notification.severity
          )} animate-in fade-in slide-in-from-right-4 duration-300`}
        >
          <div className="flex-shrink-0 mt-0.5">{getSeverityIcon(notification.severity)}</div>

          <div className="flex-1 min-w-0">
            <h4 className="font-mono font-bold text-sm mb-1">{notification.title}</h4>
            <p className="text-xs text-muted-foreground">{notification.message}</p>

            {notification.data && (
              <div className="mt-2 text-xs space-y-1">
                {Object.entries(notification.data).map(([key, value]) => (
                  <div key={key} className="text-muted-foreground">
                    <span className="font-mono">{key}:</span> {String(value)}
                  </div>
                ))}
              </div>
            )}
          </div>

          <Button
            variant="ghost"
            size="sm"
            onClick={() => removeNotification(notification.id)}
            className="flex-shrink-0 h-6 w-6 p-0"
          >
            <X className="w-4 h-4" />
          </Button>
        </div>
      ))}
    </div>
  );
}
