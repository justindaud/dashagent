"use client";
import { Users, Calendar, MessageCircle } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { DashboardStats } from "@/lib/types";

interface StatCardsProps {
  stats: DashboardStats | null;
}

export function StatCards({ stats }: StatCardsProps) {
  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
      <Card className="shadow-md">
        <CardContent className="p-4">
          <div className="flex items-center">
            <Users className="w-10 h-10 text-primary" />
            <div className="ml-4">
              <p className="text-normal font-medium text-gray-600">Total Guests</p>
              <p className="text-2xl font-bold text-gray-900">{stats?.total_guests || 0}</p>
            </div>
          </div>
        </CardContent>
      </Card>
      <Card className="shadow-md">
        <CardContent className="p-4">
          <div className="flex items-center">
            <Calendar className="w-10 h-10 text-primary" />
            <div className="ml-4">
              <p className="text-normal font-medium text-gray-600">Reservations</p>
              <p className="text-2xl font-bold text-gray-900">{stats?.total_reservations || 0}</p>
            </div>
          </div>
        </CardContent>
      </Card>
      <Card className="shadow-md">
        <CardContent className="p-4">
          <div className="flex items-center">
            <MessageCircle className="w-10 h-10 text-primary" />
            <div className="ml-4">
              <p className="text-normal font-medium text-gray-600">Chats</p>
              <p className="text-2xl font-bold text-gray-900">{stats?.total_chats || 0}</p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
