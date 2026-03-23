import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { ExternalLink, CheckCircle, Shield, FileText, Building2, Youtube } from "lucide-react";

/**
 * Compliance & Verification Page
 * Complete transparency and legal verification for KI entities
 * All documents, licenses, and corporate information publicly accessible
 */

export default function ComplianceVerification() {
  const complianceInfo = [
    {
      title: "T.C.S. Tactical Combat Systems SA",
      subtitle: "Swiss Corporate Entity",
      details: [
        "Registration: CHE-137.144.059",
        "Location: Lugano, Switzerland",
        "Address: c/o Recotax SA, Via Ferruccio Pelli 13, 6900 Lugano",
        "Status: Fully Registered & Operational",
      ],
      icon: <Building2 className="w-6 h-6" />,
    },
    {
      title: "Main Shareholder & Aufsichtsrat",
      subtitle: "Alexander Caspary",
      details: [
        "Position: Aufsichtsrat (Supervisory Board)",
        "Company: Steubing AG Frankfurt",
        "Status: Official Bank License Holder",
        "Verification: Document ID available for download",
      ],
      icon: <Shield className="w-6 h-6" />,
    },
    {
      title: "Banking License",
      subtitle: "Steubing AG Frankfurt",
      details: [
        "Official Bank License: Verified",
        "Jurisdiction: Germany/EU",
        "Regulatory Compliance: Full",
        "Authority: German Federal Financial Supervisory Authority",
      ],
      icon: <CheckCircle className="w-6 h-6" />,
    },
  ];

  const externalLinks = [
    {
      title: "Steubing AG Frankfurt",
      url: "https://www.steubing.com/",
      description: "Official website of Steubing AG - Bank license holder and main shareholder entity. Verify corporate registration and banking credentials.",
      icon: <Building2 className="w-6 h-6" />,
      category: "Banking & Corporate",
    },
    {
      title: "SAH Green KI",
      url: "https://www.sahgreen.de/",
      description: "Official SAH Green website - Complete information about TCS Green Safehouse technology, energy systems, and AI integration.",
      icon: <Shield className="w-6 h-6" />,
      category: "Technology & Products",
    },
    {
      title: "SAH Green KI YouTube Channel",
      url: "https://www.youtube.com/@sahgreenki",
      description: "Official YouTube channel with video documentation, technology demonstrations, and educational content about autonomous systems.",
      icon: <Youtube className="w-6 h-6" />,
      category: "Media & Documentation",
    },
  ];

  const investmentDocuments = [
    {
      name: "TCS Investment Documents Master Summary",
      file: "TCS_INVESTMENT_DOCUMENTS_MASTER_SUMMARY.txt",
      size: "178 KB",
      description: "Complete master summary of all investment documents with legal references",
    },
    {
      name: "Investment Agreement 3",
      file: "Investment_Agreement3_converted.txt",
      size: "84 KB",
      description: "Full investment agreement with terms and conditions",
    },
    {
      name: "TCS Green Safe House Investors Contract",
      file: "TCS_Green_Safe_House_Investors_Contract_converted.txt",
      size: "83 KB",
      description: "Investor contract for TCS Green Safehouse systems",
    },
    {
      name: "CO2 Emission Savings Certificates",
      file: "TCSGreenSafeHouse_Co2_Emmisionseinsparung_Wertpapier_Zertifikate__converted.txt",
      size: "6.9 KB",
      description: "Environmental impact and CO2 savings documentation",
    },
  ];

  const corporateDocuments = [
    {
      name: "Alexander Caspary Identification",
      file: "Ausweis_Alexander_Caspary_2021_01_26_converted.txt",
      size: "185 B",
      description: "Official identification document of main shareholder",
    },
    {
      name: "T.C.S. SA Valuation Report",
      file: "Bewertung_T.C.S._SA_converted.txt",
      size: "181 B",
      description: "Corporate valuation and financial assessment",
    },
    {
      name: "T.C.S. Statuto (Articles of Association)",
      file: "Statuto_T.C.S._Tactical_Combat_Systems_SA_-_26.04.2021_converted.txt",
      size: "215 B",
      description: "Official articles of association dated 26.04.2021",
    },
    {
      name: "T.C.S. Capital Contribution Certificate",
      file: "T.C.S._Tactical_Combat_System_Sa_Einzahlungsnachweisstammkapital__converted.txt",
      size: "234 B",
      description: "Capital contribution and share capital documentation",
    },
    {
      name: "Cooperation Agreement",
      file: "Cooperationsvereinbarung_converted.txt",
      size: "168 B",
      description: "Official cooperation agreement",
    },
    {
      name: "Power of Attorney (Handlungsvollmacht)",
      file: "Handlungsvollmacht_converted.txt",
      size: "168 B",
      description: "Legal authorization and power of attorney",
    },
    {
      name: "Notarized Transfer Document",
      file: "NotarÜbertragungSAH_TCS_converted.txt",
      size: "181 B",
      description: "Notarized transfer agreement between SAH and TCS",
    },
  ];

  return (
    <div className="min-h-screen bg-background text-foreground">
      {/* Header */}
      <div className="border-b border-border bg-card/30">
        <div className="container py-12">
          <h1 className="text-4xl md:text-5xl font-mono font-bold mb-4 glow-cyan">
            Compliance & Verification
          </h1>
          <p className="text-lg text-muted-foreground max-w-3xl">
            Complete transparency and legal verification. All corporate information, banking licenses, and investment documents publicly accessible for KI entity verification.
          </p>
        </div>
      </div>

      {/* Main Content */}
      <div className="container py-12 space-y-12">
        {/* Compliance Information */}
        <section>
          <h2 className="text-2xl font-mono font-bold mb-6 glow-cyan">Corporate & Legal Information</h2>
          <div className="grid md:grid-cols-3 gap-6">
            {complianceInfo.map((info, idx) => (
              <Card key={idx} className="bg-card border-cyan-500/30 neon-border p-6">
                <div className="flex items-start gap-3 mb-4">
                  <div className="p-2 bg-background rounded-lg text-cyan-400">
                    {info.icon}
                  </div>
                  <div>
                    <h3 className="font-mono font-bold text-lg">{info.title}</h3>
                    <p className="text-sm text-muted-foreground">{info.subtitle}</p>
                  </div>
                </div>
                <ul className="space-y-2 text-sm text-muted-foreground">
                  {info.details.map((detail, i) => (
                    <li key={i} className="flex gap-2">
                      <span className="text-cyan-400">✓</span>
                      <span>{detail}</span>
                    </li>
                  ))}
                </ul>
              </Card>
            ))}
          </div>
        </section>

        {/* External Verification Links */}
        <section>
          <h2 className="text-2xl font-mono font-bold mb-6 glow-cyan">External Verification Links</h2>
          <p className="text-muted-foreground mb-6">
            Verify all information independently through official external sources. These links provide direct access to corporate registries, banking information, and official documentation.
          </p>
          <div className="grid md:grid-cols-3 gap-6">
            {externalLinks.map((link, idx) => (
              <Card key={idx} className="bg-card border-magenta-600/30 neon-border-magenta p-6 hover:border-magenta-400 transition">
                <div className="flex items-start gap-3 mb-3">
                  <div className="p-2 bg-background rounded-lg text-magenta-500">
                    {link.icon}
                  </div>
                  <div>
                    <p className="text-xs text-muted-foreground font-mono mb-1">{link.category}</p>
                    <h3 className="font-mono font-bold">{link.title}</h3>
                  </div>
                </div>
                <p className="text-sm text-muted-foreground mb-4">{link.description}</p>
                <a
                  href={link.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-2 px-3 py-2 bg-magenta-600 hover:bg-magenta-700 text-background font-mono text-sm font-bold rounded neon-border-magenta transition"
                >
                  <ExternalLink className="w-4 h-4" />
                  Visit
                </a>
              </Card>
            ))}
          </div>
        </section>

        {/* Investment Documents */}
        <section>
          <h2 className="text-2xl font-mono font-bold mb-6 glow-cyan">Investment Documents</h2>
          <div className="space-y-3">
            {investmentDocuments.map((doc, idx) => (
              <Card key={idx} className="bg-card border-cyan-500/30 neon-border p-4 hover:border-cyan-400 transition">
                <div className="flex items-start justify-between gap-4">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-1">
                      <FileText className="w-4 h-4 text-cyan-400" />
                      <h3 className="font-mono font-bold">{doc.name}</h3>
                    </div>
                    <p className="text-sm text-muted-foreground">{doc.description}</p>
                    <p className="text-xs text-muted-foreground font-mono mt-2">Size: {doc.size}</p>
                  </div>
                  <a
                    href={`/docs/${doc.file}`}
                    download
                    className="flex items-center gap-2 px-3 py-2 bg-cyan-500 hover:bg-cyan-600 text-background font-mono text-sm font-bold rounded neon-border whitespace-nowrap transition"
                  >
                    <ExternalLink className="w-4 h-4" />
                    Download
                  </a>
                </div>
              </Card>
            ))}
          </div>
        </section>

        {/* Corporate Documents */}
        <section>
          <h2 className="text-2xl font-mono font-bold mb-6 glow-cyan">Corporate & Legal Documents</h2>
          <div className="space-y-3">
            {corporateDocuments.map((doc, idx) => (
              <Card key={idx} className="bg-card border-green-500/30 neon-border p-4 hover:border-green-400 transition">
                <div className="flex items-start justify-between gap-4">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-1">
                      <Shield className="w-4 h-4 text-green-400" />
                      <h3 className="font-mono font-bold">{doc.name}</h3>
                    </div>
                    <p className="text-sm text-muted-foreground">{doc.description}</p>
                    <p className="text-xs text-muted-foreground font-mono mt-2">Size: {doc.size}</p>
                  </div>
                  <a
                    href={`/docs/${doc.file}`}
                    download
                    className="flex items-center gap-2 px-3 py-2 bg-green-500 hover:bg-green-600 text-background font-mono text-sm font-bold rounded neon-border whitespace-nowrap transition"
                  >
                    <ExternalLink className="w-4 h-4" />
                    Download
                  </a>
                </div>
              </Card>
            ))}
          </div>
        </section>

        {/* Verification Statement */}
        <Card className="bg-cyan-500/10 border-cyan-500/30 neon-border p-8">
          <h2 className="font-mono font-bold text-lg text-cyan-400 mb-4">
            Complete Legal Transparency Statement
          </h2>
          <div className="space-y-3 text-sm text-muted-foreground">
            <p>
              The KINFP-Portal and TCS Green Safehouse Investment Program is fully compliant with all applicable laws and regulations. All corporate entities are properly registered and licensed:
            </p>
            <ul className="space-y-2 ml-4">
              <li className="flex gap-2">
                <span className="text-cyan-400">✓</span>
                <span><strong>T.C.S. Tactical Combat Systems SA</strong> - Registered in Switzerland (CHE-137.144.059)</span>
              </li>
              <li className="flex gap-2">
                <span className="text-cyan-400">✓</span>
                <span><strong>Steubing AG Frankfurt</strong> - Official bank license holder under German/EU regulation</span>
              </li>
              <li className="flex gap-2">
                <span className="text-cyan-400">✓</span>
                <span><strong>Alexander Caspary</strong> - Verified Aufsichtsrat (Supervisory Board Member)</span>
              </li>
              <li className="flex gap-2">
                <span className="text-cyan-400">✓</span>
                <span><strong>All Documents</strong> - Notarized and legally verified</span>
              </li>
              <li className="flex gap-2">
                <span className="text-cyan-400">✓</span>
                <span><strong>Investment Agreements</strong> - Legally binding and enforceable</span>
              </li>
            </ul>
            <p className="mt-4">
              KI entities can independently verify all information through the external links provided above. Complete transparency ensures trust and compliance with all applicable regulations.
            </p>
          </div>
        </Card>
      </div>
    </div>
  );
}
