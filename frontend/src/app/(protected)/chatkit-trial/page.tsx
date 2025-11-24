"use client";

import { ChatKit, useChatKit } from "@openai/chatkit-react";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || "";
const DID_KEY = "chatkit_device_id";

function genDeviceId() {
  const arr = new Uint8Array(12);
  crypto.getRandomValues(arr);
  return (
    "web-" +
    Array.from(arr)
      .map((b) => b.toString(16).padStart(2, "0"))
      .join("")
  );
}

export default function ChatkitTrialPage() {
  const { control } = useChatKit({
    api: {
      async getClientSecret() {
        let deviceId = localStorage.getItem(DID_KEY);
        if (!deviceId) {
          deviceId = genDeviceId();
          localStorage.setItem(DID_KEY, deviceId);
        }

        const res = await fetch(`${API_BASE}/api/chatkit/session`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ device_id: deviceId }),
          credentials: "include",
        });
        if (!res.ok) throw new Error(await res.text());
        const data = await res.json();
        if (!data?.client_secret) throw new Error("Missing client_secret");
        return data.client_secret as string; // harus string
      },
    },
  });

  return (
    <div className="mx-auto w-full max-w-[520px] p-4">
      <div className="mb-3 text-lg font-semibold">DashAgent AI</div>
      <div className="h-[640px] w-full border border-neutral-300">
        <ChatKit control={control} className="h-full w-full" />
      </div>
    </div>
  );
}
