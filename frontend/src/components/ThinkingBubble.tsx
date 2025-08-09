import React from "react";

const ThinkingBubble: React.FC = () => {
  return (
    <div className="my-2 flex justify-start">
      <div className="max-w-[75%] rounded-lg border border-border bg-surface p-3 text-sm rounded-bl-none">
        <div className="animate-pulse space-y-2">
          <div className="h-3 w-3/4 rounded bg-border/70" />
          <div className="h-3 w-2/3 rounded bg-border/60" />
          <div className="h-3 w-1/2 rounded bg-border/50" />
        </div>
        <div className="mt-2 text-xs text-muted">Thinking<span className="animate-pulse">...</span></div>
      </div>
    </div>
  );
};

export default ThinkingBubble;


