"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Button } from "./ui/button";

export default function Navigation() {
    const pathname = usePathname();

    return (
        <nav className="bg-white shadow-sm border-b">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                <div className="flex justify-between h-16">
                    <div className="flex items-center">
                        <Link href="/" className="flex items-center space-x-2">
                            <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center">
                                <span className="text-white font-bold text-sm">AI</span>
                            </div>
                            <span className="font-semibold text-xl text-gray-900">
                                Interview Assistant
                            </span>
                        </Link>
                    </div>

                    <div className="flex items-center space-x-4">
                        <Link href="/">
                            <Button
                                variant={pathname === "/" ? "default" : "ghost"}
                                className="text-sm"
                            >
                                Home
                            </Button>
                        </Link>
                        <Link href="/login">
                            <Button variant="outline" className="text-sm">
                                Sign In
                            </Button>
                        </Link>
                        <Link href="/signup">
                            <Button className="text-sm">
                                Sign Up
                            </Button>
                        </Link>
                    </div>
                </div>
            </div>
        </nav>
    );
} 