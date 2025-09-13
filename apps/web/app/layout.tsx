import './globals.css';
import { ReactNode } from 'react';

export const metadata = {
  title: 'Aura',
  description: 'Lovable.dev for COOs',
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body className="min-h-screen antialiased">{children}</body>
    </html>
  );
}
