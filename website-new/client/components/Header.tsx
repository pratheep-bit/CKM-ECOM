import { Link, useLocation } from "react-router-dom";
import { ShoppingCart } from "lucide-react";
import { useCart } from "@/context/CartContext";
import { useAuth } from "@/context/AuthContext";

export default function Header() {
  const appName = import.meta.env.VITE_APP_NAME || "Karungali Heritage";
  const { itemCount } = useCart();
  const { isLoggedIn } = useAuth();
  const location = useLocation();

  // Hero pages use transparent bg + white text; other pages use solid bg + dark text
  const isHeroPage = location.pathname === "/";

  return (
    <header
      className={`fixed top-0 left-0 right-0 z-50 px-4 md:px-12 py-4 transition-colors ${isHeroPage ? "bg-transparent" : "bg-white border-b border-[#F3E9DC] shadow-sm"
        }`}
    >
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-8">
          <Link
            to="/"
            className={`text-sm md:text-base font-light tracking-wide ${isHeroPage ? "text-white" : "text-[#765341]"
              }`}
          >
            {appName}
          </Link>

          <nav className={`hidden md:flex items-center gap-6 text-sm ${isHeroPage ? "text-white" : "text-[#765341]"
            }`}>
            <Link to="/" className="hover:opacity-80 transition-opacity">
              HOME
            </Link>
            <Link to="/about" className="hover:opacity-80 transition-opacity">
              ABOUT
            </Link>
            <Link to="/faq" className="hover:opacity-80 transition-opacity">
              FAQ
            </Link>
            <Link to="/contact" className="hover:opacity-80 transition-opacity">
              CONTACT
            </Link>
          </nav>
        </div>

        <div className={`flex items-center gap-6 text-sm ${isHeroPage ? "text-white" : "text-[#765341]"
          }`}>
          {isLoggedIn ? (
            <Link to="/account" className="hover:opacity-80 transition-opacity">
              ACCOUNT
            </Link>
          ) : (
            <Link to="/login" className="hover:opacity-80 transition-opacity">
              LOGIN
            </Link>
          )}
          <Link to="/cart" className="hover:opacity-80 transition-opacity flex items-center gap-2 relative">
            <ShoppingCart className="w-5 h-5" />
            <span className="hidden md:inline">CART</span>
            {itemCount > 0 && (
              <span className="absolute -top-2 -right-3 bg-[#765341] text-white text-[10px] font-bold w-5 h-5 flex items-center justify-center rounded-full border border-white">
                {itemCount}
              </span>
            )}
          </Link>
        </div>
      </div>
    </header>
  );
}
