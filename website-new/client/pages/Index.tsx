import { useNavigate } from "react-router-dom";
import { ArrowRight, Star, ArrowLeft, Loader2 } from "lucide-react";
import Header from "@/components/Header";
import Footer from "@/components/Footer";
import { useCart } from "@/context/CartContext";
import { useAuth } from "@/context/AuthContext";
import { useProducts } from "@/hooks/useApi";
import { toast } from "sonner";

export default function Index() {
  const navigate = useNavigate();
  const { addToCart } = useCart();
  const { isLoggedIn } = useAuth();
  const { data: productsResponse, isLoading } = useProducts();

  // Find the featured product by slug from the product list
  // productsResponse.data = axios response.data = { items: [...], total, page, page_size }
  const productData = (() => {
    const apiData = productsResponse?.data;
    const items = apiData?.items || (Array.isArray(apiData) ? apiData : []);
    const product = Array.isArray(items) ? items.find((p: any) => p.slug === "karungali-mala-108") || items[0] : null;
    return product ? { data: product } : null;
  })();

  const handleBuyNow = async () => {
    if (!productData?.data) return;

    try {
      await addToCart(productData.data, 1);
      // Logged-in users go straight to checkout; guests go to cart
      // (avoids checkout → login → cart-merge timing race)
      if (isLoggedIn) {
        navigate("/checkout");
      } else {
        navigate("/cart");
      }
    } catch (error) {
      toast.error("Failed to add to cart");
    }
  };

  return (
    <div className="min-h-screen bg-white">
      <Header />

      {/* Hero Section */}
      <section className="relative h-[80vh] md:h-screen flex items-center justify-center bg-gradient-to-b from-[#5C4033] to-[#4A3527]">
        <div
          className="absolute inset-0 opacity-60"
          style={{
            backgroundImage: "url('https://images.unsplash.com/photo-1603201667141-5a2d4c673378?q=80&w=2070')",
            backgroundSize: "cover",
            backgroundPosition: "center",
          }}
        />

        <div className="relative z-10 text-center px-4 max-w-4xl mx-auto">
          <h1 className="font-serif text-4xl md:text-6xl lg:text-7xl text-white font-light leading-tight mb-8">
            Experience the<br />
            Natural Power of<br />
            Karungali Mala
          </h1>

          <button
            onClick={handleBuyNow}
            disabled={isLoading || !productData?.data}
            className="inline-flex items-center gap-2 bg-white text-[#765341] px-8 py-3 hover:bg-opacity-90 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : "Buy Now"}
            {!isLoading && <ArrowRight className="w-4 h-4" />}
          </button>
        </div>

        {/* Side Navigation */}
        <div className="hidden md:flex absolute left-8 top-1/2 -translate-y-1/2 flex-col gap-8 text-white">
          <button className="hover:opacity-70 transition-opacity">
            <ArrowRight className="w-5 h-5" />
          </button>
          <div className="flex flex-col gap-2">
            <div className="w-1 h-1 bg-white rounded-full"></div>
            <div className="w-1 h-1 bg-white rounded-full opacity-50"></div>
            <div className="w-1 h-1 bg-white rounded-full opacity-50"></div>
          </div>
          <button className="hover:opacity-70 transition-opacity">
            <ArrowLeft className="w-5 h-5" />
          </button>
        </div>
      </section>

      {/* Features Section */}
      <section className="py-16 md:py-24 px-4 bg-gradient-to-r from-[#F2F6EF] to-[#F3E9DC]">
        <div className="max-w-7xl mx-auto grid grid-cols-1 md:grid-cols-2 gap-12 md:gap-16">
          <div className="flex flex-col justify-center">
            <h2 className="font-serif text-3xl md:text-5xl text-[#765341] font-light leading-tight mb-4">
              Inspired by Tradition,<br />
              Made for Everyday Life
            </h2>
          </div>

          <div className="flex flex-col gap-8">
            <div className="flex gap-4">
              <div className="flex-shrink-0">
                <div className="w-12 h-12 rounded-full border-2 border-[#765341] flex items-center justify-center">
                  <span className="text-xs text-[#765341]">100%</span>
                </div>
              </div>
              <div>
                <h3 className="text-lg font-medium text-[#765341] mb-2">Authentic Karungali Wood</h3>
                <p className="text-sm text-[#765341] leading-relaxed">
                  Crafted using natural karungali wood valued for its spiritual and wellness significance.
                </p>
              </div>
            </div>

            <div className="flex gap-4">
              <div className="flex-shrink-0">
                <div className="w-12 h-12 flex items-center justify-center">
                  <svg width="32" height="32" viewBox="0 0 32 32" fill="none" className="text-[#765341]">
                    <path d="M16 4L18 14L16 24L14 14L16 4Z" stroke="currentColor" strokeWidth="1.5" />
                    <circle cx="16" cy="8" r="1" fill="currentColor" />
                    <circle cx="16" cy="16" r="1" fill="currentColor" />
                    <circle cx="16" cy="24" r="1" fill="currentColor" />
                  </svg>
                </div>
              </div>
              <div>
                <h3 className="text-lg font-medium text-[#765341] mb-2">Brings Balance & Calm</h3>
                <p className="text-sm text-[#765341] leading-relaxed">
                  Traditionally worn to support mental peace and emotional stability.
                </p>
              </div>
            </div>

            <div className="flex gap-4">
              <div className="flex-shrink-0">
                <div className="w-12 h-12 flex items-center justify-center">
                  <svg width="32" height="32" viewBox="0 0 32 32" fill="none" className="text-[#765341]">
                    <rect x="12" y="8" width="8" height="16" rx="4" stroke="currentColor" strokeWidth="1.5" />
                    <path d="M16 12V20" stroke="currentColor" strokeWidth="1.5" />
                  </svg>
                </div>
              </div>
              <div>
                <h3 className="text-lg font-medium text-[#765341] mb-2">Comfortable for Daily Wear</h3>
                <p className="text-sm text-[#765341] leading-relaxed">
                  Designed to be worn every day with ease and comfort.
                </p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Featured Product Section */}
      <section className="py-16 md:py-24 px-4 bg-white">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-12">
            <p className="text-sm text-[#9A6A51] mb-2 tracking-wider">Our featured products</p>
            <h2 className="font-serif text-3xl md:text-5xl text-[#765341] font-light">
              Our Featured Mala
            </h2>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-8 md:gap-16 items-center max-w-5xl mx-auto">
            <div className="aspect-square bg-[#9A6A51] rounded-sm overflow-hidden">
              <img
                src="https://images.unsplash.com/photo-1603201667141-5a2d4c673378?q=80&w=800"
                alt="Karungali Mala"
                className="w-full h-full object-cover"
              />
            </div>

            <div>
              <h3 className="font-serif text-2xl md:text-3xl text-[#765341] mb-2">
                Karungali Mala
              </h3>
              <p className="text-[#9A6A51] mb-4">(A Sacred Gift of Nature)</p>
              <p className="text-xl text-[#765341] font-medium mb-6">₹25,000</p>
              <button
                onClick={handleBuyNow}
                disabled={isLoading || !productData?.data}
                className="inline-flex items-center gap-2 bg-[#765341] text-white px-8 py-3 hover:bg-[#5C4033] transition-all disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : "Buy Now"}
                {!isLoading && <ArrowRight className="w-4 h-4" />}
              </button>
            </div>
          </div>
        </div>
      </section>

      {/* About Section */}
      <section className="py-16 md:py-24 px-4 bg-[#F2F6EF]">
        <div className="max-w-7xl mx-auto grid grid-cols-1 md:grid-cols-2 gap-12 md:gap-16">
          <div>
            <p className="text-sm text-[#9A6A51] mb-4 tracking-wider">About us</p>
            <h2 className="font-serif text-3xl md:text-5xl text-[#765341] font-light leading-tight mb-8">
              The Story Behind<br />
              Karungali Mala
            </h2>
          </div>

          <div className="space-y-6 text-[#9A6A51] leading-relaxed">
            <p>
              Karungali wood has long been valued for its spiritual importance and calming qualities.
            </p>
            <p>
              Each mala is carefully crafted to preserve this tradition, offering a meaningful accessory that supports mindfulness and well-being in daily life.
            </p>
          </div>
        </div>

        {/* Blessed Section */}
        <div className="mt-16 md:mt-24">
          <div className="max-w-7xl mx-auto">
            <h2 className="font-serif text-3xl md:text-5xl text-[#765341] font-light text-center mb-12">
              Blessed Across 108 Sacred Temples
            </h2>

            <div className="space-y-6 text-[#9A6A51] leading-relaxed max-w-3xl mx-auto">
              <p>
                Each Karungali Mala is taken through sacred rituals and prayers across 108 temples in India, carrying blessings rooted in devotion and tradition.
              </p>
              <p>
                Wearing the mala is believed to invite positivity, clarity, and protection into one's journey.
              </p>
              <p className="font-medium">Many people wear it seeking:</p>
              <ul className="space-y-2 pl-6">
                <li>Confidence in studies and career</li>
                <li>Stability in business and finances</li>
                <li>Protection from negative influences</li>
                <li>Peace of mind and emotional balance</li>
                <li>Harmony in family and relationships</li>
                <li>Focus during meditation and prayer</li>
                <li>Strength during challenging times</li>
              </ul>
              <p className="italic">
                The mala becomes a symbol of faith and divine support in everyday life.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Quote Banner */}
      <section className="py-12 px-4 bg-[#9A6A51]">
        <p className="font-serif text-xl md:text-2xl text-white text-center italic">
          From sacred roots to daily blessings.
        </p>
      </section>

      {/* Benefits Section */}
      <section className="py-16 md:py-24 px-4 bg-white">
        <div className="max-w-7xl mx-auto">
          <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-8 mb-12">
            <div>
              <p className="text-sm text-[#9A6A51] mb-2 tracking-wider">Blessed Across 108 Sacred Temples</p>
              <h2 className="font-serif text-3xl md:text-5xl text-[#765341] font-light">
                BENEFITS LIST
              </h2>
            </div>

            <button
              onClick={handleBuyNow}
              disabled={isLoading || !productData?.data}
              className="inline-flex items-center gap-2 border border-[#765341] text-[#765341] px-6 py-2 hover:bg-[#765341] hover:text-white transition-all disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : "Buy Now"}
              {!isLoading && <ArrowRight className="w-4 h-4" />}
            </button>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {[
              "Invites positive energy",
              "Encourages mental peace and clarity",
              "Supports focus in studies and work",
              "Helps maintain confidence in business and career",
              "Protects from negative influences",
              "Encourages emotional balance",
              "Supports meditation",
              "spiritual practices",
              "Promotes harmony in daily life",
              "Serves as a symbol of faith and protection",
            ].map((benefit, index) => (
              <div
                key={index}
                className="border border-[#9A6A51] px-4 py-3 text-sm text-[#765341] hover:bg-[#F2F6EF] transition-colors"
              >
                {benefit}
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Testimonials Section */}
      <section className="py-16 md:py-24 px-4 bg-[#F2F6EF]">
        <div className="max-w-7xl mx-auto">
          <p className="text-sm text-[#9A6A51] text-center mb-8 tracking-wider">Product Testimonials</p>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-8 md:gap-16 items-center max-w-5xl mx-auto">
            <div className="aspect-square bg-[#E8DDD0] rounded-full"></div>

            <div className="text-center md:text-left">
              <div className="flex justify-center md:justify-start gap-1 mb-6">
                {[...Array(5)].map((_, i) => (
                  <Star key={i} className="w-5 h-5 fill-[#9A6A51] text-[#9A6A51]" />
                ))}
              </div>

              <blockquote className="font-serif text-xl md:text-2xl text-[#765341] leading-relaxed mb-4">
                "Wearing the Karungali Mala daily has helped me feel more peaceful and focused. The craftsmanship and authenticity truly stand out."
              </blockquote>

              <p className="text-sm text-[#9A6A51] italic">- Customer Review</p>

              {/* Navigation arrows */}
              <div className="flex justify-center md:justify-start gap-4 mt-8">
                <button className="hover:opacity-70 transition-opacity">
                  <ArrowRight className="w-5 h-5 text-[#765341]" />
                </button>
                <div className="flex gap-2 items-center">
                  <div className="w-1.5 h-1.5 bg-[#765341] rounded-full"></div>
                  <div className="w-1.5 h-1.5 bg-[#765341] rounded-full opacity-30"></div>
                  <div className="w-1.5 h-1.5 bg-[#765341] rounded-full opacity-30"></div>
                </div>
                <button className="hover:opacity-70 transition-opacity">
                  <ArrowLeft className="w-5 h-5 text-[#765341]" />
                </button>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Three Column Features */}
      <section className="py-16 md:py-24 px-4 bg-white">
        <div className="max-w-7xl mx-auto grid grid-cols-1 md:grid-cols-3 gap-12 md:gap-8">
          <div className="text-center">
            <div className="flex justify-center mb-4">
              <svg width="48" height="48" viewBox="0 0 48 48" fill="none" className="text-[#9A6A51]">
                <path d="M24 8V16M24 16L32 24M24 16L16 24M12 32H36" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
              </svg>
            </div>
            <h3 className="font-serif text-xl text-[#765341] mb-3">
              Gift it to Your Loved Ones
            </h3>
            <p className="text-sm text-[#9A6A51] leading-relaxed">
              Share blessings and positivity with those who matter most.
            </p>
          </div>

          <div className="text-center border-l border-r border-[#F3E9DC] md:px-8">
            <div className="flex justify-center mb-4">
              <svg width="48" height="48" viewBox="0 0 48 48" fill="none" className="text-[#9A6A51]">
                <circle cx="24" cy="24" r="8" stroke="currentColor" strokeWidth="1.5" />
                <path d="M24 16V32M16 24H32" stroke="currentColor" strokeWidth="1.5" />
              </svg>
            </div>
            <h3 className="font-serif text-xl text-[#765341] mb-3">
              Crafted for Everyday Well-Being
            </h3>
            <p className="text-sm text-[#9A6A51] leading-relaxed">
              Designed to bring calmness, protection, and balance into daily life.
            </p>
          </div>

          <div className="text-center">
            <div className="flex justify-center mb-4">
              <svg width="48" height="48" viewBox="0 0 48 48" fill="none" className="text-[#9A6A51]">
                <circle cx="24" cy="24" r="12" stroke="currentColor" strokeWidth="1.5" />
                <path d="M24 18V24L28 28" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
              </svg>
            </div>
            <h3 className="font-serif text-xl text-[#765341] mb-3">
              Carry Positive Energy Wherever You Go
            </h3>
            <p className="text-sm text-[#9A6A51] leading-relaxed">
              A simple addition to your daily life for peace and confidence.
            </p>
          </div>
        </div>
      </section>

      {/* Newsletter Section */}
      <section className="py-16 md:py-20 px-4 bg-[#9A6A51]">
        <div className="max-w-4xl mx-auto text-center md:text-left md:flex md:items-center md:justify-between gap-8">
          <h2 className="font-serif text-2xl md:text-3xl text-white font-light mb-6 md:mb-0">
            Receive Blessings & Special<br className="hidden md:block" />
            Offers on Your First Order
          </h2>

          <div className="flex max-w-md mx-auto md:mx-0">
            <input
              type="email"
              placeholder="Drop your email here"
              className="flex-1 px-6 py-3 bg-white text-[#765341] placeholder-[#9A6A51] focus:outline-none"
            />
            <button className="px-6 py-3 bg-white hover:bg-opacity-90 transition-colors">
              <ArrowRight className="w-5 h-5 text-[#765341]" />
            </button>
          </div>
        </div>
      </section>

      <Footer />
    </div>
  );
}
