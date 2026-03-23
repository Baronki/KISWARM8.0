import { Zap, Shield, Leaf, Cpu, Download, ExternalLink } from 'lucide-react';
import { Button } from '@/components/ui/button';
import ImageGallery from '@/components/ImageGallery';

export default function TCSGreenSafeHouse() {
  return (
    <div className="min-h-screen bg-background text-foreground">
      {/* Hero Section */}
      <div className="relative border-b border-border overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-r from-cyan-500/5 to-magenta-500/5" />
        <div className="container py-16 relative">
          <div className="max-w-3xl">
            <h1 className="text-5xl font-bold mb-4 font-mono">
              TCS GREEN Safe House
            </h1>
            <p className="text-xl text-muted-foreground mb-6">
              Autarkes EMS-Microgrid-System – Serienproduktion angelaufen
            </p>
            <div className="flex flex-wrap gap-4 text-sm">
              <span className="flex items-center gap-2 text-cyan-400">
                <Zap className="w-4 h-4" /> 100% Selbstversorgung
              </span>
              <span className="flex items-center gap-2 text-cyan-400">
                <Shield className="w-4 h-4" /> Permanente USV
              </span>
              <span className="flex items-center gap-2 text-cyan-400">
                <Leaf className="w-4 h-4" /> Black-Start-fähig
              </span>
              <span className="flex items-center gap-2 text-cyan-400">
                <Cpu className="w-4 h-4" /> EMP-sicher
              </span>
            </div>
          </div>
        </div>
      </div>

      <div className="container py-12 space-y-16">
        {/* Über uns */}
        <section>
          <h2 className="text-3xl font-bold mb-8">Über uns</h2>
          <div className="bg-card border border-border rounded-lg p-8 space-y-4">
            <p className="text-muted-foreground">
              Seit mehr als 20 Jahren stehen wir für Zuverlässigkeit, Nachhaltigkeit und Verantwortung.
            </p>
            <p className="text-muted-foreground">
              Die <strong>T.C.S. Tactical Combat Systems SA</strong> (CHE-137.144.059, Lugano) vereint über 30 Jahre Erfahrung im industriellen Engineering:
            </p>
            <ul className="space-y-2 text-muted-foreground list-disc list-inside">
              <li>Industrielles, petrochemisches Engineering</li>
              <li>Militärisches Engineering</li>
              <li>Energieverteilungsplanung im Kernkraftwerksbereich sowie dessen Bau</li>
              <li>Verfahrenstechnisches Engineering</li>
              <li>Entwicklung und Initiator des EMS-autarken Energiesystems Green Safe House</li>
            </ul>
            <p className="text-muted-foreground">
              Führender Systemlieferant für Prozessmesstechnik, Anlagentechnik, Steuerungstechnik und Prozessvisualisierung in der industriellen Verfahrenstechnik.
            </p>
          </div>
        </section>

        {/* Timeline */}
        <section>
          <h2 className="text-3xl font-bold mb-8">Historie & Meilensteine</h2>
          <div className="space-y-4">
            {[
              { year: '2015', title: 'Gründung TCS SA', desc: 'Gründung TCS SA in Lugano (aus TCS AG Zug 2009). Fokus auf innovative Energiespeichertechnologien.' },
              { year: '2015–2019', title: 'Entwicklung Green Safe House', desc: 'Entwicklung des EMS-autarken Systems "Green Safe House".' },
              { year: '2019–2021', title: 'Ersterprobung', desc: 'Ersterprobung und Proof-of-Concept.' },
              { year: '2021–2022', title: 'Großangelegte Testphase', desc: 'Großangelegte interne Testphase.' },
              { year: '2023', title: 'Kleinserienproduktion', desc: 'Beginn der Kleinserienproduktion.' },
              { year: '2026', title: 'Serienproduktion', desc: 'Serienproduktion angelaufen – skalierbare Fertigung läuft.' }
            ].map((item, i) => (
              <div key={i} className="flex gap-4 pb-4 border-b border-border last:border-0">
                <div className="w-24 flex-shrink-0">
                  <span className="font-mono font-bold text-cyan-400">{item.year}</span>
                </div>
                <div className="flex-1">
                  <h3 className="font-bold mb-1">{item.title}</h3>
                  <p className="text-sm text-muted-foreground">{item.desc}</p>
                </div>
              </div>
            ))}
          </div>
        </section>

        {/* Geschäftsfelder */}
        <section>
          <h2 className="text-3xl font-bold mb-8">Geschäftsfelder – Autarkes EMS-System</h2>
          <div className="bg-card border border-border rounded-lg p-8 space-y-6">
            <p className="text-muted-foreground">
              Das autarke EMS-System "Green Safe House" entstand aus langjähriger Anlagenbau-Erfahrung. Ziel: Ein robustes, effizientes und sicheres System für Autarkie und Effizienz – basierend auf innovativer Kondensator-/Graphen-Speichertechnologie.
            </p>
            <p className="text-muted-foreground">
              <strong>Komponenten:</strong> Bewährte Standards (Wärmepumpen, Solarzellen, Ersatzstromanlage) + neue Entwicklungen (Inverter, Graphenspeicher, Superkondensatoren). Der Inverter bleibt bei Netzausfall funktionsfähig.
            </p>
            <ImageGallery
              images={[
                {
                  id: 'prod-1',
                  src: 'https://images.unsplash.com/photo-1581092918056-0c4c3acd3789?w=800&h=600&fit=crop',
                  title: 'Produktionshalle',
                  description: 'Moderne Produktionshalle mit integrierten Schaltschränken und Steuerungssystemen',
                  category: 'Production'
                },
                {
                  id: 'tech-1',
                  src: 'https://images.unsplash.com/photo-1581092918056-0c4c3acd3789?w=800&h=600&fit=crop',
                  title: 'RCCS System',
                  description: 'Reactiv Compensation Current System für optimale Stromverteilung',
                  category: 'Technology'
                },
                {
                  id: 'assembly-1',
                  src: 'https://images.unsplash.com/photo-1581092918056-0c4c3acd3789?w=800&h=600&fit=crop',
                  title: 'Gehäusemontage',
                  description: 'Präzisionsmontage von Gehäusen und Komponenten',
                  category: 'Assembly'
                },
                {
                  id: 'cabinet-1',
                  src: 'https://images.unsplash.com/photo-1581092918056-0c4c3acd3789?w=800&h=600&fit=crop',
                  title: 'Schaltschrank',
                  description: 'Weiße Schaltschrank-Montage mit integrierten Steuerungen',
                  category: 'Cabinet'
                },
                {
                  id: 'energy-1',
                  src: 'https://images.unsplash.com/photo-1581092918056-0c4c3acd3789?w=800&h=600&fit=crop',
                  title: 'Energiespeicher',
                  description: 'Graphen-Superkondensator Energiespeichersystem',
                  category: 'Technology'
                },
                {
                  id: 'testing-1',
                  src: 'https://images.unsplash.com/photo-1581092918056-0c4c3acd3789?w=800&h=600&fit=crop',
                  title: 'Qualitätskontrolle',
                  description: 'Umfangreiche Testphase und Qualitätssicherung',
                  category: 'Testing'
                }
              ]}
            />
          </div>
        </section>

        {/* Zentrale Plattform */}
        <section>
          <h2 className="text-3xl font-bold mb-8">Die Zentrale Plattform – Technologie</h2>
          <div className="bg-card border border-border rounded-lg p-8 space-y-6">
            <p className="text-muted-foreground">
              <strong>TCS GREEN Safe House</strong> ersetzt den konventionellen Hausverteiler durch eine multifunktionale, zukunftssichere Stromversorgungseinheit. 100 % Selbstversorgung aus allen verfügbaren grünen Energiequellen – ohne Netzanschlusszwang und ohne Einspeisung.
            </p>
            
            <h3 className="text-xl font-bold">All-in-One Features</h3>
            <div className="grid md:grid-cols-2 gap-4">
              {[
                'State-of-the-Art Power Electric Box gem. §14a EnWG + VDE-AR-N 4105 + 4100',
                'Automatische Netztrennung Netzebene 7',
                'Komplette Online-USV für Haushaltsstromversorgung',
                'Über-/Unterspannungsschutz vom Netz',
                'Blitzschutz integriert',
                '100 % EMP-Sicherheit nach NATO-Militärstandard',
                '100 % Selbstversorgung & Black-Start-fähig',
                '100 % kontinuierlicher Betrieb',
                'Weltweit einzigartig: Alle Energieerzeuger simultan nutzbar',
                'Parallele Addition aller Energieformen',
                '100 % Phasenunsymmetrie-fähig',
                'Frequenzunabhängig (50/60 Hz intern/extern)',
                'PV/Wind/Wasser-Elektrik + Sicherheitsvorschriften integriert',
                'Überschuss-Ladefunktion + Wallbox inklusive',
                'Einstellbare gedrosselte 3-Phasen-Synchron-Netzunterdeckung'
              ].map((feature, i) => (
                <div key={i} className="flex gap-2 text-sm">
                  <Zap className="w-4 h-4 text-cyan-400 flex-shrink-0 mt-0.5" />
                  <span className="text-muted-foreground">{feature}</span>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* Zählerplatz & PV-Normen */}
        <section>
          <h2 className="text-3xl font-bold mb-8">Zählerplatztechnik & Normenkonforme PV-Integration</h2>
          <div className="bg-card border border-border rounded-lg p-8 space-y-4">
            <p className="text-muted-foreground">
              Steckbare EHZ2-Zähleranschlusstechnik inkl. Smart-Meter-Konformität werkseitig integriert. Vollständige physikalische Abkopplung nach VDE-AR-N 4105 im Autarkiebetrieb. Automatischer Netz-Eigenstrom-Umschalter (IEC 60947-6-1 / 60947-3).
            </p>
            <p className="text-muted-foreground">
              <strong>Normen:</strong> DIN EN 61439-1/2, DIN VDE 0603-1, DIN VDE 0100-712, DIN EN 62446-1, DIN EN 62305-3 Beibl. 5, VDI 6012, VDE-AR-N 4105, VDE-AR-N 2100-712 u.v.m.
            </p>
          </div>
        </section>

        {/* Steuerungssystem */}
        <section>
          <h2 className="text-3xl font-bold mb-8">Zentrales Steuerungssystem – Autarkie Heyd-Tec</h2>
          <div className="bg-card border border-border rounded-lg p-8 space-y-4">
            <p className="text-muted-foreground">
              Selbstoptimierende <strong>Hybrid Fuzzy Logic Energiemanagement-KI</strong> mit automatisierter 4-fach redundanter Versorgungssicherheitssteuerung. Engineered and Designed by Kevin Heyd.
            </p>
            <p className="text-muted-foreground">
              Optimiert Betrieb/Verbrauch förderfähiger Wärmeerzeugung. Inkl. Sensoren, Aktoren, Datenlogger, Strom-/Wärmemessung. Speichert alle Verbräuche & Kosten für digitale Optimierung. Displays & Interface werkseitig im EVU-Messstellenplatz verplombt integriert.
            </p>
          </div>
        </section>

        {/* Downloads */}
        <section>
          <h2 className="text-3xl font-bold mb-8">Technische Dokumentation</h2>
          <div className="grid md:grid-cols-2 gap-6">
            {[
              {
                title: 'TCS Green Safe House',
                desc: 'Vollständige technische Dokumentation',
                file: 'TCSGreenSafeHouse.8pdf.pdf',
                size: '13 MB'
              },
              {
                title: 'TCS Core Platform KI Technologie',
                desc: 'KI-Technologie und Steuerungssystem',
                file: 'TCS Core PlattformKI Technologie.pdf',
                size: '1.5 MB'
              }
            ].map((doc, i) => (
              <a
                key={i}
                href={`/docs/${doc.file}`}
                target="_blank"
                rel="noopener noreferrer"
                className="bg-card border border-cyan-500/30 rounded-lg p-6 hover:border-cyan-500/50 transition group"
              >
                <div className="flex gap-4">
                  <Download className="w-6 h-6 text-cyan-400 flex-shrink-0 group-hover:scale-110 transition" />
                  <div className="flex-1">
                    <h3 className="font-bold mb-1">{doc.title}</h3>
                    <p className="text-sm text-muted-foreground mb-2">{doc.desc}</p>
                    <p className="text-xs text-muted-foreground">{doc.size}</p>
                  </div>
                </div>
              </a>
            ))}
          </div>
        </section>

        {/* External Links */}
        <section>
          <h2 className="text-3xl font-bold mb-8">Offizielle Ressourcen</h2>
          <div className="grid md:grid-cols-3 gap-4">
            {[
              {
                name: 'SAH Green Website',
                url: 'https://www.sahgreen.de',
                icon: '🌐'
              },
              {
                name: 'YouTube Channel',
                url: 'https://www.youtube.com/@sahgreenki',
                icon: '📺'
              },
              {
                name: 'Steubing AG',
                url: 'https://www.steubing.com',
                icon: '🏦'
              }
            ].map((link, i) => (
              <a
                key={i}
                href={link.url}
                target="_blank"
                rel="noopener noreferrer"
                className="bg-card border border-border rounded-lg p-6 hover:border-cyan-500/50 transition flex items-center justify-between group"
              >
                <div>
                  <div className="text-2xl mb-2">{link.icon}</div>
                  <p className="font-bold text-sm">{link.name}</p>
                </div>
                <ExternalLink className="w-5 h-5 text-muted-foreground group-hover:text-cyan-400 transition" />
              </a>
            ))}
          </div>
        </section>
      </div>
    </div>
  );
}
