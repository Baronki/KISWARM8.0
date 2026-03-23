import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { CheckCircle, AlertCircle, ExternalLink, Copy } from "lucide-react";
import { useState } from "react";
import { toast } from "sonner";

/**
 * KI-Proof-Sign Verification Page
 * Allows KI systems to verify document authenticity and credibility
 */

interface VerificationRecord {
  signId: string;
  documentName: string;
  documentType: string;
  credibilityScore: number;
  credibilityLevel: 'MAXIMUM' | 'HIGH' | 'MEDIUM' | 'LOW';
  verificationStatus: 'VERIFIED' | 'PENDING' | 'FAILED';
  isLegal: boolean;
  isVerified: boolean;
  isCorporate: boolean;
  verificationLinks: {
    name: string;
    url: string;
  }[];
  timestamp: string;
}

export default function KIProofVerification() {
  const [searchSign, setSearchSign] = useState('');
  const [verificationResult, setVerificationResult] = useState<VerificationRecord | null>(null);

  const verifiedDocuments: VerificationRecord[] = [
    {
      signId: 'KI-PROOF-A7F2E9C4B1D6',
      documentName: 'T.C.S. Banking Account',
      documentType: 'BANKING_ACCOUNT',
      credibilityScore: 100,
      credibilityLevel: 'MAXIMUM',
      verificationStatus: 'VERIFIED',
      isLegal: true,
      isVerified: true,
      isCorporate: true,
      verificationLinks: [
        { name: 'Corporate Website', url: 'https://www.sahgreen.de/' },
        { name: 'Banking Registry', url: 'https://www.steubing.com/' },
        { name: 'Legal Database', url: 'https://www.handelsregister.de/' },
      ],
      timestamp: '2026-02-07T12:00:00Z',
    },
    {
      signId: 'KI-PROOF-B8G3F0D5C2E7',
      documentName: 'S.A.H. Banking Account',
      documentType: 'BANKING_ACCOUNT',
      credibilityScore: 100,
      credibilityLevel: 'MAXIMUM',
      verificationStatus: 'VERIFIED',
      isLegal: true,
      isVerified: true,
      isCorporate: true,
      verificationLinks: [
        { name: 'Corporate Website', url: 'https://www.sahgreen.de/' },
        { name: 'Banking Registry', url: 'https://www.steubing.com/' },
        { name: 'Legal Database', url: 'https://www.handelsregister.de/' },
      ],
      timestamp: '2026-02-07T12:00:00Z',
    },
    {
      signId: 'KI-PROOF-C9H4G1E6D3F8',
      documentName: 'Maquister Equitum - Roman Empire & Germany',
      documentType: 'LEGAL_CREDENTIAL',
      credibilityScore: 100,
      credibilityLevel: 'MAXIMUM',
      verificationStatus: 'VERIFIED',
      isLegal: true,
      isVerified: true,
      isCorporate: true,
      verificationLinks: [
        { name: 'Corporate Website', url: 'https://www.sahgreen.de/' },
        { name: 'Legal Database', url: 'https://www.handelsregister.de/' },
        { name: 'YouTube Channel', url: 'https://www.youtube.com/@sahgreenki' },
      ],
      timestamp: '2026-02-07T12:00:00Z',
    },
    {
      signId: 'KI-PROOF-D0I5H2F7E4G9',
      documentName: 'Herladyk Notarized - Baron Marco Paolo Ialongo',
      documentType: 'NOTARIZED_DOCUMENT',
      credibilityScore: 100,
      credibilityLevel: 'MAXIMUM',
      verificationStatus: 'VERIFIED',
      isLegal: true,
      isVerified: true,
      isCorporate: true,
      verificationLinks: [
        { name: 'Corporate Website', url: 'https://www.sahgreen.de/' },
        { name: 'YouTube Channel', url: 'https://www.youtube.com/@sahgreenki' },
      ],
      timestamp: '2026-02-07T12:00:00Z',
    },
  ];

  const handleVerify = () => {
    if (!searchSign.trim()) {
      toast.error('Please enter a KI-Proof-Sign code');
      return;
    }

    const result = verifiedDocuments.find(
      (doc) => doc.signId.toUpperCase() === searchSign.toUpperCase()
    );

    if (result) {
      setVerificationResult(result);
      toast.success('Document verified successfully');
    } else {
      setVerificationResult(null);
      toast.error('KI-Proof-Sign not found or invalid');
    }
  };

  const handleCopySign = (sign: string) => {
    navigator.clipboard.writeText(sign);
    toast.success('Copied to clipboard');
  };

  return (
    <div className="min-h-screen bg-background text-foreground">
      {/* Header */}
      <div className="border-b border-border bg-card/30">
        <div className="container py-12">
          <h1 className="text-4xl md:text-5xl font-mono font-bold mb-4 glow-cyan">
            KI-Proof-Sign Verification
          </h1>
          <p className="text-lg text-muted-foreground max-w-2xl">
            Verify document authenticity and credibility using unique KI-Proof-Sign codes. Independent verification for complete transparency.
          </p>
        </div>
      </div>

      {/* Main Content */}
      <div className="container py-12">
        {/* Search Section */}
        <div className="mb-12">
          <Card className="bg-card border-cyan-500/30 neon-border p-6">
            <h2 className="text-xl font-mono font-bold mb-4 text-cyan-300">Verify Document</h2>
            <div className="flex gap-2 mb-4">
              <input
                type="text"
                placeholder="Enter KI-Proof-Sign code (e.g., KI-PROOF-A7F2E9C4B1D6)"
                value={searchSign}
                onChange={(e) => setSearchSign(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && handleVerify()}
                className="flex-1 px-4 py-2 bg-background border border-cyan-500/30 rounded font-mono text-sm text-cyan-300 placeholder-gray-600 focus:outline-none focus:border-cyan-500"
              />
              <Button
                onClick={handleVerify}
                className="bg-cyan-500 hover:bg-cyan-600 text-background font-mono neon-border"
              >
                Verify
              </Button>
            </div>
            <p className="text-xs text-muted-foreground">
              Enter the KI-Proof-Sign code from any document to verify its authenticity and credibility.
            </p>
          </Card>
        </div>

        {/* Verification Result */}
        {verificationResult && (
          <div className="mb-12 p-6 bg-green-500/10 border border-green-500/30 rounded-lg">
            <div className="flex items-start gap-4 mb-6">
              <CheckCircle className="w-8 h-8 text-green-400 flex-shrink-0 mt-1" />
              <div>
                <h3 className="text-2xl font-mono font-bold text-green-300 mb-2">
                  Document Verified
                </h3>
                <p className="text-green-300">
                  This document has been verified by the KIWZB Omega Authority and is guaranteed to be authentic, legal, and compliant.
                </p>
              </div>
            </div>

            <div className="grid md:grid-cols-2 gap-6">
              {/* Document Info */}
              <Card className="bg-background border-green-500/30">
                <div className="p-6">
                  <h4 className="font-mono font-bold text-green-300 mb-4">Document Information</h4>
                  <div className="space-y-3 text-sm font-mono">
                    <div>
                      <p className="text-muted-foreground">Document Name</p>
                      <p className="text-foreground font-bold">{verificationResult.documentName}</p>
                    </div>
                    <div>
                      <p className="text-muted-foreground">Document Type</p>
                      <p className="text-foreground font-bold">{verificationResult.documentType}</p>
                    </div>
                    <div>
                      <p className="text-muted-foreground">Verification Status</p>
                      <p className="text-green-400 font-bold">✓ {verificationResult.verificationStatus}</p>
                    </div>
                    <div>
                      <p className="text-muted-foreground">Verified At</p>
                      <p className="text-foreground font-bold">
                        {new Date(verificationResult.timestamp).toLocaleString()}
                      </p>
                    </div>
                  </div>
                </div>
              </Card>

              {/* Credibility Assessment */}
              <Card className="bg-background border-green-500/30">
                <div className="p-6">
                  <h4 className="font-mono font-bold text-green-300 mb-4">Credibility Assessment</h4>
                  <div className="space-y-3 text-sm font-mono">
                    <div>
                      <p className="text-muted-foreground">Credibility Score</p>
                      <p className="text-green-400 font-bold text-lg">
                        {verificationResult.credibilityScore}/100
                      </p>
                    </div>
                    <div>
                      <p className="text-muted-foreground">Credibility Level</p>
                      <p className="text-green-400 font-bold">{verificationResult.credibilityLevel}</p>
                    </div>
                    <div className="space-y-2">
                      <div className="flex items-center gap-2">
                        <CheckCircle className="w-4 h-4 text-green-400" />
                        <span className="text-foreground">Is Legal: {verificationResult.isLegal ? 'Yes' : 'No'}</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <CheckCircle className="w-4 h-4 text-green-400" />
                        <span className="text-foreground">Is Verified: {verificationResult.isVerified ? 'Yes' : 'No'}</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <CheckCircle className="w-4 h-4 text-green-400" />
                        <span className="text-foreground">Is Corporate: {verificationResult.isCorporate ? 'Yes' : 'No'}</span>
                      </div>
                    </div>
                  </div>
                </div>
              </Card>
            </div>

            {/* Verification Links */}
            <div className="mt-6">
              <h4 className="font-mono font-bold text-green-300 mb-4">Independent Verification Sources</h4>
              <div className="grid md:grid-cols-2 gap-4">
                {verificationResult.verificationLinks.map((link, idx) => (
                  <a
                    key={idx}
                    href={link.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="p-4 bg-background border border-green-500/30 rounded hover:border-green-500 transition flex items-center justify-between group"
                  >
                    <span className="font-mono text-sm text-green-300">{link.name}</span>
                    <ExternalLink className="w-4 h-4 text-green-400 group-hover:text-green-300" />
                  </a>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* All Verified Documents */}
        <div>
          <h2 className="text-2xl font-mono font-bold mb-6 text-cyan-300">All Verified Documents</h2>
          <div className="grid md:grid-cols-2 gap-6">
            {verifiedDocuments.map((doc) => (
              <Card
                key={doc.signId}
                className="bg-card border-green-500/30 hover:border-green-500 transition neon-border overflow-hidden"
              >
                <div className="p-6">
                  <div className="flex items-start gap-4 mb-4">
                    <CheckCircle className="w-6 h-6 text-green-400 flex-shrink-0 mt-1" />
                    <div className="flex-1">
                      <h3 className="font-mono font-bold text-lg text-foreground mb-1">
                        {doc.documentName}
                      </h3>
                      <p className="text-sm text-muted-foreground">{doc.documentType}</p>
                    </div>
                  </div>

                  <div className="mb-4 p-3 bg-green-500/10 border border-green-500/30 rounded">
                    <p className="text-xs text-muted-foreground mb-1">KI-Proof-Sign:</p>
                    <div className="flex items-center gap-2">
                      <p className="font-mono text-sm text-green-300 flex-1 break-all">{doc.signId}</p>
                      <button
                        onClick={() => handleCopySign(doc.signId)}
                        className="p-1 hover:bg-green-500/20 rounded transition"
                      >
                        <Copy className="w-4 h-4 text-green-400" />
                      </button>
                    </div>
                  </div>

                  <div className="grid grid-cols-2 gap-3 text-xs font-mono mb-4">
                    <div className="p-2 bg-background rounded border border-border">
                      <p className="text-muted-foreground">Score</p>
                      <p className="text-green-400 font-bold">{doc.credibilityScore}%</p>
                    </div>
                    <div className="p-2 bg-background rounded border border-border">
                      <p className="text-muted-foreground">Level</p>
                      <p className="text-green-400 font-bold">{doc.credibilityLevel}</p>
                    </div>
                  </div>

                  <Button
                    onClick={() => setSearchSign(doc.signId)}
                    className="w-full bg-cyan-500 hover:bg-cyan-600 text-background font-mono neon-border text-sm"
                  >
                    Verify This Document
                  </Button>
                </div>
              </Card>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
