import { Instagram, Facebook, Mail, Phone } from "lucide-react";
import { Link } from "react-router-dom";

export default function Footer() {
  const appName = import.meta.env.VITE_APP_NAME || "Karungali Heritage";
  const year = new Date().getFullYear();

  return (
    <footer className="bg-[#F2F6EF] border-t border-[#F3E9DC]">
      <div className="max-w-7xl mx-auto px-4 md:px-12 py-12 md:py-16">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8 md:gap-4">
          {/* Brand Column */}
          <div className="flex flex-col items-center md:items-start gap-6">
            <div className="text-center md:text-left">
              <div className="text-[#765341] text-lg font-serif mb-2">{appName}</div>
              <div className="text-[#9A6A51] text-sm">
                Sacred & Natural<br />
                Blessed Across 108 Temples
              </div>
            </div>

            <div className="flex items-center gap-3">
              <a href="https://instagram.com" target="_blank" rel="noopener noreferrer" className="text-[#9A6A51] hover:opacity-70 transition-opacity">
                <Instagram className="w-4 h-4" />
              </a>
              <a href="https://facebook.com" target="_blank" rel="noopener noreferrer" className="text-[#9A6A51] hover:opacity-70 transition-opacity">
                <Facebook className="w-4 h-4" />
              </a>
            </div>
          </div>

          {/* Quick Links Column */}
          <div className="flex flex-col items-center md:items-start gap-4 md:border-l md:border-r border-[#F3E9DC] md:px-6">
            <h3 className="text-[#9A6A51] text-base font-light">Quick Links</h3>
            <nav className="flex flex-col items-center md:items-start gap-2 text-sm text-[#765341]">
              <Link to="/" className="hover:opacity-70 transition-opacity">Home</Link>
              <Link to="/cart" className="hover:opacity-70 transition-opacity">Buy Now</Link>
              <Link to="/about" className="hover:opacity-70 transition-opacity">About Us</Link>
              <Link to="/faq" className="hover:opacity-70 transition-opacity">FAQ</Link>
              <Link to="/shipping" className="hover:opacity-70 transition-opacity">Shipping & Returns</Link>
            </nav>
          </div>

          {/* Contact Column */}
          <div className="flex flex-col items-center md:items-start gap-4">
            <h3 className="text-[#9A6A51] text-base font-light">Contact Us</h3>
            <div className="flex flex-col items-center md:items-start gap-3 text-sm text-[#765341]">
              <a href="tel:+919876543210" className="flex items-center gap-2 hover:opacity-70 transition-opacity">
                <Phone className="w-4 h-4" />
                +91 98765 43210
              </a>
              <a href="mailto:info@karungaliheritage.com" className="flex items-center gap-2 hover:opacity-70 transition-opacity">
                <Mail className="w-4 h-4" />
                info@karungaliheritage.com
              </a>
              <p className="text-center md:text-left mt-2">
                Free Delivery Across India
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Bottom Bar */}
      <div className="border-t border-[#F3E9DC] px-4 md:px-12 py-4">
        <div className="max-w-7xl mx-auto flex flex-col md:flex-row justify-between items-center gap-4 text-xs text-[#765341]">
          <div>© {year} {appName}</div>
          <div className="flex items-center gap-6">
            <Link to="/privacy" className="hover:opacity-70 transition-opacity">Privacy Policy</Link>
            <Link to="/terms" className="hover:opacity-70 transition-opacity">Terms of Service</Link>
          </div>
        </div>
      </div>
    </footer>
  );
}
