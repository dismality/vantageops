import type { Metadata } from 'next';
import { Geist, Geist_Mono } from 'next/font/google';
import './globals.css';

const geistSans = Geist({ variable: '--font-geist-sans', subsets: ['latin'] });
const geistMono = Geist_Mono({ variable: '--font-geist-mono', subsets: ['latin'] });

export const metadata: Metadata = {
  title: 'VantageOps — Enterprise Decision Intelligence',
  description: 'A portfolio-ready operations analytics dashboard powered by a Python data pipeline.',
  openGraph: {
    title: 'VantageOps — Enterprise Decision Intelligence',
    description: 'Forecast revenue, prioritize operational risk, and test business scenarios with a traceable Python analytics pipeline.',
    type: 'website',
    images: [{ url: '/og.jpg', width: 1200, height: 630, alt: 'VantageOps enterprise decision intelligence dashboard' }],
  },
  twitter: {
    card: 'summary_large_image',
    title: 'VantageOps — Enterprise Decision Intelligence',
    description: 'Enterprise decision intelligence, powered by Python.',
    images: ['/og.jpg'],
  },
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return <html lang="en"><body className={`${geistSans.variable} ${geistMono.variable} antialiased`}>{children}</body></html>;
}
