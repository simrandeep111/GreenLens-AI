import type { Metadata } from 'next';
import Link from 'next/link';
import '../styles/globals.css';

export const metadata: Metadata = {
  title: 'GreenLens AI — ESG Intelligence Platform',
  description: 'GreenLens AI processes your operational and financial records to generate a verified ESG score, emissions breakdown, and compliance report aligned with Canadian reporting standards.',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <link
          href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600&family=DM+Serif+Display:ital@0;1&family=JetBrains+Mono:wght@400;500&display=swap"
          rel="stylesheet"
        />
      </head>
      <body>
        <Navbar />
        {children}
      </body>
    </html>
  );
}

function Navbar() {
  return (
    <nav>
      <Link href="/" className="nav-logo" style={{ textDecoration: 'none' }}>
        <div className="nav-logo-mark">
          <svg viewBox="0 0 16 16" fill="none" stroke="white" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
            <path d="M8 2 C4 2 2 5 2 8 C2 12 5.5 14 8 14 C8 14 8 10 12 8 C14 7 14 4 12 3 C11 2.5 9.5 2 8 2Z"/>
            <path d="M8 14 C8 10 12 8 14 6"/>
          </svg>
        </div>
        <span className="nav-logo-text">GreenLens<span> AI</span></span>
      </Link>

      <div className="nav-tabs">
        <NavTab href="/" label="Intake" />
        <NavTab href="/processing" label="Analysis" />
        <NavTab href="/dashboard" label="Dashboard" />
        <NavTab href="/report" label="ESG Report" />
      </div>

      <div className="nav-right">
        <span className="badge-pilot">Pilot</span>
      </div>
    </nav>
  );
}

function NavTab({ href, label }: { href: string; label: string }) {
  return (
    <Link href={href} className="nav-tab">
      {label}
    </Link>
  );
}
