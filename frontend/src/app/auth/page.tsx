"use client";

// Import React untuk tipe data event
import React, { useState } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

export default function AuthPage() {
  const router = useRouter();

  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  // Perbaikan 1: Tambahkan tipe data untuk parameter 'event'
  const handleLogin = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault(); // (Baris 17) Sekarang sudah aman
    setIsLoading(true);
    setError("");

    try {
      const response = await fetch("http://localhost:8000/api/auth/login", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ username, password }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || "Login gagal. Periksa kembali username dan password Anda.");
      }

      localStorage.setItem("authToken", data.dash_agent);
      router.push("/");
    } catch (err) {
      // Perbaikan 2: Cek tipe data 'err' sebelum digunakan
      if (err instanceof Error) {
        setError(err.message);
      } else {
        setError("Terjadi kesalahan yang tidak terduga.");
      }
      console.error("Login error:", err);
    } finally {
      setIsLoading(false);
    } // (Baris 46) Error di sekitar sini sudah teratasi
  };

  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-background p-4">
      <Card className="w-full max-w-sm">
        <form onSubmit={handleLogin}>
          <CardHeader>
            <CardTitle>Login to DashAgent</CardTitle>
            <CardDescription>Enter your username below to login to your account</CardDescription>
            {error && <p className="mt-2 text-sm font-medium text-red-500">{error}</p>}
          </CardHeader>
          <CardContent>
            <div className="flex flex-col gap-6">
              <div className="grid gap-2">
                <Label htmlFor="username">Username</Label>
                <Input
                  id="username"
                  type="text"
                  placeholder="JohnDoe"
                  required
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  disabled={isLoading}
                />
              </div>
              <div className="grid gap-2">
                <Label htmlFor="password">Password</Label>
                <Input id="password" type="password" required value={password} onChange={(e) => setPassword(e.target.value)} disabled={isLoading} />
              </div>
            </div>
          </CardContent>
          <CardFooter>
            <Button type="submit" className="w-full" disabled={isLoading}>
              {isLoading ? "Logging in..." : "Login"}
            </Button>
          </CardFooter>
        </form>
      </Card>
    </div>
  );
}
