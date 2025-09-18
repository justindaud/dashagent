"use client"; // Komponen ini perlu berjalan di sisi client untuk mengakses localStorage

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";

// Komponen ini akan membungkus halaman yang ingin kita lindungi
export default function AuthGuard({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  // State untuk melacak apakah pengecekan sudah selesai
  const [isVerified, setIsVerified] = useState(false);

  useEffect(() => {
    // Cek apakah ada token di localStorage
    const token = localStorage.getItem("authToken");

    if (!token) {
      // Jika tidak ada token, tendang ke halaman login
      router.push("/auth");
    } else {
      // Jika ada token, izinkan pengguna melihat halaman
      setIsVerified(true);
    }
  }, [router]); // useEffect akan berjalan saat komponen dimuat

  // Selama pengecekan, jangan tampilkan apa-apa (atau tampilkan loading spinner)
  // Setelah terverifikasi, tampilkan konten halaman (`children`)
  if (!isVerified) {
    return null; // atau <p>Loading...</p>
  }

  return <>{children}</>;
}
