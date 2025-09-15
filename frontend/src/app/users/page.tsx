"use client";

import { useState } from "react";
import { Header } from "../../components/dashboard/Header";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Switch } from "@/components/ui/switch";
import { User, Shield } from "lucide-react";

type UserRole = "admin" | "manager" | "staff";
interface UserAccount {
  id: number;
  fullName: string;
  username: string;
  role: UserRole;
}

const sampleUsers: UserAccount[] = [
  { id: 1, fullName: "Admin Utama", username: "admin", role: "admin" },
  { id: 2, fullName: "Budi Santoso", username: "budi.manager", role: "manager" },
  { id: 3, fullName: "Citra Lestari", username: "citra.staff", role: "staff" },
];

export default function UserManagementPage() {
  const [isAdmin, setIsAdmin] = useState(true);
  const currentUserRole: UserRole = isAdmin ? "admin" : "staff";

  const [users, setUsers] = useState<UserAccount[]>(sampleUsers);

  const [selectedUser, setSelectedUser] = useState<UserAccount | null>(null);

  const AdminView = () => (
    <Tabs defaultValue="create" className="w-full">
      <TabsList className="grid w-full grid-cols-2">
        <TabsTrigger value="create">Create User</TabsTrigger>
        <TabsTrigger value="manage">Manage Users</TabsTrigger>
      </TabsList>

      {/* Tab untuk Membuat Pengguna Baru */}
      <TabsContent value="create">
        <Card>
          <CardHeader>
            <CardTitle>Create New User</CardTitle>
            <CardDescription>Fill in the details to create a new user account.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="fullname-create">Full Name</Label>
              <Input id="fullname-create" placeholder="e.g., John Doe" />
            </div>
            <div className="space-y-2">
              <Label htmlFor="username-create">Username</Label>
              <Input id="username-create" placeholder="e.g., johndoe" />
            </div>
            <div className="space-y-2">
              <Label htmlFor="password-create">Password</Label>
              <Input id="password-create" type="password" />
            </div>
            <div className="space-y-2">
              <Label htmlFor="confirm-password-create">Confirm Password</Label>
              <Input id="confirm-password-create" type="password" />
            </div>
            <div className="space-y-2">
              <Label htmlFor="role-create">Role</Label>
              <Select>
                <SelectTrigger id="role-create">
                  <SelectValue placeholder="Select a role" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="admin">Admin</SelectItem>
                  <SelectItem value="manager">Manager</SelectItem>
                  <SelectItem value="staff">Staff</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <Button className="w-full">Create Account</Button>
          </CardContent>
        </Card>
      </TabsContent>

      {/* Tab untuk Mengelola Pengguna */}
      <TabsContent value="manage">
        <Card>
          <CardHeader>
            <CardTitle>Manage Existing Users</CardTitle>
            <CardDescription>Update credentials and roles for existing users.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {users.map((user) => (
              <div key={user.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg border">
                <div>
                  <p className="font-semibold">{user.fullName}</p>
                  <p className="text-sm text-gray-500">
                    @{user.username} - <span className="capitalize font-medium">{user.role}</span>
                  </p>
                </div>
                <Button variant="outline" onClick={() => setSelectedUser(user)}>
                  Edit
                </Button>
              </div>
            ))}
          </CardContent>
        </Card>
      </TabsContent>
    </Tabs>
  );

  const UserView = () => (
    <Card className="w-full max-w-md">
      <CardHeader>
        <CardTitle>Update Your Profile</CardTitle>
        <CardDescription>Keep your personal information up to date.</CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="space-y-2">
          <Label htmlFor="fullname-update">Full Name</Label>
          <Input id="fullname-update" defaultValue="Citra Lestari" />
        </div>
        <div className="space-y-2">
          <Label htmlFor="username-update">Username</Label>
          <Input id="username-update" defaultValue="citra.staff" />
        </div>
        <div className="space-y-2">
          <Label htmlFor="current-password">Current Password</Label>
          <Input id="current-password" type="password" />
        </div>
        <div className="space-y-2">
          <Label htmlFor="new-password">New Password</Label>
          <Input id="new-password" type="password" />
        </div>
        <div className="space-y-2">
          <Label htmlFor="confirm-new-password">Confirm New Password</Label>
          <Input id="confirm-new-password" type="password" />
        </div>
        <Button className="w-full">Update Profile</Button>
      </CardContent>
    </Card>
  );

  return (
    <div className="min-h-screen bg-gray-50">
      <Header page="users" onUploadClick={() => {}} />
      <main className="max-w-4xl mx-auto p-4 md:p-6">
        <div className="flex items-center justify-center space-x-2 mb-6 p-4 bg-yellow-100 border border-yellow-300 rounded-lg">
          <Shield size={16} className="text-yellow-700" />
          <Label htmlFor="role-switcher" className="font-semibold text-yellow-800">
            Admin View
          </Label>
          <Switch id="role-switcher" checked={isAdmin} onCheckedChange={setIsAdmin} />
          <p className="text-sm text-yellow-700">Toggle to see user view</p>
        </div>

        <div className="flex justify-center">{currentUserRole === "admin" ? <AdminView /> : <UserView />}</div>
      </main>
    </div>
  );
}
