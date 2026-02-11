import { useState, useEffect, useRef } from "react";
import { useNavigate, Link } from "react-router-dom";
import Header from "@/components/Header";
import Footer from "@/components/Footer";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import {
    Dialog,
    DialogContent,
    DialogHeader,
    DialogTitle,
    DialogTrigger
} from "@/components/ui/dialog";
import { useCart } from "@/context/CartContext";
import { useAuth } from "@/context/AuthContext";
import { apiService } from "@/lib/api";
import { toast } from "sonner";
import { Check, Plus, Loader2, ArrowLeft, ShoppingBag, Shield, ChevronRight, Package } from "lucide-react";

interface Address {
    id: string;
    name: string;
    mobile: string;
    line1: string;
    line2?: string;
    city: string;
    state: string;
    pincode: string;
    country: string;
    address_type: string;
    is_default: boolean;
}

// Dynamically load Razorpay checkout.js
function loadRazorpayScript(): Promise<boolean> {
    return new Promise((resolve) => {
        if ((window as any).Razorpay) {
            resolve(true);
            return;
        }
        const script = document.createElement("script");
        script.src = "https://checkout.razorpay.com/v1/checkout.js";
        script.onload = () => resolve(true);
        script.onerror = () => resolve(false);
        document.body.appendChild(script);
    });
}

export default function Checkout() {
    const navigate = useNavigate();
    const { items, subtotal, itemCount, loading: cartLoading, clearCart } = useCart();
    const { isLoggedIn } = useAuth();

    const [step, setStep] = useState<1 | 2 | 3>(1); // 1: Address, 2: Summary, 3: Payment
    const [addresses, setAddresses] = useState<Address[]>([]);
    const [selectedAddressId, setSelectedAddressId] = useState<string | null>(null);
    const [loadingAddresses, setLoadingAddresses] = useState(true);
    const [processing, setProcessing] = useState(false);
    const orderInFlight = useRef(false); // Prevents duplicate order creation
    // Track if payment just completed successfully — prevents empty-cart redirect race
    const paymentJustCompleted = useRef(false);

    // Order success popup
    const [orderSuccess, setOrderSuccess] = useState<{ orderNumber: string; total: string } | null>(null);

    // New Address Form State
    const [isAddressDialogOpen, setIsAddressDialogOpen] = useState(false);
    const [newAddress, setNewAddress] = useState({
        name: "",
        mobile: "",
        line1: "",
        line2: "",
        city: "",
        state: "",
        pincode: "",
        country: "India",
        address_type: "home",
        is_default: false
    });

    // Auth guard — redirect to login if not authenticated
    useEffect(() => {
        if (!isLoggedIn) {
            sessionStorage.setItem("return_url", "/checkout");
            navigate("/login");
        }
    }, [isLoggedIn, navigate]);

    // Track whether initial cart data has settled (prevents premature redirect)
    const cartSettled = useRef(false);
    useEffect(() => {
        // Only mark as settled once we've seen cart finish loading with auth
        if (!cartLoading && isLoggedIn) {
            // Small delay to allow cart merge to propagate
            const timer = setTimeout(() => {
                cartSettled.current = true;
            }, 500);
            return () => clearTimeout(timer);
        }
    }, [cartLoading, isLoggedIn]);

    // Empty cart guard — but NOT if payment just completed, and NOT before cart settles
    useEffect(() => {
        if (cartSettled.current && !cartLoading && itemCount === 0 && !paymentJustCompleted.current) {
            navigate("/cart");
        }
    }, [cartLoading, itemCount, navigate]);

    // Load addresses on mount
    useEffect(() => {
        if (!isLoggedIn) return;
        const fetchAddresses = async () => {
            try {
                const response = await apiService.getAddresses();
                const addrs = response.data || [];
                setAddresses(addrs);
                const defaultAddr = addrs.find((a: Address) => a.is_default);
                if (defaultAddr) setSelectedAddressId(defaultAddr.id);
                else if (addrs.length > 0) setSelectedAddressId(addrs[0].id);
            } catch (error) {
                console.error("Failed to load addresses", error);
                toast.error("Failed to load addresses");
            } finally {
                setLoadingAddresses(false);
            }
        };
        fetchAddresses();
    }, [isLoggedIn]);

    const handleAddAddress = async () => {
        if (!newAddress.name || !newAddress.mobile || !newAddress.line1 || !newAddress.city || !newAddress.state || !newAddress.pincode) {
            toast.error("Please fill in all required fields");
            return;
        }

        // Sanitize mobile: strip spaces, leading 0s, ensure 10 digits for Indian numbers
        let mobile = newAddress.mobile.replace(/[\s\-()]/g, '');
        if (mobile.startsWith('0')) mobile = mobile.substring(1);
        if (!mobile.startsWith('+') && mobile.length === 10) mobile = `+91${mobile}`;
        if (!/^\+?[1-9]\d{9,14}$/.test(mobile)) {
            toast.error("Please enter a valid 10-digit mobile number");
            return;
        }

        try {
            const response = await apiService.createAddress({ ...newAddress, mobile });
            setAddresses([...addresses, response.data]);
            setSelectedAddressId(response.data.id);
            setIsAddressDialogOpen(false);
            toast.success("Address added successfully");
            setNewAddress({
                name: "",
                mobile: "",
                line1: "",
                line2: "",
                city: "",
                state: "",
                pincode: "",
                country: "India",
                address_type: "home",
                is_default: false
            });
        } catch (error: any) {
            console.error("Failed to add address", error);
            const detail = error.response?.data?.detail;
            if (Array.isArray(detail)) {
                toast.error(detail.map((d: any) => d.msg).join(", "));
            } else {
                toast.error(typeof detail === 'string' ? detail : "Failed to add address");
            }
        }
    };

    const handleCreateOrder = async () => {
        if (!selectedAddressId) {
            toast.error("Please select a delivery address");
            return;
        }

        // Prevent duplicate submissions
        if (orderInFlight.current || processing) return;
        orderInFlight.current = true;
        setProcessing(true);

        try {
            // 1. Create Order
            const orderRes = await apiService.createOrder(selectedAddressId);
            const orderId = orderRes.data.id;

            // 2. Initiate Payment
            const paymentRes = await apiService.createPayment(orderId);
            const { razorpay_order_id, razorpay_key_id, amount, currency } = paymentRes.data;

            // 3. Load Razorpay script
            const scriptLoaded = await loadRazorpayScript();
            if (!scriptLoaded) {
                toast.error("Failed to load payment gateway. Please refresh and try again.");
                setProcessing(false);
                orderInFlight.current = false;
                return;
            }

            // 4. Open Razorpay Checkout
            const options = {
                key: razorpay_key_id,
                amount: amount,
                currency: currency,
                name: "Karungali Heritage",
                description: `Order #${orderRes.data.order_number}`,
                order_id: razorpay_order_id,
                handler: async function (response: any) {
                    try {
                        await apiService.verifyPayment({
                            razorpay_order_id: response.razorpay_order_id,
                            razorpay_payment_id: response.razorpay_payment_id,
                            razorpay_signature: response.razorpay_signature
                        });
                        // Mark payment as completed BEFORE clearing cart
                        paymentJustCompleted.current = true;
                        await clearCart();
                        // Show success popup instead of navigating directly
                        setOrderSuccess({
                            orderNumber: orderRes.data.order_number,
                            total: Number(orderRes.data.total).toLocaleString()
                        });
                    } catch (err) {
                        console.error("Payment verification failed:", err);
                        toast.error("Payment verification failed. Contact support if amount was deducted.");
                    } finally {
                        setProcessing(false);
                        orderInFlight.current = false;
                    }
                },
                prefill: {
                    contact: addresses.find(a => a.id === selectedAddressId)?.mobile
                },
                theme: {
                    color: "#765341"
                },
                modal: {
                    ondismiss: function () {
                        // User closed Razorpay modal — cart stays intact, order saved on backend
                        setProcessing(false);
                        orderInFlight.current = false;
                        toast.info("Payment cancelled. Your order is saved — you can retry from your account.");
                    }
                }
            };

            const rzp = new (window as any).Razorpay(options);
            rzp.on('payment.failed', function (response: any) {
                toast.error(response.error.description || "Payment failed");
                setProcessing(false);
                orderInFlight.current = false;
            });
            rzp.open();

        } catch (error: any) {
            console.error("Order creation failed:", error);
            const msg = error.response?.data?.detail || "Failed to process order";
            toast.error(msg);
            setProcessing(false);
            orderInFlight.current = false;
        }
    };

    if (!isLoggedIn || cartLoading || loadingAddresses) {
        return (
            <div className="min-h-screen bg-white flex items-center justify-center">
                <Loader2 className="w-8 h-8 animate-spin text-[#765341]" />
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-white">
            <Header />
            <main className="pt-24 pb-16 px-4 max-w-5xl mx-auto">

                {/* Breadcrumb Navigation */}
                <nav className="flex items-center gap-2 text-sm text-[#9A6A51] mb-6">
                    <Link to="/" className="hover:text-[#765341] transition-colors">Home</Link>
                    <ChevronRight className="w-3 h-3" />
                    <Link to="/cart" className="hover:text-[#765341] transition-colors">Cart</Link>
                    <ChevronRight className="w-3 h-3" />
                    <span className="text-[#765341] font-medium">Checkout</span>
                </nav>

                {/* Back to Cart + Title Row */}
                <div className="flex items-center justify-between mb-8">
                    <div className="flex items-center gap-4">
                        <button
                            onClick={() => navigate("/cart")}
                            className="flex items-center gap-2 text-[#9A6A51] hover:text-[#765341] transition-colors"
                            disabled={processing}
                        >
                            <ArrowLeft className="w-4 h-4" />
                            <span className="text-sm">Back to Cart</span>
                        </button>
                        <h1 className="font-serif text-3xl text-[#765341]">Checkout</h1>
                    </div>
                    <Link
                        to="/"
                        className="flex items-center gap-2 text-sm text-[#9A6A51] hover:text-[#765341] transition-colors"
                    >
                        <ShoppingBag className="w-4 h-4" />
                        Continue Shopping
                    </Link>
                </div>

                <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                    {/* Left Column: Flow */}
                    <div className="lg:col-span-2 space-y-6">

                        {/* Step 1: Address */}
                        <div className={`border rounded-lg p-6 ${step === 1 ? 'border-[#765341] bg-[#FDFBF7]' : 'border-gray-200'}`}>
                            <div className="flex justify-between items-center mb-4">
                                <h2 className="text-xl font-serif text-[#765341]">1. Delivery Address</h2>
                                {step > 1 && <Button variant="link" onClick={() => setStep(1)} className="text-[#765341]">Change</Button>}
                            </div>

                            {step === 1 && (
                                <div className="space-y-4">
                                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                        {addresses.map(addr => (
                                            <div
                                                key={addr.id}
                                                onClick={() => setSelectedAddressId(addr.id)}
                                                className={`p-4 border rounded-lg cursor-pointer transition-all relative ${selectedAddressId === addr.id
                                                    ? 'border-[#765341] bg-[#F2F6EF]'
                                                    : 'border-gray-200 hover:border-[#765341]'
                                                    }`}
                                            >
                                                <div className="flex justify-between items-start">
                                                    <div>
                                                        <div className="flex items-center gap-2">
                                                            <span className="font-medium">{addr.name}</span>
                                                            <span className="text-[10px] px-2 py-0.5 bg-gray-100 rounded uppercase">{addr.address_type}</span>
                                                        </div>
                                                        <p className="text-sm text-gray-600 mt-1">{addr.line1}</p>
                                                        {addr.line2 && <p className="text-sm text-gray-600">{addr.line2}</p>}
                                                        <p className="text-sm text-gray-600">{addr.city}, {addr.state} - {addr.pincode}</p>
                                                        <p className="text-sm text-gray-600 mt-1">Mobile: {addr.mobile}</p>
                                                    </div>
                                                    {selectedAddressId === addr.id && <Check className="w-4 h-4 text-[#765341]" />}
                                                </div>
                                            </div>
                                        ))}

                                        {/* Add New Address Dialog */}
                                        <Dialog open={isAddressDialogOpen} onOpenChange={setIsAddressDialogOpen}>
                                            <DialogTrigger asChild>
                                                <div className="p-4 border border-dashed border-gray-300 rounded-lg flex items-center justify-center cursor-pointer hover:bg-gray-50 min-h-[160px]">
                                                    <div className="text-center text-gray-500">
                                                        <Plus className="w-6 h-6 mx-auto mb-2" />
                                                        <span>Add New Address</span>
                                                    </div>
                                                </div>
                                            </DialogTrigger>
                                            <DialogContent className="sm:max-w-[425px] max-h-[90vh] overflow-y-auto">
                                                <DialogHeader>
                                                    <DialogTitle>Add New Address</DialogTitle>
                                                </DialogHeader>
                                                <div className="grid gap-4 py-4">
                                                    <div className="grid gap-2">
                                                        <Label htmlFor="name">Full Name</Label>
                                                        <Input id="name" value={newAddress.name} onChange={(e) => setNewAddress({ ...newAddress, name: e.target.value })} />
                                                    </div>
                                                    <div className="grid gap-2">
                                                        <Label htmlFor="mobile">Mobile Number</Label>
                                                        <Input id="mobile" placeholder="e.g. 9876543210" value={newAddress.mobile} onChange={(e) => setNewAddress({ ...newAddress, mobile: e.target.value })} />
                                                    </div>
                                                    <div className="grid gap-2">
                                                        <Label htmlFor="line1">Address Line 1</Label>
                                                        <Input id="line1" value={newAddress.line1} onChange={(e) => setNewAddress({ ...newAddress, line1: e.target.value })} />
                                                    </div>
                                                    <div className="grid gap-2">
                                                        <Label htmlFor="line2">Address Line 2 (Optional)</Label>
                                                        <Input id="line2" value={newAddress.line2} onChange={(e) => setNewAddress({ ...newAddress, line2: e.target.value })} />
                                                    </div>
                                                    <div className="grid grid-cols-2 gap-4">
                                                        <div className="grid gap-2">
                                                            <Label htmlFor="city">City</Label>
                                                            <Input id="city" value={newAddress.city} onChange={(e) => setNewAddress({ ...newAddress, city: e.target.value })} />
                                                        </div>
                                                        <div className="grid gap-2">
                                                            <Label htmlFor="pincode">Pincode</Label>
                                                            <Input id="pincode" value={newAddress.pincode} onChange={(e) => setNewAddress({ ...newAddress, pincode: e.target.value })} />
                                                        </div>
                                                    </div>
                                                    <div className="grid grid-cols-2 gap-4">
                                                        <div className="grid gap-2">
                                                            <Label htmlFor="state">State</Label>
                                                            <Input id="state" value={newAddress.state} onChange={(e) => setNewAddress({ ...newAddress, state: e.target.value })} />
                                                        </div>
                                                        <div className="grid gap-2">
                                                            <Label htmlFor="country">Country</Label>
                                                            <Input id="country" value={newAddress.country} disabled />
                                                        </div>
                                                    </div>
                                                    <div className="grid gap-2">
                                                        <Label>Address Type</Label>
                                                        <RadioGroup
                                                            defaultValue="home"
                                                            value={newAddress.address_type}
                                                            onValueChange={(val) => setNewAddress({ ...newAddress, address_type: val })}
                                                            className="flex gap-4"
                                                        >
                                                            <div className="flex items-center space-x-2">
                                                                <RadioGroupItem value="home" id="home" />
                                                                <Label htmlFor="home">Home</Label>
                                                            </div>
                                                            <div className="flex items-center space-x-2">
                                                                <RadioGroupItem value="office" id="office" />
                                                                <Label htmlFor="office">Office</Label>
                                                            </div>
                                                            <div className="flex items-center space-x-2">
                                                                <RadioGroupItem value="other" id="other" />
                                                                <Label htmlFor="other">Other</Label>
                                                            </div>
                                                        </RadioGroup>
                                                    </div>
                                                </div>
                                                <Button onClick={handleAddAddress} className="w-full bg-[#765341] hover:bg-[#5C4033]">
                                                    Save Address
                                                </Button>
                                            </DialogContent>
                                        </Dialog>
                                    </div>

                                    <Button
                                        onClick={() => setStep(2)}
                                        className="bg-[#765341] text-white hover:bg-[#5C4033] mt-4 w-full md:w-auto"
                                        disabled={!selectedAddressId}
                                    >
                                        Deliver Here
                                    </Button>
                                </div>
                            )}

                            {step > 1 && selectedAddressId && (
                                <div className="text-sm text-gray-600">
                                    {(() => {
                                        const addr = addresses.find(a => a.id === selectedAddressId);
                                        return addr ? (
                                            <div>
                                                <span className="font-medium">{addr.name}</span>, {addr.line1}, {addr.city} - {addr.pincode}
                                                <br />
                                                <span className="text-xs">Mobile: {addr.mobile}</span>
                                            </div>
                                        ) : '';
                                    })()}
                                </div>
                            )}
                        </div>

                        {/* Step 2: Order Summary */}
                        <div className={`border rounded-lg p-6 ${step === 2 ? 'border-[#765341] bg-[#FDFBF7]' : 'border-gray-200'}`}>
                            <div className="flex justify-between items-center mb-4">
                                <h2 className="text-xl font-serif text-[#765341]">2. Order Summary</h2>
                                {step === 2 && itemCount > 0 && (
                                    <span className="text-sm text-gray-500">{itemCount} Items</span>
                                )}
                            </div>

                            {step === 2 && (
                                <div className="space-y-4">
                                    {items.map(item => (
                                        <div key={item.product_id} className="flex gap-4 border-b border-gray-100 pb-4">
                                            <div className="w-20 h-20 bg-gray-100 rounded flex-shrink-0 overflow-hidden">
                                                {item.product.images?.[0] && (
                                                    <img src={item.product.images[0]} className="w-full h-full object-cover" alt={item.product.name} />
                                                )}
                                            </div>
                                            <div className="flex-1">
                                                <p className="font-medium text-[#765341]">{item.product.name}</p>
                                                <p className="text-sm text-gray-500 mt-1">Quantity: {item.quantity}</p>
                                                <p className="text-sm text-gray-500">Price: ₹{item.product.price.toLocaleString()}</p>
                                            </div>
                                            <div className="text-right">
                                                <p className="font-medium">₹{(item.product.price * item.quantity).toLocaleString()}</p>
                                            </div>
                                        </div>
                                    ))}

                                    {/* Edit Cart Link */}
                                    <div className="text-center">
                                        <button
                                            onClick={() => navigate("/cart")}
                                            className="text-sm text-[#9A6A51] hover:text-[#765341] underline transition-colors"
                                        >
                                            Need to change items? Edit your cart
                                        </button>
                                    </div>

                                    <div className="pt-4 space-y-3">
                                        <Button
                                            onClick={handleCreateOrder}
                                            className="bg-[#765341] w-full text-white hover:bg-[#5C4033] py-6 text-lg"
                                            disabled={processing}
                                        >
                                            {processing ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : null}
                                            {processing ? "Processing..." : "Proceed to Payment"}
                                        </Button>

                                        {/* Cancel / Go Back option */}
                                        <button
                                            onClick={() => navigate("/cart")}
                                            className="w-full text-center text-sm text-[#9A6A51] hover:text-[#765341] transition-colors py-2"
                                            disabled={processing}
                                        >
                                            Cancel and return to cart
                                        </button>
                                    </div>
                                </div>
                            )}
                        </div>

                        {/* Step 3: Payment */}
                        <div className={`border rounded-lg p-6 border-gray-200 opacity-50`}>
                            <h2 className="text-xl font-serif text-gray-400">3. Payment</h2>
                            <p className="text-sm text-gray-400 mt-2">Secure payment via Razorpay</p>
                        </div>

                    </div>

                    {/* Right Column: Price Details */}
                    <div className="h-fit border border-[#F3E9DC] rounded-lg p-6 sticky top-24 bg-[#FDFBF7]">
                        <h3 className="font-serif text-lg text-[#765341] mb-4">Price Details</h3>
                        <div className="space-y-3 mb-4 text-sm">
                            <div className="flex justify-between">
                                <span>Price ({itemCount} items)</span>
                                <span>₹{subtotal.toLocaleString()}</span>
                            </div>
                            <div className="flex justify-between">
                                <span>Delivery Charges</span>
                                <span className="text-green-600">Free</span>
                            </div>
                        </div>
                        <div className="border-t border-dashed border-[#F3E9DC] pt-4 flex justify-between font-medium text-lg text-[#765341]">
                            <span>Total Payable</span>
                            <span>₹{subtotal.toLocaleString()}</span>
                        </div>

                        <div className="mt-6 flex items-center justify-center gap-2 text-xs text-gray-500">
                            <Shield className="w-3 h-3" />
                            Safe and Secure Payments. 100% Authentic Products.
                        </div>
                    </div>
                </div>
            </main>
            <Footer />

            {/* ──── ORDER SUCCESS POPUP ──── */}
            {orderSuccess && (
                <div className="fixed inset-0 z-[100] flex items-center justify-center bg-black/60 backdrop-blur-sm">
                    <div className="bg-white rounded-2xl shadow-2xl max-w-lg w-[90vw] p-8 md:p-12 text-center animate-in fade-in zoom-in duration-300">
                        {/* Animated checkmark */}
                        <div className="mx-auto w-20 h-20 rounded-full bg-green-100 flex items-center justify-center mb-6">
                            <Check className="w-10 h-10 text-green-600" strokeWidth={3} />
                        </div>

                        <h2 className="font-serif text-2xl md:text-3xl text-[#765341] mb-2">
                            Order Placed Successfully!
                        </h2>
                        <p className="text-gray-500 mb-6">
                            Thank you for your purchase. Your order has been confirmed.
                        </p>

                        <div className="bg-[#FDFBF7] rounded-xl p-6 mb-6 space-y-3">
                            <div className="flex justify-between text-sm">
                                <span className="text-gray-500">Order Number</span>
                                <span className="font-medium text-[#765341]">#{orderSuccess.orderNumber}</span>
                            </div>
                            <div className="flex justify-between text-sm">
                                <span className="text-gray-500">Amount Paid</span>
                                <span className="font-medium text-[#765341]">₹{orderSuccess.total}</span>
                            </div>
                            <div className="flex justify-between text-sm">
                                <span className="text-gray-500">Status</span>
                                <span className="text-green-600 font-medium">Confirmed</span>
                            </div>
                        </div>

                        <p className="text-xs text-gray-400 mb-6">
                            You will receive an order confirmation on your registered mobile number.
                        </p>

                        <div className="flex flex-col sm:flex-row gap-3">
                            <Button
                                onClick={() => navigate("/account")}
                                className="flex-1 bg-[#765341] hover:bg-[#5C4033] text-white py-3 text-sm"
                            >
                                <Package className="w-4 h-4 mr-2" /> View My Orders
                            </Button>
                            <Button
                                variant="outline"
                                onClick={() => navigate("/")}
                                className="flex-1 border-[#F3E9DC] text-[#765341] hover:bg-[#FDFBF7] py-3 text-sm"
                            >
                                Continue Shopping
                            </Button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}
