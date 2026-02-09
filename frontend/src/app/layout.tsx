import "./globals.css";

export const metadata = {
  title: "AI Executive Cockpit",
  description: "AI-powered analytics dashboard",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="bg-slate-900 text-white antialiased">{children}</body>
    </html>
  );
}
