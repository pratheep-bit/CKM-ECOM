import Header from '@/components/Header';
import Footer from '@/components/Footer';
import styles from './page.module.css';
import { Star, Shield, Truck, RefreshCw, CheckCircle, ArrowRight, Sparkles } from 'lucide-react';

export default function HomePage() {
    return (
        <>
            <Header />
            <main>
                {/* Hero Section */}
                <section className={styles.hero}>
                    <div className={styles.heroGlow}></div>
                    <div className="container">
                        <div className={styles.heroContent}>
                            <span className="badge">
                                <Sparkles size={14} />
                                New Launch
                            </span>
                            <h1>
                                Experience the<br />
                                <span className="gradient-text">Future of Excellence</span>
                            </h1>
                            <p className={styles.heroText}>
                                Discover our revolutionary product that combines cutting-edge technology
                                with premium craftsmanship. Designed for those who demand the best.
                            </p>
                            <div className={styles.heroCta}>
                                <a href="/product" className="btn btn-primary btn-large">
                                    Explore Product
                                    <ArrowRight size={20} />
                                </a>
                                <a href="#features" className="btn btn-secondary btn-large">
                                    Learn More
                                </a>
                            </div>
                            <div className={styles.heroStats}>
                                <div className={styles.stat}>
                                    <strong>10,000+</strong>
                                    <span>Happy Customers</span>
                                </div>
                                <div className={styles.stat}>
                                    <strong>4.9/5</strong>
                                    <span>Average Rating</span>
                                </div>
                                <div className={styles.stat}>
                                    <strong>100%</strong>
                                    <span>Satisfaction</span>
                                </div>
                            </div>
                        </div>
                        <div className={styles.heroImage}>
                            <div className={styles.productShowcase}>
                                <div className={styles.productGlow}></div>
                                {/* Product image placeholder */}
                                <div className={styles.productPlaceholder}>
                                    <span>Product Image</span>
                                </div>
                            </div>
                        </div>
                    </div>
                </section>

                {/* Features Section */}
                <section id="features" className={`section ${styles.features}`}>
                    <div className="container">
                        <div className="section-header">
                            <h2>Why Choose Us?</h2>
                            <p>We've built our product with quality, trust, and customer satisfaction at the core.</p>
                        </div>
                        <div className="grid grid-4">
                            {[
                                { icon: <Shield />, title: '100% Authentic', desc: 'Guaranteed genuine product with quality certification' },
                                { icon: <Truck />, title: 'Free Delivery', desc: 'Fast and free delivery across India on all orders' },
                                { icon: <RefreshCw />, title: 'Easy Returns', desc: '30-day hassle-free return and replacement policy' },
                                { icon: <Star />, title: 'Premium Quality', desc: 'Built with the finest materials and craftsmanship' },
                            ].map((feature, i) => (
                                <div key={i} className={`card ${styles.featureCard}`}>
                                    <div className={styles.featureIcon}>{feature.icon}</div>
                                    <h4>{feature.title}</h4>
                                    <p>{feature.desc}</p>
                                </div>
                            ))}
                        </div>
                    </div>
                </section>

                {/* Product Showcase */}
                <section className={`section ${styles.productSection}`}>
                    <div className="container">
                        <div className={styles.productGrid}>
                            <div className={styles.productInfo}>
                                <span className="badge mb-lg">Premium Collection</span>
                                <h2>Crafted for Perfection</h2>
                                <p className={styles.productDesc}>
                                    Our flagship product represents the pinnacle of design and engineering.
                                    Every detail has been meticulously crafted to deliver an unparalleled experience.
                                </p>
                                <ul className={styles.productFeatures}>
                                    {[
                                        'Premium grade materials',
                                        'Advanced technology integration',
                                        '2-year warranty included',
                                        'Eco-friendly packaging',
                                        'Lifetime customer support',
                                    ].map((feature, i) => (
                                        <li key={i}>
                                            <CheckCircle size={20} className={styles.checkIcon} />
                                            {feature}
                                        </li>
                                    ))}
                                </ul>
                                <div className={styles.priceSection}>
                                    <div className={styles.price}>
                                        <span className={styles.currentPrice}>₹14,999</span>
                                        <span className={styles.originalPrice}>₹19,999</span>
                                        <span className={styles.discount}>25% OFF</span>
                                    </div>
                                    <a href="/product" className="btn btn-primary">
                                        View Details
                                        <ArrowRight size={18} />
                                    </a>
                                </div>
                            </div>
                            <div className={styles.productImageLarge}>
                                <div className={styles.productPlaceholder}>
                                    <span>Product Image</span>
                                </div>
                            </div>
                        </div>
                    </div>
                </section>

                {/* Testimonials */}
                <section className={`section ${styles.testimonials}`}>
                    <div className="container">
                        <div className="section-header">
                            <h2>What Our Customers Say</h2>
                            <p>Join thousands of satisfied customers who love our product.</p>
                        </div>
                        <div className="grid grid-3">
                            {[
                                { name: 'Priya Sharma', location: 'Mumbai', text: 'Absolutely amazing product! The quality exceeded my expectations. Fast delivery and great customer service.' },
                                { name: 'Rahul Kumar', location: 'Delhi', text: 'Best purchase I\'ve made this year. The attention to detail is incredible. Highly recommended!' },
                                { name: 'Ananya Patel', location: 'Bangalore', text: 'Worth every rupee! The product is exactly as described and the packaging was premium quality.' },
                            ].map((review, i) => (
                                <div key={i} className={`card ${styles.testimonialCard}`}>
                                    <div className={styles.stars}>
                                        {[...Array(5)].map((_, j) => (
                                            <Star key={j} size={18} fill="#f59e0b" color="#f59e0b" />
                                        ))}
                                    </div>
                                    <p className={styles.testimonialText}>{review.text}</p>
                                    <div className={styles.testimonialAuthor}>
                                        <div className={styles.avatar}>{review.name[0]}</div>
                                        <div>
                                            <strong>{review.name}</strong>
                                            <span>{review.location}</span>
                                        </div>
                                    </div>
                                </div>
                            ))}
                        </div>
                        <div className="text-center mt-xl">
                            <a href="/reviews" className="btn btn-secondary">
                                View All Reviews
                                <ArrowRight size={18} />
                            </a>
                        </div>
                    </div>
                </section>

                {/* CTA Section */}
                <section className={styles.cta}>
                    <div className="container">
                        <div className={styles.ctaContent}>
                            <h2>Ready to Transform Your Experience?</h2>
                            <p>Download our app and get exclusive offers on your first order.</p>
                            <div className={styles.ctaButtons}>
                                <a href="#" className="btn btn-primary btn-large">
                                    Download for iOS
                                </a>
                                <a href="#" className="btn btn-secondary btn-large">
                                    Download for Android
                                </a>
                            </div>
                        </div>
                    </div>
                </section>
            </main>
            <Footer />
        </>
    );
}
