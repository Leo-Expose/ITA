"use client";

import { useEffect, useState } from "react";
import { getApiKeys, saveApiKey, deleteApiKey, testApiKey } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Eye, EyeOff, Trash2, CheckCircle2, XCircle, Loader2, ExternalLink, Key } from "lucide-react";
import { toast } from "sonner";

interface KeyStatus {
  provider: string;
  name: string;
  configured: boolean;
  source: "ui" | "env" | null;
  masked: string | null;
  signup_url: string;
  key_format: string;
}

export function ApiKeysManager() {
  const [keys, setKeys] = useState<Record<string, KeyStatus>>({});
  const [loading, setLoading] = useState(true);
  const [editing, setEditing] = useState<Record<string, string>>({});
  const [showKey, setShowKey] = useState<Record<string, boolean>>({});
  const [testing, setTesting] = useState<Record<string, boolean>>({});
  const [testResult, setTestResult] = useState<Record<string, { ok: boolean; message: string }>>({});

  const load = async () => {
    setLoading(true);
    try {
      const data: any = await getApiKeys();
      setKeys(data);
    } catch {
      toast.error("Failed to load API keys");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const handleSave = async (provider: string) => {
    const key = editing[provider]?.trim();
    if (!key) {
      toast.error("Enter an API key");
      return;
    }
    try {
      await saveApiKey(provider, key);
      toast.success(`${keys[provider]?.name} API key saved`);
      setEditing((e) => ({ ...e, [provider]: "" }));
      setShowKey((s) => ({ ...s, [provider]: false }));
      setTestResult((r) => ({ ...r, [provider]: undefined as any }));
      load();
    } catch (e: any) {
      toast.error(e.message || "Failed to save");
    }
  };

  const handleDelete = async (provider: string) => {
    if (!confirm(`Remove ${keys[provider]?.name} API key?`)) return;
    try {
      await deleteApiKey(provider);
      toast.success("API key removed");
      load();
    } catch (e: any) {
      toast.error(e.message || "Failed to remove");
    }
  };

  const handleTest = async (provider: string) => {
    setTesting((t) => ({ ...t, [provider]: true }));
    setTestResult((r) => ({ ...r, [provider]: undefined as any }));
    try {
      const keyToTest = editing[provider]?.trim();
      const result: any = await testApiKey(provider, keyToTest || undefined);
      setTestResult((r) => ({
        ...r,
        [provider]: { ok: result.ok, message: result.ok ? result.message : result.error },
      }));
      if (result.ok) toast.success(`${keys[provider]?.name} works!`);
      else toast.error(`Test failed: ${result.error}`);
    } catch (e: any) {
      setTestResult((r) => ({ ...r, [provider]: { ok: false, message: e.message } }));
    } finally {
      setTesting((t) => ({ ...t, [provider]: false }));
    }
  };

  const priorityProviders = ["anthropic", "openai", "google"];
  const sortedKeys = Object.values(keys).sort((a, b) => {
    const aIdx = priorityProviders.indexOf(a.provider);
    const bIdx = priorityProviders.indexOf(b.provider);
    const aVal = aIdx === -1 ? 99 : aIdx;
    const bVal = bIdx === -1 ? 99 : bIdx;
    return aVal - bVal;
  });

  return (
    <Card>
      <CardHeader className="pb-3">
        <CardTitle className="text-lg flex items-center gap-2">
          <Key className="h-5 w-5" />
          API Keys
        </CardTitle>
        <p className="text-xs text-muted-foreground">
          Keys saved here are stored locally in <code className="bg-muted px-1 rounded">~/.tradingagents/trading_agent.db</code> and take priority over <code className="bg-muted px-1 rounded">.env</code>. Never shared or synced.
        </p>
      </CardHeader>
      <CardContent className="space-y-3">
        {loading ? (
          <div className="py-6 text-center text-muted-foreground text-sm">Loading...</div>
        ) : (
          sortedKeys.map((k) => (
            <div key={k.provider} className={`p-4 rounded-lg border ${k.configured ? "border-green-200 bg-green-50/30" : "border-border"}`}>
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-2">
                  <span className="font-medium">{k.name}</span>
                  {k.configured ? (
                    <Badge variant="outline" className="bg-green-100 text-green-800 border-green-300 text-xs">
                      <CheckCircle2 className="h-3 w-3 mr-1" />
                      Configured
                    </Badge>
                  ) : (
                    <Badge variant="outline" className="text-xs">Not set</Badge>
                  )}
                  {k.source && (
                    <Badge variant="outline" className="text-xs">
                      via {k.source === "ui" ? "UI" : ".env"}
                    </Badge>
                  )}
                </div>
                {k.signup_url && !k.configured && (
                  <a
                    href={k.signup_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-xs text-blue-600 hover:underline flex items-center gap-1"
                  >
                    Get key <ExternalLink className="h-3 w-3" />
                  </a>
                )}
              </div>

              {k.configured && k.masked && (
                <p className="text-xs font-mono text-muted-foreground mb-2">{k.masked}</p>
              )}

              <div className="flex gap-2 items-center">
                <div className="relative flex-1">
                  <Input
                    type={showKey[k.provider] ? "text" : "password"}
                    placeholder={k.key_format || "Enter API key..."}
                    value={editing[k.provider] || ""}
                    onChange={(e) => setEditing((ed) => ({ ...ed, [k.provider]: e.target.value }))}
                    className="pr-9 font-sans"
                  />
                  <button
                    type="button"
                    onClick={() => setShowKey((s) => ({ ...s, [k.provider]: !s[k.provider] }))}
                    className="absolute right-2 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
                  >
                    {showKey[k.provider] ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                  </button>
                </div>
                <Button size="sm" onClick={() => handleSave(k.provider)} disabled={!editing[k.provider]?.trim()}>
                  Save
                </Button>
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => handleTest(k.provider)}
                  disabled={testing[k.provider] || (!k.configured && !editing[k.provider]?.trim())}
                >
                  {testing[k.provider] ? <Loader2 className="h-3 w-3 animate-spin" /> : "Test"}
                </Button>
                {k.configured && k.source === "ui" && (
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={() => handleDelete(k.provider)}
                    className="text-red-600 hover:text-red-700 hover:bg-red-50"
                  >
                    <Trash2 className="h-3 w-3" />
                  </Button>
                )}
              </div>

              {testResult[k.provider] && (
                <div className={`mt-2 text-xs flex items-start gap-1 ${testResult[k.provider].ok ? "text-green-700" : "text-red-700"}`}>
                  {testResult[k.provider].ok ? (
                    <CheckCircle2 className="h-3 w-3 mt-0.5 flex-shrink-0" />
                  ) : (
                    <XCircle className="h-3 w-3 mt-0.5 flex-shrink-0" />
                  )}
                  <span>{testResult[k.provider].message}</span>
                </div>
              )}
            </div>
          ))
        )}
      </CardContent>
    </Card>
  );
}
