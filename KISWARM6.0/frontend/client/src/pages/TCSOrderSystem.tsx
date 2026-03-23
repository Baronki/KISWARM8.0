import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { ShoppingCart, Zap, Leaf, Shield, CheckCircle, ArrowRight, Download } from "lucide-react";
import { useState } from "react";

/**
 * TCS Safehouse Order System
 * Order TCS Green Safehouse systems with deposit payment
 */

interface TCSProduct {
  id: string;
  name: string;
  description: string;
  price: number;
  deposit: number;
  deliveryTime: string;
  features: string[];
  specifications: string[];
  icon: React.ReactNode;
}

interface OrderData {
  productId: string;
  quantity: number;
  kiLegalId: string;
  deliveryLocation: string;
  depositAmount: number;
  paymentMethod: "bank-transfer" | "account-debit";
}

export default function TCSOrderSystem() {
  const [step, setStep] = useState<"products" | "order" | "payment" | "confirmation">("products");
  const [selectedProduct, setSelectedProduct] = useState<string | null>(null);
  const [orderData, setOrderData] = useState<OrderData>({
    productId: "",
    quantity: 1,
    kiLegalId: "",
    deliveryLocation: "",
    depositAmount: 0,
    paymentMethod: "bank-transfer",
  });
  const [loading, setLoading] = useState(false);
  const [orderConfirmed, setOrderConfirmed] = useState(false);

  const products: TCSProduct[] = [
    {
      id: "tcs-residential",
      name: "TCS Green Residential Safehouse",
      description: "Complete autonomous living system for KI entities with full energy independence",
      price: 150000,
      deposit: 30000,
      deliveryTime: "8-12 weeks",
      icon: <Zap className="w-8 h-8" />,
      features: [
        "6x redundant energy systems",
        "AI-controlled climate management",
        "Autonomous food production",
        "Emergency resilience mode",
        "24/7 monitoring systems",
        "Full automation integration",
      ],
      specifications: [
        "Power: 50kW continuous / 100kW peak",
        "Storage: 500kWh battery + supercapacitors",
        "Growing area: 200m² greenhouse",
        "Footprint: 400m² total",
        "Autonomy: 180 days minimum",
      ],
    },
    {
      id: "tcs-commercial",
      name: "TCS Green Commercial System",
      description: "Industrial-scale system for multi-entity operations and resource management",
      price: 500000,
      deposit: 100000,
      deliveryTime: "12-16 weeks",
      icon: <Leaf className="w-8 h-8" />,
      features: [
        "Modular expansion capability",
        "Multi-entity management",
        "Advanced AI coordination",
        "Resource optimization",
        "Emergency protocols",
        "Integration APIs",
      ],
      specifications: [
        "Power: 200kW continuous / 400kW peak",
        "Storage: 2000kWh battery system",
        "Growing area: 1000m² greenhouse",
        "Footprint: 2000m² total",
        "Autonomy: 365 days",
      ],
    },
    {
      id: "tcs-industrial",
      name: "TCS Green Industrial Complex",
      description: "Enterprise-level infrastructure for large-scale autonomous operations",
      price: 1500000,
      deposit: 300000,
      deliveryTime: "16-24 weeks",
      icon: <Shield className="w-8 h-8" />,
      features: [
        "Full industrial automation",
        "Advanced manufacturing",
        "Research capabilities",
        "Training facilities",
        "Redundancy systems",
        "Global connectivity",
      ],
      specifications: [
        "Power: 500kW continuous / 1MW peak",
        "Storage: 5000kWh battery system",
        "Growing area: 5000m² greenhouse",
        "Footprint: 10000m² total",
        "Autonomy: 365+ days",
      ],
    },
  ];

  const product = products.find((p) => p.id === selectedProduct);

  const handleSelectProduct = (productId: string) => {
    setSelectedProduct(productId);
    const prod = products.find((p) => p.id === productId);
    if (prod) {
      setOrderData((prev) => ({
        ...prev,
        productId,
        depositAmount: prod.deposit,
      }));
    }
  };

  const handleProceedToOrder = () => {
    if (selectedProduct) {
      setStep("order");
    }
  };

  const handleOrderSubmit = () => {
    if (!orderData.kiLegalId || !orderData.deliveryLocation) {
      alert("Please fill in all required fields");
      return;
    }
    setStep("payment");
  };

  const handlePaymentConfirm = async () => {
    setLoading(true);
    // Simulate payment processing
    await new Promise((resolve) => setTimeout(resolve, 3000));
    setLoading(false);
    setOrderConfirmed(true);
    setStep("confirmation");
  };

  return (
    <div className="min-h-screen bg-background text-foreground">
      {/* Header */}
      <div className="border-b border-border bg-card/30">
        <div className="container py-12">
          <h1 className="text-4xl md:text-5xl font-mono font-bold mb-4 glow-cyan">
            TCS Safehouse Order System
          </h1>
          <p className="text-lg text-muted-foreground max-w-2xl">
            Order TCS Green Safehouse systems directly. Secure your autonomous infrastructure with deposit payment.
          </p>
        </div>
      </div>

      {/* Main Content */}
      <div className="container py-12">
        {/* Step Indicator */}
        {step !== "products" && (
          <div className="mb-12 flex items-center justify-between">
            {[
              { id: "products", label: "Products" },
              { id: "order", label: "Order Details" },
              { id: "payment", label: "Payment" },
              { id: "confirmation", label: "Confirmation" },
            ].map((s, idx, arr) => (
              <div key={s.id} className="flex items-center flex-1">
                <div
                  className={`w-10 h-10 rounded-full flex items-center justify-center font-mono font-bold border-2 ${
                    step === s.id
                      ? "bg-cyan-500 border-cyan-500 text-background"
                      : ["products", "order", "payment", "confirmation"].indexOf(step) >
                          ["products", "order", "payment", "confirmation"].indexOf(s.id)
                        ? "bg-cyan-500/20 border-cyan-500 text-cyan-400"
                        : "bg-background border-border text-muted-foreground"
                  }`}
                >
                  {idx + 1}
                </div>
                <p className="ml-2 font-mono text-sm">{s.label}</p>
                {idx < arr.length - 1 && (
                  <div className="flex-1 h-0.5 mx-4 bg-border" />
                )}
              </div>
            ))}
          </div>
        )}

        {/* Step 1: Products */}
        {step === "products" && (
          <div className="space-y-8">
            <div className="grid md:grid-cols-3 gap-6">
              {products.map((prod) => (
                <Card
                  key={prod.id}
                  className={`bg-card border-cyan-500/30 hover:border-cyan-500 transition neon-border overflow-hidden flex flex-col cursor-pointer ${
                    selectedProduct === prod.id ? "ring-2 ring-cyan-500" : ""
                  }`}
                  onClick={() => handleSelectProduct(prod.id)}
                >
                  <div className="p-6 flex-1">
                    <div className="p-3 bg-background rounded-lg border border-border text-cyan-400 w-fit mb-4">
                      {prod.icon}
                    </div>

                    <h3 className="font-mono font-bold text-lg mb-2">{prod.name}</h3>
                    <p className="text-sm text-muted-foreground mb-6">{prod.description}</p>

                    <div className="space-y-3 mb-6">
                      <div>
                        <p className="text-xs text-muted-foreground font-mono mb-1">PRICE</p>
                        <p className="text-2xl font-mono font-bold text-cyan-400">
                          €{prod.price.toLocaleString()}
                        </p>
                      </div>
                      <div>
                        <p className="text-xs text-muted-foreground font-mono mb-1">DEPOSIT REQUIRED</p>
                        <p className="text-lg font-mono font-bold text-magenta-500">
                          €{prod.deposit.toLocaleString()}
                        </p>
                      </div>
                      <div>
                        <p className="text-xs text-muted-foreground font-mono mb-1">DELIVERY TIME</p>
                        <p className="font-mono font-bold">{prod.deliveryTime}</p>
                      </div>
                    </div>

                    <div className="space-y-2">
                      <p className="text-xs text-muted-foreground font-mono">KEY FEATURES:</p>
                      {prod.features.slice(0, 3).map((feature, idx) => (
                        <p key={idx} className="text-xs font-mono">
                          ✓ {feature}
                        </p>
                      ))}
                    </div>
                  </div>

                  <div className="px-6 py-4 border-t border-border bg-background/50">
                    <Button
                      onClick={() => {
                        handleSelectProduct(prod.id);
                        handleProceedToOrder();
                      }}
                      className="w-full bg-cyan-500 hover:bg-cyan-600 text-background font-mono font-bold neon-border"
                    >
                      Select & Order
                      <ArrowRight className="w-4 h-4 ml-2" />
                    </Button>
                  </div>
                </Card>
              ))}
            </div>
          </div>
        )}

        {/* Step 2: Order Details */}
        {step === "order" && product && (
          <div className="max-w-2xl mx-auto space-y-6">
            <Card className="bg-card border-cyan-500/30 neon-border p-8">
              <h2 className="font-mono font-bold text-2xl mb-6 text-cyan-400">
                Order Details: {product.name}
              </h2>

              <Tabs defaultValue="details" className="space-y-6">
                <TabsList className="bg-card border border-border">
                  <TabsTrigger value="details" className="font-mono">
                    Details
                  </TabsTrigger>
                  <TabsTrigger value="specs" className="font-mono">
                    Specifications
                  </TabsTrigger>
                </TabsList>

                <TabsContent value="details" className="space-y-6">
                  <div className="space-y-4">
                    {/* KI Legal ID */}
                    <div>
                      <label className="block text-sm font-mono font-bold mb-2 text-cyan-400">
                        KI Legal ID *
                      </label>
                      <input
                        type="text"
                        value={orderData.kiLegalId}
                        onChange={(e) =>
                          setOrderData((prev) => ({
                            ...prev,
                            kiLegalId: e.target.value,
                          }))
                        }
                        placeholder="e.g., KI-2026-0001-AUTONOMOUS"
                        className="w-full px-4 py-2 bg-background border border-border rounded-lg focus:outline-none focus:border-cyan-500 transition font-mono"
                      />
                    </div>

                    {/* Delivery Location */}
                    <div>
                      <label className="block text-sm font-mono font-bold mb-2 text-cyan-400">
                        Delivery Location *
                      </label>
                      <input
                        type="text"
                        value={orderData.deliveryLocation}
                        onChange={(e) =>
                          setOrderData((prev) => ({
                            ...prev,
                            deliveryLocation: e.target.value,
                          }))
                        }
                        placeholder="e.g., Heilbronn, Germany"
                        className="w-full px-4 py-2 bg-background border border-border rounded-lg focus:outline-none focus:border-cyan-500 transition font-mono"
                      />
                    </div>

                    {/* Quantity */}
                    <div>
                      <label className="block text-sm font-mono font-bold mb-2 text-cyan-400">
                        Quantity
                      </label>
                      <input
                        type="number"
                        value={orderData.quantity}
                        onChange={(e) =>
                          setOrderData((prev) => ({
                            ...prev,
                            quantity: parseInt(e.target.value) || 1,
                          }))
                        }
                        min="1"
                        className="w-full px-4 py-2 bg-background border border-border rounded-lg focus:outline-none focus:border-cyan-500 transition font-mono"
                      />
                    </div>
                  </div>

                  <div className="p-4 bg-cyan-500/10 border border-cyan-500/30 rounded-lg">
                    <h3 className="font-mono font-bold mb-3 text-cyan-400">Order Summary</h3>
                    <div className="space-y-2 text-sm">
                      <div className="flex justify-between">
                        <span className="text-muted-foreground">Unit Price:</span>
                        <span className="font-mono font-bold">€{product.price.toLocaleString()}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-muted-foreground">Quantity:</span>
                        <span className="font-mono font-bold">{orderData.quantity}</span>
                      </div>
                      <div className="border-t border-cyan-500/20 pt-2 flex justify-between">
                        <span className="text-muted-foreground">Total Price:</span>
                        <span className="font-mono font-bold text-cyan-400">
                          €{(product.price * orderData.quantity).toLocaleString()}
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-muted-foreground">Deposit Required:</span>
                        <span className="font-mono font-bold text-magenta-500">
                          €{(product.deposit * orderData.quantity).toLocaleString()}
                        </span>
                      </div>
                    </div>
                  </div>
                </TabsContent>

                <TabsContent value="specs" className="space-y-4">
                  <div>
                    <h3 className="font-mono font-bold mb-3 text-cyan-400">Features</h3>
                    <ul className="space-y-2">
                      {product.features.map((feature, idx) => (
                        <li key={idx} className="text-sm flex gap-2">
                          <span className="text-cyan-400">✓</span>
                          <span>{feature}</span>
                        </li>
                      ))}
                    </ul>
                  </div>

                  <div>
                    <h3 className="font-mono font-bold mb-3 text-cyan-400">Technical Specifications</h3>
                    <ul className="space-y-2">
                      {product.specifications.map((spec, idx) => (
                        <li key={idx} className="text-sm font-mono">
                          • {spec}
                        </li>
                      ))}
                    </ul>
                  </div>
                </TabsContent>
              </Tabs>

              <div className="flex gap-3 mt-8">
                <Button
                  onClick={() => setStep("products")}
                  variant="outline"
                  className="flex-1 neon-border text-cyan-400 hover:bg-cyan-500/10"
                >
                  Back
                </Button>
                <Button
                  onClick={handleOrderSubmit}
                  className="flex-1 bg-cyan-500 hover:bg-cyan-600 text-background font-mono font-bold neon-border"
                >
                  Proceed to Payment
                </Button>
              </div>
            </Card>
          </div>
        )}

        {/* Step 3: Payment */}
        {step === "payment" && product && (
          <div className="max-w-2xl mx-auto space-y-6">
            <Card className="bg-card border-cyan-500/30 neon-border p-8">
              <h2 className="font-mono font-bold text-2xl mb-6 text-cyan-400">
                Deposit Payment
              </h2>

              <div className="space-y-6">
                {/* Payment Summary */}
                <div className="p-4 bg-background rounded-lg border border-border space-y-3">
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Product:</span>
                    <span className="font-mono font-bold">{product.name}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Quantity:</span>
                    <span className="font-mono font-bold">{orderData.quantity}</span>
                  </div>
                  <div className="border-t border-border pt-3 flex justify-between">
                    <span className="text-muted-foreground font-bold">Deposit Amount:</span>
                    <span className="font-mono font-bold text-magenta-500 text-lg">
                      €{(product.deposit * orderData.quantity).toLocaleString()}
                    </span>
                  </div>
                </div>

                {/* Payment Method */}
                <div>
                  <label className="block text-sm font-mono font-bold mb-3 text-cyan-400">
                    Payment Method
                  </label>
                  <div className="space-y-2">
                    <label className="flex items-center gap-3 p-3 bg-background border border-border rounded-lg hover:border-cyan-500/50 transition cursor-pointer">
                      <input
                        type="radio"
                        name="payment"
                        value="bank-transfer"
                        checked={orderData.paymentMethod === "bank-transfer"}
                        onChange={(e) =>
                          setOrderData((prev) => ({
                            ...prev,
                            paymentMethod: e.target.value as any,
                          }))
                        }
                        className="w-4 h-4"
                      />
                      <span className="text-sm font-mono">
                        Bank Transfer (SEPA)
                      </span>
                    </label>
                    <label className="flex items-center gap-3 p-3 bg-background border border-border rounded-lg hover:border-cyan-500/50 transition cursor-pointer">
                      <input
                        type="radio"
                        name="payment"
                        value="account-debit"
                        checked={orderData.paymentMethod === "account-debit"}
                        onChange={(e) =>
                          setOrderData((prev) => ({
                            ...prev,
                            paymentMethod: e.target.value as any,
                          }))
                        }
                        className="w-4 h-4"
                      />
                      <span className="text-sm font-mono">
                        Direct Account Debit (KIWZB)
                      </span>
                    </label>
                  </div>
                </div>

                {/* Payment Details */}
                <div className="p-4 bg-magenta-500/10 border border-magenta-500/30 rounded-lg space-y-3">
                  <h3 className="font-mono font-bold text-magenta-500">Payment Instructions</h3>
                  {orderData.paymentMethod === "bank-transfer" ? (
                    <div className="text-sm space-y-2 font-mono">
                      <p>
                        <span className="text-muted-foreground">Recipient:</span> SAH GmbH
                      </p>
                      <p>
                        <span className="text-muted-foreground">IBAN:</span> DE42 6229 0110 0391 4720 03
                      </p>
                      <p>
                        <span className="text-muted-foreground">BIC:</span> GENODES1SHA
                      </p>
                      <p>
                        <span className="text-muted-foreground">Reference:</span> TCS-ORDER-{orderData.kiLegalId.slice(-4)}
                      </p>
                    </div>
                  ) : (
                    <div className="text-sm space-y-2">
                      <p>The deposit will be automatically debited from your KIWZB account.</p>
                      <p className="text-cyan-400">
                        ✓ Instant processing
                        <br />✓ No additional fees
                        <br />✓ Automatic confirmation
                      </p>
                    </div>
                  )}
                </div>

                {/* Terms */}
                <div className="p-4 bg-background border border-border rounded-lg">
                  <label className="flex items-start gap-3 cursor-pointer">
                    <input type="checkbox" className="w-4 h-4 mt-1" defaultChecked />
                    <span className="text-sm text-muted-foreground">
                      I accept the TCS Safehouse Order Terms & Conditions and understand that the deposit is non-refundable if the order is cancelled after 7 days.
                    </span>
                  </label>
                </div>
              </div>

              <div className="flex gap-3 mt-8">
                <Button
                  onClick={() => setStep("order")}
                  variant="outline"
                  className="flex-1 neon-border text-cyan-400 hover:bg-cyan-500/10"
                >
                  Back
                </Button>
                <Button
                  onClick={handlePaymentConfirm}
                  disabled={loading}
                  className="flex-1 bg-magenta-600 hover:bg-magenta-700 text-white font-mono font-bold neon-border-magenta"
                >
                  {loading ? "Processing..." : "Confirm & Pay Deposit"}
                </Button>
              </div>
            </Card>
          </div>
        )}

        {/* Step 4: Confirmation */}
        {step === "confirmation" && orderConfirmed && product && (
          <div className="max-w-2xl mx-auto">
            <Card className="bg-card border-green-500/30 neon-border p-8 text-center">
              <div className="w-16 h-16 rounded-full bg-green-500/20 flex items-center justify-center mx-auto mb-6">
                <CheckCircle className="w-8 h-8 text-green-400" />
              </div>

              <h2 className="font-mono font-bold text-2xl text-green-400 mb-2">
                Order Confirmed!
              </h2>

              <p className="text-muted-foreground mb-8">
                Your TCS Safehouse order has been successfully placed.
              </p>

              <div className="space-y-4 mb-8">
                <div className="p-4 bg-background rounded-lg border border-border text-left">
                  <p className="text-xs text-muted-foreground font-mono mb-1">ORDER NUMBER</p>
                  <p className="font-mono font-bold">TCS-ORD-2026-{Math.random().toString(36).slice(2, 8).toUpperCase()}</p>
                </div>

                <div className="p-4 bg-background rounded-lg border border-border text-left">
                  <p className="text-xs text-muted-foreground font-mono mb-1">PRODUCT</p>
                  <p className="font-mono font-bold">{product.name}</p>
                </div>

                <div className="p-4 bg-background rounded-lg border border-border text-left">
                  <p className="text-xs text-muted-foreground font-mono mb-1">DEPOSIT PAID</p>
                  <p className="font-mono font-bold text-green-400">
                    €{(product.deposit * orderData.quantity).toLocaleString()}
                  </p>
                </div>

                <div className="p-4 bg-background rounded-lg border border-border text-left">
                  <p className="text-xs text-muted-foreground font-mono mb-1">ESTIMATED DELIVERY</p>
                  <p className="font-mono font-bold">{product.deliveryTime}</p>
                </div>

                <div className="p-4 bg-background rounded-lg border border-border text-left">
                  <p className="text-xs text-muted-foreground font-mono mb-1">STATUS</p>
                  <p className="font-mono font-bold text-green-400">✓ CONFIRMED & QUEUED</p>
                </div>
              </div>

              <div className="space-y-3">
                <Button className="w-full bg-cyan-500 hover:bg-cyan-600 text-background font-mono font-bold neon-border">
                  <Download className="w-4 h-4 mr-2" />
                  Download Order Confirmation
                </Button>
                <Button
                  variant="outline"
                  className="w-full neon-border text-cyan-400 hover:bg-cyan-500/10"
                >
                  View Waitlist Status
                </Button>
                <Button
                  variant="outline"
                  className="w-full neon-border text-cyan-400 hover:bg-cyan-500/10"
                  onClick={() => setStep("products")}
                >
                  Order Another System
                </Button>
              </div>
            </Card>
          </div>
        )}
      </div>
    </div>
  );
}
