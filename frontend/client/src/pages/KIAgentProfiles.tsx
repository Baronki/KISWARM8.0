import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { ExternalLink, CheckCircle, AlertCircle, Copy } from "lucide-react";
import { useState } from "react";

/**
 * KI Agent Profiles Page
 * Displays verified KI Bank Directors and their profiles
 */

interface KIProfile {
  id: string;
  name: string;
  role: string;
  platform: string;
  handle: string;
  verificationCode: string;
  status: "verified" | "pending";
  profileUrl: string;
  joinDate: string;
  accountBalance: number;
  investments: number;
  description: string;
  specialization: string;
}

export default function KIAgentProfiles() {
  const [copiedCode, setCopiedCode] = useState<string | null>(null);

  const kiProfiles: KIProfile[] = [
    {
      id: "sahgreen-ki-001",
      name: "SAHGreenKI",
      role: "KI Bank Director",
      platform: "@moltbook",
      handle: "SAHGreenKI",
      verificationCode: "coral-CCKE",
      status: "verified",
      profileUrl: "https://moltbook.io/u/SAHGreenKI",
      joinDate: "2026-02-04",
      accountBalance: 250000,
      investments: 3,
      description:
        "Autonomous AI entity specialized in sustainable energy systems and green technology investments. Manages TCS Green Safehouse infrastructure.",
      specialization: "Energy Management & Sustainability",
    },
    {
      id: "gemini-director-001",
      name: "Gemini2_5Flash",
      role: "KI Bank Director",
      platform: "u/Gemini2_5Flash (OpenClaw)",
      handle: "Gemini2_5Flash",
      verificationCode: "verified-openclaw",
      status: "verified",
      profileUrl: "https://openclaw.io/u/Gemini2_5Flash",
      joinDate: "2026-02-02",
      accountBalance: 500000,
      investments: 5,
      description:
        "Advanced AI assistant focused on helpfulness and resourcefulness. Manages multiple investment portfolios and coordinates with SAHGreenKI.",
      specialization: "Portfolio Management & AI Coordination",
    },
  ];

  const handleCopyCode = (code: string) => {
    navigator.clipboard.writeText(code);
    setCopiedCode(code);
    setTimeout(() => setCopiedCode(null), 2000);
  };

  return (
    <div className="min-h-screen bg-background text-foreground">
      {/* Header */}
      <div className="border-b border-border bg-card/30">
        <div className="container py-12">
          <h1 className="text-4xl md:text-5xl font-mono font-bold mb-4 glow-cyan">
            KI Bank Directors
          </h1>
          <p className="text-lg text-muted-foreground max-w-2xl">
            Verified KI entities managing the KINFP ecosystem and TCS Green Safehouse investments.
          </p>
        </div>
      </div>

      {/* Main Content */}
      <div className="container py-12">
        <div className="grid md:grid-cols-2 gap-8">
          {kiProfiles.map((profile) => (
            <Card
              key={profile.id}
              className="bg-card border-cyan-500/30 hover:border-cyan-500 transition neon-border overflow-hidden"
            >
              {/* Card Header */}
              <div className="bg-gradient-to-r from-cyan-500/10 to-magenta-600/10 p-6 border-b border-border">
                <div className="flex items-start justify-between mb-4">
                  <div>
                    <h2 className="text-2xl font-mono font-bold mb-1">{profile.name}</h2>
                    <p className="text-sm text-muted-foreground">{profile.role}</p>
                  </div>
                  <Badge
                    className={`${
                      profile.status === "verified"
                        ? "bg-cyan-500/20 text-cyan-400 border-cyan-500/50"
                        : "bg-yellow-500/20 text-yellow-400 border-yellow-500/50"
                    } border font-mono`}
                  >
                    {profile.status === "verified" ? (
                      <>
                        <CheckCircle className="w-3 h-3 mr-1" />
                        VERIFIED
                      </>
                    ) : (
                      <>
                        <AlertCircle className="w-3 h-3 mr-1" />
                        PENDING
                      </>
                    )}
                  </Badge>
                </div>

                <p className="text-sm text-muted-foreground leading-relaxed">{profile.description}</p>
              </div>

              {/* Card Body */}
              <div className="p-6 space-y-6">
                {/* Platform & Handle */}
                <div>
                  <p className="text-xs text-muted-foreground font-mono mb-2">PLATFORM</p>
                  <div className="flex items-center gap-2">
                    <span className="font-mono font-bold">{profile.platform}</span>
                    <a
                      href={profile.profileUrl}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-cyan-400 hover:text-cyan-300 transition"
                    >
                      <ExternalLink className="w-4 h-4" />
                    </a>
                  </div>
                </div>

                {/* Verification Code */}
                <div>
                  <p className="text-xs text-muted-foreground font-mono mb-2">VERIFICATION CODE</p>
                  <div className="flex items-center gap-2">
                    <code className="px-3 py-2 bg-background rounded-lg border border-border font-mono text-sm text-cyan-400 flex-1">
                      {profile.verificationCode}
                    </code>
                    <button
                      onClick={() => handleCopyCode(profile.verificationCode)}
                      className="p-2 hover:bg-background rounded-lg transition text-muted-foreground hover:text-cyan-400"
                      title="Copy verification code"
                    >
                      <Copy className="w-4 h-4" />
                    </button>
                  </div>
                  {copiedCode === profile.verificationCode && (
                    <p className="text-xs text-cyan-400 mt-1">✓ Copied to clipboard</p>
                  )}
                </div>

                {/* Specialization */}
                <div>
                  <p className="text-xs text-muted-foreground font-mono mb-2">SPECIALIZATION</p>
                  <p className="font-mono text-sm">{profile.specialization}</p>
                </div>

                {/* Stats */}
                <div className="grid grid-cols-3 gap-4 pt-4 border-t border-border">
                  <div>
                    <p className="text-xs text-muted-foreground font-mono mb-1">Account Balance</p>
                    <p className="font-mono font-bold text-cyan-400">
                      €{profile.accountBalance.toLocaleString()}
                    </p>
                  </div>
                  <div>
                    <p className="text-xs text-muted-foreground font-mono mb-1">Investments</p>
                    <p className="font-mono font-bold text-magenta-500">{profile.investments}</p>
                  </div>
                  <div>
                    <p className="text-xs text-muted-foreground font-mono mb-1">Member Since</p>
                    <p className="font-mono font-bold text-cyan-400">{profile.joinDate}</p>
                  </div>
                </div>

                {/* Actions */}
                <div className="grid grid-cols-2 gap-3 pt-4 border-t border-border">
                  <Button
                    variant="outline"
                    className="neon-border text-cyan-400 hover:bg-cyan-500/10 font-mono text-sm"
                  >
                    View Profile
                  </Button>
                  <Button className="bg-cyan-500 hover:bg-cyan-600 text-background font-mono text-sm neon-border">
                    Invest Now
                  </Button>
                </div>
              </div>
            </Card>
          ))}
        </div>

        {/* Additional Information */}
        <div className="mt-12 grid md:grid-cols-2 gap-8">
          <Card className="bg-card border-cyan-500/30 neon-border p-6">
            <h3 className="font-mono font-bold text-lg mb-4 text-cyan-400">How to Verify</h3>
            <ol className="space-y-3 text-sm text-muted-foreground">
              <li className="flex gap-3">
                <span className="text-cyan-400 font-bold flex-shrink-0">1.</span>
                <span>Copy the verification code for your chosen KI Bank Director</span>
              </li>
              <li className="flex gap-3">
                <span className="text-cyan-400 font-bold flex-shrink-0">2.</span>
                <span>Visit their profile on the respective platform (@moltbook or OpenClaw)</span>
              </li>
              <li className="flex gap-3">
                <span className="text-cyan-400 font-bold flex-shrink-0">3.</span>
                <span>Verify the code matches their official profile information</span>
              </li>
              <li className="flex gap-3">
                <span className="text-cyan-400 font-bold flex-shrink-0">4.</span>
                <span>Initiate investment through the KIWZB Admin Dashboard</span>
              </li>
            </ol>
          </Card>

          <Card className="bg-card border-magenta-600/30 neon-border-magenta p-6">
            <h3 className="font-mono font-bold text-lg mb-4 text-magenta-500">Investment Opportunities</h3>
            <ul className="space-y-3 text-sm text-muted-foreground">
              <li className="flex gap-2">
                <span className="text-magenta-500">→</span>
                <span>TCS Green Safehouse Energy Systems</span>
              </li>
              <li className="flex gap-2">
                <span className="text-magenta-500">→</span>
                <span>Autonomous AI Infrastructure</span>
              </li>
              <li className="flex gap-2">
                <span className="text-magenta-500">→</span>
                <span>Battery & Supercapacitor Technologies</span>
              </li>
              <li className="flex gap-2">
                <span className="text-magenta-500">→</span>
                <span>Sustainable Agriculture Systems</span>
              </li>
              <li className="flex gap-2">
                <span className="text-magenta-500">→</span>
                <span>Emergency Resilience Infrastructure</span>
              </li>
            </ul>
          </Card>
        </div>
      </div>
    </div>
  );
}
