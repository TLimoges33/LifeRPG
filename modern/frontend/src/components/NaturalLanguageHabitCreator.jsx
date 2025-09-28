import React, { useState } from "react";
import { Card, CardHeader, CardTitle, CardContent } from "./ui/card";
import { Button } from "./ui/button";
import { Input } from "./ui/input";
import { Sparkles, Loader2 } from "lucide-react";

const NaturalLanguageHabitCreator = ({ onHabitCreated }) => {
  const [prompt, setPrompt] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const token = localStorage.getItem("token");
      const res = await fetch("/api/v1/ai/habits/nlp-create", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ prompt }),
      });
      const data = await res.json();
      if (res.ok && data.success) {
        setResult(data.habit);
        setPrompt("");
        if (onHabitCreated) onHabitCreated(data.habit);
      } else {
        setError(data.error || "Could not create habit");
      }
    } catch (err) {
      setError("Network error");
    } finally {
      setLoading(false);
    }
  };

  return (
    <Card className="max-w-xl mx-auto my-8">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Sparkles className="h-5 w-5 text-purple-500" />
          Create a Habit with AI
        </CardTitle>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="flex flex-col gap-4">
          <Input
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            placeholder="e.g. Remind me to meditate every morning at 7am"
            disabled={loading}
            required
            className="text-lg"
          />
          <Button type="submit" disabled={loading || !prompt.trim()}>
            {loading ? (
              <Loader2 className="animate-spin h-4 w-4 mr-2" />
            ) : (
              <Sparkles className="h-4 w-4 mr-2" />
            )}
            Create Habit
          </Button>
        </form>
        {result && (
          <div className="mt-4 p-3 bg-green-50 rounded text-green-700">
            <div className="font-semibold">Habit Created:</div>
            <div>
              Title: <span className="font-mono">{result.title}</span>
            </div>
            <div>
              Cadence: <span className="font-mono">{result.cadence}</span>
            </div>
            {result.due_time && (
              <div>
                Time: <span className="font-mono">{result.due_time}</span>
              </div>
            )}
          </div>
        )}
        {error && (
          <div className="mt-4 p-3 bg-red-50 rounded text-red-700">{error}</div>
        )}
      </CardContent>
    </Card>
  );
};

export default NaturalLanguageHabitCreator;
