"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { BookText, LogOut } from "lucide-react";
import { useAuth } from "@/lib/store";
import { Button } from "./ui/button";
import { ThemeToggle } from "./ThemeToggle";

export function Navbar() {
  const { user, logout } = useAuth();
  const router = useRouter();

  return (
    <header className="sticky top-0 z-10 border-b border-border bg-card/80 backdrop-blur">
      <div className="mx-auto flex h-14 max-w-6xl items-center justify-between px-4">
        <Link href="/dashboard" className="flex items-center gap-2 font-semibold">
          <BookText className="h-5 w-5 text-primary" />
          Index Generator
        </Link>
        <div className="flex items-center gap-2">
          <ThemeToggle />
          {user && (
            <>
              <span className="hidden text-sm text-muted sm:inline">
                {user.name}
              </span>
              <Button
                variant="outline"
                size="sm"
                onClick={() => {
                  logout();
                  router.push("/login");
                }}
              >
                <LogOut className="h-4 w-4" /> Logout
              </Button>
            </>
          )}
        </div>
      </div>
    </header>
  );
}
