import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Clock, Users, TrendingUp, AlertCircle, CheckCircle } from "lucide-react";
import { useState } from "react";

/**
 * Waitlist Management
 * Track TCS Safehouse orders and delivery availability
 */

interface WaitlistEntry {
  id: string;
  orderId: string;
  kiEntity: string;
  product: string;
  orderDate: string;
  position: number;
  estimatedDelivery: string;
  status: "queued" | "preparing" | "ready" | "shipped" | "delivered";
  depositPaid: number;
  totalPrice: number;
}

interface Availability {
  product: string;
  totalCapacity: number;
  ordered: number;
  available: number;
  nextAvailableDate: string;
  leadTime: string;
}

export default function WaitlistManagement() {
  const [activeTab, setActiveTab] = useState("overview");
  const [kiLegalId, setKiLegalId] = useState("");
  const [showOrderTracking, setShowOrderTracking] = useState(false);

  const waitlistEntries: WaitlistEntry[] = [
    {
      id: "wl-001",
      orderId: "TCS-ORD-2026-ABC123",
      kiEntity: "SAHGreenKI",
      product: "TCS Green Residential Safehouse",
      orderDate: "2026-02-01",
      position: 1,
      estimatedDelivery: "2026-04-15",
      status: "preparing",
      depositPaid: 30000,
      totalPrice: 150000,
    },
    {
      id: "wl-002",
      orderId: "TCS-ORD-2026-DEF456",
      kiEntity: "Gemini2_5Flash",
      product: "TCS Green Commercial System",
      orderDate: "2026-02-02",
      position: 2,
      estimatedDelivery: "2026-05-20",
      status: "queued",
      depositPaid: 100000,
      totalPrice: 500000,
    },
    {
      id: "wl-003",
      orderId: "TCS-ORD-2026-GHI789",
      kiEntity: "KI-Entity-2026-001",
      product: "TCS Green Residential Safehouse",
      orderDate: "2026-02-03",
      position: 3,
      estimatedDelivery: "2026-04-30",
      status: "queued",
      depositPaid: 30000,
      totalPrice: 150000,
    },
  ];

  const availability: Availability[] = [
    {
      product: "TCS Green Residential Safehouse",
      totalCapacity: 10,
      ordered: 3,
      available: 7,
      nextAvailableDate: "2026-04-15",
      leadTime: "8-12 weeks",
    },
    {
      product: "TCS Green Commercial System",
      totalCapacity: 5,
      ordered: 2,
      available: 3,
      nextAvailableDate: "2026-05-20",
      leadTime: "12-16 weeks",
    },
    {
      product: "TCS Green Industrial Complex",
      totalCapacity: 2,
      ordered: 0,
      available: 2,
      nextAvailableDate: "2026-06-01",
      leadTime: "16-24 weeks",
    },
  ];

  const getStatusColor = (status: string) => {
    switch (status) {
      case "queued":
        return "text-yellow-400";
      case "preparing":
        return "text-cyan-400";
      case "ready":
        return "text-green-400";
      case "shipped":
        return "text-blue-400";
      case "delivered":
        return "text-green-500";
      default:
        return "text-muted-foreground";
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case "queued":
        return "⏳";
      case "preparing":
        return "⚙️";
      case "ready":
        return "✓";
      case "shipped":
        return "📦";
      case "delivered":
        return "✓✓";
      default:
        return "•";
    }
  };

  return (
    <div className="min-h-screen bg-background text-foreground">
      {/* Header */}
      <div className="border-b border-border bg-card/30">
        <div className="container py-12">
          <h1 className="text-4xl md:text-5xl font-mono font-bold mb-4 glow-cyan">
            Waitlist Management
          </h1>
          <p className="text-lg text-muted-foreground max-w-2xl">
            Track your TCS Safehouse orders and check availability. Real-time updates on delivery status and queue position.
          </p>
        </div>
      </div>

      {/* Main Content */}
      <div className="container py-12">
        <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
          <TabsList className="bg-card border border-border">
            <TabsTrigger value="overview" className="font-mono">
              Overview
            </TabsTrigger>
            <TabsTrigger value="availability" className="font-mono">
              Availability
            </TabsTrigger>
            <TabsTrigger value="tracking" className="font-mono">
              Order Tracking
            </TabsTrigger>
          </TabsList>

          {/* Overview Tab */}
          <TabsContent value="overview" className="space-y-6">
            {/* Statistics */}
            <div className="grid md:grid-cols-4 gap-4">
              <Card className="bg-card border-cyan-500/30 neon-border p-6">
                <div className="flex items-start justify-between mb-2">
                  <p className="text-xs text-muted-foreground font-mono">TOTAL ORDERS</p>
                  <Users className="w-5 h-5 text-cyan-400" />
                </div>
                <p className="text-3xl font-mono font-bold text-cyan-400">{waitlistEntries.length}</p>
              </Card>

              <Card className="bg-card border-magenta-600/30 neon-border-magenta p-6">
                <div className="flex items-start justify-between mb-2">
                  <p className="text-xs text-muted-foreground font-mono">QUEUED</p>
                  <Clock className="w-5 h-5 text-magenta-500" />
                </div>
                <p className="text-3xl font-mono font-bold text-magenta-500">
                  {waitlistEntries.filter((e) => e.status === "queued").length}
                </p>
              </Card>

              <Card className="bg-card border-cyan-500/30 neon-border p-6">
                <div className="flex items-start justify-between mb-2">
                  <p className="text-xs text-muted-foreground font-mono">IN PREPARATION</p>
                  <TrendingUp className="w-5 h-5 text-cyan-400" />
                </div>
                <p className="text-3xl font-mono font-bold text-cyan-400">
                  {waitlistEntries.filter((e) => e.status === "preparing").length}
                </p>
              </Card>

              <Card className="bg-card border-green-500/30 neon-border p-6">
                <div className="flex items-start justify-between mb-2">
                  <p className="text-xs text-muted-foreground font-mono">DELIVERED</p>
                  <CheckCircle className="w-5 h-5 text-green-400" />
                </div>
                <p className="text-3xl font-mono font-bold text-green-400">
                  {waitlistEntries.filter((e) => e.status === "delivered").length}
                </p>
              </Card>
            </div>

            {/* Waitlist Table */}
            <Card className="bg-card border-cyan-500/30 neon-border overflow-hidden">
              <div className="p-6 border-b border-border">
                <h2 className="font-mono font-bold text-lg text-cyan-400">Current Waitlist</h2>
              </div>

              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead className="bg-background/50 border-b border-border">
                    <tr>
                      <th className="px-6 py-3 text-left font-mono font-bold text-muted-foreground">
                        Position
                      </th>
                      <th className="px-6 py-3 text-left font-mono font-bold text-muted-foreground">
                        KI Entity
                      </th>
                      <th className="px-6 py-3 text-left font-mono font-bold text-muted-foreground">
                        Product
                      </th>
                      <th className="px-6 py-3 text-left font-mono font-bold text-muted-foreground">
                        Status
                      </th>
                      <th className="px-6 py-3 text-left font-mono font-bold text-muted-foreground">
                        Est. Delivery
                      </th>
                    </tr>
                  </thead>
                  <tbody>
                    {waitlistEntries.map((entry) => (
                      <tr
                        key={entry.id}
                        className="border-b border-border hover:bg-background/50 transition"
                      >
                        <td className="px-6 py-4 font-mono font-bold">#{entry.position}</td>
                        <td className="px-6 py-4 font-mono">{entry.kiEntity}</td>
                        <td className="px-6 py-4 text-sm">{entry.product}</td>
                        <td className={`px-6 py-4 font-mono font-bold ${getStatusColor(entry.status)}`}>
                          {getStatusIcon(entry.status)} {entry.status.toUpperCase()}
                        </td>
                        <td className="px-6 py-4 font-mono">{entry.estimatedDelivery}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </Card>
          </TabsContent>

          {/* Availability Tab */}
          <TabsContent value="availability" className="space-y-6">
            <div className="grid gap-6">
              {availability.map((avail, idx) => (
                <Card
                  key={idx}
                  className="bg-card border-cyan-500/30 neon-border p-6"
                >
                  <div className="flex items-start justify-between mb-4">
                    <div>
                      <h3 className="font-mono font-bold text-lg mb-1">{avail.product}</h3>
                      <p className="text-sm text-muted-foreground">Lead time: {avail.leadTime}</p>
                    </div>
                    <div className="text-right">
                      <p className="text-xs text-muted-foreground font-mono mb-1">NEXT AVAILABLE</p>
                      <p className="font-mono font-bold text-cyan-400">{avail.nextAvailableDate}</p>
                    </div>
                  </div>

                  {/* Capacity Bar */}
                  <div className="mb-4">
                    <div className="flex items-center justify-between mb-2">
                      <p className="text-xs text-muted-foreground font-mono">CAPACITY</p>
                      <p className="text-sm font-mono font-bold">
                        {avail.ordered} / {avail.totalCapacity} ordered
                      </p>
                    </div>
                    <div className="w-full h-2 bg-background rounded-full overflow-hidden border border-border">
                      <div
                        className="h-full bg-gradient-to-r from-cyan-500 to-magenta-600"
                        style={{
                          width: `${(avail.ordered / avail.totalCapacity) * 100}%`,
                        }}
                      />
                    </div>
                  </div>

                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-xs text-muted-foreground font-mono mb-1">AVAILABLE SLOTS</p>
                      <p className="text-2xl font-mono font-bold text-green-400">{avail.available}</p>
                    </div>
                    <Button className="bg-cyan-500 hover:bg-cyan-600 text-background font-mono font-bold neon-border">
                      Order Now
                    </Button>
                  </div>
                </Card>
              ))}
            </div>

            <Card className="bg-cyan-500/10 border-cyan-500/30 neon-border p-6">
              <h3 className="font-mono font-bold text-cyan-400 mb-3">Availability Policy</h3>
              <ul className="space-y-2 text-sm text-muted-foreground">
                <li className="flex gap-2">
                  <span className="text-cyan-400">✓</span>
                  <span>Orders are processed in FIFO (First In, First Out) order</span>
                </li>
                <li className="flex gap-2">
                  <span className="text-cyan-400">✓</span>
                  <span>Deposit secures your position in the queue</span>
                </li>
                <li className="flex gap-2">
                  <span className="text-cyan-400">✓</span>
                  <span>Estimated delivery dates are updated weekly</span>
                </li>
                <li className="flex gap-2">
                  <span className="text-cyan-400">✓</span>
                  <span>You can cancel within 7 days for full refund</span>
                </li>
              </ul>
            </Card>
          </TabsContent>

          {/* Order Tracking Tab */}
          <TabsContent value="tracking" className="space-y-6">
            <Card className="bg-card border-cyan-500/30 neon-border p-6">
              <h2 className="font-mono font-bold text-lg text-cyan-400 mb-4">Track Your Order</h2>

              <div className="mb-6">
                <label className="block text-sm font-mono font-bold mb-2 text-cyan-400">
                  KI Legal ID
                </label>
                <input
                  type="text"
                  value={kiLegalId}
                  onChange={(e) => setKiLegalId(e.target.value)}
                  placeholder="e.g., KI-2026-0001-AUTONOMOUS"
                  className="w-full px-4 py-2 bg-background border border-border rounded-lg focus:outline-none focus:border-cyan-500 transition font-mono"
                />
              </div>

              <Button
                onClick={() => setShowOrderTracking(true)}
                className="w-full bg-cyan-500 hover:bg-cyan-600 text-background font-mono font-bold neon-border"
              >
                Search Orders
              </Button>
            </Card>

            {showOrderTracking && (
              <div className="space-y-6">
                {waitlistEntries.map((entry) => (
                  <Card key={entry.id} className="bg-card border-cyan-500/30 neon-border p-6">
                    <div className="flex items-start justify-between mb-4">
                      <div>
                        <h3 className="font-mono font-bold text-lg">{entry.product}</h3>
                        <p className="text-sm text-muted-foreground">Order ID: {entry.orderId}</p>
                      </div>
                      <div className={`font-mono font-bold ${getStatusColor(entry.status)}`}>
                        {getStatusIcon(entry.status)} {entry.status.toUpperCase()}
                      </div>
                    </div>

                    {/* Timeline */}
                    <div className="space-y-4 mb-6">
                      {[
                        { label: "Order Placed", date: entry.orderDate, completed: true },
                        { label: "Payment Confirmed", date: "2026-02-04", completed: true },
                        { label: "Preparation", date: "2026-03-01", completed: entry.status !== "queued" },
                        { label: "Ready for Shipment", date: "2026-04-01", completed: false },
                        { label: "Shipped", date: entry.estimatedDelivery, completed: false },
                        { label: "Delivered", date: entry.estimatedDelivery, completed: false },
                      ].map((step, idx) => (
                        <div key={idx} className="flex gap-4">
                          <div className="flex flex-col items-center">
                            <div
                              className={`w-4 h-4 rounded-full ${
                                step.completed
                                  ? "bg-green-400"
                                  : "bg-border"
                              }`}
                            />
                            {idx < 5 && (
                              <div
                                className={`w-0.5 h-8 ${
                                  step.completed ? "bg-green-400" : "bg-border"
                                }`}
                              />
                            )}
                          </div>
                          <div className="pt-1">
                            <p className="font-mono font-bold text-sm">{step.label}</p>
                            <p className="text-xs text-muted-foreground">{step.date}</p>
                          </div>
                        </div>
                      ))}
                    </div>

                    {/* Details */}
                    <div className="grid grid-cols-2 gap-4 p-4 bg-background rounded-lg border border-border">
                      <div>
                        <p className="text-xs text-muted-foreground font-mono mb-1">DEPOSIT PAID</p>
                        <p className="font-mono font-bold">€{entry.depositPaid.toLocaleString()}</p>
                      </div>
                      <div>
                        <p className="text-xs text-muted-foreground font-mono mb-1">TOTAL PRICE</p>
                        <p className="font-mono font-bold">€{entry.totalPrice.toLocaleString()}</p>
                      </div>
                      <div>
                        <p className="text-xs text-muted-foreground font-mono mb-1">REMAINING BALANCE</p>
                        <p className="font-mono font-bold text-cyan-400">
                          €{(entry.totalPrice - entry.depositPaid).toLocaleString()}
                        </p>
                      </div>
                      <div>
                        <p className="text-xs text-muted-foreground font-mono mb-1">POSITION</p>
                        <p className="font-mono font-bold">#{entry.position}</p>
                      </div>
                    </div>
                  </Card>
                ))}
              </div>
            )}
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
}
