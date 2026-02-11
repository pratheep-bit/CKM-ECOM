import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Loader2 } from "lucide-react";
import Header from "@/components/Header";
import Footer from "@/components/Footer";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { InputOTP, InputOTPGroup, InputOTPSlot } from "@/components/ui/input-otp";
import { useSendOTP } from "@/hooks/useApi";
import { useAuth } from "@/context/AuthContext";
import { apiService } from "@/lib/api";
import { useToast } from "@/hooks/use-toast";

export default function Login() {
    const navigate = useNavigate();
    const { toast } = useToast();
    const { login } = useAuth();
    const sendOTP = useSendOTP();

    const [step, setStep] = useState<"phone" | "otp">("phone");
    const [mobileNumber, setMobileNumber] = useState("");
    const [otp, setOtp] = useState("");
    const [verifying, setVerifying] = useState(false);

    const handleSendOTP = async () => {
        if (!mobileNumber || mobileNumber.length !== 10) {
            toast({
                title: "Invalid Mobile Number",
                description: "Please enter a valid 10-digit mobile number",
                variant: "destructive",
            });
            return;
        }

        try {
            await sendOTP.mutateAsync(mobileNumber);
            setStep("otp");
            toast({
                title: "OTP Sent",
                description: "Please check your phone for the OTP",
            });
        } catch (error: any) {
            toast({
                title: "Failed to Send OTP",
                description: error.response?.data?.detail || "Please try again",
                variant: "destructive",
            });
        }
    };

    const handleVerifyOTP = async () => {
        if (!otp || otp.length !== 6) {
            toast({
                title: "Invalid OTP",
                description: "Please enter the 6-digit OTP",
                variant: "destructive",
            });
            return;
        }

        setVerifying(true);
        try {
            const response = await apiService.verifyOTP(mobileNumber, otp);

            if (response.data.access_token) {
                // Use AuthContext login — single source of truth for token storage
                login(response.data.access_token, response.data.refresh_token);

                toast({
                    title: "Login Successful",
                    description: "Welcome back!",
                });

                // Check for return url — use navigate() to preserve React state
                const returnUrl = sessionStorage.getItem("return_url");
                if (returnUrl) {
                    sessionStorage.removeItem("return_url");
                    navigate(returnUrl);
                } else {
                    navigate("/account");
                }
            } else {
                toast({
                    title: "Error",
                    description: "Failed to retrieve access token",
                    variant: "destructive"
                });
            }
        } catch (error: any) {
            console.error(error);
            toast({
                title: "Invalid OTP",
                description: error.response?.data?.detail || "Please try again",
                variant: "destructive",
            });
        } finally {
            setVerifying(false);
        }
    };

    return (
        <div className="min-h-screen bg-white">
            <Header />

            <main className="pt-32 pb-16 px-4">
                <div className="max-w-md mx-auto">
                    <div className="text-center mb-8">
                        <h1 className="font-serif text-4xl text-[#765341] mb-2">
                            Welcome
                        </h1>
                        <p className="text-[#9A6A51]">
                            {step === "phone"
                                ? "Enter your mobile number to continue"
                                : "Check your phone for the OTP"}
                        </p>
                    </div>

                    <div className="border border-[#F3E9DC] p-8 shadow-sm rounded-sm">
                        {step === "phone" ? (
                            <div className="space-y-6">
                                <div>
                                    <Label htmlFor="mobile" className="text-[#765341] block mb-2">Mobile Number</Label>
                                    <div className="flex gap-2">
                                        <div className="flex items-center justify-center px-3 border border-[#F3E9DC] bg-[#FDFBF7] text-[#765341] font-medium">+91</div>
                                        <Input
                                            id="mobile"
                                            type="tel"
                                            value={mobileNumber}
                                            onChange={(e) => setMobileNumber(e.target.value.replace(/\D/g, ""))}
                                            placeholder="9876543210"
                                            maxLength={10}
                                            className="text-lg tracking-wide border-[#F3E9DC] focus-visible:ring-[#765341]"
                                        />
                                    </div>
                                </div>

                                <Button
                                    onClick={handleSendOTP}
                                    disabled={sendOTP.isPending || mobileNumber.length !== 10}
                                    className="w-full bg-[#765341] text-white hover:bg-[#5C4033] h-11 text-lg"
                                >
                                    {sendOTP.isPending ? (
                                        <>
                                            <Loader2 className="w-4 h-4 animate-spin mr-2" />
                                            Sending...
                                        </>
                                    ) : (
                                        "Get OTP"
                                    )}
                                </Button>
                            </div>
                        ) : (
                            <div className="space-y-6">
                                <div>
                                    <div className="text-center mb-6">
                                        <p className="text-sm text-[#9A6A51] mb-1">Enter OTP sent to</p>
                                        <p className="font-medium text-[#765341]">+91 {mobileNumber}</p>
                                        <button
                                            onClick={() => setStep("phone")}
                                            className="text-xs text-[#765341] underline mt-1 hover:text-[#5C4033]"
                                        >
                                            Change Number
                                        </button>
                                    </div>

                                    <div className="flex justify-center mb-2">
                                        <InputOTP
                                            maxLength={6}
                                            value={otp}
                                            onChange={(value) => setOtp(value)}
                                        >
                                            <InputOTPGroup className="gap-2">
                                                {[0, 1, 2, 3, 4, 5].map((idx) => (
                                                    <InputOTPSlot
                                                        key={idx}
                                                        index={idx}
                                                        className="w-10 h-12 border-[#F3E9DC] text-xl"
                                                    />
                                                ))}
                                            </InputOTPGroup>
                                        </InputOTP>
                                    </div>
                                </div>

                                <Button
                                    onClick={handleVerifyOTP}
                                    disabled={verifying || otp.length !== 6}
                                    className="w-full bg-[#765341] text-white hover:bg-[#5C4033] h-11 text-lg"
                                >
                                    {verifying ? (
                                        <>
                                            <Loader2 className="w-4 h-4 animate-spin mr-2" />
                                            Verifying...
                                        </>
                                    ) : (
                                        "Verify & Login"
                                    )}
                                </Button>

                                <div className="text-center">
                                    <button
                                        className="text-sm text-[#9A6A51] hover:underline"
                                        onClick={handleSendOTP}
                                        disabled={sendOTP.isPending}
                                    >
                                        Resend OTP
                                    </button>
                                </div>
                            </div>
                        )}
                    </div>

                    <p className="text-xs text-center text-[#9A6A51] mt-6">
                        By continuing, you agree to our Terms of Service and Privacy Policy
                    </p>
                </div>
            </main>

            <Footer />
        </div>
    );
}
