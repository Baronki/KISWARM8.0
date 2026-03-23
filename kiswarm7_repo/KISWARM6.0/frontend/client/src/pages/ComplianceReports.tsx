import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Download, FileText, Calendar, AlertCircle, CheckCircle, Clock } from "lucide-react";
import { useState, useEffect } from "react";
import { complianceReportGenerator, type ComplianceReport } from "@/lib/compliance-report-generator";
import { analyticsService } from "@/lib/analytics-service";

/**
 * Compliance Reports Management
 * Generate, view, and download daily and weekly compliance reports
 */

export default function ComplianceReports() {
  const [reports, setReports] = useState<ComplianceReport[]>([]);
  const [selectedReport, setSelectedReport] = useState<ComplianceReport | null>(null);
  const [generatingReport, setGeneratingReport] = useState<"daily" | "weekly" | null>(null);

  useEffect(() => {
    // Load sample reports
    const analyticsData = analyticsService.generateAnalyticsData();
    const dailyReport = complianceReportGenerator.generateReport(analyticsData, "daily");
    const weeklyReport = complianceReportGenerator.generateReport(analyticsData, "weekly");
    setReports([weeklyReport, dailyReport]);
  }, []);

  const handleGenerateReport = (type: "daily" | "weekly") => {
    setGeneratingReport(type);
    setTimeout(() => {
      const analyticsData = analyticsService.generateAnalyticsData();
      const newReport = complianceReportGenerator.generateReport(analyticsData, type);
      setReports([newReport, ...reports]);
      setGeneratingReport(null);
      setSelectedReport(newReport);
    }, 1000);
  };

  const handleDownloadReport = (report: ComplianceReport) => {
    complianceReportGenerator.downloadReportAsHTML(report);
  };

  return (
    <div className="min-h-screen bg-background text-foreground">
      {/* Header */}
      <div className="border-b border-border bg-card/30">
        <div className="container py-8">
          <h1 className="text-4xl md:text-5xl font-mono font-bold mb-4 glow-cyan">
            Compliance Reports
          </h1>
          <p className="text-muted-foreground">
            Automated daily and weekly compliance reports with audit trails and recommendations
          </p>
        </div>
      </div>

      {/* Main Content */}
      <div className="container py-12">
        <div className="grid md:grid-cols-3 gap-6">
          {/* Left: Report List */}
          <div className="md:col-span-2">
            {/* Generate Report Buttons */}
            <div className="mb-8 flex gap-4">
              <Button
                onClick={() => handleGenerateReport("daily")}
                disabled={generatingReport === "daily"}
                className="flex-1 bg-cyan-500 hover:bg-cyan-600 text-background font-mono neon-border"
              >
                {generatingReport === "daily" ? "Generating..." : "Generate Daily Report"}
              </Button>
              <Button
                onClick={() => handleGenerateReport("weekly")}
                disabled={generatingReport === "weekly"}
                className="flex-1 bg-magenta-600 hover:bg-magenta-700 text-background font-mono neon-border-magenta"
              >
                {generatingReport === "weekly" ? "Generating..." : "Generate Weekly Report"}
              </Button>
            </div>

            {/* Reports List */}
            <div className="space-y-4">
              {reports.map((report) => (
                <Card
                  key={report.id}
                  onClick={() => setSelectedReport(report)}
                  className={`bg-card border-cyan-500/30 hover:border-cyan-500 transition cursor-pointer neon-border p-6 ${
                    selectedReport?.id === report.id ? "border-cyan-500 bg-cyan-500/10" : ""
                  }`}
                >
                  <div className="flex items-start justify-between mb-3">
                    <div className="flex items-center gap-3">
                      <FileText className="w-5 h-5 text-cyan-400" />
                      <div>
                        <h3 className="font-mono font-bold text-cyan-300">{report.title}</h3>
                        <p className="text-xs text-muted-foreground">ID: {report.id}</p>
                      </div>
                    </div>
                    <span className={`px-2 py-1 rounded text-xs font-mono ${
                      report.type === "daily"
                        ? "bg-cyan-500/20 text-cyan-300"
                        : "bg-magenta-600/20 text-magenta-300"
                    }`}>
                      {report.type.toUpperCase()}
                    </span>
                  </div>

                  <div className="grid grid-cols-3 gap-3 text-xs mb-3">
                    <div>
                      <p className="text-muted-foreground">Compliance Rate</p>
                      <p className={`font-mono font-bold ${
                        report.summary.complianceRate >= 98 ? "text-green-400" : "text-red-400"
                      }`}>
                        {report.summary.complianceRate.toFixed(2)}%
                      </p>
                    </div>
                    <div>
                      <p className="text-muted-foreground">Transactions</p>
                      <p className="font-mono font-bold text-cyan-300">
                        {report.summary.totalTransactions.toLocaleString()}
                      </p>
                    </div>
                    <div>
                      <p className="text-muted-foreground">Alerts</p>
                      <p className={`font-mono font-bold ${
                        report.alerts.length > 0 ? "text-yellow-400" : "text-green-400"
                      }`}>
                        {report.alerts.length}
                      </p>
                    </div>
                  </div>

                  <div className="flex items-center gap-2 text-xs text-muted-foreground">
                    <Clock className="w-3 h-3" />
                    <span>{new Date(report.generatedAt).toLocaleString("de-DE")}</span>
                  </div>
                </Card>
              ))}
            </div>
          </div>

          {/* Right: Report Details */}
          <div>
            {selectedReport ? (
              <Card className="bg-card border-cyan-500/30 neon-border p-6 sticky top-20">
                <h3 className="font-mono font-bold text-cyan-300 mb-4">Report Details</h3>

                {/* Summary Metrics */}
                <div className="space-y-3 mb-6 text-sm">
                  <div className="p-3 bg-background rounded border border-border">
                    <p className="text-muted-foreground text-xs mb-1">Compliance Rate</p>
                    <p className={`font-mono font-bold text-lg ${
                      selectedReport.summary.complianceRate >= 98 ? "text-green-400" : "text-red-400"
                    }`}>
                      {selectedReport.summary.complianceRate.toFixed(2)}%
                    </p>
                  </div>

                  <div className="p-3 bg-background rounded border border-border">
                    <p className="text-muted-foreground text-xs mb-1">Total Transactions</p>
                    <p className="font-mono font-bold text-cyan-300">
                      {selectedReport.summary.totalTransactions.toLocaleString()}
                    </p>
                  </div>

                  <div className="p-3 bg-background rounded border border-border">
                    <p className="text-muted-foreground text-xs mb-1">Failed Compliance</p>
                    <p className={`font-mono font-bold ${
                      selectedReport.summary.failedCompliance > 0 ? "text-red-400" : "text-green-400"
                    }`}>
                      {selectedReport.summary.failedCompliance}
                    </p>
                  </div>
                </div>

                {/* Alerts Summary */}
                {selectedReport.alerts.length > 0 && (
                  <div className="mb-6">
                    <p className="font-mono font-bold text-yellow-300 text-sm mb-2">Alerts ({selectedReport.alerts.length})</p>
                    <div className="space-y-2 text-xs">
                      {selectedReport.alerts.slice(0, 3).map((alert, idx) => (
                        <div key={idx} className="p-2 bg-yellow-500/10 border border-yellow-500/30 rounded">
                          <p className="text-yellow-300 font-mono text-xs">{alert.message}</p>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Download Button */}
                <Button
                  onClick={() => handleDownloadReport(selectedReport)}
                  className="w-full bg-green-500 hover:bg-green-600 text-background font-mono neon-border"
                >
                  <Download className="w-4 h-4 mr-2" />
                  Download Report
                </Button>
              </Card>
            ) : (
              <Card className="bg-card border-border p-6 text-center">
                <FileText className="w-12 h-12 text-muted-foreground mx-auto mb-4" />
                <p className="text-muted-foreground text-sm">Select a report to view details</p>
              </Card>
            )}
          </div>
        </div>

        {/* Report Details View */}
        {selectedReport && (
          <div className="mt-12">
            <Card className="bg-card border-cyan-500/30 neon-border p-8">
              <h2 className="text-2xl font-mono font-bold text-cyan-300 mb-6">Full Report: {selectedReport.title}</h2>

              {/* Executive Summary */}
              <div className="mb-8">
                <h3 className="font-mono font-bold text-cyan-300 mb-4">Executive Summary</h3>
                <div className="grid md:grid-cols-4 gap-4">
                  <div className="p-4 bg-background rounded border border-border">
                    <p className="text-xs text-muted-foreground mb-2">Compliance Rate</p>
                    <p className={`text-2xl font-mono font-bold ${
                      selectedReport.summary.complianceRate >= 98 ? "text-green-400" : "text-red-400"
                    }`}>
                      {selectedReport.summary.complianceRate.toFixed(2)}%
                    </p>
                  </div>
                  <div className="p-4 bg-background rounded border border-border">
                    <p className="text-xs text-muted-foreground mb-2">Total Transactions</p>
                    <p className="text-2xl font-mono font-bold text-cyan-300">
                      {selectedReport.summary.totalTransactions.toLocaleString()}
                    </p>
                  </div>
                  <div className="p-4 bg-background rounded border border-border">
                    <p className="text-xs text-muted-foreground mb-2">Compliant</p>
                    <p className="text-2xl font-mono font-bold text-green-400">
                      {selectedReport.summary.compliantTransactions.toLocaleString()}
                    </p>
                  </div>
                  <div className="p-4 bg-background rounded border border-border">
                    <p className="text-xs text-muted-foreground mb-2">Failed</p>
                    <p className={`text-2xl font-mono font-bold ${
                      selectedReport.summary.failedCompliance > 0 ? "text-red-400" : "text-green-400"
                    }`}>
                      {selectedReport.summary.failedCompliance}
                    </p>
                  </div>
                </div>
              </div>

              {/* Alerts */}
              {selectedReport.alerts.length > 0 && (
                <div className="mb-8">
                  <h3 className="font-mono font-bold text-yellow-300 mb-4">Compliance Alerts ({selectedReport.alerts.length})</h3>
                  <div className="space-y-2">
                    {selectedReport.alerts.map((alert, idx) => (
                      <div
                        key={idx}
                        className={`p-3 rounded border ${
                          alert.level === "critical"
                            ? "bg-red-500/10 border-red-500/30"
                            : alert.level === "warning"
                            ? "bg-yellow-500/10 border-yellow-500/30"
                            : "bg-blue-500/10 border-blue-500/30"
                        }`}
                      >
                        <p className={`font-mono text-sm ${
                          alert.level === "critical"
                            ? "text-red-300"
                            : alert.level === "warning"
                            ? "text-yellow-300"
                            : "text-blue-300"
                        }`}>
                          <strong>{alert.level.toUpperCase()}:</strong> {alert.message}
                        </p>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Recommendations */}
              <div className="mb-8">
                <h3 className="font-mono font-bold text-cyan-300 mb-4">Recommendations</h3>
                <ul className="space-y-2">
                  {selectedReport.recommendations.map((rec, idx) => (
                    <li key={idx} className="flex gap-3 text-sm">
                      <CheckCircle className="w-4 h-4 text-green-400 flex-shrink-0 mt-0.5" />
                      <span className="text-muted-foreground">{rec}</span>
                    </li>
                  ))}
                </ul>
              </div>

              {/* Audit Trail */}
              <div>
                <h3 className="font-mono font-bold text-cyan-300 mb-4">Audit Trail</h3>
                <div className="space-y-2">
                  {selectedReport.auditTrail.map((entry, idx) => (
                    <div key={idx} className="p-3 bg-background rounded border border-border text-sm">
                      <div className="flex justify-between mb-1">
                        <p className="font-mono font-bold text-cyan-300">{entry.action}</p>
                        <p className="text-xs text-muted-foreground">
                          {new Date(entry.timestamp).toLocaleTimeString("de-DE")}
                        </p>
                      </div>
                      <p className="text-xs text-muted-foreground">{entry.details}</p>
                    </div>
                  ))}
                </div>
              </div>
            </Card>
          </div>
        )}
      </div>
    </div>
  );
}
