import type { Metadata } from 'next';
import './globals.css';
export const metadata: Metadata = { title: 'MandiMitra · Har Fasal Ka Sahi Sauda', description: 'Understand your crop-selling options with transparent market references, costs and voice conversations in Punjabi and Hindi.' };
export default function RootLayout({ children }: { children: React.ReactNode }) {
  return <html lang="en"><body>{children}</body></html>;
}
