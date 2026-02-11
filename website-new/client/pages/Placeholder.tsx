import { Link } from "react-router-dom";
import { ArrowLeft } from "lucide-react";
import Header from "@/components/Header";
import Footer from "@/components/Footer";

interface PlaceholderProps {
  title: string;
}

export default function Placeholder({ title }: PlaceholderProps) {
  return (
    <div className="min-h-screen flex flex-col">
      <Header />
      
      <main className="flex-1 flex items-center justify-center px-4 py-24">
        <div className="text-center max-w-2xl">
          <h1 className="font-serif text-4xl md:text-5xl text-[#765341] mb-6">
            {title}
          </h1>
          <p className="text-[#9A6A51] mb-8 leading-relaxed">
            This page is coming soon. We're working on bringing you more content about Karungali Mala and our sacred offerings.
          </p>
          <Link 
            to="/"
            className="inline-flex items-center gap-2 border border-[#765341] text-[#765341] px-6 py-3 hover:bg-[#765341] hover:text-white transition-all"
          >
            <ArrowLeft className="w-4 h-4" />
            Back to Home
          </Link>
        </div>
      </main>

      <Footer />
    </div>
  );
}
