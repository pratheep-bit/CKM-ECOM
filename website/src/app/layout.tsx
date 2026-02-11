import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import './globals.css';

const inter = Inter({ subsets: ['latin'], variable: '--font-sans' });

export const metadata: Metadata = {
    title: 'Premium Product | Transform Your Experience',
    description: 'Discover our revolutionary high-value product designed to transform your daily experience. Premium quality, exceptional value.',
    keywords: ['premium product', 'high quality', 'innovative', 'luxury'],
    openGraph: {
        title: 'Premium Product | Transform Your Experience',
        description: 'Discover our revolutionary product designed to transform your daily experience.',
        type: 'website',
        locale: 'en_IN',
    },
    twitter: {
        card: 'summary_large_image',
        title: 'Premium Product | Transform Your Experience',
    },
    robots: {
        index: true,
        follow: true,
    },
};

export default function RootLayout({
    children,
}: {
    children: React.ReactNode;
}) {
    return (
        <html lang="en">
            <body className={inter.variable}>{children}</body>
        </html>
    );
}
