import Header from '@/components/Header';
import Footer from '@/components/Footer';
import styles from './page.module.css';
import { CheckCircle, Star, Shield, Truck, Package, ArrowRight } from 'lucide-react';

export const metadata = {
    title: 'Product Details | Premium Quality',
    description: 'Explore our flagship product with premium features, quality materials, and exceptional craftsmanship.',
};

export default function ProductPage() {
    return (
        <>
            <Header />
            <main className={styles.productPage}>
                <div className="container">
                    {/* Product Hero */}
                    <section className={styles.productHero}>
                        <div className={styles.productGallery}>
                            <div className={styles.mainImage}>
                                <div className={styles.imagePlaceholder}>Main Product Image</div>
                            </div>
                            <div className={styles.thumbnails}>
                                {[1, 2, 3, 4].map((i) => (
                                    <div key={i} className={styles.thumbnail}>
                                        <div className={styles.thumbPlaceholder}>Img {i}</div>
                                    </div>
                                ))}
                            </div>
                        </div>

                        <div className={styles.productDetails}>
                            <span className="badge mb-lg">Best Seller</span>
                            <h1>Premium Product Name</h1>

                            <div className={styles.rating}>
                                <div className={styles.stars}>
                                    {[...Array(5)].map((_, i) => (
                                        <Star key={i} size={20} fill="#f59e0b" color="#f59e0b" />
                                    ))}
                                </div>
                                <span>4.9 (1,247 reviews)</span>
                            </div>

                            <p className={styles.description}>
                                Experience unparalleled quality with our flagship product. Crafted with precision
                                using premium materials, this product delivers exceptional performance and lasting durability.
                            </p>

                            <div className={styles.priceBox}>
                                <div className={styles.pricing}>
                                    <span className={styles.currentPrice}>₹14,999</span>
                                    <span className={styles.originalPrice}>₹19,999</span>
                                    <span className={styles.saveTag}>Save ₹5,000</span>
                                </div>
                                <p className={styles.taxInfo}>Inclusive of all taxes</p>
                            </div>

                            <div className={styles.buyButtons}>
                                <button className="btn btn-primary btn-large">
                                    Buy Now
                                    <ArrowRight size={20} />
                                </button>
                                <button className="btn btn-secondary btn-large">
                                    Add to Cart
                                </button>
                            </div>

                            <div className={styles.deliveryInfo}>
                                <div className={styles.infoItem}>
                                    <Truck size={20} />
                                    <div>
                                        <strong>Free Delivery</strong>
                                        <span>Estimated delivery: 3-5 days</span>
                                    </div>
                                </div>
                                <div className={styles.infoItem}>
                                    <Package size={20} />
                                    <div>
                                        <strong>Easy Returns</strong>
                                        <span>30-day return policy</span>
                                    </div>
                                </div>
                                <div className={styles.infoItem}>
                                    <Shield size={20} />
                                    <div>
                                        <strong>2 Year Warranty</strong>
                                        <span>Manufacturer warranty</span>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </section>

                    {/* Product Specifications */}
                    <section className={styles.specifications}>
                        <h2>Specifications</h2>
                        <div className={styles.specGrid}>
                            {[
                                { label: 'Material', value: 'Premium Grade Aluminum' },
                                { label: 'Dimensions', value: '25 x 15 x 10 cm' },
                                { label: 'Weight', value: '500 grams' },
                                { label: 'Color', value: 'Midnight Black' },
                                { label: 'Warranty', value: '2 Years' },
                                { label: 'Origin', value: 'Made in India' },
                            ].map((spec, i) => (
                                <div key={i} className={styles.specItem}>
                                    <span className={styles.specLabel}>{spec.label}</span>
                                    <span className={styles.specValue}>{spec.value}</span>
                                </div>
                            ))}
                        </div>
                    </section>

                    {/* Features */}
                    <section className={styles.featuresSection}>
                        <h2>Key Features</h2>
                        <div className="grid grid-2">
                            {[
                                'Premium quality materials for durability',
                                'Ergonomic design for comfort',
                                'Advanced technology integration',
                                'Eco-friendly and sustainable',
                                'Easy maintenance and cleaning',
                                'Compatible with all accessories',
                            ].map((feature, i) => (
                                <div key={i} className={styles.featureItem}>
                                    <CheckCircle size={20} />
                                    <span>{feature}</span>
                                </div>
                            ))}
                        </div>
                    </section>
                </div>
            </main>
            <Footer />
        </>
    );
}
