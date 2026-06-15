import { useState } from "react";
import { Outlet } from "react-router-dom";
import { LogOut, Settings as SettingsIcon } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { SettingsDialog } from "@/components/settings/SettingsDialog";
import { ApiKeyStatusBadge } from "@/components/settings/ApiKeyStatusBadge";
import { useAuth } from "@/hooks/useAuth";
import { useTutorialAnchor } from "@/hooks/useTutorial";

function initials(name: string): string {
  return name
    .split(/[\s._-]+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0]?.toUpperCase())
    .join("");
}

export function AppShell() {
  const { agent, logout } = useAuth();
  const [settingsOpen, setSettingsOpen] = useState(false);

  useTutorialAnchor("api-key", true);

  const displayName = agent?.display_name ?? agent?.sub ?? "Agent";

  return (
    <div className="flex min-h-svh flex-col">
      <header className="flex items-center justify-between border-b px-4 py-3 print:hidden">
        <h1 className="text-lg font-semibold">TTB Label Verification System</h1>
        <div className="flex items-center gap-2">
          <div id="tutorial-api-key">
            <ApiKeyStatusBadge onOpenSettings={() => setSettingsOpen(true)} />
          </div>
          <Button
            variant="ghost"
            size="icon"
            aria-label="Settings"
            onClick={() => setSettingsOpen(true)}
          >
            <SettingsIcon className="size-4" />
          </Button>
          <DropdownMenu>
            <DropdownMenuTrigger
              render={
                <Button variant="ghost" className="gap-2 px-2">
                  <Avatar className="size-6">
                    <AvatarFallback>{initials(displayName)}</AvatarFallback>
                  </Avatar>
                  <span className="text-sm">{displayName}</span>
                </Button>
              }
            />
            <DropdownMenuContent align="end">
              <DropdownMenuItem onClick={logout}>
                <LogOut className="size-4" />
                Log out
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </header>

      <main className="flex-1 p-4">
        <Outlet />
      </main>

      <SettingsDialog open={settingsOpen} onOpenChange={setSettingsOpen} />
    </div>
  );
}
