import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import './globals.css'

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  metadataBase: new URL(process.env.NEXT_PUBLIC_BASE_URL || 'http://localhost:3001'),
  title: 'AICOS - Where AI Runs Your Business',
  description: 'Transform your business with AI-powered automation. AICOS helps you create content, manage workflows, and grow your business with intelligent automation.',
  keywords: 'AI automation, business automation, content creation, workflow management, AI agents, AICOS',
  openGraph: {
    title: 'AICOS - Where AI Runs Your Business',
    description: 'Transform your business with AI-powered automation',
    type: 'website',
    url: '/',
    images: [
      {
        url: '/og-image.png',
        width: 1200,
        height: 630,
        alt: 'AICOS',
      },
    ],
  },
  twitter: {
    card: 'summary_large_image',
    title: 'AICOS - Where AI Runs Your Business',
    description: 'Transform your business with AI-powered automation',
    images: ['/og-image.png'],
  },
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" className="scroll-smooth">
      <body className={inter.className}>{children}</body>
    </html>
  )
}