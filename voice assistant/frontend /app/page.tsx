"use client";
import { motion } from 'motion/react';
import { Button } from '@/components/ui/button';
import { useRouter } from 'next/navigation';
import Navigation from '@/components/navigation';

export default function Page() {
    const router = useRouter();

    return (
        <div className="min-h-screen bg-background flex flex-col">
            <Navigation />
            <main className="flex-1 flex items-center justify-center px-4 sm:px-6 lg:px-8 py-8">
                <div className="w-full max-w-4xl">
                    <motion.div
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        className="text-center space-y-8 w-full max-w-md mx-auto"
                    >
                        <div className="space-y-4">
                            <h1 className="text-4xl font-bold">AI Interview Assistant</h1>
                            <p className="text-xl text-muted-foreground">
                                Practice interviews with AI and get personalized job recommendations
                            </p>
                        </div>
                        <div className="flex flex-col sm:flex-row justify-center space-y-4 sm:space-y-0 sm:space-x-4">
                            <Button onClick={() => router.push('/login')} size="lg" className="w-full sm:w-auto">
                                Sign In
                            </Button>
                            <Button onClick={() => router.push('/signup')} variant="outline" size="lg" className="w-full sm:w-auto">
                                Sign Up
                            </Button>
                        </div>
                    </motion.div>
                </div>
            </main>
        </div>
    );
} 