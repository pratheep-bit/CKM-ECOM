import { useState, useEffect, useRef } from "react";
import { useNavigate } from "react-router-dom";
import Header from "@/components/Header";
import Footer from "@/components/Footer";
import { useProfile, useOrders } from "@/hooks/useApi";
import { useAuth } from "@/context/AuthContext";
import { apiService } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
    Dialog,
    DialogContent,
    DialogHeader,
    DialogTitle,
} from "@/components/ui/dialog";
import { toast } from "sonner";
import {
    LogOut, Package, ChevronDown, ChevronUp, Loader2, X,
    User, MapPin, Plus, Pencil, Trash2, Check, Star, CreditCard
} from "lucide-react";

// Dynamically load Razorpay checkout.js
function loadRazorpayScript(): Promise<boolean> {
    return new Promise((resolve) => {
        if ((window as any).Razorpay) { resolve(true); return; }
        const script = document.createElement("script");
        script.src = "https://checkout.razorpay.com/v1/checkout.js";
        script.onload = () => resolve(true);
        script.onerror = () => resolve(false);
        document.body.appendChild(script);
    });
}

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
    landmark?: string;
    is_default: boolean;
}

const EMPTY_ADDRESS = {
    name: "", mobile: "", line1: "", line2: "", city: "",
    state: "", pincode: "", country: "India", address_type: "home",
    landmark: "", is_default: false,
};

export default function Account() {
    const navigate = useNavigate();
    const { isLoggedIn, logout } = useAuth();
    const { data: profileData, isLoading: profileLoading, refetch: refetchProfile } = useProfile();
    const { data: ordersData, isLoading: ordersLoading, refetch: refetchOrders } = useOrders();

    // Profile editing
    const [editingProfile, setEditingProfile] = useState(false);
    const [profileName, setProfileName] = useState("");
    const [profileEmail, setProfileEmail] = useState("");
    const [savingProfile, setSavingProfile] = useState(false);

    // Address management
    const [addresses, setAddresses] = useState<Address[]>([]);
    const [loadingAddresses, setLoadingAddresses] = useState(true);
    const [addressDialogOpen, setAddressDialogOpen] = useState(false);
    const [editingAddressId, setEditingAddressId] = useState<string | null>(null);
    const [addressForm, setAddressForm] = useState(EMPTY_ADDRESS);
    const [savingAddress, setSavingAddress] = useState(false);
    const [deletingAddressId, setDeletingAddressId] = useState<string | null>(null);

    // Orders
    const [expandedOrderId, setExpandedOrderId] = useState<string | null>(null);
    const [cancellingId, setCancellingId] = useState<string | null>(null);
    const [cancelDialogOrderId, setCancelDialogOrderId] = useState<string | null>(null);
    const [payingOrderId, setPayingOrderId] = useState<string | null>(null);
    const paymentInFlight = useRef(false);

    // Tab navigation
    const [activeTab, setActiveTab] = useState<"orders" | "addresses">("orders");

    // Auth guard
    useEffect(() => {
        if (!isLoggedIn) navigate("/login");
    }, [isLoggedIn, navigate]);

    // Load addresses
    useEffect(() => {
        if (!isLoggedIn) return;
        const fetch = async () => {
            try {
                const res = await apiService.getAddresses();
                setAddresses(res.data || []);
            } catch { /* ignore */ }
            finally { setLoadingAddresses(false); }
        };
        fetch();
    }, [isLoggedIn]);

    // Sync profile form when data loads
    const profile = profileData?.data;
    useEffect(() => {
        if (profile) {
            setProfileName(profile.name || "");
            setProfileEmail(profile.email || "");
        }
    }, [profile]);

    // ── Handlers ──────────────────────────────────────────────────────────

    const handleLogout = async () => {
        await logout();
        navigate("/");
    };

    const handleSaveProfile = async () => {
        setSavingProfile(true);
        try {
            await apiService.updateProfile({
                name: profileName.trim() || undefined,
                email: profileEmail.trim() || undefined,
            });
            toast.success("Profile updated");
            setEditingProfile(false);
            refetchProfile();
        } catch (err: any) {
            toast.error(err.response?.data?.detail || "Failed to update profile");
        } finally {
            setSavingProfile(false);
        }
    };

    const openAddressDialog = (addr?: Address) => {
        if (addr) {
            setEditingAddressId(addr.id);
            setAddressForm({
                name: addr.name, mobile: addr.mobile, line1: addr.line1,
                line2: addr.line2 || "", city: addr.city, state: addr.state,
                pincode: addr.pincode, country: addr.country || "India",
                address_type: addr.address_type || "home",
                landmark: addr.landmark || "", is_default: addr.is_default,
            });
        } else {
            setEditingAddressId(null);
            setAddressForm({ ...EMPTY_ADDRESS });
        }
        setAddressDialogOpen(true);
    };

    const handleSaveAddress = async () => {
        if (!addressForm.name || !addressForm.mobile || !addressForm.line1 || !addressForm.city || !addressForm.state || !addressForm.pincode) {
            toast.error("Please fill all required fields");
            return;
        }
        let mobile = addressForm.mobile.replace(/[\s\-()]/g, '');
        if (mobile.startsWith('0')) mobile = mobile.substring(1);
        if (!mobile.startsWith('+') && mobile.length === 10) mobile = `+91${mobile}`;

        setSavingAddress(true);
        try {
            const payload = { ...addressForm, mobile };
            if (editingAddressId) {
                const res = await apiService.updateAddress(editingAddressId, payload);
                setAddresses(prev => prev.map(a => a.id === editingAddressId ? res.data : a));
                toast.success("Address updated");
            } else {
                const res = await apiService.createAddress(payload);
                setAddresses(prev => [...prev, res.data]);
                toast.success("Address added");
            }
            setAddressDialogOpen(false);
        } catch (err: any) {
            const detail = err.response?.data?.detail;
            toast.error(Array.isArray(detail) ? detail.map((d: any) => d.msg).join(", ") : (typeof detail === 'string' ? detail : "Failed to save address"));
        } finally {
            setSavingAddress(false);
        }
    };

    const handleDeleteAddress = async (id: string) => {
        setDeletingAddressId(id);
        try {
            await apiService.deleteAddress(id);
            setAddresses(prev => prev.filter(a => a.id !== id));
            toast.success("Address deleted");
        } catch (err: any) {
            toast.error(err.response?.data?.detail || "Failed to delete");
        } finally {
            setDeletingAddressId(null);
        }
    };

    const handleCancelOrder = async (orderId: string) => {
        setCancellingId(orderId);
        try {
            const res = await apiService.cancelOrder(orderId);
            toast.success(res.data?.message || "Order cancelled successfully");
            setCancelDialogOrderId(null);
            refetchOrders();
        } catch (error: any) {
            toast.error(error.response?.data?.detail || "Failed to cancel order");
        } finally {
            setCancellingId(null);
        }
    };

    const handleContinuePayment = async (order: any) => {
        if (paymentInFlight.current) return;
        paymentInFlight.current = true;
        setPayingOrderId(order.id);

        try {
            // Create payment for the existing pending order
            const paymentRes = await apiService.createPayment(order.id);
            const { razorpay_order_id, razorpay_key_id, amount, currency } = paymentRes.data;

            const scriptLoaded = await loadRazorpayScript();
            if (!scriptLoaded) {
                toast.error("Failed to load payment gateway. Please refresh.");
                setPayingOrderId(null);
                paymentInFlight.current = false;
                return;
            }

            const options = {
                key: razorpay_key_id,
                amount,
                currency,
                name: "Karungali Heritage",
                description: `Order #${order.order_number}`,
                order_id: razorpay_order_id,
                handler: async function (response: any) {
                    try {
                        await apiService.verifyPayment({
                            razorpay_order_id: response.razorpay_order_id,
                            razorpay_payment_id: response.razorpay_payment_id,
                            razorpay_signature: response.razorpay_signature
                        });
                        toast.success("Payment successful! Order confirmed.");
                        refetchOrders();
                    } catch (err) {
                        console.error("Payment verification failed:", err);
                        toast.error("Payment verification failed. Contact support if amount was deducted.");
                    } finally {
                        setPayingOrderId(null);
                        paymentInFlight.current = false;
                    }
                },
                prefill: {
                    contact: order.shipping_mobile
                },
                theme: { color: "#765341" },
                modal: {
                    ondismiss: function () {
                        setPayingOrderId(null);
                        paymentInFlight.current = false;
                        toast.info("Payment cancelled. You can retry anytime.");
                    }
                }
            };

            const rzp = new (window as any).Razorpay(options);
            rzp.on('payment.failed', function (response: any) {
                toast.error(response.error.description || "Payment failed");
                setPayingOrderId(null);
                paymentInFlight.current = false;
            });
            rzp.open();
        } catch (error: any) {
            toast.error(error.response?.data?.detail || "Failed to initiate payment");
            setPayingOrderId(null);
            paymentInFlight.current = false;
        }
    };

    if (!isLoggedIn) return null;

    const orders = ordersData?.data?.items || [];

    // ── Render ────────────────────────────────────────────────────────────

    return (
        <div className="min-h-screen bg-[#FDFBF7]">
            <Header />

            <main className="pt-24 pb-16 px-4 max-w-5xl mx-auto">
                <h1 className="font-serif text-3xl md:text-4xl text-[#765341] mb-8 text-center">
                    My Account
                </h1>

                <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">

                    {/* ────── LEFT SIDEBAR: Profile ────── */}
                    <div className="space-y-4">
                        <div className="bg-white border border-[#F3E9DC] rounded-xl p-6 shadow-sm">
                            <div className="flex items-center justify-between mb-4">
                                <h2 className="font-serif text-xl text-[#765341] flex items-center gap-2">
                                    <User className="w-5 h-5" /> Profile
                                </h2>
                                {!editingProfile && profile && (
                                    <button onClick={() => setEditingProfile(true)} className="text-xs text-[#9A6A51] hover:text-[#765341] flex items-center gap-1">
                                        <Pencil className="w-3 h-3" /> Edit
                                    </button>
                                )}
                            </div>

                            {profileLoading ? (
                                <div className="flex justify-center py-6"><Loader2 className="w-5 h-5 animate-spin text-[#9A6A51]" /></div>
                            ) : profile ? (
                                editingProfile ? (
                                    <div className="space-y-4">
                                        <div>
                                            <Label className="text-[#9A6A51] text-xs">Full Name</Label>
                                            <Input value={profileName} onChange={e => setProfileName(e.target.value)} placeholder="Your name" className="mt-1 border-[#F3E9DC]" />
                                        </div>
                                        <div>
                                            <Label className="text-[#9A6A51] text-xs">Email</Label>
                                            <Input type="email" value={profileEmail} onChange={e => setProfileEmail(e.target.value)} placeholder="your@email.com" className="mt-1 border-[#F3E9DC]" />
                                        </div>
                                        <div>
                                            <Label className="text-[#9A6A51] text-xs">Mobile</Label>
                                            <Input value={profile.mobile_number || ""} disabled className="mt-1 bg-gray-50 border-[#F3E9DC] text-gray-500" />
                                            <p className="text-[10px] text-gray-400 mt-1">Mobile cannot be changed</p>
                                        </div>
                                        <div className="flex gap-2">
                                            <Button onClick={handleSaveProfile} disabled={savingProfile} className="flex-1 bg-[#765341] hover:bg-[#5C4033] text-white" size="sm">
                                                {savingProfile ? <Loader2 className="w-3 h-3 animate-spin mr-1" /> : <Check className="w-3 h-3 mr-1" />}
                                                Save
                                            </Button>
                                            <Button variant="outline" size="sm" onClick={() => { setEditingProfile(false); setProfileName(profile.name || ""); setProfileEmail(profile.email || ""); }} className="border-[#F3E9DC]">
                                                Cancel
                                            </Button>
                                        </div>
                                    </div>
                                ) : (
                                    <div className="space-y-3 text-sm">
                                        <div>
                                            <span className="text-[#9A6A51] text-xs">Name</span>
                                            <p className="font-medium text-[#765341]">{profile.name || <span className="text-gray-400 italic">Not set</span>}</p>
                                        </div>
                                        <div>
                                            <span className="text-[#9A6A51] text-xs">Mobile</span>
                                            <p className="font-medium text-[#765341]">{profile.mobile_number || "—"}</p>
                                        </div>
                                        <div>
                                            <span className="text-[#9A6A51] text-xs">Email</span>
                                            <p className="font-medium text-[#765341]">{profile.email || <span className="text-gray-400 italic">Not set</span>}</p>
                                        </div>
                                    </div>
                                )
                            ) : (
                                <p className="text-sm text-gray-400">Failed to load profile</p>
                            )}
                        </div>

                        <Button
                            variant="outline"
                            className="w-full justify-start gap-2 border-red-200 text-red-500 hover:bg-red-50 rounded-xl"
                            onClick={handleLogout}
                        >
                            <LogOut className="w-4 h-4" /> Logout
                        </Button>
                    </div>

                    {/* ────── RIGHT: Tabs (Orders / Addresses) ────── */}
                    <div className="lg:col-span-2 space-y-4">

                        {/* Tab Buttons */}
                        <div className="flex gap-2 border-b border-[#F3E9DC] pb-0">
                            <button
                                onClick={() => setActiveTab("orders")}
                                className={`flex items-center gap-2 px-4 py-2.5 text-sm font-medium border-b-2 transition-colors -mb-px ${activeTab === "orders" ? "border-[#765341] text-[#765341]" : "border-transparent text-gray-400 hover:text-[#9A6A51]"}`}
                            >
                                <Package className="w-4 h-4" /> My Orders
                            </button>
                            <button
                                onClick={() => setActiveTab("addresses")}
                                className={`flex items-center gap-2 px-4 py-2.5 text-sm font-medium border-b-2 transition-colors -mb-px ${activeTab === "addresses" ? "border-[#765341] text-[#765341]" : "border-transparent text-gray-400 hover:text-[#9A6A51]"}`}
                            >
                                <MapPin className="w-4 h-4" /> Addresses
                            </button>
                        </div>

                        {/* ──── ORDERS TAB ──── */}
                        {activeTab === "orders" && (
                            <div className="bg-white border border-[#F3E9DC] rounded-xl p-6 shadow-sm">
                                {ordersLoading ? (
                                    <div className="flex justify-center py-8"><Loader2 className="w-6 h-6 animate-spin text-[#9A6A51]" /></div>
                                ) : orders.length === 0 ? (
                                    <div className="text-center py-12">
                                        <Package className="w-12 h-12 text-gray-300 mx-auto mb-4" />
                                        <p className="text-gray-500 mb-4">No orders yet</p>
                                        <Button onClick={() => navigate("/")} className="bg-[#765341] text-white hover:bg-[#5C4033]">Shop Now</Button>
                                    </div>
                                ) : (
                                    <div className="space-y-3">
                                        {orders.map((order: any) => (
                                            <div key={order.id} className="border border-gray-200 rounded-lg overflow-hidden">
                                                {/* Order Header */}
                                                <div
                                                    className="flex justify-between items-center p-4 cursor-pointer hover:bg-gray-50 transition-colors"
                                                    onClick={() => setExpandedOrderId(expandedOrderId === order.id ? null : order.id)}
                                                >
                                                    <div className="flex-1">
                                                        <div className="flex items-center gap-3 mb-1">
                                                            <span className="font-medium text-sm text-[#765341]">#{order.order_number}</span>
                                                            <span className={`text-[10px] px-2 py-0.5 rounded-full font-medium uppercase tracking-wider ${order.status === 'delivered' ? 'bg-green-100 text-green-700' :
                                                                order.status === 'cancelled' ? 'bg-red-100 text-red-700' :
                                                                    order.status === 'confirmed' ? 'bg-blue-100 text-blue-700' :
                                                                        order.status === 'processing' ? 'bg-purple-100 text-purple-700' :
                                                                            order.status === 'shipped' ? 'bg-indigo-100 text-indigo-700' :
                                                                                'bg-yellow-100 text-yellow-700'
                                                                }`}>
                                                                {order.status}
                                                            </span>
                                                        </div>
                                                        <div className="flex items-center gap-4 text-xs text-gray-500">
                                                            <span>{new Date(order.created_at).toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' })}</span>
                                                            <span className="font-medium">₹{Number(order.total).toLocaleString()}</span>
                                                            <span>{order.items?.length || 0} item(s)</span>
                                                        </div>
                                                    </div>
                                                    {expandedOrderId === order.id ? <ChevronUp className="w-4 h-4 text-gray-400" /> : <ChevronDown className="w-4 h-4 text-gray-400" />}
                                                </div>

                                                {/* Expanded Details */}
                                                {expandedOrderId === order.id && (
                                                    <div className="border-t border-gray-100 p-4 bg-[#FDFBF7]">
                                                        {/* Items */}
                                                        <div className="space-y-3 mb-4">
                                                            {order.items?.map((item: any) => (
                                                                <div key={item.id} className="flex gap-3">
                                                                    <div className="w-12 h-12 bg-gray-100 rounded flex-shrink-0 overflow-hidden">
                                                                        {item.product_image && <img src={item.product_image} className="w-full h-full object-cover" alt={item.product_name} />}
                                                                    </div>
                                                                    <div className="flex-1">
                                                                        <p className="text-sm font-medium">{item.product_name}</p>
                                                                        <p className="text-xs text-gray-500">Qty: {item.quantity} × ₹{Number(item.price).toLocaleString()}</p>
                                                                    </div>
                                                                    <p className="text-sm font-medium">₹{Number(item.total).toLocaleString()}</p>
                                                                </div>
                                                            ))}
                                                        </div>

                                                        {/* Price Breakdown */}
                                                        <div className="border-t border-gray-200 pt-3 mt-3 space-y-1 text-sm">
                                                            <div className="flex justify-between"><span>Subtotal</span><span>₹{Number(order.subtotal).toLocaleString()}</span></div>
                                                            <div className="flex justify-between"><span>Shipping</span><span>{Number(order.shipping_fee) === 0 ? 'Free' : `₹${Number(order.shipping_fee).toLocaleString()}`}</span></div>
                                                            {Number(order.tax) > 0 && <div className="flex justify-between"><span>Tax</span><span>₹{Number(order.tax).toLocaleString()}</span></div>}
                                                            {Number(order.discount) > 0 && <div className="flex justify-between text-green-600"><span>Discount</span><span>-₹{Number(order.discount).toLocaleString()}</span></div>}
                                                            <div className="flex justify-between font-medium border-t border-gray-200 pt-2"><span>Total</span><span>₹{Number(order.total).toLocaleString()}</span></div>
                                                        </div>

                                                        {/* Shipping Address */}
                                                        <div className="border-t border-gray-200 pt-3 mt-3 text-sm">
                                                            <p className="text-gray-500 mb-1 text-xs font-medium uppercase tracking-wider">Delivery Address</p>
                                                            <p>{order.shipping_name}, {order.shipping_line1}</p>
                                                            {order.shipping_line2 && <p>{order.shipping_line2}</p>}
                                                            <p>{order.shipping_city}, {order.shipping_state} - {order.shipping_pincode}</p>
                                                            <p className="text-xs text-gray-500 mt-1">Phone: {order.shipping_mobile}</p>
                                                        </div>

                                                        {/* Continue Payment — for pending (unpaid) orders */}
                                                        {order.status === 'pending' && (
                                                            <div className="border-t border-gray-200 pt-3 mt-3 flex gap-2">
                                                                <Button
                                                                    size="sm"
                                                                    className="bg-[#765341] hover:bg-[#5C4033] text-white"
                                                                    onClick={(e) => { e.stopPropagation(); handleContinuePayment(order); }}
                                                                    disabled={payingOrderId === order.id}
                                                                >
                                                                    {payingOrderId === order.id ? (
                                                                        <><Loader2 className="w-3 h-3 animate-spin mr-1" /> Processing...</>
                                                                    ) : (
                                                                        <><CreditCard className="w-3 h-3 mr-1" /> Continue Payment</>
                                                                    )}
                                                                </Button>
                                                            </div>
                                                        )}

                                                        {/* Cancel — only for paid orders */}
                                                        {['confirmed', 'processing'].includes(order.status) && (
                                                            <div className="border-t border-gray-200 pt-3 mt-3">
                                                                <Button
                                                                    variant="outline"
                                                                    size="sm"
                                                                    className="border-red-200 text-red-500 hover:bg-red-50"
                                                                    onClick={(e) => { e.stopPropagation(); setCancelDialogOrderId(order.id); }}
                                                                    disabled={cancellingId === order.id}
                                                                >
                                                                    <X className="w-3 h-3 mr-1" /> Cancel Order
                                                                </Button>
                                                            </div>
                                                        )}
                                                    </div>
                                                )}
                                            </div>
                                        ))}
                                    </div>
                                )}
                            </div>
                        )}

                        {/* ──── ADDRESSES TAB ──── */}
                        {activeTab === "addresses" && (
                            <div className="bg-white border border-[#F3E9DC] rounded-xl p-6 shadow-sm">
                                <div className="flex items-center justify-between mb-4">
                                    <h3 className="font-serif text-lg text-[#765341]">Saved Addresses</h3>
                                    <Button size="sm" onClick={() => openAddressDialog()} className="bg-[#765341] hover:bg-[#5C4033] text-white">
                                        <Plus className="w-3 h-3 mr-1" /> Add New
                                    </Button>
                                </div>

                                {loadingAddresses ? (
                                    <div className="flex justify-center py-8"><Loader2 className="w-6 h-6 animate-spin text-[#9A6A51]" /></div>
                                ) : addresses.length === 0 ? (
                                    <div className="text-center py-12">
                                        <MapPin className="w-10 h-10 text-gray-300 mx-auto mb-3" />
                                        <p className="text-gray-500 mb-3">No saved addresses</p>
                                        <Button onClick={() => openAddressDialog()} className="bg-[#765341] text-white hover:bg-[#5C4033]" size="sm">
                                            <Plus className="w-3 h-3 mr-1" /> Add Address
                                        </Button>
                                    </div>
                                ) : (
                                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                        {addresses.map((addr) => (
                                            <div key={addr.id} className={`relative border rounded-lg p-4 ${addr.is_default ? "border-[#765341] bg-[#FDFBF7]" : "border-gray-200"}`}>
                                                {addr.is_default && (
                                                    <span className="absolute top-2 right-2 flex items-center gap-1 text-[10px] font-medium text-[#765341] bg-[#F3E9DC] px-2 py-0.5 rounded-full">
                                                        <Star className="w-2.5 h-2.5" /> Default
                                                    </span>
                                                )}
                                                <div className="flex items-start gap-2 mb-2">
                                                    <span className="font-medium text-sm">{addr.name}</span>
                                                    <span className="text-[10px] px-1.5 py-0.5 bg-gray-100 rounded uppercase text-gray-500">{addr.address_type}</span>
                                                </div>
                                                <p className="text-sm text-gray-600">{addr.line1}</p>
                                                {addr.line2 && <p className="text-sm text-gray-600">{addr.line2}</p>}
                                                <p className="text-sm text-gray-600">{addr.city}, {addr.state} - {addr.pincode}</p>
                                                {addr.landmark && <p className="text-xs text-gray-400 mt-1">Landmark: {addr.landmark}</p>}
                                                <p className="text-xs text-gray-500 mt-1">📞 {addr.mobile}</p>

                                                <div className="flex gap-2 mt-3 pt-2 border-t border-gray-100">
                                                    <button onClick={() => openAddressDialog(addr)} className="text-xs text-[#9A6A51] hover:text-[#765341] flex items-center gap-1">
                                                        <Pencil className="w-3 h-3" /> Edit
                                                    </button>
                                                    <button
                                                        onClick={() => handleDeleteAddress(addr.id)}
                                                        disabled={deletingAddressId === addr.id}
                                                        className="text-xs text-red-400 hover:text-red-600 flex items-center gap-1"
                                                    >
                                                        {deletingAddressId === addr.id ? <Loader2 className="w-3 h-3 animate-spin" /> : <Trash2 className="w-3 h-3" />} Delete
                                                    </button>
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                )}
                            </div>
                        )}
                    </div>
                </div>
            </main>

            <Footer />

            {/* ──── CANCEL ORDER CONFIRMATION DIALOG ──── */}
            <Dialog open={!!cancelDialogOrderId} onOpenChange={() => setCancelDialogOrderId(null)}>
                <DialogContent className="sm:max-w-md">
                    <DialogHeader>
                        <DialogTitle className="text-[#765341]">Cancel Order?</DialogTitle>
                    </DialogHeader>
                    <p className="text-sm text-gray-600 mt-2">
                        Are you sure you want to cancel this order? If payment was already made, a refund will be initiated and will reflect in 5-7 business days.
                    </p>
                    <div className="flex gap-3 mt-6">
                        <Button
                            variant="outline"
                            className="flex-1"
                            onClick={() => setCancelDialogOrderId(null)}
                            disabled={!!cancellingId}
                        >
                            Keep Order
                        </Button>
                        <Button
                            className="flex-1 bg-red-500 hover:bg-red-600 text-white"
                            onClick={() => cancelDialogOrderId && handleCancelOrder(cancelDialogOrderId)}
                            disabled={!!cancellingId}
                        >
                            {cancellingId ? <><Loader2 className="w-3 h-3 animate-spin mr-1" /> Cancelling...</> : "Yes, Cancel"}
                        </Button>
                    </div>
                </DialogContent>
            </Dialog>

            {/* ──── ADDRESS ADD/EDIT DIALOG ──── */}
            <Dialog open={addressDialogOpen} onOpenChange={setAddressDialogOpen}>
                <DialogContent className="sm:max-w-[480px] max-h-[90vh] overflow-y-auto">
                    <DialogHeader>
                        <DialogTitle className="text-[#765341]">{editingAddressId ? "Edit Address" : "Add New Address"}</DialogTitle>
                    </DialogHeader>
                    <div className="grid gap-4 py-2">
                        <div className="grid grid-cols-2 gap-3">
                            <div>
                                <Label className="text-xs text-[#9A6A51]">Full Name *</Label>
                                <Input value={addressForm.name} onChange={e => setAddressForm({ ...addressForm, name: e.target.value })} className="mt-1 border-[#F3E9DC]" />
                            </div>
                            <div>
                                <Label className="text-xs text-[#9A6A51]">Mobile *</Label>
                                <Input value={addressForm.mobile} onChange={e => setAddressForm({ ...addressForm, mobile: e.target.value })} placeholder="9876543210" className="mt-1 border-[#F3E9DC]" />
                            </div>
                        </div>
                        <div>
                            <Label className="text-xs text-[#9A6A51]">Address Line 1 *</Label>
                            <Input value={addressForm.line1} onChange={e => setAddressForm({ ...addressForm, line1: e.target.value })} className="mt-1 border-[#F3E9DC]" />
                        </div>
                        <div>
                            <Label className="text-xs text-[#9A6A51]">Address Line 2</Label>
                            <Input value={addressForm.line2} onChange={e => setAddressForm({ ...addressForm, line2: e.target.value })} className="mt-1 border-[#F3E9DC]" />
                        </div>
                        <div className="grid grid-cols-2 gap-3">
                            <div>
                                <Label className="text-xs text-[#9A6A51]">City *</Label>
                                <Input value={addressForm.city} onChange={e => setAddressForm({ ...addressForm, city: e.target.value })} className="mt-1 border-[#F3E9DC]" />
                            </div>
                            <div>
                                <Label className="text-xs text-[#9A6A51]">Pincode *</Label>
                                <Input value={addressForm.pincode} onChange={e => setAddressForm({ ...addressForm, pincode: e.target.value })} className="mt-1 border-[#F3E9DC]" />
                            </div>
                        </div>
                        <div className="grid grid-cols-2 gap-3">
                            <div>
                                <Label className="text-xs text-[#9A6A51]">State *</Label>
                                <Input value={addressForm.state} onChange={e => setAddressForm({ ...addressForm, state: e.target.value })} className="mt-1 border-[#F3E9DC]" />
                            </div>
                            <div>
                                <Label className="text-xs text-[#9A6A51]">Landmark</Label>
                                <Input value={addressForm.landmark} onChange={e => setAddressForm({ ...addressForm, landmark: e.target.value })} className="mt-1 border-[#F3E9DC]" />
                            </div>
                        </div>
                        <div className="flex gap-4">
                            <Label className="text-xs text-[#9A6A51] self-center">Type:</Label>
                            {["home", "office", "other"].map(t => (
                                <button
                                    key={t}
                                    onClick={() => setAddressForm({ ...addressForm, address_type: t })}
                                    className={`px-3 py-1 text-xs rounded-full border transition-colors ${addressForm.address_type === t ? "bg-[#765341] text-white border-[#765341]" : "border-gray-200 text-gray-500 hover:border-[#765341]"}`}
                                >
                                    {t.charAt(0).toUpperCase() + t.slice(1)}
                                </button>
                            ))}
                        </div>
                        <label className="flex items-center gap-2 text-sm text-gray-600 cursor-pointer">
                            <input type="checkbox" checked={addressForm.is_default} onChange={e => setAddressForm({ ...addressForm, is_default: e.target.checked })} className="rounded border-gray-300" />
                            Set as default address
                        </label>
                    </div>
                    <Button onClick={handleSaveAddress} disabled={savingAddress} className="w-full bg-[#765341] hover:bg-[#5C4033] text-white mt-2">
                        {savingAddress ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : null}
                        {editingAddressId ? "Update Address" : "Save Address"}
                    </Button>
                </DialogContent>
            </Dialog>
        </div>
    );
}
