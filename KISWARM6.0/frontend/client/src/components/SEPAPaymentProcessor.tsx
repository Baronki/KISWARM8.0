import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { useState } from "react";
import { Copy, Download, Check, AlertCircle, Loader2, CreditCard } from "lucide-react";
import {
  createSEPAPayment,
  processSEPAPayment,
  generateSEPAInstructions,
  generatePaymentReceipt,
  BANKING_HUBS,
  SEPAPayment,
  PaymentConfirmation,
} from "@/lib/sepa-payment";

/**
 * SEPA Payment Processor Component
 * Handles payment processing and display of SEPA transfer instructions
 */

interface SEPAPaymentProcessorProps {
  orderId: string;
  amount: number;
  jurisdiction: "DE" | "CH" | "EU" | "INT";
  kiEntityName: string;
  onPaymentComplete: (confirmation: PaymentConfirmation) => void;
}

export default function SEPAPaymentProcessor({
  orderId,
  amount,
  jurisdiction,
  kiEntityName,
  onPaymentComplete,
}: SEPAPaymentProcessorProps) {
  const [payment, setPayment] = useState<SEPAPayment | null>(null);
  const [confirmation, setConfirmation] = useState<PaymentConfirmation | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [copied, setCopied] = useState<string | null>(null);
  const [step, setStep] = useState<"init" | "instructions" | "processing" | "confirmed">("init");

  const handleInitiatePayment = async () => {
    const newPayment = createSEPAPayment(orderId, amount, jurisdiction, kiEntityName);
    setPayment(newPayment);
    setStep("instructions");
  };

  const handleProcessPayment = async () => {
    if (!payment) return;

    setIsProcessing(true);
    try {
      const paymentConfirmation = await processSEPAPayment(payment);
      setConfirmation(paymentConfirmation);
      setStep("confirmed");
      onPaymentComplete(paymentConfirmation);
    } catch (error) {
      console.error("Payment processing error:", error);
    } finally {
      setIsProcessing(false);
    }
  };

  const copyToClipboard = (text: string, id: string) => {
    navigator.clipboard.writeText(text);
    setCopied(id);
    setTimeout(() => setCopied(null), 2000);
  };

  const downloadInstructions = () => {
    if (!payment) return;

    const instructions = generateSEPAInstructions(payment, kiEntityName);
    const element = document.createElement("a");
    element.setAttribute("href", "data:text/plain;charset=utf-8," + encodeURIComponent(instructions));
    element.setAttribute("download", `SEPA_Instructions_${payment.reference}.txt`);
    element.style.display = "none";
    document.body.appendChild(element);
    element.click();
    document.body.removeChild(element);
  };

  const downloadReceipt = () => {
    if (!payment || !confirmation) return;

    const receipt = generatePaymentReceipt(payment, confirmation, kiEntityName);
    const element = document.createElement("a");
    element.setAttribute("href", "data:text/plain;charset=utf-8," + encodeURIComponent(receipt));
    element.setAttribute("download", `Payment_Receipt_${confirmation.confirmationCode}.txt`);
    element.style.display = "none";
    document.body.appendChild(element);
    element.click();
    document.body.removeChild(element);
  };

  if (step === "init") {
    return (
      <Card className="bg-card border-cyan-500/30 neon-border p-6">
        <div className="flex items-start gap-4 mb-4">
          <CreditCard className="w-6 h-6 text-cyan-400 flex-shrink-0 mt-1" />
          <div>
            <h3 className="font-mono font-bold text-lg mb-2">SEPA Payment Processing</h3>
            <p className="text-sm text-muted-foreground">
              Automatisierte SEPA-Überweisung für Ihre Anzahlung. Secure payment processing with full compliance.
            </p>
          </div>
        </div>

        <div className="bg-background rounded border border-border p-4 mb-6">
          <p className="text-sm text-muted-foreground mb-2">Zahlungsbetrag / Payment Amount:</p>
          <p className="text-3xl font-mono font-bold text-cyan-400">
            {amount.toLocaleString()} {jurisdiction === "CH" ? "CHF" : "EUR"}
          </p>
        </div>

        <Button
          onClick={handleInitiatePayment}
          className="w-full bg-cyan-500 hover:bg-cyan-600 text-background font-mono font-bold neon-border"
        >
          SEPA-Zahlung initiieren / Initiate SEPA Payment
        </Button>
      </Card>
    );
  }

  if (step === "instructions" && payment) {
    const account = payment.targetAccount;

    return (
      <Card className="bg-card border-cyan-500/30 neon-border p-6 space-y-6">
        <div>
          <h3 className="font-mono font-bold text-lg mb-4 glow-cyan">SEPA Zahlungsanweisungen</h3>

          {/* Payment Details */}
          <div className="space-y-4 mb-6">
            <div className="bg-background rounded border border-border p-4">
              <p className="text-xs text-muted-foreground font-mono mb-1">ZAHLUNGSREFERENZ / PAYMENT REFERENCE</p>
              <div className="flex items-center justify-between gap-2">
                <p className="font-mono font-bold text-cyan-400">{payment.reference}</p>
                <button
                  onClick={() => copyToClipboard(payment.reference, "reference")}
                  className="p-2 hover:bg-background rounded transition"
                >
                  {copied === "reference" ? (
                    <Check className="w-4 h-4 text-green-400" />
                  ) : (
                    <Copy className="w-4 h-4 text-muted-foreground" />
                  )}
                </button>
              </div>
            </div>

            <div className="bg-background rounded border border-border p-4">
              <p className="text-xs text-muted-foreground font-mono mb-1">EMPFÄNGER / RECIPIENT</p>
              <p className="font-mono font-bold mb-2">{account.name}</p>
              <p className="text-sm text-muted-foreground">{account.address}</p>
            </div>

            <div className="bg-background rounded border border-border p-4">
              <p className="text-xs text-muted-foreground font-mono mb-3">BANKVERBINDUNG / BANK DETAILS</p>
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-sm text-muted-foreground">IBAN:</span>
                  <div className="flex items-center gap-2">
                    <span className="font-mono font-bold">{account.iban}</span>
                    <button
                      onClick={() => copyToClipboard(account.iban, "iban")}
                      className="p-1 hover:bg-background rounded transition"
                    >
                      {copied === "iban" ? (
                        <Check className="w-4 h-4 text-green-400" />
                      ) : (
                        <Copy className="w-4 h-4 text-muted-foreground" />
                      )}
                    </button>
                  </div>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-muted-foreground">BIC:</span>
                  <div className="flex items-center gap-2">
                    <span className="font-mono font-bold">{account.bic}</span>
                    <button
                      onClick={() => copyToClipboard(account.bic, "bic")}
                      className="p-1 hover:bg-background rounded transition"
                    >
                      {copied === "bic" ? (
                        <Check className="w-4 h-4 text-green-400" />
                      ) : (
                        <Copy className="w-4 h-4 text-muted-foreground" />
                      )}
                    </button>
                  </div>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-muted-foreground">Bank:</span>
                  <span className="font-mono text-sm">{account.bankName}</span>
                </div>
              </div>
            </div>

            <div className="bg-background rounded border border-border p-4">
              <p className="text-xs text-muted-foreground font-mono mb-1">BETRAG / AMOUNT</p>
              <p className="text-2xl font-mono font-bold text-cyan-400">
                {payment.amount.toLocaleString()} {payment.currency}
              </p>
            </div>
          </div>

          {/* Important Notice */}
          <Card className="bg-magenta-500/10 border-magenta-600/30 neon-border-magenta p-4 mb-6">
            <div className="flex gap-3">
              <AlertCircle className="w-5 h-5 text-magenta-500 flex-shrink-0 mt-0.5" />
              <div className="text-sm text-muted-foreground">
                <p className="font-mono font-bold text-magenta-400 mb-2">Wichtig / Important:</p>
                <ul className="space-y-1 text-xs">
                  <li>• Verwenden Sie die exakte Referenznummer / Use exact reference number</li>
                  <li>• Verarbeitungsdauer: 1-2 Werktage / Processing time: 1-2 business days</li>
                  <li>• Bestätigung erfolgt per E-Mail / Confirmation by email</li>
                  <li>• Bestellung wird nach Zahlungsbestätigung aktiviert / Order activated after payment confirmation</li>
                </ul>
              </div>
            </div>
          </Card>

          {/* Action Buttons */}
          <div className="flex gap-4">
            <Button
              onClick={downloadInstructions}
              variant="outline"
              className="flex-1 font-mono neon-border"
            >
              <Download className="w-4 h-4 mr-2" />
              Anleitung herunterladen
            </Button>
            <Button
              onClick={handleProcessPayment}
              disabled={isProcessing}
              className="flex-1 bg-cyan-500 hover:bg-cyan-600 text-background font-mono font-bold neon-border"
            >
              {isProcessing ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  Verarbeitung...
                </>
              ) : (
                "Zahlung bestätigen"
              )}
            </Button>
          </div>
        </div>
      </Card>
    );
  }

  if (step === "confirmed" && payment && confirmation) {
    return (
      <Card className="bg-card border-green-500/30 neon-border p-6 space-y-6">
        <div className="text-center">
          <Check className="w-12 h-12 text-green-400 mx-auto mb-4" />
          <h3 className="font-mono font-bold text-2xl mb-2 glow-cyan">Zahlung Bestätigt</h3>
          <p className="text-muted-foreground">Payment Confirmation Code: {confirmation.confirmationCode}</p>
        </div>

        <div className="bg-background rounded border border-border p-4 space-y-3">
          <div className="flex justify-between">
            <span className="text-sm text-muted-foreground">Bestätigungscode / Confirmation Code:</span>
            <span className="font-mono font-bold text-cyan-400">{confirmation.confirmationCode}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-sm text-muted-foreground">Status:</span>
            <span className="font-mono font-bold text-green-400">{confirmation.status.toUpperCase()}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-sm text-muted-foreground">Zeitstempel / Timestamp:</span>
            <span className="font-mono text-sm">{new Date(confirmation.timestamp).toLocaleString()}</span>
          </div>
        </div>

        <Card className="bg-cyan-500/10 border-cyan-500/30 neon-border p-4">
          <p className="text-sm text-muted-foreground mb-2">
            Ihre Zahlung wurde erfolgreich verarbeitet. Sie erhalten eine Bestätigung per E-Mail.
          </p>
          <p className="text-xs text-muted-foreground">
            Your payment has been processed successfully. You will receive confirmation by email.
          </p>
        </Card>

        <Button
          onClick={downloadReceipt}
          className="w-full bg-cyan-500 hover:bg-cyan-600 text-background font-mono font-bold neon-border"
        >
          <Download className="w-4 h-4 mr-2" />
          Zahlungsbeleg herunterladen / Download Receipt
        </Button>
      </Card>
    );
  }

  return null;
}
