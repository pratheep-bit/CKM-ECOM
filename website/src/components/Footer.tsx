import Link from 'next/link';
import { Mail, Phone, MapPin, Facebook, Twitter, Instagram, Youtube } from 'lucide-react';
import styles from './Footer.module.css';

const footerLinks = {
    company: [
        { href: '/about', label: 'About Us' },
        { href: '/contact', label: 'Contact' },
        { href: '/careers', label: 'Careers' },
    ],
    support: [
        { href: '/faq', label: 'FAQ' },
        { href: '/shipping', label: 'Shipping' },
        { href: '/returns', label: 'Returns' },
        { href: '/track-order', label: 'Track Order' },
    ],
    legal: [
        { href: '/privacy', label: 'Privacy Policy' },
        { href: '/terms', label: 'Terms of Service' },
        { href: '/refund', label: 'Refund Policy' },
    ],
};

export default function Footer() {
    return (
        <footer className={styles.footer}>
            <div className="container">
                <div className={styles.footerGrid}>
                    {/* Brand section */}
                    <div className={styles.brand}>
                        <Link href="/" className={styles.logo}>
                            <span className="gradient-text">BRAND</span>
                        </Link>
                        <p className={styles.tagline}>
                            Transforming experiences with premium quality products.
                        </p>
                        <div className={styles.social}>
                            <a href="#" aria-label="Facebook"><Facebook size={20} /></a>
                            <a href="#" aria-label="Twitter"><Twitter size={20} /></a>
                            <a href="#" aria-label="Instagram"><Instagram size={20} /></a>
                            <a href="#" aria-label="Youtube"><Youtube size={20} /></a>
                        </div>
                    </div>

                    {/* Links sections */}
                    <div className={styles.linksGroup}>
                        <h4>Company</h4>
                        <ul>
                            {footerLinks.company.map((link) => (
                                <li key={link.href}>
                                    <Link href={link.href}>{link.label}</Link>
                                </li>
                            ))}
                        </ul>
                    </div>

                    <div className={styles.linksGroup}>
                        <h4>Support</h4>
                        <ul>
                            {footerLinks.support.map((link) => (
                                <li key={link.href}>
                                    <Link href={link.href}>{link.label}</Link>
                                </li>
                            ))}
                        </ul>
                    </div>

                    <div className={styles.linksGroup}>
                        <h4>Contact</h4>
                        <ul>
                            <li className={styles.contactItem}>
                                <Mail size={16} />
                                <span>support@brand.com</span>
                            </li>
                            <li className={styles.contactItem}>
                                <Phone size={16} />
                                <span>+91 98765 43210</span>
                            </li>
                            <li className={styles.contactItem}>
                                <MapPin size={16} />
                                <span>Chennai, India</span>
                            </li>
                        </ul>
                    </div>
                </div>

                {/* App download */}
                <div className={styles.appDownload}>
                    <p>Download our app for the best experience</p>
                    <div className={styles.appButtons}>
                        <a href="#" className={styles.appButton}>
                            <img src="/app-store.svg" alt="App Store" width={135} height={40} />
                        </a>
                        <a href="#" className={styles.appButton}>
                            <img src="/play-store.svg" alt="Play Store" width={135} height={40} />
                        </a>
                    </div>
                </div>

                {/* Bottom bar */}
                <div className={styles.bottomBar}>
                    <p>© {new Date().getFullYear()} Brand. All rights reserved.</p>
                    <div className={styles.bottomLinks}>
                        {footerLinks.legal.map((link) => (
                            <Link key={link.href} href={link.href}>{link.label}</Link>
                        ))}
                    </div>
                </div>
            </div>
        </footer>
    );
}
