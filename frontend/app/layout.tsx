import type { Metadata } from "next";
import "./globals.css";
import { Montserrat, Share_Tech_Mono } from "next/font/google";
import { ViewTransitionErrorSuppressor } from "@/components/ViewTransitionErrorSuppressor";
import { SettingsStatusProvider } from "@/context/SettingsStatusContext";

// 1. Define Montserrat
const montserrat = Montserrat({
  subsets: ["latin"],
  variable: "--font-montserrat", // This matches your CSS variable
  display: "swap",
});

// 2. Define Share Tech Mono
const mono = Share_Tech_Mono({
  weight: "400",
  subsets: ["latin"],
  variable: "--font-share-tech",
  display: "swap",
});

export const metadata: Metadata = {
  title: "Linudio",
  description: "Self-hosted YouTube video translation and dubbing, powered by local AI models.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="en"
      className={`${montserrat.variable} ${mono.variable} h-full antialiased dark`}
    >
      <body className="min-h-screen flex flex-col font-sans" suppressHydrationWarning={true}>
        <ViewTransitionErrorSuppressor />
        <SettingsStatusProvider>{children}</SettingsStatusProvider>
      </body>
    </html>
  );
}
