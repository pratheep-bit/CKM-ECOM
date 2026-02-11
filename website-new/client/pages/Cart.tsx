import { useNavigate, Link } from "react-router-dom";
import { Minus, Plus, Trash2, ShoppingBag, ArrowLeft, ChevronRight } from "lucide-react";
import Header from "@/components/Header";
import Footer from "@/components/Footer";
import { Button } from "@/components/ui/button";
import { useCart } from "@/context/CartContext";
import { useAuth } from "@/context/AuthContext";

export default function Cart() {
    const navigate = useNavigate();
    const { items, itemCount, subtotal, updateQuantity, removeFromCart, loading } = useCart();
    const { isLoggedIn } = useAuth();

    const handleCheckout = () => {
        if (itemCount === 0) return;

        if (!isLoggedIn) {
            sessionStorage.setItem("return_url", "/checkout");
            navigate("/login");
        } else {
            navigate("/checkout");
        }
    };

    if (loading) {
        return (
            <div className="min-h-screen bg-white">
                <Header />
                <main className="pt-32 pb-16 px-4 text-center">
                    <p className="text-[#9A6A51]">Loading cart...</p>
                </main>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-white">
            <Header />

            <main className="pt-24 pb-16 px-4">
                <div className="max-w-5xl mx-auto">

                    {/* Breadcrumb */}
                    <nav className="flex items-center gap-2 text-sm text-[#9A6A51] mb-6">
                        <Link to="/" className="hover:text-[#765341] transition-colors">Home</Link>
                        <ChevronRight className="w-3 h-3" />
                        <span className="text-[#765341] font-medium">Cart</span>
                    </nav>

                    {/* Back + Title Row */}
                    <div className="flex items-center justify-between mb-8">
                        <div className="flex items-center gap-4">
                            <button
                                onClick={() => navigate("/")}
                                className="flex items-center gap-2 text-[#9A6A51] hover:text-[#765341] transition-colors"
                            >
                                <ArrowLeft className="w-4 h-4" />
                                <span className="text-sm">Back</span>
                            </button>
                            <h1 className="font-serif text-3xl md:text-4xl text-[#765341]">
                                Your Cart
                            </h1>
                        </div>
                        {items.length > 0 && (
                            <Link
                                to="/"
                                className="flex items-center gap-2 text-sm text-[#9A6A51] hover:text-[#765341] transition-colors"
                            >
                                <ShoppingBag className="w-4 h-4" />
                                Continue Shopping
                            </Link>
                        )}
                    </div>

                    {items.length === 0 ? (
                        <div className="text-center py-16">
                            <ShoppingBag className="w-16 h-16 text-gray-300 mx-auto mb-4" />
                            <p className="text-xl text-[#9A6A51] mb-2">Your cart is empty</p>
                            <p className="text-sm text-gray-400 mb-6">Add items to your cart to continue shopping.</p>
                            <Button
                                onClick={() => navigate('/')}
                                className="bg-[#765341] text-white hover:bg-[#5C4033]"
                            >
                                <ShoppingBag className="w-4 h-4 mr-2" />
                                Start Shopping
                            </Button>
                        </div>
                    ) : (
                        <div className="flex flex-col lg:flex-row gap-8">
                            {/* Cart Items List */}
                            <div className="flex-1 space-y-6">
                                {items.map((item) => (
                                    <div key={item.product_id} className="border border-[#F3E9DC] rounded-lg p-6">
                                        <div className="flex flex-col md:flex-row gap-6">
                                            {/* Product Image */}
                                            <div className="w-full md:w-32 h-32 bg-[#F2F6EF] rounded overflow-hidden flex-shrink-0">
                                                {item.product.images && item.product.images.length > 0 ? (
                                                    <img
                                                        src={item.product.images[0]}
                                                        alt={item.product.name}
                                                        className="w-full h-full object-cover"
                                                    />
                                                ) : (
                                                    <div className="w-full h-full bg-gray-100 flex items-center justify-center text-gray-400">
                                                        No Image
                                                    </div>
                                                )}
                                            </div>

                                            {/* Product Info */}
                                            <div className="flex-1">
                                                <div className="flex justify-between">
                                                    <h2 className="font-serif text-xl text-[#765341] mb-1">
                                                        {item.product.name}
                                                    </h2>
                                                    <button
                                                        onClick={() => removeFromCart(item.product_id)}
                                                        className="text-red-400 hover:text-red-600 transition-colors"
                                                        title="Remove item"
                                                    >
                                                        <Trash2 size={18} />
                                                    </button>
                                                </div>

                                                <p className="text-lg text-[#765341] font-medium mb-4">
                                                    ₹{item.product.price.toLocaleString()}
                                                </p>

                                                {/* Quantity Selector */}
                                                <div className="flex items-center gap-4">
                                                    <div className="flex items-center gap-3">
                                                        <button
                                                            onClick={() => updateQuantity(item.product_id, item.quantity - 1)}
                                                            className="w-8 h-8 border border-[#765341] rounded flex items-center justify-center hover:bg-[#F2F6EF] transition-colors disabled:opacity-50"
                                                            disabled={item.quantity <= 1}
                                                        >
                                                            <Minus className="w-3 h-3 text-[#765341]" />
                                                        </button>
                                                        <span className="text-[#765341] font-medium min-w-[30px] text-center">
                                                            {item.quantity}
                                                        </span>
                                                        <button
                                                            onClick={() => updateQuantity(item.product_id, item.quantity + 1)}
                                                            className="w-8 h-8 border border-[#765341] rounded flex items-center justify-center hover:bg-[#F2F6EF] transition-colors disabled:opacity-50"
                                                            disabled={item.quantity >= item.product.stock}
                                                        >
                                                            <Plus className="w-3 h-3 text-[#765341]" />
                                                        </button>
                                                    </div>
                                                </div>
                                            </div>

                                            {/* Item Total */}
                                            <div className="text-right md:self-end">
                                                <p className="text-sm text-[#9A6A51]">Subtotal</p>
                                                <p className="text-xl text-[#765341] font-medium">
                                                    ₹{(item.product.price * item.quantity).toLocaleString()}
                                                </p>
                                            </div>
                                        </div>
                                    </div>
                                ))}
                            </div>

                            {/* Order Summary Sidebar */}
                            <div className="lg:w-96">
                                <div className="border border-[#F3E9DC] rounded-lg p-6 sticky top-24 bg-white">
                                    <h3 className="font-serif text-xl text-[#765341] mb-6">
                                        Order Summary
                                    </h3>

                                    <div className="space-y-3 mb-6 pb-6 border-b border-[#F3E9DC]">
                                        <div className="flex justify-between text-[#765341]">
                                            <span>Subtotal ({itemCount} items)</span>
                                            <span>₹{subtotal.toLocaleString()}</span>
                                        </div>
                                        <div className="flex justify-between text-[#765341]">
                                            <span>Delivery</span>
                                            <span className="text-green-600">Free</span>
                                        </div>
                                    </div>

                                    <div className="flex justify-between font-medium text-[#765341] text-xl mb-6">
                                        <span>Total</span>
                                        <span>₹{subtotal.toLocaleString()}</span>
                                    </div>

                                    <Button
                                        onClick={handleCheckout}
                                        className="w-full bg-[#765341] text-white hover:bg-[#5C4033] h-12 text-lg"
                                    >
                                        {isLoggedIn ? "Proceed to Checkout" : "Login & Checkout"}
                                    </Button>

                                    <p className="text-xs text-center text-[#9A6A51] mt-4">
                                        Tax included. Shipping calculated at checkout.
                                    </p>
                                </div>
                            </div>
                        </div>
                    )}
                </div>
            </main>

            <Footer />
        </div>
    );
}
