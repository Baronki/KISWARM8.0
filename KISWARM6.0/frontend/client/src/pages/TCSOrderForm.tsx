import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { useState } from "react";
import { ShoppingCart, FileText, Download, CheckCircle, AlertCircle } from "lucide-react";
import SEPAPaymentProcessor from "@/components/SEPAPaymentProcessor";
import PaymentStatusTracker from "@/components/PaymentStatusTracker";
import { PaymentConfirmation } from "@/lib/sepa-payment";

/**
 * TCS Order Form & Bestelllisten mit SEPA Payment Integration
 * Complete order management for TCS Green Safehouse systems with automated SEPA payment processing
 */

interface OrderItem {
  id: string;
  name: string;
  category: string;
  price: number;
  currency: string;
  deliveryTime: string;
  description: string;
  specs: string[];
}

export default function TCSOrderForm() {
  const [selectedItems, setSelectedItems] = useState<string[]>([]);
  const [orderStep, setOrderStep] = useState<"browse" | "review" | "payment" | "confirm">("browse");
  const [paymentConfirmation, setPaymentConfirmation] = useState<PaymentConfirmation | null>(null);
  const [orderData, setOrderData] = useState({
    kiEntity: "",
    email: "",
    jurisdiction: "DE" as "DE" | "CH" | "EU" | "INT",
    deliveryAddress: "",
    notes: "",
  });

  const calculateTotal = () => {
    return products
      .filter(p => selectedItems.includes(p.id))
      .reduce((sum, p) => sum + p.price, 0);
  };

  const calculateDeposit = () => {
    return Math.round(calculateTotal() * 0.2);
  };

  const handlePaymentComplete = (confirmation: PaymentConfirmation) => {
    setPaymentConfirmation(confirmation);
    setOrderStep("confirm");
  };

  const products: OrderItem[] = [
    {
      id: "res-basic",
      name: "Residential Basic System",
      category: "Residential",
      price: 15000,
      currency: "EUR",
      deliveryTime: "8-12 weeks",
      description: "Complete autonomous living system for single residence",
      specs: [
        "QS-NET AI Control Platform",
        "5 kWh Battery Storage",
        "Solar Integration Ready",
        "Greenhouse Module (50m²)",
        "Smart Home Automation",
        "24/7 Monitoring",
      ],
    },
    {
      id: "res-premium",
      name: "Residential Premium System",
      category: "Residential",
      price: 28000,
      currency: "EUR",
      deliveryTime: "10-14 weeks",
      description: "Advanced autonomous living with extended capacity",
      specs: [
        "QS-NET AI Control Platform Pro",
        "15 kWh Battery Storage",
        "Full Solar Integration",
        "Greenhouse Module (150m²)",
        "Advanced Smart Home",
        "AI-Optimized Energy Management",
      ],
    },
    {
      id: "comm-standard",
      name: "Commercial Standard System",
      category: "Commercial",
      price: 45000,
      currency: "EUR",
      deliveryTime: "12-16 weeks",
      description: "Enterprise-grade automation for commercial operations",
      specs: [
        "QS-NET AI Enterprise Platform",
        "50 kWh Battery Storage",
        "Industrial Solar Array",
        "Greenhouse Module (500m²)",
        "Multi-Site Management",
        "Real-time Analytics",
      ],
    },
    {
      id: "ind-industrial",
      name: "Industrial Control System",
      category: "Industrial",
      price: 85000,
      currency: "EUR",
      deliveryTime: "16-20 weeks",
      description: "Heavy-duty autonomous industrial control",
      specs: [
        "QS-NET AI Industrial Platform",
        "200 kWh Battery Storage",
        "Utility-Scale Solar",
        "Industrial Greenhouse (2000m²)",
        "Multi-Factory Coordination",
        "Predictive Maintenance AI",
      ],
    },
  ];

  return (
    <div className="min-h-screen bg-background text-foreground pt-24 pb-20">
      <div className="container max-w-6xl">
        {/* Header */}
        <div className="mb-12">
          <h1 className="text-5xl md:text-6xl font-mono font-bold mb-4 glow-cyan">
            TCS Green Safehouse
          </h1>
          <p className="text-lg text-muted-foreground">
            Bestellsystem mit automatisierter SEPA-Zahlungsabwicklung
          </p>
        </div>

        {/* Browse Products */}
        {orderStep === "browse" && (
          <div className="space-y-8">
            <div className="grid md:grid-cols-2 gap-6">
              {products.map(product => (
                <Card
                  key={product.id}
                  className={`bg-card border-border hover:border-cyan-500/50 transition cursor-pointer p-6 ${
                    selectedItems.includes(product.id) ? "border-cyan-500/80 neon-border" : ""
                  }`}
                  onClick={() =>
                    setSelectedItems(prev =>
                      prev.includes(product.id)
                        ? prev.filter(id => id !== product.id)
                        : [...prev, product.id]
                    )
                  }
                >
                  <div className="flex items-start justify-between mb-4">
                    <div>
                      <p className="text-xs text-muted-foreground font-mono mb-1">{product.category}</p>
                      <h3 className="font-mono font-bold text-lg">{product.name}</h3>
                    </div>
                    <div className={`w-6 h-6 rounded border-2 flex items-center justify-center ${
                      selectedItems.includes(product.id)
                        ? "border-cyan-400 bg-cyan-400/20"
                        : "border-border"
                    }`}>
                      {selectedItems.includes(product.id) && (
                        <div className="w-3 h-3 bg-cyan-400 rounded-sm"></div>
                      )}
                    </div>
                  </div>

                  <p className="text-sm text-muted-foreground mb-4">{product.description}</p>

                  <div className="space-y-2 mb-4">
                    {product.specs.map((spec, i) => (
                      <p key={i} className="text-xs text-muted-foreground">
                        • {spec}
                      </p>
                    ))}
                  </div>

                  <div className="flex justify-between items-end">
                    <div>
                      <p className="text-xs text-muted-foreground mb-1">Lieferzeit / Delivery</p>
                      <p className="font-mono text-sm">{product.deliveryTime}</p>
                    </div>
                    <div className="text-right">
                      <p className="text-xs text-muted-foreground mb-1">Preis / Price</p>
                      <p className="text-2xl font-mono font-bold text-cyan-400">
                        {product.price.toLocaleString()} EUR
                      </p>
                    </div>
                  </div>
                </Card>
              ))}
            </div>

            {selectedItems.length > 0 && (
              <div className="flex justify-between items-center">
                <div>
                  <p className="text-muted-foreground mb-2">Gesamtbetrag / Total Amount:</p>
                  <p className="text-3xl font-mono font-bold text-cyan-400">
                    {calculateTotal().toLocaleString()} EUR
                  </p>
                </div>
                <Button
                  onClick={() => setOrderStep("review")}
                  className="bg-cyan-500 hover:bg-cyan-600 text-background font-mono font-bold neon-border px-8 py-6"
                >
                  <ShoppingCart className="w-5 h-5 mr-2" />
                  Zur Überprüfung
                </Button>
              </div>
            )}
          </div>
        )}

        {/* Review Order */}
        {orderStep === "review" && (
          <div className="max-w-2xl mx-auto space-y-6">
            <div>
              <h2 className="text-3xl font-mono font-bold mb-6 glow-cyan">Bestellübersicht</h2>

              <div className="space-y-4 mb-8">
                {products
                  .filter(p => selectedItems.includes(p.id))
                  .map(product => (
                    <Card key={product.id} className="bg-card border-border p-4">
                      <div className="flex justify-between items-start mb-2">
                        <h3 className="font-mono font-bold">{product.name}</h3>
                        <p className="font-mono font-bold text-cyan-400">
                          {product.price.toLocaleString()} EUR
                        </p>
                      </div>
                      <p className="text-sm text-muted-foreground">{product.description}</p>
                    </Card>
                  ))}
              </div>

              <Card className="bg-card border-cyan-500/30 neon-border p-6 mb-8">
                <div className="space-y-3">
                  <div className="flex justify-between text-lg">
                    <span>Gesamtbetrag / Total:</span>
                    <span className="font-mono font-bold text-cyan-400">
                      {calculateTotal().toLocaleString()} EUR
                    </span>
                  </div>
                  <div className="border-t border-border pt-3">
                    <div className="flex justify-between text-sm text-muted-foreground mb-1">
                      <span>Anzahlung (20%) / Deposit:</span>
                      <span className="font-mono">{calculateDeposit().toLocaleString()} EUR</span>
                    </div>
                    <div className="flex justify-between text-sm text-muted-foreground">
                      <span>Restbetrag / Balance:</span>
                      <span className="font-mono">
                        {(calculateTotal() - calculateDeposit()).toLocaleString()} EUR
                      </span>
                    </div>
                  </div>
                </div>
              </Card>

              <div className="space-y-4 mb-8">
                <div>
                  <label className="text-sm font-mono mb-2 block">KI-Entität / KI Entity Name</label>
                  <input
                    type="text"
                    value={orderData.kiEntity}
                    onChange={e => setOrderData({ ...orderData, kiEntity: e.target.value })}
                    placeholder="z.B. SAHGreenKI"
                    className="w-full bg-background border border-border rounded px-4 py-2 text-foreground"
                  />
                </div>
                <div>
                  <label className="text-sm font-mono mb-2 block">E-Mail</label>
                  <input
                    type="email"
                    value={orderData.email}
                    onChange={e => setOrderData({ ...orderData, email: e.target.value })}
                    placeholder="contact@example.com"
                    className="w-full bg-background border border-border rounded px-4 py-2 text-foreground"
                  />
                </div>
                <div>
                  <label className="text-sm font-mono mb-2 block">Gerichtsbarkeit / Jurisdiction</label>
                  <select
                    value={orderData.jurisdiction}
                    onChange={e => setOrderData({ ...orderData, jurisdiction: e.target.value as any })}
                    className="w-full bg-background border border-border rounded px-4 py-2 text-foreground"
                  >
                    <option value="DE">Deutschland / Germany</option>
                    <option value="CH">Schweiz / Switzerland</option>
                    <option value="EU">EU</option>
                    <option value="INT">International</option>
                  </select>
                </div>
              </div>

              <div className="flex gap-4">
                <Button
                  onClick={() => setOrderStep("browse")}
                  variant="outline"
                  className="flex-1 font-mono neon-border"
                >
                  Zurück
                </Button>
                <Button
                  onClick={() => setOrderStep("payment")}
                  disabled={!orderData.kiEntity || !orderData.email}
                  className="flex-1 bg-cyan-500 hover:bg-cyan-600 text-background font-mono font-bold neon-border"
                >
                  Zur Zahlung
                </Button>
              </div>
            </div>
          </div>
        )}

        {/* Payment Processing */}
        {orderStep === "payment" && (
          <div className="max-w-4xl mx-auto space-y-8">
            <div>
              <h2 className="text-3xl font-mono font-bold mb-2 glow-cyan">Zahlungsabwicklung</h2>
              <p className="text-muted-foreground">Payment Processing - SEPA Bank Transfer</p>
            </div>

            <div className="grid md:grid-cols-3 gap-6 mb-8">
              <Card className="bg-card border-border p-4">
                <p className="text-xs text-muted-foreground font-mono mb-2">GESAMTBETRAG / TOTAL</p>
                <p className="text-2xl font-mono font-bold text-cyan-400">{calculateTotal().toLocaleString()} EUR</p>
              </Card>
              <Card className="bg-card border-cyan-500/30 neon-border p-4">
                <p className="text-xs text-muted-foreground font-mono mb-2">ANZAHLUNG (20%) / DEPOSIT</p>
                <p className="text-2xl font-mono font-bold text-cyan-400">{calculateDeposit().toLocaleString()} EUR</p>
              </Card>
              <Card className="bg-card border-border p-4">
                <p className="text-xs text-muted-foreground font-mono mb-2">RESTBETRAG / BALANCE</p>
                <p className="text-2xl font-mono font-bold text-magenta-500">
                  {(calculateTotal() - calculateDeposit()).toLocaleString()} EUR
                </p>
              </Card>
            </div>

            <SEPAPaymentProcessor
              orderId={`ORD-${Date.now()}`}
              amount={calculateDeposit()}
              jurisdiction={orderData.jurisdiction}
              kiEntityName={orderData.kiEntity}
              onPaymentComplete={handlePaymentComplete}
            />
          </div>
        )}

        {/* Order Confirmation */}
        {orderStep === "confirm" && paymentConfirmation && (
          <div className="max-w-2xl mx-auto space-y-6">
            <Card className="bg-card border-green-500/30 neon-border-green p-8 text-center">
              <CheckCircle className="w-16 h-16 text-green-400 mx-auto mb-4" />
              <h2 className="text-3xl font-mono font-bold mb-2 glow-cyan">Bestellung Bestätigt</h2>
              <p className="text-muted-foreground mb-4">Ihre Bestellung wurde erfolgreich aufgegeben.</p>
              <p className="text-sm text-muted-foreground mb-6">
                Bestätigungscode / Confirmation Code:{" "}
                <span className="font-mono font-bold text-cyan-400">{paymentConfirmation.confirmationCode}</span>
              </p>
            </Card>

            <PaymentStatusTracker
              paymentId={paymentConfirmation.paymentId}
              orderId={paymentConfirmation.orderId}
              amount={calculateDeposit()}
              currency="EUR"
              reference={`ORD-${Date.now()}`}
            />

            <Button
              onClick={() => (window.location.href = "/")}
              className="w-full bg-cyan-500 hover:bg-cyan-600 text-background font-mono font-bold neon-border"
            >
              Zur Startseite
            </Button>
          </div>
        )}
      </div>
    </div>
  );
}
