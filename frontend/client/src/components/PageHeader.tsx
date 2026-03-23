import { ChevronLeft } from "lucide-react";

/**
 * Page Header Component
 * Consistent header with back navigation for all sub-pages
 */

interface PageHeaderProps {
  title: string;
  subtitle?: string;
  showBackButton?: boolean;
  onBack?: () => void;
}

export default function PageHeader({ title, subtitle, showBackButton = true, onBack }: PageHeaderProps) {
  const handleBack = () => {
    if (onBack) {
      onBack();
    } else {
      window.history.back();
    }
  };

  return (
    <div className="pt-24 pb-12 border-b border-border">
      <div className="container max-w-7xl">
        {showBackButton && (
          <button
            onClick={handleBack}
            className="flex items-center gap-2 text-sm text-muted-foreground hover:text-cyan-400 transition mb-6"
          >
            <ChevronLeft className="w-4 h-4" />
            Zurück zur Startseite
          </button>
        )}
        <h1 className="text-5xl md:text-6xl font-mono font-bold mb-4 glow-cyan">{title}</h1>
        {subtitle && <p className="text-lg text-muted-foreground">{subtitle}</p>}
      </div>
    </div>
  );
}
