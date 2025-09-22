"use client";

import { useState, useEffect } from "react";
import api from "@/lib/axios";
import { Header } from "@/components/dashboard/Header";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import { User, Trash2, Loader2 } from "lucide-react";
import { Skeleton } from "@/components/ui/skeleton";

// Tipe data untuk pengguna dari API
interface UserAccount {
  user_id: string;
  username: string;
  full_name: string;
  role: string;
  is_active?: boolean;
}

// Komponen untuk Tampilan Admin
interface AdminViewProps {
  users: UserAccount[];
  isLoadingUsers: boolean;
  handleRegister: (e: React.FormEvent) => void;
  newFullName: string;
  setNewFullName: (value: string) => void;
  newUsername: string;
  setNewUsername: (value: string) => void;
  newPassword: string;
  setNewPassword: (value: string) => void;
  newConfirmPassword: string;
  setNewConfirmPassword: (value: string) => void;
  newRole: string;
  setNewRole: (value: string) => void;
  isRegistering: boolean;
  message: { type: "success" | "error"; text: string } | null;
  confirmDelete: (username: string) => void;
}

const AdminView = ({
  users,
  isLoadingUsers,
  handleRegister,
  newFullName,
  setNewFullName,
  newUsername,
  setNewUsername,
  newPassword,
  setNewPassword,
  newConfirmPassword,
  setNewConfirmPassword,
  newRole,
  setNewRole,
  isRegistering,
  message,
  confirmDelete,
}: AdminViewProps) => (
  <Tabs defaultValue="create" className="w-full max-w-4xl">
    <TabsList className="grid w-full grid-cols-2">
      <TabsTrigger value="create">Create User</TabsTrigger>
      <TabsTrigger value="manage">Manage Users</TabsTrigger>
    </TabsList>

    <TabsContent value="create">
      <Card>
        <CardHeader>
          <CardTitle>Create New User</CardTitle>
          <CardDescription>Fill in the details to create a new user account.</CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleRegister} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="fullname-create">Full Name</Label>
              <Input
                id="fullname-create"
                placeholder="e.g., John Doe"
                value={newFullName}
                onChange={(e) => setNewFullName(e.target.value)}
                required
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="username-create">Username</Label>
              <Input id="username-create" placeholder="e.g., johndoe" value={newUsername} onChange={(e) => setNewUsername(e.target.value)} required />
            </div>
            <div className="space-y-2">
              <Label htmlFor="password-create">Password</Label>
              <Input id="password-create" type="password" value={newPassword} onChange={(e) => setNewPassword(e.target.value)} required />
            </div>
            <div className="space-y-2">
              <Label htmlFor="confirm-password-create">Confirm Password</Label>
              <Input
                id="confirm-password-create"
                type="password"
                value={newConfirmPassword}
                onChange={(e) => setNewConfirmPassword(e.target.value)}
                required
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="role-create">Role</Label>
              <Select value={newRole} onValueChange={(value) => setNewRole(value)}>
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
            <Button type="submit" className="w-full" disabled={isRegistering}>
              {isRegistering ? "Creating Account..." : "Create Account"}
            </Button>
            {message && (
              <p className={`mt-2 text-sm text-center font-medium ${message.type === "success" ? "text-green-600" : "text-red-600"}`}>
                {message.text}
              </p>
            )}
          </form>
        </CardContent>
      </Card>
    </TabsContent>

    <TabsContent value="manage">
      <Card>
        <CardHeader>
          <CardTitle>Manage Existing Users</CardTitle>
          <CardDescription>View, update, or delete existing users.</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {isLoadingUsers ? (
            <div className="space-y-2">
              <Skeleton className="h-16 w-full" />
              <Skeleton className="h-16 w-full" />
            </div>
          ) : (
            users.map((user) => (
              <div key={user.user_id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg border">
                <div className="flex items-center gap-3">
                  <span
                    className={`h-2.5 w-2.5 rounded-full ${user.is_active ? "bg-green-500" : "bg-gray-400"}`}
                    title={user.is_active ? "Active" : "Inactive"}
                  ></span>
                  <div>
                    <p className="font-semibold">{user.full_name}</p>
                    <p className="text-sm text-gray-500">
                      @{user.username} - <span className="capitalize font-medium">{user.role}</span>
                    </p>
                  </div>
                </div>
                <Button variant="destructive" size="icon" onClick={() => confirmDelete(user.username)}>
                  <Trash2 className="w-4 h-4" />
                </Button>
              </div>
            ))
          )}
        </CardContent>
      </Card>
    </TabsContent>
  </Tabs>
);

// Komponen untuk Tampilan Pengguna Biasa
interface UserViewProps {
  currentUser: UserAccount;
}
const UserView = ({ currentUser }: UserViewProps) => (
  <Card className="w-full max-w-md">
    <CardHeader>
      <CardTitle className="flex items-center gap-2">
        <User /> Your Profile
      </CardTitle>
      <CardDescription>View your personal information.</CardDescription>
    </CardHeader>
    <CardContent className="space-y-4">
      <div>
        <Label>Full Name</Label>
        <p className="font-semibold text-lg">{currentUser.full_name}</p>
      </div>
      <div>
        <Label>Username</Label>
        <p className="text-gray-700">{currentUser.username}</p>
      </div>
      <div>
        <Label>Role</Label>
        <p className="text-gray-700 capitalize">{currentUser.role}</p>
      </div>
      <div>
        <Label>Status</Label>
        <p className={`font-semibold ${currentUser.is_active ? "text-green-600" : "text-red-600"}`}>
          {currentUser.is_active ? "Active" : "Inactive"}
        </p>
      </div>
    </CardContent>
  </Card>
);

// Komponen Halaman Utama
export default function UserManagementPage() {
  const [currentUser, setCurrentUser] = useState<UserAccount | null>(null);
  const [isCheckingAuth, setIsCheckingAuth] = useState(true);
  const [users, setUsers] = useState<UserAccount[]>([]);
  const [isLoadingUsers, setIsLoadingUsers] = useState(false);
  const [newFullName, setNewFullName] = useState("");
  const [newUsername, setNewUsername] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [newConfirmPassword, setNewConfirmPassword] = useState("");
  const [newRole, setNewRole] = useState("staff");
  const [isRegistering, setIsRegistering] = useState(false);
  const [message, setMessage] = useState<{ type: "success" | "error"; text: string } | null>(null);
  const [userToDelete, setUserToDelete] = useState<string | null>(null);
  const [isAlertOpen, setIsAlertOpen] = useState(false);

  const fetchCurrentUser = async () => {
    try {
      const response = await api.get("/api/profile");
      if (response.data && response.data.data && response.data.data.length > 0) {
        const userData = response.data.data[0];
        setCurrentUser(userData);
        if (userData.role === "admin") {
          fetchUsers();
        }
      }
    } catch (error) {
      console.error("Failed to fetch current user", error);
    } finally {
      setIsCheckingAuth(false);
    }
  };

  const fetchUsers = async () => {
    setIsLoadingUsers(true);
    try {
      const response = await api.get("/api/users");
      if (response.data && response.data.data) {
        setUsers(response.data.data);
      }
    } catch (error: any) {
      if (error.response?.status !== 401) {
        console.error("Failed to fetch users:", error);
        setMessage({ type: "error", text: "Failed to load user list." });
      }
    } finally {
      setIsLoadingUsers(false);
    }
  };

  useEffect(() => {
    fetchCurrentUser();
  }, []);

  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault();
    if (newPassword !== newConfirmPassword) {
      setMessage({ type: "error", text: "Passwords do not match." });
      return;
    }
    setIsRegistering(true);
    setMessage(null);
    try {
      await api.post("/api/auth/register", {
        full_name: newFullName,
        username: newUsername,
        password: newPassword,
        confirm_password: newConfirmPassword,
        role: newRole,
      });
      setMessage({ type: "success", text: "User registered successfully!" });
      setNewFullName("");
      setNewUsername("");
      setNewPassword("");
      setNewConfirmPassword("");
      setNewRole("staff");
      fetchUsers();
    } catch (error: any) {
      if (error.response?.status !== 401) {
        setMessage({ type: "error", text: error.response?.data?.detail || "Registration failed." });
      }
    } finally {
      setIsRegistering(false);
    }
  };

  const confirmDelete = (username: string) => {
    setUserToDelete(username);
    setIsAlertOpen(true);
  };

  const handleDelete = async () => {
    if (!userToDelete) return;
    try {
      await api.delete(`/api/users/${userToDelete}`);
      setMessage({ type: "success", text: `User '${userToDelete}' deleted successfully.` });
      fetchUsers();
    } catch (error: any) {
      if (error.response?.status !== 401) {
        setMessage({ type: "error", text: error.response?.data?.detail || "Failed to delete user." });
      }
    } finally {
      setUserToDelete(null);
    }
  };

  if (isCheckingAuth) {
    return (
      <div className="flex h-screen w-full items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <Header page="users" />
      <main className="flex justify-center p-4 md:p-6">
        {currentUser?.role === "admin" ? (
          <AdminView
            users={users}
            isLoadingUsers={isLoadingUsers}
            handleRegister={handleRegister}
            newFullName={newFullName}
            setNewFullName={setNewFullName}
            newUsername={newUsername}
            setNewUsername={setNewUsername}
            newPassword={newPassword}
            setNewPassword={setNewPassword}
            newConfirmPassword={newConfirmPassword}
            setNewConfirmPassword={setNewConfirmPassword}
            newRole={newRole}
            setNewRole={setNewRole}
            isRegistering={isRegistering}
            message={message}
            confirmDelete={confirmDelete}
          />
        ) : currentUser ? (
          <UserView currentUser={currentUser} />
        ) : (
          <p>Could not load user profile.</p>
        )}
      </main>

      <AlertDialog open={isAlertOpen} onOpenChange={setIsAlertOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Are you sure?</AlertDialogTitle>
            <AlertDialogDescription>This will permanently delete the user '{userToDelete}'. This action cannot be undone.</AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel onClick={() => setUserToDelete(null)}>Cancel</AlertDialogCancel>
            <AlertDialogAction onClick={handleDelete}>Delete User</AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}
