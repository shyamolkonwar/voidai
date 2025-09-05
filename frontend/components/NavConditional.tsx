"use client";
import { usePathname } from "next/navigation";
import Navbar from "./Navbar";

export default function NavConditional() {
  const pathname = usePathname();
  if (pathname?.startsWith("/chat")) return null;
  return <Navbar />;
}




