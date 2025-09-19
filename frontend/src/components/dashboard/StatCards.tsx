"use client";
import { Users, Calendar, MessageCircle } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { DashboardStats } from "@/lib/types";
import { Skeleton } from "@/components/ui/skeleton";

interface StatCardsProps {
  stats: DashboardStats | null;
}

const StatCard = ({ icon: Icon, title, value }: { icon: React.ElementType; title: string; value: string | number }) => (
  <Card className="shadow-sm hover:shadow-md transition-shadow duration-200">
    <CardContent className="p-4 sm:p-5">
      <div className="flex items-center">
        <div className="flex-shrink-0 bg-primary/10 text-primary p-3 rounded-lg">
          <Icon className="w-6 h-6" />
        </div>
        <div className="ml-4">
          <p className="text-sm font-medium text-gray-500 truncate">{title}</p>
          <p className="text-2xl font-bold text-gray-900">{value}</p>
        </div>
      </div>
    </CardContent>
  </Card>
);

const StatCardSkeleton = () => (
  <Card className="shadow-sm">
    <CardContent className="p-4 sm:p-5">
      <div className="flex items-center">
        <Skeleton className="w-12 h-12 rounded-lg" />
        <div className="ml-4 space-y-2">
          <Skeleton className="h-4 w-24" />
          <Skeleton className="h-7 w-16" />
        </div>
      </div>
    </CardContent>
  </Card>
);

export function StatCards({ stats }: StatCardsProps) {
  if (!stats) {
    return (
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 mb-6">
        <StatCardSkeleton />
        <StatCardSkeleton />
        <StatCardSkeleton />
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 mb-6">
      <StatCard icon={Users} title="Total Guests" value={stats.total_guests.toLocaleString("id-ID")} />
      <StatCard icon={Calendar} title="Reservations" value={stats.total_reservations.toLocaleString("id-ID")} />
      <StatCard icon={MessageCircle} title="Chats" value={stats.total_chats.toLocaleString("id-ID")} />
    </div>
  );
}
