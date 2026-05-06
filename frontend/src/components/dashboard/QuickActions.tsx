"use client";

import { useState } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Radar, Target, CandlestickChart, Award, FlaskConical, Calculator } from "lucide-react";
import Link from "next/link";
import { PositionSizeCalculator } from "@/components/PositionSizeCalculator";

const quickLinks = [
  {
    href: "/scanner",
    label: "Scan Market",
    description: "Gap, Volume, Breakout",
    icon: Radar,
    color: "text-orange-600 bg-orange-50",
  },
  {
    href: "/strategies",
    label: "Strategies",
    description: "S/R, Cyclical patterns",
    icon: Target,
    color: "text-purple-600 bg-purple-50",
  },
  {
    href: "/charts",
    label: "Charts",
    description: "Candlestick charts",
    icon: CandlestickChart,
    color: "text-blue-600 bg-blue-50",
  },
  {
    href: "/performance",
    label: "Performance",
    description: "Strategy win rates",
    icon: Award,
    color: "text-green-600 bg-green-50",
  },
  {
    href: "/backtest",
    label: "Backtest",
    description: "Historical testing",
    icon: FlaskConical,
    color: "text-indigo-600 bg-indigo-50",
  },
];

export function QuickActions() {
  const [calcOpen, setCalcOpen] = useState(false);

  return (
    <>
      <Card>
        <CardContent className="p-4">
          <h3 className="text-sm font-semibold mb-3">Quick Actions</h3>
          <div className="grid grid-cols-2 md:grid-cols-6 gap-2">
            {quickLinks.map((action) => (
              <Link key={action.href} href={action.href}>
                <div className="p-3 rounded-lg border border-border hover:border-primary/30 hover:bg-accent/30 transition-colors cursor-pointer h-full">
                  <div className={`p-1.5 rounded-lg ${action.color} inline-flex mb-2`}>
                    <action.icon className="h-4 w-4" />
                  </div>
                  <p className="font-medium text-sm">{action.label}</p>
                  <p className="text-xs text-muted-foreground">{action.description}</p>
                </div>
              </Link>
            ))}
            {/* Position Size Calculator - opens dialog */}
            <button
              onClick={() => setCalcOpen(true)}
              className="p-3 rounded-lg border border-border hover:border-primary/30 hover:bg-accent/30 transition-colors cursor-pointer text-left"
            >
              <div className="p-1.5 rounded-lg text-teal-600 bg-teal-50 inline-flex mb-2">
                <Calculator className="h-4 w-4" />
              </div>
              <p className="font-medium text-sm">Position Size</p>
              <p className="text-xs text-muted-foreground">Calculate shares to buy</p>
            </button>
          </div>
        </CardContent>
      </Card>
      <PositionSizeCalculator open={calcOpen} onClose={() => setCalcOpen(false)} />
    </>
  );
}
