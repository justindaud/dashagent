"use client";

import { useState, useEffect } from "react";
import api from "@/lib/axios";
import axios from "axios";
import { Header } from "@/components/dashboard/Header";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Switch } from "@/components/ui/switch";
import { User, Shield, Loader2, Edit } from "lucide-react";
import { Skeleton } from "@/components/ui/skeleton";

interface UserAccount {
  user_id: string;
  username: string;
  full_name: string;
  role: string;
  is_active?: boolean;
}

interface UserViewProps {
  currentUser: UserAccount;
  handleProfileUpdate: (payload: any) => Promise<void>;
  isUpdatingProfile: boolean;
  updateMessage: { type: "success" | "error"; text: string } | null;
}

const UserView = ({ currentUser, handleProfileUpdate, isUpdatingProfile, updateMessage }: UserViewProps) => {
  const [isEditing, setIsEditing] = useState(false);
  const [updatedUsername, setUpdatedUsername] = useState(currentUser.username);
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmNewPassword, setConfirmNewPassword] = useState("");

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    handleProfileUpdate({
      username: updatedUsername,
      current_password: currentPassword,
      new_password: newPassword,
      confirm_new_password: confirmNewPassword,
    })
      .then(() => {
        setCurrentPassword("");
        setNewPassword("");
        setConfirmNewPassword("");
        setIsEditing(false);
      })
      .catch(() => {});
  };

  if (!isEditing) {
    return (
      <Card className="w-full max-w-md">
        <CardHeader>
          <div className="flex justify-between items-center">
            <CardTitle className="flex items-center gap-2">
              <User /> Your Profile
            </CardTitle>
            <Button variant="ghost" size="icon" onClick={() => setIsEditing(true)}>
              <Edit className="h-4 w-4" />
            </Button>
          </div>
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
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="w-full max-w-md">
      <CardHeader>
        <CardTitle>Edit Your Profile</CardTitle>
        <CardDescription>Update your username or password below.</CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="username-update">Username</Label>
            <Input id="username-update" value={updatedUsername} onChange={(e) => setUpdatedUsername(e.target.value.toUpperCase())} required />
          </div>
          <hr />
          <p className="text-sm text-gray-500">To change your password, fill all password fields.</p>
          <div className="space-y-2">
            <Label htmlFor="current-password">Current Password</Label>
            <Input
              id="current-password"
              type="password"
              value={currentPassword}
              onChange={(e) => setCurrentPassword(e.target.value)}
              placeholder="Required to save changes"
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="new-password">New Password</Label>
            <Input id="new-password" type="password" value={newPassword} onChange={(e) => setNewPassword(e.target.value)} />
          </div>
          <div className="space-y-2">
            <Label htmlFor="confirm-new-password">Confirm New Password</Label>
            <Input id="confirm-new-password" type="password" value={confirmNewPassword} onChange={(e) => setConfirmNewPassword(e.target.value)} />
          </div>
          <div className="flex gap-2 pt-2">
            <Button type="submit" className="flex-1" disabled={isUpdatingProfile}>
              {isUpdatingProfile ? <Loader2 className="h-4 w-4 animate-spin" /> : "Save Changes"}
            </Button>
            <Button type="button" variant="outline" onClick={() => setIsEditing(false)}>
              Cancel
            </Button>
          </div>
          {updateMessage && (
            <p className={`mt-2 text-sm text-center font-medium ${updateMessage.type === "success" ? "text-green-600" : "text-red-600"}`}>
              {updateMessage.text}
            </p>
          )}
        </form>
      </CardContent>
    </Card>
  );
};

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
  openEditModal: (user: UserAccount) => void;
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
  openEditModal,
}: AdminViewProps) => (
  <Tabs defaultValue="create" className="w-full">
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
              <Input
                id="username-create"
                placeholder="e.g., JOHNDOE"
                value={newUsername}
                onChange={(e) => setNewUsername(e.target.value.toUpperCase())}
                required
              />
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
          <CardDescription>Update roles and details for existing users.</CardDescription>
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
                <Button variant="outline" size="icon" onClick={() => openEditModal(user)}>
                  <Edit className="w-4 h-4" />
                </Button>
              </div>
            ))
          )}
        </CardContent>
      </Card>
    </TabsContent>
  </Tabs>
);

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
  const [registerMessage, setRegisterMessage] = useState<{ type: "success" | "error"; text: string } | null>(null);

  const [isUpdating, setIsUpdating] = useState(false);
  const [updateMessage, setUpdateMessage] = useState<{ type: "success" | "error"; text: string } | null>(null);

  const [isEditModalOpen, setIsEditModalOpen] = useState(false);
  const [userToEdit, setUserToEdit] = useState<UserAccount | null>(null);
  const [editFormData, setEditFormData] = useState({
    full_name: "",
    username: "",
    role: "",
    is_active: true,
    password: "",
    confirm_password: "",
  });

  const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8000";

  const fetchCurrentUser = async () => {
    try {
      const response = await axios.get(`${API_BASE}/profile`, { withCredentials: true });
      if (response.data?.data?.[0]) {
        const userData = response.data.data[0];
        setCurrentUser(userData);
        if (userData.role === "admin") fetchUsers();
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
      const response = await axios.get(`${API_BASE}/users`, { withCredentials: true });
      if (response.data?.data) setUsers(response.data.data);
    } catch (error: any) {
      if (error.response?.status !== 401) setRegisterMessage({ type: "error", text: "Failed to load user list." });
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
      setRegisterMessage({ type: "error", text: "Passwords do not match." });
      return;
    }
    setIsRegistering(true);
    setRegisterMessage(null);
    try {
      await axios.post(
        `${API_BASE}/auth/register`,
        {
          full_name: newFullName,
          username: newUsername.toUpperCase(),
          password: newPassword,
          confirm_password: newConfirmPassword,
          role: newRole,
        },
        { withCredentials: true }
      );
      setRegisterMessage({ type: "success", text: "User registered successfully!" });
      setNewFullName("");
      setNewUsername("");
      setNewPassword("");
      setNewConfirmPassword("");
      setNewRole("staff");
      fetchUsers();
    } catch (error: any) {
      const errorMessage = error.response?.data?.detail || "Registration failed.";
      setRegisterMessage({ type: "error", text: errorMessage });
    } finally {
      setIsRegistering(false);
    }
  };

  const handleProfileUpdate = async (payload: any) => {
    if (!currentUser) throw new Error("Current user not found");
    if (payload.new_password && payload.new_password !== payload.confirm_new_password) {
      setUpdateMessage({ type: "error", text: "New passwords do not match." });
      throw new Error("Passwords do not match");
    }
    if (payload.new_password && !payload.current_password) {
      setUpdateMessage({ type: "error", text: "Current password is required to set a new one." });
      throw new Error("Current password required");
    }
    setIsUpdating(true);
    setUpdateMessage(null);
    try {
      await axios.put(`${API_BASE}/users/${currentUser.user_id}`, payload);
      setUpdateMessage({ type: "success", text: "Profile updated successfully!" });
      await fetchCurrentUser();
    } catch (error: any) {
      const errorMessage = error.response?.data?.detail || "Failed to update profile.";
      setUpdateMessage({ type: "error", text: errorMessage });
      throw error;
    } finally {
      setIsUpdating(false);
    }
  };

  const openEditModal = (user: UserAccount) => {
    setUserToEdit(user);
    setEditFormData({
      full_name: user.full_name,
      username: user.username,
      role: user.role,
      is_active: user.is_active ?? true,
      password: "",
      confirm_password: "",
    });
    setIsEditModalOpen(true);
  };

  const handleUpdateUserByAdmin = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!userToEdit) return;

    if (editFormData.password && editFormData.password !== editFormData.confirm_password) {
      setUpdateMessage({ type: "error", text: "New passwords do not match." });
      return;
    }

    const payload: { [key: string]: any } = {};
    if (editFormData.full_name !== userToEdit.full_name) payload.full_name = editFormData.full_name;
    if (editFormData.username !== userToEdit.username) payload.username = editFormData.username.toUpperCase();
    if (editFormData.role !== userToEdit.role) payload.role = editFormData.role;
    if (editFormData.is_active !== userToEdit.is_active) payload.is_active = editFormData.is_active;
    if (editFormData.password) {
      payload.password = editFormData.password;
      payload.confirm_password = editFormData.confirm_password;
    }

    if (Object.keys(payload).length === 0) {
      setUpdateMessage({ type: "error", text: "No changes detected." });
      return;
    }

    setIsUpdating(true);
    setUpdateMessage(null);
    try {
      await axios.put(`${API_BASE}/users/${userToEdit.user_id}`, payload);
      setUpdateMessage({ type: "success", text: "User updated successfully!" });
      setIsEditModalOpen(false);
      fetchUsers();
    } catch (error: any) {
      const errorMessage = error.response?.data?.detail || "Failed to update user.";
      setUpdateMessage({ type: "error", text: errorMessage });
    } finally {
      setIsUpdating(false);
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
      <main className="max-w-7xl mx-auto p-4 md:p-6 w-full">
        {currentUser?.role === "admin" ? (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 items-start">
            <div className="lg:sticky lg:top-6">
              <UserView
                currentUser={currentUser}
                handleProfileUpdate={handleProfileUpdate}
                isUpdatingProfile={isUpdating}
                updateMessage={updateMessage}
              />
            </div>
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
              message={registerMessage}
              openEditModal={openEditModal}
            />
          </div>
        ) : currentUser ? (
          <div className="flex justify-center">
            <UserView
              currentUser={currentUser}
              handleProfileUpdate={handleProfileUpdate}
              isUpdatingProfile={isUpdating}
              updateMessage={updateMessage}
            />
          </div>
        ) : (
          <p>Could not load user profile.</p>
        )}
      </main>

      <Dialog open={isEditModalOpen} onOpenChange={setIsEditModalOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Edit User: {userToEdit?.full_name}</DialogTitle>
            <DialogDescription>Update the user's details below. Only fill in the fields you want to change.</DialogDescription>
          </DialogHeader>
          <form onSubmit={handleUpdateUserByAdmin} className="space-y-4 pt-4">
            <div className="space-y-2">
              <Label htmlFor="fullname-edit">Full Name</Label>
              <Input
                id="fullname-edit"
                value={editFormData.full_name}
                onChange={(e) => setEditFormData({ ...editFormData, full_name: e.target.value })}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="username-edit">Username</Label>
              <Input
                id="username-edit"
                value={editFormData.username}
                onChange={(e) => setEditFormData({ ...editFormData, username: e.target.value.toUpperCase() })}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="role-edit">Role</Label>
              <Select value={editFormData.role} onValueChange={(value) => setEditFormData({ ...editFormData, role: value })}>
                <SelectTrigger id="role-edit">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="admin">Admin</SelectItem>
                  <SelectItem value="manager">Manager</SelectItem>
                  <SelectItem value="staff">Staff</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="flex items-center space-x-2">
              <Switch
                id="is-active-edit"
                checked={editFormData.is_active}
                onCheckedChange={(checked) => setEditFormData({ ...editFormData, is_active: checked })}
              />
              <Label htmlFor="is-active-edit">User is Active</Label>
            </div>
            <hr />
            <p className="text-sm text-gray-500 pt-2">Leave password fields blank to keep it unchanged.</p>
            <div className="space-y-2">
              <Label htmlFor="password-edit">New Password</Label>
              <Input
                id="password-edit"
                type="password"
                value={editFormData.password}
                onChange={(e) => setEditFormData({ ...editFormData, password: e.target.value })}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="confirm-password-edit">Confirm New Password</Label>
              <Input
                id="confirm-password-edit"
                type="password"
                value={editFormData.confirm_password}
                onChange={(e) => setEditFormData({ ...editFormData, confirm_password: e.target.value })}
              />
            </div>
            {updateMessage && (
              <p className={`text-sm text-center font-medium ${updateMessage.type === "success" ? "text-green-600" : "text-red-600"}`}>
                {updateMessage.text}
              </p>
            )}
            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => setIsEditModalOpen(false)}>
                Cancel
              </Button>
              <Button type="submit" disabled={isUpdating}>
                {isUpdating ? <Loader2 className="h-4 w-4 animate-spin" /> : "Save Changes"}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
}
