"use client";

import Link from "next/link";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { ArrowRight, type LucideIcon } from "lucide-react";

interface Props {
  title: string;
  description: string;
  href: string;
  buttonText?: string;
  icon?: LucideIcon;
}

export function NextStep({ title, description, href, buttonText = "Go", icon: Icon }: Props) {
  return (
    <Card className="bg-gradient-to-r from-blue-50 to-purple-50 border-blue-200">
      <CardContent className="p-4 flex items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          {Icon && (
            <div className="p-2 rounded-lg bg-blue-100">
              <Icon className="h-4 w-4 text-blue-600" />
            </div>
          )}
          <div>
            <p className="text-xs font-semibold text-blue-700">NEXT STEP</p>
            <p className="font-medium text-sm">{title}</p>
            <p className="text-xs text-muted-foreground">{description}</p>
          </div>
        </div>
        <Link href={href}>
          <Button size="sm">
            {buttonText} <ArrowRight className="h-3 w-3 ml-1" />
          </Button>
        </Link>
      </CardContent>
    </Card>
  );
}
